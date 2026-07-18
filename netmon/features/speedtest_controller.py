"""Speedtest controller helpers for NetMon."""

from __future__ import annotations

import json
import os
import re
import threading

try:
    from netmon.core.utils import call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import call_in_ui_thread

try:
    from netmon.config.constants import SPEEDTEST_WARN_DEFAULTS
    from netmon.core.state import get_netmon_documents_subdir
except ModuleNotFoundError:
    from config.constants import SPEEDTEST_WARN_DEFAULTS
    from core.state import get_netmon_documents_subdir


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _app_var_set(app, name: str, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _tr(app, key: str, default: str) -> str:
    translator = getattr(app, "tr", None)
    if callable(translator):
        try:
            return str(translator(key, default) or default)
        except Exception:
            return default
    return default


def _speedtest_history_records(app):
    return list(_app_value(app, "speedtest_history", []) or [])


def _speedtest_history_limit(app, default: int = 5) -> int:
    value = _app_value(app, "speedtest_history_limit", default)
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, limit)


def _speedtest_trimmed_records_for_app(app, records):
    return _speedtest_trimmed_history(records, _speedtest_history_limit(app))


def _speedtest_history_window(app):
    return _speedtest_trimmed_records_for_app(app, _speedtest_history_records(app))


def _speedtest_history_list(history):
    return list(history or [])


def _speedtest_trimmed_history(records, limit: int):
    return list(records or [])[-max(1, int(limit)) :]


def _speedtest_ms_text(value) -> str:
    return f"{round(value)} ms" if value is not None else "-"


def _speedtest_mbps_text(value) -> str:
    return f"{value:.1f} Mbit/s" if value is not None else "-"


def _speedtest_history_metric_text(value, decimals: int) -> str:
    if value is None:
        return "-"
    return f"{value:.{decimals}f}"


def _speedtest_history_log_fields(item) -> dict:
    return {
        "timestamp": item.get("timestamp") or "-",
        "ping": _speedtest_history_metric_text(item.get("ping_ms"), 0),
        "jitter": _speedtest_history_metric_text(item.get("jitter_ms"), 0),
        "download": _speedtest_history_metric_text(item.get("download_mbps"), 1),
        "upload": _speedtest_history_metric_text(item.get("upload_mbps"), 1),
    }


def _speedtest_history_log_parts(fields: dict) -> tuple[str, ...]:
    data = dict(fields or {})
    return (
        str(data.get("timestamp") or "-"),
        f"Ping {data.get('ping', '-')} ms",
        f"Jitter {data.get('jitter', '-')} ms",
        f"DL {data.get('download', '-')}",
        f"UL {data.get('upload', '-')}",
    )


def _speedtest_history_log_line(item) -> str:
    fields = _speedtest_history_log_fields(item)
    return " | ".join(_speedtest_history_log_parts(fields))


def _speedtest_empty_history_message() -> str:
    return "Speedtest-Verlauf: noch keine Einträge."


def _speedtest_history_header_message() -> str:
    return "Speedtest-Verlauf (letzte Ergebnisse):"


def _speedtest_history_message_lines(records) -> list[str]:
    items = _speedtest_history_list(records)
    if not items:
        return [_speedtest_empty_history_message()]
    return [_speedtest_history_header_message()] + [
        _speedtest_history_log_line(item) for item in items
    ]


def _speedtest_empty_panel_values() -> dict:
    return {
        "ping": "-",
        "jitter": "-",
        "download": "-",
        "upload": "-",
        "timestamp": "Noch kein Speedtest durchgeführt",
    }


def _speedtest_panel_value_text(result, key: str, formatter) -> str:
    return formatter(dict(result or {}).get(key))


def _speedtest_panel_values(result) -> dict:
    if not result:
        return _speedtest_empty_panel_values()

    return {
        "ping": _speedtest_panel_value_text(result, "ping_ms", _speedtest_ms_text),
        "jitter": _speedtest_panel_value_text(result, "jitter_ms", _speedtest_ms_text),
        "download": _speedtest_panel_value_text(
            result, "download_mbps", _speedtest_mbps_text
        ),
        "upload": _speedtest_panel_value_text(
            result, "upload_mbps", _speedtest_mbps_text
        ),
        "timestamp": result.get("timestamp") or "-",
    }


