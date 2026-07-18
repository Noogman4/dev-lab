"""ClamAV controller helpers for NetMon."""

from __future__ import annotations

import json
import os
import re
import signal
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import getpass

try:
    from netmon.core.utils import safe_write_json, call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import safe_write_json, call_in_ui_thread

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.core.tooling import has_cmd
except ModuleNotFoundError:
    from core.tooling import has_cmd


CLAMAV_DATABASE_EXTENSIONS = (".cvd", ".cld")
CLAMAV_PROGRESS_TICK_MS = 500
CLAMAV_QUICK_TARGET_IDS = (
    "downloads",
    "desktop",
    "documents_de",
    "documents_en",
)


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _app_list(app, name: str):
    return list(_app_value(app, name, []) or [])


def _app_var_set(app, name: str, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _app_widget(app, name: str):
    return _app_value(app, name)


def _clamav_runtime_state(app):
    started = float(getattr(app, "clamav_scan_started_at", 0.0) or 0.0)
    scanned = int(getattr(app, "clamav_scanned_files", 0) or 0)
    expected = getattr(app, "clamav_expected_files", None)
    return started, scanned, expected


def _tr(app, key: str, default: str) -> str:
    translator = getattr(app, "tr", None)
    if callable(translator):
        try:
            return str(translator(key, default) or default)
        except Exception:
            return default
    return default


def clamav_user_database_dir() -> str:
    xdg_data_home = str(os.environ.get("XDG_DATA_HOME", "") or "").strip()
    if xdg_data_home:
        base_dir = os.path.abspath(os.path.expanduser(xdg_data_home))
    else:
        user_home = os.path.expanduser(f"~{getpass.getuser()}")
        base_dir = os.path.join(user_home, ".local", "share")
    return os.path.join(base_dir, "netmon", "clamav-db")


def _clamav_database_dir_is_secure(path: str) -> bool:
    try:
        entry = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(entry.st_mode) or not stat.S_ISDIR(entry.st_mode):
        return False
    if entry.st_uid != os.getuid():
        return False
    return (stat.S_IMODE(entry.st_mode) & 0o077) == 0


def clamav_database_dir_has_signatures(path: str) -> bool:
    if not path or not os.path.isdir(path):
        return False
    try:
        return any(
            entry.lower().endswith(CLAMAV_DATABASE_EXTENSIONS)
            for entry in os.listdir(path)
        )
    except Exception:
        return False


def clamav_database_args(app) -> list[str]:
    user_db_dir = clamav_user_database_dir()
    candidates = [
        _app_value(app, "clamav_database_dir", ""),
        user_db_dir,
        "/var/lib/clamav",
    ]
    seen = set()
    for path in candidates:
        path = str(path or "").strip()
        if not path or path in seen:
            continue
        seen.add(path)
        if path != "/var/lib/clamav" and not _clamav_database_dir_is_secure(path):
            continue
        if clamav_database_dir_has_signatures(path):
            return ["--database", path]
    return []


def _clamav_findings_path(app) -> str:
    return str(getattr(app, "clamav_findings_path", "") or "").strip()


def _safe_makedirs_no_symlink(path: str) -> None:
    target = os.path.abspath(str(path or "").strip())
    if not target:
        raise ValueError("empty path")

    current = os.path.sep
    for part in [item for item in target.split(os.path.sep) if item]:
        current = os.path.join(current, part)
        if os.path.lexists(current):
            entry = os.lstat(current)
            if stat.S_ISLNK(entry.st_mode):
                raise RuntimeError(f"Symlink path component not allowed: {current}")
            if not stat.S_ISDIR(entry.st_mode):
                raise RuntimeError(
                    f"Non-directory path component not allowed: {current}"
                )
            continue
        os.mkdir(current, 0o700)


def update_clamav_panel(
    app,
    status=None,
    signatures=None,
    last_scan=None,
    last_target=None,
    findings=None,
    result=None,
):
    updates = (
        ("clamav_status_var", status),
        ("clamav_signatures_var", signatures),
        ("clamav_last_scan_var", last_scan),
        ("clamav_last_target_var", last_target),
        ("clamav_findings_var", findings),
        ("clamav_result_var", result),
    )
    for name, value in updates:
        if value is not None:
            _app_var_set(app, name, value)


def update_clamav_panel_safe(
    app,
    status=None,
    signatures=None,
    last_scan=None,
    last_target=None,
    findings=None,
    result=None,
):
    if threading.current_thread() is threading.main_thread():
        update_clamav_panel(
            app,
            status=status,
            signatures=signatures,
            last_scan=last_scan,
            last_target=last_target,
            findings=findings,
            result=result,
        )
        return
    app.after(
        0,
        lambda s=status, sig=signatures, ls=last_scan, lt=last_target, f=findings, r=result: update_clamav_panel(
            app,
            status=s,
            signatures=sig,
            last_scan=ls,
            last_target=lt,
            findings=f,
            result=r,
        ),
    )


def clamav_findings_open(app):
    return [
        item
        for item in _app_list(app, "clamav_findings")
        if (item.get("status") or "").strip().lower() == "found"
    ]


def clamav_findings_quarantined(app):
    return [
        item
        for item in _app_list(app, "clamav_findings")
        if (item.get("status") or "").strip().lower() == "quarantine"
        and (item.get("quarantine_path") or "").strip()
    ]


def update_clamav_findings_buttons_state(app):
    has_open = bool(clamav_findings_open(app))
    has_quarantined = bool(clamav_findings_quarantined(app))
    open_state = "normal" if has_open else "disabled"
    quarantine_state = "normal" if has_quarantined else "disabled"

    for name in (
        "btn_clamav_show_findings",
        "btn_clamav_quarantine",
        "btn_clamav_quarantine_selected",
    ):
        btn = _app_widget(app, name)
        if btn is not None:
            try:
                btn.configure(state=open_state)
            except Exception:
                pass

    export_btn = _app_widget(app, "btn_clamav_export_findings")
    if export_btn is not None:
        try:
            export_btn.configure(
                state=(
                    "normal" if bool(_app_list(app, "clamav_findings")) else "disabled"
                )
            )
        except Exception:
            pass

    for name in (
        "btn_clamav_show_quarantine",
        "btn_clamav_restore_quarantine",
        "btn_clamav_restore_selected",
    ):
        btn = _app_widget(app, name)
        if btn is not None:
            try:
                btn.configure(state=quarantine_state)
            except Exception:
                pass


def update_clamav_findings_buttons_state_safe(app):
    if threading.current_thread() is threading.main_thread():
        update_clamav_findings_buttons_state(app)
        return
    call_in_ui_thread(app, lambda: update_clamav_findings_buttons_state(app))


def clamav_is_excluded_root(path, excluded_roots):
    real = os.path.realpath(path)
    for root in excluded_roots or []:
        resolved_root = os.path.realpath(root)
        if real == resolved_root or real.startswith(resolved_root + os.sep):
            return True
    return False


def clamav_system_targets():
    home = os.path.expanduser("~")
    candidates = [home, "/etc", "/opt", "/usr/local"]
    targets = []
    seen = set()
    for raw in candidates:
        path = os.path.realpath(os.path.normpath(raw))
        if path in seen:
            continue
        seen.add(path)
        if os.path.isdir(path):
            targets.append(path)
    return targets


def clamav_system_excluded_roots():
    return [
        "/proc",
        "/sys",
        "/dev",
        "/run",
        "/tmp",
        "/var/tmp",
    ]


def clamav_quick_target_definitions():
    home = os.path.expanduser("~")
    return [
        {
            "id": "downloads",
            "label": "Downloads",
            "path": os.path.join(home, "Downloads"),
        },
        {
            "id": "desktop",
            "label": "Desktop",
            "path": os.path.join(home, "Desktop"),
        },
        {
            "id": "documents_de",
            "label": "Dokumente",
            "path": os.path.join(home, "Dokumente"),
        },
        {
            "id": "documents_en",
            "label": "Documents",
            "path": os.path.join(home, "Documents"),
        },
    ]


def clamav_default_quick_target_ids():
    return ["downloads", "desktop", "documents_de", "documents_en"]


def clamav_normalize_quick_target_ids(target_ids):
    allowed = set(CLAMAV_QUICK_TARGET_IDS)
    normalized = []
    for raw in target_ids or []:
        value = str(raw or "").strip().lower()
        if value and value in allowed and value not in normalized:
            normalized.append(value)
    return normalized


def clamav_normalize_custom_quick_paths(paths):
    normalized = []
    seen = set()
    for raw in paths or []:
        value = str(raw or "").strip()
        if not value:
            continue
        path = os.path.realpath(os.path.normpath(value))
        if not os.path.isabs(path) or path in seen:
            continue
        seen.add(path)
        normalized.append(path)
    return normalized


def clamav_load_quickscan_config(app):
    settings = getattr(app, "settings", {}) if app is not None else {}
    if not isinstance(settings, dict):
        settings = {}
    target_ids = clamav_normalize_quick_target_ids(
        settings.get("clamav_quickscan_targets")
    )
    if not target_ids:
        target_ids = clamav_default_quick_target_ids()
    custom_paths = clamav_normalize_custom_quick_paths(
        settings.get("clamav_quickscan_custom_paths")
    )
    app.clamav_quickscan_target_ids = list(target_ids)
    app.clamav_quickscan_custom_paths = list(custom_paths)
    return target_ids, custom_paths


def clamav_quick_excluded_roots():
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".cache"),
        os.path.join(home, ".local", "share", "Trash"),
        os.path.join(home, ".local", "share", "Steam"),
        os.path.join(home, ".steam"),
        os.path.join(home, "snap"),
    ]
    seen = set()
    excluded = []
    for path in candidates:
        norm = os.path.realpath(os.path.normpath(path))
        if norm in seen or not os.path.isdir(norm):
            continue
        seen.add(norm)
        excluded.append(norm)
    return excluded


def clamav_exclude_dir_args(paths):
    args = []
    seen = set()
    for raw_path in paths or []:
        path = os.path.realpath(os.path.normpath(str(raw_path or "").strip()))
        if not path or path in seen:
            continue
        seen.add(path)
        args.append(f"--exclude-dir=^{re.escape(path)}($|/)")
    return args


def clamav_count_files(app, targets, excluded_roots=None, limit=600000):
    total = 0
    excluded_roots = list(excluded_roots or [])
    for target in targets or []:
        if not os.path.isdir(target):
            continue
        for root, dirs, files in os.walk(target, topdown=True):
            if clamav_is_excluded_root(root, excluded_roots):
                dirs[:] = []
                continue
            dirs[:] = [
                directory
                for directory in dirs
                if not clamav_is_excluded_root(
                    os.path.join(root, directory), excluded_roots
                )
            ]
            total += len(files)
            if total >= limit:
                return total
    return total


