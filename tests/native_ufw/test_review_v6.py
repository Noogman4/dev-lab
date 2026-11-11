"""Fifth review: endpoints, logged tuple metadata and literal policy grammar."""

from pathlib import Path
import pytest

from test_review_v5 import system as system, real_app, profile, change_kernel
from support import PLAN, reboot, ufw_cli
from netmon.core.ufw_snapshot import SnapshotError
from netmon.features import firewall_controller as fc


@pytest.mark.parametrize(
    "endpoint",
    [
        "198.51.100.53:51820",
        "53.1.2.3:51820",
        "198.53.1.2:51820",
        "[2001:db8::53]:51820",
        "198.51.100.10:53",
        "[2001:db8::53]:53",
        "198.51.100.54:51820",
        "198.51.100.153:51820",
        "198.51.100.80:443",
    ],
)
def test_selected_endpoint_is_not_a_global_dns_exception(system, monkeypatch, endpoint):
    profile("wg0", endpoint)
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.state()["state"] == "on"
    assert reboot().returncode == 0
    assert system.state()["state"] == "on"
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("stage", ["before_on", "during_on"])
def test_unused_endpoint_with_53_cannot_break_on_or_live_resync(
    system, monkeypatch, stage
):
    profile("wg0")
    if stage == "before_on":
        profile("unused1", "198.51.100.53:51820")
    app, env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    if stage == "during_on":
        profile("unused1", "198.51.100.53:51820")
        assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert env.live == {"wg0"}
    assert system.load()["plan"]["endpoints"] == [["198.51.100.10", "51820"]]
    assert system.state()["state"] == "on"
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("existing_manual_endpoint", [False, True])
def test_distinct_unused_endpoints_do_not_fill_the_plan(
    system, monkeypatch, existing_manual_endpoint
):
    profile("wg0")
    for i in range(130):
        profile(f"p{i:03}", f"203.0.113.{i + 1}:51820")
    expected = [["198.51.100.10", "51820"]]
    if existing_manual_endpoint:
        profile("manual1", "203.0.114.77:51820")
        assert ufw_cli(["allow", "out", "on", "manual1"])[0] == 0
        assert (
            ufw_cli(
                ["allow", "out", "to", "203.0.114.77", "port", "51820", "proto", "udp"]
            )[0]
            == 0
        )
        expected.append(["203.0.114.77", "51820"])
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert len(app.list_wg_profiles()) > 128
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.load()["plan"]["endpoints"] == expected
    if existing_manual_endpoint:
        assert system.load()["plan"]["blocked_interfaces"] == ["manual1"]
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


def test_distinct_slot_endpoints_and_existing_old_grant_survive_resync(
    system, monkeypatch
):
    profile("wg0")
    profile("wg2", "203.0.113.22:51820")
    assert (
        ufw_cli(
            ["allow", "out", "to", "198.51.100.10", "port", "51820", "proto", "udp"]
        )[0]
        == 0
    )
    app, env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.load()["plan"]["endpoints"] == [["198.51.100.10", "51820"]]
    app.vpn_slots = [{"profile": "wg2"}]
    env.live = {"wg2"}
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.load()["plan"]["endpoints"] == [
        ["198.51.100.10", "51820"],
        ["203.0.113.22", "51820"],
    ]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert system.load()["plan"]["endpoints"] == [
        ["198.51.100.10", "51820"],
        ["203.0.113.22", "51820"],
    ]
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize(
    "action,logging,family",
    [
        ("deny", "log", "4"),
        ("deny", "log", "6"),
        ("deny", "log", "both"),
        ("deny", "log-all", "both"),
        ("reject", "log", "both"),
        ("reject", "log-all", "both"),
    ],
)
def test_logged_tuple_only_block_prevents_ack_and_can_regenerate(
    system, action, logging, family
):
    system.begin(PLAN)
    assert ufw_cli([action, "out", "on", "future1", logging])[0] == 0
    for af, filename in (("4", "user.rules"), ("6", "user6.rules")):
        path = Path("/etc/ufw") / filename
        rows = path.read_text().splitlines()
        rows = [
            row
            for row in rows
            if not (row.startswith("-A ") and "future1" in row)
            and not (
                family not in (af, "both")
                and row.startswith("### tuple ###")
                and "future1" in row
            )
        ]
        path.write_text("\n".join(rows) + "\n")
        if family in (af, "both"):
            assert f"### tuple ### {action}_{logging}" in path.read_text()

    def remove(state, _prefix):
        for chain in state["chains"]:
            state["chains"][chain] = [
                row for row in state["chains"][chain] if "future1" not in row
            ]

    change_kernel(remove)
    record, current = system.load(), system.capture()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert system.capture() == current
    assert not list(system.registry.glob("reviewed-*.json"))
    assert ufw_cli(["allow", "1234/tcp"])[0] == 0
    assert reboot().returncode == 0
    for af in ("4", "6"):
        returned = any("future1" in row for row in system.capture()["runtime"][af])
        assert returned == (family in (af, "both"))
    assert system.load()["original"] == record["original"]


