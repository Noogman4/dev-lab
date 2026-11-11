"""Real harmless process trees, only under the existing isolated starter."""

import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from netmon.core import projectm_process as ownership
from netmon import netmon_projectm_sidecar as sidecar

pytestmark = pytest.mark.skipif(
    os.environ.get("NETMON_TEST_ISOLATED") != "1",
    reason="Process fixtures require tests/run_isolated_suite.py",
)

SCRIPT = """
import os, signal, sys, time
from pathlib import Path
directory = Path(sys.argv[1])
mode = sys.argv[2]
if mode == 'tree':
    child = os.fork()
    if child == 0:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        (directory / 'child').write_text(str(os.getpid()))
        while True: time.sleep(1)
(directory / 'ready').write_text(str(os.getpid()))
while True: time.sleep(1)
"""


def wait_for(predicate, timeout=4):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.01)
    raise AssertionError("Private process fixture did not become ready")


@pytest.fixture
def processes(tmp_path):
    children = []

    def spawn(mode="single", name="fixture"):
        directory = tmp_path / name
        directory.mkdir()
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                SCRIPT,
                str(directory),
                mode,
                "projectm-pulseaudio",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
        tracked = ownership.OwnedProcess(process)
        children.append(tracked)
        wait_for(lambda: (directory / "ready").exists())
        if mode == "tree":
            wait_for(lambda: (directory / "child").exists())
        tracked.capture_descendants()
        return tracked, directory

    yield spawn
    for process in children:
        assert process.stop()


def test_stop_preserves_identically_named_foreign_process(processes, monkeypatch):
    own, _ = processes("tree", "own")
    foreign, _ = processes("single", "foreign")
    assert len(own.pids) == 2
    app = SimpleNamespace(
        radio_projectm_proc=own,
        # Neither a stale PID cache nor command names confer ownership.
        radio_projectm_known_pids={foreign.pid},
        radio_projectm_command=["flatpak", "run", sidecar.PROJECTM_FLATPAK_APP_ID],
        radio_projectm_log_handle=io.StringIO(),
        radio_projectm_log_path="",
    )

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Global PID/group/app-ID signaling is forbidden")

    monkeypatch.setattr(sidecar.os, "kill", forbidden)
    monkeypatch.setattr(sidecar.os, "killpg", forbidden)
    monkeypatch.setattr(sidecar.subprocess, "run", forbidden)
    assert sidecar.stop_projectm_sidecar(app)
    assert own.poll() is not None
    assert foreign.poll() is None
    assert app.radio_projectm_proc is None
    assert app.radio_projectm_log_handle is None
    assert app.radio_projectm_known_pids == set()
    assert not sidecar.stop_projectm_sidecar(app)


def test_captured_child_remains_owned_after_launcher_exit(processes):
    own, directory = processes("tree")
    child = int((directory / "child").read_text())
    root_fd = own._handles[own.pid]
    signal.pidfd_send_signal(root_fd, signal.SIGTERM)
    own.process.wait(timeout=2)
    assert own.poll() is None
    assert own.pids == {child}
    assert own.stop()
    assert own.poll() is not None
    assert not own._handles


def test_stop_never_adopts_old_pid_lists_or_raw_process_objects(processes):
    foreign, _ = processes()
    app = SimpleNamespace(
        radio_projectm_proc=foreign.process,
        radio_projectm_known_pids={foreign.pid},
    )
    assert not sidecar.stop_projectm_sidecar(app)
    assert foreign.poll() is None
    app.radio_projectm_proc = None
    assert not sidecar.stop_projectm_sidecar(app)
    assert foreign.poll() is None


def test_poll_releases_handles_only_after_all_owned_tasks_exit(processes):
    own, _ = processes()
    handles = list(own._handles.values())
    signal.pidfd_send_signal(handles[0], signal.SIGTERM)
    own.process.wait(timeout=2)
    assert own.poll() is not None
    for descriptor in handles:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    assert own.poll() is not None
    assert own.stop()


