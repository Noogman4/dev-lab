"""Security monitoring controller helpers for NetMon."""

from __future__ import annotations

import os
import threading
from datetime import datetime
from tkinter import messagebox

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd


def security_update_status(app, color):
    app.set_light(app.l_sec, color)
    app.security_status_var.set(
        "Monitoring: AKTIV" if app.security_monitoring else "Monitoring: AUS"
    )
    app.security_level_var.set(f"Logging: {app.security_log_level}")
    app.security_count_var.set(f"Events: {len(app.security_events)}")
    app.security_alarm_var.set(f"Letzter Alarm: {app.security_last_alarm}")


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


def security_filtered_events(app):
    store = app._security_store()
    if store is not None:
        return store.filtered_events(
            app.security_events, app.security_filter_mode, limit=400
        )

    if app.security_filter_mode == "portscan":
        base = [e for e in app.security_events if e.get("type") == "Portscan-Verdacht"]
    elif app.security_filter_mode == "relevant":
        base = [
            e
            for e in app.security_events
            if any(
                token in str(e.get("level", "")).upper()
                for token in ("WARN", "ALERT", "CRITICAL")
            )
        ]
    elif app.security_filter_mode == "external":
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


def refresh_security_table(app):
    for item in app.security_table.get_children():
        app.security_table.delete(item)
    app.security_visible_events = security_filtered_events(app)

    if app.security_filter_mode == "all":
        agg_idx = 0
        for cat, count in app.security_aggregated.items():
            if count > 0:
                app.security_table.insert(
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
                agg_idx += 1

    for idx, event in enumerate(app.security_visible_events):
        app.security_table.insert(
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
    security_update_stats_view(app)


def on_security_event_select(app, _event=None):
    selection = app.security_table.selection()
    if not selection:
        return
    try:
        idx = int(selection[0].split("-", 1)[1])
    except Exception:
        return
    view = app.security_visible_events
    if idx < 0 or idx >= len(view):
        return
    event = view[idx]
    app.security_detail.delete("1.0", "end")
    app.security_detail.insert("end", event.get("raw", ""))
    app.security_detail.see("1.0")


def security_refresh_table_action(app):
    refresh_security_table(app)
    app.log(
        app.tr(
            "security_log_table_refreshed",
            "Security-Tabelle aktualisiert.",
        )
    )


def security_filter_portscan(app):
    app.security_filter_mode = "portscan"
    refresh_security_table(app)
    app.log(
        app.tr(
            "security_log_filter_portscan",
            "Security-Filter: Nur Portscan.",
        )
    )


def security_filter_relevant(app):
    app.security_filter_mode = "relevant"
    refresh_security_table(app)
    app.log(
        app.tr(
            "security_log_filter_relevant",
            "Security-Filter: Nur Warnungen/Alarme.",
        )
    )


def security_filter_external(app):
    app.security_filter_mode = "external"
    refresh_security_table(app)
    app.log(
        app.tr(
            "security_log_filter_external",
            "Security-Filter: Nur externe UFW-Blocks.",
        )
    )


def security_filter_all(app):
    app.security_filter_mode = "all"
    refresh_security_table(app)
    app.log(
        app.tr(
            "security_log_filter_all",
            "Security-Filter: Alle Events.",
        )
    )


def security_clear_events(app, confirm=False):
    if confirm and app.security_events:
        ok = messagebox.askyesno(
            app.tr("security_clear_title", "Security-Events leeren"),
            app.tr(
                "security_clear_body",
                "Die aktuell angezeigten Security-Events werden entfernt.\n\nFortfahren?",
            ),
            parent=app,
        )
        if not ok:
            app.log(
                app.tr(
                    "security_log_clear_cancelled",
                    "Security-Events leeren abgebrochen.",
                )
            )
            return
    app.security_events = []
    app.security_event_keys = set()
    app.security_visible_events = []
    app.security_last_portscan_alert = {}
    app.security_aggregated = {}
    app.security_dedup_cache = {}
    app.security_last_alarm = "–"
    app.security_detail.delete("1.0", "end")
    refresh_security_table(app)
    security_update_status(app, "green" if app.security_monitoring else "gray")
    app.log(
        app.tr(
            "security_log_cleared",
            "Security-Events geleert.",
        )
    )


def security_export_dir():
    home = os.path.expanduser("~")
    desk_de = os.path.join(home, "Schreibtisch")
    desk_en = os.path.join(home, "Desktop")
    if os.path.isdir(desk_de):
        return desk_de
    if os.path.isdir(desk_en):
        return desk_en
    return home


def export_security_logs(app):
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    export_dir = security_export_dir()
    path = os.path.join(export_dir, f"netmon_security_log_{stamp}.txt")
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("NetMon Security Export\n")
            handle.write("=" * 24 + "\n")
            handle.write(
                f"Exportzeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            handle.write(
                f"Monitoring-Status: {'AKTIV' if app.security_monitoring else 'AUS'}\n"
            )
            handle.write(f"UFW Logging-Level: {app.security_log_level}\n")
            handle.write(f"Anzahl Events: {len(app.security_events)}\n")
            handle.write(f"Letzter Alarm: {app.security_last_alarm}\n\n")

            handle.write("SECURITY SUMMARY\n")
            handle.write("-" * 20 + "\n")
            handle.write(
                f"Externe UFW-Blocks: {len([e for e in app.security_events if e.get('type') == 'UFW BLOCK'])}\n"
            )
            handle.write(
                f"Portscan-Verdacht: {len([e for e in app.security_events if 'PORTSCAN' in e.get('type', '')])}\n"
            )
            handle.write(
                f"Dateiänderungen: {len([e for e in app.security_events if e.get('type', '').startswith('FILE')])}\n"
            )
            handle.write(
                f"Device-Änderungen: {len([e for e in app.security_events if e.get('type', '').startswith('DEVICE')])}\n"
            )
            handle.write(
                f"Input-Access: {len([e for e in app.security_events if 'INPUT ACCESS' in e.get('type', '')])}\n"
            )
            for cat, count in app.security_aggregated.items():
                handle.write(f"Aggregiert {cat}: {count}\n")
            handle.write("\n")

            handle.write("SECURITY EVENTS\n")
            handle.write("-" * 120 + "\n")
            handle.write(
                "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n"
            )
            for event in app.security_events:
                handle.write(
                    f"{event.get('time','-')} | {event.get('type','-')} | {event.get('src','-')} | "
                    f"{event.get('port','-')} | {event.get('proto','-')} | {event.get('level','-')} | "
                    f"{event.get('action','-')}\n"
                )

            handle.write("\nDETAIL / ROHDATEN\n")
            handle.write("-" * 120 + "\n")
            for idx, event in enumerate(app.security_events, start=1):
                handle.write(
                    f"[{idx}] {event.get('time','-')} {event.get('type','-')}\n"
                )
                handle.write((event.get("raw") or "-") + "\n\n")

        app.log(
            app.tr(
                "security_log_exported",
                "Security-Logs exportiert: {path}",
            ).format(path=path)
        )
    except Exception as exc:
        messagebox.showerror(
            app.tr("security_export_title", "Security Export"),
            app.tr(
                "security_export_failed_body",
                "Export fehlgeschlagen:\n{error}",
            ).format(error=exc),
            parent=app,
        )
        app.log(
            app.tr(
                "security_log_export_failed",
                "Security-Export fehlgeschlagen: {error}",
            ).format(error=exc)
        )


def security_poll_async(app):
    if not app.security_monitoring or app.security_scan_running:
        return
    app.security_scan_running = True

    def job():
        lines = app._read_ufw_log_tail()
        new_events = []
        for line in lines:
            event = app._parse_ufw_block_line(line)
            if not event:
                continue
            if event["key"] in app.security_event_keys:
                continue
            app.security_event_keys.add(event["key"])
            new_events.append(event)

        if new_events:
            app.security_events.extend(new_events)
            app.security_events = app.security_events[-1200:]

        findings = app._security_detect_portscan()
        for finding in findings:
            if finding["key"] in app.security_event_keys:
                continue
            app.security_event_keys.add(finding["key"])
            app.security_events.append(finding)

        integrity_events = app.scan_integrity_changes()
        for finding in integrity_events:
            if finding["key"] in app.security_event_keys:
                continue
            app.security_event_keys.add(finding["key"])
            app.security_events.append(finding)

        device_events = app.scan_device_changes()
        for finding in device_events:
            if finding["key"] in app.security_event_keys:
                continue
            app.security_event_keys.add(finding["key"])
            app.security_events.append(finding)

        input_access_events = app.scan_input_access_changes()
        for finding in input_access_events:
            if finding["key"] in app.security_event_keys:
                continue
            app.security_event_keys.add(finding["key"])
            app.security_events.append(finding)

        harmless_rst_events = [
            event
            for event in new_events
            if event.get("type") == "HARMLESS RETURN TRAFFIC"
        ]
        has_scan_alert = bool(findings)
        has_new_blocks = any(
            event.get("external") and event.get("type") == "UFW BLOCK"
            for event in new_events
        )
        has_custom_alert = bool(
            integrity_events or device_events or input_access_events
        )
        if has_scan_alert:
            color = "red"
            app.security_last_alarm = "Portscan-Verdacht"
        elif has_new_blocks:
            color = "yellow"
            app.security_last_alarm = "Neue BLOCK-Events"
        elif has_custom_alert:
            color = "yellow"
            app.security_last_alarm = "Datei-/Geräte-Änderung"
        else:
            color = "green"

        def done():
            app._refresh_security_table()
            for event in harmless_rst_events[:5]:
                app.log(event.get("summary") or "[INFO] harmless return traffic (RST)")
            if len(harmless_rst_events) > 5:
                app.log(
                    f"[INFO] harmless return traffic (RST): {len(harmless_rst_events)} Ereignisse"
                )
            app._security_update_status(color)
            app.security_scan_running = False
            if app.security_monitoring:
                app.after(5000, app._security_poll_async)

        app.after(0, done)

    threading.Thread(target=job, daemon=True).start()


def security_start_monitoring(app):
    if app.security_monitoring:
        app.log(
            app.tr(
                "security_log_monitoring_already_running",
                "Security Monitoring läuft bereits.",
            )
        )
        return
    app.security_monitoring = True

    query_fn = getattr(app, "_security_query_log_level", None)
    if callable(query_fn):
        try:
            app.security_log_level = query_fn()
        except Exception as exc:
            app.security_log_level = "–"
            app.log(
                app.tr(
                    "security_log_level_query_failed",
                    "Security: Log-Level-Abfrage fehlgeschlagen: {error}",
                ).format(error=exc)
            )
    else:
        app.security_log_level = "–"
        app.log(
            app.tr(
                "security_log_level_query_unavailable",
                "Security: Log-Level-Abfrage nicht verfügbar, Fallback '–'.",
            )
        )

    app.log(
        app.tr(
            "security_log_monitoring_started",
            "Security Monitoring gestartet.",
        )
    )
    app._security_update_status("green")
    app._security_poll_async()


def security_stop_monitoring(app):
    app.security_monitoring = False
    app.security_scan_running = False
    app.log(
        app.tr(
            "security_log_monitoring_stopped",
            "Security Monitoring gestoppt.",
        )
    )
    app._security_update_status("gray")


def security_scan_now(app):
    if app.security_scan_running:
        app.log("Security-Scan läuft bereits.")
        return
    app.security_scan_running = True

    def job():
        new_events = []
        try:
            new_events.extend(app.scan_integrity_changes())
            new_events.extend(app.scan_device_changes())
            new_events.extend(app.scan_input_access_changes())
        except Exception as exc:
            app.log_safe(f"Security-Scan fehlgeschlagen: {exc}")
        finally:
            app.security_scan_running = False

        for event in new_events:
            if event["key"] in app.security_event_keys:
                continue
            app.security_event_keys.add(event["key"])
            app.security_events.append(event)
        if new_events:
            app.log_safe(f"Security-Scan: {len(new_events)} neue Events")
        app._refresh_security_table_safe()

    threading.Thread(target=job, daemon=True).start()


def security_input_access_scan(app):
    if app.security_scan_running:
        app.log("Security-Scan läuft bereits.")
        return
    app.security_scan_running = True

    def job():
        events = []
        try:
            events.extend(app.scan_input_access_changes())
        except Exception as exc:
            app.log_safe(f"Input-Zugriffscheck fehlgeschlagen: {exc}")
        finally:
            app.security_scan_running = False

        for event in events:
            if event["key"] in app.security_event_keys:
                continue
            app.security_event_keys.add(event["key"])
            app.security_events.append(event)
        if events:
            app.log_safe(f"Input-Zugriffscheck: {len(events)} neue Events")
        app._refresh_security_table_safe()

    threading.Thread(target=job, daemon=True).start()
