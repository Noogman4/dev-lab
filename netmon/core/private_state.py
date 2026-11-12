"""Bounded, owner-only state files in descriptor-validated private directories.

The directory walk and regular-file checks are shared with diagnostic output,
but state is never redacted. Locks serialize cooperating writers and consumers.
"""

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import secrets

from .private_logs import _check_file, _open_file, _private_directory

MAX_STATE_BYTES = 128 * 1024


def _entry(directory, name):
    info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    _check_file(info)
    if info.st_mode & 0o022:
        raise PermissionError("Writable state file")
    return info


def _same_file(first, second):
    return (first.st_dev, first.st_ino) == (second.st_dev, second.st_ino)


def _read_bytes(directory, name, limit):
    expected = _entry(directory, name)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    fd = os.open(name, flags, dir_fd=directory)
    with os.fdopen(fd, "rb") as source:
        actual = os.fstat(source.fileno())
        _check_file(actual)
        if not _same_file(expected, actual) or actual.st_size > limit:
            raise PermissionError("Changed or oversized state file")
        content = source.read(limit + 1)
        if len(content) > limit:
            raise ValueError("Oversized state file")
    return content, expected


@contextmanager
def _lock(directory, name):
    try:
        fd = _open_file(directory, name, "a")
    except FileExistsError:
        # Another cooperating process created the missing lock first.
        fd = _open_file(directory, name, "a")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


@contextmanager
def private_state_lock(path):
    """Lock a checked owner-only file without following its name as a link."""
    path = Path(path)
    with _private_directory(path.parent) as directory:
        with _lock(directory, path.name):
            yield


@contextmanager
def _state_directory(path):
    path = Path(path)
    with _private_directory(path.parent) as directory:
        with _lock(directory, f".{path.name}.lock"):
            yield directory, path.name


def _read_json(directory, name):
    content, info = _read_bytes(directory, name, MAX_STATE_BYTES)
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("State must be a JSON object")
    return payload, info


def read_private_json(path, *, consume_if=None):
    """Read bounded JSON; optionally validate and remove the same locked entry."""
    with _state_directory(path) as (directory, name):
        payload, expected = _read_json(directory, name)
        if consume_if is not None:
            if not consume_if(payload):
                return None
            if not _same_file(expected, _entry(directory, name)):
                raise PermissionError("State changed before consumption")
            os.unlink(name, dir_fd=directory)
        return payload


def write_private_json(path, payload):
    """Publish complete JSON atomically, refusing unsafe existing entries."""
    content = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(content) > MAX_STATE_BYTES:
        raise ValueError("Oversized state file")
    with _state_directory(path) as (directory, name):
        try:
            expected = _entry(directory, name)
        except FileNotFoundError:
            expected = None
        temporary = f".netmon-state-{secrets.token_hex(16)}.tmp"
        fd = _open_file(directory, temporary, "x")
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            try:
                current = _entry(directory, name)
            except FileNotFoundError:
                current = None
            if (expected is None) != (current is None) or (
                expected is not None and not _same_file(expected, current)
            ):
                raise PermissionError("State changed before publication")
            os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass


def remove_private_state(path, *, remove_if=None):
    """Remove a checked entry, optionally matching its bounded JSON first."""
    with _state_directory(path) as (directory, name):
        try:
            expected = _entry(directory, name)
        except FileNotFoundError:
            return True
        if remove_if is not None:
            payload, expected = _read_json(directory, name)
            if not remove_if(payload):
                return False
        if not _same_file(expected, _entry(directory, name)):
            raise PermissionError("State changed before removal")
        os.unlink(name, dir_fd=directory)
        return True


def private_state_key(path, *, create=False):
    """Load/create a private 256-bit authentication key shared by radio peers."""
    with _state_directory(path) as (directory, name):
        try:
            content, info = _read_bytes(directory, name, 32)
        except FileNotFoundError:
            if not create:
                raise
            content = secrets.token_bytes(32)
            fd = _open_file(directory, name, "x")
            with os.fdopen(fd, "wb") as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            return content
        if len(content) != 32 or info.st_mode & 0o077:
            raise PermissionError("Unsafe state authentication key")
        return content
