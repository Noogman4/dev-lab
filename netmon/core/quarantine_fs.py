"""Descriptor-anchored quarantine moves bound to the scanned file identity.

ClamAV findings are acted on long after the scan. Paths are therefore never
re-resolved: every component is opened from ``/`` without following links,
the leaf must still be the regular file recorded at scan time, and moves use
``renameat``/``linkat`` relative to the retained directory descriptors.
"""

from __future__ import annotations

import errno
import os
import stat

_DIR_FLAGS = os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_COPY_ERRNOS = {errno.EXDEV, errno.EPERM, errno.EMLINK, errno.EOPNOTSUPP}
_IDENTITY_KEYS = ("dev", "ino", "size", "mtime_ns")
_CHUNK = 1024 * 1024


class UnsafePath(Exception):
    """The object or a path component is not the one NetMon may touch."""


def file_identity(entry: os.stat_result) -> dict:
    return {
        "dev": entry.st_dev,
        "ino": entry.st_ino,
        "size": entry.st_size,
        "mtime_ns": entry.st_mtime_ns,
    }


def directory_identity(entry: os.stat_result) -> dict:
    return {"dev": entry.st_dev, "ino": entry.st_ino}


def clean_identity(value, keys=_IDENTITY_KEYS):
    """Return a validated identity dict from persisted data, else None."""
    if not isinstance(value, dict):
        return None
    cleaned = {}
    for key in keys:
        item = value.get(key)
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            return None
        cleaned[key] = item
    return cleaned


def record_identity(path: str):
    """Identity of a regular file at scan time, without following links."""
    try:
        entry = os.lstat(path)
    except OSError:
        return None
    if not stat.S_ISREG(entry.st_mode):
        return None
    return file_identity(entry)


def _components(path: str) -> list[str]:
    text = str(path or "")
    if not os.path.isabs(text) or "\0" in text:
        raise UnsafePath(f"kein absoluter Pfad: {text!r}")
    parts = [part for part in text.split("/") if part]
    if any(part in {".", ".."} for part in parts):
        raise UnsafePath(f"unzulässiger Pfad: {text!r}")
    return parts


def plain_name(name: str) -> str:
    if not name or name in {".", ".."} or "/" in name or "\0" in name:
        raise UnsafePath(f"unzulässiger Dateiname: {name!r}")
    return name


def is_within(path: str, root: str) -> bool:
    """Lexical containment; the no-follow walk makes it authoritative."""
    path_parts, root_parts = _components(path), _components(root)
    return path_parts[: len(root_parts)] == root_parts


def open_directory(path: str, *, create: bool = False) -> int:
    """Open a directory from ``/`` without following any symlink."""
    fd = os.open("/", _DIR_FLAGS)
    try:
        for part in _components(path):
            try:
                child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            except OSError as exc:
                if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
                    raise UnsafePath(f"Symlink oder kein Ordner: {part}") from exc
                raise
            os.close(fd)
            fd = child
            if not stat.S_ISDIR(os.fstat(fd).st_mode):
                raise UnsafePath(f"kein Ordner: {part}")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _private_directory(path: str) -> int:
    fd = open_directory(path, create=True)
    entry = os.fstat(fd)
    if entry.st_uid != os.getuid() or stat.S_IMODE(entry.st_mode) & 0o077:
        os.close(fd)
        raise UnsafePath(f"Quarantäne-Ordner nicht privat: {path}")
    return fd


def _leaf(dir_fd: int, name: str) -> os.stat_result:
    try:
        return os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise UnsafePath(f"{name}: {exc.strerror or exc}") from exc


