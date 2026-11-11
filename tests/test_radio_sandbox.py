"""Playback policy tests; real first-level probes use the isolated starter."""

from types import SimpleNamespace
import os
import threading

import pytest

from netmon.core import radio_sandbox as sandbox
from netmon.features import radio_controller as radio


class Child:
    def __init__(self, result=None):
        self.result = result
        self.signals = []

    def poll(self):
        return self.result

    def kill(self):
        self.signals.append("kill")
        self.result = -9

    def terminate(self):
        self.signals.append("terminate")
        self.result = -15

    def wait(self, timeout=None):
        assert self.result is not None
        return self.result


class FakeOutput:
    def __init__(self, lost=False, events=None):
        self._lost = lost
        self.events = events if events is not None else []
        self.descriptor = None

    def lost(self):
        return self._lost

    def silence(self):
        self.events.append("silence")

    def handed_over(self):
        self.events.append("handed_over")

    def close(self):
        self.events.append("close")


class FakeGate:
    def __init__(self, events=None, *, done=False, error=None):
        self.events = events if events is not None else []
        self.done = threading.Event()
        if done:
            self.done.set()
        self.error = error

    def request_stop(self):
        self.events.append("gate-stop")

    def close(self):
        self.events.append("gate-close")
        self.done.set()


def session(tmp_path, cleaned=None):
    return SimpleNamespace(
        name=str(tmp_path),
        cleanup=lambda: cleaned.append(True) if cleaned is not None else None,
    )


def test_lost_output_stops_everything_without_relinking(tmp_path):
    decoder, relay, source = Child(), Child(), Child()
    output, cleaned = FakeOutput(lost=True), []
    process = sandbox.SandboxProcess(
        decoder, session(tmp_path, cleaned), output, source, relay
    )
    assert process.wait(timeout=0.1) == 1
    assert process.output_lost is True
    assert decoder.signals == relay.signals == source.signals == ["kill"]
    assert output.events[0] == "silence" and output.events[-1] == "close"
    assert cleaned == [True]


def test_source_failure_ends_decoder_and_output(tmp_path):
    decoder, relay, source, output = Child(), Child(), Child(2), FakeOutput()
    process = sandbox.SandboxProcess(decoder, session(tmp_path), output, source, relay)
    assert process.wait(timeout=0.1) == 2
    assert decoder.signals == relay.signals == ["kill"]
    assert "close" in output.events


def test_natural_eof_plays_out_the_paced_lead_then_unlinks(monkeypatch, tmp_path):
    decoder, relay, source, output = Child(0), Child(0), Child(), FakeOutput()
    clock = [10.0]
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])
    process = sandbox.SandboxProcess(decoder, session(tmp_path), output, source, relay)
    assert process.poll() is None
    assert source.signals == ["kill"]
    assert output.events == []
    clock[0] += sandbox.SandboxProcess.OUTPUT_DRAIN + 0.01
    assert process.poll() == 0
    assert output.events == ["close"]  # FifoOutput.close() unlinks first


@pytest.mark.parametrize("signal", ["terminate", "kill"])
def test_stop_unlinks_before_signalling_any_process(tmp_path, signal):
    events = []

    class Ordered(Child):
        def terminate(self):
            events.append("signal")
            super().terminate()

        def kill(self):
            events.append("signal")
            super().kill()

    decoder, relay, source = Ordered(), Ordered(), Ordered()
    output = FakeOutput(events=events)
    process = sandbox.SandboxProcess(decoder, session(tmp_path), output, source, relay)
    getattr(process, signal)()
    assert events[0] == "silence"
    assert process.wait(timeout=0.1) != 0
    assert decoder.signals == relay.signals == source.signals == [signal]


def test_failed_unlink_does_not_prevent_stop(tmp_path):
    class Broken(FakeOutput):
        def silence(self):
            raise RuntimeError("pw-link failed")

    decoder = Child()
    process = sandbox.SandboxProcess(decoder, session(tmp_path), Broken())
    process.terminate()
    assert decoder.signals == ["terminate"]


