import threading

import pytest

from tools import netmon


@pytest.fixture(autouse=True)
def fake_verified_interfaces(monkeypatch):
    # This suite models already authenticated synthetic WG links. The dedicated
    # interface-security suite exercises the real verifier and closed gate.
    monkeypatch.setattr(
        netmon.firewall_controller.nm_ownership,
        "verified_interface",
        lambda name: {"name": name, "kind": "wireguard", "ifindex": 7},
    )


def _run_as_other_thread(target):
    original_get_ident = netmon.threading.get_ident
    owner_thread_id = original_get_ident()
    netmon.threading.get_ident = lambda: owner_thread_id + 1
    try:
        target()
    finally:
        netmon.threading.get_ident = original_get_ident


def _ufw_verbose_killswitch_on_status(wg_ifaces=None, handshake_rules=None):
    lines = [
        "Status: active",
        "Default: deny (incoming), deny (outgoing), disabled (routed)",
        "Anywhere on lo ALLOW IN Anywhere",
        "Anywhere ALLOW OUT Anywhere on lo",
    ]
    for iface in wg_ifaces or []:
        lines.append(f"Anywhere on {iface} ALLOW IN Anywhere")
        lines.append(f"Anywhere ALLOW OUT Anywhere on {iface}")
    for endpoint_ip, endpoint_port in handshake_rules or []:
        lines.append(f"{endpoint_ip} {endpoint_port}/udp ALLOW OUT Anywhere")
    return "\n".join(lines)


def _ufw_verbose_killswitch_off_status():
    return "\n".join(
        [
            "Status: active",
            "Default: deny (incoming), allow (outgoing), disabled (routed)",
        ]
    )


def test_parse_vpn_endpoint_reads_endpoint_from_profile(monkeypatch):
    app = netmon.App.__new__(netmon.App)

    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return (
            0,
            """[Peer]
Endpoint = 66.234.146.66:51820
PersistentKeepalive = 25
""",
        )

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app.parse_vpn_endpoint("proton") == ("66.234.146.66", "51820")
    assert calls == [["sudo", "-n", "cat", "/etc/wireguard/proton.conf"]]


def test_parse_vpn_endpoint_rejects_non_ip_host(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    warnings = []

    def fake_run_cmd(args, timeout=0, text=True):
        return (
            0,
            """[Peer]
Endpoint = any:51820
""",
        )

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller,
        "_warn_non_ip_endpoint_once",
        lambda _app, profile, host: warnings.append((profile, host)),
    )

    assert app.parse_vpn_endpoint("proton") == (None, None)
    assert warnings == [("proton", "any")]


def test_startup_repair_disables_killswitch_without_active_vpn(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    app.privacy_config = {}
    app.isp_stealth_running = False
    app._network_operation_active_elsewhere = lambda: False
    app.killswitch_is_on = lambda: True
    app.get_wg_interfaces = lambda: []
    app.is_vpn_active = lambda: False
    app.log_safe = lambda message: calls.append(("log", message))
    app.log_debug_safe = lambda message: calls.append(("debug", message))
    app.killswitch_off = lambda **kwargs: calls.append(("off", kwargs)) or True
    monkeypatch.setattr(
        netmon.vpn_controller, "get_active_nm_wireguard_connections", lambda _app: []
    )
    monkeypatch.setattr(
        netmon.vpn_controller, "get_active_nm_vpn_connections", lambda _app: []
    )
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: True)

    assert app.repair_orphaned_killswitch_on_startup() is True
    assert (
        "off",
        {
            "async_mode": False,
            "ensure_sudo": False,
            "refresh_ui": True,
            "interactive_guard": False,
        },
    ) in calls


def test_startup_repair_keeps_killswitch_with_active_vpn(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    app.privacy_config = {}
    app.isp_stealth_running = False
    app._network_operation_active_elsewhere = lambda: False
    app.killswitch_is_on = lambda: True
    app.get_wg_interfaces = lambda: ["wg0"]
    app.is_vpn_active = lambda: False
    app.log_safe = lambda message: calls.append(("log", message))
    app.log_debug_safe = lambda message: calls.append(("debug", message))
    app.killswitch_off = lambda **kwargs: calls.append(("off", kwargs)) or True
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: True)

    assert app.repair_orphaned_killswitch_on_startup() is False
    assert not any(kind == "off" for kind, _value in calls)


def test_startup_repair_skips_stealth_autostart():
    app = netmon.App.__new__(netmon.App)
    app.privacy_config = {"enabled": True, "autostart": True}
    app.isp_stealth_running = False
    app._network_operation_active_elsewhere = lambda: False
    app.killswitch_is_on = lambda: (_ for _ in ()).throw(
        AssertionError("killswitch state must not be queried during stealth autostart")
    )

    assert app.repair_orphaned_killswitch_on_startup() is False


