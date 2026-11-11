"""DNS routing and repair behaviour; every external operation is simulated."""

import copy

import pytest

from netmon.services.dns_control_service import DNSControlService
from tools import netmon

UUID = "12345678-1234-5678-9012-123456789abc"
TARGET = ("eth0", "Wired")
PROPS = ("ipv4.ignore-auto-dns", "ipv6.ignore-auto-dns", "ipv4.dns", "ipv6.dns")


def status(
    *,
    global_dns="",
    ethernet="",
    eth_domain="",
    vpn_domain="~.",
    eth_default="yes",
    vpn_dns="10.2.0.1",
    vpn=True,
):
    text = f"Global\n    DNS Servers: {global_dns}\n"
    text += f"Link 2 (eth0)\n    Current Scopes: DNS\n    DefaultRoute setting: {eth_default}\n    DNS Servers: {ethernet}\n    DNS Domain: {eth_domain}\n"
    if vpn:
        text += f"Link 3 (wg0)\n    Current Scopes: DNS\n    DefaultRoute setting: no\n    DNS Servers: {vpn_dns}\n    DNS Domain: {vpn_domain}\n"
    return text


class FakeNetwork:
    def __init__(self, path):
        self.path = path
        self.text = status()
        self.status_code = 0
        self.profiles = {
            "Wired": {
                "uuid": UUID,
                "iface": "eth0",
                "kind": "802-3-ethernet",
                "props": dict(zip(PROPS, ("yes", "yes", "", ""))),
            }
        }
        self.commands = []
        self.fail = ""
        self.on_read = None
        self.correct_on_up = True

    @property
    def writes(self):
        return [cmd for cmd in self.commands if cmd[0] == "sudo"]

    def run(self, cmd, **_kwargs):
        self.commands.append(list(cmd))
        if cmd == ["resolvectl", "status"]:
            return self.status_code, self.text
        if cmd[:2] == ["nmcli", "-g"]:
            if cmd[2] == "GENERAL.CON-UUID":
                profile = next(
                    p for p in self.profiles.values() if p["iface"] == cmd[-1]
                )
                return 0, profile["uuid"] + "\n"
            assert cmd[3:6] == ["con", "show", "id"]
            profile = self.profiles[cmd[-1]]
            out = (
                "\n".join(
                    [
                        profile["uuid"],
                        profile["iface"],
                        profile["kind"],
                        *profile["props"].values(),
                    ]
                )
                + "\n"
            )
            if self.on_read:
                callback, self.on_read = self.on_read, None
                callback()
            return 0, out
        if cmd[:6] == ["sudo", "-n", "nmcli", "con", "mod", "uuid"]:
            if self.fail == "modify":
                return 1, "simulated modify failure"
            profile = next(p for p in self.profiles.values() if p["uuid"] == cmd[6])
            profile["props"].update(zip(cmd[7::2], cmd[8::2]))
            return 0, ""
        if cmd[:6] == ["sudo", "-n", "nmcli", "con", "up", "uuid"]:
            if self.fail == "up":
                return 1, "simulated activation failure"
            if self.correct_on_up:
                self.text = status()
            return 0, ""
        if cmd == ["sudo", "-n", "rm", "-f", str(self.path)]:
            if self.fail == "remove":
                return 1, "simulated remove failure"
            self.path.unlink(missing_ok=True)
            return 0, ""
        if cmd == ["sudo", "-n", "systemctl", "restart", "systemd-resolved"]:
            if self.fail == "restart":
                return 1, "simulated restart failure"
            self.text = status()
            return 0, ""
        raise AssertionError(f"Unexpected external operation: {cmd}")


@pytest.fixture
def network(tmp_path):
    fake = FakeNetwork(tmp_path / "netmon.conf")
    service = DNSControlService(
        fake.run,
        lambda cmd: cmd == "nmcli",
        dot_dropin_path=str(fake.path),
        dot_dropin_dir=str(tmp_path),
    )
    service.get_wireguard_interfaces = lambda: {
        name for name in ("wg0", "wg1") if f"({name})" in fake.text
    }
    return fake, service


class Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def make_app(service):
    app = netmon.App.__new__(netmon.App)
    app._dns_control_service = lambda: service
    app.dns_guard_enabled_var = Var(True)
    app.dns_guard_status_var = Var()
    app.dns_guard_last_action_var = Var()
    app.dns_guard_transition_until = 0
    app.last_dns_guard_repair_ts = 0
    app.dns_guard_check_running = False
    app.logs = []
    app.errors = []
    app.log_safe = app.logs.append
    app.log_debug_safe = app.errors.append
    app.update_dns_guard_indicator = lambda: None
    app.update_dns_output = lambda text, append=False: app.logs.append(text)
    app._auto_dns_control_available = lambda: True
    app._active_nm_dns_targets = lambda: [TARGET]
    app.get_selected_user_dns = lambda: ["1.1.1.1"]
    app.get_selected_dot_dns = lambda: ["9.9.9.9"]
    return app


@pytest.mark.parametrize("global_dns", ["", "1.1.1.1", "2606:4700:4700::1111"])
def test_vpn_root_route_shadows_global_and_does_not_repair(
    network, monkeypatch, global_dns
):
    fake, service = network
    fake.text = status(global_dns=global_dns)
    app = make_app(service)
    for now in [1000, 1005, 1035, 1070]:
        monkeypatch.setattr(netmon.time, "time", lambda: now)
        app.run_dns_guard_check_once(auto_repair=True)
    assert app.dns_guard_state == "ok"
    assert not app.errors
    assert fake.writes == []
    report = service.evaluate_dns_snapshot(service.read_dns_snapshot())
    assert not report["conflict"] and not report["leak"]
    assert report["risk"] == "niedrig"
    assert report["configured_global_dns"] == ([global_dns] if global_dns else [])


@pytest.mark.parametrize("eth_default", ["yes", "no"])
def test_noncompeting_split_dns_preserved(network, eth_default):
    fake, service = network
    fake.text = status(
        ethernet="192.168.1.1", eth_domain="~lan.example", eth_default=eth_default
    )
    report = service.evaluate_dns_snapshot(service.read_dns_snapshot())
    assert report["split_ifaces"] == ["eth0"]
    assert not report["conflict"]
    assert service.apply_vpn_dns_policy(targets=[TARGET])[0]
    assert fake.writes == []


def test_split_only_vpn_does_not_hide_default_dns_sources(network):
    fake, service = network
    fake.text = status(
        global_dns="1.1.1.1", ethernet="192.168.1.1", vpn_domain="~corp.example"
    )
    assert service.evaluate_dns_snapshot(service.read_dns_snapshot())["conflict"]
    fake.text = status(
        ethernet="192.168.1.1", eth_domain="~corp.example", vpn_domain="~corp.example"
    )
    assert service.evaluate_dns_snapshot(service.read_dns_snapshot())["conflict"]


@pytest.mark.parametrize(
    "eth_domain,vpn_domain",
    [("~.", "~."), (".", "~."), ("~corp.example", "corp.example"), ("", "")],
)
def test_real_competing_route_is_detected(network, eth_domain, vpn_domain):
    fake, service = network
    fake.text = status(ethernet="1.1.1.1", eth_domain=eth_domain, vpn_domain=vpn_domain)
    report = service.evaluate_dns_snapshot(service.read_dns_snapshot())
    assert report["conflict"] and report["leak"]
    assert report["repair_ifaces"] == ["eth0"]