def prepared_start(monkeypatch, tmp_path, output):
    (tmp_path / "media").write_bytes(b"synthetic")
    monkeypatch.setattr(sandbox, "available", lambda: True)
    monkeypatch.setattr(sandbox, "_runtime_files", lambda _path: ())
    monkeypatch.setattr(sandbox, "_pcm_runtime", lambda: (tmp_path, ()))
    monkeypatch.setattr(sandbox, "_network_files", lambda: ())
    monkeypatch.setattr(sandbox, "_open_output", output)
    # The isolated suite has no user manager; quota checks have own tests.
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    return [
        "mpv",
        f"--input-ipc-server={sandbox.IPC_PATH}",
        "--",
        str(tmp_path / "media"),
    ]


def test_output_not_ready_starts_no_process(monkeypatch, tmp_path):
    def not_ready():
        raise sandbox.RadioSandboxError("Geschützte Radioausgabe nicht bereit: x")

    command = prepared_start(monkeypatch, tmp_path, not_ready)
    monkeypatch.setattr(
        sandbox.subprocess, "Popen", lambda *_a, **_k: pytest.fail("process started")
    )
    with pytest.raises(sandbox.RadioSandboxError, match="nicht bereit"):
        sandbox.start_playback(
            command, ipc_root=tmp_path, local_file=tmp_path / "media"
        )
    assert not list(tmp_path.glob("play-*"))


@pytest.mark.parametrize("failure", ["relay-spawn", "decoder-spawn", "handshake"])
def test_failed_start_reaps_gate_and_releases_output(monkeypatch, tmp_path, failure):
    output = FakeOutput()
    fifo_read, output.descriptor = os.pipe()
    pcm = Child()
    raw = Child()
    descriptors = []
    gates = []
    real_gate = sandbox._PcmOutputGate

    def capture_gate(*args):
        gate = real_gate(*args)
        gates.append(gate)
        return gate

    monkeypatch.setattr(sandbox, "_PcmOutputGate", capture_gate)
    command = prepared_start(monkeypatch, tmp_path, lambda: output)

    def spawn(command, **kwargs):
        assert str(sandbox.PACAT) not in command
        assert "/run/audio/pulse" not in command
        if "/run/pcm.py" in command:
            assert kwargs["stdout"] != output.descriptor
            assert (
                os.fstat(kwargs["stdout"]).st_ino != os.fstat(output.descriptor).st_ino
            )
            assert kwargs["close_fds"] is True and "pass_fds" not in kwargs
            descriptors.extend((kwargs["stdin"], kwargs["stdout"]))
            if failure == "relay-spawn":
                raise OSError("synthetic spawn error")
            return pcm
        descriptors.append(kwargs["stdout"])
        assert kwargs["close_fds"] is True
        if failure == "handshake":
            return raw
        raise OSError("synthetic spawn error")

    def no_handshake(_process):
        raise OSError("synthetic handshake error")

    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    monkeypatch.setattr(sandbox, "_wait_for_ipc", no_handshake)
    try:
        with pytest.raises(OSError, match="synthetic"):
            sandbox.start_playback(
                command, ipc_root=tmp_path, local_file=tmp_path / "media"
            )
    finally:
        os.close(fifo_read)
        os.close(output.descriptor)
    assert pcm.signals == ([] if failure == "relay-spawn" else ["kill"])
    assert raw.signals == (["kill"] if failure == "handshake" else [])
    assert output.events[-1] == "close" and "silence" in output.events
    assert ("handed_over" in output.events) is (failure != "relay-spawn")
    assert len(descriptors) == (2 if failure == "relay-spawn" else 3)
    assert len(gates) == 1 and gates[0].done.is_set()
    assert not gates[0]._thread.is_alive()
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    assert not list(tmp_path.glob("play-*"))


def test_gate_failure_stops_owned_processes_without_reconnecting(tmp_path):
    decoder, relay, source = Child(), Child(), Child()
    gate = FakeGate(done=True, error=OSError("lost writer"))
    output = FakeOutput()
    process = sandbox.SandboxProcess(
        decoder, session(tmp_path), output, source, relay, gate
    )
    assert process.wait(timeout=0.1) == 1
    assert process.output_lost
    assert decoder.signals == relay.signals == source.signals == ["kill"]
    assert output.events[0] == "silence"
    assert gate.events[-1] == "gate-close"


def test_eof_waits_for_gate_before_audio_drain(monkeypatch, tmp_path):
    clock = [10.0]
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])
    gate, output = FakeGate(), FakeOutput()
    process = sandbox.SandboxProcess(
        Child(0), session(tmp_path), output, None, Child(0), gate
    )
    assert process.poll() is None and output.events == []
    gate.done.set()
    assert process.poll() is None and output.events == []
    clock[0] += process.OUTPUT_DRAIN + 0.01
    assert process.poll() == 0
    assert gate.events == ["gate-close"] and output.events == ["close"]


