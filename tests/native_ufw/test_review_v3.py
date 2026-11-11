"""Independent-review regressions, only in the capability-free native runner."""

from test_review_regressions import native_application
from support import ON, PLAN, activate, fresh_system, reboot, store, ufw_cli
from netmon.core.ufw_snapshot import SnapshotError
import pytest


def boot_baseline(system):
    assert reboot().returncode == 0
    return system.capture()


@pytest.mark.parametrize("live", [[], ["wg0"]])
def test_on_after_normal_vpn_use_preserves_inactive_profile_grants(
    system, monkeypatch, live
):
    from netmon.features import firewall_controller as fc

    for iface in ("wg0", "wg1"):
        assert ufw_cli(["allow", "out", "on", iface])[0] == 0
    before = boot_baseline(system)
    app, logs = native_application(system)
    app._collect_interface_rules_for_profiles = lambda *_a, **_k: {"wg0", "wg1"}
    app.get_wg_interfaces = lambda: live
    monkeypatch.setattr(
        fc.nm_ownership, "verified_interface", lambda name: name in live
    )
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on"
    for fam, prefix in (("4", "ufw-"), ("6", "ufw6-")):
        rows = system.capture()["runtime"][fam]
        for iface in {"wg0", "wg1"} - set(live):
            allow = f"-A {prefix}user-output -o {iface} -j ACCEPT"
            block = f"-A {prefix}user-output -o {iface} -j DROP"
            assert allow in rows  # Existing rules are not deleted or claimed as owned.
            assert block in rows
            assert rows.index(block) < rows.index(allow)
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_legacy_block_rejected_with_changed_plan(system):
    # Old legacy policy had no tunnel grants; new activation has wg0.
    for action in ON[:4]:
        assert ufw_cli(action)[0] == 0
    before = system.capture()
    with pytest.raises(SnapshotError) as exc:
        system.begin(PLAN)
    assert exc.value.code == "no_snapshot"
    assert system.capture() == before
    assert system.load() is None


def test_ack_cannot_discard_partial_rollback(system):
    before = boot_baseline(system)
    token = system.begin(PLAN)["token"]
    assert system.command(token, ["default", "deny", "outgoing"])["rc"] == 0
    record = system.load()
    current = system.capture()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert system.capture() == current
    assert store().restore()["state"] == "off"
    assert store().capture() == before


def test_ack_without_snapshot_refuses_legacy_block(system):
    for action in ON[:4]:
        assert ufw_cli(action)[0] == 0
    current = system.capture()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.capture() == current


def crash_write(system, monkeypatch, count):
    original = system._write
    done = []

    def crash(path, row):
        original(path, row)
        if str(path).startswith("/etc/"):
            done.append(path)
            if len(done) == count:
                raise SystemExit("Power cut after durable file replace")

    monkeypatch.setattr(system, "_write", crash)


@pytest.mark.parametrize("cut", [1, 2, 3])
def test_on_power_cut_then_boot_recovers_exactly(system, monkeypatch, cut):
    before = boot_baseline(system)
    token = system.begin(PLAN)["token"]
    crash_write(system, monkeypatch, cut)
    with pytest.raises(SystemExit):
        system.command(token, ["default", "deny", "outgoing"])
    assert reboot().returncode == 0
    assert store().restore()["state"] == "off"
    assert store().capture() == before


@pytest.mark.parametrize("cut", range(1, 7))
def test_off_power_cut_then_boot_recovers_exactly(system, monkeypatch, cut):
    before = boot_baseline(system)
    token, commands = activate(system)
    assert all(rc == 0 for _, rc in commands)
    system.commit(token)
    crash_write(system, monkeypatch, cut)
    with pytest.raises(SystemExit):
        system.restore()
    assert reboot().returncode == 0
    assert store().restore()["state"] == "off"
    assert store().capture() == before


def test_boot_recovery_still_refuses_foreign_rule(system, monkeypatch):
    boot_baseline(system)
    token, _ = activate(system)
    system.commit(token)
    crash_write(system, monkeypatch, 1)
    with pytest.raises(SystemExit):
        system.restore()
    assert reboot().returncode == 0
    assert ufw_cli(["allow", "22/tcp"])[0] == 0
    current = store().capture()
    with pytest.raises(SnapshotError) as exc:
        store().restore()
    assert exc.value.code == "conflict"
    assert store().capture() == current


