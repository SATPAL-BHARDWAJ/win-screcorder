# ADR-005: WASAPI Loopback Device Detection by Name Substring Match

**Status:** Accepted (with known fragility)  
**Date:** 2026-05-17  
**Affects:** [F-004](../features/F-004-audio-capture.md)

---

## Context

To capture system audio output (what the user hears), ScRecorder needs to open a WASAPI loopback input stream. PyAudio does not expose a `is_loopback` flag — it only provides device names and host API types. The loopback device must be identified programmatically from the list of available PyAudio devices.

Common WASAPI loopback device names across Windows versions and drivers:
- English Windows 10/11: "Stereo Mix (Realtek...)" or "WASAPI Loopback"
- Some systems: "What U Hear"
- Virtual audio cables: "VB-Audio Virtual Cable"

## Decision

In `AudioCaptureThread._find_loopback_device(pa)`, iterate all PyAudio devices and return the index of the first device whose name contains any of `["loopback", "stereo mix", "what u hear"]` (case-insensitive) and has input channels. Fall back to `None` (PyAudio default input device) if no match is found.

See `recorder/audio_capture.py` — `_find_loopback_device()`.

## Rationale

- **No portable PyAudio API for loopback enumeration** — PyAudio does not expose WASAPI loopback flags. The Windows Core Audio COM API (`IAudioClient` with `AUDCLNT_STREAMFLAGS_LOOPBACK`) would require pywin32 COM interop, which is significantly more complex.
- **Name-based detection is the de facto community approach** for Python WASAPI loopback — the same pattern is used in OBS Python plugins, Soundcard, and AudioStream libraries.
- **Fallback to default input** ensures the app always produces _some_ audio rather than failing silently — for most users on English Windows, the loopback device will be found.

## Consequences

**Positive:**
- Works on the majority of English Windows 10/11 systems out of the box
- Simple implementation, no COM interop

**Negative:**
- **Fails on non-English Windows** where device names are localised (e.g., German "Stereo Mixer", Japanese driver names) (KI-002)
- Falls back to microphone input silently — users may not realise they're recording their mic instead of system audio
- Custom virtual audio devices (VB-Cable, Voicemeeter) use different names not in the detection list
- Device name match is a fragile heuristic; future Windows updates or driver changes could break it

## Alternatives Considered

- **Windows Core Audio COM API via pywin32:** Proper `AUDCLNT_STREAMFLAGS_LOOPBACK` enumeration. More reliable but requires complex COM setup. Worth revisiting for v2.0 if non-English support is required.
- **soundcard library:** Abstracts loopback detection, but adds another dependency with its own device enumeration quirks.
- **Hardcode device index in config:** Allows user to specify the exact device index. Fragile across system changes but could be a user-facing workaround exposed in config.

## Future Mitigation

If non-English support becomes a requirement, replace `_find_loopback_device()` with a Windows Core Audio COM enumeration via `pywin32.comtypes` or the `soundcard` library. Expose device selection as a config key for advanced users.
