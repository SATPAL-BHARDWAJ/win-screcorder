# CHANGELOG

All notable changes to ScRecorder are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
Versions follow [Semantic Versioning](https://semver.org/).

> **Rule:** This file is append-only. Never delete or rewrite past entries.  
> When releasing: move items from `[Unreleased]` to a new version block with today's date.

---

## [Unreleased]

### Added
### Changed
### Fixed
### Removed

---

## [1.0.0] — 2026-05-17

### Added
- **Fullscreen recording** — captures all connected monitors as a single combined region ([F-001](docs/features/F-001-fullscreen-recording.md))
- **Region recording** — fullscreen drag-select overlay to record any arbitrary rectangular area ([F-002](docs/features/F-002-region-recording.md))
- **Window recording** — HWND picker dialog to record a specific application window ([F-003](docs/features/F-003-window-recording.md))
- **Audio capture** — WASAPI loopback capture (system audio); falls back to default input device ([F-004](docs/features/F-004-audio-capture.md))
- **Pause / Resume** — flag-based pause that freezes timer and stops writing without stopping ffmpeg ([F-005](docs/features/F-005-pause-resume.md))
- **Global hotkeys** — Ctrl+Alt+R (record), Ctrl+Alt+P (pause) work from any foreground window ([F-006](docs/features/F-006-global-hotkeys.md))
- **System tray integration** — minimize to tray, restore, quick record/stop from tray context menu ([F-007](docs/features/F-007-system-tray.md))
- **Recording timer** — HH:MM:SS elapsed counter; pauses when recording is paused ([F-008](docs/features/F-008-timer-display.md))
- **Config persistence** — user settings saved to `%APPDATA%\ScRecorder\config.json` ([F-009](docs/features/F-009-config-persistence.md))
- **Versioned PyInstaller build** — `build.bat --bump patch|minor|major` produces `dist/ScRecorder-X.Y.Z.exe` with Windows PE metadata ([F-010](docs/features/F-010-versioned-build.md))
- **Floating frameless toolbar** — semi-transparent, always-on-top, drag-to-reposition ([F-011](docs/features/F-011-floating-toolbar.md))
- **Button tooltips** — multi-line dark-themed tooltips on all toolbar controls ([F-012](docs/features/F-012-tooltips.md))
- Output format: H.264 video (`libx264 -preset ultrafast -crf 23`) + AAC audio (`192k`) in MP4
- Output location: `~/Videos/ScRecorder/Recording_{timestamp}.mp4`
- ffmpeg bundled in release exe; auto-detected from `assets/` or system PATH in dev mode

### Known Issues at Release
- **KI-001:** `opencv-python` and `Pillow` listed in `requirements.txt` but never imported
- **KI-002:** WASAPI audio loopback device detected by name substring — fails on non-English Windows
- **KI-003:** WAV file path passed to encoder via private attribute assignment
- **KI-004:** ffmpeg errors are not surfaced to the UI — recording fails silently on encoder crash
- **KI-005:** Dropped frames (queue overflow) are not reported to the user

---

[Unreleased]: https://github.com/user/screcorder/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/user/screcorder/releases/tag/v1.0.0
