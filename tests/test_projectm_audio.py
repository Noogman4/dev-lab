"""Private adapter protocol/lifecycle tests; actual audio uses its native probe."""

import json
import os
from pathlib import Path
import resource
import socket
import tempfile
import time
from types import SimpleNamespace

import pytest

from netmon.core import (
    projectm_audio as audio,
    radio_pcm as pcm,
    radio_sandbox as sandbox,
)
from test_radio_sandbox import Child


@pytest.fixture
def root():
    # Keep Unix socket names below the kernel limit, independently of test names.
    with tempfile.TemporaryDirectory(
        prefix="pa-", dir=os.environ.get("TMPDIR")
    ) as name:
        yield Path(name)


@pytest.fixture
def source(root):
    directory = root / "source"
    directory.mkdir()
    (directory / "tap").mkdir()
    return sandbox.SandboxProcess(
        Child(),
        SimpleNamespace(name=str(directory), cleanup=lambda: None),
        pcm_process=Child(),
    )


class Process(Child):
    def __init__(self, ready):
        super().__init__()
        read, write = os.pipe()
        self.stdout = os.fdopen(read, "rb", buffering=0)
        os.write(write, ready)
        os.close(write)
        self.input_reader, write = os.pipe()
        self.stdin = os.fdopen(write, "wb", buffering=0)


@pytest.fixture
def factory(monkeypatch):
    processes = []
    sockets = []
    monkeypatch.setattr(audio, "available", lambda: True)
    monkeypatch.setattr(
        audio, "_runtime", lambda: (Path("/usr/lib/python3.12"), (), ())
    )
    settings = {"ready": b'{"ready":true,"source":"netmon_pcm"}\n', "socket": "real"}

    def spawn(command, **kwargs):
        assert kwargs["close_fds"] and kwargs["env"] == sandbox._ENV
        assert command[0] == str(sandbox.BWRAP)
        runtime = Path(command[command.index(audio.RUNTIME) - 1])
        path = runtime / "pulse/native"
        if settings["socket"] == "real":
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(str(path))
            sockets.append(sock)
        elif settings["socket"] == "file":
            path.write_text("not a socket")
        elif settings["socket"] == "symlink":
            path.symlink_to(runtime / "elsewhere")
        elif settings["socket"] == "parent-symlink":
            external = runtime.parent.parent / "foreign"
            external.mkdir()
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(str(external / "native"))
            sockets.append(sock)
            path.parent.rmdir()
            path.parent.symlink_to(external)
        process = Process(settings["ready"])
        processes.append(process)
        return process

    monkeypatch.setattr(audio.subprocess, "Popen", spawn)
    yield settings, processes
    for process in processes:
        process.stdin.close()
        process.stdout.close()
        os.close(process.input_reader)
    for sock in sockets:
        sock.close()


def wait_for(predicate):
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("Private pump did not finish")


def test_private_profile_has_no_hardware_bus_or_host_audio_grants(root):
    command = audio._command(root, Path("/usr/lib/python3.12"), (), ())
    assert "--unshare-net" in command and "--clearenv" in command
    writable = [command[i + 1 : i + 3] for i, v in enumerate(command) if v == "--bind"]
    assert writable == [[str(root / "runtime"), audio.RUNTIME]]
    assert not {
        "/dev/snd",
        "/run/dbus",
        "/run/control",
        "/run/audio/pulse",
        "/home/happy",
    } & set(command)
    assert command[command.index("--") + 1 :] == [
        str(sandbox.PYTHON),
        "-I",
        "-S",
        "-B",
        "-X",
        "pycache_prefix=/nonexistent",
        "/run/audio-worker.py",
    ]
    configs = audio.configurations()
    assert "pulse.allow-module-loading" not in configs["pipewire-pulse.conf"]
    assert "module-pipe-source" in configs["pipewire-pulse.conf"]
    assert "monitors/" not in configs["wireplumber.conf"]
    assert "config/lua" not in configs["wireplumber.conf"]


