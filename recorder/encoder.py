import os
import sys
import queue
import subprocess
import threading
import shutil


def _find_ffmpeg():
    """Locate ffmpeg: bundled next to exe, assets folder, or system PATH."""
    if getattr(sys, "frozen", False):
        # --onefile: PyInstaller extracts bundle to sys._MEIPASS at runtime
        # --onedir: files sit next to sys.executable
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    candidates = [
        os.path.join(base, "assets", "ffmpeg.exe"),
        os.path.join(base, "ffmpeg.exe"),
        "ffmpeg",   # system PATH
    ]
    for c in candidates:
        if shutil.which(c) or os.path.isfile(c):
            return c
    return "ffmpeg"


class Encoder:
    """
    Drives an ffmpeg subprocess that receives raw BGR24 video frames via stdin
    and produces an H.264 MP4 file. Audio is muxed in a second pass after stop().
    """

    def __init__(self, output_path: str, width: int, height: int, fps: int):
        self.output_path = output_path
        self._width = width
        self._height = height
        self._fps = fps
        self._ffmpeg = _find_ffmpeg()

        self.frame_queue: queue.Queue = queue.Queue(maxsize=60)
        self.audio_queue: queue.Queue = queue.Queue(maxsize=200)

        self._proc = None
        self._feed_thread = None
        self._running = False

        # Temp video-only file (before audio mux)
        self._video_only_path = output_path + ".noaudio.mp4"
        self._wav_path = None   # set by toolbar after audio thread finishes

    def start(self):
        cmd = [
            self._ffmpeg, "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self._width}x{self._height}",
            "-r", str(self._fps),
            "-i", "pipe:0",          # stdin
            "-vcodec", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            self._video_only_path,
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        self._running = True
        self._feed_thread = threading.Thread(target=self._feed_loop, daemon=True)
        self._feed_thread.start()

    def _feed_loop(self):
        while self._running:
            try:
                frame = self.frame_queue.get(timeout=0.5)
                if self._proc and self._proc.stdin:
                    self._proc.stdin.write(frame.tobytes())
            except queue.Empty:
                pass
            except Exception:
                break

    def stop(self):
        self._running = False
        if self._feed_thread:
            self._feed_thread.join(timeout=3)

        if self._proc:
            try:
                self._proc.stdin.close()
            except Exception:
                pass
            self._proc.wait(timeout=10)
            self._proc = None

        # wav_path is supplied by toolbar after audio thread stops
        wav_path = self._wav_path
        if wav_path and os.path.exists(wav_path) and os.path.getsize(wav_path) > 44:
            self._mux_audio(wav_path)
            try:
                os.remove(wav_path)
            except Exception:
                pass
        else:
            # No audio — just rename video-only to final
            if os.path.exists(self._video_only_path):
                os.replace(self._video_only_path, self.output_path)

    def _mux_audio(self, wav_path: str):
        cmd = [
            self._ffmpeg, "-y",
            "-i", self._video_only_path,
            "-i", wav_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            self.output_path,
        ]
        try:
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                timeout=60,
            )
        except Exception:
            pass
        finally:
            try:
                os.remove(self._video_only_path)
            except Exception:
                pass

