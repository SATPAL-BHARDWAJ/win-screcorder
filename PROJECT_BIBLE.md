# PROJECT_BIBLE.md — ScRecorder Technical Reference

> The North Star. Read this before making architectural changes. Updated only when the architecture changes — not for feature additions.

---

## 1. Project Identity

| Property | Value |
|----------|-------|
| Name | ScRecorder |
| Version policy | Semantic versioning: `MAJOR.MINOR.PATCH` |
| Platform | Windows 7, 10, 11 |
| Language | Python 3.13 |
| UI framework | PyQt5 |
| Encoding | ffmpeg (external binary) |
| Distribution | Single PyInstaller exe |
| Config storage | `%APPDATA%\ScRecorder\config.json` |
| Output directory | `~/Videos/ScRecorder/` |

### Repository Layout

```
screcorder/
├── CLAUDE.md               AI agent orientation guide
├── PROJECT_BIBLE.md        This file
├── CHANGELOG.md            Version history
├── README.md               Quick start
├── main.py                 Entry point
├── version.py              Semver source of truth
├── build.py                Build orchestrator
├── build.bat               Build wrapper
├── requirements.txt        Python dependencies
├── assets/
│   ├── ffmpeg.exe          Bundled encoder binary
│   └── icons/              App icons (app.ico)
├── recorder/
│   ├── encoder.py          ffmpeg subprocess wrapper
│   ├── screen_capture.py   mss capture thread
│   └── audio_capture.py    PyAudio WASAPI thread
├── ui/
│   ├── toolbar.py          Main UI + state machine
│   ├── region_selector.py  Drag-select overlay
│   └── window_picker.py    HWND picker dialog
├── utils/
│   └── win_utils.py        win32gui wrappers
└── docs/
    ├── features/           F-NNN feature cards
    ├── decisions/          ADR-NNN architecture records
    └── runbook/            Setup and deployment guides
```

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  main.py                                                        │
│  load_config() ──► Toolbar(config, save_config, version)        │
│  QApplication.exec_()                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │ owns
          ┌──────────────────▼──────────────────────────┐
          │  ui/toolbar.py  (State Machine)              │
          │  IDLE ◄──► RECORDING ◄──► PAUSED             │
          │  - button controls     - hotkeys             │
          │  - system tray         - timer               │
          └────┬─────────────┬──────────────┬────────────┘
               │ spawns      │ spawns       │ spawns
     ┌─────────▼──┐   ┌──────▼──────┐  ┌───▼───────────┐
     │ScreenCapture│   │AudioCapture │  │   Encoder     │
     │  QThread    │   │  QThread    │  │  (+ ffmpeg)   │
     │  mss loop   │   │ PyAudio loop│  │  subprocess   │
     │  BGR24      │   │  WAV file   │  │               │
     └──────┬──────┘   └──────┬──────┘  └───────────────┘
            │ queue(60)       │ wav path        ▲
            └─────────────────┴─────────────────┘
                  frame_queue fed to ffmpeg stdin
