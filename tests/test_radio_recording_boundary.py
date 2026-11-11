"""Recording pipe policy, file ownership, child lifetime and start cancellation."""

import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace

import pytest

from netmon.core import radio_sandbox as sandbox
from netmon.features import radio_controller as radio

PROGRESS = b"out_time_us=100000\ntotal_size=7\nprogress=continue\n"


def controlled_pipeline(
    monkeypatch,
    tmp_path,
    encoder,
    source="import sys;sys.stdout.buffer.write(b'media')",
    *,
    progress_channel=True,
):
    children = []
    real = sandbox.subprocess.Popen
    monkeypatch.setattr(sandbox, "recording_available", lambda: True)
    # Plain python stand-ins instead of bwrap capsules; no user manager in the
    # isolated suite. Quota wiring for recording has its own tests below.
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    monkeypatch.setattr(sandbox, "_limited", lambda command, _profile: command)
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))
    monkeypatch.setattr(sandbox, "_runtime_files", lambda *_a, **_k: ())
    monkeypatch.setattr(
        sandbox,
        "_fetch_command",
        lambda *_a: [str(sandbox.PYTHON), "-I", "-S", "-B", "-c", source],
    )

    def command(directory, _runtime):
        prefix = (
            f"import os;fd=os.open({str(directory / 'progress')!r},os.O_WRONLY);os.dup2(fd,2);os.close(fd);"
            if progress_channel
            else ""
        )
        return [str(sandbox.PYTHON), "-I", "-S", "-B", "-c", prefix + encoder]

    monkeypatch.setattr(sandbox, "_recording_sandbox_command", command)

    def spawn(args, **kwargs):
        assert kwargs["close_fds"] and "private-token" not in " ".join(args)
        child = real(args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    return children


def encoder_script(*, tail=""):
    return (
        f"import os,sys;sys.stdin.buffer.read();os.write(1,b'encoded');os.write(2,{PROGRESS!r});"
        + tail
    )


def test_completed_recording_owns_exact_output_and_reaps_both(monkeypatch, tmp_path):
    children = controlled_pipeline(monkeypatch, tmp_path, encoder_script())
    proc = sandbox.start_recording(
        "https://example.com/?private-token", tmp_path / "test.mp3", work_root=tmp_path
    )
    assert proc.ready and proc.runtime_verified is False
    assert proc.wait(timeout=2) == 0 and proc.poll() == 0
    assert Path(proc.output_path).read_bytes() == b"encoded"
    assert Path(proc.output_path).stat().st_mode & 0o777 == 0o600
    assert all(p.poll() == 0 for p in children)
    assert not list(tmp_path.glob("record-*"))


@pytest.mark.parametrize("kind", ["file", "symlink", "fifo", "directory"])
def test_existing_targets_are_never_overwritten_or_followed(tmp_path, kind):
    target = tmp_path / "name.mp3"
    victim = tmp_path / "private"
    victim.write_bytes(b"keep")
    if kind == "file":
        target.write_bytes(b"old")
    elif kind == "symlink":
        target.symlink_to(victim)
    elif kind == "fifo":
        os.mkfifo(target)
    else:
        target.mkdir()
    fd, path = sandbox._recording_target(target)
    try:
        os.write(fd, b"new")
    finally:
        os.close(fd)
    assert Path(path) == tmp_path / "name-001.mp3"
    assert victim.read_bytes() == b"keep"
    if kind == "file":
        assert target.read_bytes() == b"old"


def test_encoder_gets_no_directory_media_network_or_control_mount(
    monkeypatch, tmp_path
):
    sandbox._prepare_directory(tmp_path)
    command = sandbox._recording_sandbox_command(tmp_path, ())
    assert "--unshare-net" in command and "--disable-userns" in command
    for name in (
        "/run/control",
        "/run/audio/pulse",
        "/run/request.json",
        "/media/selected",
    ):
        assert name not in command
    assert command.count(str(tmp_path)) == 0
    assert command[command.index("-protocol_whitelist") + 1] == "pipe"
    assert command[-1] == "pipe:1"
    assert command[command.index("-progress") + 1] == "/run/record-progress"
    assert ["--bind", str(tmp_path / "progress"), "/run/record-progress"] == command[
        command.index(str(tmp_path / "progress"))
        - 1 : command.index(str(tmp_path / "progress"))
        + 2
    ]


@pytest.mark.parametrize(
    "failure", ["source", "encoder", "missing-progress", "progress-flood", "spawn"]
)
def test_failed_starts_reap_children_and_keep_existing_files(
    monkeypatch, tmp_path, failure
):
    source = "import sys;sys.stdout.buffer.write(b'media')"
    encoder = encoder_script()
    if failure == "source":
        source += ";raise SystemExit(2)"
    elif failure == "encoder":
        encoder += "raise SystemExit(2)"
    elif failure == "missing-progress":
        encoder = (
            "import sys;sys.stdin.buffer.read();print('no progress',file=sys.stderr)"
        )
    elif failure == "progress-flood":
        encoder = "import os;os.write(2,b'X'*30000)"
    children = controlled_pipeline(monkeypatch, tmp_path, encoder, source)
    if failure == "spawn":
        monkeypatch.setattr(
            sandbox,
            "_recording_sandbox_command",
            lambda *_a, **_k: (_ for _ in ()).throw(OSError("spawn failed")),
        )
    target = tmp_path / "saved.mp3"
    target.write_bytes(b"previous")
    with pytest.raises((sandbox.RadioSandboxError, OSError)):
        sandbox.start_recording("https://example.com/live", target, work_root=tmp_path)
    assert target.read_bytes() == b"previous"
    assert all(p.poll() is not None for p in children)
    assert not list(tmp_path.glob("record-*"))


def test_stderr_cannot_forge_recording_progress(monkeypatch, tmp_path):
    children = controlled_pipeline(
        monkeypatch, tmp_path, encoder_script(), progress_channel=False
    )
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.start_recording(
            "https://example.com/live", tmp_path / "forged.mp3", work_root=tmp_path
        )
    assert all(child.poll() is not None for child in children)
    assert not list(tmp_path.glob("record-*"))


def test_stop_closes_source_and_flushes_encoder(monkeypatch, tmp_path):
    source = "import sys,time;sys.stdout.buffer.write(b'M');sys.stdout.buffer.flush();time.sleep(20)"
    encoder = f"import os,sys;sys.stdin.buffer.read(1);os.write(1,b'encoded');os.write(2,{PROGRESS!r});sys.stdin.buffer.read();os.write(1,b'flushed')"
    children = controlled_pipeline(monkeypatch, tmp_path, encoder, source)
    proc = sandbox.start_recording(
        "https://example.com/live", tmp_path / "stop.mp3", work_root=tmp_path
    )
    proc.terminate()
    assert proc.wait(timeout=2) == 0
    assert Path(proc.output_path).read_bytes() == b"encodedflushed"
    assert all(p.poll() is not None for p in children)


def test_kill_reaps_both_and_never_reports_success(monkeypatch, tmp_path):
    source = "import sys,time;sys.stdout.buffer.write(b'M');sys.stdout.buffer.flush();time.sleep(20)"
    encoder = f"import os,sys,time;sys.stdin.buffer.read(1);os.write(1,b'encoded');os.write(2,{PROGRESS!r});time.sleep(20)"
    children = controlled_pipeline(monkeypatch, tmp_path, encoder, source)
    proc = sandbox.start_recording(
        "https://example.com/live", tmp_path / "kill.mp3", work_root=tmp_path
    )
    proc.kill()
    assert proc.wait(timeout=2) != 0
    assert all(p.poll() is not None for p in children)
    assert not list(tmp_path.glob("record-*"))


def app_fixture(tmp_path, monkeypatch):
    jobs, callbacks, statuses = [], [], []

    class QueuedThread:
        def __init__(self, target, **_k):
            self.target = target

        def start(self):
            jobs.append(self.target)

    monkeypatch.setattr(radio.threading, "Thread", QueuedThread)
    monkeypatch.setattr(radio, "radio_recording_available", lambda _app: True)
    monkeypatch.setattr(radio, "refresh_radio_recording_ui", lambda _app: None)
    monkeypatch.setattr(
        radio, "_recording_status_text", lambda _app, text: statuses.append(text)
    )
    monkeypatch.setattr(radio, "_schedule_ui", lambda _app, cb: callbacks.append(cb))
    station = {"id": "test", "name": "Test", "url": "https://example.com/live"}
    app = SimpleNamespace(
        radio_current_station=station,
        radio_current_station_id="test",
        radio_stations=[station],
        radio_search_results=[station],
        radio_record_proc=None,
        radio_recordings_dir=str(tmp_path),
        netmon_state_dir=str(tmp_path),
    )
    return app, jobs, callbacks, statuses


def test_cancel_before_worker_start_prevents_spawn_and_duplicate_start(
    monkeypatch, tmp_path
):
    app, jobs, callbacks, statuses = app_fixture(tmp_path, monkeypatch)
    refreshes = []
    monkeypatch.setattr(
        radio,
        "refresh_radio_recording_ui",
        lambda current: refreshes.append(current.radio_record_starting),
    )
    monkeypatch.setattr(
        sandbox,
        "start_recording",
        lambda *_a, **_k: pytest.fail("cancelled worker spawned"),
    )
    assert radio.start_radio_recording(app)
    assert not radio.start_radio_recording(app)
    assert radio.stop_radio_recording(app)
    assert app.radio_record_starting
    jobs.pop()()
    for cb in callbacks:
        cb()
    assert not app.radio_record_starting and app.radio_record_proc is None
    assert statuses[-1] == "Aufnahme gestoppt."
    assert refreshes[-1] is False


def test_cancel_during_start_reaps_late_process_and_discards_old_ui(
    monkeypatch, tmp_path
):
    real_thread = threading.Thread
    app, jobs, callbacks, statuses = app_fixture(tmp_path, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    signals = []
    proc = SimpleNamespace(
        output_path=str(tmp_path / "late.mp3"),
        terminate=lambda: signals.append("terminate"),
        kill=lambda: signals.append("kill"),
        wait=lambda timeout=None: 0,
    )

    def start(*_a, **_k):
        entered.set()
        assert release.wait(2)
        return proc

    monkeypatch.setattr(sandbox, "start_recording", start)
    assert radio.start_radio_recording(app)
    thread = real_thread(target=jobs.pop())
    thread.start()
    assert entered.wait(2)
    assert radio.stop_radio_recording(app)
    release.set()
    thread.join(3)
    assert not thread.is_alive() and signals == ["terminate"]
    for cb in callbacks:
        cb()
    assert app.radio_record_proc is None and not app.radio_record_starting
    assert not any(
        "Aufnahme läuft:" in value or "gespeichert" in value for value in statuses
    )


def test_old_completion_cannot_clear_new_pending_start(monkeypatch, tmp_path):
    app, jobs, callbacks, statuses = app_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        sandbox,
        "start_recording",
        lambda *_a, **_k: SimpleNamespace(
            output_path=str(tmp_path / "result.mp3"),
            poll=lambda: 0,
        ),
    )
    assert radio.start_radio_recording(app)
    jobs.pop(0)()
    assert radio.start_radio_recording(app)
    assert app.radio_record_starting and len(jobs) == 1
    for cb in callbacks:
        cb()
    assert not any("gespeichert" in value for value in statuses)
    jobs.pop(0)()
    for cb in callbacks:
        cb()
    assert not app.radio_record_starting


def test_start_failure_has_no_direct_ffmpeg_fallback_or_sensitive_log(
    monkeypatch, tmp_path
):
    app, jobs, callbacks, statuses = app_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        sandbox,
        "start_recording",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("secret-token")),
    )
    assert radio.start_radio_recording(app)
    jobs.pop()()
    for cb in callbacks:
        cb()
    assert not app.radio_record_starting and app.radio_record_proc is None
    assert statuses[-1] == "Geschützte Aufnahme fehlgeschlagen."
    assert not any("secret-token" in value for value in statuses)


