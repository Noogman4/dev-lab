"""Bounded local-display authorization and pinned-capability lifecycle."""

import fcntl
import os
from pathlib import Path
import socket
import struct
import tempfile
from types import SimpleNamespace

import pytest

from netmon.core import projectm_display as display
from netmon.core import projectm_display_worker as worker
from netmon.core import radio_sandbox as sandbox
from test_radio_sandbox import Child


@pytest.mark.parametrize("value", [":0", ":23.0", "unix:7", "unix/:8.1"])
def test_only_local_display_identifiers_are_accepted(value):
    number, screen = display._display(value)
    assert number.isdecimal() and 0 <= screen <= 99


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "localhost:0",
        "example.org:1",
        "tcp/:3",
        ":-1",
        ":1;bad",
        ":12345",
        ":0.100",
    ],
)
def test_remote_ambiguous_or_excessive_display_is_rejected(value):
    with pytest.raises(sandbox.RadioSandboxError):
        display._display(value)


def record(family, address, number, name, cookie):
    return struct.pack(">H", family) + b"".join(
        struct.pack(">H", len(x)) + x for x in (address, number, name, cookie)
    )


def test_snapshot_selects_only_exact_local_cookie_and_accepts_identical_aliases():
    cookie = b"a" * 16
    data = record(256, b"host", b"8", display.AUTH_NAME, cookie)
    data += record(65535, b"", b"8", display.AUTH_NAME, cookie)
    data += record(256, b"other", b"8", display.AUTH_NAME, b"b" * 16)
    data += record(0, b"host", b"8", display.AUTH_NAME, b"c" * 16)
    data += record(65535, b"", b"9", display.AUTH_NAME, b"d" * 16)
    assert display._cookie(data, "8", b"host") == cookie


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"x",
        b"x" * 262145,
        b"\0\0\0\x10bad",
        record(65535, b"", b"8", display.AUTH_NAME, b"short"),
        record(65535, b"", b"9", display.AUTH_NAME, b"a" * 16),
        record(65535, b"", b"8", display.AUTH_NAME, b"a" * 16)
        + record(65535, b"", b"8", display.AUTH_NAME, b"b" * 16),
    ],
)
def test_malformed_or_conflicting_authority_fails_closed(data):
    with pytest.raises(sandbox.RadioSandboxError):
        display._cookie(data, "8", b"host")


def test_auth_snapshot_is_sealed_and_remapped_without_other_cookies():
    descriptor = display._sealed_auth(b"p" * 16, "1")
    try:
        seals = fcntl.fcntl(descriptor, fcntl.F_GET_SEALS)
        assert seals & fcntl.F_SEAL_WRITE
        data = os.read(descriptor, 4096)
        assert display._cookie(data, "1", b"unused") == b"p" * 16
        with pytest.raises(sandbox.RadioSandboxError):
            display._cookie(data, "8", b"unused")
        with pytest.raises(OSError):
            os.write(descriptor, b"X")
        with pytest.raises(OSError):
            os.ftruncate(descriptor, 0)
        assert not os.get_inheritable(descriptor)
    finally:
        os.close(descriptor)


@pytest.fixture
def source(monkeypatch):
    with tempfile.TemporaryDirectory(
        prefix="px-", dir=os.environ.get("TMPDIR")
    ) as name:
        root = Path(name)
        auth = root / "auth"
        auth.write_bytes(display.auth_record(b"h" * 16, "8"))
        auth.chmod(0o600)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(str(root / "X8"))
        monkeypatch.setattr(display, "X11_DIR", root)
        monkeypatch.setenv("DISPLAY", ":8.1")
        monkeypatch.setenv("XAUTHORITY", str(auth))
        yield root, auth, sock
        sock.close()


def test_host_cookie_snapshot_pins_exact_socket_and_screen(source):
    root, _, _ = source
    descriptor, cookie, screen = display._host()
    try:
        assert cookie == b"h" * 16 and screen == 1
        assert os.fstat(descriptor).st_ino == (root / "X8").stat().st_ino
    finally:
        os.close(descriptor)


@pytest.mark.parametrize("mode", [0o620, 0o602])
def test_writable_authority_is_not_used(source, mode):
    _, auth, _ = source
    auth.chmod(mode)
    with pytest.raises(sandbox.RadioSandboxError):
        display._host()


def test_no_implicit_authority_or_socket_symlink_fallback(source, monkeypatch):
    root, auth, _ = source
    monkeypatch.delenv("XAUTHORITY")
    with pytest.raises(sandbox.RadioSandboxError):
        display._host()
    monkeypatch.setenv("XAUTHORITY", str(auth))
    (root / "X8").rename(root / "original")
    (root / "X8").symlink_to(root / "original")
    with pytest.raises(sandbox.RadioSandboxError):
        display._host()


