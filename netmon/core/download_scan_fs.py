"""No-follow download imports and release of the exact file supplied to ClamAV."""

from __future__ import annotations

from dataclasses import dataclass
import os
import secrets
import shutil
import stat
import unicodedata

from . import quarantine_fs as qfs

UnsafePath = qfs.UnsafePath
is_within = qfs.is_within
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
_WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
_CHUNK = 1024 * 1024


def validate_scan_path(path):
    """Reject names that can add records to line-oriented scanner/UI output."""
    text = os.fsdecode(path)
    if any(unicodedata.category(char) in {"Cc", "Zl", "Zp"} for char in text):
        raise UnsafePath("Scan-Pfad enthält unzulässige Steuerzeichen")


def _identity(entry):
    # ctime cannot be reset with utime after an in-place edit or rename.
    return (
        entry.st_dev,
        entry.st_ino,
        entry.st_size,
        entry.st_mtime_ns,
        entry.st_ctime_ns,
        entry.st_nlink,
    )


@dataclass
class ScanFile:
    fd: int
    parent: int
    name: str
    identity: tuple
    path: str

    def verify(self):
        try:
            current = os.stat(self.name, dir_fd=self.parent, follow_symlinks=False)
            if (
                _identity(os.fstat(self.fd)) != self.identity
                or _identity(current) != self.identity
                or not stat.S_ISREG(current.st_mode)
            ):
                raise UnsafePath("Datei hat sich seit Scan-Beginn geändert")
        except OSError as exc:
            raise UnsafePath("Scan-Datei wurde entfernt oder ausgetauscht") from exc

    def close(self):
        os.close(self.fd)
        os.close(self.parent)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()


def open_scan_file(path):
    validate_scan_path(path)
    parent_path, name = os.path.split(path)
    qfs.plain_name(name)
    parent = qfs.open_directory(parent_path)
    descriptor = None
    try:
        descriptor = os.open(name, _READ_FLAGS, dir_fd=parent)
        entry = os.fstat(descriptor)
        if not stat.S_ISREG(entry.st_mode) or entry.st_nlink != 1:
            raise UnsafePath("Scan-Quelle muss eine reguläre Datei ohne Hardlinks sein")
        result = ScanFile(descriptor, parent, name, _identity(entry), os.fsdecode(path))
        result.verify()
        return result
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        os.close(parent)
        raise


def prepare_directory(path):
    validate_scan_path(path)
    descriptor = qfs.open_directory(path, create=True, private=True)
    os.close(descriptor)


def _listing(directory):
    # O_PATH descriptors cannot be listed; reopen "." read-only through it.
    readable = os.open(
        ".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=directory
    )
    try:
        return sorted(os.listdir(readable))
    finally:
        os.close(readable)


def list_directory(path):
    """Entry names of the private pre-quarantine, checked like prepare_directory."""
    validate_scan_path(path)
    descriptor = qfs.open_directory(path, private=True)
    try:
        return _listing(descriptor)
    finally:
        os.close(descriptor)


def clear_directory(path, names=None):
    """Delete entries of the private pre-quarantine without following links.

    The directory must pass the same no-follow ownership and mode checks as
    prepare_directory. Removal happens relative to that descriptor, so a
    swapped path or a planted symlink cannot redirect deletion elsewhere.
    With ``names`` only those confirmed entries are removed.
    """
    validate_scan_path(path)
    descriptor = qfs.open_directory(path, private=True)
    removed, errors = 0, []
    try:
        present = _listing(descriptor)
        confirmed = None if names is None else set(names)
        wanted = [n for n in present if confirmed is None or n in confirmed]
        for name in wanted:
            try:
                entry = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISDIR(entry.st_mode):
                    shutil.rmtree(name, dir_fd=descriptor)
                else:
                    os.unlink(name, dir_fd=descriptor)
                removed += 1
            except OSError as exc:
                errors.append((name, exc))
    finally:
        os.close(descriptor)
    return removed, errors


