"""Synthetic kernel identities and UFW sinks; no host network operations."""

import json
from types import SimpleNamespace

import pytest

from netmon.features import vpn_controller as vpn


@pytest.fixture
def tunnel(monkeypatch):
    links, rules, events = {}, [], []
    state = SimpleNamespace(up_rc=0, kind="wireguard", publish=True, links=links)

    def command(args, **kwargs):
        assert args == ["ip", "-j", "-d", "link", "show"]
        return 0, json.dumps(
            [
                {"ifname": name, "ifindex": index, "linkinfo": {"info_kind": kind}}
                for name, (index, kind) in links.items()
            ]
        )

    def up(name, **kwargs):
        events.append("up")
        assert name not in links
        if state.publish:
            links[name] = (42, state.kind)
        return state.up_rc, "synthetic activation"

    app = SimpleNamespace(
        _try_begin_network_operation=lambda label: True,
        _end_network_operation=lambda: events.append("end"),
        debug_nm_state=None,
        resolve_profile_family_runtime=lambda name, **kw: {"runtime_profile": name},
        get_wg_interfaces=lambda: [n for n, v in links.items() if v[1] == "wireguard"],
        _network_service=lambda: SimpleNamespace(
            file_exists=lambda path: (0, ""), wg_quick_up=up
        ),
        _wg_profile_path=lambda name: "/synthetic/" + name + ".conf",
        _check_wireguard_profile_for_multiple_endpoints=lambda *a: None,
        killswitch_is_on=lambda: False,
        _read_ufw_status=lambda **kw: (0, "Status: active"),
        _ufw_status_is_active=lambda text: True,
        _ufw_existing_rule_keys=lambda text: set(),
        ensure_ufw_rule_exists=lambda rule, **kw: (
            rules.append(rule) or True,
            True,
            "",
            set(),
        ),
        _dedupe_vpn_ufw_rules=lambda: 0,
        tr=lambda key, fallback: fallback,
        run_async=lambda fn: None,
        verify_vpn_exit_country=lambda name: None,
    )
    for name in (
        "log_safe",
        "log_debug",
        "log_debug_safe",
        "log_network_debug",
        "log",
        "prepare_dns_for_vpn_profile_switch",
        "refresh_wg_profiles",
        "update_primary_vpn_form_controls",
        "sync_primary_vpn_form_selection",
        "update_ipv6_controls_state_safe",
        "refresh_safe",
        "_schedule_dns_finalize_after_vpn_profile_switch",
    ):
        setattr(app, name, lambda *a, **kw: None)
    app.reconcile_vpn_slot_firewall_state = (
        lambda **kw: vpn.apply_profile_ufw_rules_non_killswitch(
            app, {"work", "work__ipv4", "eth0"}, set()
        )
    )

    def cleanup(app):
        events.append("cleanup")
        links.clear()
        app.__dict__.pop("_wg_activation_links", None)
        return True

    def owned(operation, *, identity=None):
        assert operation == "wg-up"
        rc, _out = up(identity[0])
        if rc:
            raise vpn.nm_ownership.OwnershipError("synthetic start failure")

    monkeypatch.setattr(vpn, "_owned_nm_command", owned)
    monkeypatch.setattr(vpn, "run_cmd", command)
    monkeypatch.setattr(vpn, "cleanup_wireguard_interfaces", cleanup)
    state.app, state.rules, state.events = app, rules, events
    return state


@pytest.mark.parametrize("name", ["work", "work__ipv4"])
def test_rules_only_after_successful_activation_of_exact_runtime(tunnel, name):
    app = tunnel.app
    assert vpn.apply_profile_ufw_rules_non_killswitch(app, {name}, set())
    assert tunnel.rules == []
    assert vpn.vpn_switch(app, name, ensure_sudo=False)
    assert tunnel.events == ["cleanup", "up", "end"]
    assert app._wg_activation_links == {name: 42}
    assert tunnel.rules == [
        {"type": "interface", "iface": name, "direction": "out"},
        {"type": "interface", "iface": name, "direction": "in"},
    ]


@pytest.mark.parametrize("kind", ["ether", "bridge", "dummy", ""])
def test_physical_collision_never_starts_or_grants_rules(tunnel, kind):
    tunnel.links["eth0"] = (2, kind)
    assert not vpn.vpn_switch(tunnel.app, "eth0", ensure_sudo=False)
    assert tunnel.events == ["end"]
    assert tunnel.rules == []
    assert vpn.apply_profile_ufw_rules_non_killswitch(tunnel.app, {"eth0"}, set())
    assert tunnel.rules == []


@pytest.mark.parametrize("failure", ["command", "missing", "wrong_kind"])
def test_unverified_activation_never_records_ownership(tunnel, failure):
    if failure == "command":
        tunnel.up_rc = 1
    elif failure == "missing":
        tunnel.publish = False
    else:
        tunnel.kind = "ether"
    assert not vpn.vpn_switch(tunnel.app, "work", ensure_sudo=False)
    assert not tunnel.app.__dict__.get("_wg_activation_links")
    assert tunnel.rules == []


@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("external", [False, True])
def test_foreign_live_wireguard_is_not_adopted(tunnel, force, external):
    tunnel.links["work"] = (20, "wireguard")
    if external:
        tunnel.links["corporate"] = (7, "wireguard")
    assert not vpn.vpn_switch(
        tunnel.app, "work", ensure_sudo=False, force_reconnect=force
    )
    assert tunnel.events == ["end"]
    assert tunnel.rules == []


@pytest.mark.parametrize("replacement", [None, (43, "wireguard"), (42, "ether")])
def test_deleted_or_replaced_link_loses_firewall_authority(tunnel, replacement):
    assert vpn.vpn_switch(tunnel.app, "work", ensure_sudo=False)
    tunnel.rules.clear()
    if replacement is None:
        tunnel.links.clear()
    else:
        tunnel.links["work"] = replacement
    assert vpn.apply_profile_ufw_rules_non_killswitch(tunnel.app, {"work"}, set())
    assert tunnel.rules == []
    assert not tunnel.app._wg_activation_links


@pytest.mark.parametrize(
    "reply",
    [(1, ""), (0, "garbage"), (0, "{}"), (0, '[{"ifname":"work","ifindex":true}]')],
)
def test_query_failure_or_malformed_evidence_fails_closed(tunnel, monkeypatch, reply):
    tunnel.app._wg_activation_links = {"work": 42}
    monkeypatch.setattr(vpn, "run_cmd", lambda *a, **kw: reply)
    assert vpn._verified_firewall_interfaces(tunnel.app, {"work"}) == set()
    assert not vpn.vpn_switch(tunnel.app, "work", ensure_sudo=False)
    assert tunnel.rules == []


def test_offline_profile_remains_startable_but_is_not_a_firewall_interface(tunnel):
    app = tunnel.app
    app._base_wg_profile_name = lambda name: name
    app.ipv6_is_disabled = lambda: False
    app._internal_ipv4_profile_name = lambda name: name + "__ipv4"
    app.profile_supports_ipv6 = lambda name: False
    app._wg_profile_exists = lambda name: name == "work"
    resolved = vpn.resolve_profile_family_runtime(app, "work")
    assert resolved["runtime_profile"] == "work"
    assert resolved["endpoint_profiles"] == ["work"]
    assert resolved["effective_ipv4_interface"] == ""
    app.resolve_profile_family_runtime = lambda *a, **kw: resolved
    assert vpn.collect_interface_rules_for_profiles(app, ["work"]) == set()