def test_gate_eof_wait_has_a_deadline(monkeypatch, tmp_path):
    clock = [10.0]
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])
    gate, output = FakeGate(), FakeOutput()
    process = sandbox.SandboxProcess(
        Child(0), session(tmp_path), output, None, Child(0), gate
    )
    assert process.poll() is None
    clock[0] += 5.01
    assert process.poll() == 1 and process.output_lost
    assert output.events[0] == "silence"
    assert gate.events == ["gate-stop", "gate-close"]


@pytest.mark.parametrize("signal", ["terminate", "kill"])
def test_stop_requests_gate_cancel_without_joining(monkeypatch, tmp_path, signal):
    events = []
    gate, output = FakeGate(events), FakeOutput(events=events)
    process = sandbox.SandboxProcess(
        Child(), session(tmp_path), output, None, Child(), gate
    )
    getattr(process, signal)()
    assert events == ["silence", "gate-stop"]

    def close():
        assert not process._cleanup_lock._is_owned()
        events.append("gate-close")

    monkeypatch.setattr(gate, "close", close)
    assert process.wait(timeout=0.1) != 0
    assert events.index("gate-close") < events.index("close")


def test_open_output_fails_closed_and_releases_writer(monkeypatch, tmp_path):
    from netmon.core import radio_fifo_output as fifo

    events = []

    class Writer:
        def __init__(self, paths):
            pass

        def open(self):
            events.append("open")

        def close(self):
            events.append("close")

    monkeypatch.setattr(fifo, "paths", lambda: fifo.Paths(*(tmp_path,) * 5))
    monkeypatch.setattr(
        fifo, "setup_status", lambda _p: {"ready": False, "reasons": ["x"]}
    )
    with pytest.raises(sandbox.RadioSandboxError, match="nicht bereit: x"):
        sandbox._open_output()
    assert events == []
    monkeypatch.setattr(fifo, "setup_status", lambda _p: {"ready": True, "reasons": []})
    monkeypatch.setattr(fifo, "FifoWriter", Writer)

    def no_tunnel(_fifo):
        raise fifo.RadioOutputError("kein Tunnel")

    monkeypatch.setattr(fifo, "link", no_tunnel)
    with pytest.raises(sandbox.RadioSandboxError, match="kein Tunnel"):
        sandbox._open_output()
    assert events == ["open", "close"]


def test_fifo_output_silences_once_and_rate_limits_watchdog(monkeypatch):
    from netmon.core import radio_fifo_output as fifo

    calls = []
    clock = [100.0]
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(fifo, "unlink", lambda linked, run: calls.append("unlink"))
    monkeypatch.setattr(
        fifo, "verify", lambda linked, run: calls.append("verify") or False
    )
    writer = SimpleNamespace(fd=7, close=lambda: calls.append("close"))
    output = sandbox.FifoOutput(writer, object())
    assert output.lost() is False and calls == []
    clock[0] += output.VERIFY_INTERVAL
    assert output.lost() is True and calls == ["verify"]
    assert output.lost() is True and calls == ["verify"]
    output.silence()
    output.close()
    output.close()
    assert calls == ["verify", "unlink", "close"]


def test_radio_needs_no_pacat_anymore(monkeypatch):
    import inspect

    source = inspect.getsource(sandbox.start_playback)
    assert "PACAT" not in source and "_audio_socket" not in source
    assert "PACAT" not in inspect.getsource(sandbox.available)


def test_mpv_disables_ambient_configuration_and_helpers():
    command = radio._mpv_command(41, "https://example.invalid/s", sandbox.IPC_PATH)
    assert {"--no-config", "--load-scripts=no", "--no-ytdl", "--ao=pcm"} <= set(
        command[:-2]
    )
    assert command[-2:] == ["--", "https://example.invalid/s"]


def test_both_playback_paths_have_no_direct_process_fallback():
    import inspect

    for function in (radio.play_radio_station, radio._play_local_audio_file):
        source = inspect.getsource(function)
        assert "_start_radio_playback(" in source
        assert "subprocess.Popen" not in source