class SlowRecording:
    """A recording whose encoder flush is controlled by the test."""

    def __init__(self, path):
        self.output_path = str(path)
        self.stop_seen = threading.Event()
        self.flushed = threading.Event()
        self.calls = []

    def poll(self):
        self.calls.append(("poll", threading.get_ident()))
        return 0 if self.flushed.is_set() else None

    def terminate(self):
        self.calls.append(("terminate", threading.get_ident()))
        self.stop_seen.set()

    def kill(self):
        self.calls.append(("kill", threading.get_ident()))
        self.flushed.set()

    def wait(self, timeout=None):
        self.calls.append(("wait", threading.get_ident()))
        if not self.flushed.wait(timeout):
            raise sandbox.subprocess.TimeoutExpired("controlled encoder", timeout)
        return 0


@pytest.fixture
def live_recording(monkeypatch, tmp_path):
    from collections import deque
    import time

    callbacks, statuses, workers = deque(), [], []
    station = {"id": "test", "name": "Test", "url": "https://example.com/live"}
    app = SimpleNamespace(
        radio_current_station=station,
        radio_current_station_id="test",
        radio_stations=[station],
        radio_search_results=[station],
        radio_record_proc=None,
        radio_recordings_dir=str(tmp_path),
        netmon_state_dir=str(tmp_path),
    )
    proc = SlowRecording(tmp_path / "slow.mp3")
    monkeypatch.setattr(radio, "radio_recording_available", lambda _app: True)
    monkeypatch.setattr(radio, "refresh_radio_recording_ui", lambda _app: None)
    monkeypatch.setattr(
        radio, "_recording_status_text", lambda _app, text: statuses.append(text)
    )
    monkeypatch.setattr(
        radio, "_schedule_ui", lambda _app, cb: callbacks.append(cb) or True
    )

    def start(*_a, **_k):
        workers.append(threading.current_thread())
        return proc

    monkeypatch.setattr(sandbox, "start_recording", start)

    def until(predicate):
        deadline = time.monotonic() + 3
        while not predicate():
            assert time.monotonic() < deadline, "recording owner did not progress"
            time.sleep(0.005)

    assert radio.start_radio_recording(app)
    until(lambda: app.radio_record_proc is proc)
    try:
        yield app, proc, callbacks, statuses, workers, until
    finally:
        radio.stop_radio_recording(app)
        proc.flushed.set()
        for worker in workers:
            worker.join(3)
            assert not worker.is_alive()


