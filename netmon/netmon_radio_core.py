"""Helpers for launching and sharing state with the standalone NetMon Radio app."""

from __future__ import annotations

import json
import os
import shutil
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass

try:
    from netmon.config.constants import (
        RADIO_FAVORITES_CONFIG_FILE,
        RADIO_SETTINGS_CONFIG_FILE,
        RADIO_STATIONS_CONFIG_FILE,
    )
except ModuleNotFoundError:
    from config.constants import (
        RADIO_FAVORITES_CONFIG_FILE,
        RADIO_SETTINGS_CONFIG_FILE,
        RADIO_STATIONS_CONFIG_FILE,
    )

try:
    from netmon.core.state import (
        get_netmon_config_dir,
        get_netmon_documents_dir,
        get_netmon_state_dir,
    )
except ModuleNotFoundError:
    from core.state import (
        get_netmon_config_dir,
        get_netmon_documents_dir,
        get_netmon_state_dir,
    )


@dataclass(frozen=True)
class RadioPathSet:
    config_dir: str
    state_dir: str
    default_stations_path: str
    radio_db_path: str
    radio_db_meta_path: str
    radio_stations_path: str
    radio_favorites_path: str
    radio_settings_path: str
    radio_host_state_path: str
    radio_attach_request_path: str
    radio_standalone_attach_request_path: str
    radio_standalone_show_request_path: str
    radio_detached_state_path: str
    radio_handover_request_path: str
    radio_handover_ack_path: str


def repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def radio_entrypoint_path() -> str:
    return os.path.join(os.path.dirname(__file__), "netmon_radio_app.py")


def radio_wrapper_path() -> str:
    wrapper_path = os.path.join(repo_root(), "netmon_radio_app.py")
    if os.path.isfile(wrapper_path):
        return wrapper_path
    return radio_entrypoint_path()


def project_venv_python_executable() -> str:
    return os.path.join(repo_root(), "venv", "bin", "python")


def project_python_executable() -> str:
    venv_python = project_venv_python_executable()
    if os.path.isfile(venv_python) and os.access(venv_python, os.X_OK):
        return venv_python
    return sys.executable or "python3"


def radio_desktop_entry_dir() -> str:
    return os.path.expanduser("~/.local/share/applications")


def radio_desktop_entry_path() -> str:
    return os.path.join(radio_desktop_entry_dir(), "netmon-radio.desktop")


def radio_runtime_desktop_entry_path() -> str:
    return os.path.join(radio_desktop_entry_dir(), "netmon-radio-runtime.desktop")


def radio_user_data_dir() -> str:
    path = os.path.join(get_netmon_documents_dir(), "Radio")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _migrate_radio_user_file(legacy_path: str, target_path: str) -> None:
    if (
        not legacy_path
        or not os.path.isfile(legacy_path)
        or os.path.exists(target_path)
    ):
        return
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(legacy_path, target_path)
    except Exception:
        return


def _prepare_radio_user_data_paths(config_dir: str, state_dir: str) -> dict[str, str]:
    user_dir = radio_user_data_dir()
    paths = {
        "radio_db_path": os.path.join(user_dir, "radio_db.json"),
        "radio_db_meta_path": os.path.join(user_dir, "radio_db_meta.json"),
        "radio_stations_path": os.path.join(user_dir, RADIO_STATIONS_CONFIG_FILE),
        "radio_favorites_path": os.path.join(user_dir, RADIO_FAVORITES_CONFIG_FILE),
        "radio_settings_path": os.path.join(user_dir, RADIO_SETTINGS_CONFIG_FILE),
    }
    legacy_map = {
        "radio_db_path": os.path.join(state_dir, "radio_db.json"),
        "radio_db_meta_path": os.path.join(state_dir, "radio_db_meta.json"),
        "radio_stations_path": os.path.join(config_dir, RADIO_STATIONS_CONFIG_FILE),
        "radio_favorites_path": os.path.join(config_dir, RADIO_FAVORITES_CONFIG_FILE),
        "radio_settings_path": os.path.join(config_dir, RADIO_SETTINGS_CONFIG_FILE),
    }
    for key, target_path in paths.items():
        _migrate_radio_user_file(legacy_map[key], target_path)
    return paths