@pytest.mark.parametrize("local_file", [None, "/selected.wav"])
def test_controller_start_failure_is_not_announced_or_retried(
    monkeypatch, tmp_path, local_file
):
    app = SimpleNamespace(radio_sandbox_state="starting")
    monkeypatch.setattr(radio, "_radio_ipc_dir", lambda _app: str(tmp_path))
    monkeypatch.setattr(radio, "radio_eq_filter_spec", lambda _app: "")
    attempts = []

    def reject(command, **kwargs):
        attempts.append((command, kwargs))
        raise sandbox.RadioSandboxError("blocked")

    monkeypatch.setattr(sandbox, "start_playback", reject)
    with pytest.raises(sandbox.RadioSandboxError, match="blocked"):
        radio._start_radio_playback(app, 40, "source", local_file=local_file)
    assert app.radio_sandbox_state == "starting"
    assert not hasattr(app, "radio_ipc_path")
    assert not hasattr(app, "radio_proc")
    assert len(attempts) == 1
    assert attempts[0][1]["local_file"] == local_file


def test_controller_preparation_leaves_publication_to_lifecycle(monkeypatch, tmp_path):
    app = SimpleNamespace(radio_sandbox_state="starting")
    process = SimpleNamespace(ipc_path="/private/one/control/mpv.sock")
    monkeypatch.setattr(radio, "_radio_ipc_dir", lambda _app: str(tmp_path))
    monkeypatch.setattr(radio, "radio_eq_filter_spec", lambda _app: "")

    def start(command, **kwargs):
        assert app.radio_sandbox_state == "starting"
        assert f"--input-ipc-server={sandbox.IPC_PATH}" in command
        assert kwargs == {"ipc_root": str(tmp_path), "local_file": None}
        return process

    monkeypatch.setattr(sandbox, "start_playback", start)
    assert radio._start_radio_playback(app, 40, "https://example.invalid/s") is process
    assert app.radio_sandbox_state == "starting"
    assert not hasattr(app, "radio_ipc_path")


@pytest.mark.parametrize(
    "output",
    [
        "libbroken.so => not found\n",
        "lib.so => /home/user/lib.so (0x123)\n",
        "not a dynamic executable\n",
        "linux-vdso.so.1 (0x123)\n",
    ],
)
def test_unusable_library_plan_fails_closed(monkeypatch, output):
    monkeypatch.setattr(
        sandbox.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=output),
    )
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox._runtime_files(sandbox.MPV)


