"""Strict UFW inventories and narrow cleanup, with synthetic state only."""

from copy import deepcopy

import pytest
from test_m05_adversarial_review import setup_model

from netmon.features import firewall_controller as fw

DEFAULTS = "Default: deny (incoming), deny (outgoing), disabled (routed)"


@pytest.mark.parametrize(
    "row",
    [
        "ALLOW OUT Anywhere on eth0",
        "Anywhere ALLOW OUT",
        "Anywhere ALLOW SIDEWAYS Anywhere on eth0",
        "Anywhere on wg0 ALLOW Anywhere",
        "Anywhere on eth0 ALLOW FWD Anywhere on wg0",
        "Anywhere on eth0 ALLOW OUT Anywhere",
        "Anywhere ALLOW IN Anywhere on eth0",
        "Anywhere on lo ALLOW IN Anywhere on eth0",
        "Anywhere ALLOW OUT BAD Anywhere on eth0",
        "Anywhere ALLOW OUT 999.1.2.3 on eth0",
        "Anywhere (v6) ALLOW OUT 192.0.2.10 on eth0",
        "192.0.2.10 ALLOW OUT 2001:db8::10 on eth0",
        "Anywhere ALLOW OUT 2001:db8::10 (v6) (v6) on eth0",
        "22/tcp (v6) on wg0 ALLOW IN 192.0.2.10",
        "22/tcp on wg0 ALLOW IN Anywhere/udp",
        "22/unknown on wg0 ALLOW IN Anywhere",
        "22/icmp on wg0 ALLOW IN Anywhere",
        "Anywhere/ipv6-icmp on wg0 ALLOW IN 192.0.2.10",
        "Anywhere/icmp (v6) on wg0 ALLOW IN Anywhere (v6)",
        "Anywhere(v6) on wg0 ALLOW IN Anywhere (v6)",
        "22/tcp on wg0 ALLOW IN Anywhere trailing",
        "70000/tcp on wg0 ALLOW IN Anywhere",
        "30:20/tcp on wg0 ALLOW IN Anywhere",
        "Status: active\nStatus: inactive",
        "Default: unknown",
        "Default: allow (incoming), allow (outgoing), disabled (routed)\n" + DEFAULTS,
        "Default: Anywhere on eth0 ALLOW OUT Anywhere",
        "unexpected output",
        "Anywhere\x00 ALLOW OUT Anywhere on wg0",
        "Anywhere\x7f ALLOW OUT Anywhere on wg0",
    ],
)
def test_unknown_or_contradictory_rows_refuse_before_mutation(monkeypatch, row):
    model, app = setup_model(monkeypatch)
    before = deepcopy(model.rules)
    original_status = app._read_ufw_status

    def status(verbose=False):
        rc, text = original_status(verbose=verbose)
        return rc, text + "\n" + row

    app._read_ufw_status = status
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert model.count == 0
    assert model.rules == before


@pytest.mark.parametrize(
    "row",
    [
        "Anywhere ALLOW OUT 192.0.2.10 on eth0",
        "Anywhere (v6) ALLOW OUT 2001:db8::10 on eth0",
        "198.51.100.7 ALLOW OUT 192.0.2.10 on eth0",
        "2001:db8:1::/64 ALLOW OUT 2001:db8:2::10 on eth0",
        "198.51.100.7 443/tcp ALLOW OUT Anywhere on eth0",
        "443/tcp ALLOW OUT 192.0.2.10",
        "Anywhere ALLOW OUT Anywhere",
        "0.0.0.0/0 ALLOW OUT 192.0.2.10 on eth0",
        "::/0 ALLOW OUT 2001:db8::10 on eth0",
        "203.0.113.0/24 51820/udp ALLOW OUT Anywhere on eth0",
        "203.0.113.1 51820/tcp ALLOW OUT Anywhere on eth0",
        "203.0.113.1 12345/udp ALLOW OUT Anywhere on eth0",
    ],
)
def test_restricted_egress_is_not_an_implicit_management_exception(row):
    assert fw._killswitch_interface_rule_issues(
        "Status: active\n" + row,
        ["wg0"],
        [("203.0.113.1", "51820")],
        allow_cleanup=True,
    )


@pytest.mark.parametrize(
    "row",
    [
        "22/tcp on eth0 ALLOW IN 192.0.2.10",
        "22/tcp (v6) on eth0 ALLOW IN Anywhere (v6)",
        "2001:db8::1 22/tcp on eth0 ALLOW IN 2001:db8::2",
        "80,443,8000:8090/tcp on wg0 ALLOW IN Anywhere",
        "Anywhere ALLOW OUT Anywhere on wg0",
        "203.0.113.1 51820/udp ALLOW OUT 192.0.2.10 on eth0",
        "2001:db8::1 51820/udp ALLOW OUT Anywhere (v6) on eth0",
    ],
)
def test_numeric_management_and_exact_handshake_rules_remain_supported(row):
    assert (
        fw._killswitch_interface_rule_issues(
            "Status: active\n" + row,
            ["wg0"],
            [("203.0.113.1", "51820"), ("2001:db8::1", "51820")],
        )
        == []
    )


