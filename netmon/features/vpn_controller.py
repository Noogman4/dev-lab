"""VPN controller helpers for NetMon."""

from __future__ import annotations

import ipaddress
import hashlib
import json
import logging
import os
import re
import socket
import threading
import time
import traceback
from tkinter import filedialog, messagebox

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
    from netmon.core import manual_wireguard, nm_ownership, wireguard_import
    from netmon.core.command import run_cmd, run_cmd_with_input
    from netmon.core.nm_import_session import ImportSession
except ModuleNotFoundError:
    from core import manual_wireguard, nm_ownership, wireguard_import
    from core.command import run_cmd, run_cmd_with_input
    from core.nm_import_session import ImportSession

try:
    from netmon.core.tooling import has_cmd
except ModuleNotFoundError:
    from core.tooling import has_cmd

try:
    from netmon.core.utils import safe_write_json, call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import safe_write_json, call_in_ui_thread

try:
    from netmon.core.state import get_netmon_documents_dir
except ModuleNotFoundError:
    from core.state import get_netmon_documents_dir


def _app_value(app, name, default=None):
    return app.__dict__.get(name, default)


def _app_list(app, name):
    return _app_value(app, name, []) or []


def _app_var_get(app, name):
    var = _app_value(app, name, None)
    if var is None:
        return ""
    try:
        return var.get()
    except Exception:
        return ""


def _app_var_set(app, name, value):
    var = _app_value(app, name, None)
    if var is None:
        return False
    try:
        var.set(value)
        return True
    except Exception:
        return False


def _single_line(text) -> str:
    return " ".join(str(text or "").split())


def _format_command_output(out) -> str:
    text = str(out or "").strip()
    if not text:
        return "-"
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "-"
    if len(lines) == 1:
        return lines[0]
    return "\n".join(f"    {line}" for line in lines)


def _log_command_result(app, scope: str, cmd, rc, out):
    scope = str(scope or "CMD").strip().upper()
    app.log_network_debug(f"[VPN][{scope}] cmd: {_single_line(' '.join(cmd or []))}")
    app.log_network_debug(f"[VPN][{scope}] rc: {int(rc)}")
    app.log_network_debug(f"[VPN][{scope}] out:\n{_format_command_output(out)}")


def _vpn_user_log(app, message: str):
    text = str(message or "").strip()
    if not text:
        return
    app.log_safe(text)


WIREGUARD_HOOK_DIRECTIVES = {"preup", "postup", "predown", "postdown"}


def _wireguard_profile_hook_directives(path: str) -> list[str]:
    return list(wireguard_import.ProfileSnapshot.read(path).hooks)


def _warn_wireguard_import_hooks(app, selected_files) -> bool:
    findings = []
    for src in list(selected_files or []):
        snapshot = (
            src
            if isinstance(src, wireguard_import.ProfileSnapshot)
            else wireguard_import.ProfileSnapshot.read(src)
        )
        directives = snapshot.hooks
        if directives:
            findings.append((snapshot.name, directives))
    if not findings:
        return False

    details = "; ".join(
        f"{name}: {', '.join(directives)}" for name, directives in findings
    )
    text = app.tr(
        "wg_import_hooks_warning",
        "Hinweis: Das ausgewählte WireGuard-Profil enthält Hook-Direktiven "
        "wie PreUp/PostUp/PreDown/PostDown. Diese Befehle können bei der "
        "Profil-Aktivierung mit Root-Rechten ausgeführt werden.\n\n"
        "Gefundene Direktiven:\n{details}",
    ).format(details=details)
    try:
        messagebox.showwarning(
            app.tr("wg_import_hooks_warning_title", "WireGuard Hook-Hinweis"),
            text,
            parent=app,
        )
    except Exception:
        pass
    _vpn_user_log(app, _single_line(text))
    return True


def _prepare_wireguard_imports(app, paths):
    """Read and confirm one exact immutable batch on the caller/UI thread."""
    snapshots = []
    total = 0
    if len(paths) > wireguard_import.MAX_PROFILES:
        raise ValueError("Zu viele WireGuard-Profile ausgewaehlt")
    for path in paths:
        if isinstance(path, wireguard_import.ProfileSnapshot):
            raise ValueError("Unbestaetigte Snapshot-Uebergabe")
        name = wireguard_import.profile_name(path)
        if str(path) == os.path.join(nm_ownership.PROFILE_DIRECTORY, name + ".conf"):
            payload = _owned_nm_command("snapshot-profile", payload={"name": name})
            nm_ownership.checked_import_payload(payload)
            snapshot = wireguard_import.ProfileSnapshot.from_bytes(
                path, name, payload["content"].encode(), protected=True
            )
        else:
            snapshot = wireguard_import.ProfileSnapshot.read(path)
        total += len(snapshot.data)
        if total > wireguard_import.MAX_BATCH_BYTES:
            raise ValueError("WireGuard-Import-Batch ist zu gross")
        snapshots.append(snapshot)
    if not snapshots:
        return None
    _warn_wireguard_import_hooks(app, snapshots)
    details = "\n".join(
        f"{s.name}: {', '.join(s.hooks) or '-'}\nSHA-256: {s.sha256}" for s in snapshots
    )
    # Digest is of the reviewed bytes, not a mutable pathname. Never display keys
    # or hook command values; an unavailable/closed GUI cannot approve the batch.
    text = (
        "Gepruefte WireGuard-Profile importieren? / Import reviewed WireGuard profiles?\n\n"
        + details
    )
    if not messagebox.askyesno("WireGuard-Import bestaetigen", text, parent=app):
        return None
    return tuple(snapshots)


def _verify_import_snapshot(snapshot):
    snapshot.verify_source()
    payload = snapshot.payload()
    nm_ownership.checked_import_payload(payload)
    if snapshot.protected:
        latest = _owned_nm_command("snapshot-profile", payload={"name": snapshot.name})
        nm_ownership.checked_import_payload(latest)
        if latest != payload:
            raise ValueError(
                "Geschuetztes WireGuard-Profil wurde nach Bestaetigung veraendert"
            )
    return payload


def _install_wireguard_snapshot(app, snapshot):
    target = app._wg_profile_path(snapshot.name)
    if target != os.path.join(nm_ownership.PROFILE_DIRECTORY, snapshot.name + ".conf"):
        raise ValueError("Unsicherer WireGuard-Zielpfad")
    _owned_nm_command("install-profile", payload=_verify_import_snapshot(snapshot))


def _write_generated_wireguard_profile(app, name, content):
    snapshot = wireguard_import.ProfileSnapshot.from_bytes(
        "generated", name, content.encode("utf-8")
    )
    _install_wireguard_snapshot(app, snapshot)


def _warn_non_ip_endpoint_once(app, profile_name: str, host: str) -> None:
    warned = app.__dict__.setdefault("_vpn_non_ip_endpoint_warned_profiles", set())
    key = (str(profile_name or "").strip(), str(host or "").strip())
    if key in warned:
        return
    warned.add(key)
    _vpn_user_log(
        app,
        (
            "WireGuard-Hinweis: Profil "
            f"'{profile_name}' nutzt den Endpoint-Host '{host}'. "
            "Für Firewall-/Killswitch-Handshake-Regeln werden nur feste IP-Adressen unterstützt."
        ),
    )


def _show_killswitch_active_after_vpn_off_notice(app) -> bool:
    try:
        killswitch_active = bool(app.killswitch_is_on())
    except Exception:
        killswitch_active = False
    if not killswitch_active:
        return False

    title = app.tr(
        "vpn_off_killswitch_notice_title",
        "Killswitch bleibt aktiv",
    )
    message = app.tr(
        "vpn_off_killswitch_notice_message",
        "VPN wurde deaktiviert, der Killswitch ist aber noch aktiv.\n\n"
        "Bitte Killswitch deaktivieren, wenn du danach wieder normales Netz "
        "verwenden möchtest.",
    )
    try:
        messagebox.showwarning(title, message, parent=app)
    except Exception:
        pass
    return True


