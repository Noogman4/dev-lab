"""Private FIFO sink for native probes, never a real PipeWire/host output.

Only _open_output is substituted. The real output gate, decoder/relay/source
capsules, quota manager and owner cleanup remain in use. Each sink is bounded
to counters, owns its FIFO/reader and persists its terminal audit under work.
"""

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time


def _write(path, value):
    temp = path.with_suffix(".new")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


class PrivateOutput:
    def __init__(self, work):
        from netmon.core import radio_fifo_output as fifo

        self.temporary = tempfile.TemporaryDirectory(prefix="sink-", dir=work)
        directory = Path(self.temporary.name)
        os.chmod(directory, 0o700)
        self.paths = fifo.Paths(
            directory,
            directory / fifo.FIFO_NAME,
            directory / fifo.LOCK_NAME,
            directory,
            directory / "unused.conf",
        )
        os.mkfifo(self.paths.fifo, 0o600)
        self.reader = os.open(
            self.paths.fifo, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC
        )
        self.writer = fifo.FifoWriter(self.paths)
        try:
            self.writer.open()
        except BaseException:
            os.close(self.reader)
            self.temporary.cleanup()
            raise
        self.count = 0
        self.error = None
        self.events = []
        self.closed = False
        self.cancelled = threading.Event()
        self.audit_path = Path(work) / (directory.name + ".json")
        self.open_path = Path(work) / ("opened-" + directory.name + ".json")
        self.thread = threading.Thread(
            target=self._drain, name="private-fifo-sink", daemon=False
        )
        try:
            _write(self.open_path, {"pid": os.getpid(), "audit": self.audit_path.name})
            self.thread.start()
        except BaseException:
            self.writer.close()
            os.close(self.reader)
            self.temporary.cleanup()
            raise

    @property
    def descriptor(self):
        return self.writer.fd

    def handed_over(self):
        self.writer.close_descriptor()

    def _drain(self):
        try:
            while not self.cancelled.is_set():
                try:
                    data = os.read(self.reader, 8192)
                except BlockingIOError:
                    data = b""
                self.count += len(data)
                if not data:
                    self.cancelled.wait(0.002)
        except OSError as error:
            self.error = str(error)

    def lost(self):
        return self.error is not None

    def silence(self):
        if "silence" not in self.events:
            self.events.append("silence")

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.silence()
        self.events.append("close")
        self.writer.close()
        self.cancelled.set()
        self.thread.join(1)
        os.close(self.reader)
        self.temporary.cleanup()
        _write(
            self.audit_path,
            {
                "bytes": self.count,
                "events": self.events,
                "reader_joined": not self.thread.is_alive(),
                "error": self.error,
                "fifo_removed": not self.paths.fifo.exists(),
            },
        )
        if self.thread.is_alive() or self.error is not None:
            raise RuntimeError("private FIFO reader failed cleanup")


def quota_audit(sandbox, process, profile, expected_net=None):
    """Read only this owned child's live kernel limits, no process-name search."""
    pid = process.pid
    membership = (Path("/proc") / str(pid) / "cgroup").read_text().splitlines()
    relative = next(line[3:] for line in membership if line.startswith("0::"))
    assert relative.startswith("/") and ".." not in Path(relative).parts
    group = Path("/sys/fs/cgroup") / relative.lstrip("/")
    unit = group.name
    assert re.fullmatch(
        rf"netmon-radio-{re.escape(profile)}-{os.getpid()}-\d+\.scope", unit
    ), unit
    quota = sandbox.QUOTAS[profile]
    memory = str(quota["memory"])
    maximum = int(memory[:-1]) * 1024 ** {"M": 2, "G": 3}[memory[-1]]
    measured = {
        name: (group / name).read_text().strip()
        for name in ("memory.max", "memory.swap.max", "pids.max", "cpu.max")
    }
    assert int(measured["memory.max"]) == maximum
    assert measured["memory.swap.max"] == "0"
    assert int(measured["pids.max"]) == quota["tasks"]
    amount, period = map(int, measured["cpu.max"].split())
    assert abs(amount * 100 / period - quota["cpu"]) < 0.01
    limits = (Path("/proc") / str(pid) / "limits").read_text()
    for label, key in [("Max open files", "nofile"), ("Max file size", "fsize")]:
        match = re.search(re.escape(label) + r"\s+(\d+)\s+(\d+)", limits)
        assert match and tuple(map(int, match.groups())) == (quota[key], quota[key])
    measured["rlimit_nofile"] = quota["nofile"]
    measured["rlimit_fsize"] = quota["fsize"]
    net = os.readlink(f"/proc/{pid}/ns/net")
    if expected_net is not None and profile in {"fetch"}:
        assert net == expected_net, (net, expected_net)
    # Bwrap's creating PID is outside its child's net namespace; audit cgroup
    # here. Individual namespace/grant checks are the boundary payload's job.
    return {
        "pid": pid,
        "profile": profile,
        "unit": unit,
        "limits": measured,
        "cgroup": relative,
    }


