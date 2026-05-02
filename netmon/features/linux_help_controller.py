"""Linux Help controller helpers for NetMon."""

from __future__ import annotations

import csv
import json
import os
import re

try:
    from tkinter import filedialog
except Exception:
    filedialog = None

try:
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    from core.utils import safe_write_json


NETMON_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def set_linux_help_dirty(app, dirty=True):
    app.linux_help_dirty = bool(dirty)


def linux_help_csv_candidates():
    return [
        os.path.join(NETMON_REPO_ROOT, "netmon", "linux-befehle.csv"),
        os.path.join(NETMON_REPO_ROOT, "linux-befehle.csv"),
        os.path.join(os.getcwd(), "linux-befehle.csv"),
    ]


def linux_help_csv_path():
    for path in linux_help_csv_candidates():
        if path and os.path.isfile(path):
            return path
    return linux_help_csv_candidates()[0]


def linux_help_slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", (text or "").strip().lower()).strip("_")
    return slug or "linux_help"


def linux_help_make_id(raw, existing_ids=None):
    entry = raw or {}
    base = linux_help_slugify(
        entry.get("id")
        or entry.get("name")
        or entry.get("cmd")
        or entry.get("category")
        or "linux_help"
    )
    used = set(existing_ids or [])
    candidate = base
    idx = 2
    while candidate in used:
        candidate = f"{base}_{idx}"
        idx += 1
    return candidate


def linux_help_get_risk_level(cmd: str) -> str:
    text = (cmd or "").strip().lower()
    if not text:
        return "unknown"

    danger_patterns = [
        " rm ",
        "rm ",
        " dd ",
        "dd if=",
        "mkfs",
        " fdisk",
        " parted",
        "chmod ",
        "chown ",
        "systemctl restart",
        "systemctl stop",
        "systemctl disable",
        "apt remove",
        "apt purge",
        "kill -9",
        "reboot",
        "shutdown",
    ]
    caution_patterns = [
        "apt install",
        "apt update",
        "systemctl status",
        "systemctl start",
        "mount ",
        "umount ",
        "cp ",
        "mv ",
        "tar ",
        "find ",
        "grep ",
        "journalctl",
        "ping ",
        "curl ",
        "wget ",
        "ssh ",
    ]
    safe_prefixes = (
        "ls",
        "pwd",
        "ip a",
        "ip addr",
        "df -h",
        "free -h",
        "uname -a",
        "whoami",
        "id",
        "cat ",
        "head ",
        "tail ",
        "ps ",
        "top",
        "du ",
    )

    padded = f" {text} "
    if any(
        pattern in padded or text.startswith(pattern) for pattern in danger_patterns
    ):
        return "danger"
    if any(pattern in text for pattern in caution_patterns):
        return "caution"
    if text.startswith(safe_prefixes):
        return "safe"
    return "caution"


def normalize_linux_help_entry(app, raw, existing_ids=None):
    item = dict(raw or {})
    cmd = (item.get("cmd") or "").strip()
    info = (item.get("info") or "").strip()
    category = (item.get("category") or "Allgemein").strip() or "Allgemein"
    name = (item.get("name") or cmd or "Unbenannt").strip() or "Unbenannt"
    explanation = (item.get("explanation") or info).strip()
    warning_text = (item.get("warning_text") or "").strip()
    risk = (item.get("risk") or "").strip().lower()
    if risk not in {"safe", "caution", "danger"}:
        risk = linux_help_get_risk_level(cmd)
    enabled_raw = item.get("enabled", True)
    if isinstance(enabled_raw, str):
        enabled = enabled_raw.strip().lower() not in {"0", "false", "no", "off"}
    else:
        enabled = bool(enabled_raw)
    normalized = {
        "id": linux_help_make_id(item, existing_ids=existing_ids),
        "category": category,
        "name": name,
        "info": info,
        "cmd": cmd,
        "risk": risk,
        "explanation": explanation,
        "warning_text": warning_text,
        "enabled": enabled,
    }
    return normalized


