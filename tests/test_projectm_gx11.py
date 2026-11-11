"""Production raw-pixel capability/lifecycle boundary and real private Tk sink."""

from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import tkinter as tk
from types import SimpleNamespace

import pytest

from netmon.core import projectm_pixels as pixels, projectm_pixel_worker as worker
from netmon.core import projectm_display_worker as display_worker
from netmon.core import radio_sandbox as sandbox, projectm_frontend as frontend
from netmon.ui import projectm_pixel_window as ui
from test_projectm_frontend import Component


def wait(predicate, timeout=3, root=None):
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline
        if root is not None:
            root.update()
        time.sleep(0.002)


def child(program):
    return subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            program,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )


def test_fragmented_raw_stream_has_fixed_frames_and_bounded_remainder():
    parser = pixels.RawFrames()
    data = b"a" * pixels.FRAME_BYTES + b"b" * pixels.FRAME_BYTES + b"partial"
    frames = []
    for offset in range(0, len(data), pixels.CHUNK):
        frame = parser.feed(data[offset : offset + pixels.CHUNK])
        if frame is not None:
            frames.append(frame)
    assert frames == [b"a" * pixels.FRAME_BYTES, b"b" * pixels.FRAME_BYTES]
    assert parser.buffer == b"partial"
    assert parser.peak <= pixels.FRAME_BYTES + pixels.CHUNK


@pytest.mark.parametrize("data", [b"x" * (pixels.CHUNK + 1), bytearray(8), None])
def test_raw_chunk_budget_is_not_taken_from_input(data):
    with pytest.raises(ValueError):
        pixels.RawFrames().feed(data)


def test_mailbox_drops_pending_old_frame_and_does_not_queue():
    box = pixels.FrameMailbox()
    for value in (b"a", b"b", b"c"):
        box.put(value * pixels.FRAME_BYTES)
    assert box.received == 3 and box.dropped == 2
    assert box.take() == b"c" * pixels.FRAME_BYTES and box.take() is None
    with pytest.raises(ValueError):
        box.put(b"bad")


def test_real_pipe_reader_keeps_latest_and_stop_reaps_only_own_child(tmp_path):
    process = child(
        f"import sys,time;sys.stdout.buffer.write(b'a'*{pixels.FRAME_BYTES}+b'b'*{pixels.FRAME_BYTES});sys.stdout.buffer.flush();time.sleep(10)"
    )
    clean = []
    stream = pixels.PixelStream(
        process, SimpleNamespace(cleanup=lambda: clean.append(True))
    )
    try:
        assert stream.ready.wait(2)
        wait(lambda: stream.frames.received == 2)
        assert stream.frames.take() == b"b" * pixels.FRAME_BYTES
    finally:
        stream.stop()
    assert process.poll() is not None and not stream.thread.is_alive() and clean


@pytest.mark.parametrize(
    "program", ["pass", "import sys;sys.stdout.buffer.write(b'JPEG'+b'x'*200)"]
)
def test_eof_or_partial_image_like_input_cannot_publish_frame(program):
    process = child(program)
    stream = pixels.PixelStream(process, SimpleNamespace(cleanup=lambda: None))
    try:
        assert stream.ready.wait(2)
        assert stream.poll() == 2 and stream.frames.take() is None
    finally:
        stream.stop()


def test_stalled_reader_has_finite_complete_frame_deadline(monkeypatch):
    monkeypatch.setattr(pixels, "FRAME_TIMEOUT", 0.03)
    process = child("import time;time.sleep(10)")
    stream = pixels.PixelStream(process, SimpleNamespace(cleanup=lambda: None))
    try:
        assert stream.ready.wait(2) and "stalled" in stream.error
    finally:
        stream.stop()


