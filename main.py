import sys
import os
import json
import traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from ui.toolbar import Toolbar
from version import __version__


def _excepthook(exc_type, exc_value, exc_tb):
    """Log unhandled exceptions without terminating the Qt process."""
    try:
        log_dir = os.path.join(os.environ.get("APPDATA", "."), "ScRecorder")
        os.makedirs(log_dir, exist_ok=True)
        import datetime
        with open(os.path.join(log_dir, "error.log"), "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.datetime.now().isoformat()} [unhandled] ---\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    except Exception:
        pass
    if sys.stderr is not None:
        traceback.print_exception(exc_type, exc_value, exc_tb)

sys.excepthook = _excepthook

CONFIG_PATH = os.path.join(os.environ.get("APPDATA", "."), "ScRecorder", "config.json")

DEFAULT_CONFIG = {
    "output_dir": os.path.join(os.path.expanduser("~"), "Videos", "ScRecorder"),
    "fps": 30,
    "capture_mode": "fullscreen",
    "hotkey_record": "ctrl+alt+r",
    "hotkey_pause": "ctrl+alt+p",
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def ensure_output_dir(config):
    os.makedirs(config["output_dir"], exist_ok=True)


if __name__ == "__main__":
    # Enable high-DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    # Show tooltips quickly (400 ms delay, 10 s visible duration)
    app.setStyleSheet("QToolTip { }")  # force Qt to apply QToolTip style from widgets
    from PyQt5.QtWidgets import QToolTip
    QToolTip.setFont(app.font())

    config = load_config()
    ensure_output_dir(config)

    toolbar = Toolbar(config, save_config, __version__)
    toolbar.show()

    sys.exit(app.exec_())