def build_radio_paths() -> RadioPathSet:
    config_dir = get_netmon_config_dir()
    state_dir = get_netmon_state_dir()
    try:
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(state_dir, exist_ok=True)
    except Exception:
        pass
    user_paths = _prepare_radio_user_data_paths(config_dir, state_dir)
    return RadioPathSet(
        config_dir=config_dir,
        state_dir=state_dir,
        default_stations_path=os.path.join(
            os.path.dirname(__file__),
            "config",
            RADIO_STATIONS_CONFIG_FILE,
        ),
        radio_db_path=user_paths["radio_db_path"],
        radio_db_meta_path=user_paths["radio_db_meta_path"],
        radio_stations_path=user_paths["radio_stations_path"],
        radio_favorites_path=user_paths["radio_favorites_path"],
        radio_settings_path=user_paths["radio_settings_path"],
        radio_host_state_path=os.path.join(state_dir, "radio_host_state.json"),
        radio_attach_request_path=os.path.join(state_dir, "radio_attach_request.json"),
        radio_standalone_attach_request_path=os.path.join(
            state_dir, "radio_standalone_attach_request.json"
        ),
        radio_standalone_show_request_path=os.path.join(
            state_dir, "radio_standalone_show_request.json"
        ),
        radio_detached_state_path=os.path.join(state_dir, "radio_detached_state.json"),
        radio_handover_request_path=os.path.join(
            state_dir, "radio_handover_request.json"
        ),
        radio_handover_ack_path=os.path.join(state_dir, "radio_handover_ack.json"),
    )


