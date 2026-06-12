"""Linux command database controller helpers for NetMon."""

from __future__ import annotations

import csv
import json
import os
import re
import tkinter as tk
from tkinter import ttk

try:
    from tkinter import filedialog, messagebox
except Exception:
    filedialog = messagebox = None

try:
    from openpyxl import load_workbook
except Exception:
    load_workbook = None

try:
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    from core.utils import safe_write_json


NETMON_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LINUX_HELP_EXPORT_FIELDS = [
    "category",
    "name",
    "info",
    "cmd",
    "syntax",
    "example",
    "explanation",
    "root_required",
    "tags",
    "risk",
]
RISK_UI = {
    "safe": ("🟢 Sicher", "green"),
    "caution": ("🟡 Admin", "#d8a106"),
    "danger": ("🔴 Gefährlich", "red"),
    "unknown": ("⚪ Unbekannt", "gray"),
}
SOURCE_FIELD_ALIASES = {
    "category": ("category", "kategorie"),
    "name": ("name", "befehl", "command_name", "command name", "title"),
    "info": (
        "info",
        "description",
        "beschreibung",
        "kurzbeschreibung",
        "short_description",
        "short description",
        "summary",
    ),
    "cmd": ("cmd", "command", "kommando", "befehl", "command_line", "command line"),
    "syntax": ("syntax", "usage"),
    "example": ("example", "beispiel", "examples"),
    "explanation": (
        "explanation",
        "ausgabe/erklaerung",
        "erklaerung",
        "details",
        "notes",
    ),
    "warning_text": ("warning_text", "warning", "warnung", "hinweis"),
    "tags": ("tags",),
    "root_required": (
        "root_required",
        "root noetig",
        "root nötig",
        "requires_root",
        "requires root",
        "root_needed",
        "root needed",
    ),
    "risk": ("risk", "risiko", "risk_level", "risk level"),
}
RISK_DIALOG_CHOICES = (
    ("🟢 Sicher", "safe"),
    ("🟡 Admin", "caution"),
    ("🔴 Gefährlich", "danger"),
)


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _app_var_get(app, name: str, default=""):
    var = _app_value(app, name)
    if var is None:
        return default
    try:
        value = var.get()
    except Exception:
        value = default
    return value if value is not None else default


