"""Private, exclusive output for collect_netmon_diagnostics.sh (Linux)."""

import os
import secrets
import shutil
import stat
import sys
import tempfile
from pathlib import Path


def write_diagnostics(source, destination=None):
    """Publish complete diagnostics without opening any existing destination."""
    os.umask(0o077)
    if destination is None:
        parent = Path(tempfile.gettempdir())
        name = None
    else:
        target = Path(os.path.abspath(destination))
        parent, name = target.parent, target.name
        # Keep the existing convenience of creating missing parent directories.
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    private_fd = None
    private_name = None
    keep_private = False
    try:
        if name is not None:
            try:
                os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise FileExistsError(f"Destination already exists: {destination}")

        # mkdir is exclusive; directory FDs anchor all subsequent operations.
        for _ in range(100):
            candidate = "netmon_diagnostics_" + secrets.token_hex(16)
            try:
                os.mkdir(candidate, mode=0o700, dir_fd=parent_fd)
            except FileExistsError:
                continue
            private_name = candidate
            break
        else:
            raise FileExistsError("Cannot create private diagnostics directory")
        private_fd = os.open(
            private_name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        info = os.fstat(private_fd)
        if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
            # A hostile writable parent may have substituted the directory.
            private_name = None
            os.close(private_fd)
            private_fd = None
            raise PermissionError("Private diagnostics directory was substituted")
        fd = os.open(
            "diagnostics.txt",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=private_fd,
        )
        with os.fdopen(fd, "wb") as output:
            shutil.copyfileobj(source, output)
            output.flush()
            os.fsync(output.fileno())
        if name is None:
            keep_private = True
            return str(parent / private_name / "diagnostics.txt")
        # Atomic no-replace publication, including against a last-moment symlink.
        os.link(
            "diagnostics.txt",
            name,
            src_dir_fd=private_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
        return str(parent / name)
    finally:
        if private_fd is not None:
            try:
                if not keep_private:
                    try:
                        os.unlink("diagnostics.txt", dir_fd=private_fd)
                    except FileNotFoundError:
                        pass
            finally:
                os.close(private_fd)
        if private_name is not None and not keep_private:
            os.rmdir(private_name, dir_fd=parent_fd)
        os.close(parent_fd)


if __name__ == "__main__":
    try:
        path = write_diagnostics(
            sys.stdin.buffer, sys.argv[1] if len(sys.argv) > 1 else None
        )
    except (OSError, ValueError) as error:
        print(f"Diagnostics output failed: {error}", file=sys.stderr)
        sys.exit(1)
    print(f"Diagnostics written to {path}")
