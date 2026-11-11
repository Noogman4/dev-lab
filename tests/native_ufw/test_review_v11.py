"""VM-P2-1 regression: real UFW, actual App descriptors, simulated kernel only."""

import pytest

from test_review_v5 import system as system, real_app, profile
from support import ufw_cli
from netmon.features import firewall_controller as fc, vpn_controller as vc


@pytest.mark.parametrize(
    "service", ["53/udp", "53/tcp", "80/tcp", "443/tcp", "4443/tcp"]
)
@pytest.mark.parametrize("logging", ["", "log", "log-all"])
@pytest.mark.parametrize("family", ["both", "4", "6"])
def test_vpn_off_fences_service_grant_and_retains_verified_on(
    system, monkeypatch, service, logging, family
):
    profile("wg0")
    port, proto = service.split("/")
    command = ["allow", "out", "on", "wg0"] + ([logging] if logging else [])
    command += [
        "to",
        {"both": "any", "4": "0.0.0.0/0", "6": "::/0"}[family],
        "port",
        port,
        "proto",
        proto,
    ]
    assert ufw_cli(command)[0] == 0
    app, env, logs = real_app(system, monkeypatch)
    calls = []
    monkeypatch.setattr(
        vc, "cleanup_wireguard_interfaces", lambda _a: env.live.clear() or True
    )
    monkeypatch.setattr(
        vc,
        "_show_killswitch_active_after_vpn_off_notice",
        lambda _a: calls.append("notice"),
    )
    app.debug_nm_state = None
    app.prepare_dns_for_vpn_profile_switch = lambda: calls.append("dns-prepare")
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda **_k: calls.append(
        "dns-schedule"
    )
    app.refresh_wg_profiles = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    original = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert vc.vpn_off(app, ensure_sudo=False, refresh_ui=False), logs
    status = app._read_ufw_status(verbose=True)[1]
    assert app.killswitch_is_on() and fc.classify_killswitch_state(app, status) == "on"
    assert system.state()["state"] == "on"
    assert system.load()["plan"]["blocked_interfaces"] == ["wg0"]
    assert calls == ["dns-prepare", "dns-schedule", "notice"]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == original


def test_failed_offline_preflight_preserves_on_snapshot_and_defers_dns(
    system, monkeypatch
):
    profile("wg0")
    assert (
        ufw_cli(
            ["allow", "out", "on", "wg0", "to", "any", "port", "443", "proto", "tcp"]
        )[0]
        == 0
    )
    assert ufw_cli(["deny", "out", "on", "wg0"])[0] == 0
    app, env, logs = real_app(system, monkeypatch)
    calls = []
    app.debug_nm_state = None
    app.prepare_dns_for_vpn_profile_switch = lambda: calls.append("dns-prepare")
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda **_k: calls.append(
        "dns-schedule"
    )
    monkeypatch.setattr(
        vc, "cleanup_wireguard_interfaces", lambda _a: env.live.clear() or True
    )
    original = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    before, receipt = system.capture(), system.load()
    assert not vc.vpn_off(app, ensure_sudo=False, refresh_ui=False)
    assert app._vpn_firewall_sync_pending and calls == []
    assert system.capture() == before and system.load() == receipt
    assert app.finalize_dns_after_vpn_profile_switch() is False
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert not app.__dict__.get("_vpn_firewall_sync_pending")
    assert system.capture() == original