def _app_var_set(app, name: str, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _set_text_widget_content(widget, text: str):
    if widget is None:
        return
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    if text:
        widget.insert("1.0", text)
    widget.configure(state="disabled")


def set_linux_help_dirty(app, dirty=True):
    app.linux_help_dirty = bool(dirty)


def linux_help_csv_candidates():
    return [
        os.path.join(NETMON_REPO_ROOT, "netmon", "linux-befehle.csv"),
        os.path.join(NETMON_REPO_ROOT, "netmon", "linux-befehle.xlsx"),
        os.path.join(NETMON_REPO_ROOT, "linux-befehle.csv"),
        os.path.join(NETMON_REPO_ROOT, "linux-befehle.xlsx"),
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
        "userdel",
        "groupdel",
    ]
    caution_patterns = [
        "sudo ",
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
        "ufw ",
        "iptables",
        "docker ",
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
        "which ",
        "history",
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


def linux_help_requires_root(cmd: str, risk: str) -> bool:
    text = (cmd or "").strip().lower()
    if text.startswith("sudo "):
        return True
    if risk == "danger":
        return True
    root_patterns = (
        "apt ",
        "systemctl ",
        "mount ",
        "umount ",
        "ufw ",
        "iptables",
        "mkfs",
        "fdisk",
        "parted",
        "chown ",
        "chmod ",
        "journalctl -u",
        "useradd",
        "usermod",
        "userdel",
    )
    return any(pattern in text for pattern in root_patterns)


def linux_help_tag_text(value) -> str:
    if isinstance(value, (list, tuple, set)):
        parts = [str(part).strip() for part in value if str(part).strip()]
    else:
        text = str(value or "").strip()
        if not text:
            parts = []
        else:
            parts = [part.strip() for part in re.split(r"[;,|]", text) if part.strip()]
    deduped = []
    seen = set()
    for part in parts:
        lowered = part.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(part)
    return ", ".join(deduped)


def _derive_linux_help_tags(item) -> str:
    explicit = linux_help_tag_text(item.get("tags"))
    if explicit:
        return explicit
    derived = []
    for value in (item.get("category"), item.get("name")):
        text = str(value or "").strip()
        if text:
            derived.append(text)
    cmd = str(item.get("cmd") or "").strip()
    if cmd:
        first_token = cmd.split()[0]
        if first_token:
            derived.append(first_token)
    return linux_help_tag_text(derived)


def _bool_from_raw(value, default=True):
    if value is None or value == "":
        return bool(default)
    if isinstance(value, str):
        text = value.strip().lower()
        false_tokens = {"0", "false", "no", "off", "nein", "n", "selten"}
        true_tokens = {"1", "true", "yes", "on", "ja", "j", "immer"}
        parts = [part.strip() for part in re.split(r"[/,;|]", text) if part.strip()]
        if parts:
            if any(part in false_tokens for part in parts):
                return False
            if any(part in true_tokens for part in parts):
                return True
        return text not in false_tokens
    return bool(value)


def _normalize_source_row(row):
    normalized = {}
    source = {
        str(key or "").strip().lower(): value for key, value in dict(row or {}).items()
    }
    for target_key, aliases in SOURCE_FIELD_ALIASES.items():
        for alias in aliases:
            if alias in source:
                normalized[target_key] = source.get(alias)
                break
    return normalized


def _normalize_risk_value(value):
    text = str(value or "").strip().lower()
    if not text:
        return ""
    if any(token in text for token in ("rot", "red", "danger", "gefähr", "gefaehr")):
        return "danger"
    if any(
        token in text for token in ("gelb", "yellow", "admin", "vorsicht", "caution")
    ):
        return "caution"
    if any(token in text for token in ("gruen", "grün", "green", "safe", "sicher")):
        return "safe"
    return text


def _risk_storage_to_dialog_label(value):
    normalized = _normalize_risk_value(value)
    for label, key in RISK_DIALOG_CHOICES:
        if key == normalized:
            return label
    return RISK_DIALOG_CHOICES[1][0]


def _risk_dialog_label_to_storage(value):
    label = str(value or "").strip()
    for option_label, key in RISK_DIALOG_CHOICES:
        if label == option_label:
            return key
    return _normalize_risk_value(value) or "caution"


def _selected_linux_help_id(app) -> str:
    command_id = str(_app_value(app, "linux_help_selected_id", "") or "").strip()
    if command_id:
        return command_id
    tree = _app_value(app, "linux_help_tree")
    if tree is not None:
        try:
            selection = tree.selection()
        except Exception:
            selection = ()
        if selection:
            return str(selection[0] or "").strip()
    listbox = _app_value(app, "linux_help_listbox")
    if listbox is not None:
        try:
            idx = int(listbox.curselection()[0])
        except Exception:
            idx = -1
        visible_ids = list(_app_value(app, "linux_help_visible_command_ids", []) or [])
        if 0 <= idx < len(visible_ids):
            return str(visible_ids[idx] or "").strip()
    return ""


def _linux_help_command_resolver(app):
    resolver = _app_value(app, "get_linux_help_command_by_id")
    return resolver if callable(resolver) else None


def _resolve_linux_help_item(app, command_id=None):
    target_id = str(command_id or _selected_linux_help_id(app) or "").strip()
    if not target_id:
        return None
    resolver = _linux_help_command_resolver(app)
    if resolver is not None:
        return resolver(target_id)
    return get_linux_help_command_by_id(app, target_id)


def _set_chad_direct_prompt_safe(app, title, prompt):
    direct_prompt_setter = _app_value(app, "set_chad_direct_prompt")
    if callable(direct_prompt_setter):
        direct_prompt_setter(title, prompt)
        return True
    return False


def _get_selected_linux_help_item(app):
    return _resolve_linux_help_item(app)


def _linux_help_chad_title(item) -> str:
    entry = dict(item or {})
    return (
        f"Linux-Befehl erklären: "
        f"{entry.get('name') or entry.get('cmd') or 'Unbekannt'}"
    )


def build_linux_help_chad_prompt(app, item):
    entry = dict(item or {})
    risk_label, _fill = RISK_UI.get(
        str(entry.get("risk") or "").strip().lower(),
        RISK_UI["unknown"],
    )
    root_text = (
        app.tr("label_yes", "Ja")
        if entry.get("root_required")
        else app.tr("label_no", "Nein")
    )
    tags = str(entry.get("tags") or "–").strip() or "–"
    explanation = (
        str(entry.get("explanation") or "").strip()
        or "Keine Zusatz-Erklärung hinterlegt."
    )
    warning_text = (
        str(entry.get("warning_text") or "").strip()
        or "Kein zusätzlicher Hinweis hinterlegt."
    )
    lines = [
        "Bitte erkläre den folgenden Linux-Befehl für Anfänger sehr verständlich und sauber strukturiert auf Deutsch.",
        "",
        "Wichtige Anforderungen an deine Antwort:",
        "- Schreibe anfängerfreundlich, ohne Vorwissen vorauszusetzen.",
        "- Erkläre zuerst kurz, wofür der Befehl gedacht ist.",
        "- Zerlege danach die Syntax und die wichtigsten Bestandteile.",
        "- Erkläre das Beispiel Schritt für Schritt.",
        "- Nenne typische Anwendungsfälle im Alltag.",
        "- Weise klar auf Risiken, Root-Bedarf und mögliche Fehler hin.",
        "- Gib am Ende 3 sichere Einsteiger-Tipps oder Varianten.",
        "- Nutze eine ruhige, verständliche Sprache statt unnötig technischer Begriffe.",
        "",
        "Befehlsdaten aus NetMon:",
        f"Befehl: {entry.get('name') or entry.get('cmd') or '–'}",
        f"Kategorie: {entry.get('category') or '–'}",
        f"Kommando: {entry.get('cmd') or '–'}",
        f"Kurzbeschreibung: {entry.get('info') or '–'}",
        f"Syntax: {entry.get('syntax') or entry.get('cmd') or '–'}",
        f"Beispiel: {entry.get('example') or entry.get('cmd') or '–'}",
        f"Erklärung/Hinweis aus Datenbank: {explanation}",
        f"Zusätzlicher Warnhinweis: {warning_text}",
        f"Root nötig: {root_text}",
        f"Risiko-Ampel: {risk_label}",
        f"Tags: {tags}",
    ]
    return "\n".join(lines).strip()


def _selected_linux_help_chad_payload(app):
    item = _get_selected_linux_help_item(app)
    if item is None:
        return None, "", ""
    prompt = build_linux_help_chad_prompt(app, item)
    return item, _linux_help_chad_title(item), prompt


def _iter_source_rows(path):
    extension = os.path.splitext(str(path or ""))[1].lower()
    if extension == ".xlsx":
        if load_workbook is None:
            raise RuntimeError("XLSX-Import benötigt openpyxl.")
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            sheet = workbook.active
            rows = list(sheet.iter_rows(values_only=True))
        finally:
            workbook.close()
        if not rows:
            return []
        headers = [str(cell or "").strip() for cell in rows[0]]
        return [dict(zip(headers, row)) for row in rows[1:] if any(row)]
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader if row]


def normalize_linux_help_entry(app, raw, existing_ids=None):
    item = dict(raw or {})
    cmd = str(item.get("cmd") or "").strip()
    info = str(item.get("info") or item.get("description") or "").strip()
    category = str(item.get("category") or "Allgemein").strip() or "Allgemein"
    name = str(item.get("name") or cmd or "Unbenannt").strip() or "Unbenannt"
    syntax = str(item.get("syntax") or cmd).strip() or cmd
    example = str(item.get("example") or cmd).strip() or cmd
    explanation = str(item.get("explanation") or info).strip()
    warning_text = str(item.get("warning_text") or item.get("warning") or "").strip()
    risk = _normalize_risk_value(item.get("risk"))
    if risk not in {"safe", "caution", "danger"}:
        risk = linux_help_get_risk_level(cmd)
    enabled = _bool_from_raw(item.get("enabled"), default=True)
    root_required = _bool_from_raw(
        item.get("root_required"),
        default=linux_help_requires_root(cmd, risk),
    )
    normalized = {
        "id": linux_help_make_id(item, existing_ids=existing_ids),
        "category": category,
        "name": name,
        "info": info,
        "cmd": cmd,
        "syntax": syntax or cmd,
        "example": example or cmd,
        "explanation": explanation,
        "warning_text": warning_text,
        "tags": _derive_linux_help_tags(item),
        "risk": risk,
        "root_required": root_required,
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
    for row in _iter_source_rows(path):
        source_row = _normalize_source_row(row)
        reduced = {
            "category": source_row.get("category"),
            "name": source_row.get("name"),
            "info": source_row.get("info"),
            "cmd": source_row.get("cmd"),
            "syntax": source_row.get("syntax"),
            "example": source_row.get("example"),
            "explanation": source_row.get("explanation"),
            "warning_text": source_row.get("warning_text"),
            "tags": source_row.get("tags"),
            "root_required": source_row.get("root_required"),
            "risk": source_row.get("risk"),
        }
        if not (
            str(reduced.get("category") or "").strip()
            and str(reduced.get("name") or "").strip()
            and str(reduced.get("cmd") or "").strip()
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
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LINUX_HELP_EXPORT_FIELDS)
        writer.writeheader()
        for item in app.linux_help_data:
            row = dict(item)
            row["root_required"] = "yes" if item.get("root_required") else "no"
            writer.writerow(
                {field: row.get(field, "") for field in LINUX_HELP_EXPORT_FIELDS}
            )


def load_linux_help_data(app):
    data_path = app.linux_help_data_path
    if os.path.isfile(data_path):
        with open(data_path, "r", encoding="utf-8") as handle:
            raw_items = json.load(handle)
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
        update_linux_help_notes(app, None, extra_error=str(err))
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
    name = str(category or "").strip()
    if not name or name == "Alle Kategorien":
        return list(app.linux_help_commands)
    return list(app.linux_help_commands_by_category.get(name, []))


def get_linux_help_command_by_id(app, command_id):
    target = str(command_id or "").strip()
    data = _app_value(app, "linux_help_data", []) or []
    for item in data:
        if item.get("id") == target:
            return item
    return None


def sync_linux_help_form_categories(app):
    categories = ["Alle Kategorien", *get_linux_help_categories(app)]
    category_combo = _app_value(app, "linux_help_category_combo")
    if category_combo is not None:
        category_combo["values"] = categories
    form_category_combo = _app_value(app, "linux_help_form_category_combo")
    if form_category_combo is not None:
        form_category_combo["values"] = categories[1:]


def set_linux_help_form_from_entry(app, item=None):
    entry = item or {}
    _app_var_set(app, "linux_help_form_category_var", entry.get("category", ""))
    _app_var_set(app, "linux_help_form_name_var", entry.get("name", ""))
    _app_var_set(app, "linux_help_form_info_var", entry.get("info", ""))
    _app_var_set(app, "linux_help_form_cmd_var", entry.get("cmd", ""))
    _app_var_set(app, "linux_help_form_risk_var", entry.get("risk", "caution"))
    _app_var_set(app, "linux_help_form_explanation_var", entry.get("explanation", ""))
    _app_var_set(app, "linux_help_form_warning_var", entry.get("warning_text", ""))
    _app_var_set(app, "linux_help_form_enabled_var", bool(entry.get("enabled", True)))


def set_linux_help_risk_light(app, risk):
    canvas = _app_value(app, "linux_help_risk_canvas")
    dot = _app_value(app, "linux_help_risk_dot")
    if canvas is None or dot is None:
        return
    _label, fill = RISK_UI.get((risk or "").strip().lower(), RISK_UI["unknown"])
    canvas.itemconfigure(dot, fill=fill)


def update_linux_help_notes(app, item=None, extra_error=""):
    widget = _app_value(app, "linux_help_text")
    if widget is None:
        return
    if not item:
        body = app.tr(
            "linux_help_notes_empty",
            "Waehle oben einen Linux-Befehl aus, um hier Erklaerungen, Hinweise und Beispiele zu sehen.",
        )
        if extra_error:
            body = f"{body}\n\nFehler: {extra_error}"
        _set_text_widget_content(widget, body)
        return

    risk_label, _fill = RISK_UI.get(
        str(item.get("risk") or "").strip().lower(),
        RISK_UI["unknown"],
    )
    lines = [
        f"{app.tr('linux_help_label_command_name', 'Befehl')}: {item.get('name') or item.get('cmd') or '–'}",
        f"{app.tr('label_category', 'Kategorie')}: {item.get('category') or '–'}",
        f"{app.tr('linux_help_col_risk', 'Risiko')}: {risk_label}",
        f"{app.tr('linux_help_label_root_required', 'Root nötig')}: "
        + (
            app.tr("label_yes", "Ja")
            if item.get("root_required")
            else app.tr("label_no", "Nein")
        ),
        f"{app.tr('linux_help_label_tags', 'Tags')}: {item.get('tags') or '–'}",
        "",
        f"{app.tr('linux_help_col_command', 'Befehl')}: {item.get('cmd') or '–'}",
        f"{app.tr('linux_help_label_syntax', 'Syntax')}: {item.get('syntax') or item.get('cmd') or '–'}",
        f"{app.tr('linux_help_label_example', 'Beispiel')}: {item.get('example') or item.get('cmd') or '–'}",
        "",
        f"{app.tr('linux_help_label_description', 'Beschreibung')}:",
        item.get("info") or "–",
        "",
        f"{app.tr('linux_help_label_explanation_text', 'Erklärung')}:",
        item.get("explanation") or item.get("info") or "–",
        "",
        f"{app.tr('linux_help_label_warning_text', 'Hinweis')}:",
        item.get("warning_text")
        or app.tr(
            "linux_help_note_display_only",
            "Dieser Eintrag dient als NetMon-Nachschlagewerk und kann bei Bedarf ins Terminal gesendet werden.",
        ),
    ]
    _set_text_widget_content(widget, "\n".join(lines))


def _risk_filter_value(app):
    label = str(_app_var_get(app, "linux_help_risk_filter_var", "") or "").strip()
    return {
        "🟢 Sicher": "safe",
        "🟡 Admin": "caution",
        "🔴 Gefährlich": "danger",
    }.get(label, "")


def _matches_linux_help_query(item, query):
    text = " ".join(
        [
            str(item.get("category") or ""),
            str(item.get("name") or ""),
            str(item.get("info") or ""),
            str(item.get("cmd") or ""),
            str(item.get("syntax") or ""),
            str(item.get("example") or ""),
            str(item.get("explanation") or ""),
            str(item.get("tags") or ""),
        ]
    ).lower()
    return query in text


def clear_linux_help_filters(app):
    _app_var_set(app, "linux_help_search_var", "")
    _app_var_set(app, "linux_help_category_var", "Alle Kategorien")
    _app_var_set(app, "linux_help_risk_filter_var", "Alle Risiken")
    refresh_linux_help_list(app)


def refresh_linux_help_list(app, category=None):
    category_name = str(
        category or _app_var_get(app, "linux_help_category_var", "") or ""
    ).strip()
    if not category_name:
        category_name = "Alle Kategorien"
    if (
        category_name != "Alle Kategorien"
        and category_name not in app.linux_help_categories
    ):
        category_name = "Alle Kategorien"
    _app_var_set(app, "linux_help_category_var", category_name)

    commands = list(get_linux_help_commands_for_category(app, category_name))
    query = str(_app_var_get(app, "linux_help_search_var", "") or "").strip().lower()
    if query:
        commands = [item for item in commands if _matches_linux_help_query(item, query)]
    risk_filter = _risk_filter_value(app)
    if risk_filter:
        commands = [item for item in commands if item.get("risk") == risk_filter]

    app.linux_help_visible_commands = commands
    app.linux_help_visible_command_ids = [item.get("id", "") for item in commands]

    tree = _app_value(app, "linux_help_tree")
    listbox = _app_value(app, "linux_help_listbox")
    if tree is not None:
        tree.delete(*tree.get_children())
        for item in commands:
            risk_label, _fill = RISK_UI.get(item.get("risk"), RISK_UI["unknown"])
            tree.insert(
                "",
                "end",
                iid=item.get("id", ""),
                text=item.get("name") or item.get("cmd") or "–",
                values=(
                    item.get("category") or "–",
                    risk_label,
                    "Ja" if item.get("root_required") else "Nein",
                    item.get("tags") or "–",
                    item.get("info") or "–",
                ),
            )
    elif listbox is not None:
        listbox.delete(0, "end")
        for item in commands:
            listbox.insert("end", item.get("name") or item.get("cmd") or "–")

    app.linux_help_selected_id = ""
    _app_var_set(app, "linux_help_detail_name_var", "–")
    _app_var_set(app, "linux_help_detail_category_var", "–")
    _app_var_set(
        app,
        "linux_help_command_var",
        app.tr("linux_help_no_command_selected", "Kein Befehl ausgewählt."),
    )
    _app_var_set(
        app,
        "linux_help_desc_var",
        app.tr(
            "linux_help_select_left_hint",
            "Wähle oben einen Befehl aus, um Syntax, Beschreibung, Tags und Risiken zu sehen.",
        ),
    )
    _app_var_set(app, "linux_help_detail_syntax_var", "–")
    _app_var_set(app, "linux_help_detail_example_var", "–")
    _app_var_set(app, "linux_help_detail_root_var", "–")
    _app_var_set(app, "linux_help_detail_tags_var", "–")
    _app_var_set(
        app, "linux_help_risk_var", app.tr("linux_help_risk_unknown", "Risiko: –")
    )
    _app_var_set(app, "linux_help_risk_badge_var", "⚪ Unbekannt")
    set_linux_help_risk_light(app, "unknown")
    set_linux_help_form_from_entry(app, None)
    update_linux_help_notes(app, None)

    if commands:
        first_id = commands[0].get("id", "")
        if tree is not None:
            tree.selection_set(first_id)
            tree.focus(first_id)
        elif listbox is not None:
            listbox.selection_clear(0, "end")
            listbox.selection_set(0)
            listbox.activate(0)
        on_linux_help_select(app)


def on_linux_help_select(app, _event=None):
    command_id = _selected_linux_help_id(app)
    if not command_id:
        return
    item = _resolve_linux_help_item(app, command_id)
    if not item:
        return

    app.linux_help_selected_id = command_id
    risk = str(item.get("risk") or "").strip().lower()
    risk_label, _fill = RISK_UI.get(risk, RISK_UI["unknown"])

    _app_var_set(app, "linux_help_detail_name_var", item.get("name") or "–")
    _app_var_set(app, "linux_help_detail_category_var", item.get("category") or "–")
    _app_var_set(app, "linux_help_command_var", item.get("cmd") or "–")
    _app_var_set(
        app,
        "linux_help_desc_var",
        item.get("info")
        or app.tr("linux_help_no_description", "Keine Beschreibung vorhanden."),
    )
    _app_var_set(
        app,
        "linux_help_detail_syntax_var",
        item.get("syntax") or item.get("cmd") or "–",
    )
    _app_var_set(
        app,
        "linux_help_detail_example_var",
        item.get("example") or item.get("cmd") or "–",
    )
    _app_var_set(
        app,
        "linux_help_detail_root_var",
        (
            app.tr("label_yes", "Ja")
            if item.get("root_required")
            else app.tr("label_no", "Nein")
        ),
    )
    _app_var_set(app, "linux_help_detail_tags_var", item.get("tags") or "–")
    _app_var_set(app, "linux_help_risk_var", risk_label)
    _app_var_set(app, "linux_help_risk_badge_var", risk_label)
    set_linux_help_risk_light(app, risk)
    set_linux_help_form_from_entry(app, item)
    update_linux_help_notes(app, item)


def linux_help_apply_form_to_entry(app, mark_dirty=True):
    target = get_linux_help_command_by_id(app, app.linux_help_selected_id)
    if target is None or _app_value(app, "linux_help_form_category_var") is None:
        return False
    target["category"] = (
        str(
            _app_var_get(app, "linux_help_form_category_var", "Allgemein")
            or "Allgemein"
        ).strip()
        or "Allgemein"
    )
    target["name"] = (
        str(_app_var_get(app, "linux_help_form_name_var", "") or "").strip()
        or target["name"]
    )
    target["info"] = str(
        _app_var_get(app, "linux_help_form_info_var", "") or ""
    ).strip()
    target["cmd"] = str(_app_var_get(app, "linux_help_form_cmd_var", "") or "").strip()
    target["explanation"] = str(
        _app_var_get(app, "linux_help_form_explanation_var", "") or ""
    ).strip()
    target["warning_text"] = str(
        _app_var_get(app, "linux_help_form_warning_var", "") or ""
    ).strip()
    manual_risk = (
        str(_app_var_get(app, "linux_help_form_risk_var", "") or "").strip().lower()
    )
    target["risk"] = (
        manual_risk
        if manual_risk in {"safe", "caution", "danger"}
        else linux_help_get_risk_level(target.get("cmd", ""))
    )
    target["enabled"] = bool(_app_var_get(app, "linux_help_form_enabled_var", False))
    normalized = normalize_linux_help_entry(
        app,
        target,
        existing_ids={item["id"] for item in app.linux_help_data if item is not target},
    )
    target.update(normalized)
    rebuild_linux_help_indexes(app)
    sync_linux_help_form_categories(app)
    refresh_linux_help_list(app, category=target.get("category"))
    if mark_dirty:
        set_linux_help_dirty(app, True)
    return True


def linux_help_new_entry(app):
    base = {
        "category": app.linux_help_category_var.get() or "Allgemein",
        "name": "Neuer Befehl",
        "info": "Neue Kurzbeschreibung",
        "cmd": "",
        "syntax": "",
        "example": "",
        "tags": "",
        "root_required": False,
        "explanation": "",
        "warning_text": "",
        "risk": "caution",
        "enabled": True,
    }
    open_linux_help_entry_dialog(app, item=base, is_new=True)


def linux_help_edit_selected(app):
    if not app.linux_help_selected_id:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_select_entry_first",
                "Linux Hilfe: Bitte zuerst einen Eintrag auswählen.",
            )
        )
        return
    target = get_linux_help_command_by_id(app, app.linux_help_selected_id)
    if target is None:
        return
    open_linux_help_entry_dialog(app, item=target, is_new=False)


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
    if messagebox is not None:
        confirmed = messagebox.askyesno(
            app.tr("linux_help_delete_title", "Eintrag löschen"),
            app.tr(
                "linux_help_delete_confirm",
                "Soll der ausgewählte Linux-Befehl wirklich gelöscht werden?",
            ),
            parent=app,
        )
        if not confirmed:
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
    save_linux_help_data(app, update_status=False)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_entry_deleted",
            "Linux Hilfe: Eintrag gelöscht.",
        )
    )