@pytest.mark.parametrize("text", ["", "Status: active", "To Action From", "garbage"])
def test_incomplete_verbose_inventory_is_distinct_from_zero_rules(monkeypatch, text):
    model, app = setup_model(monkeypatch)
    app._read_ufw_status = lambda verbose=False: (0, text)
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert model.count == 0


@pytest.mark.parametrize(
    "text,verbose,numbered",
    [
        ("Status: inactive", True, False),
        ("Status: active\n" + DEFAULTS, True, False),
        ("Status: active", False, True),
    ],
)
def test_explicit_zero_rule_inventory_is_valid(text, verbose, numbered):
    assert fw._killswitch_status_rules(text, verbose=verbose, numbered=numbered) == []


@pytest.mark.parametrize(
    "text",
    [
        "[1] Anywhere ALLOW OUT Anywhere on wg0",
        "Status: active\nAnywhere ALLOW OUT Anywhere on wg0",
        "Status: active\n[2] Anywhere ALLOW OUT Anywhere on wg0",
        "Status: active\n[1] Anywhere ALLOW OUT Anywhere on wg0\n"
        "[1] Anywhere ALLOW OUT Anywhere on wg0",
    ],
)
def test_unreliable_numbered_inventory_triggers_recovery(monkeypatch, text):
    model, app = setup_model(monkeypatch)
    original_run = model.run

    def runner(args, **kwargs):
        if args[3:] == ["status", "numbered"]:
            return 0, text
        return original_run(args, **kwargs)

    app.run_cmd = runner
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    model.assert_closed()
    assert not any(call[:2] == ["--force", "delete"] for call in model.calls)


def test_numbered_out_attribute_and_comment_do_not_change_rule_fields():
    rows = fw._killswitch_status_rules(
        "Status: active\n[1] Anywhere ALLOW OUT Anywhere on wg0 (out) # note",
        numbered=True,
    )
    assert rows[0]["interface"] == "wg0"
    assert rows[0]["direction"] == "OUT"


@pytest.mark.parametrize("service", [False, True])
@pytest.mark.parametrize("stage", ["cleanup", "verification"])
def test_late_source_specific_egress_recovers_and_preserves_foreign_rules(
    monkeypatch, service, stage
):
    model, app = setup_model(monkeypatch, service=service)
    inserted = False

    def inject():
        nonlocal inserted
        if inserted:
            return
        for ipv6, rules in model.rules.items():
            source = "2001:db8::10" if ipv6 else "192.0.2.10"
            rules.append(("ALLOW", "OUT", "Anywhere", f"{source} on eth0"))
        inserted = True

    original_run = model.run

    def runner(args, **kwargs):
        if stage == "cleanup" and args[3:] == ["status", "numbered"]:
            inject()
        return original_run(args, **kwargs)

    app.run_cmd = runner
    if service:
        adapter = app._network_service()
        adapter.run = runner
        app._network_service = lambda: adapter
    original_status = app._read_ufw_status
    reads = 0

    def status(verbose=False):
        nonlocal reads
        reads += 1
        if stage == "verification" and reads == 2:
            inject()
        return original_status(verbose=verbose)

    app._read_ufw_status = status
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert inserted
    model.assert_closed()
    assert not any("Killswitch AN" in message for message in model.logs)
    for rules in model.rules.values():
        assert any("eth0" in rule[3] for rule in rules)


@pytest.mark.parametrize("interface", ["lo", "wg0"])
@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("kind", ["port", "source", "protocol"])
def test_cleanup_preserves_both_narrow_and_unrestricted_interface_shapes(
    monkeypatch, interface, ipv6, kind
):
    model, app = setup_model(monkeypatch)
    source = "2001:db8::10" if ipv6 else "192.0.2.10"
    narrow = {
        "port": ("ALLOW", "IN", f"22/tcp on {interface}", source),
        "source": ("ALLOW", "IN", f"Anywhere on {interface}", source),
        "protocol": ("ALLOW", "IN", f"Anywhere/tcp on {interface}", "Anywhere/tcp"),
    }[kind]
    broad = ("ALLOW", "IN", f"Anywhere on {interface}", "Anywhere")
    model.rules[ipv6].extend([narrow, broad])
    with app.ufw_lock:
        fw._remove_residual_killswitch_rules(app, ["wg0"], [], strict=True)
    assert narrow in model.rules[ipv6]
    assert broad in model.rules[ipv6]
    assert not any("delete" in call for call in model.calls)
