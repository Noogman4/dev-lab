"""Bounds and accounting of the finite prototype performance measurement."""

import struct

import pytest

from projectm_pixel_benchmark import (
    END,
    MAGIC,
    TimedDecoder,
    capture_source,
    distribution,
    slots,
)
from projectm_pixel_protocol import CHUNK, FRAME_BYTES


def feed(decoder, data):
    frames = []
    for offset in range(0, len(data), CHUNK):
        frames.extend(decoder.feed(data[offset : offset + CHUNK]))
    return frames


def record(sequence, stamp):
    return struct.pack(">IQ", sequence, stamp) + b"x" * FRAME_BYTES


@pytest.mark.parametrize("fps", [0, 1, 25, 120, True, "30", None])
def test_only_fixed_trusted_profiles(fps):
    with pytest.raises(ValueError):
        capture_source(fps)


@pytest.mark.parametrize("fps", [30, 60])
def test_source_has_absolute_pacing_and_finite_limits(fps):
    source = capture_source(fps)
    assert f"frame<{slots(fps)}" in source
    assert "TIMER_ABSTIME" in source and "continue;" in source
    assert "RLIMIT_CPU,45" in source
    assert "RLIMIT_AS,512ULL*1024*1024" in source
    assert "RLIMIT_NOFILE,64" in source
    assert "NMPB01" in source and "NMPX01" not in source
    assert "nanosleep(&delay" not in source


def test_fragmented_stream_accepts_skipped_slots_and_requires_end():
    decoder = TimedDecoder(30)
    assert len(feed(decoder, MAGIC + record(0, 10) + record(3, 20))) == 2
    with pytest.raises(ValueError):
        decoder.finish()
    feed(decoder, struct.pack(">IQ", END, 0))
    decoder.finish()
    assert decoder.count == 2 and decoder.last == 3
    assert decoder.peak <= FRAME_BYTES + 12 + CHUNK
    with pytest.raises(ValueError):
        decoder.feed(b"extra")


@pytest.mark.parametrize("sequence,stamp", [(0, 20), (1, 10), (1, 0), (900, 20)])
def test_duplicate_order_timestamp_and_slot_limits(sequence, stamp):
    decoder = TimedDecoder(30)
    feed(decoder, MAGIC + record(0, 10))
    with pytest.raises(ValueError):
        feed(decoder, record(sequence, stamp))


@pytest.mark.parametrize("data", [b"bad", MAGIC + struct.pack(">IQ", END, 0)])
def test_signature_and_empty_terminal_fail(data):
    with pytest.raises(ValueError):
        feed(TimedDecoder(60), data)


def test_deadline_on_stalled_reader():
    import subprocess
    import sys
    from projectm_pixel_benchmark import collect_timed

    child = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            "import time;time.sleep(5)",
        ],
        stdout=subprocess.PIPE,
    )
    try:
        with pytest.raises(TimeoutError):
            collect_timed(child, lambda _: None, fps=30, timeout=0.05)
    finally:
        child.kill()
        child.wait(timeout=2)
        child.stdout.close()


def test_distribution_uses_documented_nearest_lower_sample():
    assert distribution([]) is None
    assert distribution([5, 1, 4, 3, 2]) == {"p50": 3, "p95": 4, "max": 5}
