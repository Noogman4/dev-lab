"""NetMon-specific backup/export and reviewed restore; desktop backups stay separate."""

from collections import Counter
import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from netmon.core import user_backup
from netmon.core.state import netmon_documents_path
from netmon.core.utils import call_in_ui_thread, human_size, protect_user_json_writes


def _tr(app, key, text):
    return app.tr(key, text)


def _with_duration(app, text):
    hint = _tr(
        app,
        "backup_duration_hint",
        "Dieser Vorgang kann je nach Datenmenge mehrere Minuten dauern. Bitte das Fenster bis zum Abschluss geöffnet lassen.",
    )
    return text + "\n" + hint


def _busy(app, active):
    app._netmon_backup_busy = active
    for name in ("btn_backup_netmon_export", "btn_backup_netmon_restore"):
        widget = app.__dict__.get(name)
        if widget is not None:
            widget.configure(state="disabled" if active else "normal")


def _progress(app):
    labels = {
        "export": _tr(app, "backup_progress_export", "Sichern"),
        "verify": _tr(app, "backup_progress_verify", "Prüfen"),
        "stage": _tr(app, "backup_progress_stage", "Zwischenablage prüfen"),
        "restore": _tr(app, "backup_progress_restore", "Übernehmen"),
    }

    def update(phase, done, total):
        text = _with_duration(app, f"{labels[phase]}: {done} / {total}")
        call_in_ui_thread(app, lambda: app.backup_status_var.set(text))

    return update


def _run(app, operation, finished, *, failed=None):
    if app.__dict__.get("_netmon_backup_busy", False):
        return False
    _busy(app, True)

    def complete(result, error):
        _busy(app, False)
        if error is not None:
            if failed is not None:
                failed(error)
            app.backup_status_var.set(
                _tr(
                    app,
                    "backup_own_failed",
                    "NetMon-Sicherung/Wiederherstellung fehlgeschlagen.",
                )
            )
            app._append_backup_log(str(error))
            messagebox.showerror(
                _tr(app, "backup_group_netmon", "NetMon-Sicherung"),
                str(error),
                parent=app,
            )
        else:
            finished(result)

    def work():
        try:
            result = operation()
        except Exception as exc:
            result, error = None, exc
        else:
            error = None
        try:
            call_in_ui_thread(app, lambda: complete(result, error))
        except (RuntimeError, tk.TclError):
            # Closing the app cannot authorize a different action or a system change.
            pass

    threading.Thread(target=work, daemon=True).start()
    return True


def export_documents(app):
    if app.__dict__.get("_netmon_backup_busy", False):
        return False
    selected = app._netmon_backup_selected_entries()
    if not selected:
        messagebox.showinfo(
            _tr(app, "backup_group_netmon", "NetMon-Sicherung"),
            _tr(
                app,
                "backup_netmon_export_no_selection",
                "Es sind keine NetMon-Ordner für den Export ausgewählt.",
            ),
            parent=app,
        )
        return False
    root = Path(netmon_documents_path())
    if selected[0].get("key") == "__all__":
        names = None
    else:
        names = [item["key"] for item in selected]
    destination = filedialog.askdirectory(
        title=_tr(
            app,
            "backup_netmon_export_target_title",
            "Externes Ziel für NetMon-Sicherung wählen",
        ),
        initialdir=os.path.expanduser("~"),
        parent=app,
    )
    if not destination:
        return False
    app.backup_status_var.set(
        _with_duration(
            app,
            _tr(
                app,
                "backup_export_hashing",
                "Sicherung wird erstellt und mit Prüfsummen versehen …",
            ),
        )
    )

    def finished(path):
        text = _tr(
            app,
            "backup_export_verified",
            "Versionierte NetMon-Sicherung erstellt: {path}",
        ).format(path=path)
        app.backup_status_var.set(text)
        app._append_backup_log(text)
        messagebox.showinfo(
            _tr(app, "backup_group_netmon", "NetMon-Sicherung"), text, parent=app
        )

    return _run(
        app,
        lambda: user_backup.export_backup(
            root, destination, selected=names, progress=_progress(app)
        ),
        finished,
    )


