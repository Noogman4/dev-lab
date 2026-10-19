"""Guard classification tests: no tested command or network call is executed."""

import socket

import conftest as guard
import pytest


@pytest.fixture
def denied(monkeypatch):
    def reject(kind, target):
        raise RuntimeError(f"blocked {kind}: {target}")

    monkeypatch.setattr(guard, "_record_host_attempt", reject)


@pytest.mark.parametrize(
    "command",
    [
        "sudo",
        "pkexec",
        "nmcli",
        "wg",
        "wg-quick",
        "ufw",
        "resolvectl",
        "sysctl",
        "ip",
        "systemctl",
        "loginctl",
    ],
)
def test_installed_host_command_is_rejected_before_spawn(command, denied):
    with pytest.raises(RuntimeError, match="blocked command"):
        guard._reject_host_command([f"/usr/bin/{command}", "status"])


def test_executable_override_cannot_hide_host_command(denied):
    with pytest.raises(RuntimeError, match="blocked command"):
        guard._reject_host_command(["innocent"], executable="/usr/bin/sudo")


def test_shell_text_never_reaches_a_real_shell(denied):
    with pytest.raises(RuntimeError, match="blocked shell"):
        guard._reject_host_command("printf harmless", shell=True)


def test_synthetic_executable_remains_usable(tmp_path, denied):
    fake = tmp_path / "nmcli"
    fake.write_text("#!/bin/sh\nexit 0\n")
    guard._reject_host_command([str(fake)])


@pytest.mark.parametrize(
    "host", ["198.51.100.1", "example.invalid", "::ffff:192.0.2.1"]
)
def test_non_loopback_network_is_rejected(host, denied):
    with pytest.raises(RuntimeError, match="blocked network"):
        guard._reject_network((host, 80), socket.AF_INET)


def test_loopback_requires_isolated_test_environment(monkeypatch, denied):
    monkeypatch.delenv("NETMON_TEST_ISOLATED", raising=False)
    with pytest.raises(RuntimeError, match="blocked network"):
        guard._reject_network(("127.0.0.1", 80), socket.AF_INET)


@pytest.mark.parametrize(
    "host,family", [("127.0.0.1", socket.AF_INET), ("::1", socket.AF_INET6)]
)
def test_isolated_loopback_servers_remain_usable(host, family, monkeypatch, denied):
    monkeypatch.setenv("NETMON_TEST_ISOLATED", "1")
    guard._reject_network((host, 80), family)


def test_destructive_guard_is_not_replaced_by_host_guard(denied):
    with pytest.raises(RuntimeError, match="destruktives Systemkommando"):
        guard._GuardedPopen(["systemctl", "reboot"])
