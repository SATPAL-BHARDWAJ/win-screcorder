---
id: F-011
name: Floating Frameless Toolbar
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
---

### Purpose
Provide a compact, always-on-top, non-intrusive recording control surface that floats above all other windows and can be repositioned by dragging.

### User-Facing Behaviour
- Toolbar appears at the top-center of the primary screen when the app starts
- Window has no title bar, borders, or resize handles
- Background is semi-transparent dark glass (`rgba(28,28,32,235)` with 8px rounded corners)
- The toolbar stays on top of all other windows at all times
- Click-and-drag anywhere on the toolbar body (not on a button) to reposition it
- Fixed height of 44px; width auto-sizes to fit all controls

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_setup_window()`, `mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`, `paintEvent` |

#### Data Flow
**Window creation:**
1. `_setup_window()` sets `Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint`
2. `WA_TranslucentBackground` attribute enables OS-level window transparency
3. `setFixedHeight(44)` enforces compact height
4. Positioned at `(screen_center_x - 200, screen_top + 10)` using `QDesktopWidget`

**Drag to reposition:**
1. `mousePressEvent(event)`: if left button, store `_drag_pos = event.globalPos() - self.frameGeometry().topLeft()`
2. `mouseMoveEvent(event)`: if dragging, `self.move(event.globalPos() - _drag_pos)`
3. `mouseReleaseEvent(event)`: clear `_drag_pos`

**Background painting:**
- `paintEvent()` uses `QPainter` to draw a filled `QRoundedRect` with the dark semi-transparent color
- This is required because `WA_TranslucentBackground` suppresses Qt's default stylesheet background rendering on `QWidget` subclasses

#### Key Classes / Methods
- `toolbar._setup_window()` — window flags, attributes, size, initial position
- `toolbar.paintEvent(a0)` — manual background draw; required for translucent window + stylesheet
- `toolbar.mousePressEvent / mouseMoveEvent / mouseReleaseEvent` — drag implementation

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| — | — | Position is not persisted between sessions |

### Dependencies
- `PyQt5.QtCore.Qt` — window flags
- `PyQt5.QtGui.QPainter`, `QColor` — custom paint

### Known Issues / Limitations
- Toolbar position resets to top-center on every launch — position is not saved to config
- On some Windows 7 systems with Aero disabled, `WA_TranslucentBackground` may fall back to an opaque window
- The toolbar can be dragged off-screen with no snap-back; restart the app to recover default position

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
