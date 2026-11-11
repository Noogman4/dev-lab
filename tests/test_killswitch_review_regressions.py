"""Review fixes independent of the kernel; all external commands are fakes."""

import json
import os
import threading
from types import SimpleNamespace

import pytest

from netmon.core.killswitch_journal import KillswitchJournal
from netmon.core import command, ufw_snapshot
from netmon.features import firewall_controller as firewall
from tools import netmon


def test_default_journal_uses_private_leaf_under_group_writable_netmon(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    parent = tmp_path / "netmon"
    parent.mkdir()
    parent.chmod(0o770)
    journal = KillswitchJournal()
    assert journal.phase() == "absent"
    previous = os.umask(0o002)
    try:
        journal.mark("applying")
    finally:
        os.umask(previous)
    assert journal.directory.stat().st_mode & 0o777 == 0o700
    assert parent.stat().st_mode & 0o777 == 0o770
    assert KillswitchJournal().phase() == "applying"


def test_old_pending_marker_is_not_silently_lost(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    parent = tmp_path / "netmon"
    KillswitchJournal(parent).mark("recovery_required")
    assert KillswitchJournal().phase() == "recovery_required"
    parent.chmod(0o770)
    assert KillswitchJournal().phase() == "unreadable"


@pytest.mark.parametrize("operation", ["off", "recovery"])
def test_missing_helper_does_not_invent_a_pending_mutation(tmp_path, operation):
    calls, logs = [], []

    def unavailable(action, payload):
        calls.append(action)
        raise ufw_snapshot.SnapshotError("Helper unavailable", "no_snapshot")

    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        killswitch_journal=KillswitchJournal(tmp_path / "journal"),
        firewall_snapshots=ufw_snapshot.UfwSnapshotClient(unavailable),
        log_safe=logs.append,
    )
    target = (
        firewall.killswitch_off_sync
        if operation == "off"
        else firewall.recover_firewall_after_killswitch_failure
    )
    assert target(app, **({"refresh_ui": False} if operation == "off" else {})) is False
    assert app.killswitch_journal.phase() == "absent"
    assert not app.__dict__.get("killswitch_recovery_required", False)
    assert not any("Killswitch AUS" in line for line in logs)
    assert calls == ["restore" if operation == "off" else "begin"]


@pytest.mark.parametrize("state", ["on", "recovery", "unknown"])
@pytest.mark.parametrize(
    "args",
    [
        ["sudo", "-n", "ufw", "logging", "high"],
        ["sudo", "-n", "ufw", "allow", "22/tcp"],
        ["ufw", "allow", "out", "443/tcp"],
        ["sudo", "-n", "ufw", "default", "allow", "outgoing"],
    ],
)
def test_unrelated_writes_cannot_bypass_active_or_pending_killswitch(state, args):
    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        firewall_snapshots=SimpleNamespace(state=lambda: state),
    )
    rc, message = firewall.guarded_ufw_command(
        app,
        args,
        runner=lambda *_a, **_k: pytest.fail("Unrelated UFW mutation escaped"),
    )
    assert rc != 0 and "gesperrt" in message


def test_normal_writes_after_retired_snapshot_are_allowed():
    calls = []
    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        firewall_snapshots=SimpleNamespace(state=lambda: "off"),
        _read_ufw_status=lambda **_k: (0, "Status: active\n22/tcp ALLOW OUT Anywhere"),
    )
    args = ["sudo", "-n", "ufw", "allow", "out", "on", "wg0"]
    assert (
        firewall.guarded_ufw_command(
            app, args, runner=lambda cmd, **_k: (calls.append(cmd) or 0, "ok")
        )[0]
        == 0
    )
    assert calls == [args]


def test_dns_finalize_cannot_bypass_pending_firewall_gate():
    app = netmon.App.__new__(netmon.App)
    app.firewall_snapshots = SimpleNamespace(state=lambda: "recovery")
    app.log_safe = lambda *_a: None
    app._collect_dot_status = lambda **_k: pytest.fail("DNS finalization must pause")
    app._restore_isp_dns_after_vpn_switch = lambda: pytest.fail("DNS mutation escaped")
    assert app.finalize_dns_after_vpn_profile_switch() is False


