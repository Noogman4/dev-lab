"""Manage the private D-Bus and the lifetime of NetMon's Firefox profile."""

from contextlib import ExitStack, contextmanager
import fcntl
from functools import partial
import os
from pathlib import Path
from queue import Empty, Full, Queue, SimpleQueue
import select
import stat
import subprocess
import tempfile
from threading import Event, Thread
import time
from urllib.parse import quote_from_bytes

from netmon.core.private_logs import _private_directory
from tools.secure_browser_manager.browser_container_builder import (
    ContainerSpec,
    build_policies_payload,
)

from . import link_socket, sandbox
from .sandbox import BrowserSandboxError

FIREFOX_DIR = Path("/opt/netmon-web-browser/firefox")
_DAEMON = "/usr/bin/dbus-daemon"
_SEND = "/usr/bin/dbus-send"
_SETPRIV = "/usr/bin/setpriv"
_BUS_CONFIGURATION = b"""<busconfig>
  <type>session</type>
  <listen>%s</listen>
  <auth>EXTERNAL</auth>
  <policy context="default">
    <allow send_destination="*"/>
    <allow receive_sender="*"/>
    <allow own="*"/>
  </policy>
</busconfig>"""


class _ProfileBusy(BrowserSandboxError):
    pass


def _managed_runtime(path):
    """Use only a provisioned, administrator-managed runtime."""
    for entry in (*reversed(path.parents), path):
        try:
            info = entry.lstat()
        except OSError as exc:
            raise BrowserSandboxError("Die eigene Firefox-Basis fehlt.") from exc
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            raise BrowserSandboxError("Die eigene Firefox-Basis ist nicht geschützt.")
    for entry in path.rglob("*"):
        info = entry.lstat()
        if (
            not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))
            or info.st_uid != 0
            or info.st_mode & 0o022
        ):
            raise BrowserSandboxError("Die eigene Firefox-Basis ist nicht geschützt.")
    return path


def _wayland_socket():
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", ""))
    display = os.environ.get("WAYLAND_DISPLAY", "")
    if (
        not runtime.is_absolute()
        or ".." in runtime.parts
        or not display
        or Path(display).name != display
        or display in {".", ".."}
    ):
        raise BrowserSandboxError("Der eigene Browser benötigt eine Wayland-Sitzung.")
    info = runtime.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise BrowserSandboxError("Der Wayland-Laufzeitordner ist nicht privat.")
    path = runtime / display
    sandbox._owned_socket(path)
    return path


@contextmanager
def _lock_profile(state_dir):
    with _private_directory(state_dir) as directory:
        fd = os.open(
            "session.lock",
            os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            0o600,
            dir_fd=directory,
        )
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.getuid()
                or info.st_nlink != 1
                or info.st_mode & 0o077
            ):
                raise BrowserSandboxError(
                    "Die Sperrdatei des Browserprofils ist ungültig."
                )
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise _ProfileBusy(
                    "Das eigene Browserprofil wird bereits von einer NetMon-Sitzung verwendet."
                ) from exc
            yield directory
        finally:
            os.close(fd)


def _bus_address(path):
    return "unix:path=" + quote_from_bytes(os.fsencode(path), safe="/_-.")


@contextmanager
def _private_bus(runtime_dir):
    for executable in (_DAEMON, _SEND, _SETPRIV):
        if not os.access(executable, os.X_OK):
            raise BrowserSandboxError(
                f"Browser-Werkzeug fehlt: {Path(executable).name}"
            )
    with ExitStack() as stack:
        directory = stack.enter_context(
            tempfile.TemporaryDirectory(prefix="nmb-", dir=runtime_dir)
        )
        path = Path(directory) / "private-bus"
        config = stack.enter_context(tempfile.TemporaryFile(dir=directory))
        config.write(_BUS_CONFIGURATION % _bus_address(path).encode("ascii"))
        config.seek(0)
        read, write = sandbox._pipe(stack)
        process = stack.enter_context(
            sandbox._process(
                [
                    _SETPRIV,
                    "--pdeathsig",
                    "TERM",
                    _DAEMON,
                    "--nofork",
                    f"--config-file=/proc/self/fd/{config.fileno()}",
                    f"--print-address={write.fileno()}",
                ],
                (config.fileno(), write.fileno()),
            )
        )
        write.close()
        sandbox._read_signal(read, "Privater Browser-D-Bus")
        sandbox._owned_socket(path)
        config.close()
        read.close()
        yield path, process


