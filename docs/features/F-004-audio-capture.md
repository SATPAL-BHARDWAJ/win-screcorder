---
id: F-004
name: Audio Capture (WASAPI Loopback)
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - recorder/audio_capture.py
  - recorder/encoder.py
  - ui/toolbar.py
---

### Purpose
Capture system audio output (what the user hears) and mux it into the final MP4 recording alongside the video.

### User-Facing Behaviour
- Audio is captured automatically whenever a recording is started
- No configuration required — the app auto-detects the WASAPI loopback device
- If no loopback device is found, the system default input (typically the microphone) is used as fallback
- Audio is not heard in real-time (no monitoring)
- On stop, the audio WAV is muxed into the final MP4; audio track is always AAC stereo 44.1 kHz

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `recorder/audio_capture.py` | `AudioCaptureThread` — PyAudio WASAPI stream → temp WAV file |
| `recorder/encoder.py` | `_mux_audio()` — ffmpeg command to combine video + WAV into final MP4 |
| `ui/toolbar.py` | Spawns/stops `AudioCaptureThread`; hands WAV path to encoder after stop |

#### Data Flow
1. `toolbar._on_record()` creates and starts `AudioCaptureThread(audio_queue)`
2. `AudioCaptureThread.run()` creates a temp WAV file via `tempfile.mkstemp(suffix=".wav")`
3. `_find_loopback_device(pa)` scans all PyAudio devices for name containing `"loopback"`, `"stereo mix"`, or `"what u hear"` (case-insensitive); returns device index or `None`
4. PyAudio stream opened: 44100 Hz, 16-bit, stereo, input=True, `exception_on_overflow=False`
5. Each 1024-frame chunk is written to the WAV file (skipped if `_paused`)
6. On `stop()`: stream closed, WAV file closed; `self.temp_wav_path` set
7. `toolbar._on_stop()` joins audio thread, reads `audio_thread.temp_wav_path`
8. Sets `encoder._wav_path = temp_wav_path` (see [ADR-006](../decisions/ADR-006-wav-handoff-private-attribute.md))
9. `encoder.stop()` checks if WAV exists and is `> 44 bytes`; if so calls `_mux_audio(wav_path)`
10. ffmpeg mux: `-c:v copy` (no video re-encode) + `-c:a aac -b:a 192k -shortest`

#### Key Classes / Methods
- `AudioCaptureThread.run()` — opens PyAudio, writes WAV, honours `_paused` flag
- `AudioCaptureThread._find_loopback_device(pa) -> int | None` — name-based loopback detection
- `Encoder._mux_audio(wav_path: str)` — runs ffmpeg mux with 60s timeout, cleans up temp files

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| — | — | No config key for audio; always enabled |

### Dependencies
- `pyaudio` — PyAudio stream (WASAPI on Windows)
- `ffmpeg` (external binary) — AAC encoding and mux

### Known Issues / Limitations
- Loopback device detection is name-based — fails silently on non-English Windows where device names differ (KI-002). See [ADR-005](../decisions/ADR-005-wasapi-loopback-device-detection.md)
- WAV path is handed off via private attribute `encoder._wav_path` — tight coupling (KI-003). See [ADR-006](../decisions/ADR-006-wav-handoff-private-attribute.md)
- `audio_queue` is populated but never consumed by the encoder — dead code; WAV file is the actual audio path
- WAV size check (`> 44 bytes`) is a byte count heuristic, not a validity check — a corrupt WAV header will not be detected
- If PyAudio cannot open any device, the thread exits silently; recording continues without audio

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
