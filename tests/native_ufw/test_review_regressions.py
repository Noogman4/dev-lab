"""Real UFW parser, serializer and ufw-init with a simulated filter kernel."""

import os
from pathlib import Path

import pytest

if os.environ.get("NETMON_NATIVE_UFW_ISOLATED") != "1":
    pytest.skip(
        "Requires tests/run_native_ufw_suite.py; never run on host",
        allow_module_level=True,
    )

# No capabilities, real firewall executables, host /etc or network namespace.
assert os.readlink("/proc/self/ns/net") != os.environ["NETMON_PARENT_NET_NS"]
assert "CapEff:\t0000000000000000" in Path("/proc/self/status").read_text()
assert not Path("/home/happy").exists()
assert Path("/usr/sbin/iptables").read_bytes().startswith(b"#!/usr/bin/python3")

from support import PLAN, activate, fresh_system, reboot, store, ufw_cli  # noqa: E402


@pytest.fixture
def system():
    assert fresh_system()[0] == 0
    return store()


def test_native_round_trip_and_restart(system):
    before = system.capture()
    token, commands = activate(system)
    assert all(rc == 0 for _cmd, rc in commands), commands
    system.commit(token)
    assert system.state()["state"] == "on"
    assert reboot().returncode == 0
    if system.state()["state"] != "on":
        from support import diff_runtime

        print(
            "\n".join(
                diff_runtime(
                    system.load()["expected"]["runtime"], system.capture()["runtime"]
                )
            )
        )
    assert system.state()["state"] == "on"
    assert system.restore()["state"] == "off"
    assert system.capture() == before


def test_off_receipt_does_not_block_normal_firewall_use(system):
    token, _ = activate(system)
    system.commit(token)
    system.restore()
    assert ufw_cli(["allow", "22/tcp"])[0] == 0
    assert system.state()["state"] == "off"
    current = system.capture()
    with pytest.raises(Exception) as error:
        system.restore()
    assert error.value.code == "no_snapshot"
    assert system.capture() == current
    token = system.begin(PLAN)["token"]
    assert system.restore()["state"] == "off"
    assert system.capture() == current


@pytest.mark.parametrize(
    "rule",
    [
        ["allow", "out", "22/tcp"],
        ["allow", "out", "443/tcp"],
        ["allow", "out", "on", "eth0"],
    ],
)
def test_incompatible_rule_rejected_before_any_mutation(system, rule):
    assert ufw_cli(rule)[0] == 0
    before = system.capture()
    with pytest.raises(Exception) as error:
        system.begin(PLAN)
    assert error.value.code == "preflight"
    assert system.capture() == before
    assert system.load() is None


def test_limit_input_rule_survives_round_trip(system):
    assert ufw_cli(["limit", "22/tcp"])[0] == 0
    before = system.capture()
    token, commands = activate(system)
    assert all(rc == 0 for _cmd, rc in commands), commands
    system.commit(token)
    system.restore()
    assert system.capture() == before


def test_malformed_application_warning_does_not_break_transport(system):
    Path("/etc/ufw/applications.d/bad-profile").write_text("[Broken\n")
    assert system.backend.ready()
    system.begin(PLAN)
    system.restore()


def test_planning_has_no_live_file_or_kernel_writes(system):
    before = system.capture()
    log = Path("/work/kernel/calls.log")
    offset = len(log.read_text())
    planned = system.backend.prepare(["default", "deny", "outgoing"], before)
    calls = log.read_text()[offset:].splitlines()
    assert system.capture() == before
    assert planned != before
    assert all(line.endswith(" -V") for line in calls), calls
    assert system.load() is None


@pytest.mark.parametrize("stage", [1, 2, 3])
def test_command_crash_after_each_changed_file_is_recoverable(
    system, monkeypatch, stage
):
    before = system.capture()
    token = system.begin(PLAN)["token"]
    original = system._write
    steps = []

    def crash(path, row):
        original(path, row)
        if path.name != "state.json":
            steps.append(path)
            if len(steps) == stage:
                raise SystemExit("Power-cut after file replace")

    monkeypatch.setattr(system, "_write", crash)
    with pytest.raises(SystemExit):
        system.command(token, ["default", "deny", "outgoing"])
    restarted = store()
    assert restarted.state()["state"] == "recovery"
    assert restarted.restore()["state"] == "off"
    assert restarted.capture() == before