def _firefox_has_bus_name(path):
    try:
        reply = subprocess.run(
            [
                _SEND,
                f"--bus={_bus_address(path)}",
                "--print-reply=literal",
                "--reply-timeout=500",
                "--dest=org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus.ListNames",
            ],
            env=sandbox._HOST_ENV,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=1,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False
    return reply.returncode == 0 and b"org.mozilla." in reply.stdout


def _browser_policies(state_dir, runtime):
    spec = ContainerSpec(
        name="NetMon Browser",
        path=state_dir,
        allowed_domains=["netmonroots.com"],
        source_firefox_dir=runtime,
        homepage_url="about:blank",
        security_profile="strict",
        enable_website_filter=False,
    )
    policies = build_policies_payload(spec)["policies"]
    policies.pop("DisablePocket", None)
    policies["DNSOverHTTPS"] = {"Enabled": False, "Locked": True}
    policies["HttpsOnlyMode"] = "enabled"
    # Firefox skips locked exception preferences when applying the strict category.
    policies["EnableTrackingProtection"] = {
        "Category": "strict",
        "Locked": True,
        "BaselineExceptions": True,
        "ConvenienceExceptions": True,
    }
    policies["NetworkPrediction"] = False
    policies["DefaultDownloadDirectory"] = "${home}/Downloads"
    policies["Bookmarks"] = [
        {
            "Title": "NetMonRoots",
            "URL": "https://netmonroots.com/",
            "Placement": "menu",
        }
    ]
    policies["Preferences"] = {
        "toolkit.legacyUserProfileCustomizations.stylesheets": {
            "Value": True,
            "Status": "user",
        }
    }
    return {"policies": policies}


class BrowserSession:
    """Queue links from the GUI and report asynchronous errors to its main thread."""

    def __init__(self, state_dir, *, browser_dir=FIREFOX_DIR):
        self.state_dir = Path(state_dir)
        self.browser_dir = Path(browser_dir)
        self._links = Queue(maxsize=16)
        self._errors = SimpleQueue()
        self._stop = Event()
        self._worker = None

    def open(self, url):
        if self._stop.is_set():
            raise BrowserSandboxError("Die Browser-Sitzung wird beendet.")
        sandbox._check_url(url)
        try:
            self._links.put_nowait(url)
        except Full as exc:
            raise BrowserSandboxError("Zu viele Browserlinks warten bereits.") from exc
        if self._worker is None:
            self._worker = Thread(target=self._run, name="netmon-browser")
            self._worker.start()

    def take_error(self):
        try:
            return self._errors.get_nowait()
        except Empty:
            return None

    def close(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            try:
                first = self._links.get(timeout=0.25)
            except Empty:
                continue
            try:
                self._serve(first)
            except (BrowserSandboxError, OSError) as exc:
                if not self._stop.is_set():
                    self._errors.put(str(exc))

    def _serve(self, first):
        deadline = time.monotonic() + 30
        while not self._stop.is_set():
            with ExitStack() as stack:
                try:
                    directory = stack.enter_context(_lock_profile(self.state_dir))
                except _ProfileBusy:
                    with _private_directory(self.state_dir) as directory:
                        if link_socket.forward(directory, first, self._stop):
                            return
                else:
                    self._serve_profile(directory, first)
                    return
            if time.monotonic() >= deadline:
                raise BrowserSandboxError(
                    "Die laufende Browser-Sitzung ist nicht erreichbar."
                )
            self._stop.wait(0.25)

    def _serve_profile(self, directory, first):
        runtime = _managed_runtime(self.browser_dir)
        wayland = _wayland_socket()
        policies = _browser_policies(self.state_dir, runtime)
        with (
            link_socket.listen(directory) as listener,
            _private_bus(wayland.parent) as (bus, daemon),
        ):
            args = (runtime, self.state_dir, wayland, bus)
            handoff = partial(self._handoff, args, policies=policies)
            with sandbox._launch_link(
                *args, first, policies=policies, brand=True
            ) as primary:
                ready_deadline = time.monotonic() + 30
                while not self._stop.wait(0.25) and sandbox._browser_running(*primary):
                    if daemon.poll() is not None:
                        raise BrowserSandboxError(
                            "Der private Browser-D-Bus ist beendet."
                        )
                    remote_pending = bool(select.select([listener], [], [], 0)[0])
                    if self._links.empty() and not remote_pending:
                        continue
                    if not _firefox_has_bus_name(bus):
                        if time.monotonic() >= ready_deadline:
                            raise BrowserSandboxError(
                                "Firefox wurde für weitere Links nicht bereit."
                            )
                        continue
                    if remote_pending:
                        link_socket.receive(listener, handoff)
                    if not self._stop.is_set() and not self._links.empty():
                        try:
                            handoff(self._links.get_nowait())
                        except BrowserSandboxError as exc:
                            self._errors.put(str(exc))

    def _handoff(self, args, url, *, policies):
        if self._stop.is_set():
            raise BrowserSandboxError("Die Browser-Sitzung wird beendet.")
        with sandbox._launch_link(
            *args, url, policies=policies, brand=True
        ) as secondary:
            deadline = time.monotonic() + 15
            while sandbox._browser_running(*secondary):
                if self._stop.wait(0.25) or time.monotonic() >= deadline:
                    raise BrowserSandboxError(
                        "Firefox hat die Linkübergabe nicht bestätigt."
                    )
