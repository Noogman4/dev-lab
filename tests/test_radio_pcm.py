"""Bounded PCM copying and lifecycle, without a host audio capture service."""

from pathlib import Path
from types import SimpleNamespace
import os
import socket

import pytest

from netmon.core import radio_pcm as pcm
from netmon.core import radio_sandbox as sandbox
from test_radio_sandbox import Child, FakeOutput


def run_relay(monkeypatch, chunks, *, blocked=False):
    source = iter([*chunks, b""])
    output = bytearray()
    packets = []

    class Sender:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def setblocking(self, value):
            assert value is False

        def sendto(self, packet, target):
            assert target == pcm.TAP_PATH
            packets.append(packet)
            if blocked:
                raise BlockingIOError("optional queue full")

    def read(descriptor, maximum):
        assert descriptor == 0 and maximum == pcm.MAX_PAYLOAD
        return next(source)

    def write(descriptor, data):
        assert descriptor == 1
        count = min(7, len(data))
        output.extend(data[:count])
        return count

    with monkeypatch.context() as patch:
        patch.setattr(pcm.socket, "socket", lambda *_: Sender())
        patch.setattr(pcm.os, "read", read)
        patch.setattr(pcm.os, "write", write)
        pcm.relay()
    return bytes(output), packets


@pytest.mark.parametrize("blocked", [False, True])
def test_fragmented_pcm_is_exact_and_slow_optional_consumer_never_blocks(
    monkeypatch, blocked
):
    chunks = [b"a", b"bc", b"defgh", bytes(range(256)) * 16]
    output, packets = run_relay(monkeypatch, chunks, blocked=blocked)
    assert output == b"".join(chunks)
    decoded = [pcm.decode_packet(packet) for packet in packets]
    assert [sequence for sequence, _ in decoded] == list(range(len(decoded)))
    assert b"".join(payload for _, payload in decoded) == output
    assert all(len(packet) <= pcm.MAX_PACKET for packet in packets)


@pytest.mark.parametrize(
    "packet",
    [
        b"",
        pcm.HEADER.pack(pcm.MAGIC, 1),
        b"bad" * 20,
        pcm.HEADER.pack(pcm.MAGIC, 1) + b"a",
        pcm.HEADER.pack(pcm.MAGIC, 1) + b"a" * (pcm.MAX_PAYLOAD + 4),
    ],
)
def test_invalid_packets_are_rejected(packet):
    with pytest.raises(ValueError):
        pcm.decode_packet(packet)


def test_partial_pcm_frame_is_not_announced_as_complete(monkeypatch):
    with pytest.raises(ValueError, match="Incomplete PCM frame"):
        run_relay(monkeypatch, [b"12345"])


