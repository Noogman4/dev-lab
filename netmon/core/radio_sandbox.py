"""Offline decoder with separate HTTP(S) source and a protected FIFO output.

Audio leaves the sandboxes through an anonymous pipe. A trusted bounded writer
alone owns the FIFO read by the user's PipeWire server (form H1). No sandbox
receives that FIFO or an audio control socket; there is no fallback to pacat.

Media, metadata, preset download and offline ZIP preparation; not projectM rendering.
No successful launch is presented as an independent security verification.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
import json
import importlib.util
from functools import lru_cache
import itertools
import os
from pathlib import Path
import re
import selectors
import socket
import stat
import struct
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlsplit

from netmon.core import radio_fifo_output as fifo_output

BWRAP = Path("/usr/bin/bwrap")
MPV = Path("/usr/bin/mpv")
FFMPEG = Path("/usr/bin/ffmpeg")
PACAT = Path("/usr/bin/pacat")  # diagnostic probes only; not in playback
PYTHON = Path("/usr/bin/python3")
FETCHER = Path(__file__).with_name("radio_fetch.py")
CATALOG = Path(__file__).with_name("radio_catalog.py")
PRESET_ZIP = Path(__file__).with_name("projectm_zip.py")
LOGO = Path(__file__).with_name("radio_logo.py")
PCM = Path(__file__).with_name("radio_pcm.py")
ICON_HTTP = Path(__file__).with_name("icon_http.py")
ICON_PAYLOAD = Path(__file__).with_name("icon_payload.py")
PILLOW = Path("/usr/lib/python3/dist-packages/PIL")
IPC_PATH = "/run/control/mpv.sock"
_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": "/nonexistent"}
SYSTEMD_RUN = Path("/usr/bin/systemd-run")
PRLIMIT = Path("/usr/bin/prlimit")

# G-Quota: per-capsule limits in a transient user scope (cgroup v2, no root)
# plus per-process rlimits and a bounded /tmp. Measured use (2026-11-10):
# mpv ~70 MiB/10 threads, fetch ~26 MiB/3, relay ~18 MiB/3, CPU < 0.3 %.
# Generous bounds: stop runaways, never touch normal playback.
QUOTAS = {
    "decoder": {
        "memory": "512M",
        "tasks": 64,
        "cpu": 100,
        "tmpfs": 16 << 20,
        "nofile": 256,
        "fsize": 16 << 20,
    },
    "fetch": {
        "memory": "128M",
        "tasks": 16,
        "cpu": 50,
        "tmpfs": 16 << 20,
        "nofile": 64,
        "fsize": 1 << 20,
    },
    "relay": {
        "memory": "128M",
        "tasks": 16,
        "cpu": 50,
        "tmpfs": 16 << 20,
        "nofile": 64,
        "fsize": 1 << 20,
    },
    # Recording: FSIZE also bounds writes to the inherited output file (R10).
    "encoder": {
        "memory": "256M",
        "tasks": 32,
        "cpu": 100,
        "tmpfs": 16 << 20,
        "nofile": 64,
        "fsize": 2 << 30,
    },
}
# projectM (measured 2026-11-10, synthetic preset, 30 fps): renderer ~122 MiB,
# 9 threads, ~24 % CPU; Xvfb ~16 MiB/3; PCM feeder and pixel reader (ffmpeg)
# ~50 MiB/6 each. Renderer defaults to 200 % CPU; the explicit performance
# profile allows 300 %. Neither profile promises its target FPS for every preset.
# FSIZE/NOFILE for Xvfb close G1.
QUOTAS.update(
    {
        "pm-feeder": {
            "memory": "256M",
            "tasks": 32,
            "cpu": 50,
            "tmpfs": 16 << 20,
            "nofile": 128,
            "fsize": 16 << 20,
        },
        "pm-display": {
            "memory": "256M",
            "tasks": 16,
            "cpu": 50,
            "tmpfs": 16 << 20,
            "nofile": 128,
            "fsize": 16 << 20,
        },
        "pm-renderer": {
            "memory": "1G",
            "tasks": 64,
            "cpu": 200,
            "tmpfs": 16 << 20,
            "nofile": 256,
            "fsize": 16 << 20,
        },
        "pm-pixels": {
            "memory": "512M",
            "tasks": 32,
            "cpu": 50,
            "tmpfs": 16 << 20,
            "nofile": 128,
            "fsize": 16 << 20,
        },
    }
)
QUOTAS["pm-renderer-performance"] = {**QUOTAS["pm-renderer"], "cpu": 300}
RECORDING_MAX_BYTES = QUOTAS["encoder"]["fsize"]
# Short-lived helpers (title, reachability, catalog, logo, presets) run very
# often; a transient scope each would log a journal line per call. They get a
# bounded /tmp here and fixed self-limits (AS, CPU, NPROC 0, ...) in-process.
HELPER_TMPFS = 16 << 20
_SCOPES = itertools.count()


class RadioSandboxError(RuntimeError):
    """The protected playback could not be started; never retry unprotected."""


def available() -> bool:
    """Tool presence only; this does not prove that namespaces or audio work."""
    return (
        all(
            path.is_file() and os.access(path, os.X_OK)
            for path in (
                BWRAP,
                MPV,
                PYTHON,
                SYSTEMD_RUN,
                PRLIMIT,
                fifo_output.PW_DUMP,
                fifo_output.PW_LINK,
            )
        )
        and FETCHER.is_file()
        and PCM.is_file()
    )


def recording_available():
    """Tool presence only, not successful startup or a security acceptance."""
    return all(
        path.is_file()
        for path in (BWRAP, FFMPEG, PYTHON, FETCHER, SYSTEMD_RUN, PRLIMIT)
    )


def _recording_command():
    # No media URL, host filename, network protocol or file protocol reaches
    # ffmpeg. The parent exclusively owns the already opened output file.
    return [
        str(FFMPEG),
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostats",
        "-stats_period",
        "0.25",
        "-progress",
        "/run/record-progress",
        "-protocol_whitelist",
        "pipe",
        "-probesize",
        "262144",
        "-analyzeduration",
        "1000000",
        "-threads",
        "1",
        "-i",
        "pipe:0",
        "-map",
        "0:a:0",
        "-map_metadata",
        "-1",
        "-map_chapters",
        "-1",
        "-vn",
        "-sn",
        "-dn",
        "-threads",
        "1",
        "-acodec",
        "libmp3lame",
        "-b:a",
        "192k",
        "-write_xing",
        "0",
        "-id3v2_version",
        "0",
        "-f",
        "mp3",
        "pipe:1",
    ]


def _recording_target(path):
    path = Path(path)
    if not path.is_absolute() or path.suffix.lower() != ".mp3":
        raise RadioSandboxError("Ungültiges Aufnahmeziel.")
    parent = path.parent.resolve(strict=True)
    directory = os.open(
        parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        for index in range(1000):
            name = path.name if index == 0 else f"{path.stem}-{index:03d}.mp3"
            try:
                descriptor = os.open(
                    name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600,
                    dir_fd=directory,
                )
            except FileExistsError:
                continue
            return descriptor, str(parent / name)
        raise RadioSandboxError("Kein freier Aufnahmedateiname verfügbar.")
    finally:
        os.close(directory)


def _recording_sandbox_command(directory, runtime):
    command = _sandbox_command(
        _recording_command(),
        directory,
        runtime,
        None,
        local_file=None,
        catalog_parser=True,
    )
    index = command.index("--")
    command[index:index] = [
        "--bind",
        str(directory / "progress"),
        "/run/record-progress",
    ]
    return command


class RecordingProcess:
    """Own a fixed pipe-only encoder and source until both have been reaped."""

    def __init__(self, encoder, source, temporary, output_path, progress_fd):
        self._process = encoder
        self._source_process = source
        self._temporary = temporary
        self.output_path = output_path
        self.sandbox_state = "started"
        self.runtime_verified = False
        self._lock = threading.RLock()
        self._result = None
        self._failure = None
        self._stopping = False
        self._drain_deadline = None
        self._buffer = bytearray()
        self._progress_size = self._progress_time = 0
        self.ready = False
        self.size_limit_reached = False
        self._progress_file = os.fdopen(progress_fd, "rb", buffering=0)

    @property
    def pid(self):
        return self._process.pid

    def _drain_progress(self):
        try:
            data = os.read(self._progress_file.fileno(), 8192)
        except BlockingIOError:
            return
        self._buffer.extend(data)
        while b"\n" in self._buffer:
            line, _, rest = self._buffer.partition(b"\n")
            self._buffer = bytearray(rest)
            key, _, value = bytes(line).partition(b"=")
            if key in {b"out_time_us", b"total_size"} and re.fullmatch(
                rb"[0-9]{1,20}", value
            ):
                if key == b"out_time_us":
                    self._progress_time = int(value)
                else:
                    self._progress_size = int(value)
            if key == b"progress" and value in {b"continue", b"end"}:
                self.ready = self.ready or (
                    self._progress_size > 0 and self._progress_time > 0
                )
        if len(self._buffer) > 8192:
            self._failure = 1
            self._buffer.clear()
            self.kill()

    def poll(self):
        with self._lock:
            if self._result is not None:
                return self._result
            self._drain_progress()
            result = self._process.poll()
            source_result = self._source_process.poll()
            if source_result is not None:
                if source_result != 0 and not self._stopping:
                    self._failure = source_result
                if result is None:
                    if self._drain_deadline is None:
                        self._drain_deadline = time.monotonic() + 3
                        if self._failure is not None:
                            self._process.terminate()
                    if time.monotonic() >= self._drain_deadline:
                        self._process.kill()
                        result = self._process.wait(timeout=3)
            if result is not None:
                if source_result is None:
                    self._source_process.kill()
                    self._source_process.wait(timeout=3)
                self._result = self._failure if self._failure is not None else result
                if result != 0:
                    # Require a failed encoder and an actually full file;
                    # a source error or a file just below the limit is not enough.
                    try:
                        size = os.stat(self.output_path).st_size
                    except OSError:
                        size = 0
                    self.size_limit_reached = size >= RECORDING_MAX_BYTES
                self._progress_file.close()
                self._temporary.cleanup()
            return self._result

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            result = self.poll()
            if result is not None:
                return result
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(str(FFMPEG), timeout)
            time.sleep(0.03)

    def terminate(self):
        with self._lock:
            source_result = self._source_process.poll()
            if source_result not in (None, 0) and not self._stopping:
                self._failure = source_result
            self._stopping = True
            if source_result is None:
                self._source_process.terminate()
            # EOF lets ffmpeg flush its MP3 encoder; the caller bounds wait().

    def kill(self):
        with self._lock:
            self._stopping = True
            for child in (self._process, self._source_process):
                if child.poll() is None:
                    child.kill()


def start_recording(url, output_path, *, work_root=None):
    """Return only after bounded positive encoder progress; no unsafe retry."""
    if (
        not recording_available()
        or not isinstance(url, str)
        or not 0 < len(url) <= 8192
    ):
        raise RadioSandboxError(
            "Geschützte Aufnahme ist nicht verfügbar oder ungültig."
        )
    _require_quota_manager()
    # The same fixed public-target and direct-stream policy as playback.
    stdlib, source_runtime = _fetch_runtime()
    runtime = _runtime_files(FFMPEG)
    temporary = tempfile.TemporaryDirectory(prefix="record-", dir=work_root)
    source = encoder = owner = None
    descriptor = read_fd = write_fd = progress_fd = None
    try:
        directory = Path(temporary.name)
        _prepare_directory(directory)
        request = directory / "request.json"
        request.write_text(json.dumps({"url": url}))
        request.chmod(0o600)
        progress_path = directory / "progress"
        os.mkfifo(progress_path, 0o600)
        progress_fd = os.open(progress_path, os.O_RDWR | os.O_NONBLOCK | os.O_CLOEXEC)
        descriptor, actual_path = _recording_target(output_path)
        read_fd, write_fd = os.pipe()
        source = subprocess.Popen(
            _limited(_fetch_command(directory, None, stdlib, source_runtime), "fetch"),
            cwd="/",
            env=_quota_env(),
            stdin=subprocess.DEVNULL,
            stdout=write_fd,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        encoder = subprocess.Popen(
            _limited(_recording_sandbox_command(directory, runtime), "encoder"),
            cwd="/",
            env=_quota_env(),
            stdin=read_fd,
            stdout=descriptor,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        for fd in (descriptor, read_fd, write_fd):
            os.close(fd)
        descriptor = read_fd = write_fd = None
        owner = RecordingProcess(encoder, source, temporary, actual_path, progress_fd)
        progress_fd = None
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            result = owner.poll()
            if owner.ready and (result is None or result == 0):
                return owner
            if result is not None:
                break
            time.sleep(0.03)
        raise RadioSandboxError(
            "Geschützte Aufnahme meldet keinen Encoder-Fortschritt."
        )
    except Exception:
        for child in (encoder, source):
            if child is not None:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=3)
        if owner is not None:
            owner._progress_file.close()
        temporary.cleanup()
        raise
    finally:
        for fd in (descriptor, read_fd, write_fd, progress_fd):
            if fd is not None:
                os.close(fd)


def _runtime_files(
    executable: Path, *, allow_static_extension=False
) -> tuple[Path, ...]:
    """Resolve the installed executable's ELF closure, without ambient LD_*.

    ldd is only used for trusted system executables/libraries, never for media.
    Missing libraries and unexpected output fail closed. No whole /usr tree is
    exposed, and no shell or package manager is mounted into the sandbox.
    """
    result = subprocess.run(
        ["/usr/bin/ldd", str(executable)],
        env=_ENV,
        cwd="/",
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode != 0:
        raise RadioSandboxError(
            "mpv-Laufzeitbibliotheken konnten nicht ermittelt werden."
        )
    if allow_static_extension and result.stdout.strip() == "statically linked":
        return (executable,)
    files = {executable}
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"linux-vdso\S* \(0x[0-9a-fA-F]+\)", line):
            continue
        match = re.fullmatch(r"(?:\S+ => )?(/\S+) \(0x[0-9a-fA-F]+\)", line)
        if match is None:
            raise RadioSandboxError("Unvollständiger mpv-Bibliotheksplan.")
        path = Path(match[1])
        if not str(path).startswith(("/lib/", "/lib64/", "/usr/lib/", "/usr/lib64/")):
            raise RadioSandboxError("Unerwarteter mpv-Bibliothekspfad.")
        files.add(path)
    if len(files) < 2 or any(not path.is_file() for path in files):
        raise RadioSandboxError("Unvollständiger mpv-Bibliotheksplan.")
    return tuple(sorted(files))


def _audio_socket() -> Path:
    # Deliberately ignore PULSE_SERVER and do not copy an authentication cookie.
    # No autospawn, TCP fallback, full runtime directory or /dev/snd grant.
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    path = Path(runtime) / "pulse/native"
    try:
        info = path.lstat()
    except OSError as exc:
        raise RadioSandboxError("Lokaler PulseAudio-Zugang fehlt.") from exc
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
        raise RadioSandboxError("Lokaler PulseAudio-Zugang ist nicht zulässig.")
    return path


def _network_files() -> tuple[tuple[Path, str], ...]:
    files = []
    for name in (
        "/etc/resolv.conf",
        "/etc/hosts",
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        source = Path(name).resolve(strict=True)
        if not source.is_file():
            raise RadioSandboxError("Systemdatei für Radiostreams fehlt.")
        files.append((source, name))
    return tuple(files)


def _sandbox_command(
    command: list[str],
    directory: Path,
    runtime_files: tuple[Path, ...],
    audio_socket: Path,
    *,
    local_file: Path | None,
    audio_output: bool = False,
    network_source: bool = False,
    catalog_parser: bool = False,
) -> list[str]:
    """Only the fixed HTTP(S) source receives the caller's network namespace."""
    args = [
        str(BWRAP),
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--unshare-cgroup-try",
        "--disable-userns",
        "--assert-userns-disabled",
        "--die-with-parent",
        "--new-session",
        "--cap-drop",
        "ALL",
        "--clearenv",
    ]
    if not network_source:
        args += ["--unshare-net"]
    for path in runtime_files:
        args += ["--ro-bind", str(path.resolve(strict=True)), str(path)]
    args += [
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/home/radio",
        "--ro-bind",
        str(directory / "passwd"),
        "/etc/passwd",
        "--ro-bind",
        str(directory / "group"),
        "/etc/group",
        "--ro-bind",
        str(directory / "nsswitch.conf"),
        "/etc/nsswitch.conf",
        "--chdir",
        "/home/radio",
    ]
    if audio_output:
        args += [
            "--ro-bind",
            str(audio_socket),
            "/run/audio/pulse",
            "--ro-bind",
            str(directory / "pulse.conf"),
            "/etc/pulse/client.conf",
        ]
    elif not network_source and not catalog_parser:
        args += ["--bind", str(directory / "control"), "/run/control"]
    if local_file is not None:
        args += ["--ro-bind", str(local_file), "/media/selected"]
    if network_source:
        # Resolved file binds, not the parent /run/systemd or /etc directories.
        for source, name in _network_files():
            args += ["--ro-bind", str(source), name]
    environment = {
        "PATH": "/usr/bin",
        "HOME": "/home/radio",
        "LC_ALL": "C.UTF-8",
        "TMPDIR": "/tmp",
        "XDG_RUNTIME_DIR": "/run",
        "XDG_CONFIG_HOME": "/home/radio/.config",
        "XDG_CACHE_HOME": "/home/radio/.cache",
        "XDG_DATA_HOME": "/home/radio/.local/share",
        "XDG_STATE_HOME": "/home/radio/.local/state",
    }
    if audio_output:
        environment.update(
            PULSE_SERVER="unix:/run/audio/pulse",
            PULSE_CLIENTCONFIG="/etc/pulse/client.conf",
        )
    if network_source:
        environment["RES_OPTIONS"] = "timeout:2 attempts:1"
    for key, value in environment.items():
        args += ["--setenv", key, value]
    return args + ["--", *command]


