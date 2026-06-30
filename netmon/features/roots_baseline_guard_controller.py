"""Manual baseline helpers for the Roots Baseline Guard tab."""

from __future__ import annotations

import json
import os
import re
import fnmatch
from glob import glob
from datetime import datetime

try:
    from netmon.core.utils import safe_write_json
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.utils import safe_write_json
    from core.command import run_cmd


ROOTS_GUARD_SUPPORTED_AREAS = (
    "SSH Konfiguration",
    "SSH Schlüssel / authorized_keys",
    "DNS / Hosts",
    "Kritische Systemdateien",
    "Autostart / systemd / cron",
)

ROOTS_GUARD_PLACEHOLDER_TEXT = "Noch keine Änderungen erkannt."

ROOTS_GUARD_DEFAULT_AREA_PATHS = {
    "SSH Konfiguration": [
        "/etc/ssh/sshd_config",
        "/etc/ssh/ssh_config",
        "/etc/ssh/sshd_config.d",
    ],
    "SSH Schlüssel / authorized_keys": [
        "/root/.ssh/authorized_keys",
        "/home/*/.ssh/authorized_keys",
    ],
    "DNS / Hosts": ["/etc/hosts", "/etc/resolv.conf"],
    "Kritische Systemdateien": [
        "/etc/passwd",
        "/etc/group",
        "/etc/shadow",
        "/etc/sudoers",
        "/etc/sudoers.d",
        "/etc/pam.d",
        "/etc/polkit-1",
        "/etc/sysctl.conf",
        "/etc/sysctl.d",
        "/etc/modprobe.d",
        "/etc/modules-load.d",
        "/etc/modules",
        "/etc/default/grub",
        "/boot/grub/grub.cfg",
        "/boot/grub2/grub.cfg",
        "/etc/tmpfiles.d",
        "/usr/lib/tmpfiles.d",
        "/etc/profile",
        "/etc/profile.d",
        "/etc/environment",
        "/etc/bash.bashrc",
        "/root/.bashrc",
        "/root/.profile",
        "/home/*/.bashrc",
        "/home/*/.profile",
        "/etc/ld.so.preload",
    ],
    "Autostart / systemd / cron": [
        "/etc/crontab",
        "/etc/cron.d",
        "/etc/cron.hourly",
        "/etc/cron.daily",
        "/etc/cron.weekly",
        "/etc/cron.monthly",
        "/etc/systemd/system",
        "/etc/systemd/user",
        "/root/.config/systemd/user",
        "/home/*/.config/systemd/user",
    ],
}


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _app_list(app, name: str):
    return list(_app_value(app, name, []) or [])


def _tr(app, key: str, fallback: str) -> str:
    callback = getattr(app, "tr", None)
    if not callable(callback):
        return fallback
    try:
        return callback(key, fallback)
    except Exception:
        return fallback


def _ensure_app_tr(app) -> None:
    if callable(getattr(app, "tr", None)):
        return
    try:
        setattr(app, "tr", lambda _key, fallback=None: fallback)
    except Exception:
        pass


def _roots_list_widget(app, name: str):
    return _app_value(app, name)


def _roots_baseline_guard_info_path(app) -> str:
    return str(getattr(app, "roots_baseline_guard_info_path", "") or "").strip()


def _normalize_guard_path_pattern(path: str) -> str:
    raw = str(path or "").strip()
    if not raw:
        return ""
    return os.path.realpath(os.path.expanduser(raw))


def _is_allowed_guard_path(path: str) -> bool:
    normalized = _normalize_guard_path_pattern(path)
    if not normalized:
        return False
    for patterns in ROOTS_GUARD_DEFAULT_AREA_PATHS.values():
        for pattern in patterns:
            allowed = _normalize_guard_path_pattern(pattern)
            if not allowed:
                continue
            if fnmatch.fnmatch(normalized, allowed):
                return True
    return False


def _open_path_in_file_manager_safe(app, path: str, *, label: str) -> bool:
    opener = getattr(app, "open_path_in_file_manager", None)
    if not callable(opener):
        return False
    return bool(opener(path, label=label))


def _now_iso() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")


def roots_baseline_guard_supported_area_paths(app) -> dict[str, list[str]]:
    overrides = getattr(app, "roots_baseline_guard_path_overrides", {}) or {}
    if overrides:
        normalized = {}
        for key, value in overrides.items():
            if str(key) not in ROOTS_GUARD_DEFAULT_AREA_PATHS:
                continue
            if isinstance(value, (list, tuple)):
                items = [
                    _normalize_guard_path_pattern(item)
                    for item in value
                    if _normalize_guard_path_pattern(item)
                ]
                if items:
                    normalized[str(key)] = items
            else:
                item = _normalize_guard_path_pattern(value)
                if item:
                    normalized[str(key)] = [item]
        if normalized:
            return normalized

    return {
        area: [_normalize_guard_path_pattern(path) for path in paths]
        for area, paths in ROOTS_GUARD_DEFAULT_AREA_PATHS.items()
    }


def _selected_supported_areas(app) -> list[str]:
    scope_vars = getattr(app, "roots_baseline_guard_scope_vars", {}) or {}
    selected = []
    for label in ROOTS_GUARD_SUPPORTED_AREAS:
        var = scope_vars.get(label)
        try:
            is_enabled = bool(var.get()) if var is not None else False
        except Exception:
            is_enabled = False
        if is_enabled:
            selected.append(label)
    return selected


def _roots_trust_option_enabled(app, label: str) -> bool:
    trust_vars = getattr(app, "roots_baseline_guard_trust_vars", {}) or {}
    var = trust_vars.get(label)
    try:
        return bool(var.get()) if var is not None else False
    except Exception:
        return False


def _roots_root_mode_enabled(app) -> bool:
    var = getattr(app, "roots_baseline_guard_root_mode_var", None)
    try:
        return bool(var.get()) if var is not None else False
    except Exception:
        return False


def _is_optional_snapshot_path(path: str) -> bool:
    normalized = os.path.abspath(os.path.expanduser(str(path or "")))
    basename = os.path.basename(normalized)
    if "*" in str(path or ""):
        return True
    if basename in {"sshd_config", ".bashrc", ".profile", "authorized_keys"}:
        return True
    if normalized.endswith(("/sshd_config.d", "/systemd/user")):
        return True
    if normalized.endswith("/.config/systemd/user"):
        return True
    return False


def refresh_roots_baseline_guard_root_mode_status(app):
    is_enabled = _roots_root_mode_enabled(app)
    _set_stringvar(
        app,
        "roots_root_mode_status_var",
        (
            "Root-Modus: aktiv fuer naechsten Vorgang"
            if is_enabled
            else "Root-Modus: aus"
        ),
    )
    label = getattr(app, "roots_root_mode_status_label", None)
    if label is not None:
        try:
            label.configure(fg="#d4a017" if is_enabled else "#7a7f87")
        except Exception:
            pass


def _read_file_sha(app, path: str) -> str:
    hash_fn = getattr(app, "hash_file_sha256", None)
    if callable(hash_fn):
        return str(hash_fn(path) or "")
    return ""


def _signal_scan_role(path: str) -> str:
    normalized = os.path.abspath(os.path.expanduser(str(path or "")))
    basename = os.path.basename(normalized)
    parent = os.path.dirname(normalized)

    if basename == "sudoers" or parent.endswith("/sudoers.d"):
        return "sudoers"
    if parent.endswith("/pam.d"):
        return "pam"
    if "/polkit-1/" in normalized or normalized.endswith("/polkit-1"):
        return "polkit"
    if basename == "sysctl.conf" or parent.endswith("/sysctl.d"):
        return "sysctl"
    if basename == "modules" or parent.endswith(("/modprobe.d", "/modules-load.d")):
        return "kernel_modules"
    if basename == "grub.cfg" or normalized.endswith("/default/grub"):
        return "boot_config"
    if parent.endswith("/tmpfiles.d"):
        return "tmpfiles"
    if basename in {
        "profile",
        "environment",
        "bash.bashrc",
        ".bashrc",
        ".profile",
    } or parent.endswith("/profile.d"):
        return "shell_profile"
    if basename == "passwd":
        return "passwd"
    if basename == "shadow":
        return "shadow"
    if basename == "ld.so.preload":
        return "ld_preload"
    if basename == "authorized_keys":
        return "authorized_keys"
    if basename == "crontab" or parent.endswith(
        ("/cron.d", "/cron.hourly", "/cron.daily", "/cron.weekly", "/cron.monthly")
    ):
        return "cron"
    if parent.endswith(("/systemd/system", "/systemd/user")) or normalized.endswith(
        ("/systemd/system", "/systemd/user")
    ):
        return "systemd"
    if basename in {"sshd_config", "ssh_config"} or parent.endswith("/sshd_config.d"):
        return "ssh"
    return ""


def _path_supports_signal_scan(path: str) -> bool:
    return bool(_signal_scan_role(path))


def _parse_authorized_key_line(line: str) -> tuple[str, str] | None:
    tokens = str(line or "").split()
    if len(tokens) < 2:
        return None

    algo_prefixes = (
        "ssh-",
        "ecdsa-",
        "sk-ssh-",
    )
    algo_index = -1
    for idx, token in enumerate(tokens):
        if token.startswith(algo_prefixes):
            algo_index = idx
            break
    if algo_index < 0 or algo_index + 1 >= len(tokens):
        return None

    algo = tokens[algo_index].strip()
    comment = (
        tokens[algo_index + 2].strip()
        if len(tokens) > algo_index + 2
        else "ohne-kommentar"
    )
    comment = re.sub(r"\s+", "_", comment)
    return algo, comment


def _extract_security_signals(path: str, content: str) -> list[str]:
    role = _signal_scan_role(path)
    text = str(content or "")
    signals: list[str] = []

    if role == "sudoers":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            upper_line = line.upper()
            if "NOPASSWD:" in upper_line:
                signals.append("sudoers:nopasswd")
            if "!AUTHENTICATE" in upper_line:
                signals.append("sudoers:no_authenticate")
            if "SETENV:" in upper_line:
                signals.append("sudoers:setenv")
            if " ALL=(ALL" in upper_line and " ALL" in upper_line:
                signals.append("sudoers:full_access")

    elif role == "pam":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized_line = re.sub(r"\s+", " ", line).strip()
            lower_line = normalized_line.lower()
            parts = normalized_line.split()
            pam_section = parts[0].lower() if parts else ""
            if "pam_permit.so" in lower_line:
                signals.append("pam:permit")
                if pam_section == "auth":
                    signals.append("pam:permit_auth")
            if " nullok" in f" {lower_line} " or lower_line.endswith(" nullok"):
                signals.append("pam:nullok")
                if pam_section == "auth":
                    signals.append("pam:nullok_auth")
            if "pam_exec.so" in lower_line:
                signals.append("pam:exec")
                if pam_section == "auth":
                    signals.append("pam:exec_auth")
                if "/tmp/" in lower_line:
                    signals.append("pam:exec_tmp")

    elif role == "polkit":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("#", "//", "/*", "*")):
                continue
            lower_line = re.sub(r"\s+", " ", line).strip().lower()
            if "resultactive" in lower_line and "yes" in lower_line:
                signals.append("polkit:result_active_yes")
            if "resultany" in lower_line and "yes" in lower_line:
                signals.append("polkit:result_any_yes")
            if "resultinactive" in lower_line and "yes" in lower_line:
                signals.append("polkit:result_inactive_yes")
            if "polkit.addrule" in lower_line:
                signals.append("polkit:add_rule")
            if "subject.isinrole" in lower_line and "wheel" in lower_line:
                signals.append("polkit:wheel_role")
            if "org.freedesktop.policykit.exec" in lower_line or "pkexec" in lower_line:
                signals.append("polkit:pkexec")

    elif role == "sysctl":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized_line = re.sub(r"\s+", "", line).lower()
            if normalized_line in {
                "kernel.unprivileged_bpf_disabled=0",
                "kernel.unprivileged_userns_clone=1",
                "net.ipv4.conf.all.accept_redirects=1",
                "net.ipv4.conf.default.accept_redirects=1",
                "net.ipv4.conf.all.send_redirects=1",
                "net.ipv4.conf.default.send_redirects=1",
                "net.ipv4.conf.all.accept_source_route=1",
                "net.ipv4.conf.default.accept_source_route=1",
                "net.ipv4.ip_forward=1",
            }:
                signals.append(f"sysctl:{normalized_line}")

    elif role == "kernel_modules":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized_line = re.sub(r"\s+", " ", line).strip()
            lower_line = normalized_line.lower()
            if lower_line.startswith("install "):
                if (
                    lower_line.endswith("/bin/true")
                    or lower_line.endswith("/bin/false")
                    or lower_line.endswith(" true")
                    or lower_line.endswith(" false")
                ):
                    continue
                if "/tmp/" in lower_line:
                    signals.append("kernel:install_tmp")
                if "curl " in lower_line or "wget " in lower_line:
                    signals.append("kernel:network_fetch")
                if "/bin/sh" in lower_line or "/bin/bash" in lower_line:
                    signals.append("kernel:shell_exec")
            elif lower_line.startswith("softdep "):
                signals.append("kernel:softdep")
            elif lower_line.startswith("blacklist "):
                continue
            else:
                module_name = normalized_line.split(" ", 1)[0].strip()
                if module_name:
                    signals.append(f"kernel:module_load:{module_name}")

    elif role == "boot_config":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized_line = re.sub(r"\s+", " ", line).strip()
            lower_line = normalized_line.lower()
            if "init=/bin/sh" in lower_line:
                signals.append("boot:init_shell")
            if "rd.break" in lower_line:
                signals.append("boot:rd_break")
            if "systemd.unit=rescue.target" in lower_line or "single" in lower_line:
                signals.append("boot:rescue_mode")
            if "selinux=0" in lower_line:
                signals.append("boot:selinux_off")
            if "enforcing=0" in lower_line:
                signals.append("boot:selinux_permissive")
            if "audit=0" in lower_line:
                signals.append("boot:audit_off")
            if "module.sig_enforce=0" in lower_line:
                signals.append("boot:module_sig_off")

    elif role == "tmpfiles":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized_line = re.sub(r"\s+", " ", line).strip()
            lower_line = normalized_line.lower()
            parts = normalized_line.split()
            entry_type = parts[0][:1].lower() if parts else ""
            if "/tmp/" in lower_line:
                signals.append("tmpfiles:tmp_path")
            if entry_type == "l":
                signals.append("tmpfiles:symlink")
            if any(
                token in lower_line
                for token in (
                    " /etc/cron.",
                    " /etc/systemd/",
                    " /root/.ssh/",
                    " /etc/sudoers",
                )
            ):
                signals.append("tmpfiles:sensitive_target")
            if entry_type in {"c", "b"}:
                signals.append("tmpfiles:device_node")

    elif role == "shell_profile":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized_line = re.sub(r"\s+", " ", line).strip()
            lower_line = normalized_line.lower()
            if "ld_preload" in lower_line:
                signals.append("shell:ld_preload")
            if "path=" in lower_line:
                if "/tmp" in lower_line:
                    signals.append("shell:path_tmp")
                if ":." in lower_line or "=." in lower_line or "::" in lower_line:
                    signals.append("shell:path_dot")
            if lower_line.startswith("alias sudo="):
                signals.append("shell:alias_sudo")
            if "prompt_command=" in lower_line and (
                "curl " in lower_line
                or "wget " in lower_line
                or "/bin/sh" in lower_line
                or "/bin/bash" in lower_line
            ):
                signals.append("shell:prompt_command_exec")

    elif role == "passwd":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) < 3:
                continue
            username = parts[0].strip()
            uid = parts[2].strip()
            if uid == "0" and username and username != "root":
                signals.append(f"passwd:extra_uid0:{username}")

    elif role == "shadow":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) < 2:
                continue
            username = parts[0].strip()
            secret = parts[1].strip()
            if not username:
                continue
            if secret == "":
                signals.append(f"shadow:empty_password:{username}")
            elif secret not in {"!", "*", "!!"} and not secret.startswith("!"):
                signals.append(f"shadow:active_password:{username}")

    elif role == "ssh":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            normalized = re.sub(r"\s+", " ", line).strip()
            lower_line = normalized.lower()
            if lower_line == "permitrootlogin yes":
                signals.append("ssh:permit_root_login_yes")
            elif lower_line == "passwordauthentication yes":
                signals.append("ssh:password_auth_yes")
            elif lower_line == "pubkeyauthentication no":
                signals.append("ssh:pubkey_auth_no")

    elif role == "authorized_keys":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parsed = _parse_authorized_key_line(line)
            if not parsed:
                continue
            algo, comment = parsed
            signals.append(f"authkeys:key:{algo}:{comment}")
            if algo == "ssh-rsa":
                signals.append(f"authkeys:weak_algo:{algo}:{comment}")

    elif role == "ld_preload":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            signals.append(f"ld_preload:entry:{line}")

    elif role == "cron":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@reboot"):
                signals.append("cron:at_reboot")
            lower_line = line.lower()
            if "/tmp/" in lower_line:
                signals.append("cron:tmp_exec")
            if "curl " in lower_line or "wget " in lower_line:
                signals.append("cron:network_fetch")
            if "/bin/sh" in lower_line or "/bin/bash" in lower_line:
                signals.append("cron:shell_exec")
            if (
                "| sh" in lower_line
                or "| /bin/sh" in lower_line
                or "| bash" in lower_line
                or "| /bin/bash" in lower_line
            ):
                signals.append("cron:pipe_to_shell")

    elif role == "systemd":
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            lower_line = line.lower()
            if lower_line.startswith("execstart="):
                cmd = lower_line.split("=", 1)[-1].strip()
                if "/tmp/" in cmd:
                    signals.append("systemd:exec_tmp")
                if "curl " in cmd or "wget " in cmd:
                    signals.append("systemd:network_fetch")
                if "/bin/sh" in cmd or "/bin/bash" in cmd:
                    signals.append("systemd:shell_exec")
            elif lower_line == "wantedby=multi-user.target":
                signals.append("systemd:enabled_boot")

    return sorted(set(signals))