def test_failed_stop_preserves_owner_for_retry(processes, monkeypatch):
    own, _ = processes()
    app = SimpleNamespace(radio_projectm_proc=own)
    with monkeypatch.context() as patch:
        patch.setattr(own, "_wait", lambda _timeout: False)

        def denied(*_args):
            raise PermissionError("fixture signal denied")

        patch.setattr(ownership.signal, "pidfd_send_signal", denied)
        patch.setattr(
            own.process,
            "wait",
            lambda **_: (_ for _ in ()).throw(subprocess.TimeoutExpired("fixture", 1)),
        )
        assert not sidecar.stop_projectm_sidecar(app)
        assert app.radio_projectm_proc is own
        assert own.pids == {own.pid}
    assert sidecar.stop_projectm_sidecar(app)


def test_log_failure_does_not_retain_stopped_owner(processes, monkeypatch):
    own, _ = processes()
    app = SimpleNamespace(
        radio_projectm_proc=own, radio_projectm_log_path="fixture.log"
    )

    def denied(*_args):
        raise OSError("fixture disk error")

    monkeypatch.setattr(sidecar, "_append_log", denied)
    assert sidecar.stop_projectm_sidecar(app)
    assert app.radio_projectm_proc is None


def test_disappearing_root_does_not_adopt_replacement_pid(monkeypatch):
    descriptor, writer = os.pipe()
    process = SimpleNamespace(pid=12345, poll=lambda: 0)
    monkeypatch.setattr(ownership.os, "pidfd_open", lambda _pid: descriptor)
    try:
        owned = ownership.OwnedProcess(process)
        assert not owned._handles
        with pytest.raises(OSError):
            os.fstat(descriptor)
    finally:
        os.close(writer)


def test_reparented_candidate_is_rejected_after_open(monkeypatch, processes):
    own, _ = processes()
    read_fd, write_fd = os.pipe()
    original_open = os.pidfd_open
    ancestry = iter([True, False])
    monkeypatch.setattr(
        ownership.Path, "iterdir", lambda _self: iter([Path("/proc/123456")])
    )
    monkeypatch.setattr(ownership, "_descends_from", lambda *_: next(ancestry))
    monkeypatch.setattr(ownership.os, "pidfd_open", lambda _pid: read_fd)
    try:
        own.capture_descendants()
        assert 123456 not in own._handles
        with pytest.raises(OSError):
            os.fstat(read_fd)
    finally:
        os.close(write_fd)
        monkeypatch.setattr(ownership.os, "pidfd_open", original_open)
        monkeypatch.undo()


@pytest.fixture
def launcher(monkeypatch, tmp_path, processes):
    from netmon.core import projectm_frontend as frontend, radio_sandbox as sandbox
    from test_radio_sandbox import Child

    playback = sandbox.SandboxProcess(
        Child(), SimpleNamespace(name=str(tmp_path), cleanup=lambda: None)
    )
    state = SimpleNamespace(
        start_gate=threading.Event(),
        entered=threading.Event(),
        stop_gate=threading.Event(),
        sessions=[],
        calls=[],
        failure=False,
        exited=False,
        unknown=None,
    )
    state.start_gate.set()
    state.stop_gate.set()
    app = SimpleNamespace(
        radio_proc=playback,
        radio_projectm_preset_dir=str(tmp_path),
        radio_stop_requested=False,
    )
    state.app = app
    metadata = sidecar.ProjectMSidecarStatus(
        True, True, False, "fixture", "fixture", backend_label="Fixture"
    )
    app._projectm_detected_status = metadata
    app._projectm_probe_time = time.monotonic()

    class Session(frontend.FrontendSession):
        def __init__(self, owned):
            self.owned = owned
            self.pid = owned.pid
            from netmon.core.projectm_pixels import FrameMailbox

            self.pixels = SimpleNamespace(frames=FrameMailbox())

        def poll(self):
            return 7 if state.exited else self.owned.poll()

        def stop(self):
            assert state.stop_gate.wait(4)
            assert self.owned.stop()

    def start(
        playback_arg,
        preset_dir,
        *,
        cancelled,
        resolution="640x480",
        preset_name=None,
        cpu_profile="standard",
        backend="cpu",
    ):
        state.calls.append((playback_arg, preset_dir, cancelled, threading.get_ident()))
        state.entered.set()
        assert state.start_gate.wait(4)
        if state.failure:
            raise RuntimeError("synthetic protected start failure")
        if state.unknown is not None:
            return state.unknown
        own, _ = processes(name="protected-" + str(len(state.sessions)))
        session = Session(own)
        state.sessions.append(session)
        return session

    monkeypatch.setattr(frontend, "start", start)
    yield state
    state.start_gate.set()
    state.stop_gate.set()
    request = vars(app).get("radio_projectm_proc")
    if isinstance(request, sidecar._ProjectMRequest):
        request.stop()
        if request.thread.ident is not None:
            request.thread.join(timeout=4)