def collect_non_ip_endpoint_profiles(app, profiles):
    results = []
    seen = set()
    for profile_name in profiles or []:
        profile_name = app._base_wg_profile_name(profile_name)
        if not profile_name:
            continue
        try:
            rc, out = app._read_wg_profile_text(profile_name)
        except Exception:
            path = app._wg_profile_path(profile_name)
            if not path:
                continue
            rc, out = run_cmd(["sudo", "-n", "cat", path], timeout=5)
            if rc != 0:
                rc, out = run_cmd(["cat", path], timeout=5)
        if rc != 0:
            continue

        for raw_line in (out or "").splitlines():
            line = raw_line.split("#", 1)[0].split(";", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key, value = [part.strip() for part in line.split("=", 1)]
            if key.lower() != "endpoint" or not value:
                continue

            if value.startswith("[") and "]:" in value:
                host, _port = value[1:].split("]:", 1)
            else:
                host, sep, _port = value.rpartition(":")
                if not sep:
                    continue

            host = host.strip()
            if not host:
                continue
            try:
                ipaddress.ip_address(host)
            except ValueError:
                key = (profile_name, host)
                if key not in seen:
                    seen.add(key)
                    results.append({"profile": profile_name, "host": host})
            break
    return results


def _privacy_config_dict(app):
    raw_config = _app_value(app, "privacy_config", None)
    if isinstance(raw_config, dict):
        return raw_config
    raw_config = {}
    app.__dict__["privacy_config"] = raw_config
    return raw_config


def netmon_wireguard_profiles_dir():
    path = os.path.join(get_netmon_documents_dir(), "WireGuard")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _legacy_netmon_wireguard_profiles_dir():
    return os.path.expanduser("~/.local/share/netmon/wireguard")


def ensure_netmon_wireguard_profiles_dir():
    target_dir = netmon_wireguard_profiles_dir()
    legacy_dir = _legacy_netmon_wireguard_profiles_dir()
    if os.path.isdir(legacy_dir) and os.path.abspath(legacy_dir) != os.path.abspath(
        target_dir
    ):
        try:
            entries = sorted(os.listdir(legacy_dir))
        except OSError:
            entries = []
        for entry in entries:
            source = os.path.join(legacy_dir, entry)
            target = os.path.join(target_dir, entry)
            if not os.path.isfile(source) or os.path.exists(target):
                continue
            try:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(source, "rb") as src_handle, open(target, "wb") as dst_handle:
                    dst_handle.write(src_handle.read())
            except Exception:
                continue
    return target_dir


def _save_privacy_config_safe(app, error_prefix: str = "") -> bool:
    save_fn = getattr(app, "save_privacy_config", None)
    if not callable(save_fn):
        return False
    try:
        save_fn()
    except Exception as exc:
        prefix = str(error_prefix or "").strip()
        if prefix:
            app.log_debug_safe(f"{prefix}: {exc}")
        return False
    return True


def _normalized_nm_last_import_state(state):
    raw_state = state if isinstance(state, dict) else {}
    connections = [
        str(item or "").strip()
        for item in raw_state.get("connections", [])
        if str(item or "").strip()
    ]
    source_files = [
        str(item or "").strip()
        for item in raw_state.get("source_files", [])
        if str(item or "").strip()
    ]
    imported_at = raw_state.get("imported_at", 0)
    try:
        imported_at = int(imported_at or 0)
    except (TypeError, ValueError):
        imported_at = 0
    result = {
        "connections": connections,
        "source_files": source_files,
        "imported_at": imported_at,
    }
    # Session references only. The root helper independently verifies every
    # receipt, UUID and keyfile; this user-controlled state grants no ownership.
    if isinstance(raw_state.get("owned_connections"), list):
        result["owned_connections"] = [
            item
            for item in raw_state["owned_connections"][:512]
            if isinstance(item, dict)
        ]
    return result


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
    slot_labels = {}
    slots = _app_list(app, "primary_vpn_slots")
    for slot in slots:
        profile = app._base_wg_profile_name(slot.get("profile"))
        if not profile:
            continue
        raw_label = (slot.get("custom_name") or "").strip()
        if raw_label and profile not in slot_labels:
            slot_labels[profile] = raw_label

    available_profiles = [
        app._base_wg_profile_name(profile) for profile in _app_list(app, "wg_profiles")
    ]
    available_profiles = [profile for profile in available_profiles if profile]

    source_profiles = []
    if available_profiles:
        source_profiles.extend(available_profiles)
    else:
        for slot in slots:
            profile = app._base_wg_profile_name(slot.get("profile"))
            if profile:
                source_profiles.append(profile)

    seen_profiles = set()
    for profile in source_profiles:
        if profile in seen_profiles:
            continue
        seen_profiles.add(profile)

        label = slot_labels.get(profile) or profile
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


INTERNAL_IPV4_PROFILE_PREFIX = "n4_"
INTERNAL_IPV4_PROFILE_BASE_MARKER = "# NetMon-Base-Profile: "
INTERNAL_IPV4_PROFILE_KIND_MARKER = "# NetMon-Internal-IPv4: yes"


def _legacy_internal_ipv4_profile_name(base_profile):
    return f"{base_profile}{WG_IPV4_PROFILE_SUFFIX}"


def _compact_internal_ipv4_profile_name(base_profile):
    raw = str(base_profile or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "", raw) or "wg"
    digest = hashlib.sha1(
        str(base_profile or "").encode("utf-8"), usedforsecurity=False
    ).hexdigest()[:4]
    stem_max = max(1, 15 - len(INTERNAL_IPV4_PROFILE_PREFIX) - len(digest))
    stem = cleaned[:stem_max]
    return f"{INTERNAL_IPV4_PROFILE_PREFIX}{stem}{digest}"


def _unique_profile_names(candidates):
    unique = []
    seen = set()
    for candidate in candidates:
        name = str(candidate or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def _read_internal_ipv4_base_profile_marker(app, profile_name):
    rc, out = read_wg_profile_text(app, profile_name)
    if rc != 0:
        return ""
    for raw_line in (out or "").splitlines():
        line = str(raw_line or "").strip()
        if line.startswith(INTERNAL_IPV4_PROFILE_BASE_MARKER):
            return line[len(INTERNAL_IPV4_PROFILE_BASE_MARKER) :].strip()
    return ""


def base_wg_profile_name(app, profile):
    name = str(profile or "").strip()
    if not name:
        return ""
    if name.endswith(WG_IPV4_PROFILE_SUFFIX):
        return name[: -len(WG_IPV4_PROFILE_SUFFIX)].strip()
    if name.startswith(INTERNAL_IPV4_PROFILE_PREFIX):
        resolved = _read_internal_ipv4_base_profile_marker(app, name)
        if resolved:
            return resolved
    return name


def internal_ipv4_profile_candidates(app, profile_name):
    base_profile = base_wg_profile_name(app, profile_name)
    if not base_profile:
        return []
    legacy_name = _legacy_internal_ipv4_profile_name(base_profile)
    preferred_name = (
        legacy_name
        if len(legacy_name) <= 15
        else _compact_internal_ipv4_profile_name(base_profile)
    )
    candidates = [preferred_name]
    if legacy_name != preferred_name:
        candidates.append(legacy_name)
    return _unique_profile_names(candidates)


def internal_ipv4_profile_name(app, profile_name):
    candidates = internal_ipv4_profile_candidates(app, profile_name)
    return candidates[0] if candidates else ""


def is_internal_ipv4_profile(app, profile_name):
    name = str(profile_name or "").strip()
    if not name:
        return False
    if name.endswith(WG_IPV4_PROFILE_SUFFIX):
        return True
    if name.startswith(INTERNAL_IPV4_PROFILE_PREFIX):
        return bool(_read_internal_ipv4_base_profile_marker(app, name))
    return False


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
    combo = _app_value(app, "isp_stealth_vpn_combo")
    if combo is not None:
        try:
            if combo.winfo_exists():
                combo["values"] = values
        except Exception:
            pass

    current_profile = str(_app_var_get(app, "isp_stealth_vpn_profile") or "").strip()
    if current_profile and app._privacy_vpn_label_for_profile(current_profile):
        _app_var_set(
            app,
            "isp_stealth_vpn_choice",
            app._privacy_vpn_label_for_profile(current_profile),
        )
        _app_var_set(app, "isp_stealth_vpn_profile", current_profile)
    else:
        if current_profile:
            _app_var_set(app, "isp_stealth_vpn_profile", "")
        _app_var_set(app, "isp_stealth_vpn_choice", "")
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


def _widget_alive(widget):
    try:
        return widget is not None and bool(widget.winfo_exists())
    except Exception:
        return False


def update_primary_vpn_buttons(app):
    btn1 = _app_value(app, "btn_primary_vpn_1")
    btn2 = _app_value(app, "btn_primary_vpn_2")
    primary_slots = _app_list(app, "primary_vpn_slots")
    if len(primary_slots) < 2:
        return

    if _widget_alive(btn1):
        btn1.config(text=primary_slots[0].get("custom_name", "VPN CH"))
    if _widget_alive(btn2):
        btn2.config(text=primary_slots[1].get("custom_name", "VPN DE"))


def update_primary_vpn_form_controls(app):
    if threading.current_thread() is not threading.main_thread():
        call_in_ui_thread(app, app.update_primary_vpn_form_controls)
        return
    combo1 = _app_value(app, "primary_vpn_1_profile_combo")
    combo2 = _app_value(app, "primary_vpn_2_profile_combo")

    if _widget_alive(combo1):
        combo1["values"] = app.wg_profiles

    if _widget_alive(combo2):
        combo2["values"] = app.wg_profiles


def refresh_vpn_slots_table(app):
    if threading.current_thread() is not threading.main_thread():
        call_in_ui_thread(app, app.refresh_vpn_slots_table)
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
        call_in_ui_thread(app, app.sync_primary_vpn_form_selection)
        return
    available_profiles = set(_app_list(app, "wg_profiles"))
    primary_slots = _app_list(app, "primary_vpn_slots")
    if len(primary_slots) < 2:
        return
    for slot_no, (var_name, combo_name) in enumerate(
        (
            ("primary_vpn_1_profile_var", "primary_vpn_1_profile_combo"),
            ("primary_vpn_2_profile_var", "primary_vpn_2_profile_combo"),
        ),
        1,
    ):
        saved_profile = primary_slots[slot_no - 1].get("profile", "")
        base_profile = app._base_wg_profile_name(saved_profile)
        current_value = ""
        try:
            current_value = str(getattr(app, var_name).get() or "").strip()
        except Exception:
            current_value = ""
        current_base_profile = app._base_wg_profile_name(current_value)

        # Do not overwrite a manually changed combobox value that has not been saved yet.
        if current_base_profile and current_base_profile != base_profile:
            combo = _app_value(app, combo_name)
            if _widget_alive(combo):
                try:
                    combo.configure(values=app.wg_profiles)
                except Exception:
                    pass
            continue

        if base_profile and base_profile in available_profiles:
            _app_var_set(app, var_name, saved_profile)
        else:
            _app_var_set(app, var_name, "")


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
        call_in_ui_thread(app, app.sync_vpn_profile_form_selection)
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
        combo = _app_value(app, "vpn_profile_combo")
        if combo is not None:
            try:
                combo["values"] = app.wg_profiles
            except Exception:
                pass

    profiles = [
        app._base_wg_profile_name(name)
        for name in _app_list(app, "wg_profiles")
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
        table = app.__dict__.get("vpn_table")
        if table is not None:
            try:
                selection = table.selection()
            except Exception:
                selection = ()
            if selection:
                try:
                    values = table.item(selection[0], "values")
                except Exception:
                    values = ()
                if values and len(values) >= 3:
                    profile = app._base_wg_profile_name(values[2])
                    if profile:
                        try:
                            app.vpn_profile_var.set(profile)
                        except Exception:
                            pass
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
    active_connections = [
        name
        for name in get_active_nm_vpn_connections(app)
        if app._base_wg_profile_name(name) == profile
        or str(name or "").strip() == profile
    ]

    app.log_debug(f"Originalpfad = {original_path}")
    app.log_debug(f"exists(original) = {original_exists}")
    app.log_debug(f"aktive NetworkManager-VPNs = {active_connections}")

    if not original_exists and not active_connections:
        app.log(f"Dateiprofil nicht vorhanden: {profile}.conf")
        app.log("Löschen abgebrochen: Kein Dateiprofil vorhanden.")
        return

    if not original_exists and active_connections:
        app.log_debug(
            "Kein Dateiprofil gefunden, aber aktive NetworkManager-VPN-Verbindung "
            f"vorhanden für '{profile}': {active_connections}"
        )
        app.log(
            "Versuche aktive VPN-Verbindung zu beenden und anschließend Delete zu prüfen."
        )

    active_profile = app._base_wg_profile_name(app.active_wg_profile())
    if active_profile and active_profile == profile:
        app.vpn_off(ensure_sudo=False, refresh_ui=False)
        remaining_connections = [
            name
            for name in get_active_nm_vpn_connections(app)
            if app._base_wg_profile_name(name) == profile
            or str(name or "").strip() == profile
        ]
        if remaining_connections:
            app.log(
                "Löschen abgebrochen: VPN-Verbindung für "
                f"'{profile}' ist noch aktiv: {', '.join(remaining_connections)}"
            )
            try:
                app.refresh()
            except Exception:
                pass
            return

    deleted = []
    missing = []
    failed = []
    internal_ipv4_profiles = app._internal_ipv4_profile_candidates(profile)

    exist_map = {profile: original_exists}
    for internal_profile in internal_ipv4_profiles:
        exist_map[internal_profile] = app._wg_profile_exists(internal_profile)

    delete_candidates = [(profile, "Originalprofil")]
    for index, internal_profile in enumerate(internal_ipv4_profiles):
        label = "Interne IPv4-Kopie" if index == 0 else "Alte interne IPv4-Kopie"
        delete_candidates.append((internal_profile, label))

    for candidate, label in delete_candidates:
        candidate = (candidate or "").strip()
        if not candidate:
            continue

        target = app._wg_profile_path(candidate)
        candidate_exists = exist_map.get(candidate, app._wg_profile_exists(candidate))
        if not target:
            failed.append((label, candidate, "Ungültiger WireGuard-Profilpfad"))
            continue

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
    primary_slots_cleared = 0
    privacy_profile_cleared = False
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

        previous_primary_slots = [
            dict(existing_slot)
            for existing_slot in app.__dict__.get("primary_vpn_slots", [])
        ]
        for slot in app.__dict__.get("primary_vpn_slots", []):
            slot_profile = app._base_wg_profile_name(slot.get("profile"))
            if slot_profile != profile:
                continue
            slot["profile"] = ""
            slot["custom_name"] = ""
            primary_slots_cleared += 1
        if primary_slots_cleared:
            try:
                app.save_primary_vpn_slots_config()
            except Exception as exc:
                app.primary_vpn_slots = previous_primary_slots
                primary_slots_cleared = 0
                app.log(
                    "Primäre VPN-Slot-Bereinigung nach Profil-Löschung fehlgeschlagen – Änderungen wurden zurückgesetzt."
                )
                app.log_debug_safe(
                    f"Primäre VPN-Slot-Bereinigung fehlgeschlagen: {exc}"
                )

        privacy_config = _privacy_config_dict(app)
        privacy_profile = app._base_wg_profile_name(privacy_config.get("vpn_profile"))
        if privacy_profile == profile:
            privacy_config["vpn_profile"] = ""
            _app_var_set(app, "isp_stealth_vpn_profile", "")
            _app_var_set(app, "isp_stealth_vpn_choice", "")
            privacy_profile_cleared = _save_privacy_config_safe(
                app,
                "Privacy-Konfig konnte nach Profil-Löschung nicht gespeichert werden",
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
    if primary_slots_cleared:
        app.log(f"Primäre VPN-Slots bereinigt: {primary_slots_cleared}")
    if privacy_profile_cleared:
        app.log("Privacy-VPN-Profil zurückgesetzt.")
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

    resolved_profile = app._resolve_vpn_profile_input(profile, refresh_profiles=False)

    def profile_is_available(candidate):
        if not candidate:
            return False
        if candidate in (app.wg_profiles or []):
            return True
        try:
            return bool(app._wg_profile_exists(candidate))
        except Exception:
            return False

    if not profile_is_available(resolved_profile):
        resolved_profile = app._resolve_vpn_profile_input(
            profile, refresh_profiles=True
        )

    if not profile_is_available(resolved_profile):
        app.log(f"VPN-Slot {idx + 1}: Profil '{profile}' nicht gefunden.")
        if hasattr(app, "tab_vpn_slots"):
            app._select_system_tab(app.tab_vpn_slots)
            app.load_vpn_slot_into_form(idx + 1)
        return

    app._start_vpn_slot_profile(resolved_profile, slot_no=idx + 1)


def clear_manual_wireguard_form(app):
    if "manual_wg_profile_name_var" not in app.__dict__:
        return
    app.manual_wg_profile_name_var.set("")
    app.manual_wg_private_key_var.set("")
    app.manual_wg_public_key_var.set("")
    app.manual_wg_preshared_key_var.set("")
    app.manual_wg_endpoint_var.set("")
    app.manual_wg_address_var.set("")
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


def normalize_wireguard_key(_app, value):
    token = str(value or "").strip()
    token = " ".join(token.split())
    token = token.replace(" ", "")
    if token.startswith("=") and token.count("=") >= 2:
        token = token[1:].strip()
    return token


def validate_wireguard_key_value(app, value, label):
    token = app._normalize_wireguard_key(value)
    if not token:
        return "", f"{label} fehlt."
    if not app._is_valid_wireguard_key(token):
        return (
            "",
            f"{label} ungültig. Bitte nur den reinen Base64-Key ohne führendes '=' oder zusätzliche Zeichen einfügen.",
        )
    return token, ""


def manual_wireguard_error_widget_name(_app, error_text):
    text = str(error_text or "").strip()
    mapping = (
        ("Profilname", "manual_wg_profile_name_entry"),
        ("Private Key", "manual_wg_private_key_entry"),
        ("Public Key", "manual_wg_public_key_entry"),
        ("Preshared Key", "manual_wg_preshared_key_entry"),
        ("Endpoint", "manual_wg_endpoint_entry"),
        ("Address", "manual_wg_address_entry"),
        ("Allowed IP", "manual_wg_allowed_ips_entry"),
        ("DNS-Eintrag", "manual_wg_dns_entry"),
        ("Persistent Keepalive", "manual_wg_keepalive_entry"),
        ("VPN-Slot", "manual_wg_slot_combo"),
    )
    for prefix, widget_name in mapping:
        if text.startswith(prefix):
            return widget_name
    return ""


def parse_manual_wireguard_endpoint(_app, endpoint):
    try:
        host, port = manual_wireguard.parse_endpoint(endpoint)
        return host, port, ""
    except ValueError as exc:
        return None, None, str(exc)


def validate_manual_wireguard_form(app):
    profile = (app.manual_wg_profile_name_var.get() or "").strip()
    private_key_raw = app.manual_wg_private_key_var.get() or ""
    public_key_raw = app.manual_wg_public_key_var.get() or ""
    preshared_key_var = app.__dict__.get("manual_wg_preshared_key_var")
    preshared_key_raw = preshared_key_var.get() if preshared_key_var is not None else ""
    preshared_key_raw = preshared_key_raw or ""
    endpoint = app.manual_wg_endpoint_var.get() or ""
    address_raw = (app.manual_wg_address_var.get() or "").strip()
    allowed_ips_raw = (app.manual_wg_allowed_ips_var.get() or "").strip()
    dns_raw = (app.manual_wg_dns_var.get() or "").strip()
    keepalive_raw = (app.manual_wg_keepalive_var.get() or "").strip()

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", profile or ""):
        return None, "Profilname ungültig (erlaubt: A-Z, a-z, 0-9, _, -, .)."
    if app._is_internal_ipv4_profile(profile) or profile.startswith(
        INTERNAL_IPV4_PROFILE_PREFIX
    ):
        return (
            None,
            "Profilname ist fuer interne NetMon-IPv4-Laufzeitprofile reserviert.",
        )

    private_key, private_key_err = app._validate_wireguard_key_value(
        private_key_raw, "Private Key"
    )
    if private_key_err:
        return None, private_key_err
    public_key, public_key_err = app._validate_wireguard_key_value(
        public_key_raw, "Public Key"
    )
    if public_key_err:
        return None, public_key_err
    preshared_key = ""
    if preshared_key_raw.strip():
        preshared_key, preshared_key_err = app._validate_wireguard_key_value(
            preshared_key_raw, "Preshared Key"
        )
        if preshared_key_err:
            return None, preshared_key_err

    endpoint_host, endpoint_port, endpoint_err = app._parse_manual_wireguard_endpoint(
        endpoint
    )
    if endpoint_err:
        return None, endpoint_err

    address_values = [p.strip() for p in address_raw.split(",") if p.strip()]
    if not address_values:
        return None, "Address darf nicht leer sein."
    for token in address_values:
        try:
            ipaddress.ip_network(token, strict=False)
        except ValueError:
            return None, f"Address ungültig: {token}"

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
        "preshared_key": preshared_key,
        "endpoint": normalized_endpoint,
        "address": ", ".join(address_values),
        "allowed_ips": ", ".join(allowed_ips),
        "dns": ", ".join(dns_values),
        "keepalive": keepalive,
    }, ""


def build_manual_wireguard_config_text(_app, payload):
    for key in (
        "private_key",
        "public_key",
        "address",
        "allowed_ips",
        "endpoint",
        "dns",
        "preshared_key",
        "keepalive",
    ):
        manual_wireguard.validate_single_line(payload.get(key, ""))
    lines = [
        "[Interface]",
        f"PrivateKey = {payload['private_key']}",
        f"Address = {payload['address']}",
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
    if payload.get("preshared_key"):
        lines.append(f"PresharedKey = {payload['preshared_key']}")
    if payload.get("keepalive"):
        lines.append(f"PersistentKeepalive = {payload['keepalive']}")

    text = "\n".join(lines) + "\n"
    manual_wireguard.validate_config(text)
    return text


def write_manual_wg_profile(app, profile_name, config_text):
    try:
        manual_wireguard.validate_config(config_text)
        _write_generated_wireguard_profile(app, profile_name, config_text)
        return True, ""
    except Exception:
        return False, "WireGuard-Profil konnte nicht sicher installiert werden."


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
            err,
            level="error",
        )
        widget_name = app._manual_wireguard_error_widget_name(err)
        if widget_name:
            app._focus_manual_wg_field(widget_name)
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
            app._focus_manual_wg_field("manual_wg_slot_combo")
            app.log("Manuelles WireGuard-Profil: Ungültiger VPN-Slot ausgewählt.")
            return

    try:
        config_text = app._build_manual_wireguard_config_text(payload)
    except ValueError:
        app._set_manual_wg_status(
            "Manuelle WireGuard-Konfiguration ist ungueltig.", level="error"
        )
        app.log("Manuelles WireGuard-Profil: unsichere Konfiguration verworfen.")
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

        call_in_ui_thread(app, finish)

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
            try:
                endpoint_ip, endpoint_port = app.parse_vpn_endpoint(candidate)
            except Exception as exc:
                app.log_debug(
                    f"[DEBUG] Endpoint fuer Profil {candidate} konnte nicht gelesen werden: {exc}"
                )
                continue
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
    ufw_lock = app.__dict__.get("ufw_lock")
    if ufw_lock is None:
        ufw_lock = threading.Lock()
        app.ufw_lock = ufw_lock
    with ufw_lock:
        try:
            rc_status, out_status = app._read_ufw_status(verbose=True)
        except Exception as exc:
            app.log_debug(
                f"VPN/UFW-Reconcile: UFW-Status konnte nicht gelesen werden: {exc}"
            )
            return True
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


def wait_for_vpn_ready(app, timeout=15, interval=0.5):
    deadline = time.time() + max(0, timeout)
    last_iface = ""
    last_internet_ok = False

    while time.time() <= deadline:
        wg_iface = str((app.get_wg_iface() or "")).strip()
        internet_ok = False
        if wg_iface:
            try:
                internet_ok = bool(app.check_internet())
            except Exception:
                internet_ok = False

        last_iface = wg_iface
        last_internet_ok = internet_ok

        if wg_iface and internet_ok:
            return True

        time.sleep(max(0.1, interval))

    log_debug_safe = app.__dict__.get("log_debug_safe")
    if callable(log_debug_safe):
        log_debug_safe(
            "VPN-Ready-Timeout: "
            + f"iface={'set' if last_iface else 'missing'}, "
            + f"internet_ok={last_internet_ok}"
        )
    return False


def _parse_nm_name_type_rows(out):
    rows = []
    for raw_line in (out or "").splitlines():
        line = str(raw_line or "").strip()
        if not line:
            continue
        name, sep, conn_type = line.rpartition(":")
        if not sep:
            continue
        name = name.strip()
        conn_type = conn_type.strip().lower()
        if name:
            rows.append((name, conn_type))
    return rows


def get_nm_vpn_profiles(app):
    if not has_cmd("nmcli"):
        return []
    cmd = ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"]
    rc, out = run_cmd(cmd, timeout=10)
    if callable(getattr(app, "_debug_log_system_cmd", None)):
        app._debug_log_system_cmd(cmd, rc, out)
    if rc != 0:
        return []
    return [
        name for name, conn_type in _parse_nm_name_type_rows(out) if conn_type == "vpn"
    ]


def get_nm_connection_rows(app):
    if not has_cmd("nmcli"):
        return []
    cmd = ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"]
    rc, out = run_cmd(cmd, timeout=10)
    if callable(getattr(app, "_debug_log_system_cmd", None)):
        app._debug_log_system_cmd(cmd, rc, out)
    if rc != 0:
        return []
    return _parse_nm_name_type_rows(out)


def get_nm_wireguard_profiles(app):
    return [
        name
        for name, conn_type in get_nm_connection_rows(app)
        if conn_type == "wireguard"
    ]


def get_active_nm_vpn_connections(app):
    if not has_cmd("nmcli"):
        return []
    cmd = ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"]
    rc, out = run_cmd(cmd, timeout=10)
    if callable(getattr(app, "_debug_log_system_cmd", None)):
        app._debug_log_system_cmd(cmd, rc, out)
    if rc != 0:
        return []
    return [
        name for name, conn_type in _parse_nm_name_type_rows(out) if conn_type == "vpn"
    ]


def get_active_nm_wireguard_connections(app):
    if not has_cmd("nmcli"):
        return []
    cmd = ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"]
    rc, out = run_cmd(cmd, timeout=10)
    if callable(getattr(app, "_debug_log_system_cmd", None)):
        app._debug_log_system_cmd(cmd, rc, out)
    if rc != 0:
        return []
    return [
        name
        for name, conn_type in _parse_nm_name_type_rows(out)
        if conn_type == "wireguard"
    ]


_NM_SESSION_INIT_LOCK = threading.Lock()


def _nm_session(app):
    with _NM_SESSION_INIT_LOCK:
        value = app.__dict__.get("_nm_last_import_state")
        if not isinstance(value, ImportSession):
            value = ImportSession(_normalized_nm_last_import_state(value))
            app.__dict__["_nm_last_import_state"] = value
        return value


def get_nm_last_import_state(app):
    # Session references are deliberately separate from persisted settings.
    # Neither loaded user JSON nor a config save can restore/drop this state.
    return _nm_session(app).snapshot()


def set_nm_last_import_state(app, state):
    session = _nm_session(app)
    with session.lock:
        next_state = session.snapshot()
        if isinstance(state, dict):
            next_state.update(state)
        session.replace_when_idle(_normalized_nm_last_import_state(next_state))
        return session.snapshot()


def collect_referenced_wg_profile_import_paths(app):
    paths = []
    seen = set()
    profiles = collect_referenced_vpn_profiles(app, include_active=False)
    for profile in profiles:
        profile_name = app._base_wg_profile_name(profile)
        if not profile_name or profile_name in seen:
            continue
        seen.add(profile_name)
        path = app._wg_profile_path(profile_name)
        paths.append((profile_name, path))
    return paths


def build_nm_wireguard_readiness_report(app):
    referenced_profiles = [
        profile for profile, _path in collect_referenced_wg_profile_import_paths(app)
    ]
    nm_wireguard_profiles = sorted(set(get_nm_wireguard_profiles(app)))

    referenced_set = set(referenced_profiles)
    nm_set = set(nm_wireguard_profiles)

    missing_profiles = sorted(referenced_set - nm_set)
    extra_profiles = sorted(nm_set - referenced_set)
    ready = bool(referenced_profiles) and not missing_profiles

    return {
        "ready": ready,
        "referenced_profiles": referenced_profiles,
        "nm_wireguard_profiles": nm_wireguard_profiles,
        "missing_profiles": missing_profiles,
        "extra_profiles": extra_profiles,
    }


def log_nm_wireguard_readiness_report(app):
    if not has_cmd("nmcli"):
        app.log("Phase-3-Prüfung nicht verfügbar: nmcli fehlt.")
        return {
            "ready": False,
            "referenced_profiles": [],
            "nm_wireguard_profiles": [],
            "missing_profiles": [],
            "extra_profiles": [],
        }

    report = build_nm_wireguard_readiness_report(app)
    referenced_profiles = report["referenced_profiles"]
    nm_wireguard_profiles = report["nm_wireguard_profiles"]
    missing_profiles = report["missing_profiles"]
    extra_profiles = report["extra_profiles"]

    if referenced_profiles:
        app.log("Referenzierte NetMon-Profile: " + ", ".join(referenced_profiles))
    else:
        app.log("Referenzierte NetMon-Profile: keine")

    if nm_wireguard_profiles:
        app.log(
            "NetworkManager-WireGuard-Connections: " + ", ".join(nm_wireguard_profiles)
        )
    else:
        app.log("NetworkManager-WireGuard-Connections: keine")

    if missing_profiles:
        app.log(
            "Phase-3-Prüfung: fehlende NM-Connections: " + ", ".join(missing_profiles)
        )
    else:
        app.log("Phase-3-Prüfung: keine fehlenden NM-Connections.")

    if extra_profiles:
        app.log(
            "Phase-3-Prüfung: zusätzliche NM-WireGuard-Connections: "
            + ", ".join(extra_profiles)
        )

    if report["ready"]:
        app.log(
            "Phase-3-Prüfung: bereit für Umstellung auf NetworkManager-Wechselpfad."
        )
    else:
        app.log(
            "Phase-3-Prüfung: noch nicht bereit für Umstellung auf NetworkManager-Wechselpfad."
        )

    return report


def get_vpn_backend_mode(app):
    return "wg-quick"


def set_vpn_backend_mode(app, mode):
    normalized = "wg-quick"
    config = _privacy_config_dict(app)
    config["vpn_backend_mode"] = normalized
    _save_privacy_config_safe(app)
    return normalized


def enable_networkmanager_vpn_backend(app):
    set_vpn_backend_mode(app, "wg-quick")
    app.log(
        "NetworkManager-Wechselpfad ist zurueckgerollt. NetMon bleibt im stabilen wg-quick-Modus."
    )
    return True


def disable_networkmanager_vpn_backend(app):
    set_vpn_backend_mode(app, "wg-quick")
    app.log("VPN-Backend zurück auf wg-quick gesetzt.")
    return True


def get_active_nm_vpn_interfaces(app):
    nm_active = getattr(app, "nm_active_connections_detailed", None)
    rows = []
    if callable(nm_active):
        try:
            rows = nm_active() or []
        except Exception:
            rows = []
    if not rows and has_cmd("nmcli"):
        cmd = ["nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "con", "show", "--active"]
        rc, out = run_cmd(cmd, timeout=10)
        if callable(getattr(app, "_debug_log_system_cmd", None)):
            app._debug_log_system_cmd(cmd, rc, out)
        if rc == 0:
            for line in (out or "").splitlines():
                parts = line.split(":")
                if len(parts) < 3:
                    continue
                rows.append((parts[0], parts[1], parts[2]))
    interfaces = []
    seen = set()
    for _name, device, conn_type in rows:
        if str(conn_type or "").strip().lower() != "vpn":
            continue
        iface = str(device or "").strip()
        if not iface or iface in seen:
            continue
        seen.add(iface)
        interfaces.append(iface)
    return interfaces


def get_active_nm_wireguard_interfaces(app):
    nm_active = getattr(app, "nm_active_connections_detailed", None)
    rows = []
    if callable(nm_active):
        try:
            rows = nm_active() or []
        except Exception:
            rows = []
    if not rows and has_cmd("nmcli"):
        cmd = ["nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "con", "show", "--active"]
        rc, out = run_cmd(cmd, timeout=10)
        if callable(getattr(app, "_debug_log_system_cmd", None)):
            app._debug_log_system_cmd(cmd, rc, out)
        if rc == 0:
            for line in (out or "").splitlines():
                parts = line.split(":")
                if len(parts) < 3:
                    continue
                rows.append((parts[0], parts[1], parts[2]))
    interfaces = []
    seen = set()
    for _name, device, conn_type in rows:
        if str(conn_type or "").strip().lower() != "wireguard":
            continue
        iface = str(device or "").strip()
        if not iface or iface in seen:
            continue
        seen.add(iface)
        interfaces.append(iface)
    return interfaces


def wg_profile_path(_app, profile_name):
    name = os.path.basename(str(profile_name or "").strip())
    if not name:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        return ""
    wireguard_root = os.path.realpath("/etc/wireguard")
    target = os.path.realpath(os.path.join(wireguard_root, f"{name}.conf"))
    try:
        if os.path.commonpath([wireguard_root, target]) != wireguard_root:
            return ""
    except ValueError:
        return ""
    return target


def wg_profile_exists(app, profile_name):
    path = app._wg_profile_path(profile_name)
    if not path:
        return False

    user_exists = os.path.isfile(path)
    if user_exists:
        app.log_debug(f"os.path.isfile({path}) = True")
        return True
    app.log_debug(f"os.path.isfile({path}) = False")

    rc, out = run_cmd(["sudo", "-n", "test", "-f", path], timeout=5)
    app.log_debug(f"sudo test -f {path} rc={rc}, out={out!r}")
    return rc == 0


def active_wg_profile(app):
    ifaces = app.get_wg_interfaces()
    if ifaces:
        return app._base_wg_profile_name(ifaces[0])
    return None


def get_wg_interfaces(app):
    commands = [
        ["wg", "show", "interfaces"],
        ["sudo", "-n", "wg", "show", "interfaces"],
    ]
    rc = 1
    out = ""
    for cmd in commands:
        rc, out = run_cmd(cmd, timeout=3)
        if callable(getattr(app, "_debug_log_system_cmd", None)):
            app._debug_log_system_cmd(cmd, rc, out)
        if rc == 0:
            break
    if rc != 0:
        return []

    interfaces = []
    seen = set()
    for value in (out or "").split():
        iface = str(value or "").strip()
        if not iface or iface in seen:
            continue
        seen.add(iface)
        interfaces.append(iface)
    return interfaces


def cleanup_wireguard_interfaces(app):
    network_service = app._network_service()
    app.log_safe("WG Cleanup gestartet")

    active_ifaces = app.get_wg_interfaces()
    for iface in active_ifaces:
        app.log_safe(f"WG down: {iface}")
        down_cmd = ["sudo", "-n", "wg-quick", "down", iface]
        if network_service is not None:
            rc_down, out_down = network_service.wg_quick_down(iface, timeout=12)
        else:
            rc_down, out_down = run_cmd(down_cmd, timeout=12)
        _log_command_result(app, "WG", down_cmd, rc_down, out_down)
        if rc_down != 0:
            app.log_safe(f"WG down Fehler ({iface}): rc={rc_down}")
            if out_down:
                app.log_safe((out_down or "").strip())

    remaining_ifaces = app.get_wg_interfaces()
    deleted_ifaces = []
    for iface in remaining_ifaces:
        app.log_safe(f"WG forced delete: {iface}")
        delete_cmd = ["sudo", "-n", "ip", "link", "delete", iface]
        rc_delete, out_delete = run_cmd(delete_cmd, timeout=10)
        _log_command_result(app, "NET", delete_cmd, rc_delete, out_delete)
        if rc_delete != 0:
            app.log_safe(f"WG forced delete Fehler ({iface}): rc={rc_delete}")
            if out_delete:
                app.log_safe((out_delete or "").strip())
        else:
            deleted_ifaces.append(iface)

    final_ifaces = app.get_wg_interfaces()
    if final_ifaces and deleted_ifaces:
        lingering = [
            iface for iface in final_ifaces if iface not in set(deleted_ifaces)
        ]
        if not lingering:
            app.log_safe(
                "WG Cleanup: keine bestaetigte Rest-Schnittstelle mehr, stale Interface-Liste wird ignoriert."
            )
            final_ifaces = []
    if final_ifaces:
        app.log_safe(
            "WG Cleanup fehlgeschlagen: " + ", ".join(final_ifaces) + " weiterhin aktiv"
        )
        return False

    app.log_safe("WG state clean")
    return True


def parse_vpn_endpoint(app, profile_name):
    if not profile_name:
        return None, None

    try:
        rc, out = app._read_wg_profile_text(profile_name)
    except Exception:
        path = app._wg_profile_path(profile_name)
        if not path:
            return None, None
        rc, out = run_cmd(["sudo", "-n", "cat", path], timeout=5)
        if rc != 0:
            rc, out = run_cmd(["cat", path], timeout=5)
    if rc != 0:
        return None, None

    for raw_line in (out or "").splitlines():
        line = raw_line.split("#", 1)[0].split(";", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        if key.lower() != "endpoint" or not value:
            continue

        if value.startswith("[") and "]:" in value:
            host, port = value[1:].split("]:", 1)
        else:
            host, sep, port = value.rpartition(":")
            if not sep:
                continue

        host = host.strip()
        port = port.strip()
        if not host or not port.isdigit():
            continue
        try:
            endpoint_ip = ipaddress.ip_address(host)
        except ValueError:
            _warn_non_ip_endpoint_once(app, profile_name, host)
            continue
        return endpoint_ip.compressed, port

    return None, None


def resolve_profile_family_runtime(app, profile_name, log_missing=True):
    base_profile = app._base_wg_profile_name(profile_name)
    system_ipv6_disabled = app.ipv6_is_disabled()
    ipv4_profile = app._internal_ipv4_profile_name(base_profile) if base_profile else ""
    runtime = {
        "base_profile": base_profile,
        "ipv4_profile": ipv4_profile or base_profile,
        "effective_ipv4_interface": "",
        "effective_ipv6_interface": None,
        "supports_ipv6": (
            app.profile_supports_ipv6(base_profile) if base_profile else False
        ),
        "runtime_profile": "",
        "system_ipv6_disabled": system_ipv6_disabled,
        "endpoint_profiles": [],
    }
    if not base_profile:
        return runtime

    base_exists = app._wg_profile_exists(base_profile)
    ipv4_exists = bool(ipv4_profile and app._wg_profile_exists(ipv4_profile))
    if system_ipv6_disabled and not ipv4_exists:
        ipv4_exists = app.ensure_internal_ipv4_profile(
            base_profile,
            log_failures=log_missing,
        )
    if base_exists:
        runtime["effective_ipv4_interface"] = base_profile
        runtime["runtime_profile"] = base_profile
        runtime["endpoint_profiles"] = [base_profile]
    if ipv4_exists:
        runtime["ipv4_profile"] = ipv4_profile
        if system_ipv6_disabled:
            runtime["effective_ipv4_interface"] = ipv4_profile
            runtime["runtime_profile"] = ipv4_profile
        if ipv4_profile not in runtime["endpoint_profiles"]:
            runtime["endpoint_profiles"].append(ipv4_profile)

    app.log_debug(
        f"[DEBUG] Resolver {base_profile} -> IPv4={runtime['effective_ipv4_interface'] or '-'}, "
        f"IPv6={runtime['effective_ipv6_interface'] or 'None'}, supports_ipv6={runtime['supports_ipv6']}"
    )
    return runtime


def resolve_runtime_vpn_profile(app, profile_name, log_missing=True):
    base_profile = app._base_wg_profile_name(profile_name)
    if not base_profile:
        return ""
    if app.ipv6_is_disabled():
        ipv4_profile = app._internal_ipv4_profile_name(base_profile)
        if app._wg_profile_exists(ipv4_profile):
            return ipv4_profile
        if app.ensure_internal_ipv4_profile(
            base_profile,
            log_failures=log_missing,
        ) and app._wg_profile_exists(ipv4_profile):
            return ipv4_profile
        if log_missing:
            app.log_safe(
                f"VPN Start abgebrochen: Fuer Profil '{base_profile}' ist keine interne IPv4-only Kopie verfuegbar."
            )
            app.log_safe(
                "Bitte IPv6 aktivieren oder ein Profil mit nutzbaren IPv4-Eintraegen verwenden."
            )
        return ""
    if app._wg_profile_exists(base_profile):
        return base_profile
    if log_missing:
        app.log_safe(f"VPN Start abgebrochen: Profil '{base_profile}' nicht gefunden.")
    return ""


def vpn_switch(
    app,
    target,
    ensure_sudo=True,
    refresh_ui=True,
    force_reconnect=False,
    skip_cleanup=False,
):
    if not app._try_begin_network_operation(f"VPN wechseln auf {target}"):
        if refresh_ui:
            app.refresh_safe()
        return False
    try:
        if callable(getattr(app, "debug_nm_state", None)):
            app.debug_nm_state(f"vor VPN Wechsel auf {target}")
        target = str(target or "").strip()
        app.log_debug(f"Basisprofil = {target!r}")
        if not target:
            app.log_safe(
                app.tr("vpn_log_no_profile_selected", "Kein WireGuard-Profil gewählt.")
            )
            app._recover_firewall_preserving_killswitch()
            if refresh_ui:
                app.refresh_safe()
            return False

        if ensure_sudo and not app.ensure_sudo_session(f"VPN umschalten auf {target}"):
            return False

        resolved = app.resolve_profile_family_runtime(target, log_missing=True)
        runtime_target = (resolved.get("runtime_profile") or "").strip()
        app.log_debug(f"Runtimeprofil = {runtime_target!r}")
        app.log_debug(f"IPv6 deaktiviert = {resolved.get('system_ipv6_disabled')}")
        app.log_debug(
            f"[DEBUG] Resolver {target} -> IPv4={resolved.get('effective_ipv4_interface') or '-'}, "
            f"IPv6={resolved.get('effective_ipv6_interface') or 'None'}, supports_ipv6={resolved.get('supports_ipv6')}"
        )

        if not runtime_target:
            runtime_target = app.resolve_runtime_vpn_profile(target, log_missing=True)
        if not runtime_target:
            app._recover_firewall_preserving_killswitch()
            if refresh_ui:
                app.refresh_safe()
            return False

        active_ifaces = app.get_wg_interfaces()
        reconnecting_same_profile = runtime_target in active_ifaces
        if reconnecting_same_profile:
            if not force_reconnect and len(active_ifaces) == 1:
                app.log_safe(
                    app.tr(
                        "vpn_log_profile_already_active",
                        "VPN-Profil bereits aktiv.",
                    )
                )
                if refresh_ui:
                    app.refresh_safe()
                return True
            app.log_safe(
                app.tr(
                    "vpn_log_force_reconnect",
                    "Vorhandenes Runtimeprofil erkannt - Reconnect wird erzwungen.",
                )
            )
        elif len(active_ifaces) > 1:
            app.log_safe(
                "Mehrere aktive WG-Interfaces erkannt. Cleanup vor neuem Start wird erzwungen."
            )

        if len(runtime_target) > 15:
            app.log_safe(
                f"VPN Start abgebrochen: Runtime-Profilname '{runtime_target}' ist zu lang fuer ein WireGuard-Interface (max 15 Zeichen)."
            )
            app.log_safe(
                "Bitte interne IPv4-Runtime-Profile pruefen oder die Profilaufbereitung aktualisieren."
            )
            if refresh_ui:
                app.refresh_safe()
            return False

        network_service = app._network_service()
        runtime_path = app._wg_profile_path(runtime_target)
        app._check_wireguard_profile_for_multiple_endpoints(
            runtime_target, runtime_path
        )
        if network_service is not None:
            rc_check, out_check = network_service.file_exists(runtime_path)
        else:
            rc_check, out_check = run_cmd(
                ["sudo", "-n", "test", "-f", runtime_path], timeout=5
            )
        app.log_debug_safe(f"Runtimepfad = {runtime_path}")
        app.log_debug_safe(f"sudo test -f Runtimepfad rc = {rc_check}")
        if rc_check != 0:
            _vpn_user_log(
                app,
                app.tr(
                    "vpn_log_runtime_file_missing",
                    "VPN Start abgebrochen: Runtime-Datei nicht gefunden: {path}",
                ).format(path=runtime_path),
            )
            if out_check:
                _vpn_user_log(app, out_check)
            if refresh_ui:
                app.refresh_safe()
            return False

        app.prepare_dns_for_vpn_profile_switch()
        if skip_cleanup:
            app.log_network_debug(
                "[DEBUG] WG Cleanup vor VPN Start übersprungen: bereits sauber."
            )
        elif not cleanup_wireguard_interfaces(app):
            app._recover_firewall_preserving_killswitch()
            if refresh_ui:
                app.refresh_safe()
            return False

        up_cmd = ["sudo", "-n", "wg-quick", "up", runtime_target]
        if network_service is not None:
            rc, out = network_service.wg_quick_up(runtime_target, timeout=20)
        else:
            rc, out = run_cmd(up_cmd, timeout=20)
        _log_command_result(app, "WG", up_cmd, rc, out)
        if rc == 0:
            if force_reconnect:
                _vpn_user_log(
                    app,
                    app.tr(
                        "vpn_log_reconnected",
                        "VPN Verbindung neu aufgebaut.",
                    ),
                )
            else:
                _vpn_user_log(
                    app, app.tr("vpn_log_connected", "VPN Verbindung aufgebaut.")
                )
            _vpn_user_log(
                app,
                app.tr("vpn_log_started", "VPN gestartet: {target}").format(
                    target=target
                ),
            )
            app.log_debug_safe(out)
        else:
            _vpn_user_log(
                app,
                app.tr(
                    "vpn_log_start_failed_rc", "VPN Start fehlgeschlagen: rc={rc}"
                ).format(rc=rc),
            )
            if out:
                _vpn_user_log(app, (out or "").strip())
            app.log_debug_safe(out)

        app.last_wg_transfer = None
        app.last_wg_ts = None
        app.refresh_wg_profiles()
        app.update_primary_vpn_form_controls()
        app.sync_primary_vpn_form_selection()
        if rc == 0:
            if app.killswitch_is_on():
                app._killswitch_on_sync(refresh_ui=False)
            else:
                app.reconcile_vpn_slot_firewall_state(
                    reason=f"VPN aktiv: {target}",
                    touched_profiles=[target],
                    refresh_ui=False,
                )
        if rc == 0:
            app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=2500)
            app.run_async(lambda t=target: app.verify_vpn_exit_country(t))
        else:
            app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=750)
        if callable(getattr(app, "debug_nm_state", None)):
            app.debug_nm_state(f"nach VPN Wechsel auf {target}")

        app.update_ipv6_controls_state_safe()
        if refresh_ui:
            app.refresh_safe()
        return rc == 0
    finally:
        app._end_network_operation()


def vpn_off(app, ensure_sudo=True, refresh_ui=True):
    if not app._try_begin_network_operation("VPN deaktivieren"):
        if refresh_ui:
            app.refresh_safe()
        return False
    try:
        if callable(getattr(app, "debug_nm_state", None)):
            app.debug_nm_state("vor VPN AUS")
        if ensure_sudo and not app.ensure_sudo_session("VPN deaktivieren"):
            return False
        cleanup_ok = cleanup_wireguard_interfaces(app)
        if not cleanup_ok:
            if refresh_ui:
                app.refresh_safe()
            return False
        _vpn_user_log(app, app.tr("vpn_log_disabled", "VPN deaktiviert."))
        app.prepare_dns_for_vpn_profile_switch()
        app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=2500)
        if app.killswitch_is_on():
            _show_killswitch_active_after_vpn_off_notice(app)
            _vpn_user_log(
                app,
                app.tr(
                    "killswitch_log_notice_enabled_without_vpn",
                    "HINWEIS: Killswitch ist AN – ohne VPN evtl. kein Internet (gewollt).",
                ),
            )
        app.refresh_wg_profiles()
        if callable(getattr(app, "debug_nm_state", None)):
            app.debug_nm_state("nach VPN AUS")
        app.update_ipv6_controls_state_safe()
        if refresh_ui:
            app.refresh_safe()
        return True
    finally:
        app._end_network_operation()


def _vpn_switch_networkmanager(app, target, *, refresh_ui=True, force_reconnect=False):
    target = app._base_wg_profile_name(target)
    report = build_nm_wireguard_readiness_report(app)
    if not report.get("ready"):
        _vpn_user_log(
            app,
            "NetworkManager-Wechselpfad blockiert: Phase-3-Prüfung ist noch nicht grün.",
        )
        if refresh_ui:
            app.refresh_safe()
        return False
    if target not in set(get_nm_wireguard_profiles(app)):
        _vpn_user_log(
            app,
            f"VPN Start abgebrochen: NetworkManager-Connection '{target}' nicht gefunden.",
        )
        if refresh_ui:
            app.refresh_safe()
        return False

    active_connections = get_active_nm_wireguard_connections(app)
    reconnecting_same_profile = target in active_connections
    if reconnecting_same_profile and not force_reconnect:
        _vpn_user_log(
            app,
            app.tr(
                "vpn_log_profile_already_active",
                "VPN-Profil bereits aktiv.",
            ),
        )
        if refresh_ui:
            app.refresh_safe()
        return True
    if reconnecting_same_profile and force_reconnect:
        _vpn_user_log(
            app,
            app.tr(
                "vpn_log_force_reconnect",
                "Vorhandenes Runtimeprofil erkannt - Reconnect wird erzwungen.",
            ),
        )

    app.prepare_dns_for_vpn_profile_switch()
    app.log_network_debug("[VPN][NM] path: sudo nmcli connection down/up")

    for name in active_connections:
        if name != target or reconnecting_same_profile:
            down_cmd = ["sudo", "-n", "nmcli", "connection", "down", name]
            rc_down, out_down = run_cmd(down_cmd, timeout=20)
            _log_command_result(app, "NM", down_cmd, rc_down, out_down)

    up_cmd = ["sudo", "-n", "nmcli", "connection", "up", target]
    rc, out = run_cmd(up_cmd, timeout=40)
    _log_command_result(app, "NM", up_cmd, rc, out)
    if rc == 0:
        if force_reconnect:
            _vpn_user_log(
                app, app.tr("vpn_log_reconnected", "VPN Verbindung neu aufgebaut.")
            )
        else:
            _vpn_user_log(app, app.tr("vpn_log_connected", "VPN Verbindung aufgebaut."))
        _vpn_user_log(
            app,
            app.tr("vpn_log_started", "VPN gestartet: {target}").format(target=target),
        )
        app.log_debug_safe(out)
    else:
        _vpn_user_log(
            app,
            app.tr(
                "vpn_log_start_failed_rc", "VPN Start fehlgeschlagen: rc={rc}"
            ).format(rc=rc),
        )
        if out:
            _vpn_user_log(app, (out or "").strip())
        app.log_debug_safe(out)

    app.last_wg_transfer = None
    app.last_wg_ts = None
    app.refresh_wg_profiles()
    app.update_primary_vpn_form_controls()
    app.sync_primary_vpn_form_selection()
    if rc == 0 and app.killswitch_is_on():
        app._killswitch_on_sync(refresh_ui=False)
    if rc == 0:
        app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=2500)
        app.run_async(lambda t=target: app.verify_vpn_exit_country(t))
    else:
        app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=750)
    if callable(getattr(app, "debug_nm_state", None)):
        app.debug_nm_state(f"nach VPN Wechsel auf {target}")

    app.update_ipv6_controls_state_safe()
    if refresh_ui:
        app.refresh_safe()
    return rc == 0


def _vpn_off_networkmanager(app, *, refresh_ui=True):
    targets = get_active_nm_wireguard_connections(app)
    app.log_network_debug("[VPN][NM] path: sudo nmcli connection down")
    for target in targets:
        down_cmd = ["sudo", "-n", "nmcli", "connection", "down", target]
        rc_down, out_down = run_cmd(down_cmd, timeout=20)
        _log_command_result(app, "NM", down_cmd, rc_down, out_down)
    _vpn_user_log(app, app.tr("vpn_log_disabled", "VPN deaktiviert."))
    app.prepare_dns_for_vpn_profile_switch()
    app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=2500)
    if app.killswitch_is_on():
        _show_killswitch_active_after_vpn_off_notice(app)
        _vpn_user_log(
            app,
            app.tr(
                "killswitch_log_notice_enabled_without_vpn",
                "HINWEIS: Killswitch ist AN – ohne VPN evtl. kein Internet (gewollt).",
            ),
        )
    app.refresh_wg_profiles()
    if callable(getattr(app, "debug_nm_state", None)):
        app.debug_nm_state("nach VPN AUS")
    app.update_ipv6_controls_state_safe()
    if refresh_ui:
        app.refresh_safe()
    return True


