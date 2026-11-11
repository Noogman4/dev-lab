"""Root snapshot workflow exercised over a temporary, unprivileged fake system."""

from copy import deepcopy
import json
import os
import subprocess

import pytest

from netmon.core import ufw_snapshot as snapshot
from netmon.core.killswitch_journal import KillswitchJournal
from netmon.features import firewall_controller as firewall
from netmon.features import vpn_controller as vpn
from test_killswitch_incident import app_context, configured_model


class Backend:
    def __init__(self, root, model):
        self.root, self.model = root, model
        self.fail_restore = False
        self.fail_command = False

    def ready(self):
        return self.model.active

    def verify_interface(self, name):
        assert name == "wg0"

    def runtime(self):
        return {
            family: [
                json.dumps(
                    {"rules": self.model.rules[ipv6], "defaults": self.model.defaults},
                    sort_keys=True,
                )
            ]
            for family, ipv6 in (("4", False), ("6", True))
        }

    def command(self, arguments):
        def execute():
            result = self.model.run(["sudo", "-n", "ufw", *arguments])
            if arguments[:1] != ["status"]:
                for family, name in (("4", "user.rules"), ("6", "user6.rules")):
                    (self.root / "etc" / "ufw" / name).write_text(
                        self.runtime()[family][0]
                    )
                (self.root / "etc/default/ufw").write_text(
                    json.dumps(self.model.defaults)
                )
                if arguments[:1] == ["default"]:
                    for name in ("after.rules", "after6.rules"):
                        (self.root / "etc/ufw" / name).write_text(
                            "UFW logging policy changed"
                        )
            return (1, "synthetic partial failure") if self.fail_command else result

        if self.model.app.ufw_lock.locked():
            return execute()
        with self.model.app.ufw_lock:
            return execute()

    def verify_enabled(self, plan, *, original=None):
        app = self.model.app

        def verify():
            _, text = self.model.status(verbose=True)
            return firewall.verify_killswitch_rules(
                app, text, True, plan["interfaces"], plan["endpoints"]
            )[0]

        if app.ufw_lock.locked():
            return verify()
        with app.ufw_lock:
            return verify()

    def restore(self, runtime):
        for family, ipv6 in (("4", False), ("6", True)):
            row = json.loads(runtime[family][0])
            self.model.rules[ipv6] = [tuple(rule) for rule in row["rules"]]
            self.model.defaults = row["defaults"]
            if self.fail_restore:
                raise OSError("synthetic IPv6 restore failure after IPv4")


@pytest.fixture
def system(tmp_path, monkeypatch):
    root = tmp_path / "system"
    root.mkdir(mode=0o700)
    for name in snapshot.OBSERVED:
        path = root / name.lstrip("/")
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_text(f"original {name}\n")
        path.chmod(0o640)
    for path in root.rglob("*"):
        if path.is_dir():
            path.chmod(0o700)
    model = configured_model("off")
    monkeypatch.setattr(
        vpn,
        "_network_links",
        lambda: {"wg0": (42, "wireguard"), "wg1": (43, "wireguard")},
    )
    # Real preflight rejects unrestricted outbound user grants before mutation.
    # This fake backend has no real-kernel preflight: use a compatible baseline.
    for rules in model.rules.values():
        rules.remove(("ALLOW", "OUT", "443/tcp", "Anywhere"))
    model.defaults["incoming"] = "reject"  # Must not be reset to a guessed deny.
    app_context(model)
    backend = Backend(root, model)
    store = snapshot.SnapshotStore(backend, root=root, owner=os.geteuid())

    def transport(operation, payload):
        if operation == "begin":
            return store.begin(payload)
        if operation == "command":
            return store.command(payload["token"], payload["arguments"])
        if operation in {"commit", "recovery"}:
            return getattr(store, operation)(payload["token"])
        return getattr(store, operation)()

    def attach():
        app = app_context(model)
        app._wg_activation_links = {"wg0": 42}
        app.killswitch_journal = KillswitchJournal(tmp_path / "desktop-state")
        app.firewall_snapshots = snapshot.UfwSnapshotClient(transport)
        return app

    monkeypatch.setattr(
        firewall.nm_ownership, "verified_interface", lambda name: {"name": name}
    )
    return root, model, backend, store, attach


