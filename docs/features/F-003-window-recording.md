---
id: F-003
name: Window Recording
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
  - ui/window_picker.py
  - utils/win_utils.py
  - recorder/screen_capture.py
---

### Purpose
Allow the user to select a specific application window to record, capturing only that window's screen region.

### User-Facing Behaviour
- User selects the ⬜ (window) mode button on the toolbar
- When Record is clicked, a modal dialog lists all visible, titled windows
- User can filter the list by typing in a search box
- Double-clicking or selecting a window and clicking "Capture this window" begins recording
- Recording captures the screen region occupied by the window at the time of selection
- Clicking Cancel returns to IDLE

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_resolve_capture_rect()` opens `WindowPicker` and converts HWND to rect |
| `ui/window_picker.py` | Modal `QDialog` with searchable list; returns HWND |
| `utils/win_utils.py` | `enumerate_windows()` lists HWNDs; `get_window_rect(hwnd)` converts to rect |
| `recorder/screen_capture.py` | Captures the resolved window rect at target FPS |

#### Data Flow
1. `toolbar._capture_mode == "window"` at Record click
2. `_resolve_capture_rect()` creates `WindowPicker()` and calls `.pick()`
3. `WindowPicker.__init__()` calls `win_utils.enumerate_windows()` to populate the list
4. `enumerate_windows()` uses `win32gui.EnumWindows()` to collect `(hwnd, title)` pairs for all visible, titled windows
5. User selects a window; `pick()` returns the selected `hwnd` (int)
6. `toolbar._resolve_capture_rect()` calls `win_utils.get_window_rect(hwnd)` → `(x, y, w, h)`
7. Even-dimension enforcement applied; `ScreenCaptureThread` spawned with this rect

#### Key Classes / Methods
- `WindowPicker.pick() -> int | None` — modal dialog; returns HWND or None on cancel
- `WindowPicker._populate()` — calls `enumerate_windows()`, renders list items with HWND stored in `Qt.UserRole`
- `WindowPicker._filter(text)` — case-insensitive substring filter on window titles
- `win_utils.enumerate_windows() -> list[tuple[int, str]]` — `[(hwnd, title), ...]` for visible windows
- `win_utils.get_window_rect(hwnd) -> tuple | None` — `(x, y, w, h)` or None if minimized/invalid

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| `fps` | `30` | Capture frame rate |

### Dependencies
- `pywin32` (`win32gui`, `win32con`) — HWND enumeration and rect query

### Known Issues / Limitations
- The window list is captured once when the dialog opens — windows that open or close during selection are not shown until the picker is reopened
- Recording captures the screen region at the window's position at start time; if the window moves after selection starts, the captured region does not follow
- Minimized windows are excluded from the list; minimizing a window after starting its recording captures whatever is behind it
- `get_window_rect()` returns None for minimized windows — causes recording to abort silently

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
