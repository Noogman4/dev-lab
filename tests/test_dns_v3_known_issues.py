"""Independent V3 challenge cases; all commands are local deterministic spies."""

import pytest

from netmon.services.dns_control_service import DNSControlService
from netmon.features.dns_controller import apply_dns_profile_choice_via_control
from tools import netmon

UUID = "12345678-1234-5678-9012-123456789abc"
TARGET = ("eth0", "Wired")
PROPS = ("ipv4.ignore-auto-dns", "ipv6.ignore-auto-dns", "ipv4.dns", "ipv6.dns")


def status(
    *,
    eth="192.168.0.1",
    eth_domain="~lan.example",
    eth_default="yes",
    vpn_dns="10.64.0.1",
    vpn_domain="~corp.example",
    vpn_default=True,
    global_dns="",
    global_domain="",
    extra="",
):
    vpn_route = "+DefaultRoute" if vpn_default else "-DefaultRoute"
    return (
        f"Global\n    DNS Servers: {global_dns}\n    DNS Domain: {global_domain}\n"
        f"Link 2 (eth0)\n    Current Scopes: DNS\n    DefaultRoute setting: {eth_default}\n"
        f"    DNS Servers: {eth}\n    DNS Domain: {eth_domain}\n"
        f"Link 3 (wg0)\n    Current Scopes: DNS\n    Protocols: {vpn_route}\n"
        f"    DNS Servers: {vpn_dns}\n    DNS Domain: {vpn_domain}\n" + extra
    )


class Model:
    def __init__(self, tmp_path):
        self.path = tmp_path / "netmon-dot.conf"
        self.text = status()
        self.inventory = {"wg0"}
        self.props = dict(zip(PROPS, ("no", "no", "8.8.8.8", "")))
        self.commands = []
        self.reads = 0
        self.flip_state_on_modify = None
        self.flip_modify = False
        self.flip_state_on_up = None
        self.flip_up = False
        self.vpn_state = False
        self.on_modify = None
        self.on_up = None
        self.service = DNSControlService(
            self.run,
            lambda cmd: cmd in {"nmcli", "wg", "resolvectl"},
            dot_dropin_path=str(self.path),
            dot_dropin_dir=str(tmp_path),
        )
        self.service.get_wireguard_interfaces = lambda: self.inventory

    def run(self, cmd, **_kwargs):
        cmd = list(cmd)
        self.commands.append(cmd)
        if cmd == ["resolvectl", "status"]:
            return 0, self.text
        if cmd == ["wg", "show", "interfaces"]:
            return 0, " ".join(self.inventory)
        if cmd[:2] == ["nmcli", "-g"]:
            if cmd[2] == "GENERAL.CON-UUID":
                return 0, UUID + "\n"
            self.reads += 1
            return (
                0,
                "\n".join([UUID, "eth0", "802-3-ethernet", *self.props.values()])
                + "\n",
            )
        if cmd[:5] == ["sudo", "-n", "nmcli", "con", "mod"]:
            offset = 7 if cmd[5] == "uuid" else 6
            self.props.update(zip(cmd[offset::2], cmd[offset + 1 :: 2]))
            if self.flip_modify:
                self.vpn_state = self.flip_state_on_modify
            if self.on_modify:
                self.on_modify()
            return 0, ""
        if cmd[:5] == ["sudo", "-n", "nmcli", "con", "up"]:
            if self.flip_up:
                self.vpn_state = self.flip_state_on_up
            self.text = status(eth="", eth_domain="", eth_default="no", vpn_domain="~.")
            if self.on_up:
                self.on_up()
            return 0, ""
        if cmd == ["sudo", "-n", "rm", "-f", str(self.path)]:
            self.path.unlink(missing_ok=True)
            return 0, ""
        if cmd == ["sudo", "-n", "systemctl", "restart", "systemd-resolved"]:
            return 0, ""
        raise AssertionError(cmd)

    @property
    def writes(self):
        return [c for c in self.commands if c and c[0] == "sudo"]


def fake_app(model):
    app = netmon.App.__new__(netmon.App)
    app._dns_control_service = lambda: model.service
    app.is_vpn_active = lambda: model.vpn_state
    app._dns_runtime_transition_active = lambda: False
    app._dns_servers_for_choice = lambda _choice: []
    app._apply_nm_dns_policy_to_targets = (
        lambda *, ignore_auto_dns: model.service.apply_nm_dns_policy_to_targets(
            ignore_auto_dns=ignore_auto_dns, targets=[TARGET]
        )
    )
    app._read_dot_dropin = lambda: model.path.read_text() if model.path.exists() else ""
    app._remove_manual_dns_dropin = model.service.remove_dropin
    app._write_manual_dns_dropin = lambda _choice: model.service.write_dropin(
        "DNS=9.9.9.9\n"
    )
    app._restart_resolved_for_dns_policy = model.service.restart_resolved
    app._restore_dot_dropin_backup = lambda _previous: (True, "")
    return app