@pytest.mark.parametrize("family", ["iptables-restore", "ip6tables-restore"])
def test_command_crash_after_each_family_commit_is_recoverable(
    system, monkeypatch, family
):
    before = system.capture()
    token = system.begin(PLAN)["token"]
    original = system.backend._execute

    def crash(args, data=None):
        result = original(args, data)
        if Path(args[0]).name == family:
            raise SystemExit("Power-cut after kernel commit")
        return result

    monkeypatch.setattr(system.backend, "_execute", crash)
    with pytest.raises(SystemExit):
        system.command(token, ["default", "deny", "outgoing"])
    restarted = store()
    assert restarted.restore()["state"] == "off"
    assert restarted.capture() == before


def test_command_crash_before_checkpoint_preserves_intent(system, monkeypatch):
    before = system.capture()
    token = system.begin(PLAN)["token"]
    original = system.save

    def crash(record):
        if "intent" not in record:
            raise SystemExit("Power-cut before checkpoint")
        original(record)

    monkeypatch.setattr(system, "save", crash)
    with pytest.raises(SystemExit):
        system.command(token, ["default", "deny", "outgoing"])
    restarted = store()
    assert restarted.restore()["state"] == "off"
    assert restarted.capture() == before


def test_interrupt_receipt_does_not_authorize_foreign_changes(system, monkeypatch):
    token = system.begin(PLAN)["token"]
    original = system.save

    def crash(record):
        original(record)
        if "intent" in record:
            raise SystemExit("Power-cut before first write")

    monkeypatch.setattr(system, "save", crash)
    with pytest.raises(SystemExit):
        system.command(token, ["default", "deny", "outgoing"])
    assert ufw_cli(["allow", "22/tcp"])[0] == 0
    current = system.capture()
    with pytest.raises(Exception) as error:
        store().restore()
    assert error.value.code == "conflict"
    assert store().capture() == current


def test_restore_ipv6_failure_closes_ipv4_and_remains_retryable(system):
    before = system.capture()
    token, _ = activate(system)
    system.commit(token)
    failure = Path("/work/kernel/fail-ip6tables-restore")
    failure.touch()
    with pytest.raises(Exception) as error:
        system.restore()
    assert error.value.code == "rollback_failed"
    assert system.state()["state"] == "recovery"
    rows = system.backend.runtime()
    for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
        assert (
            ":OUTPUT DROP [0:0]" in rows[family]
            or f"-A {prefix}user-output -j DROP" in rows[family]
        )
    failure.unlink()
    assert store().restore()["state"] == "off"
    assert store().capture() == before


def test_empty_ruleset_emergency_uses_append_after_insert_rejection(system):
    from netmon.core.ufw_snapshot import SnapshotError

    token = system.begin({"interfaces": [], "endpoints": [["198.51.100.10", "51820"]]})[
        "token"
    ]
    system.recovery(token)
    for direction in ("out", "in"):
        try:
            result = system.command(
                token, ["insert", "1", "deny", direction, "from", "any", "to", "any"]
            )
        except SnapshotError:
            result = {"rc": 1}
        if result["rc"]:
            result = system.command(
                token, ["deny", direction, "from", "any", "to", "any"]
            )
        assert result["rc"] == 0
    rows = system.backend.runtime()
    for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
        for direction in ("input", "output"):
            assert f"-A {prefix}user-{direction} -j DROP" in rows[family]


