"""Linux command database controller helpers for NetMon."""

from __future__ import annotations

import csv
import io
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
    from netmon.core.docx_archive import open_validated_xlsx
    from netmon.core.import_limits import ImportLimitError, read_bounded_text
    from netmon.services.linux_help_reading_service import ReadingState
except ModuleNotFoundError:
    from core.utils import safe_write_json
    from core.docx_archive import open_validated_xlsx
    from core.import_limits import ImportLimitError, read_bounded_text
    from services.linux_help_reading_service import ReadingState

# Bounds for user-selected CSV/XLSX command databases (shipped DB: ~180 KiB,
# ~700 rows). XLSX archive bounds come from docx_archive (OOXML validator).
MAX_SOURCE_CSV_BYTES = 8 * 1024 * 1024
MAX_SOURCE_ROWS = 20_000
MAX_SOURCE_COLUMNS = 64
MAX_SOURCE_CELL_CHARS = 64 * 1024
MAX_SOURCE_CELLS = 200_000
MAX_SOURCE_TEXT_CHARS = 8 * 1024 * 1024

try:
    from netmon.services.linux_help_library_service import (
        delete_linux_help_document,
        get_linux_help_document_by_id,
        inspect_markdown_import,
        save_linux_help_markdown,
        read_linux_help_markdown,
        load_linux_help_markdown,
        list_linux_help_documents,
    )
    from netmon.services.linux_help_library_markdown import (
        split_markdown,
        format_entry_markdown,
    )
    from netmon.services.linux_help_prompt_service import (
        build_linux_help_markdown_prompt,
    )
except ModuleNotFoundError:
    from services.linux_help_library_service import (
        delete_linux_help_document,
        get_linux_help_document_by_id,
        inspect_markdown_import,
        save_linux_help_markdown,
        read_linux_help_markdown,
        load_linux_help_markdown,
        list_linux_help_documents,
    )
    from services.linux_help_library_markdown import (
        split_markdown,
        format_entry_markdown,
    )
    from services.linux_help_prompt_service import build_linux_help_markdown_prompt


NETMON_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RISK_UI = {
    "safe": ("linux_help_risk_safe", "🟢 Safe", "green"),
    "caution": ("linux_help_risk_caution", "🟡 Admin", "#d8a106"),
    "danger": ("linux_help_risk_danger", "🔴 Dangerous", "red"),
    "unknown": ("linux_help_risk_unknown_label", "⚪ Unknown", "gray"),
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
    ("linux_help_risk_safe", "🟢 Safe", "safe"),
    ("linux_help_risk_caution", "🟡 Admin", "caution"),
    ("linux_help_risk_danger", "🔴 Dangerous", "danger"),
)


def _tr(app, key: str, fallback: str) -> str:
    translate = getattr(app, "tr", None)
    if callable(translate):
        try:
            return str(translate(key, fallback))
        except Exception:
            return fallback
    return fallback


def _linux_help_all_categories_label(app) -> str:
    return _tr(app, "linux_help_all_categories", "All categories")


def _linux_help_all_sources_label(app) -> str:
    return _tr(app, "linux_help_source_both", "Both")


def _linux_help_all_risks_label(app) -> str:
    return _tr(app, "linux_help_all_risks", "All risks")


def _risk_label(app, risk_key: str) -> str:
    key, fallback, _color = RISK_UI.get(risk_key, RISK_UI["unknown"])
    return _tr(app, key, fallback)


def _source_label(app, source_key: str) -> str:
    mapping = {
        "command": ("linux_help_source_commands", "Commands"),
        "glossary": ("linux_help_source_glossary", "Glossary"),
    }
    key, fallback = mapping.get(source_key, ("linux_help_source_unknown", "Unknown"))
    return _tr(app, key, fallback)


def _risk_dialog_choices_for_app(app):
    return [
        (_tr(app, key, fallback), risk_key)
        for key, fallback, risk_key in RISK_DIALOG_CHOICES
    ]


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
        os.path.join(NETMON_REPO_ROOT, "tools", "netmon-linux-befehlsdatenbank-v1.csv"),
        os.path.join(NETMON_REPO_ROOT, "netmon", "linux-befehle.csv"),
        os.path.join(NETMON_REPO_ROOT, "netmon", "linux-befehle.xlsx"),
        os.path.join(
            NETMON_REPO_ROOT, "netmon", "netmon-linux-befehlsdatenbank-v1.csv"
        ),
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
    used = existing_ids if isinstance(existing_ids, set) else set(existing_ids or [])
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


def _glossary_category(item) -> str:
    tags = item.get("tags")
    if isinstance(tags, (list, tuple, set)):
        tag_values = [str(tag).strip() for tag in tags if str(tag).strip()]
    else:
        tag_values = [
            part.strip() for part in re.split(r"[;,|]", str(tags or "")) if part.strip()
        ]
    if tag_values:
        return tag_values[0].title()
    return "Glossary"


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


def _risk_storage_to_dialog_label(app, value):
    normalized = _normalize_risk_value(value)
    for label, key in _risk_dialog_choices_for_app(app):
        if key == normalized:
            return label
    return _risk_dialog_choices_for_app(app)[1][0]


def _risk_dialog_label_to_storage(app, value):
    label = str(value or "").strip()
    for option_label, key in _risk_dialog_choices_for_app(app):
        if label == option_label:
            return key
    return _normalize_risk_value(value) or "caution"


def _selected_linux_help_id(app) -> str:
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
    command_id = str(_app_value(app, "linux_help_selected_id", "") or "").strip()
    if command_id:
        return command_id
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
    direct_prompt_setter = getattr(app, "set_chad_direct_prompt", None)
    if callable(direct_prompt_setter):
        direct_prompt_setter(title, prompt)
        return True
    return False


def _get_selected_linux_help_item(app):
    return _resolve_linux_help_item(app)


def _is_glossary_item(item) -> bool:
    return str((item or {}).get("entry_type") or "").strip().lower() == "glossary"


def _linux_help_source_value(app):
    label = str(_app_var_get(app, "linux_help_source_var", "") or "").strip()
    return {
        _tr(app, "linux_help_source_commands", "Commands"): "command",
        _tr(app, "linux_help_source_glossary", "Glossary"): "glossary",
        _tr(app, "linux_help_source_both", "Both"): "both",
    }.get(label, "both")


def _linux_help_chad_title(app, item) -> str:
    entry = dict(item or {})
    if _is_glossary_item(entry):
        return _tr(
            app,
            "linux_help_chad_title_glossary",
            "Explain glossary term: {name}",
        ).format(name=entry.get("name") or "Unknown")
    return _tr(
        app,
        "linux_help_chad_title_command",
        "Explain Linux command: {name}",
    ).format(name=entry.get("name") or entry.get("cmd") or "Unknown")


