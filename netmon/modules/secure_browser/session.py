"""Manage the private D-Bus and the lifetime of NetMon's Firefox profile."""

from contextlib import ExitStack, contextmanager
import fcntl
import logging
from functools import partial
import os
from pathlib import Path
from queue import Empty, Full, Queue, SimpleQueue
import re
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
_WESTON = "/usr/bin/weston"
_WESTON_SOCKET = "wayland-0"
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


class X11DisplayError(BrowserSandboxError):
    """The nested display could not be started for this request."""


class _ProfileBusy(BrowserSandboxError):
    pass


def _managed_runtime(path):
    """Use only a provisioned, administrator-managed runtime."""
    for entry in (*reversed(path.parents), path):
        try:
            info = entry.lstat()
        except FileNotFoundError as exc:
            raise BrowserSandboxError(
                f"Die eigene Firefox-Basis fehlt unter {path}. "
                "Bitte das Paket netmon-web-browser-runtime installieren."
            ) from exc
        except OSError as exc:
            raise BrowserSandboxError(
                f"Die eigene Firefox-Basis unter {path} konnte nicht gelesen werden."
            ) from exc
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
    if not all(
        (path / name).is_file() and os.access(path / name, os.X_OK)
        for name in ("firefox", "firefox-bin")
    ):
        raise BrowserSandboxError(
            f"Die Firefox-Basis unter {path} ist unvollständig oder nicht ausführbar. "
            "Bitte das Paket netmon-web-browser-runtime prüfen."
        )
    return path


def managed_runtime_error():
    """Return the protected browser's startup error for the preflight, if any."""
    try:
        _managed_runtime(FIREFOX_DIR)
    except (BrowserSandboxError, OSError) as exc:
        return str(exc)
    return ""


def _private_runtime_dir():
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", ""))
    if not runtime.is_absolute() or ".." in runtime.parts:
        raise BrowserSandboxError("Der Browser benötigt einen privaten Laufzeitordner.")
    info = runtime.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise BrowserSandboxError("Der Browser-Laufzeitordner ist nicht privat.")
    return runtime


def _wayland_socket():
    display = os.environ.get("WAYLAND_DISPLAY", "")
    if not display or Path(display).name != display or display in {".", ".."}:
        raise BrowserSandboxError("Der eigene Browser benötigt eine Wayland-Sitzung.")
    path = _private_runtime_dir() / display
    sandbox._owned_socket(path)
    return path


def _uses_nested_display():
    return os.environ.get(
        "XDG_SESSION_TYPE", ""
    ).lower() == "x11" and not os.environ.get("WAYLAND_DISPLAY")


def _weston_env():
    if os.getuid() == 0:
        raise BrowserSandboxError("NetMon startet Weston nur als regulärer Benutzer.")
    display = os.environ.get("DISPLAY", "")
    if not re.fullmatch(r"(?:unix)?:[0-9]+(?:\.[0-9]+)?", display):
        raise X11DisplayError("Für Weston ist eine lokale X11-Anzeige erforderlich.")
    for executable in (_WESTON, _SETPRIV):
        if not os.access(executable, os.X_OK):
            raise X11DisplayError(
                f"Für den geschützten Start unter X11 fehlt {Path(executable).name}."
            )
    return {
        **sandbox._HOST_ENV,
        "DISPLAY": display,
        "XAUTHORITY": os.environ.get("XAUTHORITY") or str(Path.home() / ".Xauthority"),
    }


def _check_display_requirements():
    if _uses_nested_display():
        _weston_env()
        _private_runtime_dir()
    else:
        _wayland_socket()


def _wait_for_weston(path, process):
    deadline = time.monotonic() + sandbox._START_TIMEOUT
    while time.monotonic() < deadline:
        status = process.poll()
        if status is not None:
            raise BrowserSandboxError(
                f"Weston konnte nicht gestartet werden (Status {status})."
            )
        try:
            sandbox._owned_socket(path)
        except FileNotFoundError:
            time.sleep(0.05)
        else:
            return
    raise BrowserSandboxError("Weston hat keinen Wayland-Socket bereitgestellt.")


def _brand_weston_window(log_path, title, env):
    """Set desktop metadata on the window created by this Weston instance."""
    try:
        with log_path.open("rb") as log:
            # Weston reports the XID before it opens the Wayland listener.
            match = re.search(
                rb"\bx11 output [0-9]+\s*x[0-9]+, window id ([0-9]+)\n",
                log.read(16384),
            )
        if match is None:
            return
        xid = int(match[1])
        if not 0 < xid <= 0xFFFFFFFF:
            return

        subprocess.run(
            [
                "/usr/bin/python3",
                "-I",
                "-B",
                str(Path(__file__).with_name("x11_window.py")),
                str(xid),
                title,
                str(sandbox._BROWSER_ICON),
            ],
            env=env,
            stdin=subprocess.DEVNULL,
            timeout=2,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        logging.getLogger(__name__).warning("Could not set Weston window metadata")


@contextmanager
def _display_socket(*, title="NetmonRoots Browser"):
    if not _uses_nested_display():
        yield _wayland_socket(), None
        return

    env = _weston_env()
    with ExitStack() as stack:
        try:
            runtime = stack.enter_context(
                tempfile.TemporaryDirectory(prefix="nmw-", dir=_private_runtime_dir())
            )
            path = Path(runtime) / _WESTON_SOCKET
            log_path = path.with_name("weston.log")
            process = stack.enter_context(
                sandbox._process(
                    [
                        _SETPRIV,
                        "--no-new-privs",
                        "--pdeathsig",
                        "TERM",
                        _WESTON,
                        "--backend=x11-backend.so",
                        "--shell=kiosk-shell.so",
                        "--no-config",
                        "--use-pixman",
                        "--idle-time=0",
                        f"--socket={_WESTON_SOCKET}",
                        f"--log={log_path}",
                    ],
                    (),
                    env={**env, "XDG_RUNTIME_DIR": runtime},
                )
            )
            _wait_for_weston(path, process)
        except (OSError, BrowserSandboxError) as exc:
            raise X11DisplayError(
                f"Weston-Anzeige konnte nicht eingerichtet werden. {exc}"
            ) from exc
        _brand_weston_window(log_path, title, env)
        yield path, process


def _display_running(process):
    status = process.poll() if process is not None else None
    if status not in (None, 0):
        raise BrowserSandboxError(f"Weston wurde unerwartet beendet (Status {status}).")
    return status is None


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


def _browser_policies(state_dir, runtime, *, nested_x11=False):
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
    if nested_x11:
        policies["Preferences"]["browser.netmon.nestedX11"] = {
            "Value": True,
            "Status": "locked",
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
                    self._errors.put(
                        (str(exc), first if isinstance(exc, X11DisplayError) else None)
                    )

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
        with (
            link_socket.listen(directory) as listener,
            _display_socket() as (wayland, display_process),
            _private_bus(wayland.parent) as (bus, daemon),
        ):
            policies = _browser_policies(
                self.state_dir, runtime, nested_x11=display_process is not None
            )
            args = (runtime, self.state_dir, wayland, bus)
            handoff = partial(self._handoff, args, policies=policies)
            with sandbox._launch_link(
                *args, first, policies=policies, brand=True
            ) as primary:
                ready_deadline = time.monotonic() + 30
                while (
                    not self._stop.wait(0.25)
                    and _display_running(display_process)
                    and sandbox._browser_running(*primary)
                ):
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
                            self._errors.put((str(exc), None))

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
