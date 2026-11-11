"""Hostname-only offline closure over real UFW and a capability-free kernel stub."""

import pytest

from test_review_v5 import system as system, real_app, profile
from support import ufw_cli, reboot
from netmon.features import firewall_controller as fc, vpn_controller as vc


@pytest.mark.parametrize("family", ["none", "4", "6"])
def test_hostname_only_offline_continuation_and_reconnect(system, monkeypatch, family):
    profile("wg0", "peer.example.test:51820")
    if family != "none":
        assert (
            ufw_cli(
                [
                    "allow",
                    "out",
                    "on",
                    "wg0",
                    "log",
                    "to",
                    "0.0.0.0/0" if family == "4" else "::/0",
                    "port",
                    "443",
                    "proto",
                    "tcp",
                ]
            )[0]
            == 0
        )
    app, env, logs = real_app(system, monkeypatch)
    # The native starter hides /usr/sbin except its fixed kernel stubs; UFW's
    # Python backend is real and available through the protected test transport.
    available = vc.has_cmd
    monkeypatch.setattr(vc, "has_cmd", lambda name: name == "ufw" or available(name))
    app.debug_nm_state = None
    app.prepare_dns_for_vpn_profile_switch = lambda: None
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda **_k: None
    app.refresh_wg_profiles = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    notices = []
    monkeypatch.setattr(
        vc, "cleanup_wireguard_interfaces", lambda _a: env.live.clear() or True
    )
    monkeypatch.setattr(
        vc,
        "_show_killswitch_active_after_vpn_off_notice",
        lambda _a: notices.append(True),
    )
    original = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    for _ in range(2):
        assert vc.vpn_off(app, ensure_sudo=False, refresh_ui=False), logs
        assert system.state() == {"state": "on", "closed": True}
        assert app.killswitch_is_on()
        assert (
            fc.classify_killswitch_state(app, app._read_ufw_status(verbose=True)[1])
            == "on"
        )
    assert notices == [True, True]
    assert reboot().returncode == 0
    assert system.state() == {"state": "on", "closed": True}
    assert app.killswitch_is_on()
    env.live.add("wg0")
    assert app.reconcile_vpn_slot_firewall_state(
        touched_profiles=["wg0"], refresh_ui=False
    )
    assert not system.load().get("closed")
    assert system.state()["state"] == "on" and app.killswitch_is_on()
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == original


def test_empty_continuation_after_explicit_off_cannot_reactivate(system, monkeypatch):
    profile("wg0", "peer.example.test:51820")
    app, env, logs = real_app(system, monkeypatch)
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert fc.killswitch_off_sync(app, refresh_ui=False)
    env.live.clear()
    before, receipt = system.capture(), system.load()
    assert not fc.killswitch_on_sync(app, refresh_ui=False, require_active=True)
    assert system.capture() == before and system.load() == receipt