def test_f1_unresolved_parallel_default_route_is_still_a_leak(tmp_path):
    model = Model(tmp_path)
    policy = model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())
    assert policy["conflict"] and "eth0" in policy["repair_ifaces"]
    assert "eth0" in policy["split_ifaces"]
    ok, message = model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert not ok and "ungeklärt" in message
    assert model.writes == []
    # For a name matching neither specific route, both links retain default DNS.
    # This is the routing condition the V3 decision leaves in place.
    candidates = {"eth0", "wg0"}  # both link defaults are yes/+DefaultRoute
    assert candidates == {"eth0", "wg0"}
    assert model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())[
        "conflict"
    ]


@pytest.mark.parametrize("source", ["physical", "global"])
def test_f1_split_only_vpn_reports_default_dns_exposure(tmp_path, source):
    model = Model(tmp_path)
    model.text = status(
        eth="192.168.0.1" if source == "physical" else "",
        eth_domain="~lan.example",
        eth_default="yes",
        vpn_domain="~corp.example",
        vpn_default=False,
        global_dns="9.9.9.9" if source == "global" else "",
        global_domain="~office.example" if source == "global" else "",
    )
    policy = model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())
    # For public.example, neither ~lan nor ~corp/~office matches. systemd-resolved
    # falls back to default-route links and global DNS; the VPN is split-only.
    # Specific routes cannot hide the independent default/global fallback.
    assert not policy["policy_unknown"]
    assert policy["conflict"]
    assert policy["leak"]
    assert not policy["only_vpn_dns"]
    print(
        "F1_EXPOSURE_DETECTED",
        source,
        {
            k: policy[k]
            for k in (
                "conflict",
                "leak",
                "only_vpn_dns",
                "policy_unknown",
                "repair_ifaces",
                "split_ifaces",
            )
        },
    )
    ok, _message = model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert not ok and model.writes == []


@pytest.mark.parametrize("source", ["physical", "global"])
@pytest.mark.parametrize("address", ["192.0.2.53", "2001:db8::53"])
@pytest.mark.parametrize("default", ["yes", "no", None])
def test_f1_default_sources_are_evaluated_separately_from_split_domains(
    tmp_path, source, address, default
):
    model = Model(tmp_path)
    model.text = status(
        eth=address if source == "physical" else "",
        eth_default=default,
        vpn_default=False,
        global_dns=address if source == "global" else "",
        global_domain="~office.example",
    )
    if default is None:
        model.text = model.text.replace("    DefaultRoute setting: None\n", "")
    snapshot = model.service.read_dns_snapshot()
    policy = model.service.evaluate_dns_snapshot(snapshot)
    exposed = source == "global" or default != "no"
    assert not policy["policy_unknown"]
    assert policy["conflict"] is exposed
    assert policy["leak"] is exposed
    assert policy["only_vpn_dns"] is not exposed
    app = fake_app(model)
    app.rebuild_dns_guard_whitelist = lambda _snapshot: policy["vpn_dns"]
    state, _detail = app._dns_guard_observation(snapshot)
    assert state == ("problem" if exposed else "ok")
    assert model.writes == []


@pytest.mark.parametrize("transition", ["active", "unknown"])
@pytest.mark.parametrize("point", ["modify", "up"])
def test_f6_dhcp_release_is_rejected_before_transition_can_be_triggered(
    tmp_path, transition, point
):
    model = Model(tmp_path)
    model.props["ipv4.ignore-auto-dns"] = "yes"
    model.props["ipv6.ignore-auto-dns"] = "yes"
    # The initial public UI gate has already succeeded while VPN is confirmed down.
    app = fake_app(model)
    assert app.is_vpn_active() is False
    state = True if transition == "active" else None
    if point == "modify":
        model.flip_state_on_modify = state
        model.flip_modify = True
    else:
        model.flip_state_on_up = state
        model.flip_up = True
    result = apply_dns_profile_choice_via_control(
        app, "System (DHCP/auto)", manual=True
    )
    assert not result["success"]
    assert "vorläufig gesperrt" in " ".join(result["nm_details"])
    assert model.props["ipv4.ignore-auto-dns"] == "yes"
    assert model.props["ipv6.ignore-auto-dns"] == "yes"
    # No NM command is started, so neither armed in-command transition runs.
    assert model.writes == []
    print(
        "F6_RELEASE_REFUSED",
        transition,
        point,
        [c[4:8] for c in model.writes if c[0] == "sudo"],
    )


@pytest.mark.parametrize("entry", ["public", "private"])
def test_f6_direct_service_cannot_bypass_dhcp_release_refusal(tmp_path, entry):
    model = Model(tmp_path)
    model.props.update({"ipv4.ignore-auto-dns": "yes", "ipv6.ignore-auto-dns": "yes"})
    profiles = model.service.read_nm_dns_profiles([TARGET])
    before = dict(model.props)
    model.commands.clear()
    if entry == "public":
        ok, details = model.service.apply_nm_dns_policy_to_targets(
            ignore_auto_dns=False, targets=[TARGET]
        )
    else:
        ok, details = model.service._apply_nm_dns_profiles(profiles, False)
    assert not ok
    assert "vorläufig gesperrt" in " ".join(details)
    assert model.commands == []
    assert model.props == before


