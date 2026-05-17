---
id: F-007
name: System Tray Integration
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - ui/toolbar.py
---

### Purpose
Allow the ScRecorder toolbar to be minimized to the Windows system tray while keeping the app running and accessible.

### User-Facing Behaviour
- Clicking ✕ on the toolbar hides the window; a tray icon remains visible in the system tray
- The tray icon tooltip shows `"ScRecorder {version}"`
- Right-clicking the tray icon shows a context menu:
  - **Show toolbar** — restores the toolbar window
  - **Start recording** — starts recording (same as clicking ●)
  - **Stop recording** — stops recording (same as clicking ■)
  - **About ScRecorder {version}** — opens version dialog
  - **Exit** — stops recording if active, hides tray, quits app
- Double-clicking the tray icon restores the toolbar
- Tray notifications shown when recording starts (2 seconds) and when a file is saved (4 seconds with filename)

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `ui/toolbar.py` | `_setup_tray()` — creates `QSystemTrayIcon`, wires up context menu and signals |

#### Data Flow
1. `_setup_tray()` called during toolbar init
2. `QSystemTrayIcon` created with standard computer icon (`QStyle.SP_ComputerIcon`)
3. `QMenu` built with 5 actions; each wired to a toolbar method
4. `_tray.activated` signal connected to `_tray_activated(reason)`
5. `_tray_activated`: if `DoubleClick`, calls `self.show()` + `self.raise_()`
6. Toolbar `closeEvent()` overridden to call `event.ignore()` and `self.hide()` instead of closing
7. On recording start: `_tray.showMessage("ScRecorder", "Recording started...", msecs=2000)`
8. On stop with output file: `_tray.showMessage("ScRecorder", filename, msecs=4000)`

#### Key Classes / Methods
- `toolbar._setup_tray()` — builds `QSystemTrayIcon` and `QMenu`
- `toolbar._tray_activated(reason)` — handles double-click to restore
- `toolbar.closeEvent(event)` — overridden to hide-to-tray rather than close
- `toolbar._show_about()` — `QMessageBox.about()` with version string

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| — | — | No configuration for tray behaviour |

### Dependencies
- `PyQt5.QtWidgets.QSystemTrayIcon` — tray icon
- `PyQt5.QtWidgets.QMenu`, `QAction` — context menu

### Known Issues / Limitations
- Tray icon uses a generic system computer icon (no custom app icon in current build — `assets/icons/app.ico` not present)
- Notification balloon support depends on Windows version and notification settings; may be suppressed in focus assist / do not disturb mode

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