def test_old_helper_is_rejected_before_any_mutating_rpc(monkeypatch):
    calls = []
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)

    def old_helper(args, **kwargs):
        calls.append(args[-1])
        return 1, json.dumps({"protocol": 1, "error": "snapshot_failed"})

    monkeypatch.setattr(command, "run_cmd_with_input", old_helper)
    with pytest.raises(ufw_snapshot.SnapshotError) as error:
        ufw_snapshot.UfwSnapshotClient().begin()
    assert error.value.code == "incompatible"
    assert calls == ["capabilities"]


def test_gui_observation_is_nonblocking_and_stale_workers_cannot_publish(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    threads = []
    real_thread = threading.Thread

    def observe(_app):
        entered.set()
        assert release.wait(2)
        return "on"

    def worker(**kwargs):
        thread = real_thread(**kwargs)
        threads.append(thread)
        return thread

    app = SimpleNamespace()
    monkeypatch.setattr(firewall, "killswitch_state", observe)
    monkeypatch.setattr(firewall.threading, "Thread", worker)
    assert firewall.cached_killswitch_state(app) == "unknown"
    assert entered.wait(1)
    assert firewall.cached_killswitch_state(app) == "unknown"
    assert len(threads) == 1
    firewall._invalidate_killswitch_cache(app)
    release.set()
    threads[0].join(2)
    assert not threads[0].is_alive()
    assert "_killswitch_cached_state" not in app.__dict__


@pytest.mark.parametrize("confirmed", [False, True])
def test_manual_review_requires_confirmation_and_never_runs_ufw(tmp_path, confirmed):
    calls, logs = [], []
    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        killswitch_journal=KillswitchJournal(tmp_path / "journal"),
        killswitch_recovery_required=True,
        firewall_snapshots=SimpleNamespace(acknowledge=lambda: calls.append("review")),
        _confirm_danger_action=lambda *a, **k: confirmed
        and k["require_phrase"] == "MANUELL GEPRUEFT",
        run_async=lambda fn, **kwargs: fn(),
        log_safe=logs.append,
    )
    assert firewall.acknowledge_manual_firewall_review(app) is confirmed
    assert calls == (["review"] if confirmed else [])
    assert app.killswitch_journal.phase() == (
        "manual_reviewed" if confirmed else "absent"
    )
    assert app.killswitch_recovery_required is not confirmed


def test_manual_review_label_never_claims_verified_off(tmp_path):
    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        killswitch_journal=KillswitchJournal(tmp_path / "journal"),
        _read_ufw_status=lambda **_k: (0, "Status: active"),
        tr=lambda _key, fallback: fallback,
    )
    app.killswitch_journal.mark("manual_reviewed")
    state = firewall.killswitch_state(app)
    assert state == "reviewed"
    assert not firewall.firewall_recovery_pending(app)
    assert "OFF" not in firewall.killswitch_status_label(app, state)
    assert "geprüft" in firewall.killswitch_status_label(app, state)


def test_native_family_failure_does_not_skip_other_family(monkeypatch):
    rows = {
        family: [
            ":INPUT DROP [0:0]",
            ":OUTPUT DROP [0:0]",
            f":{prefix}user-output - [0:0]",
        ]
        for family, prefix in (("4", "ufw-"), ("6", "ufw6-"))
    }
    monkeypatch.setattr(ufw_snapshot.NativeUfw, "runtime", lambda _self: rows)
    calls = []

    def execute(args, data=None):
        calls.append(args[0])
        if "ip6tables" not in args[0]:
            raise ufw_snapshot.SnapshotError("Injected IPv4 failure")

    monkeypatch.setattr(ufw_snapshot.NativeUfw, "_execute", staticmethod(execute))
    with pytest.raises(ufw_snapshot.SnapshotError):
        ufw_snapshot.NativeUfw().restore(rows)
    assert calls == ["/usr/sbin/iptables-restore", "/usr/sbin/ip6tables-restore"]