def test_multiple_vpn_links_ipv6_and_route_continuations(network):
    fake, service = network
    fake.text = status(
        vpn_dns="2001:0db8:0000::1", vpn_domain="~.\n                 ~corp.example"
    )
    fake.text += "Link 4 (wg1)\n    DNS Servers: 10.3.0.1\n    DNS Domain: ~other.example\n    Protocols: -DefaultRoute\n"
    snap = service.read_dns_snapshot()
    assert snap["links"][1]["domains"] == ["~.", "~corp.example"]
    assert service.vpn_dns_routing(snap)["vpn_dns"] == ["10.3.0.1", "2001:db8::1"]
    app = make_app(service)
    assert app.rebuild_dns_guard_whitelist(snap) == ["10.3.0.1", "2001:db8::1"]
    assert app.dns_is_clean(["2001:0db8:0:0::1"], ["2001:db8::1"])
    assert not app.dns_is_clean(["fe80::1%eth0"], ["fe80::1%wg0"])


@pytest.mark.parametrize(
    "text,rc", [("", 1), ("Global\nDNS Servers: 1.1.1.1", 1), ("not a status", 0)]
)
def test_unknown_status_cannot_repair_or_signal_disconnect(network, text, rc):
    fake, service = network
    fake.text, fake.status_code = text, rc
    app = make_app(service)
    app.run_dns_guard_check_once(auto_repair=True)
    assert app.dns_guard_state == "unknown"
    assert app.is_vpn_active() is None
    assert app.is_vpn_active_for_dns_ui()
    assert not app.enforce_dns_clean()[0]
    assert not service.apply_vpn_dns_policy(targets=[TARGET])[0]
    assert not fake.writes and not app.errors
    callbacks = []
    app.last_vpn_state = True
    app.get_vpn_state = lambda: None
    app.on_vpn_state_changed = lambda value: callbacks.append(value)
    app.after = lambda *args: callbacks.append(args[0])
    app.monitor_vpn_changes()
    assert app.last_vpn_state is True
    assert callbacks == [3000]


def test_missing_vpn_dns_is_unknown(network):
    fake, service = network
    fake.text = status(vpn_dns="", ethernet="1.1.1.1")
    app = make_app(service)
    app.run_dns_guard_check_once(auto_repair=True)
    assert app.dns_guard_state == "unknown"
    assert fake.writes == []


def dirty_profile(fake):
    fake.text = status(ethernet="1.1.1.1", eth_domain="~.")
    fake.profiles["Wired"]["props"].update(
        dict(zip(PROPS, ("no", "no", "1.1.1.1", "")))
    )


def test_repair_changes_only_differences_and_uses_uuid(network):
    fake, service = network
    dirty_profile(fake)
    ok, text = service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert ok and "nachgeprüft" in text and "automatische Prüfung" in text
    assert fake.writes == [
        [
            "sudo",
            "-n",
            "nmcli",
            "con",
            "mod",
            "uuid",
            UUID,
            "ipv4.ignore-auto-dns",
            "yes",
            "ipv6.ignore-auto-dns",
            "yes",
            "ipv4.dns",
            "",
        ],
        ["sudo", "-n", "nmcli", "con", "up", "uuid", UUID],
    ]
    assert service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert len(fake.writes) == 2


def test_correct_ethernet_never_reactivated_even_if_runtime_wrong(network):
    fake, service = network
    fake.text = status(ethernet="1.1.1.1", eth_domain="~.")
    for _ in range(3):
        assert not service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert not fake.writes


def test_ineffective_repair_is_suppressed_until_actual_state_changes(
    network, monkeypatch
):
    fake, service = network
    dirty_profile(fake)
    fake.correct_on_up = False
    app = make_app(service)
    for now in [1000, 1005, 1035, 1070]:
        monkeypatch.setattr(netmon.time, "time", lambda: now)
        app.run_dns_guard_check_once(auto_repair=True)
    assert len(fake.writes) == 2
    assert app.dns_guard_state == "problem" and not app.errors
    assert any("Wiederholung unterdrückt" in text for text in app.logs)
    # A healthy observation ends the unresolved episode; a real new violation
    # can be repaired again, rather than disabled by a permanent circuit breaker.
    fake.text = status()
    app.run_dns_guard_check_once(auto_repair=True)
    dirty_profile(fake)
    fake.correct_on_up = True
    monkeypatch.setattr(netmon.time, "time", lambda: 1110)
    app.run_dns_guard_check_once(auto_repair=True)
    assert len(fake.writes) == 4 and app.dns_guard_state == "ok"