def test_main_output_failure_is_not_hidden(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(pcm.os, "write", lambda *_: 0)
        patch.setattr(pcm.os, "read", lambda *_: b"1234")
        with pytest.raises(OSError, match="Incomplete PCM output"):
            pcm.relay()


def test_receiver_counts_gaps_rejects_replays_and_bounds_packets(tmp_path):
    path = tmp_path / "pcm.sock"
    with (
        pcm.PcmTap(path) as tap,
        socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sender,
    ):
        assert os.stat(path).st_mode & 0o777 == 0o600
        for sequence in [10, 13]:
            sender.sendto(pcm.HEADER.pack(pcm.MAGIC, sequence) + b"1234", str(path))
            assert tap.read() == b"1234"
        assert tap.dropped == 2
        sender.sendto(pcm.HEADER.pack(pcm.MAGIC, 13) + b"1234", str(path))
        with pytest.raises(ValueError, match="Out-of-order"):
            tap.read()
        sender.sendto(pcm.HEADER.pack(pcm.MAGIC, 14) + b"x" * 10000, str(path))
        with pytest.raises(ValueError):
            tap.read()
    assert tap.closed and not path.exists()
    tap.close()


def test_receiver_deadline_and_existing_path_are_preserved(tmp_path):
    path = tmp_path / "pcm.sock"
    with pcm.PcmTap(path) as tap:
        with pytest.raises(socket.timeout):
            tap.read(0.01)
        with pytest.raises(ValueError):
            tap.read(0)
    path.write_text("existing")
    with pytest.raises(OSError):
        pcm.PcmTap(path)
    assert path.read_text() == "existing"


@pytest.mark.parametrize("latest", [False, True])
def test_receiver_freshness_is_opt_in_and_counts_discarded_packets(tmp_path, latest):
    path = tmp_path / "pcm.sock"
    with (
        pcm.PcmTap(path) as tap,
        socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sender,
    ):
        for sequence in range(4):
            sender.sendto(
                pcm.HEADER.pack(pcm.MAGIC, sequence) + bytes([sequence]) * 4, str(path)
            )
        assert tap.read(0.01, latest=latest) == bytes([3 if latest else 0]) * 4
        assert tap.stale_dropped == (3 if latest else 0)
        assert tap.dropped == 0
        if not latest:
            assert tap.read() == b"\1" * 4
        else:
            with pytest.raises(socket.timeout):
                tap.read(0.01, latest=True)


def test_freshness_drain_still_rejects_invalid_queued_packet(tmp_path):
    path = tmp_path / "pcm.sock"
    with (
        pcm.PcmTap(path) as tap,
        socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sender,
    ):
        sender.sendto(pcm.HEADER.pack(pcm.MAGIC, 0) + b"1234", str(path))
        sender.sendto(b"invalid", str(path))
        with pytest.raises(ValueError):
            tap.read(0.01, latest=True)
        assert tap.socket.gettimeout() == 0.01


def test_freshness_drain_has_fixed_receive_budget():
    class Flood:
        sequence = 0
        timeout = None

        def settimeout(self, value):
            self.timeout = value

        def setblocking(self, value):
            assert value is False
            self.timeout = 0.0

        def recv(self, maximum):
            assert maximum == pcm.MAX_PACKET + 1
            self.sequence += 1
            return pcm.HEADER.pack(pcm.MAGIC, self.sequence) + b"1234"

    tap = object.__new__(pcm.PcmTap)
    tap.socket = Flood()
    tap.sequence = None
    tap.dropped = tap.stale_dropped = 0
    assert tap.read(0.1, latest=True) == b"1234"
    assert tap.socket.sequence == 32 and tap.stale_dropped == 31
    assert tap.socket.timeout == 0.1 and tap.dropped == 0


def owner(tmp_path, decoder=None, relay=None, output=None, source=None):
    (tmp_path / "tap").mkdir()
    cleaned = []
    process = sandbox.SandboxProcess(
        decoder or Child(),
        SimpleNamespace(name=str(tmp_path), cleanup=lambda: cleaned.append(True)),
        output,
        source,
        relay or Child(),
    )
    return process, cleaned


def test_owner_allows_one_receiver_and_cleans_it_at_end(tmp_path):
    decoder, relay = Child(), Child()
    process, cleaned = owner(tmp_path, decoder, relay)
    first = process.open_pcm_tap()
    with pytest.raises(sandbox.RadioSandboxError, match="bereits"):
        process.open_pcm_tap()
    first.close()
    second = process.open_pcm_tap()
    first.close()
    assert second.path.exists()
    decoder.result = relay.result = 0
    assert process.poll() == 0
    assert second.closed and not second.path.exists() and cleaned == [True]
    with pytest.raises(sandbox.RadioSandboxError):
        process.open_pcm_tap()


def test_relay_loss_stops_decoder_output_and_source(tmp_path):
    decoder, relay, output, source = Child(), Child(2), FakeOutput(), Child()
    process, cleaned = owner(tmp_path, decoder, relay, output, source)
    assert process.wait(0.1) == 2
    assert decoder.signals == source.signals == ["kill"]
    assert output.events == ["close"]
    assert cleaned == [True]


@pytest.mark.parametrize("stop", ["terminate", "kill"])
def test_stop_ends_all_three_processes_and_closes_receiver(tmp_path, stop):
    decoder, relay, output, source = Child(), Child(), FakeOutput(), Child()
    process, cleaned = owner(tmp_path, decoder, relay, output, source)
    tap = process.open_pcm_tap()
    getattr(process, stop)()
    assert output.events == ["silence"]
    assert process.wait(0.1) != 0
    assert decoder.signals == relay.signals == source.signals == [stop]
    assert tap.closed and cleaned == [True]


def test_relay_drain_has_finite_deadline(tmp_path, monkeypatch):
    relay = Child()
    process, cleaned = owner(tmp_path, Child(0), relay, FakeOutput())
    clock = [100.0]
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])
    assert process.poll() is None
    clock[0] += 6
    assert process.poll() != 0
    assert relay.signals == ["kill"] and cleaned == [True]