def _speedtest_warn_specs():
    return (
        ("download_mbps", "Download niedrig", "download_mbps_min", "Mbit/s", 1, "<"),
        ("upload_mbps", "Upload niedrig", "upload_mbps_min", "Mbit/s", 1, "<"),
        ("ping_ms", "Ping hoch", "ping_ms_max", "ms", 0, ">"),
        ("jitter_ms", "Jitter hoch", "jitter_ms_max", "ms", 0, ">"),
    )


def _speedtest_warn_message(
    *,
    label: str,
    value,
    threshold,
    unit: str,
    decimals: int,
    comparison: str,
) -> str:
    value_text = f"{value:.{decimals}f}"
    threshold_text = f"{threshold:.{decimals}f}"
    return f"{label}: {value_text} {unit} ({comparison} {threshold_text})"


def _speedtest_warn_triggered(value, threshold, comparison: str) -> bool:
    return value < threshold if comparison == "<" else value > threshold


def _speedtest_attempted_cli(err) -> str:
    marker = "Versuchte Befehle:"
    if marker not in str(err):
        return ""
    return str(err).split(marker, 1)[1].strip()


def _speedtest_failure_messages(err) -> list[str]:
    messages = [f"Speedtest fehlgeschlagen: {err}"]
    attempted = _speedtest_attempted_cli(err)
    if attempted:
        messages.append(f"Speedtest-Diagnose (CLI): {attempted}")
    return messages


def _speedtest_status_message(state: str) -> str:
    return {
        "started": "Speedtest gestartet...",
        "completed": "Speedtest abgeschlossen.",
    }.get(str(state or "").strip().lower(), "Speedtest-Status unbekannt.")


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _legacy_speedtest_history_candidates(app) -> tuple[str, ...]:
    candidates = []
    state_dir = str(getattr(app, "netmon_state_dir", "") or "").strip()
    if state_dir:
        candidates.append(os.path.join(state_dir, "logs", "speedtest_history.jsonl"))
    candidates.append(os.path.join(_repo_root(), "logs", "speedtest_history.jsonl"))
    return tuple(candidates)


def _migrate_speedtest_history(app, target_path: str) -> None:
    if os.path.isfile(target_path):
        return
    for source in _legacy_speedtest_history_candidates(app):
        if not source or os.path.abspath(source) == os.path.abspath(target_path):
            continue
        if not os.path.isfile(source):
            continue
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with (
                open(source, "rb") as src_handle,
                open(target_path, "wb") as target_handle,
            ):
                target_handle.write(src_handle.read())
            return
        except Exception:
            continue


