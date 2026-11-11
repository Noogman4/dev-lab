"""Opt-in stall diagnosis: off by default, bounded file, correct events."""

import os
import threading
import time
import tkinter as tk
from types import SimpleNamespace

import pytest

from netmon.core import projectm_pixels as pixels
from netmon.core import stall_log
from netmon.features import radio_controller
from netmon.ui import projectm_pixel_window as ui


@pytest.fixture
def log_file(tmp_path, monkeypatch):
    target = tmp_path / "logs" / "radio_stall.log"
    monkeypatch.setattr(stall_log, "path", lambda: str(target))
    monkeypatch.setattr(stall_log, "_disabled_after_error", False)
    return target


def test_disabled_by_default_writes_nothing(log_file, monkeypatch):
    monkeypatch.delenv(stall_log.ENV, raising=False)
    assert not stall_log.enabled()
    stall_log.write("ui-stall", ms=99.0)
    assert not log_file.exists()
    monitor = stall_log.WindowMonitor(clock=lambda: 0.0)
    monitor.observe(1, 50.0)
    assert not log_file.exists()


@pytest.mark.parametrize("value", ["0", "off", "", "maybe"])
def test_only_exact_truthy_values_enable(value, monkeypatch):
    monkeypatch.setenv(stall_log.ENV, value)
    assert not stall_log.enabled()


def test_monitor_reports_stalls_gaps_pastes_and_summary(log_file, monkeypatch):
    monkeypatch.setenv(stall_log.ENV, "1")
    now = [0.0]
    monitor = stall_log.WindowMonitor(clock=lambda: now[0])
    received = 0
    # 1 s of healthy 5 ms ticks with a frame every ~33 ms: no events.
    for step in range(200):
        now[0] += 0.005
        if step % 7 == 0:
            received += 1
        monitor.observe(received)
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1 and " monitor-start " in lines[0]
    # One 80 ms main-thread stall.
    now[0] += 0.080
    monitor.observe(received)
    # A 200 ms hole in frame arrival (ticks keep coming).
    for _ in range(40):
        now[0] += 0.005
        monitor.observe(received)
    received += 1
    monitor.observe(received)
    # One slow paste.
    now[0] += 0.005
    monitor.observe(received, 31.0)
    # Cross the 10 s summary boundary.
    now[0] += 9.0
    monitor.observe(received)
    text = log_file.read_text()
    assert "ui-stall ms=80.0" in text
    assert "update-gap ms=295.0" in text
    assert "paste ms=31.0" in text
    summary = [line for line in text.splitlines() if " summary " in line][-1]
    # the 9 s jump that crosses the summary boundary counts as a stall too
    assert "stalls=2" in summary and "max_stall_ms=9000.0" in summary
    assert "gaps=1" in summary and "max_gap_ms=295.0" in summary
    assert "pastes=1" in summary and "max_paste_ms=31.0" in summary
    assert "reader_fps=" in summary and "shown_fps=" in summary
    assert "updates=" in summary and "ticks=" in summary
    assert oct(os.stat(log_file).st_mode & 0o777) == "0o600"


def test_event_lines_are_capped_per_window_and_file_is_bounded(log_file, monkeypatch):
    monkeypatch.setenv(stall_log.ENV, "1")
    now = [0.0]
    monitor = stall_log.WindowMonitor(clock=lambda: now[0])
    for _ in range(100):
        now[0] += 0.050
        monitor.observe(0)
    lines = log_file.read_text().splitlines()
    assert (
        sum(1 for line in lines if "ui-stall" in line) == monitor.MAX_LINES_PER_WINDOW
    )
    monkeypatch.setattr(stall_log, "MAX_BYTES", 10)
    before = log_file.read_bytes()
    stall_log.write("ui-stall", ms=1.0)
    assert log_file.read_bytes() == before


def test_write_failure_disables_quietly(log_file, monkeypatch):
    monkeypatch.setenv(stall_log.ENV, "1")
    monkeypatch.setattr(
        stall_log, "path", lambda: (_ for _ in ()).throw(OSError("no state dir"))
    )
    stall_log.write("ui-stall", ms=1.0)
    assert stall_log._disabled_after_error
    stall_log.write("ui-stall", ms=1.0)


def _window(root, request):
    root.radio_projectm_proc = request
    view = ui.ensure(root, request)
    root.update()
    return view