def test_stop_hands_off_to_owner_without_waiting_and_blocks_overlap(live_recording):
    import time

    app, proc, callbacks, statuses, workers, until = live_recording
    # Even the old synchronous stopper is released after a bounded interval.
    release = threading.Timer(0.5, proc.flushed.set)
    release.start()
    try:
        before = time.monotonic()
        assert radio.stop_radio_recording(app)
        assert time.monotonic() - before < 0.2
        until(proc.stop_seen.is_set)
        assert workers[0].is_alive() and not workers[0].daemon
        assert not radio.start_radio_recording(app)
        assert radio.stop_radio_recording(app)
        assert app.radio_record_stopping
        proc.flushed.set()
        until(lambda: not app.radio_record_stopping)
        for cb in callbacks:
            cb()
        assert statuses[-1] == "Aufnahme gestoppt."
        assert [name for name, _tid in proc.calls].count("terminate") == 1
        assert all(tid == workers[0].ident for _name, tid in proc.calls)
    finally:
        release.cancel()
        release.join()


def test_old_recording_completion_cannot_overwrite_next_start(
    live_recording, monkeypatch
):
    app, proc, callbacks, statuses, workers, until = live_recording
    assert radio.stop_radio_recording(app)
    proc.flushed.set()
    until(lambda: not getattr(app, "radio_record_stopping", False))
    workers[0].join(3)
    next_proc = SlowRecording(proc.output_path + ".next")
    monkeypatch.setattr(sandbox, "start_recording", lambda *_a, **_k: next_proc)
    try:
        assert radio.start_radio_recording(app)
        until(lambda: app.radio_record_proc is next_proc)
        # Publish queued completions from the old generation only now.
        for _ in range(len(callbacks)):
            callbacks.popleft()()
        assert app.radio_record_proc is next_proc
        assert statuses[-1].startswith("Aufnahme läuft:")
    finally:
        radio.stop_radio_recording(app)
        next_proc.flushed.set()


