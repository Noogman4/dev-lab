"""Persistent diagnostics and guarded errors; all firewall writes are fake."""

from copy import deepcopy
import json
import os
from types import SimpleNamespace

import pytest

from netmon.core.killswitch_journal import KillswitchJournal
from netmon.features import firewall_controller as firewall
from test_killswitch_incident import app_context, configured_model
from test_killswitch_failure_recovery import (
    simulated_snapshot_transport as simulated_snapshot_transport,
    synthetic_kernel_links as synthetic_kernel_links,
)
from tools import netmon


@pytest.fixture(autouse=True)
def verified_interface(monkeypatch):
    monkeypatch.setattr(
        firewall.nm_ownership, "verified_interface", lambda name: {"name": name}
    )


def application(model, tmp_path):
    app = app_context(model)
    app.killswitch_journal = KillswitchJournal(tmp_path / "state")
    return app


@pytest.mark.parametrize(
    "phase", ["applying", "active", "restoring", "recovery_required", "off_verified"]
)
def test_journal_survives_new_instance_without_firewall_data(tmp_path, phase):
    journal = KillswitchJournal(tmp_path / "state")
    assert journal.phase() == "absent"
    journal.mark(phase)
    assert KillswitchJournal(tmp_path / "state").phase() == phase
    path = tmp_path / "state" / "killswitch-state.json"
    assert path.stat().st_mode & 0o777 == 0o600
    assert set(json.loads(path.read_text())) == {"version", "phase", "time"}


@pytest.mark.parametrize(
    "damage",
    ["invalid_json", "future_phase", "permissions", "symlink", "hardlink", "oversize"],
)
def test_damaged_journal_cannot_be_read_as_completed(tmp_path, damage):
    journal = KillswitchJournal(tmp_path / "state")
    journal.mark("off_verified")
    path = tmp_path / "state" / "killswitch-state.json"
    if damage == "invalid_json":
        path.write_text("{")
    elif damage == "future_phase":
        path.write_text('{"version":1,"phase":"future"}')
    elif damage == "permissions":
        path.chmod(0o644)
    elif damage == "symlink":
        other = tmp_path / "other"
        path.rename(other)
        path.symlink_to(other)
    elif damage == "hardlink":
        os.link(path, tmp_path / "alias")
    else:
        path.write_text("x" * 4097)
    assert journal.phase() == "unreadable"


