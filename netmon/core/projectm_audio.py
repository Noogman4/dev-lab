"""Private Pulse-compatible PCM source for a future protected projectM frontend.

No host audio socket, devices, D-Bus, renderer, or system service is started.
The optional adapter owns its own PipeWire/WirePlumber processes and takes
only the current NetMon playback's bounded PCM tap.
"""

from functools import lru_cache
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import selectors
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time

WORKER = Path(__file__).resolve()
SOURCE = "netmon_pcm"
RUNTIME = "/run/private-audio"
SOCKET = RUNTIME + "/pulse/native"
CONFIG = "/etc/netmon-audio"
FIFO = "/tmp/netmon.pcm"
TOOLS = tuple(
    Path("/usr/bin") / name
    for name in ("pipewire", "pipewire-pulse", "wireplumber", "pactl")
)
PW_MODULES = (
    "protocol-native",
    "metadata",
    "spa-node-factory",
    "client-node",
    "client-device",
    "access",
    "adapter",
    "link-factory",
    "session-manager",
    "protocol-pulse",
    "pipe-tunnel",
)
WP_MODULES = (
    "lua-scripting",
    "metadata",
    "si-node",
    "si-audio-adapter",
    "si-standard-link",
    "si-audio-endpoint",
    "default-nodes-api",
    "default-nodes",
    "mixer-api",
)
WP_SCRIPTS = ("create-item.lua", "policy-node.lua", "access/access-default.lua")


def _spa():
    return """
context.spa-libs = {
    audio.convert.* = audioconvert/libspa-audioconvert
    support.* = support/libspa-support
}
"""


def _modules(names):
    return (
        "context.modules = [\n"
        + "".join(" { name = libpipewire-module-" + name + " }\n" for name in names)
        + "]\n"
    )


def configurations():
    core = (
        "context.properties = { core.daemon = true core.name = pipewire-0 support.dbus = false }\n"
        + _spa()
        + _modules(PW_MODULES[:9])
        + """
context.objects = [
 { factory = spa-node-factory args = {
   factory.name = support.node.driver node.name = Private-Driver
   node.group = pipewire.dummy priority.driver = 20000
 } }
]
"""
    )
    pulse = (
        "context.properties = { support.dbus = false }\n"
        + _spa()
        + _modules(
            ("protocol-native", "client-node", "adapter", "metadata", "protocol-pulse")
        )
        + 'pulse.properties = { server.address = [ "unix:'
        + SOCKET
        + '" ] }\n'
        + 'pulse.cmd = [ { cmd = "load-module" args = "module-pipe-source '
        + f"file={FIFO} source_name={SOURCE} format=s16{'le' if sys.byteorder == 'little' else 'be'} "
        'rate=48000 channels=2 channel_map=front-left,front-right" } ]\n'
    )
    wp = (
        "context.properties = { support.dbus = false wireplumber.export-core = false }\n"
        + _spa()
        + _modules(
            ("protocol-native", "client-node", "adapter", "metadata", "session-manager")
        )
        + "wireplumber.components = [\n"
        + "".join(
            " { name = libwireplumber-module-" + name + ", type = module }\n"
            for name in WP_MODULES
        )
        + "".join(
            " { name = " + name + ", type = script/lua }\n" for name in WP_SCRIPTS
        )
        + "]\n"
    )
    return {"pipewire.conf": core, "pipewire-pulse.conf": pulse, "wireplumber.conf": wp}


def available():
    from netmon.core import radio_sandbox as sandbox

    return all(p.is_file() for p in (*TOOLS, WORKER, sandbox.BWRAP, sandbox.PYTHON))


