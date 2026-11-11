"""Sixth independent review: shared selection, LIMIT and related diagnostics."""

import pytest

from test_review_v5 import system as system, real_app, profile
from support import reboot, ufw_cli
from netmon.features import firewall_controller as fc, vpn_controller as vc
from netmon.core import ufw_snapshot


@pytest.mark.parametrize("endpoint_kind", ["same", "distinct"])
def test_catalog_does_not_change_active_diagnostics(system, monkeypatch, endpoint_kind):
    profile("wg0")
    profile(
        "unused1",
        "203.0.113.77:51820" if endpoint_kind == "distinct" else "198.51.100.10:51820",
    )
    app, env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on"
    assert app.killswitch_is_on()
    status = app._read_ufw_status(verbose=True)[1]
    assert fc.classify_killswitch_state(app, status) == "on"
    assert reboot().returncode == 0
    assert app.killswitch_is_on()
    assert (
        fc.classify_killswitch_state(app, app._read_ufw_status(verbose=True)[1]) == "on"
    )
    assert app._recover_firewall_preserving_killswitch(), logs
    assert not any("VPN-Fehler ohne bestätigten Killswitch" in row for row in logs)
    # The actual VPN-OFF notice path, with only its UI output replaced.
    env.live.clear()
    notices = []
    monkeypatch.setattr(vc.messagebox, "showwarning", lambda *a, **k: notices.append(a))
    assert app.killswitch_is_on()
    assert vc._show_killswitch_active_after_vpn_off_notice(app)
    assert len(notices) == 1
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before
    assert not app.killswitch_is_on()
    assert (
        fc.classify_killswitch_state(app, app._read_ufw_status(verbose=True)[1])
        == "off"
    )


@pytest.mark.parametrize("protocol,port", [("udp", "53"), ("tcp", "443")])
@pytest.mark.parametrize("family", ["4", "6", "both"])
def test_global_limit_rejected_before_mutation(
    system, monkeypatch, protocol, port, family
):
    profile("wg0")
    args = ["limit", "out"]
    if family != "both":
        args += [
            "to",
            "0.0.0.0/0" if family == "4" else "::/0",
            "port",
            port,
            "proto",
            protocol,
        ]
    else:
        args += [port + "/" + protocol]
    assert ufw_cli(args)[0] == 0
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert any(
        "user-limit-accept" in row and "--dport " + port in row
        for rows in before["runtime"].values()
        for row in rows
    )
    assert not fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.capture() == before
    assert system.load() is None
    assert not any("Notfallregeln" in line for line in logs)
    assert not ufw_snapshot.runtime_matches_plan(
        before["runtime"],
        {"interfaces": ["wg0"], "endpoints": [["198.51.100.10", "51820"]]},
        require_active=False,
    )


@pytest.mark.parametrize("iface", ["wg0", "manual1"])
def test_interface_bound_limit_is_preserved_with_required_fence(
    system, monkeypatch, iface
):
    profile("wg0")
    profile("manual1")
    assert (
        ufw_cli(
            ["limit", "out", "on", iface, "to", "any", "port", "53", "proto", "udp"]
        )[0]
        == 0
    )
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on"
    if iface == "manual1":
        assert system.load()["plan"]["blocked_interfaces"] == ["manual1"]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("restriction", ["interface", "source", "both"])
def test_restricted_old_endpoint_is_not_broadened(system, monkeypatch, restriction):
    profile("wg0")
    profile("unused1", "203.0.113.77:51820")
    args = ["allow", "out"]
    if restriction in {"interface", "both"}:
        args += ["on", "eth0"]
    if restriction in {"source", "both"}:
        args += ["from", "10.0.0.5"]
    args += ["to", "203.0.113.77", "port", "51820", "proto", "udp"]
    assert ufw_cli(args)[0] == 0
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert not fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.capture() == before
    assert system.load() is None
    status = app._read_ufw_status(verbose=True)[1]
    assert fc.select_killswitch_vpn_endpoints(app, status) == [
        ("198.51.100.10", "51820")
    ]


def test_catalog_without_selection_has_precise_refusal(system, monkeypatch):
    profile("unused1", "203.0.113.77:51820")
    app, env, logs = real_app(system, monkeypatch, slots=())
    env.live.clear()
    before = system.capture()
    assert not fc.killswitch_on_sync(app, refresh_ui=False)
    assert system.capture() == before
    assert system.load() is None
    assert any("Ungenutzte Katalogprofile allein reichen nicht" in row for row in logs)
    assert not any("Kein WireGuard-Profil mit Endpoint gefunden" in row for row in logs)


@pytest.mark.parametrize("ports", ["53,443", "50:60", "50:52,53,440:445"])
def test_outgoing_multiport_is_detected_before_root_preflight(
    system, monkeypatch, ports
):
    assert ufw_cli(["allow", "out", "proto", "udp", "to", "any", "port", ports])[0] == 0
    status = system.backend.command(["status", "verbose"])[1]
    assert fc.ufw_has_outgoing_port_rule(status, "53", "udp")
    assert not fc.ufw_has_outgoing_port_rule(status, "53", "tcp")
    profile("wg0")
    app, _env, _logs = real_app(system, monkeypatch)
    before = system.capture()
    assert not fc.killswitch_on_sync(app, refresh_ui=False)
    assert system.capture() == before
    assert system.load() is None


def test_unused_endpoint_bound_to_verified_tunnel_is_not_promoted(system, monkeypatch):
    profile("wg0")
    profile("unused1", "203.0.113.77:51820")
    assert (
        ufw_cli(
            [
                "allow",
                "out",
                "on",
                "wg0",
                "to",
                "203.0.113.77",
                "port",
                "51820",
                "proto",
                "udp",
            ]
        )[0]
        == 0
    )
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.load()["plan"]["endpoints"] == [["198.51.100.10", "51820"]]
    assert app.killswitch_is_on()
    rules = [
        fc.parse_ufw_structured_rule(row)
        for row in app._read_ufw_status(verbose=True)[1].splitlines()
    ]
    matching = [rule for rule in rules if rule and rule["ip"] == "203.0.113.77"]
    assert matching and all(rule["interface"] == "wg0" for rule in matching)
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before