def request_running(launcher):
    request = launcher.app.radio_projectm_proc
    wait_for(lambda: request.snapshot()[0] == "running")
    return request


@pytest.mark.parametrize(
    "app", [None, SimpleNamespace(), SimpleNamespace(radio_proc=object())]
)
def test_launch_requires_owned_radio_playback_before_backend(monkeypatch, app):
    monkeypatch.setattr(
        sidecar.projectm_frontend,
        "start",
        lambda *a, **k: pytest.fail("Backend reached"),
    )
    result = sidecar.launch_projectm_sidecar(app)
    assert not result.launched and not result.starting


def test_asynchronous_start_has_one_owner_and_preserves_foreign_process(
    launcher, processes
):
    foreign, _ = processes(name="foreign")
    launcher.start_gate.clear()
    result = sidecar.launch_projectm_sidecar(launcher.app)
    assert result.starting and not result.launched
    assert launcher.entered.wait(2)
    again = sidecar.launch_projectm_sidecar(launcher.app)
    assert again.starting and len(launcher.calls) == 1
    launcher.start_gate.set()
    request = request_running(launcher)
    assert launcher.calls[0][3] != threading.get_ident()
    assert request.thread.is_alive()
    assert sidecar.launch_projectm_sidecar(launcher.app).launched
    assert sidecar.stop_projectm_sidecar(launcher.app)
    assert request.done.wait(3)
    assert foreign.poll() is None
    assert launcher.sessions[0].poll() is not None


def test_late_start_after_stop_is_reaped_without_publication(launcher):
    launcher.start_gate.clear()
    sidecar.launch_projectm_sidecar(launcher.app)
    assert launcher.entered.wait(2)
    request = launcher.app.radio_projectm_proc
    assert sidecar.stop_projectm_sidecar(launcher.app)
    assert request.snapshot()[0] == "stopping" and request.pid == 0
    launcher.start_gate.set()
    assert request.done.wait(3)
    assert request.poll() == 0 and request.pid == 0
    assert launcher.sessions[0].poll() is not None


def test_protected_start_failure_never_uses_direct_launcher(launcher, monkeypatch):
    launcher.failure = True
    monkeypatch.setattr(
        sidecar,
        "_build_projectm_launch_command",
        lambda *a, **k: pytest.fail("Unprotected fallback"),
    )
    sidecar.launch_projectm_sidecar(launcher.app)
    request = launcher.app.radio_projectm_proc
    assert request.done.wait(2)
    assert (
        request.poll() == 2
        and "synthetic protected start failure" in request.snapshot()[1]
    )
    assert not launcher.sessions


def test_unknown_backend_result_confers_no_stop_authority(launcher, processes):
    foreign, _ = processes(name="foreign-result")
    launcher.unknown = foreign
    sidecar.launch_projectm_sidecar(launcher.app)
    assert launcher.app.radio_projectm_proc.done.wait(2)
    assert launcher.app.radio_projectm_proc.poll() == 2
    assert foreign.poll() is None


def test_stop_restart_waits_for_previous_cleanup_and_old_status_cannot_clear_new(
    launcher,
):
    sidecar.launch_projectm_sidecar(launcher.app)
    old = request_running(launcher)
    launcher.stop_gate.clear()
    sidecar.stop_projectm_sidecar(launcher.app)
    sidecar.launch_projectm_sidecar(launcher.app)
    new = launcher.app.radio_projectm_proc
    assert new is not old
    assert not old.done.wait(0.1) and len(launcher.calls) == 1
    sidecar.describe_projectm_sidecar_runtime(launcher.app)
    assert launcher.app.radio_projectm_proc is new
    launcher.stop_gate.set()
    request_running(launcher)
    assert old.done.is_set() and len(launcher.calls) == 2