def open_linux_help_entry_dialog(app, item=None, is_new=False):
    existing = getattr(app, "linux_help_entry_dialog", None)
    if existing is not None and existing.winfo_exists():
        try:
            existing.destroy()
        except Exception:
            pass

    base = dict(item or {})
    dialog = tk.Toplevel(app)
    dialog.title(
        app.tr("linux_help_dialog_title_new", "Linux-Befehl anlegen")
        if is_new
        else app.tr("linux_help_dialog_title_edit", "Linux-Befehl bearbeiten")
    )
    dialog.transient(app)
    dialog.resizable(True, True)
    dialog.minsize(760, 560)
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)
    app.linux_help_entry_dialog = dialog

    category_var = tk.StringVar(value=base.get("category") or "Allgemein")
    name_var = tk.StringVar(value=base.get("name") or "")
    info_var = tk.StringVar(value=base.get("info") or "")
    cmd_var = tk.StringVar(value=base.get("cmd") or "")
    syntax_var = tk.StringVar(value=base.get("syntax") or base.get("cmd") or "")
    example_var = tk.StringVar(value=base.get("example") or "")
    tags_var = tk.StringVar(value=base.get("tags") or "")
    risk_var = tk.StringVar(value=_risk_storage_to_dialog_label(base.get("risk")))
    root_var = tk.BooleanVar(value=bool(base.get("root_required")))
    enabled_var = tk.BooleanVar(value=bool(base.get("enabled", True)))

    shell = ttk.Frame(dialog, padding=12)
    shell.grid(row=0, column=0, sticky="nsew")
    shell.columnconfigure(0, weight=1)
    shell.rowconfigure(1, weight=1)

    form = ttk.LabelFrame(
        shell,
        text=app.tr("linux_help_dialog_group", "Eintrag bearbeiten"),
        padding=10,
    )
    form.grid(row=0, column=0, sticky="ew")
    form.columnconfigure(1, weight=1)
    form.columnconfigure(3, weight=1)

    ttk.Label(form, text=app.tr("label_category", "Kategorie")).grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    category_combo = ttk.Combobox(
        form,
        textvariable=category_var,
        values=[value for value in get_linux_help_categories(app) if value],
    )
    category_combo.grid(row=0, column=1, sticky="ew", pady=(0, 6))

    ttk.Label(form, text=app.tr("linux_help_label_command_name", "Befehl")).grid(
        row=0, column=2, sticky="w", padx=(12, 8), pady=(0, 6)
    )
    ttk.Entry(form, textvariable=name_var).grid(
        row=0, column=3, sticky="ew", pady=(0, 6)
    )

    ttk.Label(form, text=app.tr("linux_help_label_description", "Beschreibung")).grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    ttk.Entry(form, textvariable=info_var).grid(
        row=1, column=1, columnspan=3, sticky="ew", pady=(0, 6)
    )

    ttk.Label(form, text=app.tr("linux_help_col_command", "Befehl")).grid(
        row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    ttk.Entry(form, textvariable=cmd_var).grid(
        row=2, column=1, columnspan=3, sticky="ew", pady=(0, 6)
    )

    ttk.Label(form, text=app.tr("linux_help_label_syntax", "Syntax")).grid(
        row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    ttk.Entry(form, textvariable=syntax_var).grid(
        row=3, column=1, columnspan=3, sticky="ew", pady=(0, 6)
    )

    ttk.Label(form, text=app.tr("linux_help_label_example", "Beispiel")).grid(
        row=4, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    ttk.Entry(form, textvariable=example_var).grid(
        row=4, column=1, columnspan=3, sticky="ew", pady=(0, 6)
    )

    ttk.Label(form, text=app.tr("linux_help_label_tags", "Tags")).grid(
        row=5, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    ttk.Entry(form, textvariable=tags_var).grid(
        row=5, column=1, sticky="ew", pady=(0, 6)
    )

    ttk.Label(form, text=app.tr("linux_help_label_risk_filter", "Risiko")).grid(
        row=5, column=2, sticky="w", padx=(12, 8), pady=(0, 6)
    )
    ttk.Combobox(
        form,
        textvariable=risk_var,
        values=[label for label, _key in RISK_DIALOG_CHOICES],
        state="readonly",
    ).grid(row=5, column=3, sticky="ew", pady=(0, 6))

    flags_row = ttk.Frame(form)
    flags_row.grid(row=6, column=0, columnspan=4, sticky="w", pady=(2, 0))
    ttk.Checkbutton(
        flags_row,
        text=app.tr("linux_help_label_root_required", "Root nötig"),
        variable=root_var,
    ).pack(side="left")
    ttk.Checkbutton(
        flags_row,
        text=app.tr("label_enabled", "Aktiv"),
        variable=enabled_var,
    ).pack(side="left", padx=(14, 0))

    editors = ttk.Frame(shell)
    editors.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    editors.columnconfigure(0, weight=1)
    editors.columnconfigure(1, weight=1)
    editors.rowconfigure(0, weight=1)

    explanation_frame = ttk.LabelFrame(
        editors,
        text=app.tr("linux_help_label_explanation_text", "Erklärung"),
        padding=8,
    )
    explanation_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    explanation_frame.columnconfigure(0, weight=1)
    explanation_frame.rowconfigure(0, weight=1)
    explanation_text = tk.Text(explanation_frame, wrap="word", height=10)
    explanation_text.grid(row=0, column=0, sticky="nsew")
    explanation_text.insert("1.0", base.get("explanation") or "")

    warning_frame = ttk.LabelFrame(
        editors,
        text=app.tr("linux_help_label_warning_text", "Hinweis"),
        padding=8,
    )
    warning_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    warning_frame.columnconfigure(0, weight=1)
    warning_frame.rowconfigure(0, weight=1)
    warning_text = tk.Text(warning_frame, wrap="word", height=10)
    warning_text.grid(row=0, column=0, sticky="nsew")
    warning_text.insert("1.0", base.get("warning_text") or "")

    buttons = ttk.Frame(shell)
    buttons.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    buttons.columnconfigure(0, weight=1)

    def _close_dialog():
        app.__dict__.pop("linux_help_entry_dialog", None)
        try:
            dialog.destroy()
        except Exception:
            pass

    def _save_dialog():
        raw = {
            "id": base.get("id", ""),
            "category": (category_var.get() or "").strip() or "Allgemein",
            "name": (name_var.get() or "").strip(),
            "info": (info_var.get() or "").strip(),
            "cmd": (cmd_var.get() or "").strip(),
            "syntax": (syntax_var.get() or "").strip(),
            "example": (example_var.get() or "").strip(),
            "tags": (tags_var.get() or "").strip(),
            "risk": _risk_dialog_label_to_storage(risk_var.get()),
            "root_required": bool(root_var.get()),
            "enabled": bool(enabled_var.get()),
            "explanation": explanation_text.get("1.0", "end").strip(),
            "warning_text": warning_text.get("1.0", "end").strip(),
        }
        if not raw["name"] or not raw["cmd"]:
            if messagebox is not None:
                messagebox.showwarning(
                    app.tr(
                        "linux_help_dialog_validation_title", "Eingabe unvollständig"
                    ),
                    app.tr(
                        "linux_help_dialog_validation_body",
                        "Bitte mindestens Name und Befehl ausfüllen.",
                    ),
                    parent=dialog,
                )
            return
        target = (
            None if is_new else get_linux_help_command_by_id(app, base.get("id", ""))
        )
        existing_ids = {
            item.get("id")
            for item in app.linux_help_data
            if item is not target and item.get("id")
        }
        normalized = normalize_linux_help_entry(app, raw, existing_ids=existing_ids)
        if target is None:
            app.linux_help_data.append(normalized)
        else:
            target.clear()
            target.update(normalized)
        rebuild_linux_help_indexes(app)
        sync_linux_help_form_categories(app)
        app.linux_help_category_var.set("Alle Kategorien")
        refresh_linux_help_list(app)
        if hasattr(app, "linux_help_tree") and app.linux_help_tree is not None:
            try:
                app.linux_help_tree.selection_set(normalized["id"])
                app.linux_help_tree.focus(normalized["id"])
            except Exception:
                pass
        app.linux_help_selected_id = normalized["id"]
        on_linux_help_select(app)
        set_linux_help_dirty(app, True)
        save_linux_help_data(app, update_status=False)
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_entry_saved",
                "Linux Hilfe: Eintrag gespeichert.",
            )
        )
        _close_dialog()

    ttk.Button(
        buttons,
        text=app.tr("btn_cancel", "Abbrechen"),
        command=_close_dialog,
    ).pack(side="right")
    ttk.Button(
        buttons,
        text=app.tr("btn_save", "Speichern"),
        command=_save_dialog,
    ).pack(side="right", padx=(0, 8))

    dialog.protocol("WM_DELETE_WINDOW", _close_dialog)
    try:
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.focus_force()
    except Exception:
        pass


def copy_linux_help_chad_prompt(app):
    item, _title, prompt = _selected_linux_help_chad_payload(app)
    if item is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_no_command_selected",
                "Linux Hilfe: Kein Befehl ausgewählt.",
            )
        )
        return False
    app.clipboard_clear()
    app.clipboard_append(prompt)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_prompt_copied",
            "Linux Hilfe: Chad-Prompt wurde in die Zwischenablage kopiert.",
        )
    )
    return True


