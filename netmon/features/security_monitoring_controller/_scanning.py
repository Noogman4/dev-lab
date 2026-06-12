"""Security scan sub-module: device, integrity, and input-access scanning."""

from __future__ import annotations

from ._core import (
    _app_callback, _app_logger, _app_tr, _append_device_change_event,
    _append_input_access_change_event, _append_integrity_change_event, _current_security_baseline_payload, _device_baseline,
    _device_type, _device_type_mapping, _input_access_baseline, _input_access_processes,
    _input_access_scan_error_message, _input_access_sorted_process_items, _input_access_whitelist_status, _integrity_baseline,
    _integrity_entry, _integrity_scan_state, _mapping_path_sets, _normalized_device_name,
    _refresh_connected_devices_safe, _refresh_security_log_level_safe, _refresh_security_table_callback_safe, _save_security_baseline_callback_safe,
    _security_baseline_exists, _security_baseline_path, _security_export_blocks_for_app, _security_export_target,
    _security_export_write_blocks, _security_monitoring_log_message, _security_scan_log_message, _store_device_baseline,
    _store_input_access_baseline, _store_integrity_baseline, _write_security_baseline, security_integrity_ignore_path,
)



def hash_file_sha256(path):
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except Exception:
        return ""


def integrity_watch_files(app):
    app_file_path = _integrity_watch_app_file_path()
    files = _integrity_watch_base_files(app, app_file_path)
    files.extend(_integrity_watch_wireguard_files())
    return files


def _integrity_watch_app_file_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))


def _integrity_watch_base_files(app, app_file_path: str):
    return [
        app.vpn_config_path,
        app.primary_vpn_config_path,
        app.link_config_path,
        app.privacy_config_path,
        app.hdd_config_path,
        _security_baseline_path(app),
        app.clamav_findings_path,
        app_file_path,
    ]


def _integrity_watch_wireguard_files(wgdir="/etc/wireguard"):
    if not os.path.isdir(wgdir):
        return []
    try:
        return [
            os.path.join(wgdir, entry)
            for entry in os.listdir(wgdir)
            if os.path.isfile(os.path.join(wgdir, entry))
        ]
    except Exception:
        return []


def build_integrity_baseline(app):
    baseline = _integrity_scan_state(app)
    return _store_integrity_baseline(app, baseline)


def _integrity_watch_files_set(app):
    try:
        return {
            _integrity_normalized_path(str(path))
            for path in (app._integrity_watch_files() or [])
            if str(path or "").strip()
        }
    except Exception:
        return set()


def _integrity_normalized_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def _integrity_path_allowed(app, path: str, watch_files) -> bool:
    if watch_files and path not in watch_files:
        return False
    return not security_integrity_ignore_path(app, path)


def _sanitize_integrity_entry(app, raw_path, entry, watch_files):
    raw_key = str(raw_path or "").strip()
    if not raw_key:
        return None
    if not raw_key.startswith("/"):
        return raw_key, entry
    path = _integrity_normalized_path(raw_key)
    if not _integrity_path_allowed(app, path, watch_files):
        return None
    return path, entry


def sanitize_integrity_baseline(app, baseline):
    cleaned = {}
    if not isinstance(baseline, dict):
        return cleaned

    watch_files = _integrity_watch_files_set(app)

    for raw_path, entry in baseline.items():
        sanitized = _sanitize_integrity_entry(app, raw_path, entry, watch_files)
        if sanitized is None:
            continue
        key, value = sanitized
        cleaned[key] = value
    return cleaned


def _integrity_entries_differ(old, cur) -> bool:
    return (
        old.get("sha") != cur.get("sha")
        or old.get("size") != cur.get("size")
        or abs(old.get("mtime", 0) - cur.get("mtime", 0)) > 1e-6
    )


def _append_modified_integrity_event(events, app, baseline, current, path) -> None:
    old = _integrity_entry(baseline, path)
    cur = _integrity_entry(current, path)
    if not old or not cur:
        return
    if _integrity_entries_differ(old, cur):
        _append_integrity_change_event(events, app, "FILE MODIFIED", path, cur)