@pytest.fixture
def system(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    assert fresh_system()[0] == 0
    return store()


@pytest.mark.parametrize("fenced", [False, True])
def test_commit_refuses_missing_or_late_inactive_interface_fence(system, fenced):
    assert ufw_cli(["allow", "out", "on", "wg1"])[0] == 0
    plan = dict(PLAN, blocked_interfaces=["wg1"])
    token, commands = activate(system, plan)
    assert all(rc == 0 for _, rc in commands)
    if fenced:
        for direction in ("in", "out"):
            assert (
                system.command(token, ["insert", "1", "deny", direction, "on", "wg1"])[
                    "rc"
                ]
                == 0
            )
    if fenced:
        import json
        from pathlib import Path

        for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
            path = Path(f"/work/kernel/{family}.json")
            state = json.loads(path.read_text())
            for chain, flag in (("input", "-i"), ("output", "-o")):
                rows = state["chains"][prefix + "user-" + chain]
                fence = f"{flag} wg1 -j DROP"
                rows.remove(fence)
                rows.append(fence)
            path.write_text(json.dumps(state))
        record = system.load()
        record["expected"] = system.capture()
        system.save(record)
    with pytest.raises(SnapshotError):
        system.commit(token)
    assert system.state()["state"] != "on"


@pytest.mark.parametrize("user_deny", [False, True])
def test_replan_releases_only_temporary_fence_and_preserves_original(
    system, monkeypatch, user_deny
):
    from netmon.features import firewall_controller as fc

    if user_deny:
        assert ufw_cli(["deny", "in", "on", "wg1"])[0] == 0
    assert ufw_cli(["allow", "out", "on", "wg1"])[0] == 0
    before = boot_baseline(system)
    app, logs = native_application(system)
    app._collect_interface_rules_for_profiles = lambda *_a, **_k: {"wg0", "wg1"}
    live = {"wg0"}
    monkeypatch.setattr(
        fc.nm_ownership, "verified_interface", lambda name: name in live
    )
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    live.add("wg1")
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
        assert (
            f"-A {prefix}user-input -i wg1 -j DROP"
            in system.capture()["runtime"][family]
        ) == user_deny
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_boot_recovery_refuses_foreign_kernel_only_rule(system, monkeypatch):
    import json

    boot_baseline(system)
    token, _ = activate(system)
    system.commit(token)
    crash_write(system, monkeypatch, 1)
    with pytest.raises(SystemExit):
        system.restore()
    assert reboot().returncode == 0
    path = __import__("pathlib").Path("/work/kernel/4.json")
    state = json.loads(path.read_text())
    state["chains"]["ufw-user-input"].append("-p tcp -m tcp --dport 1234 -j ACCEPT")
    path.write_text(json.dumps(state))
    current = store().capture()
    with pytest.raises(SnapshotError) as exc:
        store().restore()
    assert exc.value.code == "conflict"
    assert store().capture() == current


@pytest.mark.parametrize("cut", [1, 2])
@pytest.mark.parametrize("mark_recovery", [False, True])
def test_caught_partial_write_error_then_boot_keeps_restore_intent(
    system, monkeypatch, cut, mark_recovery
):
    before = boot_baseline(system)
    token = system.begin(PLAN)["token"]
    original = system._write
    done = []

    def fail(path, row):
        original(path, row)
        if str(path).startswith("/etc/"):
            done.append(path)
            if len(done) == cut:
                raise OSError("Durable write completed, next operation failed")

    monkeypatch.setattr(system, "_write", fail)
    assert system.command(token, ["default", "deny", "outgoing"])["rc"] == 1
    if mark_recovery:
        system.recovery(token)
    assert reboot().returncode == 0
    assert store().restore()["state"] == "off"
    assert store().capture() == before


def test_live_profile_becoming_inactive_keeps_original_grant_behind_fence(
    system, monkeypatch
):
    from netmon.features import firewall_controller as fc

    assert ufw_cli(["allow", "out", "on", "wg0"])[0] == 0
    before = boot_baseline(system)
    app, logs = native_application(system)
    app._collect_interface_rules_for_profiles = lambda *_a, **_k: {"wg0", "wg1"}
    live = {"wg0", "wg1"}
    monkeypatch.setattr(
        fc.nm_ownership, "verified_interface", lambda name: name in live
    )
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    live.remove("wg0")
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
        rows = system.capture()["runtime"][family]
        assert rows.index(f"-A {prefix}user-output -o wg0 -j DROP") < rows.index(
            f"-A {prefix}user-output -o wg0 -j ACCEPT"
        )
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_replan_cannot_delete_original_grant_when_fence_was_not_requested(system):
    assert ufw_cli(["allow", "out", "on", "wg0"])[0] == 0
    before = boot_baseline(system)
    token, commands = activate(system)
    assert all(rc == 0 for _, rc in commands)
    system.commit(token)
    active, record = system.capture(), system.load()
    with pytest.raises(SnapshotError) as exc:
        system.begin({"interfaces": ["wg1"], "endpoints": PLAN["endpoints"]})
    assert exc.value.code == "preflight"
    assert system.capture() == active
    assert system.load() == record
    assert system.restore()["state"] == "off"
    assert system.capture() == before