def rebuild_linux_help_indexes(app):
    active_entries = [item for item in app.linux_help_data if item.get("enabled", True)]
    active_entries.sort(
        key=lambda item: (
            item.get("category", "").lower(),
            item.get("name", "").lower(),
        )
    )
    categories = sorted(
        {item.get("category", "Allgemein") for item in active_entries},
        key=str.lower,
    )
    commands_by_category = {category: [] for category in categories}
    for item in active_entries:
        commands_by_category.setdefault(item["category"], []).append(item)
    app.linux_help_commands = active_entries
    app.linux_help_categories = categories
    app.linux_help_commands_by_category = commands_by_category


def import_linux_help_csv(app, path):
    commands = []
    seen_ids = set()
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not row:
                continue
            reduced = {
                "category": row.get("category"),
                "name": row.get("name"),
                "info": row.get("info"),
                "cmd": row.get("cmd"),
            }
            if not (
                reduced.get("category") and reduced.get("name") and reduced.get("cmd")
            ):
                continue
            item = normalize_linux_help_entry(app, reduced, existing_ids=seen_ids)
            seen_ids.add(item["id"])
            commands.append(item)
    commands.sort(
        key=lambda item: (
            item.get("category", "").lower(),
            item.get("name", "").lower(),
        )
    )
    app.linux_help_data = commands
    rebuild_linux_help_indexes(app)
    set_linux_help_dirty(app, True)
    return commands


def export_linux_help_csv(app, path):
    rows = []
    for item in app.linux_help_data:
        rows.append(
            {
                "category": item.get("category", ""),
                "name": item.get("name", ""),
                "info": item.get("info", ""),
                "cmd": item.get("cmd", ""),
            }
        )
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["category", "name", "info", "cmd"])
        writer.writeheader()
        writer.writerows(rows)


def load_linux_help_data(app):
    data_path = app.linux_help_data_path
    if os.path.isfile(data_path):
        with open(data_path, "r", encoding="utf-8") as fh:
            raw_items = json.load(fh)
        items = raw_items if isinstance(raw_items, list) else []
        seen_ids = set()
        app.linux_help_data = []
        for item in items:
            normalized = normalize_linux_help_entry(app, item, existing_ids=seen_ids)
            seen_ids.add(normalized["id"])
            app.linux_help_data.append(normalized)
        rebuild_linux_help_indexes(app)
        set_linux_help_dirty(app, False)
        return app.linux_help_data

    commands = import_linux_help_csv(app, linux_help_csv_path())
    save_linux_help_data(app, update_status=False)
    set_linux_help_dirty(app, False)
    return commands


def save_linux_help_data(app, update_status=True):
    app.linux_help_apply_form_to_entry(mark_dirty=False)
    ok, err = safe_write_json(
        app.linux_help_data_path,
        app.linux_help_data,
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_save_failed",
                "Linux Hilfe: Speichern fehlgeschlagen.",
            )
        )
        if hasattr(app, "linux_help_text") and app.linux_help_text is not None:
            app.linux_help_text.delete("1.0", "end")
            app.linux_help_text.insert(
                "1.0",
                app.tr(
                    "linux_help_save_failed_body",
                    "Die Linux-Hilfe-Daten konnten nicht gespeichert werden.\n\n"
                    "Pfad: {path}\n"
                    "Fehler: {error}",
                ).format(path=app.linux_help_data_path, error=err),
            )
        return False
    set_linux_help_dirty(app, False)
    if update_status:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_saved_count",
                "Linux Hilfe: {count} Einträge gespeichert.",
            ).format(count=len(app.linux_help_data))
        )
    return True


def get_linux_help_categories(app):
    return list(app.linux_help_categories)


def get_linux_help_commands_for_category(app, category):
    return list(app.linux_help_commands_by_category.get((category or "").strip(), []))


def get_linux_help_command_by_id(app, command_id):
    target = (command_id or "").strip()
    for item in app.linux_help_data:
        if item.get("id") == target:
            return item
    return None


