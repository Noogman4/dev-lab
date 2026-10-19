"""M-05 follow-up: synthetic dual-family UFW only, no privileged operations."""

from copy import deepcopy

import pytest

from netmon.features import firewall_controller as fw
from test_killswitch_failure_recovery import Ufw


def bind_verifier(model):
    app = model.app
    app._ufw_default_policy_matches = fw.ufw_default_policy_matches
    app._ufw_has_interface_rule = fw.ufw_has_interface_rule
    app._ufw_has_endpoint_rule = fw.ufw_has_endpoint_rule
    app._verify_killswitch_rules = lambda text, **kw: fw.verify_killswitch_rules(
        app, text, **kw
    )
    return app


@pytest.mark.parametrize("iface", ["eth0", "enp4s0", "wlan0", "wg-foreign"])
@pytest.mark.parametrize("direction", ["IN", "OUT"])
@pytest.mark.parametrize("ipv6", [False, True])
def test_preexisting_foreign_allow_aborts_before_any_mutation(
    monkeypatch, iface, direction, ipv6
):
    model = Ufw()
    app = bind_verifier(model)
    app.get_wg_interfaces = lambda: [iface]
    monkeypatch.setattr(fw.nm_ownership, "verified_interface", lambda name: None)
    model.rules[ipv6].append(("ALLOW", direction, "Anywhere", f"Anywhere on {iface}"))
    before = deepcopy(model.rules)
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert model.rules == before
    assert model.count == 0
    assert any(iface in line and "manuelle Pruefung" in line for line in model.logs)
    assert not any("Killswitch AN" in line for line in model.logs)
    assert fw.killswitch_is_on(app) is False


@pytest.mark.parametrize("service", [False, True])
@pytest.mark.parametrize("stage", ["cleanup", "final_verification"])
def test_late_foreign_allow_triggers_recovery_without_deleting_it(
    monkeypatch, service, stage
):
    model = Ufw(service=service)
    app = bind_verifier(model)
    app.get_wg_interfaces = list
    monkeypatch.setattr(fw.nm_ownership, "verified_interface", lambda name: None)
    inserted = False

    def inject():
        nonlocal inserted
        if not inserted:
            for rules in model.rules.values():
                rules.append(("ALLOW", "OUT", "Anywhere", "Anywhere on eth0"))
            inserted = True

    original_run = model.run

    def runner(args, **kwargs):
        if stage == "cleanup" and args[3:] == ["status", "numbered"]:
            inject()
        return original_run(args, **kwargs)

    app.run_cmd = runner
    if service:
        # The model's provider returns a fresh adapter on each call.
        adapter = app._network_service()
        adapter.run = runner
        app._network_service = lambda: adapter

    original_status = app._read_ufw_status
    reads = 0

    def status(verbose=False):
        nonlocal reads
        reads += 1
        if stage == "final_verification" and reads == 2:
            inject()
        return original_status(verbose=verbose)

    app._read_ufw_status = status
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert inserted
    model.assert_closed()
    assert not any("Killswitch AN" in line for line in model.logs)
    for rules in model.rules.values():
        assert ("ALLOW", "OUT", "Anywhere", "Anywhere on eth0") in rules


@pytest.mark.parametrize(
    "line",
    [
        "[ 12] Anywhere on eth0 ALLOW IN Anywhere # old rule",
        "Anywhere (v6) ALLOW OUT Anywhere (v6) on eth0 # old rule",
        "Anywhere on eth0 ALLOW Anywhere",
        "Anywhere on lo ALLOW IN Anywhere on eth0",
        "Anywhere on eth0 ALLOW OUT Anywhere on lo",
        "unrecognized rule output",
    ],
)
def test_numbered_commented_or_ambiguous_rules_cannot_hide_foreign_allow(line):
    assert fw._killswitch_interface_rule_issues("Status: active\n" + line, [])


def test_known_loopback_and_verified_wireguard_remain_usable(monkeypatch):
    model = Ufw()
    app = bind_verifier(model)
    monkeypatch.setattr(
        fw.nm_ownership,
        "verified_interface",
        lambda name: {"name": name} if name == "wg0" else None,
    )
    assert fw.killswitch_on_sync(app, refresh_ui=False) is True
    assert fw.killswitch_is_on(app) is True
    assert any("Killswitch AN" in line for line in model.logs)


def test_narrow_management_rule_is_not_automatically_removed_or_blocked():
    text = "Status: active\n22/tcp on eth0 ALLOW IN 192.0.2.10\n"
    assert fw._killswitch_interface_rule_issues(text, []) == []


@pytest.mark.parametrize("service", [False, True])
def test_inactive_ufw_hidden_legacy_rules_are_checked_after_enable(
    monkeypatch, service
):
    model = Ufw(active=False, service=service)
    app = bind_verifier(model)
    app.get_wg_interfaces = list
    monkeypatch.setattr(fw.nm_ownership, "verified_interface", lambda name: None)
    for rules in model.rules.values():
        rules.append(("ALLOW", "OUT", "Anywhere", "Anywhere on eth0"))
    original_status = app._read_ufw_status
    app._read_ufw_status = lambda verbose=False: (
        original_status(verbose=verbose) if model.active else (0, "Status: inactive")
    )
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    model.assert_closed()
    assert not any("Killswitch AN" in line for line in model.logs)
    assert not any(call[:2] == ["--force", "delete"] for call in model.calls)
    for rules in model.rules.values():
        assert ("ALLOW", "OUT", "Anywhere", "Anywhere on eth0") in rules