def clamav_select_items_dialog(app, items, title, mode="found"):
    if not items:
        return None

    win = tk.Toplevel(app)
    win.title(title)
    win.transient(app)
    win.grab_set()
    win.resizable(True, True)
    win.minsize(760, 360)

    container = ttk.Frame(win, padding=10)
    container.pack(fill="both", expand=True)

    hint = (
        "Mehrfachauswahl mit Strg/Shift möglich."
        if mode == "found"
        else "Wähle Quarantäne-Einträge zur Wiederherstellung aus."
    )
    ttk.Label(container, text=hint).pack(anchor="w", pady=(0, 8))

    list_wrap = ttk.Frame(container)
    list_wrap.pack(fill="both", expand=True)
    list_wrap.columnconfigure(0, weight=1)
    list_wrap.rowconfigure(0, weight=1)

    listbox = tk.Listbox(
        list_wrap,
        selectmode=tk.EXTENDED,
        exportselection=False,
        font=("Courier", 10),
    )
    listbox.grid(row=0, column=0, sticky="nsew")
    scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=listbox.yview)
    scroll.grid(row=0, column=1, sticky="ns")
    listbox.configure(yscrollcommand=scroll.set)

    for idx, item in enumerate(items, start=1):
        src = (item.get("path") or "-").strip() or "-"
        sig = (item.get("signature") or "-").strip() or "-"
        marker = ""
        if mode == "quarantine":
            qpath = (item.get("quarantine_path") or "").strip()
            marker = f" | Q: {qpath}" if qpath else ""
        line = f"{idx:>2}. {src} | Sig: {sig}{marker}"
        if len(line) > 240:
            line = line[:237] + "..."
        listbox.insert("end", line)

    result = {"selection": None}

    def on_select_all():
        listbox.selection_set(0, "end")

    def on_clear():
        listbox.selection_clear(0, "end")

    def on_cancel():
        result["selection"] = None
        win.destroy()

    def on_ok():
        selected_idx = listbox.curselection()
        if not selected_idx:
            result["selection"] = []
        else:
            result["selection"] = [items[i] for i in selected_idx if i < len(items)]
        win.destroy()

    btns = ttk.Frame(container)
    btns.pack(fill="x", pady=(10, 0))
    ttk.Button(btns, text="Alle", command=on_select_all).pack(side="left")
    ttk.Button(btns, text="Keine", command=on_clear).pack(side="left", padx=(8, 0))
    ttk.Button(btns, text="Abbrechen", command=on_cancel).pack(side="right")
    ttk.Button(btns, text="Übernehmen", command=on_ok).pack(side="right", padx=(0, 8))

    win.protocol("WM_DELETE_WINDOW", on_cancel)
    win.wait_window()
    return result["selection"]


def set_clamav_abort_button_state(app, enabled):
    btn = _app_widget(app, "btn_clamav_abort_scan")
    if btn is None:
        return
    state = "normal" if enabled else "disabled"
    if threading.current_thread() is threading.main_thread():
        try:
            btn.configure(state=state)
        except Exception:
            pass
        return
    call_in_ui_thread(app, lambda s=state: btn.configure(state=s))


def run_clamscan_with_progress(app, cmd, timeout=3600, progress_cb=None):
    proc = None
    cancelled = False
    timed_out = False
    out_lines = []
    scanned = 0

    app.clamav_cancel_requested = False
    app._set_clamav_abort_button_state(True)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
        app.clamav_active_process = proc
        started = time.time()

        while True:
            if app.clamav_cancel_requested and proc.poll() is None:
                cancelled = True
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except Exception:
                    try:
                        proc.terminate()
                    except Exception:
                        pass

            if (time.time() - started) > float(timeout) and proc.poll() is None:
                timed_out = True
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except Exception:
                    try:
                        proc.terminate()
                    except Exception:
                        pass

            line = proc.stdout.readline() if proc.stdout is not None else ""
            if line:
                out_lines.append(line)
                text = line.strip()
                if text.endswith(" OK") or text.endswith(" FOUND"):
                    scanned += 1
                    if callable(progress_cb):
                        progress_cb(scanned)

            if proc.poll() is not None:
                try:
                    rest = proc.stdout.read() if proc.stdout is not None else ""
                except Exception:
                    rest = ""
                if rest:
                    out_lines.append(rest)
                break

            if not line:
                time.sleep(0.05)

        rc = proc.returncode if proc.returncode is not None else 1
        if timed_out:
            rc = 124
        elif rc < 0:
            cancelled = True
        elif cancelled and rc == 0:
            rc = -15
        return rc, "".join(out_lines), cancelled, timed_out, scanned
    finally:
        app.clamav_active_process = None
        app._set_clamav_abort_button_state(False)
        app.clamav_cancel_requested = False


def run_clamscan_with_cancel(app, cmd, timeout=900):
    proc = None
    cancelled = False
    out = ""
    rc = 1
    app.clamav_cancel_requested = False
    app._set_clamav_abort_button_state(True)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        app.clamav_active_process = proc

        while True:
            if app.clamav_cancel_requested and proc.poll() is None:
                cancelled = True
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except Exception:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
            try:
                out, _ = proc.communicate(timeout=0.25)
                rc = proc.returncode if proc.returncode is not None else 1
                break
            except subprocess.TimeoutExpired:
                if app.clamav_cancel_requested:
                    cancelled = True
                    continue

        if cancelled and rc not in (0,):
            rc = -15
        return rc, out or "", cancelled
    finally:
        app.clamav_active_process = None
        app._set_clamav_abort_button_state(False)
        app.clamav_cancel_requested = False


def write_clamav_output(app, lines, replace=True):
    widget = _app_widget(app, "clamav_output_text")
    if widget is None:
        return

    if isinstance(lines, str):
        text = lines
    else:
        text = "\n".join([str(line) for line in (lines or [])])
    if text and not text.endswith("\n"):
        text += "\n"

    def _apply():
        try:
            widget.configure(state="normal")
            if replace:
                widget.delete("1.0", "end")
            widget.insert("end", text)
            widget.see("end")
            widget.configure(state="disabled")
        except Exception:
            pass

    if threading.current_thread() is threading.main_thread():
        _apply()
        return
    call_in_ui_thread(app, _apply)


def clamav_scan_failure_lines(app, title, target_label, scanned_files, rc, output):
    error_line = clamav_extract_error_message(output)
    lines = [
        title,
        _tr(app, "clamav_output_target", "Ziel: {value}").format(
            value=target_label or "-"
        ),
        _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
            value=scanned_files
        ),
        _tr(app, "clamav_output_return_code", "Rückgabecode: {value}").format(
            value=rc
        ),
    ]
    if error_line:
        lines.append(
            _tr(app, "clamav_output_details", "Details: {value}").format(
                value=error_line
            )
        )
    else:
        lines.append(
            _tr(
                app,
                "clamav_output_details_no_error_line",
                "Details: keine technische Fehlerzeile erkannt",
            )
        )
    raw_lines = [line.strip() for line in (output or "").splitlines() if line.strip()]
    if raw_lines:
        lines.extend(
            ["", _tr(app, "clamav_output_raw_section", "ClamAV-Ausgabe:"), *raw_lines[-8:]]
        )
    return lines


def format_runtime_hms(seconds):
    try:
        total = max(0, int(seconds))
    except Exception:
        total = 0
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def clamav_progress_apply(app):
    started, scanned, expected = _clamav_runtime_state(app)
    elapsed = max(0.0, time.time() - started) if started > 0 else 0.0

    runtime_txt = format_runtime_hms(elapsed) if started > 0 else "-"
    speed_txt = "-"
    eta_txt = "-"
    if elapsed >= 1.0 and scanned > 0:
        speed = scanned / elapsed
        speed_txt = f"{speed:.1f} Dateien/s"
        if (
            isinstance(expected, int)
            and expected > scanned
            and speed > 0.1
            and scanned >= 10
        ):
            remaining = expected - scanned
            eta_seconds = int(max(1, remaining / speed))
            if eta_seconds >= 3600:
                eta_txt = f"~{eta_seconds // 3600} h"
            elif eta_seconds >= 60:
                eta_txt = f"~{eta_seconds // 60} min"
            else:
                eta_txt = f"~{eta_seconds} s"
        elif isinstance(expected, int) and expected > 0:
            eta_txt = "wird berechnet..."

    _app_var_set(app, "clamav_runtime_var", runtime_txt)
    _app_var_set(app, "clamav_scanned_files_var", str(max(0, scanned)))
    _app_var_set(app, "clamav_speed_var", speed_txt)
    _app_var_set(app, "clamav_eta_var", eta_txt)


def clamav_progress_tick(app):
    app.clamav_progress_after_id = None
    clamav_progress_apply(app)
    if getattr(app, "security_clamav_running", False):
        try:
            app.clamav_progress_after_id = app.after(
                CLAMAV_PROGRESS_TICK_MS,
                lambda: clamav_progress_tick(app),
            )
        except Exception:
            app.clamav_progress_after_id = None


def clamav_progress_start(app, expected_files=None):
    app.clamav_scan_started_at = time.time()
    app.clamav_scanned_files = 0
    app.clamav_expected_files = (
        int(expected_files)
        if isinstance(expected_files, int) and expected_files > 0
        else None
    )
    if app.clamav_progress_after_id is not None:
        try:
            app.after_cancel(app.clamav_progress_after_id)
        except Exception:
            pass
        app.clamav_progress_after_id = None
    clamav_progress_apply(app)
    try:
        app.clamav_progress_after_id = app.after(
            CLAMAV_PROGRESS_TICK_MS,
            lambda: clamav_progress_tick(app),
        )
    except Exception:
        app.clamav_progress_after_id = None


def clamav_progress_update_safe(app, scanned_files):
    def _apply():
        try:
            val = int(scanned_files)
        except Exception:
            val = 0
        if val > app.clamav_scanned_files:
            app.clamav_scanned_files = val
        clamav_progress_apply(app)

    if threading.current_thread() is threading.main_thread():
        _apply()
        return
    call_in_ui_thread(app, _apply)


def clamav_progress_finish_safe(app):
    def _finish():
        if app.clamav_progress_after_id is not None:
            try:
                app.after_cancel(app.clamav_progress_after_id)
            except Exception:
                pass
            app.clamav_progress_after_id = None
        clamav_progress_apply(app)
        _app_var_set(app, "clamav_eta_var", "-")
        app.clamav_scan_started_at = 0.0
        app.clamav_expected_files = None

    if threading.current_thread() is threading.main_thread():
        _finish()
        return
    call_in_ui_thread(app, _finish)


def clamav_parse_scanned_files(output):
    for line in (output or "").splitlines():
        s = line.strip()
        if s.startswith("Scanned files:"):
            try:
                return int(s.split(":", 1)[1].strip())
            except Exception:
                return None
    return None


def load_clamav_findings(app):
    app.clamav_findings = []
    path = _clamav_findings_path(app)
    if not path or not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if not isinstance(raw, list):
            return
        cleaned = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            p = (item.get("path") or "").strip()
            if not p:
                continue
            cleaned.append(
                {
                    "path": p,
                    "signature": (item.get("signature") or "-").strip() or "-",
                    "timestamp": (item.get("timestamp") or "").strip()
                    or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "scan_type": (item.get("scan_type") or "unknown").strip()
                    or "unknown",
                    "status": (item.get("status") or "found").strip() or "found",
                    "quarantine_path": (item.get("quarantine_path") or "").strip(),
                    "quarantine_timestamp": (
                        item.get("quarantine_timestamp") or ""
                    ).strip(),
                }
            )
        app.clamav_findings = cleaned[-300:]
    except Exception as exc:
        app.log_debug(f"ClamAV-Fundliste laden fehlgeschlagen: {exc}")


