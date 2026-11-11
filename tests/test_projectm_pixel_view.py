"""Fixed-pixel mailbox, Tk lifecycle and owned stream failure tests."""

import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk

import pytest

from projectm_pixel_benchmark import END, MAGIC
from projectm_pixel_protocol import FRAME_BYTES
from projectm_pixel_view import LatestFrame, PixelView, Request, own


def command(program):
    return [
        sys.executable,
        "-I",
        "-S",
        "-B",
        "-X",
        "pycache_prefix=/nonexistent",
        "-c",
        program,
    ]


def pixel_program():
    header = MAGIC + struct.pack(">IQ", 0, 1)
    end = struct.pack(">IQ", END, 0)
    return f"import sys;sys.stdout.buffer.write({header!r}+b'\\x7f'*{FRAME_BYTES}+{end!r});sys.stdout.buffer.flush()"


def test_mailbox_keeps_exactly_latest_frame_and_counts_overwrites():
    box = LatestFrame()
    for value in (b"a", b"b", b"c"):
        box.put(value * FRAME_BYTES)
    assert box.received == 3 and box.dropped == 2
    assert box.take() == b"c" * FRAME_BYTES
    assert box.take() is None


@pytest.mark.parametrize("value", [b"", b"x", bytearray(FRAME_BYTES), None, "pixels"])
def test_mailbox_rejects_non_fixed_bytes(value):
    with pytest.raises(ValueError):
        LatestFrame().put(value)


@pytest.fixture
def app():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


def until(app, predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline, "UI test deadline"
        app.update()
        time.sleep(0.002)
    app.update()


def view(app, program):
    label = tk.Label(app)
    status = tk.StringVar(app)
    return PixelView(app, label, status, lambda _: (command(program), dict(os.environ)))


def test_fixed_raw_frame_is_displayed_then_terminal_status(app):
    instance = view(app, pixel_program())
    request = instance.start()
    try:
        until(app, lambda: request.done.is_set() and request.displayed == 1)
        assert request.state == "ended" and not request.error
        assert instance.status.get() == "ended"
        assert instance.photo.width() == 640 and instance.photo.height() == 480
    finally:
        instance.close()
        assert request.done.wait(3)


@pytest.mark.parametrize(
    "program", ["pass", "import sys;sys.stdout.buffer.write(b'evil')"]
)
def test_bad_or_truncated_stream_is_terminal_error(app, program):
    instance = view(app, program)
    request = instance.start()
    try:
        until(app, lambda: request.done.is_set() and instance.status.get() == "error")
        assert request.error and not request.displayed
        assert request.process.poll() is not None
    finally:
        instance.close()


def test_close_destroy_returns_without_wait_or_worker_tk_calls(app):
    instance = view(app, "import sys;sys.stdin.buffer.read(1)")
    request = instance.start()
    until(app, lambda: request.process is not None)
    start = time.monotonic()
    instance.close()
    assert time.monotonic() - start < 0.1
    app.destroy()
    assert request.done.wait(3)
    assert request.state == "cancelled" and not request.forced_kill
    assert request.process.poll() is not None
    instance.close()
    assert instance.start() is None


def test_stop_invalidates_pending_frame_before_tk_publication(app):
    instance = view(app, "import sys;sys.stdin.buffer.read(1)")
    request = instance.start()
    request.frames.put(b"x" * FRAME_BYTES)
    instance.stop()
    try:
        until(app, request.done.is_set)
        assert request.displayed == 0 and request.frames.take() is None
        until(app, lambda: instance.status.get() == "stopped")
    finally:
        instance.close()


def test_launch_error_completes_request_and_does_not_block_replacement(app):
    instance = view(app, pixel_program())
    instance.launch = lambda _: (_ for _ in ()).throw(ValueError("launch denied"))
    with pytest.raises(ValueError):
        instance.start()
    assert instance.request is None
    instance.launch = lambda _: (command(pixel_program()), dict(os.environ))
    request = instance.start()
    try:
        until(app, request.done.is_set)
        assert request.state == "ended"
    finally:
        instance.close()


def test_cancelled_intermediate_does_not_skip_older_cleanup():
    predecessor = Request(1)
    middle = Request(2, previous=predecessor)
    middle.cancel.set()
    newest = Request(3, previous=middle)
    threads = [
        threading.Thread(
            target=own, args=(r, command(pixel_program()), dict(os.environ))
        )
        for r in (middle, newest)
    ]
    for thread in threads:
        thread.start()
    try:
        assert not middle.done.wait(0.05)
        assert newest.process is None
        predecessor.done.set()
        assert newest.done.wait(3)
        assert middle.process is None and middle.state == "cancelled"
        assert newest.state == "ended" and newest.process.poll() is not None
    finally:
        predecessor.done.set()
        for thread in threads:
            thread.join(3)


def test_failed_launch_retains_incomplete_predecessor_for_next_start(app):
    instance = view(app, pixel_program())
    older = Request(0)
    instance.request = older
    instance.launch = lambda _: (_ for _ in ()).throw(ValueError("launch denied"))
    with pytest.raises(ValueError):
        instance.start()
    assert instance.request is older and older.cancel.is_set()
    instance.launch = lambda _: (command(pixel_program()), dict(os.environ))
    newest = instance.start()
    try:
        assert not newest.done.wait(0.05) and newest.process is None
        older.done.set()
        until(app, newest.done.is_set)
        assert newest.state == "ended"
    finally:
        older.done.set()
        instance.close()
        assert newest.done.wait(3)


def test_no_worker_calls_tk_or_image_decoder():
    import inspect

    source = inspect.getsource(own)
    assert ".after(" not in source and "PhotoImage" not in source
    assert (
        "Image.open"
        not in Path(__file__).with_name("projectm_pixel_view.py").read_text()
    )


def test_launcher_rejects_combined_pixel_probe_modes():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            str(Path(__file__).with_name("run_isolated_suite.py")),
            "--projectm-pixel-ui-probe",
            "--projectm-pixel-benchmark",
        ],
        capture_output=True,
        text=True,
        timeout=3,
    )
    assert completed.returncode == 2
    assert "does not accept other test options" in completed.stderr