def _append_integrity_event_for_path(events, app, mapping, kind, path) -> None:
    entry = _integrity_entry(mapping, path)
    _append_integrity_change_event(events, app, kind, path, entry)


def _finish_scan_integrity_changes(app, current, events):
    _store_integrity_baseline(app, current)
    return events


def scan_integrity_changes(app):
    current = _integrity_scan_state(app)
    events = []

    baseline = _integrity_baseline(app)
    old_paths, new_paths = _mapping_path_sets(baseline, current)

    for path in sorted(new_paths - old_paths):
        _append_integrity_event_for_path(events, app, current, "FILE NEW", path)

    for path in sorted(old_paths - new_paths):
        _append_integrity_event_for_path(events, app, baseline, "FILE DELETED", path)

    for path in sorted(old_paths & new_paths):
        _append_modified_integrity_event(events, app, baseline, current, path)

    return _finish_scan_integrity_changes(app, current, events)


def _device_paths_in(directory: str, exists_fn) -> list[str]:
    if not os.path.isdir(directory):
        return []
    try:
        return [
            os.path.join(directory, name)
            for name in os.listdir(directory)
            if exists_fn(os.path.join(directory, name))
        ]
    except Exception:
        return []


def _sorted_device_watch_paths(paths) -> list[str]:
    return sorted(set(paths or []))


def _device_input_watch_paths() -> list[str]:
    return _device_paths_in("/dev/input", os.path.exists)


def _device_sysfs_watch_paths() -> list[str]:
    return _device_paths_in("/sys/class/input", os.path.islink)


def _collected_device_watch_paths() -> list[str]:
    devices = _device_input_watch_paths()
    devices.extend(_device_sysfs_watch_paths())
    return devices


def device_watch_paths():
    devices = _collected_device_watch_paths()
    return _sorted_device_watch_paths(devices)


def _current_device_state(app) -> dict:
    return _device_type_mapping(app)


def _device_scan_context(app) -> tuple[dict, dict, set[str], set[str]]:
    current = _current_device_state(app)
    baseline = _device_baseline(app)
    _old_paths, _new_paths, added_paths, removed_paths = _device_change_path_sets(
        baseline, current
    )
    return current, baseline, added_paths, removed_paths


def build_device_baseline(app):
    return _store_device_baseline(app, _current_device_state(app))


def _append_device_event_for_path(events, app, mapping, kind, change, path) -> None:
    device_type = _device_type(mapping, path)
    _append_device_change_event(events, app, kind, change, path, device_type)


def _append_device_events_for_paths(
    events, app, mapping, kind: str, change: str, paths
) -> None:
    for path in sorted(paths or []):
        _append_device_event_for_path(events, app, mapping, kind, change, path)


def _append_device_change_events(
    events, app, current, baseline, added_paths, removed_paths
) -> None:
    _append_device_events_for_paths(
        events,
        app,
        current,
        "DEVICE NEW",
        "new",
        added_paths,
    )
    _append_device_events_for_paths(
        events,
        app,
        baseline,
        "DEVICE REMOVED",
        "removed",
        removed_paths,
    )


def _device_change_path_sets(
    baseline, current
) -> tuple[set[str], set[str], set[str], set[str]]:
    old_paths, new_paths = _mapping_path_sets(baseline, current)
    return old_paths, new_paths, new_paths - old_paths, old_paths - new_paths


def _finish_scan_device_changes(app, current, events):
    _store_device_baseline(app, current)
    return events


def _device_name_is_input_event(name: str) -> bool:
    return name.startswith("event")


def _device_name_is_mouse(name: str) -> bool:
    return "mouse" in name


def _device_name_is_keyboard(name: str) -> bool:
    return "kbd" in name or "keyboard" in name


def _device_type_for_name(name: str) -> str:
    if _device_name_is_input_event(name):
        return "input-event"
    if _device_name_is_mouse(name):
        return "mouse"
    if _device_name_is_keyboard(name):
        return "keyboard"
    return "hid"