@lru_cache(maxsize=1)
def _runtime():
    from netmon.core import radio_sandbox as sandbox

    plan = subprocess.run(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            "import subprocess,selectors,socket,struct,resource,json,sys,sysconfig; "
            "print(json.dumps({'stdlib':sysconfig.get_path('stdlib'),'arch':sysconfig.get_config_var('MULTIARCH'),"
            "'extensions':[m.__file__ for m in sys.modules.values() if str(getattr(m,'__file__','')).endswith('.so')]}))",
        ],
        cwd="/",
        env=sandbox._ENV,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    plan = json.loads(plan.stdout)
    stdlib = Path(plan["stdlib"]).resolve(strict=True)
    arch = plan["arch"]
    if not re.fullmatch(r"/usr/lib/python3\.\d+", str(stdlib)) or not re.fullmatch(
        r"[a-zA-Z0-9_-]+", arch or ""
    ):
        raise sandbox.RadioSandboxError("Ungültige private Audio-Laufzeit.")
    files = set(sandbox._runtime_files(sandbox.PYTHON))
    for name in plan["extensions"]:
        path = Path(name).resolve(strict=True)
        if not path.is_relative_to(stdlib / "lib-dynload"):
            raise sandbox.RadioSandboxError("Unerwartete private Audio-Erweiterung.")
        files.update(sandbox._runtime_files(path, allow_static_extension=True))
    wp_runtime = set(sandbox._runtime_files(TOOLS[2]))
    if not any(p.name.startswith("libwireplumber-0.4.so") for p in wp_runtime):
        raise sandbox.RadioSandboxError(
            "Privates Audioprofil benötigt WirePlumber 0.4."
        )
    files.update(wp_runtime)
    libraries = Path("/usr/lib") / arch
    modules = [
        libraries / "pipewire-0.3" / f"libpipewire-module-{n}.so" for n in PW_MODULES
    ]
    modules += [
        libraries / "wireplumber-0.4" / f"libwireplumber-module-{n}.so"
        for n in WP_MODULES
    ]
    modules += [
        libraries / "spa-0.2" / p
        for p in ("support/libspa-support.so", "audioconvert/libspa-audioconvert.so")
    ]
    for path in (*TOOLS, *modules):
        if not path.is_file():
            raise sandbox.RadioSandboxError("Unvollständige private Audio-Laufzeit.")
        files.update(sandbox._runtime_files(path, allow_static_extension=True))
    scripts = [Path("/usr/share/wireplumber/scripts") / p for p in WP_SCRIPTS]
    if any(not path.is_file() for path in scripts):
        raise sandbox.RadioSandboxError("Private Audio-Policy fehlt.")
    return stdlib, tuple(sorted(files)), tuple(scripts)


def _command(directory, stdlib, files, scripts):
    from netmon.core import radio_sandbox as sandbox

    command = sandbox._sandbox_command(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/audio-worker.py",
        ],
        directory,
        files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    extra = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(WORKER),
        "/run/audio-worker.py",
        "--ro-bind",
        str(directory / "config"),
        CONFIG,
        "--bind",
        str(directory / "runtime"),
        RUNTIME,
    ]
    for path in scripts:
        extra += ["--ro-bind", str(path), str(path)]
    environment = {
        "XDG_RUNTIME_DIR": RUNTIME,
        "XDG_CONFIG_HOME": "/tmp/config",
        "XDG_CACHE_HOME": "/tmp/cache",
        "XDG_STATE_HOME": "/tmp/state",
        "PIPEWIRE_RUNTIME_DIR": RUNTIME,
        "PIPEWIRE_REMOTE": "pipewire-0",
        "PIPEWIRE_CONFIG_DIR": CONFIG,
        "WIREPLUMBER_CONFIG_DIR": CONFIG,
        "WIREPLUMBER_DATA_DIR": "/usr/share/wireplumber",
        "PULSE_SERVER": "unix:" + SOCKET,
        "PULSE_CLIENTCONFIG": CONFIG + "/pulse-client.conf",
    }
    for key, value in environment.items():
        extra += ["--setenv", key, value]
    command[command.index("--") : command.index("--")] = extra
    return command


def _ready(process):
    deadline = time.monotonic() + 12
    data = bytearray()
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while time.monotonic() < deadline and len(data) <= 1024:
            if not selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                continue
            chunk = os.read(process.stdout.fileno(), 1025 - len(data))
            if not chunk:
                break
            data.extend(chunk)
            if b"\n" in data:
                if data.count(b"\n") != 1 or not data.endswith(b"\n"):
                    break
                reply = json.loads(data)
                if (
                    isinstance(reply, dict)
                    and set(reply) == {"ready", "source"}
                    and reply["ready"] is True
                    and reply["source"] == SOURCE
                    and process.poll() is None
                ):
                    return
                break
    raise RuntimeError("Private Audioquelle wurde nicht verifiziert bereit.")


