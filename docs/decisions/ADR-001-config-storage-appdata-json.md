# ADR-001: Store Configuration in %APPDATA% as JSON

**Status:** Accepted  
**Date:** 2026-05-17  
**Affects:** [F-009](../features/F-009-config-persistence.md)

---

## Context

ScRecorder needs to persist user preferences (output directory, FPS, capture mode) between sessions. Several options exist for Windows configuration storage:

- Windows Registry
- INI file (configparser)
- JSON file in `%APPDATA%`
- JSON file next to the exe
- SQLite database

The application is a simple single-user desktop tool with a small, flat config schema (3–5 keys).

## Decision

Store configuration as a plain JSON file at `%APPDATA%\ScRecorder\config.json`, loaded and written by functions in `main.py` using the Python stdlib `json` module.

## Rationale

- **Human-readable and hand-editable** — users and developers can inspect and fix the config without special tools
- **Easy to reset** — deleting the file restores defaults
- **No registry pollution** — avoids leaving orphaned registry entries on uninstall
- **No extra dependencies** — Python's `json` stdlib handles everything
- **Standard location** — `%APPDATA%` is the correct Windows location for per-user application data; it roams with the user profile on domain machines

## Consequences

**Positive:**
- Simple implementation (10 lines in `main.py`)
- Portable between Python versions
- Trivially backed up

**Negative:**
- No schema validation — a hand-edited config with a wrong type (e.g., `"fps": "thirty"`) causes silent failures downstream rather than a clear error at load time
- Corrupt JSON (partial write on crash) silently resets to defaults — no warning to the user
- JSON next to the exe would be easier for portable/USB use; `%APPDATA%` is per-user-profile only

## Alternatives Considered

- **Windows Registry:** Harder to inspect, requires `winreg` API, leaves orphaned keys on uninstall. Rejected.
- **INI file next to exe:** Breaks in the frozen PyInstaller exe (write to `sys._MEIPASS` directory is not possible). Rejected.
- **SQLite:** Overkill for a 3-key flat config. Rejected.
