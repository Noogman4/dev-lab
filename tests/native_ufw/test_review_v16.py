"""G4 slot reconciliation on real UFW with a private capability-free kernel stub."""

import json
from pathlib import Path

import pytest

from test_review_v5 import system as system, profile, real_app
from support import ufw_cli, reboot
from netmon.core.ufw_snapshot import SnapshotError
from netmon.features import firewall_controller as fc, vpn_controller as vc


def observe(app, system):
    return {
        "root": system.state(),
        "boolean": app.killswitch_is_on(),
        "classification": fc.classify_killswitch_state(
            app, app._read_ufw_status(verbose=True)[1]
        ),
    }


def scene(system, monkeypatch, endpoint="198.51.100.10:51820"):
    profile("wg0", endpoint)
    assert ufw_cli(["allow", "in", "22/tcp"])[0] == 0
    assert (
        ufw_cli(
            [
                "allow",
                "out",
                "on",
                "wg0",
                "log",
                "to",
                "any",
                "port",
                "443",
                "proto",
                "tcp",
            ]
        )[0]
        == 0
    )
    app, env, logs = real_app(system, monkeypatch)
    available = vc.has_cmd
    monkeypatch.setattr(vc, "has_cmd", lambda name: name == "ufw" or available(name))
    env.live.clear()
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    profile("wg0", "peer.example.test:51820")
    logs.clear()
    return app, env, logs, before


@pytest.mark.parametrize("endpoint", ["198.51.100.10:51820", "[2001:db8::10]:51820"])
def test_offline_slot_change_to_hostname_has_consistent_closed_state(
    system, monkeypatch, endpoint
):
    app, env, logs, original = scene(system, monkeypatch, endpoint)
    assert app.reconcile_vpn_slot_firewall_state(touched_profiles=["wg0"]), logs
    expected = {
        "root": {"state": "on", "closed": True},
        "boolean": True,
        "classification": "on",
    }
    assert observe(app, system) == expected
    assert system.load()["original"] == original
    assert system.load()["plan"]["interfaces"] == []
    assert system.load()["plan"]["endpoints"] == []
    assert system.load()["plan"]["blocked_interfaces"] == ["wg0"]
    assert all(
        ":OUTPUT DROP [0:0]" in system.capture()["runtime"][af] for af in ("4", "6")
    )
    assert reboot().returncode == 0
    assert observe(app, system) == expected

    # A concrete later plan must retire the protected empty-plan marker.
    profile("wg0", "198.51.100.20:51820")
    assert app.reconcile_vpn_slot_firewall_state(touched_profiles=["wg0"]), logs
    assert not system.load().get("closed")
    assert system.load()["plan"]["endpoints"] == [["198.51.100.20", "51820"]]
    assert app.killswitch_is_on()
    profile("wg0", "peer.example.test:51820")
    env.live.add("wg0")
    assert app.reconcile_vpn_slot_firewall_state(touched_profiles=["wg0"]), logs
    assert system.load()["plan"]["interfaces"] == ["wg0"]
    assert not system.load().get("closed")
    assert observe(app, system) == {
        "root": {"state": "on"},
        "boolean": True,
        "classification": "on",
    }
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == original
    Path(
        "/work/G4-cycle-" + ("6" if endpoint.startswith("[") else "4") + ".json"
    ).write_text(
        json.dumps(
            {
                "closed": expected,
                "boot": True,
                "concrete_plan": True,
                "live_plan": True,
                "off_exact_with_user_rules": True,
            },
            indent=2,
        )
        + "\n"
    )


def test_explicit_off_after_slot_state_read_wins(system, monkeypatch):
    app, _env, logs, original = scene(system, monkeypatch)
    activate = fc.killswitch_on_sync
    observed = {}

    def interleaved_off(candidate, **kwargs):
        assert kwargs["require_active"] is True
        assert fc.killswitch_off_sync(candidate, refresh_ui=False), logs
        observed["capture"] = system.capture()
        observed["record"] = system.load()
        return activate(candidate, **kwargs)

    monkeypatch.setattr(fc, "killswitch_on_sync", interleaved_off)
    assert not app.reconcile_vpn_slot_firewall_state(touched_profiles=["wg0"])
    assert system.capture() == observed["capture"] == original
    assert system.load() == observed["record"]
    assert system.state()["state"] == "off"
    assert "Killswitch-Sollzustand vorbereitet." not in logs


def test_fresh_hostname_only_empty_activation_stays_refused(system, monkeypatch):
    profile("wg0", "peer.example.test:51820")
    app, env, _logs = real_app(system, monkeypatch)
    env.live.clear()
    before, record = system.capture(), system.load()
    assert not fc.killswitch_on_sync(app, refresh_ui=False)
    assert system.capture() == before and system.load() == record
    assert not fc.killswitch_on_sync(app, refresh_ui=False, require_active=True)
    assert system.capture() == before and system.load() == record


def test_foreign_rule_after_state_read_prevents_slot_commit(system, monkeypatch):
    app, _env, logs, _original = scene(system, monkeypatch)
    activate = fc.killswitch_on_sync
    record = system.load()
    changed = {}

    def external_rule(candidate, **kwargs):
        assert ufw_cli(["allow", "in", "2222/tcp"])[0] == 0
        changed["capture"] = system.capture()
        return activate(candidate, **kwargs)

    monkeypatch.setattr(fc, "killswitch_on_sync", external_rule)
    assert not app.reconcile_vpn_slot_firewall_state(touched_profiles=["wg0"])
    assert system.capture() == changed["capture"] and system.load() == record
    assert system.state()["state"] == "unknown"
    assert "Killswitch-Sollzustand vorbereitet." not in logs


def test_failed_slot_commit_is_recovery_and_explicit_off_restores(system, monkeypatch):
    app, _env, logs, original = scene(system, monkeypatch)

    def fail_commit(_token):
        raise SnapshotError("Injected slot commit failure")

    monkeypatch.setattr(system, "commit", fail_commit)
    assert not app.reconcile_vpn_slot_firewall_state(touched_profiles=["wg0"])
    assert system.state()["state"] == "recovery"
    assert "Killswitch-Sollzustand vorbereitet." not in logs
    assert all(
        ":OUTPUT DROP [0:0]" in system.capture()["runtime"][af] for af in ("4", "6")
    )
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == original