def sync_linux_help_form_categories(app):
    categories = get_linux_help_categories(app)
    app.linux_help_category_combo["values"] = categories
    app.linux_help_form_category_combo["values"] = categories


def set_linux_help_form_from_entry(app, item=None):
    entry = item or {}
    app.linux_help_form_category_var.set(entry.get("category", ""))
    app.linux_help_form_name_var.set(entry.get("name", ""))
    app.linux_help_form_info_var.set(entry.get("info", ""))
    app.linux_help_form_cmd_var.set(entry.get("cmd", ""))
    app.linux_help_form_risk_var.set(entry.get("risk", "caution"))
    app.linux_help_form_explanation_var.set(entry.get("explanation", ""))
    app.linux_help_form_warning_var.set(entry.get("warning_text", ""))
    app.linux_help_form_enabled_var.set(bool(entry.get("enabled", True)))


def set_linux_help_risk_light(app, risk):
    if not hasattr(app, "linux_help_risk_canvas"):
        return
    fill = {
        "safe": "green",
        "caution": "yellow",
        "danger": "red",
    }.get((risk or "").strip().lower(), "gray")
    app.linux_help_risk_canvas.itemconfigure(app.linux_help_risk_dot, fill=fill)


def update_linux_help_notes(app, item=None):
    if not hasattr(app, "linux_help_text") or app.linux_help_text is None:
        return
    app.linux_help_text.delete("1.0", "end")
    if not item:
        app.linux_help_text.insert(
            "1.0",
            app.tr(
                "linux_help_notes_empty",
                "Hier erscheinen später ausführliche Erklärungen, Hinweise und "
                "Sicherheitsinfos zu Linux-Befehlen.\n\n"
                "Die vollständige Ausführung wird später integriert. Aktuell "
                "dient dieser Bereich zur Anzeige, Datenpflege und Vorbereitung.",
            ),
        )
        return
    app.linux_help_text.insert(
        "1.0",
        "\n".join(
            [
                f"{app.tr('label_id', 'ID')}: {item.get('id') or '–'}",
                f"{app.tr('linux_help_label_name', 'Name')}: {item.get('name') or '–'}",
                f"{app.tr('label_category', 'Kategorie')}: {item.get('category') or '–'}",
                f"{app.tr('linux_help_label_description', 'Beschreibung')}: {item.get('info') or '–'}",
                f"{app.tr('linux_help_label_command_name', 'Befehl')}: {item.get('cmd') or '–'}",
                f"{app.tr('linux_help_label_risk_text', 'Risiko')}: {item.get('risk') or '–'}",
                f"{app.tr('label_active', 'Aktiv')}: {app.tr('label_yes', 'ja') if item.get('enabled', True) else app.tr('label_no', 'nein')}",
                "",
                f"{app.tr('linux_help_label_explanation_text', 'Erklärung')}: {item.get('explanation') or '–'}",
                f"{app.tr('linux_help_label_warning_text', 'Warntext')}: {item.get('warning_text') or '–'}",
                "",
                f"{app.tr('label_note', 'Hinweis')}:",
                app.tr(
                    "linux_help_note_execution_later",
                    "Die vollständige Ausführung wird später integriert.",
                ),
                app.tr(
                    "linux_help_note_display_only",
                    "Aktuell dient dieser Bereich zur Anzeige, Datenpflege und Vorbereitung.",
                ),
            ]
        ),
    )


