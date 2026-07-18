#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import tempfile

RKHUNTER_CONFIG_PATH = "/etc/rkhunter.conf"
RKHUNTER_BACKUP_PATH = "/etc/rkhunter.conf.netmon.bak"
RKHUNTER_PROP_DB_PATH = "/var/lib/rkhunter/db/rkhunter.dat"
RKHUNTER_PROP_DB_BACKUP_PATH = "/var/lib/rkhunter/db/rkhunter.dat.netmon.bak"

REPAIR_TARGETS = {
    "UPDATE_MIRRORS": "1",
    "MIRRORS_MODE": "0",
}

TRUSTED_WEB_CMD_PREFIXES = ("/usr/bin/", "/bin/", "/usr/local/bin/")


def _preferred_web_cmd():
    for candidate in ("wget", "curl"):
        resolved = shutil.which(candidate)
        if resolved and any(
            str(resolved).startswith(prefix) for prefix in TRUSTED_WEB_CMD_PREFIXES
        ):
            return resolved
    return ""


def _normalize_allowed_path(path, *, allow_backup=False, allow_prop_db=False):
    candidate = os.path.realpath(str(path or "").strip())
    allowed = {os.path.realpath(RKHUNTER_CONFIG_PATH)}
    if allow_backup:
        allowed.add(os.path.realpath(RKHUNTER_BACKUP_PATH))
    if allow_prop_db:
        allowed.update(
            {
                os.path.realpath(RKHUNTER_PROP_DB_PATH),
                os.path.realpath(RKHUNTER_PROP_DB_BACKUP_PATH),
            }
        )
    if not candidate or candidate not in allowed:
        return ""
    return candidate


def _run_cmd(args, timeout=15):
    try:
        proc = subprocess.run(
            list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, (proc.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "Command timed out"
    except Exception as exc:
        return 1, f"Command failed: {exc}"


def is_rkhunter_installed():
    return shutil.which("rkhunter") is not None


def run_rkhunter_update(timeout=600):
    return _run_cmd(["sudo", "-n", "rkhunter", "--update"], timeout=timeout)


def run_rkhunter_propupd(timeout=600):
    backup_rc, backup_out = backup_property_database()
    if backup_rc != 0:
        return backup_rc, backup_out or "rkhunter property database backup failed."
    propupd_rc, propupd_out = _run_cmd(
        ["sudo", "-n", "rkhunter", "--propupd"], timeout=timeout
    )
    if propupd_out:
        return propupd_rc, f"{backup_out}\n{propupd_out}".strip()
    return propupd_rc, backup_out


def backup_property_database(
    db_path=RKHUNTER_PROP_DB_PATH,
    backup_path=RKHUNTER_PROP_DB_BACKUP_PATH,
):
    safe_db_path = _normalize_allowed_path(db_path, allow_prop_db=True)
    safe_backup_path = _normalize_allowed_path(backup_path, allow_prop_db=True)
    if not safe_db_path or not safe_backup_path:
        return 1, "Nicht erlaubter rkhunter-Datenbankpfad."
    return _run_cmd(
        ["sudo", "-n", "cp", "-a", safe_db_path, safe_backup_path], timeout=20
    )


def restore_property_database(
    db_path=RKHUNTER_PROP_DB_PATH,
    backup_path=RKHUNTER_PROP_DB_BACKUP_PATH,
):
    safe_db_path = _normalize_allowed_path(db_path, allow_prop_db=True)
    safe_backup_path = _normalize_allowed_path(backup_path, allow_prop_db=True)
    if not safe_db_path or not safe_backup_path:
        return 1, "Nicht erlaubter rkhunter-Datenbankpfad."
    exists_rc, _exists_out = _run_cmd(
        ["sudo", "-n", "test", "-f", safe_backup_path], timeout=10
    )
    if exists_rc != 0:
        return (
            2,
            "Kein NetMon-Backup der RKHunter-Referenzdatenbank vorhanden. "
            "Ein Widerruf ist erst möglich, nachdem eine Referenz mit dieser "
            "NetMon-Version übernommen wurde.",
        )
    return _run_cmd(
        ["sudo", "-n", "cp", "-a", safe_backup_path, safe_db_path], timeout=20
    )


def update_after_repair(timeout=600):
    return run_rkhunter_update(timeout=timeout)


def detect_update_failure(output):
    text = str(output or "").strip().lower()
    if not text:
        return False

    markers = [
        "mirrors.dat does not exist",
        "unable to determine the latest version number",
        "update failed",
        "invalid web_cmd configuration option",
    ]
    if any(marker in text for marker in markers):
        return True
    return "web_cmd" in text


def backup_config(
    config_path=RKHUNTER_CONFIG_PATH,
    backup_path=RKHUNTER_BACKUP_PATH,
):
    if not config_path or not backup_path:
        return False, "config_path oder backup_path fehlt"
    safe_config_path = _normalize_allowed_path(config_path)
    safe_backup_path = _normalize_allowed_path(backup_path, allow_backup=True)
    if not safe_config_path or not safe_backup_path:
        return False, "Nicht erlaubter rkhunter-Pfad."
    return _run_cmd(
        ["sudo", "-n", "cp", safe_config_path, safe_backup_path], timeout=20
    )


def _read_config(config_path):
    safe_config_path = _normalize_allowed_path(config_path)
    if not safe_config_path:
        return 1, "Nicht erlaubter rkhunter-Pfad."
    return _run_cmd(["sudo", "-n", "cat", safe_config_path], timeout=20)


def _write_config(config_text, config_path):
    tmp_path = ""
    try:
        safe_config_path = _normalize_allowed_path(config_path)
        if not safe_config_path:
            return 1, "Nicht erlaubter rkhunter-Pfad."
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix="netmon-rkhunter-",
            suffix=".conf",
            delete=False,
        ) as fh:
            fh.write(config_text)
            fh.flush()
            os.fsync(fh.fileno())
            tmp_path = fh.name

        rc, out = _run_cmd(
            ["sudo", "-n", "install", "-m", "644", tmp_path, safe_config_path],
            timeout=20,
        )
        return rc, out
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def repair_config(config_path=RKHUNTER_CONFIG_PATH):
    rc, out = _read_config(config_path)
    if rc != 0:
        return rc, out or "rkhunter-Konfiguration konnte nicht gelesen werden."

    lines = (out or "").splitlines()
    replaced = set()
    result_lines = []

    repair_targets = dict(REPAIR_TARGETS)
    repair_targets["WEB_CMD"] = _preferred_web_cmd()

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        replaced_line = False
        for key, value in repair_targets.items():
            if re.match(rf"^\s*{re.escape(key)}\s*=", stripped):
                result_lines.append(f"{key}={value}")
                replaced.add(key)
                replaced_line = True
                break
        if not replaced_line:
            result_lines.append(line)

    for key, value in repair_targets.items():
        if key not in replaced:
            result_lines.append(f"{key}={value}")

    new_content = "\n".join(result_lines).rstrip() + "\n"
    return _write_config(new_content, config_path)