def _populate_security_signals(entry: dict[str, object], path: str, content: str):
    try:
        entry["signals"] = _extract_security_signals(path, content)
    except Exception:
        entry["signals"] = []


def _is_authorized_keys_rotation(
    added_signals: set[str], removed_signals: set[str]
) -> bool:
    if not added_signals or not removed_signals:
        return False
    combined = set(added_signals) | set(removed_signals)
    if not combined:
        return False
    return all(
        str(item).startswith(("authkeys:key:", "authkeys:weak_algo:"))
        for item in combined
    )


def _signal_change_label(
    path: str, added_signals: set[str], removed_signals: set[str]
) -> str:
    role = _signal_scan_role(path)
    added_labels = [_short_signal_label(item) for item in sorted(added_signals)]
    removed_labels = [_short_signal_label(item) for item in sorted(removed_signals)]
    if role == "sudoers":
        if added_labels:
            return f"Sudo-Regel aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Sudo-Regel entschärft: {removed_labels[0]}"
        return "Sudo-Regeln sicherheitsrelevant geändert"
    if role == "pam":
        if added_labels:
            return f"PAM-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"PAM-Fund entschärft: {removed_labels[0]}"
        return "PAM-Konfiguration geändert"
    if role == "polkit":
        if added_labels:
            return f"Polkit-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Polkit-Fund entschärft: {removed_labels[0]}"
        return "Polkit-Regel geändert"
    if role == "sysctl":
        if added_labels:
            return f"Sysctl-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Sysctl-Fund entschärft: {removed_labels[0]}"
        return "Sysctl-Konfiguration geändert"
    if role == "kernel_modules":
        if added_labels:
            return f"Kernel-Modul-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Kernel-Modul-Fund entschärft: {removed_labels[0]}"
        return "Kernel-Modul-Startkonfiguration geändert"
    if role == "boot_config":
        if added_labels:
            return f"Boot-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Boot-Fund entschärft: {removed_labels[0]}"
        return "Boot-Konfiguration geändert"
    if role == "tmpfiles":
        if added_labels:
            return f"Tmpfiles-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Tmpfiles-Fund entschärft: {removed_labels[0]}"
        return "Tmpfiles-Regel geändert"
    if role == "shell_profile":
        if added_labels:
            return f"Shell-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Shell-Fund entschärft: {removed_labels[0]}"
        return "Shell-Profil geändert"
    if role == "passwd":
        if added_labels:
            return f"UID-0-Konto erkannt: {added_labels[0].replace('UID0 ', '')}"
        if removed_labels:
            return f"UID-0-Konto entfernt: {removed_labels[0].replace('UID0 ', '')}"
        return "UID-0-/Benutzerstruktur geändert"
    if role == "shadow":
        if added_labels:
            return f"Passwortstatus auffällig: {added_labels[0]}"
        if removed_labels:
            return f"Passwortstatus entschärft: {removed_labels[0]}"
        return "Passwort-/Sperrstatus geändert"
    if role == "authorized_keys":
        weak_added = [
            item
            for item in sorted(added_signals)
            if item.startswith("authkeys:weak_algo:")
        ]
        weak_removed = [
            item
            for item in sorted(removed_signals)
            if item.startswith("authkeys:weak_algo:")
        ]
        if (
            _is_authorized_keys_rotation(added_signals, removed_signals)
            and not weak_added
        ):
            if len(added_labels) == 1 and len(removed_labels) == 1:
                return (
                    f"SSH-Schluessel rotiert: {removed_labels[0]} -> {added_labels[0]}"
                )
            return "SSH-Schluessel rotiert/ersetzt"
        if len(weak_added) == 1:
            return f"Schwacher SSH-Schluessel erkannt: {_short_signal_label(weak_added[0])}"
        if len(weak_added) > 1:
            return "Schwache SSH-Schluessel erkannt"
        if len(weak_removed) == 1:
            return f"Schwacher SSH-Schluessel entfernt: {_short_signal_label(weak_removed[0])}"
        if len(weak_removed) > 1:
            return "Schwache SSH-Schluessel entfernt"
        if len(added_labels) == 1:
            return f"SSH-Schlüssel erkannt: {added_labels[0]}"
        if len(added_labels) > 1:
            return "Neue SSH-Schlüssel erkannt"
        if len(removed_labels) == 1:
            return f"SSH-Schlüssel entfernt: {removed_labels[0]}"
        if len(removed_labels) > 1:
            return "SSH-Schlüssel entfernt/rotiert"
        return "authorized_keys geändert"
    if role == "ld_preload":
        if added_labels:
            return f"LD_PRELOAD-Eintrag erkannt: {added_labels[0]}"
        if removed_labels:
            return f"LD_PRELOAD-Eintrag entfernt: {removed_labels[0]}"
        return "LD_PRELOAD geändert"
    if role == "cron":
        if added_labels:
            return f"Cron-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Cron-Fund entschärft: {removed_labels[0]}"
        return "Cron-Konfiguration geändert"
    if role == "systemd":
        if added_labels:
            return f"Systemd-Fund aktiviert: {added_labels[0]}"
        if removed_labels:
            return f"Systemd-Fund entschärft: {removed_labels[0]}"
        return "Systemd-Service geändert"
    if role == "ssh":
        if len(added_labels) == 1:
            return f"SSH-Option aktiviert: {added_labels[0]}"
        if len(added_labels) > 1:
            return "Unsichere SSH-Optionen aktiviert"
        if len(removed_labels) == 1:
            return f"SSH-Option entschärft: {removed_labels[0]}"
        if len(removed_labels) > 1:
            return "SSH-Sicherheitsoptionen entschärft"
        return "SSH-Sicherheitsoption geändert"
    return "Sicherheitsprofil geändert"


def _signal_change_kind(
    path: str, added_signals: set[str], removed_signals: set[str]
) -> str:
    role = _signal_scan_role(path)
    if role == "sudoers":
        return "critical" if added_signals else "hint"
    if role == "pam":
        if any(
            item in added_signals
            for item in {
                "pam:permit",
                "pam:permit_auth",
                "pam:exec_auth",
                "pam:exec_tmp",
            }
        ):
            return "critical"
        if "pam:nullok_auth" in added_signals:
            return "warning"
        if added_signals:
            return "warning"
        return "hint"
    if role == "polkit":
        if any(
            item in added_signals
            for item in {
                "polkit:result_any_yes",
                "polkit:result_inactive_yes",
                "polkit:pkexec",
            }
        ):
            return "critical"
        if added_signals:
            return "warning"
        return "hint"
    if role == "sysctl":
        critical_signals = {
            "sysctl:kernel.unprivileged_bpf_disabled=0",
            "sysctl:net.ipv4.conf.all.accept_source_route=1",
            "sysctl:net.ipv4.conf.default.accept_source_route=1",
        }
        warning_signals = {
            "sysctl:kernel.unprivileged_userns_clone=1",
            "sysctl:net.ipv4.conf.all.accept_redirects=1",
            "sysctl:net.ipv4.conf.default.accept_redirects=1",
            "sysctl:net.ipv4.conf.all.send_redirects=1",
            "sysctl:net.ipv4.conf.default.send_redirects=1",
            "sysctl:net.ipv4.ip_forward=1",
        }
        if any(item in critical_signals for item in added_signals):
            return "critical"
        if any(item in warning_signals for item in added_signals):
            return "warning"
        if added_signals:
            return "warning"
        return "hint"
    if role == "kernel_modules":
        if any(
            item in added_signals
            for item in {
                "kernel:install_tmp",
                "kernel:network_fetch",
                "kernel:shell_exec",
            }
        ):
            return "critical"
        if any(
            item == "kernel:softdep" or item.startswith("kernel:module_load:")
            for item in added_signals
        ):
            return "warning"
        return "hint"
    if role == "boot_config":
        if any(
            item in added_signals
            for item in {
                "boot:init_shell",
                "boot:rd_break",
                "boot:module_sig_off",
            }
        ):
            return "critical"
        if any(
            item in added_signals
            for item in {
                "boot:rescue_mode",
                "boot:selinux_off",
                "boot:selinux_permissive",
                "boot:audit_off",
            }
        ):
            return "warning"
        return "hint"
    if role == "tmpfiles":
        if any(
            item in added_signals
            for item in {"tmpfiles:sensitive_target", "tmpfiles:device_node"}
        ):
            return "critical"
        if any(
            item in added_signals for item in {"tmpfiles:symlink", "tmpfiles:tmp_path"}
        ):
            return "warning"
        return "hint"
    if role == "shell_profile":
        if any(
            item in added_signals
            for item in {"shell:ld_preload", "shell:prompt_command_exec"}
        ):
            return "critical"
        if any(
            item in added_signals
            for item in {"shell:path_tmp", "shell:path_dot", "shell:alias_sudo"}
        ):
            return "warning"
        if added_signals:
            return "warning"
        return "hint"
    if role == "passwd":
        return "critical" if added_signals else "hint"
    if role == "shadow":
        if any(item.startswith("shadow:empty_password:") for item in added_signals):
            return "critical"
        if added_signals:
            return "warning"
        return "hint"
    if role == "authorized_keys":
        weak_algo_added = any(
            item.startswith("authkeys:weak_algo:") for item in added_signals
        )
        root_key_path = os.path.abspath(os.path.expanduser(str(path or ""))).startswith(
            "/root/"
        )
        if (
            _is_authorized_keys_rotation(added_signals, removed_signals)
            and not weak_algo_added
        ):
            return "warning" if root_key_path else "hint"
        if weak_algo_added and root_key_path:
            return "critical"
        if weak_algo_added:
            return "warning"
        if added_signals:
            return "critical" if root_key_path else "warning"
        return "hint"
    if role == "ld_preload":
        return "critical" if added_signals else "hint"
    if role == "cron":
        risky_added = set(added_signals)
        if risky_added == {"cron:at_reboot"}:
            return "hint"
        if "cron:pipe_to_shell" in risky_added:
            return "critical"
        if (
            "cron:network_fetch" in risky_added and "cron:shell_exec" in risky_added
        ) or ("cron:tmp_exec" in risky_added and "cron:shell_exec" in risky_added):
            return "critical"
        return "warning" if added_signals else "hint"
    if role == "systemd":
        risky_added = {
            "systemd:exec_tmp",
            "systemd:network_fetch",
            "systemd:shell_exec",
        }
        if any(item in risky_added for item in added_signals):
            return "critical"
        if set(added_signals) == {"systemd:enabled_boot"}:
            return "hint"
        return "warning" if added_signals else "hint"
    if role == "ssh":
        return "warning" if added_signals else "hint"
    return "hint"


def _format_signal(signal: str) -> str:
    signal = str(signal or "").strip()
    mapping = {
        "sudoers:nopasswd": "sudoers erlaubt NOPASSWD",
        "sudoers:no_authenticate": "sudoers erlaubt !authenticate",
        "sudoers:setenv": "sudoers erlaubt SETENV",
        "sudoers:full_access": "sudoers erlaubt sehr breite ALL=(ALL) ALL-Regel",
        "pam:permit": "PAM erlaubt Zugriff ueber pam_permit.so",
        "pam:permit_auth": "PAM erlaubt Authentifizierung ueber pam_permit.so",
        "pam:nullok": "PAM erlaubt leere Passwoerter ueber nullok",
        "pam:nullok_auth": "PAM erlaubt leere Passwoerter im Auth-Stack",
        "pam:exec": "PAM fuehrt externes Kommando ueber pam_exec aus",
        "pam:exec_auth": "PAM fuehrt externes Kommando im Auth-Stack aus",
        "pam:exec_tmp": "PAM fuehrt externes Kommando aus /tmp aus",
        "polkit:result_active_yes": "Polkit erlaubt aktive Sitzung per ResultActive=yes",
        "polkit:result_any_yes": "Polkit erlaubt jede Sitzung per ResultAny=yes",
        "polkit:result_inactive_yes": "Polkit erlaubt inaktive Sitzung per ResultInactive=yes",
        "polkit:add_rule": "Polkit fuegt benutzerdefinierte Regel per addRule hinzu",
        "polkit:wheel_role": "Polkit erlaubt Freigabe fuer die Rolle wheel",
        "polkit:pkexec": "Polkit referenziert pkexec oder org.freedesktop.policykit.exec",
        "sysctl:kernel.unprivileged_bpf_disabled=0": "Sysctl erlaubt unprivilegiertes BPF",
        "sysctl:kernel.unprivileged_userns_clone=1": "Sysctl erlaubt unprivilegierte User-Namespaces",
        "sysctl:net.ipv4.conf.all.accept_redirects=1": "Sysctl akzeptiert ICMP-Redirects global",
        "sysctl:net.ipv4.conf.default.accept_redirects=1": "Sysctl akzeptiert ICMP-Redirects standardmaessig",
        "sysctl:net.ipv4.conf.all.send_redirects=1": "Sysctl sendet ICMP-Redirects global",
        "sysctl:net.ipv4.conf.default.send_redirects=1": "Sysctl sendet ICMP-Redirects standardmaessig",
        "sysctl:net.ipv4.conf.all.accept_source_route=1": "Sysctl akzeptiert Source Routing global",
        "sysctl:net.ipv4.conf.default.accept_source_route=1": "Sysctl akzeptiert Source Routing standardmaessig",
        "sysctl:net.ipv4.ip_forward=1": "Sysctl aktiviert IP-Forwarding",
        "kernel:install_tmp": "Kernel-Modul-Startpfad fuehrt Befehl aus /tmp aus",
        "kernel:network_fetch": "Kernel-Modul-Startpfad laedt Inhalt aus dem Netzwerk",
        "kernel:shell_exec": "Kernel-Modul-Startpfad startet Shell direkt",
        "kernel:softdep": "Kernel-Modul nutzt Soft-Dependencies fuer Zusatzaktionen",
        "boot:init_shell": "Boot startet direkt mit init=/bin/sh",
        "boot:rd_break": "Boot aktiviert rd.break fuer fruehen Notfall-Shell-Zugang",
        "boot:rescue_mode": "Boot startet in Rescue-/Single-User-Modus",
        "boot:selinux_off": "Boot deaktiviert SELinux",
        "boot:selinux_permissive": "Boot setzt SELinux in permissiven Modus",
        "boot:audit_off": "Boot deaktiviert Linux-Auditing",
        "boot:module_sig_off": "Boot deaktiviert Modul-Signaturpruefung",
        "tmpfiles:tmp_path": "Tmpfiles-Regel arbeitet mit Pfaden unter /tmp",
        "tmpfiles:symlink": "Tmpfiles-Regel erstellt symbolische Links",
        "tmpfiles:sensitive_target": "Tmpfiles-Regel zielt auf sicherheitsrelevante Pfade",
        "tmpfiles:device_node": "Tmpfiles-Regel erstellt Geraete-/Spezialdateien",
        "shell:ld_preload": "Shell-Profil setzt LD_PRELOAD",
        "shell:path_tmp": "Shell-Profil erweitert PATH um /tmp",
        "shell:path_dot": "Shell-Profil verwendet . oder leere Segmente im PATH",
        "shell:alias_sudo": "Shell-Profil ueberschreibt sudo per Alias",
        "shell:prompt_command_exec": "Shell-Profil fuehrt ueber PROMPT_COMMAND externe Befehle aus",
        "ssh:permit_root_login_yes": "SSH erlaubt Root-Login per Passwort/ja",
        "ssh:password_auth_yes": "SSH erlaubt Passwort-Authentifizierung",
        "ssh:pubkey_auth_no": "SSH deaktiviert Public-Key-Authentifizierung",
        "cron:at_reboot": "Cron-Job startet beim Booten",
        "cron:tmp_exec": "Cron fuehrt Datei aus /tmp aus",
        "cron:network_fetch": "Cron laedt Inhalt aus dem Netzwerk",
        "cron:shell_exec": "Cron startet Shell direkt",
        "cron:pipe_to_shell": "Cron leitet Ausgabe direkt in eine Shell",
        "systemd:exec_tmp": "Systemd startet Datei aus /tmp",
        "systemd:network_fetch": "Systemd startet Netzwerk-Download",
        "systemd:shell_exec": "Systemd startet Shell direkt",
        "systemd:enabled_boot": "Systemd-Service wird beim Booten aktiviert",
    }
    if signal in mapping:
        return mapping[signal]
    if signal.startswith("kernel:module_load:"):
        module_name = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"Kernel-Modul wird geladen: {module_name}"
    if signal.startswith("boot:"):
        return signal
    if signal.startswith("passwd:extra_uid0:"):
        username = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"Zusaetzliches UID-0-Konto erkannt: {username}"
    if signal.startswith("shadow:empty_password:"):
        username = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"Leeres Passwort erkannt: {username}"
    if signal.startswith("shadow:active_password:"):
        username = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"Aktives Passwort erkannt: {username}"
    if signal.startswith("authkeys:key:"):
        parts = signal.split(":", 3)
        algo = parts[2].strip() if len(parts) > 2 else "ssh-key"
        comment = parts[3].strip() if len(parts) > 3 else "ohne-kommentar"
        return f"SSH-Schlüssel erkannt: {algo} ({comment})"
    if signal.startswith("authkeys:weak_algo:"):
        parts = signal.split(":", 3)
        algo = parts[2].strip() if len(parts) > 2 else "ssh-key"
        comment = parts[3].strip() if len(parts) > 3 else "ohne-kommentar"
        return f"Schwacher SSH-Schluessel erkannt: {algo} ({comment})"
    if signal.startswith("ld_preload:entry:"):
        entry = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"LD_PRELOAD lädt: {entry}"
    return signal