@pytest.mark.parametrize(
    "comment", ["-s", "-j", "-m", "with spaces", 'quote"back\\slash']
)
def test_kernel_normalization_does_not_interpret_comment_values(comment):
    import shlex

    tokens = [
        "-A",
        "ufw-user-input",
        "-p",
        "tcp",
        "-m",
        "tcp",
        "--dport",
        "22",
        "-m",
        "comment",
        "--comment",
        comment,
        "-j",
        "ACCEPT",
    ]
    row = ufw_snapshot._runtime_row(ufw_snapshot._iptables_line(tokens))
    parsed = shlex.split(row)
    assert parsed[parsed.index("--comment") + 1] == comment
    assert parsed[-2:] == ["-j", "ACCEPT"]


def test_known_kernel_recent_defaults_are_equivalent_to_ufw_file_syntax():
    left = "-A ufw-user-input -p tcp --dport 22 -m recent --set"
    right = "-A ufw-user-input -p tcp -m tcp --dport 22 -m recent --set --name DEFAULT --mask 255.255.255.255 --rsource"
    assert ufw_snapshot._runtime_row(left) == ufw_snapshot._runtime_row(right)


def test_unknown_kernel_extension_keeps_its_option_values():
    import shlex

    tokens = ["-A", "ufw-before-input", "-m", "string", "--string", "-s", "-j", "DROP"]
    assert (
        shlex.split(ufw_snapshot._runtime_row(ufw_snapshot._iptables_line(tokens)))
        == tokens
    )


@pytest.mark.parametrize("action", ["logging", "game-add", "game-rollback"])
def test_real_app_entrypoints_cannot_write_around_active_snapshot(monkeypatch, action):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.firewall_snapshots = SimpleNamespace(state=lambda: "on")
    app.log_safe = lambda *_a: None
    app._read_ufw_status = lambda **_k: (0, "Status: active")
    monkeypatch.setattr(
        netmon,
        "run_cmd",
        lambda *_a, **_k: pytest.fail("Direct app command escaped the Killswitch gate"),
    )
    rule = {"type": "standard_port", "direction": "out", "port": "443", "proto": "tcp"}
    if action == "logging":
        result = app._set_ufw_logging_sync("high", ensure_sudo=False)
    elif action == "game-add":
        result = app._apply_game_mode_ufw_exception_rules([rule])[0]
    else:
        result = app._rollback_game_mode_ufw_exception_rules([rule])[0]
    assert result is False


@pytest.mark.parametrize("action", ["ssh-add", "ssh-remove"])
def test_ssh_workers_cannot_write_around_active_snapshot(monkeypatch, action):
    class Immediate:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        firewall_snapshots=SimpleNamespace(state=lambda: "on"),
        ensure_sudo_session=lambda *_a: True,
        after=lambda *_a: None,
        log=lambda *_a: None,
        tr=lambda _key, fallback: fallback,
    )
    calls = []

    def run(args, **kwargs):
        assert args[3] == "status", "SSH mutation bypassed the gate"
        calls.append(args)
        return 0, (
            "Status: active\n[1] 22/tcp ALLOW IN Anywhere"
            if action == "ssh-remove"
            else "Status: active"
        )

    monkeypatch.setattr(firewall.threading, "Thread", Immediate)
    monkeypatch.setattr(firewall, "run_cmd", run)
    if action == "ssh-add":
        firewall.allow_ssh_rule_async(app)
    else:
        firewall.remove_ssh_rule_async(app, auto=True)
    assert len(calls) == 1


def test_baseline_gate_precedes_profile_dialogs_and_configuration_writes():
    from netmon.features import security_audit_controller

    app = SimpleNamespace(
        firewall_snapshots=SimpleNamespace(state=lambda: "on"),
        log_safe=lambda *_a: None,
    )
    assert security_audit_controller.apply_security_baseline_ufw(app) is False


