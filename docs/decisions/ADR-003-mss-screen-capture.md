# ADR-003: Use mss for Screen Capture

**Status:** Accepted  
**Date:** 2026-05-17  
**Affects:** [F-001](../features/F-001-fullscreen-recording.md), [F-002](../features/F-002-region-recording.md), [F-003](../features/F-003-window-recording.md)

---

## Context

ScRecorder needs to capture screen pixels at up to 60 FPS and convert them to BGR24 numpy arrays for piping to ffmpeg. Options considered:

- **win32gui BitBlt (GDI)** — traditional Win32 screen capture
- **DXGI Desktop Duplication** — hardware-accelerated DirectX screen copy
- **PIL / Pillow ImageGrab** — Python screenshot via GDI
- **mss** — fast cross-platform screen capture library returning numpy arrays

## Decision

Use the `mss` library (`pip install mss`) for screen capture in `recorder/screen_capture.py`.

## Rationale

- **Direct numpy output:** `mss.grab()` returns a `ScreenShot` object whose raw buffer is directly viewable as a numpy BGRA array — no pixel format conversion required beyond dropping the alpha channel (`[:, :, :3]`).
- **Speed:** mss uses GDI BitBlt internally but is optimised and profiled to be faster than raw Python-level win32gui calls.
- **Multi-monitor support:** mss natively handles multi-monitor setups via the `monitor` dict with `top/left/width/height` keys, including monitors at negative coordinates.
- **Simple API:** `with mss.mss() as sct: sct.grab(monitor)` — minimal setup.

## Consequences

**Positive:**
- No intermediate PIL/numpy conversion step — `tobytes()` feeds directly to ffmpeg
- Consistent behaviour across Windows versions in scope (7–11)
- Handles monitors at non-zero origin (multi-monitor configurations)

**Negative:**
- mss uses GDI BitBlt — it **cannot capture** GPU-exclusive fullscreen DirectX applications (games running in exclusive fullscreen mode show a black frame)
- Not hardware-accelerated — CPU-intensive at high resolutions or FPS
- mss is not Windows-specific but the rest of the app is; the cross-platform benefit is unused

## Alternatives Considered

- **DXGI Desktop Duplication:** Hardware-accelerated, can capture exclusive fullscreen games. Requires win32 COM setup and is complex to implement in Python (no mature pip-installable wrapper at time of decision). Worth revisiting if exclusive fullscreen capture becomes a requirement.
- **PIL ImageGrab:** Returns a PIL Image, requiring an extra numpy conversion step. Slower than mss. Rejected.
- **win32gui BitBlt directly:** More verbose than mss with no performance advantage. Rejected.