def _short_signal_label(signal: str) -> str:
    signal = str(signal or "").strip()
    mapping = {
        "sudoers:nopasswd": "NOPASSWD",
        "sudoers:no_authenticate": "!authenticate",
        "sudoers:setenv": "SETENV",
        "sudoers:full_access": "ALL=(ALL) ALL",
        "pam:permit": "pam_permit.so",
        "pam:permit_auth": "pam_permit.so im auth-Stack",
        "pam:nullok": "nullok",
        "pam:nullok_auth": "nullok im auth-Stack",
        "pam:exec": "pam_exec.so",
        "pam:exec_auth": "pam_exec.so im auth-Stack",
        "pam:exec_tmp": "pam_exec aus /tmp",
        "polkit:result_active_yes": "ResultActive=yes",
        "polkit:result_any_yes": "ResultAny=yes",
        "polkit:result_inactive_yes": "ResultInactive=yes",
        "polkit:add_rule": "addRule",
        "polkit:wheel_role": "wheel-Rolle",
        "polkit:pkexec": "pkexec",
        "sysctl:kernel.unprivileged_bpf_disabled=0": "unprivileged_bpf_disabled=0",
        "sysctl:kernel.unprivileged_userns_clone=1": "unprivileged_userns_clone=1",
        "sysctl:net.ipv4.conf.all.accept_redirects=1": "accept_redirects=1 (all)",
        "sysctl:net.ipv4.conf.default.accept_redirects=1": "accept_redirects=1 (default)",
        "sysctl:net.ipv4.conf.all.send_redirects=1": "send_redirects=1 (all)",
        "sysctl:net.ipv4.conf.default.send_redirects=1": "send_redirects=1 (default)",
        "sysctl:net.ipv4.conf.all.accept_source_route=1": "accept_source_route=1 (all)",
        "sysctl:net.ipv4.conf.default.accept_source_route=1": "accept_source_route=1 (default)",
        "sysctl:net.ipv4.ip_forward=1": "ip_forward=1",
        "kernel:install_tmp": "Install aus /tmp",
        "kernel:network_fetch": "Netzwerk-Download",
        "kernel:shell_exec": "Shell-Start",
        "kernel:softdep": "softdep",
        "boot:init_shell": "init=/bin/sh",
        "boot:rd_break": "rd.break",
        "boot:rescue_mode": "rescue/single",
        "boot:selinux_off": "SELinux aus",
        "boot:selinux_permissive": "SELinux permissive",
        "boot:audit_off": "Audit aus",
        "boot:module_sig_off": "module.sig_enforce=0",
        "tmpfiles:tmp_path": "/tmp-Pfad",
        "tmpfiles:symlink": "Symlink",
        "tmpfiles:sensitive_target": "sensitiver Pfad",
        "tmpfiles:device_node": "Geraetedatei",
        "shell:ld_preload": "LD_PRELOAD",
        "shell:path_tmp": "PATH mit /tmp",
        "shell:path_dot": "PATH mit .",
        "shell:alias_sudo": "alias sudo",
        "shell:prompt_command_exec": "PROMPT_COMMAND Exec",
        "ssh:permit_root_login_yes": "PermitRootLogin yes",
        "ssh:password_auth_yes": "PasswordAuthentication yes",
        "ssh:pubkey_auth_no": "PubkeyAuthentication no",
        "cron:at_reboot": "@reboot",
        "cron:tmp_exec": "Exec aus /tmp",
        "cron:network_fetch": "Netzwerk-Download",
        "cron:shell_exec": "Shell-Start",
        "cron:pipe_to_shell": "Pipe zu Shell",
        "systemd:exec_tmp": "ExecStart aus /tmp",
        "systemd:network_fetch": "Netzwerk-Download",
        "systemd:shell_exec": "Shell-Start",
        "systemd:enabled_boot": "WantedBy multi-user.target",
    }
    if signal in mapping:
        return mapping[signal]
    if signal.startswith("kernel:module_load:"):
        module_name = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"Modul {module_name}"
    if signal.startswith("passwd:extra_uid0:"):
        username = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"UID0 {username}"
    if signal.startswith("shadow:empty_password:"):
        username = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"leeres Passwort {username}"
    if signal.startswith("shadow:active_password:"):
        username = signal.split(":", 2)[-1].strip() or "unbekannt"
        return f"aktives Passwort {username}"
    if signal.startswith("authkeys:key:"):
        parts = signal.split(":", 3)
        algo = parts[2].strip() if len(parts) > 2 else "ssh-key"
        comment = parts[3].strip() if len(parts) > 3 else "ohne-kommentar"
        return f"{algo} {comment}"
    if signal.startswith("authkeys:weak_algo:"):
        parts = signal.split(":", 3)
        algo = parts[2].strip() if len(parts) > 2 else "ssh-key"
        comment = parts[3].strip() if len(parts) > 3 else "ohne-kommentar"
        return f"{algo} {comment}"
    if signal.startswith("ld_preload:entry:"):
        entry = signal.split(":", 2)[-1].strip() or "unbekannt"
        return entry
    return signal


def _signal_detail_text(old: dict[str, object], new: dict[str, object]) -> str:
    old_signals = {
        str(item).strip() for item in (old.get("signals") or []) if str(item).strip()
    }
    new_signals = {
        str(item).strip() for item in (new.get("signals") or []) if str(item).strip()
    }
    added_signals = sorted(new_signals - old_signals)
    removed_signals = sorted(old_signals - new_signals)
    if not added_signals and not removed_signals:
        return ""

    lines = ["Signale:"]
    for signal in added_signals:
        lines.append(f"+ {_format_signal(signal)}")
    for signal in removed_signals:
        lines.append(f"- {_format_signal(signal)}")

    explanations = _signal_explanation_lines(added_signals, removed_signals)
    if explanations:
        lines.append("")
        lines.append("Einordnung:")
        lines.extend(f"- {line}" for line in explanations)
    return "\n".join(lines)


def _signal_explanation_lines(
    added_signals: list[str] | tuple[str, ...],
    removed_signals: list[str] | tuple[str, ...],
) -> list[str]:
    explanations: list[str] = []
    seen: set[str] = set()
    current_signals = [
        str(item or "").strip() for item in added_signals if str(item or "").strip()
    ]
    previous_signals = [
        str(item or "").strip() for item in removed_signals if str(item or "").strip()
    ]

    def add(text: str):
        text = str(text or "").strip()
        if not text or text in seen:
            return
        seen.add(text)
        explanations.append(text)

    for signal in current_signals:
        if signal in {"sudoers:nopasswd", "sudoers:no_authenticate"}:
            add(
                "Diese sudo-Regel kann Passwortabfragen oder normale Schutzstufen aushebeln."
            )
        elif signal in {"sudoers:setenv", "sudoers:full_access"}:
            add(
                "Diese sudo-Regel erweitert Rechte sehr breit und erhoeht das Missbrauchsrisiko deutlich."
            )
        elif signal in {
            "polkit:result_active_yes",
            "polkit:result_any_yes",
            "polkit:result_inactive_yes",
            "polkit:add_rule",
            "polkit:wheel_role",
            "polkit:pkexec",
        }:
            add(
                "Diese Polkit-Regel kann Rechteausweitung oder sehr freizuegige Freigaben fuer lokale Aktionen erlauben."
            )
        elif signal.startswith("sysctl:"):
            add(
                "Diese Sysctl-Einstellung kann Kernel-, Netzwerk- oder Isolationsschutz abschwaechen und sollte bewusst gesetzt sein."
            )
        elif signal.startswith("kernel:"):
            add(
                "Diese Kernel-/Modul-Startaenderung kann Persistenz, fruehe Befehlsausfuehrung oder das Laden zusaetzlicher Module beim Systemstart beeinflussen."
            )
        elif signal.startswith("boot:"):
            add(
                "Diese Boot-Konfiguration kann fruehen Root-Zugang, schwächere Integritaetspruefung oder deutlich reduzierte Systemschutzmechanismen beim Start erlauben."
            )
        elif signal.startswith("tmpfiles:"):
            add(
                "Diese tmpfiles-Regel kann beim Systemstart Dateien, Links oder spezielle Pfade vorbereiten und damit fruehe Persistenz oder Umleitungen ermoeglichen."
            )
        elif signal.startswith("shell:"):
            add(
                "Diese Shell-Profil-Aenderung kann Befehlsaufrufe, Umgebungsvariablen oder das Startverhalten von Sessions manipulieren."
            )
        elif signal in {"pam:permit", "pam:permit_auth"}:
            add(
                "pam_permit.so erlaubt Zugriffe sehr freizuegig und kann Authentifizierung praktisch aushebeln."
            )
        elif signal in {"pam:nullok", "pam:nullok_auth"}:
            add(
                "nullok kann leere Passwortzustaende akzeptieren und sollte nur sehr bewusst eingesetzt werden."
            )
        elif signal in {"pam:exec", "pam:exec_auth", "pam:exec_tmp"}:
            add(
                "pam_exec fuehrt externe Programme aus; im Auth-Stack oder aus /tmp ist das besonders heikel."
            )
        elif signal.startswith("authkeys:weak_algo:"):
            add(
                "Ein schwacher oder veralteter SSH-Schluesselalgorithmus senkt die Widerstandskraft gegen Missbrauch."
            )
        elif signal.startswith("authkeys:key:"):
            add(
                "Neue SSH-Schluessel koennen direkten Fernzugriff ermoeglichen und sollten bewusst autorisiert sein."
            )
        elif signal == "ssh:permit_root_login_yes":
            add(
                "Direkter Root-Login ueber SSH vergroessert die Angriffsoberflaeche erheblich."
            )
        elif signal == "ssh:password_auth_yes":
            add(
                "Passwort-Authentifizierung ueber SSH erhoeht die Gefahr von Brute-Force- oder Passwortangriffen."
            )
        elif signal == "ssh:pubkey_auth_no":
            add(
                "Wenn Public-Key-Authentifizierung deaktiviert wird, bleiben oft nur schwaechere Login-Wege uebrig."
            )
        elif signal.startswith("shadow:empty_password:"):
            add(
                "Leere Passwortfelder koennen direkte Kontoanmeldung ohne regulare Absicherung erlauben."
            )
        elif signal.startswith("shadow:active_password:"):
            add(
                "Ein aktiver Passwort-Hash zeigt, dass das Konto grundsaetzlich per Passwort nutzbar sein kann."
            )
        elif signal.startswith("passwd:extra_uid0:"):
            add(
                "Zusaetzliche UID-0-Konten bedeuten Root-aehnliche Rechte und sollten sehr genau geprueft werden."
            )
        elif signal.startswith("ld_preload:entry:"):
            add(
                "LD_PRELOAD kann Bibliotheken global einschleusen und ist deshalb ein besonders kritischer Hook-Punkt."
            )
        elif signal == "cron:at_reboot":
            add("Ein Cron-Job beim Booten kann zur Persistenz genutzt werden.")
        elif signal in {
            "cron:network_fetch",
            "cron:shell_exec",
            "cron:pipe_to_shell",
            "cron:tmp_exec",
        }:
            add(
                "Diese Cron-Kombination wirkt wie eine moegliche Persistenz- oder Nachlade-Technik und sollte genau geprueft werden."
            )
        elif signal in {
            "systemd:exec_tmp",
            "systemd:network_fetch",
            "systemd:shell_exec",
        }:
            add(
                "Ein systemd-Dienst mit Shell-/Netzwerk-/tmp-Ausfuehrung kann auf Persistenz oder Fernnachladen hindeuten."
            )
        elif signal == "systemd:enabled_boot":
            add(
                "Ein beim Booten aktivierter Dienst ist nicht automatisch boese, aber fuer Persistenz besonders relevant."
            )

    if previous_signals and current_signals:
        add(
            "Die Signalmenge hat sich geaendert; bitte pruefen, ob diese Sicherheitsaenderung beabsichtigt war."
        )
    elif previous_signals and not current_signals:
        add(
            "Mindestens ein zuvor auffaelliger Sicherheitsindikator wurde entfernt oder entschaerft."
        )

    return explanations


def _capture_file_state_with_root(
    app, path: str, entry: dict[str, object]
) -> dict[str, object]:
    override = getattr(app, "roots_baseline_guard_capture_file_state_as_root", None)
    if callable(override):
        try:
            override_data = override(path)
        except Exception as exc:
            override_data = {"error": str(exc)}
        if isinstance(override_data, dict):
            merged = dict(entry)
            merged.update(override_data)
            merged["path"] = os.path.abspath(os.path.expanduser(str(path)))
            merged["exists"] = bool(merged.get("exists", entry.get("exists")))
            merged["readable"] = bool(merged.get("readable", True))
            merged["read_via_root"] = bool(merged.get("read_via_root", True))
            merged["error"] = str(merged.get("error") or "")
            return merged

    if not _is_allowed_guard_path(path):
        entry["error"] = "Root-Read fuer diesen Pfad ist nicht erlaubt."
        return entry

    rc_stat, out_stat = run_cmd(
        ["sudo", "-n", "stat", "-c", "%s|%Y|%a", path],
        timeout=8,
    )
    if rc_stat == 0:
        try:
            size_text, mtime_text, mode_text = str(out_stat or "").split("|", 2)
            entry["size"] = int(size_text or 0)
            entry["mtime"] = float(mtime_text or 0.0)
            entry["mode"] = oct(int(mode_text or "0", 8))
        except Exception:
            pass

    rc_sha, out_sha = run_cmd(["sudo", "-n", "sha256sum", path], timeout=10)
    if rc_sha == 0:
        entry["sha256"] = str(out_sha or "").split()[0]
        entry["readable"] = True
        entry["read_via_root"] = True
        entry["error"] = ""
        if _path_supports_signal_scan(path):
            rc_cat, out_cat = run_cmd(["sudo", "-n", "cat", path], timeout=10)
            if rc_cat == 0:
                _populate_security_signals(entry, path, out_cat)
        return entry

    entry["error"] = str(out_sha or out_stat or "sudo read failed").strip()
    return entry