@pytest.fixture
def controlled_pixel_stream(monkeypatch):
    """Real pipe/producer, with only this reader's monotonic clock controlled.

    Rebind the module attribute rather than changing the shared time module:
    pytest, Popen waits and thread joins retain their real wall-clock deadlines.
    The producer is command-driven and each burst is finite, even if the
    tested guard is removed. Cleanup never depends on a guard firing.
    """
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(pixels, "time", SimpleNamespace(monotonic=lambda: clock.now))
    program = f"""
import sys
frame = b'x' * {pixels.FRAME_BYTES}
while True:
    command = sys.stdin.buffer.read(1)
    if not command:
        break
    if command == b'p':
        sys.stdout.buffer.write(frame[:4096])
    elif command == b'f':
        sys.stdout.buffer.write(frame)
    elif command in (b'b', b'l'):
        for _ in range(18 if command == b'b' else 16):
            sys.stdout.buffer.write(frame)
    else:
        raise ValueError('Unknown fixture command')
    sys.stdout.buffer.flush()
"""
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            program,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    stream = pixels.PixelStream(process, SimpleNamespace(cleanup=lambda: None))

    def send(command):
        process.stdin.write(command)
        process.stdin.flush()

    try:
        yield clock, stream, send
    finally:
        stream.stop()
        process.stdin.close()
        assert process.poll() is not None and not stream.thread.is_alive()


def test_flood_exceeds_byte_budget_without_clock_refill(controlled_pixel_stream):
    _clock, stream, send = controlled_pixel_stream
    # 18 frames are finite; the normal initial budget permits only 16.
    send(b"b")
    wait(lambda: bool(stream.error), timeout=1)
    assert "rate exceeded" in stream.error
    assert stream.poll() == 2
    assert (
        16 * pixels.FRAME_BYTES
        < stream.received_bytes
        <= 16 * pixels.FRAME_BYTES + pixels.CHUNK
    )
    assert stream.frames.received == 16


def test_exact_initial_burst_is_allowed(controlled_pixel_stream):
    _clock, stream, send = controlled_pixel_stream
    send(b"l")
    wait(lambda: stream.frames.received == 16)
    assert not stream.error
    assert stream.received_bytes == 16 * pixels.FRAME_BYTES
    assert stream.frames.take() == b"x" * pixels.FRAME_BYTES


def test_trickle_bytes_do_not_extend_complete_frame_deadline(controlled_pixel_stream):
    clock, stream, send = controlled_pixel_stream
    for index, now in enumerate((0.0, 2.0, 4.0), 1):
        clock.now = now
        send(b"p")
        wait(lambda: stream.received_bytes >= index * 4096)
    assert not stream.error and stream.frames.received == 0
    clock.now = 5.5
    wait(lambda: bool(stream.error), timeout=1)
    assert "stalled" in stream.error
    assert stream.received_bytes == 3 * 4096
    assert stream.frames.take() is None


def test_complete_frame_resets_deadline_but_later_partial_data_does_not(
    controlled_pixel_stream,
):
    clock, stream, send = controlled_pixel_stream
    for now in (0.0, 4.0):
        clock.now = now
        stream.ready.clear()
        send(b"f")
        assert stream.ready.wait(2) and not stream.error
    assert stream.frames.received == 2
    clock.now = 8.0  # Four seconds after the last complete image: still valid.
    send(b"p")
    wait(lambda: stream.received_bytes == 2 * pixels.FRAME_BYTES + 4096)
    assert not stream.error
    clock.now = 9.5
    wait(lambda: bool(stream.error), timeout=1)
    assert "stalled" in stream.error
    assert stream.frames.received == 2


def test_pixel_command_grants_only_private_x_and_no_user_or_audio(tmp_path):
    command = pixels._command(tmp_path, (Path("/usr/lib/python3.12"), ()), 10, 11)
    assert command[0] == str(sandbox.BWRAP) and "--unshare-net" in command
    assert "/tmp/.X11-unix/X1" in command and "/run/client.auth" in command
    assert not {
        "/tmp/.X11-unix/X0",
        "/run/host.auth",
        "/run/audio/pulse",
        "/dev/dri",
        "/dev/snd",
        "/run/control",
    } & set(command)
    assert command[-3:] == ["/run/pixel-worker.py", "--resolution", "640x480"]


def test_worker_fixed_capture_and_lower_inherited_limits(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["worker"])
    monkeypatch.setattr(worker.resource, "getrlimit", lambda _: (32, 64))
    monkeypatch.setattr(worker.resource, "setrlimit", lambda n, v: calls.append((n, v)))
    monkeypatch.setattr(worker.os, "execv", lambda exe, args: calls.append((exe, args)))
    worker.main()
    assert all(bound == (32, 32) for _, bound in calls[:-1])
    exe, args = calls[-1]
    assert exe == "/usr/bin/ffmpeg" and args[args.index("-i") + 1] == ":1.0+0,0"
    assert args[-4:] == ["rgba", "-f", "rawvideo", "pipe:1"]
    monkeypatch.setattr(sys, "argv", ["worker", "unsafe"])
    assert worker.main() == 2