@pytest.mark.parametrize("failure,write_count", [("modify", 1), ("up", 2)])
def test_partial_failure_stops_further_changes_and_auto_repetition(
    network, failure, write_count
):
    fake, service = network
    dirty_profile(fake)
    fake.path.write_text("[Resolve]\nDNS=1.1.1.1\nDomains=~.\n")
    fake.fail = failure
    ok, text = service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert not ok and "Teiländerungen" in text
    assert len(fake.writes) == write_count and fake.path.exists()
    assert not service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert len(fake.writes) == write_count
    # Explicit user retry bypasses the automatic backoff.
    fake.fail = ""
    ok, text = service.apply_vpn_dns_policy(targets=[TARGET])
    assert ok and "ausdrückliche Benutzeraktion" in text


def test_no_restart_without_actual_dropin_change(network):
    fake, service = network
    assert service.apply_vpn_dns_policy(targets=[TARGET])[0]
    assert fake.writes == []
    fake.path.write_text("[Resolve]\nDNS=1.1.1.1\nDomains=~.\n")
    assert service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert fake.writes == [
        ["sudo", "-n", "rm", "-f", str(fake.path)],
        ["sudo", "-n", "systemctl", "restart", "systemd-resolved"],
    ]


@pytest.mark.parametrize("failure", ["remove", "restart"])
def test_dropin_failure_pending_restart_and_explicit_retry(network, failure):
    fake, service = network
    fake.path.write_text("DNS=1.1.1.1\nDomains=~.\n")
    fake.fail = failure
    assert not service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert service._resolved_reload_pending is (failure == "restart")
    count = len(fake.writes)
    service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert len(fake.writes) == count
    fake.fail = ""
    assert service.apply_vpn_dns_policy(targets=[TARGET])[0]
    assert not service._resolved_reload_pending


def test_snapshot_changed_while_planning_aborts_without_write(network):
    fake, service = network
    dirty_profile(fake)
    fake.on_read = lambda: setattr(fake, "text", status(vpn=False))
    assert not service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert not fake.writes


@pytest.mark.parametrize(
    "field,value", [("uuid", "profile-name"), ("iface", "wg0"), ("kind", "vpn")]
)
def test_invalid_profile_aborts_before_any_write(network, field, value):
    fake, service = network
    dirty_profile(fake)
    fake.profiles["Wired"][field] = value
    assert not service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert not fake.writes


def test_all_profiles_validated_before_first_mutation(network):
    fake, service = network
    dirty_profile(fake)
    fake.profiles["Wifi"] = copy.deepcopy(fake.profiles["Wired"])
    fake.profiles["Wifi"].update(uuid="broken", iface="wlan0")
    assert not service.apply_vpn_dns_policy(targets=[TARGET, ("wlan0", "Wifi")])[0]
    assert not fake.writes


def test_overlapping_repair_returns_without_commands(network):
    fake, service = network
    with service._vpn_repair_lock:
        ok, text = service.apply_vpn_dns_policy(targets=[TARGET])
    assert not ok and "läuft bereits" in text and fake.commands == []


def test_passive_check_does_not_mutate_and_no_auth_cannot_repair(network):
    fake, service = network
    dirty_profile(fake)
    app = make_app(service)
    app.run_dns_guard_check_once(auto_repair=False)
    assert app.dns_guard_state == "problem" and not fake.writes
    app._auto_dns_control_available = lambda: False
    app.run_dns_guard_check_once(auto_repair=True)
    assert not fake.writes and not app.errors