def save_clamav_findings(app):
    path = _clamav_findings_path(app)
    if not path:
        return
    ok, err = safe_write_json(
        path,
        app.clamav_findings[-300:],
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        app.log_debug(f"ClamAV-Fundliste speichern fehlgeschlagen: {err}")


def clamav_extract_findings(output, scan_type, timestamp):
    findings = []
    pattern = re.compile(r"^(.*?):\s(.+?)\sFOUND$")
    for raw_line in (output or "").splitlines():
        line = raw_line.strip()
        match = pattern.match(line)
        if not match:
            continue
        file_path = os.path.normpath((match.group(1) or "").strip())
        signature = (match.group(2) or "-").strip() or "-"
        if not file_path:
            continue
        findings.append(
            {
                "path": file_path,
                "signature": signature,
                "timestamp": timestamp,
                "scan_type": scan_type,
                "status": "found",
            }
        )
    return findings


def clamav_replace_open_findings(app, findings):
    history = [
        item
        for item in _app_list(app, "clamav_findings")
        if (item.get("status") or "").strip().lower() != "found"
    ]
    app.clamav_findings = (history + list(findings or []))[-300:]
    save_clamav_findings(app)
    update_clamav_findings_buttons_state_safe(app)


def clamav_next_quarantine_path(app, source_path):
    base = os.path.basename(source_path.rstrip(os.sep)) or "file"
    stem, ext = os.path.splitext(base)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    candidate = os.path.join(
        app.clamav_quarantine_dir,
        f"{stem}__quarantine__{stamp}{ext}",
    )
    idx = 1
    while os.path.exists(candidate):
        candidate = os.path.join(
            app.clamav_quarantine_dir,
            f"{stem}__quarantine__{stamp}_{idx}{ext}",
        )
        idx += 1
    return candidate


def clamav_next_restore_path(original_path):
    target = os.path.normpath(original_path)
    if not os.path.exists(target):
        return target

    base = os.path.basename(target.rstrip(os.sep)) or "file"
    stem, ext = os.path.splitext(base)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    parent = os.path.dirname(target) or os.path.expanduser("~")
    candidate = os.path.join(parent, f"{stem}__restored__{stamp}{ext}")
    idx = 1
    while os.path.exists(candidate):
        candidate = os.path.join(
            parent,
            f"{stem}__restored__{stamp}_{idx}{ext}",
        )
        idx += 1
    return candidate


def clamav_path_is_within(candidate_path, root_path):
    try:
        candidate_real = os.path.realpath(candidate_path)
        root_real = os.path.realpath(root_path)
        return os.path.commonpath([candidate_real, root_real]) == root_real
    except Exception:
        return False


def clamav_validate_source_for_quarantine(app, source_path):
    src = os.path.realpath(os.path.normpath((source_path or "").strip()))
    if not src:
        return None, "leer"
    if not os.path.isabs(src):
        return None, "nicht absolut"
    if not os.path.exists(src):
        return None, "nicht vorhanden"
    if os.path.isdir(src):
        return None, "ist ein Ordner"
    home_root = os.path.realpath(os.path.expanduser("~"))
    if not clamav_path_is_within(src, home_root):
        return None, "außerhalb des Home-Verzeichnisses"
    return src, ""


def clamav_validate_quarantine_path(app, quarantine_path):
    qpath = os.path.realpath(os.path.normpath((quarantine_path or "").strip()))
    if not qpath:
        return None, "leer"
    if not os.path.isabs(qpath):
        return None, "nicht absolut"
    if not clamav_path_is_within(qpath, app.clamav_quarantine_dir):
        return None, "außerhalb des Quarantäne-Ordners"
    return qpath, ""


def clamav_safe_restore_source(original_path):
    original = os.path.realpath(os.path.normpath((original_path or "").strip()))
    home_root = os.path.realpath(os.path.expanduser("~"))
    if original and clamav_path_is_within(original, home_root):
        return original
    base = os.path.basename((original_path or "").strip()) or "restored_file"
    return os.path.join(home_root, base)


def clamav_quick_targets():
    candidates = [item["path"] for item in clamav_quick_target_definitions()]
    seen = set()
    targets = []
    for path in candidates:
        norm = os.path.normpath(path)
        if norm in seen:
            continue
        seen.add(norm)
        if os.path.isdir(norm):
            targets.append(norm)
    return targets, False


def clamav_quick_targets_for_app(app):
    configured_ids = clamav_normalize_quick_target_ids(
        getattr(app, "clamav_quickscan_target_ids", None)
    )
    if not configured_ids:
        configured_ids, _custom = clamav_load_quickscan_config(app)
    configured_custom = clamav_normalize_custom_quick_paths(
        getattr(app, "clamav_quickscan_custom_paths", None)
    )
    definitions = {item["id"]: item for item in clamav_quick_target_definitions()}

    targets = []
    seen = set()
    for target_id in configured_ids:
        item = definitions.get(target_id)
        if item is None:
            continue
        path = os.path.realpath(os.path.normpath(item["path"]))
        if not os.path.isdir(path) or path in seen:
            continue
        seen.add(path)
        targets.append(path)

    for path in configured_custom:
        real = os.path.realpath(os.path.normpath(path))
        if not os.path.isdir(real) or real in seen:
            continue
        seen.add(real)
        targets.append(real)

    return targets, False


def clamav_configure_quickscan_paths_dialog(app):
    existing = _app_value(app, "clamav_quickscan_popup", None)
    if existing is not None and getattr(existing, "winfo_exists", lambda: False)():
        try:
            existing.deiconify()
            existing.lift()
            existing.focus_force()
        except Exception:
            pass
        return

    target_ids, custom_paths = clamav_load_quickscan_config(app)
    win = tk.Toplevel(app)
    win.title(
        _tr(
            app,
            "clamav_quick_paths_dialog_title",
            "ClamAV Schnellscan-Pfade",
        )
    )
    win.transient(app)
    win.resizable(True, True)
    win.minsize(720, 420)
    app.clamav_quickscan_popup = win

    container = ttk.Frame(win, padding=12)
    container.pack(fill="both", expand=True)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(3, weight=1)

    ttk.Label(
        container,
        text=_tr(
            app,
            "clamav_quick_paths_dialog_body",
            "Wähle Standardpfade für den Schnellscan und füge bei Bedarf eigene Ordner hinzu.",
        ),
        justify="left",
        wraplength=640,
    ).grid(row=0, column=0, sticky="w")

    standard_frame = ttk.LabelFrame(
        container,
        text=_tr(app, "clamav_quick_paths_group_standard", "Standardpfade"),
        padding=8,
    )
    standard_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    standard_vars = {}
    for row, item in enumerate(clamav_quick_target_definitions()):
        path = os.path.realpath(os.path.normpath(item["path"]))
        var = tk.BooleanVar(value=item["id"] in target_ids)
        standard_vars[item["id"]] = var
        ttk.Checkbutton(
            standard_frame,
            text=f"{item['label']} ({path})",
            variable=var,
        ).grid(row=row, column=0, sticky="w", pady=2)

    custom_frame = ttk.LabelFrame(
        container,
        text=_tr(app, "clamav_quick_paths_group_custom", "Eigene Ordner"),
        padding=8,
    )
    custom_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
    custom_frame.columnconfigure(0, weight=1)
    custom_frame.rowconfigure(0, weight=1)

    list_frame = ttk.Frame(custom_frame)
    list_frame.grid(row=0, column=0, sticky="nsew")
    list_frame.columnconfigure(0, weight=1)
    list_frame.rowconfigure(0, weight=1)

    custom_list = tk.Listbox(list_frame, height=8, exportselection=False)
    custom_list.grid(row=0, column=0, sticky="nsew")
    custom_scroll = ttk.Scrollbar(
        list_frame, orient="vertical", command=custom_list.yview
    )
    custom_scroll.grid(row=0, column=1, sticky="ns")
    custom_list.configure(yscrollcommand=custom_scroll.set)

    def refresh_custom_list(items):
        custom_list.delete(0, "end")
        for item in items:
            custom_list.insert("end", item)

    current_custom = list(custom_paths)
    refresh_custom_list(current_custom)

    def on_add_folder():
        selected = filedialog.askdirectory(
            title=_tr(
                app,
                "clamav_quick_paths_add_folder_dialog_title",
                "Ordner für ClamAV-Schnellscan auswählen",
            ),
            initialdir=os.path.expanduser("~"),
            mustexist=True,
        )
        if not selected:
            return
        path = os.path.realpath(os.path.normpath(selected))
        if path not in current_custom:
            current_custom.append(path)
            refresh_custom_list(current_custom)

    def on_remove_selected():
        selected = list(custom_list.curselection())
        if not selected:
            return
        for index in reversed(selected):
            if 0 <= index < len(current_custom):
                current_custom.pop(index)
        refresh_custom_list(current_custom)

    def on_reset_defaults():
        for target_id, var in standard_vars.items():
            var.set(target_id in clamav_default_quick_target_ids())
        current_custom.clear()
        refresh_custom_list(current_custom)

    buttons = ttk.Frame(custom_frame)
    buttons.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    ttk.Button(
        buttons,
        text=_tr(
            app,
            "clamav_quick_paths_btn_add_folder",
            "Ordner hinzufügen",
        ),
        command=on_add_folder,
    ).pack(side="left")
    ttk.Button(
        buttons,
        text=_tr(
            app,
            "setup_assistant_btn_remove_selection",
            "Auswahl entfernen",
        ),
        command=on_remove_selected,
    ).pack(
        side="left", padx=(8, 0)
    )
    ttk.Button(
        buttons,
        text=_tr(app, "clamav_quick_paths_btn_reset", "Standard"),
        command=on_reset_defaults,
    ).pack(
        side="left", padx=(8, 0)
    )

    status_var = tk.StringVar(value="")
    ttk.Label(container, textvariable=status_var).grid(
        row=4, column=0, sticky="w", pady=(10, 0)
    )

    def close_popup():
        app.__dict__.pop("clamav_quickscan_popup", None)
        win.destroy()

    def on_save():
        selected_target_ids = [
            target_id for target_id, var in standard_vars.items() if bool(var.get())
        ]
        normalized_target_ids = clamav_normalize_quick_target_ids(selected_target_ids)
        normalized_custom = clamav_normalize_custom_quick_paths(current_custom)
        if not normalized_target_ids and not normalized_custom:
            status_var.set(
                _tr(
                    app,
                    "clamav_quick_paths_validation_select_one",
                    "Bitte mindestens einen Schnellscan-Pfad auswählen.",
                )
            )
            return
        app.clamav_quickscan_target_ids = normalized_target_ids
        app.clamav_quickscan_custom_paths = normalized_custom
        app.settings["clamav_quickscan_targets"] = list(normalized_target_ids)
        app.settings["clamav_quickscan_custom_paths"] = list(normalized_custom)
        app.save_settings(log_success=False)
        app.log_safe(
            _tr(
                app,
                "clamav_quick_paths_log_saved",
                "ClamAV-Schnellscan-Pfade gespeichert: {value}",
            ).format(value=", ".join(normalized_target_ids + normalized_custom))
        )
        close_popup()

    action_row = ttk.Frame(container)
    action_row.grid(row=5, column=0, sticky="ew", pady=(12, 0))
    ttk.Button(
        action_row,
        text=_tr(app, "btn_cancel", "Abbrechen"),
        command=close_popup,
    ).pack(side="right")
    ttk.Button(
        action_row,
        text=_tr(app, "btn_save", "Speichern"),
        command=on_save,
    ).pack(
        side="right", padx=(0, 8)
    )

    win.protocol("WM_DELETE_WINDOW", close_popup)


def clamav_extract_error_message(output):
    lines = [ln.strip() for ln in (output or "").splitlines() if ln.strip()]
    if not lines:
        return ""

    priority_patterns = [
        "libclamav error",
        "no supported database files found",
        "database initialization failed",
        "database error",
        "unknown option",
        "invalid option",
    ]
    for line in lines:
        lower = line.lower()
        if any(token in lower for token in priority_patterns):
            return line

    patterns = [
        "error:",
        "access denied",
        "permission denied",
        "can't open",
        "cannot open",
        "can't read",
        "scan aborted",
        "internal error",
        "database error",
    ]

    for line in reversed(lines):
        lower = line.lower()
        if any(token in lower for token in patterns):
            return line

    for line in lines:
        lower = line.lower()
        if lower.startswith("error"):
            return line

    return ""


def clamav_is_nonfatal_scan_issue(output):
    text = (output or "").lower()
    if not text:
        return False

    fatal_markers = [
        "no supported database files found",
        "database initialization failed",
        "libclamav error",
        "unknown option",
        "invalid option",
        "bytecode: security",
    ]
    if any(marker in text for marker in fatal_markers):
        return False

    benign_markers = [
        "can't open file or directory",
        "permission denied",
        "access denied",
        "can't read file",
    ]
    return any(marker in text for marker in benign_markers)


def clamav_allows_nonfatal_scan_completion(output, scanned_files) -> bool:
    try:
        scanned = int(scanned_files)
    except Exception:
        scanned = 0
    if scanned <= 0:
        return False
    return (
        clamav_is_nonfatal_scan_issue(output)
        or clamav_parse_scanned_files(output) is not None
    )


def clamav_is_nonfatal_update_issue(output):
    text = (output or "").lower()
    if not text:
        return False

    nonfatal_markers = [
        "failed to stop clamav-daemon.service: unit clamav-daemon.service not loaded",
        "failed to reload clamav-daemon.service: unit clamav-daemon.service not loaded",
        "failed to restart clamav-daemon.service: unit clamav-daemon.service not loaded",
        "notifyclamd: service clamav-daemon is not running",
    ]
    if not any(marker in text for marker in nonfatal_markers):
        return False

    fatal_markers = [
        "no supported database files found",
        "database initialization failed",
        "can't download",
        "download failed",
        "invalid dns reply",
        "connection failed",
    ]
    return not any(marker in text for marker in fatal_markers)


def clamav_parse_infected_count(output):
    infected_count = None
    for line in (output or "").splitlines():
        s = line.strip()
        if s.startswith("Infected files:"):
            try:
                infected_count = int(s.split(":", 1)[1].strip())
            except Exception:
                infected_count = None
            break
    if infected_count is None:
        infected_count = sum(
            1 for line in (output or "").splitlines() if line.strip().endswith("FOUND")
        )
    return infected_count


def export_clamav_findings(app):
    findings = list(app.clamav_findings or [])
    if not findings:
        app.log("Keine ClamAV-Funde zum Exportieren vorhanden.")
        update_clamav_findings_buttons_state(app)
        return

    export_dir = app._security_export_dir()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(export_dir, f"netmon_clamav_findings_{stamp}.json")
    txt_path = os.path.join(export_dir, f"netmon_clamav_findings_{stamp}.txt")

    try:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(findings, fh, indent=2, ensure_ascii=False)

        with open(txt_path, "w", encoding="utf-8") as fh:
            fh.write("NetMon ClamAV Findings Export\n")
            fh.write(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            fh.write(f"Einträge: {len(findings)}\n\n")
            for idx, item in enumerate(findings, start=1):
                fh.write(f"[{idx}]\n")
                fh.write(f"Status: {item.get('status', '-')}\n")
                fh.write(f"Pfad: {item.get('path', '-')}\n")
                fh.write(f"Signatur: {item.get('signature', '-')}\n")
                fh.write(f"Scan-Typ: {item.get('scan_type', '-')}\n")
                fh.write(f"Zeit: {item.get('timestamp', '-')}\n")
                qpath = item.get("quarantine_path")
                if qpath:
                    fh.write(f"Quarantäne: {qpath}\n")
                rpath = item.get("restore_path")
                if rpath:
                    fh.write(f"Wiederhergestellt nach: {rpath}\n")
                fh.write("\n")

        app.log(f"ClamAV-Funde exportiert: {json_path}")
        app.log(f"ClamAV-Funde exportiert: {txt_path}")
    except Exception as exc:
        app.log(f"ClamAV-Funde Export fehlgeschlagen: {exc}")
        app.log_debug_safe(f"ClamAV-Export Fehler: {exc}")


def log_clamav_quarantine_preview(app, items, label="Trockenlauf"):
    if not items:
        app.log("Keine offenen ClamAV-Funde für die Vorschau vorhanden.")
        return

    preview_limit = 20
    app.log(
        f"ClamAV-Quarantäne {label}: {len(items)} Datei(en) (keine Änderungen durchgeführt)."
    )
    for idx, item in enumerate(items, start=1):
        src = os.path.normpath((item.get("path") or "").strip())
        if not src:
            continue
        if not os.path.exists(src):
            app.log(f"{idx}. [fehlt] {src}")
            continue
        dest = app._clamav_next_quarantine_path(src)
        app.log(f"{idx}. {src}")
        app.log(f"   -> {dest}")
        if idx >= preview_limit:
            rest = len(items) - preview_limit
            if rest > 0:
                app.log(f"... und {rest} weitere Datei(en).")
            break


def log_clamav_restore_preview(app, items, label="Trockenlauf"):
    if not items:
        app.log("Keine Quarantäne-Dateien für die Vorschau vorhanden.")
        return

    preview_limit = 20
    app.log(
        f"ClamAV-Wiederherstellung {label}: {len(items)} Datei(en) (keine Änderungen durchgeführt)."
    )
    for idx, item in enumerate(items, start=1):
        qpath = os.path.normpath((item.get("quarantine_path") or "").strip())
        original = os.path.normpath((item.get("path") or "").strip())
        if not qpath or not original:
            continue
        if not os.path.exists(qpath):
            app.log(f"{idx}. [quarantäne fehlt] {qpath}")
            continue
        dest = app._clamav_next_restore_path(original)
        app.log(f"{idx}. {qpath}")
        app.log(f"   -> {dest}")
        if idx >= preview_limit:
            rest = len(items) - preview_limit
            if rest > 0:
                app.log(f"... und {rest} weitere Datei(en).")
            break


def show_clamav_findings(app):
    findings = clamav_findings_open(app)
    if not findings:
        msg = "Keine offenen ClamAV-Funde vorhanden."
        app.log(msg)
        write_clamav_output(app, [msg], replace=True)
        update_clamav_findings_buttons_state(app)
        return

    lines = ["ClamAV-Funde:", ""]
    app.log("ClamAV-Funde:")
    for idx, item in enumerate(findings, start=1):
        path = item.get("path", "-")
        sig = item.get("signature", "-")
        app.log(f"{idx}. {path}")
        app.log(f"   Signatur: {sig}")
        lines.append(f"{idx}. {path}")
        lines.append(f"   Signatur: {sig}")
        lines.append("")
    write_clamav_output(app, lines, replace=True)


def show_clamav_quarantine_history(app):
    quarantined = clamav_findings_quarantined(app)
    if not quarantined:
        msg = "Keine Dateien in der ClamAV-Quarantäne vorhanden."
        app.log(msg)
        write_clamav_output(app, [msg], replace=True)
        update_clamav_findings_buttons_state(app)
        return

    lines = ["ClamAV-Quarantäne:", ""]
    app.log("ClamAV-Quarantäne:")
    for idx, item in enumerate(quarantined, start=1):
        src = item.get("path", "-")
        qpath = item.get("quarantine_path", "-")
        qts = item.get("quarantine_timestamp") or item.get("timestamp") or "-"
        app.log(f"{idx}. {src}")
        app.log(f"   Quarantäne: {qpath}")
        app.log(f"   Zeit: {qts}")
        lines.append(f"{idx}. {src}")
        lines.append(f"   Quarantäne: {qpath}")
        lines.append(f"   Zeit: {qts}")
        lines.append("")
    write_clamav_output(app, lines, replace=True)


def clamav_abort_scan(app):
    if not app.security_clamav_running:
        app.log("Kein ClamAV-Scan läuft.")
        app._set_clamav_abort_button_state(False)
        return
    app.clamav_cancel_requested = True
    proc = app.clamav_active_process
    if proc is not None and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except Exception:
            try:
                proc.terminate()
            except Exception:
                pass
    app.log("ClamAV-Scan-Abbruch angefordert...")


def security_clamav_update_async(app):
    if not has_cmd("freshclam"):
        update_clamav_panel(
            app, status="nicht installiert", signatures="nicht aktualisierbar"
        )
        app.log("ClamAV-Update nicht möglich: freshclam fehlt.")
        return
    if app.security_clamav_update_running:
        app.log("ClamAV-Update läuft bereits.")
        return

    app.security_clamav_update_running = True
    update_clamav_panel(app, status="Update läuft")

    def job():
        temp_cfg_path = ""
        try:
            app.log_safe("ClamAV-Update gestartet...")

            try:
                user_db_dir = clamav_user_database_dir()
                user_tag = re.sub(r"[^a-zA-Z0-9_.-]", "_", getpass.getuser())
                user_log_file = os.path.join(
                    tempfile.gettempdir(),
                    f"netmon-freshclam-{user_tag}.log",
                )
                _safe_makedirs_no_symlink(user_db_dir)
                with tempfile.NamedTemporaryFile(
                    "w",
                    delete=False,
                    prefix="netmon-freshclam-",
                    suffix=".conf",
                ) as cfg:
                    cfg.write(f"DatabaseDirectory {user_db_dir}\n")
                    cfg.write("DatabaseMirror database.clamav.net\n")
                    cfg.write(f"UpdateLogFile {user_log_file}\n")
                    cfg.write("Foreground true\n")
                    cfg.write("CompressLocalDatabase no\n")
                    temp_cfg_path = cfg.name
            except Exception as cfg_exc:
                temp_cfg_path = ""
                app.log_debug_safe(
                    f"ClamAV-Update: Temp-Config konnte nicht erstellt werden: {cfg_exc}"
                )

            attempts = []
            if temp_cfg_path:
                attempts.append(
                    (
                        "freshclam --stdout --config-file <temp>",
                        [
                            "freshclam",
                            "--stdout",
                            "--config-file",
                            temp_cfg_path,
                        ],
                    )
                )
                if has_cmd("sudo"):
                    attempts.append(
                        (
                            "sudo -n freshclam --stdout --config-file <temp>",
                            [
                                "sudo",
                                "-n",
                                "freshclam",
                                "--stdout",
                                "--config-file",
                                temp_cfg_path,
                            ],
                        )
                    )

            attempts.append(("freshclam --stdout", ["freshclam", "--stdout"]))
            if has_cmd("sudo"):
                attempts.append(
                    (
                        "sudo -n freshclam --stdout",
                        ["sudo", "-n", "freshclam", "--stdout"],
                    )
                )

            rc = 1
            used_sudo = False
            all_outputs = []
            for label, cmd in attempts:
                rc, cmd_out = run_cmd(cmd, timeout=900)
                if cmd_out:
                    all_outputs.append(f"[{label}]\n{cmd_out}")
                if rc == 0:
                    used_sudo = label.startswith("sudo ")
                    break

            if rc == 0:
                if used_sudo:
                    app.clamav_database_dir = ""
                elif clamav_database_dir_has_signatures(user_db_dir):
                    app.clamav_database_dir = user_db_dir
                update_clamav_panel_safe(app, status="bereit", signatures="aktuell")
                app.log_safe("ClamAV-Update abgeschlossen.")
                if getattr(app, "clamav_database_dir", ""):
                    app.log_safe(
                        f"ClamAV nutzt Signaturen aus: {app.clamav_database_dir}"
                    )
                if used_sudo:
                    app.log_debug_safe("ClamAV-Update wurde mit sudo -n ausgeführt.")
            else:
                merged = "\n".join(all_outputs).strip()
                lines = [ln.strip() for ln in merged.splitlines() if ln.strip()]
                last_line = lines[-1] if lines else ""
                lower_merged = merged.lower()

                if clamav_is_nonfatal_update_issue(merged):
                    update_clamav_panel_safe(
                        app, status="bereit", signatures="unbekannt"
                    )
                    app.log_safe(
                        "ClamAV-Update: Hinweis – clamav-daemon/clamd ist nicht geladen."
                    )
                    app.log_safe("Update-Lauf wurde ohne aktiven Daemon fortgesetzt.")
                else:
                    if "a password is required" in lower_merged:
                        user_error = (
                            "freshclam benötigt Root-Rechte "
                            "(sudo ohne Passwort derzeit nicht möglich)."
                        )
                    elif any(
                        token in merged
                        for token in [
                            "Failed to open log file /var/log/clamav/freshclam",
                            "Can't open /var/log/clamav/freshclam",
                        ]
                    ):
                        user_error = (
                            "freshclam kann sein System-Logfile nicht öffnen "
                            "(/var/log/clamav/freshclam)."
                        )
                    elif last_line:
                        user_error = last_line
                    else:
                        user_error = f"Unbekannter Fehler (rc={rc})."

                    update_clamav_panel_safe(
                        app, status="Fehler", signatures="Update fehlgeschlagen"
                    )
                    app.log_safe(f"ClamAV-Update fehlgeschlagen: {user_error}")

            if all_outputs:
                app.log_debug_safe(
                    "ClamAV update raw: " + "\n\n".join(all_outputs)[:3000]
                )
        finally:
            if temp_cfg_path:
                try:
                    os.remove(temp_cfg_path)
                except Exception:
                    pass
            app.security_clamav_update_running = False

    threading.Thread(target=job, daemon=True).start()


def security_clamav_quickscan_async(app):
    if not has_cmd("clamscan"):
        update_clamav_panel(app, status="nicht installiert", result="clamscan fehlt")
        app.log("ClamAV nicht gefunden (clamscan fehlt).")
        return
    if app.security_clamav_running:
        app.log("ClamAV-Schnellscan läuft bereits.")
        return

    app.security_clamav_running = True
    app.security_clamav_last_systemcheck_text = ""
    update_clamav_panel(app, status="Scan läuft", result="-")

    def job():
        try:
            targets, used_home_fallback = app._clamav_quick_targets()
            if not targets:
                update_clamav_panel_safe(
                    app,
                    status=_tr(app, "status_ready_short", "bereit"),
                    result=_tr(
                        app,
                        "clamav_quickscan_result_no_paths",
                        "Keine Schnellscan-Pfade konfiguriert",
                    ),
                )
                write_clamav_output(
                    app,
                    [
                        _tr(
                            app,
                            "clamav_quickscan_output_not_started",
                            "ClamAV-Schnellscan nicht gestartet.",
                        ),
                        _tr(
                            app,
                            "clamav_quickscan_output_not_started_reason",
                            "Grund: keine gültigen Schnellscan-Pfade ausgewählt.",
                        ),
                        "",
                        _tr(
                            app,
                            "clamav_quickscan_output_not_started_hint",
                            "Bitte Schnellscan-Pfade festlegen und erneut starten.",
                        ),
                    ],
                    replace=True,
                )
                app.log_safe(
                    _tr(
                        app,
                        "clamav_quickscan_log_not_started_no_paths",
                        "ClamAV-Schnellscan nicht gestartet: keine gültigen Schnellscan-Pfade.",
                    )
                )
                return
            excluded = clamav_quick_excluded_roots()
            target_label = ", ".join(targets)
            if len(target_label) > 120:
                target_label = target_label[:117] + "..."
            update_clamav_panel_safe(app, last_target=target_label)
            call_in_ui_thread(app, app._clamav_progress_start)

            app.log_safe(
                _tr(
                    app,
                    "clamav_quickscan_log_started",
                    "ClamAV-Schnellscan gestartet...",
                )
            )
            if used_home_fallback:
                app.log_safe(
                    _tr(
                        app,
                        "clamav_quickscan_log_home_fallback",
                        "ClamAV: Keine Standardordner gefunden, nutze Home-Verzeichnis.",
                    )
                )
            if excluded:
                app.log_debug_safe(
                    _tr(
                        app,
                        "clamav_quickscan_log_excluded",
                        "ClamAV-Schnellscan Ausschlüsse: {value}",
                    ).format(value=", ".join(excluded))
                )

            exclude_args = clamav_exclude_dir_args(excluded)
            cmd = [
                "clamscan",
                *clamav_database_args(app),
                "-r",
                "--infected",
                *exclude_args,
                *targets,
            ]
            rc, out, cancelled = app._run_clamscan_with_cancel(cmd, timeout=900)
            timed_out = rc == 124
            scanned_live = 0

            if cancelled:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                app.security_clamav_last_systemcheck_text = "\n".join(
                    [
                        "=== ClamAV ===",
                        "Status: abgebrochen",
                        "Signaturen: -",
                        f"Letzter Scan: {timestamp}",
                        f"Ziel: {target_label or '-'}",
                        "Funde: -",
                        "Ergebnis: Scan abgebrochen",
                    ]
                )
                update_clamav_panel_safe(
                    app,
                    status="abgebrochen",
                    last_scan=timestamp,
                    result="Scan abgebrochen",
                )
                lines = [
                    _tr(
                        app,
                        "clamav_quickscan_output_cancelled",
                        "ClamAV-Schnellscan abgebrochen.",
                    ),
                    _tr(app, "clamav_output_targets", "Ziele: {value}").format(
                        value=target_label or "-"
                    ),
                    _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
                        value=scanned_live
                    ),
                    _tr(app, "clamav_output_return_code", "Rückgabecode: {value}").format(
                        value=rc
                    ),
                ]
                raw_lines = [
                    line.strip() for line in (out or "").splitlines() if line.strip()
                ]
                if raw_lines:
                    lines.extend(
                        [
                            "",
                            _tr(app, "clamav_output_raw_section", "ClamAV-Ausgabe:"),
                            *raw_lines[-8:],
                        ]
                    )
                write_clamav_output(app, lines, replace=True)
                app.log_safe(
                    _tr(
                        app,
                        "clamav_quickscan_output_cancelled",
                        "ClamAV-Schnellscan abgebrochen.",
                    )
                )
                if out:
                    app.log_debug_safe("ClamAV scan raw: " + out[:1000])
                return

            if timed_out:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    last_scan=timestamp,
                    last_target=target_label,
                    findings="-",
                    result=_tr(app, "status_timeout", "Timeout"),
                )
                write_clamav_output(
                    app,
                    [
                        _tr(
                            app,
                            "clamav_quickscan_output_timeout",
                            "ClamAV-Schnellscan Timeout.",
                        ),
                        _tr(app, "clamav_output_targets", "Ziele: {value}").format(
                            value=target_label
                        ),
                        _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
                            value=scanned_live
                        ),
                    ],
                    replace=True,
                )
                app.log_safe(
                    _tr(
                        app,
                        "clamav_quickscan_log_timeout",
                        "ClamAV-Schnellscan fehlgeschlagen: Timeout.",
                    )
                )
                return

            infected_count = clamav_parse_infected_count(out)
            scanned_files = clamav_parse_scanned_files(out)
            if not isinstance(scanned_files, int):
                scanned_files = scanned_live
            if isinstance(scanned_files, int) and scanned_files >= 0:
                app._clamav_progress_update_safe(scanned_files)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            findings_txt = str(infected_count)
            result_txt = (
                _tr(
                    app,
                    "clamav_quickscan_result_clean",
                    "Keine Bedrohungen gefunden",
                )
                if infected_count == 0
                else _tr(
                    app,
                    "clamav_quickscan_result_found",
                    "{count} verdächtige Dateien gefunden",
                ).format(count=infected_count)
            )

            nonfatal_issue = rc == 2 and clamav_allows_nonfatal_scan_completion(
                out, scanned_files
            )
            if rc in (0, 1) or nonfatal_issue:
                extracted_findings = clamav_extract_findings(
                    out, scan_type="quickscan", timestamp=timestamp
                )
                clamav_replace_open_findings(app, extracted_findings)
                app.security_clamav_last_systemcheck_text = "\n".join(
                    [
                        "=== ClamAV ===",
                        (
                            "Status: abgeschlossen"
                            if not nonfatal_issue
                            else "Status: abgeschlossen (Warnungen)"
                        ),
                        (
                            "Signaturen: aktuell"
                            if has_cmd("freshclam")
                            else "Signaturen: unbekannt"
                        ),
                        f"Letzter Scan: {timestamp}",
                        f"Ziel: {target_label or '-'}",
                        f"Funde: {findings_txt}",
                        "Ergebnis: "
                        + (
                            result_txt
                            if not nonfatal_issue
                            else _tr(
                                app,
                                "clamav_quickscan_result_with_warnings",
                                "{value} (mit Zugriffswarnungen)",
                            ).format(value=result_txt)
                        ),
                    ]
                )
                update_clamav_panel_safe(
                    app,
                    status=(
                        "abgeschlossen"
                        if not nonfatal_issue
                        else _tr(
                            app,
                            "clamav_quickscan_status_completed_warnings",
                            "abgeschlossen (Warnungen)",
                        )
                    ),
                    signatures="aktuell" if has_cmd("freshclam") else "unbekannt",
                    last_scan=timestamp,
                    findings=findings_txt,
                    result=(
                        result_txt
                        if not nonfatal_issue
                        else _tr(
                            app,
                            "clamav_quickscan_result_with_warnings",
                            "{value} (mit Zugriffswarnungen)",
                        ).format(value=result_txt)
                    ),
                )
                if len(targets) == 1:
                    app.log_safe(
                        _tr(
                            app,
                            "clamav_quickscan_log_completed_single",
                            "ClamAV-Schnellscan abgeschlossen. Ziel: {target} | Funde: {count}",
                        ).format(target=targets[0], count=infected_count)
                    )
                else:
                    app.log_safe(
                        _tr(
                            app,
                            "clamav_quickscan_log_completed_multi",
                            "ClamAV-Schnellscan abgeschlossen. Ziele: {count_targets} | Funde: {count_findings}",
                        ).format(
                            count_targets=len(targets),
                            count_findings=infected_count,
                        )
                    )
                if nonfatal_issue:
                    app.log_safe(
                        _tr(
                            app,
                            "clamav_quickscan_log_read_warnings",
                            "ClamAV-Schnellscan: Einige Dateien konnten nicht gelesen werden (Zugriffswarnungen).",
                        )
                    )
            else:
                error_line = clamav_extract_error_message(out)
                app.security_clamav_last_systemcheck_text = "\n".join(
                    [
                        "=== ClamAV ===",
                        "Status: Fehler",
                        "Signaturen: -",
                        f"Letzter Scan: {timestamp}",
                        f"Ziel: {target_label or '-'}",
                        "Funde: -",
                        "Ergebnis: "
                        + (
                            f"Scan fehlgeschlagen: {error_line}"
                            if error_line
                            else f"Scan fehlgeschlagen (rc={rc})"
                        ),
                    ]
                )
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    last_scan=timestamp,
                    findings="-",
                    result=_tr(
                        app,
                        "clamav_quickscan_result_failed",
                        "Scan fehlgeschlagen",
                    ),
                )
                write_clamav_output(
                    app,
                    clamav_scan_failure_lines(
                        app,
                        "ClamAV-Schnellscan fehlgeschlagen.",
                        target_label,
                        scanned_files if isinstance(scanned_files, int) else 0,
                        rc,
                        out,
                    ),
                    replace=True,
                )
                if error_line:
                    app.log_safe(f"ClamAV-Schnellscan fehlgeschlagen: {error_line}")
                else:
                    app.log_safe(
                        _tr(
                            app,
                            "clamav_quickscan_log_failed_no_error_line",
                            "ClamAV-Schnellscan fehlgeschlagen (rc={rc}, keine technische Fehlerzeile erkannt).",
                        ).format(rc=rc)
                    )

            if out:
                app.log_debug_safe("ClamAV scan raw: " + out[:1000])
        finally:
            app.security_clamav_running = False
            app._clamav_progress_finish_safe()

    threading.Thread(target=job, daemon=True).start()