def test_non_killswitch_vpn_service_rechecks_after_acquiring_mutation_lock(monkeypatch):
    from netmon.features import vpn_controller

    observations = iter(["off", "off", "on", "on"])
    monkeypatch.setattr(
        vpn_controller, "_network_links", lambda: {"wg0": (42, "wireguard")}
    )
    app = SimpleNamespace(
        _wg_activation_links={"wg0": 42},
        ufw_lock=threading.Lock(),
        firewall_snapshots=SimpleNamespace(state=lambda: next(observations)),
        _network_service=lambda: SimpleNamespace(),
        _read_ufw_status=lambda **_k: pytest.fail(
            "Plain VPN service reached a protected transaction"
        ),
        log=lambda *_a: None,
    )
    assert (
        vpn_controller.apply_profile_ufw_rules_non_killswitch(app, ["wg0"], []) is False
    )


@pytest.mark.parametrize("state", ["on", "recovery", "unknown"])
@pytest.mark.parametrize("action", ["interface", "endpoint", "reconcile"])
def test_profile_cleanup_cannot_bypass_firewall_transaction(monkeypatch, state, action):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.firewall_snapshots = SimpleNamespace(state=lambda: state)
    app.log = app.log_safe = app.log_debug = lambda *_a: None
    app._try_begin_network_operation = lambda *_a: True
    app._end_network_operation = lambda *_a: None
    app._read_ufw_status = lambda **_k: (0, "Status: active")
    monkeypatch.setattr(netmon, "has_cmd", lambda *_a: True)
    monkeypatch.setattr(
        netmon,
        "run_cmd",
        lambda *_a, **_k: pytest.fail("Profile deletion escaped transaction gate"),
    )
    if action == "interface":
        assert app._remove_interface_rule("wg0", "out")[0] == "failed"
    elif action == "endpoint":
        assert app._remove_udp_endpoint_rule("198.51.100.10", "51820")[0] == "failed"
    else:
        assert (
            app._reconcile_vpn_firewall_rules(
                {"wg0"}, set(), {("198.51.100.10", "51820")}, set()
            )
            is False
        )


@pytest.mark.parametrize(
    "args",
    [
        ["insert", "1", "allow", "out", "on", "eth0"],
        ["insert", "1", "allow", "in", "on", "lo"],
    ],
)
def test_interface_fence_extension_never_allows_inserted_unverified_grants(args):
    with pytest.raises(ufw_snapshot.SnapshotError):
        ufw_snapshot._command(args)


def policy_snapshot(defaults, conf="ENABLED=yes\nLOGLEVEL=low\n"):
    import base64

    return {
        "files": {
            name: {"data": base64.b64encode(data.encode()).decode()}
            for name, data in (
                ("/etc/default/ufw", defaults),
                ("/etc/ufw/ufw.conf", conf),
            )
        }
    }


def test_persistent_policies_follow_ufw_init_source_order():
    defaults = 'DEFAULT_INPUT_POLICY="DROP"\nDEFAULT_OUTPUT_POLICY="ACCEPT"\nDEFAULT_FORWARD_POLICY="DROP"\nIPT_MODULES="nf_conntrack_ftp nf_nat_ftp"\n'
    original = ufw_snapshot.persistent_policies(policy_snapshot(defaults))
    overridden = ufw_snapshot.persistent_policies(
        policy_snapshot(defaults, 'ENABLED=yes\nDEFAULT_OUTPUT_POLICY="DROP"\n')
    )
    assert original["DEFAULT_OUTPUT_POLICY"] == "ACCEPT"
    assert overridden["DEFAULT_OUTPUT_POLICY"] == "DROP"


@pytest.mark.parametrize(
    "line",
    [
        "export DEFAULT_OUTPUT_POLICY=DROP",
        "DEFAULT_OUTPUT_POLICY=$(false)",
        ". /etc/other-firewall-settings",
        "DEFAULT_OUTPUT_POLICY=DROP; true",
        "DEFAULT_OUTPUT_POLICY=$OTHER_POLICY",
    ],
)
def test_persistent_policy_verification_never_accepts_unevaluated_shell(line):
    defaults = 'DEFAULT_INPUT_POLICY="DROP"\nDEFAULT_OUTPUT_POLICY="ACCEPT"\nDEFAULT_FORWARD_POLICY="DROP"\n'
    with pytest.raises(ufw_snapshot.SnapshotError) as error:
        ufw_snapshot.persistent_policies(policy_snapshot(defaults + line + "\n"))
    assert error.value.code == "pending"


