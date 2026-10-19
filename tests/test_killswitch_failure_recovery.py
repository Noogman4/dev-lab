"""Stateful failure injection; all privileged commands are simulated."""

import ast
import ipaddress
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon.features import firewall_controller as controller


@pytest.fixture(autouse=True)
def fake_verified_interfaces(monkeypatch):
    # Keep the existing mutation-stage oracle on a verified synthetic link.
    monkeypatch.setattr(
        controller.nm_ownership,
        "verified_interface",
        lambda name: {"name": name, "kind": "wireguard", "ifindex": 7},
    )


class Ufw:
    """Minimal ordered dual-family UFW model, independent of status parsing."""

    def __init__(self, fail_at=None, raises=False, active=True, service=False):
        self.defaults = {"incoming": "deny", "outgoing": "deny"}
        self.rules = {False: [], True: []}
        # Rules owned by the user, including a cleanup candidate.
        for ipv6 in self.rules:
            self.rules[ipv6] = [
                ("ALLOW", "IN", "22/tcp", "Anywhere"),
                ("ALLOW", "OUT", "443/tcp", "Anywhere"),
            ]
        self.active = active
        self.fail_at = fail_at
        self.raises = raises
        self.count = 0
        self.calls = []
        self.logs = []
        self.bad_status = False
        self.bad_recovery = False
        self.app = SimpleNamespace(
            ufw_lock=threading.Lock(),
            get_wg_interfaces=lambda: ["wg0"],
            get_killswitch_vpn_profiles=list,
            get_killswitch_vpn_endpoints=lambda: [("203.0.113.1", "51820")],
            log_safe=self.logs.append,
            refresh_safe=lambda: None,
            tr=lambda _key, fallback: fallback,
            _read_ufw_status=self.status,
            _ufw_status_is_active=lambda text: text.startswith("Status: active"),
            _verify_killswitch_rules=lambda *_args, **_kwargs: (False, ["injected"]),
            run_cmd=self.run,
        )
        if service:
            self.app._network_service = lambda: SimpleNamespace(
                run=self.run,
                ufw_enable_force=lambda timeout: self.run(
                    ["sudo", "-n", "ufw", "--force", "enable"], timeout=timeout
                ),
            )

    @staticmethod
    def format_rule(rule, ipv6):
        policy, direction, target, source = rule
        # Model storage keeps the interface alongside the source for the
        # packet oracle; real UFW prints an IN interface in its To column.
        if direction == "IN" and " on " in source:
            source, _, iface = source.partition(" on ")
            target += f" on {iface}"
        suffix = " (v6)" if ipv6 else ""
        return f"{target}{suffix}  {policy} {direction}  {source}{suffix}"

    def status(self, verbose=False):
        assert self.app.ufw_lock.locked(), "read escaped transaction lock"
        if self.bad_status:
            return 1, "unreadable"
        lines = ["Status: active" if self.active else "Status: inactive"]
        if verbose:
            lines += [
                (
                    f"Default: {self.defaults['incoming']} (incoming), "
                    f"{self.defaults['outgoing']} (outgoing), disabled (routed)"
                ),
                "To                         Action      From",
                "--                         ------      ----",
            ]
            for ipv6, rules in self.rules.items():
                for rule in rules:
                    lines.append(self.format_rule(rule, ipv6))
        return 0, "\n".join(lines)

    def run(self, args, timeout=0, text=True):
        assert self.app.ufw_lock.locked(), "mutation escaped transaction lock"
        assert args[:3] == ["sudo", "-n", "ufw"]
        cmd = args[3:]
        self.calls.append(cmd)
        if cmd == ["status", "numbered"]:
            lines = ["Status: active"]
            n = 0
            for ipv6, rules in self.rules.items():
                for rule in rules:
                    n += 1
                    lines.append(f"[{n}] {self.format_rule(rule, ipv6)}")
            return 0, "\n".join(lines)
        self.count += 1
        if self.count == self.fail_at or (self.bad_recovery and cmd[0] == "insert"):
            if self.raises:
                raise OSError("injected command error")
            return 1, "injected command failure"
        if cmd[:2] == ["--force", "delete"]:
            index = int(cmd[2]) - 1
            for rules in self.rules.values():
                if index < len(rules):
                    del rules[index]
                    break
                index -= len(rules)
        elif cmd[0] == "default":
            self.defaults[cmd[2]] = cmd[1]
        elif cmd == ["--force", "enable"]:
            self.active = True
        elif cmd[0] == "allow":
            if "on" in cmd:
                rule = ("ALLOW", cmd[1].upper(), "Anywhere", f"Anywhere on {cmd[-1]}")
            else:
                rule = ("ALLOW", "OUT", f"{cmd[3]} {cmd[5]}/udp", "Anywhere")
            for ipv6, rules in self.rules.items():
                if (
                    "on" not in cmd
                    and (ipaddress.ip_address(cmd[3]).version == 6) != ipv6
                ):
                    continue
                rules.append(rule)
        elif cmd[:3] == ["insert", "1", "deny"]:
            for rules in self.rules.values():
                rules.insert(0, ("DENY", cmd[3].upper(), "Anywhere", "Anywhere"))
        else:
            raise AssertionError(cmd)
        return 0, "ok"

    def assert_closed(self):
        assert self.active
        assert self.defaults == {"incoming": "deny", "outgoing": "deny"}
        for rules in self.rules.values():
            # Independent oracle: first matching unrestricted rule wins.
            for direction in ("IN", "OUT"):
                first = next(rule for rule in rules if rule[1] == direction)
                assert first == ("DENY", direction, "Anywhere", "Anywhere")
            assert ("ALLOW", "IN", "22/tcp", "Anywhere") in rules
        assert ["default", "allow", "outgoing"] not in self.calls
        assert self.app.killswitch_recovery_required
        assert any("Manuelle Firewall-Wiederherstellung" in msg for msg in self.logs)


