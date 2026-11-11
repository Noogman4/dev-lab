"""Real Unix-socket probes inside the existing isolated test launcher."""

import os
import socket
import json
import threading
import stat
import struct
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from netmon.core import radio_sandbox as sandbox
from netmon.features import radio_controller as radio


@contextmanager
def responding_socket(path):
    received = []
    errors = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(path))
        server.listen(1)
        server.settimeout(0.2)

        def serve():
            try:
                try:
                    connection, _ = server.accept()
                except socket.timeout:
                    return
                with connection:
                    connection.settimeout(0.5)
                    data = connection.recv(8192)
                    received.append(data)
                    request = json.loads(data)
                    connection.sendall(
                        json.dumps(
                            {
                                "request_id": request.get("request_id"),
                                "error": "success",
                                "data": "controlled reply",
                            }
                        ).encode()
                        + b"\n"
                    )
            except Exception as exc:
                errors.append(exc)

        worker = threading.Thread(target=serve, daemon=True)
        worker.start()
        try:
            yield received
        finally:
            worker.join(1)
            assert not worker.is_alive()
            assert not errors


@pytest.mark.parametrize("route", ["send", "query", "startup"])
@pytest.mark.parametrize("link_kind", ["symlink", "hardlink"])
def test_production_ipc_refuses_foreign_link(tmp_path, route, link_kind):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    path = control / "mpv.sock"
    foreign = tmp_path / "foreign.sock"
    with responding_socket(foreign) as received:
        if link_kind == "hardlink":
            os.link(foreign, path)
            assert path.stat().st_nlink == 2
        else:
            path.symlink_to(foreign)
        app = SimpleNamespace(radio_ipc_path=str(path))
        if route == "send":
            assert radio._send_mpv_command(app, ["get_property", "time-pos"]) is False
        elif route == "query":
            assert radio._query_mpv_property(app, "mpv-version") is None
        else:
            process = SimpleNamespace(ipc_path=str(path), poll=lambda: None)
            with pytest.raises(sandbox.RadioSandboxError):
                sandbox._wait_for_ipc(process, timeout=0.05)
        assert not received


@pytest.mark.parametrize("route", ["send", "query", "startup"])
def test_production_ipc_accepts_selected_socket(tmp_path, route):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    path = control / "mpv.sock"
    with responding_socket(path) as received:
        app = SimpleNamespace(radio_ipc_path=str(path))
        if route == "send":
            assert radio._send_mpv_command(app, ["get_property", "time-pos"])
        elif route == "query":
            assert radio._query_mpv_property(app, "mpv-version") == "controlled reply"
        else:
            sandbox._wait_for_ipc(
                SimpleNamespace(ipc_path=str(path), poll=lambda: None), timeout=0.1
            )
        assert len(received) == 1


@pytest.mark.parametrize("kind", ["file", "fifo", "directory", "symlink"])
def test_non_socket_rejected_before_client_allocation(tmp_path, monkeypatch, kind):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    path = control / "mpv.sock"
    if kind == "file":
        path.write_text("not a socket")
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        path.symlink_to(tmp_path / "missing")
    monkeypatch.setattr(
        sandbox.socket,
        "socket",
        lambda *_a: pytest.fail("invalid inode reached connect"),
    )
    before = set(os.listdir("/proc/self/fd"))
    for _ in range(3):
        with pytest.raises(sandbox.RadioSandboxError):
            sandbox.connect_mpv(path, timeout=0.1)
    assert set(os.listdir("/proc/self/fd")) == before


@pytest.mark.parametrize("mode", [0o755, 0o770])
def test_non_private_control_directory_rejected(tmp_path, mode):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    control.chmod(mode)
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.connect_mpv(control / "mpv.sock", timeout=0.1)


def test_symlinked_control_directory_rejected(tmp_path):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    link = tmp_path / "control"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(OSError):
        sandbox.connect_mpv(link / "mpv.sock", timeout=0.1)


@pytest.mark.parametrize("wrong_owner", ["directory", "socket"])
def test_wrong_inode_owner_rejected(tmp_path, monkeypatch, wrong_owner):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    path = control / "mpv.sock"
    real_fstat = os.fstat
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(path))
        server.listen(1)
        server.settimeout(0.03)

        def fstat(fd):
            value = real_fstat(fd)
            match = (
                stat.S_ISDIR(value.st_mode)
                if wrong_owner == "directory"
                else stat.S_ISSOCK(value.st_mode)
            )
            return (
                SimpleNamespace(st_mode=value.st_mode, st_uid=os.getuid() + 1)
                if match
                else value
            )

        monkeypatch.setattr(sandbox.os, "fstat", fstat)
        with pytest.raises(sandbox.RadioSandboxError):
            sandbox.connect_mpv(path, timeout=0.1)
        with pytest.raises(socket.timeout):
            server.accept()