def list_wg_profile_files(app, include_internal=False):
    profiles = set()
    cmd = [
        "find",
        "/etc/wireguard",
        "-maxdepth",
        "1",
        "-type",
        "f",
        "-name",
        "*.conf",
        "-printf",
        "%f\n",
    ]
    rc, out = run_cmd(["sudo", "-n", *cmd], timeout=5)
    if rc != 0:
        rc, out = run_cmd(cmd, timeout=5)
    if rc != 0:
        return []
    for line in (out or "").splitlines():
        name = line.strip()
        if name.endswith(".conf"):
            name = name[:-5]
        if not name:
            continue
        if app._is_internal_ipv4_profile(name):
            if include_internal:
                profiles.add(name)
            continue
        profiles.add(name)
    return sorted(profiles)


def list_netmon_wg_profile_files(app, include_internal=False):
    profiles = set()
    wg_dir = ensure_netmon_wireguard_profiles_dir()
    if not os.path.isdir(wg_dir):
        return []
    try:
        entries = sorted(os.listdir(wg_dir))
    except OSError:
        return []
    for entry in entries:
        name = str(entry or "").strip()
        if not name.endswith(".conf"):
            continue
        name = name[:-5]
        if not name:
            continue
        if app._is_internal_ipv4_profile(name):
            if include_internal:
                profiles.add(name)
            continue
        profiles.add(name)
    return sorted(profiles)


