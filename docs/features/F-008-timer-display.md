---
id: F-008
name: Recording Timer
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
---

### Purpose
Show the elapsed recording time on the toolbar so the user knows how long the current recording has been running.

### User-Facing Behaviour
- A `HH:MM:SS` label is always visible on the toolbar between the control buttons and the mode buttons
- Counter starts at `00:00:00` and increments each second when recording is active
- Timer freezes while recording is paused — paused duration is not counted
- Timer resets to `00:00:00` when recording is stopped
- Hovering the timer label shows a tooltip: "Recording duration (hours : minutes : seconds)"

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `QTimer` setup, `_tick()` callback, `lbl_timer` label |

#### Data Flow
1. `_build_ui()` creates `lbl_timer = QLabel("00:00:00")` with object name `"timer"`
2. `_timer = QTimer(self)` with 1000ms interval; `timeout` signal connected to `_tick()`
3. On `_on_record()`: `_elapsed_secs = 0`, `_timer.start()`
4. Each `_tick()`: if not `_paused`, increment `_elapsed_secs`; format and update label
5. On `_on_pause()`: `_timer.stop()` — no more ticks while paused; resume calls `_timer.start()`
6. On `_on_stop()`: `_timer.stop()`, `lbl_timer.setText("00:00:00")`, `_elapsed_secs = 0`

**Format function (inline in `_tick()`):**
```python
h = self._elapsed_secs // 3600
m = (self._elapsed_secs % 3600) // 60
s = self._elapsed_secs % 60
self.lbl_timer.setText(f"{h:02d}:{m:02d}:{s:02d}")
```

#### Key Classes / Methods
- `toolbar._tick()` — called every 1000ms; increments counter, updates label
- `toolbar._timer` — `QTimer` instance, 1000ms interval

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| — | — | No configuration |

### Dependencies
- `PyQt5.QtCore.QTimer`

### Known Issues / Limitations
- Timer resolution is 1 second; the displayed value lags real time by up to 1 second
- `QTimer` accuracy on Windows is ~15ms; this is more than sufficient for 1-second resolution
- Timer does not track wall-clock time — it counts timer ticks, which may drift slightly if the system is under heavy load and Qt event processing is delayed

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
