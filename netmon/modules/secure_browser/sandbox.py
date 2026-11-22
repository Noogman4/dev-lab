"""Sandboxed Firefox launcher for the NetMon browser integration.

The caller selects a verified Firefox build and supplies an instance-private
D-Bus socket. The regular desktop bus is not part of the browser's environment.
"""

from contextlib import ExitStack, contextmanager
import fcntl
import json
import os
from pathlib import Path
import select
import stat
import subprocess
import tempfile
from threading import Thread
import time
from urllib.parse import urlsplit

from netmon.core.private_logs import _private_directory

from . import network_policy

_BWRAP = "/usr/bin/bwrap"
_SLIRP = "/usr/bin/slirp4netns"
_NSENTER = "/usr/bin/nsenter"
_CHROME_DIR = Path(__file__).with_name("resources") / "browser-chrome"
_BROWSER_ICON = Path(__file__).resolve().parents[3] / "tools" / "netmon.png"
_HOST_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
_START_TIMEOUT = 12
_NS_GET_USERNS = 0xB701  # _IO(NSIO, 0x1), linux/nsfs.h
_GTK_WINDOW_BUTTONS = ":minimize,maximize,close"
_RUNTIME_PATHS = (
    "/usr/lib",
    "/lib",
    "/lib64",
    "/usr/share/fontconfig",
    "/usr/share/fonts",
    "/usr/share/glib-2.0/schemas",
    "/usr/share/icons",
    "/usr/share/mime",
    "/usr/share/X11/xkb",
    "/etc/fonts",
    "/etc/ssl/certs",
)


class BrowserSandboxError(RuntimeError):
    """The browser cannot be run with the intended isolation."""


def _check_url(url):
    if (
        not isinstance(url, str)
        or not url
        or len(url) > 8192
        or any(
            char.isspace() or ord(char) <= 32 or ord(char) == 127 or char == "\\"
            for char in url
        )
    ):
        raise BrowserSandboxError("Ungültiger Weblink.")
    try:
        parts = urlsplit(url)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or "%" in parts.netloc
            or parts.netloc.endswith(":")
            or parts.port == 0
        ):
            raise ValueError
    except ValueError as exc:
        raise BrowserSandboxError(
            "Nur HTTP(S)-Links ohne Zugangsdaten sind erlaubt."
        ) from exc


def _owned_socket(path):
    info = path.lstat()
    if (
        not path.is_absolute()
        or not stat.S_ISSOCK(info.st_mode)
        or info.st_uid != os.getuid()
    ):
        raise BrowserSandboxError("Erwarteter benutzereigener Unix-Socket fehlt.")
    return str(path)


def _pipe(stack):
    read_fd, write_fd = os.pipe()
    return (
        stack.enter_context(os.fdopen(read_fd, "rb", buffering=0)),
        stack.enter_context(os.fdopen(write_fd, "wb", buffering=0)),
    )


@contextmanager
def _process(command, fds, *, env=_HOST_ENV):
    process = subprocess.Popen(
        command,
        env=env,
        stdin=subprocess.DEVNULL,
        pass_fds=fds,
        start_new_session=True,
    )
    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def _read_signal(pipe, description, *, limit=4096, until_eof=False):
    deadline = time.monotonic() + _START_TIMEOUT
    data = bytearray()
    while len(data) < limit:
        readable, _, _ = select.select(
            [pipe], [], [], max(0, deadline - time.monotonic())
        )
        if not readable:
            break
        chunk = os.read(pipe.fileno(), limit - len(data))
        if not chunk:
            if data:
                return bytes(data)
            break
        data.extend(chunk)
        if not until_eof:
            return bytes(data)
    raise BrowserSandboxError(f"{description} wurde nicht bereit.")