@pytest.mark.parametrize(
    "line",
    [
        "X=1#;DEFAULT_OUTPUT_POLICY=DROP",
        "X=1#$(printf DROP)",
        'X="1"#;DEFAULT_OUTPUT_POLICY=DROP',
        "X=1;DEFAULT_OUTPUT_POLICY=DROP # misleading comment",
        "X=one two # unquoted words",
        "X=1\\#;DEFAULT_OUTPUT_POLICY=DROP",
        "\u00a0DEFAULT_OUTPUT_POLICY=ACCEPT",
        "X=1\u2028DEFAULT_OUTPUT_POLICY=ACCEPT",
        "X=1\u0085DEFAULT_OUTPUT_POLICY=ACCEPT",
        "X=1\vDEFAULT_OUTPUT_POLICY=ACCEPT",
    ],
)
def test_policy_grammar_does_not_discard_non_comment_shell_text(line):
    defaults = "DEFAULT_INPUT_POLICY=DROP\nDEFAULT_OUTPUT_POLICY=ACCEPT\nDEFAULT_FORWARD_POLICY=DROP\n"
    with pytest.raises(ufw_snapshot.SnapshotError) as exc:
        ufw_snapshot.persistent_policies(policy_snapshot(defaults + line + "\n"))
    assert exc.value.code == "pending"


@pytest.mark.parametrize(
    "line",
    [
        "X=1 #;DEFAULT_OUTPUT_POLICY=DROP",
        'X="one two" # normal comment',
        "X='one two'\t# normal comment",
        "IPT_MODULES=",
        "# DEFAULT_OUTPUT_POLICY=DROP",
        "  X=1\t# $(false);DEFAULT_OUTPUT_POLICY=DROP  ",
    ],
)
def test_policy_literal_assignments_and_word_boundary_comments_remain_supported(line):
    defaults = "DEFAULT_INPUT_POLICY=DROP\nDEFAULT_OUTPUT_POLICY=ACCEPT\nDEFAULT_FORWARD_POLICY=DROP\n"
    assert (
        ufw_snapshot.persistent_policies(policy_snapshot(defaults + line + "\n"))[
            "DEFAULT_OUTPUT_POLICY"
        ]
        == "ACCEPT"
    )


@pytest.mark.parametrize(
    "row,port,proto,expected",
    [
        ("198.51.100.53 51820/udp ALLOW OUT Anywhere", "53", "udp", False),
        ("53.1.2.3 51820/udp ALLOW OUT Anywhere", "53", "udp", False),
        ("198.53.1.2 51820/udp ALLOW OUT Anywhere", "53", "udp", False),
        ("2001:db8::53 51820/udp ALLOW OUT Anywhere (v6)", "53", "udp", False),
        ("198.51.100.80 51820/udp ALLOW OUT Anywhere", "80", "tcp", False),
        ("53/udp ALLOW OUT Anywhere", "53", "udp", True),
        ("53/tcp ALLOW OUT Anywhere", "53", "tcp", True),
        ("53 ALLOW OUT Anywhere", "53", "udp", True),
        ("53 ALLOW OUT Anywhere", "53", "tcp", True),
        ("9.9.9.9 53/udp ALLOW OUT Anywhere", "53", "udp", True),
        ("53/udp ALLOW IN Anywhere", "53", "udp", False),
        ("53/udp DENY OUT Anywhere", "53", "udp", False),
        ("51820/udp ALLOW OUT 198.51.100.53", "53", "udp", False),
    ],
)
def test_outgoing_port_comparison_uses_parsed_destination(row, port, proto, expected):
    assert firewall.ufw_has_outgoing_port_rule(row, port, proto) is expected