def _request():
    request = SimpleNamespace(
        frames=pixels.FrameMailbox(),
        cancelled=threading.Event(),
        done=threading.Event(),
    )
    request.stop = request.cancelled.set
    return request


def test_pixel_window_has_no_monitor_without_flag(monkeypatch):
    monkeypatch.delenv(stall_log.ENV, raising=False)
    root = tk.Tk()
    root.withdraw()
    try:
        view = _window(root, _request())
        assert view.monitor is None
        view.close()
    finally:
        root.destroy()


def test_pixel_window_monitor_observes_ticks_and_frames(log_file, monkeypatch):
    monkeypatch.setenv(stall_log.ENV, "1")
    root = tk.Tk()
    root.withdraw()
    try:
        request = _request()
        view = _window(root, request)
        assert view.monitor is not None
        request.frames.put(b"\x10\x20\x30\xff" * (pixels.WIDTH * pixels.HEIGHT))
        for _ in range(60):
            root.update()
            if view.displayed:
                break
            root.after(5)
            root.update()
        assert view.displayed == 1
        assert view.monitor.ticks >= 2 and view.monitor.pastes == 1
        assert "monitor-start" in log_file.read_text()
        view.close()
    finally:
        root.destroy()


def test_title_poll_writes_one_line_per_round(log_file, monkeypatch):
    monkeypatch.setenv(stall_log.ENV, "1")
    proc = object()
    app = SimpleNamespace(radio_proc=proc)

    def read_title(_app, _proc):
        assert _proc is proc
        app.radio_proc = None  # end the loop before its 5 s sleep
        return "", {"metadata": None, "icy-fetch": ""}

    monkeypatch.setattr(radio_controller, "_read_radio_stream_title", read_title)
    radio_controller._poll_radio_metadata(app, proc)
    lines = [line for line in log_file.read_text().splitlines() if "title-poll" in line]
    assert len(lines) == 1 and "icy=True" in lines[0] and "found=False" in lines[0]


def test_gc_hook_only_with_flag_and_reports_generation_two(log_file, monkeypatch):
    import gc

    monkeypatch.delenv(stall_log.ENV, raising=False)
    gc.callbacks[:] = [c for c in gc.callbacks if c is not stall_log._gc_callback]
    assert not stall_log.install_gc_hook()
    assert stall_log._gc_callback not in gc.callbacks
    monkeypatch.setenv(stall_log.ENV, "1")
    try:
        assert stall_log.install_gc_hook() and stall_log.install_gc_hook()
        assert gc.callbacks.count(stall_log._gc_callback) == 1
        gc.collect(2)
        assert not log_file.exists() or "gc gen" not in log_file.read_text()
        stall_log.flush_gc_events()  # the callback only queues (review R-1)
        text = log_file.read_text()
        assert "gc gen=2 ms=" in text and "collected=" in text
        monitor = stall_log.WindowMonitor(clock=lambda: 0.0)
        assert "monitor-start gc_threshold=" in log_file.read_text()
        gc.collect(2)
        monitor._window_start = -20.0
        monitor.observe(0)
        summary = [x for x in log_file.read_text().splitlines() if " summary " in x][-1]
        assert "gc2=" in summary and "gc2_max_ms=" in summary and "gc2=0" not in summary
    finally:
        gc.callbacks[:] = [c for c in gc.callbacks if c is not stall_log._gc_callback]


def test_gc_callback_never_raises():
    stall_log._gc_callback("stop", {"generation": 7})  # no matching start
    stall_log._gc_callback("start", {})
    stall_log._gc_callback("stop", {"generation": None, "collected": "x"})


def test_after_hook_times_slow_tk_callbacks_only_with_flag(log_file, monkeypatch):
    import tkinter

    monkeypatch.delenv(stall_log.ENV, raising=False)
    assert not stall_log.install_after_hook()
    monkeypatch.setenv(stall_log.ENV, "1")
    original_after = tkinter.Misc.after
    monkeypatch.setattr(stall_log, "_after_installed", False)
    try:
        assert stall_log.install_after_hook() and stall_log.install_after_hook()
        root = tk.Tk()
        root.withdraw()
        seen = []

        class Owner:
            def slow(self):
                seen.append("slow")
                time.sleep(0.06)

            def quick(self):
                seen.append("quick")

        owner = Owner()
        root.after(1, owner.slow)
        root.after(1, owner.quick)
        root.after_idle(owner.slow)
        root.after(5)  # plain sleep form still works
        end = time.time() + 2
        while len(seen) < 3 and time.time() < end:
            root.update()
        root.destroy()
        text = log_file.read_text()
        assert seen.count("slow") == 2 and "quick" in seen
        assert text.count("after-callback") == 2 and "Owner.slow" in text
        assert "Owner.quick" not in text
    finally:
        tkinter.Misc.after = original_after


