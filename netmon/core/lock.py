"""Single-instance lock helpers for NetMon."""

from __future__ import annotations

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
