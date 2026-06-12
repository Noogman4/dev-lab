"""Command helpers shared across NetMon modules."""

from __future__ import annotations

import shutil
import subprocess


def run_cmd(args, timeout=15, text=True):
    """
    args: list[str]
    returns (returncode, combined_output_str)
    """
    try:
        exec_args = list(args)

        p = subprocess.run(
            exec_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=text,
            timeout=timeout,
            check=False,
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

        p = subprocess.run(
            exec_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
            input=payload,
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
