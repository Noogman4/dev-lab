"""Protected radio output: PCM FIFO read by a PipeWire pipe-tunnel (form H1).

The sandboxed PCM relay only receives a write descriptor for one FIFO. The
user's PipeWire server reads that FIFO with libpipewire-module-pipe-tunnel,
loaded by a user drop-in (``flags = [ nofail ]``, ``node.autoconnect=false``).
NetMon links the tunnel to the current default sink itself and unlinks it
first on stop. There is never a fallback to pacat or any other host client.

Nothing here runs implicitly: ``install``/``uninstall`` change the user's
configuration only when the UI calls them after explicit confirmation.
Readiness checks are evidence of configuration, not a security acceptance.
"""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
import errno
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

TUNNEL_NODE = "netmon-radio-fifo"
FIFO_NAME = "radio.pcm"
LOCK_NAME = "writer.lock"
DROPIN_NAME = "50-netmon-radio-fifo.conf"
DROPIN_MARKER = "# NetMon radio FIFO output (H1)"
PW_DUMP = Path("/usr/bin/pw-dump")
PW_LINK = Path("/usr/bin/pw-link")
PIPEWIRE = Path("/usr/bin/pipewire")
SYSTEMCTL = Path("/usr/bin/systemctl")
AUDIO_UNITS = ("pipewire", "pipewire-pulse", "wireplumber")
CHANNELS = ("FL", "FR")
MAX_TOOL_OUTPUT = 16 * 1024 * 1024
SYSTEM_CONFIGS = (Path("/usr/share/pipewire"), Path("/etc/pipewire"))


class RadioOutputError(RuntimeError):
    """The protected output is not usable; never fall back to pacat."""


@dataclass(frozen=True)
class Paths:
    state_dir: Path
    fifo: Path
    lock: Path
    config_dir: Path
    dropin: Path


@dataclass(frozen=True)
class Linked:
    tunnel_id: int
    tunnel_serial: str
    sink_id: int
    pairs: tuple[tuple[int, int], ...]


def paths(home: Path | None = None, config_home: Path | None = None) -> Paths:
    home = Path(home or os.path.expanduser("~"))
    if config_home is None:
        value = os.environ.get("XDG_CONFIG_HOME", "")
        config_home = Path(value) if os.path.isabs(value) else home / ".config"
    if not home.is_absolute() or not Path(config_home).is_absolute():
        raise RadioOutputError("Ungültiges Benutzerverzeichnis.")
    state_dir = home / ".local/state/netmon/radio-output"
    config_dir = Path(config_home) / "pipewire/pipewire.conf.d"
    return Paths(
        state_dir=state_dir,
        fifo=state_dir / FIFO_NAME,
        lock=state_dir / LOCK_NAME,
        config_dir=config_dir,
        dropin=config_dir / DROPIN_NAME,
    )


def dropin_text(fifo: Path) -> str:
    text = str(fifo)
    if not fifo.is_absolute() or any(c in text for c in '"\\\n\r\0'):
        raise RadioOutputError("Ungültiger FIFO-Pfad für PipeWire.")
    native = "S16LE" if sys.byteorder == "little" else "S16BE"
    return f"""{DROPIN_MARKER}. Remove via NetMon or delete this file.
context.modules = [
 {{ name = libpipewire-module-pipe-tunnel
   args = {{
     tunnel.mode = playback
     remote.name = "internal"
     pipe.filename = "{text}"
     audio.format = {native}
     audio.rate = 48000
     audio.channels = 2
     audio.position = [ FL FR ]
     node.name = "{TUNNEL_NODE}"
     node.description = "NetMon Radio"
     stream.props = {{ node.autoconnect = false }}
   }}
   flags = [ nofail ]
 }}
]
"""


# -- configuration checks (files only, no server contact) -----------------


def _owned_private_dir(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    return (
        stat.S_ISDIR(info.st_mode)
        and info.st_uid == os.getuid()
        and stat.S_IMODE(info.st_mode) == 0o700
    )


def _strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] for line in text.splitlines())


SOCKET_ACCESS = re.compile(r"access\.socket\s*=|access\.legacy\s*=\s*false")


