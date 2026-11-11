"""Third independent review: production binding, resync and recovery."""

from test_review_regressions import native_application
from support import PLAN, ON, activate, fresh_system, reboot, store, ufw_cli
from netmon.app import App
from netmon.core.ufw_snapshot import SnapshotError
from netmon.features import firewall_controller as fc
from pathlib import Path
from copy import deepcopy
import pytest


@pytest.fixture
def system(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    assert fresh_system()[0] == 0
    assert reboot().returncode == 0
    return store()


class ProductionShape:
    # The actual App descriptors, not lambdas attached to an instance.
    _collect_referenced_vpn_profiles = App._collect_referenced_vpn_profiles
    _collect_interface_rules_for_profiles = App._collect_interface_rules_for_profiles
    resolve_profile_family_runtime = App.resolve_profile_family_runtime
    get_killswitch_vpn_profiles = App.get_killswitch_vpn_profiles
    get_killswitch_vpn_endpoints = App.get_killswitch_vpn_endpoints
    collect_non_ip_endpoint_profiles = App.collect_non_ip_endpoint_profiles

    def _read_wg_profile_text(self, _name):
        return 0, "[Peer]\nEndpoint=198.51.100.10:51820\n"

    def _base_wg_profile_name(self, name):
        return name or ""

    def _internal_ipv4_profile_name(self, name):
        return name + "__ipv4"

    def ipv6_is_disabled(self):
        return self.system_ipv6_disabled

    def profile_supports_ipv6(self, name):
        return False

    def _wg_profile_exists(self, name):
        return name in self.files

    def active_wg_profile(self):
        return next(iter(self.live), "")

    def list_wg_profiles(self):
        return list(self.refs)

    def parse_vpn_endpoint(self, name):
        return tuple(PLAN["endpoints"][0])


def production_app(system, monkeypatch, refs=("wg0", "wg1"), live=()):
    fake, logs = native_application(system)
    app = ProductionShape()
    app.__dict__.update(vars(fake))
    for name in (
        "_collect_referenced_vpn_profiles",
        "_collect_interface_rules_for_profiles",
        "get_killswitch_vpn_profiles",
        "get_killswitch_vpn_endpoints",
    ):
        del app.__dict__[name]
        assert callable(getattr(type(app), name))
    app.refs, app.live = list(refs), set(live)
    app.files = set(refs)
    app.system_ipv6_disabled = False
    app.vpn_slots = [{"profile": n} for n in refs]
    app.get_wg_interfaces = lambda: sorted(app.live)
    monkeypatch.setattr(
        fc.nm_ownership, "verified_interface", lambda name: name in app.live
    )
    return app, logs


@pytest.mark.parametrize("live", [(), ("wg0",)])
def test_production_methods_include_inactive_profile_interfaces(
    system, monkeypatch, live
):
    app, logs = production_app(system, monkeypatch, live=live)
    for name in app.refs:
        assert ufw_cli(["allow", "out", "on", name])[0] == 0
    before = system.capture()
    assert app._collect_interface_rules_for_profiles(app.refs) == set(live)
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert set(system.load()["plan"]["blocked_interfaces"]) == set(app.refs) - set(live)
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def count_fences(system, name):
    return sum(
        row == f"-A {prefix}user-{chain} {flag} {name} -j DROP"
        for family, prefix in (("4", "ufw-"), ("6", "ufw6-"))
        for chain, flag in (("input", "-i"), ("output", "-o"))
        for row in system.capture()["runtime"][family]
    )


def test_resync_is_idempotent_then_online_fence_is_removed(system, monkeypatch):
    app, logs = production_app(system, monkeypatch, live=("wg0",))
    assert ufw_cli(["allow", "out", "on", "wg1"])[0] == 0
    before = system.capture()
    for _ in range(4):
        assert fc.killswitch_on_sync(app, refresh_ui=False), logs
        assert count_fences(system, "wg1") == 4
    app.live.add("wg1")
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert count_fences(system, "wg1") == 0
    assert system.state()["state"] == "on"
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_retired_blocked_original_grant_rejected_before_first_write(system):
    assert ufw_cli(["allow", "out", "on", "wg1"])[0] == 0
    before = system.capture()
    plan = dict(PLAN, blocked_interfaces=["wg1"])
    token = system.begin(plan)["token"]
    for direction in ("in", "out"):
        assert (
            system.command(token, ["insert", "1", "deny", direction, "on", "wg1"])["rc"]
            == 0
        )
    for cmd in ON:
        assert system.command(token, cmd)["rc"] == 0
    system.commit(token)
    current, record = system.capture(), system.load()
    with pytest.raises(SnapshotError) as exc:
        system.begin(PLAN)
    assert exc.value.code == "preflight"
    assert system.capture() == current
    assert system.load() == record
    assert system.restore()["state"] == "off"
    assert system.capture() == before


def test_acknowledged_kernel_write_with_unknown_normalization_can_restore(system):
    # A formatting gap, not a claim about actual xtables output.
    Path("/work/kernel/quirk").touch()
    before = system.capture()
    token = system.begin(PLAN)["token"]
    result = system.command(token, ["default", "deny", "outgoing"])
    assert result["rc"] == 1  # Unknown comparison is never an ON success.
    assert system.load()["phase"] == "recovery"
    system.recovery(token)
    assert store().restore()["state"] == "off"
    assert store().capture() == before


def test_confirmed_write_does_not_adopt_concurrent_foreign_file_edit(
    system, monkeypatch
):
    token = system.begin(PLAN)["token"]
    original = system.backend.restore

    def changed(runtime):
        original(runtime)
        with Path("/etc/ufw/before.rules").open("a") as f:
            f.write("# admin edit after kernel commit\n")

    monkeypatch.setattr(system.backend, "restore", changed)
    with pytest.raises(SnapshotError) as exc:
        system.command(token, ["default", "deny", "outgoing"])
    assert exc.value.code == "conflict"
    assert "# admin edit" in Path("/etc/ufw/before.rules").read_text()
    with pytest.raises(SnapshotError):
        store().restore()


@pytest.mark.parametrize("extra", ["before-file", "input-rule"])
def test_explicit_review_after_manual_repair_archives_original_and_retains_admin_edit(
    system, extra
):
    from netmon.core.ufw_snapshot import MUTABLE

    token, _ = activate(system)
    system.commit(token)
    original = deepcopy(system.load()["original"])
    if extra == "before-file":
        with Path("/etc/ufw/before.rules").open("a") as f:
            f.write("# retained admin note\n")
    with pytest.raises(SnapshotError):
        # Own active KS, not a legacy KS. It must remain pending.
        system.acknowledge()
    for name in MUTABLE:
        system._write(Path(name), original["files"][name])
    system.backend.restore(original["runtime"])
    if extra == "input-rule":
        assert ufw_cli(["allow", "22/tcp"])[0] == 0
    repaired = system.capture()
    assert repaired != original
    assert system.acknowledge()["state"] == "reviewed"
    assert system.capture() == repaired
    assert system.load()["original"] == original
    archives = list(system.registry.glob("reviewed-*.json"))
    assert len(archives) == 1
    assert archives[0].stat().st_mode & 0o777 == 0o600
    import json

    assert json.loads(archives[0].read_text())["original"] == original
    assert system.removal()["removable"]
    assert store().state()["state"] == "reviewed"


def test_ack_keeps_pending_when_profile_fence_remains_after_policy_repair(system):
    assert ufw_cli(["allow", "out", "on", "wg1"])[0] == 0
    token = system.begin(dict(PLAN, blocked_interfaces=["wg1"]))["token"]
    for direction in ("in", "out"):
        assert (
            system.command(token, ["insert", "1", "deny", direction, "on", "wg1"])["rc"]
            == 0
        )
    record = system.load()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record


@pytest.mark.parametrize("user_deny", [False, True])
def test_old_duplicate_fences_are_all_removed_without_losing_original_comment(
    system, monkeypatch, user_deny
):
    import ufw.frontend

    app, logs = production_app(system, monkeypatch, live=("wg0",))
    if user_deny:
        assert (
            ufw_cli(["deny", "in", "on", "wg1", "comment", "keep original comment"])[0]
            == 0
        )
    assert ufw_cli(["allow", "out", "on", "wg1"])[0] == 0
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    # Model the bad checkpoint written by protocol 3. All files and tables are
    # private. This setup deliberately reintroduces that version's duplicates.
    ui = ufw.frontend.UFWFrontend(False)
    for v6, rules in ((False, ui.backend.rules), (True, ui.backend.rules6)):
        fences = [
            r
            for r in rules
            if r.action == "deny"
            and (r.interface_in == "wg1" or r.interface_out == "wg1")
        ]
        for fence in fences:
            rules[0:0] = [fence.dup_rule(), fence.dup_rule()]
        ui.backend._write_rules(v6)
    assert reboot().returncode == 0
    record = system.load()
    record["expected"] = system.capture()
    system.save(record)
    assert count_fences(system, "wg1") > 4
    app.live.add("wg1")
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert count_fences(system, "wg1") == (2 if user_deny else 0)
    for name in ("user.rules", "user6.rules"):
        text = Path("/etc/ufw", name).read_text()
        if user_deny:
            # Comments are hex-encoded in UFW tuple metadata.
            assert text.count("keep original comment".encode().hex()) == 1
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_known_checkpoint_with_unretired_own_fence_cannot_claim_on(system):
    import json

    token, _ = activate(system)
    system.commit(token)
    for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
        path = Path(f"/work/kernel/{family}.json")
        state = json.loads(path.read_text())
        state["chains"][prefix + "user-output"].insert(0, "-o wg0 -j DROP")
        path.write_text(json.dumps(state))
    record = system.load()
    record["expected"] = system.capture()
    system.save(record)
    assert system.state()["state"] == "unknown"
    record["phase"] = "applying"
    system.save(record)
    with pytest.raises(SnapshotError):
        system.commit(token)


def test_archive_write_failure_cannot_retire_rollback(system, monkeypatch):
    token = system.begin(PLAN)["token"]
    assert system.command(token, ["default", "deny", "outgoing"])["rc"] == 0
    assert ufw_cli(["default", "allow", "outgoing"])[0] == 0
    record, current = system.load(), system.capture()
    original = system._write

    def fail_archive(path, row):
        if path.name.startswith("reviewed-"):
            raise OSError("Archive cannot be made durable")
        original(path, row)

    monkeypatch.setattr(system, "_write", fail_archive)
    with pytest.raises(OSError):
        system.acknowledge()
    assert system.load() == record
    assert system.capture() == current
    with pytest.raises(SnapshotError) as exc:
        system.removal()
    assert exc.value.code == "pending"


def test_manual_admin_repair_clears_controller_gate_without_off_message(
    system, monkeypatch
):
    app, logs = production_app(system, monkeypatch)
    token = system.begin(PLAN)["token"]
    assert system.command(token, ["default", "deny", "outgoing"])["rc"] == 0
    system.recovery(token)
    assert ufw_cli(["allow", "22/tcp"])[0] == 0
    assert ufw_cli(["default", "allow", "outgoing"])[0] == 0
    app.killswitch_recovery_required = True
    app.killswitch_journal.mark("recovery_required")
    app._confirm_danger_action = lambda *_a, **_k: True
    app.run_async = lambda fn, **_k: fn()
    current = system.capture()
    assert fc.acknowledge_manual_firewall_review(app)
    assert system.capture() == current
    assert system.state()["state"] == "reviewed"
    assert not fc.firewall_recovery_pending(app)
    assert not any("Killswitch AUS" in line for line in logs)
    archive = next(system.registry.glob("reviewed-*.json"))
    archived = archive.read_bytes()
    system.begin(PLAN)
    assert system.restore()["state"] == "off"
    assert system.capture() == current
    assert archive.read_bytes() == archived


@pytest.mark.parametrize("disabled", [False, True])
def test_known_existing_family_variant_is_fenced_after_family_setting_changes(
    system, monkeypatch, disabled
):
    app, logs = production_app(system, monkeypatch, refs=("wg0",))
    app.files.add("wg0__ipv4")
    app.system_ipv6_disabled = disabled
    for name in app.files:
        assert ufw_cli(["allow", "out", "on", name])[0] == 0
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert set(system.load()["plan"]["blocked_interfaces"]) == {"wg0", "wg0__ipv4"}
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_controller_can_explicitly_restore_after_unknown_kernel_normalization(
    system, monkeypatch
):
    app, logs = production_app(system, monkeypatch, live=("wg0",))
    Path("/work/kernel/quirk").touch()
    before = system.capture()
    assert not fc.killswitch_on_sync(app, refresh_ui=False)
    assert system.load()["original"] == before
    assert system.load()["phase"] == "recovery"
    assert fc.firewall_recovery_pending(app)
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before
    assert not fc.firewall_recovery_pending(app)
    assert system.state()["state"] == "off"


def test_manual_completion_cannot_hide_old_fence_outside_current_plan(system):
    token = system.begin(PLAN)["token"]
    # Models an old checkpoint whose plan had already lost this interface.
    for direction in ("in", "out"):
        assert (
            system.command(token, ["insert", "1", "deny", direction, "on", "retired0"])[
                "rc"
            ]
            == 0
        )
    record = system.load()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
