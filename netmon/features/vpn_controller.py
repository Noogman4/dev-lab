"""VPN controller helpers for NetMon."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import tempfile
import threading
import time
import traceback
from tkinter import messagebox

try:
    from netmon.config.constants import (
        PRIVACY_VPN_LABELS,
        PRIVACY_VPN_PROFILES_TO_LABEL,
        VPN_SLOT_COUNT,
        WG_IPV4_PROFILE_SUFFIX,
    )
except ModuleNotFoundError:
    from config.constants import (
        PRIVACY_VPN_LABELS,
        PRIVACY_VPN_PROFILES_TO_LABEL,
        VPN_SLOT_COUNT,
        WG_IPV4_PROFILE_SUFFIX,
    )

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.core.tooling import has_cmd
except ModuleNotFoundError:
    from core.tooling import has_cmd

try:
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    from core.utils import safe_write_json


def load_primary_vpn_slots_config(app):
    slots = app._default_primary_vpn_slots()
    try:
        if os.path.isfile(app.primary_vpn_config_path):
            with open(app.primary_vpn_config_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    slot_no = int(item.get("slot", 0))
                    if 1 <= slot_no <= len(slots):
                        profile = app._base_wg_profile_name(item.get("profile"))
                        slots[slot_no - 1] = {
                            "slot": slot_no,
                            "custom_name": (item.get("custom_name") or "").strip(),
                            "profile": profile,
                        }
    except Exception as exc:
        app.log(f"Primäre VPN-Slot-Konfig konnte nicht geladen werden: {exc}")
    return slots


def get_privacy_vpn_options(app):
    options = []
    seen_labels = set()
    slots = app.__dict__.get("primary_vpn_slots", []) or []
    for slot in slots:
        profile = app._base_wg_profile_name(slot.get("profile"))
        if not profile:
            continue

        raw_label = (slot.get("custom_name") or "").strip()
        label = raw_label or profile
        if not label:
            continue

        unique_label = label
        suffix = 2
        while unique_label in seen_labels:
            unique_label = f"{label} ({suffix})"
            suffix += 1

        seen_labels.add(unique_label)
        options.append({"label": unique_label, "profile": profile})

    if not options:
        for label, profile in PRIVACY_VPN_LABELS.items():
            options.append({"label": label, "profile": profile})

    return options


def privacy_vpn_label_profile_maps(app):
    label_to_profile = {}
    profile_to_label = {}

    for item in get_privacy_vpn_options(app):
        label = item.get("label", "")
        profile = item.get("profile", "")
        if label and profile:
            label_to_profile[label] = profile
            profile_to_label.setdefault(profile, label)

    for label, profile in PRIVACY_VPN_LABELS.items():
        label_to_profile.setdefault(label, profile)
        profile_to_label.setdefault(profile, label)

    return label_to_profile, profile_to_label


def update_privacy_vpn_combo(app):
    values = [item["label"] for item in get_privacy_vpn_options(app)]
    if "isp_stealth_vpn_combo" in app.__dict__:
        app.isp_stealth_vpn_combo["values"] = values

    current_profile = ""
    if "isp_stealth_vpn_profile" in app.__dict__:
        current_profile = (app.isp_stealth_vpn_profile.get() or "").strip()
    if current_profile and app._privacy_vpn_label_for_profile(current_profile):
        if "isp_stealth_vpn_choice" in app.__dict__:
            app.isp_stealth_vpn_choice.set(
                app._privacy_vpn_label_for_profile(current_profile)
            )
        if "isp_stealth_vpn_profile" in app.__dict__:
            app.isp_stealth_vpn_profile.set(current_profile)
    else:
        if current_profile and "isp_stealth_vpn_profile" in app.__dict__:
            app.isp_stealth_vpn_profile.set("")
        if "isp_stealth_vpn_choice" in app.__dict__:
            app.isp_stealth_vpn_choice.set("")
        if current_profile:
            app.save_privacy_config()


def privacy_vpn_profile_from_value(app, value):
    selected = (value or "").strip()
    if not selected:
        return ""

    label_to_profile, profile_to_label = privacy_vpn_label_profile_maps(app)
    if selected in label_to_profile:
        return label_to_profile[selected]
    if selected in profile_to_label:
        return selected

    if selected in PRIVACY_VPN_LABELS:
        return PRIVACY_VPN_LABELS[selected]
    if selected in PRIVACY_VPN_PROFILES_TO_LABEL:
        return selected

    return ""


def privacy_vpn_label_for_profile(app, profile):
    selected = (profile or "").strip()
    if not selected:
        return ""

    _, profile_to_label = privacy_vpn_label_profile_maps(app)
    if selected in profile_to_label:
        return profile_to_label[selected]

    return PRIVACY_VPN_PROFILES_TO_LABEL.get(selected, "")


def save_primary_vpn_slots_config(app):
    ok, err = safe_write_json(
        app.primary_vpn_config_path,
        app.primary_vpn_slots,
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        app.log(f"Primäre VPN-Slot-Konfig konnte nicht gespeichert werden: {err}")


def load_vpn_slots_config(app):
    slots = app._default_vpn_slots()
    try:
        if os.path.isfile(app.vpn_config_path):
            with open(app.vpn_config_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    slot_no = int(item.get("slot", 0))
                    if 1 <= slot_no <= VPN_SLOT_COUNT:
                        slots[slot_no - 1] = {
                            "slot": slot_no,
                            "custom_name": (item.get("custom_name") or "").strip(),
                            "profile": app._base_wg_profile_name(item.get("profile")),
                        }
    except Exception as exc:
        app.log(f"VPN-Slot-Konfig konnte nicht geladen werden: {exc}")
    return slots


def save_vpn_slots_config(app):
    ok, err = safe_write_json(
        app.vpn_config_path,
        app.vpn_slots,
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        app.log(f"VPN-Slot-Konfig konnte nicht gespeichert werden: {err}")
        return False
    return True


def update_primary_vpn_buttons(app):
    if not hasattr(app, "btn_primary_vpn_1"):
        return
    app.btn_primary_vpn_1.config(
        text=app.primary_vpn_slots[0].get("custom_name", "VPN CH")
    )
    app.btn_primary_vpn_2.config(
        text=app.primary_vpn_slots[1].get("custom_name", "VPN DE")
    )


def update_primary_vpn_form_controls(app):
    if threading.current_thread() is not threading.main_thread():
        app.after(0, app.update_primary_vpn_form_controls)
        return
    if "primary_vpn_1_profile_combo" in app.__dict__:
        app.primary_vpn_1_profile_combo["values"] = app.wg_profiles
    if "primary_vpn_2_profile_combo" in app.__dict__:
        app.primary_vpn_2_profile_combo["values"] = app.wg_profiles


def refresh_vpn_slots_table(app):
    if threading.current_thread() is not threading.main_thread():
        app.after(0, app.refresh_vpn_slots_table)
        return
    if not hasattr(app, "vpn_table"):
        return
    selected = app.vpn_table.selection()
    selected_iid = selected[0] if selected else None
    app._vpn_table_refreshing = True
    try:
        for item in app.vpn_table.get_children():
            app.vpn_table.delete(item)
        for slot in app.vpn_slots:
            status, _color = app._vpn_slot_status(slot)
            name = (slot.get("custom_name") or "").strip() or "-"
            profile = app._base_wg_profile_name(slot.get("profile")) or "-"
            iid = f"vpn-slot-{slot['slot']}"
            app.vpn_table.insert(
                "",
                "end",
                iid=iid,
                values=(
                    slot["slot"],
                    name,
                    profile,
                    status,
                ),
            )
        if selected_iid and selected_iid in app.vpn_table.get_children():
            current_selection = app.vpn_table.selection()
            if not current_selection or current_selection[0] != selected_iid:
                app.vpn_table.selection_set(selected_iid)
            app.vpn_table.focus(selected_iid)
    finally:
        app._vpn_table_refreshing = False


def sync_primary_vpn_form_selection(app):
    if threading.current_thread() is not threading.main_thread():
        app.after(0, app.sync_primary_vpn_form_selection)
        return
    available_profiles = set(app.__dict__.get("wg_profiles", []) or [])
    for slot_no, var_name in enumerate(
        ("primary_vpn_1_profile_var", "primary_vpn_2_profile_var"), 1
    ):
        profile_var = app.__dict__.get(var_name)
        if profile_var is None:
            continue
        saved_profile = app.primary_vpn_slots[slot_no - 1].get("profile", "")
        base_profile = app._base_wg_profile_name(saved_profile)
        if base_profile and base_profile in available_profiles:
            profile_var.set(saved_profile)
        else:
            profile_var.set("")


def open_primary_vpn_slot(app, slot_no):
    if not (1 <= slot_no <= len(app.primary_vpn_slots)):
        app.log(f"Unbekannter Standard-VPN-Slot: {slot_no}")
        return False
    slot = app.primary_vpn_slots[slot_no - 1]
    profile = app._base_wg_profile_name(slot.get("profile"))
    if not profile:
        app.log(f"Standard-VPN-Slot {slot_no} ist nicht konfiguriert.")
        return False
    app.log(f"Standard-VPN-Slot {slot_no}: starte Profil '{profile}'")
    try:
        ok = app.vpn_switch(profile)
    except Exception as exc:
        app.log(
            f"Standard-VPN-Slot {slot_no}: interner Fehler beim Start von '{profile}': {exc}"
        )
        app.log_debug_safe(traceback.format_exc())
        ok = False
    if not ok:
        app.log(f"Standard-VPN-Slot {slot_no} konnte Profil '{profile}' nicht starten.")
    return ok


def save_primary_vpn_slot(app, slot_no):
    if not (1 <= slot_no <= len(app.primary_vpn_slots)):
        app.log(f"Unbekannter Standard-VPN-Slot zum Speichern: {slot_no}")
        return

    if slot_no == 1:
        custom_name = (app.primary_vpn_1_name_var.get() or "").strip()
        profile = app.primary_vpn_1_profile_var.get() or ""
    else:
        custom_name = (app.primary_vpn_2_name_var.get() or "").strip()
        profile = app.primary_vpn_2_profile_var.get() or ""

    profile = app._base_wg_profile_name(profile)

    available_profiles = set(app.__dict__.get("wg_profiles", []) or [])
    if profile:
        if (
            available_profiles
            and profile not in available_profiles
            and not app._wg_profile_exists(profile)
        ):
            app.log(
                f"Standard-VPN-Slot {slot_no}: Profil '{profile}' nicht gefunden. Speichern abgebrochen."
            )
            return

    app.primary_vpn_slots[slot_no - 1]["custom_name"] = custom_name
    app.primary_vpn_slots[slot_no - 1]["profile"] = profile
    app.save_primary_vpn_slots_config()
    app.update_primary_vpn_buttons()
    app.update_privacy_vpn_combo()
    app.log(f"Standard-VPN-Slot {slot_no} gespeichert: {custom_name or profile}.")
    if profile:
        app.run_async(
            lambda p=profile, s=slot_no: app.reconcile_vpn_slot_firewall_state(
                reason=f"Primary-Slot-Zuordnung {s}->{p}",
                touched_profiles=[p],
                refresh_ui=False,
            )
        )


def load_vpn_slot_into_form(app, slot_no):
    if not (1 <= slot_no <= VPN_SLOT_COUNT):
        return
    slot = app.vpn_slots[slot_no - 1]
    app._vpn_form_loading = True
    try:
        app.vpn_slot_choice.set(str(slot_no))
        app.vpn_custom_name_var.set((slot.get("custom_name") or "").strip())
        app.vpn_profile_var.set(app._base_wg_profile_name(slot.get("profile")))
    finally:
        app._vpn_form_loading = False
    app._vpn_form_dirty = False


def sync_vpn_profile_form_selection(app):
    if threading.current_thread() is not threading.main_thread():
        app.after(0, app.sync_vpn_profile_form_selection)
        return
    profile_var = app.__dict__.get("vpn_profile_var")
    if profile_var is None:
        return
    profile = app._base_wg_profile_name(profile_var.get())
    available_profiles = set(app.__dict__.get("wg_profiles", []) or [])
    if profile and profile not in available_profiles:
        profile_var.set("")


def on_vpn_slot_select(app, _event=None):
    try:
        slot_no = int((app.vpn_slot_choice.get() or "0").strip())
    except ValueError:
        slot_no = 0
    app.load_vpn_slot_into_form(slot_no)


def on_vpn_table_select(app, _event=None):
    if getattr(app, "_vpn_table_refreshing", False):
        return
    selection = app.vpn_table.selection() if hasattr(app, "vpn_table") else ()
    if not selection:
        return
    values = app.vpn_table.item(selection[0], "values")
    if not values:
        return
    try:
        slot_no = int(values[0])
    except (TypeError, ValueError):
        return

    if getattr(app, "_vpn_form_dirty", False):
        try:
            current_slot = int((app.vpn_slot_choice.get() or "0").strip())
        except ValueError:
            current_slot = 0
        if slot_no == current_slot:
            return

    app.load_vpn_slot_into_form(slot_no)


def resolve_vpn_profile_input(app, profile_value, *, refresh_profiles=False):
    candidate = app._base_wg_profile_name(profile_value)
    if not candidate:
        return ""

    if refresh_profiles:
        app.refresh_wg_profiles()
        combo = app.__dict__.get("vpn_profile_combo")
        if combo is not None:
            try:
                combo["values"] = app.wg_profiles
            except Exception:
                pass

    profiles = [
        app._base_wg_profile_name(name)
        for name in (app.__dict__.get("wg_profiles", []) or [])
        if app._base_wg_profile_name(name)
    ]

    if candidate in profiles:
        return candidate

    if not profiles:
        return candidate

    lowered = candidate.lower()
    case_matches = [name for name in profiles if name.lower() == lowered]
    if len(case_matches) == 1:
        return case_matches[0]

    if app._wg_profile_exists(candidate):
        return candidate

    return candidate


def assign_vpn_slot(app):
    try:
        slot_no = int((app.vpn_slot_choice.get() or "0").strip())
    except ValueError:
        slot_no = 0
    if not (1 <= slot_no <= VPN_SLOT_COUNT):
        app.log("Ungültiger VPN-Slot ausgewählt.")
        return

    profile_input = (app.vpn_profile_var.get() or "").strip()
    profile = app._resolve_vpn_profile_input(profile_input, refresh_profiles=True)
    custom_name = (app.vpn_custom_name_var.get() or "").strip()
    if not profile:
        app.log(
            "Bitte ein gültiges WireGuard-Profil auswählen oder manuell einen vorhandenen Profilnamen eingeben."
        )
        return
    if profile_input != profile:
        app.vpn_profile_var.set(profile)

    previous_slots = [dict(existing_slot) for existing_slot in app.vpn_slots]
    for idx, slot in enumerate(app.vpn_slots):
        if idx != slot_no - 1 and (slot.get("profile") or "").strip() == profile:
            slot["profile"] = ""
            slot["custom_name"] = ""

    slot = app.vpn_slots[slot_no - 1]
    slot["custom_name"] = custom_name
    slot["profile"] = profile
    save_result = app.save_vpn_slots_config()
    if save_result is False:
        app.vpn_slots = previous_slots
        app.load_vpn_slot_into_form(slot_no)
        app.update_vpn_slot_buttons()
        app.refresh_vpn_slots_table()
        app.log(
            f"VPN-Slot {slot_no} konnte nicht gespeichert werden – Änderungen wurden zurückgesetzt."
        )
        return
    app.update_vpn_slot_buttons()
    app.refresh_vpn_slots_table()
    app.log(f"VPN-Slot {slot_no} gespeichert: {profile}.")
    app.run_async(
        lambda p=profile, s=slot_no: app.reconcile_vpn_slot_firewall_state(
            reason=f"Slot-Zuordnung {s}->{p}",
            touched_profiles=[p],
            refresh_ui=False,
        )
    )


def is_vpn_profile_referenced_in_other_slots(app, profile, skip_slot_no=None):
    profile = app._base_wg_profile_name(profile)
    if not profile:
        return False
    for idx, slot in enumerate(app.vpn_slots, start=1):
        if skip_slot_no and idx == skip_slot_no:
            continue
        if app._base_wg_profile_name(slot.get("profile")) == profile:
            return True
    return False


def collect_referenced_vpn_profiles(app, include_active=True):
    profiles = []
    seen = set()

    def add_profile(value):
        profile = app._base_wg_profile_name(value)
        if not profile or profile in seen:
            return
        seen.add(profile)
        profiles.append(profile)

    for slot in app.__dict__.get("vpn_slots") or []:
        add_profile(slot.get("profile"))

    for slot in app.__dict__.get("primary_vpn_slots") or []:
        add_profile(slot.get("profile"))

    privacy_profile = ""
    if "isp_stealth_vpn_profile" in app.__dict__:
        try:
            privacy_profile = (
                app._base_wg_profile_name(app.isp_stealth_vpn_profile.get()) or ""
            )
        except Exception:
            privacy_profile = ""

    if not privacy_profile and "isp_stealth_vpn_choice" in app.__dict__:
        try:
            privacy_profile = app._base_wg_profile_name(
                app._privacy_vpn_profile_from_value(app.isp_stealth_vpn_choice.get())
            )
        except Exception:
            privacy_profile = ""

    if not privacy_profile:
        cfg = app.__dict__.get("privacy_config") or {}
        cfg_profile = str(cfg.get("vpn_profile") or "").strip()
        if cfg_profile:
            try:
                privacy_profile = app._base_wg_profile_name(
                    app._privacy_vpn_profile_from_value(cfg_profile)
                )
            except Exception:
                privacy_profile = app._base_wg_profile_name(cfg_profile)

    add_profile(privacy_profile)

    if include_active:
        try:
            add_profile(app.active_wg_profile())
        except Exception:
            pass

    return profiles


def clear_vpn_slot(app, confirm=False):
    try:
        slot_no = int((app.vpn_slot_choice.get() or "0").strip())
    except ValueError:
        slot_no = 0
    if not (1 <= slot_no <= VPN_SLOT_COUNT):
        app.log("Ungültiger VPN-Slot ausgewählt.")
        return

    slot = app.vpn_slots[slot_no - 1]
    old_profile = app._base_wg_profile_name(slot.get("profile"))
    previous_slot_state = {
        "custom_name": slot.get("custom_name", ""),
        "profile": slot.get("profile", ""),
    }

    if confirm and old_profile:
        ok = messagebox.askyesno(
            "VPN-Slot aufheben",
            f"Slot {slot_no} mit Profil '{old_profile}' wird geleert. Fortfahren?",
            parent=app,
        )
        if not ok:
            app.log(f"VPN-Slot {slot_no} aufheben abgebrochen.")
            return

    old_profiles = app._collect_referenced_vpn_profiles(include_active=True)
    old_interfaces = app._collect_interface_rules_for_profiles_safe(
        old_profiles, include_family_candidates=True
    )
    old_endpoints = app._collect_endpoint_rules_for_profiles(old_profiles)

    slot["custom_name"] = ""
    slot["profile"] = ""
    save_result = app.save_vpn_slots_config()
    if save_result is False:
        slot["custom_name"] = previous_slot_state["custom_name"]
        slot["profile"] = previous_slot_state["profile"]
        app.load_vpn_slot_into_form(slot_no)
        app.update_vpn_slot_buttons()
        app.refresh_vpn_slots_table()
        app.log(
            f"VPN-Slot {slot_no} konnte nicht gelöscht werden – Änderungen wurden zurückgesetzt."
        )
        return

    if old_profile:
        app.log(
            f"VPN-Slot {slot_no}: Profil '{old_profile}' entfernt – gleicht die Firewall mit dem neuen Sollzustand ab."
        )
        new_profiles = app._collect_referenced_vpn_profiles(include_active=True)
        new_interfaces = app._collect_interface_rules_for_profiles(new_profiles)
        new_endpoints = app._collect_endpoint_rules_for_profiles(new_profiles)
        reconcile_ok = app._reconcile_vpn_firewall_rules(
            old_interfaces=old_interfaces,
            new_interfaces=new_interfaces,
            old_endpoints=old_endpoints,
            new_endpoints=new_endpoints,
            removed_profile=old_profile,
        )
        if reconcile_ok is False:
            app.log(
                "Firewall-Reconcile nach Slot-Löschung unvollständig. Bitte UFW-Regeln prüfen."
            )

    app.load_vpn_slot_into_form(slot_no)
    app.update_vpn_slot_buttons()
    app.refresh_vpn_slots_table()
    if old_profile:
        app.log(f"VPN-Slot {slot_no} aufgehoben ({old_profile}).")
    else:
        app.log(f"VPN-Slot {slot_no} aufgehoben.")


def delete_selected_vpn_profile(app):
    profile = app._base_wg_profile_name(app.vpn_profile_var.get())
    if not profile:
        app.log("Bitte erst ein WireGuard-Profil auswählen.")
        return

    ok = messagebox.askyesno(
        "WireGuard-Profil löschen",
        (
            "Dieses WireGuard-Profil wird gelöscht.\n\n"
            f"Original: {profile}.conf\n"
            "Fortfahren?"
        ),
        parent=app,
    )
    if not ok:
        app.log("Löschen abgebrochen.")
        return

    if not app.ensure_sudo_session("VPN-Profil löschen"):
        return

    old_referenced_profiles = app._collect_referenced_vpn_profiles(include_active=True)
    old_referenced_interfaces = app._collect_interface_rules_for_profiles_safe(
        old_referenced_profiles, include_family_candidates=True
    )
    old_referenced_endpoints = app._collect_endpoint_rules_for_profiles(
        old_referenced_profiles
    )

    app.log_debug(f"Formular-Profilwert = {app.vpn_profile_var.get()!r}")
    app.log_debug(f"Basisprofil = {profile!r}")

    original_path = app._wg_profile_path(profile)
    original_exists = app._wg_profile_exists(profile)
    active_ifaces = [
        iface
        for iface in app.get_wg_interfaces()
        if app._base_wg_profile_name(iface) == profile
    ]

    app.log_debug(f"Originalpfad = {original_path}")
    app.log_debug(f"exists(original) = {original_exists}")
    app.log_debug(f"aktive Interfaces = {active_ifaces}")

    if not original_exists and not active_ifaces:
        app.log(f"Dateiprofil nicht vorhanden: {profile}.conf")
        app.log("Löschen abgebrochen: Kein Dateiprofil vorhanden.")
        return

    if not original_exists and active_ifaces:
        app.log_debug(
            f"Kein Dateiprofil gefunden, aber aktives Interface vorhanden für '{profile}': {active_ifaces}"
        )
        app.log(
            "Versuche aktives Interface zu beenden und anschließend Delete zu prüfen."
        )

    active_profile = app._base_wg_profile_name(app.active_wg_profile())
    if active_profile and active_profile == profile:
        app.vpn_off(ensure_sudo=False, refresh_ui=False)
        remaining_ifaces = [
            iface
            for iface in app.get_wg_interfaces()
            if app._base_wg_profile_name(iface) == profile
        ]
        for iface in remaining_ifaces:
            rc_down, out_down = run_cmd(
                ["sudo", "-n", "wg-quick", "down", iface], timeout=12
            )
            if rc_down != 0:
                app.log(
                    f"Zusätzliches Stoppen fehlgeschlagen ({iface}): {(out_down or '').strip() or 'unknown'}"
                )
        remaining_ifaces = [
            iface
            for iface in app.get_wg_interfaces()
            if app._base_wg_profile_name(iface) == profile
        ]
        if remaining_ifaces:
            app.log(
                f"Löschen abgebrochen: WireGuard-Interface für '{profile}' ist noch aktiv: {', '.join(remaining_ifaces)}"
            )
            try:
                app.refresh()
            except Exception:
                pass
            return

    deleted = []
    missing = []
    failed = []
    internal_ipv4_profile = f"{profile}{WG_IPV4_PROFILE_SUFFIX}"

    exist_map = {
        profile: original_exists,
        internal_ipv4_profile: app._wg_profile_exists(internal_ipv4_profile),
    }

    for candidate, label in (
        (profile, "Originalprofil"),
        (internal_ipv4_profile, "Interne IPv4-Kopie"),
    ):
        candidate = (candidate or "").strip()
        if not candidate:
            continue

        target = app._wg_profile_path(candidate)
        candidate_exists = exist_map.get(candidate, app._wg_profile_exists(candidate))

        app.log_debug(
            f"Prüfe Löschung {label} ({candidate}) -> {target} (exists={candidate_exists})"
        )
        app.log_debug(f"target = {target}")
        app.log_debug(f"hostname = {socket.gethostname()}")
        try:
            app.log_debug(f"pwd = {os.getcwd()}")
        except Exception as exc:
            app.log_debug(f"pwd = <err: {exc}>")

        app.log_debug(f"exists(target) vor rm = {os.path.exists(target)}")
        app.log_debug("ls -l /etc/wireguard (vorher):")
        _rc_ls_before, out_ls_before = run_cmd(
            ["ls", "-l", "/etc/wireguard"], timeout=5
        )
        app.log_debug(out_ls_before or "<kein Output>")

        if not candidate_exists:
            if label == "Originalprofil":
                app.log(f"Dateiprofil nicht gefunden: {candidate}")
            else:
                app.log(f"Runtime-Dateiprofil nicht gefunden: {candidate}")
            missing.append((label, candidate))
            continue

        rc, out = run_cmd(["sudo", "-n", "rm", "-f", target], timeout=10)
        app.log_debug(f"sudo -n rm rc={rc}, out={out!r}")

        after_exists = os.path.exists(target)
        app.log_debug(f"exists(target) nach rm = {after_exists}")
        app.log_debug("ls -l /etc/wireguard (nachher):")
        _rc_ls_after, out_ls_after = run_cmd(["ls", "-l", "/etc/wireguard"], timeout=5)
        app.log_debug(out_ls_after or "<kein Output>")

        if rc != 0:
            failed.append(
                (
                    label,
                    candidate,
                    f"sudo rm fehlgeschlagen (rc={rc}): {(out or '').strip() or 'unknown'}",
                )
            )
            continue

        if app._wg_profile_exists(candidate):
            failed.append((label, candidate, "Datei existiert nach sudo rm weiterhin"))
        else:
            deleted.append((label, candidate))

    original_deleted = any(candidate == profile for _label, candidate in deleted)

    slots_cleared = 0
    if original_deleted:
        previous_slots = [dict(existing_slot) for existing_slot in app.vpn_slots]
        for slot in app.vpn_slots:
            slot_profile = app._base_wg_profile_name(slot.get("profile"))
            if slot_profile != profile:
                continue
            slot["profile"] = ""
            slot["custom_name"] = ""
            slots_cleared += 1
        if slots_cleared:
            save_result = app.save_vpn_slots_config()
            if save_result is False:
                app.vpn_slots = previous_slots
                slots_cleared = 0
                app.log(
                    "VPN-Slot-Bereinigung nach Profil-Löschung fehlgeschlagen – Slot-Änderungen wurden zurückgesetzt."
                )
        new_referenced_profiles = app._collect_referenced_vpn_profiles(
            include_active=True
        )
        new_referenced_interfaces = app._collect_interface_rules_for_profiles(
            new_referenced_profiles
        )
        new_referenced_endpoints = app._collect_endpoint_rules_for_profiles(
            new_referenced_profiles
        )
        if slots_cleared:
            reconcile_ok = app._reconcile_vpn_firewall_rules(
                old_interfaces=old_referenced_interfaces,
                new_interfaces=new_referenced_interfaces,
                old_endpoints=old_referenced_endpoints,
                new_endpoints=new_referenced_endpoints,
                removed_profile=profile,
            )
            if reconcile_ok is False:
                app.log(
                    "Firewall-Reconcile nach Profil-Löschung unvollständig. Bitte UFW-Regeln prüfen."
                )

    app.refresh_wg_profiles()
    if hasattr(app, "vpn_profile_combo"):
        app.vpn_profile_combo["values"] = app.wg_profiles
    app.update_primary_vpn_form_controls()
    app.sync_primary_vpn_form_selection()
    if original_deleted:
        app.vpn_profile_var.set("")
    app.sync_vpn_profile_form_selection()
    try:
        slot_no = int((app.vpn_slot_choice.get() or "0").strip())
    except ValueError:
        slot_no = 1
    if not (1 <= slot_no <= VPN_SLOT_COUNT):
        slot_no = 1
    if original_deleted:
        app.load_vpn_slot_into_form(slot_no)
    app.update_vpn_slot_buttons()
    app.refresh_vpn_slots_table()
    app.update_ipv6_controls_state()

    for label, candidate in deleted:
        app.log(f"{label} gelöscht: {candidate}")
    for label, candidate in missing:
        app.log(f"{label} nicht gefunden: {candidate}")
    for label, candidate, reason in failed:
        app.log(f"{label} löschen fehlgeschlagen ({candidate}): {reason}")
    if slots_cleared:
        app.log(f"VPN-Slots bereinigt: {slots_cleared}")
    if original_deleted:
        app.log(f"WireGuard-Profil gelöscht: {profile}")


def start_vpn_slot_profile(app, profile, slot_no=None, test_mode=False):
    profile = app._base_wg_profile_name(profile)
    if not profile:
        app.log("Bitte ein WireGuard-Profil auswählen.")
        return False
    if not app.ensure_sudo_session("VPN-Slot starten"):
        return False
    active_profile = app._base_wg_profile_name(app.active_wg_profile())
    if active_profile == profile:
        app.log_safe("VPN-Profil bereits aktiv.")
        app.refresh_safe()
        return True

    app.dns_guard_transition_until = time.time() + 5.0
    try:
        app.set_dns_guard_state("transition")
    except Exception:
        pass
    app.update_dns_controls_state_safe()

    def runner():
        try:
            ok = app.vpn_switch(profile, ensure_sudo=False, refresh_ui=False)
        except Exception as exc:
            ok = False
            app.log_safe(f"VPN-Slot-Start interner Fehler ({profile}): {exc}")
            app.log_debug_safe(traceback.format_exc())
        if ok:
            prefix = "VPN-Test" if test_mode else f"VPN-Slot {slot_no}"
            app.log_safe(f"{prefix}: {profile} gestartet.")
        elif test_mode:
            app.log_safe(f"VPN-Test fehlgeschlagen: {profile}")
        app.refresh_safe()
        return ok

    app.run_async(runner)
    return True


def test_vpn_slot(app):
    profile_input = (app.vpn_profile_var.get() or "").strip()
    profile = app._resolve_vpn_profile_input(profile_input, refresh_profiles=True)
    if not profile:
        app.log(
            "VPN-Test abgebrochen: Profil nicht gefunden. Bitte gültigen Profilnamen wählen/eingeben."
        )
        return
    if profile_input != profile:
        app.vpn_profile_var.set(profile)
    app._start_vpn_slot_profile(profile, test_mode=True)


def open_vpn_slot(app, idx):
    if idx < 0 or idx >= len(app.vpn_slots):
        return

    slot = app.vpn_slots[idx]
    profile = app._base_wg_profile_name(slot.get("profile"))

    if not profile:
        app.log(f"VPN-Slot {idx + 1} ist frei.")
        if hasattr(app, "tab_vpn_slots"):
            app._select_system_tab(app.tab_vpn_slots)
            app.load_vpn_slot_into_form(idx + 1)
        return

    if profile not in (app.wg_profiles or []):
        app.log(f"VPN-Slot {idx + 1}: Profil '{profile}' nicht gefunden.")
        if hasattr(app, "tab_vpn_slots"):
            app._select_system_tab(app.tab_vpn_slots)
            app.load_vpn_slot_into_form(idx + 1)
        return

    app._start_vpn_slot_profile(profile, slot_no=idx + 1)


def clear_manual_wireguard_form(app):
    if "manual_wg_profile_name_var" not in app.__dict__:
        return
    app.manual_wg_profile_name_var.set("")
    app.manual_wg_private_key_var.set("")
    app.manual_wg_public_key_var.set("")
    app.manual_wg_endpoint_var.set("")
    app.manual_wg_allowed_ips_var.set("0.0.0.0/0")
    app.manual_wg_dns_var.set("")
    app.manual_wg_keepalive_var.set("25")
    app.manual_wg_save_slot_var.set(False)
    app.manual_wg_slot_var.set("1")
    app._sync_manual_wg_slot_controls()
    app._set_manual_wg_status(
        "Eingabefelder zurückgesetzt.",
        level="info",
    )


def is_valid_wireguard_key(_app, value):
    token = (value or "").strip()
    if not token:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9+/=]{40,}", token))


def parse_manual_wireguard_endpoint(_app, endpoint):
    raw = (endpoint or "").strip()
    if not raw:
        return None, None, "Endpoint fehlt (Format host:port)."

    if raw.startswith("[") and "]:" in raw:
        host, port = raw[1:].split("]:", 1)
    else:
        host, sep, port = raw.rpartition(":")
        if not sep:
            return None, None, "Endpoint ungültig (Format host:port)."

    host = host.strip()
    port = port.strip()
    if not host:
        return None, None, "Endpoint-Host fehlt."
    if not port.isdigit():
        return None, None, "Endpoint-Port muss numerisch sein."
    port_no = int(port)
    if not (1 <= port_no <= 65535):
        return None, None, "Endpoint-Port muss zwischen 1 und 65535 liegen."

    return host, str(port_no), ""


def validate_manual_wireguard_form(app):
    profile = (app.manual_wg_profile_name_var.get() or "").strip()
    private_key = (app.manual_wg_private_key_var.get() or "").strip()
    public_key = (app.manual_wg_public_key_var.get() or "").strip()
    endpoint = (app.manual_wg_endpoint_var.get() or "").strip()
    allowed_ips_raw = (app.manual_wg_allowed_ips_var.get() or "").strip()
    dns_raw = (app.manual_wg_dns_var.get() or "").strip()
    keepalive_raw = (app.manual_wg_keepalive_var.get() or "").strip()

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", profile or ""):
        return None, "Profilname ungültig (erlaubt: A-Z, a-z, 0-9, _, -, .)."
    if app._is_internal_ipv4_profile(profile):
        return None, "Profilname darf nicht auf __ipv4 enden (reserviert)."

    if not app._is_valid_wireguard_key(private_key):
        return None, "Private Key ungültig."
    if not app._is_valid_wireguard_key(public_key):
        return None, "Public Key ungültig."

    endpoint_host, endpoint_port, endpoint_err = app._parse_manual_wireguard_endpoint(
        endpoint
    )
    if endpoint_err:
        return None, endpoint_err

    allowed_ips = [p.strip() for p in allowed_ips_raw.split(",") if p.strip()]
    if not allowed_ips:
        return None, "Allowed IPs darf nicht leer sein."
    for token in allowed_ips:
        try:
            ipaddress.ip_network(token, strict=False)
        except ValueError:
            return None, f"Allowed IP ungültig: {token}"

    dns_values = []
    if dns_raw:
        dns_values = [p.strip() for p in dns_raw.split(",") if p.strip()]
        for token in dns_values:
            candidate = token
            if candidate.startswith("[") and candidate.endswith("]"):
                candidate = candidate[1:-1].strip()
            try:
                ipaddress.ip_address(candidate)
            except ValueError:
                return None, f"DNS-Eintrag ungültig: {token}"

    keepalive = ""
    if keepalive_raw:
        if not keepalive_raw.isdigit():
            return None, "Persistent Keepalive muss numerisch sein."
        keepalive_no = int(keepalive_raw)
        if not (0 <= keepalive_no <= 65535):
            return None, "Persistent Keepalive muss zwischen 0 und 65535 liegen."
        keepalive = str(keepalive_no)

    normalized_endpoint = (
        f"[{endpoint_host}]:{endpoint_port}"
        if ":" in endpoint_host and not endpoint_host.startswith("[")
        else f"{endpoint_host}:{endpoint_port}"
    )

    return {
        "profile": profile,
        "private_key": private_key,
        "public_key": public_key,
        "endpoint": normalized_endpoint,
        "allowed_ips": ", ".join(allowed_ips),
        "dns": ", ".join(dns_values),
        "keepalive": keepalive,
    }, ""


def build_manual_wireguard_config_text(_app, payload):
    lines = [
        "[Interface]",
        f"PrivateKey = {payload['private_key']}",
    ]
    if payload.get("dns"):
        lines.append(f"DNS = {payload['dns']}")

    lines.extend(
        [
            "",
            "[Peer]",
            f"PublicKey = {payload['public_key']}",
            f"AllowedIPs = {payload['allowed_ips']}",
            f"Endpoint = {payload['endpoint']}",
        ]
    )
    if payload.get("keepalive"):
        lines.append(f"PersistentKeepalive = {payload['keepalive']}")

    return "\n".join(lines) + "\n"


def write_manual_wg_profile(app, profile_name, config_text):
    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_file.write(config_text)
            tmp_path = temp_file.name

        try:
            os.chmod(tmp_path, 0o600)
        except Exception:
            pass

        target = app._wg_profile_path(profile_name)
        rc, out = run_cmd(
            ["sudo", "-n", "install", "-m", "600", tmp_path, target],
            timeout=12,
        )
        if rc != 0:
            return False, (out or "").strip() or "unbekannter Fehler"
        return True, ""
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def assign_manual_profile_to_slot(app, profile_name, slot_no):
    if not (1 <= slot_no <= VPN_SLOT_COUNT):
        return False, "Ungültiger Zielslot für manuelles Profil."

    previous_slots = [dict(existing_slot) for existing_slot in app.vpn_slots]
    for idx, slot in enumerate(app.vpn_slots):
        if (
            idx != slot_no - 1
            and app._base_wg_profile_name(slot.get("profile")) == profile_name
        ):
            slot["profile"] = ""
            slot["custom_name"] = ""

    slot = app.vpn_slots[slot_no - 1]
    slot["profile"] = profile_name
    if not (slot.get("custom_name") or "").strip():
        slot["custom_name"] = profile_name

    save_result = app.save_vpn_slots_config()
    if save_result is False:
        app.vpn_slots = previous_slots
        return False, "VPN-Slot konnte nicht gespeichert werden."
    app.reconcile_vpn_slot_firewall_state(
        reason=f"Manuelle Slot-Zuordnung {slot_no}->{profile_name}",
        touched_profiles=[profile_name],
        refresh_ui=False,
    )
    return True, ""


def apply_manual_wireguard_profile(app):
    payload, err = app._validate_manual_wireguard_form()
    if err:
        app._set_manual_wg_status(
            f"Validierung fehlgeschlagen: {err}",
            level="error",
        )
        app.log(f"Manuelle WireGuard-Konfiguration ungültig: {err}")
        return

    save_to_slot = bool(app.manual_wg_save_slot_var.get())
    slot_no = 0
    if save_to_slot:
        try:
            slot_no = int((app.manual_wg_slot_var.get() or "0").strip())
        except ValueError:
            slot_no = 0
        if not (1 <= slot_no <= VPN_SLOT_COUNT):
            app._set_manual_wg_status(
                "Ungültiger VPN-Slot ausgewählt.",
                level="error",
            )
            app.log("Manuelles WireGuard-Profil: Ungültiger VPN-Slot ausgewählt.")
            return

    profile = payload["profile"]
    if not app.ensure_sudo_session(f"Manuelles WireGuard-Profil anwenden ({profile})"):
        app._set_manual_wg_status(
            "Sudo-Freigabe fehlt - Profil wurde nicht angewendet.",
            level="warn",
        )
        return

    app._set_manual_wg_status(
        f"Profil wird angewendet: {profile}",
        level="info",
    )
    app.log(f"Manuelle WireGuard-Konfiguration wird angewendet (Profil: {profile}).")

    def job():
        config_text = app._build_manual_wireguard_config_text(payload)
        ok_write, write_err = app._write_manual_wg_profile(profile, config_text)
        if not ok_write:
            app.after(
                0,
                lambda m=write_err: app._set_manual_wg_status(
                    f"Speichern fehlgeschlagen: {m}",
                    level="error",
                ),
            )
            app.after(
                0,
                lambda m=write_err: app.log(
                    f"Manuelles WireGuard-Profil konnte nicht gespeichert werden: {m}"
                ),
            )
            return

        app.refresh_wg_profiles()

        slot_saved = True
        slot_err = ""
        if save_to_slot:
            slot_saved, slot_err = app._assign_manual_profile_to_slot(profile, slot_no)

        start_ok = app.vpn_switch(profile, ensure_sudo=False, refresh_ui=False)

        def finish():
            if hasattr(app, "vpn_profile_combo"):
                app.vpn_profile_combo["values"] = app.wg_profiles
            app.update_primary_vpn_form_controls()
            app.sync_primary_vpn_form_selection()
            app.sync_vpn_profile_form_selection()
            app.update_vpn_slot_buttons()
            app.refresh_vpn_slots_table()
            app.update_ipv6_controls_state()

            if save_to_slot:
                if slot_saved:
                    app.log(
                        f"Manuelles Profil '{profile}' in VPN-Slot {slot_no} gespeichert."
                    )
                else:
                    app.log(
                        f"Manuelles Profil '{profile}' gestartet, Slot-Speicherung fehlgeschlagen: {slot_err}"
                    )

            if start_ok:
                app._set_manual_wg_status(
                    f"Profil aktiv: {profile}",
                    level="ok",
                )
                app.log(f"Manuelles WireGuard-Profil aktiv: {profile}")
            else:
                app._set_manual_wg_status(
                    f"Profil gespeichert, Start fehlgeschlagen: {profile}",
                    level="warn",
                )
                app.log(
                    f"Manuelles WireGuard-Profil gespeichert, Start fehlgeschlagen: {profile}"
                )

        app.after(0, finish)

    app.run_async(job)


def collect_interface_rules_for_profiles(
    app, profiles, include_family_candidates=False
):
    # include_family_candidates bleibt aus API-Kompatibilitätsgründen bestehen,
    # wird in der vereinfachten Architektur aber bewusst ignoriert.
    profile_set = {
        app._base_wg_profile_name(profile)
        for profile in (profiles or [])
        if app._base_wg_profile_name(profile)
    }
    interfaces = set()
    for base_profile in sorted(profile_set):
        resolved = app.resolve_profile_family_runtime(base_profile, log_missing=False)
        effective_ipv4 = (resolved.get("effective_ipv4_interface") or "").strip()
        effective_ipv6 = (resolved.get("effective_ipv6_interface") or "").strip()

        if effective_ipv4:
            interfaces.add(effective_ipv4)
        if effective_ipv6:
            interfaces.add(effective_ipv6)

        app.log_debug(
            f"[DEBUG] UFW-Regeln für {base_profile} basieren auf IPv4={effective_ipv4 or '-'}, IPv6={effective_ipv6 or 'None'}"
        )

    return {iface for iface in interfaces if iface}


def collect_interface_rules_for_profiles_safe(
    app, profiles, include_family_candidates=False
):
    collector = app._collect_interface_rules_for_profiles
    try:
        return collector(profiles, include_family_candidates=include_family_candidates)
    except TypeError:
        return collector(profiles)


def collect_endpoint_rules_for_profiles(app, profiles):
    endpoints = set()
    profile_set = {
        app._base_wg_profile_name(profile)
        for profile in (profiles or [])
        if app._base_wg_profile_name(profile)
    }
    for base_profile in sorted(profile_set):
        resolved = app.resolve_profile_family_runtime(base_profile, log_missing=False)
        candidates = resolved.get("endpoint_profiles") or [base_profile]
        for candidate in candidates:
            endpoint_ip, endpoint_port = app.parse_vpn_endpoint(candidate)
            if endpoint_ip and endpoint_port:
                endpoints.add((endpoint_ip, endpoint_port))
    return endpoints


def ensure_profile_family_ready_for_use(app, profile_name, log_failures=True):
    base_profile = app._base_wg_profile_name(profile_name)
    if not base_profile:
        return None
    resolved = app.resolve_profile_family_runtime(
        base_profile, log_missing=log_failures
    )
    app.log_debug(
        f"[DEBUG] Profilfamilie {base_profile}: base={base_profile}, ipv4={resolved.get('ipv4_profile') or '-'}"
    )
    return resolved


def apply_profile_ufw_rules_non_killswitch(app, interfaces, endpoints):
    interfaces = sorted(
        {str(i).strip() for i in (interfaces or set()) if str(i).strip()}
    )
    endpoints = sorted(
        {
            (str(ip).strip(), str(port).strip())
            for ip, port in (endpoints or set())
            if str(ip).strip() and str(port).strip()
        }
    )
    if not interfaces and not endpoints:
        app.log_debug(
            "VPN/UFW-Reconcile: Keine Interface- oder Endpoint-Regeln erforderlich."
        )
        return True

    network_service = app._network_service()
    with app.ufw_lock:
        rc_status, out_status = app._read_ufw_status(verbose=True)
        if rc_status != 0:
            app.log(
                "VPN/UFW-Reconcile: UFW-Status nicht lesbar – Regelsetzung übersprungen."
            )
            if out_status:
                app.log_debug_safe(out_status)
            return False
        if not app._ufw_status_is_active(out_status):
            app.log(
                "VPN/UFW-Reconcile: UFW ist deaktiviert – Vorbereitung gespeichert, Regelsetzung übersprungen."
            )
            return True

        known_keys = app._ufw_existing_rule_keys(out_status)

        added_iface_rules = []
        added_endpoint_rules = []
        failed_rules = []
        dedup_removed = 0

        for iface in interfaces:
            app.log_debug(f"[DEBUG] UFW-Regeln werden auf Interface {iface} angewendet")
            for direction in ("out", "in"):
                ok_rule, added, detail, known_keys = app.ensure_ufw_rule_exists(
                    {
                        "type": "interface",
                        "iface": iface,
                        "direction": direction,
                    },
                    network_service=network_service,
                    known_keys=known_keys,
                )
                if ok_rule and not added:
                    continue
                if ok_rule and added:
                    added_iface_rules.append(f"{direction} on {iface}")
                else:
                    failed_rules.append((f"{direction} on {iface}", detail))

        for endpoint_ip, endpoint_port in endpoints:
            ok_rule, added, detail, known_keys = app.ensure_ufw_rule_exists(
                {
                    "type": "endpoint",
                    "ip": endpoint_ip,
                    "port": endpoint_port,
                },
                network_service=network_service,
                known_keys=known_keys,
            )
            if ok_rule and not added:
                continue
            if ok_rule and added:
                added_endpoint_rules.append(f"{endpoint_ip}:{endpoint_port}")
            else:
                failed_rules.append(
                    (f"udp endpoint {endpoint_ip}:{endpoint_port}", detail)
                )

        dedup_removed = app._dedupe_vpn_ufw_rules()

    if dedup_removed:
        app.log(f"UFW-Duplikate bereinigt: {dedup_removed}")

    if added_iface_rules:
        app.log("UFW-Regeln gesetzt (Interfaces): " + ", ".join(added_iface_rules))
    if added_endpoint_rules:
        app.log("UDP-Endpoint-Regeln gesetzt: " + ", ".join(added_endpoint_rules))
    if not added_iface_rules and not added_endpoint_rules:
        app.log_debug(
            "VPN/UFW-Reconcile: Alle benötigten Regeln waren bereits vorhanden."
        )

    if failed_rules:
        app.log(
            "VPN/UFW-Reconcile: Einige Regeln konnten nicht gesetzt werden: "
            + ", ".join(label for label, _ in failed_rules)
        )
        detail = failed_rules[0][1]
        if detail:
            app.log_debug_safe(detail)
        return False
    return True


def reconcile_vpn_slot_firewall_state(
    app, reason="", touched_profiles=None, refresh_ui=False
):
    touched = []
    for profile in touched_profiles or []:
        base = app._base_wg_profile_name(profile)
        if base and base not in touched:
            touched.append(base)

    referenced_profiles = app._collect_referenced_vpn_profiles(include_active=True)
    for profile in touched:
        if profile not in referenced_profiles:
            referenced_profiles.append(profile)

    resolved_by_profile = {}
    for profile in sorted(set(referenced_profiles)):
        resolved = app.ensure_profile_family_ready_for_use(profile, log_failures=True)
        if resolved:
            resolved_by_profile[profile] = resolved

    if touched:
        for profile in touched:
            resolved = resolved_by_profile.get(profile) or {}
            app.log(
                f"Profilfamilie vorbereitet: {profile} | "
                f"IPv4-Interface={resolved.get('effective_ipv4_interface') or '-'} | "
                f"IPv6-Interface={resolved.get('effective_ipv6_interface') or 'None'}"
            )

    interfaces = app._collect_interface_rules_for_profiles(referenced_profiles)
    endpoints = app._collect_endpoint_rules_for_profiles(referenced_profiles)

    reason_text = (reason or "").strip() or "VPN-Slot-Reconcile"
    app.log_debug(
        f"[DEBUG] {reason_text}: Interfaces={sorted(interfaces)} Endpoints={sorted(endpoints)}"
    )

    if not has_cmd("ufw"):
        app.log(
            "VPN/UFW-Reconcile: UFW nicht verfügbar – nur Profilvorbereitung durchgeführt."
        )
        return True

    if app.killswitch_is_on():
        app.log(
            "Killswitch-Sollzustand wird mit aktueller Profilfamilie synchronisiert."
        )
        ok = app._killswitch_on_sync(refresh_ui=refresh_ui)
        if ok:
            app.log("Killswitch-Sollzustand vorbereitet.")
        return ok

    ok = app._apply_profile_ufw_rules_non_killswitch(interfaces, endpoints)
    if ok:
        app.log("VPN/UFW-Sollzustand vorbereitet.")
    return ok


def remove_firewall_rules_for_vpn_profile(app, profile, removed_from_slot=None):
    profile = app._base_wg_profile_name(profile)
    if not profile:
        app.log("Firewall-Cleanup übersprungen: Kein Profil im Slot hinterlegt.")
        return True

    if app._is_vpn_profile_referenced_in_other_slots(
        profile, skip_slot_no=removed_from_slot
    ):
        app.log(
            f"Firewall-Cleanup übersprungen: Profil '{profile}' wird noch in einem anderen VPN-Slot verwendet."
        )
        return True

    profile_interfaces = app._collect_interface_rules_for_profiles_safe(
        [profile], include_family_candidates=True
    )
    profile_endpoints = app._collect_endpoint_rules_for_profiles([profile])
    all_profiles = app._collect_referenced_vpn_profiles(include_active=True)
    referenced_interfaces = app._collect_interface_rules_for_profiles(all_profiles)
    referenced_endpoints = app._collect_endpoint_rules_for_profiles(all_profiles)
    return app._reconcile_vpn_firewall_rules(
        old_interfaces=profile_interfaces,
        new_interfaces=referenced_interfaces,
        old_endpoints=profile_endpoints,
        new_endpoints=referenced_endpoints,
        removed_profile=profile,
    )