def _safe_write_json(path: str, payload: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def _safe_read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass
    return {}


def _write_radio_host_state_payload(payload: dict) -> bool:
    paths = build_radio_paths()
    normalized = _normalize_radio_host_state(payload)
    normalized["updated_at"] = int(time.time())
    return _safe_write_json(paths.radio_host_state_path, normalized)


def _build_session_id(mode: str, owner_pid: int) -> str:
    return f"{str(mode or 'radio').strip().lower()}-{int(owner_pid)}-{int(time.time() * 1000)}"


def _build_transition_id(target_mode: str, owner_pid: int) -> str:
    return (
        f"{str(target_mode or 'transition').strip().lower()}-"
        f"{int(owner_pid)}-{int(time.time() * 1000)}"
    )


def _state_from_mode(mode: str, *, attached: bool = True) -> str:
    normalized_mode = str(mode or "").strip().lower() or "embedded"
    if normalized_mode == "standalone" or not bool(attached):
        return "standalone_active"
    return "embedded_active"


def _transition_state_name(target_mode: str) -> str:
    normalized_target = str(target_mode or "").strip().lower()
    if normalized_target == "standalone":
        return "detaching"
    if normalized_target == "embedded":
        return "attaching"
    return ""


def _normalize_radio_host_state(payload: dict) -> dict:
    normalized = dict(payload or {})
    launcher_state = str(normalized.get("launcher_state", "") or "").strip().lower()
    if not launcher_state:
        transition_state = (
            str(normalized.get("transition_state", "") or "").strip().lower()
        )
        transition_target = (
            str(normalized.get("transition_target", "") or "").strip().lower()
        )
        if transition_state == "pending":
            launcher_state = _transition_state_name(transition_target)
        else:
            launcher_state = _state_from_mode(
                str(normalized.get("mode", "") or "embedded"),
                attached=bool(normalized.get("attached", True)),
            )
    if launcher_state == "detaching":
        normalized["launcher_state"] = "detaching"
        normalized["mode"] = "embedded"
        normalized["attached"] = True
        normalized["transition_state"] = "pending"
        normalized["transition_target"] = "standalone"
    elif launcher_state == "attaching":
        normalized["launcher_state"] = "attaching"
        normalized["mode"] = "standalone"
        normalized["attached"] = False
        normalized["transition_state"] = "pending"
        normalized["transition_target"] = "embedded"
    elif launcher_state == "standalone_active":
        normalized["launcher_state"] = "standalone_active"
        normalized["mode"] = "standalone"
        normalized["attached"] = False
        normalized["transition_state"] = ""
        normalized["transition_target"] = ""
    else:
        normalized["launcher_state"] = "embedded_active"
        normalized["mode"] = "embedded"
        normalized["attached"] = True
        normalized["transition_state"] = ""
        normalized["transition_target"] = ""
    return normalized


def _process_exists(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def write_netmon_host_state(pid: int) -> bool:
    return _write_radio_host_state_payload(
        {
            "pid": int(pid),
            "owner_pid": int(pid),
            "launcher_state": "embedded_active",
            "mode": "embedded",
            "attached": True,
            "started_from": "netmon",
            "session_id": _build_session_id("embedded", int(pid)),
            "transition_state": "",
            "transition_target": "",
        },
    )


def clear_netmon_host_state(pid: int | None = None) -> bool:
    paths = build_radio_paths()
    if not os.path.exists(paths.radio_host_state_path):
        return True
    if pid is not None:
        state = _safe_read_json(paths.radio_host_state_path)
        if int(state.get("pid") or 0) != int(pid):
            return False
    try:
        os.remove(paths.radio_host_state_path)
        return True
    except FileNotFoundError:
        return True
    except Exception:
        return False


def read_netmon_host_state() -> dict:
    return _safe_read_json(build_radio_paths().radio_host_state_path)


def read_radio_host_state() -> dict:
    state = _normalize_radio_host_state(read_netmon_host_state())
    if "owner_pid" not in state and "pid" in state:
        state["owner_pid"] = int(state.get("pid") or 0)
    if "session_id" not in state and state.get("owner_pid"):
        state["session_id"] = _build_session_id(
            str(state.get("mode", "radio") or "radio"),
            int(state.get("owner_pid") or 0),
        )
    return state


def write_radio_launcher_state(
    *,
    launcher_state: str,
    owner_pid: int,
    current_station_id: str = "",
    started_from: str = "",
    session_id: str = "",
    transition_id: str = "",
    extras: dict | None = None,
) -> bool:
    normalized_launcher_state = (
        str(launcher_state or "").strip().lower() or "embedded_active"
    )
    payload = {
        "pid": int(owner_pid),
        "owner_pid": int(owner_pid),
        "launcher_state": normalized_launcher_state,
        "session_id": (
            str(session_id or "").strip()
            or _build_session_id(normalized_launcher_state, int(owner_pid))
        ),
        "current_station_id": str(current_station_id or "").strip(),
        "started_from": str(started_from or "").strip(),
        "transition_id": str(transition_id or "").strip(),
    }
    if isinstance(extras, dict):
        payload.update(extras)
    return _write_radio_host_state_payload(payload)


def write_radio_host_state(
    *,
    mode: str,
    owner_pid: int,
    attached: bool | None = None,
    current_station_id: str = "",
    started_from: str = "",
    extras: dict | None = None,
) -> bool:
    normalized_mode = str(mode or "").strip().lower() or "embedded"
    if normalized_mode not in {"embedded", "standalone"}:
        normalized_mode = "embedded"
    normalized_attached = (
        bool(attached) if attached is not None else normalized_mode == "embedded"
    )
    return write_radio_launcher_state(
        launcher_state=_state_from_mode(
            normalized_mode,
            attached=normalized_attached,
        ),
        owner_pid=owner_pid,
        current_station_id=current_station_id,
        started_from=started_from,
        extras=extras,
    )


def set_radio_mode(
    mode: str,
    *,
    owner_pid: int,
    current_station_id: str = "",
    started_from: str = "",
) -> bool:
    normalized_mode = str(mode or "").strip().lower() or "embedded"
    return write_radio_host_state(
        mode=normalized_mode,
        owner_pid=owner_pid,
        attached=normalized_mode == "embedded",
        current_station_id=current_station_id,
        started_from=started_from,
    )


def netmon_host_is_available() -> bool:
    state = read_netmon_host_state()
    pid = int(state.get("pid") or 0)
    return pid > 0 and _process_exists(pid)


def radio_host_is_running(mode: str | None = None) -> bool:
    state = read_radio_host_state()
    owner_pid = int(state.get("owner_pid") or state.get("pid") or 0)
    if owner_pid <= 0 or not _process_exists(owner_pid):
        return False
    expected_mode = str(mode or "").strip().lower()
    if expected_mode:
        launcher_state = str(state.get("launcher_state", "") or "").strip().lower()
        if expected_mode == "standalone":
            if launcher_state not in {"standalone_active", "attaching"}:
                return False
        elif expected_mode == "embedded":
            if launcher_state not in {"embedded_active", "detaching"}:
                return False
        elif str(state.get("mode", "")).strip().lower() != expected_mode:
            return False
    return True


def standalone_radio_is_running() -> bool:
    return radio_host_is_running(mode="standalone")


def radio_transition_in_progress(
    target_mode: str | None = None, max_age_s: int = 20
) -> bool:
    state = read_radio_host_state()
    launcher_state = str(state.get("launcher_state", "") or "").strip().lower()
    if launcher_state not in {"detaching", "attaching"}:
        return False
    requested_target = str(target_mode or "").strip().lower()
    current_target = (
        "standalone"
        if launcher_state == "detaching"
        else ("embedded" if launcher_state == "attaching" else "")
    )
    if requested_target and current_target != requested_target:
        return False
    updated_at = int(state.get("updated_at") or 0)
    if updated_at > 0 and (int(time.time()) - updated_at) > int(max_age_s):
        return False
    return True


def begin_radio_transition(
    *,
    from_mode: str,
    target_mode: str,
    owner_pid: int,
    current_station_id: str = "",
    started_from: str = "",
) -> bool:
    state = read_radio_host_state()
    transition_id = _build_transition_id(target_mode, owner_pid)
    return write_radio_launcher_state(
        launcher_state=_transition_state_name(target_mode),
        owner_pid=owner_pid,
        current_station_id=current_station_id,
        started_from=started_from,
        session_id=str(
            state.get("session_id") or _build_session_id(from_mode, owner_pid)
        ),
        transition_id=transition_id,
    )


def complete_radio_transition(
    *,
    mode: str,
    owner_pid: int,
    current_station_id: str = "",
    started_from: str = "",
    attached: bool | None = None,
) -> bool:
    normalized_mode = str(mode or "").strip().lower() or "embedded"
    normalized_attached = (
        bool(attached) if attached is not None else normalized_mode == "embedded"
    )
    return write_radio_launcher_state(
        launcher_state=_state_from_mode(
            normalized_mode,
            attached=normalized_attached,
        ),
        owner_pid=owner_pid,
        current_station_id=current_station_id,
        started_from=started_from,
    )


def cancel_radio_transition(owner_pid: int | None = None) -> bool:
    state = read_radio_host_state()
    if not state:
        return True
    if owner_pid is not None and int(state.get("owner_pid") or 0) != int(owner_pid):
        return False
    state["launcher_state"] = _state_from_mode(
        str(state.get("mode", "") or "embedded"),
        attached=bool(state.get("attached", True)),
    )
    state["transition_id"] = ""
    return _write_radio_host_state_payload(state)


def set_radio_detached_state(detached: bool) -> bool:
    state = read_radio_host_state()
    if not state:
        return False
    state["attached"] = not bool(detached)
    launcher_state = str(state.get("launcher_state", "") or "").strip().lower()
    transition_pending = launcher_state in {"detaching", "attaching"}
    if not transition_pending:
        if detached:
            state["mode"] = "standalone"
        elif state.get("mode") == "standalone":
            state["mode"] = "embedded"
        state["launcher_state"] = _state_from_mode(
            str(state.get("mode", "") or "embedded"),
            attached=bool(state.get("attached", True)),
        )
    ok = _write_radio_host_state_payload(state)
    try:
        os.remove(build_radio_paths().radio_detached_state_path)
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return ok


def radio_is_detached() -> bool:
    state = read_radio_host_state()
    if not state:
        return False
    launcher_state = str(state.get("launcher_state", "") or "").strip().lower()
    if launcher_state in {"standalone_active", "attaching"}:
        return True
    if launcher_state in {"embedded_active", "detaching"}:
        return False
    return False


def current_radio_transition_id() -> str:
    state = read_radio_host_state()
    return str(state.get("transition_id", "") or "").strip()


def _request_radio_signal(path: str, *, action: str, transition_id: str = "") -> bool:
    return _safe_write_json(
        path,
        {
            "action": str(action or "").strip(),
            "transition_id": str(transition_id or "").strip(),
            "requested_at": int(time.time()),
        },
    )


def _consume_radio_signal(path: str, *, action: str, transition_id: str = "") -> bool:
    payload = _safe_read_json(path)
    if payload.get("action") != str(action or "").strip():
        return False
    expected_transition_id = str(transition_id or "").strip()
    payload_transition_id = str(payload.get("transition_id", "") or "").strip()
    if expected_transition_id and payload_transition_id != expected_transition_id:
        return False
    try:
        os.remove(path)
    except Exception:
        pass
    return True


def _clear_radio_signal(path: str) -> bool:
    if not os.path.exists(path):
        return True
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return True
    except Exception:
        return False


def _request_radio_payload(
    path: str,
    *,
    target_mode: str,
    payload: dict | None = None,
    action: str,
    transition_id: str = "",
) -> bool:
    return _safe_write_json(
        path,
        {
            "action": str(action or "").strip().lower(),
            "target_mode": str(target_mode or "").strip().lower(),
            "transition_id": str(transition_id or "").strip(),
            "payload": dict(payload or {}),
            "requested_at": int(time.time()),
        },
    )


def _consume_radio_payload(
    path: str,
    *,
    target_mode: str,
    transition_id: str = "",
) -> dict | None:
    payload = _safe_read_json(path)
    if not payload:
        return None
    expected_mode = str(target_mode or "").strip().lower()
    if str(payload.get("target_mode", "")).strip().lower() != expected_mode:
        return None
    expected_transition_id = str(transition_id or "").strip()
    payload_transition_id = str(payload.get("transition_id", "") or "").strip()
    if expected_transition_id and payload_transition_id != expected_transition_id:
        return None
    try:
        os.remove(path)
    except Exception:
        pass
    data = payload.get("payload")
    return dict(data) if isinstance(data, dict) else {}


def _clear_radio_payload(path: str, *, target_mode: str | None = None) -> bool:
    if not os.path.exists(path):
        return True
    if target_mode:
        payload = _safe_read_json(path)
        if (
            str(payload.get("target_mode", "")).strip().lower()
            != str(target_mode or "").strip().lower()
        ):
            return False
    return _clear_radio_signal(path)


def _append_radio_launch_args(
    command: list[str],
    *,
    theme_name: str | None = None,
    started_from: str | None = None,
) -> list[str]:
    _ignored_theme_name = theme_name
    command.extend(["--theme", "dark"])
    source = str(started_from or "").strip().lower()
    if source:
        command.extend(["--started-from", source])
    return command


def request_radio_attach(*, transition_id: str = "") -> bool:
    return _request_radio_signal(
        build_radio_paths().radio_attach_request_path,
        action="attach",
        transition_id=transition_id,
    )


def request_standalone_radio_attach(*, transition_id: str = "") -> bool:
    return _request_radio_signal(
        build_radio_paths().radio_standalone_attach_request_path,
        action="attach_to_netmon",
        transition_id=transition_id,
    )


def request_standalone_radio_show(*, transition_id: str = "") -> bool:
    return _request_radio_signal(
        build_radio_paths().radio_standalone_show_request_path,
        action="show_standalone_radio",
        transition_id=transition_id,
    )


def consume_standalone_radio_attach_request(*, transition_id: str = "") -> bool:
    return _consume_radio_signal(
        build_radio_paths().radio_standalone_attach_request_path,
        action="attach_to_netmon",
        transition_id=transition_id,
    )


def consume_standalone_radio_show_request(*, transition_id: str = "") -> bool:
    return _consume_radio_signal(
        build_radio_paths().radio_standalone_show_request_path,
        action="show_standalone_radio",
        transition_id=transition_id,
    )


def clear_standalone_radio_attach_request() -> bool:
    return _clear_radio_signal(build_radio_paths().radio_standalone_attach_request_path)


def clear_radio_attach_request() -> bool:
    return _clear_radio_signal(build_radio_paths().radio_attach_request_path)


def request_radio_handover(
    *,
    target_mode: str,
    payload: dict | None = None,
    action: str = "handover",
    transition_id: str = "",
) -> bool:
    return _request_radio_payload(
        build_radio_paths().radio_handover_request_path,
        target_mode=target_mode,
        payload=payload,
        action=str(action or "handover").strip().lower() or "handover",
        transition_id=transition_id,
    )


def clear_radio_handover_request(target_mode: str | None = None) -> bool:
    return _clear_radio_payload(
        build_radio_paths().radio_handover_request_path,
        target_mode=target_mode,
    )


def request_radio_handover_ack(
    *,
    target_mode: str,
    payload: dict | None = None,
    action: str = "handover_ack",
    transition_id: str = "",
) -> bool:
    return _request_radio_payload(
        build_radio_paths().radio_handover_ack_path,
        target_mode=target_mode,
        payload=payload,
        action=str(action or "handover_ack").strip().lower() or "handover_ack",
        transition_id=transition_id,
    )


def consume_radio_handover_ack(
    target_mode: str, *, transition_id: str = ""
) -> dict | None:
    return _consume_radio_payload(
        build_radio_paths().radio_handover_ack_path,
        target_mode=target_mode,
        transition_id=transition_id,
    )


def consume_radio_attach_request(*, transition_id: str = "") -> bool:
    return _consume_radio_signal(
        build_radio_paths().radio_attach_request_path,
        action="attach",
        transition_id=transition_id,
    )


def consume_radio_handover(target_mode: str, *, transition_id: str = "") -> dict | None:
    return _consume_radio_payload(
        build_radio_paths().radio_handover_request_path,
        target_mode=target_mode,
        transition_id=transition_id,
    )


def build_radio_app_command(
    python_executable: str | None = None,
    theme_name: str | None = None,
    started_from: str | None = None,
) -> list[str]:
    command = [
        python_executable or project_python_executable(),
        "-m",
        "netmon.netmon_radio_app",
    ]
    return _append_radio_launch_args(
        command,
        theme_name=theme_name,
        started_from=started_from,
    )


def build_radio_wrapper_command(
    python_executable: str | None = None,
    theme_name: str | None = None,
    started_from: str | None = None,
) -> list[str]:
    command = [python_executable or project_python_executable(), radio_wrapper_path()]
    return _append_radio_launch_args(
        command,
        theme_name=theme_name,
        started_from=started_from,
    )


def build_radio_desktop_exec_command(
    python_executable: str | None = None,
    theme_name: str | None = None,
) -> str:
    return shlex.join(
        build_radio_wrapper_command(
            python_executable=python_executable,
            theme_name=theme_name,
            started_from="desktop",
        )
    )


def radio_icon_path() -> str:
    root = repo_root()
    candidate = os.path.join(root, "tools", "netmon-radio.png")
    if os.path.isfile(candidate):
        return candidate
    return ""


def build_radio_desktop_entry(
    exec_command: str,
    *,
    icon_path: str = "",
    name: str = "NetMon Radio",
    comment: str = "Standalone Radio-Player aus NetMon",
    no_display: bool = False,
) -> str:
    entry_path = repo_root()
    if entry_path == "/dev-lab/projects/dev-lab":
        entry_path = "/workspaces/dev-lab"
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        f"Name={name}",
        f"Comment={comment}",
        f"Exec={exec_command}",
        f"Path={entry_path}",
        "Terminal=false",
        "Categories=AudioVideo;Player;Network;",
        "StartupNotify=true",
        "StartupWMClass=NetMonRadio",
        "X-GNOME-WMClass=NetMonRadio",
    ]
    icon = str(icon_path or "").strip()
    if icon:
        lines.append(f"Icon={icon}")
    if no_display:
        lines.append("NoDisplay=true")
    return "\n".join(lines) + "\n"


def ensure_radio_runtime_desktop_entry(
    theme_name: str | None = None,
    started_from: str | None = None,
) -> str:
    path = radio_runtime_desktop_entry_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        content = build_radio_desktop_entry(
            shlex.join(
                build_radio_wrapper_command(
                    theme_name=theme_name,
                    started_from=started_from or "desktop",
                )
            ),
            icon_path=radio_icon_path(),
            no_display=True,
        )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path
    except Exception:
        return ""


def ensure_radio_desktop_entry(
    theme_name: str | None = None,
    started_from: str | None = None,
) -> str:
    path = radio_desktop_entry_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        content = build_radio_desktop_entry(
            shlex.join(
                build_radio_wrapper_command(
                    theme_name=theme_name,
                    started_from=started_from or "desktop",
                )
            ),
            icon_path=radio_icon_path(),
            no_display=False,
        )
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path
    except Exception:
        return ""


def _radio_launch_desktop_env(
    theme_name: str | None = None,
    started_from: str | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    desktop_path = ""
    user_desktop_path = radio_desktop_entry_path()
    if os.path.isfile(user_desktop_path):
        desktop_path = ensure_radio_desktop_entry(
            theme_name=theme_name,
            started_from=started_from,
        )
    if not desktop_path:
        desktop_path = ensure_radio_runtime_desktop_entry(
            theme_name=theme_name,
            started_from=started_from,
        )
    if desktop_path:
        env["BAMF_DESKTOP_FILE_HINT"] = desktop_path
        env["GIO_LAUNCHED_DESKTOP_FILE"] = desktop_path
    return env


def _radio_launch_desktop_hint(env: dict[str, str]) -> str:
    return str(
        dict(env or {}).get("BAMF_DESKTOP_FILE_HINT")
        or dict(env or {}).get("GIO_LAUNCHED_DESKTOP_FILE")
        or ""
    ).strip()


def _radio_desktop_id_from_path(path: str) -> str:
    desktop_path = str(path or "").strip()
    if not desktop_path:
        return ""
    return os.path.splitext(os.path.basename(desktop_path))[0].strip()


def _radio_log_handle_write(log_handle, message: str) -> bool:
    if log_handle is None:
        return False
    try:
        log_handle.write(message)
        log_handle.flush()
    except Exception:
        return False
    return True


def _close_radio_log_handle(log_handle) -> bool:
    if log_handle is None:
        return False
    try:
        log_handle.close()
    except Exception:
        return False
    return True


def _notify_radio_logger(logger, message: str) -> bool:
    if not callable(logger):
        return False
    try:
        logger(message)
    except Exception:
        return False
    return True


def launch_radio_app(
    logger=None,
    python_executable: str | None = None,
    theme_name: str | None = None,
    started_from: str | None = None,
):
    direct_command = build_radio_wrapper_command(
        python_executable=python_executable,
        theme_name=theme_name,
        started_from=started_from,
    )
    desktop_launch = False
    command = list(direct_command)
    launcher_log_path = os.path.join(
        build_radio_paths().state_dir, "radio_launcher_start.log"
    )
    log_handle = None
    try:
        os.makedirs(os.path.dirname(launcher_log_path), exist_ok=True)
        log_handle = open(launcher_log_path, "a", encoding="utf-8")
        launch_env = _radio_launch_desktop_env(
            theme_name=theme_name,
            started_from=started_from,
        )
        desktop_hint = _radio_launch_desktop_hint(launch_env)
        desktop_id = _radio_desktop_id_from_path(desktop_hint)
        if desktop_hint and shutil.which("gtk-launch") and desktop_id:
            command = ["gtk-launch", desktop_id]
            desktop_launch = True
        _radio_log_handle_write(
            log_handle,
            f"[{int(time.time())}] launch: {shlex.join(command)}\n",
        )
        _radio_log_handle_write(
            log_handle,
            "[RadioLaunchDiag] "
            f"startup_wm_class=NetMonRadio desktop_hint={desktop_hint or '-'}\n",
        )
        proc = subprocess.Popen(
            command,
            cwd=repo_root(),
            env=launch_env,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=log_handle,
            start_new_session=True,
        )
    except Exception as exc:
        _close_radio_log_handle(log_handle)
        _notify_radio_logger(logger, f"Radio-App konnte nicht gestartet werden: {exc}")
        return None
    time.sleep(0.35)
    exit_code = proc.poll()
    if exit_code is not None and not desktop_launch:
        _radio_log_handle_write(
            log_handle,
            f"[{int(time.time())}] launch failed early rc={exit_code}\n",
        )
        _close_radio_log_handle(log_handle)
        _notify_radio_logger(
            logger,
            "Radio-App ist sofort wieder beendet "
            f"(rc={exit_code}). Details: {launcher_log_path}",
        )
        return None
    _radio_log_handle_write(
        log_handle,
        f"[{int(time.time())}] launch running pid={proc.pid}\n",
    )
    _close_radio_log_handle(log_handle)
    _notify_radio_logger(
        logger,
        f"Radio-App gestartet (PID {proc.pid}). Log: {launcher_log_path}",
    )
    _notify_radio_logger(
        logger,
        "[RadioLaunchDiag] "
        f"startup_wm_class=NetMonRadio | desktop_hint={desktop_hint or '-'}",
    )
    return proc
