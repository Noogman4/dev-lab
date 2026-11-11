"""Bounded fixed-PCM feeding and fail-closed native artifact selection."""

import json
import os
from pathlib import Path
import socket
from types import SimpleNamespace

import pytest

from netmon.core import projectm_pcm as pcm, projectm_native as native
from netmon.core import radio_sandbox as sandbox


class Tap:
    closed = False

    def __init__(self, packets):
        self.packets = iter(packets)

    def read(self, timeout, *, latest=False):
        try:
            return next(self.packets)
        except StopIteration:
            self.closed = True
            raise socket.timeout()

    def close(self):
        self.closed = True


def feed(packets):
    read, write = os.pipe()
    handle = os.fdopen(write, "wb", buffering=0)
    pcm.bounded_pipe(handle)
    value = pcm.PcmFeed(Tap(packets), handle)
    assert value.done.wait(2)
    value.stop()
    with os.fdopen(read, "rb") as incoming:
        return value, incoming.read()


def test_feeder_forwards_only_fixed_aligned_packet():
    session, result = feed([b"\0" * 4096])
    assert result == b"\0" * 4096 and session.max_pending == 4096
    assert session.reason == "source-ended"


@pytest.mark.parametrize("packet", [b"", b"abc", b"\0" * 4100])
def test_feeder_rejects_malformed_packet(packet):
    session, result = feed([packet])
    assert result == b"" and session.reason == "input-error"


def test_full_pipe_drops_packets_without_growing_queue():
    session, result = feed([b"\0" * 4096] * 16)
    assert session.dropped > 0 and len(result) <= 16384
    assert session.max_pending == 4096


