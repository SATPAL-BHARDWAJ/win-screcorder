# ADR-006: WAV File Path Handoff via Private Attribute

**Status:** Accepted (technical debt)  
**Date:** 2026-05-17  
**Affects:** [F-004](../features/F-004-audio-capture.md)

---

## Context

After `AudioCaptureThread` stops and its WAV file is finalized, `Encoder` needs to know the path to that WAV file so it can run the audio mux pass. The handoff must happen after the audio thread has fully stopped (WAV closed) but before `Encoder.stop()` is called.

Options for handoff:
- **Return value from `thread.stop()`** — but `QThread.stop()` convention returns None
- **Qt signal** — `AudioCaptureThread` emits `finished(wav_path: str)` signal
- **Public property** — `audio_thread.wav_path` read by toolbar after join
- **Direct private attribute assignment** — `encoder._wav_path = audio_thread.temp_wav_path`
- **Shared state object** — a dict or dataclass passed to both objects at construction

## Decision

`toolbar._on_stop()` reads `audio_thread.temp_wav_path` after `audio_thread.wait(3000)`, then sets `encoder._wav_path = temp_wav_path` directly. Both are accessed on the main thread after the audio thread is joined, so there is no race condition.

See `ui/toolbar.py` — `_on_stop()`.

## Rationale

- **Simplest implementation** at the time of writing — the recording lifecycle is managed entirely in `toolbar._on_stop()`, which already holds references to both objects
- **No race condition** — both accesses happen on the main thread after `audio_thread.wait()` confirms the thread has stopped and the WAV is finalised
- **Deferred complexity** — a Qt signal would require `AudioCaptureThread` to know about `Encoder`, or the toolbar to connect them, adding structural coupling in the other direction

## Consequences

**Positive:**
- Zero boilerplate; handoff is a single line in `_on_stop()`
- No threading issues (main-thread only, post-join)

**Negative:**
- Tight coupling: `toolbar.py` directly accesses `audio_thread.temp_wav_path` (a "public enough" attribute) and `encoder._wav_path` (a private attribute) — breaks encapsulation (KI-003)
- If `AudioCaptureThread` is refactored and `temp_wav_path` is renamed, the link silently breaks (no type checking)
- `encoder._wav_path` is a private attribute (`_`-prefixed) being set externally — contrary to Python conventions

## Remediation (future)

Replace with one of:
1. A `finished = pyqtSignal(str)` on `AudioCaptureThread` that toolbar connects to `encoder` setter at construction
2. A public `encoder.set_audio_path(path: str)` method called by toolbar
3. A `RecordingSession` dataclass holding both thread references and the WAV path, owned by toolbar

Option 2 is the smallest change.