def send_linux_help_to_chad(app):
    item, title, prompt = _selected_linux_help_chad_payload(app)
    if item is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_no_command_selected",
                "Linux Hilfe: Kein Befehl ausgewählt.",
            )
        )
        return False
    if not _set_chad_direct_prompt_safe(app, title, prompt):
        app.chad_analysis_current_prompt = prompt
        app.chad_online_result = ""
        try:
            app.chad_analysis_source_var.set(
                f"{app.tr('chad_label_source_prefix', 'Quelle')}: {title}"
            )
            app.chad_analysis_status_var.set(
                app.tr("chad_status_analysis_prepared", "Analyse vorbereitet.")
            )
        except Exception:
            pass
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_sent_to_chad",
            "Linux Hilfe: Befehl wurde an Chad zur Erklärung übergeben.",
        )
    )
    return True


def show_linux_help_tree_menu(app, event):
    tree = getattr(app, "linux_help_tree", None)
    if tree is None:
        return
    try:
        row_id = tree.identify_row(event.y)
    except Exception:
        row_id = ""
    if row_id:
        try:
            tree.selection_set(row_id)
            tree.focus(row_id)
        except Exception:
            pass
        on_linux_help_select(app)
    item = _get_selected_linux_help_item(app)
    if item is None:
        return
    menu = tk.Menu(app, tearoff=0)
    menu.add_command(
        label=app.tr("linux_help_menu_send_chad", "An Chad senden"),
        command=lambda: send_linux_help_to_chad(app),
    )
    menu.add_command(
        label=app.tr("linux_help_menu_copy_prompt", "Als Prompt kopieren"),
        command=lambda: copy_linux_help_chad_prompt(app),
    )
    menu.add_separator()
    menu.add_command(
        label=app.tr("btn_edit", "Bearbeiten"),
        command=app.linux_help_edit_selected,
    )
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        try:
            menu.grab_release()
        except Exception:
            pass


