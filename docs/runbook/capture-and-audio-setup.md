# Capture Source and Audio Setup

Reference guide for ScRecorder's three capture modes and audio configuration.

---

## 1. Screen Capture Modes

### 1.1 Fullscreen

**Button:** 🖥  
**What it captures:** The bounding rectangle of all connected monitors combined.

- No selection step — recording starts immediately
- On a single monitor (1920×1080): captures exactly that resolution
- On two 1920×1080 monitors side-by-side: captures a 3840×1080 region
- Gaps between non-adjacent monitors (e.g., different heights) appear as black bars
- Horizontal/vertical position of monitors is respected (uses `QDesktopWidget` geometry)

**Best for:** Single-monitor setups; full-desktop tutorials.

---

### 1.2 Region

**Button:** ▣  
**What it captures:** A user-defined rectangular region dragged on screen.

**Workflow:**
1. Click ▣ to select region mode
2. Click ● Record — the toolbar hides and a fullscreen semi-transparent overlay appears
3. Click and drag to draw your rectangle — a blue border and live dimension label appear
4. Release the mouse — overlay closes, toolbar reappears, recording begins immediately
5. Press **Escape** at any point to cancel

**Notes:**
- Minimum selectable area: 10×10 pixels
- Width and height are auto-rounded to even numbers (H.264 requirement)
- The region can span across multiple monitors if you drag across a monitor boundary
- The overlay may have coordinate drift on mixed-DPI multi-monitor setups

**Best for:** Recording a specific area (e.g., one application panel, a browser tab, a code window).

---

### 1.3 Window

**Button:** ⬜  
**What it captures:** The screen region occupied by a specific application window.

**Workflow:**
1. Click ⬜ to select window mode
2. Click ● Record — a dialog lists all visible, titled windows
3. Type in the filter box to narrow the list
4. Double-click a window or select it and click **Capture this window**
5. Recording begins capturing the screen region at that window's current position

**Notes:**
- The window must be visible and **not minimized** at the time of selection
- The list is captured once when the dialog opens — it does not update live
- If the target window is moved or resized after recording starts, the captured region does not follow (it records the original screen coordinates)
- The window does not need to remain in focus during recording

**Best for:** Recording a single application; avoiding capturing the browser bar in a "capture window" scenario.

---

## 2. Audio Capture

### 2.1 WASAPI Loopback (System Audio)

ScRecorder captures system audio output — whatever is currently playing through your speakers or headphones — using Windows WASAPI loopback.

**Requirements:**
- An audio output device must be active and set as the default playback device
- The device does not need to produce sound at the moment recording starts, but must be enabled at the OS level (not disabled in Device Manager)

**How detection works:**  
The app searches all PyAudio devices for names containing (case-insensitive): `"loopback"`, `"stereo mix"`, or `"what u hear"`. The first match with at least one input channel is used.

Common device names by system:
| System | Typical device name |
|--------|-------------------|
| Windows 10/11 Realtek | "Stereo Mix (Realtek...)" |
| Windows 10/11 generic | "WASAPI Loopback" |
| Older systems | "What U Hear" |
| VB-Audio Virtual Cable | "CABLE Output (VB-Audio...)" |

**Enabling Stereo Mix** (if not visible):
1. Right-click the speaker icon in the system tray → **Sounds**
2. **Recording** tab → right-click empty area → **Show Disabled Devices**
3. Right-click **Stereo Mix** → **Enable**

---

### 2.2 Fallback to Default Input

If no loopback device is found, the app falls back to the system **default input device** (typically the microphone). Audio will still be recorded, but it will capture microphone input rather than system audio.

To check which device is being used: if the output MP4 contains unexpected microphone audio rather than system audio, the loopback device was not detected. See [ADR-005](../decisions/ADR-005-wasapi-loopback-device-detection.md).

---

### 2.3 Audio Not Needed

If you do not want audio in your recording:
- In the current version (v1.0.0), there is no audio disable toggle in the UI
- Workaround: mute the system audio output before starting recording — the loopback will capture silence; the resulting MP4 will have a silent audio track

---

## 3. Multi-Monitor Considerations

| Mode | Multi-Monitor Behaviour |
|------|------------------------|
| Fullscreen | Captures the bounding box of all monitors; gap regions are black |
| Region | Can span monitors; coordinates use the combined virtual desktop space |
| Window | Captures the window's position in virtual desktop coordinates; works correctly if window is on any monitor |

**DPI mixing:** If monitors have different DPI scaling (e.g., 100% + 150%), the region selector overlay may have a coordinate offset. This is a known limitation of Qt's `WA_TranslucentBackground` overlay on mixed-DPI setups. Use Fullscreen or Window mode as a workaround.

---

## 4. Performance Tuning

### FPS

Edit `%APPDATA%\ScRecorder\config.json`:
```json
{ "fps": 30 }
```

| FPS | Use Case | CPU Impact |
|-----|----------|-----------|
| 15 | Presentations, slideshows | Low |
| 30 | Standard recording (default) | Medium |
| 60 | Fast motion, gaming | High |

Higher FPS increases CPU load during capture and encoding, and increases output file size.

### Encoding Quality

The encoding preset and quality are hardcoded in `recorder/encoder.py`:

| Parameter | Value | Effect of Changing |
|-----------|-------|-------------------|
| `-preset` | `ultrafast` | Lower presets = smaller file, higher CPU |
| `-crf` | `23` | Lower = better quality, larger file (range: 0–51) |

To change these, edit the ffmpeg command in `Encoder.start()` and rebuild. See [ADR-002](../decisions/ADR-002-ffmpeg-subprocess-encoding.md).

### Queue Sizes

| Queue | Size | Buffer at 30fps |
|-------|------|----------------|
| `frame_queue` | 60 frames | ~2 seconds |
| `audio_queue` | 200 chunks | Unused (dead code) |

If frames are being dropped (video stutters in output), the encoder is too slow for the capture rate. Reduce FPS or use a lower-resolution capture region.