def _sandbox_command(
    browser, profile, downloads, wayland, bus, url, config, *, chrome=None
):
    command = [
        _BWRAP,
        "--unshare-user",
        "--unshare-net",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--cap-drop",
        "ALL",
        "--die-with-parent",
        "--new-session",
        "--clearenv",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--perms",
        "0700",
        "--dir",
        "/run/browser",
        "--perms",
        "0700",
        "--dir",
        "/home/browser",
    ]
    for path in _RUNTIME_PATHS:
        if Path(path).is_dir():
            command += ["--ro-bind", path, path]
    for name, fd in config.items():
        command += ["--ro-bind-data", str(fd), f"/etc/{name}"]
    command += [
        "--ro-bind-fd",
        str(browser),
        "/browser",
        "--bind-fd",
        str(profile),
        "/home/browser/profile",
        "--bind-fd",
        str(downloads),
        "/home/browser/Downloads",
        "--ro-bind",
        wayland,
        "/run/browser/wayland-0",
        "--ro-bind",
        bus,
        "/run/browser/private-bus",
        "--chdir",
        "/home/browser",
    ]
    if chrome is not None:
        style_dir, icon = chrome
        command += [
            "--ro-bind-fd",
            str(style_dir),
            "/home/browser/profile/chrome",
            "--ro-bind-data",
            str(icon),
            "/etc/netmon-browser.png",
        ]
    environment = {
        "HOME": "/home/browser",
        "LC_ALL": "C",
        "XDG_RUNTIME_DIR": "/run/browser",
        "XDG_CONFIG_HOME": "/home/browser/.config",
        "XDG_CACHE_HOME": "/home/browser/.cache",
        "XDG_DATA_HOME": "/home/browser/.local/share",
        "XDG_DATA_DIRS": "/usr/share",
        "WAYLAND_DISPLAY": "wayland-0",
        "GDK_BACKEND": "wayland",
        "GSETTINGS_BACKEND": "keyfile",
        "MOZ_ENABLE_WAYLAND": "1",
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/browser/private-bus",
        "GTK_USE_PORTAL": "0",
        "NO_AT_BRIDGE": "1",
        "MOZ_CRASHREPORTER_DISABLE": "1",
    }
    for key, value in environment.items():
        command += ["--setenv", key, value]
    command += [
        "--",
        "/browser/firefox",
        "--profile",
        "/home/browser/profile",
    ]
    if url is None:
        return command + ["--no-remote"]
    return command + ["--new-tab", url]


def _network_user_namespace(stack, child_pid):
    net_ns = os.open(f"/proc/{child_pid}/ns/net", os.O_RDONLY | os.O_CLOEXEC)
    stack.callback(os.close, net_ns)
    if os.path.samestat(os.fstat(net_ns), os.stat("/proc/self/ns/net")):
        raise BrowserSandboxError("Der Browser hat keinen eigenen Netzwerk-Namensraum.")
    # The network namespace can belong to an outer user namespace of the child.
    user_ns = fcntl.ioctl(net_ns, _NS_GET_USERNS, 0)
    stack.callback(os.close, user_ns)
    return net_ns, user_ns