def install(sandbox, work):
    """Install only in a trusted native-probe coordinator/UI fixture."""
    work = Path(work).resolve(strict=True)
    original_open = sandbox._open_output
    original_start = sandbox.start_playback
    original_record = sandbox.start_recording
    original_limited = sandbox._limited
    outputs, audits = [], []
    audit_path = work / f"scope-audit-{os.getpid()}.json"

    def limited(command, profile):
        plan = original_limited(command, profile)
        at = plan.index("--tmpfs")
        assert plan[at - 2] == "--size" and plan[at + 1] == "/tmp"
        assert int(plan[at - 1]) <= sandbox.QUOTAS[profile]["tmpfs"]
        unit = next(
            part.split("=", 1)[1] for part in plan if part.startswith("--unit=")
        )
        audits.append({"unit": unit + ".scope", "profile": profile, "planned": True})
        _write(audit_path, audits)
        return plan

    def open_output():
        value = PrivateOutput(work)
        outputs.append(value)
        return value

    def audited_start(*args, **kwargs):
        owner = original_start(*args, **kwargs)
        try:
            entries = [
                quota_audit(sandbox, owner._process, "decoder"),
                quota_audit(sandbox, owner._pcm_process, "relay"),
            ]
            if owner._source_process is not None:
                entries.append(quota_audit(sandbox, owner._source_process, "fetch"))
            owner._probe_quota = entries
            audits.extend(entries)
            _write(audit_path, audits)
            assert isinstance(owner._output, PrivateOutput)
            return owner
        except BaseException:
            owner.kill()
            owner.wait(timeout=3)
            raise

    def audited_record(*args, **kwargs):
        owner = original_record(*args, **kwargs)
        try:
            entries = [quota_audit(sandbox, owner._process, "encoder")]
            if owner._source_process is not None:
                entries.append(quota_audit(sandbox, owner._source_process, "fetch"))
            audits.extend(entries)
            _write(audit_path, audits)
            return owner
        except BaseException:
            owner.kill()
            owner.wait(timeout=3)
            raise

    sandbox._open_output = open_output
    sandbox.start_playback = audited_start
    sandbox.start_recording = audited_record
    sandbox._limited = limited

    def restore():
        sandbox._open_output = original_open
        sandbox.start_playback = original_start
        sandbox.start_recording = original_record
        sandbox._limited = original_limited
        for output in outputs:
            if not output.closed:
                output.close()

    return restore, outputs, audits


def scopes_gone(sandbox, entries, timeout=5):
    """Ask only for already recorded own units; never stop or enumerate units."""
    result = {}
    for unit in sorted({entry["unit"] for entry in entries}):
        assert re.fullmatch(r"netmon-radio-[a-z-]+-\d+-\d+\.scope", unit)
        deadline = time.monotonic() + timeout
        while True:
            reply = subprocess.run(
                [
                    "/usr/bin/systemctl",
                    "--user",
                    "show",
                    unit,
                    "--property=LoadState",
                    "--value",
                ],
                env=sandbox._quota_env(),
                capture_output=True,
                text=True,
                timeout=2,
            )
            if reply.stdout.strip() == "not-found":
                result[unit] = "not-found"
                break
            assert time.monotonic() < deadline, (unit, reply.stdout, reply.stderr)
            time.sleep(0.05)
    return result
