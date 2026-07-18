"""State and configuration path helpers for NetMon."""

import os


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


def get_netmon_config_dir() -> str:
    return _xdg_dir("XDG_CONFIG_HOME", "~/.config")


def get_netmon_state_dir() -> str:
    return _xdg_dir("XDG_STATE_HOME", "~/.local/state")


def get_netmon_documents_dir() -> str:
    candidates = []
    env_value = (os.environ.get("XDG_DOCUMENTS_DIR") or "").strip()
    if env_value:
        path = os.path.join(os.path.expanduser(env_value), "NetMon")
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
        return path
    candidates.extend(
        [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Dokumente"),
        ]
    )
    for base in candidates:
        if os.path.isdir(base):
            path = os.path.join(base, "NetMon")
            try:
                os.makedirs(path, exist_ok=True)
            except Exception:
                pass
            return path
    fallback = os.path.join(os.path.expanduser("~/Documents"), "NetMon")
    try:
        os.makedirs(fallback, exist_ok=True)
    except Exception:
        pass
    return fallback


def get_netmon_documents_subdir(*parts: str) -> str:
    path = os.path.join(
        get_netmon_documents_dir(),
        *[str(part or "").strip() for part in parts if str(part or "").strip()],
    )
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


__all__ = [
    "get_netmon_config_dir",
    "get_netmon_documents_dir",
    "get_netmon_documents_subdir",
    "get_netmon_state_dir",
]