def _exists(dir_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _same_object(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _copy_exclusive(src_fd, src_name, expected, dst_fd, dst_name, mode):
    """Copy the expected object into a newly created file, then unlink it."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    source = os.open(src_name, flags, dir_fd=src_fd)
    try:
        opened = os.fstat(source)
        if not stat.S_ISREG(opened.st_mode) or not _same_object(opened, expected):
            raise UnsafePath(f"{src_name}: Datei hat sich geändert")
        target = os.open(
            dst_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            mode,
            dir_fd=dst_fd,
        )
        try:
            while True:
                chunk = os.read(source, _CHUNK)
                if not chunk:
                    break
                view = memoryview(chunk)
                while view:
                    view = view[os.write(target, view) :]
            os.fsync(target)
        except BaseException:
            os.close(target)
            os.unlink(dst_name, dir_fd=dst_fd)
            raise
        os.close(target)
    finally:
        os.close(source)
    # Remove the source name only while it still names the copied object.
    if _same_object(_leaf(src_fd, src_name), expected):
        os.unlink(src_name, dir_fd=src_fd)
    else:
        raise UnsafePath(f"{src_name}: Datei hat sich während der Kopie geändert")


def quarantine_file(source_path, quarantine_dir, dest_name, identity=None):
    """Move exactly the scanned file into the private quarantine directory.

    Returns ``(quarantine_path, origin_directory_identity)``.
    """
    plain_name(dest_name)
    parent_path, name = os.path.split(os.path.normpath(source_path))
    plain_name(name)
    parent = open_directory(parent_path)
    try:
        entry = _leaf(parent, name)
        if not stat.S_ISREG(entry.st_mode):
            raise UnsafePath(f"{source_path}: keine reguläre Datei")
        if entry.st_nlink != 1:
            raise UnsafePath(f"{source_path}: Datei hat mehrere Hardlinks")
        if identity is not None and file_identity(entry) != identity:
            raise UnsafePath(f"{source_path}: Datei hat sich seit dem Scan geändert")
        origin = directory_identity(os.fstat(parent))
        quarantine = _private_directory(quarantine_dir)
        try:
            if _exists(quarantine, dest_name):
                raise UnsafePath(f"Quarantäne-Ziel existiert bereits: {dest_name}")
            try:
                os.rename(name, dest_name, src_dir_fd=parent, dst_dir_fd=quarantine)
            except OSError as exc:
                if exc.errno not in _COPY_ERRNOS:
                    raise
                _copy_exclusive(parent, name, entry, quarantine, dest_name, 0o600)
            else:
                # renameat moves the entry, never a link target. If the name was
                # swapped meanwhile, the substitute stays quarantined.
                if not _same_object(_leaf(quarantine, dest_name), entry):
                    raise UnsafePath(f"{source_path}: Datei wurde ausgetauscht")
        finally:
            os.close(quarantine)
    finally:
        os.close(parent)
    return os.path.join(quarantine_dir, dest_name), origin


def _restore_names(name: str, stamp: str):
    yield name
    stem, ext = os.path.splitext(name)
    yield f"{stem}__restored__{stamp}{ext}"
    for index in range(1, 1000):
        yield f"{stem}__restored__{stamp}_{index}{ext}"


def restore_file(
    quarantine_path,
    quarantine_dir,
    original_path,
    *,
    home_root,
    fallback_dir,
    origin=None,
    stamp="restored",
):
    """Restore without overwriting, anchored to a no-follow directory walk.

    Falls back to ``fallback_dir`` when the original directory is outside
    the home, now contains a link, or is no longer the directory recorded at
    quarantine time. Returns ``(restored_path, used_fallback)``.
    """
    q_parent, q_name = os.path.split(os.path.normpath(quarantine_path))
    if os.path.normpath(q_parent) != os.path.normpath(quarantine_dir):
        raise UnsafePath(f"außerhalb des Quarantäne-Ordners: {quarantine_path}")
    plain_name(q_name)
    original_dir, name = os.path.split(os.path.normpath(original_path))
    plain_name(name)
    if not is_within(fallback_dir, home_root):
        raise UnsafePath(f"Ersatzordner außerhalb des Home: {fallback_dir}")

    quarantine = _private_directory(quarantine_dir)
    try:
        entry = _leaf(quarantine, q_name)
        if not stat.S_ISREG(entry.st_mode):
            raise UnsafePath(f"{quarantine_path}: keine reguläre Datei")
        target, target_path, used_fallback = None, original_dir, False
        if is_within(original_dir, home_root):
            try:
                target = open_directory(original_dir, create=True)
                if (
                    origin is not None
                    and directory_identity(os.fstat(target)) != origin
                ):
                    os.close(target)
                    target = None
            except (UnsafePath, OSError):
                target = None
        if target is None:
            target = open_directory(fallback_dir, create=True)
            target_path, used_fallback = fallback_dir, True
        try:
            for candidate in _restore_names(name, stamp):
                if _exists(target, candidate):
                    continue
                try:
                    os.link(
                        q_name,
                        candidate,
                        src_dir_fd=quarantine,
                        dst_dir_fd=target,
                        follow_symlinks=False,
                    )
                except FileExistsError:
                    continue
                except OSError as exc:
                    if exc.errno not in _COPY_ERRNOS:
                        raise
                    try:
                        _copy_exclusive(
                            quarantine, q_name, entry, target, candidate, 0o600
                        )
                    except FileExistsError:
                        continue
                else:
                    if not _same_object(_leaf(target, candidate), entry):
                        raise UnsafePath(f"{quarantine_path}: Datei wurde ausgetauscht")
                    os.unlink(q_name, dir_fd=quarantine)
                return os.path.join(target_path, candidate), used_fallback
            raise UnsafePath(f"kein freier Zielname für {name}")
        finally:
            os.close(target)
    finally:
        os.close(quarantine)