def security_clamav_folder_scan_async(app):
    if not has_cmd("clamscan"):
        update_clamav_panel(app, status="nicht installiert", result="clamscan fehlt")
        app.log("ClamAV ist nicht installiert.")
        return
    if app.security_clamav_running:
        app.log("ClamAV-Scan läuft bereits.")
        return

    selected = filedialog.askdirectory(
        title=app.tr(
            "clamav_scan_folder_dialog_title",
            "Ordner für ClamAV-Scan auswählen",
        ),
        initialdir=os.path.expanduser("~"),
        mustexist=True,
    )
    if not selected:
        return

    target = os.path.realpath(os.path.normpath(selected))
    if not os.path.isabs(target) or not os.path.isdir(target):
        app.log("ClamAV-Ordnerscan abgebrochen: Ordner nicht gefunden.")
        return

    app.security_clamav_running = True
    update_clamav_panel(app, status="Scan läuft", result="-", last_target=target)

    def job():
        try:
            call_in_ui_thread(app, app._clamav_progress_start)
            app.log_safe(f"ClamAV-Ordnerscan gestartet: {target}")

            rc, out, cancelled, timed_out, scanned_live = (
                app._run_clamscan_with_progress(
                    [
                        "clamscan",
                        *clamav_database_args(app),
                        "-r",
                        "--infected",
                        target,
                    ],
                    timeout=900,
                    progress_cb=app._clamav_progress_update_safe,
                )
            )
            if cancelled:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_clamav_panel_safe(
                    app,
                    status="abgebrochen",
                    last_scan=timestamp,
                    last_target=target,
                    result=_tr(app, "status_cancelled", "Abgebrochen"),
                )
                lines = [
                    _tr(
                        app,
                        "clamav_folder_scan_output_cancelled",
                        "ClamAV-Ordnerscan abgebrochen.",
                    ),
                    _tr(app, "clamav_output_target", "Ziel: {value}").format(
                        value=target
                    ),
                    _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
                        value=scanned_live
                    ),
                    _tr(app, "clamav_output_return_code", "Rückgabecode: {value}").format(
                        value=rc
                    ),
                ]
                raw_lines = [
                    line.strip() for line in (out or "").splitlines() if line.strip()
                ]
                if raw_lines:
                    lines.extend(
                        [
                            "",
                            _tr(app, "clamav_output_raw_section", "ClamAV-Ausgabe:"),
                            *raw_lines[-8:],
                        ]
                    )
                write_clamav_output(app, lines, replace=True)
                app.log_safe(
                    _tr(
                        app,
                        "clamav_folder_scan_output_cancelled",
                        "ClamAV-Ordnerscan abgebrochen.",
                    )
                )
                if out:
                    app.log_debug_safe("ClamAV folder scan raw: " + out[:1000])
                return

            if timed_out:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    last_scan=timestamp,
                    last_target=target,
                    findings="-",
                    result=_tr(app, "status_timeout", "Timeout"),
                )
                write_clamav_output(
                    app,
                    [
                        _tr(
                            app,
                            "clamav_folder_scan_output_timeout",
                            "ClamAV-Ordnerscan Timeout.",
                        ),
                        _tr(app, "clamav_output_target", "Ziel: {value}").format(
                            value=target
                        ),
                        _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
                            value=scanned_live
                        ),
                    ],
                    replace=True,
                )
                app.log_safe(
                    _tr(
                        app,
                        "clamav_folder_scan_log_timeout",
                        "ClamAV-Ordnerscan fehlgeschlagen: Timeout.",
                    )
                )
                return

            infected_count = clamav_parse_infected_count(out)
            scanned_files = clamav_parse_scanned_files(out)
            if not isinstance(scanned_files, int):
                scanned_files = scanned_live
            if isinstance(scanned_files, int) and scanned_files >= 0:
                app._clamav_progress_update_safe(scanned_files)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_txt = (
                _tr(
                    app,
                    "clamav_quickscan_result_clean",
                    "Keine Bedrohungen gefunden",
                )
                if infected_count == 0
                else _tr(
                    app,
                    "clamav_quickscan_result_found",
                    "{count} verdächtige Dateien gefunden",
                ).format(count=infected_count)
            )

            nonfatal_issue = rc == 2 and clamav_allows_nonfatal_scan_completion(
                out, scanned_files
            )
            if rc in (0, 1) or nonfatal_issue:
                extracted_findings = clamav_extract_findings(
                    out, scan_type="folder_scan", timestamp=timestamp
                )
                clamav_replace_open_findings(app, extracted_findings)
                update_clamav_panel_safe(
                    app,
                    status=(
                        "abgeschlossen"
                        if not nonfatal_issue
                        else _tr(
                            app,
                            "clamav_quickscan_status_completed_warnings",
                            "abgeschlossen (Warnungen)",
                        )
                    ),
                    signatures="aktuell" if has_cmd("freshclam") else "unbekannt",
                    last_scan=timestamp,
                    last_target=target,
                    findings=str(infected_count),
                    result=(
                        result_txt
                        if not nonfatal_issue
                        else _tr(
                            app,
                            "clamav_quickscan_result_with_warnings",
                            "{value} (mit Zugriffswarnungen)",
                        ).format(value=result_txt)
                    ),
                )
                app.log_safe(
                    _tr(
                        app,
                        "clamav_folder_scan_log_completed",
                        "ClamAV-Ordnerscan abgeschlossen. Ziel: {target} | Funde: {count}",
                    ).format(target=target, count=infected_count)
                )
                if nonfatal_issue:
                    app.log_safe(
                        _tr(
                            app,
                            "clamav_folder_scan_log_read_warnings",
                            "ClamAV-Ordnerscan: Einige Dateien konnten nicht gelesen werden (Zugriffswarnungen).",
                        )
                    )
            else:
                error_line = clamav_extract_error_message(out)
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    last_scan=timestamp,
                    last_target=target,
                    findings="-",
                    result=_tr(
                        app,
                        "clamav_quickscan_result_failed",
                        "Scan fehlgeschlagen",
                    ),
                )
                write_clamav_output(
                    app,
                    clamav_scan_failure_lines(
                        app,
                        "ClamAV-Ordnerscan fehlgeschlagen.",
                        target,
                        scanned_files if isinstance(scanned_files, int) else 0,
                        rc,
                        out,
                    ),
                    replace=True,
                )
                if error_line:
                    app.log_safe(f"ClamAV-Ordnerscan fehlgeschlagen: {error_line}")
                else:
                    app.log_safe(
                        _tr(
                            app,
                            "clamav_folder_scan_log_failed_no_error_line",
                            "ClamAV-Ordnerscan fehlgeschlagen (rc={rc}, keine technische Fehlerzeile erkannt).",
                        ).format(rc=rc)
                    )

            if out:
                app.log_debug_safe("ClamAV folder scan raw: " + out[:1000])
        finally:
            app.security_clamav_running = False
            app._clamav_progress_finish_safe()

    threading.Thread(target=job, daemon=True).start()


