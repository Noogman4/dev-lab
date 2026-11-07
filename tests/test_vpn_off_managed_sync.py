"""Offline resync authority, DNS deferral and concurrent explicit OFF."""

import json
from types import SimpleNamespace

import pytest

from netmon.app import App
from netmon.core import ufw_snapshot as us
from netmon.features import firewall_controller as fc, vpn_controller as vc
from test_ufw_snapshot import system as system


@pytest.mark.parametrize("phase", [None, "off", "reviewed", "recovery", "applying"])
def test_active_only_begin_never_creates_or_revives_authority(system, phase):
    _root, _model, _backend, store, attach = system
    if phase is not None:
        assert fc.killswitch_on_sync(attach(), refresh_ui=False)
        if phase == "off":
            store.restore()
        else:
            row = store.load()
            row["phase"] = phase
            store.save(row)
    before, receipt = store.capture(), store.load()
    with pytest.raises(us.SnapshotError) as exc:
        store.begin({"interfaces": [], "endpoints": [], "require_active": True})
    assert exc.value.code == "not_active"
    assert store.capture() == before and store.load() == receipt


@pytest.mark.parametrize("value", [None, 0, 1, "true", [], {}])
def test_active_only_precondition_is_strict_boolean(system, value):
    _root, _model, _backend, store, _attach = system
    before = store.capture()
    with pytest.raises(us.SnapshotError):
        store.begin({"interfaces": [], "endpoints": [], "require_active": value})
    assert store.capture() == before and store.load() is None


def test_active_resync_preserves_original_and_verified_off_clears_pending(system):
    _root, _model, _backend, store, attach = system
    app = attach()
    original = store.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False)
    app._vpn_firewall_sync_pending = True
    assert fc.killswitch_on_sync(app, refresh_ui=False, require_active=True)
    assert not app.__dict__.get("_vpn_firewall_sync_pending")
    assert store.load()["original"] == original
    app._vpn_firewall_sync_pending = True
    assert fc.killswitch_off_sync(app, refresh_ui=False)
    assert not app.__dict__.get("_vpn_firewall_sync_pending")
    assert store.capture() == original


def test_delayed_resync_after_off_cannot_activate_or_reuse_old_token(system):
    _root, _model, _backend, store, attach = system
    app = attach()
    assert fc.killswitch_on_sync(app, refresh_ui=False)
    old_token = app.firewall_snapshots.token
    store.restore()  # Another privileged actor explicitly switched OFF.
    before, receipt = store.capture(), store.load()
    assert not fc.killswitch_on_sync(app, refresh_ui=False, require_active=True)
    with pytest.raises(us.SnapshotError):
        store.command(old_token, ["default", "deny", "outgoing"])
    assert store.capture() == before and store.load() == receipt


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
def test_protocol_nine_cannot_ignore_active_only_requirement(monkeypatch, operation):
    calls = []

    def old_helper(arguments, **_kwargs):
        calls.append(arguments[-1])
        return 0, json.dumps({"protocol": 9, "prepared_commands": True})

    monkeypatch.setattr(us, "trusted_helper_available", lambda: True)
    monkeypatch.setattr("netmon.core.command.run_cmd_with_input", old_helper)
    with pytest.raises(us.SnapshotError) as exc:
        us.UfwSnapshotClient().request(operation, {})
    assert exc.value.code == "incompatible" and calls == ["capabilities"]


def workflow(monkeypatch, state="on", sync=True, concurrent_off=False):
    calls, logs = [], []
    protected = [state]
    active = [False]
    app = SimpleNamespace(
        _try_begin_network_operation=lambda _label: True,
        _end_network_operation=lambda: calls.append("end"),
        debug_nm_state=None,
        log_safe=logs.append,
        log=logs.append,
        log_debug=lambda *_a: None,
        tr=lambda key, fallback=None: fallback or key,
        firewall_snapshots=SimpleNamespace(state=lambda: protected[0]),
        prepare_dns_for_vpn_profile_switch=lambda: calls.append("dns-prepare"),
        _schedule_dns_finalize_after_vpn_profile_switch=lambda **_k: calls.append(
            "dns-schedule"
        ),
        killswitch_is_on=lambda: active[0],
        refresh_wg_profiles=lambda: None,
        update_ipv6_controls_state_safe=lambda: None,
        refresh_safe=lambda: None,
    )

    def cleanup(_app):
        calls.append("cleanup")
        assert (
            state not in {"on", "unknown", "recovery"} or app._vpn_firewall_sync_pending
        )
        return True

    def resync(_app, **kwargs):
        assert kwargs == {"refresh_ui": False, "require_active": True}
        calls.append("resync")
        if concurrent_off:
            protected[0] = "off"
        if sync:
            active[0] = True
            app.__dict__.pop("_vpn_firewall_sync_pending", None)
        return sync

    monkeypatch.setattr(vc, "cleanup_wireguard_interfaces", cleanup)
    monkeypatch.setattr(fc, "killswitch_on_sync", resync)
    monkeypatch.setattr(
        vc,
        "_show_killswitch_active_after_vpn_off_notice",
        lambda _a: calls.append("notice"),
    )
    return app, calls, logs


def test_vpn_off_syncs_before_dns_and_notice(monkeypatch):
    app, calls, _logs = workflow(monkeypatch)
    assert vc.vpn_off(app, ensure_sudo=False, refresh_ui=False)
    assert calls == [
        "cleanup",
        "resync",
        "dns-prepare",
        "dns-schedule",
        "notice",
        "end",
    ]


@pytest.mark.parametrize("state", ["on", "unknown", "recovery"])
def test_failed_offline_sync_defers_dns_and_reports_error(monkeypatch, state):
    app, calls, logs = workflow(monkeypatch, state=state, sync=False)
    assert not vc.vpn_off(app, ensure_sudo=False, refresh_ui=False)
    assert app._vpn_firewall_sync_pending
    assert "dns-prepare" not in calls and "dns-schedule" not in calls
    assert "notice" not in calls and any("pausiert" in line for line in logs)
    assert not any("VPN deaktiviert." in line for line in logs)


@pytest.mark.parametrize("state", ["off", "absent", "reviewed"])
def test_vpn_off_does_not_invent_active_authority(monkeypatch, state):
    app, calls, _logs = workflow(monkeypatch, state=state)
    assert vc.vpn_off(app, ensure_sudo=False, refresh_ui=False)
    assert "resync" not in calls and "notice" not in calls


def test_explicit_off_wins_over_delayed_offline_sync(monkeypatch):
    app, calls, _logs = workflow(monkeypatch, sync=False, concurrent_off=True)
    assert vc.vpn_off(app, ensure_sudo=False, refresh_ui=False)
    assert not app.__dict__.get("_vpn_firewall_sync_pending")
    assert calls.count("resync") == 1 and "notice" not in calls


def test_already_scheduled_dns_finalizer_stops_at_pending_sync():
    app = App.__new__(App)
    app._vpn_firewall_sync_pending = True
    app.log_safe = lambda _message: None
    app._restore_isp_dns_after_vpn_switch = lambda: pytest.fail(
        "ISP release during pending sync"
    )
    app._collect_dot_status = lambda **_k: pytest.fail(
        "DNS finalization during pending sync"
    )
    assert app.finalize_dns_after_vpn_profile_switch() is False