def speedtest_logs_dir(app):
    log_dir = get_netmon_documents_subdir("Logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def speedtest_history_path(app):
    path = os.path.join(speedtest_logs_dir(app), "speedtest_history.jsonl")
    _migrate_speedtest_history(app, path)
    return path


def load_speedtest_history(app):
    path = speedtest_history_path(app)
    if not os.path.isfile(path):
        return
    loaded = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = (line or "").strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                if isinstance(item, dict):
                    loaded.append(item)
    except Exception as exc:
        app.log_debug_safe(f"Speedtest-Verlauf konnte nicht geladen werden: {exc}")
        return

    if loaded:
        limit = _speedtest_history_limit(app)
        app.speedtest_history = _speedtest_trimmed_records_for_app(app, loaded)
        app.speedtest_last_result = dict(app.speedtest_history[-1])
        if len(loaded) > limit:
            persist_speedtest_history(app)


def persist_speedtest_history(app):
    path = speedtest_history_path(app)
    records = _speedtest_history_window(app)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            for item in records:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as exc:
        app.log_debug_safe(f"Speedtest-Verlauf konnte nicht gespeichert werden: {exc}")


def append_speedtest_history(app, result):
    if not isinstance(result, dict):
        return
    app.speedtest_last_result = dict(result)
    history = _speedtest_history_records(app)
    history.append(dict(result))
    app.speedtest_history = _speedtest_trimmed_records_for_app(app, history)
    persist_speedtest_history(app)


def speedtest_warn_messages(result):
    warns = []
    if not isinstance(result, dict):
        return warns
    for (
        key,
        label,
        threshold_key,
        unit,
        decimals,
        comparison,
    ) in _speedtest_warn_specs():
        value = result.get(key)
        threshold = SPEEDTEST_WARN_DEFAULTS[threshold_key]
        if not isinstance(value, (int, float)):
            continue
        if _speedtest_warn_triggered(value, threshold, comparison):
            warns.append(
                _speedtest_warn_message(
                    label=label,
                    value=value,
                    threshold=threshold,
                    unit=unit,
                    decimals=decimals,
                    comparison=comparison,
                )
            )
    return warns


def _speedtest_panel_var_items(values: dict):
    data = _speedtest_empty_panel_values()
    data.update(dict(values or {}))
    return (
        ("speedtest_ping_var", data.get("ping", "-")),
        ("speedtest_jitter_var", data.get("jitter", "-")),
        ("speedtest_download_var", data.get("download", "-")),
        ("speedtest_upload_var", data.get("upload", "-")),
        ("speedtest_timestamp_var", data.get("timestamp")),
    )


def _apply_speedtest_panel_values(app, values: dict):
    for name, value in _speedtest_panel_var_items(values):
        _app_var_set(app, name, value)


def update_speedtest_panel(app, result):
    values = _speedtest_panel_values(result)
    _apply_speedtest_panel_values(app, values)


def _speedtest_history_messages(history) -> list[str]:
    return _speedtest_history_message_lines(history)


def _speedtest_result_debug_messages(
    result, format_summary_fn, format_table_fn
) -> list[str]:
    return [
        json.dumps(result, ensure_ascii=False),
        format_summary_fn(result),
        format_table_fn(result),
    ]


def _speedtest_internal_debug_message(result, history_size: int) -> str:
    return f"Speedtest intern: tool={result.get('tool','-')} history={history_size}"


def normalize_speedtest_server_id(value) -> str:
    text = str(value or "").strip()
    if text.isdigit():
        return text

    match = re.search(
        r"(?:^|\]\s*)(?:server[- ]?id|id)\s*[:#-]?\s*(\d+)" r"(?=\s*(?:$|\||\n))",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1) if match else ""


def configured_speedtest_server_id(app) -> str:
    server_var = getattr(app, "speedtest_server_id_var", None)
    if server_var is not None:
        try:
            return normalize_speedtest_server_id(server_var.get())
        except Exception:
            pass
    settings = getattr(app, "settings", {}) or {}
    return normalize_speedtest_server_id(settings.get("speedtest_server_id", ""))


def _speedtest_server_place(server) -> str:
    location = str(server.get("location", "") or "").strip()
    country = str(server.get("country", "") or "").strip()
    return ", ".join(value for value in (location, country) if value) or "-"


def _speedtest_server_log_line(app, server) -> str:
    distance = str(server.get("distance", "") or "").strip()
    distance_text = (
        _tr(app, "speedtest_server_list_distance", " | Entfernung: {value}").format(
            value=distance
        )
        if distance
        else ""
    )
    return _tr(
        app,
        "speedtest_server_list_item",
        "ID {id} | Anbieter: {name} | Ort: {place}{distance}",
    ).format(
        id=str(server.get("id", "") or "-").strip() or "-",
        name=str(server.get("name", "") or server.get("host", "") or "-").strip()
        or "-",
        place=_speedtest_server_place(server),
        distance=distance_text,
    )


def _prepare_speedtest_server_log(app) -> None:
    def prepare_log():
        notebook = _app_value(app, "nb")
        log_tab = _app_value(app, "tab_log")
        if notebook is not None and log_tab is not None:
            try:
                notebook.select(log_tab)
            except Exception:
                pass

        if bool(_app_value(app, "log_overlay_active", False)):
            toggle_overlay = getattr(app, "toggle_log_overlay", None)
            if callable(toggle_overlay):
                try:
                    toggle_overlay()
                except Exception:
                    pass

        clear_log = getattr(app, "clear_log", None)
        if callable(clear_log):
            clear_log()

    call_in_ui_thread(app, prepare_log)


def _set_speedtest_server_lookup_running(app, running: bool) -> None:
    app.speedtest_servers_running = bool(running)
    button = _app_value(app, "btn_speedtest_server_lookup")
    if button is None:
        return

    def apply_state():
        try:
            button.configure(state="disabled" if running else "normal")
        except Exception:
            pass

    call_in_ui_thread(app, apply_state)


def speedtest_servers_async(
    app,
    *,
    list_servers_fn,
    run_cmd_fn,
    has_cmd_fn,
):
    if bool(_app_value(app, "speedtest_servers_running", False)):
        app.log_safe(
            _tr(
                app,
                "speedtest_server_list_already_running",
                "Speedtest-Server werden bereits abgerufen.",
            )
        )
        return

    _prepare_speedtest_server_log(app)
    _set_speedtest_server_lookup_running(app, True)
    app.log_safe(
        _tr(
            app,
            "speedtest_server_list_started",
            "Speedtest-Server-IDs werden abgerufen...",
        )
    )

    def job():
        try:
            servers, error = list_servers_fn(
                run_cmd_fn,
                has_cmd_fn,
                timeout=60,
                limit=20,
            )
            if error:
                app.log_safe(
                    _tr(
                        app,
                        "speedtest_server_list_failed",
                        "Speedtest-Server konnten nicht abgerufen werden: {error}",
                    ).format(error=error)
                )
                return

            app.log_safe(
                _tr(
                    app,
                    "speedtest_server_list_header",
                    "Verfügbare Speedtest-Server ({count} Treffer):",
                ).format(count=len(servers))
            )
            for server in servers:
                app.log_safe(_speedtest_server_log_line(app, server))
            app.log_safe(
                _tr(
                    app,
                    "speedtest_server_list_hint",
                    "Gewünschte ID in das Feld Server-ID eintragen und speichern.",
                )
            )
        except Exception as exc:
            app.log_safe(
                _tr(
                    app,
                    "speedtest_server_list_failed",
                    "Speedtest-Server konnten nicht abgerufen werden: {error}",
                ).format(error=exc)
            )
        finally:
            _set_speedtest_server_lookup_running(app, False)

    threading.Thread(target=job, daemon=True).start()


def show_speedtest_history(app):
    history = _speedtest_history_window(app)
    for message in _speedtest_history_messages(history):
        app.log(message)


def speedtest_async(
    app,
    *,
    run_speedtest_fn,
    format_summary_fn,
    format_table_fn,
    run_cmd_fn,
    has_cmd_fn,
):
    def job():
        server_id = configured_speedtest_server_id(app)
        app.log_safe(_speedtest_status_message("started"))
        result, err = run_speedtest_fn(
            run_cmd_fn,
            has_cmd_fn,
            timeout=120,
            server_id=server_id,
        )
        if err:
            for message in _speedtest_failure_messages(err):
                app.log_safe(message)
            return

        if server_id and isinstance(result, dict) and not result.get("server_id"):
            result["server_id"] = server_id

        append_speedtest_history(app, result)
        call_in_ui_thread(app, lambda r=dict(result): update_speedtest_panel(app, r))
        for message in _speedtest_result_debug_messages(
            result,
            format_summary_fn,
            format_table_fn,
        ):
            app.log_debug_safe(message)
        app.log_safe(_speedtest_status_message("completed"))

        for warn in speedtest_warn_messages(result):
            app.log_debug_safe(f"[WARN] Speedtest: {warn}")

        if bool(_app_value(app, "debug_mode", False)):
            app.log_debug_safe(
                _speedtest_internal_debug_message(result, len(app.speedtest_history))
            )

    threading.Thread(target=job, daemon=True).start()
