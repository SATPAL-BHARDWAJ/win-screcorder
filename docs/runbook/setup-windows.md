# Setup Guide — Windows

Covers: Windows 7, 10, 11 · Python source setup and release exe install.

---

## 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Windows | 7, 10, or 11 | 64-bit recommended |
| Python | 3.13 | [python.org/downloads](https://www.python.org/downloads/) — **source run only** |
| ffmpeg | Any recent static build | [ffmpeg.org/download.html](https://ffmpeg.org/download.html) — place `ffmpeg.exe` in `assets/` |
| Git | Any | Optional — for cloning the repo |

---

## 2. Install from Source

### 2.1 Get the code

```bash
git clone https://github.com/user/screcorder.git
cd screcorder
```

Or download and extract the ZIP from GitHub.

### 2.2 Create a virtual environment (recommended)

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2.3 Install dependencies

```bash
pip install -r requirements.txt
```

### 2.4 Place ffmpeg

Download a Windows static build of ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html).  
Extract and copy `ffmpeg.exe` to the `assets/` folder:

```
screcorder/
  assets/
    ffmpeg.exe   ← here
```

Alternatively, add ffmpeg to your system PATH.

### 2.5 Verify ffmpeg is found

```bash
python -c "from recorder.encoder import _find_ffmpeg; print(_find_ffmpeg())"
```

Expected output: a path ending in `ffmpeg.exe`.

### 2.6 Launch

```bash
python main.py
```

The floating toolbar appears at the top center of your screen.

---

## 3. Install from Release Exe

1. Download `ScRecorder-{version}.exe` from the [Releases](https://github.com/user/screcorder/releases) page
2. Double-click to run — no installation required
3. If Windows SmartScreen shows a warning: click **More info → Run anyway**  
   (The exe is unsigned — see [ADR-008](../decisions/ADR-008-pyinstaller-single-exe.md))

ffmpeg is bundled inside the exe — no separate download needed.

---

## 4. First Run

On first launch, ScRecorder automatically:
- Creates `%APPDATA%\ScRecorder\config.json` with default settings
- Creates `~/Videos/ScRecorder/` as the default output folder

No configuration is required to start recording.

---

## 5. Audio Setup

ScRecorder auto-detects your system's WASAPI loopback device.  
For most users on English Windows 10/11, this works with no setup.

**Check your audio device is active:**
- Ensure your audio output device (speakers/headphones) is not muted at the OS level
- The loopback captures whatever is playing through the current default output device

**Non-English Windows / unusual driver names:**  
The loopback device is detected by name. If it is not found, the app falls back to the default microphone. See [ADR-005](../decisions/ADR-005-wasapi-loopback-device-detection.md) for details and workarounds.

---

## 6. Troubleshooting

### ffmpeg Not Found — recording starts but produces no output file

```
FileNotFoundError: [WinError 2] The system cannot find the file specified
```

**Fix:**
1. Verify `assets/ffmpeg.exe` exists: `dir assets\ffmpeg.exe`
2. Or add ffmpeg to PATH and restart the app
3. Run the verification command from §2.5

---

### No Audio Track in Output

**Symptom:** MP4 plays but has no sound.

**Causes and fixes:**
1. System audio output was muted or silent during recording — nothing to capture
2. WASAPI loopback device not detected → fell back to mic (check mic is not muted)
3. Non-English Windows: device name mismatch (see [ADR-005](../decisions/ADR-005-wasapi-loopback-device-detection.md))

---

### Region Selector Overlay Flickers / Off-Position

**Symptom:** The drag-select overlay appears on the wrong monitor or flickers.

**Cause:** Mixed-DPI multi-monitor setup where monitors have different scaling factors.

**Workaround:** Use Fullscreen or Window capture mode instead.

---

### Antivirus Blocks or Quarantines the Exe

**Cause:** PyInstaller-packaged executables trigger heuristic AV detection because they self-extract to `%TEMP%` on startup.

**Fix:** Add an exception for `ScRecorder-{version}.exe` in your AV software.  
The exe is not signed — see [ADR-008](../decisions/ADR-008-pyinstaller-single-exe.md).

---

### Hotkeys Do Not Work

**Symptom:** `Ctrl+Alt+R` and `Ctrl+Alt+P` have no effect.

**Causes:**
- Some environments (e.g., sandboxed processes, corporate managed PCs) block low-level keyboard hooks
- Another application has registered the same hotkey combo

**Workaround:** Use the toolbar buttons directly. Hotkey registration is silent on failure.

---

### Toolbar is Off-Screen

**Symptom:** The toolbar was dragged off-screen and cannot be seen.

**Fix:** Delete `%APPDATA%\ScRecorder\config.json` and restart the app. The toolbar resets to the top-center of the primary screen.

---

## 7. Uninstall

1. Delete `ScRecorder-{version}.exe` (or the source folder)
2. Delete `%APPDATA%\ScRecorder\` — contains config and no recordings
3. Optionally delete `~/Videos/ScRecorder/` — contains your recordings

No registry entries are created.
