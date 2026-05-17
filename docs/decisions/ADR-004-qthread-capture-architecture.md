# ADR-004: QThread with Bounded Queues and Silent Frame Drops

**Status:** Accepted  
**Date:** 2026-05-17  
**Affects:** [F-001](../features/F-001-fullscreen-recording.md), [F-004](../features/F-004-audio-capture.md), [F-005](../features/F-005-pause-resume.md)

---

## Context

Screen capture and audio capture must not block the Qt main event loop (which drives the UI). The encoder feeds an ffmpeg subprocess, which may be slower than the capture rate under CPU load. A coordination mechanism is needed.

Options for threading model:
- **Python `threading.Thread`** with stdlib queues
- **Qt `QThread`** with Qt signals/slots
- **`asyncio`** coroutines
- **`concurrent.futures.ThreadPoolExecutor`**

Options for backpressure / overflow:
- **Blocking put:** Capture thread sleeps when queue is full (backpressure)
- **Non-blocking put with drop:** Capture thread skips frame if queue is full
- **Unbounded queue:** Always enqueue; risk of unbounded memory growth

## Decision

Each capture source (`ScreenCaptureThread`, `AudioCaptureThread`) runs as a `QThread`. A shared `queue.Queue` with `maxsize` connects each capture thread to the encoder. Overflow uses non-blocking `put_nowait()` — frames are silently dropped.

Queue sizes: `frame_queue` maxsize=60, `audio_queue` maxsize=200.

## Rationale

- **QThread over threading.Thread:** Qt signals work correctly only from QThread subclasses; using QThread allows future UI feedback (signals) from capture threads without refactoring. `wait(timeout_ms)` is also more ergonomic than `threading.Thread.join(timeout=sec)`.
- **Non-blocking drop over backpressure:** If the encoder falls behind (slow CPU, large frame), backpressure would cause the capture thread to sleep, making the capture timing unpredictable. Silent drops are preferable to stalling — the video may skip frames but the overall recording continues.
- **Bounded queue over unbounded:** An unbounded queue grows without limit if the encoder is consistently slower than capture (e.g., capturing 4K at 60fps on a slow machine). Bounded queues cap memory usage.
- **maxsize=60 for frames:** At 30fps, this is 2 seconds of buffering — enough to absorb short encoder stalls while being conservative on memory (each 1080p frame ≈ 6MB → 360MB max for frame queue).

## Consequences

**Positive:**
- Qt signals/slots available for future UI feedback from capture threads
- Bounded memory regardless of encoder speed
- Simple flag-based pause (`_paused` bool checked each iteration)

**Negative:**
- Dropped frames are invisible to the user (KI-005) — the output video may have stutters with no indication
- Queue sizes (60, 200) are empirically chosen, not tuned for worst-case hardware
- `audio_queue` is populated but never consumed by the encoder (dead code) — WAV file path is used instead; this wastes memory for each audio chunk

## Alternatives Considered

- **Blocking put (backpressure):** Guarantees no drops but risks desync between audio and video capture timing. Rejected for real-time capture.
- **Unbounded queue:** Simplest implementation but risks OOM on slow machines. Rejected.
- **threading.Thread:** No Qt signal integration; harder to join with timeout. Rejected.
