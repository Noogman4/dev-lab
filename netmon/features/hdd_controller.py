"""HDD controller helpers for NetMon."""

from __future__ import annotations

import json
import os
import re
import threading
from tkinter import messagebox, simpledialog

try:
    from netmon.config.constants import HDD_SLOT_COUNT
except ModuleNotFoundError:
    from config.constants import HDD_SLOT_COUNT

try:
    from netmon.core.utils import call_in_ui_thread, human_size, safe_write_json
except ModuleNotFoundError:
    from core.utils import call_in_ui_thread, human_size, safe_write_json

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.services import hdd_mount_service
except ModuleNotFoundError:
    from services import hdd_mount_service

try:
    from netmon.core.tooling import has_cmd
except ModuleNotFoundError:
    from core.tooling import has_cmd


def _app_value(app, name, default):
    return app.__dict__.get(name, default)


def _app_callable(app, name, fallback):
    candidate = app.__dict__.get(name)
    return candidate if callable(candidate) else fallback


def _call_with_optional_select_tab(func, idx, select_tab, log_event=True):
    try:
        return func(idx, select_tab=select_tab, log_event=log_event)
    except TypeError:
        try:
            return func(idx, select_tab=select_tab)
        except TypeError:
            return func(idx)


def _detected_disks(app):
    return _app_value(app, "detected_disks", []) or []


def _detected_disks_by_device(app):
    return _app_value(app, "detected_disks_by_device", {}) or {}


def _selected_hdd_slot_no(app) -> int:
    try:
        slot_no = int((app.hdd_slot_choice.get() or "0").strip())
    except ValueError:
        slot_no = 0
    return slot_no if 1 <= slot_no <= HDD_SLOT_COUNT else 0


def _selected_hdd_slot(app):
    slot_no = _selected_hdd_slot_no(app)
    if not slot_no:
        return 0, None
    slots = list(_app_value(app, "hdd_slots", []) or [])
    if slot_no > len(slots):
        return 0, None
    return slot_no, slots[slot_no - 1]


def _hdd_slot_has_assignment(slot):
    slot = slot or {}
    return bool(
        (slot.get("device") or "").strip()
        or (slot.get("device_uuid") or "").strip()
        or (slot.get("mountpoint") or "").strip()
        or (slot.get("custom_name") or "").strip()
    )


def _clear_hdd_slot_fields(slot):
    slot["device"] = ""
    slot["device_uuid"] = ""
    slot["mountpoint"] = ""
    slot["custom_name"] = ""
    slot["auto_mount"] = False


def _clear_device_slot_assignments(app, device, *, skip_slot_no=0, device_uuid=""):
    device = str(device or "").strip()
    device_uuid = str(device_uuid or "").strip()
    for idx, slot in enumerate(_app_value(app, "hdd_slots", []) or [], start=1):
        if idx == skip_slot_no:
            continue
        slot_device = (slot.get("device") or "").strip()
        slot_uuid = (slot.get("device_uuid") or "").strip()
        if slot_device == device or (device_uuid and slot_uuid == device_uuid):
            _clear_hdd_slot_fields(slot)


def _assign_disk_to_hdd_slot(slot, device, disk, custom_name):
    disk = disk or {}
    slot["device"] = str(device or "").strip()
    slot["device_uuid"] = str(disk.get("uuid") or "").strip()
    slot["mountpoint"] = (
        str(disk.get("mountpoint") or "").strip()
        or str(slot.get("mountpoint") or "").strip()
        or f"/mnt/{os.path.basename(device or '') or 'netmon_hdd'}"
    )
    slot["custom_name"] = str(custom_name or "").strip()


_SAFE_MOUNT_BASES = ("/mnt/", "/media/", "/run/media/")


def _slot_mountpoint(slot, device):
    default = f"/mnt/{os.path.basename(device) or 'netmon_hdd'}"
    raw = (slot.get("mountpoint") or "").strip()
    if not raw:
        return default
    resolved = os.path.realpath(raw)
    if any(resolved.startswith(base) for base in _SAFE_MOUNT_BASES):
        return resolved
    return default


def default_hdd_slots():
    return [
        {
            "slot": i + 1,
            "custom_name": "",
            "device": "",
            "device_uuid": "",
            "mountpoint": "",
            "auto_mount": False,
        }
        for i in range(HDD_SLOT_COUNT)
    ]


