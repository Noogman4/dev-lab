"""Single-instance lock helpers for NetMon."""

from __future__ import annotations

import errno
import os

try:
    import fcntl
except Exception:
    fcntl = None

try:
    from netmon.core.state import get_netmon_state_dir
except ModuleNotFoundError:
    try:
        from core.state import get_netmon_state_dir
    except ModuleNotFoundError:

        def _xdg_dir(env_name: str, default_suffix: str) -> str:
            base = (os.environ.get(env_name) or "").strip()
            if not base:
                base = os.path.expanduser(default_suffix)
            path = os.path.join(base, "netmon")
            try:
                os.makedirs(path, exist_ok=True)
            except Exception:
                pass
            return path

        def get_netmon_state_dir() -> str:
            return _xdg_dir("XDG_STATE_HOME", "~/.local/state")


NETMON_INSTANCE_LOCK_NAME = "netmon_gui.lock"
NETMON_INSTANCE_LOCK_HANDLE = None
NETMON_INSTANCE_LOCK_PATH = ""


def read_netmon_instance_lock_info(lock_path: str | None = None) -> dict[str, object]:
    path = (lock_path or NETMON_INSTANCE_LOCK_PATH or "").strip()
    if not path:
        lock_dir = get_netmon_state_dir()
        path = os.path.join(lock_dir, NETMON_INSTANCE_LOCK_NAME)

    info: dict[str, object] = {
        "lock_path": path,
        "pid": None,
        "pid_raw": "",
        "pid_valid": False,
        "process_running": False,
        "cmdline": "",
        "error": "",
    }

    try:
        with open(path, encoding="utf-8") as handle:
            pid_raw = handle.read().strip()
        info["pid_raw"] = pid_raw
    except FileNotFoundError:
        info["error"] = "lock file missing"
        return info
    except Exception as exc:
        info["error"] = f"lock file unreadable: {exc}"
        return info

    try:
        pid = int(str(info["pid_raw"]))
        if pid > 0:
            info["pid"] = pid
            info["pid_valid"] = True
    except Exception:
        info["error"] = f"invalid pid in lock file: {info['pid_raw']!r}"
        return info

    pid = info["pid"]
    if not isinstance(pid, int) or pid <= 0:
        return info

    try:
        os.kill(pid, 0)
        info["process_running"] = True
    except OSError as exc:
        # EPERM: process exists but is owned by another user — still running.
        # ESRCH: no such process — lock is stale.
        if exc.errno == errno.EPERM:
            info["process_running"] = True
        else:
            info["process_running"] = False
            return info

    proc_cmdline = f"/proc/{pid}/cmdline"
    try:
        with open(proc_cmdline, "rb") as handle:
            raw = handle.read().replace(b"\x00", b" ").strip()
        info["cmdline"] = raw.decode("utf-8", errors="replace")
    except Exception:
        info["cmdline"] = ""
    return info


def format_netmon_instance_lock_info(lock_path: str | None = None) -> str:
    info = read_netmon_instance_lock_info(lock_path)
    lines = [f"Lock-Datei: {info['lock_path']}"]

    pid = info.get("pid")
    if isinstance(pid, int) and pid > 0:
        lines.append(f"Lock-PID: {pid}")
    elif info.get("pid_raw"):
        lines.append(f"Lock-Inhalt: {info['pid_raw']}")

    if info.get("process_running"):
        lines.append("Prozessstatus: aktiv")
    elif info.get("pid_valid"):
        lines.append("Prozessstatus: PID nicht aktiv")

    cmdline = str(info.get("cmdline") or "").strip()
    if cmdline:
        lines.append(f"Prozess: {cmdline}")

    error = str(info.get("error") or "").strip()
    if error:
        lines.append(f"Hinweis: {error}")

    return "\n".join(lines)


def acquire_netmon_instance_lock():
    global NETMON_INSTANCE_LOCK_HANDLE, NETMON_INSTANCE_LOCK_PATH

    if NETMON_INSTANCE_LOCK_HANDLE is not None:
        return True, NETMON_INSTANCE_LOCK_PATH
    if fcntl is None:
        return True, ""

    lock_dir = get_netmon_state_dir()
    try:
        os.makedirs(lock_dir, exist_ok=True)
    except Exception:
        pass
    lock_path = os.path.join(lock_dir, NETMON_INSTANCE_LOCK_NAME)
    handle = open(lock_path, "a+", encoding="utf-8")

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return False, lock_path

    try:
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
    except Exception:
        pass

    NETMON_INSTANCE_LOCK_HANDLE = handle
    NETMON_INSTANCE_LOCK_PATH = lock_path
    return True, lock_path


def release_netmon_instance_lock():
    global NETMON_INSTANCE_LOCK_HANDLE, NETMON_INSTANCE_LOCK_PATH

    handle = NETMON_INSTANCE_LOCK_HANDLE
    NETMON_INSTANCE_LOCK_HANDLE = None
    NETMON_INSTANCE_LOCK_PATH = ""
    if handle is None:
        return

    try:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except Exception:
        pass
    try:
        handle.close()
    except Exception:
        pass