def restore_documents(app):
    if app.__dict__.get("_netmon_backup_busy", False):
        return False
    if app.__dict__.get("_initializing_preferences", False):
        return False
    source = filedialog.askdirectory(
        title=_tr(app, "backup_restore_choose", "NetMon-Sicherungsordner auswählen"),
        initialdir=os.path.expanduser("~"),
        parent=app,
    )
    if not source:
        return False
    app.backup_status_var.set(
        _with_duration(
            app,
            _tr(
                app,
                "backup_restore_checking",
                "Dateiinventar, Prüfsummen und Ziel werden geprüft …",
            ),
        )
    )
    target = netmon_documents_path()
    return _run(
        app,
        lambda: user_backup.preview_restore(source, target, progress=_progress(app)),
        lambda plan: show_preview(app, plan),
    )


def preview_text(app, plan):
    counts = Counter(entry.action for entry in plan.entries)
    labels = {
        "new": _tr(app, "backup_action_new", "Neu"),
        "identical": _tr(app, "backup_action_same", "Identisch"),
        "conflict": _tr(app, "backup_action_conflict", "Abweichendes Ziel"),
        "archive": _tr(app, "backup_action_archive", "Gesondertes Archiv"),
    }
    lines = [
        _tr(
            app,
            "backup_preview_origin",
            "Sicherung aus NetMon {version}; Datenformat {format}; {kind}",
        ).format(
            version=plan.app_version,
            format=user_backup.DATA_VERSION,
            kind=(
                _tr(app, "backup_kind_full", "Vollsicherung")
                if plan.kind == "full"
                else _tr(app, "backup_kind_partial", "Teilsicherung")
            ),
        ),
        _tr(app, "backup_preview_target", "Ziel: {path}").format(path=plan.target),
        _tr(
            app, "backup_preview_source", "Ursprünglicher NetMon-Ordner: {path}"
        ).format(path=plan.source_root),
        _tr(
            app,
            "backup_preview_count",
            "Dateien: {count}; Umfang: {size}; Pfadanpassungen: {adapted}",
        ).format(
            count=len(plan.entries),
            size=human_size(sum(e.size for e in plan.entries)),
            adapted=sum(e.adapted for e in plan.entries),
        ),
        "; ".join(f"{labels[key]}: {counts[key]}" for key in labels),
        "",
        _tr(
            app,
            "backup_preview_notes",
            "Hashprüfung erfolgreich. Sie prüft die Übereinstimmung mit dem Inventar, keine digitale Herkunftssignatur.\nSicherheitsreferenzen und historische Logs werden getrennt archiviert. Sie werden nicht als aktuelle Systemreferenz aktiviert.\nWireGuard-Systemverbindungen bei Bedarf anschließend regulär importieren.\nSeparates Radio und weitere NetMon-Instanzen vor der Übernahme schließen.\nDie übernommenen Einstellungen gelten nach einem manuellen Neustart; dabei gelten auch ihre gespeicherten Startoptionen.",
        ),
        "",
    ]
    for entry in plan.entries:
        adaptation = (
            _tr(app, "backup_preview_adapted", " – Pfad angepasst")
            if entry.adapted
            else ""
        )
        lines.append(f"{labels[entry.action]}: {entry.path}{adaptation}")
    if plan.excluded:
        lines.extend(
            [
                "",
                _tr(
                    app,
                    "backup_preview_excluded",
                    "Nicht gesichert (technische/erzeugte Dateien):",
                ),
            ]
        )
        lines.extend(plan.excluded)
    return "\n".join(lines)