def test_baseline_recovery_changes_deny_outgoing_to_allow():
    source = subprocess.check_output(
        [
            "git",
            "show",
            "71ed081b77e26af8853d340e777009f027251082:"
            "netmon/features/firewall_controller.py",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )
    function = next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef)
        and node.name == "recover_firewall_after_killswitch_failure"
    )
    namespace = vars(controller).copy()
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), "baseline", "exec"),
        namespace,
    )
    ufw = Ufw()
    namespace[function.name](ufw.app)
    assert ufw.defaults == {"incoming": "deny", "outgoing": "allow"}
    assert ufw.calls == [
        ["default", "allow", "outgoing"],
        ["default", "deny", "incoming"],
    ]


@pytest.mark.parametrize("service", [False, True])
@pytest.mark.parametrize("raises", [False, True])
@pytest.mark.parametrize(
    "stage,active",
    [
        (stage, active)
        for active in (False, True)
        for stage in range(1, 11 if not active else 10)
    ],
)
def test_each_partial_activation_failure_fails_closed(stage, raises, active, service):
    ufw = Ufw(fail_at=stage, raises=raises, active=active, service=service)
    assert controller.killswitch_on_sync(ufw.app, refresh_ui=False) is False
    ufw.assert_closed()
    assert not ufw.app.ufw_lock.locked()


def test_failed_final_status_read_recovers_under_same_lock():
    ufw = Ufw()
    reads = 0
    real_status = ufw.app._read_ufw_status

    def status(verbose=False):
        nonlocal reads
        reads += 1
        if reads == 2:
            return 1, "injected verification failure"
        return real_status(verbose=verbose)

    ufw.app._read_ufw_status = status
    assert controller.killswitch_on_sync(ufw.app, refresh_ui=False) is False
    ufw.assert_closed()


@pytest.mark.parametrize("raises", [False, True])
def test_recovery_command_failure_never_claims_guaranteed_protection(raises):
    ufw = Ufw(raises=raises)
    ufw.bad_recovery = True
    assert controller.recover_firewall_after_killswitch_failure(ufw.app) is False
    assert any("NICHT garantiert" in msg for msg in ufw.logs)
    assert ["default", "deny", "outgoing"] in ufw.calls
    assert ["default", "allow", "outgoing"] not in ufw.calls


def test_unreadable_initial_status_aborts_without_mutations():
    ufw = Ufw()
    ufw.bad_status = True
    assert controller.killswitch_on_sync(ufw.app, refresh_ui=False) is False
    assert ufw.calls == []


@pytest.mark.parametrize(
    "change", ["ipv6", "inactive", "early_allow", "limit", "interface"]
)
def test_recovery_verification_rejects_incomplete_or_shadowed_rules(change):
    ufw = Ufw()
    assert controller.recover_firewall_after_killswitch_failure(ufw.app)
    if change == "ipv6":
        ufw.rules[True] = []
    elif change == "inactive":
        ufw.active = False
    elif change == "early_allow":
        ufw.rules[False].insert(0, ("ALLOW", "OUT", "Anywhere", "Anywhere"))
    elif change == "limit":
        ufw.rules[False].insert(0, ("LIMIT", "IN", "22/tcp", "Anywhere"))
    else:
        ufw.rules[False][0] = ("DENY", "IN", "Anywhere", "Anywhere on wg0")
    with ufw.app.ufw_lock:
        _, status = ufw.status(verbose=True)
    assert not controller._killswitch_failure_is_closed(status)


def _with_ambiguous_rule(status, policy, direction, ipv6, position):
    suffix = " (v6)" if ipv6 else ""
    action = f"{policy} {direction}".strip()
    line = f"Anywhere{suffix}  {action}  Anywhere{suffix}"
    lines = status.splitlines()
    if position == "before":
        lines.insert(4, line)  # First rule, after the status/default/table headers.
    else:
        lines.append(line)
    return "\n".join(lines)


@pytest.mark.parametrize("policy", ["ALLOW", "DENY", "REJECT"])
@pytest.mark.parametrize("direction", ["", "FWD", "SIDEWAYS"])
@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("position", ["before", "after"])
def test_ambiguous_rule_direction_prevents_recovery_verification(
    policy, direction, ipv6, position
):
    ufw = Ufw()
    assert controller.recover_firewall_after_killswitch_failure(ufw.app) is True
    with ufw.app.ufw_lock:
        _, status = ufw.status(verbose=True)
    assert controller._killswitch_failure_is_closed(status) is True
    ambiguous = _with_ambiguous_rule(status, policy, direction, ipv6, position)
    assert controller._killswitch_failure_is_closed(ambiguous) is False