def _capture_file_state(app, path: str, *, use_root: bool = False) -> dict[str, object]:
    normalized = os.path.abspath(os.path.expanduser(str(path)))
    entry: dict[str, object] = {
        "path": normalized,
        "exists": os.path.exists(normalized),
        "sha256": "",
        "size": 0,
        "mtime": 0.0,
        "mode": "",
        "readable": False,
        "read_via_root": False,
        "error": "",
        "signals": [],
    }

    if not entry["exists"]:
        return entry

    try:
        st = os.stat(normalized)
        entry["size"] = int(st.st_size)
        entry["mtime"] = float(st.st_mtime)
        entry["mode"] = oct(st.st_mode & 0o777)
    except Exception as exc:
        entry["error"] = str(exc)
        return entry

    if os.path.isfile(normalized) and os.access(normalized, os.R_OK):
        entry["readable"] = True
        try:
            entry["sha256"] = _read_file_sha(app, normalized)
        except Exception as exc:
            entry["error"] = str(exc)
        if _path_supports_signal_scan(normalized):
            try:
                with open(
                    normalized, "r", encoding="utf-8", errors="replace"
                ) as handle:
                    _populate_security_signals(entry, normalized, handle.read())
            except Exception:
                entry["signals"] = []
    elif use_root and os.path.isfile(normalized):
        entry = _capture_file_state_with_root(app, normalized, entry)
    return entry


def _capture_monitored_path(
    app, path: str, *, use_root: bool = False
) -> list[dict[str, object]]:
    path_text = str(path or "")
    if "*" in path_text:
        items = []
        matched_paths = sorted(glob(os.path.expanduser(path_text)))
        for matched in matched_paths:
            items.extend(_capture_monitored_path(app, matched, use_root=use_root))
        if not matched_paths:
            normalized_missing = os.path.abspath(os.path.expanduser(path_text))
            items.append(
                {
                    "path": normalized_missing,
                    "exists": False,
                    "sha256": "",
                    "size": 0,
                    "mtime": 0.0,
                    "mode": "",
                    "readable": False,
                    "read_via_root": False,
                    "error": "",
                    "signals": [],
                }
            )
        return items

    normalized = os.path.abspath(os.path.expanduser(str(path)))
    base_entry = _capture_file_state(app, normalized, use_root=use_root)
    items = [base_entry]

    if not os.path.isdir(normalized):
        return items

    try:
        names = sorted(os.listdir(normalized))
    except Exception:
        return items

    for name in names:
        if str(name).startswith("."):
            continue
        child_path = os.path.join(normalized, name)
        if os.path.isdir(child_path):
            continue
        items.append(_capture_file_state(app, child_path, use_root=use_root))
    return items


def _capture_area_snapshot(
    app, area: str, *, use_root: bool = False
) -> dict[str, object]:
    paths_by_area = roots_baseline_guard_supported_area_paths(app)
    items = []
    for path in paths_by_area.get(area, []):
        items.extend(_capture_monitored_path(app, path, use_root=use_root))
    return {
        "area": area,
        "captured_at": _now_iso(),
        "capture_mode": "root" if use_root else "user",
        "items": items,
    }


def _baseline_payload(
    app, areas: list[str], *, use_root: bool = False
) -> dict[str, object]:
    payload_areas = {}
    for area in areas:
        payload_areas[area] = _capture_area_snapshot(app, area, use_root=use_root)
    return {
        "version": 1,
        "created_at": _now_iso(),
        "updated_at": "",
        "last_check_at": "",
        "last_check_results": [],
        "areas": payload_areas,
    }


def _compare_item(
    old: dict[str, object], new: dict[str, object]
) -> tuple[str, str, str]:
    path = str(new.get("path") or old.get("path") or "-")

    old_exists = bool(old.get("exists"))
    new_exists = bool(new.get("exists"))
    if old_exists and not new_exists:
        return path, "Datei fehlt", "critical"
    if not old_exists and new_exists:
        return path, "Datei neu vorhanden", "warning"

    old_error = str(old.get("error") or "").strip()
    new_error = str(new.get("error") or "").strip()
    if old_error != new_error:
        return path, "Zugriff / Fehlerstatus geändert", "hint"

    old_mode = str(old.get("mode") or "")
    new_mode = str(new.get("mode") or "")
    if old_mode != new_mode:
        return path, "Dateirechte geändert", "warning"

    old_signals = {
        str(item).strip() for item in (old.get("signals") or []) if str(item).strip()
    }
    new_signals = {
        str(item).strip() for item in (new.get("signals") or []) if str(item).strip()
    }
    if old_signals != new_signals:
        added_signals = new_signals - old_signals
        removed_signals = old_signals - new_signals
        return (
            path,
            _signal_change_label(path, added_signals, removed_signals),
            _signal_change_kind(path, added_signals, removed_signals),
        )

    old_sha = str(old.get("sha256") or "")
    new_sha = str(new.get("sha256") or "")
    if old_sha and new_sha and old_sha != new_sha:
        return path, "Inhalt geändert", "critical"

    old_size = int(old.get("size") or 0)
    new_size = int(new.get("size") or 0)
    if old_size != new_size:
        return path, "Dateigröße geändert", "warning"

    old_mtime = float(old.get("mtime") or 0.0)
    new_mtime = float(new.get("mtime") or 0.0)
    if abs(old_mtime - new_mtime) > 1e-6:
        return path, "Zeitstempel geändert", "hint"

    return "", "", ""


def _severity_for_area(
    area: str, change_kind: str, path: str = "", change: str = ""
) -> str:
    basename = os.path.basename(str(path or ""))
    role = _signal_scan_role(path)

    if role == "sudoers":
        if change == "Datei fehlt":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Kritisch"
        if change_kind == "critical":
            return "Kritisch"
        return "Warnung"

    if role == "passwd" or basename == "group":
        if change == "Datei fehlt":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "critical":
            return "Kritisch"
        return "Hinweis"

    if role == "shadow":
        if change == "Datei fehlt":
            return "Kritisch"
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "polkit":
        if change == "Datei fehlt":
            return "Warnung"
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "sysctl":
        if change == "Datei fehlt":
            return "Hinweis"
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "kernel_modules":
        if change_kind == "critical":
            return "Kritisch"
        if change in {
            "Datei neu vorhanden",
            "Inhalt geändert",
            "Dateirechte geändert",
            "Dateigröße geändert",
        }:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "boot_config":
        if change == "Datei fehlt":
            return "Warnung"
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "tmpfiles":
        if change_kind == "critical":
            return "Kritisch"
        if change in {
            "Datei neu vorhanden",
            "Inhalt geändert",
            "Dateirechte geändert",
            "Dateigröße geändert",
        }:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "shell_profile":
        if change == "Datei fehlt":
            return "Hinweis"
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "pam":
        if change == "Datei fehlt":
            return "Warnung"
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "authorized_keys":
        if change == "Datei fehlt" and os.path.abspath(
            os.path.expanduser(str(path or ""))
        ).startswith("/root/"):
            return "Warnung"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            if os.path.abspath(os.path.expanduser(str(path or ""))).startswith(
                "/root/"
            ):
                return "Kritisch"
            return "Warnung"
        if change_kind == "critical":
            return "Kritisch"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "ld_preload":
        if change in {"Datei fehlt", "Datei neu vorhanden"}:
            return "Kritisch"
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Kritisch"
        return "Warnung"

    if role in {"cron", "systemd"}:
        if change_kind == "critical":
            return "Kritisch"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if role == "ssh":
        if change == "Datei fehlt" and basename == "sshd_config":
            return "Warnung"
        if change in {"Inhalt geändert", "Dateirechte geändert", "Dateigröße geändert"}:
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"

    if area == "DNS / Hosts":
        if change_kind == "critical":
            return "Warnung"
        if change_kind == "warning":
            return "Warnung"
        return "Hinweis"
    if change_kind == "critical":
        return "Kritisch"
    if change_kind == "warning":
        return "Warnung"
    return "Hinweis"


def _status_for_severity(severity: str) -> str:
    return {
        "Kritisch": "Änderung erkannt",
        "Warnung": "Prüfen",
        "Hinweis": "Beobachten",
    }.get(severity, "Info")


def _load_baseline_payload(app) -> dict[str, object]:
    path = str(getattr(app, "roots_baseline_guard_baseline_path", "") or "").strip()
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle) or {}
    except Exception:
        return {}


def _load_whitelist_payload(app) -> dict[str, object]:
    path = str(getattr(app, "roots_baseline_guard_whitelist_path", "") or "").strip()
    if not path or not os.path.isfile(path):
        return {"version": 1, "entries": []}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle) or {}
    except Exception:
        return {"version": 1, "entries": []}
    if not isinstance(data, dict):
        return {"version": 1, "entries": []}
    entries = data.get("entries")
    if not isinstance(entries, list):
        entries = []
    return {
        "version": int(data.get("version") or 1),
        "entries": entries,
    }


def _save_whitelist_payload(app, payload: dict[str, object]) -> tuple[bool, str]:
    return safe_write_json(app.roots_baseline_guard_whitelist_path, payload)


def _set_stringvar(app, attr_name: str, value: str):
    var = _app_value(app, attr_name)
    if var is None:
        return
    try:
        var.set(value)
    except Exception:
        pass


def _set_light_color(app, color: str):
    canvas = _app_value(app, "roots_integrity_light")
    item_id = _app_value(app, "roots_integrity_light_item")
    if canvas is None or item_id is None:
        return
    try:
        canvas.itemconfig(item_id, fill=color, outline=color)
    except Exception:
        pass


def _refresh_history_list(app, lines: list[str]):
    widget = _roots_list_widget(app, "roots_baseline_guard_history_list")
    if widget is None:
        return
    try:
        widget.delete(0, "end")
        for line in lines:
            widget.insert("end", line)
    except Exception:
        pass


def _refresh_whitelist_list(app, entries: list[dict[str, object]]):
    widget = _roots_list_widget(app, "roots_baseline_guard_whitelist_list")
    if widget is None:
        return
    meta = [item for item in entries if isinstance(item, dict)]
    setattr(app, "roots_baseline_guard_whitelist_meta", meta)
    try:
        widget.delete(0, "end")
        for item in meta:
            category = (
                str(item.get("category", "") or "").strip()
                or _roots_result_category_label(item)
                or "Allgemein"
            )
            widget.insert(
                "end",
                f"[{category}] {item.get('path', '-')} :: {item.get('change', '-')}",
            )
    except Exception:
        pass


def _roots_result_category_label(row: dict[str, object]) -> str:
    path = str((row or {}).get("path") or "")
    role = _signal_scan_role(path)
    if role == "ssh":
        return "SSH"
    if role == "sudoers":
        return "sudoers"
    if role == "shadow":
        return "shadow"
    if role == "polkit":
        return "polkit"
    if role == "sysctl":
        return "sysctl"
    if role == "kernel_modules":
        return "kernel"
    if role == "boot_config":
        return "boot"
    if role == "tmpfiles":
        return "tmpfiles"
    if role == "shell_profile":
        return "shell"
    if role == "pam":
        return "PAM"
    if role == "passwd":
        return "UID0"
    if role == "authorized_keys":
        return "authkeys"
    if role == "ld_preload":
        return "LD_PRELOAD"
    if role == "cron":
        return "cron"
    if role == "systemd":
        return "systemd"
    if str((row or {}).get("area") or "") == "DNS / Hosts":
        return "DNS"
    return ""


def _roots_result_risk_rank(row: dict[str, object]) -> int:
    risk = str((row or {}).get("risk") or "-")
    return {
        "Kritisch": 0,
        "Warnung": 1,
        "Hinweis": 2,
        "-": 3,
    }.get(risk, 4)


def _roots_result_category_rank(row: dict[str, object]) -> int:
    label = _roots_result_category_label(row)
    return {
        "LD_PRELOAD": 0,
        "shadow": 1,
        "sudoers": 2,
        "polkit": 3,
        "sysctl": 4,
        "kernel": 5,
        "boot": 6,
        "tmpfiles": 7,
        "shell": 8,
        "PAM": 9,
        "UID0": 10,
        "authkeys": 11,
        "SSH": 12,
        "systemd": 13,
        "cron": 14,
        "DNS": 15,
    }.get(label, 9)


def _sorted_roots_result_rows(rows) -> list[dict[str, object]]:
    normalized_rows = [row for row in rows or [] if isinstance(row, dict)]
    return sorted(
        normalized_rows,
        key=lambda row: (
            _roots_result_risk_rank(row),
            _roots_result_category_rank(row),
            str(row.get("path") or ""),
            str(row.get("change") or ""),
            str(row.get("time") or ""),
        ),
    )


def _refresh_roots_signal_summary(app, rows):
    labels = []
    seen = set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        label = _roots_result_category_label(row)
        if not label or label in seen:
            continue
        seen.add(label)
        labels.append(label)
    summary = "Funde: " + (", ".join(labels) if labels else "-")
    _set_stringvar(app, "roots_signal_summary_var", summary)


def _detail_text_without_path_line(text: str, path: str) -> str:
    lines = str(text or "").splitlines()
    target = f"Pfad: {path}".strip()
    filtered = []
    removed = False
    for line in lines:
        if not removed and str(line).strip() == target:
            removed = True
            continue
        filtered.append(line)
    return "\n".join(filtered).strip()


def _set_info_text(app, text: str, path: str = ""):
    widget = _app_value(app, "roots_baseline_guard_info_text")
    if widget is None:
        return
    link_path = str(path or "").strip()
    body_text = (
        _detail_text_without_path_line(text, link_path)
        if link_path
        else str(text or "")
    )
    setattr(app, "roots_baseline_guard_info_path", link_path)
    try:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        if link_path:
            widget.insert("1.0", f"Pfad: {link_path}\n\n")
            try:
                widget.tag_add("roots_path_link", "1.6", f"1.{6 + len(link_path)}")
                widget.tag_configure(
                    "roots_path_link",
                    foreground="#79c0ff",
                    underline=1,
                )
                widget.tag_bind(
                    "roots_path_link",
                    "<Button-1>",
                    lambda _event: open_roots_baseline_guard_info_path(app),
                )
                widget.tag_bind(
                    "roots_path_link",
                    "<Enter>",
                    lambda _event: widget.configure(cursor="hand2"),
                )
                widget.tag_bind(
                    "roots_path_link",
                    "<Leave>",
                    lambda _event: widget.configure(cursor="xterm"),
                )
            except Exception:
                pass
            if body_text:
                widget.insert("end", body_text)
        else:
            widget.insert("1.0", body_text)
        widget.configure(state="disabled")
    except Exception:
        pass


def _detail_text_for_row(row: dict[str, str]) -> str:
    lines = [
        f"Bereich: {row.get('area', '-')}",
        f"Pfad: {row.get('path', '-')}",
        f"Änderung: {row.get('change', '-')}",
        f"Risiko: {row.get('risk', '-')}",
        f"Zeit: {row.get('time', '-')}",
        f"Status: {row.get('status', '-')}",
    ]
    detail_extra = str(row.get("detail_extra") or "").strip()
    if detail_extra:
        lines.extend(["", detail_extra])
    return "\n".join(lines).strip()


def _table_change_label(path: str, change: str, detail_extra: str = "") -> str:
    path = str(path or "")
    change = str(change or "-")
    detail_extra = str(detail_extra or "")
    basename = os.path.basename(path)

    if basename in {"sshd_config", "ssh_config"} and (
        "SSH-" in change or "SSH " in change
    ):
        return f"[SSH] {change}"
    if basename == "sudoers" and "sicherheitsrelevant" in change.lower():
        return f"[sudoers] {change}"
    if basename == "passwd" and "UID-0-" in change:
        return f"[UID0] {change}"
    if basename == "passwd" and "Zusaetzliches UID-0-Konto" in detail_extra:
        return f"[UID0] {change}"
    return change


def _make_result_row(
    *,
    area: str,
    path: str,
    change: str,
    risk: str,
    timestamp: str,
    status: str,
    detail_extra: str = "",
) -> dict[str, object]:
    path = str(path or "-")
    display_change = _table_change_label(path, change, detail_extra)
    return {
        "area": str(area or "-"),
        "path": path,
        "change": str(change or "-"),
        "risk": str(risk or "-"),
        "time": str(timestamp or "-"),
        "status": str(status or "-"),
        "display": (path, display_change, risk, timestamp, status),
        "tag": _tag_for_row(str(risk or "-"), str(status or "-")),
        "detail": _detail_text_for_row(
            {
                "area": area,
                "path": path,
                "change": change,
                "risk": risk,
                "time": timestamp,
                "status": status,
                "detail_extra": detail_extra,
            }
        ),
        "detail_extra": str(detail_extra or ""),
    }