def socket_access_configured(p: Paths, roots=SYSTEM_CONFIGS) -> list[str]:
    """Heuristic for F2 (crash with socket access + internal tunnel client).

    Scans pipewire.conf and its drop-ins; uncommented socket-access settings
    make the setup 'not ready'. A miss is not proof of legacy mode.
    """
    candidates = []
    for root in (*roots, p.config_dir.parent):
        candidates.append(Path(root) / "pipewire.conf")
        directory = Path(root) / "pipewire.conf.d"
        if directory.is_dir():
            candidates.extend(sorted(directory.glob("*.conf")))
    hits = []
    for path in candidates:
        if path == p.dropin or not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        if SOCKET_ACCESS.search(_strip_comments(text)):
            hits.append(str(path))
    return hits


def pipewire_version(run=None) -> str | None:
    rc, out = (run or run_tool)([str(PIPEWIRE), "--version"], timeout=3)
    match = re.search(r"Linked with libpipewire (\d+\.\d+\.\d+)", out or "")
    return match.group(1) if rc == 0 and match else None


def setup_status(
    p: Paths, run=None, roots=SYSTEM_CONFIGS, *, check_version=True
) -> dict:
    """Files and versions only; the live tunnel is checked by open/link.

    check_version=False runs no process at all (cheap UI hint only).
    """
    reasons = []
    try:
        info = p.dropin.lstat()
        if not stat.S_ISREG(info.st_mode):
            reasons.append("Drop-in ist keine reguläre Datei.")
        elif p.dropin.read_text() != dropin_text(p.fifo):
            reasons.append("Drop-in weicht von der NetMon-Vorlage ab.")
    except FileNotFoundError:
        reasons.append("Geschützte Radioausgabe ist nicht eingerichtet.")
    if not _owned_private_dir(p.state_dir):
        reasons.append("Privates Ausgabeverzeichnis fehlt oder ist unzulässig.")
    else:
        try:
            fifo = p.fifo.lstat()
            if not stat.S_ISFIFO(fifo.st_mode) or fifo.st_uid != os.getuid():
                reasons.append("Ausgabedatei ist unzulässig.")
        except FileNotFoundError:
            reasons.append(
                "PipeWire hat die Ausgabe noch nicht geladen "
                "(Audiodienste neu starten)."
            )
    for tool in (PW_DUMP, PW_LINK, PIPEWIRE):
        if not (tool.is_file() and os.access(tool, os.X_OK)):
            reasons.append(f"Werkzeug fehlt: {tool}")
    version = None
    if check_version:
        version = pipewire_version(run) if run or PIPEWIRE.is_file() else None
        if version is None or not version.startswith("1.0."):
            reasons.append(
                f"Nicht unterstützte PipeWire-Version: {version or 'unbekannt'}"
            )
    hits = socket_access_configured(p, roots)
    if hits:
        reasons.append(
            "Socketbasierter PipeWire-Zugriff konfiguriert: " + ", ".join(hits)
        )
    return {"ready": not reasons, "reasons": reasons, "pipewire": version}


# -- explicit install / uninstall (UI only, after confirmation) ------------


def _ensure_dir(path: Path, mode: int, own_levels: int) -> None:
    # Only NetMon's own components are checked; a symlinked $HOME is the
    # user's choice, a symlinked .local/state/netmon or pipewire is not.
    for component in (path, *list(path.parents)[:own_levels]):
        if component.is_symlink():
            raise RadioOutputError(f"Symbolischer Link im Pfad: {component}")
    try:
        path.mkdir(mode=mode, parents=True)
    except FileExistsError:
        pass
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise RadioOutputError(f"Verzeichnis ist unzulässig: {path}")