@pytest.mark.parametrize("bad_peer", ["uid", "pid", "short", "error"])
def test_untrusted_peer_closes_connection_before_sending_data(
    tmp_path, monkeypatch, bad_peer
):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    path = control / "mpv.sock"
    real_socket = socket.socket
    closed = []
    with real_socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(path))
        server.listen(1)
        server.settimeout(0.3)

        class Client:
            def __init__(self, *args):
                self.socket = real_socket(*args)

            def settimeout(self, timeout):
                self.socket.settimeout(timeout)

            def connect(self, target):
                self.socket.connect(target)

            def getsockopt(self, *_):
                if bad_peer == "error":
                    raise OSError("controlled peer-credential failure")
                if bad_peer == "short":
                    return b"bad"
                return struct.pack(
                    "3i",
                    0 if bad_peer == "pid" else os.getpid(),
                    os.getuid() + 1 if bad_peer == "uid" else os.getuid(),
                    os.getgid(),
                )

            def close(self):
                closed.append(True)
                self.socket.close()

        with monkeypatch.context() as patch:
            patch.setattr(sandbox.socket, "socket", Client)
            with pytest.raises((sandbox.RadioSandboxError, OSError, struct.error)):
                sandbox.connect_mpv(path, timeout=0.1)
        connection, _ = server.accept()
        with connection:
            connection.settimeout(0.3)
            assert connection.recv(1) == b""
        assert closed == [True]


@pytest.mark.parametrize(
    "change", ["rename_socket", "unlink_socket", "rename_directory"]
)
def test_connector_uses_pinned_inode_during_path_swap(tmp_path, monkeypatch, change):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    other = tmp_path / "other"
    other.mkdir(mode=0o700)
    path, foreign = control / "mpv.sock", other / "mpv.sock"
    real_open = os.open
    swapped = []
    with responding_socket(path) as selected, responding_socket(foreign) as rejected:

        def open_fd(target, flags, *args, **kwargs):
            fd = real_open(target, flags, *args, **kwargs)
            if not swapped and (
                (change == "rename_directory" and target == control)
                or (change != "rename_directory" and target == "mpv.sock")
            ):
                swapped.append(True)
                assert not os.get_inheritable(fd)
                if change == "rename_directory":
                    control.rename(tmp_path / "old-control")
                    control.symlink_to(other, target_is_directory=True)
                else:
                    if change == "rename_socket":
                        path.rename(control / "old.sock")
                    else:
                        path.unlink()
                    path.symlink_to(foreign)
            return fd

        monkeypatch.setattr(sandbox.os, "open", open_fd)
        if change == "unlink_socket":
            # A pinned but already unlinked inode has nlink=0 and is rejected.
            # The primitive Linux behavior is still tested separately below.
            with pytest.raises(sandbox.RadioSandboxError):
                sandbox.connect_mpv(path, timeout=0.2)
            assert not selected
        else:
            with sandbox.connect_mpv(path, timeout=0.2) as client:
                client.sendall(b'{"command":["get_property","mpv-version"]}\n')
                assert json.loads(client.recv(4096))["error"] == "success"
            assert len(selected) == 1
        assert swapped and not rejected


@pytest.mark.parametrize("change", ["add_link", "unlink"])
def test_link_change_during_connect_is_rejected_before_json(
    tmp_path, monkeypatch, change
):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    path = control / "mpv.sock"
    real_fstat = os.fstat
    changed = []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(path))
        server.listen(1)
        server.settimeout(0.3)

        def fstat(fd):
            value = real_fstat(fd)
            if stat.S_ISSOCK(value.st_mode) and not changed:
                assert value.st_nlink == 1
                changed.append(True)
                if change == "add_link":
                    os.link(path, control / "second.sock")
                else:
                    path.unlink()
                # The first check sees its earlier snapshot. The check after
                # connect must notice the visible change to two/zero links.
            return value

        monkeypatch.setattr(sandbox.os, "fstat", fstat)
        before = set(os.listdir("/proc/self/fd"))
        with pytest.raises(sandbox.RadioSandboxError):
            sandbox.connect_mpv(path, timeout=0.2)
        connection, _ = server.accept()
        with connection:
            connection.settimeout(0.3)
            assert connection.recv(1) == b"", "JSON sent before final link check"
        assert changed and set(os.listdir("/proc/self/fd")) == before


def test_descriptor_connect_failure_has_no_path_fallback(tmp_path, monkeypatch):
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    path = control / "mpv.sock"
    attempts, closed = [], []
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(path))
        server.listen(1)

        class Client:
            def __init__(self, *_):
                pass

            def settimeout(self, _):
                pass

            def connect(self, target):
                attempts.append(target)
                assert target.startswith("/proc/self/fd/")
                raise OSError("controlled procfs failure")

            def close(self):
                closed.append(True)

        monkeypatch.setattr(sandbox.socket, "socket", Client)
        before = set(os.listdir("/proc/self/fd"))
        with pytest.raises(OSError):
            sandbox.connect_mpv(path, timeout=0.1)
        assert len(attempts) == 1 and closed == [True]
        assert set(os.listdir("/proc/self/fd")) == before


@pytest.mark.parametrize("remove", [False, True])
def test_linux_pinned_socket_survives_path_replacement(tmp_path, remove):
    original = tmp_path / "mpv.sock"
    foreign = tmp_path / "foreign.sock"
    with (
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server,
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as canary,
    ):
        server.bind(str(original))
        server.listen(1)
        server.settimeout(0.3)
        canary.bind(str(foreign))
        canary.listen(1)
        canary.settimeout(0.03)
        pinned = os.open(original, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            assert not os.get_inheritable(pinned)
            if remove:
                original.unlink()
            else:
                original.rename(tmp_path / "old.sock")
            original.symlink_to(foreign)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.3)
                client.connect(f"/proc/self/fd/{pinned}")
                client.sendall(b"selected socket only")
                connection, _ = server.accept()
                with connection:
                    connection.settimeout(0.3)
                    assert connection.recv(64) == b"selected socket only"
            with pytest.raises(socket.timeout):
                canary.accept()
        finally:
            os.close(pinned)
