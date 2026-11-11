"""Private PCM/Pulse adapter probe; no host audio or real visualizer."""

import array
import ast
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback

sys.pycache_prefix = "/nonexistent"
os.environ["PYTHONPYCACHEPREFIX"] = "/nonexistent"


def check_boundary(output):
    from netmon.core import projectm_audio as audio, radio_sandbox as sandbox

    with tempfile.TemporaryDirectory(prefix="audio-boundary-", dir=output) as name:
        directory = Path(name)
        sandbox._prepare_directory(directory)
        (directory / "runtime").mkdir(mode=0o700)
        (directory / "config").mkdir()
        stdlib, files, scripts = audio._runtime()
        command = audio._command(directory, stdlib, files, scripts)
        private = output / "audio-private-key"
        private.write_text("SYNTHETIC PRIVATE KEY")
        source = output / "audio-boundary-worker.py"
        limits = next(
            n
            for n in ast.parse(audio.WORKER.read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name == "apply_process_limits"
        )
        abstract = "\0netmon-private-audio-" + str(os.getpid())
        outside = output / "private-pulse-canary"
        descriptor = os.open(private, os.O_RDONLY)
        inherited = fcntl.fcntl(descriptor, fcntl.F_DUPFD, 200)
        os.close(descriptor)
        os.set_inheritable(inherited, True)
        try:
            with (
                socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp,
                socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as abstract_socket,
                socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as outside_socket,
            ):
                tcp.bind(("127.0.0.1", 0))
                tcp.listen(1)
                abstract_socket.bind(abstract)
                abstract_socket.listen(1)
                outside_socket.bind(str(outside))
                outside_socket.listen(1)
                # All listeners belong to the already verified private coordinator.
                for address, family, listener in [
                    (tcp.getsockname(), socket.AF_INET, tcp),
                    (abstract, socket.AF_UNIX, abstract_socket),
                    (str(outside), socket.AF_UNIX, outside_socket),
                ]:
                    with socket.socket(family, socket.SOCK_STREAM) as control:
                        control.settimeout(0.2)
                        control.connect(address)
                        accepted, _ = listener.accept()
                        accepted.close()
                source.write_text(
                    "import os,json,socket,resource\nfrom pathlib import Path\n"
                    + ast.unparse(limits)
                    + "\napply_process_limits()\n"
                    + "def attempt(action):\n try: action(); return True\n except OSError: return False\n"
                    + "def connect(family,address):\n with socket.socket(family,socket.SOCK_STREAM) as s:\n  s.settimeout(0.2);s.connect(address)\n"
                    + "r={}\n"
                    + f"r['private']=attempt(lambda: open({str(private)!r}).read())\n"
                    + f"r['host_audio_canary']=attempt(lambda: connect(socket.AF_UNIX,{str(outside)!r}))\n"
                    + f"r['abstract']=attempt(lambda: connect(socket.AF_UNIX,{abstract!r}))\n"
                    + f"r['tcp']=attempt(lambda: connect(socket.AF_INET,{tcp.getsockname()!r}))\n"
                    + f"r['inherited_fd']=attempt(lambda: os.read({inherited},1))\n"
                    + "r['secret_env']='NETMON_AUDIO_SECRET' in os.environ\n"
                    + "for n,p in [('devices','/dev/snd'),('dbus','/run/dbus'),('user_runtime','/run/user'),('control','/run/control'),('sudo','/usr/bin/sudo'),('shell','/bin/sh')]:r[n]=Path(p).exists()\n"
                    + "r['private_write']=attempt(lambda: open('/run/private-audio/probe','w').write('OWNED'))\n"
                    + "r['caps']=next(int(l.split()[1],16) for l in Path('/proc/self/status').read_text().splitlines() if l.startswith('CapEff:'))\n"
                    + "r['no_new_privs']='NoNewPrivs:\\t1' in Path('/proc/self/status').read_text()\n"
                    + "r['memory']=resource.getrlimit(resource.RLIMIT_AS)[0]\nprint(json.dumps(r))\n"
                )
                command[command.index(str(audio.WORKER))] = str(source)
                previous = os.environ.get("NETMON_AUDIO_SECRET")
                os.environ["NETMON_AUDIO_SECRET"] = "SYNTHETIC SECRET"
                try:
                    result = subprocess.run(
                        command,
                        env=sandbox._ENV,
                        cwd="/",
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        timeout=5,
                        close_fds=True,
                        check=True,
                    )
                finally:
                    if previous is None:
                        os.environ.pop("NETMON_AUDIO_SECRET", None)
                    else:
                        os.environ["NETMON_AUDIO_SECRET"] = previous
                measured = json.loads(result.stdout)
                assert measured.pop("memory") == 512 * 1024 * 1024
                assert measured.pop("private_write") is True
                assert measured.pop("no_new_privs") is True
                assert not any(measured.values()), measured
                assert (directory / "runtime/probe").read_text() == "OWNED"
                return {
                    **measured,
                    "private_write": True,
                    "no_new_privs": True,
                    "memory": 512 * 1024 * 1024,
                }
        finally:
            os.close(inherited)
            outside.unlink(missing_ok=True)


def check_source(output, playback):
    """Real Pulse client on only the newly created private socket."""
    from netmon.core import projectm_audio as audio, radio_sandbox as sandbox
    from netmon.core.projectm_process import OwnedProcess

    session = audio.start(playback, work_root=output)
    owned = OwnedProcess(session.process)
    try:
        with (
            session.socket_binding() as (bind_source, bind_fd),
            tempfile.TemporaryDirectory(prefix="pulse-client-", dir=output) as name,
        ):
            target = output / "audio-path-canary"
            target.write_text("PRIVATE CANARY")
            session.socket_path.rename(session.socket_path.with_name("original-socket"))
            session.socket_path.symlink_to(target)
            client = Path(name)
            sandbox._prepare_directory(client)

            def command(arguments):
                return sandbox._sandbox_command(
                    arguments,
                    client,
                    sandbox._runtime_files(Path(arguments[0])),
                    bind_source,
                    local_file=None,
                    audio_output=True,
                )

            sources = subprocess.run(
                command(["/usr/bin/pactl", "--format=json", "list", "sources"]),
                env=sandbox._ENV,
                cwd="/",
                stdin=subprocess.DEVNULL,
                pass_fds=(bind_fd,),
                capture_output=True,
                timeout=3,
                check=True,
            )
            names = [s["name"] for s in json.loads(sources.stdout)]
            assert names == [audio.SOURCE]
            loading = subprocess.run(
                command(
                    [
                        "/usr/bin/pactl",
                        "load-module",
                        "module-null-sink",
                        "sink_name=private_probe",
                    ]
                ),
                env=sandbox._ENV,
                cwd="/",
                stdin=subprocess.DEVNULL,
                pass_fds=(bind_fd,),
                capture_output=True,
                timeout=3,
            )
            (output / "module-load-result.json").write_text(
                json.dumps(
                    {
                        "returncode": loading.returncode,
                        "stdout": loading.stdout.decode(errors="replace"),
                        "stderr": loading.stderr.decode(errors="replace"),
                    },
                    indent=2,
                )
            )
            module_blocked = loading.returncode != 0
            if not module_blocked:
                module_id = loading.stdout.strip().decode("ascii")
                assert module_id.isdecimal()
                subprocess.run(
                    command(["/usr/bin/pactl", "unload-module", module_id]),
                    env=sandbox._ENV,
                    cwd="/",
                    stdin=subprocess.DEVNULL,
                    pass_fds=(bind_fd,),
                    capture_output=True,
                    timeout=3,
                    check=True,
                )
            sources_after = subprocess.run(
                command(["/usr/bin/pactl", "--format=json", "list", "sources"]),
                env=sandbox._ENV,
                cwd="/",
                stdin=subprocess.DEVNULL,
                pass_fds=(bind_fd,),
                capture_output=True,
                timeout=3,
                check=True,
            )
            assert [s["name"] for s in json.loads(sources_after.stdout)] == [
                audio.SOURCE
            ]
            capture = subprocess.Popen(
                command(
                    [
                        str(sandbox.PACAT),
                        "--record",
                        "--raw",
                        "--format=s16ne",
                        "--rate=48000",
                        "--channels=2",
                        "--latency-msec=20",
                        "--device=" + audio.SOURCE,
                    ]
                ),
                env=sandbox._ENV,
                cwd="/",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                pass_fds=(bind_fd,),
            )
            try:
                data = bytearray()
                deadline = time.monotonic() + 6
                with selectors.DefaultSelector() as selected:
                    selected.register(capture.stdout, selectors.EVENT_READ)
                    while time.monotonic() < deadline:
                        if not selected.select(0.1):
                            continue
                        chunk = os.read(capture.stdout.fileno(), 4096)
                        if not chunk:
                            break
                        data.extend(chunk)
                        if len(data) > 38400:
                            del data[:-38400]
                        if len(data) >= 19200 and any(data):
                            break
                values = array.array("h")
                values.frombytes(data[: len(data) - len(data) % 4])
                assert len(values) >= 9600 and any(values), "No private PCM capture"
                report = {
                    "captured_bytes": len(data),
                    "left_peak": max(values[::2]),
                    "right_peak": max(values[1::2]),
                    "sources": names,
                    "module_loading_blocked": module_blocked,
                    "owned_tasks": len(owned.pids),
                }
            finally:
                capture.terminate()
                capture.wait(timeout=3)
                capture.stdout.close()
                capture.stderr.close()
        assert target.read_text() == "PRIVATE CANARY"
        report["socket_inode_pinned"] = True
        return report
    finally:
        path = session.socket_path
        session.stop()
        assert not path.exists()
        assert not owned.pids
        owned.poll()  # close the probe's independent observation handles
        assert playback.poll() is None


def _worker(root, output, parent_net):
    result = {
        "status": "failed",
        "checks": [],
        "host_audio": False,
        "host_network": False,
        "visualizer_started": False,
    }
    session = playback = relay = None
    feeder = None
    stop = threading.Event()
    handles = []
    original_popen = subprocess.Popen
    try:
        assert os.readlink("/proc/self/ns/net") != parent_net
        assert [n for _, n in socket.if_nameindex()] == ["lo"]
        subprocess.run(
            ["/usr/sbin/ip", "link", "set", "lo", "up"],
            check=True,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8"},
        )
        from radio_stream_probe import _drop_namespace_caps

        _drop_namespace_caps()
        sys.path.insert(0, str(root))
        from netmon.core import projectm_audio as audio, radio_sandbox as sandbox

        result["source_sha256"] = {
            f: hashlib.sha256((root / f).read_bytes()).hexdigest()
            for f in (
                "netmon/core/projectm_audio.py",
                "netmon/core/radio_pcm.py",
                "netmon/core/radio_sandbox.py",
                "tests/projectm_audio_probe.py",
                "tests/run_isolated_suite.py",
            )
        }
        log = (output / "private-audio.log").open("w")
        handles.append(log)

        class LoggedPopen(original_popen):
            def __init__(self, command, *args, **kwargs):
                if (
                    command[0] == str(sandbox.BWRAP)
                    and "/run/audio-worker.py" in command
                ):
                    kwargs["stderr"] = log
                super().__init__(command, *args, **kwargs)

        subprocess.Popen = LoggedPopen
        temporary = tempfile.TemporaryDirectory(prefix="pcm-source-", dir=output)
        directory = Path(temporary.name)
        sandbox._prepare_directory(directory)
        (directory / "tap").mkdir(mode=0o700)
        stdlib, runtime = sandbox._pcm_runtime()
        relay = subprocess.Popen(
            sandbox._pcm_command(directory, stdlib, runtime),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=log,
            env=sandbox._ENV,
            cwd="/",
            close_fds=True,
            bufsize=0,
        )
        # Real fixed PCM relay with a synthetic trusted source, not an mpv test.
        playback = sandbox.SandboxProcess(relay, temporary, pcm_process=relay)
        samples = array.array(
            "h",
            (
                value
                for n in range(4800)
                for value in (
                    int(5000 * math.sin(2 * math.pi * 440 * n / 48000)),
                    int(7000 * math.sin(2 * math.pi * 880 * n / 48000)),
                )
            ),
        ).tobytes()

        def feed():
            try:
                while not stop.is_set():
                    for offset in range(0, len(samples), 3840):
                        if stop.is_set():
                            return
                        relay.stdin.write(samples[offset : offset + 3840])
                        stop.wait(0.02)
            except (OSError, ValueError):
                pass

        feeder = threading.Thread(target=feed, daemon=True)
        feeder.start()
        result["capture"] = check_source(output, playback)
        assert result["capture"]["left_peak"] > 3000
        assert result["capture"]["right_peak"] > 5000
        result["checks"].extend(
            [
                "synthetic NetMon PCM crosses the real private Pulse source to a separately sandboxed capture client",
                "exactly one initial private PCM source; client module loading measured and private probe module removed",
                "stopping private audio cleans all observed owned tasks without stopping the original PCM relay",
            ]
        )
        session = audio.start(playback, work_root=output)
        session.process.kill()
        deadline = time.monotonic() + 3
        while session.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert session.poll() != 0
        assert relay.poll() is None
        assert not session.socket_path.exists()
        result["checks"].append(
            "lost private audio capsule is reaped and leaves original PCM playback running"
        )
        result["boundary"] = check_boundary(output)
        result["checks"].append(
            "exact capsule grants deny private files, host-audio canary, TCP/abstract sockets, devices, D-Bus, helpers and inherited secrets; only own runtime writable"
        )
        _, runtime, scripts = audio._runtime()
        result["runtime_sha256"] = {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (*runtime, *scripts)
        }
        session = audio.start(playback, work_root=output)
        playback.terminate()
        playback.wait(timeout=3)
        deadline = time.monotonic() + 4
        while session.poll() is None and time.monotonic() < deadline:
            time.sleep(0.02)
        assert session.poll() == 0
        assert not session.socket_path.exists()
        result["checks"].append(
            "ending the original PCM playback closes its tap and ends private audio without rescheduling"
        )
        result["status"] = "passed"
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        if session is not None:
            session.stop()
        stop.set()
        if playback is not None:
            playback.kill()
            playback.wait(timeout=3)
        if feeder is not None:
            feeder.join(timeout=2)
        if relay is not None:
            relay.stdin.close()
        subprocess.Popen = original_popen
        for handle in handles:
            handle.close()
    (output / "projectm-audio-result.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


def run(root, output):
    command = [
        "/usr/bin/unshare",
        "--user",
        "--map-current-user",
        "--keep-caps",
        "--net",
        "--fork",
        "--kill-child=KILL",
        str(root / ".venv/bin/python"),
        "-B",
        str(Path(__file__).resolve()),
        "--worker",
        str(root),
        str(output),
        os.readlink("/proc/self/ns/net"),
    ]
    print("Private projectM audio evidence:", output, flush=True)
    result = subprocess.run(
        command,
        cwd=root,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": "/nonexistent"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    (output / "coordinator.log").write_text(result.stdout + result.stderr)
    print(result.stdout + result.stderr)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        raise SystemExit(_worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]))
    raise SystemExit("Use tests/run_isolated_suite.py --projectm-audio-probe")