def test_lock_contention_waits_and_timeout_is_specific(system):
    import fcntl
    import time
    from netmon.core.ufw_snapshot import SnapshotError, _ufw_lock

    ready, signal = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(ready)
        fd = os.open("/run/ufw.lock", os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.lockf(fd, fcntl.LOCK_EX)
        os.write(signal, b"1")
        time.sleep(0.3)
        os._exit(0)
    os.close(signal)
    try:
        assert os.read(ready, 1) == b"1"
        with pytest.raises(SnapshotError) as error:
            with _ufw_lock(timeout=0.02):
                pytest.fail("A competing process still holds the lock")
        assert error.value.code == "busy"
        with _ufw_lock(timeout=2):
            pass
    finally:
        os.close(ready)
        os.waitpid(pid, 0)


@pytest.mark.parametrize("disabled", ["inactive", "ipv6-no"])
def test_inactive_or_single_family_is_refused_without_mutation(system, disabled):
    path = Path("/etc/ufw/ufw.conf" if disabled == "inactive" else "/etc/default/ufw")
    text = (
        path.read_text()
        .replace("ENABLED=yes", "ENABLED=no")
        .replace("IPV6=yes", "IPV6=no")
    )
    path.write_text(text)
    before = system.capture()
    with pytest.raises(Exception) as error:
        system.begin(PLAN)
    assert error.value.code == "inactive"
    assert system.capture() == before
    assert system.load() is None


def native_application(system):
    import threading
    from types import SimpleNamespace
    from netmon.core.killswitch_journal import KillswitchJournal
    from netmon.core.ufw_snapshot import UfwSnapshotClient
    from netmon.features import firewall_controller as controller

    def transport(action, payload):
        if action == "begin":
            return system.begin(payload)
        if action == "command":
            return system.command(payload["token"], payload["arguments"])
        if action in {"recovery", "commit"}:
            return getattr(system, action)(payload["token"])
        return getattr(system, action)()

    logs = []
    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        killswitch_journal=KillswitchJournal(),
        firewall_snapshots=UfwSnapshotClient(transport),
        get_wg_interfaces=lambda: ["wg0"],
        get_killswitch_vpn_profiles=lambda: ["wg0"],
        get_killswitch_vpn_endpoints=lambda: [
            tuple(item) for item in PLAN["endpoints"]
        ],
        _collect_referenced_vpn_profiles=lambda **_k: ["wg0"],
        _collect_interface_rules_for_profiles=lambda *_a, **_k: {"wg0"},
        _read_ufw_status=lambda verbose=False: system.backend.command(
            ["status", "verbose"] if verbose else ["status"]
        ),
        run_cmd=lambda args, **_k: system.backend.command(args[3:]),
        _ufw_status_is_active=controller.ufw_status_is_active,
        _ufw_default_policy_matches=controller.ufw_default_policy_matches,
        _ufw_has_interface_rule=controller.ufw_has_interface_rule,
        _ufw_has_endpoint_rule=controller.ufw_has_endpoint_rule,
        log_safe=logs.append,
        log=logs.append,
        log_debug_safe=lambda *_a: None,
        log_debug=lambda *_a: None,
        log_network_debug=lambda *_a: None,
        refresh_safe=lambda: None,
        tr=lambda _key, fallback: fallback,
    )
    app._verify_killswitch_rules = (
        lambda *args, **kwargs: controller.verify_killswitch_rules(app, *args, **kwargs)
    )
    return app, logs


def test_real_controller_cycle_with_umask_0002_and_0770_parent(system, monkeypatch):
    from netmon.features import firewall_controller as controller

    parent = Path("/work/home/.local/state/netmon")
    parent.mkdir(parents=True, exist_ok=True)
    parent.chmod(0o770)
    monkeypatch.setattr(
        controller.nm_ownership, "verified_interface", lambda name: {"name": name}
    )
    app, logs = native_application(system)
    before = system.capture()
    previous = os.umask(0o002)
    try:
        assert controller.killswitch_on_sync(app, refresh_ui=False), logs
        assert controller.killswitch_off_sync(app, refresh_ui=False), logs
    finally:
        os.umask(previous)
    assert system.capture() == before
    assert app.killswitch_journal.directory.stat().st_mode & 0o777 == 0o700
    assert parent.stat().st_mode & 0o777 == 0o770
    assert any("Killswitch AUS" in line for line in logs)
    assert ufw_cli(["allow", "out", "on", "wg0"])[0] == 0
    current = system.capture()
    assert not controller.firewall_recovery_pending(app)
    assert controller.killswitch_on_sync(app, refresh_ui=False), logs
    assert controller.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == current