def build_linux_help_chad_prompt(app, item):
    entry = dict(item or {})
    if _is_glossary_item(entry):
        lines = [
            _tr(
                app,
                "linux_help_prompt_glossary_intro",
                "Please explain the following IT/Linux glossary term for beginners in clear, well-structured English.",
            ),
            "",
            _tr(
                app,
                "linux_help_prompt_requirements",
                "Important requirements for your answer:",
            ),
            _tr(
                app,
                "linux_help_prompt_glossary_req_1",
                "- Start with a simple definition.",
            ),
            _tr(
                app,
                "linux_help_prompt_glossary_req_2",
                "- Explain why the term matters in Linux or IT practice.",
            ),
            _tr(
                app,
                "linux_help_prompt_glossary_req_3",
                "- Use the stored example and expand it in plain language.",
            ),
            _tr(
                app,
                "linux_help_prompt_glossary_req_4",
                "- Mention 2 or 3 related concepts beginners should learn next.",
            ),
            "",
            _tr(
                app,
                "linux_help_prompt_glossary_data_header",
                "Glossary data from NetMon:",
            ),
            _tr(app, "linux_help_prompt_glossary_term", "Term: {value}").format(
                value=entry.get("name") or "–"
            ),
            _tr(app, "linux_help_prompt_category", "Category: {value}").format(
                value=entry.get("category") or "–"
            ),
            _tr(
                app,
                "linux_help_prompt_short_description",
                "Short description: {value}",
            ).format(value=entry.get("info") or "–"),
            _tr(app, "linux_help_prompt_example", "Example: {value}").format(
                value=entry.get("example") or "–"
            ),
            _tr(app, "linux_help_prompt_tags", "Tags: {value}").format(
                value=str(entry.get("tags") or "–").strip() or "–"
            ),
            _tr(
                app,
                "linux_help_prompt_glossary_related_terms",
                "Related terms: {value}",
            ).format(value=str(entry.get("related") or "–").strip() or "–"),
        ]
        return "\n".join(lines).strip()
    _risk_key, risk_label, _fill = RISK_UI.get(
        str(entry.get("risk") or "").strip().lower(),
        RISK_UI["unknown"],
    )
    root_text = (
        app.tr("label_yes", "Yes")
        if entry.get("root_required")
        else app.tr("label_no", "No")
    )
    tags = str(entry.get("tags") or "–").strip() or "–"
    explanation = str(entry.get("explanation") or "").strip() or _tr(
        app,
        "linux_help_prompt_no_additional_explanation",
        "No additional explanation stored.",
    )
    warning_text = str(entry.get("warning_text") or "").strip() or _tr(
        app,
        "linux_help_prompt_no_additional_warning",
        "No additional warning stored.",
    )
    lines = [
        _tr(
            app,
            "linux_help_prompt_command_intro",
            "Please explain the following Linux command for beginners in clear, well-structured English.",
        ),
        "",
        _tr(
            app,
            "linux_help_prompt_requirements",
            "Important requirements for your answer:",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_1",
            "- Write in a beginner-friendly way without assuming prior knowledge.",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_2",
            "- Start with a short explanation of what the command is used for.",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_3",
            "- Then break down the syntax and the most important parts.",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_4",
            "- Explain the example step by step.",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_5",
            "- Mention typical real-world use cases.",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_6",
            "- Clearly point out risks, root requirements, and common mistakes.",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_7",
            "- End with 3 safe beginner tips or variants.",
        ),
        _tr(
            app,
            "linux_help_prompt_command_req_8",
            "- Use calm, clear language instead of unnecessary jargon.",
        ),
        "",
        _tr(
            app,
            "linux_help_prompt_command_data_header",
            "Command data from NetMon:",
        ),
        _tr(app, "linux_help_prompt_command_name", "Command name: {value}").format(
            value=entry.get("name") or entry.get("cmd") or "–"
        ),
        _tr(app, "linux_help_prompt_category", "Category: {value}").format(
            value=entry.get("category") or "–"
        ),
        _tr(app, "linux_help_prompt_command", "Command: {value}").format(
            value=entry.get("cmd") or "–"
        ),
        _tr(
            app,
            "linux_help_prompt_short_description",
            "Short description: {value}",
        ).format(value=entry.get("info") or "–"),
        _tr(app, "linux_help_prompt_syntax", "Syntax: {value}").format(
            value=entry.get("syntax") or entry.get("cmd") or "–"
        ),
        _tr(app, "linux_help_prompt_example", "Example: {value}").format(
            value=entry.get("example") or entry.get("cmd") or "–"
        ),
        _tr(
            app,
            "linux_help_prompt_database_explanation",
            "Database explanation/note: {value}",
        ).format(value=explanation),
        _tr(
            app,
            "linux_help_prompt_additional_warning",
            "Additional warning: {value}",
        ).format(value=warning_text),
        _tr(app, "linux_help_prompt_root_required", "Root required: {value}").format(
            value=root_text
        ),
        _tr(app, "linux_help_prompt_risk_level", "Risk level: {value}").format(
            value=risk_label
        ),
        _tr(app, "linux_help_prompt_tags", "Tags: {value}").format(value=tags),
    ]
    return "\n".join(lines).strip()


def _selected_linux_help_chad_payload(app):
    item = _get_selected_linux_help_item(app)
    if item is None:
        return None, "", ""
    prompt = build_linux_help_chad_prompt(app, item)
    return item, _linux_help_chad_title(app, item), prompt


def _check_source_row(row, count):
    if count > MAX_SOURCE_ROWS + 1:
        raise ImportLimitError(f"Import: mehr als {MAX_SOURCE_ROWS} Zeilen.")
    if len(row) > MAX_SOURCE_COLUMNS:
        raise ImportLimitError(f"Import: mehr als {MAX_SOURCE_COLUMNS} Spalten.")
    for cell in row:
        if isinstance(cell, str) and len(cell) > MAX_SOURCE_CELL_CHARS:
            raise ImportLimitError("Import: Zelle überschreitet die Längengrenze.")
    return row


class _SourceBudget:
    def __init__(self):
        self.rows = self.cells = self.text = 0

    def check(self, row):
        self.rows += 1
        _check_source_row(row, self.rows)
        self.cells += len(row)
        self.text += sum(len(str(cell)) for cell in row if cell is not None)
        if self.cells > MAX_SOURCE_CELLS:
            raise ImportLimitError("Import: Gesamtgrenze fuer Zellen ueberschritten.")
        if self.text > MAX_SOURCE_TEXT_CHARS:
            raise ImportLimitError("Import: Gesamtgrenze fuer Text ueberschritten.")
        return row


def _iter_xlsx_rows(path):
    if load_workbook is None:
        raise RuntimeError("XLSX import requires openpyxl.")
    budget = _SourceBudget()
    with open_validated_xlsx(path) as snapshot:
        workbook = load_workbook(
            snapshot, read_only=True, data_only=True, keep_links=False
        )
        try:
            sheet = workbook.active
            if sheet.max_column and sheet.max_column > MAX_SOURCE_COLUMNS:
                raise ImportLimitError("Import: zu viele Spalten.")
            if sheet.max_row and sheet.max_row > MAX_SOURCE_ROWS + 1:
                raise ImportLimitError("Import: zu viele Zeilen.")
            for row in sheet.iter_rows(max_col=MAX_SOURCE_COLUMNS, values_only=True):
                yield budget.check(tuple(row))
        finally:
            workbook.close()


def _iter_csv_rows(path):
    text = read_bounded_text(
        path, MAX_SOURCE_CSV_BYTES, label="CSV-Import", encoding="utf-8-sig"
    )
    budget = _SourceBudget()
    for row in csv.reader(io.StringIO(text, newline="")):
        yield budget.check(row)


def _iter_source_rows(path):
    extension = os.path.splitext(str(path or ""))[1].lower()
    rows = iter(_iter_xlsx_rows(path) if extension == ".xlsx" else _iter_csv_rows(path))
    try:
        headers = [str(cell or "").strip() for cell in next(rows)]
    except StopIteration:
        return
    for row in rows:
        if extension == ".xlsx":
            if any(row):
                yield dict(zip(headers, row))
        elif row:
            # Same short-row shape as csv.DictReader.
            yield dict(zip(headers, list(row) + [None] * (len(headers) - len(row))))


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
        "entry_type": "command",
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
    if isinstance(item.get("markdown_id"), str):
        normalized["markdown_id"] = item["markdown_id"]
    return normalized


def normalize_linux_help_glossary_entry(app, raw, existing_ids=None):
    item = dict(raw or {})
    term = str(item.get("term") or item.get("name") or "").strip() or "Glossary entry"
    short = str(item.get("short") or item.get("info") or "").strip()
    explanation = str(item.get("explanation") or short).strip()
    warning_text = str(item.get("warning_text") or "").strip()
    related = item.get("related") or []
    related_text = (
        linux_help_tag_text(related)
        if isinstance(related, (list, tuple, set))
        else linux_help_tag_text(str(related or ""))
    )
    normalized = {
        "id": linux_help_make_id(
            {"id": item.get("id") or term, "name": term}, existing_ids=existing_ids
        ),
        "entry_type": "glossary",
        "category": str(item.get("category") or "").strip() or _glossary_category(item),
        "name": term,
        "info": short,
        "cmd": "",
        "syntax": "",
        "example": str(item.get("example") or "").strip(),
        "explanation": explanation,
        "warning_text": warning_text,
        "tags": linux_help_tag_text(item.get("tags")),
        "risk": "unknown",
        "root_required": False,
        "enabled": _bool_from_raw(item.get("enabled"), default=True),
        "related": related_text,
    }

    if isinstance(item.get("markdown_id"), str):
        normalized["markdown_id"] = item["markdown_id"]
    return normalized


