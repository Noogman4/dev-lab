"""Pipe readiness must agree with the terminal helper's bounded control parser."""

import json
import os
from pathlib import Path
import subprocess
import time

import pytest

from netmon.ui.terminal_helper import ControlReader


@pytest.fixture
def helper_channel(request, tmp_path):
    """An owned real GTK helper; no automatic parent control traffic."""
    import tkinter as tk

    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"
    root = tk.Tk()
    root.geometry("640x480")
    frame = tk.Frame(root, container=True)
    frame.pack(fill="both", expand=True)
    root.update()
    helper = getattr(
        request,
        "param",
        Path(__file__).resolve().parents[1] / "netmon/ui/terminal_helper.py",
    )
    messages, pending = [], b""
    process = None
    with (tmp_path / "helper-stderr.log").open("wb") as stderr:
        try:
            process = subprocess.Popen(
                [
                    "/usr/bin/python3",
                    "-I",
                    "-B",
                    str(helper),
                    "--parent",
                    str(frame.winfo_id()),
                    "--width",
                    "640",
                    "--height",
                    "480",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=stderr,
                bufsize=0,
                env={**os.environ, "GDK_BACKEND": "x11", "NO_AT_BRIDGE": "1"},
            )
            os.set_blocking(process.stdout.fileno(), False)

            def pump(seconds, predicate):
                nonlocal pending
                deadline = time.monotonic() + seconds
                while time.monotonic() < deadline:
                    root.update()
                    try:
                        pending += os.read(process.stdout.fileno(), 8192)
                    except BlockingIOError:
                        pass
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        messages.append(json.loads(line))
                    if predicate():
                        return
                    time.sleep(0.005)

            pump(5, lambda: any(m["event"] == "ready" for m in messages))
            assert any(m["event"] == "ready" for m in messages), messages
            yield root, process, pump, messages
        finally:
            if process is not None:
                process.stdin.close()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=3)
                process.stdout.close()
            root.destroy()


def test_real_helper_dispatches_control_batch_without_followup_bytes(helper_channel):
    _root, process, pump, messages = helper_channel
    ready = next(m for m in messages if m["event"] == "ready")
    batch = b'{"action":"focus"}\n{"action":"detach"}\n{"action":"attach"}\n'
    assert os.write(process.stdin.fileno(), batch) == len(batch)
    pump(3, lambda: sum(m["event"] == "mode" for m in messages) == 2)
    modes = [m for m in messages if m["event"] == "mode"]
    assert [m["mode"] for m in modes] == ["external", "docked"], messages
    assert all(m["pid"] == ready["pid"] for m in modes)


@pytest.fixture
def channel():
    read, write = os.pipe()
    reader = ControlReader(read)
    assert not os.get_blocking(read)
    try:
        yield reader, write
    finally:
        os.close(read)
        os.close(write)


def test_empty_nonblocking_control_pipe_returns_without_waiting(channel):
    reader, _ = channel
    assert reader.read() == [] and reader.pending == b""


def test_coalesced_controls_are_all_returned_in_order(channel):
    reader, write = channel
    lines = [b'{"action":"focus"}', b'{"action":"detach"}', b'{"action":"attach"}']
    os.write(write, b"\n".join(lines) + b"\n")
    assert reader.read() == lines
    assert reader.read() == [] and reader.pending == b""


def test_fragmented_lines_preserve_every_byte_without_blocking(channel):
    reader, write = channel
    os.write(write, b'{"action":"fo')
    assert reader.read() == []
    assert reader.pending == b'{"action":"fo'
    os.write(write, b'cus"}\n{"action":"attach"}\n{"action":')
    assert reader.read() == [b'{"action":"focus"}', b'{"action":"attach"}']
    assert reader.pending == b'{"action":'
    os.write(write, b'"close"}\n')
    assert reader.read() == [b'{"action":"close"}'] and reader.pending == b""


@pytest.mark.parametrize("newline", [b"", b"\n"])
def test_oversized_complete_or_partial_line_is_rejected(channel, newline):
    reader, write = channel
    os.write(write, b"x" * (reader.MAX_LINE + 1) + newline)
    with pytest.raises(ValueError, match="exceeds limit"):
        reader.read()


def test_exact_line_limit_is_accepted(channel):
    reader, write = channel
    line = b"x" * reader.MAX_LINE
    os.write(write, line + b"\n")
    assert reader.read() == [line] and reader.pending == b""


def test_queued_complete_lines_are_delivered_before_eof():
    read, write = os.pipe()
    reader = ControlReader(read)
    try:
        os.write(write, b'{"action":"close"}\n')
    finally:
        os.close(write)
    try:
        assert reader.read() == [b'{"action":"close"}']
        assert reader.read() is None
    finally:
        os.close(read)