def security_clamav_systemscan_async(app):
    if not has_cmd("clamscan"):
        update_clamav_panel(app, status="nicht installiert", result="clamscan fehlt")
        app.log("ClamAV ist nicht installiert.")
        return
    if app.security_clamav_running:
        app.log("ClamAV-Scan läuft bereits.")
        return

    targets = app._clamav_system_targets()
    excluded = app._clamav_system_excluded_roots()
    if not targets:
        app.log("ClamAV-Systemscan: keine geeigneten Ziele gefunden.")
        return

    target_label = ", ".join(targets)
    if len(target_label) > 140:
        target_label = target_label[:137] + "..."

    app.security_clamav_running = True
    update_clamav_panel(
        app,
        status="Scan läuft",
        result="Systemscan läuft",
        last_target=target_label,
    )
    write_clamav_output(
        app,
        [
            "ClamAV-Systemscan gestartet.",
            f"Ziele: {target_label}",
            "Ausgeschlossene Pfade: " + ", ".join(excluded),
            "",
            "Fortschritt wird im Statusbereich aktualisiert.",
        ],
        replace=True,
    )

    def job():
        try:
            estimated_total = None
            try:
                estimated_total = app._clamav_count_files(
                    targets, excluded_roots=excluded
                )
            except Exception as exc:
                app.log_debug_safe(
                    f"ClamAV-Systemscan Dateivorzählung fehlgeschlagen: {exc}"
                )

            call_in_ui_thread(
                app, lambda n=estimated_total: app._clamav_progress_start(n)
            )
            app.log_safe("ClamAV-Systemscan gestartet...")

            exclude_args = [
                f"--exclude-dir=^{re.escape(root)}($|/)" for root in excluded
            ]
            cmd = [
                "clamscan",
                *clamav_database_args(app),
                "-r",
                *exclude_args,
                *targets,
            ]
            rc, out, cancelled, timed_out, scanned_live = (
                app._run_clamscan_with_progress(
                    cmd,
                    timeout=5400,
                    progress_cb=app._clamav_progress_update_safe,
                )
            )

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            scanned_files = clamav_parse_scanned_files(out)
            if not isinstance(scanned_files, int):
                scanned_files = scanned_live
            app._clamav_progress_update_safe(scanned_files)

            if cancelled:
                update_clamav_panel_safe(
                    app,
                    status="abgebrochen",
                    last_scan=timestamp,
                    last_target=target_label,
                    result=_tr(app, "status_cancelled", "Abgebrochen"),
                )
                write_clamav_output(
                    app,
                    [
                        _tr(
                            app,
                            "clamav_system_scan_output_cancelled",
                            "ClamAV-Systemscan abgebrochen.",
                        ),
                        _tr(app, "clamav_output_targets", "Ziele: {value}").format(
                            value=target_label
                        ),
                        _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
                            value=scanned_files
                        ),
                    ],
                    replace=True,
                )
                app.log_safe(
                    _tr(
                        app,
                        "clamav_system_scan_output_cancelled",
                        "ClamAV-Systemscan abgebrochen.",
                    )
                )
                return

            if timed_out:
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    last_scan=timestamp,
                    last_target=target_label,
                    result=_tr(app, "status_timeout", "Timeout"),
                )
                write_clamav_output(
                    app,
                    [
                        _tr(
                            app,
                            "clamav_system_scan_output_timeout",
                            "ClamAV-Systemscan Timeout.",
                        ),
                        _tr(app, "clamav_output_targets", "Ziele: {value}").format(
                            value=target_label
                        ),
                        _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
                            value=scanned_files
                        ),
                    ],
                    replace=True,
                )
                app.log_safe(
                    _tr(
                        app,
                        "clamav_system_scan_log_timeout",
                        "ClamAV-Systemscan fehlgeschlagen: Timeout.",
                    )
                )
                return

            infected_count = clamav_parse_infected_count(out)
            result_txt = (
                _tr(
                    app,
                    "clamav_quickscan_result_clean",
                    "Keine Bedrohungen gefunden",
                )
                if infected_count == 0
                else _tr(
                    app,
                    "clamav_quickscan_result_found",
                    "{count} verdächtige Dateien gefunden",
                ).format(count=infected_count)
            )

            nonfatal_issue = rc == 2 and clamav_allows_nonfatal_scan_completion(
                out, scanned_files
            )
            if rc in (0, 1) or nonfatal_issue:
                extracted_findings = clamav_extract_findings(
                    out, scan_type="system_scan", timestamp=timestamp
                )
                clamav_replace_open_findings(app, extracted_findings)
                update_clamav_panel_safe(
                    app,
                    status=(
                        "abgeschlossen"
                        if not nonfatal_issue
                        else _tr(
                            app,
                            "clamav_quickscan_status_completed_warnings",
                            "abgeschlossen (Warnungen)",
                        )
                    ),
                    signatures="aktuell" if has_cmd("freshclam") else "unbekannt",
                    last_scan=timestamp,
                    last_target=target_label,
                    findings=str(infected_count),
                    result=(
                        result_txt
                        if not nonfatal_issue
                        else _tr(
                            app,
                            "clamav_quickscan_result_with_warnings",
                            "{value} (mit Zugriffswarnungen)",
                        ).format(value=result_txt)
                    ),
                )
                write_clamav_output(
                    app,
                    [
                        _tr(
                            app,
                            "clamav_system_scan_output_completed",
                            "ClamAV-Systemscan abgeschlossen.",
                        ),
                        _tr(app, "clamav_output_targets", "Ziele: {value}").format(
                            value=target_label
                        ),
                        _tr(app, "clamav_output_scanned_files", "Dateien gescannt: {value}").format(
                            value=scanned_files
                        ),
                        f"Funde: {infected_count}",
                        f"Ergebnis: {result_txt}",
                    ],
                    replace=True,
                )
                app.log_safe(
                    _tr(
                        app,
                        "clamav_system_scan_log_completed",
                        "ClamAV-Systemscan abgeschlossen. Ziele: {count_targets} | Funde: {count_findings}",
                    ).format(
                        count_targets=len(targets),
                        count_findings=infected_count,
                    )
                )
                if nonfatal_issue:
                    app.log_safe(
                        _tr(
                            app,
                            "clamav_system_scan_log_read_warnings",
                            "ClamAV-Systemscan: Einige Dateien konnten nicht gelesen werden (Zugriffswarnungen).",
                        )
                    )
            else:
                error_line = clamav_extract_error_message(out)
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    last_scan=timestamp,
                    last_target=target_label,
                    findings="-",
                    result=_tr(
                        app,
                        "clamav_system_scan_result_failed",
                        "Systemscan fehlgeschlagen",
                    ),
                )
                write_clamav_output(
                    app,
                    clamav_scan_failure_lines(
                        app,
                        "ClamAV-Systemscan fehlgeschlagen.",
                        target_label,
                        scanned_files,
                        rc,
                        out,
                    ),
                    replace=True,
                )
                if error_line:
                    app.log_safe(f"ClamAV-Systemscan fehlgeschlagen: {error_line}")
                else:
                    app.log_safe(
                        f"ClamAV-Systemscan fehlgeschlagen (rc={rc}, keine technische Fehlerzeile erkannt)."
                    )

            if out:
                app.log_debug_safe("ClamAV system scan raw: " + out[:1500])
        finally:
            app.security_clamav_running = False
            app._clamav_progress_finish_safe()

    threading.Thread(target=job, daemon=True).start()