def test_on_off_restores_user_rules_defaults_files_and_both_families(system):
    root, model, backend, store, attach = system
    app = attach()
    before = store.capture()
    before_rules = deepcopy(model.rules)
    assert firewall.killswitch_on_sync(app, refresh_ui=False)
    assert store.load()["phase"] == "active"
    assert ("ALLOW", "IN", "22/tcp", "Anywhere") in model.rules[False]
    assert firewall.killswitch_off_sync(app, refresh_ui=False)
    assert store.capture() == before
    assert model.rules == before_rules
    assert model.defaults == {"incoming": "reject", "outgoing": "allow"}
    assert model.active is True
    assert firewall.killswitch_state(app) == "off"
    assert store.load()["phase"] == "off"


def test_restore_after_application_restart_uses_protected_original(system):
    root, model, backend, store, attach = system
    original = store.capture()
    assert firewall.killswitch_on_sync(attach(), refresh_ui=False)
    app = attach()
    assert app.firewall_snapshots.token is None
    assert firewall.killswitch_state(app) == "on"
    assert firewall.killswitch_off_sync(app, refresh_ui=False)
    assert store.capture() == original


@pytest.mark.parametrize(
    "where", ["user.rules", "before6.rules", "defaults", "runtime4", "runtime6"]
)
def test_external_changes_block_restore_without_overwriting_user_state(system, where):
    root, model, backend, store, attach = system
    app = attach()
    assert firewall.killswitch_on_sync(app, refresh_ui=False)
    if where.startswith("runtime"):
        model.rules[where == "runtime6"].append(("ALLOW", "IN", "8443/tcp", "Anywhere"))
    else:
        path = root / ("etc/default/ufw" if where == "defaults" else "etc/ufw/" + where)
        path.write_text(path.read_text() + "external user change\n")
    changed = store.capture()
    model.logs.clear()
    assert not firewall.killswitch_off_sync(app, refresh_ui=False)
    assert store.capture() == changed
    assert not any("Killswitch AUS" in line for line in model.logs)


def test_partial_activation_error_can_restore_original_without_guessing(system):
    root, model, backend, store, attach = system
    original = store.capture()
    app = attach()
    backend.fail_command = True
    assert not firewall.killswitch_on_sync(app, refresh_ui=False)
    assert store.load()["phase"] == "recovery"
    backend.fail_command = False
    assert firewall.killswitch_off_sync(attach(), refresh_ui=False)
    assert store.capture() == original


def test_failed_ipv6_restore_retains_original_and_recovery_state(system):
    root, model, backend, store, attach = system
    original = store.capture()
    app = attach()
    assert firewall.killswitch_on_sync(app, refresh_ui=False)
    model.logs.clear()
    backend.fail_restore = True
    assert not firewall.killswitch_off_sync(app, refresh_ui=False)
    assert store.load()["phase"] == "recovery"
    assert store.load()["original"] == original
    assert not any("Killswitch AUS" in line for line in model.logs)
    backend.fail_restore = False
    assert firewall.killswitch_off_sync(attach(), refresh_ui=False)
    assert store.capture() == original


@pytest.mark.parametrize("stage", range(1, 7))
def test_abrupt_abort_during_file_restore_is_resumable(system, monkeypatch, stage):
    class Crash(BaseException):
        pass

    root, model, backend, store, attach = system
    original = store.capture()
    assert firewall.killswitch_on_sync(attach(), refresh_ui=False)
    write = store._write
    count = 0

    def crash(path, row):
        nonlocal count
        write(path, row)
        if str(path).endswith(tuple(snapshot.MUTABLE)):
            count += 1
            if count == stage:
                raise Crash()

    monkeypatch.setattr(store, "_write", crash)
    with pytest.raises(Crash):
        store.restore()
    assert store.load()["phase"] == "restoring"
    monkeypatch.setattr(store, "_write", write)
    assert store.restore() == {"state": "off"}
    assert store.capture() == original


