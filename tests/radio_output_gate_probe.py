"""First-level product gate/decoder capsules; private FIFO, no audio server.

Invoked only by the existing isolated starter. The trusted coordinator has no
media source beyond synthetic WAV; every child uses the actual networkless
product capsule. Readiness/link management is replaced by a private writer,
so this is not a PipeWire/host-audio acceptance.
"""

import array
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import wave


def run(root, output):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from netmon.core import radio_fifo_output as fifo
    from netmon.core import radio_sandbox as sandbox
    from netmon.features.radio_controller import _mpv_command

    result = {"status": "error", "host_audio": False, "pipewire": False, "cases": []}
    real_open_output, real_pcm, real_write = sandbox._open_output, sandbox.PCM, os.write
    gate = child = playback = None
    sink = None
    reader = writer = None
    trace = []
    observed_inodes = set()

    def measured_write(fd, data):
        written = real_write(fd, data)
        info = os.fstat(fd)
        if (info.st_dev, info.st_ino) in observed_inodes:
            trace.append((time.monotonic(), written))
        return written

    def drain(fd, data):
        while True:
            try:
                chunk = os.read(fd, 8192)
            except BlockingIOError:
                return
            if not chunk:
                return
            data.extend(chunk)
            if len(data) > 2 * 1024 * 1024:
                raise AssertionError("private sink input bound exceeded")

    def rate_check(events):
        for i, (first, _) in enumerate(events):
            total = 0
            for last, count in events[i:]:
                total += count
                assert total <= 38_400 + 192_000 * (last - first) + 1

    class PrivateSink:
        """Drain already during the handshake, like a loaded tunnel would."""

        def __init__(self, fd):
            self.fd = fd
            self.data = bytearray()
            self.stop_event = threading.Event()
            self.error = None
            self.thread = threading.Thread(target=self.read)
            self.thread.start()

        def read(self):
            try:
                while not self.stop_event.is_set():
                    drain(self.fd, self.data)
                    self.stop_event.wait(0.001)
            except Exception as exc:
                self.error = exc

        def stop(self):
            self.stop_event.set()
            self.thread.join()
            if self.error is not None:
                raise self.error

    class PrivateOutput:
        def __init__(self, owned_writer):
            self.writer = owned_writer
            self.events = []

        @property
        def descriptor(self):
            return self.writer.fd

        def handed_over(self):
            self.writer.close_descriptor()

        def lost(self):
            return False

        def silence(self):
            self.events.append("silence")

        def close(self):
            self.events.append("close")
            self.writer.close()

    try:
        os.write = measured_write
        with tempfile.TemporaryDirectory(prefix="f3-", dir="/tmp/user/1000") as name:
            work = Path(name)
            state = work / "state"
            state.mkdir(mode=0o700)
            paths = fifo.Paths(
                state,
                state / fifo.FIFO_NAME,
                state / fifo.LOCK_NAME,
                work,
                work / "unused.conf",
            )
            os.mkfifo(paths.fifo, 0o600)
            info = paths.fifo.stat()
            observed_inodes.add((info.st_dev, info.st_ino))
            reader = os.open(paths.fifo, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
            writer = fifo.FifoWriter(paths)
            writer.open()

            policy = work / "policy"
            policy.mkdir(mode=0o700)
            sandbox._prepare_directory(policy)
            (policy / "tap").mkdir(mode=0o700)
            # Same runtime/capsule as the relay, replacing only its fixed script.
            canary = work / "canary.py"
            canary.write_text("""import json, os
report = {"stdout": os.readlink("/proc/self/fd/1"), "fds": [], "fifo_open": None}
for entry in os.listdir("/proc/self/fd"):
    try:
        os.fstat(int(entry))
        report["fds"].append(int(entry))
    except OSError:
        pass
try:
    fd = os.open(FIFO_PATH, os.O_WRONLY | os.O_NONBLOCK)
    os.close(fd)
    report["fifo_open"] = "unexpected success"
except OSError as exc:
    report["fifo_open"] = exc.errno
report["absent"] = {p: not os.path.exists(p) for p in ["/run/user", "/dev/snd", "/dev/dri", "/home/happy", "/run/control"]}
report["pid_namespace"] = os.readlink("/proc/self/ns/pid")
report["net_namespace"] = os.readlink("/proc/self/ns/net")
report["status"] = {line.split(":")[0]: line.split(":", 1)[1].strip() for line in open("/proc/self/status") if line.startswith(("NoNewPrivs:", "CapEff:"))}
os.write(2, (json.dumps(report) + "\\n").encode())
data = memoryview(bytes(range(256)) * 1500)
while data:
    data = data[os.write(1, data):]
""".replace("FIFO_PATH", repr(str(paths.fifo))))
            (output / "executed-canary.py").write_bytes(canary.read_bytes())
            sandbox.PCM = canary
            stdlib, runtime = sandbox._pcm_runtime()
            command = sandbox._pcm_command(policy, stdlib, runtime)
            child = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                cwd="/",
                env=sandbox._ENV,
            )
            gate = sandbox._PcmOutputGate(child.stdout.fileno(), writer.fd)
            child.stdout.close()
            child.stdout = None
            writer.close_descriptor()
            data = bytearray()
            end = time.monotonic() + 6
            while not gate.done.is_set():
                drain(reader, data)
                assert time.monotonic() < end
                time.sleep(0.001)
            drain(reader, data)
            assert gate.error is None
            child.wait(timeout=1)
            raw = child.stderr.read()
            child.stderr.close()
            (output / "canary-stderr.log").write_bytes(raw)
            assert child.returncode == 0, raw.decode(errors="replace")
            audit = json.loads(raw)
            assert audit["stdout"].startswith("pipe:[")
            assert sorted(audit["fds"]) == [0, 1, 2]
            assert audit["fifo_open"] == 2
            assert all(audit["absent"].values())
            assert audit["pid_namespace"] != os.readlink("/proc/self/ns/pid")
            assert audit["net_namespace"] != os.readlink("/proc/self/ns/net")
            assert audit["status"]["NoNewPrivs"] == "1"
            assert int(audit["status"]["CapEff"], 16) == 0
            assert data == bytes(range(256)) * 1500
            rate_check(trace)
            (output / "canary-writes.json").write_text(json.dumps(trace, indent=2))
            result["cases"].append(
                {
                    "case": "real-relay-capsule-canary",
                    "bytes": len(data),
                    "audit": audit,
                    "budget_checked": True,
                    "capsule_argv": command,
                }
            )
            gate.close()
            gate = child = None
            writer.close()
            os.close(reader)
            reader = None
            sandbox.PCM = real_pcm

            media = work / "selected.wav"
            for case, seconds in [("eof", 2), ("stop", 10), ("reader-loss", 10)]:
                with wave.open(str(media), "wb") as wav:
                    wav.setnchannels(2)
                    wav.setsampwidth(2)
                    wav.setframerate(48000)
                    wav.writeframes(
                        array.array("h", [1000, -1000] * (48000 * seconds)).tobytes()
                    )
                reader = os.open(paths.fifo, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
                writer = fifo.FifoWriter(paths)
                writer.open()
                output_owner = PrivateOutput(writer)
                sandbox._open_output = lambda: output_owner
                sink = PrivateSink(reader)
                trace.clear()
                started = time.monotonic()
                playback = sandbox.start_playback(
                    _mpv_command(100, str(media), sandbox.IPC_PATH),
                    ipc_root=work,
                    local_file=media,
                )
                data = sink.data
                event_time = None
                deadline = time.monotonic() + 8
                while True:
                    now = time.monotonic()
                    if case != "eof" and event_time is None and len(data) >= 19_200:
                        event_time = now
                        if case == "stop":
                            playback.terminate()
                        else:
                            sink.stop()
                            os.close(reader)
                            reader = None
                    rc = playback.poll()
                    if rc is not None:
                        break
                    assert now < deadline, case
                    time.sleep(0.005)
                sink.stop()
                sink = None
                if reader is not None:
                    drain(reader, data)
                if case == "eof":
                    assert rc == 0 and len(data) == 384_000
                elif case == "stop":
                    assert rc != 0 and output_owner.events[0] == "silence"
                else:
                    assert rc != 0 and playback.output_lost
                assert playback._output_gate.done.is_set()
                assert not playback._output_gate._thread.is_alive()
                assert playback._process.poll() is not None
                assert playback._pcm_process.poll() is not None
                assert not Path(playback.ipc_path).exists()
                rate_check(trace)
                (output / f"{case}-writes.json").write_text(json.dumps(trace, indent=2))
                lock_reader = os.open(paths.fifo, os.O_RDONLY | os.O_NONBLOCK)
                try:
                    with fifo.FifoWriter(paths):
                        pass  # no stale writer lock
                finally:
                    os.close(lock_reader)
                result["cases"].append(
                    {
                        "case": case,
                        "rc": rc,
                        "received_bytes": len(data),
                        "events": output_owner.events,
                        "output_lost": playback.output_lost,
                        "duration_s": time.monotonic() - started,
                        "after_event_s": (
                            time.monotonic() - event_time if event_time else None
                        ),
                        "budget_checked": True,
                        "gate_joined": True,
                        "children_reaped": True,
                    }
                )
                playback = None
                writer.close()
                if reader is not None:
                    os.close(reader)
                    reader = None
            result["status"] = "passed"
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        sandbox._open_output, sandbox.PCM, os.write = (
            real_open_output,
            real_pcm,
            real_write,
        )
        if sink is not None:
            sink.stop()
        if playback is not None:
            playback.kill()
            playback.wait(timeout=3)
        if gate is not None:
            gate.close()
        if child is not None:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=1)
            child.stderr.close()
        if writer is not None:
            writer.close()
        if reader is not None:
            os.close(reader)
    result["source_hashes"] = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (
            root / "netmon/core/radio_sandbox.py",
            root / "netmon/core/radio_pcm.py",
            root / "netmon/core/radio_fifo_output.py",
            Path(__file__),
        )
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1