def _install_network_filter(net_ns, user_ns):
    # Bubblewrap's outer UID mapping gives this helper CAP_NET_ADMIN only in
    # the private network namespace. Keep the mapped credentials on entry.
    try:
        host_networks = network_policy.host_networks(_HOST_ENV, _START_TIMEOUT)
        subprocess.run(
            [
                _NSENTER,
                f"--user=/proc/self/fd/{user_ns}",
                f"--net=/proc/self/fd/{net_ns}",
                "--preserve-credentials",
                "--",
                network_policy.NFT,
                "-f",
                "-",
            ],
            input=network_policy.ruleset(host_networks),
            text=True,
            env=_HOST_ENV,
            pass_fds=(net_ns, user_ns),
            timeout=_START_TIMEOUT,
            check=True,
        )
    except (
        OSError,
        subprocess.SubprocessError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise BrowserSandboxError(
            "Der Netzwerkfilter der Browser-Sandbox konnte nicht eingerichtet werden."
        ) from exc


def _stop_network_on_address_change(stack, monitor, network):
    cancel_read, cancel_write = _pipe(stack)

    def watch():
        try:
            readable, _, _ = select.select([monitor, cancel_read], [], [])
            if cancel_read in readable:
                return
        except (OSError, ValueError):
            pass
        network.terminate()

    watcher = Thread(target=watch, name="browser-address-monitor", daemon=True)
    watcher.start()
    stack.callback(watcher.join)
    stack.callback(cancel_write.close)


@contextmanager
def _networked_browser(stack, command, fds):
    info_read, info_write = _pipe(stack)
    start_read, start_write = _pipe(stack)
    ready_read, ready_write = _pipe(stack)
    exit_read, exit_write = _pipe(stack)
    command[1:1] = [
        "--info-fd",
        str(info_write.fileno()),
        "--block-fd",
        str(start_read.fileno()),
    ]
    browser = stack.enter_context(
        _process(command, (*fds, info_write.fileno(), start_read.fileno()))
    )
    info_write.close()
    start_read.close()
    try:
        child_pid = json.loads(
            _read_signal(info_read, "Browser-Sandbox", until_eof=True)
        )["child-pid"]
        if type(child_pid) is not int or child_pid <= 1:
            raise ValueError
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise BrowserSandboxError(
            "Die Browser-Sandbox hat keine gültige Prozess-ID gemeldet."
        ) from exc
    net_ns, user_ns = _network_user_namespace(stack, child_pid)
    monitor = stack.enter_context(network_policy.host_address_monitor())
    _install_network_filter(net_ns, user_ns)
    # Bubblewrap maps the caller to UID 0 while setting up /dev/pts, then
    # launches Firefox as the original UID. slirp needs that outer mapping
    # for its own sandbox. Only the helper joins it, keeping host networking.
    network = stack.enter_context(
        _process(
            [
                _NSENTER,
                f"--user=/proc/self/fd/{user_ns}",
                "--preserve-credentials",
                "--",
                _SLIRP,
                "--configure",
                "--disable-host-loopback",
                "--enable-sandbox",
                "--enable-seccomp",
                "--netns-type=path",
                "--ready-fd",
                str(ready_write.fileno()),
                "--exit-fd",
                str(exit_read.fileno()),
                f"/proc/self/fd/{net_ns}",
                network_policy.SLIRP_INTERFACE,
            ],
            (ready_write.fileno(), exit_read.fileno(), net_ns, user_ns),
        )
    )
    ready_write.close()
    exit_read.close()
    try:
        if (
            _read_signal(ready_read, "Browser-Netzwerk", limit=1) != b"1"
            or network.poll() is not None
        ):
            raise BrowserSandboxError(
                "Das isolierte Browser-Netzwerk konnte nicht starten."
            )
        if select.select([monitor], [], [], 0)[0]:
            raise BrowserSandboxError(
                "Die Host-Adressen haben sich beim Browser-Start geändert."
            )
        _stop_network_on_address_change(stack, monitor, network)
        start_write.write(b"1")
        start_write.close()
        yield browser, network
    finally:
        exit_write.close()


def _browser_running(browser, network):
    result = browser.poll()
    if result == 0:
        return False
    if result is not None:
        raise BrowserSandboxError(
            "Firefox konnte den Link in der Sandbox nicht öffnen."
        )
    if network.poll() is not None:
        raise BrowserSandboxError(
            "Die Verbindung zum isolierten Browser-Netzwerk ist beendet."
        )
    return True


def _require_network_tools():
    for tool in (_BWRAP, _SLIRP, _NSENTER, network_policy.IP, network_policy.NFT):
        if not os.access(tool, os.X_OK):
            raise BrowserSandboxError(f"Sandbox-Werkzeug fehlt: {Path(tool).name}")
    if not os.access("/dev/net/tun", os.R_OK | os.W_OK):
        raise BrowserSandboxError("Das TUN-Gerät ist für den Browser nicht verfügbar.")


@contextmanager
def _launch_link(
    browser_dir: Path,
    state_dir: Path,
    wayland: Path,
    private_bus: Path,
    url: str | None,
    *,
    policies: dict | None = None,
    brand: bool = False,
):
    if url is not None:
        _check_url(url)
    if os.getuid() == 0:
        raise BrowserSandboxError("NetMon startet Firefox nur als regulärer Benutzer.")
    if private_bus.name != "private-bus" or wayland == private_bus:
        raise BrowserSandboxError("Der Browser benötigt einen eigenen D-Bus-Socket.")
    _require_network_tools()
    if not browser_dir.is_absolute():
        raise BrowserSandboxError("Die Firefox-Basis benötigt einen absoluten Pfad.")
    try:
        with ExitStack() as stack:
            stack.enter_context(_private_directory(private_bus.parent))
            wayland_socket, bus_socket = _owned_socket(wayland), _owned_socket(
                private_bus
            )
            runtime = os.open(
                browser_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            )
            stack.callback(os.close, runtime)
            for name in ("firefox", "firefox-bin"):
                binary = os.stat(name, dir_fd=runtime, follow_symlinks=False)
                if (
                    not stat.S_ISREG(binary.st_mode)
                    or not binary.st_mode & stat.S_IXUSR
                ):
                    raise BrowserSandboxError(
                        "Die Firefox-Basis enthält keine ausführbare Binärdatei."
                    )
            profile = stack.enter_context(_private_directory(state_dir / "profile"))
            downloads = stack.enter_context(_private_directory(state_dir / "downloads"))
            files = {
                "passwd": f"browser:x:{os.getuid()}:{os.getgid()}:Browser:/home/browser:/bin/false\n",
                "group": f"browser:x:{os.getgid()}:\n",
                "nsswitch.conf": "passwd: files\ngroup: files\nhosts: files dns\n",
                "hosts": "127.0.0.1 localhost\n::1 localhost\n",
                "resolv.conf": (
                    f"nameserver {network_policy.SLIRP_DNS}\noptions timeout:2 attempts:2\n"
                ),
                "gtk-3.0/settings.ini": (
                    f"[Settings]\ngtk-decoration-layout={_GTK_WINDOW_BUTTONS}\n"
                ),
                # GTK on Wayland can take this value from GSettings instead.
                "glib-2.0/settings/defaults": (
                    "[org/gnome/desktop/wm/preferences]\n"
                    f"button-layout='{_GTK_WINDOW_BUTTONS}'\n"
                ),
            }
            if policies is not None:
                files["firefox/policies/policies.json"] = json.dumps(policies)
            chrome = ()
            if brand:
                stack.enter_context(
                    _private_directory(state_dir / "profile" / "chrome")
                )
                style = os.open(
                    _CHROME_DIR,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                )
                stack.callback(os.close, style)
                icon = stack.enter_context(_BROWSER_ICON.open("rb"))
                chrome = (style, icon.fileno())
            config = {}
            for name, content in files.items():
                source = stack.enter_context(tempfile.TemporaryFile())
                source.write(content.encode("ascii"))
                source.seek(0)
                config[name] = source.fileno()
            command = _sandbox_command(
                runtime,
                profile,
                downloads,
                wayland_socket,
                bus_socket,
                url,
                config,
                chrome=chrome or None,
            )
            with _networked_browser(
                stack, command, (runtime, profile, downloads, *config.values(), *chrome)
            ) as processes:
                yield processes
    except OSError as exc:
        raise BrowserSandboxError(
            "Sandbox-Start fehlgeschlagen. Bubblewrap, slirp4netns, nftables, Firefox und Wayland prüfen."
        ) from exc


def run_link(
    browser_dir: Path, state_dir: Path, wayland: Path, private_bus: Path, url: str
):
    """Run one launch or handoff and supervise it until the child exits."""
    _check_url(url)
    if private_bus != state_dir / "session" / "private-bus":
        raise BrowserSandboxError("Der Browser benötigt einen eigenen D-Bus-Socket.")
    with _launch_link(browser_dir, state_dir, wayland, private_bus, url) as processes:
        while _browser_running(*processes):
            time.sleep(0.25)