def test_shell_comment_boundary_divergence_cannot_retire_rollback(system):
    system.begin(PLAN)
    path = Path("/etc/default/ufw")
    with path.open("a") as handle:
        handle.write("X=1#;DEFAULT_OUTPUT_POLICY=DROP\n")
    record, current = system.load(), system.capture()
    with pytest.raises(SnapshotError) as exc:
        system.acknowledge()
    assert exc.value.code == "pending"
    assert system.load() == record
    assert system.capture() == current
    assert not list(system.registry.glob("reviewed-*.json"))
    assert reboot().returncode == 0
    assert all(
        any(row.startswith(":OUTPUT DROP ") for row in rows)
        for rows in system.capture()["runtime"].values()
    )
    assert system.load()["original"] == record["original"]


def test_real_global_dns_grant_is_still_detected_and_on_is_nonmutating(
    system, monkeypatch
):
    profile("wg0", "198.51.100.10:53")
    assert ufw_cli(["allow", "out", "53/udp"])[0] == 0
    status = system.backend.command(["status", "verbose"])[1]
    assert fc.ufw_has_outgoing_port_rule(status, "53", "udp")
    app, _env, _logs = real_app(system, monkeypatch)
    before = system.capture()
    assert not fc.killswitch_on_sync(app, refresh_ui=False)
    assert system.capture() == before


def test_existing_input_and_forward_exceptions_are_preserved(system, monkeypatch):
    profile("wg0")
    assert ufw_cli(["allow", "in", "on", "unknown0"])[0] == 0
    assert (
        ufw_cli(["route", "allow", "in", "on", "manual1", "out", "on", "eth0"])[0] == 0
    )
    app, _env, logs = real_app(system, monkeypatch)
    before = system.capture()
    assert fc.killswitch_on_sync(app, refresh_ui=False), logs
    assert reboot().returncode == 0
    for af in ("4", "6"):
        current = system.capture()["runtime"][af]
        for row in before["runtime"][af]:
            if row.startswith("-A ") and ("unknown0" in row or "manual1" in row):
                assert row in current
    assert fc.killswitch_off_sync(app, refresh_ui=False), logs
    assert system.capture() == before


@pytest.mark.parametrize("action", ["deny", "reject"])
def test_original_logged_block_is_preserved_during_legitimate_ack(system, action):
    import json

    assert ufw_cli([action, "out", "on", "future1", "log-all"])[0] == 0
    system.begin(PLAN)
    original = system.load()["original"]
    assert ufw_cli(["allow", "22/tcp"])[0] == 0
    current = system.capture()
    assert system.acknowledge()["state"] == "reviewed"
    assert system.capture() == current
    archives = list(system.registry.glob("reviewed-*.json"))
    assert len(archives) == 1
    assert archives[0].stat().st_mode & 0o777 == 0o600
    assert json.loads(archives[0].read_text())["original"] == original