@lru_cache(maxsize=2)
def _fetch_runtime(*, catalog=False):
    # Probe the fixed isolated system interpreter, not the application's
    # imported modules. The helper gets stdlib sources, no site-packages.
    probe = subprocess.run(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            ("import xml.etree.ElementTree; " if catalog else "")
            + "import http.client,ipaddress,json,resource,ssl,sys,sysconfig,"
            "urllib.parse; "
            "print(json.dumps({'stdlib':sysconfig.get_path('stdlib'),"
            "'extensions':[m.__file__ for m in sys.modules.values() "
            "if str(getattr(m,'__file__','')).endswith('.so')]}))",
        ],
        env=_ENV,
        cwd="/",
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    plan = json.loads(probe.stdout)
    stdlib = Path(plan["stdlib"]).resolve(strict=True)
    if not re.fullmatch(r"/usr/lib/python3\.\d+", str(stdlib)) or not stdlib.is_dir():
        raise RadioSandboxError("Ungültige Python-Laufzeit für den Radioabruf.")
    runtime = set(_runtime_files(PYTHON))
    for name in plan["extensions"]:
        extension = Path(name).resolve(strict=True)
        if not extension.is_relative_to(stdlib / "lib-dynload"):
            raise RadioSandboxError("Unerwartete Erweiterung für den Radioabruf.")
        runtime.update(_runtime_files(extension, allow_static_extension=True))
    return stdlib, tuple(sorted(runtime))