class AudioSession:
    def __init__(self, process, temporary, tap, socket_descriptor):
        self.process, self.temporary, self.tap = process, temporary, tap
        self.socket_path = Path(temporary.name) / "runtime/pulse/native"
        self._socket_descriptor = socket_descriptor
        self.source_name = SOURCE
        self.sandbox_state = "started"
        self.runtime_verified = False
        # Pulse clients may administer this private server. PipeWire 1.0
        # cannot disable module loading; isolation is enforced by the capsule.
        self.server_control_scope = "private-capsule"
        self.dropped_packets = 0
        self._stop = threading.Event()
        self._failure = False
        self._result = None
        self._lock = threading.RLock()
        self._pump_ended = None
        os.set_blocking(process.stdin.fileno(), False)
        self.thread = threading.Thread(
            target=self._pump, name="projectm-pcm", daemon=True
        )
        self.thread.start()

    def _pump(self):
        try:
            while not self._stop.is_set() and not self.tap.closed:
                try:
                    payload = self.tap.read(0.1)
                except socket.timeout:
                    continue
                try:
                    count = os.write(self.process.stdin.fileno(), payload)
                except BlockingIOError:
                    self.dropped_packets += 1
                    continue
                if count != len(payload):
                    raise OSError("Unvollständige private PCM-Übergabe.")
        except (OSError, ValueError):
            if not self._stop.is_set() and not self.tap.closed:
                self._failure = True
        finally:
            self._pump_ended = time.monotonic()
            self.process.stdin.close()

    def _cleanup(self):
        self._stop.set()
        self.thread.join(timeout=1)
        if self.thread.is_alive():
            raise RuntimeError("Private PCM-Übergabe wurde nicht beendet.")
        self.tap.close()
        self.process.stdout.close()
        if self._socket_descriptor is not None:
            os.close(self._socket_descriptor)
            self._socket_descriptor = None
        self.temporary.cleanup()

    @contextmanager
    def socket_binding(self):
        """Pin the verified socket inode; never bind a mutable server pathname.

        The consumer passes only this duplicated O_PATH fd to Bubblewrap via
        pass_fds, using the yielded /proc/self/fd path as its ro-bind source.
        This grants only the already verified private socket, even after
        pathname replacement. The pathname above is for diagnostics only.
        """
        with self._lock:
            if self.poll() is not None:
                raise RuntimeError("Private Audioquelle wurde beendet.")
            descriptor = os.dup(self._socket_descriptor)
        try:
            yield Path(f"/proc/self/fd/{descriptor}"), descriptor
        finally:
            os.close(descriptor)

    def poll(self):
        with self._lock:
            if self._result is not None:
                return self._result
            result = self.process.poll()
            if (
                result is None
                and self._pump_ended is not None
                and time.monotonic() - self._pump_ended > 4
            ):
                self.process.kill()
                result = self.process.wait(timeout=2) or 2
            if result is not None:
                final = result or (2 if self._failure or self.thread.is_alive() else 0)
                self._cleanup()
                self._result = final
            return self._result

    def stop(self):
        with self._lock:
            if self._result is not None:
                return
            self._stop.set()
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
            self._cleanup()
            self._result = 0


