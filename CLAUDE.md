# CLAUDE.md — AI Agent Guide for ScRecorder

> Read this file first. It gives you everything needed to navigate, modify, and extend the codebase without asking questions.

---

## Quick Start

```bash
# Run from source
pip install -r requirements.txt
python main.py

# ffmpeg must be available — place in assets/ffmpeg.exe or add to PATH
```

- **Python version:** 3.13
- **Platform:** Windows 7–11 only (uses win32 APIs and WASAPI)
- **No test suite** — see [Testing Approach](#test-approach)

---

## Build System

```bash
build.bat                        # Build dist/ScRecorder-1.0.0.exe
build.bat --bump patch           # 1.0.0 -> 1.0.1, then build
build.bat --bump minor           # 1.0.1 -> 1.1.0, then build
build.bat --bump major           # 1.1.0 -> 2.0.0, then build
build.bat 2.0.0                  # Set explicit version, then build
build.bat --bump patch --no-build  # Bump version.py only, no exe
```

- Build script: [build.py](build.py) — generates `version_info.txt` + `ScRecorder.spec`, runs PyInstaller, cleans up
- Version source: [version.py](version.py) — only file to edit for a version change
- Output: `dist/ScRecorder-{version}.exe` — single exe with bundled ffmpeg and PE metadata

---

## File Map

| File | Responsibility |
|------|----------------|
| [main.py](main.py) | Entry point — config I/O, QApplication lifecycle, Toolbar instantiation |
| [version.py](version.py) | Single source of truth for semver and app metadata |
| [build.py](build.py) | PyInstaller spec generation, version bump logic, build orchestration |
| [ui/toolbar.py](ui/toolbar.py) | Core state machine — all UI controls, thread coordination, hotkeys, tray |
| [ui/region_selector.py](ui/region_selector.py) | Fullscreen drag-select overlay, returns (x, y, w, h) or None |
| [ui/window_picker.py](ui/window_picker.py) | Modal HWND picker dialog, returns hwnd or None |
| [recorder/encoder.py](recorder/encoder.py) | ffmpeg subprocess wrapper — two-pass H.264 encode + AAC mux |
| [recorder/screen_capture.py](recorder/screen_capture.py) | QThread — mss capture loop, pushes BGR24 frames to queue |
| [recorder/audio_capture.py](recorder/audio_capture.py) | QThread — PyAudio WASAPI loopback, writes temp WAV file |
| [utils/win_utils.py](utils/win_utils.py) | win32gui wrappers — window enumeration, monitor rect math |

---

## Threading Model

```
Main thread (Qt event loop)
  ├── ScreenCaptureThread (QThread)
  │     mss loop → frame_queue (maxsize=60, non-blocking put, silent drop)
  ├── AudioCaptureThread (QThread)
  │     PyAudio loop → temp WAV file + audio_queue (maxsize=200, unused by encoder)
  └── Encoder._feed_loop (daemon thread)
        reads frame_queue → writes to ffmpeg stdin pipe
        ffmpeg subprocess (separate process)
```

- **Join timeout:** 3 seconds hard limit on capture thread shutdown (`thread.wait(3000)`)
- **Pause:** boolean flag `_paused` checked each loop iteration — ffmpeg subprocess keeps running, WAV writes skipped
- **Queue drop:** both queues use `put_nowait()` — frames are silently dropped when full; user is not notified

---

## State Machine (toolbar.py)

```
IDLE ──[record clicked / Ctrl+Alt+R]──► RECORDING ──[pause / Ctrl+Alt+P]──► PAUSED
 ▲                                           │                                   │
 └──────────[stop clicked]──────────────────┘◄──────[resume / Ctrl+Alt+P]───────┘
```

| State | Capture threads | ffmpeg | Timer |
|-------|----------------|--------|-------|
| IDLE | not running | not running | reset |
| RECORDING | running, writing | running | ticking |
| PAUSED | running, skipping | running | frozen |

Transitions are triggered by: button clicks in `_build_ui()` or global hotkeys in `_setup_hotkeys()`.

---

## Config Schema

**Location:** `%APPDATA%\ScRecorder\config.json`  
**Loaded/saved in:** `main.py` — `load_config()` / `save_config()`

```json
{
  "output_dir": "~/Videos/ScRecorder",
  "fps": 30,
  "capture_mode": "fullscreen"
}
```

- `output_dir` — where MP4 files are written; created on startup if missing
- `fps` — capture and encode frame rate (passed to both ScreenCaptureThread and Encoder)
- `capture_mode` — `"fullscreen"` | `"region"` | `"window"` — persists last mode selection

---

## Output Files

| File | Location | Lifetime |
|------|----------|----------|
| Final MP4 | `~/Videos/ScRecorder/Recording_{YYYYMMDD_HHMMSS}.mp4` | Permanent |
| Video-only temp | `{output_path}.noaudio.mp4` | Deleted after mux |
| Audio WAV temp | `%TEMP%\*.wav` | Deleted after mux |

---

## ffmpeg Integration

Search order (encoder.py `_find_ffmpeg()`):

1. `sys._MEIPASS/assets/ffmpeg.exe` — frozen PyInstaller exe
2. `{project_root}/assets/ffmpeg.exe` — source dev mode
3. `shutil.which("ffmpeg")` — system PATH fallback (returns `"ffmpeg"` string, may fail silently)

ffmpeg is launched with `subprocess.CREATE_NO_WINDOW` on Windows (no console flash).  
Frames are fed via **stdin pipe** as raw BGR24 bytes.  
stderr is **not captured or surfaced** to the UI — ffmpeg errors are silent (KI-004).

---

## What NOT to Touch / Gotchas

1. **WAV handoff via private attribute** — `toolbar.py` sets `encoder._wav_path = audio_thread.temp_wav_path` after joining the audio thread. This is tight coupling by design for simplicity. If you refactor `AudioCaptureThread`, update this handoff. See [ADR-006](docs/decisions/ADR-006-wav-handoff-private-attribute.md).

2. **Audio device detection is language-dependent** — `audio_capture.py` finds the loopback device by matching device names against `["loopback", "stereo mix", "what u hear"]`. This fails on non-English Windows. Do not add new name strings without documenting the language they cover. See [ADR-005](docs/decisions/ADR-005-wasapi-loopback-device-detection.md).

3. **Even dimension enforcement** — H.264 requires even width and height. `toolbar.py` enforces this after resolving the capture rect (`w -= w % 2`). Any new capture path must do the same.

4. **Dead dependencies** — `opencv-python` and `Pillow` are in `requirements.txt` but are **never imported**. Do not add imports for them without removing the dead-dependency note in [PROJECT_BIBLE.md](PROJECT_BIBLE.md) §11 (KI-001).

5. **Frozen exe detection** — use the `sys.frozen` / `sys._MEIPASS` pattern already in `build.py` and `encoder.py`. Do not assume the script's `__file__` is reliable at runtime in a frozen exe.

6. **Queue maxsizes** — `frame_queue` is capped at 60 (2 seconds at 30fps), `audio_queue` at 200. Increasing these trades dropped frames for higher memory use under slow encoding. `audio_queue` is populated but never consumed by the encoder (WAV file is used instead) — this is dead code.

---

## How to Add a New Feature

1. **UI control** — add button/widget in `toolbar.py` `_build_ui()`; update `_update_button_states()` for all three states
2. **New capture source** — create a new `QThread` in `recorder/`; follow the pattern in `screen_capture.py` (run loop, `_paused` flag, `_running` flag, bounded queue)
3. **New config key** — add to `DEFAULT_CONFIG` dict in `main.py`; document in [PROJECT_BIBLE.md](PROJECT_BIBLE.md) §4
4. **New hotkey** — register in `toolbar.py` `_setup_hotkeys()` via `keyboard.add_hotkey()`
5. **Write a feature card** — create `docs/features/F-NNN-name.md` using the template in [PROJECT_BIBLE.md](PROJECT_BIBLE.md) §12

---

## Test Approach

**No automated test suite exists.** Manual testing procedure is in [docs/runbook/deployment-checklist.md](docs/runbook/deployment-checklist.md).

Recommended additions (not yet implemented):
- `pytest` + `pytest-qt` for toolbar state machine unit tests
- Mock `ScreenCaptureThread` and `AudioCaptureThread` to test recording lifecycle without real capture
- Do **not** add integration tests requiring a live display or audio device in CI environments

---

## Known Dead Code / Technical Debt

| Item | Location | Note |
|------|----------|------|
| `opencv-python` in requirements | requirements.txt | Never imported — KI-001 |
| `Pillow` in requirements | requirements.txt | Never imported — KI-001 |
| `audio_queue` population | audio_capture.py | Queue filled but encoder reads WAV file, not queue |
| No ffmpeg error surface | encoder.py | stderr not captured; recording silently fails on ffmpeg crash — KI-004 |
| No dropped-frame feedback | screen_capture.py | Silent `put_nowait()` drops — KI-005 |

---

## Dependencies Quick Reference

| Package | Purpose |
|---------|---------|
| `PyQt5` | UI framework — widgets, threading (QThread), system tray |
| `mss` | Fast cross-monitor screen capture, returns numpy arrays |
| `pyaudio` | WASAPI loopback audio capture |
| `pywin32` | HWND enumeration (`win32gui`), window geometry |
| `keyboard` | Global hotkeys without window focus requirement |
| `PyInstaller` | Single-exe build (`build.bat`) |
| `ffmpeg` | **External binary** — not a Python package; must be in `assets/` or PATH |