@pytest.mark.parametrize(
    "reply",
    [
        b"",
        b"garbage\n",
        b"{}\n",
        b'{"ready":1,"source":"netmon_pcm"}\n',
        b'{"ready":false,"source":"netmon_pcm"}\n',
        b'{"ready":true,"source":"host_audio"}\n',
        b'{"ready":true,"source":"netmon_pcm","unknown":true}\n',
        b'{"ready":true,"source":"netmon_pcm"}\nextra',
        b"x" * 1025,
    ],
)
def test_unknown_or_excessive_ready_reply_fails_and_releases_tap(
    root, source, factory, reply
):
    settings, processes = factory
    settings["ready"] = reply
    with pytest.raises((RuntimeError, ValueError)):
        audio.start(source, work_root=root)
    assert processes[0].signals == ["kill"]
    assert not list(root.glob("projectm-audio-*"))
    assert not (root / "source/tap/pcm.sock").exists()
    with source.open_pcm_tap():
        pass


@pytest.mark.parametrize("kind", ["file", "symlink", "missing"])
def test_ready_text_cannot_authorize_non_socket(root, source, factory, kind):
    settings, processes = factory
    settings["socket"] = kind
    with pytest.raises((sandbox.RadioSandboxError, FileNotFoundError)):
        audio.start(source, work_root=root)
    assert processes[0].signals == ["kill"]
    assert not list(root.glob("projectm-audio-*"))


def test_stalled_ready_reply_has_absolute_deadline(monkeypatch):
    clock = iter([0, 13])
    monkeypatch.setattr(audio.time, "monotonic", lambda: next(clock))
    read, write = os.pipe()
    with os.fdopen(read, "rb", buffering=0) as output:
        try:
            with pytest.raises(RuntimeError):
                audio._ready(SimpleNamespace(stdout=output))
        finally:
            os.close(write)


def test_server_controlled_parent_symlink_cannot_grant_foreign_socket(
    root, source, factory
):
    settings, processes = factory
    settings["socket"] = "parent-symlink"
    with pytest.raises(NotADirectoryError):
        audio.start(source, work_root=root)
    assert processes[0].signals == ["kill"]
    assert (root / "foreign/native").is_socket()
    assert not list(root.glob("projectm-audio-*"))
    with source.open_pcm_tap():
        pass


def test_start_stop_only_own_adapter_and_releases_receiver(root, source, factory):
    session = audio.start(source, work_root=root)
    assert session.sandbox_state == "started" and session.runtime_verified is False
    assert session.poll() is None
    assert session.source_name == "netmon_pcm"
    assert session.server_control_scope == "private-capsule"
    assert session.socket_path.is_socket()
    assert session.socket_path.parent.parent.stat().st_mode & 0o777 == 0o700
    session.stop()
    session.stop()
    assert session.poll() == 0
    assert not session.socket_path.exists()
    assert source.poll() is None
    assert source._process.signals == source._pcm_process.signals == []
    with source.open_pcm_tap():
        pass


def test_busy_receiver_is_not_closed_by_failed_second_start(root, source, factory):
    with source.open_pcm_tap() as tap:
        with pytest.raises(sandbox.RadioSandboxError):
            audio.start(source, work_root=root)
        assert not tap.closed and tap.path.exists()
    assert not factory[1] and not list(root.glob("projectm-audio-*"))


def test_socket_inode_survives_path_replacement_and_closes_at_end(
    root, source, factory
):
    session = audio.start(source, work_root=root)
    original_inode = os.fstat(session._socket_descriptor).st_ino
    session.socket_path.unlink()
    target = root / "private-canary"
    target.write_text("KEEP")
    session.socket_path.symlink_to(target)
    with session.socket_binding() as (path, descriptor):
        assert path.stat().st_ino == original_inode
        assert os.fstat(descriptor).st_mode & 0o170000 == 0o140000
        assert not os.get_inheritable(descriptor)
    with pytest.raises(OSError):
        os.fstat(descriptor)
    session.stop()
    assert session._socket_descriptor is None
    assert target.read_text() == "KEEP"
    with pytest.raises(RuntimeError):
        with session.socket_binding():
            pass


def test_temporary_directory_failure_does_not_claim_receiver(
    root, source, factory, monkeypatch
):
    def fail(**_kwargs):
        raise OSError("temporary storage unavailable")

    monkeypatch.setattr(audio.tempfile, "TemporaryDirectory", fail)
    with pytest.raises(OSError):
        audio.start(source, work_root=root)
    assert source._pcm_tap is None and not factory[1]


def test_overlong_private_socket_path_fails_before_spawn(root, source, factory):
    deep = root / ("x" * 80)
    deep.mkdir()
    with pytest.raises(sandbox.RadioSandboxError, match="zu lang"):
        audio.start(source, work_root=deep)
    assert not factory[1]
    assert not list(deep.glob("projectm-audio-*"))
    with source.open_pcm_tap():
        pass