def _fetch_command(directory, audio_socket, stdlib, runtime_files):
    command = _sandbox_command(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/fetch.py",
        ],
        directory,
        runtime_files,
        audio_socket,
        local_file=None,
        network_source=True,
    )
    index = command.index("--")
    command[index:index] = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(FETCHER),
        "/run/fetch.py",
        "--ro-bind",
        str(directory / "request.json"),
        "/run/request.json",
    ]
    return _bounded_tmp(command, HELPER_TMPFS)


@lru_cache(maxsize=1)
def _pcm_runtime():
    probe = subprocess.run(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            "import socket,struct,resource,json,sys,sysconfig; "
            "print(json.dumps({'stdlib':sysconfig.get_path('stdlib'),"
            "'extensions':[m.__file__ for m in sys.modules.values() "
            "if str(getattr(m,'__file__','')).endswith('.so')]}))",
        ],
        env=_ENV,
        cwd="/",
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    plan = json.loads(probe.stdout)
    stdlib = Path(plan["stdlib"]).resolve(strict=True)
    if not re.fullmatch(r"/usr/lib/python3\.\d+", str(stdlib)) or not stdlib.is_dir():
        raise RadioSandboxError("Ungültige PCM-Python-Laufzeit.")
    runtime = set(_runtime_files(PYTHON))
    for name in plan["extensions"]:
        extension = Path(name).resolve(strict=True)
        if not extension.is_relative_to(stdlib / "lib-dynload"):
            raise RadioSandboxError("Unerwartete PCM-Laufzeitdatei.")
        runtime.update(_runtime_files(extension, allow_static_extension=True))
    return stdlib, tuple(sorted(runtime))


def _pcm_command(directory, stdlib, runtime):
    command = _sandbox_command(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/pcm.py",
        ],
        directory,
        runtime,
        None,
        local_file=None,
        catalog_parser=True,
    )
    binds = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(PCM),
        "/run/pcm.py",
        "--ro-bind",
        str(directory / "tap"),
        "/run/tap",
    ]
    command[command.index("--") : command.index("--")] = binds
    return command


def _catalog_command(directory, stdlib, runtime_files, kind):
    command = _sandbox_command(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/catalog.py",
            "--" + kind,
        ],
        directory,
        runtime_files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    index = command.index("--")
    command[index:index] = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(CATALOG),
        "/run/catalog.py",
    ]
    return _bounded_tmp(command, HELPER_TMPFS)


@lru_cache(maxsize=1)
def _zip_runtime():
    stdlib, base = _fetch_runtime(catalog=True)
    result = subprocess.run(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            "import zipfile,zlib,resource,json,sys;print(json.dumps([m.__file__ for m in sys.modules.values() if str(getattr(m,'__file__','')).endswith('.so')]))",
        ],
        env=_ENV,
        cwd="/",
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    runtime = set(base)
    for name in json.loads(result.stdout):
        path = Path(name).resolve(strict=True)
        if not path.is_relative_to(stdlib / "lib-dynload"):
            raise RadioSandboxError("Unerwartete ZIP-Laufzeitdatei.")
        runtime.update(_runtime_files(path, allow_static_extension=True))
    return stdlib, tuple(sorted(runtime))


def _zip_command(directory, stdlib, runtime):
    command = _sandbox_command(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/zip.py",
        ],
        directory,
        runtime,
        None,
        local_file=None,
        catalog_parser=True,
    )
    binds = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(PRESET_ZIP),
        "/run/zip.py",
        "--ro-bind",
        str(directory / "archive.zip"),
        "/media/archive.zip",
    ]
    for name in (
        "projectm_archive.py",
        "projectm_transport.py",
        "projectm_import_plan.py",
        "archive_limits.py",
    ):
        binds += [
            "--ro-bind",
            str(PRESET_ZIP.with_name(name)),
            "/run/netmon/core/" + name,
        ]
    command[command.index("--") : command.index("--")] = binds
    return _bounded_tmp(command, HELPER_TMPFS)