def test_only_exact_planned_udp_endpoint_is_exempt_from_dns_check():
    plan = [("2001:db8::53", "53"), ("198.51.100.10", "53")]
    status = "\n".join(
        [
            "2001:0db8:0:0:0:0:0:53 53/udp ALLOW OUT Anywhere (v6)",
            "198.51.100.10 53/udp ALLOW OUT Anywhere",
        ]
    )
    assert not firewall.ufw_has_outgoing_port_rule(
        status, "53", "udp", handshake_rules=plan
    )
    for extra in (
        "53/udp ALLOW OUT Anywhere",
        "198.51.100.11 53/udp ALLOW OUT Anywhere",
        "198.51.100.10 53 ALLOW OUT Anywhere",
    ):
        assert firewall.ufw_has_outgoing_port_rule(
            status + "\n" + extra, "53", "udp", handshake_rules=plan
        )


def test_protocol_five_helper_cannot_perform_manual_acknowledgement(monkeypatch):
    calls = []
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)

    def v5_helper(args, **_kwargs):
        calls.append(args[-1])
        return 0, json.dumps({"protocol": 5, "prepared_commands": True})

    monkeypatch.setattr(command, "run_cmd_with_input", v5_helper)
    with pytest.raises(ufw_snapshot.SnapshotError) as exc:
        ufw_snapshot.UfwSnapshotClient().acknowledge()
    assert exc.value.code == "incompatible"
    assert calls == ["capabilities"]


@pytest.mark.parametrize(
    "ports,port,expected",
    [
        ("53,443", "53", True),
        ("53,443", "443", True),
        ("53,443", "54", False),
        ("50:60", "49", False),
        ("50:60", "50", True),
        ("50:60", "53", True),
        ("50:60", "60", True),
        ("50:60", "61", False),
        ("50:52,53,440:445", "443", True),
        ("0:60", "53", False),
        ("60:50", "53", False),
        ("1:65536", "53", False),
        ("53,,443", "53", False),
    ],
)
def test_port_list_and_range_comparison(ports, port, expected):
    assert firewall._port_expression_contains(ports, port) is expected


@pytest.mark.parametrize("ports", ["53,443", "50:60", "50:52,53,440:445"])
def test_multiport_never_counts_as_one_exact_planned_endpoint(ports):
    status = f"198.51.100.53 {ports}/udp ALLOW OUT Anywhere"
    assert firewall.parse_ufw_structured_rule(status)["port"] == ports
    assert not firewall.ufw_has_endpoint_rule(status, "198.51.100.53", "53")
    assert firewall.ufw_has_outgoing_port_rule(
        status, "53", "udp", handshake_rules=[("198.51.100.53", "53")]
    )


@pytest.mark.parametrize("operation", ["begin", "commit"])
def test_protocol_six_helper_cannot_skip_limit_preflight(monkeypatch, operation):
    calls = []
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)

    def helper(args, **_kwargs):
        calls.append(args[-1])
        return 0, json.dumps({"protocol": 6, "prepared_commands": True})

    monkeypatch.setattr(command, "run_cmd_with_input", helper)
    with pytest.raises(ufw_snapshot.SnapshotError) as exc:
        ufw_snapshot.UfwSnapshotClient().request(operation, {})
    assert exc.value.code == "incompatible"
    assert calls == ["capabilities"]


def test_protocol_seven_helper_cannot_begin_before_new_order_preflight(monkeypatch):
    calls = []
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)

    def helper(args, **_kwargs):
        calls.append(args[-1])
        return 0, json.dumps({"protocol": 7, "prepared_commands": True})

    monkeypatch.setattr(command, "run_cmd_with_input", helper)
    with pytest.raises(ufw_snapshot.SnapshotError) as exc:
        ufw_snapshot.UfwSnapshotClient().request("begin", {})
    assert exc.value.code == "incompatible"
    assert calls == ["capabilities"]


def service_verification_status(extra=""):
    rows = [
        "Status: active",
        "Default: deny (incoming), deny (outgoing), disabled (routed)",
    ]
    for suffix in ("", " (v6)"):
        for iface in ("lo", "wg0"):
            for direction in ("IN", "OUT"):
                rows.append(
                    f"Anywhere{suffix} on {iface} ALLOW {direction} Anywhere{suffix}"
                )
    return "\n".join(rows) + "\n" + extra