def scan_device_changes(app):
    current, baseline, added_paths, removed_paths = _device_scan_context(app)
    events = []

    _append_device_change_events(
        events, app, current, baseline, added_paths, removed_paths
    )

    return _finish_scan_device_changes(app, current, events)


def device_type_from_path(path):
    return _device_type_for_name(_normalized_device_name(path))


def security_build_baseline(app):
    _run_security_baseline_build(app)


def _build_all_security_baselines(app) -> None:
    app.build_integrity_baseline()
    app.build_device_baseline()
    app.build_input_access_baseline()


def _run_security_baseline_build(app) -> None:
    _build_all_security_baselines(app)
    _finish_security_build_baseline(app)


def _finish_security_build_baseline(app) -> None:
    _run_security_baseline_rebuild_followups(app)


def _run_security_baseline_rebuild_followups(app) -> None:
    _save_security_baseline_callback_safe(app)
    _refresh_connected_devices_safe(app)
    app.log(_security_baseline_rebuilt_log_message(app))
    _refresh_security_table_callback_safe(app)


def _restore_security_baselines(app, data: dict) -> dict:
    raw_integrity = data.get("integrity", {}) or {}
    _store_integrity_baseline(app, sanitize_integrity_baseline(app, raw_integrity))
    _store_device_baseline(app, data.get("device", {}))
    _store_input_access_baseline(app, data.get("input_access", {}))
    return raw_integrity


def _security_baseline_pruned_log_message(app, count: int) -> str:
    return _app_tr(
        app,
        "security_log_baseline_pruned",
        "Security: Baseline bereinigt ({count} NetMon-/Alt-Einträge entfernt).",
    ).format(count=count)


def _security_baseline_rebuilt_log_message(app) -> str:
    return _app_tr(
        app,
        "security_log_baseline_rebuilt",
        "Security: Baseline (File+Device+Input) neu erstellt.",
    )


def _security_baseline_save_error_message(error) -> str:
    return f"Security-Baseline speichern fehlgeschlagen: {error}"


def _log_security_baseline_pruned_if_needed(app, raw_integrity) -> None:
    removed_entries = max(
        len(raw_integrity) - len(_integrity_baseline(app)),
        0,
    )
    if removed_entries <= 0:
        return
    logger = _app_logger(app)
    if callable(logger):
        logger(_security_baseline_pruned_log_message(app, removed_entries))


