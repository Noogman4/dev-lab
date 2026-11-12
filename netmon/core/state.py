"""State and configuration path helpers for NetMon."""

import os
import shlex

from netmon.core.private_logs import ensure_private_log_directory


def _documents_path(value: str) -> str:
    """Expand only the HOME forms supported by user-dirs.dirs; never run shell."""
    home = os.path.expanduser("~")
    for prefix in ("$HOME", "${HOME}"):
        if value == prefix or value.startswith(prefix + "/"):
            value = home + value[len(prefix) :]
            break
    value = os.path.expanduser(value)
    if not os.path.isabs(value) or any(c in value for c in ("$", "`", "\x00", "\n")):
        return ""
    return os.path.normpath(value)


def _configured_documents_dir() -> str:
    override = _documents_path((os.environ.get("XDG_DOCUMENTS_DIR") or "").strip())
    if override:
        return override
    config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    try:
        with open(os.path.join(config_home, "user-dirs.dirs"), encoding="utf-8") as f:
            content = f.read(65537)
        if len(content) > 65536:
            return ""
        for line in content.splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() == "XDG_DOCUMENTS_DIR":
                parts = shlex.split(value, comments=True)
                return _documents_path(parts[0]) if len(parts) == 1 else ""
    except (OSError, UnicodeError, ValueError):
        pass
    return ""


def _ensure_dir(path: str, *, mode=0o777) -> str:
    try:
        os.makedirs(path, mode=mode, exist_ok=True)
    except Exception:
        pass
    return path


def _netmon_child_dir(base: str, *, private: bool = False) -> str:
    path = os.path.join(base, "netmon")
    return _ensure_private_dir(path) if private else _ensure_dir(path)


def _ensure_private_dir(path: str) -> str:
    ensure_private_log_directory(path)
    return path


def _xdg_dir(env_name: str, default_suffix: str, *, private: bool = False) -> str:
    base = (os.environ.get(env_name) or "").strip()
    if not base:
        base = os.path.expanduser(default_suffix)
    return _netmon_child_dir(base, private=private)


def get_netmon_config_dir() -> str:
    return _xdg_dir("XDG_CONFIG_HOME", "~/.config")


def get_netmon_state_dir() -> str:
    return _xdg_dir("XDG_STATE_HOME", "~/.local/state", private=True)


def get_netmon_documents_dir() -> str:
    env_value = (os.environ.get("XDG_DOCUMENTS_DIR") or "").strip()
    if env_value:
        path = os.path.join(os.path.expanduser(env_value), "NetMon")
        return _ensure_private_dir(path)

    candidates = [
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Dokumente"),
    ]
    for base in candidates:
        if os.path.isdir(base):
            path = os.path.join(base, "NetMon")
            return _ensure_private_dir(path)

    fallback = os.path.join(os.path.expanduser("~/Documents"), "NetMon")
    return _ensure_private_dir(fallback)


def get_netmon_wireguard_dir() -> str:
    """Use the system profile folder without relocating existing settings/logs."""
    configured = _configured_documents_dir()
    base = (
        os.path.join(configured, "NetMon") if configured else get_netmon_documents_dir()
    )
    return _ensure_dir(os.path.join(base, "WireGuard"), mode=0o700)


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
    "get_netmon_wireguard_dir",
    "get_netmon_state_dir",
]
