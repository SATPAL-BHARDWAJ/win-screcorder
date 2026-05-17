---
id: F-012
name: Button Tooltips
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
  - main.py
---

### Purpose
Provide contextual, multi-line help text for every toolbar control, shown on mouse hover.

### User-Facing Behaviour
- Hovering any button or the timer label shows a tooltip after the system hover delay
- Tooltips are dark-themed (matching the toolbar) with white text, rounded border, and `Segoe UI` font
- Tooltips are multi-line: first line is the action name, subsequent lines give details and hotkey (where applicable)
- Example for Record button: "Start Recording / Begin capturing your screen. / Hotkey: Ctrl+Alt+R"

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_btn()` helper sets tooltip; `QToolTip` style in `STYLE` constant |
| `main.py` | `QToolTip.setFont(app.font())` applied at startup |

#### Data Flow
1. `_btn(text, obj_name, tooltip, checkable)` wraps tooltip string in `<p style='white-space:pre'>...</p>`
2. `b.setToolTip(html_string)` — Qt renders this as rich text
3. `STYLE` CSS constant includes a `QToolTip` block:
   ```css
   QToolTip {
       background-color: #1e1e24;
       color: #e0e0e0;
       border: 1px solid rgba(255,255,255,60);
       border-radius: 4px;
       padding: 4px 8px;
       font-size: 12px;
       font-family: "Segoe UI", sans-serif;
   }
   ```
4. `main.py` calls `QToolTip.setFont(app.font())` to apply the font globally

#### Tooltip Text by Control

| Control | First Line | Details |
|---------|-----------|---------|
| ● Record | Start Recording | Begin capturing your screen. / Hotkey: Ctrl+Alt+R |
| ⏸ Pause | Pause / Resume | Temporarily pause the recording. / Hotkey: Ctrl+Alt+P |
| ■ Stop | Stop Recording | Finish and save the video to your Videos folder. |
| 🖥 Fullscreen | Full Screen | Record your entire display. / For multi-monitor setups, covers all screens. |
| ▣ Region | Select Region | Draw a rectangle to record only part of the screen. / Click and drag after pressing Record. |
| ⬜ Window | Capture Window | Pick a specific application window to record. / A window list will appear. |
| ✕ Close | Minimise to Tray | Hide the toolbar. ScRecorder keeps running / in the system tray. |
| Timer | Recording duration | (hours : minutes : seconds) |

#### Key Classes / Methods
- `toolbar._btn(text, obj_name, tooltip, checkable) -> QPushButton` — creates button with HTML tooltip
- `lbl_timer.setToolTip(...)` — set directly (not via `_btn`)

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| — | — | No configuration |

### Dependencies
- `PyQt5.QtWidgets.QToolTip`

### Known Issues / Limitations
- Tooltip display delay uses the system setting — not configurable per-button in the current implementation
- On some high-DPI displays, tooltip font may appear slightly oversized depending on the system font scaling

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
