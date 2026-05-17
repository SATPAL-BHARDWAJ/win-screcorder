import queue
import wave
import tempfile
import os
from PyQt5.QtCore import QThread

SAMPLE_RATE = 44100
CHANNELS = 2
SAMPLE_WIDTH = 2   # 16-bit PCM
CHUNK = 1024


class AudioCaptureThread(QThread):
    """Captures system audio via WASAPI loopback and writes a temp WAV file."""

    def __init__(self, audio_queue: queue.Queue):
        super().__init__()
        self._audio_queue = audio_queue
        self._running = False
        self._paused = False
        self.temp_wav_path = None

    def set_paused(self, paused: bool):
        self._paused = paused

    def stop(self):
        self._running = False

    def run(self):
        import pyaudio
        self._running = True

        pa = pyaudio.PyAudio()
        device_index = self._find_loopback_device(pa)

        # Create a temp file for raw audio
        fd, self.temp_wav_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)

        wav_file = wave.open(self.temp_wav_path, "wb")
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(SAMPLE_RATE)

        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK,
            )
            while self._running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    if not self._paused:
                        wav_file.writeframes(data)
                        self._audio_queue.put_nowait(data)
                except Exception:
                    pass
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        finally:
            wav_file.close()
            pa.terminate()

    def _find_loopback_device(self, pa):
        """Find a WASAPI loopback device index, fall back to default input."""
        try:
            import pyaudio
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                name = info.get("name", "").lower()
                # WASAPI loopback devices typically contain "loopback" or "stereo mix"
                if "loopback" in name or "stereo mix" in name or "what u hear" in name:
                    if info.get("maxInputChannels", 0) > 0:
                        return i
        except Exception:
            pass
        # Fall back to default input device
        return None
