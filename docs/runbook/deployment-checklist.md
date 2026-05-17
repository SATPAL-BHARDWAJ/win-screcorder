# Deployment Checklist

Step-by-step release procedure for ScRecorder. Complete every item in order.

---

## Pre-Build

- [ ] All changes committed to git (`git status` is clean)
- [ ] `CHANGELOG.md` — move items from `[Unreleased]` to a new `[X.Y.Z] — YYYY-MM-DD` block
- [ ] `requirements.txt` is up to date (remove unused `opencv-python` and `Pillow` if still present — KI-001)
- [ ] `assets/ffmpeg.exe` is present and not corrupted: `python -c "from recorder.encoder import _find_ffmpeg; print(_find_ffmpeg())"`
- [ ] `assets/icons/app.ico` present if you want a custom tray icon (optional — build succeeds without it)
- [ ] Confirm the intended version bump: `python build.py --no-build` prints the current version

---

## Build

```bash
build.bat --bump patch      # patch release (bug fixes)
build.bat --bump minor      # minor release (new features, backwards-compatible)
build.bat --bump major      # major release (breaking changes)
build.bat 1.2.3             # explicit version (use when you know the target version)
```

- [ ] No PyInstaller errors in the console output
- [ ] `dist/ScRecorder-{version}.exe` exists
- [ ] `version.py` shows the new version: `python -c "from version import __version__; print(__version__)"`

---

## Post-Build Verification (Manual Test)

Run every test from the `dist/` folder using the built exe, **not** `python main.py`.

### Smoke Tests

- [ ] Launch `dist/ScRecorder-{version}.exe` — no console window, toolbar appears at top-center of screen
- [ ] Hover all buttons — tooltips appear with correct text
- [ ] About dialog shows correct version: right-click tray → "About ScRecorder {version}"

### Fullscreen Recording

- [ ] Select 🖥 Fullscreen mode
- [ ] Click ● Record — recording starts, timer ticks
- [ ] Record for 5 seconds
- [ ] Click ■ Stop — Explorer opens at `~/Videos/ScRecorder/`
- [ ] Verify MP4 exists, plays, shows correct screen content, has audio

### Region Recording

- [ ] Select ▣ Region mode
- [ ] Click ● Record — overlay appears, toolbar hides
- [ ] Drag-select a region (~500×400)
- [ ] Release mouse — toolbar reappears, recording starts
- [ ] Record 5 seconds, stop
- [ ] Verify MP4 is cropped to selected region

### Window Recording

- [ ] Open a test application (e.g., Notepad)
- [ ] Select ⬜ Window mode
- [ ] Click ● Record — window picker appears with Notepad in list
- [ ] Select Notepad, click "Capture this window"
- [ ] Record 5 seconds, type something in Notepad, stop
- [ ] Verify MP4 shows only the Notepad window

### Audio

- [ ] Play music or a YouTube video
- [ ] Start fullscreen recording
- [ ] Record 10 seconds
- [ ] Stop, verify MP4 has an audible audio track matching what was playing

### Pause / Resume

- [ ] Start a recording
- [ ] Click ⏸ Pause — timer freezes, button shows ▶
- [ ] Wait 5 seconds (paused)
- [ ] Click ▶ Resume — timer continues from where it stopped
- [ ] Stop recording
- [ ] Verify output duration matches active (non-paused) time

### Hotkeys

- [ ] Focus a different window (e.g., Notepad)
- [ ] Press `Ctrl+Alt+R` — recording starts (check tray notification)
- [ ] Press `Ctrl+Alt+P` — recording pauses
- [ ] Press `Ctrl+Alt+P` again — recording resumes
- [ ] Stop via toolbar

### System Tray

- [ ] Click ✕ — toolbar hides, tray icon visible
- [ ] Double-click tray icon — toolbar restores
- [ ] Right-click tray → "Start recording" — recording begins
- [ ] Right-click tray → "Stop recording" — recording stops
- [ ] Right-click tray → Exit — app closes cleanly

### Config Persistence

- [ ] Stop the app
- [ ] Select Region mode, restart — Region mode is still selected
- [ ] Config file exists at `%APPDATA%\ScRecorder\config.json`

### Windows File Properties

- [ ] Right-click `dist/ScRecorder-{version}.exe` → Properties → Details
- [ ] File version: `{version}.0`
- [ ] Product name: `ScRecorder`
- [ ] Copyright: `Copyright (C) 2025 ScRecorder`

---

## Release

- [ ] Commit `version.py` and `CHANGELOG.md`: `git commit -m "Release v{version}"`
- [ ] Tag the commit: `git tag v{version}`
- [ ] Push: `git push && git push --tags`
- [ ] Create GitHub release:
  - Title: `ScRecorder v{version}`
  - Body: paste the `[{version}]` section from `CHANGELOG.md`
  - Attach: `dist/ScRecorder-{version}.exe`
- [ ] Update `CHANGELOG.md` footer links:
  ```
  [Unreleased]: https://github.com/user/screcorder/compare/v{version}...HEAD
  [{version}]: https://github.com/user/screcorder/releases/tag/v{version}
  ```

---

## Known Non-Blockers

These issues are known and documented — do not hold a release for them unless specifically targeted:

| ID | Issue | Location |
|----|-------|----------|
| KI-001 | `opencv-python` and `Pillow` in requirements.txt, unused | requirements.txt |
| KI-004 | ffmpeg errors not surfaced to UI | recorder/encoder.py |
| KI-005 | Dropped frames not reported to user | recorder/screen_capture.py |
