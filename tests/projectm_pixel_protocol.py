"""Prototype-only fixed raw-pixel receiver; no image/container decoding."""

import os
import selectors
import struct
import time

WIDTH, HEIGHT = 640, 480
FRAME_BYTES = WIDTH * HEIGHT * 4
MAGIC = b"NMPX01\0"
FRAMES = 24
CHUNK = 65536


class FrameDecoder:
    def __init__(self, frames=FRAMES):
        if type(frames) is not int or not 1 <= frames <= FRAMES:
            raise ValueError("Invalid trusted frame budget")
        self.frames = frames
        self.count = 0
        self.buffer = bytearray()
        self.started = False
        self.peak = 0

    def feed(self, data):
        if not isinstance(data, bytes) or len(data) > CHUNK:
            raise ValueError("Invalid bounded pipe chunk")
        self.buffer.extend(data)
        self.peak = max(self.peak, len(self.buffer))
        if not self.started:
            prefix = bytes(self.buffer[: len(MAGIC)])
            if not MAGIC.startswith(prefix):
                raise ValueError("Invalid pixel signature")
            if len(self.buffer) < len(MAGIC):
                return []
            del self.buffer[: len(MAGIC)]
            self.started = True
        frames = []
        while self.count < self.frames and len(self.buffer) >= 4:
            if struct.unpack_from(">I", self.buffer)[0] != self.count:
                raise ValueError("Invalid pixel sequence")
            if len(self.buffer) < FRAME_BYTES + 4:
                break
            frames.append(bytes(self.buffer[4 : FRAME_BYTES + 4]))
            del self.buffer[: FRAME_BYTES + 4]
            self.count += 1
        if self.count == self.frames and self.buffer:
            raise ValueError("Trailing pixel data")
        if len(self.buffer) > FRAME_BYTES + 4:
            raise ValueError("Pixel buffer budget exceeded")
        return frames

    def finish(self):
        if not self.started or self.count != self.frames or self.buffer:
            raise ValueError("Truncated pixel stream")


def collect(process, on_frame, *, frames=FRAMES, timeout=8):
    """A finite probe stream with an absolute deadline and a bounded buffer.

    The caller owns and must reap the Popen, including on failure. Never poll a
    SandboxProcess or run a process waiter in a Tk callback.
    """
    decoder = FrameDecoder(frames)
    deadline = time.monotonic() + timeout
    with selectors.DefaultSelector() as selected:
        selected.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Pixel stream deadline")
            if not selected.select(min(remaining, 0.1)):
                continue
            data = os.read(process.stdout.fileno(), CHUNK)
            if not data:
                decoder.finish()
                return {"frames": decoder.count, "peak_buffer_bytes": decoder.peak}
            for frame in decoder.feed(data):
                on_frame(frame)