def refresh_linux_help_list(app, category=None):
    category_name = (category or app.linux_help_category_var.get() or "").strip()
    if (
        category_name not in app.linux_help_commands_by_category
        and app.linux_help_categories
    ):
        category_name = app.linux_help_categories[0]
        app.linux_help_category_var.set(category_name)

    app.linux_help_visible_commands = list(
        get_linux_help_commands_for_category(app, category_name)
    )
    app.linux_help_visible_command_ids = [
        item.get("id", "") for item in app.linux_help_visible_commands
    ]
    app.linux_help_listbox.delete(0, "end")
    for item in app.linux_help_visible_commands:
        app.linux_help_listbox.insert("end", item.get("name") or item.get("cmd") or "–")

    app.linux_help_selected_id = ""
    app.linux_help_command_var.set(
        app.tr("linux_help_no_command_selected", "Kein Befehl ausgewählt.")
    )
    app.linux_help_desc_var.set(
        app.tr(
            "linux_help_select_left_hint",
            "Wähle links einen Befehl aus, um Beschreibung, Kommando und Risiko anzuzeigen.",
        )
    )
    app.linux_help_risk_var.set(app.tr("linux_help_risk_unknown", "Risiko: –"))
    set_linux_help_risk_light(app, "unknown")
    set_linux_help_form_from_entry(app, None)
    update_linux_help_notes(app, None)

    if app.linux_help_visible_commands:
        app.linux_help_listbox.selection_clear(0, "end")
        app.linux_help_listbox.selection_set(0)
        app.linux_help_listbox.activate(0)
        on_linux_help_select(app)


def on_linux_help_select(app, _event=None):
    try:
        idx = int(app.linux_help_listbox.curselection()[0])
    except Exception:
        return
    if idx < 0 or idx >= len(app.linux_help_visible_commands):
        return

    command_id = app.linux_help_visible_command_ids[idx]
    item = get_linux_help_command_by_id(app, command_id)
    if not item:
        return
    app.linux_help_selected_id = command_id
    risk = (item.get("risk") or "").strip().lower()
    risk_text = {
        "safe": app.tr("linux_help_risk_safe", "Risiko: Sicher"),
        "caution": app.tr("linux_help_risk_caution", "Risiko: Vorsicht"),
        "danger": app.tr("linux_help_risk_danger", "Risiko: Gefährlich"),
    }.get(risk, app.tr("linux_help_risk_unknown", "Risiko: –"))

    app.linux_help_command_var.set(item.get("cmd") or "–")
    app.linux_help_desc_var.set(
        item.get("info")
        or app.tr(
            "linux_help_no_description",
            "Keine Beschreibung vorhanden.",
        )
    )
    app.linux_help_risk_var.set(risk_text)
    set_linux_help_risk_light(app, risk)
    set_linux_help_form_from_entry(app, item)
    update_linux_help_notes(app, item)


def linux_help_apply_form_to_entry(app, mark_dirty=True):
    target = get_linux_help_command_by_id(app, app.linux_help_selected_id)
    if target is None:
        return False
    target["category"] = (
        app.linux_help_form_category_var.get() or "Allgemein"
    ).strip() or "Allgemein"
    target["name"] = (app.linux_help_form_name_var.get() or "").strip() or target[
        "name"
    ]
    target["info"] = (app.linux_help_form_info_var.get() or "").strip()
    target["cmd"] = (app.linux_help_form_cmd_var.get() or "").strip()
    target["explanation"] = (app.linux_help_form_explanation_var.get() or "").strip()
    target["warning_text"] = (app.linux_help_form_warning_var.get() or "").strip()
    manual_risk = (app.linux_help_form_risk_var.get() or "").strip().lower()
    if manual_risk in {"safe", "caution", "danger"}:
        target["risk"] = manual_risk
    else:
        target["risk"] = linux_help_get_risk_level(target.get("cmd", ""))
    target["enabled"] = bool(app.linux_help_form_enabled_var.get())
    normalized = normalize_linux_help_entry(
        app,
        target,
        existing_ids={item["id"] for item in app.linux_help_data if item is not target},
    )
    target.update(normalized)
    rebuild_linux_help_indexes(app)
    sync_linux_help_form_categories(app)
    if target.get("category"):
        app.linux_help_category_var.set(target["category"])
    refresh_linux_help_list(app, category=target.get("category"))
    if mark_dirty:
        set_linux_help_dirty(app, True)
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_changes_pending",
                "Linux Hilfe: Änderungen vorgemerkt.",
            )
        )
    return True


