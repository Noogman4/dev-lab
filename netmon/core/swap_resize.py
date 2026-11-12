"""Root-side swap file resize pinned to verified descriptors.

The previous resize ran ``swapoff``/``rm``/``fallocate``/``dd of=``/``chmod``/
``mkswap``/``swapon`` as separate root commands on a pathname. If any parent
directory of the swap file was writable by a non-root user, that pathname could
be replaced by a symlink between two commands and root would write through it.

This module runs as one root process (``sudo -n /usr/bin/python3 -I -c``) and:

* accepts only an active, canonical swap file path from ``/proc/swaps``,
* opens every ancestor relative to its already verified parent with
  ``O_NOFOLLOW`` and requires root ownership without group/other write access,
  so only root could replace any component,
* keeps the parent directory descriptor open for the whole operation; all
  later steps (unlink, exclusive create, allocate, mkswap, swapon, swapoff)
  address the file through that descriptor or the file's own descriptor via
  ``/proc/self/fd`` and never re-resolve the pathname.

It depends on the standard library only, because its source text is executed
by an isolated root interpreter.
"""

import ctypes
import errno
import os
import stat
import subprocess
import sys

MIN_GIB = 1
MAX_GIB = 64
GIB_BYTES = 1024**3
_ROOT_UID = 0
PROC_SWAPS = "/proc/swaps"
MKSWAP = "/usr/sbin/mkswap"
_FORBIDDEN_ROOTS = {"dev", "proc", "sys"}
_ZERO_CHUNK = 1024 * 1024
_DIR_FLAGS = os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC


class SwapResizeError(RuntimeError):
    pass


def validate_path(path):
    """Return the components of a canonical absolute swap file path."""
    if (
        not isinstance(path, str)
        or not path.startswith("/")
        or len(path) > 4096
        or any(ord(c) < 32 or ord(c) == 127 for c in path)
    ):
        raise SwapResizeError("Ungültiger Swapdatei-Pfad.")
    parts = path.split("/")[1:]
    if (
        len(parts) < 1
        or any(p in {"", ".", ".."} for p in parts)
        or parts[0] in _FORBIDDEN_ROOTS
    ):
        raise SwapResizeError("Nicht kanonischer Swapdatei-Pfad.")
    return parts


def validate_gib(value):
    try:
        gib = int(str(value), 10)
    except ValueError as exc:
        raise SwapResizeError("Ungültige Swap-Größe.") from exc
    if not MIN_GIB <= gib <= MAX_GIB or str(gib) != str(value):
        raise SwapResizeError("Swap-Größe außerhalb des erlaubten Bereichs.")
    return gib


def _check_trusted_directory(info):
    if not stat.S_ISDIR(info.st_mode):
        raise SwapResizeError("Swapdatei-Vorfahr ist kein Verzeichnis.")
    if info.st_uid != _ROOT_UID or info.st_mode & 0o022:
        raise SwapResizeError(
            "Swapdatei liegt in einem Verzeichnis, das nicht ausschließlich root "
            "gehört oder für andere beschreibbar ist."
        )


def check_swap_file(info):
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != _ROOT_UID
        or info.st_mode & 0o077
        or info.st_nlink != 1
    ):
        raise SwapResizeError(
            "Swapdatei ist keine root-eigene, private, einfach verlinkte Datei."
        )


