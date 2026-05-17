---
id: F-005
name: Pause / Resume
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
  - recorder/screen_capture.py
  - recorder/audio_capture.py
---

### Purpose
Allow the user to temporarily pause a recording without stopping or restarting the ffmpeg session, preserving the recording session and timer.

### User-Facing Behaviour
- The ⏸ Pause button is enabled only during an active recording
- Clicking Pause freezes the timer and stops new video frames and audio from being written
- The button icon changes to ▶ Resume while paused
- Clicking Resume resumes writing frames and audio; timer continues from where it left off
- Hotkey `Ctrl+Alt+P` toggles between Pause and Resume from any window
- Elapsed time shown in the timer reflects only active (non-paused) recording duration

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_on_pause()` — toggles `_paused` flag and propagates to threads; updates button icon |
| `recorder/screen_capture.py` | Checks `_paused` each loop iteration; skips `put_nowait()` when paused |
| `recorder/audio_capture.py` | Checks `_paused`; skips `wav.writeframes()` when paused but keeps PyAudio stream open |

#### Data Flow
1. User clicks ⏸ or presses `Ctrl+Alt+P` → `toolbar._on_pause()` called
2. `_paused` bool toggled on toolbar
3. `screen_capture_thread.set_paused(True)` called — thread sets its own `_paused = True`
4. `audio_capture_thread.set_paused(True)` called — thread sets its own `_paused = True`
5. `_timer.stop()` — Qt timer stops ticking (elapsed time frozen)
6. **While paused:** mss loop still runs but skips `frame_queue.put_nowait()` — no new frames queued
7. **While paused:** PyAudio stream still reads chunks but skips `wav.writeframes()` — audio device kept warm
8. **While paused:** ffmpeg subprocess receives no new data via stdin — creates a silent gap in the video
9. On Resume: flags set back to False, `_timer.start()` resumes

#### Key Classes / Methods
- `toolbar._on_pause()` — toggles `_paused`, calls `set_paused()` on both threads, updates button icon
- `ScreenCaptureThread.set_paused(paused: bool)` — sets `_paused` flag
- `AudioCaptureThread.set_paused(paused: bool)` — sets `_paused` flag

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| — | — | No configuration for pause behaviour |

### Dependencies
- None beyond the capture threads and Qt timer already required by recording

### Known Issues / Limitations
- ffmpeg stdin pipe receives no frames during pause, creating a variable-duration gap in the encoded video — the output duration may be shorter than wall-clock time
- The WAV file similarly has silence gaps; the `-shortest` ffmpeg flag on mux handles duration differences
- Pause state is not persisted — if the app crashes while paused, the partial recording is lost

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