```

**Thread ownership:** toolbar.py spawns and joins all threads. It is the sole owner of recording state.

---

## 3. Module Reference

### 3.1 main.py

**Responsibilities:** QApplication lifecycle, config load/save, Toolbar instantiation.

**Key functions:**

| Function | Signature | Purpose |
|----------|-----------|---------|
| `load_config` | `() -> dict` | Read `config.json`, merge with `DEFAULT_CONFIG`, return result |
| `save_config` | `(config: dict) -> None` | Write config dict to `config.json` |
| `ensure_output_dir` | `(config: dict) -> None` | Create output directory if missing |

**Config file path:** `os.path.join(os.environ["APPDATA"], "ScRecorder", "config.json")`

**Notes:**
- `app.setQuitOnLastWindowClosed(False)` — app keeps running when toolbar is hidden to tray
- `QToolTip.setFont()` called once at startup to apply custom tooltip font

---

### 3.2 ui/toolbar.py

**Responsibilities:** All UI controls, recording state machine, thread lifecycle, hotkeys, system tray.

**Class:** `Toolbar(QWidget)`

**Constructor:** `__init__(config: dict, save_config_fn, app_version: str = "0.0.0")`

**State machine:**

| State | `_recording` | `_paused` | Threads |
|-------|-------------|-----------|---------|
| IDLE | False | False | None |
| RECORDING | True | False | All running |
| PAUSED | True | True | Running, skipping writes |

**Key methods:**

| Method | Purpose |
|--------|---------|
| `_build_ui()` | Create all buttons, timer label, mode buttons, separators |
| `_btn(text, obj_name, tooltip, checkable)` | Button factory with tooltip and cursor |
| `_resolve_capture_rect()` | Returns `(x, y, w, h)` or `None` based on current mode |
| `_on_record()` | IDLE → RECORDING: spawn threads, start timer |
| `_on_pause()` | RECORDING ↔ PAUSED: toggle pause flag on both threads |
| `_on_stop()` | RECORDING → IDLE: join threads, trigger mux, open output folder |
| `_update_button_states()` | Enable/disable buttons based on state |
| `_setup_tray()` | Create `QSystemTrayIcon` with context menu |
| `_setup_hotkeys()` | Register `keyboard.add_hotkey()` bindings |
| `paintEvent(a0)` | Custom background paint (required for translucent window) |

**Window flags:** `Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint`

---

### 3.3 ui/region_selector.py

**Responsibilities:** Fullscreen transparent overlay for drag-to-select a screen region.

**Class:** `RegionSelector(QWidget)`

**Public method:** `select() -> tuple | None`
- Shows fullscreen overlay
- Runs a local `QEventLoop` (blocking) until user releases mouse or presses Escape
- Returns `(x, y, w, h)` in global screen coordinates, or `None` on cancel

**Mouse event flow:** `mousePressEvent` → sets `_origin` → `mouseMoveEvent` repaints → `mouseReleaseEvent` computes rect, calls `_loop.quit()`

**Contract:** The returned rect is always in even-pixel dimensions (enforced by caller in toolbar.py).

---

### 3.4 ui/window_picker.py

**Responsibilities:** Modal dialog listing all visible top-level windows for HWND selection.

**Class:** `WindowPicker(QDialog)`

**Public method:** `pick() -> int | None`
- Shows modal dialog via `exec_()`
- Returns HWND integer if accepted, `None` if cancelled

**Window data source:** `utils.win_utils.enumerate_windows()` — called once when dialog opens. List is **not** refreshed while the dialog is open.

---

### 3.5 recorder/encoder.py

**Responsibilities:** ffmpeg subprocess management, frame feeding loop, two-pass encode + audio mux.

**Class:** `Encoder`

**Constructor:** `__init__(output_path: str, width: int, height: int, fps: int)`

**Two-pass definition:**
1. **Pass 1 (video):** Raw BGR24 frames piped to ffmpeg → `{output}.noaudio.mp4` (H.264)
2. **Pass 2 (mux):** `{output}.noaudio.mp4` + `{wav_path}` → final `{output}.mp4` (H.264 + AAC, video stream copied)

**ffmpeg video command:**
```
ffmpeg -y -f rawvideo -vcodec rawvideo -pix_fmt bgr24
  -s {W}x{H} -r {fps} -i pipe:0
  -vcodec libx264 -preset ultrafast -crf 23 -pix_fmt yuv420p
  -movflags +faststart {output}.noaudio.mp4
```

**ffmpeg mux command:**
```
ffmpeg -y -i {video}.noaudio.mp4 -i {wav}
  -c:v copy -c:a aac -b:a 192k -shortest
  -movflags +faststart {output}.mp4