def verify_service_status(text):
    app = SimpleNamespace(
        _ufw_status_is_active=firewall.ufw_status_is_active,
        _ufw_default_policy_matches=firewall.ufw_default_policy_matches,
        _ufw_has_interface_rule=firewall.ufw_has_interface_rule,
        _ufw_has_endpoint_rule=firewall.ufw_has_endpoint_rule,
    )
    return firewall.verify_killswitch_rules(app, text, True, ["wg0"], [])


@pytest.mark.parametrize(
    "port,proto", [("53", "udp"), ("53", "tcp"), ("80", "tcp"), ("443", "tcp")]
)
def test_only_safe_bound_service_rules_are_exempt_in_verification(port, proto):
    for iface, expected in (("wg0", True), ("lo", True), ("eth0", False)):
        row = f"{port}/{proto} on {iface} ALLOW OUT Anywhere"
        assert firewall.ufw_has_outgoing_port_rule(row, port, proto)
        assert verify_service_status(service_verification_status(row))[0] is expected
    assert not verify_service_status(
        service_verification_status(f"{port}/{proto} ALLOW OUT Anywhere")
    )[0]


@pytest.mark.parametrize("fence_kind", ["both", "v4_only", "late", "specific"])
def test_blocked_interface_service_exception_needs_leading_dual_family_deny(fence_kind):
    fences = ["Anywhere on manual1 DENY OUT Anywhere"]
    if fence_kind != "v4_only":
        fences.append("Anywhere (v6) on manual1 DENY OUT Anywhere (v6)")
    if fence_kind == "specific":
        fences[0] = "9.9.9.9 on manual1 DENY OUT Anywhere"
    grant = "443/tcp on manual1 ALLOW OUT Anywhere"
    extra = "\n".join(
        ([grant] + fences) if fence_kind == "late" else (fences + [grant])
    )
    assert verify_service_status(service_verification_status(extra))[0] is (
        fence_kind == "both"
    )


def fence_metadata_snapshot(action4, action6, extra4=""):
    import base64

    return {
        "files": {
            "/etc/ufw/"
            + name: {
                "data": base64.b64encode(
                    (
                        f"### tuple ### {action} any any {address} any {address} out_manual1\n"
                        + extra
                    ).encode()
                ).decode()
            }
            for name, action, address, extra in (
                ("user.rules", action4, "0.0.0.0/0", extra4),
                ("user6.rules", action6, "::/0", ""),
            )
        }
    }


@pytest.mark.parametrize("logging", ["deny_log", "deny_log-all"])
def test_only_logging_tuples_without_plain_match_imply_a_fresh_fence(logging):
    snapshot = fence_metadata_snapshot(logging, logging)
    expected = {("4", "output", "manual1"), ("6", "output", "manual1")}
    assert ufw_snapshot.logging_only_interface_fences(snapshot) == expected
    extra = "### tuple ### deny any any 0.0.0.0/0 any 0.0.0.0/0 out_manual1 comment=6b656570\n"
    assert ufw_snapshot.logging_only_interface_fences(
        fence_metadata_snapshot(logging, logging, extra)
    ) == {("6", "output", "manual1")}
    assert (
        ufw_snapshot.logging_only_interface_fences(
            fence_metadata_snapshot("deny", "deny")
        )
        == set()
    )


def test_protocol_eight_helper_cannot_skip_logging_aware_preflight(monkeypatch):
    calls = []
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)

    def helper(args, **_kwargs):
        calls.append(args[-1])
        return 0, json.dumps({"protocol": 8, "prepared_commands": True})

    monkeypatch.setattr(command, "run_cmd_with_input", helper)
    with pytest.raises(ufw_snapshot.SnapshotError) as exc:
        ufw_snapshot.UfwSnapshotClient().request("begin", {})
    assert exc.value.code == "incompatible" and calls == ["capabilities"]
