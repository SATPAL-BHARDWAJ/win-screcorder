---
id: F-009
name: Configuration Persistence
status: stable
added_version: v1.0.0
last_modified: 2026-05-17
files:
  - main.py
---

### Purpose
Remember user preferences (output directory, FPS, last capture mode) across application restarts.

### User-Facing Behaviour
- Settings are saved automatically — no "Save" button required
- On next launch, the app restores: last capture mode button selection, output directory
- If the config file is missing or corrupt, defaults are silently applied and a new config file is created on next save

### Technical Implementation

#### Files Involved
| File | Role |
|------|------|
| `main.py` | `load_config()`, `save_config(config)`, `DEFAULT_CONFIG` dict |

#### Data Flow
1. On app start: `load_config()` checks if `config.json` exists
2. If exists: `json.load()` in a try/except; merges with `DEFAULT_CONFIG` via `{**DEFAULT_CONFIG, **saved}` (saved keys override defaults)
3. If missing or corrupt: returns `DEFAULT_CONFIG.copy()` (silent fallback)
4. Config dict passed to `Toolbar.__init__()` and held as `self.config`
5. `toolbar._set_mode(mode)` updates `config["capture_mode"]` and calls `save_config(config)`
6. `save_config()` writes the full config dict to JSON with `indent=2`

**Config file path:** `os.path.join(os.environ.get("APPDATA", "."), "ScRecorder", "config.json")`

#### Key Classes / Methods
- `main.load_config() -> dict` — reads JSON, merges with defaults, returns config dict
- `main.save_config(config: dict)` — writes config to JSON; creates directory if missing
- `main.DEFAULT_CONFIG` — defines keys and default values

### Configuration
| Key | Type | Default | Effect |
|-----|------|---------|--------|
| `output_dir` | string | `~/Videos/ScRecorder` | Where MP4 files are saved |
| `fps` | int | `30` | Capture and encode frame rate |
| `capture_mode` | string | `"fullscreen"` | Last selected capture mode |

### Dependencies
- `json` (stdlib)
- `os` (stdlib)

### Known Issues / Limitations
- No schema validation — a manually edited `config.json` with wrong types silently uses the invalid value until it causes an error elsewhere
- Config is saved only on mode change; output_dir and fps changes require manual config.json edit in v1.0.0

### Modification Log
| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-05-17 | v1.0.0 | Initial implementation | — |