def load_hdd_slots_config(app):
    slots = default_hdd_slots()
    try:
        if os.path.isfile(app.hdd_config_path):
            with open(app.hdd_config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    slot_no = int(item.get("slot", 0))
                    if 1 <= slot_no <= HDD_SLOT_COUNT:
                        slots[slot_no - 1] = {
                            "slot": slot_no,
                            "custom_name": (item.get("custom_name") or "").strip(),
                            "device": (item.get("device") or "").strip(),
                            "device_uuid": (item.get("device_uuid") or "").strip(),
                            "mountpoint": (item.get("mountpoint") or "").strip(),
                            "auto_mount": bool(item.get("auto_mount", False)),
                        }
    except Exception as e:
        app.log(f"HDD Slot-Konfig konnte nicht geladen werden: {e}")
    return slots


def save_hdd_slots_config(app):
    ok, err = safe_write_json(
        app.hdd_config_path,
        app.hdd_slots,
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        app.log(f"HDD Slot-Konfig konnte nicht gespeichert werden: {err}")


def save_hdd_config(app):
    save_hdd_slots_config(app)


def hdd_slot_configured(slot):
    return bool((slot.get("device") or "").strip())


def hdd_auto_mount_enabled(slot):
    return bool((slot or {}).get("auto_mount", False))


def hdd_find_device_by_uuid(app, device_uuid):
    device_uuid = (device_uuid or "").strip()
    if not device_uuid:
        return None
    for disk in _detected_disks(app):
        if (disk.get("uuid") or "").strip() == device_uuid:
            return disk
    return None


def hdd_resolve_slot_device(app, slot):
    """Resolve a display hint without silently changing a saved device identity."""
    configured_device = (slot.get("device") or "").strip()
    configured_uuid = (slot.get("device_uuid") or "").strip()
    if configured_device and not configured_device.startswith("/dev/"):
        return "", None
    disk = _detected_disks_by_device(app).get(configured_device)
    if disk:
        if configured_uuid and (disk.get("uuid") or "").strip() != configured_uuid:
            return "", None
        return configured_device, disk
    if configured_device and os.path.exists(configured_device):
        return "", None
    if configured_uuid:
        matches = [
            disk
            for disk in _detected_disks(app)
            if (disk.get("uuid") or "").strip() == configured_uuid
        ]
        if len(matches) == 1:
            return (matches[0].get("device") or "").strip(), matches[0]
    return "", None


def slot_for_device(app, device):
    for slot in app.hdd_slots:
        slot_device, _slot_disk = hdd_resolve_slot_device(app, slot)
        if slot_device == device:
            return slot.get("slot")
    return None


def refresh_hdd_table(app, keep_selection=True):
    selected = app.hdd_selected_device if keep_selection else None
    for item in app.hdd_table.get_children():
        app.hdd_table.delete(item)
    for disk in app.detected_disks:
        status = disk.get("status") or (
            app.tr("hdd_status_mounted", "mounted")
            if disk.get("mounted")
            else app.tr("hdd_status_not_mounted", "not mounted")
        )
        slot_no = slot_for_device(app, disk.get("device") or "")
        slot_txt = str(slot_no) if slot_no else "-"
        label_model = disk.get("label") or disk.get("model") or "-"
        app.hdd_table.insert(
            "",
            "end",
            iid=disk.get("device") or f"disk-{len(app.hdd_table.get_children())}",
            values=(
                disk.get("device") or "-",
                label_model,
                disk.get("fstype") or "-",
                human_size(disk.get("size_bytes")),
                status,
                disk.get("mountpoint") or "-",
                slot_txt,
            ),
        )
    if selected and selected in app.hdd_table.get_children():
        app._hdd_programmatic_selection = True
        app._hdd_suppress_next_selection_log_for = selected
        try:
            app.hdd_table.selection_set(selected)
            app.hdd_table.focus(selected)
        finally:
            app._hdd_programmatic_selection = False


def slot_display_name(app, idx):
    slot = app.hdd_slots[idx]
    custom = (slot.get("custom_name") or "").strip()
    if custom:
        return custom
    device, disk = hdd_resolve_slot_device(app, slot)
    if not device:
        return app.tr("hdd_slot_free", "Slot {slot} free").format(slot=idx + 1)
    disk = disk or {}
    return (
        (disk.get("label") or "").strip() or (disk.get("model") or "").strip() or device
    )


def update_hdd_slot_button_labels(app):
    for idx, btn in enumerate(app.hdd_slot_name_buttons):
        try:
            btn.configure(text=slot_display_name(app, idx))
        except Exception:
            pass


def update_hdd_buttons(app):
    update_hdd_slot_button_labels(app)


def on_hdd_name_focus_in(app, _event=None):
    app.hdd_name_editing = True


def on_hdd_name_focus_out(app, _event=None):
    app.hdd_name_editing = False


def on_hdd_name_changed(app, *_args):
    if app._hdd_name_programmatic_update:
        return
    app.hdd_name_dirty = True


def set_hdd_name_from_model(app, name):
    value = (name or "").strip()
    app._hdd_name_programmatic_update = True
    try:
        app.hdd_custom_name_var.set(value)
        app.hdd_last_loaded_name = value
        app.hdd_name_dirty = False
    finally:
        app._hdd_name_programmatic_update = False


def on_hdd_table_select(app, _event=None):
    sel = app.hdd_table.selection()
    if not sel:
        app.hdd_selected_device = None
        return
    dev = sel[0]
    current_info_device = str(
        app.__dict__.get("hdd_info_selected_device") or ""
    ).strip()
    app.hdd_selected_device = dev
    disk = app.detected_disks_by_device.get(dev)
    if not disk:
        return
    suppress_log = False
    suppressed_device = app.__dict__.get("_hdd_suppress_next_selection_log_for")
    if suppressed_device == dev:
        suppress_log = True
        app._hdd_suppress_next_selection_log_for = None
    if current_info_device == dev:
        suppress_log = True
    hdd_info_for_device_async(
        app,
        dev,
        log_event=not suppress_log
        and not bool(app.__dict__.get("_hdd_programmatic_selection", False)),
    )

    if app.hdd_name_editing or app.hdd_name_dirty:
        return

    slot_no = slot_for_device(app, dev)
    if slot_no:
        app.hdd_slot_choice.set(str(slot_no))
        set_hdd_name_from_model(
            app,
            (app.hdd_slots[slot_no - 1].get("custom_name") or "").strip(),
        )
    else:
        set_hdd_name_from_model(app, (disk.get("label") or "").strip())


def hdd_sync_auto_mount_ui(app, state=None):
    if state is None:
        device = str(getattr(app, "hdd_selected_device", "") or "").strip()
        state = hdd_collect_device_state(app, device) if device else None

    available = False
    enabled = False
    hint = ""
    if state and (state.get("device") or "").strip():
        slot_no = slot_for_device(app, state.get("device") or "")
        if slot_no:
            slot = app.hdd_slots[slot_no - 1]
            enabled = hdd_auto_mount_enabled(slot)
            available = True
            if state.get("is_luks"):
                available = False
                enabled = False
                if slot.get("auto_mount"):
                    slot["auto_mount"] = False
                    save_hdd_config(app)
                hint = app.tr(
                    "hdd_automount_hint_luks",
                    "LUKS or encrypted devices cannot be mounted automatically.",
                )
        else:
            hint = app.tr(
                "hdd_automount_hint_slot_required",
                "Automount is only available for devices assigned to an HDD slot.",
            )

    auto_mount_var = app.__dict__.get("hdd_info_auto_mount_var")
    auto_mount_check = app.__dict__.get("hdd_info_auto_mount_check")
    auto_mount_hint_var = app.__dict__.get("hdd_info_auto_mount_hint_var")

    app._hdd_auto_mount_programmatic_update = True
    try:
        if auto_mount_var is not None:
            auto_mount_var.set(bool(enabled))
        try:
            if auto_mount_check is not None:
                auto_mount_check.configure(
                    state=("normal" if available else "disabled")
                )
        except Exception:
            pass
        try:
            if auto_mount_hint_var is not None:
                auto_mount_hint_var.set(hint)
        except Exception:
            pass
    finally:
        app._hdd_auto_mount_programmatic_update = False


def on_hdd_auto_mount_toggle(app):
    if getattr(app, "_hdd_auto_mount_programmatic_update", False):
        return
    device = str(getattr(app, "hdd_selected_device", "") or "").strip()
    if not device:
        hdd_sync_auto_mount_ui(app, None)
        return
    state = hdd_collect_device_state(app, device)
    slot_no = slot_for_device(app, device)
    if not slot_no:
        hdd_sync_auto_mount_ui(app, state)
        app.log(
            app.tr(
                "hdd_automount_requires_slot",
                "HDD automount requires a slot assignment for the selected device.",
            )
        )
        return
    if state.get("is_luks"):
        app.hdd_slots[slot_no - 1]["auto_mount"] = False
        save_hdd_config(app)
        hdd_sync_auto_mount_ui(app, state)
        app.log(
            app.tr(
                "hdd_automount_luks_not_supported",
                "LUKS or encrypted devices cannot be mounted automatically.",
            )
        )
        return

    auto_mount_var = app.__dict__.get("hdd_info_auto_mount_var")
    enabled = bool(auto_mount_var.get()) if auto_mount_var is not None else False
    app.hdd_slots[slot_no - 1]["auto_mount"] = enabled
    save_hdd_config(app)
    hdd_sync_auto_mount_ui(app, state)
    app.log(
        app.tr(
            "hdd_automount_toggled",
            "HDD automount {state}: {device}.",
        ).format(
            state=(
                app.tr("label_enabled", "enabled")
                if enabled
                else app.tr("label_disabled", "disabled")
            ),
            device=device,
        )
    )


def hdd_collect_device_state(app, device):
    device = str(device or "").strip()
    slot_no = slot_for_device(app, device)
    slot = app.hdd_slots[slot_no - 1] if slot_no else {}
    disk = _detected_disks_by_device(app).get(device)
    mountpoint = (
        (slot.get("mountpoint") or "").strip()
        or str((disk or {}).get("mountpoint") or "").strip()
        or (f"/mnt/{os.path.basename(device)}" if device else "")
    )

    if not device:
        return {
            "slot": (slot_no - 1) if slot_no else -1,
            "custom_name": (slot.get("custom_name") or "").strip(),
            "device": "",
            "mountpoint": mountpoint,
            "configured": bool(slot_no),
            "present": False,
            "mounted": None,
            "actual_target": "",
            "fstype": "",
            "label": "",
            "model": "",
            "size_bytes": None,
            "usage": None,
            "is_luks": False,
            "luks_locked": False,
            "luks_mapper_name": "",
            "luks_mapper_path": "",
        }

    luks = hdd_luks_info_for_device(app, device)
    mounted, actual_target = hdd_is_mounted(app, device, mountpoint)
    if not mounted and luks.get("mounted_targets"):
        actual_target = luks["mounted_targets"][0]
        mounted = True
    if not actual_target and disk:
        actual_target = (disk.get("mountpoint") or "").strip()
    usage = hdd_usage_for_mountpoint(actual_target or mountpoint) if mounted else None
    return {
        "slot": (slot_no - 1) if slot_no else -1,
        "custom_name": (slot.get("custom_name") or "").strip(),
        "device": device,
        "mountpoint": mountpoint,
        "configured": bool(slot_no),
        "present": disk is not None,
        "mounted": mounted if disk is not None else None,
        "actual_target": actual_target,
        "fstype": (disk.get("fstype") if disk else "") or "",
        "label": (disk.get("label") if disk else "") or "",
        "model": (disk.get("model") if disk else "") or "",
        "size_bytes": disk.get("size_bytes") if disk else None,
        "usage": usage,
        "is_luks": luks.get("is_luks", bool(disk.get("is_luks")) if disk else False),
        "luks_locked": luks.get(
            "locked", bool(disk.get("luks_locked")) if disk else False
        ),
        "luks_mapper_name": luks.get("mapper_name") or "",
        "luks_mapper_path": luks.get("mapper_path") or "",
    }


def assign_selected_disk_to_slot(app):
    sel = app.hdd_table.selection()
    if not sel:
        app.log("Bitte erst eine erkannte Festplatte auswählen.")
        return
    dev = sel[0]
    disk = app.detected_disks_by_device.get(dev)
    if not disk:
        app.log("Ausgewählte Festplatte ist nicht mehr verfügbar.")
        return
    try:
        slot_no = int((app.hdd_slot_choice.get() or "0").strip())
    except ValueError:
        slot_no = 0
    if not (1 <= slot_no <= HDD_SLOT_COUNT):
        app.log("Ungültiger Slot ausgewählt.")
        return

    disk_uuid = (disk.get("uuid") or "").strip()
    _clear_device_slot_assignments(
        app,
        dev,
        skip_slot_no=slot_no,
        device_uuid=disk_uuid,
    )

    target = app.hdd_slots[slot_no - 1]
    previous_target_device = (target.get("device") or "").strip()
    _assign_disk_to_hdd_slot(
        target,
        dev,
        disk,
        (app.hdd_custom_name_var.get() or "").strip(),
    )
    target["auto_mount"] = (
        bool(target.get("auto_mount")) if previous_target_device == dev else False
    )
    save_hdd_config(app)
    app.hdd_last_loaded_name = target["custom_name"]
    app.hdd_name_dirty = False
    refresh_hdd_table(app, keep_selection=True)
    update_hdd_buttons(app)
    app.hdd_refresh_async()
    hdd_sync_auto_mount_ui(app)
    app.log(f"HDD Zuordnung übernommen: {dev} -> Slot {slot_no}.")


def clear_slot_assignment(app, confirm=False):
    try:
        slot_no = int((app.hdd_slot_choice.get() or "0").strip())
    except ValueError:
        slot_no = 0
    if not (1 <= slot_no <= HDD_SLOT_COUNT):
        app.log("Ungültiger Slot ausgewählt.")
        return

    target = app.hdd_slots[slot_no - 1]
    had_assignment = _hdd_slot_has_assignment(target)
    if confirm and had_assignment:
        slot_label = (target.get("custom_name") or "").strip() or f"Slot {slot_no}"
        ok = messagebox.askyesno(
            "HDD-Zuordnung aufheben",
            f"{slot_label} wird vom Slot getrennt. Fortfahren?",
            parent=app,
        )
        if not ok:
            app.log(f"HDD Zuordnung aufheben abgebrochen: Slot {slot_no}.")
            return
    target["device"] = ""
    target["device_uuid"] = ""
    target["mountpoint"] = ""
    target["custom_name"] = ""
    app.hdd_selected_device = None
    save_hdd_config(app)
    set_hdd_name_from_model(app, "")
    refresh_hdd_table(app, keep_selection=False)
    update_hdd_buttons(app)
    hdd_sync_auto_mount_ui(app, None)

    app.hdd_slot_states[slot_no - 1] = {
        "configured": False,
        "present": False,
        "mounted": None,
    }
    app._hdd_apply_slot_lights()
    app.log(f"HDD Zuordnung aufgehoben: Slot {slot_no}.")


def hdd_sanitize_mapper_name(device):
    base = os.path.basename(device or "slot")
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", base)
    return f"netmon_{safe}"


def hdd_list_mappers():
    mapper_dir = "/dev/mapper"
    try:
        entries = sorted(
            name for name in os.listdir(mapper_dir) if name and name != "control"
        )
    except Exception:
        entries = []
    return entries


def hdd_probe_live_device(device):
    if not device or not has_cmd("lsblk"):
        return {}

    rc, out = run_cmd(
        [
            "lsblk",
            "-J",
            "-p",
            "-o",
            "NAME,PATH,TYPE,FSTYPE,UUID,MOUNTPOINT",
        ],
        timeout=8,
    )
    if rc != 0 or not out.strip():
        return {}
    try:
        data = json.loads(out)
    except Exception:
        return {}

    def find_node(node):
        path = (node.get("path") or node.get("name") or "").strip()
        if path == device:
            return node
        for child in node.get("children") or []:
            found = find_node(child)
            if found:
                return found
        return None

    root = None
    for candidate in data.get("blockdevices", []):
        root = find_node(candidate)
        if root:
            break
    if not root:
        return {}

    info = {
        "device_path": (root.get("path") or root.get("name") or "").strip(),
        "device_uuid": (root.get("uuid") or "").strip(),
        "mapper_name": "",
        "mapper_path": "",
        "mounted_targets": [],
        "mounted_sources": [],
    }

    def walk(node):
        path = (node.get("path") or node.get("name") or "").strip()
        mountpoint = (node.get("mountpoint") or "").strip()
        if mountpoint:
            info["mounted_targets"].append(mountpoint)
            if path:
                info["mounted_sources"].append(path)

        if path.startswith("/dev/mapper/") and not info["mapper_path"]:
            info["mapper_path"] = path
            info["mapper_name"] = os.path.basename(path)

        for child in node.get("children") or []:
            walk(child)

    walk(root)

    info["mounted_targets"] = list(dict.fromkeys(info["mounted_targets"]))
    info["mounted_sources"] = list(dict.fromkeys(info["mounted_sources"]))
    return info


def hdd_luks_info_for_device(app, device):
    disk = _detected_disks_by_device(app).get(device) or {}
    live = hdd_probe_live_device(device)
    mapper_path = (live.get("mapper_path") or "").strip()
    mapper_name = (live.get("mapper_name") or "").strip()
    if not mapper_path:
        mapper_path = (disk.get("luks_mapper_path") or "").strip()
    if not mapper_name:
        mapper_name = (disk.get("luks_mapper_name") or "").strip()
    if not mapper_name and mapper_path.startswith("/dev/mapper/"):
        mapper_name = os.path.basename(mapper_path)

    cached_mapper = (_app_value(app, "hdd_luks_mappers", {}).get(device) or "").strip()
    if not mapper_name:
        mapper_name = cached_mapper
    if not mapper_path and mapper_name and os.path.exists(f"/dev/mapper/{mapper_name}"):
        mapper_path = f"/dev/mapper/{mapper_name}"
    if not mapper_name and mapper_path.startswith("/dev/mapper/"):
        mapper_name = os.path.basename(mapper_path)
    if not mapper_name:
        mapper_name = hdd_sanitize_mapper_name(device)
    if (
        not mapper_path
        and cached_mapper
        and os.path.exists(f"/dev/mapper/{cached_mapper}")
    ):
        mapper_path = f"/dev/mapper/{cached_mapper}"
    if not mapper_path and mapper_name and os.path.exists(f"/dev/mapper/{mapper_name}"):
        mapper_path = f"/dev/mapper/{mapper_name}"

    unlocked = bool(mapper_path)
    if mapper_name and mapper_path:
        _app_value(app, "hdd_luks_mappers", {})[device] = mapper_name

    return {
        "is_luks": bool(disk.get("is_luks")),
        "locked": bool(disk.get("is_luks")) and not unlocked,
        "unlocked": unlocked,
        "mapper_name": mapper_name,
        "mapper_path": mapper_path,
        "mounted_targets": live.get("mounted_targets") or [],
        "mounted_sources": live.get("mounted_sources") or [],
        "device_uuid": (live.get("device_uuid") or disk.get("uuid") or "").strip(),
        "available_mappers": hdd_list_mappers(),
    }


def hdd_find_mount_source(mapper_path):
    mapper_path = (mapper_path or "").strip()
    if not mapper_path or not has_cmd("lsblk"):
        return mapper_path

    rc, out = run_cmd(
        [
            "lsblk",
            "-J",
            "-p",
            "-o",
            "PATH,FSTYPE,TYPE",
            mapper_path,
        ],
        timeout=8,
    )
    if rc != 0 or not out.strip():
        return mapper_path
    try:
        data = json.loads(out)
    except Exception:
        return mapper_path

    def walk(node):
        node_path = (node.get("path") or node.get("name") or "").strip()
        node_fstype = (node.get("fstype") or "").strip()
        if node_path == mapper_path and node_fstype:
            return node_path
        for child in node.get("children") or []:
            child_path = (child.get("path") or child.get("name") or "").strip()
            child_fstype = (child.get("fstype") or "").strip()
            if child_path and child_fstype:
                return child_path
            found = walk(child)
            if found:
                return found
        return None

    for device in data.get("blockdevices", []):
        found = walk(device)
        if found:
            return found
    return mapper_path


def hdd_is_mounted(app, device, mountpoint):
    live = hdd_probe_live_device(device)
    targets = live.get("mounted_targets") or []
    if targets:
        if mountpoint and mountpoint in targets:
            return True, mountpoint
        return True, targets[0]

    sources = []
    if device:
        sources.append(device)
    luks = hdd_luks_info_for_device(app, device)
    mapper_path = (luks.get("mapper_path") or "").strip()
    if mapper_path:
        sources.append(mapper_path)
    sources.extend(luks.get("mounted_sources") or [])
    sources = [src for src in dict.fromkeys(src.strip() for src in sources if src)]

    if has_cmd("findmnt") and mountpoint:
        rc, out = run_cmd(
            ["findmnt", "-rn", "-T", mountpoint, "-o", "SOURCE,TARGET"], timeout=4
        )
        if rc == 0 and out.strip():
            parts = out.split(None, 1)
            source = parts[0].strip() if parts else ""
            target = parts[1].strip() if len(parts) > 1 else mountpoint
            if not sources or not source or source in sources:
                return True, target
    if has_cmd("findmnt"):
        for source in sources:
            rc, out = run_cmd(
                ["findmnt", "-rn", "-S", source, "-o", "TARGET"], timeout=4
            )
            if rc == 0 and out.strip():
                found_targets = [ln.strip() for ln in out.splitlines() if ln.strip()]
                if found_targets:
                    if mountpoint and mountpoint in found_targets:
                        return True, mountpoint
                    return True, found_targets[0]
    if has_cmd("mount") and mountpoint:
        rc, out = run_cmd(["mount"], timeout=4)
        if rc == 0 and out.strip():
            needle = f" on {mountpoint} "
            for line in out.splitlines():
                if needle not in line:
                    continue
                source = line.split(" on ", 1)[0].strip()
                if not sources or source in sources:
                    return True, mountpoint
    return False, ""


def hdd_usage_for_mountpoint(mountpoint):
    if not mountpoint or not has_cmd("df"):
        return None
    rc, out = run_cmd(["df", "-B1", mountpoint], timeout=6)
    if rc != 0 or not out.strip():
        return None
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if len(lines) < 2:
        return None
    cols = lines[-1].split()
    if len(cols) < 6:
        return None
    try:
        return {
            "total": int(cols[1]),
            "used": int(cols[2]),
            "free": int(cols[3]),
            "use_pct": cols[4],
        }
    except (TypeError, ValueError):
        return None


def hdd_collect_slot_state(app, idx):
    slot = app.hdd_slots[idx]
    device, disk = hdd_resolve_slot_device(app, slot)
    mountpoint = (slot.get("mountpoint") or "").strip()
    if not device:
        return {
            "slot": idx,
            "custom_name": (slot.get("custom_name") or "").strip(),
            "device": "",
            "mountpoint": mountpoint,
            "configured": False,
            "present": False,
            "mounted": None,
            "actual_target": "",
            "fstype": "",
            "label": "",
            "model": "",
            "size_bytes": None,
            "usage": None,
            "is_luks": False,
            "luks_locked": False,
            "luks_mapper_name": "",
            "luks_mapper_path": "",
        }
    state = hdd_collect_device_state(app, device)
    state["slot"] = idx
    state["custom_name"] = (slot.get("custom_name") or "").strip()
    state["mountpoint"] = mountpoint
    state["configured"] = True
    return state


def hdd_apply_slot_lights(app):
    for idx, light in enumerate(app.hdd_slot_lights):
        state = app.hdd_slot_states[idx] if idx < len(app.hdd_slot_states) else None
        if not state or not state.get("configured") or not state.get("present"):
            color = "gray"
        elif state.get("is_luks") and state.get("luks_locked"):
            color = "orange"
        elif state.get("mounted") is True:
            color = "green"
        elif state.get("mounted") is False:
            color = "red"
        else:
            color = "gray"
        app.set_light(light, color)
    update_hdd_slot_button_labels(app)


def hdd_refresh_async(app):
    if app.hdd_refresh_running:
        return
    app.hdd_refresh_running = True

    def job():
        disks = app.scan_hdds()
        disks_by_device = {(d.get("device") or ""): d for d in disks if d.get("device")}
        prev_detected = _detected_disks_by_device(app)
        app.detected_disks_by_device = disks_by_device
        states = [hdd_collect_slot_state(app, i) for i in range(len(app.hdd_slots))]
        app.detected_disks_by_device = prev_detected

        def done():
            app.detected_disks = disks
            app.detected_disks_by_device = disks_by_device
            refresh_hdd_table(app, keep_selection=True)
            app.hdd_slot_states = states
            hdd_apply_slot_lights(app)
            app.hdd_refresh_running = False
            if getattr(app, "_hdd_startup_auto_mount_pending", False):
                app._hdd_startup_auto_mount_pending = False
                hdd_startup_auto_mount(app)
            else:
                hdd_sync_auto_mount_ui(app)

        call_in_ui_thread(app, done)

    threading.Thread(target=job, daemon=True).start()


def hdd_render_usage_bar(app, usage):
    app.hdd_usage_canvas.delete("all")
    cw = max(app.hdd_usage_canvas.winfo_width(), 320)
    ch = max(app.hdd_usage_canvas.winfo_height(), 30)
    pad = 6
    x0, y0, x1, y1 = pad, pad, cw - pad, ch - pad
    app.hdd_usage_canvas.create_rectangle(
        x0, y0, x1, y1, fill="#f0f0f0", outline="#999"
    )

    if not usage or not usage.get("total"):
        app.hdd_usage_canvas.create_text(
            cw // 2,
            ch // 2,
            text=app.tr("hdd_usage_unavailable", "No usage data available"),
            fill="#666",
        )
        return

    total = max(int(usage["total"]), 1)
    used = min(max(int(usage.get("used", 0)), 0), total)
    frac = used / total
    ux = x0 + int((x1 - x0) * frac)
    app.hdd_usage_canvas.create_rectangle(x0, y0, ux, y1, fill="#d9534f", outline="")
    pct = usage.get("use_pct") or f"{frac * 100:.0f}%"
    txt = app.tr(
        "hdd_usage_bar_value",
        "Used {used} / Free {free} of {total} ({pct})",
    ).format(
        used=human_size(used),
        free=human_size(usage.get("free")),
        total=human_size(total),
        pct=pct,
    )
    app.hdd_usage_canvas.create_text(cw // 2, ch // 2, text=txt, fill="#111")


def hdd_render_info(app, state):
    mounted = state.get("mounted")
    if mounted is True:
        mounted_txt = app.tr("hdd_status_mounted", "mounted")
    elif mounted is False:
        mounted_txt = app.tr("hdd_status_not_mounted", "not mounted")
    else:
        mounted_txt = app.tr("hdd_status_unknown", "unknown")

    usage = state.get("usage") or {}
    display_name = (
        (state.get("custom_name") or "").strip()
        or (state.get("label") or "").strip()
        or (state.get("model") or "").strip()
        or (state.get("device") or "").strip()
        or "-"
    )
    lines = [
        app.tr("hdd_info_display_name", "Display name: {value}").format(
            value=display_name
        ),
        app.tr("hdd_info_device", "Device: {value}").format(
            value=state.get("device") or "-"
        ),
        app.tr("hdd_info_mountpoint", "Mountpoint: {value}").format(
            value=state.get("mountpoint") or "-"
        ),
        app.tr("hdd_info_status", "Status: {value}").format(value=mounted_txt),
        app.tr("hdd_info_encryption", "Encryption: {value}").format(
            value="LUKS" if state.get("is_luks") else app.tr("value_no", "NO")
        ),
        app.tr("hdd_info_luks_state", "LUKS state: {value}").format(
            value=(
                app.tr("hdd_luks_locked", "locked")
                if state.get("luks_locked")
                else (app.tr("hdd_luks_open", "open") if state.get("is_luks") else "-")
            )
        ),
        app.tr("hdd_info_actual_target", "Current target: {value}").format(
            value=state.get("actual_target") or "-"
        ),
        app.tr("hdd_info_filesystem", "Filesystem: {value}").format(
            value=state.get("fstype") or "-"
        ),
        app.tr("hdd_info_total_size", "Total size: {value}").format(
            value=human_size(state.get("size_bytes"))
        ),
        app.tr("hdd_info_used", "Used: {value}").format(
            value=human_size(usage.get("used"))
        ),
        app.tr("hdd_info_free", "Free: {value}").format(
            value=human_size(usage.get("free"))
        ),
        app.tr("hdd_info_usage", "Usage: {value}").format(
            value=usage.get("use_pct") or "-"
        ),
    ]

    app.hdd_info_text.delete("1.0", "end")
    app.hdd_info_text.insert("end", "\n".join(lines) + "\n")
    app.hdd_info_text.see("1.0")
    hdd_render_usage_bar(app, usage if usage else None)
    hdd_sync_auto_mount_ui(app, state)


def hdd_info_async(app, idx, select_tab=True, log_event=True):
    if idx < 0 or idx >= len(app.hdd_slots):
        return

    def job():
        state = hdd_collect_slot_state(app, idx)

        def show():
            slot_states = _app_value(app, "hdd_slot_states", [])
            if idx < len(slot_states):
                slot_states[idx] = state
            hdd_apply_slot_lights(app)
            app.hdd_selected_device = (state.get("device") or "").strip() or None
            if select_tab:
                app._select_system_tab(app.tab_hdd)
            hdd_render_info(app, state)
            if log_event:
                app.log(f"HDD Info geladen: Slot {idx + 1}.")

        call_in_ui_thread(app, show)

    threading.Thread(target=job, daemon=True).start()


def hdd_info_for_device_async(app, device, log_event=True):
    device = str(device or "").strip()
    if not device:
        return
    app.hdd_info_selected_device = device

    def job():
        state = hdd_collect_device_state(app, device)

        def show():
            if getattr(app, "hdd_info_selected_device", "") != device:
                return
            app.hdd_selected_device = device
            hdd_render_info(app, state)
            if log_event:
                app.log(f"HDD Info geladen: {device}.")

        call_in_ui_thread(app, show)

    threading.Thread(target=job, daemon=True).start()


def hdd_startup_auto_mount(app):
    enabled_slots = [
        idx
        for idx, slot in enumerate(app.hdd_slots)
        if hdd_auto_mount_enabled(slot) and hdd_slot_configured(slot)
    ]
    if not enabled_slots:
        return

    def schedule(idx, delay_ms):
        def run_mount(current_idx=idx):
            try:
                hdd_mount_async(app, current_idx, select_tab=False)
            except TypeError:
                hdd_mount_async(app, current_idx)

        app.after(
            delay_ms,
            run_mount,
        )

    scheduled = 0
    for idx in enabled_slots:
        state = hdd_collect_slot_state(app, idx)
        if state.get("is_luks"):
            app.hdd_slots[idx]["auto_mount"] = False
            app.log(
                f"HDD Automount übersprungen: Slot {idx + 1} ist LUKS/verschlüsselt."
            )
            continue
        schedule(idx, scheduled * 500)
        scheduled += 1

    save_hdd_config(app)


def hdd_mount_async(app, idx, select_tab=True):
    runner = hdd_mount_service.run_hdd_command
    if idx < 0 or idx >= len(app.hdd_slots):
        return
    # Freeze the selection before any dialogs or worker execution.
    slot = dict(app.hdd_slots[idx])
    device, disk = hdd_resolve_slot_device(app, slot)
    label = slot_display_name(app, idx)

    def report_failure(error):
        message = f"HDD mount rejected for {label}: {error}"
        call_in_ui_thread(app, lambda: app.log(message))

    if not device or not disk:
        report_failure("Device is not detected or its UUID no longer matches.")
        return
    if not has_cmd("udisksctl") or not has_cmd("lsblk") or not has_cmd("findmnt"):
        report_failure("udisks2, lsblk and findmnt are required for safe mounting.")
        return
    try:
        identity = hdd_mount_service.inspect_device(
            device, (slot.get("device_uuid") or "").strip(), runner
        )
    except (hdd_mount_service.MountPolicyError, OSError) as exc:
        report_failure(exc)
        return

    passphrase = None
    if identity.is_luks and identity.source is None:
        passphrase = simpledialog.askstring(
            app.tr("hdd_luks_passphrase_title", "LUKS passphrase"),
            app.tr(
                "hdd_luks_passphrase_prompt",
                "Please enter the LUKS passphrase for {device}:",
            ).format(device=device),
            show="*",
            parent=app,
        )
        if not passphrase:
            return

    def job():
        current = identity
        try:
            if passphrase is not None:
                current = hdd_mount_service.unlock_device(current, passphrase, runner)
            rc, out = hdd_mount_service.mount_device(current, runner)
        except (hdd_mount_service.MountPolicyError, OSError) as exc:
            report_failure(exc)
            return

        def done():
            if rc == 0:
                app.log(
                    app.tr(
                        "hdd_mounted_desktop_integrated",
                        "HDD desktop-integriert gemountet: {label} ({source}).",
                    ).format(label=label, source=current.source.path)
                )
            else:
                app.log(
                    app.tr(
                        "hdd_mount_failed", "HDD mount failed for {label}: {output}."
                    ).format(label=label, output=out)
                )
            app.hdd_refresh_async()
            _call_with_optional_select_tab(
                app.hdd_info_async, idx, select_tab, log_event=False
            )

        call_in_ui_thread(app, done)

    threading.Thread(target=job, daemon=True).start()


def _authorize_hdd_unmount(app, runner):
    """Keep HDD sudo authorization on the same controlled subprocess boundary."""
    rc, _out = runner(["sudo", "-n", "true"], timeout=3)
    if rc == 0:
        return True
    for _attempt in range(3):
        password = simpledialog.askstring(
            "HDD Unmount", "Sudo Passwort", show="*", parent=app
        )
        if password is None:
            return False
        try:
            rc, _out = runner(
                ["sudo", "-S", "-v"], input_text=password + "\n", timeout=6
            )
        finally:
            password = None
        if rc == 0:
            return True
    app.log("HDD unmount authorization failed.")
    return False


def hdd_unmount_async(app, idx, select_tab=True):
    runner = hdd_mount_service.run_hdd_command
    if idx < 0 or idx >= len(app.hdd_slots):
        return
    slot = dict(app.hdd_slots[idx])
    label = slot_display_name(app, idx)
    device, disk = hdd_resolve_slot_device(app, slot)
    if not hdd_slot_configured(slot):
        app.log(
            app.tr(
                "hdd_slot_not_configured",
                "HDD slot not configured: {label}.",
            ).format(label=label)
        )
        return

    def rejected(error):
        call_in_ui_thread(
            app,
            lambda: app.log(f"HDD unmount refused for {label}: {error}"),
        )

    try:
        if not device or not disk or not slot.get("device_uuid"):
            raise hdd_mount_service.MountPolicyError("No confirmed slot device.")
        identity = hdd_mount_service.inspect_device(device, slot["device_uuid"], runner)
        expected_target = hdd_mount_service.verified_mount_target(identity, runner)
    except (hdd_mount_service.MountPolicyError, OSError) as exc:
        rejected(str(exc))
        return
    if not _authorize_hdd_unmount(app, runner):
        return

    def job():
        mount_source = identity.source.path
        # Only the verified live crypt child can authorize closing a mapper.
        current_luks = {
            "is_luks": identity.is_luks,
            "mapper_name": (
                mount_source
                if identity.is_luks and identity.source.kind == "crypt"
                else ""
            ),
        }
        active_target = expected_target

        def unmount(args, timeout):
            if (
                hdd_mount_service.verified_mount_target(identity, runner)
                != expected_target
            ):
                raise hdd_mount_service.MountPolicyError("Mount target changed.")
            return runner(args, timeout=timeout)

        try:
            rc, out = unmount(["sudo", "-n", "umount", active_target], timeout=12)
            if rc != 0:
                rc, out = unmount(["sudo", "-n", "umount", mount_source], timeout=12)
            if rc != 0:
                rc, out = unmount(["umount", active_target], timeout=12)
            if rc != 0 and has_cmd("udisksctl") and not current_luks.get("is_luks"):
                rc, out = unmount(
                    ["udisksctl", "unmount", "-b", mount_source], timeout=20
                )

            if rc != 0:
                app.after(
                    0,
                    lambda: app.log(
                        app.tr(
                            "hdd_unmount_failed",
                            "HDD unmount failed for {label}: {output}",
                        ).format(label=label, output=out)
                    ),
                )
                call_in_ui_thread(app, lambda: app.hdd_refresh_async())
                app.after(
                    0,
                    lambda: _call_with_optional_select_tab(
                        app.hdd_info_async, idx, select_tab, log_event=False
                    ),
                )
                return
        except (hdd_mount_service.MountPolicyError, OSError) as exc:
            rejected(str(exc))
            return

        close_rc = 0
        close_out = ""
        if current_luks.get("is_luks") and has_cmd("cryptsetup"):
            mapper_name = current_luks.get("mapper_name")
            if mapper_name:
                try:
                    hdd_mount_service.revalidate(identity, runner)
                except (hdd_mount_service.MountPolicyError, OSError) as exc:
                    rejected(str(exc))
                    return
                close_rc, close_out = runner(
                    ["sudo", "-n", "cryptsetup", "luksClose", mapper_name],
                    timeout=20,
                )
                if close_rc != 0:
                    try:
                        hdd_mount_service.revalidate(identity, runner)
                    except (hdd_mount_service.MountPolicyError, OSError) as exc:
                        rejected(str(exc))
                        return
                    close_rc, close_out = runner(
                        ["cryptsetup", "luksClose", mapper_name], timeout=20
                    )

        def done():
            app.log(
                app.tr(
                    "hdd_unmount_success",
                    "HDD unmount successful: {label}.",
                ).format(label=label)
            )
            if current_luks.get("is_luks") and current_luks.get("mapper_name"):
                if close_rc == 0:
                    app.log(
                        app.tr(
                            "hdd_luks_closed",
                            "LUKS closed: {mapper}.",
                        ).format(mapper=current_luks.get("mapper_name"))
                    )
                elif close_out:
                    app.log(
                        app.tr(
                            "hdd_luks_close_failed",
                            "LUKS close failed ({mapper}): {output}",
                        ).format(
                            mapper=current_luks.get("mapper_name"),
                            output=close_out,
                        )
                    )
            app.hdd_refresh_async()
            _call_with_optional_select_tab(
                app.hdd_info_async, idx, select_tab, log_event=False
            )

        call_in_ui_thread(app, done)

    threading.Thread(target=job, daemon=True).start()
