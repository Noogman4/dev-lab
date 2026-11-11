"""Trusted rate gate: private FIFO/pipe I/O, no audio service or device."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from netmon.core import radio_sandbox as sandbox

RATE, BURST = 192_000, 38_400

# Always finite; only own stdin/stdout/stderr, no audio API or file access.
PRODUCER = """
import json, os, sys, time
mode = sys.argv[1]
info = {"stdout": os.readlink("/proc/self/fd/1"), "fds": []}
for name in os.listdir("/proc/self/fd"):
    try:
        os.fstat(int(name))
        info["fds"].append(int(name))
    except OSError:
        pass
def send(count):
    data = memoryview((bytes(range(256)) * ((count + 255) // 256))[:count])
    while data:
        data = data[os.write(1, data):]
try:
    if mode == "fast": send(384000)
    elif mode == "pause":
        send(38400)
        time.sleep(0.4)
        send(115200)
    elif mode == "idle": time.sleep(3)
    elif mode == "stop": send(384000)
    else: raise ValueError(mode)
except BrokenPipeError:
    pass
finally:
    os.write(2, (json.dumps(info) + "\\n").encode())
"""


@pytest.mark.parametrize("main_exit", ["return", "exception"])
def test_gate_does_not_keep_interpreter_alive_without_radio_stop(main_exit):
    script = """
import json, os, sys, threading
from netmon.core.radio_sandbox import _PcmOutputGate
source, source_write = os.pipe()
target_read, target = os.pipe()
ready = threading.Event()
def owner():
    gate = _PcmOutputGate(source, target)
    print(json.dumps({"gate_alive": gate._thread.is_alive()}), flush=True)
    ready.set()
    threading.Event().wait()
threading.Thread(target=owner, daemon=True).start()
assert ready.wait(2), "owner did not start the gate"
# No stop, close, EOF or cleanup: leave an idle live writer behind on purpose.
if sys.argv[1] == "exception":
    raise RuntimeError("synthetic main exit")
"""
    child = subprocess.Popen(
        [
            sys.executable,
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            script,
            main_exit,
        ],
        cwd=Path(__file__).resolve().parents[1],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    try:
        try:
            stdout, stderr = child.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            child.kill()
            stdout, stderr = child.communicate(timeout=1)
            pytest.fail(f"interpreter kept alive by gate: {stdout!r} {stderr!r}")
        assert json.loads(stdout) == {"gate_alive": True}
        assert child.returncode == (1 if main_exit == "exception" else 0)
        if main_exit == "exception":
            assert b"synthetic main exit" in stderr
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=1)
        child.stdout.close()
        child.stderr.close()


def test_output_budget_initial_burst_and_refill_cap():
    budget = sandbox._PcmOutputBudget(0)
    assert budget.available(0) == BURST
    budget.spend(BURST, 0)
    assert budget.available(0) == 0
    assert budget.available(0.1) == 19_200
    assert budget.available(100) == BURST
    with pytest.raises(ValueError):
        budget.spend(BURST + 1, 100)


def test_output_write_delay_buys_no_credit():
    budget = sandbox._PcmOutputBudget(0)
    budget.spend(4096, 1)
    assert budget.available(1) == BURST - 4096


@contextmanager
def private_gate(tmp_path, mode, fifo_inode=None):
    fifo = tmp_path / "output.pcm"
    os.mkfifo(fifo, 0o600)
    reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
    writer = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
    if fifo_inode is not None:
        fifo_inode.append(os.fstat(reader).st_ino)
    child = gate = None
    try:
        child = subprocess.Popen(
            [sys.executable, "-I", "-S", "-B", "-c", PRODUCER, mode],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
        )
        gate = sandbox._PcmOutputGate(child.stdout.fileno(), writer)
        child.stdout.close()
        child.stdout = None
        os.close(writer)
        writer = None
        yield gate, child, reader
    finally:
        if gate is not None:
            gate.close()
            assert gate.done.is_set() and not gate._thread.is_alive()
        if child is not None:
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=1)
            child.stderr.close()
        if writer is not None:
            os.close(writer)
        os.close(reader)


@pytest.mark.parametrize("mode,count", [("fast", 384_000), ("pause", 153_600)])
def test_gate_transfers_exact_bytes_with_external_rate_bound(
    monkeypatch, tmp_path, mode, count
):
    writes, read_sizes = [], []
    real_write, real_read = os.write, os.read
    fifo_inode = []

    def measured_write(fd, data):
        written = real_write(fd, data)
        if fifo_inode and os.fstat(fd).st_ino == fifo_inode[0]:
            writes.append((time.monotonic(), written))
        return written

    def measured_read(fd, maximum):
        if maximum == sandbox._PcmOutputGate.BLOCK:
            read_sizes.append(maximum)
        return real_read(fd, maximum)

    with monkeypatch.context() as patch:
        patch.setattr(os, "write", measured_write)
        patch.setattr(os, "read", measured_read)
        with private_gate(tmp_path, mode, fifo_inode) as (gate, child, reader):
            data = bytearray()
            end = time.monotonic() + 5
            while True:
                try:
                    chunk = real_read(reader, 8192)
                except BlockingIOError:
                    chunk = None
                if chunk:
                    data.extend(chunk)
                    assert len(data) <= count
                elif chunk == b"" and gate.done.is_set():
                    break
                assert time.monotonic() < end
                time.sleep(0.001)
            assert gate.error is None
            child.wait(timeout=1)
            audit = json.loads(child.stderr.read())
            assert audit["stdout"].startswith("pipe:[")
            assert sorted(audit["fds"]) == [0, 1, 2]
            assert data == (bytes(range(256)) * ((count + 255) // 256))[:count]
    assert read_sizes and max(read_sizes) <= 4096
    # Independent expectation: do not derive the acceptance bound from the gate.
    assert sum(n for _t, n in writes) == count
    for i, (first, _) in enumerate(writes):
        total = 0
        for last, n in writes[i:]:
            total += n
            assert total <= BURST + RATE * (last - first) + 1


@pytest.mark.parametrize("mode", ["stop", "idle"])
def test_gate_stop_cancels_backpressure_and_missing_input(tmp_path, mode):
    with private_gate(tmp_path, mode) as (gate, _child, _reader):
        time.sleep(0.1)
        assert not gate.done.is_set()
        started = time.monotonic()
        gate.request_stop()
        assert gate.done.wait(0.5)
        assert time.monotonic() - started < 0.5
        assert gate.error is None


def test_output_reader_loss_is_reported(tmp_path):
    source, write_source = os.pipe()
    target_read, target = os.pipe()
    gate = sandbox._PcmOutputGate(source, target)
    os.close(source)
    os.close(target)
    os.close(target_read)
    try:
        os.write(write_source, b"\0" * 16)
        assert gate.done.wait(1)
        assert isinstance(gate.error, BrokenPipeError)
    finally:
        os.close(write_source)
        gate.close()


@pytest.mark.parametrize("fail_at", ["first-dup", "second-dup", "thread-start"])
def test_gate_construction_failure_closes_all_acquired_fds(monkeypatch, fail_at):
    source, write_source = os.pipe()
    target_read, target = os.pipe()
    opened = []
    real_dup = os.dup

    def duplicate(fd):
        if fail_at == "first-dup" or (fail_at == "second-dup" and opened):
            raise OSError("injected dup failure")
        duplicate_fd = real_dup(fd)
        opened.append(duplicate_fd)
        return duplicate_fd

    def no_thread(_self):
        raise RuntimeError("injected thread failure")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, "dup", duplicate)
            if fail_at == "thread-start":
                patch.setattr(sandbox.threading.Thread, "start", no_thread)
            with pytest.raises((OSError, RuntimeError), match="injected"):
                sandbox._PcmOutputGate(source, target)
        for fd in opened:
            with pytest.raises(OSError):
                os.fstat(fd)
        os.fstat(source)
        os.fstat(target)
    finally:
        for fd in (source, write_source, target_read, target):
            os.close(fd)