def _placeholder_result_row() -> dict[str, object]:
    return {
        "area": "-",
        "path": ROOTS_GUARD_PLACEHOLDER_TEXT,
        "change": "-",
        "risk": "-",
        "time": "-",
        "status": "OK",
        "display": (ROOTS_GUARD_PLACEHOLDER_TEXT, "-", "-", "-", "OK"),
        "detail": ROOTS_GUARD_PLACEHOLDER_TEXT,
        "tag": "roots_ok",
    }


def _tag_for_risk(risk: str) -> str:
    return {
        "Kritisch": "roots_critical",
        "Warnung": "roots_warning",
        "Hinweis": "roots_hint",
    }.get(str(risk or ""), "roots_neutral")


def _tag_for_row(risk: str, status: str) -> str:
    status_label = str(status or "")
    if status_label in {"Fehlt", "Fehler", "Root nötig"}:
        return "roots_warning"
    if status_label == "Optional":
        return "roots_ok"
    if status_label == "Eingelesen" and str(risk or "") in {"", "-"}:
        return "roots_neutral"
    risk_tag = _tag_for_risk(risk)
    if risk_tag != "roots_neutral":
        return risk_tag
    return risk_tag


def _configure_roots_results_tags(table):
    try:
        table.tag_configure("roots_ok", foreground="#5f6770")
        table.tag_configure("roots_neutral", foreground="#77808a")
        table.tag_configure("roots_hint", foreground="#5aa07a")
        table.tag_configure("roots_warning", foreground="#c58a00")
        table.tag_configure("roots_critical", foreground="#d1495b")
    except Exception:
        pass


def _refresh_results_table(app, rows):
    table = getattr(app, "roots_baseline_guard_results_table", None)
    if table is None:
        return
    try:
        sorted_rows = _sorted_roots_result_rows(rows)
        app.roots_baseline_guard_result_meta = list(sorted_rows)
        _refresh_roots_signal_summary(app, sorted_rows)
        _configure_roots_results_tags(table)
        for item in table.get_children():
            table.delete(item)
        if not rows:
            placeholder = _placeholder_result_row()
            app.roots_baseline_guard_result_meta = [placeholder]
            _refresh_roots_signal_summary(app, [])
            table.insert("", "end", values=placeholder["display"], tags=("roots_ok",))
            return
        for row in sorted_rows:
            values = row.get("display") if isinstance(row, dict) else row
            tag = row.get("tag") if isinstance(row, dict) else None
            tags = (tag,) if tag else ()
            table.insert("", "end", values=values, tags=tags)
    except Exception:
        pass


def _serialize_result_rows(rows) -> list[dict[str, str]]:
    serialized = []
    for row in rows:
        if isinstance(row, dict):
            area = row.get("area", "-")
            path = row.get("path", "-")
            change = row.get("change", "-")
            risk = row.get("risk", "-")
            timestamp = row.get("time", "-")
            status = row.get("status", "-")
            detail_extra = row.get("detail_extra", "")
        else:
            path, change, risk, timestamp, status = row
            area = "-"
            detail_extra = ""
        serialized.append(
            {
                "area": str(area),
                "path": str(path),
                "change": str(change),
                "risk": str(risk),
                "time": str(timestamp),
                "status": str(status),
                "detail_extra": str(detail_extra or ""),
            }
        )
    return serialized


def _prepare_roots_capture_mode(app, reason: str) -> bool | None:
    use_root = _roots_root_mode_enabled(app)
    if not use_root:
        return False

    ensure_sudo = getattr(app, "ensure_sudo_session", None)
    if not callable(ensure_sudo) or not ensure_sudo(reason):
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Root-Freigabe abgebrochen. Vorgang nicht gestartet.",
        )
        _set_info_text(
            app,
            "Die Root-Freigabe wurde nicht erteilt. "
            "Geschützte Dateien werden daher nicht mit erhöhten Rechten eingelesen.",
        )
        return None
    return True


def _deserialize_result_rows(payload_rows) -> list[tuple[str, str, str, str, str]]:
    rows = []
    for item in payload_rows or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            _make_result_row(
                area=str(item.get("area", "-")),
                path=str(item.get("path", "-")),
                change=str(item.get("change", "-")),
                risk=str(item.get("risk", "-")),
                timestamp=str(item.get("time", "-")),
                status=str(item.get("status", "-")),
                detail_extra=str(item.get("detail_extra", "")),
            )
        )
    return rows


def _refresh_baseline_created_status(app, payload: dict[str, object] | None = None):
    payload = payload if isinstance(payload, dict) else _load_baseline_payload(app)
    created_at = str((payload or {}).get("created_at") or "").strip()
    _set_stringvar(
        app,
        "roots_baseline_created_var",
        (
            _tr(app, "roots_status_created_value", "Baseline erstellt am: {timestamp}").format(
                timestamp=created_at
            )
            if created_at
            else _tr(app, "roots_status_created_default", "Baseline erstellt am: noch nicht erstellt")
        ),
    )


def _refresh_baseline_updated_status(app, payload: dict[str, object] | None = None):
    payload = payload if isinstance(payload, dict) else _load_baseline_payload(app)
    updated_at = str((payload or {}).get("updated_at") or "").strip()
    _set_stringvar(
        app,
        "roots_baseline_updated_var",
        (
            _tr(app, "roots_status_updated_value", "Zuletzt aktualisiert am: {timestamp}").format(
                timestamp=updated_at
            )
            if updated_at
            else _tr(app, "roots_status_updated_default", "Zuletzt aktualisiert am: noch nicht aktualisiert")
        ),
    )


def _refresh_baseline_checked_status(app, payload: dict[str, object] | None = None):
    payload = payload if isinstance(payload, dict) else _load_baseline_payload(app)
    checked_at = str((payload or {}).get("last_check_at") or "").strip()
    _set_stringvar(
        app,
        "roots_baseline_checked_var",
        (
            _tr(app, "roots_status_checked_value", "Letzte Prüfung am: {timestamp}").format(
                timestamp=checked_at
            )
            if checked_at
            else _tr(app, "roots_status_checked_default", "Letzte Prüfung am: noch nicht durchgeführt")
        ),
    )


def _refresh_last_root_action_status(
    app, used_root: bool | None = None, payload: dict[str, object] | None = None
):
    if used_root is None:
        payload = payload if isinstance(payload, dict) else _load_baseline_payload(app)
        used_root = bool((payload or {}).get("last_action_used_root", False))
    _set_stringvar(
        app,
        "roots_last_root_action_var",
        _tr(app, "roots_status_last_root_action_value", "Letzte Aktion mit Root: {value}").format(
            value=_tr(app, "value_yes", "ja") if used_root else _tr(app, "value_no", "nein")
        ),
    )


def refresh_roots_baseline_guard_status(app):
    refresh_roots_baseline_guard_root_mode_status(app)
    payload = _load_baseline_payload(app)
    _refresh_baseline_created_status(app, payload)
    _refresh_baseline_updated_status(app, payload)
    _refresh_baseline_checked_status(app, payload)
    _refresh_last_root_action_status(app, payload=payload)
    created_at = str(payload.get("created_at") or "").strip()
    if created_at:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            app.tr(
                "roots_status_baseline_present",
                "Baseline available. Created: {timestamp}",
            ).format(timestamp=created_at),
        )
    else:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            app.tr("roots_status_no_baseline", "No baseline available yet."),
        )
    _set_info_text(
        app,
        app.tr(
            "roots_info_prepared",
            "Roots Baseline Guard is prepared as a manual working baseline. Select a comparison entry to view details here.",
        ),
    )


def clear_roots_baseline_guard_view(app):
    _ensure_app_tr(app)
    _refresh_baseline_created_status(app)
    _refresh_baseline_updated_status(app)
    _refresh_baseline_checked_status(app)
    _refresh_last_root_action_status(app)
    _refresh_results_table(app, [])
    history = getattr(app, "roots_baseline_guard_history_list", None)
    if history is not None:
        try:
            history.delete(0, "end")
        except Exception:
            pass
    whitelist_list = getattr(app, "roots_baseline_guard_whitelist_list", None)
    if whitelist_list is not None:
        try:
            whitelist_list.selected = ()
        except Exception:
            pass
    try:
        app.roots_baseline_guard_result_meta = []
    except Exception:
        pass
    try:
        app.roots_baseline_guard_info_path = ""
    except Exception:
        pass
    _set_stringvar(
        app,
        "roots_integrity_status_var",
        app.tr(
            "roots_status_no_critical_changes",
            "Keine kritischen Änderungen erkannt",
        ),
    )
    _set_stringvar(
        app,
        "roots_integrity_counts_var",
        app.tr(
            "roots_status_counts_default",
            "Kritisch: 0 | Warnungen: 0 | Hinweise: 0",
        ),
    )
    _set_stringvar(
        app,
        "roots_signal_summary_var",
        app.tr("roots_status_findings_default", "Funde: -"),
    )
    _set_stringvar(
        app,
        "roots_baseline_status_var",
        app.tr("roots_status_view_cleared", "Ansicht geleert."),
    )
    try:
        canvas = getattr(app, "roots_integrity_light", None)
        item_id = getattr(app, "roots_integrity_light_item", None)
        if canvas is not None and item_id is not None:
            canvas.itemconfig(item_id, fill="#2fbf71", outline="#2fbf71")
    except Exception:
        pass
    _set_info_text(
        app,
        app.tr(
            "roots_info_view_cleared",
            "Die Ansicht wurde geleert. Du kannst jetzt einen neuen Snapshot einlesen oder einen Vergleich laden.",
        ),
    )
    try:
        app.log("Roots Baseline Guard: Ansicht manuell geleert")
    except Exception:
        pass
    return True


def read_roots_baseline_guard_current_state(app):
    _ensure_app_tr(app)
    use_root = _prepare_roots_capture_mode(app, "Roots Baseline Guard Snapshot")
    if use_root is None:
        return False
    selected_areas = _selected_supported_areas(app)
    if not selected_areas:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Bitte mindestens einen unterstützten Bereich auswählen.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Einlesen übersprungen, keine unterstützten Bereiche ausgewählt."
            )
        except Exception:
            pass
        return False

    rows = []
    hints = 0
    now = _now_iso()
    for area in selected_areas:
        snapshot = _capture_area_snapshot(app, area, use_root=bool(use_root))
        for item in snapshot.get("items") or []:
            path = str(item.get("path") or "-")
            exists = bool(item.get("exists"))
            readable = bool(item.get("readable"))
            read_via_root = bool(item.get("read_via_root"))
            error_text = str(item.get("error") or "").strip()
            if error_text:
                change = "Zugriff / Fehler beim Einlesen"
                risk = "Hinweis"
                status = "Fehler"
                hints += 1
            elif not exists:
                if _is_optional_snapshot_path(path):
                    change = "Aktuell nicht vorhanden (optional)"
                    risk = "-"
                    status = "Optional"
                else:
                    change = "Aktuell nicht vorhanden"
                    risk = "Hinweis"
                    status = "Fehlt"
                    hints += 1
            elif readable or os.path.isdir(path):
                change = (
                    "Mit Root eingelesen"
                    if read_via_root
                    else "Aktueller Zustand eingelesen"
                )
                risk = "-"
                status = "Eingelesen"
            else:
                change = "Geschützt / Root erforderlich"
                risk = "Hinweis"
                status = "Root nötig"
                hints += 1
            rows.append(
                _make_result_row(
                    area=area,
                    path=path,
                    change=change,
                    risk=risk,
                    timestamp=now,
                    status=status,
                )
            )

    _refresh_results_table(app, rows)
    if hints > 0:
        _set_light_color(app, "#d4a017")
        _set_stringvar(
            app,
            "roots_integrity_status_var",
            app.tr("roots_status_state_read", "Zustand eingelesen"),
        )
    else:
        _set_light_color(app, "#2fbf71")
        _set_stringvar(
            app,
            "roots_integrity_status_var",
            app.tr("roots_status_state_read", "Zustand eingelesen"),
        )
    _set_stringvar(
        app,
        "roots_integrity_counts_var",
        app.tr(
            "roots_status_counts_with_hints",
            "Kritisch: 0 | Warnungen: 0 | Hinweise: {count}",
        ).format(count=hints),
    )
    _set_stringvar(
        app,
        "roots_baseline_status_var",
        (
            app.tr(
                "roots_status_state_read_with_root",
                "Aktueller Zustand mit Root eingelesen: {timestamp}",
            ).format(timestamp=now)
            if use_root
            else app.tr(
                "roots_status_state_read_without_root",
                "Aktueller Zustand eingelesen: {timestamp}",
            ).format(timestamp=now)
        ),
    )
    _refresh_last_root_action_status(app, used_root=bool(use_root))
    _set_info_text(
        app,
        (
            app.tr(
                "roots_info_state_read_with_root",
                "Snapshot mit Root eingelesen. Die Tabelle zeigt jetzt den aktuellen Snapshot der ausgewählten Bereiche, noch ohne Baseline-Vergleich.",
            )
            if use_root
            else app.tr(
                "roots_info_state_read",
                "Snapshot eingelesen. Die Tabelle zeigt jetzt den aktuellen Snapshot der ausgewählten Bereiche, noch ohne Baseline-Vergleich.",
            )
        ),
    )
    _refresh_history_list(
        app,
        [
            app.tr(
                "roots_history_last_baseline_value",
                "Last baseline: {timestamp}",
            ).format(
                timestamp=_load_baseline_payload(app).get("created_at")
                or app.tr("value_not_available", "not available")
            ),
            app.tr("roots_history_last_read", "Last read: {timestamp}").format(
                timestamp=now
            ),
            app.tr("roots_history_read_with_root", "Read with root: {value}").format(
                value=app.tr("value_yes", "YES") if use_root else app.tr("value_no", "NO")
            ),
            app.tr("roots_history_captured_entries", "Captured entries: {count}").format(
                count=len(rows)
            ),
            app.tr("roots_history_read_hints", "Read hints: {count}").format(
                count=hints
            ),
            app.tr("roots_history_covered_areas", "Covered areas: {areas}").format(
                areas=", ".join(selected_areas)
            ),
        ],
    )
    try:
        app.log(
            "Roots Baseline Guard: Aktueller Zustand "
            + ("mit Root " if use_root else "")
            + "eingelesen für "
            + ", ".join(selected_areas)
            + f" (eintraege={len(rows)}, hinweise={hints})."
        )
    except Exception:
        pass
    return True


def create_roots_baseline_guard_baseline(app):
    _ensure_app_tr(app)
    use_root = _prepare_roots_capture_mode(
        app, "Roots Baseline Guard Baseline erstellen"
    )
    if use_root is None:
        return False
    selected_areas = _selected_supported_areas(app)
    if not selected_areas:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Bitte mindestens einen unterstützten Bereich auswählen.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Keine unterstützten Bereiche für die erste Baseline ausgewählt."
            )
        except Exception:
            pass
        return False

    payload = _baseline_payload(app, selected_areas, use_root=bool(use_root))
    payload["last_action_used_root"] = bool(use_root)
    ok, err = safe_write_json(app.roots_baseline_guard_baseline_path, payload)
    if not ok:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Baseline konnte nicht gespeichert werden.",
        )
        try:
            app.log(f"Roots Baseline Guard: Baseline speichern fehlgeschlagen: {err}")
        except Exception:
            pass
        return False
    _refresh_baseline_created_status(app, payload)
    _refresh_baseline_updated_status(app, payload)
    _refresh_baseline_checked_status(app, payload)
    _refresh_last_root_action_status(app, payload=payload)

    _set_stringvar(
        app,
        "roots_baseline_status_var",
        (
            app.tr(
                "roots_status_baseline_created_with_root",
                "Baseline mit Root für {count} Bereich(e) erstellt.",
            ).format(count=len(selected_areas))
            if use_root
            else app.tr(
                "roots_status_baseline_created",
                "Baseline erstellt für {count} Bereich(e).",
            ).format(count=len(selected_areas))
        ),
    )
    _set_stringvar(
        app,
        "roots_integrity_status_var",
        app.tr(
            "roots_status_no_critical_changes",
            "Keine kritischen Änderungen erkannt",
        ),
    )
    _set_stringvar(
        app,
        "roots_integrity_counts_var",
        app.tr(
            "roots_status_counts_default",
            "Kritisch: 0 | Warnungen: 0 | Hinweise: 0",
        ),
    )
    _set_light_color(app, "#2fbf71")
    _refresh_results_table(app, [])
    _set_info_text(
        app,
        (
            app.tr(
                "roots_info_baseline_created_with_root",
                "Baseline wurde mit Root erstellt. Die erste manuelle Prüfung kann jetzt gestartet werden.",
            )
            if use_root
            else app.tr(
                "roots_info_baseline_created",
                "Baseline wurde erstellt. Die erste manuelle Prüfung kann jetzt gestartet werden.",
            )
        ),
    )
    _refresh_history_list(
        app,
        [
            app.tr(
                "roots_history_last_baseline_value",
                "Last baseline: {timestamp}",
            ).format(timestamp=payload.get("created_at", "-")),
            app.tr(
                "roots_history_last_check_default",
                "Last check: not performed yet",
            ),
            app.tr(
                "roots_history_baseline_created_with_root",
                "Baseline created with root: {value}",
            ).format(
                value=app.tr("value_yes", "YES") if use_root else app.tr("value_no", "NO")
            ),
            app.tr("roots_history_found_changes", "Found changes: {count}").format(
                count=0
            ),
            app.tr("roots_history_covered_areas", "Covered areas: {areas}").format(
                areas=", ".join(selected_areas)
            ),
        ],
    )
    try:
        app.log(
            "Roots Baseline Guard: Baseline manuell erstellt für "
            + ", ".join(selected_areas)
            + (" (mit Root)." if use_root else ".")
        )
    except Exception:
        pass
    return True