def _serialize_linux_help_glossary_entry(item):
    entry = dict(item or {})
    serialized = {
        "id": str(entry.get("id") or "").strip(),
        "term": str(entry.get("name") or entry.get("term") or "").strip(),
        "short": str(entry.get("info") or entry.get("short") or "").strip(),
        "example": str(entry.get("example") or "").strip(),
        "tags": [
            part.strip()
            for part in str(entry.get("tags") or "").split(",")
            if part.strip()
        ],
        "related": [
            part.strip()
            for part in str(entry.get("related") or "").split(",")
            if part.strip()
        ],
        "explanation": str(entry.get("explanation") or "").strip(),
        "warning_text": str(entry.get("warning_text") or "").strip(),
        "enabled": bool(entry.get("enabled", True)),
        "category": str(entry.get("category") or "").strip(),
    }

    if entry.get("markdown_id"):
        serialized["markdown_id"] = entry["markdown_id"]
    return serialized


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
    glossary_categories = set(
        (_app_value(app, "linux_help_glossary_by_category", {}) or {}).keys()
    )
    app.linux_help_combined_categories = sorted(
        set(categories).union(glossary_categories),
        key=str.lower,
    )


def rebuild_linux_help_glossary_indexes(app):
    glossary_entries = list(_app_value(app, "linux_help_glossary", []) or [])
    glossary_entries.sort(
        key=lambda item: (
            item.get("category", "").lower(),
            item.get("name", "").lower(),
        )
    )
    categories = sorted(
        {item.get("category", "Glossary") for item in glossary_entries},
        key=str.lower,
    )
    glossary_by_category = {category: [] for category in categories}
    for item in glossary_entries:
        glossary_by_category.setdefault(item["category"], []).append(item)
    app.linux_help_glossary = glossary_entries
    app.linux_help_glossary_by_category = glossary_by_category
    app.linux_help_combined_categories = sorted(
        set(_app_value(app, "linux_help_categories", []) or []).union(categories),
        key=str.lower,
    )


def load_linux_help_glossary(app):
    path = str(_app_value(app, "linux_help_glossary_path", "") or "").strip()
    seed_path = str(_app_value(app, "linux_help_glossary_seed_path", "") or "").strip()
    source_path = path if path and os.path.isfile(path) else seed_path
    if not source_path or not os.path.isfile(source_path):
        app.linux_help_glossary = []
        app.linux_help_glossary_by_category = {}
        app.linux_help_combined_categories = list(
            _app_value(app, "linux_help_categories", []) or []
        )
        return []
    with open(source_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    entries = payload.get("entries") if isinstance(payload, dict) else []
    seen_ids = set(
        item.get("id") for item in (_app_value(app, "linux_help_data", []) or [])
    )
    glossary = []
    for raw in entries if isinstance(entries, list) else []:
        normalized = normalize_linux_help_glossary_entry(
            app, raw, existing_ids=seen_ids
        )
        seen_ids.add(normalized["id"])
        glossary.append(normalized)
    app.linux_help_glossary = glossary
    rebuild_linux_help_glossary_indexes(app)
    if source_path == seed_path and path:
        save_linux_help_glossary(app, update_status=False)
    return glossary


def save_linux_help_glossary(app, update_status=True):
    payload = {
        "name": "IT-Lexikon fuer Linux Hilfe",
        "version": "0.1.0",
        "language": "de",
        "entries": [
            _serialize_linux_help_glossary_entry(item)
            for item in (_app_value(app, "linux_help_glossary", []) or [])
            if item.get("enabled", True)
        ],
    }
    ok, err = safe_write_json(
        app.linux_help_glossary_path,
        payload,
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        if update_status:
            app.linux_help_status_var.set(
                app.tr(
                    "linux_help_status_glossary_save_failed",
                    "Linux help: glossary save failed.",
                )
            )
        update_linux_help_notes(app, None, extra_error=str(err))
        return False
    if update_status:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_glossary_saved_count",
                "Linux help: {count} glossary entries saved.",
            ).format(count=len(_app_value(app, "linux_help_glossary", []) or []))
        )
    return True


def _load_linux_help_commands(path, *, isolated=True):
    if isolated:
        from netmon.core.linux_help_process import parse_commands

        return parse_commands(
            path,
            limits={
                name: globals()[name]
                for name in (
                    "MAX_SOURCE_CSV_BYTES",
                    "MAX_SOURCE_ROWS",
                    "MAX_SOURCE_COLUMNS",
                    "MAX_SOURCE_CELL_CHARS",
                    "MAX_SOURCE_CELLS",
                    "MAX_SOURCE_TEXT_CHARS",
                )
            },
        )
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
        item = normalize_linux_help_entry(None, reduced, existing_ids=seen_ids)
        seen_ids.add(item["id"])
        commands.append(item)
    commands.sort(
        key=lambda item: (
            item.get("category", "").lower(),
            item.get("name", "").lower(),
        )
    )
    return commands


def import_linux_help_csv(app, path):
    commands = _load_linux_help_commands(path)
    app.linux_help_data = commands
    rebuild_linux_help_indexes(app)
    set_linux_help_dirty(app, True)
    return commands


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
        load_linux_help_glossary(app)
        adopt_personal_markdown(app)
        set_linux_help_dirty(app, False)
        return app.linux_help_data

    commands = import_linux_help_csv(app, linux_help_csv_path())
    save_linux_help_data(app, update_status=False)
    load_linux_help_glossary(app)
    adopt_personal_markdown(app)
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
                "Linux help: save failed.",
            )
        )
        update_linux_help_notes(app, None, extra_error=str(err))
        return False
    set_linux_help_dirty(app, False)
    if update_status:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_saved_count",
                "Linux help: {count} entries saved.",
            ).format(count=len(app.linux_help_data))
        )
    return True


def get_linux_help_categories(app):
    combined = _app_value(app, "linux_help_combined_categories")
    if combined:
        return list(combined)
    return list(app.linux_help_categories)


def get_linux_help_commands_for_category(app, category):
    name = str(category or "").strip()
    source_mode = _linux_help_source_value(app)
    command_items = []
    glossary_items = []
    if source_mode in {"command", "both"}:
        if not name or name == _linux_help_all_categories_label(app):
            command_items = list(app.linux_help_commands)
        else:
            command_items = list(app.linux_help_commands_by_category.get(name, []))
    if source_mode in {"glossary", "both"}:
        glossary_by_category = (
            _app_value(app, "linux_help_glossary_by_category", {}) or {}
        )
        if not name or name == _linux_help_all_categories_label(app):
            glossary_items = list(_app_value(app, "linux_help_glossary", []) or [])
        else:
            glossary_items = list(glossary_by_category.get(name, []))
    items = [*command_items, *glossary_items]
    items.sort(
        key=lambda item: (
            item.get("category", "").lower(),
            item.get("name", "").lower(),
        )
    )
    return items


def get_linux_help_command_by_id(app, command_id):
    target = str(command_id or "").strip()
    data = list(_app_value(app, "linux_help_data", []) or []) + list(
        _app_value(app, "linux_help_glossary", []) or []
    )
    for item in data:
        if item.get("id") == target:
            return item
    return None


def sync_linux_help_form_categories(app):
    categories = [
        _linux_help_all_categories_label(app),
        *get_linux_help_categories(app),
    ]
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
    _risk_key, _label, fill = RISK_UI.get(
        (risk or "").strip().lower(),
        RISK_UI["unknown"],
    )
    canvas.itemconfigure(dot, fill=fill)


def update_linux_help_notes(app, item=None, extra_error=""):
    widget = _app_value(app, "linux_help_text")
    if widget is None:
        return
    _set_text_widget_content(
        widget, build_linux_help_notes_text(app, item, extra_error)
    )