@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("position", ["before", "after"])
def test_recovery_never_claims_protection_for_ambiguous_status(ipv6, position):
    ufw = Ufw()
    original_status = ufw.app._read_ufw_status

    def status(verbose=False):
        rc, output = original_status(verbose=verbose)
        if verbose:
            output = _with_ambiguous_rule(output, "ALLOW", "", ipv6, position)
        return rc, output

    ufw.app._read_ufw_status = status
    assert controller.recover_firewall_after_killswitch_failure(ufw.app) is False
    assert ufw.count == 5  # Successful commands alone cannot certify protection.
    assert ufw.app.killswitch_recovery_required is True
    assert any("NICHT garantiert" in message for message in ufw.logs)
    assert not any("wurden verifiziert" in message for message in ufw.logs)
    assert not ufw.app.ufw_lock.locked()


@pytest.mark.parametrize("stage", range(1, 6))
@pytest.mark.parametrize("raises", [False, True])
def test_each_emergency_command_failure_is_reported(stage, raises):
    ufw = Ufw(fail_at=stage, raises=raises)
    assert not controller.recover_firewall_after_killswitch_failure(ufw.app)
    assert ufw.count == 5  # Remaining recovery restrictions are still attempted.
    assert any("NICHT garantiert" in msg for msg in ufw.logs)
    assert ["default", "allow", "outgoing"] not in ufw.calls


def test_exception_on_initial_read_does_not_mutate_firewall():
    ufw = Ufw()

    def unreadable(verbose=False):
        raise OSError("initial read failed")

    ufw.app._read_ufw_status = unreadable
    assert not controller.killswitch_on_sync(ufw.app, refresh_ui=False)
    assert ufw.calls == []


@pytest.mark.parametrize("enabled", [False, True])
def test_emergency_rules_cannot_be_reported_as_normal_killswitch_state(enabled):
    ufw = Ufw()
    assert controller.recover_firewall_after_killswitch_failure(ufw.app)
    app = ufw.app
    app._ufw_default_policy_matches = lambda *args, **kwargs: True
    app._ufw_has_interface_rule = lambda *args: enabled
    app._ufw_has_endpoint_rule = lambda *args: enabled
    with app.ufw_lock:
        _, status = ufw.status(verbose=True)
    ok, issues = controller.verify_killswitch_rules(
        app, status, enabled=enabled, wg_ifaces=["wg0"]
    )
    assert not ok
    assert any("Globale Sperrregel" in issue for issue in issues)


@pytest.mark.parametrize("raises", [False, True])
def test_apply_verify_and_recovery_share_one_lock_acquisition(raises):
    class CountingLock:
        def __init__(self):
            self.entries = 0
            self.held = False

        def __enter__(self):
            assert not self.held
            self.entries += 1
            self.held = True

        def __exit__(self, *args):
            self.held = False

        def locked(self):
            return self.held

    ufw = Ufw(fail_at=6, raises=raises)
    ufw.app.ufw_lock = CountingLock()
    assert not controller.killswitch_on_sync(ufw.app, refresh_ui=False)
    ufw.assert_closed()
    assert ufw.app.ufw_lock.entries == 1


@pytest.mark.parametrize("failure", ["apply", "read", "verify"])
def test_failure_ui_refresh_runs_after_releasing_firewall_lock(failure):
    from netmon.app import App

    class FailOnReentryLock:
        def __init__(self):
            self.lock = threading.Lock()

        def __enter__(self):
            if not self.lock.acquire(blocking=False):
                pytest.fail("UI refresh reentered the held firewall lock")

        def __exit__(self, *args):
            self.lock.release()

        def locked(self):
            return self.lock.locked()

    ufw = Ufw(fail_at=6 if failure == "apply" else None)
    app = ufw.app
    app.ufw_lock = FailOnReentryLock()
    if failure == "read":
        original_status = app._read_ufw_status
        reads = 0

        def status(verbose=False):
            nonlocal reads
            reads += 1
            if reads == 2:
                return 1, "injected verification failure"
            return original_status(verbose=verbose)

        app._read_ufw_status = status
    app._ufw_default_policy_matches = lambda *args, **kwargs: True
    app._ufw_has_interface_rule = lambda *args: True
    app._ufw_has_endpoint_rule = lambda *args: True
    refreshed = []
    # Real refresh_safe dispatch on the main thread; model refresh's real
    # killswitch status query, which acquires ufw_lock again.
    app.refresh = lambda: refreshed.append(controller.killswitch_is_on(app))
    app.refresh_safe = lambda: App.refresh_safe(app)

    assert controller.killswitch_on_sync(app, refresh_ui=True) is False
    assert refreshed == [False]
    ufw.assert_closed()
    assert not app.ufw_lock.locked()
