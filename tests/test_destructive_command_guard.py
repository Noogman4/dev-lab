"""Regressionstests für den Suite-weiten Guard gegen destruktive Kommandos.

Sichert die Runde-10-Härtung ab: Kein Test darf jemals ein echtes
Reboot-/Shutdown-/Logout-Kommando bis zum System durchreichen.
"""

import subprocess

import pytest


def test_guard_blocks_systemctl_reboot():
    with pytest.raises(RuntimeError, match="destruktives Systemkommando"):
        subprocess.Popen(["systemctl", "reboot"])


def test_guard_blocks_systemctl_poweroff_via_run():
    with pytest.raises(RuntimeError, match="destruktives Systemkommando"):
        subprocess.run(["systemctl", "poweroff"])


def test_guard_blocks_shutdown_behind_sudo_wrapper():
    with pytest.raises(RuntimeError, match="destruktives Systemkommando"):
        subprocess.run(["sudo", "-n", "shutdown", "-h", "+15"])


def test_guard_blocks_loginctl_terminate_user():
    with pytest.raises(RuntimeError, match="destruktives Systemkommando"):
        subprocess.run(["loginctl", "terminate-user", "happy"])


def test_guard_blocks_absolute_paths_and_shell_strings():
    with pytest.raises(RuntimeError, match="destruktives Systemkommando"):
        subprocess.run("/usr/bin/systemctl reboot", shell=True)


def test_guard_allows_harmless_commands():
    completed = subprocess.run(["true"], check=False)

    assert completed.returncode == 0


def test_guard_allows_non_destructive_systemctl_verbs():
    completed = subprocess.run(
        ["systemctl", "--version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    assert completed.returncode == 0