def build_linux_help_notes_text(app, item=None, extra_error=""):
    if not item:
        body = app.tr(
            "linux_help_notes_empty",
            "Select a Linux command or glossary term above to view explanations, notes, and examples here.",
        )
        if extra_error:
            body = f"{body}\n\nError: {extra_error}"
        return body

    if _is_glossary_item(item):
        lines = [
            f"{app.tr('linux_help_label_term', 'Term')}: {item.get('name') or '–'}",
            f"{app.tr('label_category', 'Category')}: {item.get('category') or '–'}",
            f"{app.tr('linux_help_col_source', 'Source')}: {_source_label(app, 'glossary')}",
            f"{app.tr('linux_help_label_tags', 'Tags')}: {item.get('tags') or '–'}",
            "",
            f"{app.tr('linux_help_label_description', 'Description')}:",
            item.get("info") or "–",
            "",
            f"{app.tr('linux_help_label_example', 'Example')}:",
            item.get("example") or "–",
            "",
            f"{app.tr('linux_help_label_related', 'Related terms')}:",
            item.get("related") or "–",
            "",
            f"{app.tr('linux_help_label_note_readonly', 'Note')}:",
            app.tr(
                "linux_help_note_glossary_readonly",
                "This glossary entry is read-only reference content and cannot be sent to the terminal.",
            ),
        ]
    else:
        risk_key, risk_label, _fill = RISK_UI.get(
            str(item.get("risk") or "").strip().lower(),
            RISK_UI["unknown"],
        )
        risk_label = _tr(app, risk_key, risk_label)
        risk_prefix = _tr(app, "linux_help_col_risk", "Risk") + ":"
        risk_label = risk_label.removeprefix(risk_prefix).strip()
        lines = [
            f"{app.tr('linux_help_label_command_name', 'Command name')}: {item.get('name') or item.get('cmd') or '–'}",
            f"{app.tr('label_category', 'Category')}: {item.get('category') or '–'}",
            f"{app.tr('linux_help_col_source', 'Source')}: {_source_label(app, 'command')}",
            f"{app.tr('linux_help_col_risk', 'Risk')}: {risk_label}",
            f"{app.tr('linux_help_label_root_required', 'Root required')}: "
            + (
                app.tr("label_yes", "Yes")
                if item.get("root_required")
                else app.tr("label_no", "No")
            ),
            f"{app.tr('linux_help_label_tags', 'Tags')}: {item.get('tags') or '–'}",
            "",
            f"{app.tr('linux_help_col_command', 'Command')}: {item.get('cmd') or '–'}",
            f"{app.tr('linux_help_label_syntax', 'Syntax')}: {item.get('syntax') or item.get('cmd') or '–'}",
            f"{app.tr('linux_help_label_example', 'Example')}: {item.get('example') or item.get('cmd') or '–'}",
            "",
            f"{app.tr('linux_help_label_description', 'Description')}:",
            item.get("info") or "–",
            "",
            f"{app.tr('linux_help_label_explanation_text', 'Explanation')}:",
            item.get("explanation") or item.get("info") or "–",
            "",
            f"{app.tr('linux_help_label_warning_text', 'Note')}:",
            item.get("warning_text")
            or app.tr(
                "linux_help_note_display_only",
                "This entry acts as NetMon reference data and can be sent to the terminal when needed.",
            ),
        ]
    return "\n".join(lines)