def linux_help_new_entry(app):
    base = {
        "category": app.linux_help_category_var.get() or "Allgemein",
        "name": "Neuer Befehl",
        "info": "Neue Kurzbeschreibung",
        "cmd": "",
        "risk": "caution",
        "explanation": "",
        "warning_text": "",
        "enabled": True,
    }
    new_entry = normalize_linux_help_entry(
        app,
        base,
        existing_ids={item.get("id") for item in app.linux_help_data},
    )
    app.linux_help_data.append(new_entry)
    rebuild_linux_help_indexes(app)
    sync_linux_help_form_categories(app)
    app.linux_help_category_var.set(new_entry["category"])
    refresh_linux_help_list(app, category=new_entry["category"])
    app.linux_help_selected_id = new_entry["id"]
    set_linux_help_form_from_entry(app, new_entry)
    set_linux_help_dirty(app, True)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_new_entry_ready",
            "Linux Hilfe: Neuer Eintrag vorbereitet.",
        )
    )


def linux_help_edit_selected(app):
    if not app.linux_help_selected_id:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_select_entry_first",
                "Linux Hilfe: Bitte zuerst einen Eintrag auswählen.",
            )
        )
        return
    if linux_help_apply_form_to_entry(app, mark_dirty=True):
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_selection_updated",
                "Linux Hilfe: Auswahl aktualisiert.",
            )
        )


def linux_help_delete_selected(app):
    target = get_linux_help_command_by_id(app, app.linux_help_selected_id)
    if target is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_select_entry_first",
                "Linux Hilfe: Bitte zuerst einen Eintrag auswählen.",
            )
        )
        return
    app.linux_help_data = [
        item
        for item in app.linux_help_data
        if item.get("id") != app.linux_help_selected_id
    ]
    app.linux_help_selected_id = ""
    rebuild_linux_help_indexes(app)
    sync_linux_help_form_categories(app)
    refresh_linux_help_list(app)
    set_linux_help_dirty(app, True)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_entry_deleted",
            "Linux Hilfe: Eintrag gelöscht.",
        )
    )


def linux_help_import_csv_dialog(app):
    path = filedialog.askopenfilename(
        parent=app,
        title=app.tr(
            "linux_help_import_csv_title",
            "Linux-Hilfe CSV importieren",
        ),
        filetypes=[
            (app.tr("filetype_csv", "CSV-Dateien"), "*.csv"),
            (app.tr("filetype_all", "Alle Dateien"), "*.*"),
        ],
        initialfile=os.path.basename(linux_help_csv_path()),
    )
    if not path:
        return
    app.linux_help_import_path = path
    try:
        commands = import_linux_help_csv(app, path)
        sync_linux_help_form_categories(app)
        if app.linux_help_categories:
            app.linux_help_category_var.set(app.linux_help_categories[0])
        refresh_linux_help_list(app)
        save_linux_help_data(app, update_status=False)
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_imported_count",
                "Linux Hilfe: {count} Einträge aus CSV importiert.",
            ).format(count=len(commands))
        )
    except Exception as exc:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_import_failed",
                "Linux Hilfe: CSV-Import fehlgeschlagen.",
            )
        )
        update_linux_help_notes(app, None)
        if hasattr(app, "linux_help_text") and app.linux_help_text is not None:
            app.linux_help_text.delete("1.0", "end")
            app.linux_help_text.insert(
                "1.0",
                app.tr(
                    "linux_help_import_failed_body",
                    "Der CSV-Import ist fehlgeschlagen.\n\n"
                    "Pfad: {path}\n"
                    "Fehler: {error}",
                ).format(path=path, error=exc),
            )