def test_manual_completion_changes_no_firewall_and_removal_keeps_active_helper(system):
    from netmon.core.ufw_snapshot import MUTABLE

    before = system.capture()
    assert system.acknowledge()["state"] == "reviewed"
    assert system.capture() == before
    token, _ = activate(system)
    system.commit(token)
    active = system.capture()
    for phase in ("active", "applying", "recovery"):
        record = system.load()
        record["phase"] = phase
        system.save(record)
        for action in (system.acknowledge, system.removal):
            with pytest.raises(Exception) as error:
                action()
            assert error.value.code == "pending"
            assert system.capture() == active
    # Simulate an administrator's completed manual repair, keeping the pending
    # receipt. ACK may retire authority, but must not rewrite these files/tables.
    original = system.load()["original"]
    for name in MUTABLE:
        system._write(Path(name), original["files"][name])
    system.backend.restore(original["runtime"])
    repaired = system.capture()
    assert system.acknowledge()["state"] == "reviewed"
    assert system.state()["state"] == "reviewed"
    assert system.capture() == repaired
    with pytest.raises(Exception) as error:
        system.restore()
    assert error.value.code == "no_snapshot"
    assert system.removal()["removable"]
    assert system.capture() == before


def test_unmodified_failed_activation_can_be_retired_without_emergency(system):
    before = system.capture()
    system.begin(PLAN)
    assert system.abort_unmodified()["unmodified"]
    assert system.capture() == before
    assert system.state()["state"] == "off"
    token = system.begin(PLAN)["token"]
    assert system.command(token, ["default", "deny", "outgoing"])["rc"] == 0
    assert system.abort_unmodified()["unmodified"] is False
    system.restore()
    assert system.capture() == before


def test_orphaned_deny_tuples_are_detected_without_any_netmon_mutation(system):
    import re

    for direction in ("in", "out"):
        assert ufw_cli(["deny", direction, "from", "any", "to", "any"])[0] == 0
    for name in ("user.rules", "user6.rules"):
        path = Path("/etc/ufw") / name
        text, count = re.subn(
            r"^-A ufw6?-user-(?:input|output) -j DROP\n",
            "",
            path.read_text(),
            flags=re.M,
        )
        assert count == 2
        path.write_text(text)
    assert reboot().returncode == 0
    current = system.capture()
    with pytest.raises(Exception):
        system.begin(PLAN)
    assert system.capture() == current
    assert system.load() is None
    # The external UFW writer, unlike NetMon's preflight, trusts surviving tuples.
    assert ufw_cli(["allow", "22/tcp"])[0] == 0
    for name in ("user.rules", "user6.rules"):
        assert Path("/etc/ufw", name).read_text().count("-j DROP") == 2
    assert reboot().returncode == 0
    for rows in system.backend.runtime().values():
        assert sum(row.endswith(" -j DROP") and "user-" in row for row in rows) == 2


def test_legacy_active_killswitch_is_not_captured_as_unprotected_off_baseline(system):
    from support import ON

    for action in ON:
        assert ufw_cli(action)[0] == 0
    current = system.capture()
    assert system.backend.verify_enabled(PLAN)
    with pytest.raises(Exception) as error:
        system.begin(PLAN)
    assert error.value.code == "no_snapshot"
    assert system.capture() == current
    assert system.load() is None


def test_mixed_user_limit_app_route_and_comment_rules_survive_exactly(system):
    profile = Path("/etc/ufw/applications.d/NetMonTestApp")
    profile.write_text(
        "[NetMonTestApp]\ntitle=Private test\ndescription=Fixture\nports=8443/tcp\n"
    )
    rules = [
        ["limit", "22/tcp"],
        ["allow", "NetMonTestApp"],
        ["allow", "12345/tcp", "comment", "-m"],
        [
            "route",
            "allow",
            "in",
            "on",
            "eth0",
            "out",
            "on",
            "wg0",
            "to",
            "192.0.2.0/24",
            "port",
            "8443",
            "proto",
            "tcp",
        ],
    ]
    for rule in rules:
        assert ufw_cli(rule)[0] == 0, rule
    before = system.capture()
    token, results = activate(system)
    assert all(rc == 0 for _command, rc in results), results
    system.commit(token)
    assert reboot().returncode == 0
    assert system.state()["state"] == "on"
    assert system.restore()["state"] == "off"
    assert system.capture() == before