def _risk_filter_value(app):
    label = str(_app_var_get(app, "linux_help_risk_filter_var", "") or "").strip()
    return {
        _tr(app, "linux_help_risk_safe", "🟢 Safe"): "safe",
        _tr(app, "linux_help_risk_caution", "🟡 Admin"): "caution",
        _tr(app, "linux_help_risk_danger", "🔴 Dangerous"): "danger",
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
    _app_var_set(app, "linux_help_category_var", _linux_help_all_categories_label(app))
    _app_var_set(app, "linux_help_source_var", _linux_help_all_sources_label(app))
    _app_var_set(app, "linux_help_risk_filter_var", _linux_help_all_risks_label(app))
    _app_var_set(app, "linux_help_bookmarks_only_var", False)
    refresh_linux_help_list(app)


def _reading_state(app):
    state = _app_value(app, "linux_help_reading_state")
    if state is None:
        state = ReadingState()
        app.linux_help_reading_state = state
    return state


def _reading_label(app, item):
    value = _reading_state(app).get(item)
    label = (
        _tr(app, "linux_help_reading_read", "Gelesen")
        if value["read"]
        else _tr(app, "linux_help_reading_unread", "Ungelesen")
    )
    return ("★ · " if value.get("bookmark") else "") + label


def style_linux_help_reading(app):
    tree = _app_value(app, "linux_help_tree")
    if not isinstance(tree, ttk.Treeview):
        return
    style = ttk.Style(tree)
    background = style.lookup("Treeview", "background") or "#ffffff"
    base = tree.winfo_rgb(background)
    accent = tree.winfo_rgb("#408cd0")
    color = "#" + "".join(
        f"{round((a * .82 + b * .18) / 257):02x}" for a, b in zip(base, accent)
    )
    tree.tag_configure("linux_help_read", background=color)


def _refresh_reading_marks(app):
    tree = _app_value(app, "linux_help_tree")
    if tree is not None:
        if _app_var_get(app, "linux_help_bookmarks_only_var", False):
            refresh_linux_help_list(app)
        else:
            for item in _app_value(app, "linux_help_visible_commands", []):
                row = item.get("id", "")
                if not tree.exists(row):
                    continue
                tags = [
                    tag for tag in tree.item(row, "tags") if tag != "linux_help_read"
                ]
                if _reading_state(app).get(item)["read"]:
                    tags.append("linux_help_read")
                tree.item(row, tags=tags)
                if "reading" in tree["columns"]:
                    tree.set(row, "reading", _reading_label(app, item))
    for name in ("linux_help_reader_window",):
        window = _app_value(app, name)
        if window is not None and window.winfo_exists():
            try:
                from netmon.ui.linux_help_reader import set_reader_reading_state
            except ModuleNotFoundError:
                from ui.linux_help_reader import set_reader_reading_state
            set_reader_reading_state(window, _reading_state(app).get(window.entry))


def change_linux_help_reading(app, item, **changes):
    try:
        result = _reading_state(app).change(item, **changes)
    except (OSError, ValueError, UnicodeError, RecursionError):
        _app_var_set(
            app,
            "linux_help_status_var",
            _tr(
                app,
                "linux_help_reading_failed",
                "Lesestatus konnte nicht gespeichert werden.",
            ),
        )
        return None
    _refresh_reading_marks(app)
    return result


def reset_linux_help_reading(app):
    if messagebox is None or not messagebox.askyesno(
        _tr(app, "linux_help_reading_reset_title", "Lesestatus zurücksetzen"),
        _tr(
            app,
            "linux_help_reading_reset_prompt",
            "Alle Erklärungen als ungelesen markieren? Die Lesezeichen bleiben erhalten.",
        ),
        parent=app.linux_help_tree.winfo_toplevel(),
        default="no",
    ):
        return False
    try:
        _reading_state(app).change(reset_read=True)
    except (OSError, ValueError, UnicodeError, RecursionError):
        _app_var_set(
            app,
            "linux_help_status_var",
            _tr(
                app,
                "linux_help_reading_failed",
                "Lesestatus konnte nicht gespeichert werden.",
            ),
        )
        return False
    _refresh_reading_marks(app)
    _app_var_set(
        app,
        "linux_help_status_var",
        _tr(
            app,
            "linux_help_reading_reset_done",
            "Lesestatus zurückgesetzt. Lesezeichen bleiben erhalten.",
        ),
    )
    return True


def refresh_linux_help_list(app, category=None):
    category_name = str(
        category or _app_var_get(app, "linux_help_category_var", "") or ""
    ).strip()
    if not category_name:
        category_name = _linux_help_all_categories_label(app)
    if category_name != _linux_help_all_categories_label(
        app
    ) and category_name not in get_linux_help_categories(app):
        category_name = _linux_help_all_categories_label(app)
    _app_var_set(app, "linux_help_category_var", category_name)

    commands = list(get_linux_help_commands_for_category(app, category_name))
    query = str(_app_var_get(app, "linux_help_search_var", "") or "").strip().lower()
    if query:
        commands = [item for item in commands if _matches_linux_help_query(item, query)]
    risk_filter = _risk_filter_value(app)
    if risk_filter:
        commands = [item for item in commands if item.get("risk") == risk_filter]
    if _app_var_get(app, "linux_help_bookmarks_only_var", False):
        commands = [
            item for item in commands if _reading_state(app).get(item).get("bookmark")
        ]

    app.linux_help_visible_commands = commands
    app.linux_help_visible_command_ids = [item.get("id", "") for item in commands]

    tree = _app_value(app, "linux_help_tree")
    listbox = _app_value(app, "linux_help_listbox")
    if tree is not None:
        style_linux_help_reading(app)
        tree.delete(*tree.get_children())
        for item in commands:
            _risk_key, risk_label, _fill = RISK_UI.get(
                item.get("risk"),
                RISK_UI["unknown"],
            )
            values = (
                item.get("category") or "–",
                _source_label(
                    app, "glossary" if _is_glossary_item(item) else "command"
                ),
                risk_label,
                (
                    _tr(app, "label_yes", "Yes")
                    if item.get("root_required")
                    else _tr(app, "label_no", "No")
                ),
                item.get("tags") or "–",
                item.get("info") or "–",
            )
            if "reading" in tree["columns"]:
                values += (_reading_label(app, item),)
            tree.insert(
                "",
                "end",
                iid=item.get("id", ""),
                text=item.get("name") or item.get("cmd") or "–",
                values=values,
                tags=(
                    ("linux_help_read",)
                    if _reading_state(app).get(item)["read"]
                    else ()
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
        app.tr("linux_help_no_command_selected", "No command selected."),
    )
    _app_var_set(
        app,
        "linux_help_desc_var",
        app.tr(
            "linux_help_select_left_hint",
            "Select a command above to view syntax, description, tags and risks.",
        ),
    )
    _app_var_set(app, "linux_help_detail_syntax_var", "–")
    _app_var_set(app, "linux_help_detail_example_var", "–")
    _app_var_set(app, "linux_help_detail_root_var", "–")
    _app_var_set(app, "linux_help_detail_tags_var", "–")
    _app_var_set(
        app, "linux_help_risk_var", app.tr("linux_help_risk_unknown", "Risk: -")
    )
    _app_var_set(
        app,
        "linux_help_risk_badge_var",
        app.tr("linux_help_risk_unknown_label", "⚪ Unknown"),
    )
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
    _risk_key, risk_label, _fill = RISK_UI.get(risk, RISK_UI["unknown"])

    _app_var_set(app, "linux_help_detail_name_var", item.get("name") or "–")
    _app_var_set(app, "linux_help_detail_category_var", item.get("category") or "–")
    _app_var_set(
        app,
        "linux_help_command_var",
        item.get("cmd")
        or (
            app.tr("linux_help_glossary_no_command", "No terminal command")
            if _is_glossary_item(item)
            else "–"
        ),
    )
    _app_var_set(
        app,
        "linux_help_desc_var",
        item.get("info")
        or app.tr("linux_help_no_description", "No description available."),
    )
    _app_var_set(
        app,
        "linux_help_detail_syntax_var",
        item.get("syntax")
        or item.get("cmd")
        or (
            app.tr("linux_help_glossary_not_applicable", "Not applicable")
            if _is_glossary_item(item)
            else "–"
        ),
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
            app.tr("linux_help_glossary_not_applicable", "Not applicable")
            if _is_glossary_item(item)
            else (
                app.tr("label_yes", "Yes")
                if item.get("root_required")
                else app.tr("label_no", "No")
            )
        ),
    )
    _app_var_set(app, "linux_help_detail_tags_var", item.get("tags") or "–")
    _app_var_set(app, "linux_help_risk_var", risk_label)
    _app_var_set(app, "linux_help_risk_badge_var", risk_label)
    set_linux_help_risk_light(app, risk)
    set_linux_help_form_from_entry(app, None if _is_glossary_item(item) else item)
    update_linux_help_notes(app, item)


def open_linux_help_reader(app, event=None, *, command_id=None):
    tree = _app_value(app, "linux_help_tree")
    if event is not None and getattr(event, "num", None) == 1 and tree is not None:
        row = tree.identify_row(event.y)
        if not row:
            return "break"
        tree.selection_set(row)
        tree.focus(row)
    item = _resolve_linux_help_item(app, command_id)
    if item is None:
        return "break" if event is not None else None
    try:
        from netmon.ui.linux_help_reader import open_reader_window
    except ModuleNotFoundError:
        from ui.linux_help_reader import open_reader_window
    error_message = ""
    try:
        document = load_entry_document(item)
    except (OSError, ValueError, UnicodeError, RecursionError):
        document = None
        error_message = _tr(
            app,
            "linux_help_reader_failed",
            "Die Markdown-Dokumentation konnte nicht geladen werden. Die Kurzinfo bleibt verfügbar.",
        )
    window = _app_value(app, "linux_help_reader_window")
    created = window is None or not window.winfo_exists()
    parent = tree.winfo_toplevel() if tree is not None else app
    window = open_reader_window(
        parent,
        window=None if created else window,
        tr=app.tr,
        entry=item,
        short_info=build_linux_help_notes_text(app, item),
        document=document,
        error_message=error_message,
        reading_state=_reading_state(app).get(item),
        on_reading_change=lambda **changes: change_linux_help_reading(
            app, item, **changes
        ),
        on_glossary_link=lambda identifier: open_linux_help_reader(
            app, command_id=identifier
        ),
    )
    app.linux_help_reader_window = window
    if change_linux_help_reading(app, item, read=True) is None:
        window.reading_status.set(
            _tr(
                app,
                "linux_help_reading_failed",
                "Lesestatus konnte nicht gespeichert werden.",
            )
        )
    if created:
        attach_menu = _app_value(app, "attach_chad_context_menu")
        if callable(attach_menu):
            attach_menu(window.short_info, "Linux command database")
    return "break" if event is not None else window


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
    if _linux_help_source_value(app) == "glossary":
        base = {
            "entry_type": "glossary",
            "category": app.linux_help_category_var.get() or "Glossary",
            "name": "New term",
            "info": "Short definition",
            "example": "",
            "tags": "",
            "related": "",
            "explanation": "",
            "warning_text": "",
            "enabled": True,
        }
    else:
        base = {
            "entry_type": "command",
            "category": app.linux_help_category_var.get() or "General",
            "name": "New command",
            "info": "New short description",
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
                "Linux help: please select an entry first.",
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
                "Linux help: please select an entry first.",
            )
        )
        return
    if messagebox is not None:
        confirmed = messagebox.askyesno(
            app.tr("linux_help_delete_title", "Delete entry"),
            app.tr(
                (
                    "linux_help_delete_confirm_glossary"
                    if _is_glossary_item(target)
                    else "linux_help_delete_confirm"
                ),
                (
                    "Delete the selected glossary entry now?"
                    if _is_glossary_item(target)
                    else "Delete the selected Linux command now?"
                ),
            ),
            parent=app,
        )
        if not confirmed:
            return
    kind = "glossary" if _is_glossary_item(target) else "command"
    attribute = "linux_help_glossary" if kind == "glossary" else "linux_help_data"
    previous = list(getattr(app, attribute))
    updated = [item for item in previous if item is not target]
    try:
        _write_entry_list(app, kind, updated)
        if target.get("markdown_id"):
            try:
                if get_linux_help_document_by_id(target["markdown_id"]) is not None:
                    delete_linux_help_document(target["markdown_id"])
            except Exception:
                _write_entry_list(app, kind, previous)
                raise
    except (OSError, ValueError, RuntimeError) as exc:
        _app_var_set(app, "linux_help_status_var", str(exc))
        return False
    setattr(app, attribute, updated)
    rebuild_linux_help_indexes(app)
    rebuild_linux_help_glossary_indexes(app)
    app.linux_help_selected_id = ""
    sync_linux_help_form_categories(app)
    refresh_linux_help_list(app)
    set_linux_help_dirty(app, True)
    app.linux_help_status_var.set(
        app.tr(
            (
                "linux_help_status_glossary_deleted"
                if _is_glossary_item(target)
                else "linux_help_status_entry_deleted"
            ),
            (
                "Linux help: glossary entry deleted."
                if _is_glossary_item(target)
                else "Linux help: entry deleted."
            ),
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
    is_glossary = (
        _is_glossary_item(base)
        or str(base.get("entry_type") or "").strip().lower() == "glossary"
    )
    try:
        if is_new:
            markdown_body = ""
        elif base.get("markdown_id"):
            metadata = get_linux_help_document_by_id(base["markdown_id"])
            if metadata is None:
                raise FileNotFoundError("Eigene Markdown-Datei fehlt.")
            markdown_body = split_markdown(read_linux_help_markdown(metadata))[1]
        else:
            document = load_entry_document(base) if not is_new else None
            markdown_body = (
                split_markdown(document.source)[1]
                if document
                else (
                    "# "
                    + (base.get("name") or "Neuer Eintrag")
                    + "\n\n"
                    + (base.get("explanation") or base.get("info") or "")
                    + "\n"
                )
            )
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        if messagebox is not None:
            messagebox.showerror(
                _tr(app, "linux_help_reader_title", "Dokumentation"),
                str(exc),
                parent=app,
            )
        return None
    dialog = tk.Toplevel(app)
    dialog.title(
        app.tr(
            (
                "linux_help_dialog_title_new_glossary"
                if is_new and is_glossary
                else "linux_help_dialog_title_new"
            ),
            (
                "Create glossary term"
                if is_new and is_glossary
                else "Create Linux command"
            ),
        )
        if is_new
        else app.tr(
            (
                "linux_help_dialog_title_edit_glossary"
                if is_glossary
                else "linux_help_dialog_title_edit"
            ),
            "Edit glossary term" if is_glossary else "Edit Linux command",
        )
    )
    dialog.transient(app)
    dialog.resizable(True, True)
    dialog.minsize(760, 560)
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)
    app.linux_help_entry_dialog = dialog

    category_var = tk.StringVar(value=base.get("category") or "General")
    name_var = tk.StringVar(value=base.get("name") or "")
    info_var = tk.StringVar(value=base.get("info") or "")
    cmd_var = tk.StringVar(value=base.get("cmd") or "")
    syntax_var = tk.StringVar(value=base.get("syntax") or base.get("cmd") or "")
    example_var = tk.StringVar(value=base.get("example") or "")
    tags_var = tk.StringVar(value=base.get("tags") or "")
    related_var = tk.StringVar(value=base.get("related") or "")
    risk_var = tk.StringVar(value=_risk_storage_to_dialog_label(app, base.get("risk")))
    root_var = tk.BooleanVar(value=bool(base.get("root_required")))
    enabled_var = tk.BooleanVar(value=bool(base.get("enabled", True)))

    shell = ttk.Frame(dialog, padding=12)
    shell.grid(row=0, column=0, sticky="nsew")
    shell.columnconfigure(0, weight=1)
    shell.rowconfigure(1, weight=1)

    form = ttk.LabelFrame(
        shell,
        text=app.tr("linux_help_dialog_group", "Edit entry"),
        padding=10,
    )
    form.grid(row=0, column=0, sticky="ew")
    form.columnconfigure(1, weight=1)
    form.columnconfigure(3, weight=1)

    ttk.Label(form, text=app.tr("label_category", "Category")).grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    category_combo = ttk.Combobox(
        form,
        textvariable=category_var,
        values=[value for value in get_linux_help_categories(app) if value],
    )
    category_combo.grid(row=0, column=1, sticky="ew", pady=(0, 6))

    ttk.Label(
        form,
        text=app.tr(
            "linux_help_label_term" if is_glossary else "linux_help_label_command_name",
            "Term" if is_glossary else "Command name",
        ),
    ).grid(row=0, column=2, sticky="w", padx=(12, 8), pady=(0, 6))
    ttk.Entry(form, textvariable=name_var).grid(
        row=0, column=3, sticky="ew", pady=(0, 6)
    )

    ttk.Label(form, text=app.tr("linux_help_label_description", "Description")).grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
    )
    ttk.Entry(form, textvariable=info_var).grid(
        row=1, column=1, columnspan=3, sticky="ew", pady=(0, 6)
    )

    if is_glossary:
        ttk.Label(form, text=app.tr("linux_help_label_example", "Example")).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
        )
        ttk.Entry(form, textvariable=example_var).grid(
            row=2, column=1, columnspan=3, sticky="ew", pady=(0, 6)
        )

        ttk.Label(form, text=app.tr("linux_help_label_tags", "Tags")).grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=(0, 6)
        )
        ttk.Entry(form, textvariable=tags_var).grid(
            row=3, column=1, sticky="ew", pady=(0, 6)
        )
        ttk.Label(form, text=app.tr("linux_help_label_related", "Related terms")).grid(
            row=3, column=2, sticky="w", padx=(12, 8), pady=(0, 6)
        )
        ttk.Entry(form, textvariable=related_var).grid(
            row=3, column=3, sticky="ew", pady=(0, 6)
        )
    else:
        ttk.Label(form, text=app.tr("linux_help_col_command", "Command")).grid(
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

        ttk.Label(form, text=app.tr("linux_help_label_example", "Example")).grid(
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

        ttk.Label(form, text=app.tr("linux_help_label_risk_filter", "Risk")).grid(
            row=5, column=2, sticky="w", padx=(12, 8), pady=(0, 6)
        )
        ttk.Combobox(
            form,
            textvariable=risk_var,
            values=[label for label, _key in _risk_dialog_choices_for_app(app)],
            state="readonly",
        ).grid(row=5, column=3, sticky="ew", pady=(0, 6))

    flags_row = ttk.Frame(form)
    flags_row.grid(
        row=4 if is_glossary else 6, column=0, columnspan=4, sticky="w", pady=(2, 0)
    )
    if not is_glossary:
        ttk.Checkbutton(
            flags_row,
            text=app.tr("linux_help_label_root_required", "Root required"),
            variable=root_var,
        ).pack(side="left")
    ttk.Checkbutton(
        flags_row,
        text=app.tr("label_enabled", "Enabled"),
        variable=enabled_var,
    ).pack(side="left", padx=(14 if not is_glossary else 0, 0))

    notebook = ttk.Notebook(shell)
    notebook.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
    markdown_frame = ttk.Frame(notebook, padding=8)
    markdown_frame.columnconfigure(0, weight=1)
    markdown_frame.rowconfigure(0, weight=1)
    markdown_text = tk.Text(markdown_frame, wrap="word", undo=True, height=12)
    markdown_text.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(
        markdown_frame, orient="vertical", command=markdown_text.yview
    )
    scrollbar.grid(row=0, column=1, sticky="ns")
    markdown_text.configure(yscrollcommand=scrollbar.set)
    markdown_text.insert("1.0", markdown_body)
    dialog.markdown_text = markdown_text
    notebook.add(markdown_frame, text="Markdown (.md)")
    editors = ttk.Frame(notebook)
    notebook.add(
        editors, text=app.tr("linux_help_edit_notes_tab", "Kurzinfo und Hinweise")
    )
    editors.columnconfigure(0, weight=1)
    editors.columnconfigure(1, weight=1)
    editors.rowconfigure(0, weight=1)

    explanation_frame = ttk.LabelFrame(
        editors,
        text=app.tr("linux_help_label_explanation_text", "Explanation"),
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
        text=app.tr("linux_help_label_warning_text", "Note"),
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
            "entry_type": "glossary" if is_glossary else "command",
            "category": (category_var.get() or "").strip() or "General",
            "name": (name_var.get() or "").strip(),
            "info": (info_var.get() or "").strip(),
            "cmd": (cmd_var.get() or "").strip(),
            "syntax": (syntax_var.get() or "").strip(),
            "example": (example_var.get() or "").strip(),
            "tags": (tags_var.get() or "").strip(),
            "related": (related_var.get() or "").strip(),
            "risk": _risk_dialog_label_to_storage(app, risk_var.get()),
            "root_required": bool(root_var.get()),
            "enabled": bool(enabled_var.get()),
            "explanation": explanation_text.get("1.0", "end").strip(),
            "warning_text": warning_text.get("1.0", "end").strip(),
        }
        if not raw["name"]:
            if messagebox is not None:
                messagebox.showwarning(
                    app.tr("linux_help_dialog_validation_title", "Incomplete input"),
                    app.tr(
                        (
                            "linux_help_dialog_validation_body_glossary"
                            if is_glossary
                            else "linux_help_dialog_validation_body"
                        ),
                        (
                            "Please fill at least the glossary term."
                            if is_glossary
                            else "Please fill at least the name."
                        ),
                    ),
                    parent=dialog,
                )
            return
        target = (
            None if is_new else get_linux_help_command_by_id(app, base.get("id", ""))
        )
        existing_ids = {
            item.get("id")
            for item in [*app.linux_help_data, *app.linux_help_glossary]
            if item is not target and item.get("id")
        }
        normalized = (
            normalize_linux_help_glossary_entry(app, raw, existing_ids=existing_ids)
            if is_glossary
            else normalize_linux_help_entry(app, raw, existing_ids=existing_ids)
        )
        try:
            body = markdown_text.get("1.0", "end-1c")
            if not body.strip():
                body = "# " + normalized["name"] + "\n\n" + raw["explanation"] + "\n"
            saved = save_entry_markdown(app, normalized, body, target=target)
            _show_saved_entry(app, saved)
        except (OSError, ValueError, UnicodeError, RuntimeError, RecursionError) as exc:
            if messagebox is not None:
                messagebox.showerror(
                    _tr(app, "linux_help_reader_title", "Dokumentation"),
                    str(exc),
                    parent=dialog,
                )
            return
        set_linux_help_dirty(app, True)
        app.linux_help_status_var.set(
            app.tr(
                (
                    "linux_help_status_glossary_saved"
                    if is_glossary
                    else "linux_help_status_entry_saved"
                ),
                (
                    "Linux help: glossary entry saved."
                    if is_glossary
                    else "Linux help: entry saved."
                ),
            )
        )
        _close_dialog()

    ttk.Button(
        buttons,
        text=app.tr("btn_cancel", "Cancel"),
        command=_close_dialog,
    ).pack(side="right")
    dialog.save_button = ttk.Button(
        buttons,
        text=app.tr("btn_save", "Save"),
        command=_save_dialog,
    )
    dialog.save_button.pack(side="right", padx=(0, 8))

    apply_colors = _app_value(app, "_apply_tk_widget_theme")
    if callable(apply_colors) and _app_value(app, "_app_theme"):
        apply_colors(dialog, app._app_theme)
    dialog.protocol("WM_DELETE_WINDOW", _close_dialog)
    try:
        dialog.update_idletasks()
        dialog.grab_set()
        dialog.focus_force()
    except Exception:
        pass

    return dialog


def copy_linux_help_chad_prompt(app):
    item, _title, prompt = _selected_linux_help_chad_payload(app)
    if item is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_no_command_selected",
                "Linux help: no command selected.",
            )
        )
        return False
    app.clipboard_clear()
    app.clipboard_append(prompt)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_prompt_copied",
            "Linux help: Chad prompt copied to clipboard.",
        )
    )
    return True