def test_inactive_vpn_and_manual_ipv6_equivalence(network):
    fake, service = network
    fake.text = status(vpn=False, ethernet="2001:0db8:0:0::1")
    app = make_app(service)
    app.get_selected_user_dns = lambda: ["2001:db8::1"]
    app.run_dns_guard_check_once(auto_repair=True)
    assert app.dns_guard_state == "ok" and not fake.writes and not app.errors


@pytest.mark.parametrize("rc", [1, 127])
def test_wireguard_inventory_failure_is_not_confirmed_disconnect(tmp_path, rc):
    def run(cmd, **kwargs):
        if cmd == ["resolvectl", "status"]:
            return 0, status(vpn=False)
        assert cmd in (
            ["wg", "show", "interfaces"],
            ["ip", "-o", "link", "show", "type", "wireguard"],
        )
        return rc, "query failed"

    service = DNSControlService(
        run,
        lambda cmd: True,
        dot_dropin_path=str(tmp_path / "absent"),
        dot_dropin_dir=str(tmp_path),
    )
    assert service.read_dns_snapshot()["vpn_state"] == "unknown"


@pytest.mark.parametrize("choice", ["System (DHCP/auto)", "Cloudflare"])
def test_nm_failure_stops_manual_and_restore_followup(choice):
    app = netmon.App.__new__(netmon.App)
    app._apply_nm_dns_policy_to_targets = lambda **kwargs: (
        False,
        ["simulated NM error"],
    )
    app._read_dot_dropin = lambda: pytest.fail(
        "No further config access after NM failure"
    )
    app._write_manual_dns_dropin = lambda *args: pytest.fail(
        "No further write after NM failure"
    )
    app._remove_manual_dns_dropin = lambda: pytest.fail("No removal after NM failure")
    app._restart_resolved_for_dns_policy = lambda: pytest.fail(
        "No restart after NM failure"
    )
    result = netmon.dns_controller.apply_dns_profile_choice_via_control(app, choice)
    assert not result["success"] and "nicht ausgeführt" in result["restart_detail"]


def test_unknown_vpn_blocks_explicit_user_dns(network):
    _fake, service = network
    app = make_app(service)
    app.is_vpn_active = lambda: None
    app._manual_dns_choice = lambda: pytest.fail("Unknown status must not apply DNS")
    assert not netmon.dns_controller.use_user_dns(app)[0]


def test_status_refresh_before_dns_tab_exists(network):
    fake, service = network
    app = make_app(service)
    del app.dns_guard_status_var
    del app.dns_guard_last_action_var
    app.run_dns_guard_check_once()
    assert app.dns_guard_state == "ok" and not app.errors
    assert not fake.writes


def test_explicit_retry_finishes_failed_activation_without_rewriting(network):
    fake, service = network
    dirty_profile(fake)
    fake.fail = "up"
    assert not service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert len(fake.writes) == 2
    assert not service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert len(fake.writes) == 2
    fake.fail = ""
    assert service.apply_vpn_dns_policy(targets=[TARGET])[0]
    assert fake.writes[-1] == ["sudo", "-n", "nmcli", "con", "up", "uuid", UUID]
    assert len(fake.writes) == 3
    assert not service._nm_activation_pending


def test_unknown_vpn_is_visible_in_status_and_leak_report(network):
    fake, service = network
    fake.text, fake.status_code = "query failed", 1
    app = make_app(service)
    app.vpn_status_text_var = Var()
    app.public_ip = "-"
    app.country = "-"
    app.update_vpn_status_text()
    assert "unbekannt" in app.vpn_status_text_var.get()
    assert "VPN: aus" not in app.vpn_status_text_var.get()
    report = service.build_dns_leak_check_result(
        resolvectl_output="", dns_servers=[], public_ip="-"
    )
    assert "status unknown" in report and "VPN not active" not in report
    assert "Leak detected: unknown" in report