def check_roots_baseline_guard_baseline(app):
    _ensure_app_tr(app)
    use_root = _prepare_roots_capture_mode(app, "Roots Baseline Guard Baseline prüfen")
    if use_root is None:
        return False
    payload = _load_baseline_payload(app)
    areas = payload.get("areas") or {}
    if not areas:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Keine Baseline vorhanden. Bitte zuerst eine Baseline erstellen.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Prüfung übersprungen, keine Baseline vorhanden."
            )
        except Exception:
            pass
        return False

    rows = []
    critical = 0
    warnings = 0
    hints = 0
    now = _now_iso()

    for area in ROOTS_GUARD_SUPPORTED_AREAS:
        baseline_area = areas.get(area)
        if not isinstance(baseline_area, dict):
            continue
        current_area = _capture_area_snapshot(app, area, use_root=bool(use_root))
        old_items = {
            str(item.get("path") or ""): item
            for item in (baseline_area.get("items") or [])
            if str(item.get("path") or "").strip()
        }
        new_items = {
            str(item.get("path") or ""): item
            for item in (current_area.get("items") or [])
            if str(item.get("path") or "").strip()
        }
        for path in sorted(set(old_items) | set(new_items)):
            old_item = old_items.get(path, {"path": path})
            new_item = new_items.get(path, {"path": path})
            change_path, change_label, change_kind = _compare_item(
                old_item,
                new_item,
            )
            if not change_path:
                continue
            detail_extra = _signal_detail_text(old_item, new_item)
            risk = _severity_for_area(
                area,
                change_kind,
                path=change_path,
                change=change_label,
            )
            status = _status_for_severity(risk)
            rows.append(
                _make_result_row(
                    area=area,
                    path=change_path,
                    change=change_label,
                    risk=risk,
                    timestamp=now,
                    status=status,
                    detail_extra=detail_extra,
                )
            )
            if risk == "Kritisch":
                critical += 1
            elif risk == "Warnung":
                warnings += 1
            else:
                hints += 1

    previous_rows = _deserialize_result_rows(payload.get("last_check_results") or [])
    rows, ignored_by_known_system = _filter_known_system_rows(app, rows)
    rows, lowered_by_package_updates = _apply_package_update_trust(app, rows)
    rows, ignored_by_repeating_harmless = _filter_repeating_harmless_rows(
        app, rows, previous_rows
    )
    rows, ignored_by_whitelist = _filter_rows_with_whitelist(app, rows)
    critical = sum(1 for row in rows if str(row.get("risk")) == "Kritisch")
    warnings = sum(1 for row in rows if str(row.get("risk")) == "Warnung")
    hints = sum(1 for row in rows if str(row.get("risk")) == "Hinweis")
    _refresh_results_table(app, rows)

    if critical > 0:
        _set_light_color(app, "#d1495b")
        _set_stringvar(
            app, "roots_integrity_status_var", "Kritische Änderungen erkannt"
        )
    elif warnings > 0:
        _set_light_color(app, "#d4a017")
        _set_stringvar(app, "roots_integrity_status_var", "Änderungen erkannt")
    elif hints > 0:
        _set_light_color(app, "#d4a017")
        _set_stringvar(app, "roots_integrity_status_var", "Leichte Änderungen erkannt")
    else:
        _set_light_color(app, "#2fbf71")
        _set_stringvar(
            app, "roots_integrity_status_var", "Keine kritischen Änderungen erkannt"
        )

    _set_stringvar(
        app,
        "roots_integrity_counts_var",
        f"Kritisch: {critical} | Warnungen: {warnings} | Hinweise: {hints}",
    )
    _set_stringvar(
        app,
        "roots_baseline_status_var",
        (
            f"Prüfung mit Root abgeschlossen: {now}"
            if use_root
            else f"Prüfung abgeschlossen: {now}"
        ),
    )
    ignored_parts = []
    if ignored_by_known_system > 0:
        ignored_parts.append(f"{ignored_by_known_system} bekannte Systemänderung(en)")
    if ignored_by_repeating_harmless > 0:
        ignored_parts.append(
            f"{ignored_by_repeating_harmless} wiederkehrende harmlose Änderung(en)"
        )
    if lowered_by_package_updates > 0:
        ignored_parts.append(
            f"{lowered_by_package_updates} Paketupdate-/Dienst-Aenderung(en) niedriger eingestuft"
        )
    if ignored_by_whitelist > 0:
        ignored_parts.append(f"{ignored_by_whitelist} Whitelist-Eintrag/Einträge")
    ignored_suffix = ""
    if ignored_parts:
        ignored_suffix = " Ausgeblendet wurden: " + ", ".join(ignored_parts) + "."
    if rows:
        info_text = (
            app.tr(
                "roots_info_check_completed_with_results",
                "Prüfung abgeschlossen. Wähle einen Eintrag aus der Tabelle, um Pfad, Bereich und Bewertung im Detail zu prüfen.",
            )
        )
        info_text += ignored_suffix
        _set_info_text(app, info_text)
    else:
        info_text = app.tr(
            "roots_info_check_completed_no_changes",
            "Keine Änderungen erkannt. Die Baseline entspricht dem aktuellen Zustand.",
        )
        info_text += ignored_suffix
        _set_info_text(app, info_text)
    _refresh_history_list(
        app,
        [
            app.tr(
                "roots_history_last_baseline_value",
                "Last baseline: {timestamp}",
            ).format(timestamp=payload.get("created_at", "-")),
            app.tr("roots_history_last_check_value", "Last check: {timestamp}").format(
                timestamp=now
            ),
            app.tr("roots_history_check_with_root", "Check with root: {value}").format(
                value=app.tr("value_yes", "YES") if use_root else app.tr("value_no", "NO")
            ),
            app.tr("roots_history_found_changes", "Found changes: {count}").format(
                count=len(rows)
            ),
            app.tr(
                "roots_history_ignored_known_system",
                "Known system changes ignored: {count}",
            ).format(count=ignored_by_known_system),
            app.tr(
                "roots_history_lowered_package_updates",
                "Package updates rated lower: {count}",
            ).format(count=lowered_by_package_updates),
            app.tr(
                "roots_history_ignored_recurring_harmless",
                "Recurring harmless changes ignored: {count}",
            ).format(count=ignored_by_repeating_harmless),
            app.tr(
                "roots_history_ignored_by_whitelist",
                "Ignored by whitelist: {count}",
            ).format(count=ignored_by_whitelist),
            app.tr("roots_history_accepted_changes", "Accepted changes: {count}").format(
                count=0
            ),
        ],
    )
    payload["last_check_at"] = now
    payload["last_check_results"] = _serialize_result_rows(rows)
    payload["last_action_used_root"] = bool(use_root)
    try:
        safe_write_json(app.roots_baseline_guard_baseline_path, payload)
    except Exception:
        pass
    _refresh_baseline_checked_status(app, payload)
    _refresh_last_root_action_status(app, payload=payload)
    try:
        app.log(
            "Roots Baseline Guard: Prüfung "
            + ("mit Root " if use_root else "")
            + "abgeschlossen "
            f"(kritisch={critical}, warnungen={warnings}, hinweise={hints}, "
            f"bekannte_systemaenderungen_ignoriert={ignored_by_known_system}, "
            f"paketupdates_niedriger_eingestuft={lowered_by_package_updates}, "
            f"wiederkehrend_harmlos_ignoriert={ignored_by_repeating_harmless}, "
            f"whitelist_ignoriert={ignored_by_whitelist})."
        )
    except Exception:
        pass
    return True


def update_roots_baseline_guard_baseline(app):
    _ensure_app_tr(app)
    use_root = _prepare_roots_capture_mode(
        app, "Roots Baseline Guard Baseline aktualisieren"
    )
    if use_root is None:
        return False
    payload = _load_baseline_payload(app)
    areas_payload = payload.get("areas") or {}
    if not areas_payload:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Keine bestehende Baseline vorhanden. Bitte zuerst erstellen.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Baseline-Aktualisierung übersprungen, keine Baseline vorhanden."
            )
        except Exception:
            pass
        return False

    selected_areas = _selected_supported_areas(app)
    areas_to_update = selected_areas or [
        area for area in ROOTS_GUARD_SUPPORTED_AREAS if area in areas_payload
    ]
    if not areas_to_update:
        areas_to_update = list(ROOTS_GUARD_SUPPORTED_AREAS)

    for area in areas_to_update:
        payload.setdefault("areas", {})[area] = _capture_area_snapshot(
            app,
            area,
            use_root=bool(use_root),
        )

    now = _now_iso()
    payload["updated_at"] = now
    payload["last_action_used_root"] = bool(use_root)
    ok, err = safe_write_json(app.roots_baseline_guard_baseline_path, payload)
    if not ok:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Baseline konnte nicht aktualisiert werden.",
        )
        try:
            app.log(
                f"Roots Baseline Guard: Baseline aktualisieren fehlgeschlagen: {err}"
            )
        except Exception:
            pass
        return False
    _refresh_baseline_created_status(app, payload)
    _refresh_baseline_updated_status(app, payload)
    _refresh_baseline_checked_status(app, payload)
    _refresh_last_root_action_status(app, payload=payload)

    _set_stringvar(
        app,
        "roots_baseline_status_var",
        (
            app.tr(
                "roots_status_baseline_updated_with_root",
                "Baseline mit Root aktualisiert: {timestamp}",
            ).format(timestamp=now)
            if use_root
            else app.tr(
                "roots_status_baseline_updated",
                "Baseline aktualisiert: {timestamp}",
            ).format(timestamp=now)
        ),
    )
    _set_stringvar(
        app,
        "roots_integrity_status_var",
        app.tr(
            "roots_status_baseline_updated_not_checked",
            "Baseline aktualisiert, noch nicht geprüft",
        ),
    )
    _set_stringvar(
        app,
        "roots_integrity_counts_var",
        app.tr(
            "roots_status_counts_default",
            "Kritisch: 0 | Warnungen: 0 | Hinweise: 0",
        ),
    )
    _set_light_color(app, "#2fbf71")
    _refresh_results_table(app, [])
    _set_info_text(
        app,
        (
            app.tr(
                "roots_info_baseline_updated_with_root",
                "Die Baseline wurde mit Root auf den aktuellen Zustand aktualisiert. Bei Bedarf kann jetzt eine neue Prüfung gestartet werden.",
            )
            if use_root
            else app.tr(
                "roots_info_baseline_updated",
                "Die Baseline wurde auf den aktuellen Zustand aktualisiert. Bei Bedarf kann jetzt eine neue Prüfung gestartet werden.",
            )
        ),
    )
    _refresh_history_list(
        app,
        [
            app.tr(
                "roots_history_last_baseline_value",
                "Last baseline: {timestamp}",
            ).format(timestamp=payload.get("created_at", "-")),
            (
                app.tr(
                    "roots_history_baseline_updated_with_root",
                    "Baseline updated with root: {timestamp}",
                ).format(timestamp=now)
                if use_root
                else app.tr(
                    "roots_history_baseline_updated",
                    "Baseline updated: {timestamp}",
                ).format(timestamp=now)
            ),
            app.tr("roots_history_covered_areas", "Covered areas: {areas}").format(
                areas=", ".join(areas_to_update)
            ),
            app.tr("roots_history_last_check_value", "Last check: {timestamp}").format(
                timestamp=payload.get("last_check_at")
                or app.tr("value_not_available", "not available")
            ),
        ],
    )
    try:
        app.log(
            "Roots Baseline Guard: Baseline aktualisiert für "
            + ", ".join(areas_to_update)
            + (" (mit Root)." if use_root else ".")
        )
    except Exception:
        pass
    return True


def show_last_roots_baseline_guard_comparison(app):
    _ensure_app_tr(app)
    payload = _load_baseline_payload(app)
    _refresh_baseline_created_status(app, payload)
    _refresh_baseline_updated_status(app, payload)
    _refresh_baseline_checked_status(app, payload)
    _refresh_last_root_action_status(app, payload=payload)
    last_check_at = str(payload.get("last_check_at") or "").strip()
    rows = _deserialize_result_rows(payload.get("last_check_results") or [])
    if not last_check_at:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Noch kein gespeicherter Vergleich vorhanden.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Kein letzter Vergleich zum Anzeigen vorhanden."
            )
        except Exception:
            pass
        return False

    critical = sum(
        1
        for row in rows
        if (row.get("risk") if isinstance(row, dict) else row[2]) == "Kritisch"
    )
    warnings = sum(
        1
        for row in rows
        if (row.get("risk") if isinstance(row, dict) else row[2]) == "Warnung"
    )
    hints = sum(
        1
        for row in rows
        if (row.get("risk") if isinstance(row, dict) else row[2]) == "Hinweis"
    )
    _refresh_results_table(app, rows)
    if critical > 0:
        _set_light_color(app, "#d1495b")
        _set_stringvar(
            app, "roots_integrity_status_var", "Kritische Änderungen erkannt"
        )
    elif warnings > 0:
        _set_light_color(app, "#d4a017")
        _set_stringvar(app, "roots_integrity_status_var", "Änderungen erkannt")
    elif hints > 0:
        _set_light_color(app, "#d4a017")
        _set_stringvar(app, "roots_integrity_status_var", "Leichte Änderungen erkannt")
    else:
        _set_light_color(app, "#2fbf71")
        _set_stringvar(
            app, "roots_integrity_status_var", "Keine kritischen Änderungen erkannt"
        )

    _set_stringvar(
        app,
        "roots_integrity_counts_var",
        app.tr(
            "roots_status_counts_value",
            "Kritisch: {critical} | Warnungen: {warnings} | Hinweise: {hints}",
        ).format(critical=critical, warnings=warnings, hints=hints),
    )
    _set_stringvar(
        app,
        "roots_baseline_status_var",
        app.tr(
            "roots_status_last_comparison_loaded",
            "Letzter Vergleich geladen: {timestamp}",
        ).format(timestamp=last_check_at),
    )
    if rows:
        _set_info_text(
            app,
            app.tr(
                "roots_info_last_comparison_loaded_with_results",
                "Gespeicherter Vergleich geladen. Wähle einen Eintrag aus der Tabelle, um die Details anzuzeigen.",
            ),
        )
    else:
        _set_info_text(
            app,
            app.tr(
                "roots_info_last_comparison_loaded_no_changes",
                "Gespeicherter Vergleich geladen. Es wurden keine Änderungen gefunden.",
            ),
        )
    _refresh_history_list(
        app,
        [
            app.tr(
                "roots_history_last_baseline_value",
                "Last baseline: {timestamp}",
            ).format(timestamp=payload.get("created_at", "-")),
            app.tr("roots_history_last_check_value", "Last check: {timestamp}").format(
                timestamp=last_check_at
            ),
            app.tr("roots_history_found_changes", "Found changes: {count}").format(
                count=len(rows)
            ),
            app.tr("roots_history_accepted_changes", "Accepted changes: {count}").format(
                count=0
            ),
        ],
    )
    try:
        app.log(
            "Roots Baseline Guard: Letzter Vergleich geladen "
            f"({len(rows)} Einträge)."
        )
    except Exception:
        pass
    return True