def test_internal_xvfb_worker_has_fixed_screen_and_no_outer_bridge(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["worker"])
    monkeypatch.setattr(display_worker, "limits", lambda: None)
    calls = []
    monkeypatch.setattr(
        display_worker.os, "execv", lambda exe, args: calls.append((exe, args))
    )
    display_worker.main()
    exe, args = calls[0]
    assert exe == "/usr/bin/Xvfb"
    assert args[args.index("-screen") + 1 : args.index("-screen") + 3] == [
        "0",
        "640x480x24",
    ]
    assert "-iglx" in args and "Xephyr" not in " ".join(args)


def test_reader_start_failure_has_no_unguarded_retry(tmp_path, monkeypatch):
    descriptor = os.open("/dev/null", os.O_RDONLY)

    @contextmanager
    def binding():
        yield descriptor, descriptor

    calls = []

    def fail(*args, **kwargs):
        calls.append((args, kwargs))
        raise OSError("bwrap failed")

    monkeypatch.setattr(pixels, "_runtime", lambda: (Path("/usr/lib/python3.12"), ()))
    monkeypatch.setattr(pixels.subprocess, "Popen", fail)
    try:
        with pytest.raises(OSError):
            pixels.start(SimpleNamespace(display_binding=binding), work_root=tmp_path)
    finally:
        os.close(descriptor)
    command = calls[0][0][0]
    assert len(calls) == 1 and command[0] == str(sandbox.SYSTEMD_RUN)
    assert command[5].startswith("--unit=netmon-radio-pm-pixels-")
    assert str(sandbox.BWRAP) in command
    assert not list(tmp_path.glob("projectm-pixels-*"))


def test_pixel_dependency_failure_ends_frontend_and_its_other_dependencies():
    renderer, audio, display, reader = (
        Component(),
        Component(),
        Component(),
        Component(),
    )
    session = frontend.FrontendSession(
        renderer, audio, display, SimpleNamespace(cleanup=lambda: None), pixels=reader
    )
    reader.result = 3
    assert session.poll() == 2 and renderer.result is not None
    assert audio.stops == display.stops == reader.stops == 1
    session.stop()


@pytest.fixture
def app():
    app = tk.Tk()
    app.withdraw()
    app._projectm_pixel_window = None
    yield app
    try:
        app.destroy()
    except tk.TclError:
        pass


def request():
    value = SimpleNamespace(
        frames=pixels.FrameMailbox(),
        cancelled=threading.Event(),
        done=threading.Event(),
    )
    value.stop = value.cancelled.set
    return value


def test_actual_tk_draws_raw_frame_and_close_only_requests_stop(app):
    owner = request()
    app.radio_projectm_proc = owner
    window = ui.ensure(app, owner)
    owner.frames.put(b"x" * pixels.FRAME_BYTES)
    wait(lambda: window.displayed == 1, root=app)
    assert window.photo.width() == 640 and window.photo.height() == 480
    start = time.monotonic()
    window.close()
    assert time.monotonic() - start < 0.1 and owner.cancelled.is_set()
    assert window.timer is None and app._projectm_pixel_window is None


def test_stale_window_never_consumes_new_frame_or_cancels_new_owner(app):
    older, newer = request(), request()
    app.radio_projectm_proc = older
    window = ui.ensure(app, older)
    app.radio_projectm_proc = newer
    newer.frames.put(b"x" * pixels.FRAME_BYTES)
    window.tick()
    assert window.closed and not window.displayed and not newer.cancelled.is_set()
    assert newer.frames.take() is not None


def test_destroyed_root_requests_its_own_owner_stop(app):
    owner = request()
    app.radio_projectm_proc = owner
    window = ui.ensure(app, owner)
    app.destroy()
    assert window.closed and owner.cancelled.is_set() and window.timer is None


def test_ui_failure_stops_request_instead_of_starting_old_display(app, monkeypatch):
    owner = request()
    app.radio_projectm_proc = owner
    monkeypatch.setattr(
        ui, "PixelWindow", lambda *_: (_ for _ in ()).throw(RuntimeError("no Tk"))
    )
    with pytest.raises(RuntimeError):
        ui.ensure(app, owner)
    assert owner.cancelled.is_set()