def test_repeated_stop_start_cannot_skip_a_still_closing_owner(launcher):
    sidecar.launch_projectm_sidecar(launcher.app)
    oldest = request_running(launcher)
    launcher.stop_gate.clear()
    sidecar.stop_projectm_sidecar(launcher.app)
    sidecar.launch_projectm_sidecar(launcher.app)
    middle = launcher.app.radio_projectm_proc
    sidecar.stop_projectm_sidecar(launcher.app)
    sidecar.launch_projectm_sidecar(launcher.app)
    newest = launcher.app.radio_projectm_proc
    assert newest is not middle
    time.sleep(0.15)
    assert len(launcher.calls) == 1 and not oldest.done.is_set()
    launcher.stop_gate.set()
    request_running(launcher)
    assert middle.done.is_set() and oldest.done.is_set() and len(launcher.calls) == 2


def test_playback_identity_change_revokes_pending_result(launcher):
    launcher.start_gate.clear()
    sidecar.launch_projectm_sidecar(launcher.app)
    assert launcher.entered.wait(2)
    request = launcher.app.radio_projectm_proc
    launcher.app.radio_proc = object()
    launcher.start_gate.set()
    assert request.done.wait(3) and request.pid == 0
    assert launcher.sessions[0].poll() is not None


def test_old_eof_cannot_revoke_new_playback_request(launcher):
    sidecar.launch_projectm_sidecar(launcher.app)
    request = request_running(launcher)
    assert not sidecar.invalidate_projectm_playback(launcher.app, object())
    assert not request.cancelled.is_set()
    assert sidecar.invalidate_projectm_playback(launcher.app, launcher.app.radio_proc)
    assert request.done.wait(3)


def test_radio_stop_revokes_pending_request_even_after_radio_reference_is_gone(
    launcher,
):
    from netmon.features import radio_controller

    launcher.start_gate.clear()
    sidecar.launch_projectm_sidecar(launcher.app)
    assert launcher.entered.wait(2)
    request = launcher.app.radio_projectm_proc
    launcher.app.radio_proc = None
    assert radio_controller.stop_radio_playback(launcher.app)
    assert request.cancelled.is_set()
    launcher.start_gate.set()
    assert request.done.wait(3)


def test_status_and_stop_do_not_wait_for_capsule_cleanup(launcher):
    sidecar.launch_projectm_sidecar(launcher.app)
    request = request_running(launcher)
    launcher.stop_gate.clear()
    sidecar.stop_projectm_sidecar(launcher.app)
    before = time.monotonic()
    state = sidecar.describe_projectm_sidecar_runtime(launcher.app)
    assert time.monotonic() - before < 0.2
    assert state["phase"] == "stopping" and not state["runtime_verified"]
    assert not request.done.is_set()
    launcher.stop_gate.set()
    assert request.done.wait(3)


def test_owner_thread_start_failure_is_reported_without_any_backend(
    launcher, monkeypatch
):
    def fail(*_):
        raise RuntimeError("synthetic owner thread failure")

    monkeypatch.setattr(threading.Thread, "start", fail)
    status = sidecar.launch_projectm_sidecar(launcher.app)
    assert not status.launched and not status.starting
    request = launcher.app.radio_projectm_proc
    assert request.done.is_set() and request.poll() == 2 and not launcher.calls


def test_backend_already_ended_is_never_published_as_running(launcher):
    launcher.exited = True
    result = sidecar.launch_projectm_sidecar(launcher.app)
    assert result.starting
    request = launcher.app.radio_projectm_proc
    assert request.done.wait(3)
    assert request.poll() == 2 and request.pid == 0
    assert launcher.sessions[0].owned.poll() is not None


def test_parent_parser_handles_parentheses_and_invalid_proc(monkeypatch):
    monkeypatch.setattr(Path, "read_text", lambda _self: "123 (test ) name) S 45 1")
    assert ownership._parent(123) == 45
    monkeypatch.setattr(Path, "read_text", lambda _self: "broken")
    assert ownership._parent(123) is None
