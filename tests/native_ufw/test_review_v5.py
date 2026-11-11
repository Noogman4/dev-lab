"""Fourth review: actual App, real profile files and persistent ACK checks."""

from test_review_regressions import native_application
from support import PLAN, fresh_system, reboot, store, ufw_cli
from netmon.app import App
import netmon.app as app_module
from netmon.features import firewall_controller as fc, vpn_controller as vc
from netmon.core.ufw_snapshot import SnapshotError
from pathlib import Path
import json
import pytest

PROFILE = """[Interface]
Address=10.2.0.2/32
PrivateKey=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
[Peer]
PublicKey=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=
AllowedIPs=0.0.0.0/0
Endpoint={endpoint}
"""


@pytest.fixture
def system(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    directory = Path("/etc/wireguard")
    directory.mkdir(exist_ok=True)
    for path in directory.glob("*.conf"):
        path.unlink()  # Disposable private /etc, never a host path.
    assert fresh_system()[0] == 0
    assert reboot().returncode == 0
    return store()


def profile(name, endpoint="198.51.100.10:51820"):
    path = Path("/etc/wireguard") / (name + ".conf")
    path.write_text(PROFILE.format(endpoint=endpoint))
    path.chmod(0o600)
    return path


class Environment:
    def __init__(self):
        self.live = {"wg0"}
        self.ipv6_disabled = False

    def command(self, args, **_kwargs):
        args = list(args)
        if args[:2] == ["sudo", "-n"]:
            args = args[2:]
        if args[:1] == ["sysctl"]:
            return 0, str(int(self.ipv6_disabled))
        if args[:1] == ["cat"] and len(args) == 2:
            path = Path(args[1])
            assert str(path).startswith(("/etc/wireguard/", "/work/"))
            return (0, path.read_text()) if path.is_file() else (1, "")
        if args[:2] == ["test", "-f"]:
            return (0, "") if Path(args[2]).is_file() else (1, "")
        if args[:1] == ["find"]:
            assert args[1] == "/etc/wireguard"
            return 0, "\n".join(
                p.name for p in sorted(Path("/etc/wireguard").glob("*.conf"))
            )
        if args[:1] == ["nmcli"]:
            return 0, ""  # No NetworkManager connections in this fixture.
        pytest.fail("Unexpected environment command: " + args[0])


def real_app(system, monkeypatch, slots=("wg0",)):
    env = Environment()
    monkeypatch.setattr(vc, "run_cmd", env.command)
    monkeypatch.setattr(app_module, "run_cmd", env.command)
    monkeypatch.setattr(
        fc.nm_ownership, "verified_interface", lambda name: name in env.live
    )
    fake, logs = native_application(system)
    app = App.__new__(App)  # No Tk constructor/window, actual App descriptors.
    app.__dict__.update(
        tk=None,
        logs=logs,
        ufw_lock=fake.ufw_lock,
        vpn_slots=[{"profile": n} for n in slots],
        primary_vpn_slots=[],
        killswitch_journal=fake.killswitch_journal,
        firewall_snapshots=fake.firewall_snapshots,
        get_wg_interfaces=lambda: sorted(env.live),
        log_safe=logs.append,
        log=logs.append,
        log_debug=lambda *_a: None,
        log_debug_safe=lambda *_a: None,
        log_network_debug=lambda *_a: None,
        tr=lambda key, default=None, **_k: default if default is not None else key,
        refresh_safe=lambda: None,
        run_async=lambda fn, **_k: fn(),
        _confirm_danger_action=lambda *_a, **_k: True,
        _try_begin_network_operation=lambda *_a, **_k: True,
        _end_network_operation=lambda *_a, **_k: None,
        ensure_sudo_session=lambda *_a, **_k: True,
    )

    def run(args, **kwargs):
        assert args[:3] == ["sudo", "-n", "ufw"] and args[3] == "status"
        return system.backend.command(args[3:])

    app.run_cmd = run
    # Name formation, file existence, listing, IPv6 checks, resolver and all
    # collectors remain actual App methods; only external I/O/UI is replaced.
    for name in (
        "_internal_ipv4_profile_name",
        "_wg_profile_exists",
        "list_wg_profiles",
        "ipv6_is_disabled",
        "resolve_profile_family_runtime",
    ):
        assert name not in app.__dict__
    return app, env, logs


def change_kernel(callback):
    for family, prefix in (("4", "ufw-"), ("6", "ufw6-")):
        path = Path(f"/work/kernel/{family}.json")
        state = json.loads(path.read_text())
        callback(state, prefix)
        path.write_text(json.dumps(state))


@pytest.mark.parametrize("family", ["4", "6", "both"])
def test_ack_refuses_runtime_policy_repair_with_persistent_drop_then_boot(
    system, monkeypatch, family
):
    profile("wg0")
    app, _env, _logs = real_app(system, monkeypatch)
    assert fc.killswitch_on_sync(app, refresh_ui=False)
    record = system.load()
    for af in ("4", "6"):
        if family not in (af, "both"):
            continue
        path = Path(f"/work/kernel/{af}.json")
        state = json.loads(path.read_text())
        state["pol"]["OUTPUT"] = "ACCEPT"
        path.write_text(json.dumps(state))
    current = system.capture()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert system.capture() == current
    assert not list(system.registry.glob("reviewed-*.json"))
    assert reboot().returncode == 0
    assert system.load()["phase"] == "active"
    assert system.state()["state"] == "on"
    assert system.load()["original"] == record["original"]
    assert fc.killswitch_off_sync(app, refresh_ui=False)
    assert system.capture() == record["original"]


@pytest.mark.parametrize("family", ["4", "6", "both"])
def test_ack_refuses_kernel_only_fence_removal_persistent_user_rules_remain(
    system, monkeypatch, family
):
    for name in ("wg0", "wg1"):
        profile(name)
    assert ufw_cli(["allow", "out", "on", "wg1"])[0] == 0
    app, _env, _logs = real_app(system, monkeypatch, slots=("wg0", "wg1"))
    assert fc.killswitch_on_sync(app, refresh_ui=False)
    assert ufw_cli(["default", "allow", "outgoing"])[0] == 0

    def remove(state, prefix):
        af = "6" if prefix == "ufw6-" else "4"
        if family not in (af, "both"):
            return
        for chain in ("input", "output"):
            key = prefix + "user-" + chain
            state["chains"][key] = [
                r
                for r in state["chains"][key]
                if not ("wg1" in r and r.endswith("-j DROP"))
            ]

    change_kernel(remove)
    record = system.load()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert reboot().returncode == 0
    assert any(
        "wg1 -j DROP" in r
        for rows in system.capture()["runtime"].values()
        for r in rows
    )
    assert not list(system.registry.glob("reviewed-*.json"))


@pytest.mark.parametrize("name", ["proton-germany-042", "-odd"])
def test_valid_profile_file_with_invalid_interface_name_cannot_break_on(
    system, monkeypatch, name
):
    profile("wg0")
    profile(name)
    app, _env, logs = real_app(system, monkeypatch, slots=("wg0", name))
    assert app._wg_profile_exists(name)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    plan = system.load()["plan"]
    assert name not in plan["interfaces"] + plan.get("blocked_interfaces", [])
    assert any(name in line and "Interface" in line for line in logs)
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_normal_manual_profile_without_slot_can_be_fenced_then_restored(
    system, monkeypatch
):
    profile("wg0")
    profile("manual1")
    assert ufw_cli(["allow", "out", "on", "manual1"])[0] == 0
    app, _env, logs = real_app(system, monkeypatch, slots=("wg0",))
    assert "manual1" in app.list_wg_profiles()
    assert "manual1" not in app._collect_referenced_vpn_profiles()
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert "manual1" in system.load()["plan"]["blocked_interfaces"]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_fully_active_killswitch_with_original_deny_policy_cannot_be_retired(
    system, monkeypatch
):
    profile("wg0")
    assert ufw_cli(["default", "deny", "outgoing"])[0] == 0
    assert reboot().returncode == 0
    app, _env, logs = real_app(system, monkeypatch)
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on"
    record = system.load()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert "Legacy" not in str(exc.value)
    assert system.load() == record
    assert fc.killswitch_off_sync(app, refresh_ui=False)


def test_inventory_cannot_create_missing_ipv4_profile(system, monkeypatch):
    profile("wg0")
    app, env, logs = real_app(system, monkeypatch)
    env.ipv6_disabled = True
    assert app.ipv6_is_disabled()
    calls = []

    def forbidden(*_a, **_k):
        calls.append("ensure_internal_ipv4_profile")
        raise AssertionError("Read-only inventory attempted profile creation")

    monkeypatch.setattr(app, "ensure_internal_ipv4_profile", forbidden)
    before = {p.name: p.read_bytes() for p in Path("/etc/wireguard").glob("*.conf")}
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert not calls
    assert {
        p.name: p.read_bytes() for p in Path("/etc/wireguard").glob("*.conf")
    } == before
    assert fc.killswitch_off_sync(app, refresh_ui=False)


def test_hostname_notice_cannot_open_modal_on_activation_or_resync(system, monkeypatch):
    profile("wg0")
    profile("wg1", "vpn.example.org:51820")
    app, _env, logs = real_app(system, monkeypatch, slots=("wg0", "wg1"))
    calls = []
    monkeypatch.setattr(
        fc.messagebox, "showwarning", lambda *_a, **_k: calls.append(True)
    )
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert not calls
    assert (
        sum("Einige WireGuard-Profile nutzen Hostnamen" in line for line in logs) == 1
    )
    assert fc.killswitch_off_sync(app, refresh_ui=False)


@pytest.mark.parametrize("failed_commit", [False, True])
def test_ack_cannot_retire_partial_file_policy_without_loopback_rules(
    system, failed_commit
):
    token = system.begin(PLAN)["token"]
    markers = [
        Path("/work/kernel/fail-" + name)
        for name in ("iptables-restore", "ip6tables-restore")
    ]
    if failed_commit:
        for p in markers:
            p.touch()
    result = system.command(token, ["default", "deny", "outgoing"])
    for p in markers:
        if p.exists():
            p.unlink()
    assert result["rc"] == (1 if failed_commit else 0)
    if not failed_commit:
        change_kernel(
            lambda state, _prefix: state["pol"].__setitem__("OUTPUT", "ACCEPT")
        )
    record, current = system.load(), system.capture()
    assert (
        not system.backend.legacy_block_present()
    )  # No lo: policy-file check is essential.
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert system.capture() == current
    assert reboot().returncode == 0
    assert store().restore()["state"] == "off"
    assert store().capture() == record["original"]


def test_slot_change_keeps_old_available_profile_fenced_even_after_off_on(
    system, monkeypatch
):
    profile("wg0")
    profile("wg2")
    assert ufw_cli(["allow", "out", "on", "wg0"])[0] == 0
    app, env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    env.live = {"wg2"}
    app.vpn_slots = [{"profile": "wg2"}]
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert "wg0" in system.load()["plan"]["blocked_interfaces"]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert "wg0" in system.load()["plan"]["blocked_interfaces"]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_large_unused_catalog_does_not_create_redundant_fences_or_exceed_plan_limit(
    system, monkeypatch
):
    for name in ["wg0", "manual1"] + [f"p{i:03}" for i in range(100)]:
        profile(name)
    assert ufw_cli(["allow", "out", "on", "manual1"])[0] == 0
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert len(app.list_wg_profiles()) > 64
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.load()["plan"]["blocked_interfaces"] == ["manual1"]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("family", ["4", "6", "both"])
def test_ack_counts_persistent_drop_without_tuple_or_live_kernel_rule(system, family):
    system.begin(PLAN)
    original = system.load()["original"]
    for af, filename, prefix in (
        ("4", "user.rules", "ufw-"),
        ("6", "user6.rules", "ufw6-"),
    ):
        if family not in (af, "both"):
            continue
        path = Path("/etc/ufw") / filename
        text = path.read_text().replace(
            "### END RULES ###", f"-A {prefix}user-output -j DROP\n### END RULES ###"
        )
        path.write_text(text)
    assert system.capture()["runtime"] == original["runtime"]
    record = system.load()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert not list(system.registry.glob("reviewed-*.json"))
    assert reboot().returncode == 0
    assert any(
        "-user-output -j DROP" in r
        for rows in system.capture()["runtime"].values()
        for r in rows
    )
    assert system.load()["original"] == original


def test_ack_cannot_retire_interface_deny_tuples_after_lines_and_kernel_rules_removed(
    system,
):
    system.begin(PLAN)
    for direction in ("in", "out"):
        assert ufw_cli(["deny", direction, "on", "future1"])[0] == 0
    for name in ("user.rules", "user6.rules"):
        path = Path("/etc/ufw") / name
        path.write_text(
            "\n".join(
                row
                for row in path.read_text().splitlines()
                if not (
                    row.startswith("-A ")
                    and "future1" in row
                    and row.endswith("-j DROP")
                )
            )
            + "\n"
        )
        assert "### tuple ### deny" in path.read_text()

    def remove(state, prefix):
        for chain in ("input", "output"):
            key = prefix + "user-" + chain
            state["chains"][key] = [
                r
                for r in state["chains"][key]
                if not ("future1" in r and r.endswith("-j DROP"))
            ]

    change_kernel(remove)
    record = system.load()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert not list(system.registry.glob("reviewed-*.json"))