def linux_help_import_csv_dialog(app):
    if filedialog is None:
        return
    path = filedialog.askopenfilename(
        parent=app,
        title=app.tr(
            "linux_help_import_csv_title", "Linux-Befehlsdatenbank importieren"
        ),
        filetypes=[
            (app.tr("filetype_data", "Datenbanken"), "*.csv *.xlsx"),
            (app.tr("filetype_csv", "CSV-Dateien"), "*.csv"),
            (app.tr("filetype_excel", "Excel-Dateien"), "*.xlsx"),
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
        app.linux_help_category_var.set("Alle Kategorien")
        app.linux_help_risk_filter_var.set("Alle Risiken")
        refresh_linux_help_list(app)
        save_linux_help_data(app, update_status=False)
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_imported_count",
                "Linux Hilfe: {count} Einträge importiert.",
            ).format(count=len(commands))
        )
    except Exception as exc:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_import_failed",
                "Linux Hilfe: Import fehlgeschlagen.",
            )
        )
        update_linux_help_notes(app, None, extra_error=str(exc))


def linux_help_export_csv_dialog(app):
    if filedialog is None:
        return
    path = filedialog.asksaveasfilename(
        parent=app,
        title=app.tr("linux_help_export_csv_title", "Linux-Datenbank exportieren"),
        defaultextension=".csv",
        filetypes=[
            (app.tr("filetype_csv", "CSV-Dateien"), "*.csv"),
            (app.tr("filetype_all", "Alle Dateien"), "*.*"),
        ],
        initialfile="linux_befehlsdatenbank_export.csv",
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
        sync_linux_help_form_categories(app)
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_load_failed",
                "Linux Hilfe: Daten konnten nicht geladen werden.",
            )
        )
        update_linux_help_notes(app, None, extra_error=str(exc))
        return

    sync_linux_help_form_categories(app)
    app.linux_help_category_var.set("Alle Kategorien")
    app.linux_help_risk_filter_var.set("Alle Risiken")
    refresh_linux_help_list(app)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_loaded_count",
            "Linux Hilfe: {count} Einträge geladen.",
        ).format(count=len(commands))
    )


