"""Linux-only local website lifecycle; never signal a PID read from disk."""

import contextlib
import fcntl
import functools
import hashlib
import http.server
import json
import os
import secrets
import select
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def check_private(info, directory=False):
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    mode = 0o700 if directory else 0o600
    if (
        not kind(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) != mode
        or (not directory and info.st_nlink != 1)
    ):
        raise PermissionError("Unsafe website runtime owner, type, mode or link count")


def open_directory(path):
    """Walk without following symlinks, including intermediate components."""
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Runtime path must be absolute without '..'")
    fd = os.open("/", DIR_FLAGS)
    try:
        for part in path.parts[1:]:
            new_fd = os.open(part, DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = new_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


@contextlib.contextmanager
def runtime_directory():
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    parent = open_directory(runtime if runtime else "/tmp")
    fd = None
    try:
        if runtime:
            check_private(os.fstat(parent), directory=True)
        else:
            info = os.fstat(parent)
            if info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o1777:
                raise PermissionError("Unsafe /tmp fallback")
        suffix = hashlib.sha256(os.fsencode(ROOT)).hexdigest()[:20]
        name = f"netmon-site-{os.geteuid()}-{suffix}"
        try:
            os.mkdir(name, 0o700, dir_fd=parent)
        except FileExistsError:
            pass
        fd = os.open(name, DIR_FLAGS, dir_fd=parent)
        check_private(os.fstat(fd), directory=True)
        yield fd, str(Path(runtime if runtime else "/tmp") / name)
    finally:
        if fd is not None:
            os.close(fd)
        os.close(parent)


@contextlib.contextmanager
def private_file(directory, name):
    fd = os.open(
        name,
        os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
        0o600,
        dir_fd=directory,
    )
    try:
        check_private(os.fstat(fd))
        yield fd
    finally:
        os.close(fd)


def acquire(fd, timeout=5):
    end = time.monotonic() + timeout
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except BlockingIOError:
            if time.monotonic() >= end:
                return False
            time.sleep(0.05)


def boot_id():
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def proc_for_handle(fd):
    # fdinfo Pid is expressed in the PID namespace of the mounted procfs.
    # This also works when /proc shows an ancestor namespace (containers).
    for line in Path(f"/proc/self/fdinfo/{fd}").read_text().splitlines():
        if line.startswith("Pid:"):
            pid = int(line.split()[1])
            if pid <= 0:
                raise ProcessLookupError("Website process exited")
            return Path(f"/proc/{pid}")
    raise RuntimeError("pidfd process identity is unavailable")


def stat_start(proc):
    # comm may contain spaces and ')'; fields after the final ')' start at field 3.
    return (proc / "stat").read_text().rsplit(")", 1)[1].split()[19]


def start_time(pid):
    fd = os.pidfd_open(pid)
    try:
        return stat_start(proc_for_handle(fd))
    finally:
        os.close(fd)


def read_state(directory):
    try:
        fd = os.open(
            "server.json",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=directory,
        )
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as source:
        check_private(os.fstat(source.fileno()))
        data = source.read(4097)
    if len(data) > 4096:
        raise ValueError("Oversized website server state")
    record = json.loads(data)
    if (
        not isinstance(record, dict)
        or set(record) != {"pid", "start", "boot", "port", "root", "ready_fd"}
        or type(record["pid"]) is not int
        or not 1 < record["pid"] <= 2147483647
        or type(record["port"]) is not int
        or not 1 <= record["port"] <= 65535
        or type(record["ready_fd"]) is not int
        or not 3 <= record["ready_fd"] <= 2147483647
        or not isinstance(record["start"], str)
        or not record["start"].isascii()
        or not record["start"].isdecimal()
        or not isinstance(record["boot"], str)
        or record["root"] != str(ROOT)
    ):
        raise ValueError("Invalid website server state")
    return record


def server_command(port, ready):
    return [
        sys.executable,
        "-I",
        str(Path(__file__).resolve()),
        "_serve",
        str(port),
        str(ready),
    ]


def process_handle(record):
    """Pin identity before inspection; only this handle may receive a signal."""
    if record["boot"] != boot_id():
        return None
    try:
        fd = os.pidfd_open(record["pid"])
    except ProcessLookupError:
        return None
    try:
        if select.select([fd], [], [], 0)[0]:
            os.close(fd)
            return None
        proc = proc_for_handle(fd)
        if (
            proc.stat().st_uid != os.geteuid()
            or stat_start(proc) != record["start"]
            or os.readlink(proc / "cwd") != str(ROOT)
            or Path(os.readlink(proc / "exe")) != Path(sys.executable).resolve()
            or (proc / "cmdline").read_bytes()
            != b"\0".join(
                os.fsencode(arg)
                for arg in server_command(record["port"], record["ready_fd"])
            )
            + b"\0"
        ):
            raise PermissionError("Registered process is not this website server")
        return fd
    except (FileNotFoundError, ProcessLookupError):
        os.close(fd)
        return None
    except BaseException:
        os.close(fd)
        raise


def publish_state(directory, record):
    name = "state-" + secrets.token_hex(16)
    fd = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(record, output)
            output.flush()
            os.fsync(output.fileno())
        # Publish only complete state and never replace an unexpected existing entry.
        os.link(
            name,
            "server.json",
            src_dir_fd=directory,
            dst_dir_fd=directory,
            follow_symlinks=False,
        )
    finally:
        os.unlink(name, dir_fd=directory)


def serve(port, ready):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        os.write(ready, b"OK")
        os.close(ready)
        server.serve_forever()


def start(directory, port):
    with private_file(directory, "server.log") as log:
        os.lseek(log, 0, os.SEEK_END)
        read_fd, write_fd = os.pipe()
        try:
            process = subprocess.Popen(
                server_command(port, write_fd),
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
                pass_fds=(write_fd,),
            )
        except BaseException:
            os.close(read_fd)
            raise
        finally:
            os.close(write_fd)
        try:
            if (
                not select.select([read_fd], [], [], 5)[0]
                or os.read(read_fd, 8) != b"OK"
            ):
                raise RuntimeError("Website server failed to start; see server.log")
            record = {
                "pid": process.pid,
                "start": start_time(process.pid),
                "boot": boot_id(),
                "port": port,
                "root": str(ROOT),
                "ready_fd": write_fd,
            }
            handle = process_handle(record)
            if handle is None:
                raise RuntimeError("Website server exited during startup")
            os.close(handle)
            publish_state(directory, record)
        except BaseException:
            # Only our unreaped direct child, never a PID obtained from a file.
            process.terminate()
            process.wait(timeout=5)
            raise
        finally:
            os.close(read_fd)


def main(action):
    os.umask(0o077)
    if action not in {"start", "stop"}:
        raise ValueError("Expected start or stop")
    # Fail closed on systems without pidfd support. No numeric-kill fallback.
    fd = os.pidfd_open(os.getpid())
    try:
        signal.pidfd_send_signal(fd, 0)
    finally:
        os.close(fd)
    with (
        runtime_directory() as (directory, path),
        private_file(directory, "manager.lock") as manager,
    ):
        if not acquire(manager):
            raise RuntimeError("Website lifecycle operation is busy")
        record = read_state(directory)
        handle = process_handle(record) if record else None
        try:
            if action == "stop":
                if handle is not None:
                    try:
                        signal.pidfd_send_signal(handle, signal.SIGTERM)
                    except ProcessLookupError:
                        pass  # Already exited after validation; handle cannot hit reuse.
                    if not select.select([handle], [], [], 5)[0]:
                        raise RuntimeError("Website server has not stopped")
                if record:
                    os.unlink("server.json", dir_fd=directory)
                print(
                    "NetMon Website-Server gestoppt."
                    if handle is not None
                    else "Kein NetMon Website-Server registriert."
                )
            else:
                raw = os.environ.get("NETMON_SITE_PORT", "8765")
                if (
                    not raw.isascii()
                    or not raw.isdecimal()
                    or not 1 <= int(raw) <= 65535
                ):
                    raise ValueError("NETMON_SITE_PORT must be 1..65535")
                port = int(raw)
                if handle is not None:
                    if record["port"] != port:
                        raise RuntimeError(
                            "Website server already uses a different port"
                        )
                else:
                    if record:
                        os.unlink("server.json", dir_fd=directory)
                    start(directory, port)
                print(f"Logdatei: {path}/server.log", file=sys.stderr)
                print(f"http://127.0.0.1:{port}/site/index.html")
        finally:
            if handle is not None:
                os.close(handle)


if __name__ == "__main__":
    try:
        if len(sys.argv) == 4 and sys.argv[1] == "_serve":
            serve(*map(int, sys.argv[2:]))
        elif len(sys.argv) == 2:
            main(sys.argv[1])
        else:
            raise ValueError("Expected start or stop")
    except (OSError, ValueError, RuntimeError, AttributeError) as error:
        print(f"Website helper failed: {error}", file=sys.stderr)
        sys.exit(1)