def test_display_session_pins_inode_and_creates_independent_auth_handles(source):
    root, _, _ = source
    directory = root / "session"
    directory.mkdir()
    (directory / "x11").mkdir()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    path = directory / "x11/X1"
    sock.bind(str(path))
    descriptor = os.open(path, os.O_PATH | os.O_NOFOLLOW)
    session = display.DisplaySession(
        Child(),
        SimpleNamespace(name=str(directory), cleanup=lambda: None),
        descriptor,
        b"p" * 16,
    )
    try:
        inode = os.fstat(descriptor).st_ino
        path.unlink()
        path.symlink_to(root / "X8")
        with (
            session.display_binding() as (one, auth1),
            session.display_binding() as (two, auth2),
        ):
            assert os.fstat(one).st_ino == os.fstat(two).st_ino == inode
            assert (
                os.read(auth1, 4096)
                == os.read(auth2, 4096)
                == display.auth_record(b"p" * 16, "1")
            )
            assert os.read(auth1, 1) == b""
        for fd in (one, two, auth1, auth2):
            with pytest.raises(OSError):
                os.fstat(fd)
        session.stop()
        session.stop()
        assert session.poll() == 0 and session._socket is None
        with pytest.raises(sandbox.RadioSandboxError):
            with session.display_binding():
                pass
    finally:
        session.stop()
        sock.close()


def test_internal_display_never_grants_outer_x_or_cookie(source):
    root, _, _ = source
    command = display._command(root, Path("/usr/lib/python3.12"), (), 12)
    assert "--unshare-net" in command and "--unshare-ipc" in command
    assert "/run/private.auth" in command
    assert "/run/host.auth" not in command and "/tmp/.X11-unix/X0" not in command
    assert "XEPHYR_NO_SHM" not in command and "DISPLAY" not in command
    assert "--ro-bind-fd" not in command
    assert command[-3:] == ["/run/display-worker.py", "--resolution", "640x480"]


def test_worker_limits_preserve_lower_hard_bound(monkeypatch):
    calls = []
    monkeypatch.setattr(
        worker.resource, "getrlimit", lambda _: (128 * 1024 * 1024, 256 * 1024 * 1024)
    )
    monkeypatch.setattr(
        worker.resource, "setrlimit", lambda name, bounds: calls.append((name, bounds))
    )
    worker.limits()
    assert calls == [
        (worker.resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
    ]


@pytest.mark.parametrize("failure", ["popen", "early_exit"])
def test_start_failure_cleans_capabilities_and_never_starts_directly(
    source, monkeypatch, failure
):
    root, _, _ = source
    descriptors, launches, temporaries = [], [], []
    original_auth = display._sealed_auth
    original_temporary = display.tempfile.TemporaryDirectory

    def auth(*args):
        descriptor = original_auth(*args)
        descriptors.append(descriptor)
        return descriptor

    def temporary(*args, **kwargs):
        result = original_temporary(*args, **kwargs)
        temporaries.append(Path(result.name))
        return result

    def popen(command, **kwargs):
        launches.append(command)
        # G-Quota: systemd-run scope -> prlimit -> the unchanged bwrap capsule.
        assert command[0] == str(sandbox.SYSTEMD_RUN)
        assert command[5].startswith("--unit=netmon-radio-pm-display-")
        assert str(sandbox.BWRAP) in command
        assert kwargs["env"] == sandbox._quota_env()
        assert set(kwargs["pass_fds"]) == set(descriptors)
        if failure == "popen":
            raise OSError("synthetic bwrap failure")
        return SimpleNamespace(poll=lambda: 2, wait=lambda **_: 2)

    monkeypatch.setattr(display, "_runtime", lambda: (root, ()))
    monkeypatch.setattr(display, "_host", lambda: pytest.fail("outer X consulted"))
    monkeypatch.setattr(display, "_sealed_auth", auth)
    monkeypatch.setattr(display.tempfile, "TemporaryDirectory", temporary)
    monkeypatch.setattr(display.subprocess, "Popen", popen)
    with pytest.raises((OSError, sandbox.RadioSandboxError)):
        display.start(work_root=root)
    assert len(launches) == 1
    assert all(not path.exists() for path in temporaries)
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)


@pytest.mark.parametrize(
    "header",
    [
        b"",
        struct.pack("<BBHHH", 0, 0, 11, 0, 1),
        struct.pack("<BBHHH", 2, 0, 11, 0, 1),
        struct.pack("<BBHHH", 1, 0, 10, 0, 1),
        struct.pack("<BBHHH", 1, 0, 11, 1, 1),
        struct.pack("<BBHHH", 1, 0, 11, 0, 0),
        struct.pack("<BBHHH", 1, 0, 11, 0, 16385),
        struct.pack("<BBHHH", 1, 0, 11, 0, 1) + b"xx",
    ],
)
def test_handshake_rejects_failure_unknown_protocol_excess_or_truncation(
    monkeypatch, header
):
    class Reply:
        def __init__(self):
            self.data = header

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def settimeout(self, _):
            pass

        def connect(self, _):
            pass

        def sendall(self, _):
            pass

        def recv(self, count):
            result, self.data = self.data[:count], self.data[count:]
            return result

    monkeypatch.setattr(display.socket, "socket", lambda *_: Reply())
    with pytest.raises(ValueError):
        display._handshake(99, b"p" * 16)


def test_handshake_has_absolute_deadline_despite_small_fragments(monkeypatch):
    clock = [0]

    class SlowReply:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def settimeout(self, _):
            pass

        def connect(self, _):
            pass

        def sendall(self, _):
            pass

        def recv(self, _):
            clock[0] += 0.2
            return b"\1"

    monkeypatch.setattr(display.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(display.socket, "socket", lambda *_: SlowReply())
    with pytest.raises(socket.timeout):
        display._handshake(99, b"p" * 16)
    assert clock[0] < 0.7