def on_roots_baseline_guard_result_select(app, _event=None):
    table = _app_value(app, "roots_baseline_guard_results_table")
    if table is None:
        return
    try:
        selection = table.selection()
    except Exception:
        selection = ()
    if not selection:
        return
    try:
        index = int(table.index(selection[0]))
    except Exception:
        return
    rows = _app_list(app, "roots_baseline_guard_result_meta")
    if index < 0 or index >= len(rows):
        return
    row = rows[index]
    if isinstance(row, dict):
        _set_info_text(
            app,
            str(row.get("detail") or "Keine Details verfügbar."),
            path=str(row.get("path", "") or ""),
        )


def on_roots_baseline_guard_whitelist_select(app, _event=None):
    widget = _app_value(app, "roots_baseline_guard_whitelist_list")
    if widget is None:
        return
    try:
        selection = widget.curselection()
    except Exception:
        selection = ()
    if not selection:
        return
    try:
        index = int(selection[0])
    except Exception:
        return
    entries = _app_list(app, "roots_baseline_guard_whitelist_meta")
    if index < 0 or index >= len(entries):
        return
    item = entries[index]
    category = (
        str(item.get("category", "") or "").strip()
        or _roots_result_category_label(item)
        or "Allgemein"
    )
    detail = "\n".join(
        [
            "=== Roots Whitelist Eintrag ===",
            "",
            f"Kategorie: {category}",
            f"Bereich: {item.get('area', '-')}",
            f"Pfad: {item.get('path', '-')}",
            f"Änderung: {item.get('change', '-')}",
            f"Risiko: {item.get('risk', '-')}",
            f"Hinzugefügt: {item.get('added_at', '-')}",
        ]
    ).strip()
    _set_info_text(app, detail, path=str(item.get("path", "") or ""))


def open_selected_roots_baseline_guard_whitelist_entry(app, _event=None):
    widget = _app_value(app, "roots_baseline_guard_whitelist_list")
    table = _app_value(app, "roots_baseline_guard_results_table")
    if widget is None or table is None:
        return False
    try:
        selection = widget.curselection()
    except Exception:
        selection = ()
    if not selection:
        return False
    try:
        index = int(selection[0])
    except Exception:
        return False
    entries = _app_list(app, "roots_baseline_guard_whitelist_meta")
    if index < 0 or index >= len(entries):
        return False
    item = entries[index]
    target_area = str(item.get("area", "-"))
    target_path = str(item.get("path", "-"))
    target_change = str(item.get("change", "-"))
    rows = _app_list(app, "roots_baseline_guard_result_meta")
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        if (
            str(row.get("area", "-")) == target_area
            and str(row.get("path", "-")) == target_path
            and str(row.get("change", "-")) == target_change
        ):
            try:
                table.selection_set(row_index)
            except Exception:
                try:
                    table.selected = (row_index,)
                except Exception:
                    pass
            try:
                table.focus(row_index)
            except Exception:
                pass
            on_roots_baseline_guard_result_select(app)
            return True
    on_roots_baseline_guard_whitelist_select(app, _event=_event)
    return False


def _roots_chad_options(app) -> dict[str, bool]:
    vars_map = getattr(app, "roots_baseline_guard_chad_vars", {}) or {}
    options = {}
    for label, var in vars_map.items():
        try:
            options[str(label)] = bool(var.get())
        except Exception:
            options[str(label)] = False
    return options


def _roots_result_rows(app) -> list[dict[str, object]]:
    rows = _app_list(app, "roots_baseline_guard_result_meta")
    return [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("path") not in {"Noch keine Änderungen erkannt.", None}
    ]


def _roots_result_rows_for_chad(app, *, selected_only: bool) -> list[dict[str, object]]:
    rows = _roots_result_rows(app)
    if not selected_only:
        return rows
    table = _app_value(app, "roots_baseline_guard_results_table")
    if table is None:
        return []
    try:
        selection = list(table.selection())
    except Exception:
        selection = []
    if not selection:
        return []
    picked = []
    for item in selection:
        try:
            index = int(table.index(item))
        except Exception:
            continue
        if 0 <= index < len(rows):
            picked.append(rows[index])
    return picked


def _selected_roots_result_rows(app) -> list[dict[str, object]]:
    table = _app_value(app, "roots_baseline_guard_results_table")
    rows = _roots_result_rows(app)
    if table is None:
        return []
    try:
        selection = list(table.selection())
    except Exception:
        selection = []
    if not selection:
        return []
    selected = []
    for item in selection:
        try:
            index = int(table.index(item))
        except Exception:
            continue
        if 0 <= index < len(rows):
            selected.append(rows[index])
    return selected


def _selected_roots_result_parent_folder(app) -> str:
    rows = _selected_roots_result_rows(app)
    if not rows:
        return ""
    path = str(rows[0].get("path", "") or "").strip()
    if not path or path == "Noch keine Änderungen erkannt.":
        return ""
    if os.path.isdir(path):
        return path
    parent = os.path.dirname(path)
    if parent:
        return parent
    return path


def selected_roots_baseline_guard_result_path(app) -> str:
    rows = _selected_roots_result_rows(app)
    if not rows:
        return ""
    path = str(rows[0].get("path", "") or "").strip()
    if not path or path == "Noch keine Änderungen erkannt.":
        return ""
    return path


def open_roots_baseline_guard_info_path(app) -> bool:
    path = _roots_baseline_guard_info_path(app)
    if not path:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Kein Detailpfad zum Öffnen verfügbar.",
        )
        return False
    target = path if os.path.isdir(path) else (os.path.dirname(path) or path)
    if not _open_path_in_file_manager_safe(
        app,
        target,
        label="Roots Baseline Guard Ordner",
    ):
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Dateimanager-Funktion ist nicht verfügbar.",
        )
        return False
    return True


def get_roots_baseline_guard_analysis_text(app) -> str:
    rows = _roots_result_rows_for_chad(app, selected_only=True)
    if not rows:
        rows = _roots_result_rows(app)
    if not rows:
        return ""
    return _build_roots_chad_text(
        app, selected_only=bool(_roots_result_rows_for_chad(app, selected_only=True))
    )


def open_selected_roots_baseline_guard_parent_folder(app) -> bool:
    folder = _selected_roots_result_parent_folder(app)
    if not folder:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Kein gültiger Fundpfad zum Öffnen ausgewählt.",
        )
        return False

    if not _open_path_in_file_manager_safe(
        app,
        folder,
        label="Roots Baseline Guard Ordner",
    ):
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Dateimanager-Funktion ist nicht verfügbar.",
        )
        return False
    return True


def _filter_rows_with_whitelist(
    app, rows: list[dict[str, object]]
) -> tuple[list[dict[str, object]], int]:
    if not _roots_trust_option_enabled(app, "Benutzer-Whitelist berücksichtigen"):
        return list(rows), 0

    payload = _load_whitelist_payload(app)
    entries = [
        item for item in (payload.get("entries") or []) if isinstance(item, dict)
    ]
    if not entries:
        return list(rows), 0

    filtered = []
    ignored = 0
    for row in rows:
        match = any(
            str(item.get("area", "")) == str(row.get("area", ""))
            and str(item.get("path", "")) == str(row.get("path", ""))
            and str(item.get("change", "")) == str(row.get("change", ""))
            for item in entries
        )
        if match:
            ignored += 1
            continue
        filtered.append(row)
    return filtered, ignored


def _is_trust_protected_root_row(row: dict[str, object]) -> bool:
    category = _roots_result_category_label(row)
    if category in {
        "LD_PRELOAD",
        "shadow",
        "sudoers",
        "polkit",
        "sysctl",
        "kernel",
        "boot",
        "tmpfiles",
        "shell",
        "PAM",
        "UID0",
    }:
        return True
    if category == "authkeys":
        path = os.path.abspath(os.path.expanduser(str((row or {}).get("path") or "")))
        return path.startswith("/root/")
    return False


def _clone_row_with_risk(
    row: dict[str, object], new_risk: str, note: str = ""
) -> dict[str, object]:
    detail_extra = str(row.get("detail_extra") or "").strip()
    if note and note not in detail_extra:
        detail_extra = f"{detail_extra}\n\n{note}".strip() if detail_extra else note
    return _make_result_row(
        area=str(row.get("area") or "-"),
        path=str(row.get("path") or "-"),
        change=str(row.get("change") or "-"),
        risk=new_risk,
        timestamp=str(row.get("time") or "-"),
        status=_status_for_severity(new_risk),
        detail_extra=detail_extra,
    )


def _is_package_managed_style_root_path(category: str, path: str) -> bool:
    normalized = os.path.abspath(os.path.expanduser(str(path or "")))
    basename = os.path.basename(normalized)
    if category == "SSH":
        return (
            basename in {"sshd_config", "ssh_config"}
            or "/ssh/sshd_config.d/" in normalized
        )
    if category == "systemd":
        return (
            "/systemd/system/" in normalized
            or normalized.endswith("/systemd/system")
            or "/systemd/user/" in normalized
        )
    if category == "cron":
        return (
            any(
                part in normalized
                for part in (
                    "/cron.d/",
                    "/cron.hourly/",
                    "/cron.daily/",
                    "/cron.weekly/",
                    "/cron.monthly/",
                )
            )
            or basename == "crontab"
        )
    if category == "polkit":
        return "/polkit-1/" in normalized
    if category == "sysctl":
        return basename == "sysctl.conf" or "/sysctl.d/" in normalized
    if category == "kernel":
        return (
            basename == "modules"
            or "/modprobe.d/" in normalized
            or "/modules-load.d/" in normalized
        )
    if category == "boot":
        return basename == "grub.cfg" and (
            "/boot/grub/" in normalized or "/boot/grub2/" in normalized
        )
    if category == "tmpfiles":
        return "/usr/lib/tmpfiles.d/" in normalized
    if category == "shell":
        return basename in {"profile", "environment", "bash.bashrc"}
    return False


def _apply_package_update_trust(
    app, rows: list[dict[str, object]]
) -> tuple[list[dict[str, object]], int]:
    if not _roots_trust_option_enabled(app, "Paketupdates niedriger einstufen"):
        return list(rows), 0

    lowered = 0
    adjusted = []
    lowerable_changes = {
        "Inhalt geändert",
        "Dateirechte geändert",
        "Dateigröße geändert",
        "Zeitstempel geändert",
        "Zugriff / Fehlerstatus geändert",
    }
    for row in rows:
        category = _roots_result_category_label(row)
        change = str(row.get("change") or "")
        risk = str(row.get("risk") or "")
        path = str(row.get("path") or "")
        generic_package_style_change = (
            category
            in {
                "SSH",
                "systemd",
                "cron",
                "polkit",
                "sysctl",
                "kernel",
                "boot",
                "tmpfiles",
                "shell",
            }
            and change in lowerable_changes
            and risk in {"Kritisch", "Warnung", "Hinweis"}
            and _is_package_managed_style_root_path(category, path)
        )
        if generic_package_style_change and (
            category in {"SSH", "systemd", "cron"}
            or not _is_trust_protected_root_row(row)
            or _is_package_managed_style_root_path(category, path)
        ):
            if (
                category in {"polkit", "sysctl", "kernel", "boot", "tmpfiles", "shell"}
                and risk == "Kritisch"
            ):
                new_risk = "Warnung"
            elif risk == "Warnung":
                new_risk = "Hinweis"
            else:
                new_risk = risk
            if new_risk != risk:
                lowered += 1
                adjusted.append(
                    _clone_row_with_risk(
                        row,
                        new_risk,
                        "Trust-Hinweis: Als moegliche Paket-/Dienst-Aenderung niedriger eingestuft.",
                    )
                )
                continue
        adjusted.append(row)
    return adjusted, lowered


def _filter_known_system_rows(
    app, rows: list[dict[str, object]]
) -> tuple[list[dict[str, object]], int]:
    if not _roots_trust_option_enabled(app, "Bekannte Systemänderungen ignorieren"):
        return list(rows), 0

    filtered = []
    ignored = 0
    for row in rows:
        path = str(row.get("path", ""))
        area = str(row.get("area", ""))
        category = _roots_result_category_label(row)
        change = str(row.get("change") or "")
        if area == "DNS / Hosts" and os.path.basename(path) == "resolv.conf":
            ignored += 1
            continue
        if (
            category in {"polkit", "sysctl", "kernel", "boot", "tmpfiles", "shell"}
            and change in {"Zeitstempel geändert", "Zugriff / Fehlerstatus geändert"}
            and _is_package_managed_style_root_path(category, path)
        ):
            ignored += 1
            continue
        filtered.append(row)
    return filtered, ignored


def _filter_repeating_harmless_rows(
    app, rows: list[dict[str, object]], previous_rows: list[dict[str, object]]
) -> tuple[list[dict[str, object]], int]:
    if not _roots_trust_option_enabled(
        app, "Wiederkehrende harmlose Änderungen minimieren"
    ):
        return list(rows), 0

    previous_hint_keys = {
        (
            str(row.get("area", "")),
            str(row.get("path", "")),
            str(row.get("change", "")),
        )
        for row in previous_rows
        if str(row.get("risk", "")) == "Hinweis"
    }
    if not previous_hint_keys:
        return list(rows), 0

    filtered = []
    ignored = 0
    for row in rows:
        row_key = (
            str(row.get("area", "")),
            str(row.get("path", "")),
            str(row.get("change", "")),
        )
        if (
            str(row.get("risk", "")) == "Hinweis"
            and row_key in previous_hint_keys
            and not _is_trust_protected_root_row(row)
        ):
            ignored += 1
            continue
        filtered.append(row)
    return filtered, ignored


def _roots_prompt_profile_lines(options: dict[str, bool]) -> list[str]:
    lines = []
    if options.get("Nur kritische Änderungen analysieren"):
        lines.append("- Fokus: Nur kritische Änderungen priorisiert bewerten.")
    if options.get("Anfängerfreundlich erklären"):
        lines.append(
            "- Erklärungstiefe: Anfängerfreundlich und ohne unnötigen Fachjargon."
        )
    if options.get("Handlungsempfehlungen anzeigen"):
        lines.append("- Ausgabe: Konkrete Handlungsempfehlungen ergänzen.")
    if options.get("Technische Details anzeigen"):
        lines.append("- Ausgabe: Technische Details und Linux-Kontext mit aufnehmen.")
    if options.get("Reparaturvorschläge anzeigen"):
        lines.append("- Ausgabe: Vorsichtige Reparatur- oder Prüfpfade vorschlagen.")
    return lines


def _extract_context_lines_from_detail(detail_extra: str) -> list[str]:
    text = str(detail_extra or "").strip()
    if not text:
        return []
    lines = [line.rstrip() for line in text.splitlines()]
    context_lines: list[str] = []
    in_context = False
    for line in lines:
        stripped = line.strip()
        if stripped == "Einordnung:":
            in_context = True
            continue
        if not in_context:
            continue
        if not stripped:
            continue
        if stripped.startswith("- "):
            context_lines.append(stripped[2:].strip())
        else:
            context_lines.append(stripped)
    return [line for line in context_lines if line]


def _build_roots_chad_text(app, *, selected_only: bool) -> str:
    options = _roots_chad_options(app)
    rows = _roots_result_rows_for_chad(app, selected_only=selected_only)
    if options.get("Nur kritische Änderungen analysieren"):
        rows = [row for row in rows if row.get("risk") == "Kritisch"]

    if not rows:
        return ""

    lines = ["Roots Baseline Guard", "====================", ""]
    lines.append("Kontext:")
    lines.append(
        f"- Status: {getattr(app, 'roots_integrity_status_var', None).get() if getattr(app, 'roots_integrity_status_var', None) else '-'}"
    )
    lines.append(
        f"- Übersicht: {getattr(app, 'roots_integrity_counts_var', None).get() if getattr(app, 'roots_integrity_counts_var', None) else '-'}"
    )
    status_var = getattr(app, "roots_baseline_status_var", None)
    if status_var is not None:
        try:
            lines.append(f"- Baseline-Status: {status_var.get()}")
        except Exception:
            pass
    lines.append(
        f"- Modus: {'Nur ausgewählter Eintrag' if selected_only else 'Aktuelle Vergleichsliste'}"
    )
    lines.append("")

    profile_lines = _roots_prompt_profile_lines(options)
    if profile_lines:
        lines.append("Analyseprofil:")
        lines.extend(profile_lines)
    lines.append("")

    lines.append("Vergleichseinträge:")
    for idx, row in enumerate(rows, start=1):
        detail_extra = str(row.get("detail_extra") or "").strip()
        context_lines = _extract_context_lines_from_detail(detail_extra)
        lines.extend(
            [
                f"[{idx}] Bereich: {row.get('area', '-')}",
                f"Pfad: {row.get('path', '-')}",
                f"Änderung: {row.get('change', '-')}",
                f"Risiko: {row.get('risk', '-')}",
                f"Zeit: {row.get('time', '-')}",
                f"Status: {row.get('status', '-')}",
            ]
        )
        if context_lines:
            lines.append("Sicherheitskontext:")
            lines.extend(f"- {line}" for line in context_lines)
        if detail_extra:
            lines.append("Details:")
            lines.extend(detail_extra.splitlines())
        lines.append("")

    lines.append(
        "Bitte diese Änderungen inhaltlich bewerten, priorisieren und den Sicherheitskontext aus der Einordnung mit berücksichtigen."
    )
    return "\n".join(lines).strip()


