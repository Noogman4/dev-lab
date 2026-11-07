"""Eighth review: bound service grants and logged DENY preflight semantics."""

from pathlib import Path
import pytest

from test_review_v5 import system as system, real_app, profile
from support import ufw_cli, reboot
from netmon.features import firewall_controller as fc

SERVICES = [("53", "udp"), ("53", "tcp"), ("80", "tcp"), ("443", "tcp")]


def commits():
    path = Path("/work/kernel/calls.log")
    return (
        sum("restore" in row for row in path.read_text().splitlines())
        if path.exists()
        else 0
    )


@pytest.mark.parametrize("port,proto", SERVICES)
@pytest.mark.parametrize("iface", ["wg0", "manual1"])
def test_bound_service_grant_can_enable_and_resync(
    system, monkeypatch, iface, port, proto
):
    profile("wg0")
    profile("manual1")
    assert (
        ufw_cli(
            ["allow", "out", "on", iface, "to", "any", "port", port, "proto", proto]
        )[0]
        == 0
    )
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on" and app.killswitch_is_on()
    assert (
        fc.classify_killswitch_state(app, app._read_ufw_status(verbose=True)[1]) == "on"
    )
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on"
    assert not any("Notfallregeln" in row for row in logs)
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("destination", ["9.9.9.9", "2001:db8::53"])
def test_dns_target_host_on_tunnel_does_not_trigger_recovery(
    system, monkeypatch, destination
):
    profile("wg0")
    assert (
        ufw_cli(
            [
                "allow",
                "out",
                "on",
                "wg0",
                "to",
                destination,
                "port",
                "53",
                "proto",
                "udp",
            ]
        )[0]
        == 0
    )
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert reboot().returncode == 0
    assert system.state()["state"] == "on" and app.killswitch_is_on()
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("port,proto", SERVICES)
@pytest.mark.parametrize("iface", ["eth0", None])
def test_foreign_or_unbound_service_grant_rejected_without_writes(
    system, monkeypatch, iface, port, proto
):
    profile("wg0")
    args = ["allow", "out"] + (["on", iface] if iface else [])
    args += ["to", "any", "port", port, "proto", proto]
    assert ufw_cli(args)[0] == 0
    app, _env, logs = real_app(system, monkeypatch)
    before, writes = system.capture(), commits()
    assert not fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert commits() == writes
    assert system.capture() == before and system.load() is None
    assert not any("Notfallregeln" in row for row in logs)


@pytest.mark.parametrize("stage", ["initial", "offline"])
@pytest.mark.parametrize("direction", ["in", "out"])
@pytest.mark.parametrize("logging", ["log", "log-all"])
def test_logged_deny_after_grant_gets_a_new_leading_fence(
    system, monkeypatch, stage, direction, logging
):
    profile("wg0")
    profile("manual1")
    assert (
        ufw_cli(
            [
                "allow",
                direction,
                "on",
                "manual1",
                "to",
                "any",
                "port",
                "443",
                "proto",
                "tcp",
            ]
        )[0]
        == 0
    )
    assert ufw_cli(["deny", direction, "on", "manual1", logging])[0] == 0
    before = system.capture()
    app, env, logs = real_app(system, monkeypatch)
    if stage == "offline":
        env.live = {"wg0", "manual1"}
        assert fc.killswitch_on_sync(app, refresh_ui=False), logs
        env.live = {"wg0"}
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.load()["plan"]["blocked_interfaces"] == ["manual1"]
    assert system.state()["state"] == "on" and app.killswitch_is_on()
    assert not any("Notfallregeln" in row for row in logs)
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before
