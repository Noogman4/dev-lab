"""Local HTTP(S) handoff to the process holding the browser profile lock."""

from contextlib import contextmanager, suppress
import os
import socket
import stat
import struct
import time

from .sandbox import BrowserSandboxError, _check_url

_NAME = "links.sock"
_MAX_BYTES = 4 * 8192
_CREDENTIALS = struct.Struct("3i")
_CONFIRM_TIMEOUT = 70


def _check_socket(info):
    if (
        not stat.S_ISSOCK(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_nlink != 1
    ):
        raise BrowserSandboxError("Der lokale Browser-Socket ist unzulässig.")


def _check_peer(connection):
    pid, uid, _gid = _CREDENTIALS.unpack(
        connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, _CREDENTIALS.size)
    )
    if pid <= 0 or uid != os.getuid():
        raise BrowserSandboxError("Die Browser-Gegenstelle ist unzulässig.")


@contextmanager
def listen(directory):
    """Only the profile lock holder may create or reclaim the socket."""
    try:
        old = os.stat(_NAME, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        _check_socket(old)
        os.unlink(_NAME, dir_fd=directory)
    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as server:
        server.bind(f"/proc/self/fd/{directory}/{_NAME}")
        original = os.stat(_NAME, dir_fd=directory, follow_symlinks=False)
        try:
            server.listen(8)
            server.setblocking(False)
            yield server
        finally:
            with suppress(FileNotFoundError):
                current = os.stat(_NAME, dir_fd=directory, follow_symlinks=False)
                if os.path.samestat(original, current):
                    os.unlink(_NAME, dir_fd=directory)


def receive(server, handoff):
    try:
        connection, _address = server.accept()
    except BlockingIOError:
        return
    with connection:
        connection.settimeout(0.5)
        try:
            _check_peer(connection)
            packet, _, flags, _ = connection.recvmsg(_MAX_BYTES)
            if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                raise BrowserSandboxError("Ungültige Browser-Anfrage.")
            url = packet.decode("utf-8")
            _check_url(url)
            handoff(url)
        except (BrowserSandboxError, OSError, UnicodeError):
            reply = b"error"
        else:
            reply = b"ok"
        with suppress(OSError):
            connection.send(reply)


def forward(directory, url, stop):
    """Return False only when the owner was unreachable before sending a URL."""
    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as client:
        try:
            fd = os.open(
                _NAME, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory
            )
        except FileNotFoundError:
            return False
        try:
            info = os.fstat(fd)
            if info.st_nlink == 0:
                return False
            _check_socket(info)
            client.settimeout(0.25)
            try:
                client.connect(f"/proc/self/fd/{fd}")
            except (FileNotFoundError, ConnectionRefusedError, BlockingIOError):
                return False
            _check_peer(client)
            info = os.fstat(fd)
            if info.st_nlink == 0:
                return False
            _check_socket(info)
        finally:
            os.close(fd)
        if stop.is_set():
            return False
        try:
            client.sendall(url.encode("utf-8"))
            deadline = time.monotonic() + _CONFIRM_TIMEOUT
            while not stop.is_set() and time.monotonic() < deadline:
                try:
                    if client.recv(8) == b"ok":
                        return True
                    break
                except TimeoutError:
                    continue
        except (OSError, UnicodeError) as exc:
            raise BrowserSandboxError(
                "Der Browser hat die Linkübergabe nicht bestätigt."
            ) from exc
        raise BrowserSandboxError("Der Browser hat die Linkübergabe nicht bestätigt.")