def linux_help_export_csv_dialog(app):
    path = filedialog.asksaveasfilename(
        parent=app,
        title=app.tr(
            "linux_help_export_csv_title",
            "Linux-Hilfe CSV exportieren",
        ),
        defaultextension=".csv",
        filetypes=[
            (app.tr("filetype_csv", "CSV-Dateien"), "*.csv"),
            (app.tr("filetype_all", "Alle Dateien"), "*.*"),
        ],
        initialfile="linux_help_export.csv",
    )
    if not path:
        return
    export_linux_help_csv(app, path)
    app.linux_help_status_var.set(
        app.tr("linux_help_status_exported", "Linux Hilfe: CSV exportiert.")
    )


def reload_linux_help_data(app):
    try:
        commands = load_linux_help_data(app)
    except Exception as exc:
        app.linux_help_data = []
        app.linux_help_commands = []
        app.linux_help_categories = []
        app.linux_help_commands_by_category = {}
        app.linux_help_visible_commands = []
        app.linux_help_visible_command_ids = []
        app.linux_help_selected_id = ""
        app.linux_help_category_combo["values"] = []
        app.linux_help_form_category_combo["values"] = []
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_load_failed",
                "Linux Hilfe: Daten konnten nicht geladen werden.",
            )
        )
        app.linux_help_command_var.set(
            app.tr("linux_help_no_command_selected", "Kein Befehl ausgewählt.")
        )
        app.linux_help_desc_var.set(
            app.tr(
                "linux_help_desc_load_failed",
                "Die Linux-Hilfe konnte keine gültigen Daten laden.",
            )
        )
        app.linux_help_risk_var.set(app.tr("linux_help_risk_unknown", "Risiko: –"))
        set_linux_help_risk_light(app, "unknown")
        set_linux_help_form_from_entry(app, None)
        update_linux_help_notes(app, None)
        if hasattr(app, "linux_help_text") and app.linux_help_text is not None:
            app.linux_help_text.delete("1.0", "end")
            app.linux_help_text.insert(
                "1.0",
                app.tr(
                    "linux_help_load_failed_body",
                    "Die Linux-Hilfe-Daten konnten nicht geladen werden.\n\n"
                    "JSON: {json_path}\n"
                    "CSV-Basis: {csv_path}\n"
                    "Fehler: {error}",
                ).format(
                    json_path=app.linux_help_data_path,
                    csv_path=linux_help_csv_path(),
                    error=exc,
                ),
            )
        return

    sync_linux_help_form_categories(app)
    if app.linux_help_categories:
        app.linux_help_category_var.set(app.linux_help_categories[0])
    refresh_linux_help_list(app)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_loaded_count",
            "Linux Hilfe: {count} Einträge geladen.",
        ).format(count=len(commands))
    )