def read_wg_profile_text(app, profile_name):
    path = app._wg_profile_path(profile_name)
    if not path:
        return 1, ""
    rc, out = run_cmd(["sudo", "-n", "cat", path], timeout=5)
    if rc != 0:
        rc, out = run_cmd(["cat", path], timeout=5)
    return rc, out


def sync_internal_ipv4_profiles(app, log_failures=True):
    # Laufzeitkopien werden bei Bedarf erzeugt; ein separater Global-Sync ist
    # aktuell nicht erforderlich.
    app.log_debug(
        "[VPN][PROFILE] Interne IPv4-Runtimeprofile werden on-demand gepflegt."
    )


def list_wg_profiles(app):
    profiles = set()

    for profile in list_wg_profile_files(app):
        name = str(profile or "").strip()
        if name:
            profiles.add(name)

    for profile in list_netmon_wg_profile_files(app):
        name = str(profile or "").strip()
        if name:
            profiles.add(name)

    for profile in get_nm_wireguard_profiles(app):
        name = str(profile or "").strip()
        if name:
            profiles.add(name)

    return sorted(profiles)


def refresh_wg_profiles(app):
    profiles = app.list_wg_profiles()
    app.wg_profiles = profiles
    if app.__dict__.get("isp_stealth_vpn_combo") is not None:
        app.update_privacy_vpn_combo()
    try:
        app.log_network_debug(f"[VPN][PROFILE] available: {profiles}")
    except Exception:
        pass


