"""Private internal X display with no outer display capability.

Renderer and pixel-reader clients get a pinned private socket and sealed cookie.
Only the trusted Tk viewer receives raw pixels; Xvfb never sees outer X.
No renderer, host audio, hardware GPU or system service is started here.
"""

from contextlib import contextmanager
from functools import lru_cache
import fcntl
import os
from pathlib import Path
import re
import secrets
import socket
import stat
import struct
import subprocess
import tempfile
import threading
import time

from netmon.core import projectm_profile as profiles

XVFB = Path("/usr/bin/Xvfb")
WORKER = Path(__file__).with_name("projectm_display_worker.py")
X11_DIR = Path("/tmp/.X11-unix")
GLXINFO = Path("/usr/bin/glxinfo")
AUTH_NAME = b"MIT-MAGIC-COOKIE-1"
MAX_AUTH = 256 * 1024
PRIVATE_DISPLAY = ":1"


def _error(message):
    from netmon.core.radio_sandbox import RadioSandboxError

    return RadioSandboxError(message)


def _display(value):
    match = re.fullmatch(r"(?:unix/?)?:([0-9]{1,4})(?:\.([0-9]{1,2}))?", value or "")
    if not match:
        raise _error("Geschütztes Display benötigt einen lokalen X11-Zugang.")
    return str(int(match[1])), int(match[2] or 0)


def _cookie(data, number, hostname):
    if not data or len(data) > MAX_AUTH:
        raise _error("Ungültige X-Authentifizierungsdatei.")
    offset = 0
    selected = set()
    while offset < len(data):

        def field():
            nonlocal offset
            if offset + 2 > len(data):
                raise _error("Unvollständige X-Authentifizierung.")
            length = struct.unpack_from(">H", data, offset)[0]
            offset += 2
            if offset + length > len(data):
                raise _error("Unvollständige X-Authentifizierung.")
            value = data[offset : offset + length]
            offset += length
            return value

        if offset + 2 > len(data):
            raise _error("Unvollständige X-Authentifizierung.")
        family = struct.unpack_from(">H", data, offset)[0]
        offset += 2
        address, display, name, cookie = field(), field(), field(), field()
        if (
            (family == 65535 or family == 256 and address == hostname)
            and display == number.encode("ascii")
            and name == AUTH_NAME
        ):
            if len(cookie) != 16:
                raise _error("Ungültiges X-Cookie.")
            selected.add(cookie)
    if len(selected) != 1:
        raise _error("Kein eindeutiges Cookie für das gewählte X-Display.")
    return selected.pop()


def auth_record(cookie, display):
    fields = (b"", str(display).encode("ascii"), AUTH_NAME, cookie)
    return struct.pack(">H", 65535) + b"".join(
        struct.pack(">H", len(x)) + x for x in fields
    )