def send_linux_help_command_to_terminal(app):
    item = get_linux_help_command_by_id(app, app.linux_help_selected_id)
    if item is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_no_command_selected",
                "Linux Hilfe: Kein Befehl ausgewählt.",
            )
        )
        app.log(
            app.tr(
                "linux_help_log_no_command_selected",
                "Linux-Hilfe: Kein Befehl ausgewählt",
            )
        )
        return False
    if not item.get("enabled", True):
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_entry_disabled",
                "Linux Hilfe: Dieser Eintrag ist deaktiviert und kann nicht gesendet werden.",
            )
        )
        app.log(
            app.tr(
                "linux_help_log_disabled_not_sent",
                "Linux-Hilfe: Deaktivierter Eintrag nicht gesendet",
            )
        )
        return False

    cmd = item.get("cmd", "")
    ok, reason = app._validate_linux_help_command_for_terminal(cmd)
    if not ok:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_terminal_not_possible",
                "Linux Hilfe: Terminalversand nicht möglich ({reason})",
            ).format(reason=reason)
        )
        app.log(
            app.tr(
                "linux_help_log_terminal_cancelled",
                "Linux-Hilfe: Terminalversand abgebrochen",
            )
        )
        return False

    risk = (item.get("risk") or "").strip().lower()
    if risk == "caution":
        if not app._confirm_danger_action(
            f"linux_help:send:{item.get('id')}",
            title=app.tr(
                "linux_help_confirm_send_title",
                "Befehl an Terminal senden",
            ),
            prompt=app.tr(
                "linux_help_confirm_send_prompt",
                "Dieser Befehl verändert möglicherweise Systemzustände.\n\n"
                "Trotzdem ins Terminal senden?",
            ),
            cooldown_s=0,
        ):
            app.linux_help_status_var.set(
                app.tr(
                    "linux_help_status_terminal_cancelled",
                    "Linux Hilfe: Terminalversand abgebrochen.",
                )
            )
            app.log(
                app.tr(
                    "linux_help_log_terminal_cancelled",
                    "Linux-Hilfe: Terminalversand abgebrochen",
                )
            )
            return False
    elif risk == "danger":
        if not app._confirm_danger_action(
            f"linux_help:send:{item.get('id')}",
            title=app.tr(
                "linux_help_confirm_danger_title",
                "Gefährlichen Befehl senden",
            ),
            prompt=app.tr(
                "linux_help_confirm_danger_prompt",
                "Achtung: Dieser Befehl kann Systemzustände verändern oder Schaden verursachen.\n"
                "Nur senden, wenn du genau weißt, was du tust.\n\n"
                "Trotzdem ins Terminal senden?",
            ),
            cooldown_s=0,
            require_phrase="SENDEN",
            force_guard=True,
        ):
            app.linux_help_status_var.set(
                app.tr(
                    "linux_help_status_terminal_cancelled",
                    "Linux Hilfe: Terminalversand abgebrochen.",
                )
            )
            app.log(
                app.tr(
                    "linux_help_log_terminal_cancelled",
                    "Linux-Hilfe: Terminalversand abgebrochen",
                )
            )
            return False

    try:
        terminal_name = app._open_command_in_external_terminal(cmd)
    except Exception as exc:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_terminal_failed",
                "Linux Hilfe: Terminal konnte nicht gestartet werden.",
            )
        )
        app.log(
            app.tr(
                "linux_help_log_terminal_cancelled",
                "Linux-Hilfe: Terminalversand abgebrochen",
            )
        )
        if hasattr(app, "linux_help_text") and app.linux_help_text is not None:
            app.linux_help_text.delete("1.0", "end")
            app.linux_help_text.insert(
                "1.0",
                "\n".join(
                    [
                        f"{app.tr('linux_help_label_name', 'Name')}: {item.get('name') or '–'}",
                        f"{app.tr('linux_help_label_command_name', 'Befehl')}: {cmd}",
                        "",
                        f"{app.tr('label_error', 'Fehler')}:",
                        str(exc),
                    ]
                ),
            )
        return False

    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_sent_to_terminal",
            "Linux Hilfe: Befehl wurde an ein externes Terminal gesendet.",
        )
    )
    if hasattr(app, "linux_help_text") and app.linux_help_text is not None:
        app.linux_help_text.delete("1.0", "end")
        app.linux_help_text.insert(
            "1.0",
            "\n".join(
                [
                    f"{app.tr('linux_help_label_name', 'Name')}: {item.get('name') or '–'}",
                    f"{app.tr('label_category', 'Kategorie')}: {item.get('category') or '–'}",
                    f"{app.tr('linux_help_label_command_name', 'Befehl')}: {cmd}",
                    f"{app.tr('label_terminal', 'Terminal')}: {terminal_name}",
                    "",
                    f"{app.tr('label_note', 'Hinweis')}:",
                    app.tr(
                        "linux_help_terminal_note_sent",
                        "Befehl wurde an ein externes Terminal gesendet.",
                    ),
                    app.tr(
                        "linux_help_terminal_note_external",
                        "Die Ausführung erfolgt nicht direkt im NetMon-Prozess.",
                    ),
                ]
            ),
        )
    app.log(
        app.tr(
            "linux_help_log_command_sent",
            "Linux-Hilfe: Befehl an Terminal gesendet: {name}",
        ).format(name=item.get("name") or cmd)
    )
    return True
