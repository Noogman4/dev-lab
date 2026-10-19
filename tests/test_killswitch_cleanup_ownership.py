"""Ownership regressions: ordered synthetic UFW only, never system operations."""

from collections import Counter
from copy import deepcopy

import pytest
from test_killswitch_failure_recovery import Ufw
from test_killswitch_legacy_interface_rules import bind_verifier

from netmon.features import firewall_controller as fw

BASE = "f3333739841750b31f86709c1618022c65185d72"


class OwnershipUfw(Ufw):
    """Model both rule-number and exact-spec deletes, including external inserts."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rules = {
            False: [("ALLOW", "IN", "22/tcp", "Anywhere")],
            True: [("ALLOW", "IN", "22/tcp", "Anywhere")],
        }
        self.shift_on_delete = False
        self.shifted = False
        self.victim = ("ALLOW", "IN", "2222/tcp", "192.0.2.99")
        bind_verifier(self)

    def run(self, args, **kwargs):
        cmd = args[3:]
        if cmd == ["status", "numbered"] and not self.app.ufw_lock.locked():
            # The old off path reads its post-operation debug snapshot unlocked.
            with self.app.ufw_lock:
                return super().run(args, **kwargs)
        if self.shift_on_delete and "delete" in cmd and not self.shifted:
            # External administrator inserts after the numbered snapshot, before
            # the first delete. App's lock does not exclude that administrator.
            self.rules[False].insert(0, self.victim)
            self.shifted = True
        if cmd[:2] == ["delete", "allow"]:
            assert self.app.ufw_lock.locked()
            self.calls.append(cmd)
            self.count += 1
            spec = cmd[1:]
            if "on" in spec:
                rule = ("ALLOW", spec[1].upper(), "Anywhere", f"Anywhere on {spec[-1]}")
            elif "to" in spec:
                rule = ("ALLOW", "OUT", f"{spec[3]} {spec[5]}/udp", "Anywhere")
            else:
                rule = ("ALLOW", "OUT", spec[2], "Anywhere")
            for rules in self.rules.values():
                if rule in rules:
                    rules.remove(rule)
            return 0, "simulated spec delete"
        return super().run(args, **kwargs)


def setup(monkeypatch, **kwargs):
    model = OwnershipUfw(**kwargs)
    monkeypatch.setattr(
        fw.nm_ownership,
        "verified_interface",
        lambda name: {"name": name} if name == "wg0" else None,
    )
    return model, model.app


def assert_no_deletes(model):
    assert not any("delete" in cmd for cmd in model.calls), model.calls


def assert_preserved(model, before):
    for family, rules in before.items():
        assert not (Counter(rules) - Counter(model.rules[family]))


def admin_rule(kind, ipv6):
    address = "2001:db8::10" if ipv6 else "192.0.2.10"
    endpoint = "2001:db8::1" if ipv6 else "203.0.113.1"
    return {
        "lo": ("ALLOW", "OUT", "Anywhere", "Anywhere on lo"),
        "wg0": ("ALLOW", "IN", "Anywhere", "Anywhere on wg0"),
        "endpoint": ("ALLOW", "OUT", f"{endpoint} 51820/udp", address),
        "dns": ("ALLOW", "OUT", "53/udp", "Anywhere"),
        "web": ("ALLOW", "OUT", "443/tcp", "Anywhere"),
    }[kind]


@pytest.mark.parametrize("kind", ["lo", "wg0", "endpoint", "dns", "web"])
@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("service", [False, True])
def test_activation_never_deletes_matching_administrator_rules(
    monkeypatch, kind, ipv6, service
):
    model, app = setup(monkeypatch, service=service)
    app.get_killswitch_vpn_endpoints = lambda: [
        ("203.0.113.1", "51820"),
        ("2001:db8::1", "51820"),
    ]
    model.rules[ipv6].append(admin_rule(kind, ipv6))
    before = deepcopy(model.rules)
    result = fw.killswitch_on_sync(app, refresh_ui=False)
    assert_no_deletes(model)
    assert_preserved(model, before)
    if kind in {"dns", "web"}:
        assert result is False
        assert model.count == 0
        assert not any("Killswitch AN" in message for message in model.logs)
    else:
        assert result is True
        assert fw.killswitch_is_on(app) is True


@pytest.mark.parametrize("kind", ["lo", "wg0", "endpoint", "dns", "web", "slot-eth0"])
@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("service", [False, True])
def test_deactivation_preserves_all_rules_including_slot_name_matches(
    monkeypatch, kind, ipv6, service
):
    model, app = setup(monkeypatch, service=service)
    app.vpn_slots = [{"profile": "eth0"}]
    app.primary_vpn_slots = [{"profile": "eth0"}]
    app.get_killswitch_vpn_endpoints = lambda: [
        ("203.0.113.1", "51820"),
        ("2001:db8::1", "51820"),
    ]
    rule = (
        ("ALLOW", "OUT", "Anywhere", "Anywhere on eth0")
        if kind == "slot-eth0"
        else admin_rule(kind, ipv6)
    )
    model.rules[ipv6].append(rule)
    before = deepcopy(model.rules)
    assert fw.killswitch_off_sync(app, refresh_ui=False) is True
    assert_no_deletes(model)
    assert model.rules == before
    assert model.defaults == {"incoming": "deny", "outgoing": "allow"}
    assert any("erhalten" in message for message in model.logs)


def test_shifted_number_cannot_delete_unrelated_administrator_rule(monkeypatch):
    model, app = setup(monkeypatch)
    # This first rule is an old cleanup candidate; insertion before delete 1
    # makes that number point to a completely unrelated administrator rule.
    model.rules[False] = [("ALLOW", "IN", "Anywhere", "Anywhere on lo")]
    model.shift_on_delete = True
    before = deepcopy(model.rules)
    with app.ufw_lock:
        fw._remove_residual_killswitch_rules(app, ["wg0"], [], strict=True)
    assert_no_deletes(model)
    assert_preserved(model, before)
    if model.shifted:
        assert model.victim in model.rules[False]


@pytest.mark.parametrize("strict", [False, True])
def test_direct_cleanup_preserves_even_exact_unrestricted_shapes(monkeypatch, strict):
    model, app = setup(monkeypatch)
    for family in model.rules:
        model.rules[family].extend(
            [admin_rule("lo", family), admin_rule("wg0", family)]
        )
    before = deepcopy(model.rules)
    with app.ufw_lock:
        assert (
            fw._remove_residual_killswitch_rules(app, ["wg0"], [], strict=strict) == 0
        )
    assert_no_deletes(model)
    assert model.rules == before


def test_automatic_vpn_dedupe_cannot_delete_foreign_duplicate_or_shifted_number(
    monkeypatch,
):
    model, app = setup(monkeypatch)
    duplicate = ("ALLOW", "OUT", "Anywhere", "Anywhere on wg0")
    model.rules[False] = [duplicate, duplicate]
    model.shift_on_delete = True
    monkeypatch.setattr(fw, "run_cmd", model.run)
    before = deepcopy(model.rules)
    with app.ufw_lock:
        assert fw.dedupe_vpn_ufw_rules() == 0
    assert_no_deletes(model)
    assert_preserved(model, before)


def baseline_namespace():
    """Read the exact reviewed commit; execute definitions, never UFW commands."""
    import subprocess

    source = subprocess.check_output(
        ["git", "show", BASE + ":netmon/features/firewall_controller.py"], text=True
    )
    namespace = dict(fw.__dict__)
    exec(compile(source, "reviewed-baseline", "exec"), namespace)
    return namespace


@pytest.mark.parametrize("kind", ["lo", "wg0", "endpoint", "dns", "web"])
@pytest.mark.parametrize("ipv6", [False, True])
def test_original_commit_reproduces_all_activation_ownership_deletions(
    monkeypatch, kind, ipv6
):
    old = baseline_namespace()
    model, app = setup(monkeypatch)
    app.get_killswitch_vpn_endpoints = lambda: [
        ("203.0.113.1", "51820"),
        ("2001:db8::1", "51820"),
    ]
    rule = admin_rule(kind, ipv6)
    model.rules[ipv6].append(rule)
    old["killswitch_on_sync"](app, refresh_ui=False)
    assert any("delete" in cmd for cmd in model.calls)
    # Broad rules can be re-added afterwards; that is still an unauthorized
    # deletion. Narrow endpoints and global DNS/web exceptions actually vanish.
    if kind in {"endpoint", "dns", "web"}:
        assert rule not in model.rules[ipv6]


@pytest.mark.parametrize("ipv6", [False, True])
def test_original_commit_reproduces_slot_name_authorized_eth0_deletion(
    monkeypatch, ipv6
):
    old = baseline_namespace()
    model, app = setup(monkeypatch)
    app.vpn_slots = [{"profile": "eth0"}]
    rule = ("ALLOW", "OUT", "Anywhere", "Anywhere on eth0")
    model.rules[ipv6].append(rule)
    old["killswitch_off_sync"](app, refresh_ui=False)
    assert rule not in model.rules[ipv6]
    assert ["delete", "allow", "out", "on", "eth0"] in model.calls


def test_original_number_race_deletes_a_different_administrator_rule(monkeypatch):
    old = baseline_namespace()
    model, app = setup(monkeypatch)
    candidate = ("ALLOW", "OUT", "Anywhere", "Anywhere on lo")
    model.rules[False] = [candidate]
    model.shift_on_delete = True
    with app.ufw_lock:
        old["_remove_residual_killswitch_rules"](app, ["wg0"], [], strict=True)
    assert model.shifted
    assert model.victim not in model.rules[False]
    assert candidate in model.rules[False]  # The originally selected rule survives.


@pytest.mark.parametrize("kind", ["interface", "endpoint"])
def test_vpn_profile_cleanup_helpers_never_authorize_deletion(monkeypatch, kind):
    from tools import netmon

    model, app = setup(monkeypatch)
    monkeypatch.setattr(netmon, "run_cmd", model.run)
    before = deepcopy(model.rules)
    if kind == "interface":
        result, removed, detail = netmon.App._remove_interface_rule(app, "eth0", "out")
        assert removed == 0
    else:
        result, detail = netmon.App._remove_udp_endpoint_rule(
            app, "203.0.113.1", "51820"
        )
    assert result == "failed"
    assert "manuelle Administratorpruefung" in detail
    assert model.rules == before
    assert model.calls == []


@pytest.mark.parametrize("stage", ["preflight", "inventory", "verification"])
@pytest.mark.parametrize("port", ["53/udp", "53/tcp", "80/tcp", "443/tcp"])
@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("service", [False, True])
def test_conflicting_egress_is_preserved_and_never_claims_success(
    monkeypatch, stage, port, ipv6, service
):
    model, app = setup(monkeypatch, service=service)
    foreign = ("ALLOW", "OUT", port, "Anywhere")
    inserted = False

    def insert():
        nonlocal inserted
        if not inserted:
            model.rules[ipv6].append(foreign)
            inserted = True

    if stage == "preflight":
        insert()
    original_run = app.run_cmd

    def runner(args, **kwargs):
        if stage == "inventory" and args[3:] == ["status", "numbered"]:
            insert()
        return original_run(args, **kwargs)

    app.run_cmd = runner
    if service:
        adapter = app._network_service()
        adapter.run = runner
        app._network_service = lambda: adapter
    original_status = app._read_ufw_status
    reads = 0

    def status(verbose=False):
        nonlocal reads
        reads += 1
        if stage == "verification" and reads == 2:
            insert()
        return original_status(verbose=verbose)

    app._read_ufw_status = status
    assert fw.killswitch_on_sync(app, refresh_ui=False) is False
    assert inserted
    assert foreign in model.rules[ipv6]
    assert_no_deletes(model)
    assert not any("Killswitch AN" in message for message in model.logs)
    if stage == "preflight":
        assert model.count == 0
    else:
        model.assert_closed()


@pytest.mark.parametrize("active", [False, True])
@pytest.mark.parametrize("raises", [False, True])
@pytest.mark.parametrize("service", [False, True])
@pytest.mark.parametrize("stage", [1, 2, 3])
def test_deactivation_failure_never_claims_success_or_deletes(
    monkeypatch, active, raises, service, stage
):
    if active and stage == 3:
        # Active deactivation has two mutation steps; exercise verification here.
        failure_stage = None
    else:
        failure_stage = stage
    model, app = setup(
        monkeypatch,
        active=active,
        raises=raises,
        service=service,
        fail_at=failure_stage,
    )
    before = deepcopy(model.rules)
    if active and stage == 3:
        original_status = app._read_ufw_status
        reads = 0

        def status(verbose=False):
            nonlocal reads
            reads += 1
            if reads == 2:
                if raises:
                    raise OSError("simulated final inventory error")
                return 1, "simulated final inventory error"
            return original_status(verbose=verbose)

        app._read_ufw_status = status
    assert fw.killswitch_off_sync(app, refresh_ui=False) is False
    # Deactivation intentionally attempts default allow; recovery must finish
    # with leading denies and must never reopen outgoing traffic itself.
    assert model.active
    assert model.defaults == {"incoming": "deny", "outgoing": "deny"}
    for rules in model.rules.values():
        for direction in ("IN", "OUT"):
            first = next(rule for rule in rules if rule[1] == direction)
            assert first == ("DENY", direction, "Anywhere", "Anywhere")
    assert app.killswitch_recovery_required
    assert ["default", "allow", "outgoing"] not in model.calls[-5:]
    assert any(
        "Manuelle Firewall-Wiederherstellung" in message for message in model.logs
    )
    assert_preserved(model, before)
    assert_no_deletes(model)
    assert not any("Killswitch AUS" in message for message in model.logs)


@pytest.mark.parametrize(
    "text,rc",
    [
        ("", 0),
        ("garbage", 0),
        ("Status: active", 0),
        ("", 1),
        (
            "Status: active\nDefault: deny (incoming), allow (outgoing), disabled (routed)\nAnywhere ALLOW SIDEWAYS Anywhere",
            0,
        ),
    ],
)
def test_unreliable_deactivation_inventory_never_mutates_or_succeeds(
    monkeypatch, text, rc
):
    model, app = setup(monkeypatch)
    app._read_ufw_status = lambda verbose=False: (rc, text)
    assert fw.killswitch_off_sync(app, refresh_ui=False) is False
    assert model.count == 0
    assert_no_deletes(model)


def test_recovery_rules_require_manual_deactivation_and_are_not_deleted(monkeypatch):
    model, app = setup(monkeypatch)
    assert fw.recover_firewall_after_killswitch_failure(app) is True
    before = deepcopy(model.rules)
    calls = len(model.calls)
    assert fw.killswitch_off_sync(app, refresh_ui=False) is False
    assert model.calls[calls:] == []
    assert model.rules == before
    assert model.defaults["outgoing"] == "deny"
    assert_no_deletes(model)
    assert not any("Killswitch AUS" in message for message in model.logs)


def test_activation_deactivation_reactivation_preserves_rules_and_remains_functional(
    monkeypatch,
):
    model, app = setup(monkeypatch)
    before = deepcopy(model.rules)
    assert fw.killswitch_on_sync(app, refresh_ui=False) is True
    assert fw.killswitch_is_on(app) is True
    enabled_rules = deepcopy(model.rules)
    assert fw.killswitch_off_sync(app, refresh_ui=False) is True
    assert fw.killswitch_is_on(app) is False
    assert model.rules == enabled_rules
    assert fw.killswitch_on_sync(app, refresh_ui=False) is True
    assert fw.killswitch_is_on(app) is True
    assert_preserved(model, before)
    assert_no_deletes(model)


@pytest.mark.parametrize(
    "rule",
    [
        {"type": "interface", "iface": "lo", "direction": "in"},
        {"type": "interface", "iface": "wg0", "direction": "out"},
        {"type": "interface", "iface": "eth0", "direction": "out"},
        {"type": "endpoint", "ip": "203.0.113.1", "port": "51820"},
        {"type": "endpoint", "ip": "2001:db8::1", "port": "51820"},
    ],
)
def test_baseline_rollback_reports_unproven_ownership_instead_of_deleting(rule):
    from netmon.features import security_audit_controller as audit

    def no_command(*_args, **_kwargs):
        pytest.fail(
            "Rollback must preserve unknown rules, including exact profile matches"
        )

    with pytest.raises(RuntimeError, match="Herkunft nicht belegt"):
        audit._delete_ufw_profile_rule(rule, run_cmd_fn=no_command)


@pytest.mark.parametrize(
    "port,proto", [("53", "udp"), ("53", "tcp"), ("80", "tcp"), ("443", "tcp")]
)
def test_game_mode_rollback_reports_manual_review_and_preserves_rules(
    monkeypatch, port, proto
):
    from tools import netmon

    def no_command(*_args, **_kwargs):
        pytest.fail("Session lists are not rule ownership")

    monkeypatch.setattr(netmon, "run_cmd", no_command)
    ok, errors = netmon.App._rollback_game_mode_ufw_exception_rules(
        object(),
        [{"type": "standard_port", "direction": "out", "port": port, "proto": proto}],
    )
    assert ok is False
    assert any("manuelle Administratorpruefung" in error for error in errors)


def test_automatic_ssh_cleanup_cannot_skip_the_administrator_decision(monkeypatch):
    model, app = setup(monkeypatch)
    app.log = model.logs.append
    app.ensure_sudo_session = lambda *_args: pytest.fail("Must not request privileges")
    before = deepcopy(model.rules)
    fw.remove_ssh_rule_async(app, auto=True)
    assert model.rules == before
    assert model.calls == []
    assert any("manuelle Administratorpruefung" in message for message in model.logs)
