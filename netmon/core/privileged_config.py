"""Atomic configuration writer; no user-owned source pathname crosses sudo.

The installed helper is executed in isolated Python mode after the bootstrap
checks its root-owned, non-writable ancestry. Source checkouts fail closed.
"""

import hashlib
import os
import secrets
import stat
import sys
from pathlib import Path

HELPER = "/usr/lib/netmon/netmon/core/privileged_config.py"
MAX_CONTENT = 1024 * 1024
# 0: durable write; 1: rejected/failed before replace; 74: replaced, then failed.
# Timeouts and other process failures do not establish whether replace happened.
WRITE_COMMITTED_ERROR = 74
DESTINATIONS = frozenset(
    {
        "/etc/systemd/resolved.conf.d/netmon-dot.conf",
        "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "/etc/ufw/sysctl.conf",
        "/etc/rkhunter.conf",
    }
)


class CommittedWriteError(OSError):
    """The destination changed, but finalization could not be confirmed."""


# This code runs before importing any installed application code as root.
BOOTSTRAP = r"""
import os, stat, sys
path = "/usr/lib/netmon/netmon/core/privileged_config.py"
current = "/"
try:
    for part in [""] + path.strip("/").split("/"):
        current = os.path.join(current, part)
        info = os.lstat(current)
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError("Unprotected configuration helper")
        if current == path:
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("Unsafe configuration helper")
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError("Unsafe configuration helper directory")
except (OSError, ValueError) as exc:
    sys.exit(str(exc))
os.execv("/usr/bin/python3", ["/usr/bin/python3", "-I", path] + sys.argv[1:])
"""


def write_privileged_config(path, content, *, run_cmd_fn=None, timeout=20):
    """Send the exact reviewed UTF-8 content, bound to its digest, over stdin."""
    if path not in DESTINATIONS:
        return 1, "Nicht erlaubter Konfigurationspfad."
    if not isinstance(content, str):
        return 1, "Ungueltiger Konfigurationsinhalt."
    data = content.encode("utf-8")
    if len(data) > MAX_CONTENT or b"\0" in data:
        return 1, "Ungueltiger Konfigurationsinhalt oder Groessenlimit."
    if run_cmd_fn is None:
        try:
            from netmon.core.command import run_cmd
        except ModuleNotFoundError:
            from core.command import run_cmd
        run_cmd_fn = run_cmd
    return run_cmd_fn(
        [
            "sudo",
            "-n",
            "/usr/bin/python3",
            "-I",
            "-c",
            BOOTSTRAP,
            path,
            hashlib.sha256(data).hexdigest(),
        ],
        input_text=content,
        timeout=timeout,
    )


def _check_directory(fd):
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise ValueError("Unprotected destination directory")


def _destination_directory(path):
    """Anchor every component; never follow a directory link."""
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        _check_directory(directory)
        parts = Path(path).parts[1:-1]
        for index, part in enumerate(parts):
            try:
                child = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
            except FileNotFoundError:
                # Only the dedicated resolved drop-in directory may be created.
                if (
                    path != "/etc/systemd/resolved.conf.d/netmon-dot.conf"
                    or index != len(parts) - 1
                ):
                    raise
                try:
                    os.mkdir(part, mode=0o755, dir_fd=directory)
                except FileExistsError:
                    pass
                child = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
            os.close(directory)
            directory = child
            _check_directory(directory)
        return directory
    except BaseException:
        os.close(directory)
        raise


def _atomic_write(path, data):
    directory = _destination_directory(path)
    staging = ".netmon-config-" + secrets.token_hex(16)
    created = False
    replaced = False
    try:
        try:
            name = Path(path).name
            try:
                info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != 0
                    or info.st_mode & 0o022
                    or info.st_nlink != 1
                ):
                    raise ValueError("Unsafe destination file")
            fd = os.open(
                staging,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            created = True
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fchown(handle.fileno(), 0, 0)
                os.fchmod(handle.fileno(), 0o644)
                os.fsync(handle.fileno())
            os.replace(staging, name, src_dir_fd=directory, dst_dir_fd=directory)
            replaced = True
            created = False
            os.fsync(directory)
        finally:
            try:
                if created:
                    os.unlink(staging, dir_fd=directory)
            finally:
                os.close(directory)
    except OSError as exc:
        if replaced:
            raise CommittedWriteError(
                f"Destination replaced; finalization failed: {exc}"
            ) from exc
        raise


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        if os.geteuid() != 0 or os.path.abspath(__file__) != HELPER:
            raise ValueError("Protected installed root helper required")
        if len(arguments) != 2 or arguments[0] not in DESTINATIONS:
            raise ValueError("Destination not allowed")
        data = sys.stdin.buffer.read(MAX_CONTENT + 1)
        data.decode("utf-8", errors="strict")
        if (
            len(data) > MAX_CONTENT
            or b"\0" in data
            or hashlib.sha256(data).hexdigest() != arguments[1]
        ):
            raise ValueError("Invalid configuration payload or digest")
        _atomic_write(arguments[0], data)
        return 0
    except CommittedWriteError as exc:
        print(str(exc), file=sys.stderr)
        return WRITE_COMMITTED_ERROR
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
