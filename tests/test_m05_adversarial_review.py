"""Temporary review probes: stateful synthetic UFW, no system operations."""

import ast
import ipaddress
import subprocess

import pytest
from test_killswitch_failure_recovery import Ufw
from test_killswitch_legacy_interface_rules import bind_verifier

from netmon.features import firewall_controller as fw


def setup_model(monkeypatch, *, service=False):
    model = Ufw(service=service)
    app = bind_verifier(model)
    monkeypatch.setattr(
        fw.nm_ownership,
        "verified_interface",
        lambda name: {"name": name} if name == "wg0" else None,
    )
    return model, app


def packet_allowed(model, ipv6, direction, interface, source, dest_port):
    """Independent first-match oracle for these exact synthetic rule forms."""
    for policy, rule_direction, target, origin in model.rules[ipv6]:
        if direction != rule_direction:
            continue
        origin, _, bound_interface = origin.partition(" on ")
        if bound_interface and bound_interface != interface:
            continue
        if origin != "Anywhere" and ipaddress.ip_address(source) not in (
            ipaddress.ip_network(origin, strict=False)
        ):
            continue
        if target != "Anywhere" and target != f"{dest_port}/tcp":
            continue
        return policy == "ALLOW"
    return model.defaults[{"IN": "incoming", "OUT": "outgoing"}[direction]] == "allow"


@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("service", [False, True])
def test_source_restricted_all_destination_egress_must_not_claim_protection(
    monkeypatch, ipv6, service
):
    model, app = setup_model(monkeypatch, service=service)
    source = "2001:db8::10" if ipv6 else "192.0.2.10"
    rule = ("ALLOW", "OUT", "Anywhere", f"{source} on eth0")
    model.rules[ipv6].append(rule)
    claimed = fw.killswitch_on_sync(app, refresh_ui=False)
    reported = fw.killswitch_is_on(app)
    escaped = packet_allowed(model, ipv6, "OUT", "eth0", source, 12345)
    assert rule in model.rules[ipv6]
    assert not (
        claimed and reported and escaped
    ), "Protection claimed while arbitrary TCP egress on physical eth0 is allowed"


@pytest.mark.parametrize(
    "line",
    [
        "Anywhere on eth0 ALLOW OUT",
        "Anywhere on eth0 ALLOW FWD Anywhere",
        "Anywhere on wg0 ALLOW Anywhere",
        "Anywhere on eth0 ALLOW OUT SIDEWAYS Anywhere",
    ],
)
def test_incomplete_or_ambiguous_rows_must_not_claim_protection(monkeypatch, line):
    model, app = setup_model(monkeypatch)
    original_status = app._read_ufw_status

    def status(verbose=False):
        rc, text = original_status(verbose=verbose)
        return rc, text + "\n" + line

    app._read_ufw_status = status
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False, line


@pytest.mark.parametrize("interface", ["wg0", "lo"])
@pytest.mark.parametrize("service", [False, True])
def test_narrow_preexisting_rules_on_verified_interfaces_are_preserved(
    monkeypatch, interface, service
):
    model, app = setup_model(monkeypatch, service=service)
    management = ("ALLOW", "IN", f"22/tcp on {interface}", "192.0.2.10")
    model.rules[False].append(management)
    assert fw.killswitch_on_sync(app, refresh_ui=False) is True
    assert management in model.rules[False], "Preexisting narrow rule was deleted"


def test_successful_empty_preflight_response_aborts_before_mutation(monkeypatch):
    model, app = setup_model(monkeypatch)
    original_status = app._read_ufw_status
    reads = 0

    def status(verbose=False):
        nonlocal reads
        reads += 1
        return (0, "") if reads == 1 else original_status(verbose=verbose)

    app._read_ufw_status = status
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert model.count == 0


@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("deny_first", [False, True])
def test_wide_rules_are_conservatively_rejected_even_when_shadowed(
    monkeypatch, ipv6, deny_first
):
    model, app = setup_model(monkeypatch)
    deny = ("DENY", "OUT", "Anywhere", "Anywhere")
    allow = ("ALLOW", "OUT", "Anywhere", "Anywhere on eth0")
    model.rules[ipv6] = [deny, allow] if deny_first else [allow, deny]
    source = "2001:db8::10" if ipv6 else "192.0.2.10"
    assert packet_allowed(model, ipv6, "OUT", "eth0", source, 12345) is not deny_first
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert model.count == 0
    assert model.rules[ipv6] == ([deny, allow] if deny_first else [allow, deny])


@pytest.mark.parametrize("service", [False, True])
def test_physical_interface_narrow_management_rule_is_preserved(monkeypatch, service):
    model, app = setup_model(monkeypatch, service=service)
    management = ("ALLOW", "IN", "22/tcp on eth0", "192.0.2.10")
    model.rules[False].append(management)
    assert fw.killswitch_on_sync(app, refresh_ui=False) is True
    assert management in model.rules[False]


@pytest.mark.parametrize("interface", ["wg0", "lo"])
@pytest.mark.parametrize("service", [False, True])
def test_narrow_rule_cleanup_issue_already_exists_in_base(
    monkeypatch, interface, service
):
    source = subprocess.check_output(
        ["git", "show", "0dac2a36:netmon/features/firewall_controller.py"], text=True
    )
    function = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_remove_residual_killswitch_rules"
    )
    namespace = vars(fw).copy()
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), "base", "exec"), namespace
    )
    management = ("ALLOW", "IN", f"22/tcp on {interface}", "192.0.2.10")
    for index, cleanup in enumerate(
        (
            namespace["_remove_residual_killswitch_rules"],
            fw._remove_residual_killswitch_rules,
        )
    ):
        model, app = setup_model(monkeypatch, service=service)
        model.rules[False].append(management)
        with app.ufw_lock:
            cleanup(app, ["wg0"], [], strict=True)
        # Keep the historical reproduction; the corrected production function
        # must now retain exactly the same administrator rule.
        if index == 0:
            assert management not in model.rules[False]
        else:
            assert management in model.rules[False]