def test_no_original_snapshot_means_no_automatic_cleanup(system):
    root, model, backend, store, attach = system
    app = attach()
    before = store.capture()
    assert not firewall.killswitch_off_sync(app, refresh_ui=False)
    assert store.capture() == before and model.calls == []


def test_disabled_ufw_is_not_enabled_to_create_snapshot(system):
    root, model, backend, store, attach = system
    model.active = False
    before = store.capture()
    assert not firewall.killswitch_on_sync(attach(), refresh_ui=False)
    assert store.capture() == before and model.calls == []


@pytest.mark.parametrize(
    "arguments",
    [
        ["disable"],
        ["reset"],
        ["reload"],
        ["--force", "delete", "-1"],
        ["allow", "out", "on", "wg0;reboot"],
        ["allow", "out", "to", "example.org", "port", "53", "proto", "udp"],
    ],
)
def test_unapproved_commands_never_reach_backend(system, arguments):
    root, model, backend, store, attach = system
    token = store.begin({"interfaces": ["wg0"], "endpoints": []})["token"]
    before = store.capture()
    with pytest.raises((snapshot.SnapshotError, ValueError)):
        store.command(token, arguments)
    assert store.capture() == before and model.calls == []


def test_user_owned_journal_cannot_supply_restoration_bytes(system):
    root, model, backend, store, attach = system
    app = attach()
    app.killswitch_journal.mark("off_verified")
    before = store.capture()
    assert not firewall.killswitch_off_sync(app, refresh_ui=False)
    assert store.capture() == before and model.calls == []


def test_snapshot_file_symlink_is_rejected_without_writing_target(system, tmp_path):
    root, model, backend, store, attach = system
    store.begin({"interfaces": ["wg0"], "endpoints": []})
    record = store.registry / "state.json"
    other = tmp_path / "unrelated"
    record.rename(other)
    record.symlink_to(other)
    before = other.read_bytes()
    with pytest.raises(OSError):
        store.restore()
    assert other.read_bytes() == before


def test_native_restore_payload_flushes_only_ufw_chains(monkeypatch):
    calls = []
    monkeypatch.setattr(
        snapshot.NativeUfw,
        "_execute",
        staticmethod(lambda args, data=None: calls.append((args, data)) or ""),
    )
    runtime = {
        family: [
            ":INPUT DROP [0:0]",
            ":OUTPUT ACCEPT [0:0]",
            f":{prefix}output - [0:0]",
            f"-A {prefix}output -p tcp -m tcp --dport 443 -j ACCEPT",
        ]
        for family, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-"))
    }
    monkeypatch.setattr(snapshot.NativeUfw, "runtime", lambda self: deepcopy(runtime))
    snapshot.NativeUfw().restore(runtime)
    assert len(calls) == 2
    for args, data in calls:
        assert args[1:] == ["--wait", "5", "--noflush"]
        assert b"-F INPUT" not in data and b"-F OUTPUT" not in data
        assert b"*filter\n" in data and data.endswith(b"COMMIT\n")


def test_restoration_invalidates_old_activation_token(system):
    root, model, backend, store, attach = system
    app = attach()
    assert firewall.killswitch_on_sync(app, refresh_ui=False)
    token = app.firewall_snapshots.token
    assert firewall.killswitch_off_sync(app, refresh_ui=False)
    before = store.capture()
    with pytest.raises(snapshot.SnapshotError):
        store.recovery(token)
    assert store.capture() == before


def test_corrupt_snapshot_is_not_restored(system):
    root, model, backend, store, attach = system
    assert firewall.killswitch_on_sync(attach(), refresh_ui=False)
    path = store.registry / "state.json"
    record = json.loads(path.read_text())
    record["original"]["runtime"]["4"].append("corrupt row")
    path.write_text(json.dumps(record))
    before = store.capture()
    with pytest.raises(snapshot.SnapshotError):
        store.restore()
    assert store.capture() == before