def test_gc_during_locked_write_cannot_deadlock(log_file, monkeypatch):
    """Codex review R-1: a collection inside write() must not re-enter write()."""
    import gc

    monkeypatch.setenv(stall_log.ENV, "1")
    target = str(log_file)
    os.makedirs(os.path.dirname(target), exist_ok=True)

    def path_with_gc():
        gc.collect(2)  # runs while write() holds its lock
        return target

    monkeypatch.setattr(stall_log, "path", path_with_gc)
    gc.callbacks[:] = [c for c in gc.callbacks if c is not stall_log._gc_callback]
    stall_log.install_gc_hook()
    try:
        worker = threading.Thread(
            target=lambda: stall_log.write("ui-stall", ms=1.0), daemon=True
        )
        worker.start()
        worker.join(3)
        assert not worker.is_alive(), "write() deadlocked on its own lock"
        assert "ui-stall" in log_file.read_text()
        # path() collects again on every write here; flushing must still end.
        flusher = threading.Thread(target=stall_log.flush_gc_events, daemon=True)
        flusher.start()
        flusher.join(3)
        assert not flusher.is_alive(), "flush_gc_events() did not terminate"
        assert "gc gen=2" in log_file.read_text()
    finally:
        gc.callbacks[:] = [c for c in gc.callbacks if c is not stall_log._gc_callback]


def test_existing_open_log_is_tightened_to_owner_only(log_file, monkeypatch):
    monkeypatch.setenv(stall_log.ENV, "1")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("old\n")
    log_file.chmod(0o644)
    stall_log.write("ui-stall", ms=1.0)
    assert oct(os.stat(log_file).st_mode & 0o777) == "0o600"
    assert log_file.read_text().startswith("old\n")


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_linked_log_target_is_refused_and_left_untouched(log_file, monkeypatch, kind):
    monkeypatch.setenv(stall_log.ENV, "1")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    other = log_file.parent / "other.txt"
    other.write_text("keep\n")
    other.chmod(0o644)
    if kind == "symlink":
        log_file.symlink_to(other)
    else:
        os.link(other, log_file)
    stall_log.write("ui-stall", ms=1.0)
    assert other.read_text() == "keep\n"
    assert oct(os.stat(other).st_mode & 0o777) == "0o644"
    assert stall_log._disabled_after_error


def test_reader_and_shown_rates_are_counted_separately(log_file, monkeypatch):
    """Codex review H-1: counter deltas vs. observed changes vs. pastes."""
    monkeypatch.setenv(stall_log.ENV, "1")
    now = [0.0]
    monitor = stall_log.WindowMonitor(clock=lambda: now[0])
    for at, received, paste in ((1.0, 0, None), (2.0, 30, 5.0), (10.0, 300, None)):
        now[0] = at
        monitor.observe(received, paste)
    summary = [x for x in log_file.read_text().splitlines() if " summary " in x][-1]
    assert "reader_fps=30.0" in summary  # (300 - 0) / 10 s
    assert "shown_fps=0.1" in summary and "updates=2" in summary


@pytest.mark.parametrize("reader", [False, True])
def test_fifo_log_target_is_refused_without_blocking(log_file, monkeypatch, reader):
    """Codex recheck R-4a: an existing FIFO must not block the writer."""
    monkeypatch.setenv(stall_log.ENV, "1")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    os.mkfifo(log_file, 0o600)
    read_fd = os.open(log_file, os.O_RDONLY | os.O_NONBLOCK) if reader else None
    try:
        worker = threading.Thread(
            target=lambda: stall_log.write("ui-stall", ms=1.0), daemon=True
        )
        worker.start()
        worker.join(3)
        assert not worker.is_alive(), "write() blocked on a FIFO"
        assert stall_log._disabled_after_error
        if read_fd is not None:
            # Writer already closed again: EOF (b"") and no bytes were written.
            assert os.read(read_fd, 64) == b""
    finally:
        if read_fd is not None:
            os.close(read_fd)
