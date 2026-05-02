"""Speedtest controller helpers for NetMon."""

from __future__ import annotations

import json
import os
import threading

try:
    from netmon.config.constants import SPEEDTEST_WARN_DEFAULTS
except ModuleNotFoundError:
    from config.constants import SPEEDTEST_WARN_DEFAULTS


def speedtest_logs_dir(app):
    log_dir = os.path.join(app.netmon_state_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def speedtest_history_path(app):
    return os.path.join(speedtest_logs_dir(app), "speedtest_history.jsonl")


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
        app.speedtest_history = loaded[-app.speedtest_history_limit :]
        app.speedtest_last_result = dict(app.speedtest_history[-1])
        if len(loaded) > app.speedtest_history_limit:
            persist_speedtest_history(app)


def persist_speedtest_history(app):
    path = speedtest_history_path(app)
    records = list(app.speedtest_history[-app.speedtest_history_limit :])
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
    app.speedtest_history.append(dict(result))
    app.speedtest_history = app.speedtest_history[-app.speedtest_history_limit :]
    persist_speedtest_history(app)


def speedtest_warn_messages(result):
    warns = []
    if not isinstance(result, dict):
        return warns
    dl = result.get("download_mbps")
    ul = result.get("upload_mbps")
    ping = result.get("ping_ms")
    jitter = result.get("jitter_ms")

    if (
        isinstance(dl, (int, float))
        and dl < SPEEDTEST_WARN_DEFAULTS["download_mbps_min"]
    ):
        warns.append(
            f"Download niedrig: {dl:.1f} Mbit/s (< {SPEEDTEST_WARN_DEFAULTS['download_mbps_min']:.1f})"
        )
    if isinstance(ul, (int, float)) and ul < SPEEDTEST_WARN_DEFAULTS["upload_mbps_min"]:
        warns.append(
            f"Upload niedrig: {ul:.1f} Mbit/s (< {SPEEDTEST_WARN_DEFAULTS['upload_mbps_min']:.1f})"
        )
    if isinstance(ping, (int, float)) and ping > SPEEDTEST_WARN_DEFAULTS["ping_ms_max"]:
        warns.append(
            f"Ping hoch: {ping:.0f} ms (> {SPEEDTEST_WARN_DEFAULTS['ping_ms_max']:.0f})"
        )
    if (
        isinstance(jitter, (int, float))
        and jitter > SPEEDTEST_WARN_DEFAULTS["jitter_ms_max"]
    ):
        warns.append(
            f"Jitter hoch: {jitter:.0f} ms (> {SPEEDTEST_WARN_DEFAULTS['jitter_ms_max']:.0f})"
        )
    return warns


def update_speedtest_panel(app, result):
    if not result:
        app.speedtest_ping_var.set("-")
        app.speedtest_jitter_var.set("-")
        app.speedtest_download_var.set("-")
        app.speedtest_upload_var.set("-")
        app.speedtest_timestamp_var.set("Noch kein Speedtest durchgeführt")
        return

    ping = result.get("ping_ms")
    jitter = result.get("jitter_ms")
    download = result.get("download_mbps")
    upload = result.get("upload_mbps")
    timestamp = result.get("timestamp")

    app.speedtest_ping_var.set(f"{round(ping)} ms" if ping is not None else "-")
    app.speedtest_jitter_var.set(f"{round(jitter)} ms" if jitter is not None else "-")
    app.speedtest_download_var.set(
        f"{download:.1f} Mbit/s" if download is not None else "-"
    )
    app.speedtest_upload_var.set(f"{upload:.1f} Mbit/s" if upload is not None else "-")
    app.speedtest_timestamp_var.set(timestamp or "-")


def show_speedtest_history(app):
    if not app.speedtest_history:
        app.log("Speedtest-Verlauf: noch keine Einträge.")
        return

    app.log("Speedtest-Verlauf (letzte Ergebnisse):")
    for item in app.speedtest_history[-app.speedtest_history_limit :]:
        stamp = item.get("timestamp") or "-"
        ping = item.get("ping_ms")
        jitter = item.get("jitter_ms")
        download = item.get("download_mbps")
        upload = item.get("upload_mbps")

        ping_txt = "-" if ping is None else f"{ping:.0f}"
        jitter_txt = "-" if jitter is None else f"{jitter:.0f}"
        dl_txt = "-" if download is None else f"{download:.1f}"
        ul_txt = "-" if upload is None else f"{upload:.1f}"
        app.log(
            f"{stamp} | Ping {ping_txt} ms | Jitter {jitter_txt} ms | DL {dl_txt} | UL {ul_txt}"
        )


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
        app.log_safe("Speedtest gestartet...")
        result, err = run_speedtest_fn(run_cmd_fn, has_cmd_fn, timeout=120)
        if err:
            app.log_safe(f"Speedtest fehlgeschlagen: {err}")
            marker = "Versuchte Befehle:"
            if marker in str(err):
                attempted = str(err).split(marker, 1)[1].strip()
                if attempted:
                    app.log_safe(f"Speedtest-Diagnose (CLI): {attempted}")
            return

        append_speedtest_history(app, result)
        app.after(0, lambda r=dict(result): update_speedtest_panel(app, r))
        app.log_debug_safe(json.dumps(result, ensure_ascii=False))
        app.log_debug_safe(format_summary_fn(result))
        app.log_debug_safe(format_table_fn(result))
        app.log_safe("Speedtest abgeschlossen.")

        for warn in speedtest_warn_messages(result):
            app.log_debug_safe(f"[WARN] Speedtest: {warn}")

        if getattr(app, "debug_mode", False):
            app.log_debug_safe(
                f"Speedtest intern: tool={result.get('tool','-')} history={len(app.speedtest_history)}"
            )

    threading.Thread(target=job, daemon=True).start()