def open_trusted_parent(path):
    """Return (directory fd, basename); every ancestor is root-only writable."""
    parts = validate_path(path)
    fd = os.open("/", _DIR_FLAGS)
    try:
        _check_trusted_directory(os.fstat(fd))
        for component in parts[:-1]:
            child = os.open(component, _DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
            _check_trusted_directory(os.fstat(fd))
    except BaseException:
        os.close(fd)
        raise
    return fd, parts[-1]


def precheck(path):
    """Unprivileged early refusal; the root process repeats every check.

    Only definite violations are reported. Ancestors the user cannot search
    are left for the root process to judge.
    """
    try:
        dir_fd, name = open_trusted_parent(path)
    except PermissionError:
        return
    try:
        check_swap_file(os.stat(name, dir_fd=dir_fd, follow_symlinks=False))
    except PermissionError:
        pass
    finally:
        os.close(dir_fd)


def _unescape(value):
    out = []
    index = 0
    while index < len(value):
        chunk = value[index : index + 4]
        if (
            len(chunk) == 4
            and chunk[0] == "\\"
            and all(c in "01234567" for c in chunk[1:])
        ):
            out.append(chr(int(chunk[1:], 8)))
            index += 4
        else:
            out.append(value[index])
            index += 1
    return "".join(out)


def active_swap_files(proc_swaps=PROC_SWAPS):
    with open(proc_swaps, "r", encoding="utf-8") as stream:
        lines = stream.read(1024 * 1024).splitlines()
    if not lines or lines[0].split()[:2] != ["Filename", "Type"]:
        raise SwapResizeError("Kernel-Swaptabelle ist nicht lesbar.")
    result = set()
    for line in lines[1:]:
        fields = line.split()
        if len(fields) >= 2 and fields[1] == "file":
            result.add(_unescape(fields[0]))
    return result


def _libc():
    libc = ctypes.CDLL(None, use_errno=True)
    for name in ("swapon", "swapoff"):
        getattr(libc, name).argtypes = (
            [ctypes.c_char_p, ctypes.c_int] if name == "swapon" else [ctypes.c_char_p]
        )
        getattr(libc, name).restype = ctypes.c_int
    return libc


def _fd_path(fd):
    return f"/proc/self/fd/{int(fd)}"


def _swap_call(function, fd, *args):
    if function(os.fsencode(_fd_path(fd)), *args) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def _trusted_tool(path):
    current = "/"
    for component in path.strip("/").split("/"):
        current = os.path.join(current, component)
        info = os.lstat(current)
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise SwapResizeError(f"Unsicherer Systempfad: {current}")
        if current != path and not stat.S_ISDIR(info.st_mode):
            raise SwapResizeError(f"Unsicherer Systempfad: {current}")
    if not stat.S_ISREG(info.st_mode):
        raise SwapResizeError(f"Unsicheres Systemwerkzeug: {path}")
    return path


def _allocate(fd, size):
    try:
        os.posix_fallocate(fd, 0, size)
        return
    except OSError as exc:
        if exc.errno not in {errno.EOPNOTSUPP, errno.EINVAL, errno.ENOSYS}:
            raise
    os.lseek(fd, 0, os.SEEK_SET)
    zeros = bytes(_ZERO_CHUNK)
    remaining = size
    while remaining:
        view = memoryview(zeros)[: min(remaining, _ZERO_CHUNK)]
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(errno.EIO, "Swapdatei konnte nicht beschrieben werden")
            view = view[written:]
            remaining -= written


def resize(path, gib, *, libc=None, run=subprocess.run, proc_swaps=PROC_SWAPS):
    """Recreate the active swap file at path with gib GiB. Runs as root."""
    gib = validate_gib(gib)
    validate_path(path)
    if path not in active_swap_files(proc_swaps):
        raise SwapResizeError("Pfad ist keine aktive Swapdatei.")
    mkswap = _trusted_tool(MKSWAP)
    libc = libc if libc is not None else _libc()
    size = gib * GIB_BYTES

    dir_fd, name = open_trusted_parent(path)
    try:
        before = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
        check_swap_file(before)
        old_fd = os.open(name, _FILE_FLAGS, dir_fd=dir_fd)
        try:
            opened = os.fstat(old_fd)
            check_swap_file(opened)
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise SwapResizeError(
                    "Swapdatei hat sich während der Prüfung geändert."
                )
            _swap_call(libc.swapoff, old_fd)
        finally:
            os.close(old_fd)

        # From here on swap is off; errors leave it off and say so.
        created_new = False
        try:
            os.unlink(name, dir_fd=dir_fd)
            new_fd = os.open(
                name, _FILE_FLAGS | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=dir_fd
            )
            created_new = True
            try:
                os.fchmod(new_fd, 0o600)
                _allocate(new_fd, size)
                os.fsync(new_fd)
                created = os.fstat(new_fd)
                check_swap_file(created)
                result = run(
                    [mkswap, f"/dev/fd/{new_fd}"],
                    pass_fds=(new_fd,),
                    env={"PATH": "/usr/sbin:/usr/bin", "LC_ALL": "C"},
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if result.returncode != 0:
                    raise SwapResizeError(
                        "mkswap fehlgeschlagen: "
                        + (result.stderr or result.stdout or "").strip()[:500]
                    )
                _swap_call(libc.swapon, new_fd, 0)
                created_new = False  # active now: never remove it below
            finally:
                os.close(new_fd)
        except Exception as exc:
            if created_new:
                # Do not leave an incomplete file that fstab would try to use.
                try:
                    os.unlink(name, dir_fd=dir_fd)
                except OSError:
                    pass
            raise SwapResizeError(
                f"Swap ist deaktiviert, Neuanlage fehlgeschlagen: {exc}"
            ) from exc
    finally:
        os.close(dir_fd)

    if path not in active_swap_files(proc_swaps):
        raise SwapResizeError("Neue Swapdatei ist nicht als aktiv bestätigt.")
    return size


def main(argv):
    if len(argv) != 3 or argv[0] != "resize":
        print("Aufruf: resize <pfad> <GiB>", file=sys.stderr)
        return 2
    if os.geteuid() != 0:
        print("Swap-Resize muss als root laufen.", file=sys.stderr)
        return 2
    try:
        resize(argv[1], argv[2])
    except (SwapResizeError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("OK")
    return 0


def root_command(path, gib):
    """sudo argv that runs this module's own source in an isolated interpreter."""
    with open(__file__, "r", encoding="utf-8") as stream:
        source = stream.read()
    return [
        "sudo",
        "-n",
        "/usr/bin/python3",
        "-I",
        "-c",
        source,
        "resize",
        str(path),
        str(int(gib)),
    ]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