def test_missing_installed_helper_has_no_privileged_fallback(monkeypatch):
    monkeypatch.setattr(snapshot, "trusted_helper_available", lambda: False)
    client = snapshot.UfwSnapshotClient()
    assert client.state() == "absent"
    with pytest.raises(snapshot.SnapshotError):
        client.begin()


def test_root_cli_cannot_run_from_checkout(monkeypatch):
    monkeypatch.setattr(snapshot.os, "geteuid", lambda: 0)
    assert snapshot.main() == 1


def test_native_mutation_requires_prepared_store():
    with pytest.raises(snapshot.SnapshotError, match="prepared transaction"):
        snapshot.NativeUfw().command(["default", "deny", "outgoing"])


def permitted_runtime():
    return {
        family: [
            ":INPUT DROP [0:0]",
            ":OUTPUT DROP [0:0]",
            *(
                f"-A {prefix}{direction} {flag} {iface} -j ACCEPT"
                for iface in ("lo", "wg0")
                for direction, flag in (("input", "-i"), ("output", "-o"))
            ),
        ]
        for family, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-"))
    }


@pytest.mark.parametrize("family", ["4", "6"])
@pytest.mark.parametrize(
    "failure",
    [
        "missing_loopback",
        "missing_wg",
        "open_policy",
        "global_allow",
        "inverted_interface",
    ],
)
def test_kernel_verification_rejects_partial_or_bypassing_plan(family, failure):
    runtime = permitted_runtime()
    plan = {"interfaces": ["wg0"], "endpoints": []}
    assert snapshot.runtime_matches_plan(runtime, plan)
    prefix = "ufw-user-" if family == "4" else "ufw6-user-"
    if failure.startswith("missing_"):
        iface = "lo" if failure == "missing_loopback" else "wg0"
        runtime[family] = [row for row in runtime[family] if f"-o {iface} " not in row]
    elif failure == "open_policy":
        runtime[family][1] = ":OUTPUT ACCEPT [0:0]"
    elif failure == "global_allow":
        runtime[family].append(f"-A {prefix}output -p tcp --dport 22 -j ACCEPT")
    else:
        runtime[family].append(f"-A {prefix}output ! -o wg0 -j ACCEPT")
    assert not snapshot.runtime_matches_plan(runtime, plan)


@pytest.mark.parametrize("address", ["203.0.113.1", "2001:db8::1"])
def test_endpoint_verification_uses_exact_ip_port_and_udp(address):
    suffix = " (v6)" if ":" in address else ""
    status = f"{address} 51820/udp{suffix}  ALLOW OUT  Anywhere{suffix} # handshake"
    assert firewall.ufw_has_endpoint_rule(status, address, "51820")
    assert not firewall.ufw_has_endpoint_rule(status, address, "5182")
    assert not firewall.ufw_has_endpoint_rule(
        status.replace("/udp", "/tcp"), address, "51820"
    )
    if ":" in address:
        assert firewall.ufw_has_endpoint_rule(
            status, "2001:0db8:0000:0000:0000:0000:0000:0001", "51820"
        )


def test_vpn_and_dns_automatic_mutations_pause_during_recovery(system, monkeypatch):
    root, model, backend, store, attach = system
    app = attach()
    app.killswitch_journal.mark("restoring")
    monkeypatch.setattr(
        vpn,
        "_network_links",
        lambda: pytest.fail("Pending recovery must precede device inspection"),
    )
    app.resolve_profile_family_runtime = lambda *a, **kw: {"runtime_profile": "work"}
    app.log = model.logs.append
    assert not vpn.vpn_switch(app, "work", ensure_sudo=False, refresh_ui=False)
    assert not vpn.reconcile_vpn_slot_firewall_state(app)
    assert not vpn.apply_profile_ufw_rules_non_killswitch(app, ["wg0"], [])
    from tools import netmon

    result, detail = netmon.App.enforce_dns_clean(app)
    assert result is False and "pausiert" in detail
    assert model.calls == []


