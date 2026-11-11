"""Fixed PCM relay and optional, bounded, one-way visualization packets.

Input/output is s16 native-endian, stereo, 48000 Hz, as emitted by mpv PCM.
The optional Unix datagram receiver never controls or backpressures playback.
Output goes to the protected FIFO, whose PipeWire reader never applies
backpressure; the relay therefore paces itself to real time (bounded lead).
"""

import os
import socket
import struct
import threading
import time

MAGIC = b"NMRP1\0"
HEADER = struct.Struct(">6sQ")
MAX_PAYLOAD = 4096
MAX_PACKET = HEADER.size + MAX_PAYLOAD
FRAME_BYTES = 4
RATE = 48000
LEAD_FRAMES = RATE // 5  # at most 200 ms ahead of real time
TAP_PATH = "/run/tap/pcm.sock"


def decode_packet(packet):
    if not HEADER.size < len(packet) <= MAX_PACKET:
        raise ValueError("Invalid PCM packet size.")
    magic, sequence = HEADER.unpack_from(packet)
    payload = packet[HEADER.size :]
    if magic != MAGIC or len(payload) % FRAME_BYTES:
        raise ValueError("Invalid PCM packet format.")
    return sequence, payload


def apply_process_limits():
    import resource

    for name, maximum in (
        (resource.RLIMIT_AS, 128 * 1024 * 1024),
        (resource.RLIMIT_NPROC, 0),
    ):
        soft, hard = resource.getrlimit(name)
        limit = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (limit, limit))


def relay(clock=time.monotonic, sleep=time.sleep):
    sequence = 0
    pending = b""
    start = None
    sent = 0.0
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as tap:
        tap.setblocking(False)
        while True:
            chunk = os.read(0, MAX_PAYLOAD)
            if not chunk:
                if pending:
                    raise ValueError("Incomplete PCM frame.")
                return
            # Real-time pacing: functional only, not a security bound. After a
            # stall the credit is dropped, so there is never a catch-up burst.
            now = clock()
            if start is None:
                start = now
            due = (now - start) * RATE
            if sent < due:
                start = now - sent / RATE
                due = sent
            frames = len(chunk) / FRAME_BYTES
            excess = sent + frames - due - LEAD_FRAMES
            if excess > 0:
                sleep(excess / RATE)
            sent += frames
            remaining = memoryview(chunk)
            while remaining:
                written = os.write(1, remaining)
                if written <= 0:
                    raise OSError("Incomplete PCM output.")
                remaining = remaining[written:]
            pending += chunk
            complete = len(pending) - len(pending) % FRAME_BYTES
            if complete:
                packet = HEADER.pack(MAGIC, sequence) + pending[:complete]
                pending = pending[complete:]
                sequence += 1
                try:
                    tap.sendto(packet, TAP_PATH)
                except OSError:
                    # No receiver, full queue, or receiver failure: drop only
                    # this optional copy, never retry or buffer it in Python.
                    pass


class PcmTap:
    """Parent-side receiver; no Pulse, microphone, media or control capability."""

    def __init__(self, path):
        self.path = path
        self.closed = False
        self._lock = threading.Lock()
        self.sequence = None
        self.dropped = 0
        self.stale_dropped = 0
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        bound = False
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.socket.bind(str(path))
            bound = True
            os.chmod(path, 0o600)
        except Exception:
            self.socket.close()
            if bound:
                os.unlink(path)
            raise

    def _receive(self):
        sequence, payload = decode_packet(self.socket.recv(MAX_PACKET + 1))
        if self.sequence is not None:
            if sequence <= self.sequence:
                raise ValueError("Out-of-order PCM packet.")
            self.dropped += sequence - self.sequence - 1
        self.sequence = sequence
        return payload

    def read(self, timeout=1, *, latest=False):
        if not 0 < timeout <= 2:
            raise ValueError("Invalid PCM read timeout.")
        self.socket.settimeout(timeout)
        payload = self._receive()
        if latest:
            # Only the optional visualizer requests freshness over completeness.
            # No Python queue: replace one pending packet, at most 32 receives
            # per call, even if a sender floods the bounded kernel socket.
            self.socket.setblocking(False)
            try:
                for _ in range(31):
                    try:
                        payload = self._receive()
                    except BlockingIOError:
                        break
                    self.stale_dropped += 1
            finally:
                self.socket.settimeout(timeout)
        return payload

    def close(self):
        with self._lock:
            if not self.closed:
                self.closed = True
                self.socket.close()
                try:
                    os.unlink(self.path)
                except FileNotFoundError:
                    pass

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()


def main():
    import sys

    try:
        apply_process_limits()
        if sys.argv[1:]:
            raise ValueError("Invalid PCM relay arguments.")
        relay()
        return 0
    except Exception:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
