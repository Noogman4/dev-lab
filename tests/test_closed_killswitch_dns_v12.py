"""Protected empty continuation and deferred DNS completion, never host I/O."""

from types import SimpleNamespace
import json

import pytest

from netmon.app import App
from netmon.core import ufw_snapshot as us
from netmon.features import firewall_controller as fc
from test_ufw_snapshot import system as system


def test_fresh_empty_plan_is_not_activation_authority(system):
    _root, _model, _backend, store, _attach = system
    before = store.capture()
    with pytest.raises(us.SnapshotError) as exc:
        store.begin({"interfaces": [], "endpoints": []})
    assert exc.value.code == "preflight"
    assert store.capture() == before and store.load() is None


def test_old_unmarked_empty_record_cannot_be_committed(system):
    _root, _model, _backend, store, attach = system
    assert fc.killswitch_on_sync(attach(), refresh_ui=False)
    row = store.load()
    row["phase"] = "applying"
    row["plan"] = {"interfaces": [], "endpoints": []}
    store.save(row)
    before = store.capture()
    with pytest.raises(us.SnapshotError):
        store.commit(row["token"])
    assert store.capture() == before and store.load()["phase"] == "applying"
    row["phase"] = "active"
    store.save(row)
    with pytest.raises(us.SnapshotError):
        store.begin({"interfaces": [], "endpoints": [], "require_active": True})
    assert store.capture() == before


@pytest.mark.parametrize(
    "metadata",
    [
        {"state": "on"},
        {"state": "off", "closed": True},
        {"state": "unknown", "closed": True},
    ],
)
def test_only_verified_protected_closed_receipt_is_accepted(metadata):
    app = SimpleNamespace(
        firewall_snapshots=SimpleNamespace(request=lambda *_a: metadata)
    )
    assert not fc._protected_closed_plan(app)


@pytest.mark.parametrize(
    "operation",
    [
        "begin",
        "command",
        "commit",
        "recovery",
        "restore",
        "acknowledge",
        "abort_unmodified",
        "removal",
    ],
)
def test_protocol_ten_cannot_skip_closed_plan_verification(monkeypatch, operation):
    calls = []
    monkeypatch.setattr(us, "trusted_helper_available", lambda: True)

    def old(args, **_k):
        calls.append(args[-1])
        return 0, json.dumps({"protocol": 10, "prepared_commands": True})

    monkeypatch.setattr("netmon.core.command.run_cmd_with_input", old)
    with pytest.raises(us.SnapshotError) as exc:
        us.UfwSnapshotClient().request(operation, {})
    assert exc.value.code == "incompatible" and calls == ["capabilities"]


def dns_app(monkeypatch):
    app = App.__new__(App)
    calls, queue = [], []
    app.log_safe = lambda _message: None
    app.get_wg_interfaces = lambda **_kw: []
    app.after = lambda _delay, callback: queue.append(callback)
    app._collect_dot_status = lambda **_k: {}
    app._set_dot_state = lambda *_a, **_k: None
    app._restore_isp_dns_after_vpn_switch = lambda: calls.append("finalize")
    app.rebuild_dns_guard_whitelist = lambda: None
    app.run_dns_guard_check_once = lambda: None
    app.update_dns_controls_state = lambda: None
    app.run_dns_leak_check = lambda **_k: None

    def prepare():
        calls.append("prepare")
        app._vpn_dns_prepare_deferred = False
        app._dns_finalize_token = int(app.__dict__.get("_dns_finalize_token", 0)) + 1
        app.__dict__.pop("_vpn_dns_resume_token", None)
        if not app.__dict__.get("_vpn_firewall_sync_pending"):
            app._vpn_dns_completion_deferred = False

    app.prepare_dns_for_vpn_profile_switch = prepare
    monkeypatch.setattr(fc, "firewall_recovery_pending", lambda _a: False)
    return app, calls, queue


@pytest.mark.parametrize("coordinator", [False, True])
def test_deferred_completion_runs_once_after_outer_operation_releases(
    monkeypatch, coordinator
):
    app, calls, queue = dns_app(monkeypatch)
    app._vpn_dns_prepare_deferred = True
    if coordinator:
        from netmon.netmon_ops import NetworkOperationCoordinator

        app.network_ops_coordinator = NetworkOperationCoordinator()
    assert app._try_begin_network_operation("VPN AUS")
    assert app._try_begin_network_operation("Killswitch AUS")
    app._vpn_firewall_sync_pending = True
    assert app.finalize_dns_after_vpn_profile_switch() is False
    app.__dict__.pop("_vpn_firewall_sync_pending")
    app._end_network_operation()
    assert not queue and not calls
    app._end_network_operation()
    assert len(queue) == 1
    app._resume_deferred_vpn_dns()
    assert len(queue) == 1
    resume = queue.pop(0)
    resume()
    resume()  # Duplicate delivery has no second preparation.
    assert calls == ["prepare"] and len(queue) == 1
    finalize = queue.pop(0)
    finalize()
    finalize()
    assert calls == ["prepare", "finalize"]
    assert not app.__dict__.get("_vpn_dns_completion_deferred")


def test_new_transition_invalidates_old_queued_completion(monkeypatch):
    app, calls, queue = dns_app(monkeypatch)
    app._vpn_dns_completion_deferred = True
    app._resume_deferred_vpn_dns()
    old = queue.pop()
    app.prepare_dns_for_vpn_profile_switch()
    app._schedule_dns_finalize_after_vpn_profile_switch()
    old()
    assert calls == ["prepare"]
    queue.pop()()
    assert calls == ["prepare", "finalize"]


def test_recovery_during_queued_resume_does_not_spin(monkeypatch):
    app, calls, queue = dns_app(monkeypatch)
    app._vpn_dns_completion_deferred = True
    app._resume_deferred_vpn_dns()
    monkeypatch.setattr(fc, "firewall_recovery_pending", lambda _a: True)
    queue.pop()()
    assert not queue and not calls and app._vpn_dns_completion_deferred


def test_old_paused_callback_cannot_bypass_preparation_after_off(monkeypatch):
    app, calls, queue = dns_app(monkeypatch)
    app._vpn_dns_prepare_deferred = True
    app._schedule_dns_finalize_after_vpn_profile_switch()
    old = queue.pop()
    app._vpn_firewall_sync_pending = True
    old()
    assert not calls and app._vpn_dns_completion_deferred
    app.__dict__.pop("_vpn_firewall_sync_pending")
    app._resume_deferred_vpn_dns()
    old()
    assert not calls
    queue.pop(0)()
    assert calls == ["prepare"]
    queue.pop(0)()
    assert calls == ["prepare", "finalize"]


def test_monitor_schedule_cannot_skip_deferred_preparation(monkeypatch):
    app, calls, queue = dns_app(monkeypatch)
    app._vpn_dns_prepare_deferred = True
    app._vpn_dns_completion_deferred = True
    app._schedule_dns_finalize_after_vpn_profile_switch()
    assert not calls and len(queue) == 1
    queue.pop(0)()
    assert calls == ["prepare"]
    queue.pop(0)()
    assert calls == ["prepare", "finalize"]


def test_dns_guard_direct_mutation_defers_while_sync_pending(monkeypatch):
    app = App.__new__(App)
    app._vpn_firewall_sync_pending = True
    app._auto_dns_control_available = lambda: pytest.fail("DNS mutation during pause")
    assert app.enforce_dns_clean()[0] is False