def test_allowed_rule_commands_match_installed_ufw_parser():
    available = subprocess.run(
        [
            "/usr/bin/python3",
            "-I",
            "-c",
            "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('ufw') else 77)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if available.returncode == 77:
        pytest.skip(
            "System UFW Python parser is not installed in this test environment"
        )
    assert available.returncode == 0, available.stderr
    commands = [
        ["status", "verbose"],
        ["status", "numbered"],
        ["allow", "in", "on", "lo"],
        ["allow", "out", "to", "2001:db8::1", "port", "51820", "proto", "udp"],
        ["--force", "delete", "1"],
        ["insert", "1", "deny", "out", "from", "any", "to", "any"],
    ]
    script = "import gettext,json,sys; import ufw.frontend; gettext.install('ufw'); commands=json.load(sys.stdin); [ufw.frontend.parse_command(['ufw', *c]) for c in commands]; print('parsed')"
    result = subprocess.run(
        ["/usr/bin/python3", "-I", "-c", script],
        input=json.dumps(commands),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "parsed"


@pytest.mark.parametrize("helper_available", [False, True])
def test_startup_identity_distinguishes_actual_controller_files(
    monkeypatch, helper_available
):
    import builtins
    import hashlib
    import io

    real_open = builtins.open
    helper_bytes = b"synthetic installed helper identity"

    def controlled_helper(path, *args, **kwargs):
        if os.fspath(path) == snapshot.HELPER:
            if helper_available:
                return io.BytesIO(helper_bytes)
            raise FileNotFoundError("simulated missing installed helper")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", controlled_helper)
    text = firewall.firewall_implementation_identity()
    assert firewall.__file__ in text and snapshot.__file__ in text
    assert text.count("file_sha256=") == 5
    assert "executed_helper=" + snapshot.HELPER in text
    assert text.count("unreadable") == int(not helper_available)
    if helper_available:
        assert (
            "executed_helper="
            + snapshot.HELPER
            + " file_sha256="
            + hashlib.sha256(helper_bytes).hexdigest()
            in text
        )


def test_reapply_with_new_interface_retires_only_previous_transaction_grants(
    system, monkeypatch
):
    root, model, backend, store, attach = system
    original = store.capture()
    app = attach()
    assert firewall.killswitch_on_sync(app, refresh_ui=False)
    monkeypatch.setattr(backend, "verify_interface", lambda name: None)
    app.get_wg_interfaces = lambda: ["wg1"]
    app._wg_activation_links = {"wg1": 43}
    assert firewall.killswitch_on_sync(app, refresh_ui=False)
    for rules in model.rules.values():
        assert not any(rule[3] == "Anywhere on wg0" for rule in rules)
        assert any(rule[3] == "Anywhere on wg1" for rule in rules)
    assert firewall.killswitch_off_sync(app, refresh_ui=False)
    assert store.capture() == original


@pytest.mark.parametrize(
    "code,fragment",
    [
        ("no_snapshot", "Sicherung"),
        ("conflict", "Benutzeränderungen"),
        ("rollback_failed", "Rollback"),
        ("inactive", "IPv4/IPv6"),
    ],
)
def test_client_error_codes_are_specific_without_exposing_backend_data(
    monkeypatch, code, fragment
):
    from netmon.core import command

    calls = []
    monkeypatch.setattr(snapshot, "trusted_helper_available", lambda: True)

    def run(args, **kwargs):
        calls.append(args)
        if args[-1] == "capabilities":
            return 0, json.dumps(
                {"protocol": snapshot.PROTOCOL, "prepared_commands": True}
            )
        return 1, json.dumps(
            {
                "protocol": snapshot.PROTOCOL,
                "error": code,
                "private_data": "NEVER_RELAY",
            }
        )

    monkeypatch.setattr(command, "run_cmd_with_input", run)
    with pytest.raises(snapshot.SnapshotError) as error:
        snapshot.UfwSnapshotClient().restore()
    assert fragment in str(error.value) and "NEVER_RELAY" not in str(error.value)
    assert calls == [
        [
            "sudo",
            "-n",
            "/usr/bin/python3",
            "-I",
            "-c",
            snapshot.BOOTSTRAP,
            "capabilities",
        ],
        ["sudo", "-n", "/usr/bin/python3", "-I", "-c", snapshot.BOOTSTRAP, "restore"],
    ]


def test_incompatible_helper_protocol_never_confirms_off(monkeypatch):
    from netmon.core import command

    monkeypatch.setattr(snapshot, "trusted_helper_available", lambda: True)
    monkeypatch.setattr(
        command,
        "run_cmd_with_input",
        lambda *a, **k: (0, '{"state":"off","protocol":999}'),
    )
    with pytest.raises(snapshot.SnapshotError):
        snapshot.UfwSnapshotClient().restore()


def test_protected_restore_refuses_inactive_ufw_without_enabling_it(system):
    root, model, backend, store, attach = system
    assert firewall.killswitch_on_sync(attach(), refresh_ui=False)
    model.active = False
    before = store.capture()
    calls = list(model.calls)
    assert not firewall.killswitch_off_sync(attach(), refresh_ui=False)
    assert store.capture() == before and model.calls == calls


@pytest.mark.parametrize("family", ["4", "6"])
def test_limit_accept_before_inactive_interface_fence_cannot_verify(family):
    runtime = permitted_runtime()
    plan = {"interfaces": ["wg0"], "endpoints": [], "blocked_interfaces": ["manual1"]}
    for af, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-")):
        runtime[af] += [
            f"-A {prefix}input -i manual1 -j DROP",
            f"-A {prefix}output -o manual1 -j DROP",
            f"-A {prefix}output -o manual1 -p udp --dport 53 -j {prefix}limit-accept",
        ]
    assert snapshot.runtime_matches_plan(runtime, plan)
    prefix = "ufw-user-" if family == "4" else "ufw6-user-"
    limit = runtime[family].pop()
    fence = f"-A {prefix}output -o manual1 -j DROP"
    runtime[family].insert(runtime[family].index(fence), limit)
    assert not snapshot.runtime_matches_plan(runtime, plan)


@pytest.mark.parametrize("family", ["4", "6"])
def test_fence_preflight_allows_missing_fence_but_rejects_late_existing_one(family):
    runtime = permitted_runtime()
    prefix = "ufw-user-" if family == "4" else "ufw6-user-"
    grant = f"-A {prefix}output -o manual1 -p tcp --dport 443 -j ACCEPT"
    fence = f"-A {prefix}output -o manual1 -j DROP"
    runtime[family].append(grant)
    assert snapshot.interface_fences_ordered(
        runtime, ["manual1"], require_present=False
    )
    assert not snapshot.interface_fences_ordered(
        runtime, ["manual1"], require_present=True
    )
    runtime[family].append(fence)
    assert not snapshot.interface_fences_ordered(
        runtime, ["manual1"], require_present=False
    )
    runtime[family].remove(fence)
    runtime[family].insert(runtime[family].index(grant), fence)
    assert snapshot.interface_fences_ordered(
        runtime, ["manual1"], require_present=False
    )


@pytest.mark.parametrize("family", ["4", "6"])
def test_logging_preflight_exception_does_not_relax_final_fence_order(family):
    runtime = permitted_runtime()
    for af, prefix in (("4", "ufw-user-"), ("6", "ufw6-user-")):
        runtime[af] += [
            f"-A {prefix}input -i manual1 -j DROP",
            f"-A {prefix}output -o manual1 -j DROP",
        ]
    prefix = "ufw-user-" if family == "4" else "ufw6-user-"
    grant = f"-A {prefix}output -o manual1 -p tcp --dport 443 -j ACCEPT"
    runtime[family].insert(-1, grant)
    fresh = {(family, "output", "manual1")}
    assert not snapshot.interface_fences_ordered(
        runtime, ["manual1"], require_present=False
    )
    assert snapshot.interface_fences_ordered(
        runtime, ["manual1"], require_present=False, fresh_fences=fresh
    )
    assert not snapshot.interface_fences_ordered(
        runtime, ["manual1"], require_present=True, fresh_fences=fresh
    )
    assert not snapshot.runtime_matches_plan(
        runtime,
        {"interfaces": ["wg0"], "endpoints": [], "blocked_interfaces": ["manual1"]},
    )