def _load_security_baseline_data(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_security_baseline_data_for(app) -> dict:
    return _load_security_baseline_data(_security_baseline_path(app))


def _security_baseline_load_context(app) -> tuple[bool, dict | None]:
    if not _security_baseline_exists(app):
        return False, None
    return True, _load_security_baseline_data_for(app)


def _restore_loaded_security_baseline(app, data: dict) -> None:
    raw_integrity = _restore_security_baselines(app, data)
    _log_security_baseline_pruned_if_needed(app, raw_integrity)


def _load_security_baseline_pipeline(app, exists: bool, data: dict | None) -> bool:
    if not exists:
        return False
    _restore_loaded_security_baseline(app, data)
    return True


def _load_existing_security_baseline(app) -> bool:
    return _run_security_baseline_load(app)


def _run_security_baseline_load(app) -> bool:
    exists, data = _security_baseline_load_context(app)
    return _load_security_baseline_pipeline(app, exists, data)


def _load_security_baseline_result(app) -> bool:
    try:
        return _load_existing_security_baseline(app)
    except Exception:
        return False


def load_security_baseline(app):
    return _load_security_baseline_result(app)


def _write_current_security_baseline(app):
    baseline_path, payload = _security_baseline_write_context(app)
    return _write_security_baseline(baseline_path, payload)


def _security_baseline_write_context(app) -> tuple[str, dict]:
    return _security_baseline_path(app), _current_security_baseline_payload(app)


def _log_security_baseline_save_failure(app, error) -> None:
    app.log_debug(_security_baseline_save_error_message(error))


def _save_security_baseline_pipeline(app, ok: bool, err) -> bool:
    if not ok:
        _log_security_baseline_save_failure(app, err)
    return ok


def _save_current_security_baseline_result(app) -> bool:
    return _run_security_baseline_save(app)


def _run_security_baseline_save(app) -> bool:
    ok, err = _write_current_security_baseline(app)
    return _save_security_baseline_pipeline(app, ok, err)


def save_security_baseline(app):
    return _save_current_security_baseline_result(app)


def build_input_access_baseline(app):
    try:
        baseline = app._scan_input_access_state()
    except Exception as exc:
        baseline = {}
        app.log(_input_access_scan_error_message("Baseline", exc))
    return _store_input_access_baseline(app, baseline)


def scan_input_access_changes(app):
    try:
        current = app._scan_input_access_state()
    except Exception as exc:
        app.log(_input_access_scan_error_message("Scan", exc))
        return []
    events = []

    baseline = _input_access_baseline(app)
    old_paths, new_paths = _mapping_path_sets(baseline, current)

    for path in sorted(new_paths):
        old_procs = _input_access_processes(baseline, path)
        new_procs = _input_access_processes(current, path)
        for pid, pname in _input_access_sorted_process_items(new_procs):
            if pid in old_procs:
                continue
            if _input_access_whitelist_status(app, pname, pid):
                continue
            _append_input_access_change_event(
                events,
                app,
                "INPUT ACCESS START",
                "start",
                path,
                pid,
                pname,
                time.time_ns(),
            )

    for path in sorted(old_paths - new_paths):
        old_procs = _input_access_processes(baseline, path)
        for pid, pname in _input_access_sorted_process_items(old_procs):
            if _input_access_whitelist_status(app, pname, pid):
                continue
            _append_input_access_change_event(
                events,
                app,
                "INPUT ACCESS STOP",
                "stop",
                path,
                pid,
                pname,
                time.time_ns(),
            )

    for path in sorted(old_paths & new_paths):
        old_procs = _input_access_processes(baseline, path)
        new_procs = _input_access_processes(current, path)
        for pid, pname in _input_access_sorted_process_items(old_procs):
            if pid in new_procs:
                continue
            if _input_access_whitelist_status(app, pname, pid):
                continue
            _append_input_access_change_event(
                events,
                app,
                "INPUT ACCESS STOP",
                "stop",
                path,
                pid,
                pname,
                time.time_ns(),
            )

    _store_input_access_baseline(app, current)
    return events


def security_create_input_access_event(kind, path, pid, pname, occurrence_token=None):
    level = "INFO"
    raw = f"Security: {kind} {path} pid={pid} name={pname}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token = occurrence_token if occurrence_token is not None else time.time_ns()
    key = f"{kind}|{path}|{pid}|{token}"
    return {
        "time": now,
        "type": kind,
        "src": pname or "-",
        "port": pid,
        "proto": "-",
        "level": level,
        "action": "DETECT",
        "raw": raw,
        "key": key,
        "epoch": time.time(),
        "external": False,
    }


def security_create_file_event(kind, path, occurrence_token=None):
    level = "INFO"
    if "/etc/wireguard" in path:
        level = "WARN"
    elif path.endswith("netmon.py") or os.path.basename(path) in {
        VPN_SLOT_CONFIG_FILE,
        PRIMARY_VPN_SLOT_CONFIG_FILE,
        LINK_SLOT_CONFIG_FILE,
        PRIVACY_CONFIG_FILE,
        HDD_SLOT_CONFIG_FILE,
    }:
        level = "WARN"

    raw = f"Security: {kind} {path}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token = occurrence_token if occurrence_token is not None else time.time_ns()
    key = f"{kind}|{path}|{token}"
    return {
        "time": now,
        "type": kind,
        "src": "-",
        "port": "-",
        "proto": "-",
        "level": level,
        "action": "DETECT",
        "raw": raw,
        "key": key,
        "epoch": time.time(),
        "external": False,
    }


def security_create_device_event(kind, path, devtype, occurrence_token=None):
    level = "INFO"
    if os.path.basename(path).startswith("event"):
        level = "WARN"

    raw = f"Security: {kind} {path} ({devtype})"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    token = occurrence_token if occurrence_token is not None else time.time_ns()
    key = f"{kind}|{path}|{token}"
    return {
        "time": now,
        "type": kind,
        "src": "-",
        "port": "-",
        "proto": "-",
        "level": level,
        "action": "DETECT",
        "raw": raw,
        "key": key,
        "epoch": time.time(),
        "external": False,
    }


def security_input_access_whitelisted(app, proc_name, pid):
    if not proc_name:
        return False
    if pid == os.getpid():
        return True
    if proc_name in app.security_input_access_whitelist:
        return True
    return False


def scan_input_access_state(app):
    state = {}
    input_prefix = "/dev/input"

    if psutil is not None:
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pid = proc.pid
                    pname = (proc.name() or "").strip()
                    for open_file in proc.open_files():
                        path = open_file.path
                        if path.startswith(input_prefix):
                            state.setdefault(path, {})[str(pid)] = pname
                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    continue
        except Exception as exc:
            app.log(f"Security: psutil Input-Access-Scan fehlgeschlagen: {exc}")
        else:
            if state:
                return state

    if os.path.isdir("/proc"):
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            pid = entry
            fd_dir = os.path.join("/proc", pid, "fd")

            try:
                pname = ""
                with open(
                    os.path.join("/proc", pid, "comm"),
                    "r",
                    encoding="utf-8",
                    errors="ignore",
                ) as handle:
                    pname = handle.read().strip()
            except Exception:
                pname = ""

            if not os.path.isdir(fd_dir):
                continue

            try:
                fd_entries = os.listdir(fd_dir)
            except (PermissionError, OSError):
                continue

            for fd in fd_entries:
                try:
                    link = os.readlink(os.path.join(fd_dir, fd))
                except OSError:
                    continue
                if link.startswith(input_prefix):
                    state.setdefault(link, {})[pid] = pname
    return state


def security_export_dir():
    home = os.path.expanduser("~")
    for candidate in _security_export_dir_candidates(home):
        if os.path.isdir(candidate):
            return candidate
    return home


def _security_export_dir_candidates(home: str) -> tuple[str, str]:
    return (
        os.path.join(home, "Schreibtisch"),
        os.path.join(home, "Desktop"),
    )


def _security_export_success_message(app, path: str) -> str:
    return app.tr(
        "security_log_exported",
        "Security-Logs exportiert: {path}",
    ).format(path=path)


def _security_export_failure_log_message(app, error) -> str:
    return app.tr(
        "security_log_export_failed",
        "Security-Export fehlgeschlagen: {error}",
    ).format(error=error)


def _security_export_failure_dialog_message(app, error) -> str:
    return app.tr(
        "security_export_failed_body",
        "Export fehlgeschlagen:\n{error}",
    ).format(error=error)


def _security_export_dialog_title(app) -> str:
    return app.tr("security_export_title", "Security Export")


def _security_export_failure_dialog_args(app, error) -> tuple[str, str]:
    return (
        _security_export_dialog_title(app),
        _security_export_failure_dialog_message(app, error),
    )


def _security_export_failure_messages(app, error) -> tuple[str, str, str]:
    title, message = _security_export_failure_dialog_args(app, error)
    return title, message, _security_export_failure_log_message(app, error)


def _security_export_success(app, path: str) -> None:
    app.log(_security_export_success_message(app, path))


def _security_export_failure(app, error) -> None:
    title, message, log_message = _security_export_failure_messages(app, error)
    messagebox.showerror(
        title,
        message,
        parent=app,
    )
    app.log(log_message)


def _security_export_write_context(
    app, moment: datetime
) -> tuple[str, tuple[str, ...]]:
    path, export_time = _security_export_target(moment, security_export_dir())
    return path, _security_export_blocks_for_app(app, export_time)


def _write_security_export(path: str, blocks) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        _security_export_write_blocks(handle, blocks)


def _run_security_export(app, moment: datetime) -> str:
    path, blocks = _security_export_write_context(app, moment)
    _write_security_export(path, blocks)
    return path


def export_security_logs(app):
    try:
        path = _run_security_export(app, datetime.now())
        _security_export_success(app, path)
    except Exception as exc:
        _security_export_failure(app, exc)


def _scan_ufw_security_events(app) -> list[dict]:
    events: list[dict] = []
    for line in app._read_ufw_log_tail():
        event = app._parse_ufw_block_line(line)
        if not event:
            continue
        if event["key"] in app.security_event_keys:
            continue
        events.append(event)
    return events


def _scan_portscan_findings(app) -> list[dict]:
    findings: list[dict] = []
    for finding in app._security_detect_portscan():
        if finding["key"] in app.security_event_keys:
            continue
        findings.append(finding)
    return findings


def _security_scan_orchestration(
    app,
) -> tuple[list[dict], list[dict], list[dict], list[dict], list[dict]]:
    new_events = _scan_ufw_security_events(app)
    findings = _scan_portscan_findings(app)
    integrity_events = app.scan_integrity_changes()
    device_events = app.scan_device_changes()
    input_access_events = app.scan_input_access_changes()
    return (
        new_events,
        findings,
        integrity_events,
        device_events,
        input_access_events,
    )


def _append_unique_security_events(app, events) -> None:
    for event in events or []:
        if event["key"] in app.security_event_keys:
            continue
        app.security_event_keys.add(event["key"])
        app.security_events.append(event)


def _security_scan_alert_state(
    new_events, findings, integrity_events, device_events, input_access_events
) -> tuple[str, str | None]:
    if findings:
        return "red", "Portscan-Verdacht"
    if any(
        event.get("external") and event.get("type") == "UFW BLOCK"
        for event in (new_events or [])
    ):
        return "yellow", "Neue BLOCK-Events"
    if integrity_events or device_events or input_access_events:
        return "yellow", "Datei-/Geräte-Änderung"
    return "green", None


def _log_harmless_rst_events(app, harmless_rst_events) -> None:
    for event in (harmless_rst_events or [])[:5]:
        app.log(event.get("summary") or "[INFO] harmless return traffic (RST)")
    if len(harmless_rst_events or []) > 5:
        app.log(
            f"[INFO] harmless return traffic (RST): {len(harmless_rst_events)} Ereignisse"
        )


def _finish_security_poll_cycle(app, color: str, harmless_rst_events) -> None:
    _refresh_security_table_callback_safe(app)
    _log_harmless_rst_events(app, harmless_rst_events)
    app._security_update_status(color)
    app.security_scan_running = False
    if app.security_monitoring:
        app.after(5000, app._security_poll_async)


def _finish_security_scan_now(app, new_events, color: str) -> None:
    _append_unique_security_events(app, new_events)
    if new_events:
        app.log_safe(f"Security-Scan: {len(new_events)} neue Events")
    app._refresh_security_table_safe()
    refresh_devices = _app_callback(app, "refresh_connected_device_table")
    if refresh_devices is not None:
        call_in_ui_thread(app, refresh_devices)
    if hasattr(app, "_security_update_status"):
        call_in_ui_thread(app, lambda current=color: app._security_update_status(current))


def _mark_security_scan_running(app) -> bool:
    if app.security_scan_running:
        return False
    app.security_scan_running = True
    return True


def _run_security_poll_job(app) -> None:
    (
        new_events,
        findings,
        integrity_events,
        device_events,
        input_access_events,
    ) = _security_scan_orchestration(app)

    _append_unique_security_events(app, new_events)
    if new_events:
        app.security_events = app.security_events[-1200:]
    _append_unique_security_events(app, findings)
    _append_unique_security_events(app, integrity_events)
    _append_unique_security_events(app, device_events)
    _append_unique_security_events(app, input_access_events)

    harmless_rst_events = [
        event for event in new_events if event.get("type") == "HARMLESS RETURN TRAFFIC"
    ]
    color, alarm_text = _security_scan_alert_state(
        new_events,
        findings,
        integrity_events,
        device_events,
        input_access_events,
    )
    if alarm_text is not None:
        app.security_last_alarm = alarm_text

    def done():
        _finish_security_poll_cycle(app, color, harmless_rst_events)

    call_in_ui_thread(app, done)


def security_poll_async(app):
    if not app.security_monitoring or not _mark_security_scan_running(app):
        return

    def job():
        _run_security_poll_job(app)

    _start_security_scan_thread(job)


def _ensure_security_log_level(app) -> None:
    if _refresh_security_log_level_safe(app, log_failures=True):
        return
    app.security_log_level = "–"
    app.log(
        app.tr(
            "security_log_level_query_unavailable",
            "Security: Log-Level-Abfrage nicht verfügbar, Fallback '–'.",
        )
    )


def _finish_security_start_monitoring(app) -> None:
    app.log(
        app.tr(
            "security_log_monitoring_started",
            _security_monitoring_log_message("started"),
        )
    )
    app._security_update_status("green")
    app._security_poll_async()


def _finish_security_stop_monitoring(app) -> None:
    app.log(
        app.tr(
            "security_log_monitoring_stopped",
            _security_monitoring_log_message("stopped"),
        )
    )
    app._security_update_status("gray")


def security_start_monitoring(app):
    if app.security_monitoring:
        app.log(
            app.tr(
                "security_log_monitoring_already_running",
                _security_monitoring_log_message("already_running"),
            )
        )
        return
    app.security_monitoring = True
    _ensure_security_log_level(app)
    _finish_security_start_monitoring(app)


def security_stop_monitoring(app):
    app.security_monitoring = False
    app.security_scan_running = False
    _finish_security_stop_monitoring(app)


def _begin_security_scan(app) -> bool:
    if not _mark_security_scan_running(app):
        app.log(_security_scan_log_message("already_running"))
        return False
    return True


def _start_security_scan_thread(job) -> None:
    threading.Thread(target=job, daemon=True).start()


def _run_security_scan_now_job(app) -> None:
    new_events = []
    color = "green"
    try:
        (
            ufw_events,
            findings,
            integrity_events,
            device_events,
            input_access_events,
        ) = _security_scan_orchestration(app)
        new_events.extend(ufw_events)
        new_events.extend(findings)
        new_events.extend(integrity_events)
        new_events.extend(device_events)
        new_events.extend(input_access_events)

        color, alarm_text = _security_scan_alert_state(
            ufw_events,
            findings,
            integrity_events,
            device_events,
            input_access_events,
        )
        if alarm_text is not None:
            app.security_last_alarm = alarm_text
    except Exception as exc:
        app.log_safe(f"Security-Scan fehlgeschlagen: {exc}")
    finally:
        app.security_scan_running = False

    _finish_security_scan_now(app, new_events, color)


def security_scan_now(app):
    if not _begin_security_scan(app):
        return

    def job():
        _run_security_scan_now_job(app)

    _start_security_scan_thread(job)


def _finish_security_input_access_scan(app, events) -> None:
    _append_unique_security_events(app, events)
    if events:
        app.log_safe(f"Input-Zugriffscheck: {len(events)} neue Events")
    app._refresh_security_table_safe()


def _run_security_input_access_scan_job(app) -> None:
    events = []
    try:
        events.extend(app.scan_input_access_changes())
    except Exception as exc:
        app.log_safe(f"Input-Zugriffscheck fehlgeschlagen: {exc}")
    finally:
        app.security_scan_running = False

    _finish_security_input_access_scan(app, events)


def security_input_access_scan(app):
    if not _begin_security_scan(app):
        return

    def job():
        _run_security_input_access_scan_job(app)

    _start_security_scan_thread(job)
