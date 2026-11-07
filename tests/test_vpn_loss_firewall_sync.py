"""F3: protected authority and deferred external-loss worker, no host actions."""

from types import SimpleNamespace

import pytest

from netmon.features import firewall_controller as fc, vpn_controller as vc
from test_closed_killswitch_dns_v12 import dns_app


@pytest.mark.parametrize("state", ["absent", "off", "reviewed", "unknown", "recovery"])
def test_teardown_does_not_invent_authority(monkeypatch, state):
    app = SimpleNamespace(
        firewall_snapshots=SimpleNamespace(state=lambda: state),
        log_safe=lambda _m: None,
    )
    monkeypatch.setattr(
        fc, "killswitch_on_sync", lambda *_a, **_k: pytest.fail("fresh activation")
    )
    assert vc.sync_killswitch_after_tunnel_change(app) is (
        state in {"absent", "off", "reviewed"}
    )
    assert bool(app.__dict__.get("_vpn_firewall_sync_pending")) is (
        state in {"unknown", "recovery"}
    )


@pytest.mark.parametrize("concurrent_off", [False, True])
def test_teardown_uses_root_not_post_teardown_boolean(monkeypatch, concurrent_off):
    state, calls = ["on"], []
    app = SimpleNamespace(
        firewall_snapshots=SimpleNamespace(state=lambda: state[0]),
        log_safe=lambda _m: None,
    )
    app.killswitch_is_on = lambda: pytest.fail("Boolean cannot authorize resync")

    def sync(_app, **kwargs):
        calls.append(kwargs)
        if concurrent_off:
            state[0] = "off"
            return False
        app.__dict__.pop("_vpn_firewall_sync_pending", None)
        return True

    monkeypatch.setattr(fc, "killswitch_on_sync", sync)
    assert vc.sync_killswitch_after_tunnel_change(app)
    assert calls == [{"refresh_ui": False, "require_active": True}]
    assert not app.__dict__.get("_vpn_firewall_sync_pending")


@pytest.mark.parametrize("coordinator", [False, True])
@pytest.mark.parametrize("success", [False, True])
def test_external_loss_waits_for_operation_and_dns_waits_for_worker(
    monkeypatch, coordinator, success
):
    app, calls, ui = dns_app(monkeypatch)
    if coordinator:
        from netmon.netmon_ops import NetworkOperationCoordinator

        app.network_ops_coordinator = NetworkOperationCoordinator()
    jobs, syncs = [], []
    app.run_async = lambda fn, **_k: jobs.append(fn)
    app.get_wg_interfaces = lambda **_kw: []
    app.killswitch_is_on = lambda: False
    app.set_dns_guard_state = lambda *_a, **_k: None
    app.update_dns_controls_state = lambda: None

    def sync(_app):
        syncs.append(app.network_active_operation)
        if success:
            app.__dict__.pop("_vpn_firewall_sync_pending", None)
        return success

    monkeypatch.setattr(vc, "sync_killswitch_after_tunnel_change", sync)
    assert app._try_begin_network_operation("Other operation")
    app.on_vpn_state_changed(False)
    assert not jobs and not calls and not syncs
    app._end_network_operation()
    assert len(jobs) == 1 and not calls
    app._queue_vpn_loss_firewall_sync()
    assert len(jobs) == 1
    jobs.pop()()
    assert syncs == ["VPN-Verlust abgleichen"]
    assert not app._vpn_loss_firewall_pending
    if success:
        assert len(ui) == 1 and not calls
        ui.pop(0)()
        ui.pop(0)()
        assert calls == ["prepare", "finalize"]
    else:
        assert app._vpn_firewall_sync_pending and not ui and not calls
        app._resume_deferred_vpn_dns()
        assert not jobs  # No automatic repeat of a rejected preflight.


def test_external_loss_worker_observes_new_current_state(monkeypatch):
    app, calls, ui = dns_app(monkeypatch)
    jobs, seen = [], []
    app.run_async = lambda fn, **_k: jobs.append(fn)
    live = []
    app.get_wg_interfaces = lambda **_kw: live
    app.killswitch_is_on = lambda: True
    app.set_dns_guard_state = lambda *_a, **_k: None
    monkeypatch.setattr(
        fc, "killswitch_on_sync", lambda *_a, **_kw: pytest.fail("Root OFF must win")
    )
    state = ["on"]
    app.firewall_snapshots = SimpleNamespace(
        state=lambda: seen.append(list(live)) or state[0]
    )
    app.on_vpn_state_changed(False)
    assert len(jobs) == 1 and not seen
    live.append("wg1")  # A newer tunnel/explicit OFF preceded worker execution.
    state[0] = "off"
    jobs.pop()()
    assert seen == [["wg1"]] and not app.__dict__.get("_vpn_firewall_sync_pending")
    ui.pop(0)()
    ui.pop(0)()
    assert calls == ["finalize"]


def test_unexpected_worker_error_keeps_dns_paused(monkeypatch):
    app, calls, ui = dns_app(monkeypatch)
    app.run_async = lambda fn, **_kw: fn()
    app.set_dns_guard_state = lambda *_a, **_kw: None
    monkeypatch.setattr(
        vc,
        "sync_killswitch_after_tunnel_change",
        lambda _app: (_ for _ in ()).throw(RuntimeError("injected")),
    )
    app.on_vpn_state_changed(False)
    assert app._vpn_firewall_sync_pending and not app._vpn_loss_firewall_pending
    assert not calls and not ui
