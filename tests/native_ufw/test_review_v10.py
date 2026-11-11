"""Optional Z3: logging annotations retain interface, identity and closure."""

from pathlib import Path
import pytest

from test_review_v5 import system as system, real_app, profile
from support import ufw_cli
from netmon.features import firewall_controller as fc


def commits():
    path = Path("/work/kernel/calls.log")
    return (
        sum("restore" in row for row in path.read_text().splitlines())
        if path.exists()
        else 0
    )


@pytest.mark.parametrize("logging", ["log", "log-all"])
@pytest.mark.parametrize("iface", ["wg0", "manual1"])
@pytest.mark.parametrize("service", [False, True])
def test_logged_interface_grant_enables_without_recovery(
    system, monkeypatch, logging, iface, service
):
    profile("wg0")
    profile("manual1")
    args = ["allow", "out", "on", iface, logging]
    if service:
        args += ["to", "any", "port", "443", "proto", "tcp"]
    assert ufw_cli(args)[0] == 0
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    status = app._read_ufw_status(verbose=True)[1]
    parsed = [fc.parse_ufw_structured_rule(row) for row in status.splitlines()]
    logged = [rule for rule in parsed if rule and "(" + logging + ")" in rule["raw"]]
    assert logged and all(rule["interface"] == iface for rule in logged)
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on" and app.killswitch_is_on()
    assert (
        fc.classify_killswitch_state(app, app._read_ufw_status(verbose=True)[1]) == "on"
    )
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert not any("Notfallregeln" in row for row in logs)
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("logging", ["log", "log-all"])
@pytest.mark.parametrize("direction", ["in", "out"])
def test_logged_global_deny_is_recognized_and_rejected_without_write(
    system, monkeypatch, logging, direction
):
    profile("wg0")
    assert ufw_cli(["deny", direction, logging, "to", "any"])[0] == 0
    app, _env, logs = real_app(system, monkeypatch)
    before, writes = system.capture(), commits()
    rows = [
        fc.parse_ufw_structured_rule(row)
        for row in app._read_ufw_status(verbose=True)[1].splitlines()
    ]
    assert any(fc._is_global_block(rule) for rule in rows)
    assert not fc.killswitch_on_sync(app, refresh_ui=False)
    assert system.capture() == before and commits() == writes
    assert system.load() is None
    assert not any("Notfallregeln" in row for row in logs)


@pytest.mark.parametrize("logging", ["log", "log-all"])
def test_logged_foreign_interface_remains_rejected_before_write(
    system, monkeypatch, logging
):
    profile("wg0")
    assert (
        ufw_cli(
            [
                "allow",
                "out",
                "on",
                "eth0",
                logging,
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
    app, _env, logs = real_app(system, monkeypatch)
    before, writes = system.capture(), commits()
    assert not fc.killswitch_on_sync(app, refresh_ui=False)
    assert system.capture() == before and commits() == writes
    assert system.load() is None
    assert not any("Notfallregeln" in row for row in logs)