def reload_wg_profiles(app):
    app.refresh_wg_profiles()
    if hasattr(app, "vpn_profile_combo"):
        app.vpn_profile_combo["values"] = app.wg_profiles
    app.sync_primary_vpn_form_selection()
    app.sync_vpn_profile_form_selection()
    app.update_vpn_slot_buttons()
    app.update_primary_vpn_form_controls()
    app.refresh_vpn_slots_table()
    if hasattr(app, "isp_stealth_vpn_combo"):
        app.update_privacy_vpn_combo()

    app.update_ipv6_controls_state()
    if app.wg_profiles:
        app.log(f"WireGuard-Profile: {', '.join(app.wg_profiles)}")
    else:
        app.log("WireGuard-Profile: keine gefunden")


def profile_supports_ipv6(app, profile_name):
    if not profile_name:
        return False

    rc, out = app._read_wg_profile_text(profile_name)
    if rc != 0:
        return False

    def has_ipv6_token(token):
        value = (token or "").strip()
        if not value:
            return False
        if value.startswith("[") and value.endswith("]"):
            value = value[1:-1].strip()
        try:
            if "/" in value:
                return ipaddress.ip_network(value, strict=False).version == 6
            return ipaddress.ip_address(value).version == 6
        except ValueError:
            return False

    for raw_line in (out or "").splitlines():
        line = raw_line.split("#", 1)[0].split(";", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        key_l = key.lower()
        if not value:
            continue

        if key_l in {"address", "dns", "allowedips"}:
            tokens = [part.strip() for part in value.split(",") if part.strip()]
            if any(has_ipv6_token(token) for token in tokens):
                return True
            continue

        if key_l == "endpoint":
            host = value
            if value.startswith("[") and "]:" in value:
                host = value[1:].split("]:", 1)[0].strip()
            else:
                host, sep, port = value.rpartition(":")
                if sep and port.strip().isdigit():
                    host = host.strip()
            if has_ipv6_token(host):
                return True

    return False


def extract_ipv4_tokens(_app, value):
    tokens = []
    for raw_token in (value or "").split(","):
        token = raw_token.strip()
        if not token:
            continue
        candidate = token
        if candidate.startswith("[") and candidate.endswith("]"):
            candidate = candidate[1:-1].strip()
        try:
            if "/" in candidate:
                if ipaddress.ip_network(candidate, strict=False).version == 4:
                    tokens.append(token)
            elif ipaddress.ip_address(candidate).version == 4:
                tokens.append(token)
        except ValueError:
            continue
    return tokens


def endpoint_uses_ipv6_literal(_app, value):
    endpoint = (value or "").strip()
    if not endpoint:
        return False
    if endpoint.startswith("[") and "]:" in endpoint:
        return True
    host, sep, port = endpoint.rpartition(":")
    if not sep or not port.strip().isdigit():
        return False
    host = host.strip()
    try:
        return ipaddress.ip_address(host).version == 6
    except ValueError:
        return False


def build_ipv4_only_wg_profile_content(app, profile_name):
    rc, out = app._read_wg_profile_text(profile_name)
    if rc != 0:
        return "", "WireGuard-Profil konnte nicht gelesen werden."

    filtered_lines = []
    relevant_keys = {"address", "dns", "allowedips"}

    for raw_line in (out or "").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            filtered_lines.append("")
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            filtered_lines.append(stripped)
            continue
        if "=" not in raw_line:
            filtered_lines.append(raw_line.rstrip())
            continue

        key, value = [part.strip() for part in raw_line.split("=", 1)]
        key_l = key.lower()

        if key_l in relevant_keys:
            ipv4_tokens = app._extract_ipv4_tokens(value)
            if not ipv4_tokens:
                continue
            filtered_lines.append(f"{key} = {', '.join(ipv4_tokens)}")
            continue

        if key_l == "endpoint" and app._endpoint_uses_ipv6_literal(value):
            return (
                "",
                "Endpoint nutzt eine IPv6-Adresse und kann nicht als IPv4-only Kopie übernommen werden.",
            )

        filtered_lines.append(raw_line.rstrip())

    content = "\n".join(filtered_lines).rstrip() + "\n"
    return content, ""


def ensure_internal_ipv4_profile(app, profile_name, log_failures=True):
    base_profile = app._base_wg_profile_name(profile_name)
    if not base_profile:
        return False

    ipv4_profile = app._internal_ipv4_profile_name(base_profile)
    if app._wg_profile_exists(ipv4_profile):
        return True

    content, reason = app.build_ipv4_only_wg_profile_content(base_profile)
    if not content:
        if log_failures and reason:
            app.log_safe(reason)
        return False
    content = (
        "\n".join(
            [
                INTERNAL_IPV4_PROFILE_KIND_MARKER,
                f"{INTERNAL_IPV4_PROFILE_BASE_MARKER}{base_profile}",
                "",
                content.rstrip(),
            ]
        ).rstrip()
        + "\n"
    )

    try:
        _write_generated_wireguard_profile(app, ipv4_profile, content)
        return True
    except Exception:
        if log_failures:
            app.log_safe("Interne IPv4-Kopie konnte nicht sicher installiert werden.")
        return False


def import_wg_profiles_from_folder(app):
    initialdir = app.get_wg_import_dir() or ensure_netmon_wireguard_profiles_dir()
    files = filedialog.askopenfilenames(
        title=app.tr("wg_profiles_dialog_select", "WireGuard-Profile auswählen"),
        initialdir=initialdir,
        filetypes=[("WireGuard config", "*.conf"), ("Alle Dateien", "*.*")],
    )
    if not files:
        app.log("Import abgebrochen.")
        return

    first_dir = os.path.dirname(str(files[0]).strip()) if files else ""
    if first_dir:
        app.set_wg_import_dir(first_dir)

    try:
        # Filter invalid names before reading; no path-based privileged fallback.
        valid = []
        for path in files:
            try:
                wireguard_import.profile_name(path)
                valid.append(path)
            except ValueError:
                app.log(
                    f"Übersprungen (ungültiger Profilname): {_single_line(os.path.basename(path).removesuffix('.conf'))}"
                )
        snapshots = _prepare_wireguard_imports(app, valid) if valid else ()
        if snapshots is None:
            app.log("WireGuard-Import abgebrochen.")
            return
    except Exception:
        app.log("WireGuard-Import abgebrochen: Quelldatei oder Bestaetigung ungueltig.")
        return

    def job():
        selected_files = sorted(snapshots, key=lambda snapshot: snapshot.source)

        imported = 0
        skipped = len(files) - len(selected_files)
        failed = 0
        imported_profiles = []

        for snapshot in selected_files:
            name = snapshot.name
            try:
                _install_wireguard_snapshot(app, snapshot)
                rc_cp, out_cp = 0, ""
            except Exception:
                rc_cp, out_cp = 1, "Gepruefter WireGuard-Import fehlgeschlagen."
            if rc_cp == 0:
                imported += 1
                imported_profiles.append(name)
                call_in_ui_thread(
                    app, lambda n=name: app.log(f"Profil importiert: {n}")
                )
            else:
                failed += 1
                app.after(
                    0,
                    lambda n=name, o=out_cp: app.log(
                        f"Import fehlgeschlagen ({n}): {o}"
                    ),
                )

        def finish():
            if imported_profiles:
                app.reconcile_vpn_slot_firewall_state(
                    reason="Import-Reconcile",
                    touched_profiles=imported_profiles,
                    refresh_ui=False,
                )
            app.sync_internal_ipv4_profiles(log_failures=False)
            app.refresh_wg_profiles()
            if hasattr(app, "vpn_profile_combo"):
                app.vpn_profile_combo["values"] = app.wg_profiles
            app.update_primary_vpn_form_controls()
            app.sync_primary_vpn_form_selection()
            app.sync_vpn_profile_form_selection()
            app.update_vpn_slot_buttons()
            app.refresh_vpn_slots_table()
            app.log(
                f"WireGuard-Import beendet: {imported} importiert, {skipped} übersprungen, {failed} fehlgeschlagen."
            )

        call_in_ui_thread(app, finish)

    threading.Thread(target=job, daemon=True).start()


def import_wg_profiles_to_networkmanager(app):
    if not has_cmd("nmcli"):
        app.log("NetworkManager-Import nicht verfügbar: nmcli fehlt.")
        return

    initialdir = app.get_wg_import_dir() or ensure_netmon_wireguard_profiles_dir()
    if not os.path.isdir(initialdir):
        initialdir = ensure_netmon_wireguard_profiles_dir()

    files = filedialog.askopenfilenames(
        title=app.tr(
            "wg_profiles_dialog_import_nm",
            "WireGuard-Profile nach NetworkManager importieren",
        ),
        initialdir=initialdir,
        filetypes=[("WireGuard config", "*.conf"), ("Alle Dateien", "*.*")],
    )
    if not files:
        app.log("NetworkManager-Import abgebrochen.")
        return

    first_dir = os.path.dirname(str(files[0]).strip()) if files else ""
    if first_dir:
        app.set_wg_import_dir(first_dir)

    if not app.ensure_sudo_session("WireGuard nach NetworkManager importieren"):
        return

    _start_nm_import_job(
        app,
        sorted(str(path).strip() for path in files if str(path).strip()),
        "NetworkManager-WireGuard-Import",
    )


def import_referenced_wg_profiles_to_networkmanager(app):
    if not has_cmd("nmcli"):
        app.log("NetworkManager-Import nicht verfügbar: nmcli fehlt.")
        return
    if not app.ensure_sudo_session(
        "Referenzierte WireGuard-Profile nach NetworkManager importieren"
    ):
        return

    collector = app.__dict__.get("collect_referenced_wg_profile_import_paths")
    if callable(collector):
        referenced_paths = collector()
    else:
        referenced_paths = collect_referenced_wg_profile_import_paths(app)
    if not referenced_paths:
        app.log("Kein referenziertes WireGuard-Profil zum NM-Import gefunden.")
        return
    _start_nm_import_job(
        app,
        [path for _profile, path in referenced_paths],
        "NetworkManager-WireGuard-Import (referenzierte Profile)",
    )


def _owned_nm_command(operation, *, payload=None, identity=None):
    """Invoke only the fixed, protected installed helper; user state is a hint."""
    if not nm_ownership.trusted_helper_available():
        raise nm_ownership.OwnershipError("Geschützter NetMon-Eigentumshelfer fehlt")
    command = [
        "sudo",
        "-n",
        "/usr/bin/python3",
        "-I",
        nm_ownership.HELPER,
        "import-checked" if operation == "import" else operation,
    ]
    if identity is not None:
        command.extend(identity)
    rc, output = run_cmd_with_input(
        command,
        input_text=json.dumps(payload) if payload is not None else "",
        timeout=180,
    )
    if rc != 0:
        raise nm_ownership.OwnershipError(
            "Eigentumsprüfung fehlgeschlagen; Verbindung bleibt erhalten"
        )
    return (
        json.loads(output)
        if operation in {"import", "inspect", "snapshot-profile"}
        else None
    )


def _nm_import_source(path):
    return wireguard_import.ProfileSnapshot.read(path).data.decode("utf-8")


def _nm_job_error(session, job, message):
    try:
        session.error(job, message)
    except Exception:
        pass
    try:
        logging.getLogger(__name__).warning("NM-Job %s: %s", job.token, message)
    except Exception:
        pass


def _nm_finish_job(session, job, phase):
    try:
        session.finish(job, phase)
    except Exception:
        # The journal, including raw RPC results, remains authoritative even
        # when a secondary state transition fails. Never undo a newer job.
        with session.lock:
            job.phase = "state_error"
            for entry in session.entries.values():
                if entry.deleting_job == job.token and not entry.deleted:
                    entry.deleting_job = None
                    entry.phase = "recovery"
            session.active.discard(job.token)
            session.revision += 1
            job.revision = session.revision
        _nm_job_error(
            session,
            job,
            "Sitzungsabschluss fehlgeschlagen; Ergebnisse bleiben gesichert.",
        )


def _nm_notify(app, session, job, message):
    try:
        event = session.notification(job)
    except Exception:
        _nm_job_error(
            session,
            job,
            "GUI-Ereignis konnte nicht angelegt werden; Ergebnisse bleiben gesichert.",
        )
        return

    def deliver():
        try:
            if not session.consume_notification(event):
                return
            alive = app.__dict__.get("winfo_exists")
            if alive is None and app.__dict__.get("tk") is not None:
                alive = app.winfo_exists
            if callable(alive) and not alive():
                raise RuntimeError("GUI closed")
            app.log(message)
        except Exception:
            _nm_job_error(
                session,
                job,
                "GUI-Benachrichtigung fehlgeschlagen; Ergebnisse bleiben gesichert.",
            )

    try:
        app.after(0, deliver)
    except Exception:
        # A scheduler can raise after enqueueing. Invalidate that callback too.
        with session.lock:
            event["consumed"] = True
        _nm_job_error(
            session,
            job,
            "GUI-Callback konnte nicht geplant werden; Ergebnisse bleiben gesichert.",
        )


def _start_nm_import_job(app, paths, operation_name):
    try:
        snapshots = _prepare_wireguard_imports(app, paths)
        if snapshots is None:
            return
    except Exception:
        app.log(
            "NetworkManager-Import abgebrochen: Quelldatei oder Bestaetigung ungueltig."
        )
        return
    session = _nm_session(app)
    job = session.new_job("import")
    try:
        threading.Thread(
            target=lambda: import_wireguard_paths_to_networkmanager(
                app,
                paths,
                operation_name=operation_name,
                _job=job,
                _snapshots=snapshots,
            ),
            daemon=True,
        ).start()
    except Exception:
        _nm_worker_start_error(session, job)


def _nm_worker_start_error(session, job):
    with session.lock:
        if job.phase == "queued":
            _nm_finish_job(session, job, "failed")
    _nm_job_error(
        session,
        job,
        "Worker-Startmeldung fehlgeschlagen; gesicherte Jobergebnisse beachten.",
    )


def import_wireguard_paths_to_networkmanager(
    app,
    selected_files,
    *,
    operation_name="NetworkManager-WireGuard-Import",
    _job=None,
    _snapshots=None,
):
    session = _nm_session(app)
    job = _job if _job is not None else session.new_job("import")
    if not session.start(job, "import"):
        return
    imported = skipped = failed = state_errors = 0
    protected = False
    try:
        protected = nm_ownership.trusted_helper_available()
        if not protected:
            raise nm_ownership.OwnershipError(
                "Geschuetzter Importhelfer fehlt; kein unsicherer Fallback"
            )
        snapshots = (
            _snapshots
            if _snapshots is not None
            else _prepare_wireguard_imports(app, selected_files)
        )
        if snapshots is None:
            _nm_finish_job(session, job, "canceled")
            return
        for snapshot in snapshots:
            name = snapshot.name
            if name in set(get_nm_wireguard_profiles(app)):
                skipped += 1
                continue
            entry = session.reserve(job, snapshot.source)
            try:
                candidate = _owned_nm_command(
                    "import", payload=_verify_import_snapshot(snapshot)
                )
                # FIRST retain the successful privileged result. L-01/F-01
                # receipts, job association and rollback state stay authoritative.
                with session.lock:
                    entry.result = candidate
                    session.include_owned = True
                    session.revision += 1
            except Exception:
                session.failed_import(entry)
                failed += 1
                _nm_job_error(
                    session,
                    job,
                    "Import fehlgeschlagen; bereits angelegte Verbindungen separat prüfen/bereinigen.",
                )
                break
            imported += 1
            try:
                session.finish_import(entry)
            except Exception:
                state_errors += 1
                with session.lock:
                    entry.phase = "recovery"
                _nm_job_error(
                    session,
                    job,
                    "Sitzungsaktualisierung fehlgeschlagen; Importreferenz gesichert, Bereinigung separat bestätigen.",
                )
    except Exception:
        failed += 1
        _nm_job_error(
            session,
            job,
            "Import-Job abgebrochen; gesicherte Ergebnisse bleiben erhalten, Bereinigung separat bestätigen.",
        )
    phase = (
        "state_error"
        if state_errors
        else ("partial" if failed and imported else "failed" if failed else "completed")
    )
    _nm_finish_job(session, job, phase)
    if job.errors:
        message = f"{operation_name} (Job {job.token}): {imported} erstellt, {failed} fehlgeschlagen; Fehler siehe Diagnose, Ergebnisse gesichert. Bereinigung separat bestätigen."
    else:
        message = f"{operation_name} (Job {job.token}) beendet: {imported} importiert, {skipped} übersprungen, {failed} fehlgeschlagen."
    if imported and not protected:
        message += " Ohne geschützten Eigentumsnachweis; nur manuell bereinigen."
    _nm_notify(app, session, job, message)


def rollback_last_nm_wireguard_import(app):
    session = _nm_session(app)
    references = session.references()
    job = session.new_job("rollback")
    if not references or not nm_ownership.trusted_helper_available():
        _nm_finish_job(session, job, "canceled")
        _nm_notify(
            app,
            session,
            job,
            "Kein geschützter Erstellungsnachweis: Altbestände und fremde Verbindungen bleiben erhalten.",
        )
        return
    try:
        if not app.ensure_sudo_session("NetworkManager-WireGuard-Import zurückrollen"):
            _nm_finish_job(session, job, "canceled")
            return
        candidates = []
        for token, reference in references:
            try:
                candidate = _owned_nm_command(
                    "inspect", identity=[reference["uuid"], reference["receipt_id"]]
                )
                candidates.append((token, candidate))
            except Exception:
                _nm_job_error(
                    session,
                    job,
                    "Fehlender oder veränderter Nachweis; Verbindung bleibt erhalten.",
                )
        if not candidates:
            _nm_finish_job(session, job, "failed")
            _nm_notify(
                app,
                session,
                job,
                "NM-Bereinigung: fehlender oder veränderter Nachweis; Verbindung bleibt erhalten.",
            )
            return
        preview = "\n".join(
            json.dumps({"name": item["name"], "uuid": item["uuid"]}, ensure_ascii=True)
            for _token, item in candidates
        )
        if not messagebox.askyesno(
            "NetworkManager-Import zurückrollen",
            "Nur diese geprüften Verbindungen löschen?\n\n" + preview,
        ):
            _nm_finish_job(session, job, "canceled")
            _nm_notify(app, session, job, "NM-Bereinigung abgebrochen.")
            return
    except Exception:
        _nm_finish_job(session, job, "failed")
        _nm_job_error(
            session,
            job,
            "Rollback-Vorschau/Bestätigung fehlgeschlagen; keine Löschung.",
        )
        return

    def worker():
        if not session.start(job, "rollback"):
            return
        removed = failed = state_errors = 0
        try:
            for token, item in candidates:
                entry = session.claim_delete(token, item, job)
                if entry is None:
                    continue
                try:
                    # L-01 revalidates this exact immutable confirmation plan.
                    _owned_nm_command("delete", payload=item)
                    with session.lock:
                        entry.deleted = True
                        session.revision += 1
                    removed += 1
                except Exception:
                    failed += 1
                    _nm_job_error(
                        session,
                        job,
                        "UUID-Löschung/Prüfung fehlgeschlagen; Referenz bleibt zur erneuten Prüfung erhalten.",
                    )
                try:
                    session.finish_delete(entry, job)
                except Exception:
                    state_errors += 1
                    with session.lock:
                        if entry.deleting_job == job.token:
                            entry.deleting_job = None
                            entry.phase = "recovery"
                    _nm_job_error(
                        session,
                        job,
                        "Rollback-Sitzungsaktualisierung fehlgeschlagen; tatsächliches Ergebnis ist gesichert.",
                    )
        except Exception:
            failed += 1
            _nm_job_error(
                session,
                job,
                "Rollback-Job fehlgeschlagen; unverarbeitete Referenzen bleiben erhalten.",
            )
        _nm_finish_job(
            session,
            job,
            "state_error" if state_errors else "partial" if failed else "completed",
        )
        _nm_notify(
            app,
            session,
            job,
            f"NM-Bereinigung (Job {job.token}): {removed} entfernt, {failed} fehlgeschlagen."
            + (" Sitzungs-/Diagnosefehler beachten." if job.errors else ""),
        )

    try:
        threading.Thread(target=worker, daemon=True).start()
    except Exception:
        _nm_worker_start_error(session, job)
