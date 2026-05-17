import time
import queue
import numpy as np
from PyQt5.QtCore import QThread


class ScreenCaptureThread(QThread):
    """Captures screen frames using mss and pushes numpy arrays to a queue."""

    def __init__(self, capture_rect: tuple, fps: int, frame_queue: queue.Queue):
        super().__init__()
        self._rect = capture_rect      # (x, y, w, h)
        self._fps = fps
        self._frame_queue = frame_queue
        self._running = False
        self._paused = False

    def set_paused(self, paused: bool):
        self._paused = paused

    def stop(self):
        self._running = False

    def run(self):
        import mss
        self._running = True
        interval = 1.0 / self._fps
        x, y, w, h = self._rect
        monitor = {"top": y, "left": x, "width": w, "height": h}

        with mss.mss() as sct:
            while self._running:
                t0 = time.perf_counter()

                if not self._paused:
                    try:
                        img = sct.grab(monitor)
                        # mss returns BGRA; convert to BGR for ffmpeg
                        frame = np.frombuffer(img.raw, dtype=np.uint8)
                        frame = frame.reshape((h, w, 4))
                        frame = frame[:, :, :3]  # drop alpha
                        # Put without blocking; drop frame if encoder is behind
                        try:
                            self._frame_queue.put_nowait(frame)
                        except queue.Full:
                            pass
                    except Exception:
                        pass

                elapsed = time.perf_counter() - t0
                sleep_for = interval - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)
