"""F3 on actual App/UFW, private profiles and capability-free kernel stub."""

from types import SimpleNamespace

import pytest

from test_review_v5 import system as system, real_app, profile
from support import ufw_cli
from netmon.features import firewall_controller as fc, vpn_controller as vc


def scene(system, monkeypatch, *, hostname=False, second=False):
    profile("wg0", "peer.example.test:51820" if hostname else "198.51.100.10:51820")
    if second:
        profile("wg1", "198.51.100.20:51820")
    for family in ("0.0.0.0/0", "::/0"):
        assert (
            ufw_cli(
                [
                    "allow",
                    "out",
                    "on",
                    "wg0",
                    "log",
                    "to",
                    family,
                    "port",
                    "443",
                    "proto",
                    "tcp",
                ]
            )[0]
            == 0
        )
    app, env, logs = real_app(
        system, monkeypatch, slots=("wg0", "wg1") if second else ("wg0",)
    )
    app.debug_nm_state = None
    app.prepare_dns_for_vpn_profile_switch = lambda: None
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda **_kw: None
    app.refresh_wg_profiles = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app._check_wireguard_profile_for_multiple_endpoints = lambda *_a: None
    app.update_dns_controls_state = lambda: None
    app.set_dns_guard_state = lambda *_a, **_kw: None
    app.after = lambda *_a: None
    available = vc.has_cmd
    monkeypatch.setattr(vc, "has_cmd", lambda name: name == "ufw" or available(name))
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    return app, env, logs, before


def verified_on(app, system):
    assert system.state()["state"] == "on" and app.killswitch_is_on()
    assert (
        fc.classify_killswitch_state(app, app._read_ufw_status(verbose=True)[1]) == "on"
    )
    assert all(
        ":OUTPUT DROP [0:0]" in system.capture()["runtime"][af] for af in ("4", "6")
    )


@pytest.mark.parametrize("hostname", [False, True])
def test_external_tunnel_loss_is_reconciled_before_dns(system, monkeypatch, hostname):
    app, env, logs, before = scene(system, monkeypatch, hostname=hostname)
    jobs = []
    app.run_async = lambda fn, **_kw: jobs.append(fn)
    env.live.clear()
    assert not app.killswitch_is_on()
    app.on_vpn_state_changed(False)
    assert app._vpn_firewall_sync_pending and len(jobs) == 1
    jobs.pop()()
    verified_on(app, system)
    assert not app.__dict__.get("_vpn_firewall_sync_pending")
    assert system.load()["plan"]["blocked_interfaces"] == ["wg0"]
    assert any("Killswitch bleibt aktiv" in log for log in logs)
    assert fc.killswitch_off_sync(app, refresh_ui=False) and system.capture() == before


@pytest.mark.parametrize("partial_cleanup", [False, True])
def test_failed_switch_or_partial_cleanup_preserves_current_tunnels(
    system, monkeypatch, partial_cleanup
):
    app, env, logs, before = scene(system, monkeypatch, second=True)
    app.network_service = SimpleNamespace(
        file_exists=lambda _p: (0, ""),
        wg_quick_up=lambda *_a, **_kw: (1, "injected failure"),
    )

    def cleanup(_app):
        env.live.clear()
        if partial_cleanup:
            env.live.add("wg1")
        return not partial_cleanup

    monkeypatch.setattr(vc, "cleanup_wireguard_interfaces", cleanup)
    assert vc.vpn_switch(app, "wg1", ensure_sudo=False, refresh_ui=False) is False
    verified_on(app, system)
    assert system.load()["plan"]["interfaces"] == (["wg1"] if partial_cleanup else [])
    assert not app.__dict__.get("_vpn_firewall_sync_pending")
    assert fc.killswitch_off_sync(app, refresh_ui=False) and system.capture() == before


def test_rejected_loss_preflight_keeps_firewall_and_dns_paused(system, monkeypatch):
    app, env, logs, before = scene(system, monkeypatch)
    # Add late original DENY to a new pre-state, while the managed KS is off.
    assert fc.killswitch_off_sync(app, refresh_ui=False)
    assert system.capture() == before
    assert ufw_cli(["deny", "out", "on", "wg0"])[0] == 0
    original = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False)
    active, receipt = system.capture(), system.load()
    env.live.clear()
    app.on_vpn_state_changed(False)  # Native fixture executes worker synchronously.
    assert app._vpn_firewall_sync_pending
    assert system.capture() == active and system.load() == receipt
    assert app.finalize_dns_after_vpn_profile_switch() is False
    assert (
        fc.killswitch_off_sync(app, refresh_ui=False) and system.capture() == original
    )


def test_queued_loss_after_explicit_off_never_reactivates(system, monkeypatch):
    app, env, _logs, before = scene(system, monkeypatch)
    jobs = []
    app.run_async = lambda fn, **_kw: jobs.append(fn)
    env.live.clear()
    app.on_vpn_state_changed(False)
    system.restore()
    receipt = system.load()
    jobs.pop()()
    assert system.state()["state"] == "off"
    assert system.capture() == before and system.load() == receipt
    assert not app.__dict__.get("_vpn_firewall_sync_pending")