def test_pcm_grants_only_stdio_runtime_and_readonly_tap_directory(tmp_path):
    command = sandbox._pcm_command(tmp_path, Path("/usr/lib/python3.12"), ())
    assert "--unshare-net" in command and "--clearenv" in command
    assert command[command.index("--") + 1 :] == [
        str(sandbox.PYTHON),
        "-I",
        "-S",
        "-B",
        "-X",
        "pycache_prefix=/nonexistent",
        "/run/pcm.py",
    ]
    assert "--bind" not in command
    assert str(tmp_path / "tap") in command
    assert not {
        "/run/control",
        "/run/audio/pulse",
        "/run/request.json",
        "/media/selected",
    } & set(command)
    assert "PULSE_SERVER" not in command


def paced(chunks, arrivals):
    """Relay with simulated time: reads wait for arrival, sleeps advance time."""
    source = iter([*chunks, b""])
    arrival = iter([*arrivals, None])
    now = [0.0]
    sleeps = []

    def read(_fd, _n):
        at = next(arrival)
        if at is not None:
            now[0] = max(now[0], at)
        return next(source)

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    class Sender:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def setblocking(self, value):
            pass

        def sendto(self, packet, target):
            pass

    import unittest.mock as mock

    with (
        mock.patch.object(pcm.socket, "socket", lambda *_: Sender()),
        mock.patch.object(pcm.os, "read", read),
        mock.patch.object(pcm.os, "write", lambda _fd, data: len(data)),
    ):
        pcm.relay(clock=lambda: now[0], sleep=sleep)
    return now[0], sleeps


CHUNK_FRAMES = pcm.MAX_PAYLOAD // pcm.FRAME_BYTES


def test_relay_paces_fast_input_to_real_time_plus_lead():
    chunk = bytes(pcm.MAX_PAYLOAD)
    end, sleeps = paced([chunk] * 30, [0.0] * 30)
    # 30 chunks arriving at once leave after real time minus the fixed lead.
    expected = (30 * CHUNK_FRAMES - pcm.LEAD_FRAMES) / pcm.RATE
    assert abs(end - expected) < 1e-9
    assert all(s <= CHUNK_FRAMES / pcm.RATE + 1e-9 for s in sleeps)


def test_relay_never_bursts_to_catch_up_after_a_stall():
    chunk = bytes(pcm.MAX_PAYLOAD)
    step = CHUNK_FRAMES / pcm.RATE
    arrivals = [i * step for i in range(10)] + [10 * step + 5.0] * 20
    end, _sleeps = paced([chunk] * 30, arrivals)
    # Without the credit drop the 5 s stall would let the burst pass at once.
    expected = 10 * step + 5.0 + (20 * CHUNK_FRAMES - pcm.LEAD_FRAMES) / pcm.RATE
    assert abs(end - expected) < 1e-9


def test_relay_live_input_is_not_delayed():
    chunk = bytes(pcm.MAX_PAYLOAD)
    step = CHUNK_FRAMES / pcm.RATE
    end, sleeps = paced([chunk] * 50, [i * step for i in range(50)])
    assert sleeps == [] and abs(end - 49 * step) < 1e-9
