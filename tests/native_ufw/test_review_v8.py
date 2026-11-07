"""Seventh review: multiport display and pre-mutation fence-order rejection."""

import pytest

from test_review_v5 import system as system, real_app, profile
from support import ufw_cli
from netmon.features import firewall_controller as fc


def journal_bytes(app):
    path = app.killswitch_journal.directory / "killswitch-state.json"
    return path.read_bytes() if path.exists() else None


@pytest.mark.parametrize("ports", ["80,443", "6000:6007", "80,443,6000:6007"])
def test_multiport_status_consumers_keep_the_full_expression(
    system, monkeypatch, ports
):
    assert ufw_cli(["allow", ports + "/tcp"])[0] == 0
    assert (
        ufw_cli(["allow", "in", "proto", "udp", "to", "198.51.100.77", "port", ports])[
            0
        ]
        == 0
    )
    profile("wg0")
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()

    def status(args, **_kwargs):
        assert args == ["sudo", "-n", "ufw", "status", "verbose"]
        return system.backend.command(args[3:])

    monkeypatch.setattr(fc, "run_cmd", status)
    for enabled in (False, True):
        if enabled:
            assert fc.killswitch_on_sync(app, refresh_ui=False), logs
            assert app.killswitch_is_on()
        text = app._read_ufw_status(verbose=True)[1]
        rules = [fc.parse_ufw_structured_rule(row) for row in text.splitlines()]
        rules = [rule for rule in rules if rule and rule["port"] == ports]
        assert rules
        for category in {rule["category"] for rule in rules}:
            assert ports in "\n".join(
                fc.format_ufw_rule_lines(
                    [r for r in rules if r["category"] == category]
                )
            )
        assert ports in fc.format_ufw_status_grouped("active", "deny", "deny", rules)
        app.fw_status()
        assert ports in logs[-1] and "Firewall status" in logs[-1]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


BAD_CASES = [
    (stage, action, direction, "both")
    for stage in ("initial", "offline")
    for action in ("allow", "limit")
    for direction in ("in", "out")
] + [
    ("initial", action, "out", family)
    for action in ("allow", "limit")
    for family in ("4", "6")
]


@pytest.mark.parametrize("stage,action,direction,family", BAD_CASES)
def test_late_existing_deny_rejected_before_any_change(
    system, monkeypatch, stage, action, direction, family
):
    profile("wg0")
    profile("manual1")
    destination = {"4": "0.0.0.0/0", "6": "::/0", "both": "any"}[family]
    assert (
        ufw_cli(
            [
                action,
                direction,
                "on",
                "manual1",
                "to",
                destination,
                "port",
                "4443",
                "proto",
                "tcp",
            ]
        )[0]
        == 0
    )
    assert ufw_cli(["deny", direction, "on", "manual1"])[0] == 0
    original = system.capture()
    app, env, logs = real_app(system, monkeypatch)
    if stage == "offline":
        env.live = {"wg0", "manual1"}
        assert fc.killswitch_on_sync(app, refresh_ui=False), logs
        env.live = {"wg0"}
    before, record = system.capture(), system.load()
    state_path = system.registry / "state.json"
    saved_bytes = state_path.read_bytes() if state_path.exists() else None
    journal = journal_bytes(app)
    logs.clear()
    assert not fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.capture() == before
    assert system.load() == record
    assert (state_path.read_bytes() if state_path.exists() else None) == saved_bytes
    assert journal_bytes(app) == journal
    assert not any("Notfallregeln" in line for line in logs)
    if stage == "offline":
        assert system.state()["state"] == "on"
        assert fc.killswitch_off_sync(app, refresh_ui=False), logs
        assert system.capture() == original
    else:
        assert record is None


@pytest.mark.parametrize("action", ["allow", "limit"])
def test_existing_deny_before_specific_grant_stays_usable(system, monkeypatch, action):
    profile("wg0")
    profile("manual1")
    assert ufw_cli(["deny", "out", "on", "manual1"])[0] == 0
    assert (
        ufw_cli(
            [
                action,
                "out",
                "on",
                "manual1",
                "to",
                "any",
                "port",
                "4443",
                "proto",
                "tcp",
            ]
        )[0]
        == 0
    )
    before = system.capture()
    app, _env, logs = real_app(system, monkeypatch)
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on"
    assert app.killswitch_is_on()
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before
