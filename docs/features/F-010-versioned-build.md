---
id: F-010
name: Versioned PyInstaller Build
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - build.py
  - build.bat
  - version.py
---

### Purpose
Produce a single distributable Windows exe named `ScRecorder-{version}.exe` with embedded Windows PE version metadata, from a one-command build invocation with optional automatic version bumping.

### User-Facing Behaviour
- `build.bat` (or `build.bat --bump patch`) produces `dist/ScRecorder-1.0.1.exe`
- Right-click the exe → Properties → Details shows: File version `1.0.1.0`, Product name `ScRecorder`, Copyright `Copyright (C) 2025 ScRecorder`
- Running the app: tray tooltip and About dialog show the version

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `version.py` | Single source of truth — only file edited by developer or `build.py` |
| `build.py` | Reads/writes `version.py`; generates `version_info.txt` and `ScRecorder.spec`; runs PyInstaller |
| `build.bat` | Thin wrapper: `python "%~dp0build.py" %*` |

#### Data Flow
1. `build.bat --bump patch` → `python build.py --bump patch`
2. `read_version()` regex-reads `__version__` from `version.py` without importing it
3. `bump_version("1.0.0", "patch")` → `"1.0.1"`
4. `write_version("1.0.1")` regex-rewrites `__version__`, `VERSION_MAJOR/MINOR/PATCH`, `VERSION_TUPLE` in `version.py`
5. `make_version_info("1.0.1")` → generates `VSVersionInfo(...)` block string
6. Writes `version_info.txt` to project root
7. `make_spec("1.0.1")` → generates PyInstaller `.spec` file string with:
   - `name='ScRecorder-1.0.1'`
   - `version=r'...version_info.txt'`
   - `binaries=[(assets/ffmpeg.exe, assets)]` (if exists)
   - `icon=r'assets/icons/app.ico'` (if exists)
   - `console=False`
8. Writes `ScRecorder.spec`
9. Runs `python -m PyInstaller --noconfirm ScRecorder.spec`
10. Cleans up `version_info.txt` and `ScRecorder.spec`
11. Reports: `dist/ScRecorder-1.0.1.exe (245.3 MB)`

#### Key Classes / Methods
- `build.read_version() -> str` — regex parse without import
- `build.write_version(v: str)` — regex rewrite of all version constants
- `build.bump_version(current: str, part: str) -> str` — semantic bump
- `build.make_version_info(v: str) -> str` — Windows PE metadata block
- `build.make_spec(v: str) -> str` — PyInstaller spec file content
- `build.run_build(v: str)` — orchestrates the full build

### Configuration
| Key | Default | Effect |
|-----|---------|--------|
| — | — | No config.json keys; build config is in `version.py` and CLI args |

### Dependencies
- `PyInstaller` — must be installed: `pip install pyinstaller`
- `ffmpeg.exe` — bundled from `assets/ffmpeg.exe` if present
- `assets/icons/app.ico` — bundled if present; icon line omitted from spec if missing

### Known Issues / Limitations
- No code signing — Windows SmartScreen and some AV software may flag the exe (see [ADR-008](../decisions/ADR-008-pyinstaller-single-exe.md))
- `version.py` is rewritten before PyInstaller runs; if the build fails, the version is already bumped — no automatic rollback
- ffmpeg.exe (~200MB) makes the output exe very large
- The `.spec` and `version_info.txt` files are generated and deleted each build — do not hand-edit them

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
