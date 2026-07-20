"""State and configuration path helpers for NetMon."""

import os


def _ensure_dir(path: str) -> str:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _netmon_child_dir(base: str) -> str:
    return _ensure_dir(os.path.join(base, "netmon"))


def _xdg_dir(env_name: str, default_suffix: str) -> str:
    base = (os.environ.get(env_name) or "").strip()
    if not base:
        base = os.path.expanduser(default_suffix)
    return _netmon_child_dir(base)


def get_netmon_config_dir() -> str:
    return _xdg_dir("XDG_CONFIG_HOME", "~/.config")


def get_netmon_state_dir() -> str:
    return _xdg_dir("XDG_STATE_HOME", "~/.local/state")


def get_netmon_documents_dir() -> str:
    env_value = (os.environ.get("XDG_DOCUMENTS_DIR") or "").strip()
    if env_value:
        path = os.path.join(os.path.expanduser(env_value), "NetMon")
        return _ensure_dir(path)

    candidates = [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Dokumente"),
    ]
    for base in candidates:
        if os.path.isdir(base):
            path = os.path.join(base, "NetMon")
            return _ensure_dir(path)

    fallback = os.path.join(os.path.expanduser("~/Documents"), "NetMon")
    return _ensure_dir(fallback)


def get_netmon_documents_subdir(*parts: str) -> str:
    path = os.path.join(
        get_netmon_documents_dir(),
        *[str(part or "").strip() for part in parts if str(part or "").strip()],
    )
    return _ensure_dir(path)


__all__ = [
    "get_netmon_config_dir",
    "get_netmon_documents_dir",
    "get_netmon_documents_subdir",
    "get_netmon_state_dir",
]