def send_linux_help_command_to_terminal(app):
    item = _resolve_linux_help_item(app, app.linux_help_selected_id)
    if item is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_no_command_selected",
                "Linux Hilfe: Kein Befehl ausgewählt.",
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
        return False

    risk = str(item.get("risk") or "").strip().lower()
    requires_confirmation = bool(item.get("root_required")) or risk in {
        "caution",
        "danger",
    }
    if requires_confirmation and messagebox is not None:
        confirmed = messagebox.askyesno(
            app.tr("linux_help_confirm_send_title", "Befehl an Terminal senden"),
            app.tr(
                "linux_help_confirm_send_prompt",
                "Dieser Befehl verändert möglicherweise Systemzustände.\n\nTrotzdem ins Terminal senden?",
            ),
            parent=app,
        )
        if not confirmed:
            app.linux_help_status_var.set(
                app.tr(
                    "linux_help_status_terminal_cancelled",
                    "Linux Hilfe: Versand an Terminal abgebrochen.",
                )
            )
            return False

    terminal_name = app._open_command_in_external_terminal(cmd)
    if not terminal_name:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_terminal_failed",
                "Linux Hilfe: Terminal konnte nicht gestartet werden.",
            )
        )
        return False

    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_sent_to_terminal",
            "Linux Hilfe: Befehl wurde an ein externes Terminal gesendet.",
        )
    )
    if hasattr(app, "log"):
        try:
            app.log(
                app.tr(
                    "linux_help_log_command_sent",
                    "Linux-Hilfe: Befehl an Terminal gesendet",
                )
            )
        except Exception:
            pass
    if hasattr(app, "linux_help_text") and app.linux_help_text is not None:
        if hasattr(app.linux_help_text, "configure"):
            app.linux_help_text.configure(state="normal")
        app.linux_help_text.delete("1.0", "end")
        app.linux_help_text.insert(
            "1.0",
            "\n".join(
                [
                    f"{app.tr('linux_help_label_name', 'Name')}: {item.get('name') or '–'}",
                    f"{app.tr('linux_help_label_command_name', 'Befehl')}: {cmd}",
                    f"Terminal: {terminal_name}",
                    "",
                    app.tr(
                        "linux_help_terminal_note_sent",
                        "Der Befehl wurde an ein externes Terminal übergeben.",
                    ),
                ]
            ),
        )
        if hasattr(app.linux_help_text, "configure"):
            app.linux_help_text.configure(state="disabled")
    return True
