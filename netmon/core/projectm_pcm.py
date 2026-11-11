"""Bounded one-way PCM feeding; no audio-server or playback process authority."""

import fcntl
import os
import socket
import threading
import time
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile

from netmon.core import radio_sandbox as sandbox
from netmon.core.projectm_process import OwnedProcess

WORKER = Path(__file__).with_name("projectm_pcm_worker.py")


def bounded_pipe(handle):
    capacity = fcntl.fcntl(handle.fileno(), fcntl.F_GETPIPE_SZ)
    if capacity > 16384:
        fcntl.fcntl(handle.fileno(), fcntl.F_SETPIPE_SZ, 16384)
    capacity = fcntl.fcntl(handle.fileno(), fcntl.F_GETPIPE_SZ)
    if capacity > 16384:
        raise RuntimeError("pipe capacity exceeds profile")
    return capacity


class PcmFeed:
    def __init__(self, tap, writer):
        self.tap, self.writer = tap, writer
        self.cancelled = threading.Event()
        self.done = threading.Event()
        self.reason = None
        self.forwarded = self.dropped = self.rate_dropped = self.max_pending = 0
        self.stale_dropped = 0
        self.last_forward = time.monotonic()
        os.set_blocking(writer.fileno(), False)
        self.thread = threading.Thread(target=self.run, name="projectm-pcm-feed")
        self.thread.start()

    def run(self):
        credit, last_credit = 4096.0, time.monotonic()
        received = last_credit
        try:
            while not self.cancelled.is_set():
                if self.tap.closed:
                    self.reason = "source-ended"
                    return
                now = time.monotonic()
                if now - self.last_forward >= 5:
                    self.reason = (
                        "pcm-timeout" if now - received >= 5 else "backpressure-timeout"
                    )
                    return
                try:
                    packet = self.tap.read(0.1, latest=True)
                except socket.timeout:
                    continue
                previous_received = received
                received = time.monotonic()
                if not packet or len(packet) > 4096 or len(packet) % 4:
                    raise ValueError("invalid fixed PCM packet")
                self.max_pending = max(self.max_pending, len(packet))
                if received - previous_received >= 0.06:
                    # A full kernel queue can contain only pre-stall audio.
                    # Drain it via latest=True, skip that survivor, then resume
                    # from the next arrival instead of replaying old input.
                    self.stale_dropped += 1
                    continue
                # Half-packet writes leave credit headroom after ordinary timer
                # oversleep, preserving the same 4096 + 192000*t byte envelope.
                # The next tap read replaces queued old audio with fresh data;
                # this optional consumer never makes audible playback wait.
                remaining = memoryview(packet)
                while remaining:
                    chunk = remaining[:2048]
                    while True:
                        now = time.monotonic()
                        if now - self.last_forward >= 5:
                            self.reason = (
                                "pcm-timeout"
                                if now - received >= 5
                                else "backpressure-timeout"
                            )
                            return
                        credit = min(4096.0, credit + (now - last_credit) * 192000)
                        last_credit = now
                        if credit >= len(chunk):
                            break
                        if self.cancelled.wait(
                            max((len(chunk) - credit) / 192000, 1e-6)
                        ):
                            self.reason = "cancelled"
                            return
                    if self.cancelled.is_set():
                        self.reason = "cancelled"
                        return
                    if time.monotonic() - received >= 0.06:
                        self.stale_dropped += 1
                        break
                    credit -= len(chunk)
                    try:
                        count = os.write(self.writer.fileno(), chunk)
                    except BlockingIOError:
                        self.dropped += 1
                        break
                    if count != len(chunk):
                        raise OSError("partial atomic PCM write")
                    self.forwarded += count
                    self.last_forward = time.monotonic()
                    remaining = remaining[count:]
            self.reason = "cancelled"
        except (OSError, ValueError):
            self.reason = "source-ended" if self.tap.closed else "input-error"
        finally:
            try:
                self.writer.close()
            except OSError:
                pass
            self.done.set()

    def stop(self):
        self.cancelled.set()
        self.thread.join(timeout=1)
        self.tap.close()
        if self.thread.is_alive():
            raise RuntimeError("PCM feeder failed to stop")


@lru_cache(maxsize=1)
def _runtime():
    stdlib, python = sandbox._pcm_runtime()
    return stdlib, tuple(
        sorted(set(python) | set(sandbox._runtime_files(sandbox.FFMPEG)))
    )


def _command(directory, plan):
    stdlib, files = plan
    command = sandbox._sandbox_command(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/resampler.py",
        ],
        directory,
        files,
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
        str(WORKER),
        "/run/resampler.py",
    ]
    return command


class PcmSession:
    def __init__(self, process, owner, feed, temporary):
        self.process, self.owner, self.feed, self.temporary = (
            process,
            owner,
            feed,
            temporary,
        )
        self.stopped = False

    def poll(self):
        if self.feed.done.is_set() and self.feed.reason not in {
            "source-ended",
            "cancelled",
        }:
            return 2
        result = self.process.poll()
        # A closed source drains through FFmpeg into the renderer's stdin EOF.
        if result == 0 and self.feed.reason == "source-ended":
            return None
        return 2 if result == 0 else result

    def stop(self):
        if self.stopped:
            return
        errors = []
        for action in (
            self.feed.stop,
            self.owner.stop,
            self.process.stdin.close,
            self.process.stdout.close,
        ):
            try:
                if action() is False:
                    raise RuntimeError("PCM converter cleanup incomplete")
            except Exception as error:
                errors.append(error)
        self.temporary.cleanup()
        self.stopped = not errors
        if errors:
            raise RuntimeError("PCM cleanup failed") from errors[0]


def start(playback, *, work_root=None):
    # Borrow a bounded receiver, never poll/stop the playback from this consumer.
    plan = _runtime()
    temporary = tempfile.TemporaryDirectory(prefix="projectm-pcm-", dir=work_root)
    tap = process = owner = feed = None
    try:
        directory = Path(temporary.name)
        sandbox._prepare_directory(directory)
        tap = playback.open_pcm_tap()
        process = subprocess.Popen(
            sandbox._limited(_command(directory, plan), "pm-feeder"),
            env=sandbox._quota_env(),
            cwd="/",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
            close_fds=True,
        )
        owner = OwnedProcess(process)
        bounded_pipe(process.stdin)
        bounded_pipe(process.stdout)
        feed = PcmFeed(tap, process.stdin)
        return PcmSession(process, owner, feed, temporary)
    except Exception:
        try:
            if feed:
                feed.stop()
            elif tap:
                tap.close()
        finally:
            try:
                if owner:
                    owner.stop()
                elif process:
                    process.kill()
                    process.wait(timeout=2)
            finally:
                if process:
                    process.stdin.close()
                    process.stdout.close()
                temporary.cleanup()
        raise