@pytest.mark.parametrize("jitter", [False, True])
@pytest.mark.parametrize("oversleep", [0.0, 0.0005, 0.002, 0.008])
def test_rate_pacing_preserves_packets_and_byte_envelope(
    monkeypatch, jitter, oversleep
):
    clock = [0.0]
    writes = []
    waits = []

    class Cancel:
        def is_set(self):
            return False

        def wait(self, delay):
            waits.append(delay)
            clock[0] += delay + oversleep
            return False

    class Source(Tap):
        reads = 0

        def read(self, timeout, *, latest=False):
            assert latest is True
            if jitter:
                # Alternate just early/late at the nominal 48 kHz stereo rate.
                clock[0] += 4096 / 192000 + (0.00002 if self.reads % 2 else -0.00002)
            self.reads += 1
            return super().read(timeout, latest=latest)

    def write(fd, packet):
        writes.append((clock[0], bytes(packet)))
        return len(packet)

    packets = [bytes([i]) * 4096 for i in range(100)]
    value = object.__new__(pcm.PcmFeed)
    value.tap = Source(packets)
    value.writer = SimpleNamespace(fileno=lambda: 123, close=lambda: None)
    value.cancelled = Cancel()
    value.done = SimpleNamespace(set=lambda: None)
    value.last_forward = 0.0
    value.forwarded = value.dropped = value.rate_dropped = value.max_pending = 0
    monkeypatch.setattr(pcm, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(pcm, "os", SimpleNamespace(write=write))
    value.run()
    assert b"".join(packet for _, packet in writes) == b"".join(packets)
    assert value.forwarded == 409600 and value.rate_dropped == value.dropped == 0
    assert value.max_pending == 4096 and value.reason == "source-ended"
    assert waits and max(waits) <= 4096 / 192000 + 1e-6
    total = 0
    for index, (stamp, packet) in enumerate(writes):
        total += len(packet)
        assert len(packet) <= 2048 and len(packet) % 4 == 0
        assert total <= 4096 + stamp * 192000 + 0.001
        # Also preserve the burst bound over every subinterval, not just since start.
        interval_bytes = 0
        for end, data in writes[index:]:
            interval_bytes += len(data)
            assert interval_bytes <= 4096 + (end - stamp) * 192000 + 0.001
    if not jitter:
        assert writes[-1][0] <= (409600 - 4096) / 192000 + oversleep + 1e-6


@pytest.mark.parametrize("cancel,reason", [(True, "cancelled"), (False, "pcm-timeout")])
def test_rate_wait_cancel_or_long_pause_never_writes_stale_packet(
    monkeypatch, cancel, reason
):
    clock = [0.0]
    writes, closed = [], []
    value = object.__new__(pcm.PcmFeed)
    value.tap = Tap([b"\0" * 4096] * 2)
    value.writer = SimpleNamespace(
        fileno=lambda: 123, close=lambda: closed.append(True)
    )

    def wait(delay):
        clock[0] += 6  # Simulate a scheduling pause while waiting for credit.
        return cancel

    value.cancelled = SimpleNamespace(is_set=lambda: False, wait=wait)
    value.done = SimpleNamespace(set=lambda: None)
    value.last_forward = 0.0
    value.forwarded = value.dropped = value.rate_dropped = value.max_pending = 0
    monkeypatch.setattr(pcm, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(
        pcm,
        "os",
        SimpleNamespace(write=lambda fd, packet: writes.append(packet) or len(packet)),
    )
    value.run()
    assert b"".join(writes) == b"\0" * 4096
    assert closed == [True] and value.reason == reason


def test_short_scheduler_stall_discards_pending_audio_without_widening_budget(
    monkeypatch,
):
    clock, writes = [0.0], []
    value = object.__new__(pcm.PcmFeed)
    value.tap = Tap([bytes([i]) * 4096 for i in range(4)])
    value.writer = SimpleNamespace(fileno=lambda: 123, close=lambda: None)
    pauses = [0.2, 0.0]

    def wait(delay):
        clock[0] += delay + (pauses.pop(0) if pauses else 0.0)
        return False

    value.cancelled = SimpleNamespace(is_set=lambda: False, wait=wait)
    value.done = SimpleNamespace(set=lambda: None)
    value.last_forward = 0.0
    value.forwarded = value.dropped = value.rate_dropped = value.max_pending = 0
    value.stale_dropped = 0
    monkeypatch.setattr(pcm, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(
        pcm,
        "os",
        SimpleNamespace(write=lambda fd, data: writes.append(bytes(data)) or len(data)),
    )
    value.run()
    assert b"".join(writes) == b"\0" * 4096 + b"\3" * 4096
    assert value.stale_dropped == 2 and value.reason == "source-ended"


def test_short_atomic_pcm_write_fails_closed(monkeypatch):
    real_write = os.write
    monkeypatch.setattr(pcm.os, "write", lambda fd, data: real_write(fd, data[:4]))
    session, result = feed([b"a" * 4096])
    assert result == b"a" * 4 and session.reason == "input-error"


def test_converter_profile_has_no_audio_network_display_or_control_grants(tmp_path):
    command = pcm._command(tmp_path, (Path("/usr/lib/python3.12"), ()))
    assert "--unshare-net" in command and "--clearenv" in command
    assert not {"/run/audio/pulse", "/run/control", "/dev/snd", "/dev/dri", ":1"} & set(
        command
    )
    assert not any(x.startswith("PULSE_") for x in command)


def test_tap_borrowing_never_polls_or_signals_playback(tmp_path):
    (tmp_path / "tap").mkdir()

    class Process:
        def poll(self):
            pytest.fail("Borrower polled playback")

    playback = sandbox.SandboxProcess(
        Process(),
        SimpleNamespace(name=str(tmp_path), cleanup=lambda: None),
        pcm_process=object(),
    )
    tap = playback.open_pcm_tap()
    assert not tap.closed
    playback._cleanup()
    assert tap.closed
    with pytest.raises(sandbox.RadioSandboxError):
        playback.open_pcm_tap()


@pytest.fixture
def artifact(tmp_path, monkeypatch):
    source = tmp_path / "source"
    (source / "include").mkdir(parents=True)
    (source / "build").mkdir()
    (source / "pcm_renderer.cpp").write_text("fixture")
    (source / "include/projectM.hpp").write_text("fixture-header")
    binary = source / "build/pcm-renderer"
    binary.write_bytes(b"fixture-binary")
    binary.chmod(0o700)
    (tmp_path / "lib").mkdir()
    library = tmp_path / "lib/libprojectM.so.3"
    library.write_bytes(b"fixture-library")
    monkeypatch.setattr(native, "SOURCE", source)
    monkeypatch.setattr(native, "LIBRARY_SHA256", native.digest(library))
    record = {
        "schema": 1,
        "library_sha256": native.digest(library),
        "binary_sha256": native.digest(binary),
        "sources": {
            str(p.relative_to(source)): native.digest(p)
            for p in [source / "pcm_renderer.cpp", source / "include/projectM.hpp"]
        },
    }
    (source / "build/build.json").write_text(json.dumps(record))
    return source, tmp_path, binary


def test_matching_explicit_build_is_accepted(artifact):
    _, payload, binary = artifact
    assert native.artifact(payload) == binary


@pytest.mark.parametrize(
    "changed", ["binary", "library", "source", "metadata", "missing", "mode"]
)
def test_missing_or_stale_adapter_fails_without_fallback(artifact, changed):
    source, payload, binary = artifact
    if changed == "missing":
        binary.unlink()
    elif changed == "mode":
        binary.chmod(0o777)
    else:
        target = {
            "binary": binary,
            "library": payload / "lib/libprojectM.so.3",
            "source": source / "pcm_renderer.cpp",
            "metadata": source / "build/build.json",
        }[changed]
        target.write_text("changed")
    with pytest.raises(sandbox.RadioSandboxError):
        native.artifact(payload)