def copy_linux_help_markdown_prompt(app):
    item = _get_selected_linux_help_item(app)
    if item is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_no_command_selected",
                "Linux help: no command selected.",
            )
        )
        return False
    prompt = build_linux_help_markdown_prompt(item, language="de")
    app.clipboard_clear()
    app.clipboard_append(prompt)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_markdown_prompt_copied",
            "Linux help: Markdown prompt copied to clipboard.",
        )
    )
    return True


def send_linux_help_to_chad(app):
    item, title, prompt = _selected_linux_help_chad_payload(app)
    if item is None:
        app.linux_help_status_var.set(
            app.tr(
                "linux_help_status_no_command_selected",
                "Linux help: no command selected.",
            )
        )
        return False
    if not _set_chad_direct_prompt_safe(app, title, prompt):
        app.chad_analysis_current_prompt = prompt
        app.chad_online_result = ""
        try:
            app.chad_analysis_source_var.set(
                f"{app.tr('chad_label_source_prefix', 'Source')}: {title}"
            )
            app.chad_analysis_status_var.set(
                app.tr("chad_status_analysis_prepared", "Analysis prepared.")
            )
        except Exception:
            pass
    app.linux_help_status_var.set(
        app.tr(
            (
                "linux_help_status_sent_to_chad_glossary"
                if _is_glossary_item(item)
                else "linux_help_status_sent_to_chad"
            ),
            "Linux help: entry handed to Chad for explanation.",
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
        label=app.tr("linux_help_menu_send_chad", "Send to Chad"),
        command=lambda: send_linux_help_to_chad(app),
    )
    menu.add_command(
        label=app.tr("linux_help_menu_copy_prompt", "Copy as prompt"),
        command=lambda: copy_linux_help_chad_prompt(app),
    )
    menu.add_command(
        label=app.tr(
            "linux_help_menu_copy_markdown_prompt", "Als Markdown-Prompt kopieren"
        ),
        command=lambda: copy_linux_help_markdown_prompt(app),
    )
    menu.add_separator()
    was_read = _reading_state(app).get(item)["read"]
    menu.add_command(
        label=(
            _tr(app, "linux_help_mark_unread", "Als ungelesen markieren")
            if was_read
            else _tr(app, "linux_help_mark_read", "Als gelesen markieren")
        ),
        command=lambda: change_linux_help_reading(app, item, read=not was_read),
    )
    menu.add_separator()
    menu.add_command(
        label=app.tr("btn_edit", "Edit"),
        command=app.linux_help_edit_selected,
    )
    show_fn = getattr(app, "_show_context_menu", None)
    if callable(show_fn):
        return show_fn(menu, event)
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        try:
            menu.grab_release()
        except Exception:
            pass
    return "break"


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
                "Linux help: data could not be loaded.",
            )
        )
        update_linux_help_notes(app, None, extra_error=str(exc))
        return

    sync_linux_help_form_categories(app)
    app.linux_help_category_var.set(_linux_help_all_categories_label(app))
    app.linux_help_source_var.set(_linux_help_all_sources_label(app))
    app.linux_help_risk_filter_var.set(_linux_help_all_risks_label(app))
    refresh_linux_help_list(app)
    app.linux_help_status_var.set(
        app.tr(
            "linux_help_status_loaded_count",
            "Linux help: {count} commands loaded.",
        ).format(count=len(commands))
        + " | "
        + app.tr(
            "linux_help_status_loaded_glossary_count",
            "{count} glossary entries loaded.",
        ).format(count=len(_app_value(app, "linux_help_glossary", []) or []))
    )