def _sealed_auth(cookie, display):
    descriptor = os.memfd_create(
        "netmon-display-auth", os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING
    )
    try:
        payload = auth_record(cookie, display)
        if os.write(descriptor, payload) != len(payload):
            raise OSError("Unvollständige X-Authentifizierung.")
        os.lseek(descriptor, 0, os.SEEK_SET)
        fcntl.fcntl(
            descriptor,
            fcntl.F_ADD_SEALS,
            fcntl.F_SEAL_WRITE
            | fcntl.F_SEAL_GROW
            | fcntl.F_SEAL_SHRINK
            | fcntl.F_SEAL_SEAL,
        )
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _host():
    number, screen = _display(os.environ.get("DISPLAY"))
    authority = os.environ.get("XAUTHORITY")
    if not authority:
        raise _error(
            "Geschütztes Display benötigt eine ausdrückliche XAUTHORITY-Datei."
        )
    descriptor = os.open(
        authority, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    )
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid not in {0, os.getuid()}
            or info.st_mode & 0o022
        ):
            raise _error("X-Authentifizierungsdatei ist nicht geschützt.")
        cookie = _cookie(
            handle.read(MAX_AUTH + 1), number, socket.gethostname().encode()
        )
    directory = os.open(
        X11_DIR, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        descriptor = os.open(
            "X" + number, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory
        )
    finally:
        os.close(directory)
    info = os.fstat(descriptor)
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid not in {0, os.getuid()}:
        os.close(descriptor)
        raise _error("Ungültiger äußerer X-Socket.")
    return descriptor, cookie, screen


@lru_cache(maxsize=1)
def _runtime():
    from netmon.core import radio_sandbox as sandbox

    stdlib, python = sandbox._pcm_runtime()
    files = set(python) | set(sandbox._runtime_files(XVFB))
    extras = [Path("/usr/bin/xkbcomp"), Path("/bin/sh")]
    # First prototype supports only this installed multiarch software stack.
    extras += [Path("/usr/lib/xorg/modules/extensions/libglx.so")]
    for path in extras:
        if not path.is_file():
            raise _error("Software-Display-Laufzeit fehlt.")
        files.update(sandbox._runtime_files(path, allow_static_extension=True))
    files.update(_software_files())
    if not Path("/usr/share/X11/xkb").is_dir():
        raise _error("X-Tastaturlaufzeit fehlt.")
    return stdlib, tuple(sorted(files))


@lru_cache(maxsize=1)
def _software_files():
    from netmon.core import radio_sandbox as sandbox

    gl = Path("/usr/lib/x86_64-linux-gnu")
    files = set()
    for path in (gl / "dri/swrast_dri.so", gl / "libGLX_mesa.so.0"):
        if not path.is_file():
            raise _error("Software-OpenGL-Laufzeit fehlt.")
        files.update(sandbox._runtime_files(path, allow_static_extension=True))
    return tuple(sorted(files))


def _command(directory, stdlib, files, private_auth, resolution=profiles.DEFAULT):
    profile = profiles.resolve(resolution)
    from netmon.core import radio_sandbox as sandbox

    command = sandbox._sandbox_command(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/display-worker.py",
            "--resolution",
            profile.key,
        ],
        directory,
        files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    extra = [
        "--bind",
        str(directory / "x11"),
        "/tmp/.X11-unix",
        "--ro-bind-data",
        str(private_auth),
        "/run/private.auth",
        "--ro-bind",
        "/usr/share/X11/xkb",
        "/usr/share/X11/xkb",
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(WORKER),
        "/run/display-worker.py",
        "--ro-bind",
        str(Path(profiles.__file__)),
        "/run/projectm-profile.py",
    ]
    for key, value in {
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "GALLIUM_DRIVER": "llvmpipe",
        "LP_NUM_THREADS": "2",
    }.items():
        extra += ["--setenv", key, value]
    command[command.index("--") : command.index("--")] = extra
    return command


def _handshake(descriptor, cookie):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(0.25)
        deadline = time.monotonic() + 0.5
        client.connect(f"/proc/self/fd/{descriptor}")
        name = AUTH_NAME
        request = struct.pack("<BBHHHHH", ord("l"), 0, 11, 0, len(name), len(cookie), 0)
        client.sendall(
            request
            + name
            + b"\0" * (-len(name) % 4)
            + cookie
            + b"\0" * (-len(cookie) % 4)
        )

        def exact(size):
            data = bytearray()
            while len(data) < size:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise socket.timeout("X handshake deadline")
                client.settimeout(min(0.25, remaining))
                chunk = client.recv(size - len(data))
                if not chunk:
                    raise ValueError("Truncated X reply")
                data.extend(chunk)
            return data

        header = exact(8)
        status, _reason, major, minor, units = struct.unpack("<BBHHH", header)
        if status != 1 or major != 11 or minor != 0 or not 0 < units * 4 <= 65536:
            raise ValueError("X authentication failed")
        exact(units * 4)


class DisplaySession:
    def __init__(self, process, temporary, descriptor, cookie):
        self.process, self.temporary = process, temporary
        self.socket_path = Path(temporary.name) / "x11/X1"
        self._socket = descriptor
        self._cookie = cookie
        self._lock = threading.RLock()
        self._result = None
        self.sandbox_state = "started"
        self.runtime_verified = False

    @contextmanager
    def display_binding(self):
        with self._lock:
            if self.poll() is not None:
                raise _error("Privates Display wurde beendet.")
            descriptor = os.dup(self._socket)
            try:
                auth = _sealed_auth(self._cookie, "1")
            except Exception:
                os.close(descriptor)
                raise
        try:
            yield descriptor, auth
        finally:
            os.close(descriptor)
            os.close(auth)

    def _cleanup(self):
        if self._socket is not None:
            os.close(self._socket)
            self._socket = None
        self._cookie = b""
        self.temporary.cleanup()

    def poll(self):
        with self._lock:
            if self._result is not None:
                return self._result
            code = self.process.poll()
            if code is not None:
                self._cleanup()
                self._result = code
            return self._result

    def stop(self):
        with self._lock:
            if self.poll() is not None:
                return
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
            self._cleanup()
            self._result = 0


def start(*, work_root=None, resolution=profiles.DEFAULT):
    profile = profiles.resolve(resolution)
    from netmon.core import radio_sandbox as sandbox

    stdlib, files = _runtime()
    temporary = None
    private_auth = descriptor = None
    process = None
    try:
        cookie = secrets.token_bytes(16)
        private_auth = _sealed_auth(cookie, "1")
        temporary = tempfile.TemporaryDirectory(
            prefix="projectm-display-", dir=work_root
        )
        directory = Path(temporary.name)
        if len(os.fsencode(directory / "x11/X1")) > 100:
            raise _error("Privater Displaysocketpfad ist zu lang.")
        sandbox._prepare_directory(directory)
        (directory / "x11").mkdir(mode=0o700)
        process = subprocess.Popen(
            sandbox._limited(
                _command(directory, stdlib, files, private_auth, profile.key),
                "pm-display",
            ),
            env=sandbox._quota_env(),
            cwd="/",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            pass_fds=(private_auth,),
        )
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            try:
                export = os.open(
                    directory / "x11",
                    os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                )
                try:
                    descriptor = os.open(
                        "X1", os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=export
                    )
                finally:
                    os.close(export)
                info = os.fstat(descriptor)
                if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
                    raise _error("Ungültiger privater Displaysocket.")
                _handshake(descriptor, cookie)
                return DisplaySession(process, temporary, descriptor, cookie)
            except (
                FileNotFoundError,
                ConnectionRefusedError,
                socket.timeout,
                ValueError,
            ):
                if descriptor is not None:
                    os.close(descriptor)
                    descriptor = None
                time.sleep(0.03)
        raise _error("Privates Display wurde nicht verifiziert bereit.")
    except Exception:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            temporary.cleanup()
        raise
    finally:
        for fd in (private_auth,):
            if fd is not None:
                os.close(fd)