```

**WAV handoff:** Set `encoder._wav_path` after `audio_thread.join()` — see [ADR-006](docs/decisions/ADR-006-wav-handoff-private-attribute.md).

**Key methods:**

| Method | Purpose |
|--------|---------|
| `start()` | Spawn ffmpeg subprocess, start `_feed_loop` daemon thread |
| `stop()` | Signal feed loop to stop, wait for ffmpeg, trigger mux if WAV exists |
| `_feed_loop()` | Daemon thread: reads `frame_queue`, writes bytes to ffmpeg stdin |
| `_mux_audio(wav_path)` | Run ffmpeg mux command with 60s timeout |
| `_find_ffmpeg()` | Locate ffmpeg binary (frozen → assets → PATH) |

---

### 3.6 recorder/screen_capture.py

**Responsibilities:** Screen capture at target FPS using mss, feeding BGR24 frames to queue.

**Class:** `ScreenCaptureThread(QThread)`

**Constructor:** `__init__(capture_rect: tuple, fps: int, frame_queue: queue.Queue)`

**Frame format:** numpy array, shape `(height, width, 3)`, dtype `uint8`, **BGR24** (BGRA from mss with alpha dropped via `[:, :, :3]`)

**Run loop:** Captures at `1/fps` interval using adaptive sleep (`interval - capture_time`). Uses `put_nowait()` — drops frame silently if queue full.

**Control:** `_running` (threading.Event or bool) and `_paused` bool, both checked each iteration.

---

### 3.7 recorder/audio_capture.py

**Responsibilities:** PyAudio WASAPI loopback capture, writing PCM to temp WAV file.

**Class:** `AudioCaptureThread(QThread)`

**Audio format:**

| Property | Value |
|----------|-------|
| Sample rate | 44,100 Hz |
| Channels | 2 (stereo) |
| Sample width | 2 bytes (16-bit) |
| Chunk size | 1,024 frames |

**Device selection:** `_find_loopback_device(pa)` — iterates all PyAudio devices, matches name (case-insensitive) against `["loopback", "stereo mix", "what u hear"]`. Falls back to `None` (system default input) if not found. See [ADR-005](docs/decisions/ADR-005-wasapi-loopback-device-detection.md).

**WAV output:** Temp file via `tempfile.mkstemp(suffix=".wav")`. Path stored in `self.temp_wav_path`. Cleaned up by `encoder.py` after mux.

**Pause behaviour:** Thread continues reading from audio device but skips `wav.writeframes()` — keeps device stream alive to avoid reconnect latency.

---

### 3.8 utils/win_utils.py

**Responsibilities:** Windows-specific utilities for window enumeration and monitor geometry.

**Functions:**

| Function | Returns | Notes |
|----------|---------|-------|
| `enumerate_windows()` | `list[tuple[int, str]]` | `(hwnd, title)` for all visible, titled windows |
| `get_window_rect(hwnd)` | `tuple | None` | `(x, y, w, h)` from `win32gui.GetWindowRect`; None if minimized/invalid |
| `get_all_monitors_rect()` | `tuple` | `(x, y, w, h)` bounding box of all monitors via `QDesktopWidget` |
| `get_primary_monitor_rect()` | `tuple` | Primary monitor rect only (unused in current codebase) |

**Dependency:** `pywin32` (`win32gui`, `win32con`) — degrades gracefully if not installed (returns empty list from `enumerate_windows()`).

---

### 3.9 version.py

**Responsibilities:** Single source of truth for application version and metadata.

```python
__version__ = "1.0.0"           # Edit only this line manually
VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH = 1, 0, 0
VERSION_TUPLE = (1, 0, 0)       # Used by build.py for PE metadata
APP_NAME = "ScRecorder"
COMPANY_NAME = "ScRecorder"
COPYRIGHT = "Copyright (C) 2025 ScRecorder"
```

Modified by `build.py` `write_version()` via regex — never import this in `build.py`.

---

### 3.10 build.py

**Responsibilities:** Version bump, `version_info.txt` generation, PyInstaller spec generation, build orchestration.

**Key functions:**

| Function | Purpose |
|----------|---------|
| `read_version()` | Regex-read `__version__` from `version.py` without importing |
| `write_version(v)` | Regex-rewrite `__version__`, major, minor, patch, tuple in `version.py` |
| `bump_version(current, part)` | Increment major/minor/patch, reset lower components |
| `make_version_info(v)` | Generate `VSVersionInfo` block for Windows PE metadata |
| `make_spec(v)` | Generate PyInstaller `.spec` file string |
| `run_build(v)` | Write temp files, invoke PyInstaller, clean up, report output |

---

## 4. Configuration Schema

**File:** `%APPDATA%\ScRecorder\config.json`

| Key | Type | Default | Consumed by |
|-----|------|---------|-------------|
| `output_dir` | string | `~/Videos/ScRecorder` | `main.py`, `toolbar.py` `_make_output_path()` |
| `fps` | int | `30` | `toolbar.py` → `ScreenCaptureThread`, `Encoder` |
| `capture_mode` | string | `"fullscreen"` | `toolbar.py` `_capture_mode`, mode buttons |

On load, missing keys are filled from `DEFAULT_CONFIG`. Corrupt JSON resets silently to defaults via try/except in `load_config()`.

---

## 5. Data Flow: Recording Session

| Step | Action | Thread |
|------|--------|--------|
| 1 | User clicks Record or presses Ctrl+Alt+R | Main (Qt event) |
| 2 | `_on_record()` calls `_resolve_capture_rect()` | Main |
| 3 | For region mode: shows `RegionSelector` overlay, blocks on local QEventLoop | Main |
| 4 | For window mode: shows `WindowPicker` dialog, converts HWND → rect | Main |
| 5 | Even-dimension enforcement: `w -= w % 2`, `h -= h % 2` | Main |
| 6 | `Encoder(output_path, w, h, fps).start()` — spawns ffmpeg subprocess | Main |
| 7 | `AudioCaptureThread.start()` — opens PyAudio stream, begins WAV write | AudioCapture |
| 8 | `ScreenCaptureThread.start()` — begins mss capture loop | ScreenCapture |
| 9 | `_timer.start()` — 1-second tick updates HH:MM:SS label | Main |
| 10 | **RECORDING state:** frames flow queue → ffmpeg stdin; audio written to WAV | All threads |
| 11 | User pauses: `_paused = True` set on both threads | Main |
| 12 | Capture threads skip writes; ffmpeg stdin receives no new data (silent gap) | ScreenCapture, AudioCapture |
| 13 | User stops: `_on_stop()` called | Main |
| 14 | `ScreenCaptureThread.stop()` + `wait(3000)` | Main |
| 15 | `AudioCaptureThread.stop()` + `wait(3000)`; retrieve `temp_wav_path` | Main |
| 16 | `encoder._wav_path = temp_wav_path` | Main |
| 17 | `encoder.stop()` — signals feed loop, closes ffmpeg stdin, waits for ffmpeg | Main |
| 18 | If WAV > 44 bytes: `_mux_audio()` — ffmpeg mux pass (60s timeout) | Encoder daemon |
| 19 | Temp files cleaned up; final MP4 confirmed | Encoder daemon |
| 20 | `os.startfile(output_dir)` opens Explorer at output folder | Main |

---

## 6. Output File Naming

**Pattern:** `Recording_{YYYYMMDD_HHMMSS}.mp4`  
**Example:** `Recording_20260517_143022.mp4`  
**Directory:** `config["output_dir"]` (default: `~/Videos/ScRecorder/`)

---

## 7. Encoding Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Video codec | `libx264` | Widely compatible H.264 |
| Preset | `ultrafast` | Minimise CPU load during live capture |
| CRF | `23` | Default quality; lower = larger file + better quality |
| Pixel format | `yuv420p` | Maximum compatibility (required for web/players) |
| Audio codec | `aac` | Native MP4 audio |
| Audio bitrate | `192k` | CD-quality stereo |
| Container | MP4 | `movflags +faststart` for progressive playback |

**Even-dimension requirement:** H.264 requires width and height to be divisible by 2. Enforcement point: `toolbar.py` `_on_record()` after `_resolve_capture_rect()`.

---

## 8. ffmpeg Integration

**Search order** (`encoder.py` `_find_ffmpeg()`):

1. `os.path.join(sys._MEIPASS, "assets", "ffmpeg.exe")` — frozen exe
2. `os.path.join(project_root, "assets", "ffmpeg.exe")` — source dev
3. `shutil.which("ffmpeg")` or `"ffmpeg"` — system PATH

**Subprocess flags:** `subprocess.CREATE_NO_WINDOW` on Windows (prevents console window flash).

**Two-pass definition:** Pass 1 encodes video-only to `.noaudio.mp4`; Pass 2 muxes audio (no video re-encode, `-c:v copy`). This is not traditional two-pass CBR encoding.

**Error handling:** ffmpeg stderr is not captured or displayed. Failures are silent to the user (KI-004).

---

## 9. Global Hotkeys

| Hotkey | Action | Method in toolbar.py |
|--------|--------|----------------------|
| `Ctrl+Alt+R` | Start / Stop recording | `_on_record()` |
| `Ctrl+Alt+P` | Pause / Resume | `_on_pause()` |

Registered via `keyboard.add_hotkey()` with `suppress=False` (hotkey events still propagate). Silent failure if keyboard library cannot register (some environments require admin). See [ADR-007](docs/decisions/ADR-007-keyboard-library-hotkeys.md).

---

## 10. System Tray

| Action | Behaviour |
|--------|-----------|
| Click toolbar close (✕) | `toolbar.hide()` — window hidden, tray icon remains |
| Double-click tray icon | `toolbar.show()` + `raise_()` |
| Tray → Show toolbar | `toolbar.show()` |
| Tray → Start recording | `_on_record()` |
| Tray → Stop recording | `_on_stop()` |
| Tray → About | `_show_about()` — version dialog |
| Tray → Exit | `_quit()` — stops recording if active, hides tray, `QApplication.quit()` |

Tray tooltip: `"ScRecorder {version}"` — set in `_setup_tray()`.

---

## 11. Known Issues Registry

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| KI-001 | `opencv-python` and `Pillow` in `requirements.txt` but never imported | Low | Open |
| KI-002 | WASAPI loopback device detection by name — fails on non-English Windows | Medium | Open |
| KI-003 | WAV path handed off via private attribute `encoder._wav_path` | Low | Open (by design) |
| KI-004 | ffmpeg errors not surfaced to UI — recording fails silently | High | Open |
| KI-005 | Dropped frames (queue overflow) not reported to user | Low | Open |

---

## 12. Feature Card Template

Copy this template when creating a new `docs/features/F-NNN-name.md`:

```markdown
---
id: F-NNN
name: <Feature Name>
status: stable | experimental | deprecated
added_version: vX.Y.Z
last_modified: YYYY-MM-DD
files:
  - relative/path/to/file.py