def test_killswitch_on_allows_wireguard_handshake_without_active_tunnel(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    logs = []
    refreshes = []

    app.get_wg_interfaces = lambda: []
    app.get_wg_iface = lambda: None
    app.get_killswitch_vpn_profiles = lambda: ["proton", "proton-de"]

    endpoints = {
        "proton": ("66.234.146.66", "51820"),
        "proton-de": ("77.88.99.11", "443"),
    }
    app.parse_vpn_endpoint = lambda profile: endpoints[profile]
    app.log_safe = logs.append
    app.refresh_safe = lambda: refreshes.append(True)

    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_on_status(
                handshake_rules=[("66.234.146.66", "51820"), ("77.88.99.11", "443")]
            )
        if args == ["sudo", "-n", "ufw", "status", "numbered"]:
            return 0, "Status: active"
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app._killswitch_on_sync(refresh_ui=True) is True
    assert ["sudo", "-n", "ufw", "default", "deny", "outgoing"] in calls
    assert ["sudo", "-n", "ufw", "default", "deny", "incoming"] in calls
    assert ["sudo", "-n", "ufw", "allow", "in", "on", "lo"] in calls
    assert ["sudo", "-n", "ufw", "allow", "out", "on", "lo"] in calls
    assert ["sudo", "-n", "ufw", "allow", "out", "53/udp"] not in calls
    assert ["sudo", "-n", "ufw", "allow", "out", "53/tcp"] not in calls
    assert ["sudo", "-n", "ufw", "allow", "out", "80/tcp"] not in calls
    assert ["sudo", "-n", "ufw", "allow", "out", "443/tcp"] not in calls
    assert [
        "sudo",
        "-n",
        "ufw",
        "allow",
        "out",
        "to",
        "66.234.146.66",
        "port",
        "51820",
        "proto",
        "udp",
    ] in calls
    assert [
        "sudo",
        "-n",
        "ufw",
        "allow",
        "out",
        "to",
        "77.88.99.11",
        "port",
        "443",
        "proto",
        "udp",
    ] in calls
    assert not any(
        cmd[:7] == ["sudo", "-n", "ufw", "allow", "out", "on", "wg0"] for cmd in calls
    )
    assert any(
        "WireGuard Handshake erlaubt für 66.234.146.66:51820" in entry for entry in logs
    )
    assert any("Tunnelaufbau kann starten" in entry for entry in logs)
    assert refreshes == [True]


def test_killswitch_on_rejects_late_global_web_and_dns_without_deleting(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.log_safe = lambda _message: None
    app.refresh_safe = lambda: None
    app.get_wg_interfaces = lambda: []
    app.get_killswitch_vpn_endpoints = lambda: [("66.234.146.66", "51820")]

    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "numbered"]:
            return (
                0,
                "\n".join(
                    [
                        "Status: active",
                        "[ 1] 53/udp ALLOW OUT Anywhere",
                        "[ 2] 53/tcp ALLOW OUT Anywhere",
                        "[ 3] 80/tcp ALLOW OUT Anywhere",
                        "[ 4] 443/tcp ALLOW OUT Anywhere",
                    ]
                ),
            )
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_on_status(
                handshake_rules=[("66.234.146.66", "51820")]
            )
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._killswitch_on_sync(refresh_ui=False) is False
    assert not any("delete" in cmd for cmd in calls)
    assert [
        "sudo",
        "-n",
        "ufw",
        "insert",
        "1",
        "deny",
        "out",
        "from",
        "any",
        "to",
        "any",
    ] in calls


def test_killswitch_off_keeps_ufw_active_and_restores_default_routing(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    logs = []
    refreshes = []
    app.log_safe = logs.append
    app.log_network_debug = lambda _message: None
    app.refresh_safe = lambda: refreshes.append(True)
    app.get_wg_interfaces = lambda: ["wg0", "wg-slot"]
    app.get_wg_iface = lambda: "wg0"
    app.list_wg_profiles = lambda: ["proton", "proton-de", "wg-slot"]
    app.get_killswitch_vpn_profiles = lambda: ["proton", "proton-de"]

    endpoints = {
        "proton": ("66.234.146.66", "51820"),
        "proton-de": ("77.88.99.11", "443"),
    }
    app.parse_vpn_endpoint = lambda profile: endpoints[profile]

    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_off_status()
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app._killswitch_off_sync(refresh_ui=True) is True
    assert ["sudo", "-n", "ufw", "disable"] not in calls
    assert ["sudo", "-n", "ufw", "default", "allow", "outgoing"] in calls
    assert ["sudo", "-n", "ufw", "default", "deny", "incoming"] in calls
    assert ["sudo", "-n", "ufw", "status", "verbose"] in calls
    assert not any("delete" in cmd for cmd in calls)
    assert any("UFW-Defaults deny/allow verifiziert" in entry for entry in logs)
    assert any("Regeln bleiben erhalten" in entry for entry in logs)
    assert refreshes == [True]


def test_killswitch_off_enables_ufw_if_needed(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.log_safe = lambda message: None
    app.refresh_safe = lambda: None
    app.get_wg_interfaces = lambda: []
    app.get_wg_iface = lambda: None
    app.list_wg_profiles = lambda: []
    app.get_killswitch_vpn_profiles = lambda: []
    app.parse_vpn_endpoint = lambda profile: (None, None)

    calls = []
    verbose_reads = 0

    def fake_run_cmd(args, timeout=0, text=True):
        nonlocal verbose_reads
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: inactive"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            verbose_reads += 1
            return (
                (0, "Status: inactive")
                if verbose_reads == 1
                else (0, _ufw_verbose_killswitch_off_status())
            )
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app._killswitch_off_sync(refresh_ui=False) is True
    assert ["sudo", "-n", "ufw", "--force", "enable"] in calls
    assert ["sudo", "-n", "ufw", "default", "allow", "outgoing"] in calls
    assert ["sudo", "-n", "ufw", "default", "deny", "incoming"] in calls


def test_killswitch_off_does_not_delete_from_known_profile_names(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.log_safe = lambda message: None
    app.refresh_safe = lambda: None
    app.get_wg_interfaces = lambda: []
    app.list_wg_profiles = lambda: []
    app.wg_profiles = ["USA__ipv4", "Irland", "NL", "proton-de"]
    app.vpn_slots = []
    app.primary_vpn_slots = []
    app.parse_vpn_endpoint = lambda profile: (None, None)

    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_off_status()
        if args == ["sudo", "-n", "ufw", "status", "numbered"]:
            return (
                0,
                "\n".join(
                    [
                        "[ 1] Anywhere ALLOW OUT Anywhere on USA__ipv4",
                        "[ 2] Anywhere on USA__ipv4 ALLOW IN Anywhere",
                        "[ 3] Anywhere ALLOW OUT Anywhere on Irland",
                        "[ 4] Anywhere on Irland ALLOW IN Anywhere",
                        "[ 5] Anywhere ALLOW OUT Anywhere on NL",
                        "[ 6] Anywhere on NL ALLOW IN Anywhere",
                        "[ 7] Anywhere ALLOW OUT Anywhere on proton-de",
                        "[ 8] Anywhere on proton-de ALLOW IN Anywhere",
                    ]
                ),
            )
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._killswitch_off_sync(refresh_ui=False) is True
    assert not any("delete" in cmd for cmd in calls)
    assert ["sudo", "-n", "ufw", "default", "allow", "outgoing"] in calls


def test_killswitch_on_allows_all_active_wireguard_interfaces(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    logs = []
    app.get_wg_interfaces = lambda: ["wg0", "Irland2_-IE-112"]
    app.get_killswitch_vpn_profiles = lambda: ["proton", "Irland2_-IE-112"]
    app.parse_vpn_endpoint = lambda profile: (
        ("66.234.146.66", "51820") if profile == "proton" else ("203.0.113.10", "51820")
    )
    app.log_safe = logs.append
    app.refresh_safe = lambda: None

    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_on_status(
                wg_ifaces=["wg0", "Irland2_-IE-112"],
                handshake_rules=[("66.234.146.66", "51820"), ("203.0.113.10", "51820")],
            )
        if args == ["sudo", "-n", "ufw", "status", "numbered"]:
            return 0, "Status: active"
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._killswitch_on_sync(refresh_ui=False) is True
    assert ["sudo", "-n", "ufw", "allow", "out", "on", "wg0"] in calls
    assert ["sudo", "-n", "ufw", "allow", "in", "on", "wg0"] in calls
    assert ["sudo", "-n", "ufw", "allow", "out", "on", "Irland2_-IE-112"] in calls
    assert ["sudo", "-n", "ufw", "allow", "in", "on", "Irland2_-IE-112"] in calls
    assert any("wg0" in entry and "Irland2_-IE-112" in entry for entry in logs)


def test_vpn_switch_reapplies_killswitch_rules_after_successful_switch(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []
    refreshes = []
    synced = []

    app.ipv6_is_disabled = lambda: False
    app.profile_supports_ipv6 = lambda profile: False
    app.get_wg_interfaces = lambda: []
    app.log_safe = logs.append
    app.refresh_wg_profiles = lambda: refreshes.append("profiles")
    app.update_ipv6_controls_state_safe = lambda: refreshes.append("ipv6")
    app.refresh_safe = lambda: refreshes.append("ui")
    app.killswitch_is_on = lambda: True
    app._killswitch_on_sync = lambda refresh_ui=True: synced.append(refresh_ui) or True
    app.prepare_dns_for_vpn_profile_switch = lambda: []
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda delay_ms=2500: None
    app.run_async = lambda func: func()
    app.verify_vpn_exit_country = lambda profile: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app._check_wireguard_profile_for_multiple_endpoints = lambda *args: None
    app.log_debug = lambda *args: None
    app.log_debug_safe = lambda *args: None

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app.vpn_switch("wg-slot", ensure_sudo=False, refresh_ui=True) is True
    assert ["sudo", "-n", "test", "-f", "/etc/wireguard/wg-slot.conf"] in calls
    assert ["sudo", "-n", "wg-quick", "up", "wg-slot"] in calls
    assert synced == [False]


def test_cleanup_old_vpn_dns_links_reverts_detected_vpn_interfaces(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    app.get_wg_interfaces = lambda: ["wg-live"]

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["resolvectl", "status"]:
            return (
                0,
                "\n".join(
                    [
                        "Link 2 (enp0s3)",
                        "Link 9 (wg-live)",
                        "Link 11 (protonvpn0)",
                    ]
                ),
            )
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    actions = app.cleanup_old_vpn_dns_links()

    assert "resolvectl revert protonvpn0: rc=0" in actions
    assert "resolvectl revert wg-live: rc=0" in actions
    assert ["sudo", "-n", "resolvectl", "revert", "wg-live"] in calls
    assert ["sudo", "-n", "resolvectl", "revert", "protonvpn0"] in calls


def test_vpn_switch_prepares_and_schedules_dns_finalize(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []
    refreshes = []
    prepare_calls = []
    finalize_delays = []

    app.ipv6_is_disabled = lambda: False
    app.resolve_runtime_vpn_profile = lambda target, log_missing=True: target
    app.get_wg_iface = lambda: ""
    app.get_wg_interfaces = lambda: ["wg-old"]
    app._check_wireguard_profile_for_multiple_endpoints = lambda *args: None
    app.log_safe = logs.append
    app.log_debug = lambda *args: None
    app.log_debug_safe = lambda *args: None
    app.refresh_wg_profiles = lambda: refreshes.append("profiles")
    app.sync_internal_ipv4_profiles = lambda log_failures=False: refreshes.append(
        "sync"
    )
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.update_ipv6_controls_state_safe = lambda: refreshes.append("ipv6")
    app.verify_vpn_exit_country = lambda profile: None
    app.killswitch_is_on = lambda: False
    app.refresh_safe = lambda: refreshes.append("ui")
    app.prepare_dns_for_vpn_profile_switch = (
        lambda: prepare_calls.append("prepare") or []
    )
    app._schedule_dns_finalize_after_vpn_profile_switch = (
        lambda delay_ms=2500: finalize_delays.append(delay_ms)
    )
    app.run_async = lambda func: func()
    app.reconcile_vpn_slot_firewall_state = lambda **kwargs: True

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", lambda _app: True
    )

    assert app.vpn_switch("wg-slot", ensure_sudo=False, refresh_ui=True) is True
    assert prepare_calls == ["prepare"]
    assert finalize_delays == [2500]
    assert ["sudo", "-n", "test", "-f", "/etc/wireguard/wg-slot.conf"] in calls
    assert ["sudo", "-n", "wg-quick", "up", "wg-slot"] in calls


def test_vpn_switch_reconciles_non_killswitch_firewall_rules_after_success(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    finalize_delays = []
    reconciles = []

    app.ipv6_is_disabled = lambda: False
    app.profile_supports_ipv6 = lambda profile: False
    app.get_wg_interfaces = lambda: []
    app._check_wireguard_profile_for_multiple_endpoints = lambda *args: None
    app.log_safe = lambda *_args: None
    app.log_debug = lambda *_args: None
    app.log_debug_safe = lambda *_args: None
    app.refresh_wg_profiles = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.refresh_safe = lambda: None
    app.killswitch_is_on = lambda: False
    app.prepare_dns_for_vpn_profile_switch = lambda: []
    app._schedule_dns_finalize_after_vpn_profile_switch = (
        lambda delay_ms=2500: finalize_delays.append(delay_ms)
    )
    app.run_async = lambda func: func()
    app.verify_vpn_exit_country = lambda profile: None
    app.reconcile_vpn_slot_firewall_state = (
        lambda **kwargs: reconciles.append(dict(kwargs)) or True
    )

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", lambda _app: True
    )

    assert app.vpn_switch("wg-slot", ensure_sudo=False, refresh_ui=True) is True
    assert ["sudo", "-n", "wg-quick", "up", "wg-slot"] in calls
    assert reconciles == [
        {
            "reason": "VPN aktiv: wg-slot",
            "touched_profiles": ["wg-slot"],
            "refresh_ui": False,
        }
    ]
    assert finalize_delays == [2500]


def test_vpn_switch_can_skip_cleanup_after_restore_cleanup(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    cleanup_calls = []

    app.ipv6_is_disabled = lambda: False
    app.resolve_runtime_vpn_profile = lambda target, log_missing=True: target
    app.get_wg_interfaces = lambda: []
    app._check_wireguard_profile_for_multiple_endpoints = lambda *args: None
    app.log_safe = lambda *_args: None
    app.log_debug = lambda *_args: None
    app.log_debug_safe = lambda *_args: None
    app.log_network_debug = lambda *_args: None
    app.refresh_wg_profiles = lambda: None
    app.sync_internal_ipv4_profiles = lambda log_failures=False: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.verify_vpn_exit_country = lambda profile: None
    app.killswitch_is_on = lambda: False
    app.refresh_safe = lambda: None
    app.prepare_dns_for_vpn_profile_switch = lambda: []
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda delay_ms=2500: None
    app.run_async = lambda func: func()
    app.reconcile_vpn_slot_firewall_state = lambda **kwargs: True

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller,
        "cleanup_wireguard_interfaces",
        lambda _app: cleanup_calls.append("cleanup") or True,
    )

    assert (
        app.vpn_switch(
            "wg-slot",
            ensure_sudo=False,
            refresh_ui=False,
            force_reconnect=True,
            skip_cleanup=True,
        )
        is True
    )
    assert cleanup_calls == []
    assert ["sudo", "-n", "wg-quick", "up", "wg-slot"] in calls


def test_vpn_off_prepares_and_schedules_dns_finalize(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []
    finalize_delays = []
    prepare_calls = []

    app.wg_profiles = ["proton"]
    app.get_wg_interfaces = lambda: ["wg-live"]
    app.log_safe = logs.append
    app.killswitch_is_on = lambda: False
    app.refresh_wg_profiles = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.refresh_safe = lambda: None
    app.prepare_dns_for_vpn_profile_switch = (
        lambda: prepare_calls.append("prepare") or []
    )
    app._schedule_dns_finalize_after_vpn_profile_switch = (
        lambda delay_ms=2500: finalize_delays.append(delay_ms)
    )
    app.log_network_debug = lambda *_args: None

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", lambda _app: True
    )

    assert app.vpn_off(ensure_sudo=False, refresh_ui=True) is True
    assert prepare_calls == ["prepare"]
    assert finalize_delays == [2500]
    assert "VPN deaktiviert." in logs


def test_vpn_off_shows_notice_when_killswitch_stays_active(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    warnings = []
    debug_calls = []
    app.debug_nm_state = lambda context: debug_calls.append(context)

    app.wg_profiles = ["proton"]
    app.get_wg_interfaces = lambda: ["wg-live"]
    app.log_safe = logs.append
    app.killswitch_is_on = lambda: True
    app.refresh_wg_profiles = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.refresh_safe = lambda: None
    app.prepare_dns_for_vpn_profile_switch = lambda: []
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda delay_ms=2500: None
    app.log_network_debug = lambda *_args: None

    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", lambda _app: True
    )
    monkeypatch.setattr(
        netmon.vpn_controller.messagebox,
        "showwarning",
        lambda title, message, parent=None: warnings.append((title, message, parent)),
    )

    assert app.vpn_off(ensure_sudo=False, refresh_ui=True) is True
    assert len(warnings) == 1
    assert warnings[0][0] == "Killswitch bleibt aktiv"
    assert "VPN wurde deaktiviert" in warnings[0][1]
    assert warnings[0][2] is app
    assert any("Killswitch ist AN" in entry for entry in logs)
    assert debug_calls == ["vor VPN AUS", "nach VPN AUS"]


def test_vpn_off_does_not_show_killswitch_notice_when_killswitch_is_off(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    warnings = []
    debug_calls = []
    app.debug_nm_state = lambda context: debug_calls.append(context)

    app.wg_profiles = ["proton"]
    app.get_wg_interfaces = lambda: ["wg-live"]
    app.log_safe = lambda _message: None
    app.killswitch_is_on = lambda: False
    app.refresh_wg_profiles = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.refresh_safe = lambda: None
    app.prepare_dns_for_vpn_profile_switch = lambda: []
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda delay_ms=2500: None
    app.log_network_debug = lambda *_args: None

    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", lambda _app: True
    )
    monkeypatch.setattr(
        netmon.vpn_controller.messagebox,
        "showwarning",
        lambda title, message, parent=None: warnings.append((title, message, parent)),
    )

    assert app.vpn_off(ensure_sudo=False, refresh_ui=True) is True
    assert warnings == []
    assert debug_calls == ["vor VPN AUS", "nach VPN AUS"]


def test_get_killswitch_vpn_endpoints_deduplicates_same_endpoint(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.active_wg_profile = lambda: "proton"
    app.list_wg_profiles = lambda: ["proton", "proton__ipv4", "proton-de"]

    endpoints = {
        "proton": ("66.234.146.66", "51820"),
        "proton__ipv4": ("66.234.146.66", "51820"),
        "proton-de": ("77.88.99.11", "443"),
    }
    app.parse_vpn_endpoint = lambda profile: endpoints[profile]

    assert app.get_killswitch_vpn_profiles() == ["proton", "proton__ipv4", "proton-de"]
    assert app.get_killswitch_vpn_endpoints() == [
        ("66.234.146.66", "51820"),
        ("77.88.99.11", "443"),
    ]


def test_killswitch_on_logs_each_handshake_endpoint_only_once(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    logs = []

    app.get_wg_interfaces = lambda: []
    app.get_killswitch_vpn_endpoints = lambda: [
        ("66.234.146.66", "51820"),
        ("77.88.99.11", "443"),
    ]
    app.log_safe = logs.append
    app.refresh_safe = lambda: None

    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_on_status(
                handshake_rules=[("66.234.146.66", "51820"), ("77.88.99.11", "443")]
            )
        if args == ["sudo", "-n", "ufw", "status", "numbered"]:
            return 0, "Status: active"
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._killswitch_on_sync(refresh_ui=False) is True
    handshake_logs = [
        entry for entry in logs if "WireGuard Handshake erlaubt für" in entry
    ]
    assert handshake_logs == [
        "Killswitch: WireGuard Handshake erlaubt für 66.234.146.66:51820",
        "Killswitch: WireGuard Handshake erlaubt für 77.88.99.11:443",
    ]
    assert (
        calls.count(
            [
                "sudo",
                "-n",
                "ufw",
                "allow",
                "out",
                "to",
                "66.234.146.66",
                "port",
                "51820",
                "proto",
                "udp",
            ]
        )
        == 1
    )


def test_isp_stealth_on_skips_duplicate_killswitch_activation_when_already_active(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.ipv6_is_disabled = lambda: False
    app.active_wg_profile = lambda: None
    app.get_wg_iface = lambda: ""
    logs = []
    states = []
    refreshes = []
    killswitch_calls = []

    class DummyVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        netmon.security_monitoring_controller.threading,
        "Thread",
        ImmediateThread,
    )

    app.isp_stealth_running = False
    app.isp_stealth_lock = threading.Lock()
    app.ensure_sudo_session = lambda message: True
    app.isp_stealth_disable_ipv6 = DummyVar(False)
    app.isp_stealth_enable_killswitch = DummyVar(True)
    app.isp_stealth_vpn_profile = DummyVar("")
    app.isp_stealth_dns_profile = DummyVar("")
    app.killswitch_is_on = lambda: True
    app.killswitch_on = lambda **kwargs: killswitch_calls.append(kwargs) or True
    app.after = lambda delay, callback: callback()
    app._set_stealth_enabled_state = lambda enabled: states.append(enabled)
    app.log_safe = logs.append
    app.log = logs.append
    app.refresh_safe = lambda: refreshes.append(True)
    app.update_ipv6_controls_state_safe = lambda: None

    app.isp_stealth_on(from_startup=True)

    assert killswitch_calls == []
    assert states == [True]
    assert "ISP-Stealthmodus per Autostart aktiviert." in logs
    assert not any("Killswitch AN" in entry for entry in logs)
    assert refreshes == [True]


def test_vpn_switch_force_reconnect_rebuilds_same_profile(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []

    app.ipv6_is_disabled = lambda: False
    app.resolve_runtime_vpn_profile = lambda target, log_missing=True: target
    app.get_wg_iface = lambda: "wg-slot"
    app.get_wg_interfaces = lambda: ["wg-slot"]
    app._check_wireguard_profile_for_multiple_endpoints = lambda *args: None
    app.log_safe = logs.append
    app.log_debug = lambda *args: None
    app.log_debug_safe = lambda *args: None
    app.refresh_wg_profiles = lambda: None
    app.sync_internal_ipv4_profiles = lambda log_failures=False: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.verify_vpn_exit_country = lambda profile: None
    app.killswitch_is_on = lambda: False
    app.refresh_safe = lambda: None
    app.prepare_dns_for_vpn_profile_switch = lambda: []
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda delay_ms=2500: None
    app.run_async = lambda func: func()
    app.reconcile_vpn_slot_firewall_state = lambda **kwargs: True

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", lambda _app: True
    )

    assert (
        app.vpn_switch(
            "wg-slot", ensure_sudo=False, refresh_ui=False, force_reconnect=True
        )
        is True
    )
    assert ["sudo", "-n", "test", "-f", "/etc/wireguard/wg-slot.conf"] in calls
    assert ["sudo", "-n", "wg-quick", "up", "wg-slot"] in calls
    assert "Vorhandenes Runtimeprofil erkannt - Reconnect wird erzwungen." in logs
    assert "VPN Verbindung neu aufgebaut." in logs


def test_wait_for_vpn_ready_requires_interface_and_internet(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    iface_states = iter([None, "wg0", "wg0"])
    internet_states = iter([False, True])

    app.get_wg_iface = lambda: next(iface_states, "wg0")
    app.check_internet = lambda: next(internet_states, True)
    monkeypatch.setattr(netmon.time, "sleep", lambda *_args: None)

    assert app.wait_for_vpn_ready(timeout=1, interval=0.01) is True


def test_internet_on_sync_forces_reconnect_and_keeps_killswitch_active(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.debug_nm_state = lambda reason: None
    logs = []
    scheduled = []
    vpn_calls = []
    killswitch_on_calls = []
    killswitch_off_calls = []

    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": True,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    app.vpn_before_internet_off = "proton"
    app.log = logs.append
    app.refresh = lambda: None

    def fake_after(delay, callback):
        scheduled.append(delay)
        callback()

    app.after = fake_after
    app._state_coordinator = lambda: None
    app._clear_internet_suspend_request = lambda: None
    app._base_wg_profile_name = lambda profile: profile
    app.wait_for_network_ready = lambda timeout=20: True
    app.cleanup_wireguard_interfaces = lambda: True
    app.killswitch_is_on = lambda: True
    app.vpn_switch = (
        lambda target, ensure_sudo=True, refresh_ui=True, force_reconnect=False, skip_cleanup=False: vpn_calls.append(
            {
                "target": target,
                "ensure_sudo": ensure_sudo,
                "refresh_ui": refresh_ui,
                "force_reconnect": force_reconnect,
                "skip_cleanup": skip_cleanup,
            }
        )
        or True
    )
    app.wait_for_vpn_ready = lambda timeout=15, interval=0.5: True
    app.killswitch_off = lambda **kwargs: killswitch_off_calls.append(kwargs) or True
    app.killswitch_on = lambda **kwargs: killswitch_on_calls.append(kwargs) or True
    app.log_debug_safe = logs.append
    monkeypatch.setattr(netmon.time, "sleep", lambda *_args: None)

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "nmcli", "networking", "on"]:
            return 0, "ok"
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._internet_on_sync() is True
    assert vpn_calls == [
        {
            "target": "proton",
            "ensure_sudo": False,
            "refresh_ui": False,
            "force_reconnect": True,
            "skip_cleanup": True,
        }
    ]
    assert killswitch_off_calls == []
    assert killswitch_on_calls == []
    assert "Killswitch bleibt während der VPN-Wiederherstellung aktiv." in logs
    assert "VPN-Wiederherstellung gestartet (Profil: proton)." in logs
    assert "VPN-Tunnel ist bereit." in logs
    assert 1500 in scheduled and 3000 in scheduled


def test_internet_on_sync_retries_network_ready_after_wg_and_killswitch_reset(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.debug_nm_state = lambda reason: None
    logs = []
    vpn_calls = []
    cleanup_calls = []
    network_ready_states = iter([False, True])

    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": True,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    app.vpn_before_internet_off = "proton"
    app.log = logs.append
    app.log_debug_safe = logs.append
    app.refresh = lambda: None
    app.after = lambda _delay, callback: callback()
    app._state_coordinator = lambda: None
    app._clear_internet_suspend_request = lambda: None
    app._base_wg_profile_name = lambda profile: profile
    app.wait_for_network_ready = lambda timeout=20: next(network_ready_states, True)
    app.cleanup_wireguard_interfaces = lambda: cleanup_calls.append(True) or True
    app.killswitch_is_on = lambda: True
    app.killswitch_off = lambda **_kwargs: True
    app.killswitch_on = lambda **_kwargs: True
    app.vpn_switch = (
        lambda target, ensure_sudo=True, refresh_ui=True, force_reconnect=False, skip_cleanup=False: vpn_calls.append(
            {
                "target": target,
                "ensure_sudo": ensure_sudo,
                "refresh_ui": refresh_ui,
                "force_reconnect": force_reconnect,
                "skip_cleanup": skip_cleanup,
            }
        )
        or True
    )
    app.wait_for_vpn_ready = lambda timeout=15, interval=0.5: True
    monkeypatch.setattr(netmon.time, "sleep", lambda *_args: None)

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "nmcli", "networking", "on"]:
            return 0, "ok"
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._internet_on_sync() is True
    assert cleanup_calls == [True]
    assert vpn_calls == [
        {
            "target": "proton",
            "ensure_sudo": False,
            "refresh_ui": False,
            "force_reconnect": True,
            "skip_cleanup": True,
        }
    ]
    assert (
        "Internet AN: warte nach WG/Killswitch-Reset erneut auf NetworkManager." in logs
    )
    assert "Internet AN: NetworkManager nach Reset bereit." in logs
    assert "VPN-Tunnel ist bereit." in logs


def test_internet_on_sync_uses_short_initial_wait_for_pending_vpn_restore(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.debug_nm_state = lambda reason: None
    logs = []
    wait_timeouts = []

    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": False,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    app.vpn_before_internet_off = "proton"
    app.log = logs.append
    app.log_debug_safe = logs.append
    app.refresh = lambda: None
    app.after = lambda _delay, callback: callback()
    app._state_coordinator = lambda: None
    app._clear_internet_suspend_request = lambda: None
    app._base_wg_profile_name = lambda profile: profile
    app.wait_for_network_ready = (
        lambda timeout=20: wait_timeouts.append(timeout) or True
    )
    app.cleanup_wireguard_interfaces = lambda: True
    app.killswitch_is_on = lambda: False
    app.vpn_switch = lambda *args, **kwargs: True
    app.wait_for_vpn_ready = lambda timeout=15, interval=0.5: True
    monkeypatch.setattr(netmon.time, "sleep", lambda *_args: None)

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "nmcli", "networking", "on"]:
            return 0, "ok"
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._internet_on_sync() is True
    assert wait_timeouts == [5]
    assert "Internet AN: NetworkManager bereit." in logs


def test_internet_toggle_state_logging_is_quiet_without_network_debug(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []

    app.debug_network_logging = False
    app.log_safe = logs.append
    app.log_network_debug = logs.append
    app.get_wg_interfaces = lambda: ["proton"]
    app.get_current_vpn_profile = lambda: "proton"

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    app._log_internet_toggle_state("Internet AN: Zustand vorher")

    assert logs == []
    assert calls == []


def test_internet_on_sync_keeps_killswitch_active_when_vpn_not_ready(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.debug_nm_state = lambda reason: None
    logs = []
    killswitch_calls = []

    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": True,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    app.log = logs.append
    app.log_debug_safe = logs.append
    app.refresh = lambda: None
    app.after = lambda _delay, callback: callback()
    app.wait_for_network_ready = lambda timeout=20: True
    app.cleanup_wireguard_interfaces = lambda: True
    app._base_wg_profile_name = lambda profile: profile
    app.vpn_switch = lambda *args, **kwargs: True
    app.wait_for_vpn_ready = lambda timeout=15, interval=0.5: False
    app.killswitch_is_on = lambda: True
    app.killswitch_off = lambda **kwargs: True
    app.killswitch_on = lambda **kwargs: killswitch_calls.append(kwargs) or True
    monkeypatch.setattr(netmon.time, "sleep", lambda *_args: None)

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "nmcli", "networking", "on"]:
            return 0, "ok"
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._internet_on_sync() is True
    assert killswitch_calls == []
    assert app.internet_suspend_state["vpn_profile"] == "proton"
    assert "VPN-Wiederherstellung fehlgeschlagen." in logs
    assert "Killswitch bleibt während der VPN-Wiederherstellung aktiv." in logs
    assert (
        "Killswitch bleibt aus, damit Internetzugang nicht blockiert wird." not in logs
    )
    assert (
        "Wiederherstellungszustand bleibt gespeichert, damit der Restore erneut versucht werden kann."
        in logs
    )


def test_try_begin_network_operation_blocks_parallel_operation():
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.network_ops_lock = threading.Lock()
    app.network_ops_lock.acquire()
    app.network_active_operation = "Internet AN"
    app._network_op_owner = None
    app._network_op_depth = 0
    app.log_safe = logs.append

    assert app._try_begin_network_operation("VPN wechseln auf proton") is False
    assert logs == [
        "Netzwerkaktion blockiert: VPN wechseln auf proton wird nicht gestartet, da bereits 'Internet AN' läuft."
    ]

    app.network_ops_lock.release()


def test_vpn_switch_stops_when_other_network_operation_is_active():
    app = netmon.App.__new__(netmon.App)
    logs = []
    refreshes = []

    app.network_ops_lock = threading.Lock()
    app.network_ops_lock.acquire()
    app.network_active_operation = "Internet AN"
    app._network_op_owner = None
    app._network_op_depth = 0
    app.log_safe = logs.append
    app.refresh_safe = lambda: refreshes.append(True)

    assert app.vpn_switch("wg-slot", ensure_sudo=False, refresh_ui=True) is False
    assert refreshes == [True]
    assert logs == [
        "Netzwerkaktion blockiert: VPN wechseln auf wg-slot wird nicht gestartet, da bereits 'Internet AN' läuft."
    ]

    app.network_ops_lock.release()


def test_security_scan_now_refreshes_table_via_after(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    after_calls = []
    refreshes = []
    status_updates = []
    device_refreshes = []

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        netmon.security_monitoring_controller.threading,
        "Thread",
        ImmediateThread,
    )

    app.security_scan_running = False
    app.security_event_keys = set()
    app.security_events = []
    app.security_last_alarm = "–"
    app._read_ufw_log_tail = lambda: ["ufw-line"]
    app._parse_ufw_block_line = lambda line: {
        "key": f"ufw-{line}",
        "type": "UFW BLOCK",
        "external": True,
    }
    app._security_detect_portscan = lambda: [
        {"key": "scan-1", "type": "Portscan-Verdacht", "external": True}
    ]
    app.scan_integrity_changes = lambda: [{"key": "sec-1"}]
    app.scan_device_changes = lambda: []
    app.scan_input_access_changes = lambda: []
    app.log = logs.append
    app.log_safe = logs.append
    app._refresh_security_table = lambda: refreshes.append("refresh")
    app._security_update_status = lambda color: status_updates.append(color)
    app.refresh_connected_device_table = lambda: device_refreshes.append("devices")

    def fake_after(delay, callback):
        after_calls.append(delay)
        callback()

    app.after = fake_after

    app.security_scan_now()

    assert app.security_events == [
        {"key": "ufw-ufw-line", "type": "UFW BLOCK", "external": True},
        {"key": "scan-1", "type": "Portscan-Verdacht", "external": True},
        {"key": "sec-1"},
    ]
    assert "Security-Scan: 3 neue Events" in logs
    assert refreshes == ["refresh"]
    assert device_refreshes == ["devices"]
    assert status_updates == ["red"]
    assert app.security_last_alarm == "Portscan-Verdacht"
    assert after_calls == [0, 0]


def test_internet_disable_runs_nmcli_off_async_and_restores_buttons_on_error(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    messagebox_calls = []
    light_calls = []

    class DummyButton:
        def __init__(self):
            self.states = []

        def configure(self, **kwargs):
            self.states.append(kwargs.get("state"))

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    app.network_ops_lock = threading.RLock()
    app.network_active_operation = ""
    app._network_op_owner = None
    app._network_op_depth = 0
    app.log = logs.append
    app.log_safe = logs.append
    app.after = lambda _delay, callback: callback()
    app.ensure_sudo_session = lambda message: True
    app._confirm_danger_action = lambda *args, **kwargs: True
    app.active_wg_profile = lambda: "proton"
    app.get_wg_iface = lambda: "proton__ipv4"
    app._base_wg_profile_name = lambda profile: (
        str(profile).replace("__ipv4", "") if profile else ""
    )
    app._state_coordinator = lambda: None
    app.check_ufw_active = lambda: True
    app.killswitch_is_on = lambda: True
    app._clear_internet_suspend_request = lambda: setattr(
        app, "internet_suspend_requested", False
    )
    app._log_internet_toggle_state = lambda _label: None
    app.set_light = lambda light, color: light_calls.append((light, color))
    app.l_inet = object()
    app.btn_inet_off = DummyButton()
    app.btn_inet_on = DummyButton()
    app.tr = lambda _key, default=None: default

    monkeypatch.setattr(netmon, "has_cmd", lambda name: True)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        netmon.messagebox,
        "showerror",
        lambda *args, **kwargs: messagebox_calls.append(args),
    )

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "nmcli", "networking", "off"]:
            return 1, "boom"
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app.internet_disable() is True
    assert app.internet_suspend_state == app._default_internet_suspend_state()
    assert app.vpn_before_internet_off == ""
    assert app.internet_suspend_requested is False
    assert app.btn_inet_off.states == ["disabled", "normal"]
    assert app.btn_inet_on.states == ["disabled", "normal"]
    assert light_calls[0][1] == "yellow"
    assert light_calls[-1][1] == "red"
    assert "Internet AUS Fehler: boom" in logs
    assert messagebox_calls


def test_internet_disable_captures_restore_state_for_followup_enable(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    light_calls = []
    refresh_bursts = []

    class DummyButton:
        def __init__(self):
            self.states = []

        def configure(self, **kwargs):
            self.states.append(kwargs.get("state"))

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    app.network_ops_lock = threading.RLock()
    app.network_active_operation = ""
    app._network_op_owner = None
    app._network_op_depth = 0
    app.log = logs.append
    app.log_safe = logs.append
    app.after = lambda _delay, callback: callback()
    app.ensure_sudo_session = lambda message: True
    app._confirm_danger_action = lambda *args, **kwargs: True
    app.active_wg_profile = lambda: "proton"
    app.get_wg_iface = lambda: "proton__ipv4"
    app._base_wg_profile_name = lambda profile: (
        str(profile).replace("__ipv4", "") if profile else ""
    )
    app._state_coordinator = lambda: netmon.NetmonStateCoordinator()
    app.check_ufw_active = lambda: True
    app.killswitch_is_on = lambda: True
    app._clear_internet_suspend_request = lambda: setattr(
        app, "internet_suspend_requested", False
    )
    app._log_internet_toggle_state = lambda _label: None
    app._schedule_refresh_burst = lambda delays_ms=None: refresh_bursts.append(
        delays_ms
    )
    app.refresh_internet_status = lambda: logs.append("refresh-internet")
    app.debug_nm_state = lambda *_args: None
    app._debug_log_system_cmd = lambda *_args: None
    app.set_light = lambda light, color: light_calls.append((light, color))
    app.l_inet = object()
    app.btn_inet_off = DummyButton()
    app.btn_inet_on = DummyButton()
    app.tr = lambda _key, default=None: default

    monkeypatch.setattr(netmon, "has_cmd", lambda name: True)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "run_cmd", lambda args, timeout=0, text=True: (0, "ok"))

    assert app.internet_disable() is True
    assert app.internet_suspend_state == {
        "ufw_was_active": True,
        "killswitch_was_active": True,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    assert app.vpn_before_internet_off == "proton"
    assert app.internet_suspend_requested is True
    assert refresh_bursts == [(0, 1000, 2500, 5000, 9000)]
    assert light_calls[0][1] == "yellow"
    assert light_calls[-1][1] == "gray"
    assert "Internet AUS: NetworkManager networking off" in logs


def test_internet_enable_runs_nmcli_on_async_and_restores_buttons(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    light_calls = []

    class DummyButton:
        def __init__(self):
            self.states = []

        def configure(self, **kwargs):
            self.states.append(kwargs.get("state"))

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    app.network_ops_lock = threading.RLock()
    app.network_active_operation = ""
    app._network_op_owner = None
    app._network_op_depth = 0
    app.log = logs.append
    app.log_safe = logs.append
    app.after = lambda _delay, callback: callback()
    app.ensure_sudo_session = lambda message: True
    app._confirm_danger_action = lambda *args, **kwargs: True
    app._state_coordinator = lambda: None
    app._base_wg_profile_name = lambda profile: profile
    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": False,
        "vpn_was_active": False,
        "vpn_profile": "",
        "vpn_interface": "",
    }
    app._clear_internet_suspend_request = lambda: setattr(
        app, "internet_suspend_requested", False
    )
    app._log_internet_toggle_state = lambda _label: None
    app._schedule_refresh_burst = lambda delays_ms=None: logs.append("refresh-burst")
    app.wait_for_network_ready = lambda timeout=20: True
    app.set_light = lambda light, color: light_calls.append((light, color))
    app.l_inet = object()
    app.btn_inet_off = DummyButton()
    app.btn_inet_on = DummyButton()
    app.tr = lambda _key, default=None: default
    app.debug_nm_state = lambda *_args: None
    app._debug_log_system_cmd = lambda *_args: None

    monkeypatch.setattr(netmon, "has_cmd", lambda name: True)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "run_cmd", lambda args, timeout=0, text=True: (0, "ok"))

    assert app.internet_enable() is True
    assert app.btn_inet_off.states == ["disabled", "normal"]
    assert app.btn_inet_on.states == ["disabled", "normal"]
    assert light_calls[0][1] == "yellow"
    assert "Internet AN: NetworkManager networking on" in logs
    assert "refresh-burst" in logs


def test_internet_enable_temporarily_disables_killswitch_before_vpn_restore(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    vpn_calls = []
    killswitch_off_calls = []
    killswitch_on_calls = []

    class DummyButton:
        def __init__(self):
            self.states = []

        def configure(self, **kwargs):
            self.states.append(kwargs.get("state"))

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                _run_as_other_thread(self.target)

    app.network_ops_lock = threading.RLock()
    app.network_active_operation = ""
    app._network_op_owner = None
    app._network_op_depth = 0
    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": True,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    app.vpn_before_internet_off = "proton"
    app.log = logs.append
    app.log_safe = logs.append
    app.log_debug_safe = logs.append
    app.after = lambda _delay, callback: callback()
    app.ensure_sudo_session = lambda message: True
    app._confirm_danger_action = lambda *args, **kwargs: True
    app._state_coordinator = lambda: None
    app._clear_internet_suspend_request = lambda: None
    app._log_internet_toggle_state = lambda _label: None
    app.wait_for_network_ready = lambda timeout=20: True
    app.cleanup_wireguard_interfaces = lambda: True
    app.active_wg_profile = lambda: ""
    app.get_wg_iface = lambda: ""
    app.killswitch_is_on = lambda: True
    app.killswitch_off = lambda **kwargs: killswitch_off_calls.append(kwargs) or True
    app.killswitch_on = lambda **kwargs: killswitch_on_calls.append(kwargs) or True
    app.vpn_switch = lambda target, ensure_sudo=True, refresh_ui=True, force_reconnect=False, skip_cleanup=False: (
        vpn_calls.append(
            {
                "target": target,
                "ensure_sudo": ensure_sudo,
                "refresh_ui": refresh_ui,
                "force_reconnect": force_reconnect,
                "skip_cleanup": skip_cleanup,
            }
        )
        or True
    )
    app.wait_for_vpn_ready = lambda timeout=15, interval=0.5: True
    app._schedule_refresh_burst = lambda delays_ms=None: logs.append("refresh-burst")
    app._schedule_pending_internet_restore_retry = lambda: logs.append("restore-retry")
    app.set_light = lambda *_args: None
    app.l_inet = object()
    app.btn_inet_off = DummyButton()
    app.btn_inet_on = DummyButton()
    app.tr = lambda _key, default=None: default
    app.debug_nm_state = lambda *_args: None
    app._debug_log_system_cmd = lambda *_args: None
    app._base_wg_profile_name = lambda profile: profile

    monkeypatch.setattr(netmon, "has_cmd", lambda name: True)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon.time, "sleep", lambda *_args: None)
    monkeypatch.setattr(netmon, "run_cmd", lambda args, timeout=0, text=True: (0, "ok"))

    assert app.internet_enable() is True
    assert killswitch_off_calls == []
    assert vpn_calls == []
    assert killswitch_on_calls == []
    assert "Killswitch bleibt während der VPN-Wiederherstellung aktiv." in logs
    assert (
        "VPN-Wiederherstellung wird nach Abschluss von Internet AN erneut versucht."
        in logs
    )
    assert "restore-retry" in logs


def test_internet_enable_schedules_retry_when_vpn_restore_stays_pending(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    delayed_callbacks = []
    async_jobs = []

    class DummyButton:
        def __init__(self):
            self.states = []

        def configure(self, **kwargs):
            self.states.append(kwargs.get("state"))

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                _run_as_other_thread(self.target)

    def fake_after(delay, callback):
        if delay == 0:
            original_get_ident = netmon.threading.get_ident
            owner_thread_id = app.__dict__.get("_network_op_owner")
            if owner_thread_id is not None:
                netmon.threading.get_ident = lambda: owner_thread_id
            try:
                callback()
            finally:
                netmon.threading.get_ident = original_get_ident
        else:
            delayed_callbacks.append((delay, callback))

    app.network_ops_lock = threading.RLock()
    app.network_active_operation = ""
    app._network_op_owner = None
    app._network_op_depth = 0
    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": True,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    app.vpn_before_internet_off = "proton"
    app.internet_restore_retry_count = 0
    app.internet_vpn_restore_active = False
    app.log = logs.append
    app.log_safe = logs.append
    app.log_debug_safe = logs.append
    app.after = fake_after
    app.run_async = lambda func, job_name="": async_jobs.append((job_name, func))
    app.ensure_sudo_session = lambda message: True
    app._confirm_danger_action = lambda *args, **kwargs: True
    app._state_coordinator = lambda: None
    app._clear_internet_suspend_request = lambda: None
    app._log_internet_toggle_state = lambda _label: None
    app.wait_for_network_ready = lambda timeout=20: True
    app.cleanup_wireguard_interfaces = lambda: True
    app._base_wg_profile_name = lambda profile: profile
    app.active_wg_profile = lambda: ""
    app.get_wg_iface = lambda: ""
    app.vpn_switch = lambda *args, **kwargs: True
    app.wait_for_vpn_ready = lambda timeout=15, interval=0.5: False
    app.killswitch_is_on = lambda: True
    app.killswitch_off = lambda **kwargs: True
    app.killswitch_on = lambda **kwargs: True
    app._schedule_refresh_burst = lambda delays_ms=None: logs.append("refresh-burst")
    app.set_light = lambda *_args: None
    app.l_inet = object()
    app.btn_inet_off = DummyButton()
    app.btn_inet_on = DummyButton()
    app.tr = lambda _key, default=None: default
    app.debug_nm_state = lambda *_args: None
    app._debug_log_system_cmd = lambda *_args: None

    monkeypatch.setattr(netmon, "has_cmd", lambda name: True)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon.time, "sleep", lambda *_args: None)
    monkeypatch.setattr(netmon, "run_cmd", lambda args, timeout=0, text=True: (0, "ok"))

    assert app.internet_enable() is True
    assert delayed_callbacks
    assert delayed_callbacks[0][0] == 6000
    assert app.internet_restore_retry_count == 1
    assert app.internet_vpn_restore_active is True
    assert async_jobs == []
    assert (
        "VPN-Wiederherstellung: erneuter Versuch geplant (1/3, Profil: proton)." in logs
    )

    delayed_callbacks[0][1]()

    assert async_jobs
    assert async_jobs[0][0] == "Internet AN VPN-Restore Retry"


def test_internet_enable_restores_previous_vpn_after_network_ready(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    vpn_calls = []

    class DummyButton:
        def __init__(self):
            self.states = []

        def configure(self, **kwargs):
            self.states.append(kwargs.get("state"))

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                _run_as_other_thread(self.target)

    app.network_ops_lock = threading.RLock()
    app.network_active_operation = ""
    app._network_op_owner = None
    app._network_op_depth = 0
    app.log = logs.append
    app.log_safe = logs.append
    app.after = lambda _delay, callback: callback()
    app.ensure_sudo_session = lambda message: True
    app._confirm_danger_action = lambda *args, **kwargs: True
    app._clear_internet_suspend_request = lambda: setattr(
        app, "internet_suspend_requested", False
    )
    app.internet_suspend_state = {
        "ufw_was_active": False,
        "killswitch_was_active": False,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }
    app._state_coordinator = lambda: None
    app._log_internet_toggle_state = lambda _label: None
    app.wait_for_network_ready = lambda timeout=20: True
    app.cleanup_wireguard_interfaces = lambda: True
    app.vpn_before_internet_off = "proton"
    app.active_wg_profile = lambda: ""
    app.get_wg_iface = lambda: ""
    app.killswitch_is_on = lambda: False
    app.wait_for_vpn_ready = lambda timeout=15, interval=0.5: True
    app.vpn_switch = lambda target, ensure_sudo=True, refresh_ui=True, force_reconnect=False, skip_cleanup=False: (
        vpn_calls.append(
            {
                "target": target,
                "ensure_sudo": ensure_sudo,
                "refresh_ui": refresh_ui,
                "force_reconnect": force_reconnect,
                "skip_cleanup": skip_cleanup,
            }
        )
        or True
    )
    app._schedule_refresh_burst = lambda delays_ms=None: logs.append("refresh-burst")
    app._schedule_pending_internet_restore_retry = lambda: logs.append("restore-retry")
    app.set_light = lambda *_args: None
    app.l_inet = object()
    app.btn_inet_off = DummyButton()
    app.btn_inet_on = DummyButton()
    app.tr = lambda _key, default=None: default
    app.debug_nm_state = lambda *_args: None
    app._debug_log_system_cmd = lambda *_args: None
    app._base_wg_profile_name = lambda profile: profile

    monkeypatch.setattr(netmon, "has_cmd", lambda name: True)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "run_cmd", lambda args, timeout=0, text=True: (0, "ok"))

    assert app.internet_enable() is True
    assert vpn_calls == []
    assert app.vpn_before_internet_off == "proton"
    assert (
        "VPN-Wiederherstellung wird nach Abschluss von Internet AN erneut versucht."
        in logs
    )
    assert "restore-retry" in logs
    assert "refresh-burst" in logs


def test_isp_stealth_on_restores_previous_state_when_dns_apply_fails(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    states = []
    restored = []
    killswitch_calls = []

    class DummyVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    app.isp_stealth_running = False
    app.isp_stealth_lock = threading.Lock()
    app.isp_stealth_runtime_state = None
    app.ensure_sudo_session = lambda message: True
    app.isp_stealth_disable_ipv6 = DummyVar(True)
    app.isp_stealth_enable_killswitch = DummyVar(True)
    app.isp_stealth_vpn_profile = DummyVar("proton")
    app.isp_stealth_dns_profile = DummyVar("Cloudflare (1.1.1.1)")
    app._capture_stealth_runtime_state = lambda: {
        "ipv6_was_disabled": False,
        "killswitch_was_on": False,
        "vpn_was_active": False,
        "vpn_profile": "",
        "dns_choice": "System (DHCP/auto)",
    }
    app._restore_stealth_runtime_state = (
        lambda state, refresh_ui=False: restored.append((state, refresh_ui))
    )
    app.ipv6_disable = lambda refresh_ui=False: True
    app.vpn_switch = lambda *args, **kwargs: True
    app.wait_for_vpn_ready = lambda timeout=12, interval=0.5: True
    app.killswitch_is_on = lambda: False
    app.killswitch_on = lambda **kwargs: killswitch_calls.append(kwargs) or True
    app._set_dns_choice_safe = lambda choice: None
    app.apply_dns = lambda **kwargs: False
    app.after = lambda _delay, callback: callback()
    app._set_stealth_enabled_state = lambda enabled: states.append(enabled)
    app.log_safe = logs.append
    app.refresh_safe = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None

    app.isp_stealth_on()

    assert restored == [
        (
            {
                "ipv6_was_disabled": False,
                "killswitch_was_on": False,
                "vpn_was_active": False,
                "vpn_profile": "",
                "dns_choice": "System (DHCP/auto)",
            },
            False,
        )
    ]
    assert states == [False]
    assert app.isp_stealth_runtime_state is None
    assert killswitch_calls == [
        {"async_mode": False, "ensure_sudo": False, "refresh_ui": False}
    ]
    assert any("Vorzustand wiederhergestellt" in entry for entry in logs)


def test_isp_stealth_on_accepts_system_auto_dns_with_active_vpn(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    states = []
    dns_choices = []

    class DummyVar:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    previous_state = {
        "ipv6_was_disabled": False,
        "killswitch_was_on": False,
        "vpn_was_active": False,
        "vpn_profile": "",
        "dns_choice": "System (DHCP/auto)",
    }

    app.isp_stealth_running = False
    app.isp_stealth_lock = threading.Lock()
    app.isp_stealth_runtime_state = None
    app.ensure_sudo_session = lambda message: True
    app.isp_stealth_enabled = DummyVar(True)
    app.isp_stealth_disable_ipv6 = DummyVar(False)
    app.isp_stealth_enable_killswitch = DummyVar(False)
    app.isp_stealth_vpn_profile = DummyVar("proton")
    app.isp_stealth_dns_profile = DummyVar("System (DHCP/auto)")
    app._capture_stealth_runtime_state = lambda: dict(previous_state)
    app.vpn_switch = lambda *args, **kwargs: True
    app.wait_for_vpn_ready = lambda timeout=12, interval=0.5: True
    app._set_dns_choice_safe = lambda choice: dns_choices.append(choice)
    app.apply_dns = lambda **kwargs: (_ for _ in ()).throw(
        AssertionError("apply_dns should not run for stealth auto/VPN DNS")
    )
    app.after = lambda _delay, callback: callback()
    app._set_stealth_enabled_state = lambda enabled: states.append(enabled)
    app.log_safe = logs.append
    app.refresh_safe = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None

    app.isp_stealth_on()

    assert dns_choices == ["System (DHCP/auto)"]
    assert states == [True]
    assert app.isp_stealth_runtime_state == previous_state
    assert "DNS wird im Stealthmodus vom VPN-Profil verwaltet." in logs
    assert "ISP-Stealthmodus aktiviert." in logs


def test_killswitch_is_on_requires_more_than_default_policy(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.get_wg_interfaces = lambda: ["wg0"]
    app.get_killswitch_vpn_endpoints = lambda: [("66.234.146.66", "51820")]

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, "\n".join(
                [
                    "Status: active",
                    "Default: deny (incoming), deny (outgoing), disabled (routed)",
                ]
            )
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app.killswitch_is_on() is False


def test_killswitch_is_on_rejects_global_web_or_dns_allow_rules(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.get_wg_interfaces = lambda: ["wg0"]
    app.get_killswitch_vpn_endpoints = lambda: [("66.234.146.66", "51820")]

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, "\n".join(
                [
                    "Status: active",
                    "Default: deny (incoming), deny (outgoing), disabled (routed)",
                    "Anywhere on lo ALLOW IN Anywhere",
                    "Anywhere ALLOW OUT Anywhere on lo",
                    "Anywhere ALLOW IN on wg0 Anywhere",
                    "Anywhere ALLOW OUT on wg0 Anywhere",
                    "66.234.146.66 51820/udp ALLOW OUT Anywhere",
                    "443/tcp ALLOW OUT Anywhere",
                ]
            )
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app.killswitch_is_on() is False


def test_killswitch_on_sync_fails_when_postcondition_verification_fails(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    logs = []
    app.get_wg_interfaces = lambda: ["wg0"]
    app.get_killswitch_vpn_endpoints = lambda: [("66.234.146.66", "51820")]
    app.log_safe = logs.append
    app.refresh_safe = lambda: None

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_on_status(wg_ifaces=["wg0"])
        if args == ["sudo", "-n", "ufw", "status", "numbered"]:
            return 0, "Status: active"
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._killswitch_on_sync(refresh_ui=False) is False
    assert any("Aktivierung unvollstaendig" in entry for entry in logs)


def test_killswitch_off_sync_fails_when_rules_remain_present(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    logs = []
    app.log_safe = logs.append
    app.refresh_safe = lambda: None
    app.get_wg_interfaces = lambda: ["wg0"]
    app.list_wg_profiles = lambda: ["wg0"]
    app.get_killswitch_vpn_endpoints = lambda: [("66.234.146.66", "51820")]

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args == ["sudo", "-n", "ufw", "status", "verbose"]:
            return 0, _ufw_verbose_killswitch_on_status(
                wg_ifaces=["wg0"],
                handshake_rules=[("66.234.146.66", "51820")],
            )
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._killswitch_off_sync(refresh_ui=False) is False
    assert any("Deaktivierung unvollstaendig" in entry for entry in logs)


def test_recover_preserving_killswitch_reasserts_when_killswitch_active():
    app = netmon.App.__new__(netmon.App)
    events = []
    app.killswitch_is_on = lambda: True
    app._killswitch_on_sync = (
        lambda refresh_ui=True: events.append(("sync", refresh_ui)) or True
    )
    app._recover_firewall_after_killswitch_failure = lambda: events.append("open")

    app._recover_firewall_preserving_killswitch()

    # Aktiver Killswitch: deny-outgoing wird per Re-Sync erhalten,
    # NICHT auf allow-outgoing geoeffnet.
    assert events == [("sync", False)]


def test_recover_preserving_killswitch_opens_when_killswitch_inactive():
    app = netmon.App.__new__(netmon.App)
    events = []
    app.killswitch_is_on = lambda: False
    app._killswitch_on_sync = (
        lambda refresh_ui=True: events.append(("sync", refresh_ui)) or True
    )
    app._recover_firewall_after_killswitch_failure = lambda: events.append("open")

    app._recover_firewall_preserving_killswitch()

    # Ohne aktiven Killswitch wird wie bisher auf allow-outgoing zurueckgesetzt,
    # damit sich der Nutzer nicht selbst aussperrt.
    assert events == ["open"]


def test_vpn_switch_empty_target_preserves_active_killswitch(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.debug_nm_state = lambda reason: None
    events = []
    app.log_safe = lambda *args: None
    app.log_debug = lambda *args: None
    app.tr = lambda key, default, **kwargs: default
    app.refresh_safe = lambda: None
    app._try_begin_network_operation = lambda label: True
    app.killswitch_is_on = lambda: True
    app._killswitch_on_sync = (
        lambda refresh_ui=True: events.append(("sync", refresh_ui)) or True
    )
    app._recover_firewall_after_killswitch_failure = lambda: events.append("open")

    assert app.vpn_switch("", ensure_sudo=False, refresh_ui=True) is False
    # Fehlgeschlagener Slot-Wechsel bei aktivem Killswitch darf die
    # Firewall nicht still oeffnen.
    assert events == [("sync", False)]
    assert "open" not in events
