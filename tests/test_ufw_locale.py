from netmon.core import command
from netmon.features import firewall_controller


class DummyCompletedProcess:
    returncode = 0
    stdout = "Status: active\n"


def test_run_cmd_forces_c_locale_for_ufw_status(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return DummyCompletedProcess()

    monkeypatch.setattr(command.subprocess, "run", fake_run)

    rc, out = command.run_cmd(["sudo", "-n", "ufw", "status"], timeout=8)

    assert rc == 0
    assert out == "Status: active"
    assert calls[0][0] == [
        "sudo",
        "-n",
        "env",
        "LANG=C",
        "LC_ALL=C",
        "ufw",
        "status",
    ]
    env = calls[0][1]["env"]
    assert env["LANG"] == "C"
    assert env["LC_ALL"] == "C"


def test_run_cmd_keeps_ufw_rule_commands_without_locale_override(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return DummyCompletedProcess()

    monkeypatch.setattr(command.subprocess, "run", fake_run)

    command.run_cmd(["sudo", "-n", "ufw", "allow", "22/tcp"], timeout=8)

    assert calls[0][1]["env"] is None


def test_firewall_ufw_status_is_active_uses_english_status_only():
    assert firewall_controller.ufw_status_is_active("Status: active") is True
    assert firewall_controller.ufw_status_is_active("Status: inactive") is False
    assert firewall_controller.ufw_status_is_active("Status: Aktiv") is False
    assert firewall_controller.ufw_status_is_active("Status: enabled") is False
