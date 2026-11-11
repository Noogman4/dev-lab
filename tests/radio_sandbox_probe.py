"""Offline first-level probes, invoked by run_isolated_suite.py.

The trusted parent prepares synthetic fixtures and checks results. Every payload
runs in the real playback policy, with a private FIFO sink and no host network. No pytest
runs outside isolation. A test shell and its dependencies are mounted only for
the denial probes, never for actual playback.
"""

import importlib.util
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import wave

import psutil

from radio_probe_output import install, scopes_gone


def run(root: Path, output: Path) -> int:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location(
        "radio_sandbox_probe_subject", root / "netmon/core/radio_sandbox.py"
    )
    sandbox = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sandbox)
    results = {
        "scope": "offline product scopes/bwrap, synthetic PCM, private FIFO sink",
        "host_network": False,
        "host_audio": False,
        "checks": [],
        "pipewire_graph_tested": False,
    }
    print(f"Radio sandbox evidence: {output}", flush=True)
    sources = [
        "netmon/core/radio_sandbox.py",
        "netmon/core/radio_pcm.py",
        "netmon/core/radio_fifo_output.py",
        "netmon/features/radio_controller.py",
        "tests/radio_probe_output.py",
        "tests/radio_sandbox_probe.py",
        "tests/run_isolated_suite.py",
    ]
    results["source_sha256"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sources
    }
    restore = None
    audits = []
    try:
        with tempfile.TemporaryDirectory(prefix="radio-probe-") as name:
            work = Path(name)
            selected = work / "selected.wav"
            with wave.open(str(selected), "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(b"\0\0" * (3 * 8000))
            secret = work / "private-key"
            secret.write_text("SYNTHETIC-NETMON-PRIVATE-DATA")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as dummy_audio:
                audio_path = work / "audio.sock"
                dummy_audio.bind(str(audio_path))
                restore, outputs, audits = install(sandbox, work)
                policy = work / "policy"
                policy.mkdir(mode=0o700)
                sandbox._prepare_directory(policy)
                runtime = set()
                for binary in ("dash", "readlink", "env"):
                    runtime.update(sandbox._runtime_files(Path("/usr/bin") / binary))
                script = f"""set -eu
[ ! -e '{secret}' ]
[ ! -e /usr/lib/netmon ]
[ ! -e /usr/bin/sudo ]
[ ! -e /run/user ]
[ ! -e /dev/snd ]
[ ! -e /dev/dri ]
[ ! -e /tmp/.X11-unix ]
[ ! -e /run/audio/pulse ]
while read key value rest; do
    case "$key" in
        NoNewPrivs:) [ "$value" = 1 ] ;;
        CapEff:) [ "$value" = 0000000000000000 ] ;;
    esac
done < /proc/self/status
[ -f /media/selected ]
if (printf changed > /media/selected) 2>/dev/null; then exit 9; fi
printf 'ipc' > /run/control/probe
printf 'scratch' > /tmp/probe
readlink /proc/self/ns/user
readlink /proc/self/ns/pid
readlink /proc/self/ns/ipc
readlink /proc/self/ns/net
/usr/bin/env
"""
                command = sandbox._sandbox_command(
                    ["/usr/bin/dash", "-c", script],
                    policy,
                    tuple(sorted(runtime)),
                    None,
                    local_file=selected,
                )
                environment = {
                    **sandbox._ENV,
                    "NETMON_TEST_SECRET": "SYNTHETIC",
                    "SSH_AUTH_SOCK": "/synthetic/agent",
                    "DBUS_SESSION_BUS_ADDRESS": "synthetic",
                    "DISPLAY": ":12345",
                }
                probe = subprocess.run(
                    command,
                    env=environment,
                    cwd="/",
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                (output / "boundary.log").write_text(probe.stdout + probe.stderr)
                assert probe.returncode == 0, probe.stderr
                lines = probe.stdout.splitlines()
                assert len(lines) >= 4
                for kind, namespace in zip(("user", "pid", "ipc", "net"), lines[:4]):
                    assert namespace != os.readlink(f"/proc/self/ns/{kind}")
                environment = dict(line.split("=", 1) for line in lines[4:])
                assert not {
                    "NETMON_TEST_SECRET",
                    "SSH_AUTH_SOCK",
                    "DBUS_SESSION_BUS_ADDRESS",
                    "DISPLAY",
                    "LD_PRELOAD",
                }.intersection(environment)
                assert (policy / "control/probe").read_text() == "ipc"
                assert not (work / "probe").exists()
                results["checks"].append(
                    "real boundary, namespaces, read-only media, private IPC, clean environment"
                )

                from netmon.features.radio_controller import _mpv_command

                command = _mpv_command(50, str(selected), sandbox.IPC_PATH)
                command.insert(command.index("--"), "--pause")
                process = sandbox.start_playback(
                    command, ipc_root=work, local_file=selected
                )
                ipc_directory = Path(process.ipc_path).parent.parent
                try:
                    assert process.poll() is None
                    assert not process.runtime_verified
                    assert ipc_directory.stat().st_mode & 0o777 == 0o700
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                        client.settimeout(3)
                        client.connect(process.ipc_path)
                        client.sendall(
                            b'{"command":["get_property","path"],"request_id":31}\n'
                        )
                        with client.makefile("rb") as messages:
                            for _ in range(20):
                                reply = json.loads(messages.readline(8192))
                                if reply.get("request_id") == 31:
                                    assert reply.get("error") == "success"
                                    assert reply.get("data") == "/media/selected"
                                    break
                            else:
                                raise AssertionError("No media path reply")
                    with sandbox.connect_mpv(process.ipc_path, timeout=3) as client:
                        client.sendall(
                            b'{"command":["set_property","pause",false],"request_id":32}\n'
                        )
                        with client.makefile("rb") as messages:
                            for _ in range(20):
                                reply = json.loads(messages.readline(8192))
                                if reply.get("request_id") == 32:
                                    assert reply.get("error") == "success"
                                    break
                            else:
                                raise AssertionError("No acknowledged unpause")
                    deadline = time.monotonic() + 5
                    while process._output.count < 4096:
                        assert process.poll() is None
                        assert time.monotonic() < deadline
                        time.sleep(0.01)
                    results["playback_quota"] = process._probe_quota
                    results["pcm_bytes"] = process._output.count
                finally:
                    process.terminate()
                    process.wait(timeout=5)
                assert process._output_gate.done.is_set()
                assert not process._output_gate._thread.is_alive()
                assert outputs[-1].closed and not outputs[-1].thread.is_alive()
                assert not ipc_directory.exists()
                results["checks"].append(
                    "real mpv/PCM relay/gate/FIFO, live kernel quotas, IPC, owner stop and joined reader"
                )

                real_wait = sandbox._wait_for_ipc
                waiting_children = []

                def no_ready_channel(process):
                    waiting_children.extend(
                        psutil.Process(process.pid).children(recursive=True)
                    )
                    waiting_children.extend(
                        psutil.Process(process._pcm_process.pid).children(
                            recursive=True
                        )
                    )
                    process.ipc_path += ".absent"
                    return real_wait(process, timeout=0.15)

                sandbox._wait_for_ipc = no_ready_channel
                try:
                    sandbox.start_playback(command, ipc_root=work, local_file=selected)
                except sandbox.RadioSandboxError:
                    assert not list(work.glob("play-*"))
                    _gone, alive = psutil.wait_procs(waiting_children, timeout=3)
                    assert not [p for p in alive if p.status() != psutil.STATUS_ZOMBIE]
                else:
                    raise AssertionError("Missing IPC accepted")
                finally:
                    sandbox._wait_for_ipc = real_wait
                results["checks"].append(
                    "missing IPC times out, kills wrapper and cleans up"
                )

                real_bwrap = sandbox.BWRAP
                sandbox.BWRAP = Path("/usr/bin/false")
                try:
                    sandbox.start_playback(command, ipc_root=work, local_file=selected)
                except sandbox.RadioSandboxError:
                    assert not list(work.glob("play-*"))
                else:
                    raise AssertionError("Failed wrapper accepted")
                finally:
                    sandbox.BWRAP = real_bwrap
                results["checks"].append(
                    "wrapper failure closes start and removes private IPC"
                )

                runtime = set(sandbox._runtime_files(Path("/usr/bin/dash")))
                runtime.update(sandbox._runtime_files(Path("/usr/bin/sleep")))
                for method in ("terminate", "kill"):
                    script = """/usr/bin/sleep 30 &
child=$!
printf ready > /run/control/child
wait
"""
                    child_file = policy / "control/child"
                    if child_file.exists():
                        child_file.unlink()
                    args = sandbox._sandbox_command(
                        ["/usr/bin/dash", "-c", script],
                        policy,
                        tuple(sorted(runtime)),
                        None,
                        local_file=selected,
                    )
                    raw = subprocess.Popen(
                        args,
                        env=sandbox._ENV,
                        cwd="/",
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    try:
                        deadline = time.monotonic() + 3
                        descendants = []
                        while time.monotonic() < deadline:
                            descendants = psutil.Process(raw.pid).children(
                                recursive=True
                            )
                            if child_file.exists() and descendants:
                                break
                            time.sleep(0.02)
                        assert descendants
                        getattr(raw, method)()
                        raw.wait(timeout=5)
                        _gone, alive = psutil.wait_procs(descendants, timeout=3)
                        assert not [
                            p for p in alive if p.status() != psutil.STATUS_ZOMBIE
                        ]
                    finally:
                        if raw.poll() is None:
                            raw.kill()
                            raw.wait(timeout=5)
                    results["checks"].append(
                        f"wrapper {method} ends synthetic descendants"
                    )
        results["status"] = "passed"
    except Exception:
        results["status"] = "failed"
        results["error"] = traceback.format_exc()
    finally:
        if restore is not None:
            restore()
        try:
            results["scopes_after"] = scopes_gone(sandbox, audits)
        except Exception:
            results["status"] = "failed"
            results["scope_cleanup_error"] = traceback.format_exc()
        results["sources_unchanged_after"] = all(
            hashlib.sha256((root / name).read_bytes()).hexdigest() == value
            for name, value in results["source_sha256"].items()
        )
        if not results["sources_unchanged_after"]:
            results["status"] = "failed"
    (output / "radio-sandbox-result.json").write_text(
        json.dumps(results, indent=2) + "\n"
    )
    print(json.dumps(results, indent=2), flush=True)
    return 0 if results["status"] == "passed" else 1