def load_entry_document(item):
    if item.get("markdown_id"):
        metadata = get_linux_help_document_by_id(item["markdown_id"])
        if metadata is None:
            raise FileNotFoundError("Eigene Markdown-Dokumentation fehlt.")
        metadata["entry"] = item
        return load_linux_help_markdown(metadata)
    try:
        from netmon.services import linux_help_glossary_service as glossary
        from netmon.services import linux_help_markdown_service as markdown
    except ModuleNotFoundError:
        from services import linux_help_glossary_service as glossary
        from services import linux_help_markdown_service as markdown
    return (
        glossary.load_glossary_document(item)
        if _is_glossary_item(item)
        else markdown.load_command_document(item)
    )


def _write_entry_list(app, kind, items):
    if kind == "glossary":
        path = app.linux_help_glossary_path
        payload = {
            "name": "IT-Lexikon fuer Linux Hilfe",
            "version": "0.1.0",
            "language": "de",
            "entries": [_serialize_linux_help_glossary_entry(item) for item in items],
        }
    else:
        path, payload = app.linux_help_data_path, items
    ok, error = safe_write_json(path, payload, indent=2, ensure_ascii=False)
    if not ok:
        raise OSError("Einträge konnten nicht gespeichert werden: " + str(error))


def save_entry_markdown(app, item, body, *, target=None):
    """Link a fully published revision only after the entry JSON is saved."""
    kind = "glossary" if _is_glossary_item(item) else "command"
    attribute = "linux_help_glossary" if kind == "glossary" else "linux_help_data"
    metadata = save_linux_help_markdown(format_entry_markdown(item, body), item)
    saved = dict(item, markdown_id=metadata["id"])
    current = list(_app_value(app, attribute, []) or [])
    updated = [saved if row is target else row for row in current]
    if target is None:
        updated.append(saved)
    try:
        _write_entry_list(app, kind, updated)
    except Exception:
        delete_linux_help_document(metadata["id"])
        raise
    setattr(app, attribute, updated)
    rebuild_linux_help_indexes(app)
    rebuild_linux_help_glossary_indexes(app)
    if target and target.get("markdown_id"):
        try:
            delete_linux_help_document(target["markdown_id"])
        except (OSError, ValueError):
            pass  # An unlinked old revision cannot replace the saved entry.
    return saved


