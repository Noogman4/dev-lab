"""Bound ClamAV pipe reads, retained diagnostics and process-group lifetime."""

from collections import deque
from dataclasses import dataclass
import math
import os
import selectors
import signal
import subprocess
import time

MAX_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_LINE_BYTES = 16 * 1024
MAX_FINDINGS = 300
TAIL_BYTES = 64 * 1024
READ_BYTES = 16 * 1024
POLL_SECONDS = 0.05
TERM_GRACE_SECONDS = 0.2
KILL_WAIT_SECONDS = 1.0
LIMIT_RETURN_CODE = 125


@dataclass(frozen=True)
class ScanResult:
    returncode: int
    output: str
    cancelled: bool
    timed_out: bool
    scanned: int


class _OutputLimit(ValueError):
    pass


class _Output:
    def __init__(self):
        self.pending = bytearray()
        self.findings = []
        self.tail = deque()
        self.tail_size = 0
        self.total = 0
        self.scanned = 0

    def _line(self, line):
        text = line.strip()
        if text.endswith((b" OK", b" FOUND")):
            self.scanned += 1
        if text.endswith(b" FOUND"):
            if len(self.findings) >= MAX_FINDINGS:
                raise _OutputLimit("finding count")
            self.findings.append(line + b"\n")
        else:
            self.tail.append(line + b"\n")
            self.tail_size += len(line) + 1
            while self.tail_size > TAIL_BYTES:
                self.tail_size -= len(self.tail.popleft())

    def feed(self, data):
        self.total += len(data)
        if self.total > MAX_OUTPUT_BYTES:
            raise _OutputLimit("output bytes")
        for index, part in enumerate(data.split(b"\n")):
            if index:
                self._line(bytes(self.pending).rstrip(b"\r"))
                self.pending.clear()
            if len(self.pending) + len(part) > MAX_LINE_BYTES:
                raise _OutputLimit("line length")
            self.pending.extend(part)

    def finish(self):
        if self.pending:
            self._line(bytes(self.pending).rstrip(b"\r"))
            self.pending.clear()

    def text(self, failure=""):
        value = b"".join(self.findings) + b"".join(self.tail)
        return value.decode("utf-8", errors="replace") + failure


def _signal_group(process, number):
    try:
        os.killpg(process.pid, number)
    except ProcessLookupError:
        pass


def _stop_group(process):
    # The leader may already have exited while a descendant still holds stdout.
    # Always address the owned session's group, not only process.poll() == None.
    _signal_group(process, signal.SIGTERM)
    end = time.monotonic() + TERM_GRACE_SECONDS
    while time.monotonic() < end:
        process.poll()
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            break
        time.sleep(min(POLL_SECONDS, max(0, end - time.monotonic())))
    _signal_group(process, signal.SIGKILL)
    process.wait(timeout=KILL_WAIT_SECONDS)


def run_scan(command, *, timeout, cancelled, started, progress=None):
    timeout = float(timeout)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Invalid ClamAV scan deadline")
    deadline = time.monotonic() + timeout
    output = _Output()
    was_cancelled = timed_out = False
    failure = ""
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=False,
        bufsize=0,
    )
    try:
        started(process)
        os.set_blocking(process.stdout.fileno(), False)
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            eof = False
            last_progress = 0
            next_progress = 0.0
            while True:
                if cancelled():
                    was_cancelled = True
                    break
                now = time.monotonic()
                if now >= deadline:
                    timed_out = True
                    break
                if eof and process.poll() is not None:
                    break
                if eof:
                    time.sleep(min(POLL_SECONDS, deadline - now))
                else:
                    for _key, _events in selector.select(
                        min(POLL_SECONDS, deadline - now)
                    ):
                        try:
                            data = os.read(process.stdout.fileno(), READ_BYTES)
                        except BlockingIOError:
                            continue
                        if data:
                            output.feed(data)
                        else:
                            output.finish()
                            selector.unregister(process.stdout)
                            eof = True
                if (
                    progress
                    and output.scanned != last_progress
                    and now >= next_progress
                ):
                    progress(output.scanned)
                    last_progress = output.scanned
                    next_progress = now + 0.25
    except _OutputLimit as exc:
        failure = f"\nClamAV scan incomplete: resource limit exceeded ({exc}).\n"
    finally:
        try:
            _stop_group(process)
        finally:
            process.stdout.close()
    # UI notification must not delay cleanup once a deadline/cancel is observed.
    if progress and output.scanned != last_progress:
        progress(output.scanned)
    rc = process.returncode
    if timed_out:
        rc = 124
    elif was_cancelled:
        rc = -signal.SIGTERM
    elif failure:
        rc = LIMIT_RETURN_CODE
    elif rc < 0:
        was_cancelled = True
    return ScanResult(
        rc, output.text(failure), was_cancelled, timed_out, output.scanned
    )