def test_audio_does_not_accept_a_file_or_ambient_remote_server(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("PULSE_SERVER", "tcp:example.invalid")
    (tmp_path / "pulse").mkdir()
    (tmp_path / "pulse/native").write_text("not a socket")
    with pytest.raises(sandbox.RadioSandboxError, match="nicht zulässig"):
        sandbox._audio_socket()


def test_missing_tools_do_not_attempt_an_unprotected_start(monkeypatch, tmp_path):
    monkeypatch.setattr(sandbox, "available", lambda: False)
    monkeypatch.setattr(
        sandbox.subprocess, "Popen", lambda *_a, **_k: pytest.fail("process started")
    )
    with pytest.raises(sandbox.RadioSandboxError, match="Bubblewrap"):
        sandbox.start_playback([], ipc_root=str(tmp_path))


@pytest.mark.parametrize(
    "reply",
    [
        b'{"request_id":18,"error":"success","data":"mpv"}\n',
        b'{"request_id":17,"error":"unknown","data":"mpv"}\n',
        b'{"request_id":17,"error":"success","data":""}\n',
        b"[]\n",
        b'{"event":"client-message"}\n',
    ],
)
def test_ipc_rejects_unknown_or_unsolicited_replies_with_a_deadline(monkeypatch, reply):
    import time

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def sendall(self, _request):
            pass

        def recv(self, _size):
            return reply

    monkeypatch.setattr(sandbox, "connect_mpv", lambda *_a, **_k: Client())
    process = SimpleNamespace(poll=lambda: None, ipc_path="/synthetic/socket")
    started = time.monotonic()
    with pytest.raises(sandbox.RadioSandboxError, match="Steuerkanal"):
        sandbox._wait_for_ipc(process, timeout=0.04)
    assert time.monotonic() - started < 1


@pytest.mark.parametrize("local", [False, True])
def test_creating_worker_monitors_its_own_playback_without_holding_lock(
    monkeypatch, tmp_path, local
):
    import threading

    entered = threading.Event()
    release = threading.Event()
    threads = {}
    app = SimpleNamespace(
        radio_proc=None,
        radio_volume_var=SimpleNamespace(get=lambda: 37),
        after=lambda _delay, callback, *args: callback(*args),
        tr=lambda _key, default=None: default,
    )

    def start(*_args, **_kwargs):
        threads["creator"] = threading.current_thread()
        return object()

    def monitor(*_args):
        threads["monitor"] = threading.current_thread()
        entered.set()
        release.wait(timeout=3)

    monkeypatch.setattr(radio, "_start_radio_playback", start)
    monkeypatch.setattr(radio, "_wait_for_radio_process", monitor)
    monkeypatch.setattr(radio, "stop_radio_playback", lambda *_a, **_k: True)
    monkeypatch.setattr(radio, "radio_available", lambda _app: True)
    monkeypatch.setattr(radio, "_cleanup_radio_ipc_path", lambda _app: None)
    for name in (
        "_poll_radio_metadata",
        "save_radio_settings",
        "update_radio_header",
        "refresh_radio_station_table",
        "refresh_radio_favorites_list",
        "refresh_radio_source_ui",
        "_set_radio_light",
        "_set_radio_station_text",
        "_set_radio_title_text",
        "set_radio_status",
    ):
        monkeypatch.setattr(radio, name, lambda *_a, **_k: None)
    monkeypatch.setattr(
        radio,
        "_resolve_target_station",
        lambda *_a, **_k: {
            "id": "test",
            "name": "Test",
            "url": "https://example.invalid/s",
        },
    )
    try:
        if local:
            media = tmp_path / "test.wav"
            media.write_bytes(b"synthetic fixture")
            assert radio._play_local_audio_file(
                app, str(media), station_name="Test", title_text="Test"
            )
        else:
            assert radio.play_radio_station(app, "test")
        assert entered.wait(timeout=2)
        assert threads["creator"] is threads["monitor"]
        assert threads["creator"].is_alive()
        lock = radio._radio_playback_lock(app)
        assert lock.acquire(
            blocking=False
        ), "Monitor must not block Stop or next playback"
        lock.release()
    finally:
        release.set()
        for thread in set(threads.values()):
            thread.join(timeout=2)


# -- G-Quota: per-capsule limits -------------------------------------------


def capsule_plan(tmp_path):
    sandbox._prepare_directory(tmp_path)
    return sandbox._sandbox_command(
        ["/usr/bin/true"], tmp_path, (), None, local_file=None, catalog_parser=True
    )


@pytest.mark.parametrize("profile", sorted(sandbox.QUOTAS))
def test_limited_wraps_capsule_in_user_scope_rlimits_and_bounded_tmp(tmp_path, profile):
    capsule = capsule_plan(tmp_path)
    argv = sandbox._limited(capsule, profile)
    quota = sandbox.QUOTAS[profile]
    first = argv.index("--")
    assert argv[:6] == [
        str(sandbox.SYSTEMD_RUN),
        "--user",
        "--scope",
        "--quiet",
        "--collect",
        argv[5],
    ]
    assert argv[5].startswith(f"--unit=netmon-radio-{profile}-")
    assert argv[6:first] == [
        "-p",
        f"MemoryMax={quota['memory']}",
        "-p",
        "MemorySwapMax=0",
        "-p",
        f"TasksMax={quota['tasks']}",
        "-p",
        f"CPUQuota={quota['cpu']}%",
    ]
    second = argv.index("--", first + 1)
    assert argv[first + 1 : second] == [
        str(sandbox.PRLIMIT),
        f"--nofile={quota['nofile']}:{quota['nofile']}",
        f"--fsize={quota['fsize']}:{quota['fsize']}",
        "--core=0:0",
    ]
    inner = argv[second + 1 :]
    assert inner[0] == str(sandbox.BWRAP)
    at = inner.index("--tmpfs")
    assert inner[at - 2 : at + 2] == ["--size", str(quota["tmpfs"]), "--tmpfs", "/tmp"]
    # Nothing else of the capsule plan changes (flags, binds, clearenv, argv).
    assert inner[: at - 2] + inner[at:] == capsule


def test_scope_units_are_unique_per_capsule(tmp_path):
    capsule = capsule_plan(tmp_path)
    units = {sandbox._limited(capsule, "relay")[5] for _ in range(5)}
    assert len(units) == 5


@pytest.mark.parametrize(
    "plan",
    [[], ["/usr/bin/mpv", "--tmpfs", "/tmp"], ["/usr/bin/bwrap", "--tmpfs", "/home"]],
)
def test_limited_refuses_unexpected_capsule_plans(plan):
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox._limited(plan, "decoder")


def test_quota_environment_is_derived_from_own_uid(monkeypatch):
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/tmp/evil")
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/0")
    env = sandbox._quota_env()
    runtime = f"/run/user/{os.getuid()}"
    assert env["XDG_RUNTIME_DIR"] == runtime
    assert env["DBUS_SESSION_BUS_ADDRESS"] == f"unix:path={runtime}/bus"
    assert env["PATH"] == sandbox._ENV["PATH"]


def test_missing_user_manager_starts_nothing(monkeypatch, tmp_path):
    (tmp_path / "media").write_bytes(b"synthetic")
    monkeypatch.setattr(sandbox, "available", lambda: True)
    monkeypatch.setattr(sandbox.os, "getuid", lambda: 2**31 - 7)  # no such bus
    monkeypatch.setattr(sandbox, "_open_output", lambda: pytest.fail("output opened"))
    monkeypatch.setattr(
        sandbox.subprocess, "Popen", lambda *_a, **_k: pytest.fail("process started")
    )
    with pytest.raises(sandbox.RadioSandboxError, match="Ressourcengrenzen"):
        sandbox.start_playback(
            [
                "mpv",
                f"--input-ipc-server={sandbox.IPC_PATH}",
                "--",
                str(tmp_path / "media"),
            ],
            ipc_root=tmp_path,
            local_file=tmp_path / "media",
        )
    assert not list(tmp_path.glob("play-*"))


def test_all_three_playback_capsules_start_limited(monkeypatch, tmp_path):
    output = FakeOutput()
    fifo_read, output.descriptor = os.pipe()
    command = prepared_start(monkeypatch, tmp_path, lambda: output)
    command[-1] = "https://radio.example/live"
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))
    monkeypatch.setattr(sandbox, "_wait_for_ipc", lambda process: None)
    started = []

    def spawn(argv, **kwargs):
        started.append((argv, kwargs["env"]))
        return Child()

    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    try:
        process = sandbox.start_playback(command, ipc_root=tmp_path)
        process.kill()
        process.wait(timeout=1)
    finally:
        os.close(fifo_read)
        os.close(output.descriptor)
    profiles = [a[5].split("-")[4] for a, _env in started]
    assert profiles == ["fetch", "relay", "decoder"]
    for argv, env in started:
        assert argv[0] == str(sandbox.SYSTEMD_RUN)
        assert env == sandbox._quota_env()
        assert str(sandbox.BWRAP) in argv and "--clearenv" in argv


