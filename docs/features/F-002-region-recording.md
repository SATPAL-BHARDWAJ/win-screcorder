---
id: F-002
name: Region Recording
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
  - ui/region_selector.py
  - recorder/screen_capture.py
---

### Purpose
Let the user drag-select an arbitrary rectangular region of the screen to record, rather than capturing the entire display.

### User-Facing Behaviour
- User selects the ▣ (region) mode button on the toolbar
- When Record is clicked, the toolbar hides and a fullscreen semi-transparent overlay appears
- Cursor changes to a crosshair; the user clicks and drags to define a rectangle
- A live border and dimension label (`1280 × 720`) are drawn during drag
- On mouse release, the overlay closes, the toolbar reappears, and recording begins within the selected rect
- Pressing Escape cancels and returns to IDLE state

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_resolve_capture_rect()` creates and calls `RegionSelector.select()` |
| `ui/region_selector.py` | Fullscreen overlay widget; blocks on local QEventLoop until user finishes |
| `recorder/screen_capture.py` | Captures the returned rect at target FPS |

#### Data Flow
1. `toolbar._capture_mode == "region"` at Record click
2. `_resolve_capture_rect()` creates `RegionSelector()` and calls `.select()`
3. `RegionSelector.select()` shows fullscreen overlay and starts a local `QEventLoop`
4. User drags: `mousePressEvent` stores origin, `mouseMoveEvent` repaints blue rect, `mouseReleaseEvent` computes final rect
5. If rect is `>= 10x10` pixels: stores `(x, y, w, h)` in `_result`, calls `_loop.quit()`
6. If Escape pressed: `_result` remains `None`, `_loop.quit()`
7. `select()` returns `_result` (tuple or None); overlay is hidden
8. Toolbar re-shown; if None returned, recording is cancelled
9. Even-dimension enforcement applied to returned rect before passing to `ScreenCaptureThread`

#### Key Classes / Methods
- `RegionSelector.select() -> tuple | None` — blocking call via local QEventLoop; returns `(x, y, w, h)` or None
- `RegionSelector.paintEvent()` — draws dim overlay, highlighted selection rect, live dimension label
- `RegionSelector.mouseReleaseEvent()` — validates rect size (`>= 10x10`), sets result, quits loop

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| `fps` | `30` | Capture frame rate within selected region |

### Dependencies
- `PyQt5` — overlay widget, local `QEventLoop` for blocking selection

### Known Issues / Limitations
- The overlay may briefly flicker on systems with mixed-DPI multi-monitor setups
- Minimum selectable area is 10×10 pixels; smaller drags are treated as cancellation
- The local `QEventLoop` blocks Qt's main event loop — do not call long-running code during selection
- Dimension label positioning uses a fixed 110px threshold heuristic and may clip on very small selections

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
