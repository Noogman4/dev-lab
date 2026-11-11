"""G1/G2 regression on actual App/UFW; capability-free private kernel stub."""

import json
from pathlib import Path

import pytest

from test_review_v5 import system as system, profile, real_app
from netmon.features import firewall_controller as fc, vpn_controller as vc
import netmon.app as am


def closed(system, monkeypatch):
    profile("wg0", "peer.example.test:51820")
    app, env, logs = real_app(system, monkeypatch)
    app.debug_nm_state = None
    app.prepare_dns_for_vpn_profile_switch = lambda: None
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda **_kw: None
    app.refresh_wg_profiles = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    monkeypatch.setattr(
        vc, "cleanup_wireguard_interfaces", lambda _a: env.live.clear() or True
    )
    monkeypatch.setattr(
        vc, "_show_killswitch_active_after_vpn_off_notice", lambda _a: None
    )
    original = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False)
    assert vc.vpn_off(app, ensure_sudo=False, refresh_ui=False)
    assert system.state().get("closed") is True
    return app, env, logs, original


def save(name, row):
    Path("/work/" + name + ".json").write_text(json.dumps(row, indent=2) + "\n")


def test_G1_internet_on_retains_closed_killswitch(system, monkeypatch):
    app, _env, logs, original = closed(system, monkeypatch)
    before = system.capture()
    app.internet_suspend_state = {
        "killswitch_was_active": True,
        "vpn_was_active": False,
    }
    app.vpn_before_internet_off = ""
    app._state_coordinator = lambda: None
    app._clear_internet_suspend_request = lambda: None
    app._internet_suspend_restore_profile = lambda: ""
    app.wait_for_network_ready = lambda **_kw: True
    app._schedule_refresh_burst = lambda: None
    app.after = lambda *_a: None
    monkeypatch.setattr(am.time, "sleep", lambda _s: None)

    def command(args, **_kw):
        assert args == ["sudo", "-n", "nmcli", "networking", "on"]
        return 0, "private NM stub"

    monkeypatch.setattr(am, "run_cmd", command)
    result = app._internet_on_sync()
    after = system.capture()
    assert result is True and system.state().get("closed") is True
    assert after == before
    assert all(":OUTPUT DROP [0:0]" in after["runtime"][af] for af in ("4", "6"))
    assert (
        fc.killswitch_off_sync(app, refresh_ui=False) and system.capture() == original
    )
    save(
        "G1-internet-on-V14",
        {
            "return": result,
            "root": system.state(),
            "before": before,
            "after": after,
            "logs": logs,
        },
    )


def test_G1_game_preset_cannot_automatically_pause_killswitch(system, monkeypatch):
    app, _env, logs, original = closed(system, monkeypatch)
    app.game_mode_state = {}
    app._active_game_mode_preset = lambda: {
        "id": "lan_host",
        "label": "LAN",
        "pause_killswitch": True,
    }
    app._security_query_log_level = lambda: "LOW"
    app.is_dot_active = lambda: False
    app.is_vpn_active = lambda: False
    app._game_mode_recommended_exception_sets = lambda _p: []
    app.confirm_game_mode_apply = lambda *_a, **_kw: True
    app.refresh_game_mode_status = lambda: None
    app._apply_game_mode_dns_guard = lambda _enabled: None
    before = system.capture()
    assert app.enable_game_mode() is False
    assert system.state().get("closed") is True and system.capture() == before
    assert fc.killswitch_off_sync(app, refresh_ui=False)
    assert app.enable_game_mode() is True  # Explicit user OFF permits the preset.
    result = app.disable_game_mode()
    assert result is True and system.state()["state"] == "off"
    assert system.capture() == original
    save(
        "G1-game-mode-V14",
        {"restore_return": result, "root": system.state(), "logs": logs},
    )


@pytest.mark.parametrize("reason", ["firewall", "network_only"])
@pytest.mark.parametrize("live", [False, True])
def test_G2_resume_does_not_prepare_over_live_tunnel(system, monkeypatch, reason, live):
    profile("wg0")
    app, env, _logs = real_app(system, monkeypatch)
    app.get_wg_interfaces = lambda **_kw: sorted(env.live)
    if not live:
        env.live.clear()
    actions, queue = [], []
    app.after = lambda _delay, fn: queue.append(fn)
    monkeypatch.setattr(fc, "firewall_recovery_pending", lambda _a: False)

    def command(args, **_kw):
        actions.append(args)
        return 0, (
            "Link 4 (wg0)"
            if args == ["resolvectl", "status"]
            else "private DNS command stub"
        )

    monkeypatch.setattr(am, "run_cmd", command)

    app._remove_root_text_file = lambda path: actions.append(["remove", path]) or (
        True,
        "",
    )
    app.set_dns_guard_state = lambda *_a, **_kw: None
    if reason == "network_only":
        app.network_active_operation = "unrelated operation"
        assert app.finalize_dns_after_vpn_profile_switch() is False
        app.network_active_operation = ""
    else:
        vc.pause_dns_for_firewall_sync(app)
        app.__dict__.pop("_vpn_firewall_sync_pending")
    app._resume_deferred_vpn_dns()
    queue.pop(0)()
    expected = reason == "firewall" and not live
    assert (["sudo", "-n", "resolvectl", "revert", "wg0"] in actions) is expected
    assert (
        ["sudo", "-n", "systemctl", "restart", "systemd-resolved"] in actions
    ) is expected
    assert any(row[:1] == ["remove"] for row in actions) is expected
    save(
        "G2-live-" + reason + "-" + str(live) + "-V14",
        {"interfaces": app.get_wg_interfaces(), "captured_DNS_actions": actions},
    )