def install(p: Paths, *, confirmed: bool) -> None:
    if confirmed is not True:
        raise RadioOutputError("Einrichtung nur nach ausdrücklicher Bestätigung.")
    _ensure_dir(p.state_dir, 0o700, own_levels=3)
    os.chmod(p.state_dir, 0o700, follow_symlinks=False)
    _ensure_dir(p.config_dir, 0o755, own_levels=1)
    text = dropin_text(p.fifo)
    if p.dropin.is_symlink():
        raise RadioOutputError("Drop-in ist ein symbolischer Link.")
    if p.dropin.exists() and p.dropin.read_text(errors="replace") != text:
        if not p.dropin.read_text(errors="replace").startswith(DROPIN_MARKER):
            raise RadioOutputError("Fremde Datei mit gleichem Namen vorhanden.")
    temporary = p.dropin.with_name("." + DROPIN_NAME + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    try:
        os.write(fd, text.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temporary, p.dropin)


def uninstall(p: Paths) -> None:
    """Remove only NetMon's own files; takes effect after the next re-login."""
    if p.dropin.is_symlink():
        raise RadioOutputError("Drop-in ist ein symbolischer Link.")
    if p.dropin.exists():
        if not p.dropin.read_text(errors="replace").startswith(DROPIN_MARKER):
            raise RadioOutputError("Fremde Datei wird nicht entfernt.")
        p.dropin.unlink()
    if _owned_private_dir(p.state_dir):
        for name in (FIFO_NAME, LOCK_NAME):
            target = p.state_dir / name
            if target.is_symlink() or target.exists():
                target.unlink()
        p.state_dir.rmdir()


# -- writer side -----------------------------------------------------------


class FifoWriter:
    """One exclusive FIFO write descriptor for the sandboxed relay.

    ENXIO (no reader) means no loaded tunnel: fail closed, never fall back.
    The write-only flag does not stop reopening via /proc/self/fd; the
    private 0700 directory and 0600 mode bound access to the same user.
    """

    def __init__(self, p: Paths):
        self.paths = p
        self.fd = None
        self._lock = None

    def open(self) -> int:
        try:
            directory = os.open(
                self.paths.state_dir,
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            )
        except OSError as exc:
            raise RadioOutputError(
                "Privates Ausgabeverzeichnis fehlt oder ist unzulässig."
            ) from exc
        try:
            info = os.fstat(directory)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
                raise RadioOutputError("Privates Ausgabeverzeichnis ist unzulässig.")
            with ExitStack() as descriptors:
                lock = os.open(
                    LOCK_NAME,
                    os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600,
                    dir_fd=directory,
                )
                descriptors.callback(os.close, lock)
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise RadioOutputError(
                        "Geschützte Ausgabe wird bereits von NetMon verwendet."
                    ) from exc
                try:
                    fd = os.open(
                        FIFO_NAME,
                        os.O_WRONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                        dir_fd=directory,
                    )
                except OSError as exc:
                    if exc.errno == errno.ENXIO:
                        raise RadioOutputError(
                            "Geschützte Ausgabe nicht bereit: kein PipeWire-Tunnel."
                        ) from exc
                    if exc.errno == errno.ENOENT:
                        raise RadioOutputError(
                            "Geschützte Ausgabe noch nicht geladen (Audiodienste neu starten)."
                        ) from exc
                    raise RadioOutputError("Ausgabedatei ist unzulässig.") from exc
                descriptors.callback(os.close, fd)
                info = os.fstat(fd)
                if (
                    not stat.S_ISFIFO(info.st_mode)
                    or info.st_uid != os.getuid()
                    or info.st_nlink != 1
                ):
                    raise RadioOutputError("Ausgabedatei ist unzulässig.")
                os.fchmod(fd, 0o600)
                os.set_blocking(fd, True)
                # Only a fully configured writer takes ownership of both FDs,
                # before anything else (even closing the directory) can fail.
                descriptors.pop_all()
                self.fd, self._lock = fd, lock
        finally:
            os.close(directory)
        return fd

    def close_descriptor(self) -> None:
        """Close the parent copy after handing it to the relay; keep the lock."""
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def close(self) -> None:
        self.close_descriptor()
        if self._lock is not None:
            os.close(self._lock)
            self._lock = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_exc):
        self.close()


# -- graph and links (trusted NetMon side, fixed tools) --------------------


