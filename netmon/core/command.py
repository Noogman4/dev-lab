"""Command helpers shared across NetMon modules."""

from __future__ import annotations

import os
import shutil
import subprocess

try:
    from netmon.core.performance_monitor import measure, safe_command_name
except ModuleNotFoundError:
    from core.performance_monitor import measure, safe_command_name


def _is_ufw_status_command(args) -> bool:
    tokens = [str(part) for part in args]
    try:
        status_index = tokens.index("status")
    except ValueError:
        return False
    return status_index > 0 and tokens[status_index - 1] == "ufw"


def _command_env(args):
    if not _is_ufw_status_command(args):
        return None
    env = os.environ.copy()
    env["LANG"] = "C"
    env["LC_ALL"] = "C"
    return env


def _with_ufw_status_locale(args):
    tokens = [str(part) for part in args]
    if not _is_ufw_status_command(tokens):
        return tokens
    ufw_index = tokens.index("status") - 1
    if ufw_index > 0 and tokens[ufw_index - 1] == "LC_ALL=C":
        return tokens
    return tokens[:ufw_index] + ["env", "LANG=C", "LC_ALL=C"] + tokens[ufw_index:]


def run_cmd(args, timeout=15, text=True):
    """
    args: list[str]
    returns (returncode, combined_output_str)
    """
    try:
        exec_args = _with_ufw_status_locale(args)

        with measure(
            area="system_command",
            operation="run_cmd",
            command_name=safe_command_name(exec_args),
            mode="detailed",
        ) as measurement:
            p = subprocess.run(
                exec_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=text,
                timeout=timeout,
                check=False,
                env=_command_env(exec_args),
            )
            measurement.set_status(
                "success" if p.returncode == 0 else "error",
                return_code=p.returncode,
            )
        out = (p.stdout or "").strip()
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return 124, "Command timed out"
    except OSError as e:
        return 1, f"Command failed: {e}"


def run_cmd_with_input(args, input_text="", timeout=20):
    """Safe command runner with optional stdin payload (e.g. cryptsetup passphrase)."""
    try:
        exec_args = list(args)
        payload = input_text or ""

        with measure(
            area="system_command",
            operation="run_cmd_with_input",
            command_name=safe_command_name(exec_args),
            mode="detailed",
        ) as measurement:
            p = subprocess.run(
                exec_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
                check=False,
                input=payload,
            )
            measurement.set_status(
                "success" if p.returncode == 0 else "error",
                return_code=p.returncode,
            )
        out = (p.stdout or "").strip()
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return 124, "Command timed out"
    except OSError as e:
        return 1, f"Command failed: {e}"


def check_sudo_nopasswd() -> bool:
    try:
        p = subprocess.run(
            ["sudo", "-n", "true"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=3,
            check=False,
        )
        return p.returncode == 0
    except Exception:
        return False


def _safe_messagebox_showerror(messagebox, title, message, *, parent=None):
    options = {}
    if parent is not None:
        try:
            if bool(parent.winfo_exists()):
                options["parent"] = parent
        except Exception:
            pass
    try:
        messagebox.showerror(title, message, **options)
        return True
    except Exception:
        return False


def renew_sudo_timestamp(parent=None):
    """Request sudo password only to refresh system sudo timestamp; do not store it."""
    if shutil.which("sudo") is None:
        return False
    if check_sudo_nopasswd():
        return True

    try:
        from tkinter import messagebox, simpledialog
    except Exception:
        return False

    for _ in range(3):
        pw = simpledialog.askstring(
            "Sudo Passwort",
            "Bitte sudo-Passwort eingeben.\n"
            "Es wird nicht gespeichert, nur für sudo-Session-Freigabe genutzt.",
            show="*",
            parent=parent,
        )
        if pw is None:
            return False
        try:
            p = subprocess.run(
                ["sudo", "-S", "-v"],
                input=pw + "\n",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=6,
                check=False,
            )
            pw = "\0" * len(pw)
            if p.returncode == 0:
                return True
        except Exception:
            pass
        _safe_messagebox_showerror(
            messagebox,
            "Sudo Passwort",
            "Passwort ungültig oder sudo-Rechte fehlen.",
            parent=parent,
        )
    return False