def start(playback, *, work_root=None):
    from netmon.core import radio_sandbox as sandbox

    if not isinstance(playback, sandbox.SandboxProcess) or not available():
        raise sandbox.RadioSandboxError(
            "Geschützte private Audioquelle ist nicht verfügbar."
        )
    stdlib, files, scripts = _runtime()
    temporary = tempfile.TemporaryDirectory(prefix="projectm-audio-", dir=work_root)
    tap = None
    process = None
    socket_descriptor = None
    try:
        tap = playback.open_pcm_tap()
        directory = Path(temporary.name)
        if len(os.fsencode(directory / "runtime/pulse/native")) > 100:
            raise sandbox.RadioSandboxError("Privater Audiosocketpfad ist zu lang.")
        sandbox._prepare_directory(directory)
        (directory / "runtime/pulse").mkdir(mode=0o700, parents=True)
        (directory / "runtime").chmod(0o700)
        (directory / "config").mkdir(mode=0o700)
        for name, text in {
            **configurations(),
            "pulse-client.conf": "autospawn = no\nenable-shm = no\n",
        }.items():
            path = directory / "config" / name
            path.write_text(text)
            path.chmod(0o600)
        process = subprocess.Popen(
            _command(directory, stdlib, files, scripts),
            cwd="/",
            env=sandbox._ENV,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            bufsize=0,
        )
        _ready(process)
        # runtime/ is the only host directory writable by the server. Pin
        # each of its controlled components without following symlinks.
        runtime_fd = os.open(
            directory / "runtime",
            os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        try:
            pulse_fd = os.open(
                "pulse",
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=runtime_fd,
            )
            try:
                socket_descriptor = os.open(
                    "native", os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=pulse_fd
                )
            finally:
                os.close(pulse_fd)
        finally:
            os.close(runtime_fd)
        info = os.fstat(socket_descriptor)
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
            raise sandbox.RadioSandboxError("Ungültiger privater Audiosocket.")
        return AudioSession(process, temporary, tap, socket_descriptor)
    except Exception:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
            process.stdin.close()
            process.stdout.close()
        if tap is not None:
            tap.close()
        if socket_descriptor is not None:
            os.close(socket_descriptor)
        temporary.cleanup()
        raise


def apply_process_limits():
    import resource

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    maximum = min(
        [512 * 1024 * 1024] + [x for x in (soft, hard) if x != resource.RLIM_INFINITY]
    )
    resource.setrlimit(resource.RLIMIT_AS, (maximum, maximum))


def _worker():
    apply_process_limits()
    os.umask(0o077)
    os.mkfifo(FIFO, 0o600)
    children = []
    writer = None
    try:
        for name, config in (
            ("pipewire", "pipewire.conf"),
            ("wireplumber", "wireplumber.conf"),
            ("pipewire-pulse", "pipewire-pulse.conf"),
        ):
            if name != "pipewire":
                deadline = time.monotonic() + 4
                while not Path(RUNTIME + "/pipewire-0").exists():
                    if time.monotonic() >= deadline or children[0].poll() is not None:
                        raise RuntimeError("Private PipeWire-Quelle fehlt.")
                    time.sleep(0.02)
            children.append(
                subprocess.Popen(
                    ["/usr/bin/" + name, "-c", CONFIG + "/" + config],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    close_fds=True,
                )
            )
        deadline = time.monotonic() + 6
        while True:
            # Trusted local server output; bound it before parsing any JSON.
            probe = subprocess.Popen(
                ["/usr/bin/pactl", "--format=json", "list", "sources"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            try:
                with selectors.DefaultSelector() as selected:
                    selected.register(probe.stdout, selectors.EVENT_READ)
                    reply = bytearray()
                    until = min(deadline, time.monotonic() + 1)
                    while time.monotonic() < until and len(reply) <= 65536:
                        if not selected.select(0.05):
                            continue
                        chunk = os.read(probe.stdout.fileno(), 65537 - len(reply))
                        if not chunk:
                            break
                        reply.extend(chunk)
                    if len(reply) > 65536:
                        raise ValueError("Private source list too large.")
                try:
                    code = probe.wait(timeout=0.1)
                except subprocess.TimeoutExpired:
                    code = None
                if code == 0:
                    sources = json.loads(reply)
                    if [s.get("name") for s in sources] == [SOURCE]:
                        break
            finally:
                if probe.poll() is None:
                    probe.kill()
                probe.wait(timeout=1)
                probe.stdout.close()
            if time.monotonic() >= deadline or any(
                p.poll() is not None for p in children
            ):
                raise RuntimeError("Private Quelle wurde nicht bereit.")
            time.sleep(0.05)
        writer = os.open(FIFO, os.O_WRONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        if any(child.poll() is not None for child in children):
            raise RuntimeError("Private Audio-Policy wurde beendet.")
        print(json.dumps({"ready": True, "source": SOURCE}), flush=True)
        with selectors.DefaultSelector() as selector:
            selector.register(0, selectors.EVENT_READ)
            while not any(p.poll() is not None for p in children):
                if not selector.select(0.1):
                    continue
                data = os.read(0, 4096)
                if not data:
                    return 0
                if len(data) % 4:
                    raise ValueError("Incomplete PCM frame.")
                try:
                    if os.write(writer, data) != len(data):
                        raise OSError("Incomplete PCM source write.")
                except BlockingIOError:
                    pass
        return 2
    finally:
        if writer is not None:
            os.close(writer)
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
        for child in reversed(children):
            try:
                child.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=0.5)


if __name__ == "__main__":
    try:
        if sys.argv[1:]:
            raise ValueError("Invalid private audio arguments.")
        raise SystemExit(_worker())
    except Exception:
        raise SystemExit(2)