def test_no_available_tools_and_untrusted_owner_fail_before_start(
    source, factory, monkeypatch
):
    monkeypatch.setattr(audio, "available", lambda: False)
    with pytest.raises(sandbox.RadioSandboxError):
        audio.start(source)
    with pytest.raises(sandbox.RadioSandboxError):
        audio.start(SimpleNamespace())
    assert not factory[1] and source._pcm_tap is None


def test_slow_private_source_drops_only_optional_pcm(root, source, factory):
    session = audio.start(source, work_root=root)
    descriptor = session.process.stdin.fileno()
    try:
        while True:
            os.write(descriptor, b"x" * 4096)
    except BlockingIOError:
        pass
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sender:
        sender.sendto(
            pcm.HEADER.pack(pcm.MAGIC, 0) + b"1234", str(source._pcm_tap.path)
        )
    try:
        wait_for(lambda: session.dropped_packets == 1)
        assert session.poll() is None and source.poll() is None
    finally:
        session.stop()


def test_invalid_pcm_stops_adapter_without_stopping_playback(root, source, factory):
    session = audio.start(source, work_root=root)
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sender:
        sender.sendto(b"invalid", str(source._pcm_tap.path))
    wait_for(lambda: not session.thread.is_alive())
    session.process.result = 0  # Real worker exits on the closed input.
    assert session.poll() == 2
    assert source.poll() is None
    assert not session.socket_path.exists()


def test_private_worker_loss_does_not_stop_playback(root, source, factory):
    session = audio.start(source, work_root=root)
    session.process.result = 2
    assert session.poll() == 2
    assert source.poll() is None
    assert not session.socket_path.exists()


def test_playback_end_closes_private_pcm_input(root, source, factory):
    session = audio.start(source, work_root=root)
    source._process.result = source._pcm_process.result = 0
    assert source.poll() == 0
    wait_for(lambda: not session.thread.is_alive())
    assert session.process.stdin.closed
    session.process.result = 0
    assert session.poll() == 0
    assert not session.socket_path.exists()


@pytest.mark.parametrize(
    "soft,hard,expected",
    [
        (resource.RLIM_INFINITY, resource.RLIM_INFINITY, 512 * 1024 * 1024),
        (64 * 1024 * 1024, 256 * 1024 * 1024, 64 * 1024 * 1024),
    ],
)
def test_worker_limits_preserve_stricter_inherited_bounds(
    monkeypatch, soft, hard, expected
):
    calls = []
    monkeypatch.setattr(resource, "getrlimit", lambda _name: (soft, hard))
    monkeypatch.setattr(
        resource, "setrlimit", lambda name, bounds: calls.append((name, bounds))
    )
    audio.apply_process_limits()
    assert calls == [(resource.RLIMIT_AS, (expected, expected))]


def test_unsupported_runtime_and_architecture_fail_closed(monkeypatch):
    for plan in [
        {"stdlib": "/tmp", "arch": "x86_64-linux-gnu", "extensions": []},
        {"stdlib": "/usr/lib/python3.12", "arch": "../private", "extensions": []},
        {
            "stdlib": "/usr/lib/python3.12",
            "arch": "x86_64-linux-gnu",
            "extensions": ["/usr/bin/python3"],
        },
    ]:
        monkeypatch.setattr(
            audio.subprocess,
            "run",
            lambda *_a, **_k: SimpleNamespace(stdout=json.dumps(plan)),
        )
        monkeypatch.setattr(sandbox, "_runtime_files", lambda *_a, **_k: ())
        with pytest.raises(sandbox.RadioSandboxError):
            audio._runtime.__wrapped__()


def test_different_wireplumber_abi_is_not_guessed(monkeypatch):
    plan = {
        "stdlib": "/usr/lib/python3.12",
        "arch": "x86_64-linux-gnu",
        "extensions": [],
    }
    monkeypatch.setattr(
        audio.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(stdout=json.dumps(plan)),
    )
    monkeypatch.setattr(
        sandbox,
        "_runtime_files",
        lambda *_a, **_k: (Path("/usr/lib/libwireplumber-0.5.so.0"),),
    )
    with pytest.raises(sandbox.RadioSandboxError, match="0.4"):
        audio._runtime.__wrapped__()
