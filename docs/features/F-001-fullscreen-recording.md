---
id: F-001
name: Fullscreen Recording
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
  - recorder/screen_capture.py
  - utils/win_utils.py
---

### Purpose
Capture all connected monitors as a single combined region without any user selection step.

### User-Facing Behaviour
- User selects the 🖥 (fullscreen) mode button on the toolbar
- When Record is clicked, recording begins immediately — no overlay or dialog appears
- The capture area spans all connected monitors (including gaps between them if monitors are non-adjacent)
- Resulting video dimensions equal the bounding box of all monitors combined

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_resolve_capture_rect()` dispatches to `get_all_monitors_rect()` when mode is `"fullscreen"` |
| `utils/win_utils.py` | `get_all_monitors_rect()` computes the bounding union of all monitor geometries |
| `recorder/screen_capture.py` | `ScreenCaptureThread` captures the resolved rect using mss |

#### Data Flow
1. `toolbar._capture_mode == "fullscreen"` at time of Record click
2. `_resolve_capture_rect()` calls `win_utils.get_all_monitors_rect()`
3. `get_all_monitors_rect()` iterates `QDesktopWidget.screenGeometry(i)` for all screens and unites the rects
4. Returns `(x, y, w, h)` covering all monitors
5. Dimensions are forced even: `w -= w % 2`, `h -= h % 2`
6. `ScreenCaptureThread(capture_rect, fps, frame_queue)` is spawned with this rect
7. `mss.grab({"top": y, "left": x, "width": w, "height": h})` captures each frame

#### Key Classes / Methods
- `win_utils.get_all_monitors_rect() -> tuple` — returns `(x, y, w, h)` as union of all monitor rects via `QDesktopWidget`
- `ScreenCaptureThread.run()` — mss capture loop at target FPS, pushes BGR24 numpy arrays to `frame_queue`

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| `fps` | `30` | Capture and encode frame rate |

### Dependencies
- `mss` — screen capture
- `PyQt5.QtWidgets.QDesktopWidget` — monitor geometry enumeration

### Known Issues / Limitations
- Gaps between non-adjacent monitors appear as black bars in the recording
- Very large multi-monitor setups (e.g., three 4K monitors) significantly increase frame queue pressure and may cause more frequent frame drops (KI-005)
- Cannot capture GPU-exclusive fullscreen DirectX applications — use windowed/borderless mode in target app

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