def write_report(directory, name, text):
    """Create a new owner-only report; never follow or replace an existing name."""
    validate_scan_path(directory)
    descriptor = qfs.open_directory(directory, create=True)
    try:
        entry = os.fstat(descriptor)
        if entry.st_uid != os.getuid() or stat.S_IMODE(entry.st_mode) & 0o077:
            raise UnsafePath(f"Berichtsordner nicht privat: {directory}")
        data = (str(text or "").rstrip() + "\n").encode("utf-8")
        for candidate in _names(name):
            try:
                output = os.open(candidate, _WRITE_FLAGS, 0o600, dir_fd=descriptor)
            except FileExistsError:
                continue
            try:
                view = memoryview(data)
                while view:
                    view = view[os.write(output, view) :]
            finally:
                os.close(output)
            return os.path.join(directory, candidate)
        raise UnsafePath("kein freier Name im Berichtsordner")
    finally:
        os.close(descriptor)


def _names(name):
    qfs.plain_name(name)
    yield name
    stem, ext = os.path.splitext(name)
    for index in range(1, 10000):
        yield f"{stem}_{index}{ext}"


def _copy(source, destination):
    os.lseek(source, 0, os.SEEK_SET)
    while chunk := os.read(source, _CHUNK):
        view = memoryview(chunk)
        while view:
            view = view[os.write(destination, view) :]
    os.fsync(destination)


def suggest_destination(source_path, target_dir):
    validate_scan_path(source_path)
    validate_scan_path(target_dir)
    target = qfs.open_directory(target_dir, create=True)
    try:
        for name in _names(os.path.basename(source_path)):
            try:
                os.stat(name, dir_fd=target, follow_symlinks=False)
            except FileNotFoundError:
                return os.path.join(target_dir, name)
        raise UnsafePath("kein freier Dateiname im Download-Zielordner")
    finally:
        os.close(target)


def import_file(source_path, temporary_dir):
    validate_scan_path(source_path)
    validate_scan_path(temporary_dir)
    target = qfs.open_directory(temporary_dir, create=True, private=True)
    try:
        with open_scan_file(source_path) as source:
            if qfs.is_within(source_path, temporary_dir):
                return source_path, ""
            for name in _names(source.name):
                try:
                    output = os.open(name, _WRITE_FLAGS, 0o600, dir_fd=target)
                except FileExistsError:
                    continue
                try:
                    _copy(source.fd, output)
                    source.verify()
                except BaseException:
                    os.unlink(name, dir_fd=target)
                    raise
                finally:
                    os.close(output)
                return os.path.join(temporary_dir, name), source_path
            raise UnsafePath("kein freier Dateiname in der Vor-Quarantäne")
    finally:
        os.close(target)


def release_file(source, target_dir):
    """Copy from the scanned FD; publish exclusively only after revalidation."""
    validate_scan_path(target_dir)
    source.verify()
    target = qfs.open_directory(target_dir, create=True)
    temporary = f".netmon-release-{secrets.token_hex(16)}"
    output = None
    try:
        output = os.open(temporary, _WRITE_FLAGS, 0o600, dir_fd=target)
        _copy(source.fd, output)
        source.verify()
        for name in _names(source.name):
            try:
                # Link the opened output inode, not its mutable temporary name.
                # The kernel-owned proc FD link cannot be redirected by a peer
                # in a shared target directory. No-overwrite remains atomic.
                os.link(
                    f"/proc/self/fd/{output}",
                    name,
                    dst_dir_fd=target,
                    follow_symlinks=True,
                )
            except FileExistsError:
                continue
            try:
                source.verify()
            except BaseException:
                _unlink_output(target, name, output)
                raise
            os.unlink(source.name, dir_fd=source.parent)
            return os.path.join(target_dir, name)
        raise UnsafePath("kein freier Dateiname im Download-Zielordner")
    finally:
        try:
            if output is not None:
                _unlink_output(target, temporary, output)
        finally:
            if output is not None:
                os.close(output)
            os.close(target)


def _unlink_output(directory, name, descriptor):
    try:
        entry = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return
    opened = os.fstat(descriptor)
    if (entry.st_dev, entry.st_ino) == (opened.st_dev, opened.st_ino):
        os.unlink(name, dir_fd=directory)
