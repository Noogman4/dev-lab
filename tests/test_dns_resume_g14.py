"""G2 deferred preparation and G3 truthful DNS pause diagnostics."""

import pytest
from types import SimpleNamespace

from netmon.features import vpn_controller as vc
from test_closed_killswitch_dns_v12 import dns_app


@pytest.mark.parametrize("sync_pending", [False, True])
@pytest.mark.parametrize("network_busy", [False, True])
@pytest.mark.parametrize("recovery", [False, True])
def test_dns_pause_diagnostic_preserves_checks_and_deferral(
    monkeypatch, sync_pending, network_busy, recovery
):
    from netmon.features import firewall_controller as fc

    app, calls, queue = dns_app(monkeypatch)
    logs, recovery_checks = [], []
    app.log_safe = logs.append
    app._vpn_firewall_sync_pending = sync_pending
    app.network_active_operation = "VPN wechseln" if network_busy else ""
    app._dns_finalize_token = 7
    app._dns_finalize_scheduled_token = 7
    app._vpn_dns_resume_token = 7

    def recovery_pending(_app):
        recovery_checks.append(True)
        return recovery

    monkeypatch.setattr(fc, "firewall_recovery_pending", recovery_pending)
    result = app.finalize_dns_after_vpn_profile_switch()

    # A busy operation still defers the Root query until after it releases.
    assert len(recovery_checks) == int(not sync_pending and not network_busy)
    assert app._dns_finalize_token == 8
    assert "_dns_finalize_scheduled_token" not in app.__dict__
    assert "_vpn_dns_resume_token" not in app.__dict__
    assert not queue
    if sync_pending or network_busy or recovery:
        assert result is False
        assert app._vpn_dns_completion_deferred
        assert not calls
        reason = (
            "Netzoperation läuft; erneute Prüfung nach deren Abschluss."
            if network_busy and not sync_pending
            else "Firewall-Wiederherstellung ungeklärt."
        )
        assert logs == [f"DNS-Abschluss pausiert: {reason}"]
    else:
        assert not app._vpn_dns_completion_deferred
        assert calls == ["finalize"]
        assert not logs


def test_failed_wireguard_enumeration_is_not_confirmed_offline(monkeypatch):
    monkeypatch.setattr(vc, "run_cmd", lambda *_a, **_kw: (1, "unavailable"))
    app = SimpleNamespace()
    assert vc.get_wg_interfaces(app) == []  # Existing display behavior.
    with pytest.raises(RuntimeError, match="could not be read"):
        vc.get_wg_interfaces(app, strict=True)


@pytest.mark.parametrize("reason", ["firewall", "network_only"])
@pytest.mark.parametrize("live", [False, True])
def test_deferred_completion_prepares_only_when_missing_and_offline(
    monkeypatch, reason, live
):
    app, calls, ui = dns_app(monkeypatch)
    app.get_wg_interfaces = lambda **_kw: ["wg0"] if live else []
    if reason == "firewall":
        vc.pause_dns_for_firewall_sync(app)
        app.__dict__.pop("_vpn_firewall_sync_pending")
    else:
        assert app._try_begin_network_operation("unrelated operation")
        assert app.finalize_dns_after_vpn_profile_switch() is False
        app._end_network_operation()
    app._resume_deferred_vpn_dns()
    assert len(ui) == 1 and not calls
    old = ui.pop(0)
    old()
    old()
    assert len(ui) == 1
    finish = ui.pop(0)
    finish()
    finish()
    assert calls == (
        ["prepare", "finalize"] if reason == "firewall" and not live else ["finalize"]
    )
    assert not app._vpn_dns_completion_deferred


def test_tunnel_appearing_after_enqueue_skips_old_preparation(monkeypatch):
    app, calls, ui = dns_app(monkeypatch)
    interfaces = []
    app.get_wg_interfaces = lambda **_kw: interfaces
    vc.pause_dns_for_firewall_sync(app)
    app.__dict__.pop("_vpn_firewall_sync_pending")
    app._resume_deferred_vpn_dns()
    interfaces.append("wg0")
    ui.pop(0)()
    ui.pop(0)()
    assert calls == ["finalize"]


def test_unknown_tunnel_state_never_authorizes_destructive_preparation(monkeypatch):
    app, calls, ui = dns_app(monkeypatch)
    app.get_wg_interfaces = lambda **_kw: (_ for _ in ()).throw(
        RuntimeError("enumeration unavailable")
    )
    vc.pause_dns_for_firewall_sync(app)
    app.__dict__.pop("_vpn_firewall_sync_pending")
    app._resume_deferred_vpn_dns()
    ui.pop(0)()
    assert not calls and not ui


@pytest.mark.parametrize("live", [False, True])
def test_live_tunnel_decision_is_under_network_coordinator(monkeypatch, live):
    from netmon.netmon_ops import NetworkOperationCoordinator

    app, calls, ui = dns_app(monkeypatch)
    app.network_ops_coordinator = NetworkOperationCoordinator()
    observations = []

    def interfaces(**_kw):
        observations.append(app.network_active_operation)
        return ["wg0"] if live else []

    app.get_wg_interfaces = interfaces
    vc.pause_dns_for_firewall_sync(app)
    app.__dict__.pop("_vpn_firewall_sync_pending")
    app._resume_deferred_vpn_dns()
    ui.pop(0)()
    ui.pop(0)()
    assert observations == ["DNS-Abschluss fortsetzen"]
    assert calls == (["finalize"] if live else ["prepare", "finalize"])