@pytest.mark.parametrize("close", [False, True])
def test_tk_keeps_running_during_recording_stop(live_recording, monkeypatch, close):
    import tkinter as tk
    import time
    from netmon.netmon_radio_app import NetMonRadioApp
    from netmon import netmon_radio_core

    app, proc, _callbacks, _statuses, _workers, _until = live_recording
    root = tk.Tk()
    root.withdraw()
    heartbeats, durations = [], []
    app.after = root.after
    app.stop_radio_recording = lambda: radio.stop_radio_recording(app)
    app.close_radio_miniplayer = lambda: None
    app.close_custom_radio_station_editor = lambda: None
    app.close_projectm_visualizer_test = lambda: None
    app.stop_radio_playback = lambda **_k: None
    app.destroy = lambda: None
    app._on_close = lambda: NetMonRadioApp._on_close(app)
    monkeypatch.setattr(netmon_radio_core, "read_radio_host_state", lambda: {})
    monkeypatch.setattr(netmon_radio_core, "netmon_host_is_available", lambda: False)
    watchdog = threading.Timer(0.6, proc.flushed.set)
    watchdog.start()

    def stop():
        before = time.monotonic()
        if close:
            app._on_close()
        else:
            radio.stop_radio_recording(app)
        durations.append(time.monotonic() - before)

    root.after(0, stop)
    root.after(20, lambda: heartbeats.append(not proc.flushed.is_set()))
    root.after(80, proc.flushed.set)
    root.after(200, root.quit)
    try:
        root.mainloop()
        assert durations and durations[0] < 0.2
        assert heartbeats == [True]
    finally:
        proc.flushed.set()
        watchdog.cancel()
        watchdog.join()
        root.destroy()


