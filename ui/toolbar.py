import os
import datetime
import traceback
import keyboard
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton,
    QSystemTrayIcon, QMenu, QAction, QStyle, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QCursor

from recorder.screen_capture import ScreenCaptureThread
from recorder.audio_capture import AudioCaptureThread
from recorder.encoder import Encoder
from ui.region_selector import RegionSelector
from ui.window_picker import WindowPicker
from utils.win_utils import get_window_rect, get_all_monitors_rect


STYLE = """
QWidget#toolbar {
    background-color: rgba(28, 28, 32, 220);
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,30);
}
QPushButton {
    background: transparent;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    font-size: 15px;
    padding: 2px 6px;
    min-width: 28px;
    min-height: 28px;
}
QPushButton:hover {
    background: rgba(255,255,255,18);
}
QPushButton:pressed {
    background: rgba(255,255,255,30);
}
QPushButton:checked {
    background: rgba(80, 160, 255, 60);
    color: #60b0ff;
}
QPushButton#btn_record {
    color: #ff5555;
    font-size: 16px;
}
QPushButton#btn_record:disabled {
    color: #555;
}
QPushButton#btn_pause {
    color: #ffcc44;
}
QPushButton#btn_pause:disabled {
    color: #555;
}
QPushButton#btn_stop {
    color: #aaaaaa;
}
QPushButton#btn_stop:disabled {
    color: #555;
}
QPushButton#btn_close {
    color: #888;
    font-size: 13px;
}
QPushButton#btn_close:hover {
    color: #ff5555;
    background: rgba(255,60,60,18);
}
QLabel#timer {
    color: #cccccc;
    font-family: "Consolas", monospace;
    font-size: 13px;
    min-width: 60px;
}
QLabel#sep {
    color: rgba(255,255,255,30);
    font-size: 18px;
}
QToolTip {
    background-color: #1e1e24;
    color: #e0e0e0;
    border: 1px solid rgba(255,255,255,60);
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
    font-family: "Segoe UI", sans-serif;
    opacity: 240;
}
"""