def _tool_env() -> dict:
    # Always the caller's own runtime directory; an inherited XDG_RUNTIME_DIR
    # (even a well-formed /run/user/<other uid>) is never followed.
    runtime = f"/run/user/{os.getuid()}"
    return {"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "XDG_RUNTIME_DIR": runtime}


def run_tool(argv: list[str], *, timeout: float) -> tuple[int, str]:
    if argv[0] not in {str(PW_DUMP), str(PW_LINK), str(PIPEWIRE)}:
        raise RadioOutputError("Unzulässiges Audio-Werkzeug.")
    try:
        result = subprocess.run(
            argv,
            cwd="/",
            env=_tool_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RadioOutputError("Audio-Werkzeug antwortet nicht.") from exc
    if len(result.stdout) > MAX_TOOL_OUTPUT:
        raise RadioOutputError("Audio-Werkzeug liefert zu viele Daten.")
    return result.returncode, result.stdout.decode("utf-8", errors="replace")


def graph(run=None) -> list:
    rc, out = (run or run_tool)([str(PW_DUMP)], timeout=4)
    if rc != 0:
        raise RadioOutputError("PipeWire-Graph nicht lesbar.")
    try:
        data = json.loads(out)
    except ValueError as exc:
        raise RadioOutputError("PipeWire-Graph ist ungültig.") from exc
    if not isinstance(data, list):
        raise RadioOutputError("PipeWire-Graph ist ungültig.")
    return [o for o in data if isinstance(o, dict)]


def _props(obj) -> dict:
    info = obj.get("info") if isinstance(obj.get("info"), dict) else {}
    props = info.get("props")
    return props if isinstance(props, dict) else {}


def find_tunnel(g: list, fifo: Path) -> dict:
    """Weak identification: same-user clients share one trust domain."""
    clients = {
        o.get("id"): _props(o)
        for o in g
        if o.get("type") == "PipeWire:Interface:Client"
    }
    matches = []
    for o in g:
        props = _props(o)
        if (
            o.get("type") == "PipeWire:Interface:Node"
            and props.get("node.name") == TUNNEL_NODE
            and props.get("pipe.filename") == str(fifo)
        ):
            client = clients.get(props.get("client.id"), {})
            if (
                client.get("remote.name") == "internal"
                and client.get("application.process.binary") == "pipewire"
            ):
                matches.append(o)
    if len(matches) != 1:
        raise RadioOutputError("PipeWire-Tunnel der Radioausgabe nicht eindeutig.")
    return matches[0]


def default_sink(g: list) -> dict:
    name = None
    for o in g:
        # pw-dump 1.0.x puts metadata props at the top level, not in info.
        props = o.get("props") if isinstance(o.get("props"), dict) else {}
        if (
            o.get("type") == "PipeWire:Interface:Metadata"
            and props.get("metadata.name") == "default"
        ):
            for entry in o.get("metadata") or []:
                if (
                    isinstance(entry, dict)
                    and entry.get("subject") == 0
                    and entry.get("key") == "default.audio.sink"
                    and isinstance(entry.get("value"), dict)
                ):
                    name = entry["value"].get("name")
    sinks = [
        o
        for o in g
        if o.get("type") == "PipeWire:Interface:Node"
        and _props(o).get("node.name") == name
        and _props(o).get("media.class") == "Audio/Sink"
    ]
    if not isinstance(name, str) or len(sinks) != 1:
        raise RadioOutputError("Keine eindeutige Standard-Audioausgabe.")
    return sinks[0]


def _ports(g: list, node: dict, direction: str) -> dict:
    out = {}
    for o in g:
        props = _props(o)
        if (
            o.get("type") == "PipeWire:Interface:Port"
            and props.get("node.id") == node.get("id")
            and props.get("port.direction") == direction
            and not props.get("port.monitor")
        ):
            channel = props.get("audio.channel")
            if channel in out:
                raise RadioOutputError("Mehrdeutige Audio-Ports.")
            out[channel] = o.get("id")
    return out


def _ids_ok(*values) -> bool:
    return all(
        isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in values
    )


def _linked_pairs(g: list) -> set:
    return {
        (
            o["info"].get("output-port-id"),
            o["info"].get("input-port-id"),
        )
        for o in g
        if o.get("type") == "PipeWire:Interface:Link"
        and isinstance(o.get("info"), dict)
    }


def link(fifo: Path, run=None) -> Linked:
    run = run or run_tool
    g = graph(run)
    tunnel = find_tunnel(g, fifo)
    sink = default_sink(g)
    outs, ins = _ports(g, tunnel, "out"), _ports(g, sink, "in")
    if not all(c in outs and c in ins for c in CHANNELS):
        raise RadioOutputError("Audioausgabe hat keine Stereo-Eingänge (FL/FR).")
    pairs = tuple((outs[c], ins[c]) for c in CHANNELS)
    if not _ids_ok(tunnel.get("id"), sink.get("id"), *[i for p in pairs for i in p]):
        raise RadioOutputError("Ungültige PipeWire-IDs.")
    present = _linked_pairs(g)
    made = []
    try:
        for a, b in pairs:
            # pw-link creates lingering links. Reuse only these exact pairs
            # if a prior owner exited before its asynchronous unlink finished.
            if (a, b) in present:
                continue
            rc, _ = run([str(PW_LINK), str(a), str(b)], timeout=3)
            if rc != 0:
                raise RadioOutputError("Radioausgabe konnte nicht verbunden werden.")
            made.append((a, b))
    except Exception:
        _unlink_pairs(made, run)
        raise
    return Linked(
        tunnel_id=tunnel["id"],
        tunnel_serial=str(_props(tunnel).get("object.serial")),
        sink_id=sink["id"],
        pairs=pairs,
    )


def _unlink_pairs(pairs, run) -> bool:
    ok = True
    for a, b in pairs:
        try:
            rc, _ = run([str(PW_LINK), "-d", str(a), str(b)], timeout=3)
            ok = ok and rc == 0
        except RadioOutputError:
            ok = False
    return ok


def unlink(linked: Linked, run=None) -> bool:
    """First step of every stop (F4): silence before terminating the relay."""
    return _unlink_pairs(linked.pairs, run or run_tool)


def verify(linked: Linked, run=None) -> bool:
    """Watchdog check: same tunnel generation and both links still present."""
    try:
        g = graph(run)
    except RadioOutputError:
        return False
    tunnel = [
        o
        for o in g
        if o.get("type") == "PipeWire:Interface:Node"
        and o.get("id") == linked.tunnel_id
    ]
    if len(tunnel) != 1 or str(_props(tunnel[0]).get("object.serial")) != (
        linked.tunnel_serial
    ):
        return False
    present = _linked_pairs(g)
    return all(pair in present for pair in linked.pairs)


# -- explicit restart of the user's audio services (UI only, confirmed) ----


def _systemctl_env() -> dict:
    env = _tool_env()
    env["DBUS_SESSION_BUS_ADDRESS"] = f"unix:path={env['XDG_RUNTIME_DIR']}/bus"
    return env


def _run_systemctl(argv: list[str], *, timeout: float) -> tuple[int, str]:
    if argv != [str(SYSTEMCTL), "--user", "restart", *AUDIO_UNITS]:
        raise RadioOutputError("Unzulässiger Dienstbefehl.")
    try:
        result = subprocess.run(
            argv,
            cwd="/",
            env=_systemctl_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RadioOutputError("Audiodienste antworten nicht.") from exc
    return result.returncode, result.stderr.decode("utf-8", errors="replace")[:2048]


def restart_audio_services(run=None, *, timeout: float = 30.0) -> None:
    """Restart only the user's own PipeWire units; interrupts all audio briefly.

    Never called implicitly: the UI asks first. No root, no system units.
    """
    rc, _err = (run or _run_systemctl)(
        [str(SYSTEMCTL), "--user", "restart", *AUDIO_UNITS], timeout=timeout
    )
    if rc != 0:
        raise RadioOutputError("Audiodienste konnten nicht neu gestartet werden.")


def wait_for_fifo(p: Paths, *, timeout: float = 8.0, clock=None, sleep=None) -> bool:
    """After a restart PipeWire creates the FIFO asynchronously; wait bounded."""
    import time

    clock = clock or time.monotonic
    sleep = sleep or time.sleep
    end = clock() + timeout
    while True:
        try:
            if stat.S_ISFIFO(p.fifo.lstat().st_mode):
                return True
        except OSError:
            pass
        if clock() >= end:
            return False
        sleep(0.1)
