---
id: F-006
name: Global Hotkeys
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
---

### Purpose
Allow the user to start, stop, and pause recordings from any foreground application without switching to the ScRecorder toolbar.

### User-Facing Behaviour
- `Ctrl+Alt+R` — starts recording if idle; does nothing if already recording (stop is via toolbar Stop button or this hotkey is only for start — see implementation note)
- `Ctrl+Alt+P` — pauses an active recording; resumes a paused recording
- Hotkeys work regardless of which window has keyboard focus
- Hotkey events still reach the active window (`suppress=False`) — ScRecorder does not intercept them exclusively

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_setup_hotkeys()` — registers hotkeys; callbacks are `_on_record()` and `_on_pause()` |

#### Data Flow
1. On toolbar init, `_setup_hotkeys()` is called
2. `keyboard.add_hotkey("ctrl+alt+r", self._on_record, suppress=False)` registered
3. `keyboard.add_hotkey("ctrl+alt+p", self._on_pause, suppress=False)` registered
4. Registration wrapped in try/except — failure is silent; hotkeys simply don't work
5. When user presses `Ctrl+Alt+R`: `keyboard` library fires `_on_record()` on the main Qt thread via callback
6. `_on_record()` checks current state: if IDLE, starts recording; if RECORDING, is a no-op (stop is separate)

#### Key Classes / Methods
- `toolbar._setup_hotkeys()` — registers both hotkeys; try/except swallows all errors
- `keyboard.add_hotkey(combo, callback, suppress)` — from the `keyboard` library

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| `hotkey_record` | `"ctrl+alt+r"` | Hotkey combo string for record toggle |
| `hotkey_pause` | `"ctrl+alt+p"` | Hotkey combo string for pause toggle |

Config keys are read in `_setup_hotkeys()` — changing them in `config.json` and restarting applies the new bindings.

### Dependencies
- `keyboard` — global low-level keyboard hook library. See [ADR-007](../decisions/ADR-007-keyboard-library-hotkeys.md)

### Known Issues / Limitations
- Registration failure is completely silent — if admin permissions are denied or the `keyboard` library conflicts with another hook, hotkeys silently do nothing with no user notification
- `keyboard` may conflict with low-level keyboard hooks used by some games or anti-cheat systems
- `suppress=False` means the hotkey combo still reaches the active application — applications sensitive to `Ctrl+Alt` combos may react unexpectedly
- Hotkey strings are not validated at registration time; an invalid string silently fails

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
