"""Crash-persistent diagnostic state, never authority to remove firewall rules.

This user-owned journal contains no firewall backups or rule ownership claims.
An absent/edited journal cannot turn observed emergency rules into verified OFF.
"""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import stat
import time

PHASES = {
    "applying",
    "active",
    "restoring",
    "recovery_required",
    "off_verified",
    "manual_reviewed",
}
PENDING = {"applying", "restoring", "recovery_required", "unreadable"}


class KillswitchJournal:
    def __init__(self, directory=None):
        base = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
        self.directory = (
            Path(directory)
            if directory is not None
            else Path(base) / "netmon" / "killswitch"
        )
        self.legacy_directory = None if directory is not None else Path(base) / "netmon"

    @contextmanager
    def _directory(self, *, create=False):
        path = self.directory
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("Invalid journal path")
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in path.parts[1:]:
                if create:
                    try:
                        os.mkdir(part, 0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                child = os.open(
                    part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
                os.close(fd)
                fd = child
            info = os.fstat(fd)
            if info.st_uid != os.geteuid() or info.st_mode & 0o022:
                raise ValueError("Unsafe journal directory")
            yield fd
        finally:
            os.close(fd)

    def phase(self):
        try:
            with self._directory() as directory:
                fd = os.open(
                    "killswitch-state.json",
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                    dir_fd=directory,
                )
                try:
                    info = os.fstat(fd)
                    if (
                        not stat.S_ISREG(info.st_mode)
                        or info.st_nlink != 1
                        or info.st_uid != os.geteuid()
                        or info.st_mode & 0o077
                        or info.st_size > 4096
                    ):
                        return "unreadable"
                    data = os.read(fd, 4097)
                    after = os.fstat(fd)
                    if (
                        any(
                            getattr(info, key) != getattr(after, key)
                            for key in (
                                "st_dev",
                                "st_ino",
                                "st_size",
                                "st_mtime_ns",
                                "st_ctime_ns",
                            )
                        )
                        or len(data) > 4096
                    ):
                        return "unreadable"
                finally:
                    os.close(fd)
            record = json.loads(data)
            if (
                not isinstance(record, dict)
                or record.get("version") != 1
                or record.get("phase") not in PHASES
            ):
                return "unreadable"
            return record["phase"]
        except FileNotFoundError:
            if self.legacy_directory is not None:
                try:
                    (self.legacy_directory / "killswitch-state.json").lstat()
                except FileNotFoundError:
                    return "absent"
                except OSError:
                    return "unreadable"
                return KillswitchJournal(self.legacy_directory).phase()
            return "absent"
        except (OSError, ValueError, TypeError):
            return "unreadable"

    def mark(self, phase):
        if phase not in PHASES:
            raise ValueError("Invalid journal phase")
        data = json.dumps({"version": 1, "phase": phase, "time": time.time()}).encode()
        with self._directory(create=True) as directory:
            name = ".killswitch-" + secrets.token_hex(16)
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(
                    name,
                    "killswitch-state.json",
                    src_dir_fd=directory,
                    dst_dir_fd=directory,
                )
                os.fsync(directory)
            finally:
                try:
                    os.unlink(name, dir_fd=directory)
                except FileNotFoundError:
                    pass