def test_controller_stop_flushes_real_encoder_and_reaps_children(monkeypatch, tmp_path):
    import time

    real_thread = threading.Thread
    app, jobs, callbacks, statuses = app_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(radio.threading, "Thread", real_thread)
    source = "import sys,time;sys.stdout.buffer.write(b'M');sys.stdout.buffer.flush();time.sleep(20)"
    encoder = f"import os,sys;sys.stdin.buffer.read(1);os.write(1,b'encoded');os.write(2,{PROGRESS!r});sys.stdin.buffer.read();os.write(1,b'flushed')"
    children = controlled_pipeline(monkeypatch, tmp_path, encoder, source)
    assert radio.start_radio_recording(app)
    request = app.radio_record_request
    deadline = time.monotonic() + 3
    try:
        while app.radio_record_proc is None:
            assert time.monotonic() < deadline
            time.sleep(0.005)
        assert radio.stop_radio_recording(app)
        assert request.done.wait(3)
        assert Path(app.radio_last_record_path).read_bytes() == b"encodedflushed"
        assert all(child.poll() is not None for child in children)
        assert not list(tmp_path.glob("record-*"))
        for cb in callbacks:
            cb()
        assert statuses[-1] == "Aufnahme gestoppt."
    finally:
        radio.stop_radio_recording(app)
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=3)
        assert request.done.wait(3)


def test_recording_controls_never_poll_from_ui(monkeypatch):
    from netmon.netmon_radio_app import NetMonRadioApp

    calls = []
    proc = SimpleNamespace(poll=lambda: pytest.fail("UI must not poll/reap recording"))
    app = SimpleNamespace(
        radio_record_proc=proc,
        stop_radio_recording=lambda: calls.append("stop") or True,
        start_radio_recording=lambda: pytest.fail("active recording restarted"),
    )
    monkeypatch.setattr(radio, "_radio_targets", lambda _app: [])
    radio.refresh_radio_recording_ui(app)
    assert NetMonRadioApp.toggle_radio_recording(app)
    assert calls == ["stop"]


def test_failed_ui_queue_stops_owned_recording(live_recording, monkeypatch):
    app, proc, callbacks, statuses, workers, until = live_recording
    # Finish generation one, then exercise a rejected publication on generation two.
    assert radio.stop_radio_recording(app)
    proc.flushed.set()
    workers[0].join(3)
    next_proc = SlowRecording(proc.output_path + ".next")
    next_proc.flushed.set()
    monkeypatch.setattr(sandbox, "start_recording", lambda *_a, **_k: next_proc)
    monkeypatch.setattr(radio, "_schedule_ui", lambda *_a: False)
    assert radio.start_radio_recording(app)
    request = app.radio_record_request
    assert request.done.wait(3)
    assert next_proc.stop_seen.is_set()
    assert app.radio_record_proc is None


def test_cancelled_preparation_failure_preserves_stop_status(monkeypatch, tmp_path):
    app, jobs, callbacks, statuses = app_fixture(tmp_path, monkeypatch)

    def start(*_a, **_k):
        assert radio.stop_radio_recording(app)
        raise RuntimeError("cancelled helper failure with private data")

    monkeypatch.setattr(sandbox, "start_recording", start)
    assert radio.start_radio_recording(app)
    jobs.pop()()
    for cb in callbacks:
        cb()
    assert statuses[-1] == "Aufnahme gestoppt."
    assert app.radio_record_proc is None
    assert not app.radio_record_starting and not app.radio_record_stopping


# -- G-Quota for recording: 2 GiB bound and limited capsules ----------------