def load_roots_baseline_guard_demo_cases(app):
    _ensure_app_tr(app)
    now = _now_iso()

    def demo_detail(*signals: str) -> str:
        return _signal_detail_text({"signals": []}, {"signals": list(signals)})

    rows = [
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/ld.so.preload",
            change="LD_PRELOAD-Eintrag erkannt: /tmp/evil.so",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("ld_preload:entry:/tmp/evil.so"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/pam.d/common-auth",
            change="PAM-Fund aktiviert: pam_permit.so im auth-Stack",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("pam:permit_auth"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/polkit-1/rules.d/49-demo.rules",
            change="Polkit-Fund aktiviert: ResultAny=yes",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("polkit:result_any_yes", "polkit:add_rule"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/sysctl.d/99-demo.conf",
            change="Sysctl-Fund aktiviert: accept_source_route=1",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("sysctl:net.ipv4.conf.all.accept_source_route=1"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/modprobe.d/evil.conf",
            change="Kernel-Modul-Fund aktiviert: Shell-Start",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("kernel:shell_exec", "kernel:network_fetch"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/default/grub",
            change="Boot-Fund aktiviert: init=/bin/sh",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("boot:init_shell", "boot:selinux_off"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/tmpfiles.d/demo.conf",
            change="Tmpfiles-Fund aktiviert: sensitiver Pfad",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("tmpfiles:sensitive_target", "tmpfiles:symlink"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/profile",
            change="Shell-Fund aktiviert: LD_PRELOAD",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("shell:ld_preload", "shell:path_tmp"),
        ),
        _make_result_row(
            area="Kritische Systemdateien",
            path="/etc/sudoers.d/admin",
            change="Sudo-Regel aktiviert: ALL=(ALL) ALL",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("sudoers:full_access", "sudoers:setenv"),
        ),
        _make_result_row(
            area="SSH Schlüssel / authorized_keys",
            path="/root/.ssh/authorized_keys",
            change="Schwacher SSH-Schluessel erkannt: ssh-rsa legacy-admin@host",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("authkeys:weak_algo:ssh-rsa:legacy-admin@host"),
        ),
        _make_result_row(
            area="Autostart / systemd / cron",
            path="/etc/systemd/system/backup-helper.service",
            change="Systemd-Fund aktiviert: Shell-Start",
            risk="Kritisch",
            timestamp=now,
            status=_status_for_severity("Kritisch"),
            detail_extra=demo_detail("systemd:shell_exec", "systemd:network_fetch"),
        ),
        _make_result_row(
            area="Autostart / systemd / cron",
            path="/etc/cron.d/remote-maintenance",
            change="Cron-Fund aktiviert: @reboot",
            risk="Warnung",
            timestamp=now,
            status=_status_for_severity("Warnung"),
            detail_extra=demo_detail("cron:at_reboot"),
        ),
        _make_result_row(
            area="SSH Konfiguration",
            path="/etc/ssh/sshd_config",
            change="SSH-Option aktiviert: PasswordAuthentication yes",
            risk="Warnung",
            timestamp=now,
            status=_status_for_severity("Warnung"),
            detail_extra=demo_detail("ssh:password_auth_yes"),
        ),
    ]

    critical = sum(1 for row in rows if str(row.get("risk")) == "Kritisch")
    warnings = sum(1 for row in rows if str(row.get("risk")) == "Warnung")
    hints = sum(1 for row in rows if str(row.get("risk")) == "Hinweis")
    _refresh_results_table(app, rows)
    _set_light_color(app, "#d1495b" if critical else "#d4a017")
    _set_stringvar(
        app,
        "roots_integrity_status_var",
        app.tr("roots_status_demo_loaded", "Demo-Funde geladen"),
    )
    _set_stringvar(
        app,
        "roots_integrity_counts_var",
        app.tr(
            "roots_status_counts_value",
            "Kritisch: {critical} | Warnungen: {warnings} | Hinweise: {hints}",
        ).format(critical=critical, warnings=warnings, hints=hints),
    )
    _set_stringvar(
        app,
        "roots_baseline_status_var",
        app.tr("roots_status_demo_loaded_at", "Demo-Fälle geladen: {timestamp}").format(
            timestamp=now
        ),
    )
    _set_info_text(
        app,
        app.tr(
            "roots_info_demo_mode",
            "Demo-Modus aktiv. Diese Einträge sind simulierte Praxisfälle für Layout, Interaktionsfluss, Trust-Verhalten und Chad-Erklärungen. Es wurden keine echten Systemdateien verändert oder eingelesen.",
        ),
    )
    _refresh_history_list(
        app,
        [
            app.tr("roots_history_demo_mode_active", "Demo-Modus: aktiv"),
            app.tr("roots_history_loaded_at", "Geladen am: {timestamp}").format(
                timestamp=now
            ),
            app.tr("roots_history_demo_findings", "Demo-Funde: {count}").format(
                count=len(rows)
            ),
            app.tr("roots_history_critical_count", "Kritisch: {count}").format(
                count=critical
            ),
            app.tr("roots_history_warning_count", "Warnungen: {count}").format(
                count=warnings
            ),
            app.tr("roots_history_notice_count", "Hinweise: {count}").format(
                count=hints
            ),
            app.tr("roots_history_source_internal_cases", "Quelle: interne Praxisfälle"),
            app.tr("roots_history_real_system_check", "Echter Systemcheck: {value}").format(
                value=app.tr("value_no", "nein")
            ),
        ],
    )
    try:
        app.log(
            "Roots Baseline Guard: Demo-Faelle geladen "
            f"(kritisch={critical}, warnungen={warnings}, hinweise={hints})."
        )
    except Exception:
        pass
    return True


def analyze_roots_baseline_guard_with_chad(app):
    text = _build_roots_chad_text(app, selected_only=False)
    if not text:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Keine geeigneten Änderungen für die Chad Analyse vorhanden.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Keine Vergleichseinträge für Chad Analyse vorhanden."
            )
        except Exception:
            pass
        return False
    app.prepare_chad_analysis("Roots Baseline Guard Analyse", text)
    return True


def explain_selected_roots_baseline_guard_change(app):
    text = _build_roots_chad_text(app, selected_only=True)
    if not text:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Bitte zuerst einen Vergleichseintrag auswählen.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Keine Auswahl für 'Änderung erklären' vorhanden."
            )
        except Exception:
            pass
        return False
    app.prepare_chad_analysis("Roots Baseline Guard Änderung erklären", text)
    return True


def add_selected_roots_baseline_guard_change_to_whitelist(app):
    selected_rows = _selected_roots_result_rows(app)
    if not selected_rows:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Bitte zuerst einen Vergleichseintrag für die Whitelist auswählen.",
        )
        try:
            app.log(
                "Roots Baseline Guard: Keine Auswahl zum Hinzufügen zur Whitelist vorhanden."
            )
        except Exception:
            pass
        return False

    payload = _load_whitelist_payload(app)
    entries = list(payload.get("entries") or [])
    added = 0
    for row in selected_rows:
        category = _roots_result_category_label(row) or "Allgemein"
        candidate = {
            "area": str(row.get("area", "-")),
            "path": str(row.get("path", "-")),
            "change": str(row.get("change", "-")),
            "risk": str(row.get("risk", "-")),
            "category": category,
            "added_at": _now_iso(),
        }
        exists = any(
            str(item.get("area", "")) == candidate["area"]
            and str(item.get("path", "")) == candidate["path"]
            and str(item.get("change", "")) == candidate["change"]
            for item in entries
            if isinstance(item, dict)
        )
        if exists:
            continue
        entries.append(candidate)
        added += 1

    payload["entries"] = entries
    ok, err = _save_whitelist_payload(app, payload)
    if not ok:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Whitelist konnte nicht gespeichert werden.",
        )
        try:
            app.log(f"Roots Baseline Guard: Whitelist speichern fehlgeschlagen: {err}")
        except Exception:
            pass
        return False

    _set_stringvar(
        app,
        "roots_baseline_status_var",
        f"Whitelist aktualisiert: {added} Eintrag/Einträge hinzugefügt.",
    )
    _set_info_text(
        app,
        "Die Auswahl wurde in die manuelle Roots-Whitelist übernommen. "
        "Die Whitelist hat aktuell noch keine automatische Filterwirkung und dient als Arbeitsbasis.",
    )
    try:
        app.log(
            "Roots Baseline Guard: "
            f"{added} Eintrag/Einträge zur manuellen Whitelist hinzugefügt."
        )
    except Exception:
        pass
    return True


def remove_selected_roots_baseline_guard_change_from_whitelist(app):
    _ensure_app_tr(app)
    payload = _load_whitelist_payload(app)
    entries = [
        item for item in (payload.get("entries") or []) if isinstance(item, dict)
    ]
    if not entries:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            app.tr(
                "roots_whitelist_remove_empty_status",
                "Whitelist ist leer. Es konnten keine Einträge entfernt werden.",
            ),
        )
        _set_info_text(
            app,
            app.tr(
                "roots_whitelist_remove_empty_info",
                "Die Roots-Whitelist ist aktuell leer. Es gibt nichts zu entfernen.",
            ),
        )
        return False

    selected_whitelist_entries = []
    whitelist_widget = _app_value(app, "roots_baseline_guard_whitelist_list")
    whitelist_meta = _app_list(app, "roots_baseline_guard_whitelist_meta")
    if whitelist_widget is not None and whitelist_meta:
        try:
            whitelist_selection = whitelist_widget.curselection()
        except Exception:
            whitelist_selection = ()
        for item in whitelist_selection:
            try:
                index = int(item)
            except Exception:
                continue
            if 0 <= index < len(whitelist_meta):
                selected_whitelist_entries.append(whitelist_meta[index])

    selected_keys = set()
    for item in selected_whitelist_entries:
        selected_keys.add(
            (
                str(item.get("area", "-")),
                str(item.get("path", "-")),
                str(item.get("change", "-")),
                str(item.get("added_at", "-")),
            )
        )

    if not selected_keys:
        selected_rows = _selected_roots_result_rows(app)
        if not selected_rows:
            _set_stringvar(
                app,
                "roots_baseline_status_var",
                app.tr(
                    "roots_whitelist_remove_select_status",
                    "Bitte zuerst einen Vergleichseintrag oder einen Whitelist-Eintrag zum Entfernen auswählen.",
                ),
            )
            try:
                app.log(
                    app.tr(
                        "roots_whitelist_remove_log_no_selection",
                        "Roots Baseline Guard: Keine Auswahl zum Entfernen aus der Whitelist vorhanden.",
                    )
                )
            except Exception:
                pass
            return False
        for row in selected_rows:
            selected_keys.add(
                (
                    str(row.get("area", "-")),
                    str(row.get("path", "-")),
                    str(row.get("change", "-")),
                    None,
                )
            )

    kept_entries = []
    removed = 0
    for item in entries:
        item_key_exact = (
            str(item.get("area", "")),
            str(item.get("path", "")),
            str(item.get("change", "")),
            str(item.get("added_at", "-")),
        )
        item_key_loose = (
            str(item.get("area", "")),
            str(item.get("path", "")),
            str(item.get("change", "")),
            None,
        )
        if item_key_exact in selected_keys or item_key_loose in selected_keys:
            removed += 1
            continue
        kept_entries.append(item)

    if removed == 0:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            app.tr(
                "roots_whitelist_remove_no_match_status",
                "Für die aktuelle Auswahl wurde kein passender Whitelist-Eintrag gefunden.",
            ),
        )
        _set_info_text(
            app,
            app.tr(
                "roots_whitelist_remove_no_match_info",
                "Für die aktuelle Auswahl wurde kein passender Eintrag in der Roots-Whitelist gefunden.",
            ),
        )
        return False

    payload["entries"] = kept_entries
    ok, err = _save_whitelist_payload(app, payload)
    if not ok:
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            app.tr(
                "roots_whitelist_remove_update_failed_status",
                "Whitelist konnte nicht aktualisiert werden.",
            ),
        )
        try:
            app.log(f"Roots Baseline Guard: Whitelist entfernen fehlgeschlagen: {err}")
        except Exception:
            pass
        return False

    _set_stringvar(
        app,
        "roots_baseline_status_var",
        app.tr(
            "roots_whitelist_remove_updated_status",
            "Whitelist aktualisiert: {count} Eintrag/Einträge entfernt.",
        ).format(count=removed),
    )
    _set_info_text(
        app,
        app.tr(
            "roots_whitelist_remove_updated_info",
            "Die Auswahl wurde aus der manuellen Roots-Whitelist entfernt. Beim nächsten Prüflauf wird die Änderung nicht mehr als freigegeben behandelt.",
        ),
    )
    _refresh_whitelist_list(app, kept_entries)
    try:
        app.log(
            "Roots Baseline Guard: "
            f"{removed} Eintrag/Einträge aus der manuellen Whitelist entfernt."
        )
    except Exception:
        pass
    return True


def show_roots_baseline_guard_whitelist(app):
    payload = _load_whitelist_payload(app)
    entries = [
        item for item in (payload.get("entries") or []) if isinstance(item, dict)
    ]
    if not entries:
        _refresh_whitelist_list(app, [])
        _set_stringvar(
            app,
            "roots_baseline_status_var",
            "Whitelist vorhanden, aber noch leer.",
        )
        _set_info_text(
            app,
            "=== Roots Whitelist ===\n\nNoch keine Einträge gespeichert.",
        )
        try:
            app.log("Roots Baseline Guard: Whitelist ist aktuell leer.")
        except Exception:
            pass
        return True

    categorized_entries = []
    for item in entries:
        category = (
            str(item.get("category", "") or "").strip()
            or _roots_result_category_label(item)
            or "Allgemein"
        )
        categorized_entries.append((category, item))
    categorized_entries.sort(
        key=lambda pair: (
            {
                "LD_PRELOAD": 0,
                "shadow": 1,
                "sudoers": 2,
                "polkit": 3,
                "sysctl": 4,
                "kernel": 5,
                "boot": 6,
                "shell": 7,
                "PAM": 8,
                "UID0": 9,
                "authkeys": 10,
                "SSH": 11,
                "systemd": 12,
                "cron": 13,
                "DNS": 14,
                "Allgemein": 15,
            }.get(pair[0], 11),
            str(pair[1].get("path", "")),
            str(pair[1].get("change", "")),
        )
    )
    sorted_entries = [item for _category, item in categorized_entries]
    _refresh_whitelist_list(app, sorted_entries)

    lines = ["=== Roots Whitelist ===", ""]
    last_category = None
    for idx, (category, item) in enumerate(categorized_entries, start=1):
        if category != last_category:
            if last_category is not None:
                lines.append("")
            lines.append(f"--- {category} ---")
            last_category = category
        lines.extend(
            [
                f"[{idx}] Bereich: {item.get('area', '-')}",
                f"Pfad: {item.get('path', '-')}",
                f"Änderung: {item.get('change', '-')}",
                f"Risiko: {item.get('risk', '-')}",
                f"Hinzugefügt: {item.get('added_at', '-')}",
                "",
            ]
        )
    _set_stringvar(
        app,
        "roots_baseline_status_var",
        f"Whitelist geladen: {len(entries)} Eintrag/Einträge.",
    )
    _set_info_text(app, "\n".join(lines).strip())
    try:
        app.log(
            "Roots Baseline Guard: Whitelist angezeigt "
            f"({len(entries)} Eintrag/Einträge)."
        )
    except Exception:
        pass
    return True
