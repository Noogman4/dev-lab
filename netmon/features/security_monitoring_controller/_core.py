"""Security monitoring controller helpers for NetMon."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from datetime import datetime
from tkinter import messagebox

try:
    import psutil
except ModuleNotFoundError:
    psutil = None

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.core.utils import safe_write_json, call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import safe_write_json, call_in_ui_thread

try:
    from netmon.config.constants import (
        HDD_SLOT_CONFIG_FILE,
        LINK_SLOT_CONFIG_FILE,
        PRIMARY_VPN_SLOT_CONFIG_FILE,
        PRIVACY_CONFIG_FILE,
        VPN_SLOT_CONFIG_FILE,
    )
except ModuleNotFoundError:
    from config.constants import (
        HDD_SLOT_CONFIG_FILE,
        LINK_SLOT_CONFIG_FILE,
        PRIMARY_VPN_SLOT_CONFIG_FILE,
        PRIVACY_CONFIG_FILE,
        VPN_SLOT_CONFIG_FILE,
    )


def _app_value(app, name, default=""):
    state = getattr(app, "__dict__", {}) or {}
    if name in state:
        return state.get(name, default)
    try:
        return object.__getattribute__(app, name)
    except Exception:
        return default


def _app_logger(app):
    for name in ("log_safe", "log"):
        logger = _app_value(app, name, None)
        if callable(logger):
            return logger
    return None


def _app_callback(app, name):
    callback = _app_value(app, name, None)
    return callback if callable(callback) else None


def _app_tr(app, key, default):
    tr = _app_value(app, "tr", None)
    if callable(tr):
        try:
            return tr(key, default)
        except Exception:
            return default
    return default


def _refresh_security_log_level_safe(app, *, log_failures=False):
    refresh_fn = _app_callback(app, "refresh_security_log_level")
    if refresh_fn is None:
        return False
    refresh_fn(log_failures=log_failures)
    return True


def _refresh_connected_devices_safe(app):
    refresh_devices = _app_callback(app, "refresh_connected_device_table")
    if refresh_devices is None:
        return False
    refresh_devices()
    return True


def _refresh_security_table_callback_safe(app):
    refresh_table = _app_callback(app, "_refresh_security_table")
    if refresh_table is None:
        return False
    refresh_table()
    return True


def _save_security_baseline_callback_safe(app):
    save_fn = _app_callback(app, "_save_security_baseline")
    if save_fn is None:
        return False
    save_fn()
    return True


def _clear_table_rows(table) -> bool:
    if table is None:
        return False
    try:
        table.delete(*table.get_children())
    except Exception:
        return False
    return True


def _security_detail_widget(app):
    return _app_widget_value(app, "security_detail")


def _security_table(app):
    return _app_widget_value(app, "security_table")


def _security_table_row_meta(app):
    return _app_dict_value(app, "security_table_row_meta")


def _app_list_value(app, name: str):
    return list(_app_value(app, name, []) or [])


def _app_dict_value(app, name: str):
    return dict(_app_value(app, name, {}) or {})


def _app_str_value(app, name: str, default: str):
    return str(_app_value(app, name, default) or default)


def _app_widget_value(app, name: str):
    return _app_value(app, name, None)


def _app_bool_value(app, name: str):
    return bool(_app_value(app, name, False))


def _security_monitoring_active(app) -> bool:
    return _app_bool_value(app, "security_monitoring")


def _security_visible_events(app):
    return _app_list_value(app, "security_visible_events")


def _security_events(app):
    return _app_list_value(app, "security_events")


def _security_event_count(app) -> int:
    return len(_security_events(app))


def _security_aggregated(app):
    return _app_dict_value(app, "security_aggregated")


def _security_last_alarm(app):
    return _app_str_value(app, "security_last_alarm", "–")


def _security_log_level(app, default: str = "-"):
    return _app_str_value(app, "security_log_level", default)


def _device_baseline(app):
    return _app_dict_value(app, "device_baseline")


def _store_device_baseline(app, baseline: dict) -> dict:
    app.device_baseline = baseline
    return baseline


def _integrity_baseline(app):
    return _app_dict_value(app, "integrity_baseline")


def _store_integrity_baseline(app, baseline: dict) -> dict:
    app.integrity_baseline = baseline
    return baseline


def _input_access_baseline(app):
    return _app_dict_value(app, "input_access_baseline")


def _store_input_access_baseline(app, baseline: dict) -> dict:
    app.input_access_baseline = baseline
    return baseline


def _input_access_processes(mapping, path: str):
    return dict((mapping or {}).get(path, {}) or {})


def _device_type(mapping, path: str, default: str = "unknown"):
    return str((mapping or {}).get(path, default) or default)


def _integrity_entry_token(entry) -> str:
    entry = dict(entry or {})
    return f"{entry.get('sha', '')}|{entry.get('size', '')}|{entry.get('mtime', '')}"


def _integrity_entry(mapping, path: str):
    return dict((mapping or {}).get(path, {}) or {})


def _mapping_paths(mapping) -> set[str]:
    return set(dict(mapping or {}).keys())


def _mapping_path_sets(baseline, current) -> tuple[set[str], set[str]]:
    return _mapping_paths(baseline), _mapping_paths(current)


def _input_access_change_token(
    change: str, pname, path: str, pid, occurrence_token
) -> str:
    return f"{change}|{pname}|{path}|{pid}|{occurrence_token}"


def _append_input_access_change_event(
    events,
    app,
    kind: str,
    change: str,
    path: str,
    pid,
    pname,
    occurrence_token,
) -> None:
    token = _input_access_change_token(change, pname, path, pid, occurrence_token)
    events.append(
        app._security_create_input_access_event(kind, path, pid, pname, token)
    )


def _append_integrity_change_event(events, app, kind: str, path: str, entry) -> None:
    token = _integrity_entry_token(entry)
    events.append(app._security_create_file_event(kind, path, token))


def _append_device_change_event(
    events, app, kind: str, change: str, path: str, device_type: str
) -> None:
    token = f"{change}|{device_type}"
    events.append(app._security_create_device_event(kind, path, device_type, token))


def _integrity_file_entry(app, path: str, stat_result) -> dict:
    return {
        "sha": app.hash_file_sha256(path),
        "size": stat_result.st_size,
        "mtime": stat_result.st_mtime,
    }


def _integrity_scan_state(app) -> dict:
    current = {}
    for path in app._integrity_watch_files():
        if security_integrity_ignore_path(app, path):
            continue
        if not os.path.isfile(path):
            continue
        try:
            stat_result = os.stat(path)
        except Exception:
            continue
        current[path] = _integrity_file_entry(app, path, stat_result)
    return current


def _device_type_for_path(app, path: str) -> str:
    return str(app._device_type_from_path(path))


def _device_watch_paths_for(app) -> list:
    return app._device_watch_paths()


def _device_type_mapping(app) -> dict:
    return {
        path: _device_type_for_path(app, path) for path in _device_watch_paths_for(app)
    }


def _connected_device_entry(
    app, path: str, base: str, preferred_path: str, baseline
) -> dict:
    return {
        "name": _device_display_name(path),
        "path": preferred_path,
        "sys_name": base,
        "type": _device_type_for_path(app, path),
        "known_in_baseline": path in baseline or preferred_path in baseline,
        **_device_metadata(path),
    }


def _preferred_connected_device_path(path: str, existing) -> str:
    preferred_path = path
    if existing is not None and str(existing.get("path", "")).startswith("/dev/input/"):
        preferred_path = existing["path"]
    elif path.startswith("/dev/input/"):
        preferred_path = path
    return preferred_path


def _store_connected_device(devices: dict, app, path: str, base: str, baseline) -> None:
    existing = devices.get(base)
    preferred_path = _preferred_connected_device_path(path, existing)
    devices[base] = _connected_device_entry(app, path, base, preferred_path, baseline)


def _sorted_connected_device_inventory(devices: dict) -> list:
    return [devices[key] for key in sorted(devices)]


def _security_filter_mode(app):
    return _app_str_value(app, "security_filter_mode", "all")


def _security_runtime_context(app) -> dict:
    return {
        "monitoring_active": _security_monitoring_active(app),
        "logging_level": _security_log_level(app),
        "event_count": _security_event_count(app),
        "last_alarm": _security_last_alarm(app),
    }


def _security_reporting_context(app) -> dict:
    return {
        **_security_runtime_context(app),
        "events": _security_events(app),
        "visible_events": _security_visible_events(app),
        "aggregated": _security_aggregated(app),
        "filter_mode": _security_filter_mode(app),
        "integrity_baseline": _integrity_baseline(app),
        "device_baseline": _device_baseline(app),
        "input_access_baseline": _input_access_baseline(app),
    }



def _security_baseline_payload(app, timestamp: str) -> dict:
    return {**_security_baseline_state(app), "ts": timestamp}


def _current_security_baseline_payload(app) -> dict:
    return _security_baseline_payload(app, datetime.now().isoformat())


def _security_baseline_path(app) -> str:
    return _app_str_value(app, "security_baseline_path", "")


def _security_baseline_exists(app) -> bool:
    return os.path.isfile(_security_baseline_path(app))


def _write_security_baseline(path: str, payload: dict):
    return safe_write_json(
        path,
        payload,
        indent=2,
        ensure_ascii=False,
    )


def _connected_devices_inventory(app):
    return _app_list_value(app, "connected_devices_inventory")


def _selected_table_row_index(row_id: str):
    try:
        return int(str(row_id).split("-", 1)[1])
    except Exception:
        return None


def _selected_connected_device(app, table):
    row_id = _selected_table_row_id(table)
    if not row_id:
        return None
    idx = _selected_table_row_index(row_id)
    if idx is None:
        return None
    inventory = _connected_devices_inventory(app)
    if idx < 0 or idx >= len(inventory):
        return None
    return inventory[idx]


def _selected_table_row_id(table) -> str:
    if table is None:
        return ""
    try:
        selection = tuple(table.selection())
    except Exception:
        selection = ()
    if not selection:
        return ""
    return str(selection[0] or "").strip()


def _security_selected_event_text(app, row_id: str, meta: dict) -> str:
    if meta.get("kind") == "aggregate":
        return str(meta.get("raw", "") or "")
    idx = meta.get("index")
    if idx is None:
        idx = _selected_table_row_index(row_id)
        if idx is None:
            return ""
    view = _security_visible_events(app)
    if idx < 0 or idx >= len(view):
        return ""
    event = view[idx]
    return str(event.get("raw", "") or "")


def _selected_security_event_text(app, table) -> str:
    row_id = _selected_table_row_id(table)
    if not row_id:
        return ""
    meta = _security_table_row_meta(app).get(row_id, {})
    return _security_selected_event_text(app, row_id, meta)


def _connected_device_baseline_text(device) -> str:
    return (
        "Baseline: bekannt"
        if (device or {}).get("known_in_baseline")
        else "Baseline: neu/nicht in Baseline"
    )


def _connected_device_field(device, key: str, default: str) -> str:
    return str((device or {}).get(key, default) or default)


def _connected_device_field_lines(device) -> list[str]:
    return [
        f"Typ: {_connected_device_field(device, 'type', 'unknown')}",
        f"Pfad: {_connected_device_field(device, 'path', '-')}",
        f"Kennung: {_connected_device_field(device, 'sys_name', '-')}",
        f"Vendor-ID: {_connected_device_field(device, 'vendor', '-')}",
        f"Product-ID: {_connected_device_field(device, 'product', '-')}",
        f"Bus-Typ: {_connected_device_field(device, 'bustype', '-')}",
        f"Phys: {_connected_device_field(device, 'phys', '-')}",
        f"Unique-ID: {_connected_device_field(device, 'uniq', '-')}",
    ]


def _connected_device_name(device) -> str:
    return _connected_device_field(device, "name", "Unbekannt")


def _connected_device_inventory_entry_lines(index: int, device) -> list[str]:
    return [
        f"[{index}] {_connected_device_name(device)}",
        *_connected_device_field_lines(device),
        _connected_device_baseline_text(device),
        "",
    ]


def _connected_device_inventory_header_lines(inventory, baseline) -> list[str]:
    return [
        "=== Aktuell verbundene Geräte ===",
        "",
        f"Anzahl erkannter Geräte: {len(inventory or [])}",
        f"Device-Baseline Einträge: {len(baseline or {})}",
        "",
    ]


def _connected_device_inventory_empty_message() -> str:
    return "Keine verbundenen Geräte erkannt."


def _connected_device_inventory_body_lines(inventory) -> list[str]:
    lines: list[str] = []
    for idx, item in enumerate(inventory or [], start=1):
        lines.extend(_connected_device_inventory_entry_lines(idx, item))
    return lines


def _connected_device_inventory_lines(inventory, baseline) -> list[str]:
    lines = _connected_device_inventory_header_lines(inventory, baseline)
    if not inventory:
        lines.append(_connected_device_inventory_empty_message())
        return lines
    lines.extend(_connected_device_inventory_body_lines(inventory))
    return lines


def _connected_device_inventory_text(lines) -> str:
    return "\n".join(lines or []).rstrip() + "\n"


def _connected_device_inventory_context(app):
    return (
        connected_device_inventory(app),
        _device_baseline(app),
    )


def _connected_device_inventory_text_for(inventory, baseline) -> str:
    return _connected_device_inventory_text(
        _connected_device_inventory_lines(inventory, baseline)
    )


def _connected_device_detail_text(device) -> str:
    lines = [
        "=== Verbundenes Gerät ===",
        "",
        f"Name: {_connected_device_name(device)}",
        *_connected_device_field_lines(device),
        _connected_device_baseline_text(device),
    ]
    return "\n".join(lines) + "\n"


def _normalized_security_state(state) -> str:
    return str(state or "").strip().lower()


def _security_monitoring_log_message(state: str) -> str:
    return {
        "already_running": "Security Monitoring läuft bereits.",
        "started": "Security Monitoring gestartet.",
        "stopped": "Security Monitoring gestoppt.",
    }.get(_normalized_security_state(state), "Security Monitoring unbekannt.")


def _security_scan_log_message(state: str) -> str:
    return {
        "already_running": "Security-Scan läuft bereits.",
    }.get(_normalized_security_state(state), "Security-Scan unbekannt.")


def _security_monitoring_status_text(active) -> str:
    return "AKTIV" if active else "AUS"


def _security_status_text(prefix: str, value) -> str:
    return f"{prefix}: {value}"


def _security_monitoring_status_line(active, prefix: str = "Monitoring") -> str:
    return _security_status_text(prefix, _security_monitoring_status_text(active))


def _security_last_alarm_text(last_alarm) -> str:
    return _security_status_text("Letzter Alarm", last_alarm)


def _security_logging_level_text(level, prefix: str = "Logging") -> str:
    return _security_status_text(prefix, level)


def _security_events_count_text(count, prefix: str = "Events") -> str:
    return _security_status_text(prefix, count)


def _security_header_lines(title: str, width: int) -> list[str]:
    return [title, "=" * max(0, int(width)), ""]


def _security_event_field(event, key: str, default: str = "-") -> str:
    return str((event or {}).get(key, default) or default)


def _security_event_summary_line(event, *, include_proto: bool = True) -> str:
    parts = [
        f"Zeit={_security_event_field(event, 'time')}",
        f"Typ={_security_event_field(event, 'type')}",
        f"Level={_security_event_field(event, 'level')}",
        f"Quelle={_security_event_field(event, 'src')}",
        f"Port={_security_event_field(event, 'port')}",
    ]
    if include_proto:
        parts.append(f"Proto={_security_event_field(event, 'proto')}")
    parts.append(f"Aktion={_security_event_field(event, 'action')}")
    return "- " + "; ".join(parts)


def _security_export_event_table_line(event) -> str:
    return (
        f"{_security_event_field(event, 'time')} | "
        f"{_security_event_field(event, 'type')} | "
        f"{_security_event_field(event, 'src')} | "
        f"{_security_event_field(event, 'port')} | "
        f"{_security_event_field(event, 'proto')} | "
        f"{_security_event_field(event, 'level')} | "
        f"{_security_event_field(event, 'action')}\n"
    )


def _security_export_event_detail_header_line(index: int, event) -> str:
    return (
        f"[{index}] {_security_event_field(event, 'time')} "
        f"{_security_event_field(event, 'type')}\n"
    )


def _security_export_event_raw_block(event) -> str:
    return str((event or {}).get("raw") or "-") + "\n\n"


def _append_security_section(lines: list[str], title: str) -> None:
    lines.append("")
    lines.append(title)


def _security_export_count_line(label: str, count) -> str:
    return f"{label}: {count}"


def _security_export_count_block(label: str, count) -> str:
    return _security_export_count_line(label, count) + "\n"


def _security_export_aggregate_line(category, count) -> str:
    return f"Aggregiert {category}: {count}\n"


def _security_export_event_table_header_line() -> str:
    return "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n"


def _security_export_time_line(timestamp: str) -> str:
    return f"Exportzeit: {timestamp}\n"


def _security_export_status_block(text: str) -> str:
    return f"{text}\n"


def _security_export_status_blocks(
    monitoring_active, logging_level, event_count
) -> tuple[str, str, str]:
    return (
        _security_export_status_block(
            _security_monitoring_status_line(monitoring_active, "Monitoring-Status")
        ),
        _security_export_status_block(
            _security_logging_level_text(logging_level, "UFW Logging-Level")
        ),
        _security_export_status_block(
            _security_events_count_text(event_count, "Anzahl Events")
        ),
    )


def _security_export_path(export_dir: str, stamp: str) -> str:
    return os.path.join(export_dir, f"netmon_security_log_{stamp}.txt")


def _security_export_header_block() -> str:
    return "\n".join(_security_header_lines("NetMon Security Export", 24))


def _security_export_summary_section_block() -> str:
    return _security_export_section_block("SECURITY SUMMARY", 20)


def _security_export_events_section_block() -> str:
    return _security_export_section_block("SECURITY EVENTS", 120)


def _security_export_details_section_block() -> str:
    return _security_export_section_block("DETAIL / ROHDATEN", 120)


def _security_export_details_section_with_spacing() -> str:
    return "\n" + _security_export_details_section_block()


def _security_export_summary_count_blocks(events) -> tuple[str, ...]:
    return (
        _security_export_count_block(
            "Externe UFW-Blocks",
            len([e for e in events if e.get("type") == "UFW BLOCK"]),
        ),
        _security_export_count_block(
            "Portscan-Verdacht",
            len([e for e in events if "PORTSCAN" in str(e.get("type", "")).upper()]),
        ),
        _security_export_count_block(
            "Dateiänderungen",
            len([e for e in events if e.get("type", "").startswith("FILE")]),
        ),
        _security_export_count_block(
            "Device-Änderungen",
            len([e for e in events if e.get("type", "").startswith("DEVICE")]),
        ),
        _security_export_count_block(
            "Input-Access",
            len([e for e in events if "INPUT ACCESS" in e.get("type", "")]),
        ),
    )


def _security_export_aggregate_blocks(aggregated) -> tuple[str, ...]:
    return tuple(
        _security_export_aggregate_line(category, count)
        for category, count in dict(aggregated or {}).items()
    )


def _security_export_event_detail_blocks(events) -> tuple[str, ...]:
    blocks: list[str] = []
    for idx, event in enumerate(list(events or []), start=1):
        blocks.append(_security_export_event_detail_header_line(idx, event))
        blocks.append(_security_export_event_raw_block(event))
    return tuple(blocks)


def _security_export_event_blocks(events) -> tuple[str, ...]:
    return (
        _security_export_events_section_block(),
        _security_export_event_table_header_line(),
        *tuple(
            _security_export_event_table_line(event) for event in list(events or [])
        ),
    )


def _security_export_details_blocks(events) -> tuple[str, ...]:
    return (
        _security_export_details_section_with_spacing(),
        *tuple(_security_export_event_detail_blocks(events)),
    )


def _security_export_summary_blocks(events, aggregated) -> tuple[str, ...]:
    return (
        _security_export_summary_section_block(),
        *tuple(_security_export_summary_count_blocks(events)),
        *tuple(_security_export_aggregate_blocks(aggregated)),
        "\n",
    )


def _security_export_intro_blocks(
    export_time: str, monitoring_active, logging_level, event_count, last_alarm
) -> tuple[str, ...]:
    return (
        _security_export_header_block(),
        _security_export_time_line(export_time),
        *tuple(
            _security_export_status_blocks(
                monitoring_active,
                logging_level,
                event_count,
            )
        ),
        _security_export_last_alarm_block(last_alarm),
    )


def _security_export_content_blocks(events, aggregated) -> tuple[str, ...]:
    return (
        *tuple(_security_export_summary_blocks(events, aggregated)),
        *tuple(_security_export_event_blocks(events)),
        *tuple(_security_export_details_blocks(events)),
    )


def _security_export_blocks(
    export_time: str,
    monitoring_active,
    logging_level,
    event_count,
    last_alarm,
    events,
    aggregated,
) -> tuple[str, ...]:
    return (
        *tuple(
            _security_export_intro_blocks(
                export_time,
                monitoring_active,
                logging_level,
                event_count,
                last_alarm,
            )
        ),
        *tuple(_security_export_content_blocks(events, aggregated)),
    )


def _security_export_blocks_for_app(app, export_time: str) -> tuple[str, ...]:
    context = _security_reporting_context(app)
    return _security_export_blocks(
        export_time,
        context["monitoring_active"],
        _security_log_level(app, ""),
        context["event_count"],
        context["last_alarm"],
        context["events"],
        context["aggregated"],
    )


def _security_export_target(moment: datetime, export_dir: str) -> tuple[str, str]:
    stamp, export_time = _security_export_datetime_formats(moment)
    return _security_export_path(export_dir, stamp), export_time


def _security_export_write_blocks(handle, blocks) -> None:
    for block in tuple(blocks or ()):
        handle.write(block)


def _security_export_section_lines(title: str, width: int) -> list[str]:
    return [title, "-" * max(0, int(width))]


def _security_export_section_block(title: str, width: int) -> str:
    return "\n".join(_security_export_section_lines(title, width)) + "\n"


def _security_export_last_alarm_block(last_alarm) -> str:
    return _security_last_alarm_text(last_alarm) + "\n\n"


def _security_status_values(
    monitoring_active, logging_level, event_count, last_alarm
) -> tuple[str, str, str, str]:
    return (
        _security_monitoring_status_line(monitoring_active),
        _security_logging_level_text(logging_level),
        _security_events_count_text(event_count),
        _security_last_alarm_text(last_alarm),
    )


def security_update_status(app, color):
    _refresh_security_log_level_safe(app, log_failures=False)
    app.set_light(app.l_sec, color)
    context = _security_runtime_context(app)
    status, level, count, alarm = _security_status_values(
        context["monitoring_active"],
        context["logging_level"],
        context["event_count"],
        context["last_alarm"],
    )
    app.security_status_var.set(status)
    app.security_level_var.set(level)
    app.security_count_var.set(count)
    app.security_alarm_var.set(alarm)


def security_open_tab(app):
    app._select_security_tab(app.tab_security)
    _refresh_connected_devices_safe(app)


def _prepare_security_chad_analysis(app, title: str, summary_builder) -> None:
    app.prepare_chad_analysis(title, summary_builder(app))


def prepare_security_chad_analysis(app):
    _prepare_security_chad_analysis(
        app, "Security Analyse", build_security_chad_summary
    )


def prepare_security_chad_curated_analysis(app):
    _prepare_security_chad_analysis(
        app, "Security Kurzcheck", build_security_chad_curated_summary
    )


def prepare_security_chad_technical_analysis(app):
    _prepare_security_chad_analysis(
        app, "Security Tiefenanalyse", build_security_chad_summary
    )


def _normalized_security_filter_mode(filter_mode) -> str:
    return str(filter_mode or "all")


def _security_filter_label_or_default(filter_mode, default: str = "Unbekannt") -> str:
    return {
        "all": "Alle Events",
        "portscan": "Nur Portscan",
        "relevant": "Nur Warnungen/Alarme",
        "external": "Nur externe UFW-Blocks",
    }.get(_normalized_security_filter_mode(filter_mode), default)


def _security_filter_label(filter_mode: str) -> str:
    return _security_filter_label_or_default(filter_mode)


def _security_filter_log_message(filter_mode: str) -> str:
    return "Security-Filter: {label}.".format(
        label=_security_filter_label_or_default(filter_mode, "Alle Events")
    )


def _security_connected_devices_log_message(count: int) -> str:
    return "Security: {count} verbundene Geräte angezeigt.".format(
        count=max(0, int(count))
    )


def _security_table_refreshed_log_message() -> str:
    return "Security-Tabelle aktualisiert."


def _security_views_cleared_log_message() -> str:
    return "Guards-Tab: Ansichten geleert."


def _security_events_cleared_log_message() -> str:
    return "Security-Events geleert."


def _security_events_clear_cancelled_log_message() -> str:
    return "Security-Events leeren abgebrochen."


def _security_views_cleared_detail_text() -> str:
    return "Ansichten im Guards-Tab wurden geleert."


def _security_clear_events_title() -> str:
    return "Security-Events leeren"


def _security_clear_events_body() -> str:
    return "Die aktuell angezeigten Security-Events werden entfernt.\n\nFortfahren?"


def _security_clear_events_dialog_args(app) -> tuple[str, str]:
    return (
        app.tr("security_clear_title", _security_clear_events_title()),
        app.tr(
            "security_clear_body",
            _security_clear_events_body(),
        ),
    )


def _confirm_security_clear_events(app, confirm: bool) -> bool:
    if not (confirm and _security_events(app)):
        return True
    title, body = _security_clear_events_dialog_args(app)
    ok = messagebox.askyesno(
        title,
        body,
        parent=app,
    )
    if ok:
        return True
    app.log(
        app.tr(
            "security_log_clear_cancelled",
            _security_events_clear_cancelled_log_message(),
        )
    )
    return False


def _reset_security_event_state(app) -> None:
    app.security_events = []
    app.security_event_keys = set()
    app.security_visible_events = []
    app.security_last_portscan_alert = {}
    app.security_aggregated = {}
    app.security_dedup_cache = {}
    app.security_last_alarm = "–"


def _security_clear_events_status_color(app) -> str:
    return "green" if _security_monitoring_active(app) else "gray"


def _reset_security_view_state(app) -> None:
    app.security_visible_events = []
    app.security_table_row_meta = {}
    app.input_access_row_meta = {}


def _security_view_tables(app):
    return (
        _security_table(app),
        _connected_device_table(app),
        _input_access_table(app),
    )


def _clear_security_view_tables(app) -> None:
    for table in _security_view_tables(app):
        _clear_table_rows(table)


def _run_security_clear_events(app) -> None:
    _reset_security_event_state(app)
    app.security_detail.delete("1.0", "end")
    refresh_security_table(app)
    security_update_status(app, _security_clear_events_status_color(app))
    app.log(
        app.tr(
            "security_log_cleared",
            _security_events_cleared_log_message(),
        )
    )
    return None


def _run_security_clear_views(app) -> None:
    _clear_security_view_tables(app)
    _reset_security_view_state(app)
    _finish_security_clear_views(app)


def _connected_device_known_in_baseline(device) -> bool:
    return bool((device or {}).get("known_in_baseline"))


def _connected_device_status_label(device) -> str:
    return "bekannt" if _connected_device_known_in_baseline(device) else "neu"


def _connected_device_row_tags(device) -> tuple[str, ...]:
    return (
        ("device_known",)
        if _connected_device_known_in_baseline(device)
        else ("device_new",)
    )


def _connected_device_row_values(device) -> tuple:
    item = dict(device or {})
    return (
        _connected_device_name(item),
        _connected_device_field(item, "type", "unknown"),
        _connected_device_field(item, "vendor", "-"),
        _connected_device_field(item, "product", "-"),
        _connected_device_status_label(item),
        _connected_device_field(item, "path", "-"),
    )


def _security_event_level(event) -> str:
    return str((event or {}).get("level", "")).upper()


def _security_event_is_relevant(event) -> bool:
    level = _security_event_level(event)
    return (
        "WARN" in level
        or "ALERT" in level
        or "CRITICAL" in level
        or (event or {}).get("type") == "Portscan-Verdacht"
    )


def _security_summary_counts(
    *, portscan_count: int, block_count: int, relevant_count: int
) -> dict:
    return {
        "portscan_count": max(0, int(portscan_count)),
        "block_count": max(0, int(block_count)),
        "relevant_count": max(0, int(relevant_count)),
    }


def _security_summary_risk_label(
    *, portscan_count: int, block_count: int, relevant_count: int
) -> str:
    counts = _security_summary_counts(
        portscan_count=portscan_count,
        block_count=block_count,
        relevant_count=relevant_count,
    )
    if counts["portscan_count"] > 0:
        return "Hoch"
    if counts["relevant_count"] >= 3 or counts["block_count"] >= 10:
        return "Mittel"
    if counts["relevant_count"] > 0 or counts["block_count"] > 0:
        return "Niedrig bis mittel"
    return "Niedrig"


def _security_summary_immediate_actions(
    *, portscan_count: int, block_count: int, relevant_count: int
):
    counts = _security_summary_counts(
        portscan_count=portscan_count,
        block_count=block_count,
        relevant_count=relevant_count,
    )
    actions = []
    if counts["portscan_count"] > 0:
        actions.append(
            "Portscan-Quelle und betroffene Ziel-Ports priorisiert prüfen, Firewall-Regeln und exponierte Dienste verifizieren."
        )
    if counts["block_count"] > 0:
        actions.append(
            "Externe BLOCK-Events nach wiederkehrenden Quell-IP-Adressen und häufigen Ziel-Ports clustern."
        )
    if counts["relevant_count"] > 0:
        actions.append(
            "WARN/ALERT/CRITICAL-Events gegen bekannte Änderungen, geplante Admin-Aktionen und Baseline abgleichen."
        )
    if not actions:
        actions.append(
            "Keine akuten Security-Hinweise sichtbar; Baseline aktuell halten und Monitoring weiterlaufen lassen."
        )
    return actions[:3]


def _build_security_chad_summary(app, *, include_technical_sections: bool) -> str:
    context = _security_reporting_context(app)
    events = context["events"]
    visible_events = context["visible_events"]

    total = len(events)
    visible = len(visible_events)

    top_ip = "–"
    top_port = "–"
    block_count = 0
    portscan_count = 0

    if _app_value(app, "security_store", None) is not None:
        try:
            total_stats, block_count, portscan_count, top_ip, top_port = (
                app.security_store.compute_stats(events)
            )
            total = total_stats
        except Exception:
            pass

    relevant = [event for event in events if _security_event_is_relevant(event)]

    latest_relevant = relevant[-10:]
    latest_external = [event for event in events if event.get("external")][-10:]
    latest_overall = events[-5:]
    aggregated = context["aggregated"]
    filter_mode = context["filter_mode"]
    monitoring_active = context["monitoring_active"]
    logging_level = context["logging_level"]
    last_alarm = context["last_alarm"]
    integrity_baseline = context["integrity_baseline"]
    device_baseline = context["device_baseline"]
    input_access_baseline = context["input_access_baseline"]
    risk_label = _security_summary_risk_label(
        portscan_count=portscan_count,
        block_count=block_count,
        relevant_count=len(relevant),
    )
    immediate_actions = _security_summary_immediate_actions(
        portscan_count=portscan_count,
        block_count=block_count,
        relevant_count=len(relevant),
    )

    lines = _security_header_lines("NetMon Security-Zusammenfassung", 32)
    lines.append("Executive Summary:")
    lines.append(f"- Risiko-Einschätzung: {risk_label}")
    lines.append(
        f"- {_security_monitoring_status_line(monitoring_active)} | {_security_logging_level_text(logging_level, 'Logging-Level')} | {_security_last_alarm_text(last_alarm)}"
    )
    lines.append(
        f"- Events gesamt: {total} | sichtbar im aktuellen Filter: {visible} | Filter: {_security_filter_label(filter_mode)}"
    )
    lines.append(f"Externe UFW BLOCK Events: {block_count}")
    lines.append(f"Portscan-Verdacht Events: {portscan_count}")
    lines.append(f"Top externe IP: {top_ip}")
    lines.append(f"Top Port: {top_port}")

    _append_security_section(lines, "Sofortmaßnahmen für Chad:")
    for action in immediate_actions:
        lines.append(f"- {action}")

    _append_security_section(lines, "Baseline- und Kontextstatus:")
    lines.append(f"- File-Baseline Einträge: {len(integrity_baseline)}")
    lines.append(f"- Device-Baseline Einträge: {len(device_baseline)}")
    lines.append(f"- Input-Access-Baseline Einträge: {len(input_access_baseline)}")
    lines.append(f"- Relevante Events insgesamt: {len(relevant)}")
    if aggregated:
        lines.append(
            "- Aggregierte interne Kategorien: "
            + ", ".join(f"{key}={value}" for key, value in sorted(aggregated.items()))
        )
    else:
        lines.append("- Aggregierte interne Kategorien: keine")

    _append_security_section(lines, "Wichtigste relevante Events:")
    if latest_relevant:
        for event in latest_relevant:
            lines.append(_security_event_summary_line(event))
    else:
        lines.append("- Keine relevanten WARN/ALERT/CRITICAL/Portscan-Events gefunden.")

    if include_technical_sections:
        _append_security_section(lines, "Letzte externe Events:")
        if latest_external:
            for event in latest_external:
                lines.append(_security_event_summary_line(event))
        else:
            lines.append("- Keine externen Events gefunden.")

        _append_security_section(lines, "Letzte Gesamt-Events:")
        if latest_overall:
            for event in latest_overall:
                lines.append(_security_event_summary_line(event, include_proto=False))
        else:
            lines.append("- Keine Events vorhanden.")

    return "\n".join(lines)


def build_security_chad_curated_summary(app) -> str:
    return _build_security_chad_summary(app, include_technical_sections=False)


def build_security_chad_summary(app) -> str:
    return _build_security_chad_summary(app, include_technical_sections=True)


def read_ufw_log_tail(lines=1200):
    rc, out = run_cmd(
        ["sudo", "-n", "tail", "-n", str(lines), "/var/log/ufw.log"], timeout=8
    )
    if rc != 0:
        rc, out = run_cmd(["tail", "-n", str(lines), "/var/log/ufw.log"], timeout=8)
    if rc != 0:
        return []
    return [ln for ln in (out or "").splitlines() if ln.strip()]


def parse_ufw_block_line(app, line, *, is_local_or_lan_ip_fn):
    parser = app._security_parser()
    if parser is None:
        if not app.__dict__.get("_security_parser_missing_logged"):
            app._security_parser_missing_logged = True
            app.log_debug(
                "Security parser nicht verfügbar - UFW-Events werden derzeit nicht klassifiziert."
            )
        return None

    return parser.parse_ufw_block_line(
        line,
        aggregated=app.security_aggregated,
        dedup_cache=app.security_dedup_cache,
        is_local_or_lan_ip_fn=is_local_or_lan_ip_fn,
        log_debug_fn=app.log_debug,
    )


def detect_portscan(app):
    store = app._security_store()
    if store is not None:
        return store.detect_portscan(
            app.security_events, app.security_last_portscan_alert
        )

    now = time.time()
    recent = [
        event
        for event in app.security_events
        if now - event.get("epoch", now) <= 90
        and event.get("external")
        and event.get("type") == "UFW BLOCK"
    ]
    by_ip = {}
    for event in recent:
        ip = event.get("src") or "-"
        entry = by_ip.setdefault(
            ip, {"count": 0, "ports": set(), "latest": event.get("time", "-")}
        )
        entry["count"] += 1
        port = event.get("port")
        if port and port != "-":
            entry["ports"].add(port)
        entry["latest"] = event.get("time", entry["latest"])

    def severity_for(count, unique_ports):
        if count >= 40 or unique_ports >= 25:
            return 5
        if count >= 25 or unique_ports >= 15:
            return 4
        if count >= 12 or unique_ports >= 8:
            return 3
        if count >= 6 or unique_ports >= 4:
            return 2
        if count >= 1:
            return 1
        return 0

    def severity_label(level):
        return {
            1: "INFO",
            2: "WARN",
            3: "ALERT",
            4: "CRITICAL",
            5: "CRITICAL",
        }.get(level, "INFO")

    findings = []
    for ip, info in by_ip.items():
        severity = severity_for(info["count"], len(info["ports"]))
        if severity < 2:
            continue
        last_alert = app.security_last_portscan_alert.get(ip, 0.0)
        if now - last_alert < 120:
            continue
        app.security_last_portscan_alert[ip] = now
        severity_name = severity_label(severity)
        findings.append(
            {
                "time": info["latest"],
                "type": "Portscan-Verdacht",
                "src": ip,
                "port": str(len(info["ports"])),
                "proto": "-",
                "level": f"L{severity} {severity_name}",
                "action": "SUSPECT",
                "raw": (
                    f"Portscan-Verdacht: SRC={ip}, Level=L{severity} {severity_name}, "
                    f"Events={info['count']}, verschiedene Ports={len(info['ports'])}"
                ),
                "key": f"portscan|{ip}|L{severity}|{int(now // 120)}",
                "epoch": now,
                "external": True,
                "severity": severity,
            }
        )
    return findings


def get_ufw_logging_level(app):
    try:
        rc, out = run_cmd(["ufw", "status", "verbose"], timeout=5)
    except Exception as exc:
        level = "unknown"
        out = str(exc)
        _log_ufw_logging_debug(app, level, out)
        return level, out

    if rc != 0:
        level = "unknown"
        _log_ufw_logging_debug(app, level, out)
        return level, out

    text = (out or "").lower()
    level = "unknown"
    if (
        "logging: off" in text
        or "protokollierung: off" in text
        or "protokollierung: aus" in text
    ):
        level = "off"
    elif (
        "logging: on (low)" in text
        or "protokollierung: on (low)" in text
        or "protokollierung: ein (niedrig)" in text
        or "protokollierung: an (niedrig)" in text
    ):
        level = "low"
    elif (
        "logging: on (medium)" in text
        or "protokollierung: on (medium)" in text
        or "protokollierung: ein (mittel)" in text
        or "protokollierung: an (mittel)" in text
    ):
        level = "medium"
    elif (
        "logging: on (high)" in text
        or "protokollierung: on (high)" in text
        or "protokollierung: ein (hoch)" in text
        or "protokollierung: an (hoch)" in text
    ):
        level = "high"

    _log_ufw_logging_debug(app, level, out)
    return level, out


def _log_ufw_logging_debug(app, level, out):
    logger = _app_logger(app)
    if not callable(logger):
        return
    payload = (level, str(out or "").strip())
    cache = getattr(app, "__dict__", {}).get("_ufw_logging_debug_cache")
    if payload == cache:
        return
    app._ufw_logging_debug_cache = payload
    logger(f"[DEBUG] UFW logging level parsed: {level}")
    if level == "unknown":
        logger(f"[DEBUG] UFW verbose output:\n{out}")




def security_filtered_events(app):
    store = app._security_store()
    filter_mode = _security_filter_mode(app)
    if store is not None:
        return store.filtered_events(app.security_events, filter_mode, limit=400)

    if filter_mode == "portscan":
        base = [e for e in app.security_events if e.get("type") == "Portscan-Verdacht"]
    elif filter_mode == "relevant":
        base = [
            e
            for e in app.security_events
            if any(
                token in str(e.get("level", "")).upper()
                for token in ("WARN", "ALERT", "CRITICAL")
            )
        ]
    elif filter_mode == "external":
        base = [e for e in app.security_events if e.get("external")]
    else:
        base = list(app.security_events)
    return base[-400:]


def security_compute_stats(app):
    store = app._security_store()
    if store is not None:
        return store.compute_stats(app.security_events)

    total = len(app.security_events)
    block = sum(
        1
        for e in app.security_events
        if e.get("type") == "UFW BLOCK" and e.get("external")
    )
    scan = sum(1 for e in app.security_events if e.get("type") == "Portscan-Verdacht")
    src_count = {}
    port_count = {}
    for e in app.security_events:
        if not e.get("external"):
            continue
        src = e.get("src", "-")
        src_count[src] = src_count.get(src, 0) + 1
        port = e.get("port", "-")
        if port and port != "-":
            port_count[port] = port_count.get(port, 0) + 1
    top_ip = max(src_count.items(), key=lambda kv: kv[1])[0] if src_count else "–"
    top_port = max(port_count.items(), key=lambda kv: kv[1])[0] if port_count else "–"
    return total, block, scan, top_ip, top_port


def security_update_stats_view(app):
    total, block, scan, top_ip, top_port = security_compute_stats(app)
    app.security_stat_total_var.set(str(total))
    app.security_stat_block_var.set(str(block))
    app.security_stat_scan_var.set(str(scan))
    app.security_stat_top_ip_var.set(top_ip)
    app.security_stat_top_port_var.set(top_port)


def _refresh_security_table_state(app):
    app.security_table_row_meta = {}
    visible_events = security_filtered_events(app)
    app.security_visible_events = visible_events
    return visible_events


def _append_security_aggregate_rows(app, table) -> None:
    if _security_filter_mode(app) != "all":
        return
    agg_idx = 0
    for cat, count in app.security_aggregated.items():
        if count <= 0:
            continue
        table.insert(
            "",
            "end",
            iid=f"agg-{agg_idx}",
            values=(
                "-",
                f"Aggregiert {cat}",
                "-",
                f"{count}",
                "-",
                "INFO",
                "AGGREGATED",
            ),
        )
        app.security_table_row_meta[f"agg-{agg_idx}"] = {
            "kind": "aggregate",
            "raw": f"Aggregierte interne Events: {cat} = {count}",
        }
        agg_idx += 1


def _append_security_event_rows(app, table, visible_events) -> None:
    for idx, event in enumerate(visible_events):
        table.insert(
            "",
            "end",
            iid=f"sec-{idx}",
            values=(
                event.get("time", "-"),
                event.get("type", "-"),
                event.get("src", "-"),
                event.get("port", "-"),
                event.get("proto", "-"),
                event.get("level", "-"),
                event.get("action", "-"),
            ),
        )
        app.security_table_row_meta[f"sec-{idx}"] = {"kind": "event", "index": idx}


def _refresh_security_table_view(app, visible_events) -> None:
    table = app.security_table
    for item in table.get_children():
        table.delete(item)
    _append_security_aggregate_rows(app, table)
    _append_security_event_rows(app, table, visible_events)
    security_update_stats_view(app)


def refresh_security_table(app):
    visible_events = _refresh_security_table_state(app)
    _refresh_security_table_view(app, visible_events)


def _show_selected_security_event(app, table) -> bool:
    text = _selected_security_event_text(app, table)
    if not text:
        return False
    _set_security_detail_text(app, text)
    return True


def on_security_event_select(app, _event=None):
    _show_selected_security_event(app, _security_table(app))


def _finish_security_refresh_table_action(app) -> None:
    refresh_devices = getattr(app, "refresh_connected_device_table", None)
    if callable(refresh_devices):
        refresh_devices()
    app.log(
        app.tr(
            "security_log_table_refreshed",
            _security_table_refreshed_log_message(),
        )
    )


def security_refresh_table_action(app):
    refresh_security_table(app)
    _finish_security_refresh_table_action(app)


def _run_security_filter_action(
    app, filter_mode: str, tr_key: str, default_message: str
) -> None:
    app.security_filter_mode = str(filter_mode or "all")
    refresh_security_table(app)
    app.log(app.tr(tr_key, default_message))


def _apply_security_filter(app, filter_mode: str, tr_key: str, default_message: str):
    _run_security_filter_action(app, filter_mode, tr_key, default_message)


def _security_filter_apply_spec(filter_mode: str) -> tuple[str, str, str]:
    normalized = _normalized_security_filter_mode(filter_mode)
    return {
        "portscan": (
            "portscan",
            "security_log_filter_portscan",
            _security_filter_log_message("portscan"),
        ),
        "relevant": (
            "relevant",
            "security_log_filter_relevant",
            _security_filter_log_message("relevant"),
        ),
        "external": (
            "external",
            "security_log_filter_external",
            _security_filter_log_message("external"),
        ),
    }.get(
        normalized,
        (
            "all",
            "security_log_filter_all",
            _security_filter_log_message("all"),
        ),
    )


def security_filter_portscan(app):
    _apply_security_filter(app, *_security_filter_apply_spec("portscan"))


def security_filter_relevant(app):
    _apply_security_filter(app, *_security_filter_apply_spec("relevant"))


def security_filter_external(app):
    _apply_security_filter(app, *_security_filter_apply_spec("external"))


def security_filter_all(app):
    _apply_security_filter(app, *_security_filter_apply_spec("all"))


def security_clear_events(app, confirm=False):
    if not _confirm_security_clear_events(app, confirm):
        return
    _run_security_clear_events(app)


def security_clear_views(app):
    _run_security_clear_views(app)


def _finish_security_clear_views(app) -> None:
    _set_security_detail_text_safe(app, _security_views_cleared_detail_text())
    app.log(_security_views_cleared_log_message())


def _set_security_detail_text(app, text: str):
    detail_widget = _security_detail_widget(app)
    if detail_widget is None:
        return
    detail_widget.delete("1.0", "end")
    detail_widget.insert("end", text)
    detail_widget.see("1.0")


def _set_security_detail_text_safe(app, text: str) -> bool:
    try:
        _set_security_detail_text(app, text)
    except Exception:
        return False
    return True


def _device_base_name(path: str) -> str:
    return os.path.basename(path or "").strip()


def _normalized_device_name(path: str) -> str:
    return _device_base_name(path).lower()


def _read_first_available_line(*paths: str) -> str:
    for path in paths:
        if not path:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                value = handle.read().strip()
            if value:
                return value
        except Exception:
            continue
    return ""


def _device_sysfs_base(path: str) -> str:
    base = _device_base_name(path)
    if not base:
        return ""
    return os.path.join("/sys/class/input", base)


def _device_display_name(path: str) -> str:
    base = _device_base_name(path)
    if not base:
        return "Unbekannt"

    sys_base = _device_sysfs_base(path)
    return (
        _read_first_available_line(
            os.path.join(sys_base, "device", "name"),
            os.path.join(sys_base, "name"),
        )
        or base
    )


def _device_metadata(path: str) -> dict:
    sys_base = _device_sysfs_base(path)
    vendor = _read_first_available_line(
        os.path.join(sys_base, "device", "id", "vendor"),
    )
    product = _read_first_available_line(
        os.path.join(sys_base, "device", "id", "product"),
    )
    bustype = _read_first_available_line(
        os.path.join(sys_base, "device", "id", "bustype"),
    )
    phys = _read_first_available_line(
        os.path.join(sys_base, "device", "phys"),
        os.path.join(sys_base, "phys"),
    )
    uniq = _read_first_available_line(
        os.path.join(sys_base, "device", "uniq"),
        os.path.join(sys_base, "uniq"),
    )
    return {
        "vendor": vendor or "-",
        "product": product or "-",
        "bustype": bustype or "-",
        "phys": phys or "-",
        "uniq": uniq or "-",
    }


def connected_device_inventory(app):
    devices = {}
    baseline = _device_baseline(app)

    for path in _device_watch_paths_for(app):
        base = _device_base_name(path)
        if not base:
            continue
        _store_connected_device(devices, app, path, base, baseline)

    return _sorted_connected_device_inventory(devices)


def format_connected_device_inventory(app) -> str:
    inventory, baseline = _connected_device_inventory_context(app)
    return _connected_device_inventory_text_for(inventory, baseline)


def current_input_access_inventory(app):
    current = _input_access_scan_state_or_log(app)
    if current is None:
        return []

    rows = []
    for path in _input_access_sorted_paths(current):
        rows.extend(_input_access_rows_for_current_path(app, current, path))
    return rows


def _input_access_rows_for_current_path(app, current, path):
    device_name, device_type, processes = _input_access_path_context(app, current, path)
    return _input_access_inventory_rows_for_path(
        app,
        path,
        device_name,
        device_type,
        processes,
    )


def _input_access_path_context(app, current, path):
    return (
        _device_display_name(path),
        _device_type_for_path(app, path),
        current.get(path, {}) or {},
    )


def _input_access_scan_state_or_log(app):
    try:
        return app._scan_input_access_state()
    except Exception as exc:
        app.log(_input_access_inventory_error_message(exc))
        return None


def _input_access_sorted_paths(current):
    return sorted((current or {}).keys())


def _input_access_inventory_error_message(error) -> str:
    return f"Security: Input-Access-Inventar fehlgeschlagen: {error}"


def _input_access_scan_error_message(action: str, error) -> str:
    return f"Security: Input-Access-{action} fehlgeschlagen: {error}"


def _input_access_pid_number(pid, default):
    return int(pid) if str(pid).isdigit() else default


def _input_access_sorted_process_items(processes):
    return sorted(
        (processes or {}).items(),
        key=lambda kv: _input_access_pid_number(kv[0], 0),
    )


def _input_access_inventory_rows_for_path(
    app,
    path,
    device_name,
    device_type,
    processes,
):
    rows = []
    for pid, pname in _input_access_sorted_process_items(processes):
        rows.append(
            _input_access_process_row(
                app,
                path,
                device_name,
                device_type,
                pid,
                pname,
            )
        )
    return rows


def _input_access_whitelist_status(app, process_name, pid) -> bool:
    return bool(
        app._security_input_access_whitelisted(
            process_name,
            _input_access_pid_number(pid, None),
        )
    )


def _input_access_process_row(
    app,
    path,
    device_name,
    device_type,
    pid,
    process_name,
):
    return _input_access_inventory_row(
        path,
        device_name,
        device_type,
        pid,
        process_name,
        _input_access_whitelist_status(app, process_name, pid),
    )


def _input_access_status_label(is_whitelisted: bool) -> str:
    return "bekannt" if is_whitelisted else "prüfen"


def _input_access_inventory_row(
    path,
    device_name,
    device_type,
    pid,
    process_name,
    is_whitelisted,
):
    return {
        "device": device_name,
        "process": process_name or "-",
        "pid": str(pid or "-"),
        "type": device_type or "-",
        "status": _input_access_status_label(is_whitelisted),
        "path": path,
    }


def refresh_input_access_table(app, log_result=True):
    rows = current_input_access_inventory(app)
    _refresh_input_access_table_if_present(app, rows)
    _log_input_access_refresh_result(app, len(rows), enabled=log_result)
    return rows


def _input_access_table(app):
    return getattr(app, "input_access_table", None)


def _refresh_input_access_table_if_present(app, rows) -> None:
    table = _input_access_table(app)
    if table is None:
        return
    _refresh_input_access_table_rows(app, table, rows)


def _reset_input_access_row_meta(app) -> None:
    app.input_access_row_meta = {}


def _refresh_input_access_table_rows(app, table, rows) -> None:
    _reset_input_access_row_meta(app)
    _clear_input_access_table(table)
    _populate_input_access_table(app, table, rows)


def _clear_input_access_table(table) -> None:
    try:
        table.delete(*_input_access_table_children(table))
    except Exception:
        pass


def _input_access_table_children(table):
    return list(table.get_children())


def _input_access_row_insert_kwargs(row):
    return _input_access_row_insert_config(_input_access_row_insert_values(row))


def _input_access_row_insert_values(row):
    return _input_access_row_values(row)


def _input_access_row_insert_config(values):
    return {"values": values}


def _tree_insert_position():
    return ("", "end")


def _input_access_row_insert_position():
    return _tree_insert_position()


def _input_access_row_insert_spec(row):
    parent, where = _input_access_row_insert_position()
    config = _input_access_row_insert_kwargs(row)
    return parent, where, config


def _insert_input_access_row(table, row) -> str:
    parent, where, config = _input_access_row_insert_spec(row)
    return table.insert(
        parent,
        where,
        **config,
    )


def _input_access_row_field(row, key):
    return row.get(key, "-")


def _input_access_row_values(row) -> tuple[str, str, str, str, str, str]:
    return (
        _input_access_row_field(row, "device"),
        _input_access_row_field(row, "process"),
        _input_access_row_field(row, "pid"),
        _input_access_row_field(row, "type"),
        _input_access_row_field(row, "status"),
        _input_access_row_field(row, "path"),
    )


def _store_input_access_row_meta(app, row_id, row) -> None:
    app.input_access_row_meta.update(_input_access_row_meta_update(row_id, row))


def _input_access_row_meta_value(row):
    return dict(row)


def _input_access_row_meta_update(row_id, row):
    return {row_id: _input_access_row_meta_value(row)}


def _input_access_table_rows(rows):
    return list(rows or [])


def _populate_input_access_table(app, table, rows) -> None:
    for row in _input_access_table_rows(rows):
        _append_input_access_row(app, table, row)


def _append_input_access_row(app, table, row) -> None:
    row_id = _inserted_input_access_row_id(table, row)
    _store_input_access_row_meta(app, row_id, row)


def _inserted_input_access_row_id(table, row) -> str:
    return _insert_input_access_row(table, row)


def _log_input_access_refresh_result(app, count: int, *, enabled: bool) -> None:
    if enabled:
        app.log(_input_access_refresh_log_message(count))


def _input_access_refresh_log_message(count: int) -> str:
    return f"Input-Zugriffe geprüft: {count} aktiver Zugriff(e)."


def _configure_connected_device_table_tags(app, table):
    known_color, new_color = _connected_device_table_tag_colors(app)
    try:
        for tag_name, options in _connected_device_table_tag_configs(
            known_color, new_color
        ):
            table.tag_configure(tag_name, **options)
    except Exception:
        pass


def _connected_device_table_tag_colors(app):
    theme = _app_value(app, "_app_theme", {}) or {}
    return (
        str(theme.get("success", "#1a7f37") or "#1a7f37"),
        str(theme.get("warning", "#9a6700") or "#9a6700"),
    )


def _connected_device_table_tag_configs(known_color: str, new_color: str):
    return (
        _connected_device_table_tag_config("device_known", known_color),
        _connected_device_table_tag_config("device_new", new_color),
    )


def _connected_device_table_tag_config(tag_name: str, color: str):
    return (tag_name, {"foreground": color})


def _connected_device_table_children(table):
    return list(table.get_children())


def _clear_connected_device_table(table) -> None:
    for item in _connected_device_table_children(table):
        table.delete(item)


def _connected_device_row_insert_kwargs(index: int, device):
    return _connected_device_row_insert_config(
        _connected_device_row_insert_iid(index),
        _connected_device_row_insert_values(device),
        _connected_device_row_insert_tags(device),
    )


def _connected_device_row_insert_iid(index: int) -> str:
    return _connected_device_row_id(index)


def _connected_device_row_insert_values(device):
    return _connected_device_row_values(device)


def _connected_device_row_insert_tags(device):
    return _connected_device_row_tags(device)


def _connected_device_row_insert_config(iid: str, values, tags):
    return {"iid": iid, "values": values, "tags": tags}


def _connected_device_row_insert_position():
    return _tree_insert_position()


def _connected_device_row_insert_spec(index: int, device):
    parent, where = _connected_device_row_insert_position()
    config = _connected_device_row_insert_kwargs(index, device)
    return parent, where, config


def _insert_connected_device_row(table, index: int, device) -> None:
    parent, where, config = _connected_device_row_insert_spec(index, device)
    table.insert(
        parent,
        where,
        **config,
    )


def _connected_device_row_id(index: int) -> str:
    return f"dev-{index}"


def _connected_device_inventory_items(inventory):
    return list(enumerate(inventory or []))


def _populate_connected_device_table(table, inventory) -> None:
    for idx, device in _connected_device_inventory_items(inventory):
        _append_connected_device_row(table, idx, device)


def _append_connected_device_row(table, index: int, device) -> None:
    _insert_connected_device_row(table, index, device)


def _connected_device_table_inventory(app):
    inventory = _current_connected_device_inventory(app)
    return _store_connected_device_inventory(app, inventory)


def _current_connected_device_inventory(app):
    return connected_device_inventory(app)


def _store_connected_device_inventory(app, inventory):
    app.connected_devices_inventory = inventory
    return inventory


def _connected_device_table(app):
    return _app_widget_value(app, "security_devices_table")


def _refresh_connected_device_table_view(app, table, inventory) -> None:
    _configure_connected_device_table_tags(app, table)
    _clear_connected_device_table(table)
    _populate_connected_device_table(table, inventory)


def _refresh_connected_device_table_if_present(app, inventory) -> None:
    table = _connected_device_table(app)
    if table is None:
        return
    _refresh_connected_device_table_view(app, table, inventory)


def refresh_connected_device_table(app):
    inventory = _connected_device_table_inventory(app)
    _refresh_connected_device_table_if_present(app, inventory)
    return inventory


def on_connected_device_select(app, _event=None):
    text = _selected_connected_device_selection_text(app)
    if not text:
        return
    _finish_connected_device_select(app, text)


def _selected_connected_device_selection_text(app) -> str:
    return _selected_connected_device_text(app, _connected_device_table(app))


def _selected_connected_device_text(app, table) -> str:
    if table is None:
        return ""
    device = _selected_connected_device(app, table)
    if not device:
        return ""
    return _connected_device_detail_text(device)


def _finish_connected_device_select(app, text: str) -> None:
    _set_security_detail_text(app, text)


def _connected_device_display_log_text(app, inventory) -> str:
    count = len(inventory or [])
    return app.tr(
        "security_log_connected_devices_shown",
        _security_connected_devices_log_message(count),
    ).format(count=count)


def _finish_security_show_connected_devices(app, text: str, inventory) -> None:
    _set_security_detail_text(app, text)
    app.log(_connected_device_display_log_text(app, inventory))


def _connected_device_display_payload(app):
    inventory = refresh_connected_device_table(app)
    return inventory, format_connected_device_inventory(app)


def security_show_connected_devices(app):
    inventory, text = _connected_device_display_payload(app)
    _finish_security_show_connected_devices(app, text, inventory)


def security_integrity_ignore_path(app, path):
    raw_path = str(path or "").strip()
    if not raw_path:
        return False

    target = os.path.abspath(os.path.expanduser(raw_path))
    config_dir = os.path.abspath(
        os.path.expanduser(_app_str_value(app, "netmon_config_dir", ""))
    )
    state_dir = os.path.abspath(
        os.path.expanduser(_app_str_value(app, "netmon_state_dir", ""))
    )
    if _path_is_dir_or_child(target, config_dir):
        return True
    if _path_is_dir_or_child(target, state_dir):
        return True

    ignored = _security_integrity_ignored_paths(app)
    return target in ignored


def _path_is_dir_or_child(target: str, directory: str) -> bool:
    return bool(directory) and (
        target == directory or target.startswith(directory + os.sep)
    )


def _security_integrity_ignored_paths(app):
    ignored = set()
    for attr_name in (
        "netmon_config_path",
        "ai_config_path",
        "vpn_config_path",
        "primary_vpn_config_path",
        "link_config_path",
        "privacy_config_path",
        "hdd_config_path",
        "radio_stations_path",
        "radio_favorites_path",
        "radio_settings_path",
        "radio_db_path",
        "radio_db_meta_path",
        "clamav_findings_path",
        "security_baseline_path",
        "startup_guard_baseline_path",
        "startup_guard_trustlist_path",
        "process_guard_trustlist_path",
    ):
        value = str(_app_value(app, attr_name, "") or "").strip()
        if value:
            ignored.add(os.path.abspath(os.path.expanduser(value)))
    return ignored


def _security_baseline_state(app) -> dict:
    return {
        "integrity": _integrity_baseline(app),
        "device": _device_baseline(app),
        "input_access": _input_access_baseline(app),
    }


def _security_export_datetime_formats(moment: datetime) -> tuple[str, str]:
    return (
        moment.strftime("%Y-%m-%d_%H-%M-%S"),
        moment.strftime("%Y-%m-%d %H:%M:%S"),
    )
