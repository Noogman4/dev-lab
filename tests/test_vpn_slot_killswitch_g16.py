"""G4: only a protected active slot plan can request active-only continuation."""

from types import SimpleNamespace

import pytest

from netmon.features import firewall_controller as fc, vpn_controller as vc


def slot_app(monkeypatch, state, boolean=False):
    calls, logs = [], []
    app = SimpleNamespace(
        firewall_snapshots=(
            SimpleNamespace(state=lambda: state) if state is not None else None
        ),
        _collect_referenced_vpn_profiles=lambda **_kw: [],
        _collect_interface_rules_for_profiles=lambda _p: [],
        _collect_endpoint_rules_for_profiles=lambda _p: [],
        killswitch_is_on=lambda: boolean,
        _killswitch_on_sync=lambda **kw: calls.append(("legacy", kw)) or True,
        _apply_profile_ufw_rules_non_killswitch=lambda i, e: calls.append(
            ("non_killswitch", i, e)
        )
        or True,
        log=logs.append,
        log_debug=lambda _msg: None,
    )
    monkeypatch.setattr(vc, "has_cmd", lambda _name: True)
    return app, calls, logs


@pytest.mark.parametrize("success", [False, True])
def test_protected_on_continues_without_using_local_boolean(monkeypatch, success):
    app, calls, logs = slot_app(monkeypatch, "on")
    app.killswitch_is_on = lambda: pytest.fail("local Boolean is not authority")

    def protected(candidate, **kw):
        assert candidate is app
        calls.append(("protected", kw))
        return success

    monkeypatch.setattr(fc, "killswitch_on_sync", protected)
    assert vc.reconcile_vpn_slot_firewall_state(app, refresh_ui=True) is success
    assert calls == [("protected", {"refresh_ui": True, "require_active": True})]
    assert ("Killswitch-Sollzustand vorbereitet." in logs) is success
    assert "_vpn_dns_prepare_deferred" not in app.__dict__
    assert "_vpn_firewall_sync_pending" not in app.__dict__


@pytest.mark.parametrize("state", [None, "absent", "off", "reviewed"])
def test_non_killswitch_slot_behavior_is_preserved(monkeypatch, state):
    app, calls, _logs = slot_app(monkeypatch, state)
    monkeypatch.setattr(
        fc, "killswitch_on_sync", lambda *_a, **_kw: pytest.fail("fresh authority")
    )
    assert vc.reconcile_vpn_slot_firewall_state(app)
    assert calls == [("non_killswitch", [], [])]


def test_unmanaged_legacy_diagnostic_retains_old_call_contract(monkeypatch):
    app, calls, _logs = slot_app(monkeypatch, None, boolean=True)
    monkeypatch.setattr(
        fc, "killswitch_on_sync", lambda *_a, **_kw: pytest.fail("protected claim")
    )
    assert vc.reconcile_vpn_slot_firewall_state(app)
    assert calls == [("legacy", {"refresh_ui": False})]


@pytest.mark.parametrize("state", ["recovery", "unknown"])
def test_uncertain_root_state_blocks_before_slot_mutation(monkeypatch, state):
    app, calls, logs = slot_app(monkeypatch, state, boolean=True)
    assert not vc.reconcile_vpn_slot_firewall_state(app)
    assert not calls
    assert logs == ["VPN/UFW-Abgleich gesperrt: Firewall-Wiederherstellung ungeklärt."]