class Toolbar(QWidget):
    # Signals used to marshal hotkey callbacks (background thread) to the Qt main thread
    _sig_record = pyqtSignal()
    _sig_pause  = pyqtSignal()

    def __init__(self, config: dict, save_config_fn, app_version: str = "0.0.0"):
        super().__init__()
        self.config = config
        self.save_config = save_config_fn
        self._app_version = app_version
        self._drag_pos = None
        self._recording = False
        self._paused = False
        self._elapsed_secs = 0
        self._capture_rect = None
        self._capture_mode = config.get("capture_mode", "fullscreen")

        self._capture_thread: ScreenCaptureThread = None
        self._audio_thread: AudioCaptureThread = None
        self._encoder: Encoder = None

        self._setup_window()
        self._build_ui()
        self._setup_tray()
        self._setup_hotkeys()
        self._update_button_states()

    # ── window setup ────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setObjectName("toolbar")
        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        self.setFixedHeight(44)
        # Position top-centre of primary screen
        from PyQt5.QtWidgets import QDesktopWidget
        desk = QDesktopWidget().availableGeometry()
        self.move(desk.center().x() - 200, desk.top() + 10)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # Record / Pause / Stop
        self.btn_record = self._btn("●", "btn_record", "Start Recording\nBegin capturing your screen.\nHotkey: Ctrl+Alt+R")
        self.btn_pause  = self._btn("⏸", "btn_pause",  "Pause / Resume\nTemporarily pause the recording.\nHotkey: Ctrl+Alt+P")
        self.btn_stop   = self._btn("■", "btn_stop",   "Stop Recording\nFinish and save the video to your Videos folder.")
        self.btn_record.clicked.connect(self._on_record)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_stop.clicked.connect(self._on_stop)

        # Timer
        self.lbl_timer = QLabel("00:00:00")
        self.lbl_timer.setObjectName("timer")
        self.lbl_timer.setAlignment(Qt.AlignCenter)
        self.lbl_timer.setToolTip("Recording duration (hours : minutes : seconds)")

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        # Separator
        sep = QLabel("│")
        sep.setObjectName("sep")

        # Capture mode buttons
        self.btn_full   = self._btn("🖥", "btn_mode", "Full screen", checkable=True)
        self.btn_region = self._btn("▣", "btn_mode", "Select region", checkable=True)
        self.btn_window = self._btn("⬜", "btn_mode", "Capture window", checkable=True)
        self.btn_full.clicked.connect(lambda: self._set_mode("fullscreen"))
        self.btn_region.clicked.connect(lambda: self._set_mode("region"))
        self.btn_window.clicked.connect(lambda: self._set_mode("window"))
        self._mode_buttons = [self.btn_full, self.btn_region, self.btn_window]
        self._refresh_mode_buttons()

        # Close
        sep2 = QLabel("│")
        sep2.setObjectName("sep")
        self.btn_close = self._btn("✕", "btn_close", "Minimise to tray")
        self.btn_close.clicked.connect(self.hide)

        for w in [
            self.btn_record, self.btn_pause, self.btn_stop,
            self.lbl_timer, sep,
            self.btn_full, self.btn_region, self.btn_window,
            sep2, self.btn_close,
        ]:
            layout.addWidget(w)

        self.setMinimumWidth(layout.sizeHint().width() + 20)

    def _btn(self, text, obj_name, tooltip="", checkable=False):
        b = QPushButton(text)
        b.setObjectName(obj_name)
        b.setToolTip(tooltip)
        b.setCheckable(checkable)
        b.setCursor(QCursor(Qt.PointingHandCursor))
        return b

    # ── system tray ──────────────────────────────────────────────────────────

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self._tray.setToolTip(f"ScRecorder {self._app_version}")

        menu = QMenu()
        act_show   = QAction("Show toolbar", self)
        act_record = QAction("Start recording", self)
        act_stop   = QAction("Stop recording", self)
        act_about  = QAction(f"About ScRecorder {self._app_version}", self)
        act_quit   = QAction("Exit", self)

        act_show.triggered.connect(self.show)
        act_record.triggered.connect(self._on_record)
        act_stop.triggered.connect(self._on_stop)
        act_about.triggered.connect(self._show_about)
        act_quit.triggered.connect(self._quit)

        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_record)
        menu.addAction(act_stop)
        menu.addSeparator()
        menu.addAction(act_about)
        menu.addSeparator()
        menu.addAction(act_quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._tray_activated)
        self._tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()

    # ── global hotkeys ───────────────────────────────────────────────────────

    def _setup_hotkeys(self):
        # Connect signals so hotkey callbacks (fired on keyboard's background thread)
        # are safely marshalled to the Qt main thread before touching any Qt objects.
        self._sig_record.connect(self._on_record)
        self._sig_pause.connect(self._on_pause)
        try:
            keyboard.add_hotkey(
                self.config.get("hotkey_record", "ctrl+alt+r"),
                self._sig_record.emit, suppress=False
            )
            keyboard.add_hotkey(
                self.config.get("hotkey_pause", "ctrl+alt+p"),
                self._sig_pause.emit, suppress=False
            )
        except Exception:
            pass  # hotkeys unavailable without admin on some systems

    # ── capture mode ─────────────────────────────────────────────────────────

    def _set_mode(self, mode: str):
        self._capture_mode = mode
        self.config["capture_mode"] = mode
        self.save_config(self.config)
        self._refresh_mode_buttons()

    def _refresh_mode_buttons(self):
        modes = ["fullscreen", "region", "window"]
        for btn, mode in zip(self._mode_buttons, modes):
            btn.setChecked(self._capture_mode == mode)

    def _resolve_capture_rect(self):
        """Return (x, y, w, h) for the chosen capture mode. Returns None on cancel."""
        if self._capture_mode == "fullscreen":
            return get_all_monitors_rect()

        if self._capture_mode == "region":
            self.hide()
            selector = RegionSelector()
            rect = selector.select()
            self.show()
            return rect  # None if cancelled

        if self._capture_mode == "window":
            picker = WindowPicker(self)
            hwnd = picker.pick()
            if hwnd is None:
                return None
            return get_window_rect(hwnd)

        return get_all_monitors_rect()

    # ── recording controls ───────────────────────────────────────────────────

    def _on_record(self):
        if self._recording:
            return
        try:
            rect = self._resolve_capture_rect()
            if not rect:
                return

            self._capture_rect = rect
            x, y, w, h = rect
            w = w if w % 2 == 0 else w - 1
            h = h if h % 2 == 0 else h - 1
            self._capture_rect = (x, y, w, h)

            fps = self.config.get("fps", 30)
            output_path = self._make_output_path()

            # Verify ffmpeg is reachable before starting threads
            from recorder.encoder import _find_ffmpeg
            import shutil as _shutil
            _ff = _find_ffmpeg()
            if not (os.path.isfile(_ff) or _shutil.which(_ff)):
                raise FileNotFoundError(
                    f"ffmpeg not found at: {_ff}\n"
                    f"Place ffmpeg.exe in the 'assets' folder next to main.py."
                )

            self._encoder = Encoder(output_path, w, h, fps)
            self._encoder.start()

            self._audio_thread = AudioCaptureThread(self._encoder.audio_queue)
            self._audio_thread.start()

            self._capture_thread = ScreenCaptureThread(
                self._capture_rect, fps, self._encoder.frame_queue
            )
            self._capture_thread.start()

            self._recording = True
            self._paused = False
            self._elapsed_secs = 0
            self._timer.start()
            self._update_button_states()
            self._tray.showMessage("ScRecorder", "Recording started", QSystemTrayIcon.Information, 2000)

        except Exception as exc:
            tb_text = traceback.format_exc()
            # Write to log file so it survives after the dialog is closed
            try:
                import datetime as _dt
                log_dir = os.path.join(os.environ.get("APPDATA", "."), "ScRecorder")
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, "error.log")
                with open(log_path, "a", encoding="utf-8") as _f:
                    _f.write(f"\n--- {_dt.datetime.now().isoformat()} ---\n")
                    _f.write(tb_text)
            except Exception:
                pass
            import sys as _sys
            if _sys.stderr is not None:
                traceback.print_exc()
            # Clean up any partially started components so state stays consistent
            for thread in (self._capture_thread, self._audio_thread):
                if thread is not None:
                    try:
                        thread.stop()
                        thread.wait(1000)
                    except Exception:
                        pass
            self._capture_thread = None
            self._audio_thread = None
            if self._encoder is not None:
                try:
                    self._encoder.stop()
                except Exception:
                    pass
                self._encoder = None
            self._recording = False
            self._update_button_states()
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "ScRecorder — Recording Failed",
                f"<b>Failed to start recording:</b><br><br>"
                f"<pre style='font-size:11px'>{tb_text}</pre>",
            )

    def _on_pause(self):
        if not self._recording:
            return
        self._paused = not self._paused
        if self._capture_thread:
            self._capture_thread.set_paused(self._paused)
        if self._audio_thread:
            self._audio_thread.set_paused(self._paused)
        self._update_button_states()

    def _on_stop(self):
        if not self._recording:
            return
        self._recording = False
        self._paused = False
        self._timer.stop()

        if self._capture_thread:
            self._capture_thread.stop()
            self._capture_thread.wait(3000)
            self._capture_thread = None

        wav_path = None
        if self._audio_thread:
            self._audio_thread.stop()
            self._audio_thread.wait(3000)
            wav_path = self._audio_thread.temp_wav_path
            self._audio_thread = None

        output_path = None
        if self._encoder:
            output_path = self._encoder.output_path
            self._encoder._wav_path = wav_path  # hand off wav path for muxing
            self._encoder.stop()
            self._encoder = None

        self._elapsed_secs = 0
        self.lbl_timer.setText("00:00:00")
        self._update_button_states()

        if output_path and os.path.exists(output_path):
            self._tray.showMessage(
                "ScRecorder",
                f"Saved: {os.path.basename(output_path)}",
                QSystemTrayIcon.Information,
                4000
            )
            os.startfile(os.path.dirname(output_path))

    def _tick(self):
        if not self._paused:
            self._elapsed_secs += 1
        h = self._elapsed_secs // 3600
        m = (self._elapsed_secs % 3600) // 60
        s = self._elapsed_secs % 60
        self.lbl_timer.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _update_button_states(self):
        self.btn_record.setEnabled(not self._recording)
        self.btn_pause.setEnabled(self._recording)
        self.btn_stop.setEnabled(self._recording)
        self.btn_pause.setText("▶" if (self._recording and self._paused) else "⏸")
        for btn in self._mode_buttons:
            btn.setEnabled(not self._recording)

    # ── output path ──────────────────────────────────────────────────────────

    def _make_output_path(self):
        out_dir = self.config.get("output_dir", os.path.join(os.path.expanduser("~"), "Videos", "ScRecorder"))
        os.makedirs(out_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(out_dir, f"Recording_{ts}.mp4")

    # ── drag to reposition ───────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── about ────────────────────────────────────────────────────────────────

    def _show_about(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About ScRecorder",
            f"<b>ScRecorder</b> v{self._app_version}<br><br>"
            "Screen recorder for Windows 7–11.<br>"
            "Built with Python, PyQt5, and ffmpeg.",
        )

    # ── quit ────────────────────────────────────────────────────────────────

    def _quit(self):
        if self._recording:
            self._on_stop()
        self._tray.hide()
        from PyQt5.QtWidgets import QApplication
        QApplication.quit()

    def paintEvent(self, a0):  # noqa: N802
        # Required for stylesheet background-color to render on a WA_TranslucentBackground widget
        from PyQt5.QtGui import QPainter, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(28, 28, 32, 235))
        p.setPen(QColor(255, 255, 255, 30))
        p.drawRoundedRect(self.rect(), 8, 8)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