def adopt_personal_markdown(app):
    """Move existing personal Markdown into the same list; ignore PDF metadata."""
    rows = [
        *(_app_value(app, "linux_help_data", []) or []),
        *(_app_value(app, "linux_help_glossary", []) or []),
    ]
    known = {row.get("markdown_id") for row in rows}
    used = {row.get("id") for row in rows}
    for metadata in list_linux_help_documents():
        if metadata["id"] in known or "entry" in metadata:
            continue
        try:
            document = load_linux_help_markdown(metadata)
            fields = document.metadata
            raw = {
                "id": "own_" + metadata["id"],
                "name": fields["name"],
                "category": fields["category"],
                "cmd": fields.get("command", ""),
                "tags": fields.get("tags", []),
                "related": fields.get("related", []),
                "markdown_id": metadata["id"],
            }
            normalizer = (
                normalize_linux_help_glossary_entry
                if fields.get("entry_type") == "glossary"
                else normalize_linux_help_entry
            )
            item = normalizer(app, raw, existing_ids=used)
            kind = "glossary" if _is_glossary_item(item) else "command"
            attribute = (
                "linux_help_glossary" if kind == "glossary" else "linux_help_data"
            )
            updated = [*(_app_value(app, attribute, []) or []), item]
            _write_entry_list(app, kind, updated)
            setattr(app, attribute, updated)
            used.add(item["id"])
            metadata["entry"] = dict(item)
            safe_write_json(
                metadata["json_path"], metadata, indent=2, ensure_ascii=False
            )
            legacy = {
                "entry_type": "document",
                "id": metadata["id"],
                "name": metadata.get("title")
                or metadata.get("command_name")
                or "Dokumentation",
                "cmd": metadata.get("command") or "",
            }
            state = _reading_state(app)
            previous = state.get(legacy)
            if previous.get("read") or previous.get("bookmark"):
                state.change(item, **previous)
        except (OSError, ValueError, RecursionError):
            continue
    rebuild_linux_help_indexes(app)
    rebuild_linux_help_glossary_indexes(app)


def _show_saved_entry(app, item):
    sync_linux_help_form_categories(app)
    _app_var_set(app, "linux_help_category_var", _linux_help_all_categories_label(app))
    _app_var_set(app, "linux_help_source_var", _linux_help_all_sources_label(app))
    _app_var_set(app, "linux_help_risk_filter_var", _linux_help_all_risks_label(app))
    _app_var_set(app, "linux_help_search_var", "")
    _app_var_set(app, "linux_help_bookmarks_only_var", False)
    refresh_linux_help_list(app)
    tree = _app_value(app, "linux_help_tree")
    if tree is not None and tree.exists(item["id"]):
        tree.selection_set(item["id"])
        tree.focus(item["id"])
        tree.see(item["id"])
    app.linux_help_selected_id = item["id"]
    on_linux_help_select(app)
    window = _app_value(app, "linux_help_reader_window")
    if (
        window is not None
        and window.winfo_exists()
        and window.entry.get("id") == item["id"]
    ):
        open_linux_help_reader(app, command_id=item["id"])


def open_linux_help_prompt(app):
    window = _app_value(app, "linux_help_prompt_window")
    if window is not None and window.winfo_exists():
        window.deiconify()
        window.lift()
        window.focus_force()
        return window
    try:
        from netmon.ui.linux_help_prompt import MarkdownPromptWindow
    except ModuleNotFoundError:
        from ui.linux_help_prompt import MarkdownPromptWindow
    tree = _app_value(app, "linux_help_tree")
    parent = tree.winfo_toplevel() if tree is not None else app
    window = MarkdownPromptWindow(parent, app)
    app.linux_help_prompt_window = window
    if _linux_help_source_value(app) == "glossary":
        window.kind_var.set(window.kind_labels["glossary"])
    category = _app_var_get(app, "linux_help_category_var", "")
    if category and category != _linux_help_all_categories_label(app):
        window.category_var.set(category)
    return window


def deliver_linux_help_markdown_prompt(app, title, prompt):
    if not _set_chad_direct_prompt_safe(app, title, prompt):
        app.chad_analysis_current_prompt = prompt
        app.chad_online_result = ""
        _app_var_set(app, "chad_analysis_source_var", title)
        _app_var_set(
            app,
            "chad_analysis_status_var",
            _tr(app, "chad_status_analysis_prepared", "Analyse vorbereitet."),
        )


def confirm_linux_help_import_category(app, raw):
    try:
        from netmon.ui.linux_help_prompt import ImportCategoryDialog
    except ModuleNotFoundError:
        from ui.linux_help_prompt import ImportCategoryDialog
    tree = _app_value(app, "linux_help_tree")
    parent = tree.winfo_toplevel() if tree is not None else app
    return ImportCategoryDialog(parent, app, raw).result


def import_linux_help_markdown_dialog(app):
    if filedialog is None:
        return None
    path = filedialog.askopenfilename(
        parent=app,
        title=_tr(
            app,
            "linux_help_import_markdown_title",
            "Markdown-Dokumentation importieren",
        ),
        filetypes=[("Markdown", "*.md *.markdown")],
    )
    if not path:
        return None
    try:
        text, raw = inspect_markdown_import(path)
        raw = confirm_linux_help_import_category(app, raw)
        if raw is None:
            return None
        try:
            from netmon.services.linux_help_prompt_service import validate_category
        except ModuleNotFoundError:
            from services.linux_help_prompt_service import validate_category
        raw["category"] = validate_category(raw.get("category"))
        candidates = [
            *(_app_value(app, "linux_help_data", []) or []),
            *(_app_value(app, "linux_help_glossary", []) or []),
        ]
        kind = raw["entry_type"]
        matches = [
            row
            for row in candidates
            if row.get("entry_type", "command") == kind
            and raw.get("id")
            and row["id"] == raw["id"]
        ]
        if not matches:
            matches = [
                row
                for row in candidates
                if row.get("entry_type", "command") == kind
                and row["name"].casefold() == raw["name"].casefold()
            ]
        target = None
        if matches:
            if len(matches) != 1:
                raise ValueError(
                    _tr(
                        app,
                        "linux_help_import_ambiguous",
                        "Mehrere passende Einträge. Bitte einen eindeutigen Namen oder eine ID verwenden.",
                    )
                )
            if messagebox is None:
                return None
            choice = messagebox.askyesnocancel(
                _tr(
                    app, "linux_help_import_existing_title", "Eintrag bereits vorhanden"
                ),
                _tr(
                    app,
                    "linux_help_import_existing_prompt",
                    "„{name}“ ist bereits vorhanden.\n\nJa: vorhandenen Eintrag aktualisieren\nNein: als neuen Eintrag anlegen\nAbbrechen: nichts importieren",
                ).format(name=matches[0]["name"]),
                parent=app,
            )
            if choice is None:
                return None
            if choice:
                target = matches[0]
                raw = {**target, **raw, "id": target["id"]}
        used = {row["id"] for row in candidates if row is not target}
        normalizer = (
            normalize_linux_help_glossary_entry
            if kind == "glossary"
            else normalize_linux_help_entry
        )
        item = normalizer(app, raw, existing_ids=used)
        saved = save_entry_markdown(app, item, text, target=target)
        _show_saved_entry(app, saved)
    except (OSError, ValueError, UnicodeError, RuntimeError, RecursionError) as exc:
        _app_var_set(
            app,
            "linux_help_status_var",
            _tr(
                app,
                "linux_help_markdown_import_failed",
                "Markdown-Import fehlgeschlagen.",
            )
            + " "
            + str(exc),
        )
        return None
    _app_var_set(
        app,
        "linux_help_status_var",
        _tr(app, "linux_help_markdown_imported", "Markdown importiert."),
    )
    return saved
