"""HDD controller helpers for NetMon."""

from __future__ import annotations

import json
import os
import re
import threading
import time
from tkinter import messagebox, simpledialog

try:
    from netmon.config.constants import HDD_SLOT_COUNT
except ModuleNotFoundError:
    from config.constants import HDD_SLOT_COUNT

try:
    from netmon.core.utils import human_size, safe_write_json
except ModuleNotFoundError:
    from core.utils import human_size, safe_write_json

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.core.command import run_cmd_with_input
except ModuleNotFoundError:
    from core.command import run_cmd_with_input

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



def _clear_hdd_slot_fields(slot):
    slot["device"] = ""
    slot["device_uuid"] = ""
    slot["mountpoint"] = ""
    slot["custom_name"] = ""
    slot["auto_mount"] = False





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
    configured_device = (slot.get("device") or "").strip()
    configured_uuid = (slot.get("device_uuid") or "").strip()
    disks_by_device = _detected_disks_by_device(app)

    disk = disks_by_device.get(configured_device) if configured_device else None
    if disk:
        live_uuid = (disk.get("uuid") or "").strip()
        if live_uuid and live_uuid != configured_uuid:
            slot["device_uuid"] = live_uuid
        return configured_device, disk

    disk = hdd_find_device_by_uuid(app, configured_uuid)
    if disk:
        live_device = (disk.get("device") or "").strip()
        if live_device and live_device != configured_device:
            slot["device"] = live_device
        return live_device, disk

    return configured_device, None


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
            "gemountet" if disk.get("mounted") else "nicht gemountet"
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
        return f"Slot {idx + 1} frei"
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
    current_info_device = str(app.__dict__.get("hdd_info_selected_device") or "").strip()
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
                hint = "LUKS bzw. verschlüsselte Devices können nicht automatisch gemountet werden."
        else:
            hint = (
                "Automount ist nur für Devices verfügbar, die einem HDD-Slot "
                "zugeordnet sind."
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
        app.log("HDD Automount erfordert eine Slot-Zuordnung für das ausgewählte Device.")
        return
    if state.get("is_luks"):
        app.hdd_slots[slot_no - 1]["auto_mount"] = False
        save_hdd_config(app)
        hdd_sync_auto_mount_ui(app, state)
        app.log("LUKS bzw. verschlüsselte Devices können nicht automatisch gemountet werden.")
        return

    auto_mount_var = app.__dict__.get("hdd_info_auto_mount_var")
    enabled = bool(auto_mount_var.get()) if auto_mount_var is not None else False
    app.hdd_slots[slot_no - 1]["auto_mount"] = enabled
    save_hdd_config(app)
    hdd_sync_auto_mount_ui(app, state)
    app.log(
        f"HDD Automount {'aktiviert' if enabled else 'deaktiviert'}: {device}."
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

    for slot in app.hdd_slots:
        if (slot.get("device") or "").strip() == dev:
            slot["device"] = ""
            slot["mountpoint"] = ""
            slot["custom_name"] = ""

    target = app.hdd_slots[slot_no - 1]
    previous_target_device = (target.get("device") or "").strip()
    target["device"] = dev
    target["device_uuid"] = (disk.get("uuid") or "").strip()
    target["mountpoint"] = (
        (disk.get("mountpoint") or "").strip()
        or target.get("mountpoint")
        or f"/mnt/{os.path.basename(dev)}"
    )
    target["auto_mount"] = bool(target.get("auto_mount")) if previous_target_device == dev else False
    target["custom_name"] = (app.hdd_custom_name_var.get() or "").strip()
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
    had_assignment = bool(
        (target.get("device") or "").strip()
        or (target.get("device_uuid") or "").strip()
        or (target.get("mountpoint") or "").strip()
        or (target.get("custom_name") or "").strip()
    )
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

        app.after(0, done)

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
            cw // 2, ch // 2, text="Keine Nutzungsdaten verfügbar", fill="#666"
        )
        return

    total = max(int(usage["total"]), 1)
    used = min(max(int(usage.get("used", 0)), 0), total)
    frac = used / total
    ux = x0 + int((x1 - x0) * frac)
    app.hdd_usage_canvas.create_rectangle(x0, y0, ux, y1, fill="#d9534f", outline="")
    pct = usage.get("use_pct") or f"{frac * 100:.0f}%"
    txt = (
        f"Belegt {human_size(used)} / Frei {human_size(usage.get('free'))} "
        f"von {human_size(total)} ({pct})"
    )
    app.hdd_usage_canvas.create_text(cw // 2, ch // 2, text=txt, fill="#111")


def hdd_render_info(app, state):
    mounted = state.get("mounted")
    if mounted is True:
        mounted_txt = "gemountet"
    elif mounted is False:
        mounted_txt = "nicht gemountet"
    else:
        mounted_txt = "unbekannt"

    usage = state.get("usage") or {}
    display_name = (
        (state.get("custom_name") or "").strip()
        or (state.get("label") or "").strip()
        or (state.get("model") or "").strip()
        or (state.get("device") or "").strip()
        or "-"
    )
    lines = [
        f"Anzeigename: {display_name}",
        f"Device: {state.get('device') or '-'}",
        f"Mountpoint: {state.get('mountpoint') or '-'}",
        f"Status: {mounted_txt}",
        f"Verschlüsselung: {'LUKS' if state.get('is_luks') else 'nein'}",
        f"LUKS Zustand: {'gesperrt' if state.get('luks_locked') else ('offen' if state.get('is_luks') else '-')}",
        f"Aktuelles Target: {state.get('actual_target') or '-'}",
        f"Dateisystem: {state.get('fstype') or '-'}",
        f"Gesamtgröße: {human_size(state.get('size_bytes'))}",
        f"Belegt: {human_size(usage.get('used'))}",
        f"Frei: {human_size(usage.get('free'))}",
        f"Auslastung: {usage.get('use_pct') or '-'}",
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

        app.after(0, show)

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

        app.after(0, show)

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
    if idx < 0 or idx >= len(app.hdd_slots):
        return
    slot = app.hdd_slots[idx]
    label = slot_display_name(app, idx)
    resolve_slot_device = _app_callable(
        app,
        "_hdd_resolve_slot_device",
        lambda current_slot: hdd_resolve_slot_device(app, current_slot),
    )
    device, _disk = resolve_slot_device(slot)
    mountpoint = _slot_mountpoint(slot, device)
    if not hdd_slot_configured(slot):
        app.log(f"HDD Slot nicht konfiguriert: {label}.")
        return

    luks_info = _app_callable(
        app,
        "_hdd_luks_info_for_device",
        lambda current_device: hdd_luks_info_for_device(app, current_device),
    )
    mount_source_for = _app_callable(
        app, "_hdd_find_mount_source", hdd_find_mount_source
    )
    is_mounted = _app_callable(
        app,
        "_hdd_is_mounted",
        lambda current_device, current_mountpoint: hdd_is_mounted(
            app, current_device, current_mountpoint
        ),
    )
    luks = luks_info(device)
    luks_passphrase = None
    if luks.get("is_luks") and not luks.get("unlocked"):
        app.log("LUKS Schritt 1/2: Systemrechte bestätigen.")
        if not app.ensure_sudo_session("LUKS Systemrechte für HDD Mount"):
            return
        if not has_cmd("cryptsetup"):
            app.log(
                "LUKS erkannt, aber cryptsetup fehlt (sudo apt install -y cryptsetup)."
            )
            return
        app.log("LUKS Schritt 2/2: LUKS-Passphrase eingeben.")
        luks_passphrase = simpledialog.askstring(
            "LUKS Passphrase",
            f"Bitte LUKS-Passphrase für {device} eingeben:",
            show="*",
            parent=app,
        )
        if luks_passphrase is None:
            app.log(f"LUKS Mount abgebrochen: {label}.")
            return
        if not luks_passphrase:
            app.log("LUKS Passphrase leer, Mount abgebrochen.")
            return
    elif not app.ensure_sudo_session("HDD Mount"):
        return

    def job():
        if not os.path.exists(device):
            app.after(
                0,
                lambda: app.log(
                    f"HDD Mount fehlgeschlagen für {label}: Device existiert nicht ({device})."
                ),
            )
            return

        current_luks = luks_info(device)
        mount_source = mount_source_for(device)
        if current_luks.get("is_luks"):
            mapper_name = current_luks.get("mapper_name")
            mapper_path = current_luks.get("mapper_path")
            if not mapper_name:
                mapper_name = hdd_sanitize_mapper_name(device)
                mapper_path = f"/dev/mapper/{mapper_name}"

            if not os.path.exists(mapper_path):
                rc, out = run_cmd_with_input(
                    [
                        "sudo",
                        "-n",
                        "cryptsetup",
                        "luksOpen",
                        device,
                        mapper_name,
                        "--key-file",
                        "-",
                    ],
                    input_text=(luks_passphrase or "") + "\n",
                    timeout=25,
                )
                if rc != 0:
                    rc, out = run_cmd_with_input(
                        [
                            "cryptsetup",
                            "luksOpen",
                            device,
                            mapper_name,
                            "--key-file",
                            "-",
                        ],
                        input_text=(luks_passphrase or "") + "\n",
                        timeout=25,
                    )
                if rc != 0:
                    app.after(
                        0,
                        lambda: app.log(
                            f"LUKS öffnen fehlgeschlagen für {label}: {out}"
                        ),
                    )
                    return
                for _ in range(15):
                    time.sleep(0.2)
                    current_luks = luks_info(device)
                    mapper_path = current_luks.get("mapper_path") or mapper_path
                    mapper_name = current_luks.get("mapper_name") or mapper_name
                    if mapper_path and os.path.exists(mapper_path):
                        break

            if not mapper_path or not os.path.exists(mapper_path):
                available_mappers = (
                    current_luks.get("available_mappers") or hdd_list_mappers()
                )
                mapper_list = ", ".join(available_mappers) if available_mappers else "-"
                searched = mapper_path or f"/dev/mapper/{mapper_name}"
                app.after(
                    0,
                    lambda: app.log(
                        f"HDD Mount fehlgeschlagen für {label}: Gesuchtes Device: {searched} | Vorhandene Mapper: {mapper_list}"
                    ),
                )
                return

            mount_source = mount_source_for(mapper_path)
            app.hdd_luks_mappers[device] = mapper_name
            app.after(
                0,
                lambda: app.log(f"LUKS Mount-Quelle gewählt: {mount_source}"),
            )
            app.after(
                0,
                lambda: app.log(
                    "LUKS wird per Root-Mount auf den konfigurierten Pfad eingebunden."
                ),
            )

        mounted, target = is_mounted(device, mountpoint)
        if mounted is True:
            app.after(
                0,
                lambda: app.log(
                    f"HDD bereits gemountet: {label} ({target or mountpoint})."
                ),
            )
            app.after(
                0,
                lambda: _call_with_optional_select_tab(
                    app.hdd_info_async, idx, select_tab, log_event=False
                ),
            )
            return

        used_desktop_mount = False
        if has_cmd("udisksctl") and not current_luks.get("is_luks"):
            rc, out = run_cmd(["udisksctl", "mount", "-b", mount_source], timeout=20)
            if rc == 0:
                used_desktop_mount = True
            else:
                app.after(
                    0,
                    lambda: app.log(
                        "udisksctl-Mount fehlgeschlagen, versuche klassischen Mount auf konfigurierten Pfad."
                    ),
                )

        if not used_desktop_mount:
            rc, out = run_cmd(["sudo", "-n", "mkdir", "-p", mountpoint], timeout=8)
            if rc != 0:
                rc, out = run_cmd(["mkdir", "-p", mountpoint], timeout=8)
            if rc != 0:
                app.after(
                    0,
                    lambda: app.log(f"HDD Mountpoint Fehler {mountpoint}: {out}"),
                )
                return

            rc, out = run_cmd(
                ["sudo", "-n", "mount", mount_source, mountpoint], timeout=12
            )
            if rc != 0:
                rc, out = run_cmd(["mount", mount_source, mountpoint], timeout=12)

        def done():
            if rc == 0:
                if used_desktop_mount:
                    app.log(
                        f"HDD desktop-integriert gemountet: {label} ({mount_source})."
                    )
                else:
                    app.log(f"HDD gemountet: {label} ({mount_source} -> {mountpoint}).")
            else:
                app.log(f"HDD Mount fehlgeschlagen für {label}: {out}")
                if (
                    "password" in (out or "").lower()
                    or "not permitted" in (out or "").lower()
                ):
                    app.log(
                        "Hinweis: sudo-Auth fehlt oder Rechte unzureichend (siehe Sudo-Auth beim Start)."
                    )
            app.hdd_refresh_async()
            _call_with_optional_select_tab(
                app.hdd_info_async, idx, select_tab, log_event=False
            )

        app.after(0, done)

    threading.Thread(target=job, daemon=True).start()


def hdd_unmount_async(app, idx, select_tab=True):
    if idx < 0 or idx >= len(app.hdd_slots):
        return
    if not app.ensure_sudo_session("HDD Unmount"):
        return
    slot = app.hdd_slots[idx]
    label = slot_display_name(app, idx)
    resolve_slot_device = _app_callable(
        app,
        "_hdd_resolve_slot_device",
        lambda current_slot: hdd_resolve_slot_device(app, current_slot),
    )
    device, _disk = resolve_slot_device(slot)
    mountpoint = _slot_mountpoint(slot, device)
    if not hdd_slot_configured(slot):
        app.log(f"HDD Slot nicht konfiguriert: {label}.")
        return

    def job():
        luks_info = _app_callable(
            app,
            "_hdd_luks_info_for_device",
            lambda current_device: hdd_luks_info_for_device(app, current_device),
        )
        mount_source_for = _app_callable(
            app,
            "_hdd_find_mount_source",
            hdd_find_mount_source,
        )
        is_mounted = _app_callable(
            app,
            "_hdd_is_mounted",
            lambda current_device, current_mountpoint: hdd_is_mounted(
                app, current_device, current_mountpoint
            ),
        )
        current_luks = luks_info(device)
        raw_mount_source = (
            current_luks.get("mapper_path") if current_luks.get("is_luks") else device
        )
        if not raw_mount_source:
            raw_mount_source = device
        mount_source = mount_source_for(raw_mount_source)

        mounted, target = is_mounted(device, mountpoint)
        active_target = target or mountpoint
        if mounted is False:
            app.after(
                0,
                lambda: app.log(f"HDD bereits ungemountet: {label}."),
            )
        else:
            rc, out = run_cmd(["sudo", "-n", "umount", active_target], timeout=12)
            if rc != 0:
                rc, out = run_cmd(["sudo", "-n", "umount", mount_source], timeout=12)
            if rc != 0:
                rc, out = run_cmd(["umount", active_target], timeout=12)
            if rc != 0 and has_cmd("udisksctl") and not current_luks.get("is_luks"):
                rc, out = run_cmd(
                    ["udisksctl", "unmount", "-b", mount_source], timeout=20
                )

            if rc != 0:
                app.after(
                    0,
                    lambda: app.log(f"HDD Unmount fehlgeschlagen für {label}: {out}"),
                )
                app.after(0, lambda: app.hdd_refresh_async())
                app.after(
                    0,
                    lambda: _call_with_optional_select_tab(
                        app.hdd_info_async, idx, select_tab, log_event=False
                    ),
                )
                return

        close_rc = 0
        close_out = ""
        if current_luks.get("is_luks") and has_cmd("cryptsetup"):
            mapper_name = current_luks.get("mapper_name")
            if mapper_name:
                close_rc, close_out = run_cmd(
                    ["sudo", "-n", "cryptsetup", "luksClose", mapper_name],
                    timeout=20,
                )
                if close_rc != 0:
                    close_rc, close_out = run_cmd(
                        ["cryptsetup", "luksClose", mapper_name], timeout=20
                    )

        def done():
            app.log(f"HDD unmount erfolgreich: {label}.")
            if current_luks.get("is_luks") and current_luks.get("mapper_name"):
                if close_rc == 0:
                    app.log(f"LUKS geschlossen: {current_luks.get('mapper_name')}.")
                elif close_out:
                    app.log(
                        f"LUKS schließen fehlgeschlagen ({current_luks.get('mapper_name')}): {close_out}"
                    )
            app.hdd_refresh_async()
            _call_with_optional_select_tab(
                app.hdd_info_async, idx, select_tab, log_event=False
            )

        app.after(0, done)

    threading.Thread(target=job, daemon=True).start()