@contextmanager
def prepared_preset_bundle(path):
    """Snapshot only the selected file; the worker cannot access its original."""
    if not all(item.is_file() for item in (BWRAP, PYTHON, PRESET_ZIP)):
        raise RadioSandboxError("Geschützte ZIP-Verarbeitung fehlt.")
    stdlib, runtime = _zip_runtime()
    descriptor = os.open(
        path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    )
    with os.fdopen(descriptor, "rb") as original:
        info = os.fstat(original.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 <= info.st_size <= 256 * 1024 * 1024:
            raise RadioSandboxError("Ungültige oder zu große Archivdatei.")
        with tempfile.TemporaryDirectory(prefix="preset-zip-") as name:
            directory = Path(name)
            _prepare_directory(directory)
            snapshot = directory / "archive.zip"
            descriptor = os.open(snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as destination:
                copied = 0
                while True:
                    chunk = original.read(min(65536, 256 * 1024 * 1024 + 1 - copied))
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > 256 * 1024 * 1024:
                        raise RadioSandboxError(
                            "Archivkopie überschreitet das Bytebudget."
                        )
                    if destination.write(chunk) != len(chunk):
                        raise OSError("Unvollständige Archivkopie.")
            descriptor = os.open(
                directory / "members.bin", os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600
            )
            with os.fdopen(descriptor, "w+b") as output:
                process = subprocess.Popen(
                    _zip_command(directory, stdlib, runtime),
                    cwd="/",
                    env=_ENV,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
                try:
                    try:
                        process.wait(timeout=120)
                    except subprocess.TimeoutExpired as exc:
                        raise RadioSandboxError(
                            "ZIP-Verarbeitung hat ihr Zeitlimit erreicht."
                        ) from exc
                    if process.returncode != 0:
                        raise RadioSandboxError(
                            "Geschützte ZIP-Prüfung oder Entpackung fehlgeschlagen."
                        )
                    if (
                        os.fstat(output.fileno()).st_size
                        > 1024 * 1024 * 1024 + 32 * 1024 * 1024 + 9
                    ):
                        raise RadioSandboxError(
                            "ZIP-Helferantwort überschreitet das Bytebudget."
                        )
                    output.seek(0)
                    yield output, copied
                finally:
                    if process.poll() is None:
                        process.kill()
                    process.wait(timeout=3)


def _read_process_reply(process, timeout, limit):
    deadline = time.monotonic() + timeout
    output = bytearray()
    with selectors.DefaultSelector() as selected:
        selected.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RadioSandboxError("Radio-Abruf hat sein Zeitlimit erreicht.")
            if not selected.select(min(0.1, remaining)):
                continue
            chunk = os.read(
                process.stdout.fileno(), min(65536, limit + 1 - len(output))
            )
            if not chunk:
                break
            output.extend(chunk)
            if len(output) > limit:
                raise RadioSandboxError("Radio-Helferantwort ist zu groß.")
    process.wait(timeout=max(0.001, deadline - time.monotonic()))
    if process.returncode != 0:
        raise RadioSandboxError("Geschützter Radio-Abruf fehlgeschlagen.")
    return bytes(output)


def fetch_preset_archive(
    url, destination, *, timeout=30, total_timeout=300, limit=256 * 1024 * 1024
):
    """Stream bounded raw bytes from the fixed source; never parse ZIP here."""
    timeout, total_timeout = float(timeout), float(total_timeout)
    if (
        not isinstance(url, str)
        or not 0 < len(url) <= 8192
        or not 0 < timeout <= 300
        or not 0 < total_timeout <= 300
        or type(limit) is not int
        or not 0 < limit <= 256 * 1024 * 1024
    ):
        raise RadioSandboxError("Ungültige Preset-Downloadanfrage.")
    if not all(path.is_file() for path in (BWRAP, PYTHON, FETCHER)):
        raise RadioSandboxError("Geschützter Preset-Download ist nicht verfügbar.")
    stdlib, runtime = _fetch_runtime()
    with tempfile.TemporaryDirectory(prefix="preset-source-") as name:
        directory = Path(name)
        _prepare_directory(directory)
        request = directory / "request.json"
        request.write_text(
            json.dumps(
                {"url": url, "mode": "preset", "timeout": min(timeout, total_timeout)}
            )
        )
        request.chmod(0o600)
        process = subprocess.Popen(
            _fetch_command(directory, None, stdlib, runtime),
            cwd="/",
            env=_ENV,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        deadline = time.monotonic() + total_timeout
        idle_deadline = min(deadline, time.monotonic() + timeout)
        count = 0
        try:
            with selectors.DefaultSelector() as selected:
                selected.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = min(deadline, idle_deadline) - time.monotonic()
                    if remaining <= 0:
                        raise RadioSandboxError(
                            "Preset-Download hat sein Zeitlimit erreicht."
                        )
                    if not selected.select(min(0.1, remaining)):
                        continue
                    data = os.read(
                        process.stdout.fileno(), min(65536, limit + 1 - count)
                    )
                    if not data:
                        break
                    count += len(data)
                    if count > limit:
                        raise RadioSandboxError(
                            "Preset-Download überschreitet das Bytebudget."
                        )
                    pending = memoryview(data)
                    while pending:
                        written = destination.write(pending)
                        if written is None or not 0 < written <= len(pending):
                            raise OSError("Unvollständige Preset-Datei.")
                        pending = pending[written:]
                    idle_deadline = min(deadline, time.monotonic() + timeout)
            try:
                process.wait(
                    timeout=max(0.001, min(deadline, idle_deadline) - time.monotonic())
                )
            except subprocess.TimeoutExpired as exc:
                raise RadioSandboxError(
                    "Preset-Download hat sein Zeitlimit erreicht."
                ) from exc
            if process.returncode != 0:
                raise RadioSandboxError("Geschützter Preset-Download fehlgeschlagen.")
            return count
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=3)
            process.stdout.close()


def _read_json_reply(process, timeout, limit):
    output = _read_process_reply(process, timeout, limit)
    try:
        reply = json.loads(output)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise RadioSandboxError("Ungültige Radio-Helferantwort.") from exc
    return reply


@lru_cache(maxsize=1)
def _logo_runtime():
    stdlib, base = _fetch_runtime(catalog=True)
    if not (PILLOW / "__init__.py").is_file():
        raise RadioSandboxError("System-Pillow für geschützte Logos fehlt.")
    result = subprocess.run(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            "import sys,json; sys.path.insert(0,'/usr/lib/python3/dist-packages'); "
            "from PIL import Image,PngImagePlugin,JpegImagePlugin,GifImagePlugin,WebPImagePlugin,IcoImagePlugin; "
            "print(json.dumps([m.__file__ for m in sys.modules.values() "
            "if str(getattr(m,'__file__','')).endswith('.so')]))",
        ],
        env=_ENV,
        cwd="/",
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    runtime = set(base)
    for name in json.loads(result.stdout):
        extension = Path(name).resolve(strict=True)
        if not (
            extension.is_relative_to(PILLOW)
            or extension.is_relative_to(stdlib / "lib-dynload")
        ):
            raise RadioSandboxError("Unerwartete Logo-Laufzeitdatei.")
        runtime.update(_runtime_files(extension, allow_static_extension=True))
    return stdlib, tuple(sorted(runtime))


def _logo_command(directory, stdlib, runtime, *, fetch):
    command = _sandbox_command(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/logo.py",
            "--fetch" if fetch else "--decode",
        ],
        directory,
        runtime,
        None,
        local_file=None,
        network_source=fetch,
        catalog_parser=not fetch,
    )
    binds = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(LOGO),
        "/run/logo.py",
        "--ro-bind",
        str(ICON_HTTP),
        "/run/netmon/core/icon_http.py",
    ]
    if fetch:
        binds += ["--ro-bind", str(directory / "request.json"), "/run/request.json"]
        binds += [
            "--setenv",
            "SSL_CERT_FILE",
            "/etc/ssl/certs/ca-certificates.crt",
            "--setenv",
            "SSL_CERT_DIR",
            "/nonexistent",
        ]
    else:
        binds += [
            "--ro-bind",
            str(ICON_PAYLOAD),
            "/run/netmon/core/icon_payload.py",
            "--ro-bind",
            str(PILLOW),
            str(PILLOW),
        ]
    command[command.index("--") : command.index("--")] = binds
    return _bounded_tmp(command, HELPER_TMPFS)


@lru_cache(maxsize=1)
def _logo_policy():
    spec = importlib.util.spec_from_file_location("radio_logo_pixels", LOGO)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    return policy


def _run_logo(*, url=None, raw=None, timeout=8, work_root=None):
    radio_logo = _logo_policy()

    timeout = float(timeout)
    if not 0 < timeout <= 10:
        raise RadioSandboxError("Ungültiges Logo-Zeitlimit.")
    if url is not None:
        if not isinstance(url, str) or not 0 < len(url) <= 4096 or raw is not None:
            raise RadioSandboxError("Ungültige Logo-Adresse.")
    elif not isinstance(raw, bytes) or not 0 < len(raw) <= radio_logo.INPUT_BYTES:
        raise RadioSandboxError("Ungültige Logo-Daten.")
    if not all(
        path.is_file() for path in (BWRAP, PYTHON, LOGO, ICON_HTTP, ICON_PAYLOAD)
    ):
        raise RadioSandboxError("Geschützte Logo-Verarbeitung fehlt.")
    stdlib, runtime = _logo_runtime()
    with tempfile.TemporaryDirectory(prefix="logo-", dir=work_root) as name:
        directory = Path(name)
        _prepare_directory(directory)
        source = process = handle = None
        read_fd = write_fd = None
        deadline = time.monotonic() + timeout
        try:
            if url is not None:
                request = directory / "request.json"
                request.write_text(json.dumps({"url": url}))
                request.chmod(0o600)
                read_fd, write_fd = os.pipe()
                source_stdlib, source_runtime = _fetch_runtime()
                source = subprocess.Popen(
                    _logo_command(directory, source_stdlib, source_runtime, fetch=True),
                    cwd="/",
                    env=_ENV,
                    stdin=subprocess.DEVNULL,
                    stdout=write_fd,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                )
                input_stream = read_fd
            else:
                path = directory / "input"
                path.write_bytes(raw)
                path.chmod(0o600)
                handle = path.open("rb")
                input_stream = handle
            process = subprocess.Popen(
                _logo_command(directory, stdlib, runtime, fetch=False),
                cwd="/",
                env=_ENV,
                stdin=input_stream,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            for descriptor in (read_fd, write_fd):
                if descriptor is not None:
                    os.close(descriptor)
            read_fd = write_fd = None
            reply = _read_process_reply(
                process,
                max(0.001, deadline - time.monotonic()),
                radio_logo.MAX_REPLY_BYTES,
            )
            if source is not None:
                source.wait(timeout=max(0.001, deadline - time.monotonic()))
                if source.returncode != 0:
                    raise RadioSandboxError("Geschützter Logoabruf fehlgeschlagen.")
            radio_logo.validate_pixels(reply)
            return reply
        finally:
            for child in (source, process):
                if child is not None and child.poll() is None:
                    child.kill()
                    child.wait(timeout=3)
            if process is not None:
                process.stdout.close()
            if handle is not None:
                handle.close()
            for descriptor in (read_fd, write_fd):
                if descriptor is not None:
                    os.close(descriptor)


def fetch_logo(url, *, timeout=8, work_root=None):
    return _run_logo(url=url, timeout=timeout, work_root=work_root)


def decode_logo(raw, *, timeout=8, work_root=None):
    return _run_logo(raw=raw, timeout=timeout, work_root=work_root)


def _read_title_reply(process, timeout):
    reply = _read_json_reply(process, timeout, 8192)
    if (
        not isinstance(reply, dict)
        or set(reply) != {"title"}
        or not isinstance(reply["title"], str)
        or len(reply["title"]) > 512
        or any(not char.isprintable() for char in reply["title"])
    ):
        raise RadioSandboxError("Ungültige Radio-Metadatenantwort.")
    return reply["title"]


@lru_cache(maxsize=1)
def _catalog_policy():
    spec = importlib.util.spec_from_file_location("radio_catalog_schema", CATALOG)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    return policy


def fetch_catalog(url, *, kind="json", post=False, timeout=30, work_root=None):
    """Fetch and parse remotely supplied catalogs in the restricted source."""
    if (
        not isinstance(url, str)
        or not 0 < len(url) <= 8192
        or kind not in {"json", "xml"}
    ):
        raise RadioSandboxError("Ungültige Kataloganfrage.")
    timeout = float(timeout)
    if not 0 < timeout <= 30 or type(post) is not bool or (post and kind != "json"):
        raise RadioSandboxError("Ungültige Kataloganfrage.")
    if not all(path.is_file() for path in (BWRAP, PYTHON, FETCHER, CATALOG)):
        raise RadioSandboxError("Geschützter Katalogabruf ist nicht verfügbar.")
    radio_catalog = _catalog_policy()
    stdlib, runtime = _fetch_runtime()
    parser_stdlib, parser_runtime = _fetch_runtime(catalog=True)
    with tempfile.TemporaryDirectory(prefix="catalog-", dir=work_root) as name:
        directory = Path(name)
        _prepare_directory(directory)
        request = directory / "request.json"
        mode = "catalog-post" if post else "catalog-" + kind
        request.write_text(json.dumps({"url": url, "mode": mode}))
        request.chmod(0o600)
        source = process = None
        read_fd, write_fd = os.pipe()
        deadline = time.monotonic() + timeout
        try:
            source = subprocess.Popen(
                _fetch_command(directory, None, stdlib, runtime),
                cwd="/",
                env=_ENV,
                stdin=subprocess.DEVNULL,
                stdout=write_fd,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            process = subprocess.Popen(
                _catalog_command(directory, parser_stdlib, parser_runtime, kind),
                cwd="/",
                env=_ENV,
                stdin=read_fd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            os.close(read_fd)
            os.close(write_fd)
            read_fd = write_fd = None
            reply = _read_json_reply(
                process,
                max(0.001, deadline - time.monotonic()),
                radio_catalog.MAX_REPLY_BYTES,
            )
            source.wait(timeout=max(0.001, deadline - time.monotonic()))
            if source.returncode != 0:
                raise RadioSandboxError("Geschützter Katalogabruf fehlgeschlagen.")
            if not isinstance(reply, dict) or set(reply) != {"rows"}:
                raise RadioSandboxError("Ungültige Katalogantwort.")
            return radio_catalog.validate_rows(reply["rows"])
        finally:
            for child in (source, process):
                if child is not None and child.poll() is None:
                    child.kill()
                    child.wait(timeout=3)
            if process is not None:
                process.stdout.close()
            for descriptor in (read_fd, write_fd):
                if descriptor is not None:
                    os.close(descriptor)


def probe_reachability(url, *, station=False, ranged=False, timeout=4, work_root=None):
    """Return bool/None from the restricted HTTP source; never open a URL here."""
    if (
        not isinstance(url, str)
        or not 0 < len(url) <= 8192
        or type(station) is not bool
        or type(ranged) is not bool
        or (ranged and not station)
    ):
        raise RadioSandboxError("Ungültige Radio-Erreichbarkeitsanfrage.")
    timeout = float(timeout)
    if not 0 < timeout <= 10:
        raise RadioSandboxError("Ungültiges Zeitlimit für Radio-Erreichbarkeit.")
    if not all(path.is_file() for path in (BWRAP, PYTHON, FETCHER)):
        raise RadioSandboxError("Geschützte Radio-Erreichbarkeitsprüfung fehlt.")
    stdlib, runtime = _fetch_runtime()
    with tempfile.TemporaryDirectory(prefix="probe-", dir=work_root) as name:
        directory = Path(name)
        _prepare_directory(directory)
        mode = (
            "probe-station-range"
            if ranged
            else "probe-station" if station else "probe-source"
        )
        request = directory / "request.json"
        request.write_text(json.dumps({"url": url, "mode": mode}))
        request.chmod(0o600)
        process = subprocess.Popen(
            _fetch_command(directory, None, stdlib, runtime),
            env=_ENV,
            cwd="/",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        try:
            reply = _read_json_reply(process, timeout, 512)
            if (
                not isinstance(reply, dict)
                or set(reply) != {"reachable"}
                or (
                    reply["reachable"] is not None
                    and type(reply["reachable"]) is not bool
                )
            ):
                raise RadioSandboxError("Ungültige Radio-Erreichbarkeitsantwort.")
            return reply["reachable"]
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            process.stdout.close()


def fetch_icy_title(url, *, timeout=4, work_root=None):
    """Return bounded text from a separate source process; no direct fallback."""
    if not isinstance(url, str) or not 0 < len(url) <= 8192:
        raise RadioSandboxError("Ungültige Adresse für Radio-Metadaten.")
    timeout = float(timeout)
    if not 0 < timeout <= 10:
        raise RadioSandboxError("Ungültiges Zeitlimit für Radio-Metadaten.")
    if not all(path.is_file() for path in (BWRAP, PYTHON, FETCHER)):
        raise RadioSandboxError("Geschützter Radio-Metadatenabruf ist nicht verfügbar.")
    stdlib, runtime = _fetch_runtime()
    with tempfile.TemporaryDirectory(prefix="icy-", dir=work_root) as name:
        directory = Path(name)
        _prepare_directory(directory)
        request = directory / "request.json"
        request.write_text(json.dumps({"url": str(url), "mode": "icy"}))
        request.chmod(0o600)
        process = subprocess.Popen(
            _fetch_command(directory, None, stdlib, runtime),
            env=_ENV,
            cwd="/",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        try:
            return _read_title_reply(process, timeout)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
            process.stdout.close()


class _PcmOutputBudget:
    RATE = 192_000  # 48000 Hz * stereo * 16-bit PCM
    BURST = 38_400  # at most 200 ms, including after an idle period

    def __init__(self, now):
        self.updated = now
        self.credit = float(self.BURST)

    def available(self, now):
        self.credit = min(
            self.BURST, self.credit + max(0, now - self.updated) * self.RATE
        )
        self.updated = now
        return int(self.credit)

    def spend(self, count, completed):
        if not 0 < count <= int(self.credit):
            raise ValueError("Invalid PCM output debit.")
        self.credit -= count
        # A delayed write buys no additional catch-up credit.
        self.updated = completed


class _PcmOutputGate:
    """Trusted pipe -> FIFO writer; never runs Tk or manages child processes.

    Own duplicated FDs, at most one pending block, no accumulating trace/log.
    Children get only the pipe's write end, never the FIFO or its pathname.
    Only the playback owner joins this worker; requesting stop never waits.
    """

    BLOCK = 4096
    WAIT = 0.05

    def __init__(self, source, target):
        self._stop = threading.Event()
        self.done = threading.Event()
        self.error = None
        with ExitStack() as descriptors:
            self._source = os.dup(source)
            descriptors.callback(os.close, self._source)
            self._target = os.dup(target)
            descriptors.callback(os.close, self._target)
            # Match the daemon playback owner's interpreter lifetime. Normal
            # cleanup still joins us before releasing the FIFO writer lock.
            self._thread = threading.Thread(
                target=self._run, name="netmon-radio-output", daemon=True
            )
            self._thread.start()
            descriptors.pop_all()

    def request_stop(self):
        self._stop.set()

    def close(self):
        self.request_stop()
        self._thread.join()

    def _run(self):
        pending = b""
        budget = _PcmOutputBudget(time.monotonic())
        try:
            os.set_blocking(self._source, False)
            os.set_blocking(self._target, False)
            with selectors.DefaultSelector() as source_ready:
                source_ready.register(self._source, selectors.EVENT_READ)
                with selectors.DefaultSelector() as target_ready:
                    target_ready.register(self._target, selectors.EVENT_WRITE)
                    while not self._stop.is_set():
                        if not pending:
                            if not source_ready.select(self.WAIT):
                                continue
                            try:
                                pending = os.read(self._source, self.BLOCK)
                            except BlockingIOError:
                                continue
                            if not pending:
                                return
                        available = budget.available(time.monotonic())
                        if available < len(pending):
                            self._stop.wait(
                                min(
                                    self.WAIT,
                                    (len(pending) - budget.credit) / budget.RATE,
                                )
                            )
                            continue
                        try:
                            written = os.write(self._target, pending)
                        except BlockingIOError:
                            target_ready.select(self.WAIT)
                            continue
                        if written <= 0:
                            raise OSError("PCM output made no progress.")
                        budget.spend(written, time.monotonic())
                        pending = pending[written:]
        except Exception as exc:
            self.error = exc
        finally:
            try:
                os.close(self._source)
            finally:
                try:
                    os.close(self._target)
                finally:
                    self.done.set()


class FifoOutput:
    """Trusted owner of the FIFO writer and its two PipeWire links.

    silence() unlinks first on every stop (F4); the relay is then terminated,
    never drained (F6). lost() is a rate-limited watchdog for the owner
    thread; it never runs on the Tk thread.
    """

    VERIFY_INTERVAL = 2.0

    def __init__(self, writer, linked, run=None):
        self._writer = writer
        self._linked = linked
        self._run = run
        self._lock = threading.RLock()
        self._silenced = False
        self._closed = False
        self._lost = False
        self._next_check = time.monotonic() + self.VERIFY_INTERVAL

    @property
    def descriptor(self):
        return self._writer.fd

    def handed_over(self):
        self._writer.close_descriptor()

    def silence(self):
        with self._lock:
            if self._silenced:
                return
            self._silenced = True
        fifo_output.unlink(self._linked, self._run)

    def lost(self):
        with self._lock:
            if self._lost or self._silenced:
                return self._lost
            now = time.monotonic()
            if now < self._next_check:
                return False
            self._next_check = now + self.VERIFY_INTERVAL
        if not fifo_output.verify(self._linked, self._run):
            with self._lock:
                self._lost = True
        return self._lost

    def close(self):
        self.silence()
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._writer.close()


def _open_output():
    """Readiness, exclusive FIFO writer, then links; any failure fails closed."""
    paths = fifo_output.paths()
    status = fifo_output.setup_status(paths)
    if not status["ready"]:
        raise RadioSandboxError(
            "Geschützte Radioausgabe nicht bereit: " + "; ".join(status["reasons"])
        )
    writer = fifo_output.FifoWriter(paths)
    try:
        writer.open()
        linked = fifo_output.link(paths.fifo)
    except fifo_output.RadioOutputError as exc:
        writer.close()
        raise RadioSandboxError(str(exc)) from exc
    except Exception:
        writer.close()
        raise
    return FifoOutput(writer, linked)


def _prepare_directory(directory: Path) -> None:
    (directory / "control").mkdir(mode=0o700)
    (directory / "pulse.conf").write_text("autospawn = no\nenable-shm = no\n")
    (directory / "nsswitch.conf").write_text("hosts: files dns\n")
    (directory / "passwd").write_text(
        f"radio:x:{os.getuid()}:{os.getgid()}:Radio:/home/radio:/nonexistent\n"
    )
    (directory / "group").write_text(f"radio:x:{os.getgid()}:\n")


class SandboxProcess:
    """Popen-like owner of the wrapper and its one private IPC directory."""

    OUTPUT_DRAIN = 0.6  # paced lead + FIFO buffer at a natural EOF

    def __init__(
        self,
        process,
        temporary,
        output=None,
        source_process=None,
        pcm_process=None,
        output_gate=None,
    ):
        self._process = process
        self._output = output
        self._source_process = source_process
        self._pcm_process = pcm_process
        self._output_gate = output_gate
        self._pcm_tap = None
        self._pcm_closed = False
        self._source_stopped = False
        self._drain_deadline = None
        self._output_drain = None
        self._gate_drain_deadline = None
        self._result = None
        self._temporary = temporary
        self._cleanup_lock = threading.RLock()
        self.ipc_path = str(Path(temporary.name) / "control/mpv.sock")
        self.output_lost = False
        # Launch/IPC readiness is not an independent verification of protection.
        self.sandbox_state = "started"
        self.runtime_verified = False

    @property
    def pid(self):
        return self._process.pid

    def _kill(self, *children):
        for child in children:
            if child is not None and child.poll() is None:
                child.kill()
                child.wait(timeout=3)

    def poll(self):
        if self._result is not None:
            return self._result
        result = self._process.poll()
        pcm_result = self._pcm_process.poll() if self._pcm_process is not None else None
        if self._pcm_process is not None and pcm_result is not None and result is None:
            # Relay end (including EPIPE from a lost FIFO reader) ends decoding.
            self._kill(self._process)
            result = pcm_result or 1
        if self._source_process is not None and not self._source_stopped:
            source_result = self._source_process.poll()
            if source_result is not None and source_result != 0:
                # Fetch errors must not become a successful media EOF.
                self._kill(self._process, self._pcm_process)
                result = source_result
            elif result is not None and source_result is None:
                self._source_stopped = True
                self._source_process.kill()
                self._source_process.wait(timeout=3)
        gate_failed = (
            self._output_gate is not None
            and self._output_gate.done.is_set()
            and self._output_gate.error is not None
        )
        if gate_failed or (
            result is None and self._output is not None and self._output.lost()
        ):
            # Watchdog: tunnel generation or links changed. Never relink to
            # another target silently; stop with a visible error instead.
            self.output_lost = True
            self._silence()
            self._kill(self._process, self._pcm_process, self._source_process)
            self._source_stopped = True
            result = 1
        if result is not None and self._pcm_process is not None:
            pcm_result = self._pcm_process.poll()
            if pcm_result is None:
                if self._drain_deadline is None:
                    self._drain_deadline = time.monotonic() + 5
                if time.monotonic() < self._drain_deadline:
                    return None
                self._kill(self._pcm_process)
                result = result or 1
            elif result == 0 and pcm_result:
                result = pcm_result
        if result is not None and self._output_gate is not None:
            if result != 0:
                self._silence()
            elif not self._output_gate.done.is_set():
                if self._gate_drain_deadline is None:
                    self._gate_drain_deadline = time.monotonic() + 5
                if time.monotonic() < self._gate_drain_deadline:
                    return None
                self.output_lost = True
                self._silence()
                result = 1
        if result == 0 and self._output is not None:
            # Natural EOF: let the paced lead and FIFO buffer play out, then
            # unlink. Stops and failures unlink immediately instead.
            if self._output_drain is None:
                self._output_drain = time.monotonic() + self.OUTPUT_DRAIN
            if time.monotonic() < self._output_drain:
                return None
        if result is not None:
            if self._source_process is not None and self._source_process.poll() is None:
                self._source_stopped = True
                self._source_process.kill()
                self._source_process.wait(timeout=3)
            self._result = result
            self._cleanup()
        return result

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            result = self.poll()
            if result is not None:
                return result
            if deadline is not None and time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(str(MPV), timeout)
            time.sleep(0.03)

    def _cleanup(self):
        # Owner thread only. Never join under the playback/PCM state lock.
        try:
            if self._output_gate is not None:
                self._output_gate.close()
        finally:
            self._cleanup_output()

    def _cleanup_output(self):
        with self._cleanup_lock:
            self._pcm_closed = True
            if self._pcm_tap is not None:
                self._pcm_tap.close()
            try:
                if self._output is not None:
                    self._output.close()
            finally:
                self._temporary.cleanup()

    def open_pcm_tap(self):
        """One trusted consumer of fixed PCM, never a host capture connection."""
        from netmon.core.radio_pcm import PcmTap

        with self._cleanup_lock:
            if (
                self._pcm_process is None
                or self._pcm_closed
                or self._result is not None
            ):
                raise RadioSandboxError("Kein laufender geschützter PCM-Ausgang.")
            if self._pcm_tap is not None and not self._pcm_tap.closed:
                raise RadioSandboxError("PCM-Ausgang ist bereits verbunden.")
            self._pcm_tap = PcmTap(Path(self._temporary.name) / "tap/pcm.sock")
            return self._pcm_tap

    def _silence(self):
        # F4: silence first. A failing unlink must not prevent the stop.
        if self._output is not None:
            try:
                self._output.silence()
            except Exception:
                pass
        if self._output_gate is not None:
            self._output_gate.request_stop()

    def terminate(self):
        self._silence()
        self._process.terminate()
        if self._pcm_process is not None:
            self._pcm_process.terminate()
        if self._source_process is not None:
            self._source_stopped = True
            self._source_process.terminate()

    def kill(self):
        self._silence()
        self._process.kill()
        if self._pcm_process is not None:
            self._pcm_process.kill()
        if self._source_process is not None:
            self._source_stopped = True
            self._source_process.kill()


def connect_mpv(ipc_path, *, timeout):
    """Connect to the pinned socket inode, never to a decoder-supplied link.

    Linux O_PATH/procfs is intentional. Descriptor failure has no pathname
    fallback. Peer credentials restrict the UID; they do not authenticate an
    executable or make a compromised decoder trustworthy.
    """
    path = Path(ipc_path)
    directory_fd = socket_fd = None
    client = None
    try:
        directory_fd = os.open(
            path.parent, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        )
        directory = os.fstat(directory_fd)
        if directory.st_uid != os.getuid() or stat.S_IMODE(directory.st_mode) != 0o700:
            raise RadioSandboxError("Privates Radio-Steuerverzeichnis ist unzulässig.")
        socket_fd = os.open(
            path.name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory_fd
        )
        info = os.fstat(socket_fd)
        if (
            not stat.S_ISSOCK(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
        ):
            raise RadioSandboxError("Privater Radio-Steuersocket ist unzulässig.")
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(timeout)
        client.connect(f"/proc/self/fd/{socket_fd}")
        credentials = client.getsockopt(
            socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
        )
        peer_pid, peer_uid, _peer_gid = struct.unpack("3i", credentials)
        if peer_pid <= 0 or peer_uid != os.getuid():
            raise RadioSandboxError(
                "Gegenstelle des Radio-Steuerkanals ist unzulässig."
            )
        # Also reject a visible link change during connect, before any JSON.
        # Link count is not origin authentication or an atomic host-race guard.
        if os.fstat(socket_fd).st_nlink != 1:
            raise RadioSandboxError("Linkzahl des Radio-Steuersockets ist unzulässig.")
        return client
    except Exception:
        if client is not None:
            client.close()
        raise
    finally:
        for descriptor in (socket_fd, directory_fd):
            if descriptor is not None:
                os.close(descriptor)


def _wait_for_ipc(process: SandboxProcess, timeout=5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RadioSandboxError("mpv-Sandbox wurde beim Start beendet.")
        try:
            with connect_mpv(
                process.ipc_path,
                timeout=min(0.2, max(0.01, deadline - time.monotonic())),
            ) as client:
                client.sendall(
                    b'{"command":["get_property","mpv-version"],"request_id":17}\n'
                )
                data = b""
                received = 0
                while received < 8192 and time.monotonic() < deadline:
                    chunk = client.recv(min(1024, 8192 - received))
                    if not chunk:
                        break
                    data += chunk
                    received += len(chunk)
                    while b"\n" in data:
                        line, data = data.split(b"\n", 1)
                        reply = json.loads(line)
                        if (
                            isinstance(reply, dict)
                            and reply.get("request_id") == 17
                            and reply.get("error") == "success"
                            and isinstance(reply.get("data"), str)
                            and reply["data"]
                        ):
                            return
        except (OSError, ValueError):
            pass
        time.sleep(0.03)
    raise RadioSandboxError("mpv-Sandbox meldet keinen bereiten Steuerkanal.")


def _quota_env() -> dict:
    """Own user manager only: derived from the UID, never from inherited env."""
    runtime = f"/run/user/{os.getuid()}"
    return {
        **_ENV,
        "XDG_RUNTIME_DIR": runtime,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime}/bus",
    }


def _require_quota_manager() -> None:
    """D-Q1: without the user manager there are no limits, so no playback."""
    bus = Path(f"/run/user/{os.getuid()}/bus")
    try:
        info = bus.lstat()
    except OSError:
        info = None
    if info is None or not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
        raise RadioSandboxError(
            "Radio gestoppt: Ressourcengrenzen nicht verfügbar "
            "(Benutzer-Dienstmanager nicht erreichbar)."
        )


def _bounded_tmp(command: list[str], size: int) -> list[str]:
    """Bound the capsule's only tmpfs (/tmp); keep the smaller of two bounds."""
    if not command or command[0] != str(BWRAP) or command.count("--tmpfs") != 1:
        raise RadioSandboxError("Ungültiger Kapselplan für Ressourcengrenzen.")
    capsule = list(command)
    at = capsule.index("--tmpfs")
    if capsule[at + 1] != "/tmp":
        raise RadioSandboxError("Ungültiger Kapselplan für Ressourcengrenzen.")
    if at >= 2 and capsule[at - 2] == "--size":
        capsule[at - 1] = str(min(int(capsule[at - 1]), size))
    else:
        capsule[at:at] = ["--size", str(size)]
    return capsule


def _limited(command: list[str], profile: str) -> list[str]:
    """systemd-run --user --scope -> prlimit -> bwrap; the PID stays bwrap.

    If the user manager is unreachable, systemd-run exits before running
    anything (fail-closed). The capsule environment stays --clearenv.
    """
    quota = QUOTAS[profile]
    capsule = _bounded_tmp(command, quota["tmpfs"])
    unit = f"netmon-radio-{profile}-{os.getpid()}-{next(_SCOPES)}"
    nofile, fsize = quota["nofile"], quota["fsize"]
    return [
        str(SYSTEMD_RUN),
        "--user",
        "--scope",
        "--quiet",
        "--collect",
        f"--unit={unit}",
        "-p",
        f"MemoryMax={quota['memory']}",
        "-p",
        "MemorySwapMax=0",
        "-p",
        f"TasksMax={quota['tasks']}",
        "-p",
        f"CPUQuota={quota['cpu']}%",
        "--",
        str(PRLIMIT),
        f"--nofile={nofile}:{nofile}",
        f"--fsize={fsize}:{fsize}",
        "--core=0:0",
        "--",
        *capsule,
    ]


def start_playback(command, *, ipc_root, local_file=None) -> SandboxProcess:
    """Start only protected mpv; return after a bounded IPC handshake.

    The command is built by the controller, never accepted from a radio source.
    For local playback the only media file is remapped and networking unshared.
    """
    if not available():
        raise RadioSandboxError(
            "Geschützte Wiedergabe benötigt mpv, PipeWire-Werkzeuge, "
            "systemd-run, prlimit und Bubblewrap."
        )
    command = list(command)
    if (
        not command
        or command[0] != "mpv"
        or command[-2:-1] != ["--"]
        or f"--input-ipc-server={IPC_PATH}" not in command[:-2]
    ):
        raise RadioSandboxError("Ungültiger mpv-Startplan.")
    media = None
    source_url = None
    if local_file is not None:
        media = Path(local_file).resolve(strict=True)
        if not stat.S_ISREG(media.stat().st_mode):
            raise RadioSandboxError(
                "Die gewählte Mediendatei ist keine reguläre Datei."
            )
        command[-1] = "/media/selected"
    else:
        if not isinstance(command[-1], str) or not 0 < len(command[-1]) <= 8192:
            raise RadioSandboxError("Ungültige Streamadresse.")
        try:
            parsed = urlsplit(command[-1])
        except ValueError as exc:
            raise RadioSandboxError("Ungültige Streamadresse.") from exc
        if parsed.scheme not in {"http", "https"}:
            raise RadioSandboxError(
                "Geschützte Wiedergabe unterstützt zunächst nur HTTP(S)-Direktstreams."
            )
        if parsed.path.lower().endswith((".m3u", ".m3u8", ".pls", ".mpd")):
            raise RadioSandboxError(
                "Entfernte Playlists und HLS werden noch nicht geschützt unterstützt."
            )
        source_url = command[-1]
        command[-1] = "fd://0"
        command.insert(-2, "--access-references=no")
    _require_quota_manager()
    command[0] = str(MPV)
    runtime_files = _runtime_files(MPV)
    pcm_stdlib, pcm_runtime = _pcm_runtime()
    fetch_runtime = _fetch_runtime() if source_url is not None else None
    temporary = tempfile.TemporaryDirectory(prefix="play-", dir=ipc_root)
    process = None
    output = None
    gate = None
    pcm = raw = None
    source = None
    source_read = source_write = None
    decode_read = decode_write = None
    gate_read = gate_write = None
    try:
        directory = Path(temporary.name)
        if len(os.fsencode(directory / "control/mpv.sock")) > 100:
            raise RadioSandboxError("Privater Radio-Steuerpfad ist zu lang.")
        _prepare_directory(directory)
        (directory / "tap").mkdir(mode=0o700)
        # Linked before the relay writes; no output means no start (D1).
        output = _open_output()
        decode_read, decode_write = os.pipe()
        gate_read, gate_write = os.pipe()
        gate = _PcmOutputGate(gate_read, output.descriptor)
        if source_url is not None:
            request = directory / "request.json"
            request.write_text(json.dumps({"url": source_url}))
            request.chmod(0o600)
            source_read, source_write = os.pipe()
            stdlib, source_runtime = fetch_runtime
            source = subprocess.Popen(
                _limited(
                    _fetch_command(directory, None, stdlib, source_runtime), "fetch"
                ),
                cwd="/",
                env=_quota_env(),
                stdin=subprocess.DEVNULL,
                stdout=source_write,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        args = _sandbox_command(
            command, directory, runtime_files, None, local_file=media
        )
        pcm = subprocess.Popen(
            _limited(_pcm_command(directory, pcm_stdlib, pcm_runtime), "relay"),
            cwd="/",
            env=_quota_env(),
            stdin=decode_read,
            stdout=gate_write,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        output.handed_over()
        raw = subprocess.Popen(
            _limited(args, "decoder"),
            cwd="/",
            env=_quota_env(),
            stdin=source_read if source_read is not None else subprocess.DEVNULL,
            stdout=decode_write,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        for descriptor in (
            decode_read,
            decode_write,
            source_read,
            source_write,
            gate_read,
            gate_write,
        ):
            if descriptor is not None:
                os.close(descriptor)
        decode_read = decode_write = source_read = source_write = None
        gate_read = gate_write = None
        process = SandboxProcess(raw, temporary, output, source, pcm, gate)
        _wait_for_ipc(process)
        return process
    except Exception:
        if process is not None:
            process.kill()
            process.wait(timeout=3)
        else:
            if output is not None:
                try:
                    output.silence()
                except Exception:
                    pass
            for child in (raw, pcm, source):
                if child is not None and child.poll() is None:
                    child.kill()
                    child.wait(timeout=3)
            if gate is not None:
                gate.close()
            if output is not None:
                output.close()
        temporary.cleanup()
        raise
    finally:
        for descriptor in (
            decode_read,
            decode_write,
            source_read,
            source_write,
            gate_read,
            gate_write,
        ):
            if descriptor is not None:
                os.close(descriptor)
