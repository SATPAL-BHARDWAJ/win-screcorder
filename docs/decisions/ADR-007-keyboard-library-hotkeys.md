# ADR-007: Use `keyboard` Library for Global Hotkeys

**Status:** Accepted  
**Date:** 2026-05-17  
**Affects:** [F-006](../features/F-006-global-hotkeys.md)

---

## Context

ScRecorder requires hotkeys that work regardless of which window has keyboard focus — the user should be able to start and pause recordings while using other applications. Options considered:

- **`keyboard` library** (`pip install keyboard`) — pure Python global hotkey hooks
- **`pynput`** — cross-platform input monitoring
- **win32api `RegisterHotKey`** — Windows API hotkey registration
- **Qt `QShortcut`** — only works when the Qt window has focus

## Decision

Use `keyboard.add_hotkey(combo, callback, suppress=False)` in `toolbar._setup_hotkeys()`.

See `ui/toolbar.py` — `_setup_hotkeys()`.

## Rationale

- **Simple API:** `keyboard.add_hotkey("ctrl+alt+r", callback)` — one line per hotkey, no message loop plumbing
- **Works from any window:** Hooks into the OS keyboard input stream directly
- **`suppress=False`:** Hotkey events still reach the active application; ScRecorder does not intercept them exclusively, reducing conflicts
- **No WM_HOTKEY integration needed:** `win32api.RegisterHotKey` requires a Win32 message pump integration with Qt's event loop, which adds non-trivial plumbing

## Consequences

**Positive:**
- Minimal implementation (3 lines in `_setup_hotkeys()`)
- Complex combos supported (e.g., `ctrl+shift+alt+r`)
- No window focus requirement

**Negative:**
- `keyboard` library installs a low-level keyboard hook — this may conflict with games using anti-cheat software or other low-level hooks
- Registration failure is completely silent (wrapped in try/except) — users don't know hotkeys failed (see KI in [F-006](../features/F-006-global-hotkeys.md))
- `suppress=False` means `Ctrl+Alt+R` reaches the active window — applications sensitive to this combo may react unexpectedly
- `keyboard` library may require elevated permissions in some sandboxed environments

## Alternatives Considered

- **`win32api.RegisterHotKey` + WM_HOTKEY:** Most reliable Windows approach, but requires integrating with Qt's native event filter (`QAbstractNativeEventFilter`) to receive `WM_HOTKEY` messages. Significant boilerplate. Worth considering for a future version if `keyboard` causes compatibility issues.
- **`pynput`:** Cross-platform, good API, but heavier dependency with no benefit given Windows-only target. Rejected.
- **`QShortcut`:** Only fires when the Qt window is focused. Rejected for this use case.