@pytest.mark.parametrize("choice", ["System (DHCP/auto)", "Cloudflare (1.1.1.1)"])
@pytest.mark.parametrize("transition", [False, True])
def test_f6_automatic_isp_restore_never_delegates_to_profile_writers(
    tmp_path, choice, transition
):
    model = Model(tmp_path)
    app = fake_app(model)
    actions, logs = [], []
    app._auto_dns_control_available = lambda: True
    app._dns_runtime_transition_active = lambda: transition
    app.apply_dns = lambda **kwargs: actions.append("apply") or True
    app._apply_dns_profile_choice_via_control = lambda _choice: actions.append(
        "control"
    ) or {"success": True}
    app._set_dns_choice_safe = lambda _choice: actions.append("choice")
    app.refresh_dns_policy_status = lambda: None
    app.log_safe = logs.append
    assert app._apply_automatic_dns_restore_choice(choice) is False
    assert actions == [] and model.writes == []
    assert any("vorläufig gesperrt" in message for message in logs)


def test_f6_disconnect_does_not_remove_dropin_or_restart_after_refusal(
    tmp_path, monkeypatch
):
    model = Model(tmp_path)
    model.path.write_text("[Resolve]\nDNS=10.64.0.1\n")
    app = fake_app(model)
    reports = []
    app._auto_dns_control_available = lambda: True
    app._active_nm_dns_targets = lambda: [TARGET]
    app.log_safe = lambda _message: None
    app.tr = lambda _key, fallback: fallback
    app.after = lambda _delay, callback: callback()
    app._show_auto_dns_policy_result = lambda title, text: reports.append(text)
    monkeypatch.setattr(
        netmon.threading,
        "Thread",
        lambda target, **kwargs: type("Worker", (), {"start": staticmethod(target)})(),
    )
    app.on_vpn_disconnected()
    assert model.writes == []
    assert model.path.read_text() == "[Resolve]\nDNS=10.64.0.1\n"
    assert reports and "failed" in reports[-1]


@pytest.mark.parametrize(
    "change",
    [
        "global_dns",
        "global_domain",
        "non_target_dns",
        "non_target_domains",
        "non_target_default",
    ],
)
def test_f7_activation_rejects_stale_routing_snapshot(tmp_path, change):
    model = Model(tmp_path)
    model.path.write_text("DNS=1.1.1.1\nDNSOverTLS=yes\n")
    # Existing dirty target creates a real planned NM action.
    model.text = status(eth="192.168.0.1", eth_domain="~.", vpn_domain="~.")

    def changed():
        base = status(eth="", eth_domain="", eth_default="no", vpn_domain="~.")
        if change == "global_dns":
            model.text = status(
                eth="",
                eth_domain="",
                eth_default="no",
                vpn_domain="~.",
                global_dns="9.9.9.9",
            )
        elif change == "global_domain":
            model.text = status(
                eth="",
                eth_domain="",
                eth_default="no",
                vpn_domain="~.",
                global_domain="~.",
            )
        elif change == "non_target_dns":
            model.text = base.replace(
                "Link 3 (wg0)",
                "Link 4 (enp5s0)\n    Current Scopes: DNS\n    DefaultRoute setting: yes\n    DNS Servers: 192.0.2.53\n    DNS Domain: ~corp.example\nLink 3 (wg0)",
            )
        elif change == "non_target_domains":
            model.text = base.replace(
                "Link 3 (wg0)",
                "Link 4 (enp5s0)\n    Current Scopes: DNS\n    DefaultRoute setting: no\n    DNS Servers: 192.0.2.53\n    DNS Domain: ~corp.example\nLink 3 (wg0)",
            )
        elif change == "non_target_default":
            model.text = base.replace(
                "Link 3 (wg0)",
                "Link 4 (enp5s0)\n    Current Scopes: DNS\n    DefaultRoute setting: yes\n    DNS Servers: 192.0.2.53\n    DNS Domain: ~corp.example\nLink 3 (wg0)",
            )

    model.on_up = changed
    ok, output = model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert not ok, (change, output)
    assert not any(
        c == ["sudo", "-n", "rm", "-f", str(model.path)] for c in model.writes
    )
    assert not any("systemctl" in c for c in model.writes)
    print("F7_STALE", change, "aborted before remove/restart")


def test_f7_planned_target_dns_removal_is_accepted(tmp_path):
    model = Model(tmp_path)
    model.text = status(eth="192.168.0.1", eth_domain="~.", vpn_domain="~.")
    ok, output = model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert ok, output
    assert len([c for c in model.writes if c[3:5] == ["con", "up"]]) == 1


def test_f7_plan_aborts_if_planned_target_still_has_dns(tmp_path):
    model = Model(tmp_path)
    model.text = status(eth="192.168.0.1", eth_domain="~.", vpn_domain="~.")
    model.on_up = lambda: setattr(
        model, "text", status(eth="192.168.0.53", eth_domain="~.", vpn_domain="~.")
    )
    ok, output = model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)
    assert not ok, output
    assert len([c for c in model.writes if c[3:5] == ["con", "up"]]) == 1
    assert not any("systemctl" in c for c in model.writes)
