"""Track only a launched child and proven descendants with Linux pidfds.

This is process ownership, not a sandbox. Children that escape the observed
tree still require containment by the future visualizer sandbox.
"""

import os
from pathlib import Path
import select
import signal
import subprocess
import threading
import time


def available():
    return hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal")


def _parent(pid):
    try:
        data = Path(f"/proc/{int(pid)}/stat").read_text()
        return int(data[data.rindex(")") + 2 :].split()[1])
    except (OSError, ValueError, IndexError):
        return None


def _descends_from(pid, root):
    seen = set()
    while pid and pid != root and pid not in seen:
        seen.add(pid)
        pid = _parent(pid)
    return pid == root


class OwnedProcess:
    """Never signal a PID number, a process-name match, or a Flatpak app ID."""

    def __init__(self, process):
        self.process = process
        self.pid = process.pid
        self._handles = {}
        self._lock = threading.RLock()
        try:
            descriptor = os.pidfd_open(self.pid)
        except ProcessLookupError:
            process.wait(timeout=1)
        else:
            # poll may already have reaped a fast child. An opened replacement
            # PID must never acquire ownership through a stale Popen object.
            if process.poll() is None:
                self._handles[self.pid] = descriptor
            else:
                os.close(descriptor)
        try:
            self.capture_descendants()
        except Exception:
            self._close()
            raise

    def _alive(self, descriptor):
        return not select.select([descriptor], [], [], 0)[0]

    @property
    def returncode(self):
        return self.process.returncode

    def capture_descendants(self):
        with self._lock:
            root = self._handles.get(self.pid)
            if root is None or not self._alive(root):
                return
            for item in Path("/proc").iterdir():
                if not item.name.isdecimal():
                    continue
                pid = int(item.name)
                if pid in self._handles or not _descends_from(pid, self.pid):
                    continue
                try:
                    descriptor = os.pidfd_open(pid)
                except ProcessLookupError:
                    continue
                # Recheck ancestry after opening. A pidfd continues to refer to
                # that task even if it exits and the PID number is reused.
                if self._alive(root) and _descends_from(pid, self.pid):
                    self._handles[pid] = descriptor
                else:
                    os.close(descriptor)

    @property
    def pids(self):
        with self._lock:
            return {pid for pid, fd in self._handles.items() if self._alive(fd)}

    def _close(self):
        for descriptor in self._handles.values():
            os.close(descriptor)
        self._handles.clear()

    def poll(self):
        with self._lock:
            code = self.process.poll()
            if code is None or self.pids:
                return None
            self._close()
            return code

    def _signal(self, sig):
        # Signal the launcher last, retaining ancestry during initial capture.
        order = sorted(self._handles, key=lambda pid: pid == self.pid)
        for pid in order:
            descriptor = self._handles[pid]
            if self._alive(descriptor):
                try:
                    signal.pidfd_send_signal(descriptor, sig)
                except OSError:
                    # Keep ownership for a retry when the task is still alive.
                    pass

    def _wait(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = [fd for fd in self._handles.values() if self._alive(fd)]
            if not remaining:
                return True
            delay = deadline - time.monotonic()
            if delay <= 0:
                return False
            select.select(remaining, [], [], min(delay, 0.05))

    def stop(self):
        with self._lock:
            self.capture_descendants()
            self._signal(signal.SIGTERM)
            if not self._wait(2):
                self._signal(signal.SIGKILL)
            stopped = self._wait(1)
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                stopped = False
            if stopped:
                self._close()
            return stopped