def security_clamav_scan_async(app):
    security_clamav_quickscan_async(app)


def quarantine_clamav_findings_async(app):
    if not has_cmd("clamscan"):
        update_clamav_panel(app, status="nicht installiert", result="clamscan fehlt")
        app.log("ClamAV ist nicht installiert.")
        app._update_clamav_findings_buttons_state()
        return
    if app.security_clamav_running:
        app.log("ClamAV-Scan läuft bereits.")
        return

    open_findings = app._clamav_findings_open()
    if not open_findings:
        app.log("Keine offenen ClamAV-Funde vorhanden.")
        app._update_clamav_findings_buttons_state()
        return

    app._log_clamav_quarantine_preview(open_findings, label="Vorschau")
    if not messagebox.askyesno(
        app.tr("clamav_quarantine_title", "ClamAV Quarantäne"),
        app.tr(
            "clamav_quarantine_confirm",
            "{count} offene Datei(en) in Quarantäne verschieben?",
        ).format(count=len(open_findings)),
        parent=app,
    ):
        app.log("ClamAV-Quarantäne abgebrochen.")
        return

    app.security_clamav_running = True
    update_clamav_panel(app, status="Quarantäne läuft", result="-")

    def job():
        moved = 0
        missing = 0
        failed = 0
        try:
            app.log_safe("ClamAV-Quarantäne gestartet...")
            try:
                _safe_makedirs_no_symlink(app.clamav_quarantine_dir)
            except Exception as exc:
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    result="Quarantäne fehlgeschlagen",
                )
                app.log_safe(f"ClamAV-Quarantäne fehlgeschlagen: {exc}")
                return

            for item in open_findings:
                src_raw = os.path.normpath((item.get("path") or "").strip())
                if not src_raw:
                    continue
                src, src_error = app._clamav_validate_source_for_quarantine(src_raw)
                if src is None:
                    item["status"] = "missing"
                    item["quarantine_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if src_error == "nicht vorhanden":
                        missing += 1
                        app.log_safe(f"Datei nicht mehr vorhanden: {src_raw}")
                    else:
                        failed += 1
                        app.log_safe(f"Datei übersprungen (unsicherer Pfad): {src_raw}")
                        app.log_debug_safe(
                            "ClamAV-Quarantäne Pfadprüfung fehlgeschlagen: "
                            f"{src_raw} ({src_error})"
                        )
                    continue

                dest = app._clamav_next_quarantine_path(src)
                if not app._clamav_path_is_within(dest, app.clamav_quarantine_dir):
                    failed += 1
                    app.log_safe(
                        f"Datei übersprungen (unsicheres Quarantäne-Ziel): {src}"
                    )
                    app.log_debug_safe(
                        "ClamAV-Quarantäne Ziel außerhalb Quarantäne-Ordner: " f"{dest}"
                    )
                    continue
                try:
                    shutil.move(src, dest)
                    moved += 1
                    item["status"] = "quarantine"
                    item["quarantine_path"] = dest
                    item["quarantine_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except Exception as exc:
                    failed += 1
                    app.log_safe(
                        f"Datei konnte nicht in Quarantäne verschoben werden: {src}"
                    )
                    app.log_debug_safe(
                        f"ClamAV-Quarantäne Move-Fehler ({src} -> {dest}): {exc}"
                    )

            app._save_clamav_findings()
            app._update_clamav_findings_buttons_state_safe()

            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "abgeschlossen" if failed == 0 else "Fehler"
            if moved > 0:
                result_msg = f"{moved} Datei(en) in Quarantäne verschoben"
            elif missing > 0 and failed == 0:
                result_msg = "Keine Datei verschoben (nicht mehr vorhanden)"
            else:
                result_msg = "Quarantäne teilweise fehlgeschlagen"

            update_clamav_panel_safe(
                app,
                status=status,
                signatures="aktuell" if has_cmd("freshclam") else "unbekannt",
                last_scan=now_ts,
                findings=str(len(app._clamav_findings_open())),
                result=result_msg,
            )

            app.log_safe(f"{moved} Datei(en) in Quarantäne verschoben.")
            app.log_safe(f"Quarantäne-Ordner: {app.clamav_quarantine_dir}")
            if missing:
                app.log_safe(f"{missing} Datei(en) waren nicht mehr vorhanden.")
            if failed:
                app.log_safe(f"{failed} Datei(en) konnten nicht verschoben werden.")
        finally:
            app.security_clamav_running = False

    threading.Thread(target=job, daemon=True).start()


def quarantine_selected_clamav_findings_async(app):
    if not has_cmd("clamscan"):
        update_clamav_panel(app, status="nicht installiert", result="clamscan fehlt")
        app.log("ClamAV ist nicht installiert.")
        app._update_clamav_findings_buttons_state()
        return
    if app.security_clamav_running:
        app.log("ClamAV-Scan läuft bereits.")
        return

    open_findings = app._clamav_findings_open()
    if not open_findings:
        app.log("Keine offenen ClamAV-Funde vorhanden.")
        app._update_clamav_findings_buttons_state()
        return

    selected = app._clamav_select_items_dialog(
        open_findings,
        title=app.tr(
            "clamav_quarantine_select_title",
            "ClamAV: Funde zur Quarantäne auswählen",
        ),
        mode="found",
    )
    if selected is None:
        return
    if not selected:
        app.log("Keine Funde ausgewählt.")
        return

    app._log_clamav_quarantine_preview(selected, label="Vorschau (Auswahl)")
    if not messagebox.askyesno(
        app.tr(
            "clamav_quarantine_selected_title",
            "ClamAV Quarantäne (Auswahl)",
        ),
        app.tr(
            "clamav_quarantine_selected_confirm",
            "{count} ausgewählte Datei(en) in Quarantäne verschieben?",
        ).format(count=len(selected)),
        parent=app,
    ):
        app.log("ClamAV-Quarantäne (Auswahl) abgebrochen.")
        return

    app.security_clamav_running = True
    update_clamav_panel(app, status="Quarantäne läuft", result="-")

    def job():
        moved = 0
        missing = 0
        failed = 0
        try:
            app.log_safe("ClamAV-Quarantäne (Auswahl) gestartet...")
            try:
                _safe_makedirs_no_symlink(app.clamav_quarantine_dir)
            except Exception as exc:
                update_clamav_panel_safe(
                    app,
                    status="Fehler",
                    result="Quarantäne fehlgeschlagen",
                )
                app.log_safe(f"ClamAV-Quarantäne fehlgeschlagen: {exc}")
                return

            for item in selected:
                src_raw = os.path.normpath((item.get("path") or "").strip())
                if not src_raw:
                    continue
                src, src_error = app._clamav_validate_source_for_quarantine(src_raw)
                if src is None:
                    item["status"] = "missing"
                    item["quarantine_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if src_error == "nicht vorhanden":
                        missing += 1
                        app.log_safe(f"Datei nicht mehr vorhanden: {src_raw}")
                    else:
                        failed += 1
                        app.log_safe(f"Datei übersprungen (unsicherer Pfad): {src_raw}")
                        app.log_debug_safe(
                            "ClamAV-Quarantäne-Auswahl Pfadprüfung fehlgeschlagen: "
                            f"{src_raw} ({src_error})"
                        )
                    continue

                dest = app._clamav_next_quarantine_path(src)
                if not app._clamav_path_is_within(dest, app.clamav_quarantine_dir):
                    failed += 1
                    app.log_safe(
                        f"Datei übersprungen (unsicheres Quarantäne-Ziel): {src}"
                    )
                    app.log_debug_safe(
                        "ClamAV-Quarantäne-Auswahl Ziel außerhalb "
                        f"Quarantäne-Ordner: {dest}"
                    )
                    continue
                try:
                    shutil.move(src, dest)
                    moved += 1
                    item["status"] = "quarantine"
                    item["quarantine_path"] = dest
                    item["quarantine_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                except Exception as exc:
                    failed += 1
                    app.log_safe(
                        f"Datei konnte nicht in Quarantäne verschoben werden: {src}"
                    )
                    app.log_debug_safe(
                        f"ClamAV-Quarantäne-Auswahl Move-Fehler ({src} -> {dest}): {exc}"
                    )

            app._save_clamav_findings()
            app._update_clamav_findings_buttons_state_safe()

            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "abgeschlossen" if failed == 0 else "Fehler"
            if moved > 0:
                result_msg = f"{moved} ausgewählte Datei(en) in Quarantäne verschoben"
            elif missing > 0 and failed == 0:
                result_msg = "Keine ausgewählte Datei verschoben (nicht mehr vorhanden)"
            else:
                result_msg = "Auswahl-Quarantäne teilweise fehlgeschlagen"

            update_clamav_panel_safe(
                app,
                status=status,
                signatures="aktuell" if has_cmd("freshclam") else "unbekannt",
                last_scan=now_ts,
                findings=str(len(app._clamav_findings_open())),
                result=result_msg,
            )

            app.log_safe(f"{moved} ausgewählte Datei(en) in Quarantäne verschoben.")
            app.log_safe(f"Quarantäne-Ordner: {app.clamav_quarantine_dir}")
            if missing:
                app.log_safe(
                    f"{missing} ausgewählte Datei(en) waren nicht mehr vorhanden."
                )
            if failed:
                app.log_safe(
                    f"{failed} ausgewählte Datei(en) konnten nicht verschoben werden."
                )
        finally:
            app.security_clamav_running = False

    threading.Thread(target=job, daemon=True).start()


def restore_clamav_quarantine_async(app):
    if not has_cmd("clamscan"):
        update_clamav_panel(
            app,
            status="nicht installiert",
            result="clamscan fehlt",
        )
        app.log("ClamAV ist nicht installiert.")
        app._update_clamav_findings_buttons_state()
        return
    if app.security_clamav_running:
        app.log("ClamAV-Scan läuft bereits.")
        return

    quarantined = app._clamav_findings_quarantined()
    if not quarantined:
        app.log("Keine Dateien in der ClamAV-Quarantäne vorhanden.")
        app._update_clamav_findings_buttons_state()
        return

    app._log_clamav_restore_preview(quarantined, label="Vorschau")
    if not messagebox.askyesno(
        app.tr("clamav_restore_title", "ClamAV Wiederherstellung"),
        app.tr(
            "clamav_restore_confirm",
            "{count} Quarantäne-Datei(en) wiederherstellen?",
        ).format(count=len(quarantined)),
        parent=app,
    ):
        app.log("ClamAV-Wiederherstellung abgebrochen.")
        return

    app.security_clamav_running = True
    update_clamav_panel(app, status="Wiederherstellung läuft", result="-")

    def job():
        restored = 0
        missing = 0
        failed = 0
        try:
            app.log_safe("ClamAV-Wiederherstellung gestartet...")
            for item in quarantined:
                qpath_raw = os.path.normpath(
                    (item.get("quarantine_path") or "").strip()
                )
                original_path = os.path.normpath((item.get("path") or "").strip())
                if not qpath_raw or not original_path:
                    failed += 1
                    continue
                qpath, qpath_error = app._clamav_validate_quarantine_path(qpath_raw)
                if qpath is None:
                    item["status"] = "quarantine_missing"
                    item["restore_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if qpath_error == "außerhalb des Quarantäne-Ordners":
                        failed += 1
                        app.log_safe(
                            f"Quarantäne-Datei übersprungen (unsicherer Pfad): {qpath_raw}"
                        )
                        app.log_debug_safe(
                            "ClamAV-Restore Quarantäne-Pfadprüfung fehlgeschlagen: "
                            f"{qpath_raw} ({qpath_error})"
                        )
                    else:
                        missing += 1
                        app.log_safe(
                            f"Quarantäne-Datei nicht mehr vorhanden: {qpath_raw}"
                        )
                    continue
                if not os.path.exists(qpath):
                    item["status"] = "quarantine_missing"
                    item["restore_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    missing += 1
                    app.log_safe(f"Quarantäne-Datei nicht mehr vorhanden: {qpath}")
                    continue

                safe_original = app._clamav_safe_restore_source(original_path)
                restore_target = app._clamav_next_restore_path(safe_original)
                home_root = os.path.realpath(os.path.expanduser("~"))
                if not app._clamav_path_is_within(restore_target, home_root):
                    failed += 1
                    app.log_safe(
                        f"Datei konnte nicht sicher wiederhergestellt werden: {original_path}"
                    )
                    app.log_debug_safe(
                        f"ClamAV-Restore Ziel außerhalb Home-Verzeichnis: {restore_target}"
                    )
                    continue
                restore_dir = os.path.dirname(restore_target)
                try:
                    if restore_dir and not os.path.isdir(restore_dir):
                        os.makedirs(restore_dir, exist_ok=True)
                    shutil.move(qpath, restore_target)
                    item["status"] = "restored"
                    item["restore_path"] = restore_target
                    item["restore_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    restored += 1
                except Exception as exc:
                    failed += 1
                    app.log_safe(
                        f"Datei konnte nicht wiederhergestellt werden: {original_path}"
                    )
                    app.log_debug_safe(
                        f"ClamAV-Restore-Fehler ({qpath} -> {restore_target}): {exc}"
                    )

            app._save_clamav_findings()
            app._update_clamav_findings_buttons_state_safe()

            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "abgeschlossen" if failed == 0 else "Fehler"
            if restored > 0:
                result_msg = f"{restored} Datei(en) aus Quarantäne wiederhergestellt"
            elif missing > 0 and failed == 0:
                result_msg = "Keine Datei wiederhergestellt (Quarantäne-Dateien fehlen)"
            else:
                result_msg = "Wiederherstellung teilweise fehlgeschlagen"

            update_clamav_panel_safe(
                app,
                status=status,
                signatures="aktuell" if has_cmd("freshclam") else "unbekannt",
                last_scan=now_ts,
                findings=str(len(app._clamav_findings_open())),
                result=result_msg,
            )
            app.log_safe(
                f"ClamAV-Wiederherstellung abgeschlossen. Wiederhergestellt: {restored}"
            )
            if missing:
                app.log_safe(f"{missing} Quarantäne-Datei(en) fehlten.")
            if failed:
                app.log_safe(
                    f"{failed} Datei(en) konnten nicht wiederhergestellt werden."
                )
        finally:
            app.security_clamav_running = False

    threading.Thread(target=job, daemon=True).start()


def restore_selected_clamav_quarantine_async(app):
    if not has_cmd("clamscan"):
        update_clamav_panel(
            app,
            status="nicht installiert",
            result="clamscan fehlt",
        )
        app.log("ClamAV ist nicht installiert.")
        app._update_clamav_findings_buttons_state()
        return
    if app.security_clamav_running:
        app.log("ClamAV-Scan läuft bereits.")
        return

    quarantined = app._clamav_findings_quarantined()
    if not quarantined:
        app.log("Keine Dateien in der ClamAV-Quarantäne vorhanden.")
        app._update_clamav_findings_buttons_state()
        return

    selected = app._clamav_select_items_dialog(
        quarantined,
        title=app.tr(
            "clamav_restore_select_title",
            "ClamAV: Quarantäne-Dateien zur Wiederherstellung auswählen",
        ),
        mode="quarantine",
    )
    if selected is None:
        return
    if not selected:
        app.log("Keine Quarantäne-Dateien ausgewählt.")
        return

    app._log_clamav_restore_preview(selected, label="Vorschau (Auswahl)")
    if not messagebox.askyesno(
        app.tr(
            "clamav_restore_selected_title",
            "ClamAV Wiederherstellung (Auswahl)",
        ),
        app.tr(
            "clamav_restore_selected_confirm",
            "{count} ausgewählte Quarantäne-Datei(en) wiederherstellen?",
        ).format(count=len(selected)),
        parent=app,
    ):
        app.log("ClamAV-Wiederherstellung (Auswahl) abgebrochen.")
        return

    app.security_clamav_running = True
    update_clamav_panel(app, status="Wiederherstellung läuft", result="-")

    def job():
        restored = 0
        missing = 0
        failed = 0
        try:
            app.log_safe("ClamAV-Wiederherstellung (Auswahl) gestartet...")
            for item in selected:
                qpath_raw = os.path.normpath(
                    (item.get("quarantine_path") or "").strip()
                )
                original_path = os.path.normpath((item.get("path") or "").strip())
                if not qpath_raw or not original_path:
                    failed += 1
                    continue
                qpath, qpath_error = app._clamav_validate_quarantine_path(qpath_raw)
                if qpath is None:
                    item["status"] = "quarantine_missing"
                    item["restore_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if qpath_error == "außerhalb des Quarantäne-Ordners":
                        failed += 1
                        app.log_safe(
                            f"Quarantäne-Datei übersprungen (unsicherer Pfad): {qpath_raw}"
                        )
                        app.log_debug_safe(
                            "ClamAV-Restore-Auswahl Quarantäne-Pfadprüfung fehlgeschlagen: "
                            f"{qpath_raw} ({qpath_error})"
                        )
                    else:
                        missing += 1
                        app.log_safe(
                            f"Quarantäne-Datei nicht mehr vorhanden: {qpath_raw}"
                        )
                    continue
                if not os.path.exists(qpath):
                    item["status"] = "quarantine_missing"
                    item["restore_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    missing += 1
                    app.log_safe(f"Quarantäne-Datei nicht mehr vorhanden: {qpath}")
                    continue

                safe_original = app._clamav_safe_restore_source(original_path)
                restore_target = app._clamav_next_restore_path(safe_original)
                home_root = os.path.realpath(os.path.expanduser("~"))
                if not app._clamav_path_is_within(restore_target, home_root):
                    failed += 1
                    app.log_safe(
                        f"Datei konnte nicht sicher wiederhergestellt werden: {original_path}"
                    )
                    app.log_debug_safe(
                        "ClamAV-Restore-Auswahl Ziel außerhalb Home-Verzeichnis: "
                        f"{restore_target}"
                    )
                    continue
                restore_dir = os.path.dirname(restore_target)
                try:
                    if restore_dir and not os.path.isdir(restore_dir):
                        os.makedirs(restore_dir, exist_ok=True)
                    shutil.move(qpath, restore_target)
                    item["status"] = "restored"
                    item["restore_path"] = restore_target
                    item["restore_timestamp"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    restored += 1
                except Exception as exc:
                    failed += 1
                    app.log_safe(
                        f"Datei konnte nicht wiederhergestellt werden: {original_path}"
                    )
                    app.log_debug_safe(
                        f"ClamAV-Restore-Auswahl Fehler ({qpath} -> {restore_target}): {exc}"
                    )

            app._save_clamav_findings()
            app._update_clamav_findings_buttons_state_safe()

            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "abgeschlossen" if failed == 0 else "Fehler"
            if restored > 0:
                result_msg = (
                    f"{restored} ausgewählte Datei(en) aus Quarantäne wiederhergestellt"
                )
            elif missing > 0 and failed == 0:
                result_msg = "Keine ausgewählte Datei wiederhergestellt (fehlend)"
            else:
                result_msg = "Auswahl-Wiederherstellung teilweise fehlgeschlagen"

            update_clamav_panel_safe(
                app,
                status=status,
                signatures="aktuell" if has_cmd("freshclam") else "unbekannt",
                last_scan=now_ts,
                findings=str(len(app._clamav_findings_open())),
                result=result_msg,
            )
            app.log_safe(
                "ClamAV-Wiederherstellung (Auswahl) abgeschlossen. "
                f"Wiederhergestellt: {restored}"
            )
            if missing:
                app.log_safe(f"{missing} ausgewählte Quarantäne-Datei(en) fehlten.")
            if failed:
                app.log_safe(
                    f"{failed} ausgewählte Datei(en) konnten nicht wiederhergestellt werden."
                )
        finally:
            app.security_clamav_running = False

    threading.Thread(target=job, daemon=True).start()