@pytest.mark.parametrize("written,expected", [(9, False), (10, True), (11, True)])
def test_encoder_stopped_at_size_bound_is_reported(
    monkeypatch, tmp_path, written, expected
):
    monkeypatch.setattr(sandbox, "RECORDING_MAX_BYTES", 10)
    # Progress first, then fail only after start_recording has returned.
    source = "import sys,time;sys.stdout.buffer.write(b'M');sys.stdout.buffer.flush();time.sleep(0.5)"
    encoder = (
        f"import os,sys;sys.stdin.buffer.read(1);os.write(1,b'encoded');os.write(2,{PROGRESS!r});"
        f"sys.stdin.buffer.read();os.write(1,b'X'*{written - 7});sys.exit(1)"
    )
    controlled_pipeline(monkeypatch, tmp_path, encoder, source)
    proc = sandbox.start_recording(
        "https://example.com/s", tmp_path / "big.mp3", work_root=tmp_path
    )
    assert proc.wait(timeout=3) != 0
    assert proc.size_limit_reached is expected


@pytest.mark.parametrize(
    "missing,encoder_rc,source_rc,expected",
    [
        (512 * 1024, 23, 0, False),
        (1, 23, 0, False),
        (0, 23, 0, True),
        (0, 0, 23, False),
        (0, 153, 23, True),
    ],
)
def test_size_bound_requires_full_file_and_encoder_failure(
    tmp_path, missing, encoder_rc, source_rc, expected
):
    target = tmp_path / "record.mp3"
    # Sparse size only; no 2 GiB data or real encoder run is needed here.
    with target.open("wb") as stream:
        stream.truncate(sandbox.RECORDING_MAX_BYTES - missing)
    progress_fd, write_fd = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
    temporary = tempfile.TemporaryDirectory(dir=tmp_path)
    proc = sandbox.RecordingProcess(
        SimpleNamespace(poll=lambda: encoder_rc),
        SimpleNamespace(poll=lambda: source_rc),
        temporary,
        str(target),
        progress_fd,
    )
    try:
        assert proc.poll() == (source_rc or encoder_rc)
        assert proc.size_limit_reached is expected
        assert proc.poll() == (source_rc or encoder_rc)
    finally:
        os.close(write_fd)
        proc._progress_file.close()
        temporary.cleanup()


def test_successful_recording_never_claims_size_bound(monkeypatch, tmp_path):
    monkeypatch.setattr(sandbox, "RECORDING_MAX_BYTES", 1)
    controlled_pipeline(monkeypatch, tmp_path, encoder_script())
    proc = sandbox.start_recording(
        "https://example.com/s", tmp_path / "ok.mp3", work_root=tmp_path
    )
    assert proc.wait(timeout=3) == 0 and proc.size_limit_reached is False


def test_recording_capsules_start_limited_with_2_gib_file_bound(monkeypatch, tmp_path):
    monkeypatch.setattr(sandbox, "recording_available", lambda: True)
    monkeypatch.setattr(sandbox, "_network_files", lambda: ())
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))
    monkeypatch.setattr(sandbox, "_runtime_files", lambda *_a, **_k: ())
    started = []

    class Stop(Exception):
        pass

    def spawn(argv, **kwargs):
        started.append((argv, kwargs["env"]))
        if len(started) == 2:
            raise Stop()

        class Child:
            def poll(self):
                return 0

            def kill(self):
                pass

            def wait(self, timeout=None):
                return 0

        return Child()

    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    with pytest.raises(Stop):
        sandbox.start_recording(
            "https://example.com/s", tmp_path / "r.mp3", work_root=tmp_path
        )
    profiles = [argv[5].split("-")[4] for argv, _env in started]
    assert profiles == ["fetch", "encoder"]
    encoder = started[1][0]
    assert encoder[0] == str(sandbox.SYSTEMD_RUN)
    assert f"--fsize={2 << 30}:{2 << 30}" in encoder
    assert sandbox.RECORDING_MAX_BYTES == 2 << 30
    assert all(env == sandbox._quota_env() for _argv, env in started)


def test_recording_without_user_manager_starts_nothing(monkeypatch, tmp_path):
    monkeypatch.setattr(sandbox, "recording_available", lambda: True)
    monkeypatch.setattr(sandbox.os, "getuid", lambda: 2**31 - 7)
    monkeypatch.setattr(
        sandbox.subprocess, "Popen", lambda *_a, **_k: pytest.fail("process started")
    )
    with pytest.raises(sandbox.RadioSandboxError, match="Ressourcengrenzen"):
        sandbox.start_recording(
            "https://example.com/s", tmp_path / "r.mp3", work_root=tmp_path
        )
    assert not list(tmp_path.iterdir())


def test_controller_names_the_size_bound():
    import inspect

    source = inspect.getsource(radio)
    assert "Höchstgröße 2 GB erreicht" in source
    assert 'getattr(record_proc, "size_limit_reached", False)' in source
