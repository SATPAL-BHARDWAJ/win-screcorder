# ADR-002: Use ffmpeg Subprocess for Video Encoding

**Status:** Accepted  
**Date:** 2026-05-17  
**Affects:** [F-001](../features/F-001-fullscreen-recording.md), [F-002](../features/F-002-region-recording.md), [F-003](../features/F-003-window-recording.md), [F-004](../features/F-004-audio-capture.md)

---

## Context

ScRecorder needs to encode a stream of raw BGR24 screen-capture frames (numpy arrays) and a PCM WAV audio file into an H.264 + AAC MP4 file in real-time. Options considered:

- **imageio / moviepy** — Python libraries wrapping ffmpeg
- **opencv-python VideoWriter** — OpenCV's built-in video writer
- **Direct libav/libavcodec Python bindings** (av, PyAV)
- **ffmpeg subprocess** — pipe raw frames to ffmpeg stdin

## Decision

Pipe raw BGR24 numpy frames to an ffmpeg subprocess via stdin. A second ffmpeg invocation muxes the audio WAV into the final MP4 after recording stops.

See `recorder/encoder.py` — `Encoder.start()`, `Encoder._feed_loop()`, `Encoder._mux_audio()`.

## Rationale

- **Performance:** ffmpeg's C-level encoder runs outside the Python GIL, maximising encode throughput. `libx264 -preset ultrafast` is specifically designed for real-time encoding.
- **Full feature set:** ffmpeg supports every codec, container, and filter without additional Python dependencies.
- **Simplicity of integration:** Piping BGR24 bytes to stdin requires ~5 lines of subprocess setup.
- **No re-encode on mux:** The two-pass approach (video-only then mux) lets the audio pass use `-c:v copy` — fast and lossless for the video stream.
- **Bundling:** A static ffmpeg.exe can be bundled in the PyInstaller exe, giving users a zero-install experience.

## Consequences

**Positive:**
- Near-optimal real-time encoding performance
- Full codec and container flexibility with no Python library updates needed
- Two-pass approach keeps mux fast

**Negative:**
- ffmpeg errors are written to stderr, which is not currently captured or surfaced to the UI (KI-004) — encoding failures are silent
- An external binary must be shipped with the exe (~200MB addition to distribution size)
- The "two-pass" here is not traditional CBR two-pass; it is video-only then audio-mux

## Alternatives Considered

- **imageio/moviepy:** Higher-level abstractions over ffmpeg, but add indirect dependencies and less control over real-time streaming. Rejected.
- **OpenCV VideoWriter:** Does not support audio; would require a separate audio library. Rejected.
- **PyAV:** Direct Python bindings to libav. Good performance, but complex API for real-time streaming and adds a large compiled dependency. May be worth revisiting if ffmpeg subprocess approach proves limiting.
