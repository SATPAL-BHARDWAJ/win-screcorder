# ADR-009: Use PyQt5 as the UI Framework

**Status:** Accepted  
**Date:** 2026-05-17  
**Affects:** All UI components

---

## Context

ScRecorder requires a GUI framework that supports:
- Frameless, translucent, always-on-top windows
- System tray icon with context menu
- QThread for background work with signal/slot communication
- Custom painting (rounded rectangle backgrounds)
- Windows 7–11 compatibility

Options considered:
- **PyQt5** — Python bindings for Qt 5
- **PySide6** — Official Qt for Python (Qt 6), LGPL licensed
- **tkinter** — Python stdlib GUI
- **wxPython** — cross-platform native widgets

## Decision

Use **PyQt5** (Qt 5) as the UI framework.

## Rationale

- **Full feature set:** `QSystemTrayIcon`, `FramelessWindowHint`, `QThread`, `QStyleSheet`, `paintEvent` — all required features are first-class.
- **Windows native integration:** Qt 5 on Windows renders using native Windows styles and integrates correctly with DWM (Desktop Window Manager) for translucency.
- **Windows 7 compatibility:** Qt 5 supports Windows 7 (Qt 6 / PySide6 dropped Windows 7 support).
- **QThread model:** The producer/consumer threading model (QThread + queue) integrates naturally with Qt's event loop.
- **PyInstaller support:** PyQt5 has a mature, well-documented PyInstaller integration with hooks.

## Consequences

**Positive:**
- Mature, stable API with extensive documentation
- Windows 7 support maintained
- Rich styling via stylesheets

**Negative:**
- **GPL license:** PyQt5 is GPL-licensed — distributing a closed-source commercial application requires purchasing a PyQt5 commercial license from Riverbank Computing. **Verify licensing before any commercial release.**
- Qt 5 is in long-term support but not receiving new features; Qt 6 is the future
- `QDesktopWidget` (used in `win_utils.py` and `toolbar.py`) is deprecated in Qt 5.13+ in favor of `QScreen` — not yet a breaking issue

## Alternatives Considered

- **PySide6:** Official Qt for Python, LGPL licensed (free for commercial use). Qt 6 API is largely compatible with Qt 5. **Does not support Windows 7.** Rejected due to Windows 7 target, but is the correct migration path when Windows 7 support is dropped.
- **tkinter:** No `QSystemTrayIcon`, no `QThread`, no stylesheet support for custom rendering. Rejected.
- **wxPython:** Native widget rendering but limited styling; no equivalent of `WA_TranslucentBackground` for translucent windows. Rejected.

## Migration Path to PySide6

When Windows 7 support is no longer required:
1. `pip install PySide6`, remove `PyQt5`
2. Replace `from PyQt5.X import Y` with `from PySide6.X import Y` throughout
3. Replace `exec_()` with `exec()` (PySide6 removed the underscore)
4. `pyqtSignal` → `Signal`, `pyqtSlot` → `Slot`
5. Update `QDesktopWidget` usages to `QScreen` API
6. Verify PyInstaller PySide6 hooks are up to date

The API surface used by ScRecorder is straightforward enough that migration should be a 1–2 hour task.