def test_symlinked_parent_is_not_followed_for_write(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(target, target_is_directory=True)
    journal = KillswitchJournal(alias / "state")
    with pytest.raises(OSError):
        journal.mark("applying")
    assert list(target.iterdir()) == []


def test_failed_atomic_replacement_preserves_last_journal(tmp_path, monkeypatch):
    journal = KillswitchJournal(tmp_path / "state")
    journal.mark("applying")

    def fail(*args, **kwargs):
        raise OSError("synthetic disk failure")

    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        journal.mark("active")
    assert journal.phase() == "applying"
    assert list((tmp_path / "state").iterdir()) == [
        tmp_path / "state" / "killswitch-state.json"
    ]


@pytest.mark.parametrize(
    "phase", ["applying", "restoring", "recovery_required", "unreadable"]
)
@pytest.mark.parametrize("operation", ["on", "off"])
def test_pending_journal_blocks_mutations_after_restart(tmp_path, phase, operation):
    model = configured_model("off")
    app = application(model, tmp_path)
    app.killswitch_journal.mark("applying" if phase == "unreadable" else phase)
    if phase == "unreadable":
        (tmp_path / "state" / "killswitch-state.json").write_text("invalid")
    app = application(model, tmp_path)
    before = deepcopy((model.defaults, model.rules))
    callback = (
        firewall.killswitch_on_sync
        if operation == "on"
        else firewall.killswitch_off_sync
    )
    assert callback(app, refresh_ui=False) is False
    assert firewall.killswitch_state(app) == "recovery"
    assert (model.defaults, model.rules) == before
    assert model.calls == []
    assert not any("Killswitch AUS" in line for line in model.logs)


def test_activation_records_verified_phase_across_instances(tmp_path):
    model = configured_model("off")
    for rules in model.rules.values():
        rules.remove(("ALLOW", "OUT", "443/tcp", "Anywhere"))
    app = application(model, tmp_path)
    app._wg_activation_links = {"wg0": 42}
    assert firewall.killswitch_on_sync(app, refresh_ui=False) is True
    assert app.killswitch_journal.phase() == "active"
    app = application(model, tmp_path)
    assert firewall.killswitch_state(app) == "on"


def test_emergency_records_failure_before_any_command(tmp_path):
    model = configured_model("off")
    app = application(model, tmp_path)
    original = app.run_cmd

    def command(args, **kwargs):
        assert KillswitchJournal(tmp_path / "state").phase() == "recovery_required"
        return original(args, **kwargs)

    app.run_cmd = command
    assert firewall.recover_firewall_after_killswitch_failure(app)
    assert firewall.killswitch_state(application(model, tmp_path)) == "recovery"


def test_crash_after_partial_apply_is_detected_after_restart(tmp_path):
    class Crash(BaseException):
        pass

    model = configured_model("off")
    app = application(model, tmp_path)
    original = app.run_cmd

    def command(args, **kwargs):
        result = original(args, **kwargs)
        if model.count == 2:
            raise Crash()
        return result

    app.run_cmd = command
    with pytest.raises(Crash):
        firewall.killswitch_on_sync(app, refresh_ui=False)
    assert app.killswitch_journal.phase() == "applying"
    assert not app.ufw_lock.locked()
    assert firewall.killswitch_state(application(model, tmp_path)) == "recovery"


def test_activation_aborts_before_mutation_if_journal_cannot_be_written(tmp_path):
    model = configured_model("off")
    app = application(model, tmp_path)
    app.killswitch_journal = SimpleNamespace(
        phase=lambda: "absent", mark=lambda phase: (_ for _ in ()).throw(OSError())
    )
    assert firewall.killswitch_on_sync(app, refresh_ui=False) is False
    assert model.calls == []


@pytest.mark.parametrize("family", [False, True])
@pytest.mark.parametrize("direction", ["IN", "OUT"])
@pytest.mark.parametrize("comment", ["", " # emergency", " # ALLOW OUT Anywhere on lo"])
def test_any_global_block_prevents_off_without_touching_user_rules(
    tmp_path, family, direction, comment
):
    model = configured_model("off")
    app = application(model, tmp_path)
    original = model.status
    suffix = " (v6)" if family else ""

    def status(verbose=False):
        rc, text = original(verbose=verbose)
        return (
            rc,
            text + f"\nAnywhere{suffix}  DENY {direction}  Anywhere{suffix}{comment}",
        )

    app._read_ufw_status = status
    before = deepcopy(model.rules)
    assert firewall.killswitch_state(app) == "recovery"
    assert firewall.killswitch_off_sync(app, refresh_ui=False) is False
    assert model.calls == [] and model.rules == before
    assert not any("Killswitch AUS" in line for line in model.logs)


@pytest.mark.parametrize("state", ["off", "on", "unreadable", "emergency"])
def test_status_label_distinguishes_verified_off_and_errors(state):
    model = configured_model(state)
    app = app_context(model)
    expected = {
        "off": "off",
        "on": "on",
        "unreadable": "unknown",
        "emergency": "recovery",
    }[state]
    actual = firewall.killswitch_state(app)
    assert actual == expected
    label = firewall.killswitch_status_label(app, actual)
    assert ("OFF" in label) is (state == "off")


def test_missing_original_preserves_rules_without_new_pending_mutation(tmp_path):
    model = configured_model("on")
    app = application(model, tmp_path)
    original = app.run_cmd

    def command(args, **kwargs):
        if args[3:5] == ["delete", "allow"]:
            return 1, "synthetic cleanup error"
        return original(args, **kwargs)

    app.run_cmd = command
    assert firewall.killswitch_off_sync(app, refresh_ui=False) is False
    assert ["default", "allow", "outgoing"] not in model.calls
    assert model.defaults["outgoing"] == "deny"
    assert app.killswitch_journal.phase() == "absent"
    assert not app.__dict__.get("killswitch_recovery_required", False)


def test_startup_pending_recovery_does_not_probe_or_change_firewall(tmp_path):
    app = netmon.App.__new__(netmon.App)
    app.killswitch_journal = KillswitchJournal(tmp_path / "state")
    app.killswitch_journal.mark("restoring")
    app.privacy_config = {}
    app.isp_stealth_running = False
    app._network_operation_active_elsewhere = lambda: False
    app.killswitch_is_on = lambda: pytest.fail(
        "Pending recovery must not trigger automatic repair"
    )
    logs = []
    app.log_safe = logs.append
    assert app.repair_orphaned_killswitch_on_startup() is False
    assert "ungeklärt" in logs[0]


def test_live_transition_is_not_misreported_as_abandoned_after_restart(tmp_path):
    model = configured_model("off")
    app = application(model, tmp_path)
    app.killswitch_journal.mark("applying")
    app._killswitch_transition_running = True
    assert firewall.killswitch_state(app) == "transition"
    assert "WIRD GEÄNDERT" in firewall.killswitch_status_label(app, "transition")
    assert firewall.killswitch_state(application(model, tmp_path)) == "recovery"


@pytest.mark.parametrize("operation", ["on", "off"])
def test_class_network_operation_methods_block_parallel_killswitch(operation):
    import threading

    app = netmon.App.__new__(netmon.App)
    app.network_ops_lock = threading.Lock()
    app.network_ops_lock.acquire()
    app.network_active_operation = "VPN-Wechsel"
    app._network_op_owner = None
    app._network_op_depth = 0
    logs = []
    app.log_safe = logs.append
    app.refresh_safe = lambda: None
    callback = (
        firewall.killswitch_on_sync
        if operation == "on"
        else firewall.killswitch_off_sync
    )
    assert callback(app, refresh_ui=False) is False
    assert "blockiert" in logs[0]
    assert "_killswitch_transition_running" not in app.__dict__
    app.network_ops_lock.release()
