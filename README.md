# ScRecorder

A lightweight Windows screen recorder with audio capture, three capture modes, and a floating toolbar.  
Outputs H.264 + AAC MP4. Compatible with Windows 7–11.

---

## Features

- **Fullscreen** — record all monitors as one combined region
- **Region** — drag-select any rectangular area of the screen
- **Window** — pick any visible application window to record
- **Audio** — WASAPI system audio loopback (records what you hear)
- **Pause / Resume** — freeze the recording without stopping the session
- **Global hotkeys** — control recording from any foreground window
- **System tray** — minimize to tray, control from the tray icon
- **Timer** — live HH:MM:SS elapsed counter on the toolbar
- **Floating toolbar** — frameless, semi-transparent, drag anywhere on screen
- **Tooltips** — hover any button for a description
- **Config persistence** — settings saved between sessions
- **Versioned exe** — single distributable exe with embedded Windows file metadata

---

## Quick Start

### Requirements

- Windows 7, 10, or 11
- Python 3.13 (source only)
- [ffmpeg](https://ffmpeg.org/download.html) — place `ffmpeg.exe` in `assets/` or add to system PATH

### Run from Source

```bash
pip install -r requirements.txt
python main.py
```

### Download Release

Download `ScRecorder-{version}.exe` from the [Releases](https://github.com/user/screcorder/releases) page.  
Double-click to run — no installation required. ffmpeg is bundled.

---

## Usage

### Capture Modes

| Button | Mode | Behaviour |
|--------|------|-----------|
| 🖥 | Fullscreen | Captures all monitors |
| ▣ | Region | Shows drag-select overlay |
| ⬜ | Window | Opens window picker dialog |

Select a mode **before** clicking Record. Mode is saved between sessions.

### Controls

| Button | Action |
|--------|--------|
| ● | Start recording |
| ⏸ | Pause / Resume |
| ■ | Stop and save |
| ✕ | Minimize to tray |

### Hotkeys

| Hotkey | Action |
|--------|--------|
| `Ctrl+Alt+R` | Start / Stop recording |
| `Ctrl+Alt+P` | Pause / Resume |

Hotkeys work from any window — the toolbar does not need focus.

### Output Files

- **Location:** `~/Videos/ScRecorder/`
- **Filename:** `Recording_{YYYYMMDD_HHMMSS}.mp4`
- **Format:** H.264 video + AAC audio, MP4 container

After stopping, Windows Explorer opens automatically at the output folder.

---

## Configuration

Settings are stored at `%APPDATA%\ScRecorder\config.json` and created on first run.

| Key | Default | Description |
|-----|---------|-------------|
| `output_dir` | `~/Videos/ScRecorder` | Where recordings are saved |
| `fps` | `30` | Capture and encode frame rate |
| `capture_mode` | `"fullscreen"` | Last used capture mode |

Delete `config.json` to reset all settings to defaults.

---

## Building a Release

```bash
build.bat                   # Build with current version
build.bat --bump patch       # Increment patch version and build
build.bat --bump minor       # Increment minor version and build
build.bat --bump major       # Increment major version and build
build.bat --bump patch --no-build  # Bump version only, no exe
```

Output: `dist/ScRecorder-{version}.exe`

Full release procedure: [docs/runbook/deployment-checklist.md](docs/runbook/deployment-checklist.md)

---

## Known Limitations

- **Audio on non-English Windows (KI-002):** WASAPI loopback device is detected by name. If your system's loopback device has a non-standard name, the app falls back to the default microphone. See [ADR-005](docs/decisions/ADR-005-wasapi-loopback-device-detection.md).
- **Silent encoder errors (KI-004):** If ffmpeg crashes during recording, there is no error message. If a recording produces no output file, verify that `assets/ffmpeg.exe` exists and is not corrupted.
- **GPU-exclusive fullscreen apps:** Screen capture uses mss which cannot capture DirectX exclusive fullscreen applications (e.g., some games). Use windowed or borderless windowed mode in the target application.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | AI agent and developer orientation |
| [PROJECT_BIBLE.md](PROJECT_BIBLE.md) | Architecture reference, module contracts, encoding params |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [docs/features/](docs/features/) | One feature card per feature |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records |
| [docs/runbook/setup-windows.md](docs/runbook/setup-windows.md) | Install and troubleshooting guide |
| [docs/runbook/capture-and-audio-setup.md](docs/runbook/capture-and-audio-setup.md) | Capture source and audio configuration |
| [docs/runbook/deployment-checklist.md](docs/runbook/deployment-checklist.md) | Release procedure |

---

## License

See LICENSE file.