def show_preview(app, plan):
    window = tk.Toplevel(app)
    window.title(_tr(app, "backup_restore_preview", "NetMon-Wiederherstellung prüfen"))
    window.geometry("1050x720")
    window.minsize(720, 480)
    window.transient(app)
    frame = ttk.Frame(window, padding=12)
    frame.pack(fill="both", expand=True)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    text = tk.Text(frame, wrap="word", width=95, height=24)
    scroll = ttk.Scrollbar(frame, command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    text.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    text.insert("1.0", preview_text(app, plan))
    text.configure(state="disabled")
    replace = tk.BooleanVar(window, value=False)
    ttk.Checkbutton(
        frame,
        text=_tr(
            app,
            "backup_restore_replace",
            "Abweichende Zieldateien ersetzen (Originale vorher sichern)",
        ),
        variable=replace,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 4))
    hint = ttk.Label(
        frame,
        text=_tr(
            app,
            "backup_restore_keep",
            "Ohne Ersetzen bleiben die Zieldateien erhalten; eingehende Konfliktdateien werden getrennt aufbewahrt.",
        ),
        wraplength=960,
    )
    hint.grid(row=2, column=0, columnspan=2, sticky="w")
    frame.bind(
        "<Configure>",
        lambda event: hint.configure(wraplength=max(400, event.width - 30)),
    )
    buttons = ttk.Frame(frame)
    buttons.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))

    def apply():
        replace_existing = bool(replace.get())
        protect_user_json_writes(plan.target)
        # Keep the preview modal while applying; stale controls cannot edit data.
        for child in buttons.winfo_children():
            child.configure(state="disabled")
        for child in frame.winfo_children():
            if child.winfo_class() == "TCheckbutton":
                child.configure(state="disabled")
        window.protocol("WM_DELETE_WINDOW", lambda: None)
        app.backup_status_var.set(
            _with_duration(
                app,
                _tr(
                    app,
                    "backup_restore_running",
                    "Sicherung wird erneut geprüft und übernommen …",
                ),
            )
        )

        def finished(result):
            path, report = result
            counts = Counter(item["action"] for item in report["files"])
            text = _tr(
                app,
                "backup_restore_done",
                "Übernahme abgeschlossen. Neu: {new}; ersetzt: {replaced}; Konflikte erhalten: {kept}; archiviert: {archived}.\nBericht: {path}\nNetMon bitte manuell neu starten, um die übernommenen Einstellungen zu laden.",
            ).format(
                new=counts["new"],
                replaced=counts["replaced"],
                kept=counts["kept"],
                archived=counts["archive"],
                path=path,
            )
            app.backup_status_var.set(
                _tr(
                    app,
                    "backup_restore_restart",
                    "Übernahme abgeschlossen – manueller Neustart erforderlich.",
                )
            )
            app._append_backup_log(text)
            window.grab_release()
            window.destroy()
            show_restart_notice(app, text)

        def failed(error):
            window.grab_release()
            window.destroy()
            if isinstance(error, user_backup.PartialRestoreError):
                show_restart_notice(app, str(error))
            else:
                protect_user_json_writes(plan.target, enabled=False)

        _run(
            app,
            lambda: user_backup.restore_backup(
                plan, replace_conflicts=replace_existing, progress=_progress(app)
            ),
            finished,
            failed=failed,
        )

    ttk.Button(
        buttons,
        text=_tr(app, "backup_restore_cancel", "Abbrechen"),
        command=window.destroy,
    ).pack(side="left", padx=(0, 8))
    ttk.Button(
        buttons,
        text=_tr(app, "backup_restore_apply", "Geprüfte Dateien übernehmen"),
        command=apply,
    ).pack(side="left")
    window.grab_set()
    return window


def show_restart_notice(app, text):
    """Keep stale controls inaccessible until the user explicitly closes NetMon."""
    window = tk.Toplevel(app)
    window.title(
        _tr(
            app,
            "backup_restore_restart",
            "Übernahme abgeschlossen – manueller Neustart erforderlich.",
        )
    )
    window.transient(app)
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=text, wraplength=650, justify="left").pack(
        fill="both", expand=True
    )
    ttk.Label(
        frame,
        text=_tr(
            app,
            "backup_restore_protected",
            "Weitere Speicherungen sind bis zum Neustart gesperrt, damit die alte Sitzung die übernommenen Einstellungen nicht überschreibt.",
        ),
        wraplength=650,
        justify="left",
    ).pack(fill="x", pady=(12, 12))
    ttk.Button(
        frame,
        text=_tr(app, "backup_restore_exit", "NetMon beenden"),
        command=app.on_close,
    ).pack(anchor="e")
    window.protocol("WM_DELETE_WINDOW", app.on_close)
    window.grab_set()
    return window
