"""Links and desktop-app controller helpers for NetMon."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import webbrowser
import tkinter as tk
from tkinter import messagebox

try:
    from netmon.config.constants import LINK_SLOT_COUNT
except ModuleNotFoundError:
    from config.constants import LINK_SLOT_COUNT

try:
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    from core.utils import safe_write_json

try:
    from netmon.services.network_helpers import normalize_external_url_target
except ModuleNotFoundError:
    from services.network_helpers import normalize_external_url_target

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.core import tooling as _tooling
except ModuleNotFoundError:
    try:
        from core import tooling as _tooling
    except ModuleNotFoundError:
        _tooling = None

if _tooling is not None:
    get_cmd_path = _tooling.get_cmd_path
    has_cmd = _tooling.has_cmd
else:
    get_cmd_path = lambda _name: ""  # noqa: E731
    has_cmd = lambda _name: False  # noqa: E731


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


def _desktop_app_maps(entries):
    labels = [entry["label"] for entry in entries]
    by_label = {entry["label"]: entry for entry in entries}
    by_id = {entry["desktop_id"]: entry for entry in entries if entry.get("desktop_id")}
    return labels, by_label, by_id


def _selected_systemlink_entry(app):
    selected_label = str(_app_var_get(app, "link_system_app_var", "") or "").strip()
    return (_app_value(app, "desktop_app_by_label", {}) or {}).get(selected_label)


def _selected_link_slot_no(app, default=0) -> int:
    try:
        return int(
            str(_app_var_get(app, "link_slot_choice", str(default)) or default).strip()
        )
    except ValueError:
        return int(default)


def _selected_link_type(app) -> str:
    return str(_app_var_get(app, "link_type_var", "") or "").strip()


def _link_slot_at(app, slot_no: int):
    slots = _app_value(app, "link_slots", []) or []
    if 1 <= slot_no <= len(slots):
        return slots[slot_no - 1]
    return None


def _link_slot_has_assignment(slot) -> bool:
    if not isinstance(slot, dict):
        return False
    return bool(
        (slot.get("custom_name") or "").strip()
        or (slot.get("link_type") or "").strip()
        or (slot.get("target") or "").strip()
    )


def _link_custom_name(app) -> str:
    return str(_app_var_get(app, "link_custom_name_var", "") or "").strip()


def _set_link_custom_name_autofill(app, value: str) -> None:
    app.__dict__["link_custom_name_autofill"] = str(value or "").strip()


def _link_custom_name_autofill(app) -> str:
    return str(_app_value(app, "link_custom_name_autofill", "") or "").strip()


def _link_target_fields(app):
    link_type = _selected_link_type(app)
    if link_type == "Systemlink":
        return build_systemlink_target(app)
    if link_type == "Externer Link":
        target = normalize_external_url_target(_app_var_get(app, "link_target_var", ""))
        return target, "", "", ""
    target = str(_app_var_get(app, "link_target_var", "") or "").strip()
    return target, "", "", ""


def _clear_link_slot_payload(slot):
    slot["custom_name"] = ""
    slot["link_type"] = ""
    slot["target"] = ""
    slot["app_name"] = ""
    slot["desktop_id"] = ""
    slot["desktop_file"] = ""


def _systemlink_form_label(app, slot) -> str:
    if not isinstance(slot, dict):
        return ""
    desktop_id = str(slot.get("desktop_id") or "").strip()
    if desktop_id:
        entry = (_app_value(app, "desktop_app_by_id", {}) or {}).get(desktop_id)
        if entry:
            return str(entry.get("label") or "").strip()
    return str(slot.get("app_name") or "").strip()


def _desktop_bool(value):
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def desktop_exec_command(app, desktop_file):
    if not desktop_file or not os.path.isfile(desktop_file):
        return None
    try:
        with open(desktop_file, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line.startswith("Exec="):
                    exec_line = line.split("=", 1)[1].strip()
                    if not exec_line:
                        return None
                    parts = shlex.split(exec_line)
                    cleaned = []
                    for part in parts:
                        if part.startswith("%"):
                            continue
                        part = re.sub(r"%[fFuUdDnNickvm]", "", part)
                        if part:
                            cleaned.append(part)
                    return cleaned or None
    except Exception:
        return None
    return None


def desktop_search_dirs():
    return [
        os.path.expanduser("~/.local/share/applications"),
        "/usr/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
        "/var/lib/flatpak/exports/share/applications",
    ]


def desktop_language_keys():
    lang = (
        os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or os.environ.get("LANGUAGE")
        or ""
    ).split(":", 1)[0]
    lang = lang.split(".", 1)[0].strip()
    if not lang:
        return []
    keys = [lang]
    if "_" in lang:
        keys.append(lang.split("_", 1)[0])
    return keys


def parse_desktop_entry(app, desktop_file):
    if not desktop_file or not os.path.isfile(desktop_file):
        return None
    data = {}
    in_entry = False
    try:
        with open(desktop_file, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("["):
                    in_entry = line == "[Desktop Entry]"
                    continue
                if not in_entry or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip()
    except Exception:
        return None

    if (data.get("Type") or "Application").strip() != "Application":
        return None
    if _desktop_bool(data.get("Hidden")) or _desktop_bool(data.get("NoDisplay")):
        return None

    name = ""
    for key in desktop_language_keys():
        localized = data.get(f"Name[{key}]")
        if localized:
            name = localized.strip()
            break
    if not name:
        name = (data.get("Name") or "").strip()
    if not name:
        return None

    exec_line = (data.get("Exec") or "").strip()
    exec_cmd = None
    if exec_line:
        try:
            parts = shlex.split(exec_line)
        except Exception:
            parts = exec_line.split()
        cleaned = []
        for part in parts:
            if part.startswith("%"):
                continue
            part = re.sub(r"%[fFuUdDnNickvm]", "", part)
            if part:
                cleaned.append(part)
        exec_cmd = cleaned or None

    desktop_id = os.path.basename(desktop_file)
    return {
        "name": name,
        "desktop_id": desktop_id,
        "desktop_file": desktop_file,
        "exec": exec_cmd,
        "icon": (data.get("Icon") or "").strip(),
    }


def load_desktop_app_entries(app):
    entries_by_id = {}
    for base in desktop_search_dirs():
        if not os.path.isdir(base):
            continue
        try:
            names = sorted(os.listdir(base), key=str.casefold)
        except Exception:
            continue
        for name in names:
            if not name.endswith(".desktop"):
                continue
            desktop_file = os.path.join(base, name)
            entry = parse_desktop_entry(app, desktop_file)
            if not entry:
                continue
            desktop_id = (entry.get("desktop_id") or "").strip().lower()
            if desktop_id and desktop_id not in entries_by_id:
                entries_by_id[desktop_id] = entry

    entries = list(entries_by_id.values())
    name_counts = {}
    for entry in entries:
        name_counts[entry["name"]] = name_counts.get(entry["name"], 0) + 1
    for entry in entries:
        label = entry["name"]
        if name_counts[label] > 1:
            label = f"{label} ({entry['desktop_id']})"
        entry["label"] = label
    entries.sort(key=lambda item: item["label"].casefold())
    return entries


def refresh_desktop_app_entries(app):
    previous = str(_app_var_get(app, "link_system_app_var", "") or "").strip()
    entries = load_desktop_app_entries(app)
    app.desktop_app_entries = entries
    (
        app.desktop_app_labels,
        app.desktop_app_by_label,
        app.desktop_app_by_id,
    ) = _desktop_app_maps(entries)

    combo = _app_value(app, "link_system_combo")
    if combo is not None:
        try:
            combo.configure(values=app.desktop_app_labels)
        except Exception:
            pass

    if previous and previous in app.desktop_app_by_label:
        _app_var_set(app, "link_system_app_var", previous)
    elif app.desktop_app_labels:
        _app_var_set(app, "link_system_app_var", app.desktop_app_labels[0])
        app.on_systemlink_app_select()
    else:
        _app_var_set(app, "link_system_app_var", "")

    app.log(f"Programmliste aktualisiert: {len(app.desktop_app_labels)} Einträge.")


def default_link_slots():
    return [
        {
            "slot": i + 1,
            "custom_name": "",
            "link_type": "",
            "target": "",
            "app_name": "",
            "desktop_id": "",
            "desktop_file": "",
        }
        for i in range(LINK_SLOT_COUNT)
    ]


def load_link_slots_config(app):
    slots = default_link_slots()
    try:
        if os.path.isfile(app.link_config_path):
            with open(app.link_config_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    slot_no = int(item.get("slot", 0))
                    if 1 <= slot_no <= LINK_SLOT_COUNT:
                        link_type = (item.get("link_type") or "").strip()
                        if link_type not in ("Systemlink", "Externer Link"):
                            link_type = ""
                        slots[slot_no - 1] = {
                            "slot": slot_no,
                            "custom_name": (item.get("custom_name") or "").strip(),
                            "link_type": link_type,
                            "target": (item.get("target") or "").strip(),
                            "app_name": (item.get("app_name") or "").strip(),
                            "desktop_id": (item.get("desktop_id") or "").strip(),
                            "desktop_file": (item.get("desktop_file") or "").strip(),
                        }
    except Exception as exc:
        app.log(f"Link-Konfig konnte nicht geladen werden: {exc}")
    return slots


def save_link_slots_config(app):
    ok, err = safe_write_json(
        app.link_config_path,
        app.link_slots,
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        app.log(f"Link-Konfig konnte nicht gespeichert werden: {err}")


def link_slot_configured(app, slot):
    return bool(
        (slot.get("link_type") or "").strip() and (slot.get("target") or "").strip()
    )


def link_slot_display_name(app, idx):
    slot = app.link_slots[idx]
    custom = (slot.get("custom_name") or "").strip()
    if custom:
        return custom
    if link_slot_configured(app, slot):
        return f"Link {idx + 1}"
    return f"Link {idx + 1} frei"


def update_link_slot_buttons(app):
    for idx, btn in enumerate(app.link_slot_buttons):
        try:
            btn.configure(text=link_slot_display_name(app, idx))
        except Exception:
            pass


def link_slot_summary(app, slot):
    name = (slot.get("custom_name") or "").strip() or f"Link {slot.get('slot')}"
    link_type = (slot.get("link_type") or "-").strip() or "-"
    target = (slot.get("target") or "").strip()
    if link_type == "Systemlink":
        target = (slot.get("app_name") or "").strip() or target
    target = target or "-"
    return name, link_type, target


def refresh_link_table(app):
    table = _app_value(app, "link_table")
    if table is None:
        return
    for item in table.get_children():
        table.delete(item)
    for slot in app.link_slots:
        name, link_type, target = link_slot_summary(app, slot)
        iid = f"link-slot-{slot['slot']}"
        table.insert(
            "",
            "end",
            iid=iid,
            values=(slot["slot"], name, link_type, target),
        )


def load_link_slot_into_form(app, slot_no):
    slot = _link_slot_at(app, slot_no)
    if slot is None:
        return
    _app_var_set(app, "link_slot_choice", str(slot_no))
    custom_name = (slot.get("custom_name") or "").strip()
    _app_var_set(app, "link_custom_name_var", custom_name)
    _set_link_custom_name_autofill(app, "")
    _app_var_set(
        app,
        "link_type_var",
        (slot.get("link_type") or "Systemlink").strip() or "Systemlink",
    )
    _app_var_set(app, "link_target_var", (slot.get("target") or "").strip())
    _app_var_set(app, "link_system_app_var", "")

    if (slot.get("link_type") or "").strip() == "Systemlink":
        _app_var_set(app, "link_system_app_var", _systemlink_form_label(app, slot))

    sync_link_target_widgets(app)


def on_link_slot_select(app, _event=None):
    load_link_slot_into_form(app, _selected_link_slot_no(app))


def on_link_table_select(app, _event=None):
    table = _app_value(app, "link_table")
    sel = table.selection() if table is not None else ()
    if not sel:
        return
    values = table.item(sel[0], "values")
    if not values:
        return
    try:
        slot_no = int(values[0])
    except (TypeError, ValueError):
        return
    load_link_slot_into_form(app, slot_no)


def _link_table_slot_no_for_row(app, row_id: str) -> int | None:
    table = _app_value(app, "link_table")
    if table is None or not row_id:
        return None
    try:
        values = table.item(row_id, "values")
    except Exception:
        return None
    if not values:
        return None
    try:
        slot_no = int(values[0])
    except (TypeError, ValueError, IndexError):
        return None
    return slot_no if 1 <= slot_no <= LINK_SLOT_COUNT else None


def remove_link_table_selection(app):
    table = _app_value(app, "link_table")
    if table is None:
        return
    try:
        selection = tuple(table.selection())
    except Exception:
        selection = ()
    if not selection:
        app.log("Kein Link-Slot ausgewählt.")
        return
    slot_no = _link_table_slot_no_for_row(app, selection[0])
    if slot_no is None:
        app.log("Ungültiger Link-Slot ausgewählt.")
        return
    _app_var_set(app, "link_slot_choice", str(slot_no))
    clear_link_slot(app, confirm=True)


def show_link_table_context_menu(app, event):
    table = _app_value(app, "link_table")
    if table is None:
        return None
    row_id = ""
    try:
        row_id = table.identify_row(event.y)
    except Exception:
        row_id = ""
    if row_id:
        try:
            table.selection_set(row_id)
            table.focus(row_id)
        except Exception:
            pass
        slot_no = _link_table_slot_no_for_row(app, row_id)
        if slot_no is not None:
            load_link_slot_into_form(app, slot_no)

    menu = tk.Menu(table, tearoff=0)
    has_row = bool(row_id)
    menu.add_command(
        label=app.tr("menu_link_remove", "Link entfernen"),
        command=lambda: remove_link_table_selection(app),
        state="normal" if has_row else "disabled",
    )
    show_fn = getattr(app, "_show_context_menu", None)
    if callable(show_fn):
        return show_fn(menu, event)
    return None


def on_link_type_change(app, _event=None):
    sync_link_target_widgets(app)


def on_systemlink_app_select(app, _event=None):
    entry = _selected_systemlink_entry(app)
    if entry:
        _app_var_set(app, "link_target_var", f"desktop:{entry['desktop_id']}")
        current_name = _link_custom_name(app)
        previous_autofill = _link_custom_name_autofill(app)
        next_name = str(entry.get("name") or entry.get("label") or "").strip()
        if next_name and (not current_name or current_name == previous_autofill):
            _app_var_set(app, "link_custom_name_var", next_name)
            _set_link_custom_name_autofill(app, next_name)


def sync_link_target_widgets(app):
    link_type = _selected_link_type(app)
    label = _app_value(app, "link_target_label")
    target_entry = _app_value(app, "link_target_entry")
    system_frame = _app_value(app, "link_system_frame")
    if link_type == "Systemlink":
        if label is not None:
            label.configure(text=app.tr("links_label_program", "Programm:"))
        if target_entry is not None:
            target_entry.grid_remove()
        if system_frame is not None:
            system_frame.grid()
    else:
        if label is not None:
            label.configure(
                text=app.tr("links_label_target_path_url", "Ziel / Pfad / URL:")
            )
        if system_frame is not None:
            system_frame.grid_remove()
        if target_entry is not None:
            target_entry.grid()


def build_systemlink_target(app):
    if _selected_link_type(app) != "Systemlink":
        return str(_app_var_get(app, "link_target_var", "") or "").strip(), "", "", ""

    entry = _selected_systemlink_entry(app)
    if not entry:
        return "", "", "", ""
    return (
        f"desktop:{entry['desktop_id']}",
        entry["name"],
        entry["desktop_id"],
        entry["desktop_file"],
    )


def assign_link_slot(app):
    slot_no = _selected_link_slot_no(app)
    slot = _link_slot_at(app, slot_no)
    if slot is None:
        app.log("Ungültiger Link-Slot ausgewählt.")
        return

    link_type = _selected_link_type(app)
    custom_name = _link_custom_name(app)
    if link_type not in ("Systemlink", "Externer Link"):
        app.log("Bitte einen gültigen Link-Typ auswählen.")
        return
    target, app_name, desktop_id, desktop_file = _link_target_fields(app)
    if not target:
        if link_type == "Systemlink":
            app.log(
                "Bitte ein Programm auswählen oder eine manuelle Eingabe hinterlegen."
            )
        else:
            app.log("Bitte eine gültige HTTP/HTTPS-URL eintragen.")
        return

    if link_type == "Systemlink":
        lowered = target.strip().lower()
        expanded = os.path.expanduser(target)
        if not (
            target.startswith("desktop:")
            or os.path.exists(expanded)
            or lowered in ("vscode", "code", "codium", "code-insiders")
        ):
            app.log(
                "Unsicherer Systemlink blockiert. Bitte Desktop-App oder lokalen Pfad verwenden."
            )
            return

    slot["custom_name"] = custom_name
    slot["link_type"] = link_type
    slot["target"] = target
    slot["app_name"] = app_name
    slot["desktop_id"] = desktop_id
    slot["desktop_file"] = desktop_file
    save_link_slots_config(app)
    update_link_slot_buttons(app)
    refresh_link_table(app)
    target_label = custom_name or app_name or target
    app.log(f"Link-Zuordnung übernommen: Slot {slot_no} -> {target_label}.")


def clear_link_slot(app, confirm=False):
    slot_no = _selected_link_slot_no(app)
    slot = _link_slot_at(app, slot_no)
    if slot is None:
        app.log("Ungültiger Link-Slot ausgewählt.")
        return
    has_assignment = _link_slot_has_assignment(slot)
    if confirm and has_assignment:
        ok = messagebox.askyesno(
            "Link-Zuordnung aufheben",
            f"Slot {slot_no} wird geleert. Fortfahren?",
            parent=app,
        )
        if not ok:
            app.log(f"Link-Zuordnung aufheben abgebrochen: Slot {slot_no}.")
            return
    _clear_link_slot_payload(slot)
    save_link_slots_config(app)
    load_link_slot_into_form(app, slot_no)
    update_link_slot_buttons(app)
    refresh_link_table(app)
    app.log(f"Link-Zuordnung aufgehoben: Slot {slot_no}.")


def build_form_link_slot(app):
    target, app_name, desktop_id, desktop_file = _link_target_fields(app)
    return {
        "slot": _selected_link_slot_no(app, default=1) or 1,
        "custom_name": _link_custom_name(app),
        "link_type": _selected_link_type(app),
        "target": target,
        "app_name": app_name,
        "desktop_id": desktop_id,
        "desktop_file": desktop_file,
    }


def test_link_slot(app):
    slot = build_form_link_slot(app)
    if not link_slot_configured(app, slot):
        app.log("Bitte erst Typ und Ziel für den Link-Test ausfüllen.")
        return
    app._execute_link_slot(slot, test_mode=True)


def open_link_slot(app, idx):
    if idx < 0 or idx >= len(app.link_slots):
        return
    slot = app.link_slots[idx]
    if not link_slot_configured(app, slot):
        app.log(f"Link-Slot {idx + 1} ist frei.")
        tab_links = _app_value(app, "tab_links")
        if tab_links is not None:
            app._select_system_tab(tab_links)
            load_link_slot_into_form(app, idx + 1)
        return
    app._execute_link_slot(slot)


def resolve_manual_system_command(app, target):
    raw = (target or "").strip()
    if not raw:
        return []
    try:
        parts = shlex.split(raw)
    except ValueError:
        parts = raw.split()
    if not parts:
        return []
    bin_part = parts[0]

    if has_cmd(bin_part):
        return parts

    expanded_bin = os.path.expanduser(bin_part)
    if os.path.isfile(expanded_bin) and os.access(expanded_bin, os.X_OK):
        parts[0] = expanded_bin
        return parts

    resolved = shutil.which(bin_part)
    if resolved:
        parts[0] = resolved
        return parts

    return []


def find_wireshark_desktop_file(app):
    env_desktop = os.environ.get("WIRESHARK_DESKTOP_FILE", "").strip()
    if env_desktop and os.path.isfile(env_desktop):
        return env_desktop

    search_dirs = [
        os.path.expanduser("~/.local/share/applications"),
        "/usr/local/share/applications",
        "/usr/share/applications",
    ]
    candidates = [
        "wireshark.desktop",
        "org.wireshark.Wireshark.desktop",
    ]
    for base in search_dirs:
        for name in candidates:
            candidate = os.path.join(base, name)
            if os.path.isfile(candidate):
                return candidate
    return ""


def find_desktop_entry_by_query(app, query):
    q = (query or "").strip().lower()
    if not q:
        return None

    entries = list(_app_value(app, "desktop_app_entries", []) or [])
    best = None

    for entry in entries:
        name = (entry.get("name") or "").strip().lower()
        label = (entry.get("label") or "").strip().lower()
        desktop_id = (entry.get("desktop_id") or "").strip().lower()
        if q in {name, label, desktop_id, desktop_id.replace(".desktop", "")}:
            return entry

    candidates = []
    for entry in entries:
        name = (entry.get("name") or "").strip().lower()
        label = (entry.get("label") or "").strip().lower()
        desktop_id = (entry.get("desktop_id") or "").strip().lower()
        if q in name or q in label or q in desktop_id:
            rank = min(len(name) or 999, len(label) or 999, len(desktop_id) or 999)
            candidates.append((rank, entry))

    if candidates:
        candidates.sort(key=lambda item: item[0])
        best = candidates[0][1]

    return best


def find_flatpak_app_id_by_query(app, query):
    q = (query or "").strip().lower()
    if not q or not has_cmd("flatpak"):
        return ""

    rc, out = run_cmd(
        ["flatpak", "list", "--app", "--columns=application,name"],
        timeout=8,
    )
    if rc != 0 or not out:
        return ""

    rows = []
    for raw in out.splitlines():
        line = (raw or "").strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if not parts:
            continue
        app_id = parts[0]
        app_name = parts[1] if len(parts) > 1 else ""
        rows.append((app_id, app_name))

    for app_id, app_name in rows:
        app_id_l = app_id.lower()
        app_name_l = app_name.lower()
        if q in {app_id_l, app_name_l}:
            return app_id
        if q == app_id_l.split(".")[-1]:
            return app_id

    candidates = []
    for app_id, app_name in rows:
        app_id_l = app_id.lower()
        app_name_l = app_name.lower()
        if q in app_id_l or (app_name_l and q in app_name_l):
            rank = min(len(app_id_l), len(app_name_l) if app_name_l else 999)
            candidates.append((rank, app_id))
    if candidates:
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    return ""


def resolve_wireshark_launcher(app):
    for candidate in [
        get_cmd_path("wireshark"),
        "/usr/bin/wireshark",
        "/usr/local/bin/wireshark",
        "/snap/bin/wireshark",
        "/var/lib/flatpak/exports/bin/org.wireshark.Wireshark",
        os.path.expanduser(
            "~/.local/share/flatpak/exports/bin/org.wireshark.Wireshark"
        ),
    ]:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return {"kind": "binary", "target": candidate}

    desktop_entry = find_desktop_entry_by_query(app, "wireshark")
    if desktop_entry:
        desktop_id = (desktop_entry.get("desktop_id") or "").strip()
        if desktop_id:
            return {"kind": "desktop", "target": desktop_id}

    desktop_file = find_wireshark_desktop_file(app)
    if desktop_file:
        return {"kind": "desktop_file", "target": desktop_file}

    flatpak_id = find_flatpak_app_id_by_query(app, "wireshark")
    if flatpak_id:
        return {"kind": "flatpak", "target": flatpak_id}

    return {"kind": "", "target": ""}


def open_local_target(app, target):
    if target.startswith("desktop:"):
        desktop_id = target.split(":", 1)[1].strip()
        if not desktop_id:
            raise RuntimeError("Ungültiger Desktop-Starter.")
        entry = app.desktop_app_by_id.get(desktop_id)
        if has_cmd("gtk-launch"):
            subprocess.Popen(
                ["gtk-launch", desktop_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.expanduser("~"),
            )
            app.log(f"Systemlink gestartet: {desktop_id}")
            return True
        if entry and entry.get("exec"):
            proc = subprocess.Popen(
                entry["exec"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.expanduser("~"),
            )
            app.log(f"Systemlink gestartet: {entry['exec'][0]} (PID {proc.pid}).")
            return True
        raise RuntimeError("Desktop-Starter konnte nicht ausgeführt werden.")

    expanded = os.path.expanduser(target)
    if os.path.exists(expanded):
        if has_cmd("xdg-open"):
            subprocess.Popen(
                ["xdg-open", expanded],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            app.log(f"Systemlink geöffnet: {expanded}")
            return True
        raise RuntimeError("xdg-open ist nicht verfügbar.")

    lowered = target.strip().lower()
    if lowered in ("vscode", "code", "codium", "code-insiders"):
        app.vscode_async()
        return True

    parts = resolve_manual_system_command(app, target)
    if parts:
        proc = subprocess.Popen(
            parts,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.path.expanduser("~"),
        )
        app.log(f"Systemlink gestartet: {parts[0]} (PID {proc.pid}).")
        return True

    launch_candidate = (target or "").strip()
    if has_cmd("gtk-launch") and launch_candidate:
        launch_ids = [launch_candidate]
        if not launch_candidate.endswith(".desktop"):
            launch_ids.append(f"{launch_candidate}.desktop")
        for launch_id in launch_ids:
            try:
                rc = subprocess.run(
                    ["gtk-launch", launch_id],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=os.path.expanduser("~"),
                    timeout=5,
                    check=False,
                ).returncode
                if rc == 0:
                    app.log(f"Systemlink gestartet: {launch_id}")
                    return True
            except Exception:
                continue

    matched_entry = find_desktop_entry_by_query(app, launch_candidate)
    if matched_entry:
        desktop_id = (matched_entry.get("desktop_id") or "").strip()
        if desktop_id and has_cmd("gtk-launch"):
            try:
                rc = subprocess.run(
                    ["gtk-launch", desktop_id],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=os.path.expanduser("~"),
                    timeout=5,
                    check=False,
                ).returncode
                if rc == 0:
                    app.log(f"Systemlink gestartet: {desktop_id}")
                    return True
            except Exception:
                pass
        exec_cmd = matched_entry.get("exec") or []
        if exec_cmd:
            try:
                proc = subprocess.Popen(
                    exec_cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=os.path.expanduser("~"),
                )
                app.log(f"Systemlink gestartet: {exec_cmd[0]} (PID {proc.pid}).")
                return True
            except Exception:
                pass

    if has_cmd("xdg-open") and launch_candidate:
        try:
            rc = subprocess.run(
                ["xdg-open", os.path.expanduser(launch_candidate)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                check=False,
            ).returncode
            if rc == 0:
                app.log(f"Systemlink geöffnet: {launch_candidate}")
                return True
        except Exception:
            pass

    flatpak_app_id = find_flatpak_app_id_by_query(app, launch_candidate)
    if flatpak_app_id and has_cmd("flatpak"):
        try:
            proc = subprocess.Popen(
                ["flatpak", "run", flatpak_app_id],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.expanduser("~"),
            )
            app.log(
                f"Systemlink gestartet: flatpak run {flatpak_app_id} (PID {proc.pid})."
            )
            return True
        except Exception:
            pass

    raise RuntimeError(
        "Manueller Befehl/Starter konnte nicht ausgeführt werden. Bitte gültigen Befehl, Desktop-ID oder Dateipfad verwenden."
    )


def open_external_target(app, target):
    url = normalize_external_url_target(target)
    if not url:
        raise RuntimeError("Ungültige oder unsichere URL (nur HTTP/HTTPS erlaubt).")
    if has_cmd("xdg-open"):
        subprocess.Popen(
            ["xdg-open", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        opened = webbrowser.open(url)
        if not opened:
            raise RuntimeError("Standardbrowser konnte nicht geöffnet werden.")
    app.log(f"Externer Link geöffnet: {url}")
    return True


def execute_link_slot(app, slot, test_mode=False):
    link_type = (slot.get("link_type") or "").strip()
    target = (slot.get("target") or "").strip()
    if not link_type or not target:
        app.log("Link-Slot ist nicht vollständig konfiguriert.")
        return False
    try:
        if link_type == "Systemlink":
            return open_local_target(app, target)
        if link_type == "Externer Link":
            return open_external_target(app, target)
        app.log(f"Unbekannter Link-Typ: {link_type}")
        return False
    except Exception as exc:
        prefix = (
            "Link-Test fehlgeschlagen"
            if test_mode
            else "Link konnte nicht geöffnet werden"
        )
        app.log(f"{prefix}: {exc}")
        return False