def test_bounded_tmp_inserts_once_and_keeps_the_smaller_bound(tmp_path):
    capsule = capsule_plan(tmp_path)
    once = sandbox._bounded_tmp(capsule, 32 << 20)
    twice = sandbox._bounded_tmp(once, 16 << 20)
    at = twice.index("--tmpfs")
    assert twice[at - 2 : at] == ["--size", str(16 << 20)]
    assert twice.count("--size") == 1
    assert sandbox._bounded_tmp(twice, 64 << 20)[at - 1] == str(16 << 20)


@pytest.mark.parametrize("builder", ["fetch", "catalog", "zip", "logo"])
def test_helper_capsules_have_a_bounded_tmp(monkeypatch, tmp_path, builder):
    monkeypatch.setattr(sandbox, "_network_files", lambda: ())
    sandbox._prepare_directory(tmp_path)
    (tmp_path / "request.json").write_text("{}")
    if builder == "fetch":
        command = sandbox._fetch_command(tmp_path, None, tmp_path, ())
    elif builder == "catalog":
        command = sandbox._catalog_command(tmp_path, tmp_path, (), "json")
    elif builder == "zip":
        command = sandbox._zip_command(tmp_path, tmp_path, ())
    else:
        command = sandbox._logo_command(tmp_path, tmp_path, (), fetch=False)
    at = command.index("--tmpfs")
    assert command[at - 2 : at + 2] == [
        "--size",
        str(sandbox.HELPER_TMPFS),
        "--tmpfs",
        "/tmp",
    ]