---

### Purpose
One sentence describing what this feature does and why it exists.

### User-Facing Behaviour
- Bullet list of observable behaviours from the user's perspective

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `path/to/file.py` | What this file contributes |

#### Data Flow
1. Step one
2. Step two
3. ...

#### Key Classes / Methods
- `ClassName.method_name(args)` — what it does

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| `config_key` | `value` | What changing this does |

### Dependencies
- List external packages or binaries required

### Known Issues / Limitations
- Description — see KI-NNN in [PROJECT_BIBLE.md](../../PROJECT_BIBLE.md) §11

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| YYYY-MM-DD | vX.Y.Z | Initial implementation | — |
```

---

## 13. ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](docs/decisions/ADR-001-config-storage-appdata-json.md) | Store configuration in %APPDATA% as JSON | Accepted | 2026-05-17 |
| [ADR-002](docs/decisions/ADR-002-ffmpeg-subprocess-encoding.md) | Use ffmpeg subprocess for encoding | Accepted | 2026-05-17 |
| [ADR-003](docs/decisions/ADR-003-mss-screen-capture.md) | Use mss for screen capture | Accepted | 2026-05-17 |
| [ADR-004](docs/decisions/ADR-004-qthread-capture-architecture.md) | QThread + bounded queues with silent drops | Accepted | 2026-05-17 |
| [ADR-005](docs/decisions/ADR-005-wasapi-loopback-device-detection.md) | WASAPI loopback device detection by name | Accepted | 2026-05-17 |
| [ADR-006](docs/decisions/ADR-006-wav-handoff-private-attribute.md) | WAV handoff via private attribute | Accepted | 2026-05-17 |
| [ADR-007](docs/decisions/ADR-007-keyboard-library-hotkeys.md) | Use `keyboard` library for global hotkeys | Accepted | 2026-05-17 |
| [ADR-008](docs/decisions/ADR-008-pyinstaller-single-exe.md) | Distribute as single PyInstaller exe | Accepted | 2026-05-17 |
| [ADR-009](docs/decisions/ADR-009-pyqt5-ui-framework.md) | Use PyQt5 as UI framework | Accepted | 2026-05-17 |
