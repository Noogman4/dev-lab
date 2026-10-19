import inspect
import subprocess
import sys

import pytest

from tools import netmon


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyWidget:
    def __init__(self):
        self.config = {}

    def configure(self, **kwargs):
        self.config.update(kwargs)

    def bind(self, *_args, **_kwargs):
        return None


class DummyLabel:
    def __init__(self):
        self.config = {}

    def configure(self, **kwargs):
        self.config.update(kwargs)


class DummyTkLabel:
    def __init__(self):
        self.values = {}

    def config(self, **kwargs):
        self.values.update(kwargs)


class DummyCombo:
    def __init__(self):
        self.values = None

    def __setitem__(self, key, value):
        if key == "values":
            self.values = value
        else:
            raise KeyError(key)


class ImmediateThread:
    def __init__(self, target=None, daemon=None, args=None, kwargs=None, **_extra):
        self.target = target
        self.args = tuple(args or ())
        self.kwargs = dict(kwargs or {})

    def start(self):
        if self.target is not None:
            self.target(*self.args, **self.kwargs)


@pytest.fixture
def passive_dns_status(monkeypatch, request):
    """Opt-in status response; every other command retains its real guard."""
    original_run_cmd = netmon.dns_controller.run_cmd
    calls = []
    status = getattr(request, "param", "Global\n    DNS Servers: 192.0.2.53\n")

    def status_only(args, *positional, **kwargs):
        if args == ["resolvectl", "status"]:
            calls.append((list(args), kwargs.get("timeout")))
            return 0, status
        return original_run_cmd(args, *positional, **kwargs)

    monkeypatch.setattr(netmon.dns_controller, "run_cmd", status_only)
    return calls


@pytest.fixture
def passive_dns_service(monkeypatch, passive_dns_status):
    """Bind the existing status dispatcher only to an explicit test instance."""

    def bind(app):
        service = app._dns_control_service()
        # Preserve the same real fallback for commands other than exact status.
        assert service.run_cmd is netmon.run_cmd
        monkeypatch.setattr(service, "run_cmd", netmon.dns_controller.run_cmd)
        monkeypatch.setattr(service, "get_wireguard_interfaces", lambda: set())
        return service

    return bind


@pytest.mark.parametrize("route", ["controller", "service"])
@pytest.mark.parametrize(
    "command", [["sudo", "-n", "true"], ["resolvectl", "status", "--no-pager"]]
)
def test_passive_dns_status_preserves_unexpected_command_guard(
    tmp_path, passive_dns_status, command, route
):
    assert netmon.dns_controller.run_cmd(["resolvectl", "status"], timeout=8) == (
        0,
        "Global\n    DNS Servers: 192.0.2.53\n",
    )
    assert passive_dns_status == [(["resolvectl", "status"], 8)]

    # Keep the real guard and its failure accounting intact in a child session.
    # Even a caller swallowing the exception must leave that session failing.
    child_test = tmp_path / "test_expected_guard_block.py"
    child_test.write_text(
        "from tests.test_netmon_dns_consistency import passive_dns_status, passive_dns_service\n"
        "from tools import netmon\n\n"
        "def test_expected_guard_block(passive_dns_status, passive_dns_service):\n"
        "    app = netmon.App.__new__(netmon.App)\n"
        "    service = passive_dns_service(app)\n"
        "    try:\n"
        f"        {('service' if route == 'service' else 'netmon.dns_controller')}.run_cmd({command!r})\n"
        "    except Exception:\n"
        "        pass\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-p",
            "tests.conftest",
            "-q",
            "--tb=short",
            "--basetemp",
            str(tmp_path / "child-tmp"),
            str(child_test),
        ],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Blocked host accesses:" in result.stdout
    assert f"'command', '{command[0]}'" in result.stdout
    assert passive_dns_status == [(["resolvectl", "status"], 8)]


def test_dns_consistency_logs_killswitch_hint_and_http_blocked(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.dns_consistency_enabled = True
    app.dns_consistency_running = False
    app.last_dns_consistency_ts = 0.0
    app.last_dns_consistency_ok = None
    app.dns_choice = DummyVar("TestDNS")
    app.killswitch_is_on = lambda: True
    app.active_wg_profile = lambda: None
    app.after = lambda delay, callback: callback()
    app.log = logs.append
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: logs.extend(text.splitlines())

    monkeypatch.setattr(netmon, "DNS_PROFILES", {"TestDNS": ["1.1.1.1"]})
    monkeypatch.setattr(
        netmon,
        "has_cmd",
        lambda name: name in {"dig", "curl"},
    )
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    def fake_run_cmd(args, timeout=0, text=True):
        if args[:5] == ["dig", "+time=2", "+tries=1", "+short", "A"]:
            return 0, "93.184.216.34\n"
        if args[:4] == ["curl", "-fsS", "--max-time", "4"]:
            return 7, ""
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    app.dns_consistency_check_async(force=True)

    assert "✔ DNS-Auflösung: STABIL" in logs
    assert "✖ HTTP-Test: blockiert" in logs
    assert (
        "Hinweis: Killswitch ist AN – ohne VPN evtl. kein Internet (gewollt)." in logs
    )
    assert app.last_dns_consistency_ok is True
    assert app.dns_consistency_running is False


def test_dns_consistency_normalizes_manual_dns_hostname_for_explicit_query(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    commands = []

    app.dns_consistency_enabled = True
    app.dns_consistency_running = False
    app.last_dns_consistency_ts = 0.0
    app.last_dns_consistency_ok = None
    app.dns_choice = DummyVar("8.8.8.8#dns.google")
    app.killswitch_is_on = lambda: False
    app.active_wg_profile = lambda: None
    app.after = lambda delay, callback: callback()
    app.log = lambda _msg: None
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: None

    monkeypatch.setattr(netmon, "DNS_PROFILES", {"System (DHCP/auto)": None})
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "dig")
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    def fake_run_cmd(args, timeout=0, text=True):
        commands.append(args)
        if args[:5] == ["dig", "+time=2", "+tries=1", "+short", "A"]:
            return 0, "93.184.216.34\n"
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    app.dns_consistency_check_async(force=True)

    assert any("@8.8.8.8" in arg for cmd in commands for arg in cmd)
    assert all("@8.8.8.8#dns.google" not in arg for cmd in commands for arg in cmd)


def test_build_dot_dropin_uses_tls_hostnames():
    app = netmon.App.__new__(netmon.App)
    app.dot_choice = DummyVar("Cloudflare")
    app.get_preferred_dnssec_mode = lambda: "standard"

    profile_name, profile, content = app._build_dot_dropin_content()

    assert profile_name == "Cloudflare"
    assert profile["hostname"] == "cloudflare-dns.com"
    assert "DNS=1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com" in content


def test_write_manual_dns_dropin_uses_plain_dns_for_custom_server(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    written = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.get_preferred_dnssec_mode = lambda: "standard"
    app._dns_servers_for_choice = lambda choice: ["8.8.8.8"]
    app._write_dot_dropin_text = lambda content: written.append(content) or (
        True,
        content,
    )

    success, _detail = app._write_manual_dns_dropin("8.8.8.8")

    assert success is True
    assert written
    assert "DNS=8.8.8.8" in written[0]
    assert "DNSOverTLS=no" in written[0]
    assert "DNSSEC=allow-downgrade" in written[0]
    assert "Domains=~." in written[0]


def test_write_manual_dns_dropin_preserves_custom_hostname(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    written = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.get_preferred_dnssec_mode = lambda: "standard"
    app._dns_servers_for_choice = lambda choice: ["8.8.8.8#dns.google"]
    app._write_dot_dropin_text = lambda content: written.append(content) or (
        True,
        content,
    )

    success, _detail = app._write_manual_dns_dropin("8.8.8.8#dns.google")

    assert success is True
    assert written
    assert "DNS=8.8.8.8#dns.google" in written[0]
    assert "DNSOverTLS=no" in written[0]


def test_build_dot_dropin_uses_strict_dnssec_when_preferred():
    app = netmon.App.__new__(netmon.App)
    app.dot_choice = DummyVar("Cloudflare")
    app.get_preferred_dnssec_mode = lambda: "strict"

    _profile_name, _profile, content = app._build_dot_dropin_content()

    assert "DNSSEC=yes" in content


def test_on_light_click_routes_to_matching_tabs():
    app = netmon.App.__new__(netmon.App)
    events = []

    class DummyNotebook:
        def select(self, tab):
            events.append(("select", tab))

    app.nb = DummyNotebook()
    app.tab_dns = object()
    app.tab_conn = object()
    app.tab_security = object()
    app.tab_lynis = object()
    app.tab_lynis_hardening = object()
    app.tab_path_guard = object()
    app.tab_system = object()
    app.tab_vpn_slots = object()
    app._select_system_tab = lambda tab: events.append(("system", tab))
    app._select_security_tab = lambda tab: events.append(("security", tab))
    app.lynis_sections = DummyNotebook()
    app.show_dns_guard_details = lambda: events.append(("dns_guard", None))
    app.open_startup_guard_tab = lambda: events.append(("startup", None))

    app.on_light_click("dns")
    app.on_light_click("connections")
    app.on_light_click("ufw")
    app.on_light_click("ufw_logging")
    app.on_light_click("security")
    app.on_light_click("killswitch")
    app.on_light_click("ssh")
    app.on_light_click("path_guard")
    app.on_light_click("vpn")
    app.on_light_click("ipv6")
    app.on_light_click("dot")
    app.on_light_click("dns_guard")
    app.on_light_click("startup_guard")
    app.on_light_click("game_mode")

    assert events == [
        ("select", app.tab_dns),
        ("select", app.tab_conn),
        ("security", app.tab_security),
        ("security", app.tab_security),
        ("security", app.tab_security),
        ("security", app.tab_security),
        ("security", app.tab_security),
        ("security", app.tab_path_guard),
        ("system", app.tab_vpn_slots),
        ("system", app.tab_system),
        ("select", app.tab_dns),
        ("dns_guard", None),
        ("startup", None),
        ("security", app.tab_lynis),
        ("select", app.tab_lynis_hardening),
    ]


def test_dns_ui_source_contains_dnssec_mode_selector_near_dns_controls():
    source = inspect.getsource(netmon.App.__init__)

    assert 'self.tr("settings_dnssec_mode_label", "DNSSEC Modus:")' in source
    assert "textvariable=self.var_dnssec_mode" in source
    assert 'self.tr("btn_apply_dnssec_mode", "DNSSEC-Modus anwenden")' in source


def test_update_dns_header_falls_back_to_active_resolver_dns():
    app = netmon.App.__new__(netmon.App)
    app.nm_dns_header_var = DummyVar("")
    app.get_default_iface = lambda: "enp4s0"
    app.nm_get_dns_list = lambda iface: []
    app.get_active_dns_servers = lambda: ["1.1.1.1", "1.0.0.1"]
    app.public_ip = "198.51.100.42"
    app.country = "DE"

    app.update_dns_header()

    assert (
        app.nm_dns_header_var.get()
        == "NM DNS (enp4s0): 1.1.1.1, 1.0.0.1 | IP: 198.51.100.42 | Land: DE"
    )


def test_parse_dot_resolvectl_status_extracts_mode_and_servers():
    app = netmon.App.__new__(netmon.App)
    parsed = app._parse_dot_resolvectl_status("""
Global
         Protocols: +LLMNR +mDNS +DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 1.1.1.1#cloudflare-dns.com
       DNS Servers: 1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com
""")

    assert parsed["mode"] == "yes"
    assert parsed["current_server"] == "1.1.1.1"
    assert parsed["servers"] == ["1.1.1.1", "1.0.0.1"]


def test_set_dot_state_updates_status_labels():
    app = netmon.App.__new__(netmon.App)
    app.dot_choice = DummyVar("Cloudflare")
    app.dot_status_var = DummyVar()
    app.dot_server_var = DummyVar()
    app.dot_mode_var = DummyVar()
    app.dot_profile_var = DummyVar()
    app.dot_last_test_var = DummyVar()
    app._update_dot_light = lambda: None

    app._set_dot_state(
        True,
        profile="Cloudflare",
        servers=["1.1.1.1", "1.0.0.1"],
        mode="yes",
        enabled=True,
        timestamp=1710000000,
    )

    assert app.dot_enabled is True
    assert app.dot_last_test_ok is True
    assert app.dot_choice.get() == "Cloudflare"
    assert app.dot_status_var.get() == "DoT: aktiv / Test ok"
    assert app.dot_profile_var.get() == "Profil: Cloudflare"
    assert app.dot_server_var.get() == "Server: 1.1.1.1, 1.0.0.1"
    assert app.dot_mode_var.get() == "Modus: yes"
    assert app.dot_last_test_var.get().startswith("Letzter Test: ")


def test_set_dot_state_marks_vpn_conflict():
    app = netmon.App.__new__(netmon.App)
    app.dot_choice = DummyVar("Cloudflare")
    app.dot_status_var = DummyVar()
    app.dot_server_var = DummyVar()
    app.dot_mode_var = DummyVar()
    app.dot_profile_var = DummyVar()
    app.dot_last_test_var = DummyVar()
    app.dot_vpn_conflict = False
    app._update_dot_light = lambda: None

    app._set_dot_state(
        True,
        profile="Cloudflare",
        servers=["1.1.1.1"],
        mode="yes",
        enabled=True,
        vpn_conflict=True,
        timestamp=1710000000,
    )

    assert app.dot_vpn_conflict is True
    assert app.dot_status_var.get() == "DoT: aktiv, aber VPN-Konflikt"


def test_show_dot_status_result_startup_stays_silent_for_dns_output_and_chad():
    app = netmon.App.__new__(netmon.App)
    app.update_dns_controls_state_safe = lambda: None
    outputs = []
    chad = []

    app.dot_choice = DummyVar("Cloudflare")
    app.dot_status_var = DummyVar()
    app.dot_server_var = DummyVar()
    app.dot_mode_var = DummyVar()
    app.dot_profile_var = DummyVar()
    app.dot_last_test_var = DummyVar()
    app.dot_test_hint_var = DummyVar()
    app._update_dot_light = lambda: None
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.append_to_chad_output = lambda title, text: chad.append((title, text))
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()

    app._show_dot_status_result(
        {
            "ok": None,
            "enabled": True,
            "profile": "Cloudflare",
            "servers": ["1.1.1.1"],
            "mode": "yes",
            "vpn_conflict": True,
            "vpn_active": True,
            "text": "DoT startup text",
        },
        startup=True,
    )

    assert outputs == []
    assert chad == []
    assert app.dot_last_test_var.get() == "Letzter Test: Startprüfung"
    assert app.dot_status_var.get() == "DoT: aktiv, aber VPN-Konflikt"
    assert app.dot_test_hint_var.get() == ""


def test_detect_netmon_dot_dropin_conflict(tmp_path):
    app = netmon.App.__new__(netmon.App)
    dropin = tmp_path / "netmon-dot.conf"
    dropin.write_text(
        "[Resolve]\nDNS=1.1.1.1#cloudflare-dns.com\nDomains=~.\n",
        encoding="utf-8",
    )

    conflict, content = app.detect_netmon_dot_dropin_conflict(str(dropin))

    assert conflict is True
    assert "DNS=1.1.1.1" in content


def test_analyze_dns_health_reports_dot_vpn_conflict(monkeypatch, tmp_path):
    app = netmon.App.__new__(netmon.App)
    dropin = tmp_path / "netmon-dot.conf"
    dropin.write_text(
        "[Resolve]\nDNS=1.1.1.1#cloudflare-dns.com\nDNSOverTLS=yes\nDomains=~.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(netmon, "DOT_DROPIN_PATH", str(dropin))

    app._dns_control_service().get_wireguard_interfaces = lambda: set()

    result = app.analyze_dns_health_output("""
Link 7 (proton0)
    Protocols: +DNSOverTLS
    DNSSEC setting: allow-downgrade
    Current DNS Server: 10.2.0.1
    DNS Servers: 10.2.0.1
""")

    assert "✔ Aktiver DNS-Server: 10.2.0.1" in result
    assert "✔ DNS-over-TLS: aktiv" in result
    assert "○ DNSSEC: aktiv (Fallback möglich)" in result
    assert "✖ DNS-Konfiguration auffällig" in result
    assert "Protocols:" not in result
    assert "Link 7" not in result


def test_enable_dot_blocks_when_vpn_dns_active(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.update_dns_controls_state_safe = lambda: None
    outputs = []
    chad = []
    logs = []
    warnings = []

    app.dot_running = False
    app.tab_dns = object()
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.is_vpn_dns_active = lambda: (True, "Link 7 (proton0)\nDNS Servers: 10.2.0.1")
    app.ensure_sudo_session = lambda reason: (_ for _ in ()).throw(
        AssertionError("sudo must not be requested when VPN DNS is active")
    )
    app.update_dns_output = lambda text, append=False: outputs.append(text)
    app.append_to_chad_output = lambda title, text: chad.append((title, text))
    app.log_safe = logs.append
    app._update_dot_light = lambda: None

    monkeypatch.setattr(
        netmon.messagebox,
        "showwarning",
        lambda title, message, parent=None: warnings.append((title, message)),
    )

    app.enable_dot_async()

    assert warnings and warnings[0][0] == "DoT blockiert"
    assert app.dot_vpn_conflict is True
    assert app.dot_last_test_ok is None
    assert "Aktivierung blockiert" in outputs[0]
    assert chad == []
    assert logs == ["DoT-Aktivierung blockiert: VPN-DNS aktiv"]


def test_enforce_dns_policy_prefers_vpn_when_active(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.is_vpn_active = lambda: True
    monkeypatch.setattr(
        netmon.dns_controller,
        "use_vpn_dns",
        lambda _app: (True, "vpn dns"),
    )
    monkeypatch.setattr(
        netmon.dns_controller,
        "use_user_dns",
        lambda _app: (True, "manual dns"),
    )

    assert app.enforce_dns_policy() == (True, "vpn dns")


def test_enforce_dns_policy_uses_user_dns_without_vpn(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.is_vpn_active = lambda: False
    monkeypatch.setattr(
        netmon.dns_controller,
        "use_vpn_dns",
        lambda _app: (True, "vpn dns"),
    )
    monkeypatch.setattr(
        netmon.dns_controller,
        "use_user_dns",
        lambda _app: (True, "manual dns"),
    )

    assert app.enforce_dns_policy() == (True, "manual dns")


def test_refresh_dns_policy_status_reports_foreign_dns_conflict(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.dns_resolver_status_var = DummyVar("")
    app.dns_conflict_status_var = DummyVar("")

    monkeypatch.setattr(
        netmon.dns_controller,
        "run_cmd",
        lambda args, timeout=0: (0, "resolver status"),
    )
    monkeypatch.setattr(
        netmon.dns_controller,
        "evaluate_dns_policy",
        lambda _app, _out: {
            "resolver": "VPN (10.2.0.1)",
            "resolver_label": "VPN (10.2.0.1)",
            "conflicts": "",
            "vpn_active": True,
            "active_dns": ["10.2.0.1", "1.1.1.1"],
            "dot_dropin_exists": False,
            "dot_dropin_conflict": False,
            "conflict": True,
            "risk": "hoch",
            "warnings": [
                "VPN ist aktiv, aber zusätzlich wurden öffentliche/globale DNS-Server erkannt."
            ],
        },
    )

    status = app.refresh_dns_policy_status()

    assert status["conflicts"] == "Fremde DNS erkannt"
    assert app.dns_resolver_status_var.get() == "Aktiver Resolver: VPN (10.2.0.1)"
    assert app.dns_conflict_status_var.get() == "Konflikte: Fremde DNS erkannt"


def test_apply_vpn_dns_policy_prefers_vpn_dns_when_vpn_active(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.evaluate_dns_policy = lambda _out: {
        "vpn_active": True,
        "vpn_dns": ["10.2.0.1"],
    }
    app.use_vpn_dns = lambda: (True, "vpn dns")

    monkeypatch.setattr(netmon, "run_cmd", lambda args, timeout=0: (0, "status"))

    assert app.apply_vpn_dns_policy() == (True, "vpn dns")


def test_use_user_dns_blocks_when_vpn_active():
    app = netmon.App.__new__(netmon.App)
    app.is_vpn_active = lambda: True
    app.refresh_dns_policy_status = lambda: None

    success, result = app.use_user_dns()

    assert success is False
    assert "blockiert" in result
    assert "VPN ist aktiv" in result


def test_manual_dns_choice_preserves_system_auto(monkeypatch):
    app = netmon.App.__new__(netmon.App)

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.dns_choice = DummyVar("System (DHCP/auto)")

    assert app._manual_dns_choice() == "System (DHCP/auto)"
    assert app.get_selected_user_dns() == []


def test_manual_dns_choice_accepts_custom_ip_and_updates_combo(monkeypatch):
    app = netmon.App.__new__(netmon.App)

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.dns_choice = DummyVar("8.8.8.8")
    app.dns_combo = DummyCombo()
    app.custom_dns_profile_choices = []

    assert app._manual_dns_choice() == "8.8.8.8"
    assert app.get_selected_user_dns() == ["8.8.8.8"]
    assert "8.8.8.8" in app.custom_dns_profile_choices
    assert "8.8.8.8" in app.dns_combo.values


def test_manual_dns_choice_accepts_custom_ip_with_hostname_and_updates_combo(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.dns_choice = DummyVar("8.8.8.8#dns.google")
    app.dns_combo = DummyCombo()
    app.custom_dns_profile_choices = []

    assert app._manual_dns_choice() == "8.8.8.8#dns.google"
    assert app.get_selected_user_dns() == ["8.8.8.8#dns.google"]
    assert "8.8.8.8#dns.google" in app.custom_dns_profile_choices
    assert "8.8.8.8#dns.google" in app.dns_combo.values


def test_manual_dns_choice_falls_back_to_system_for_unknown_profile(monkeypatch):
    app = netmon.App.__new__(netmon.App)

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.dns_choice = DummyVar("Unbekanntes Profil")

    assert app._manual_dns_choice() == "System (DHCP/auto)"


def test_add_manual_dns_server_selects_and_clears_entry(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.manual_dns_entry_var = DummyVar("9.9.9.9")
    app.dns_choice = DummyVar("System (DHCP/auto)")
    app.dns_combo = DummyCombo()
    app.custom_dns_profile_choices = []
    app.log_safe = logs.append
    app.tr = lambda _key, fallback=None: fallback or _key
    app._set_dns_choice_safe = lambda choice: app.dns_choice.set(choice)

    assert app.add_manual_dns_server() is True
    assert app.manual_dns_entry_var.get() == ""
    assert app.dns_choice.get() == "9.9.9.9"
    assert logs == ["Manueller DNS zur Auswahl hinzugefügt: 9.9.9.9"]
    assert "9.9.9.9" in app.dns_combo.values


def test_add_manual_dns_server_accepts_ip_and_hostname(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.manual_dns_entry_var = DummyVar("9.9.9.9 dns.quad9.net")
    app.dns_choice = DummyVar("System (DHCP/auto)")
    app.dns_combo = DummyCombo()
    app.custom_dns_profile_choices = []
    app.log_safe = logs.append
    app.tr = lambda _key, fallback=None: fallback or _key
    app._set_dns_choice_safe = lambda choice: app.dns_choice.set(choice)

    assert app.add_manual_dns_server() is True
    assert app.manual_dns_entry_var.get() == ""
    assert app.dns_choice.get() == "9.9.9.9#dns.quad9.net"
    assert logs == ["Manueller DNS zur Auswahl hinzugefügt: 9.9.9.9#dns.quad9.net"]
    assert "9.9.9.9#dns.quad9.net" in app.dns_combo.values


def test_remove_manual_dns_server_resets_selection(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )
    app.dns_choice = DummyVar("9.9.9.9")
    app.dns_combo = DummyCombo()
    app.custom_dns_profile_choices = ["9.9.9.9"]
    app.log_safe = logs.append
    app._set_dns_choice_safe = lambda choice: app.dns_choice.set(choice)

    assert app.remove_manual_dns_server("9.9.9.9") is True
    assert app.dns_choice.get() == "System (DHCP/auto)"
    assert app.custom_dns_profile_choices == []
    assert "9.9.9.9" not in app.dns_combo.values
    assert logs == ["Manueller DNS aus Auswahl entfernt: 9.9.9.9"]


def test_apply_dns_profile_choice_via_control_uses_manual_dns_flow(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )

    def fake_apply_nm_dns_policy_to_targets(*, ignore_auto_dns):
        calls.append(ignore_auto_dns)
        return True, ["Connection: enp4s0 (wired)"]

    app.dns_choice = DummyVar("Cloudflare (1.1.1.1)")
    app._apply_nm_dns_policy_to_targets = fake_apply_nm_dns_policy_to_targets
    app._write_manual_dns_dropin = lambda choice: (choice == "Cloudflare (1.1.1.1)", "")
    app._restart_resolved_for_dns_policy = lambda: (True, "")

    result = app._apply_dns_profile_choice_via_control("Cloudflare (1.1.1.1)")

    assert calls == [True]
    assert result["choice"] == "Cloudflare (1.1.1.1)"
    assert result["servers"] == ["1.1.1.1", "1.0.0.1"]
    assert result["dropin_state"] == "geschrieben"
    assert result["success"] is True


def test_apply_dns_profile_choice_via_control_supports_custom_dns(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )

    def fake_apply_nm_dns_policy_to_targets(*, ignore_auto_dns):
        calls.append(ignore_auto_dns)
        return True, ["Connection: enp4s0 (wired)"]

    app.dns_choice = DummyVar("8.8.8.8")
    app.custom_dns_profile_choices = ["8.8.8.8"]
    app._apply_nm_dns_policy_to_targets = fake_apply_nm_dns_policy_to_targets
    app._dns_servers_for_choice = lambda choice: ["8.8.8.8"]
    app._is_custom_dns_choice = lambda choice: choice == "8.8.8.8"
    app._register_manual_dns_choice = lambda choice: choice
    app._write_manual_dns_dropin = lambda choice: (choice == "8.8.8.8", "")
    app._restart_resolved_for_dns_policy = lambda: (True, "")
    app._read_dot_dropin = lambda: ""

    result = app._apply_dns_profile_choice_via_control("8.8.8.8")

    assert calls == [True]
    assert result["choice"] == "8.8.8.8"
    assert result["servers"] == ["8.8.8.8"]
    assert result["dropin_state"] == "geschrieben"
    assert result["success"] is True


def test_apply_dns_profile_choice_via_control_uses_auto_dns_flow(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []

    monkeypatch.setattr(
        netmon,
        "DNS_PROFILES",
        {
            "System (DHCP/auto)": None,
            "Cloudflare (1.1.1.1)": ["1.1.1.1", "1.0.0.1"],
        },
    )

    def fake_apply_nm_dns_policy_to_targets(*, ignore_auto_dns):
        calls.append(ignore_auto_dns)
        return True, ["Connection: enp4s0 (wired)"]

    app.dns_choice = DummyVar("System (DHCP/auto)")
    app._apply_nm_dns_policy_to_targets = fake_apply_nm_dns_policy_to_targets
    app._remove_manual_dns_dropin = lambda: (True, "")
    app._restart_resolved_for_dns_policy = lambda: (True, "")

    result = app._apply_dns_profile_choice_via_control("System (DHCP/auto)")

    assert calls == [False]
    assert result["choice"] == "System (DHCP/auto)"
    assert result["servers"] == []
    assert result["dropin_state"] == "entfernt"
    assert result["success"] is True


def test_format_dns_profile_control_result_compacts_normal_output():
    app = netmon.App.__new__(netmon.App)

    result = app._format_dns_profile_control_result(
        {
            "choice": "Cloudflare (1.1.1.1)",
            "servers": ["1.1.1.1", "1.0.0.1"],
            "success": True,
            "nm_details": [
                "✔ Verbindung erkannt: Ethernet-Verbindung 1 (enp4s0)",
                "✔ Auto-DNS deaktiviert (IPv4 / IPv6)",
                "✔ Manuelle DNS-Server zurückgesetzt",
                "✔ Verbindung neu gestartet",
            ],
            "dropin_ok": True,
            "dropin_detail": "",
            "dropin_state": "geschrieben",
            "restart_ok": True,
            "restart_detail": "",
        },
        heading="=== DNS anwenden ===",
        action="DNS-Profil anwenden",
    )

    assert "Server: 1.1.1.1 • 1.0.0.1" in result
    assert "[NetworkManager]" in result
    assert "[System]" in result
    assert "rc=0" not in result
    assert "sudo -n nmcli" not in result


def test_is_physical_dns_candidate_filters_virtual_interfaces():
    app = netmon.App.__new__(netmon.App)

    assert app.is_physical_dns_candidate(
        "Kabelgebundene Verbindung 2", "ethernet", "enp4s0"
    )
    assert not app.is_physical_dns_candidate("Loopback", "loopback", "lo")
    assert not app.is_physical_dns_candidate("docker bridge", "bridge", "docker0")
    assert not app.is_physical_dns_candidate("veth123", "ethernet", "veth123")
    assert not app.is_physical_dns_candidate("protonvpn", "wireguard", "wg0")


def test_active_nm_dns_targets_only_returns_physical_connections():
    app = netmon.App.__new__(netmon.App)
    app.get_default_iface = lambda: "enp4s0"
    app.nm_active_conn_for_dev = lambda iface: "Kabelgebundene Verbindung 2"
    app.nm_active_connections_detailed = lambda: [
        ("Kabelgebundene Verbindung 2", "enp4s0", "ethernet"),
        ("Loopback", "lo", "loopback"),
        ("docker bridge", "docker0", "bridge"),
        ("protonvpn", "wg0", "wireguard"),
        ("wifi-home", "wlp2s0", "wifi"),
    ]

    assert app._active_nm_dns_targets() == [
        ("enp4s0", "Kabelgebundene Verbindung 2"),
        ("wlp2s0", "wifi-home"),
    ]


def test_evaluate_dns_policy_flags_global_dns_with_vpn(monkeypatch, tmp_path):
    app = netmon.App.__new__(netmon.App)

    dropin = tmp_path / "netmon-dot.conf"
    dropin.write_text(
        "[Resolve]\nDNS=1.1.1.1#cloudflare-dns.com\nDNSOverTLS=yes\nDomains=~.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(netmon, "DOT_DROPIN_PATH", str(dropin))
    monkeypatch.setattr(netmon, "DOT_DROPIN_DIR", str(tmp_path))

    app._dns_control_service().get_wireguard_interfaces = lambda: set()

    evaluation = app.evaluate_dns_policy("""
Link 2 (enp4s0)
    Current DNS Server: 1.1.1.1
    DNS Servers: 1.1.1.1
Link 7 (proton0)
    Current DNS Server: 10.2.0.1
    DNS Servers: 10.2.0.1 2a07:b944::2:1
""")

    assert evaluation["vpn_active"] is True
    assert evaluation["vpn_dns"] == ["10.2.0.1", "2a07:b944::2:1"]
    assert evaluation["global_dns"] == ["1.1.1.1"]
    assert evaluation["dot_dropin_conflict"] is True
    assert evaluation["conflict"] is True
    assert evaluation["risk"] == "hoch"


def test_detect_vpn_active_ignores_non_link_text():
    app = netmon.App.__new__(netmon.App)
    app._dns_control_service().get_wireguard_interfaces = lambda: set()

    assert app.detect_vpn_active("""
Global
    DNS Domain: vpn.example.org
    Current DNS Server: 1.1.1.1
""") is False
    assert app.detect_vpn_active("""
Link 7 (proton0)
    Current DNS Server: 10.2.0.1
    DNS Servers: 10.2.0.1 2a07:b944::2:1
""") is True


def test_detect_vpn_active_recognizes_custom_wireguard_interface():
    service = netmon.DNSControlService(
        lambda args, timeout=0: (
            (0, "work0\n") if args == ["wg", "show", "interfaces"] else (0, "")
        ),
        lambda name: name == "wg",
        dot_dropin_path="/tmp/netmon-dot.conf",
        dot_dropin_dir="/tmp",
    )

    assert service.detect_vpn_active("""
Link 7 (work0)
    Current DNS Server: 10.2.0.1
    DNS Servers: 10.2.0.1 2a07:b944::2:1
""") is True


def test_find_vpn_dns_servers_recognizes_custom_wireguard_interface():
    service = netmon.DNSControlService(
        lambda args, timeout=0: (
            (0, "work0\n") if args == ["wg", "show", "interfaces"] else (0, "")
        ),
        lambda name: name == "wg",
        dot_dropin_path="/tmp/netmon-dot.conf",
        dot_dropin_dir="/tmp",
    )

    iface, servers = service.find_vpn_dns_servers("""
Link 7 (work0)
    Current DNS Server: 10.2.0.1
    DNS Servers: 10.2.0.1 2a07:b944::2:1
Link 2 (enp4s0)
    Current DNS Server: 1.1.1.1
    DNS Servers: 1.1.1.1
""")

    assert iface == "work0"
    assert servers == ["10.2.0.1", "2a07:b944::2:1"]


def test_parse_active_dns_servers_includes_continuation_lines():
    service = netmon.DNSControlService(
        lambda *_args, **_kwargs: (0, ""),
        lambda _name: False,
        dot_dropin_path="/tmp/netmon-dot.conf",
        dot_dropin_dir="/tmp",
    )

    servers = service.parse_active_dns_servers("""
Global
    DNS Servers: 1.1.1.1
                 8.8.8.8 2606:4700:4700::1111
    DNSSEC setting: no
""")

    assert servers == ["1.1.1.1", "2606:4700:4700::1111", "8.8.8.8"]


def test_parse_link_sections_stops_dns_collection_on_non_dns_line():
    service = netmon.DNSControlService(
        lambda *_args, **_kwargs: (0, ""),
        lambda _name: False,
        dot_dropin_path="/tmp/netmon-dot.conf",
        dot_dropin_dir="/tmp",
    )

    sections = service.parse_link_sections("""
Link 2 (enp4s0)
    DNS Servers: 192.168.1.1
                 1.1.1.1
    DNS Domain: lan
                 not-a-dns-token
""")

    assert sections == [
        {
            "header": "Link 2 (enp4s0)",
            "iface": "enp4s0",
            "is_vpn": False,
            "dns_servers": ["1.1.1.1", "192.168.1.1"],
            "current_dns_server": "",
        }
    ]


def test_dns_private_detection_normalizes_hostname_suffixes():
    app = netmon.App.__new__(netmon.App)
    service = app._dns_control_service()

    assert service is not None
    assert service.dns_server_is_private_or_local("10.2.0.1#vpn-dns") is True
    assert service.dns_server_is_private_or_local("fe80::1%wg0#resolver") is True
    assert service.dns_server_is_private_or_local("1.1.1.1#cloudflare-dns.com") is False


def test_dns_leak_check_reports_low_risk_for_exclusive_vpn_dns(monkeypatch, tmp_path):
    app = netmon.App.__new__(netmon.App)

    dropin = tmp_path / "netmon-dot.conf"
    monkeypatch.setattr(netmon, "DOT_DROPIN_PATH", str(dropin))
    monkeypatch.setattr(netmon, "DOT_DROPIN_DIR", str(tmp_path))

    app._dns_control_service().get_wireguard_interfaces = lambda: set()

    result = app.build_dns_leak_check_result(
        resolvectl_output="""
Link 7 (proton0)
    Current DNS Server: 10.2.0.1
    DNS Servers: 10.2.0.1 2a07:b944::2:1
""",
        dns_servers=["10.2.0.1", "2a07:b944::2:1"],
        public_ip="198.51.100.42",
    )

    assert "Leak erkannt: NEIN" in result
    assert "Status: OK / VPN-DNS exklusiv aktiv" in result
    assert "Risiko: niedrig" in result
    assert "- VPN-DNS aktiv, keine Aktion nötig" in result


def test_dns_analysis_prompt_mentions_low_risk_vpn_dns_rule():
    service = netmon.AiAnalysisService()

    prompt = service.build_prompt("DNS Leak Analyse", "VPN erkannt: JA")

    assert (
        "ausschließlich VPN-DNS gelistet ist, bewerte das Risiko als niedrig" in prompt
    )
    assert '"mittel" ist nur korrekt' in prompt


def test_run_dns_health_check_stays_in_dns_tab_without_auto_chad(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    outputs = []
    chad = []
    prepared = []
    tab_calls = []

    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: tab_calls.append(tab)}
    )()
    app.tab_dns = "dns-tab"
    app.log = logs.append
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.append_to_chad_output = lambda title, text: chad.append((title, text))
    app.prepare_chad_analysis = lambda title, text: prepared.append((title, text))
    app.after = lambda delay, callback: callback()
    app.analyze_dns_health_output = (
        lambda out: "=== DNS Health Check ===\n\n✔ Aktiver DNS-Server: 1.1.1.1"
    )

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        netmon,
        "run_cmd",
        lambda args, timeout=0: (0, "Link 2 (enp4s0)\n    DNS Servers: 1.1.1.1"),
    )

    app.run_dns_health_check()

    assert tab_calls == ["dns-tab", "dns-tab"]
    assert logs == [
        "DNS Health Check gestartet",
        "DNS Health Check abgeschlossen",
    ]
    assert outputs == [
        ("=== DNS Health Check ===\n\n✔ Aktiver DNS-Server: 1.1.1.1", True)
    ]
    assert chad == []
    assert prepared == []


def test_resolved_status_async_shows_compact_dns_status_without_raw_dump(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    outputs = []
    tab_calls = []
    logs = []

    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: tab_calls.append(tab)}
    )()
    app.tab_dns = "dns-tab"
    app.log = logs.append
    app.after = lambda delay, callback: callback()
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "resolvectl")

    def fake_run_cmd(args, timeout=0, text=True):
        if args == ["systemctl", "is-active", "systemd-resolved"]:
            return 0, "active\n"
        if args == ["resolvectl", "status"]:
            return (
                0,
                "Global\n"
                "         Protocols: +DNSOverTLS DNSSEC=allow-downgrade/supported\n"
                "Current DNS Server: 1.1.1.1#cloudflare-dns.com\n"
                "       DNS Servers: 1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com\n"
                "Link 2 (enp4s0)\n"
                "    Current Scopes: DNS\n"
                "Link 3 (docker0)\n",
            )
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    app.resolved_status_async()

    assert tab_calls == ["dns-tab", "dns-tab"]
    assert logs == ["DNS-Status aktualisiert"]
    assert outputs == [
        (
            "=== DNS Status ===\n\n"
            "✔ systemd-resolved: aktiv\n"
            "✔ Aktiver DNS: 1.1.1.1\n"
            "✔ Fallback DNS: 1.0.0.1\n"
            "✔ DNS-over-TLS: aktiv\n"
            "○ DNSSEC: aktiv (Fallback möglich)\n\n"
            "=== Ergebnis ===\n"
            "✔ DNS-System läuft stabil",
            False,
        )
    ]


def test_resolved_status_async_background_refresh_keeps_current_tab(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    tab_calls = []

    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: tab_calls.append(tab)}
    )()
    app.tab_dns = "dns-tab"
    app.log = lambda _message: None
    app.after = lambda _delay, callback: callback()
    app.update_dns_output = lambda _text, append=False: None

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "has_cmd", lambda _name: False)

    app.resolved_status_async(select_tab=False)

    assert tab_calls == []


def test_resolved_status_worker_never_schedules_tk_callback(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    scheduled = []
    workers = []
    outputs = []

    class DeferredThread:
        def __init__(self, target, daemon=True):
            self.target = target

        def start(self):
            workers.append(self.target)

    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = "dns-tab"
    app.log = lambda _message: None
    app.after = lambda delay, callback: scheduled.append((delay, callback))
    app.update_dns_output = lambda text, append=False: outputs.append(text)

    monkeypatch.setattr(netmon.threading, "Thread", DeferredThread)
    monkeypatch.setattr(netmon, "has_cmd", lambda _name: False)

    app.resolved_status_async(select_tab=False)

    assert len(workers) == 1
    assert len(scheduled) == 1

    workers[0]()

    assert len(scheduled) == 1
    _delay, show_when_ready = scheduled.pop()
    show_when_ready()
    assert outputs


def test_run_dns_leak_check_stays_in_dns_tab_without_auto_chad(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    outputs = []
    chad = []
    prepared = []
    tab_calls = []

    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: tab_calls.append(tab)}
    )()
    app.tab_dns = "dns-tab"
    app.log = logs.append
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.append_to_chad_output = lambda title, text: chad.append((title, text))
    app.prepare_chad_analysis = lambda title, text: prepared.append((title, text))
    app.after = lambda delay, callback: callback()
    app.get_public_ip = lambda: "198.51.100.42"
    app.build_dns_leak_check_result = (
        lambda resolvectl_output, dns_servers, public_ip: "=== DNS Leak Check ===\nLeak erkannt: NEIN"
    )

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        netmon,
        "run_cmd",
        lambda args, timeout=0: (0, "Link 7 (wg0)\n    DNS Servers: 10.2.0.1"),
    )

    app.run_dns_leak_check()

    assert tab_calls == ["dns-tab", "dns-tab"]
    assert logs == [
        "DNS Leak Check gestartet",
        "DNS Leak Check abgeschlossen",
    ]
    assert outputs == [("=== DNS Leak Check ===\nLeak erkannt: NEIN", True)]
    assert chad == []
    assert prepared == []


def test_run_dnssec_check_stays_in_dns_tab_without_auto_chad(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    outputs = []
    prepared = []
    tab_calls = []

    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: tab_calls.append(tab)}
    )()
    app.tab_dns = "dns-tab"
    app.log = logs.append
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.prepare_chad_analysis = lambda title, text: prepared.append((title, text))
    app.after = lambda delay, callback: callback()
    app.check_dnssec_status = lambda: ("yes", "raw dnssec")
    app.test_dnssec_validation = lambda: (True, "DNSSEC funktioniert korrekt")

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    app.run_dnssec_check()

    assert tab_calls == ["dns-tab", "dns-tab"]
    assert logs == [
        "DNSSEC-Prüfung gestartet",
        "DNSSEC-Prüfung abgeschlossen",
    ]
    assert outputs == [
        (
            "=== DNSSEC Prüfung ===\n"
            "\n"
            "✔ Gesamtstatus: OK\n"
            "✔ DNSSEC-Validierung aktiv\n"
            "✔ Manipulationsschutz: aktiv (Strict Mode)\n"
            "\n"
            "=== Ergebnis ===\n"
            "✔ DNSSEC funktioniert korrekt",
            False,
        )
    ]
    assert prepared == []


def test_format_dnssec_result_text_shows_allow_downgrade_mode():
    app = netmon.App.__new__(netmon.App)

    result = app._format_dnssec_result_text(
        mode="allow-downgrade",
        valid=True,
        msg="DNSSEC funktioniert korrekt",
    )

    assert "✔ Gesamtstatus: OK" in result
    assert "✔ DNSSEC-Validierung aktiv" in result
    assert "○ Manipulationsschutz: aktiv (Fallback möglich)" in result
    assert "Protocols:" not in result


def test_dnssec_strict_mode_warning_text_mentions_risk():
    app = netmon.App.__new__(netmon.App)

    warning = app.dnssec_strict_mode_warning_text()

    assert "DNSSEC Strict Mode" in warning
    assert "DNS-Probleme verursachen" in warning
    assert "DNS-Anbieter DNSSEC zuverlässig unterstützt" in warning


def test_detect_dnssec_mode_distinguishes_supported_states():
    app = netmon.App.__new__(netmon.App)
    app._dns_control_service = lambda: None

    assert app._detect_dnssec_mode("DNSSEC setting: yes") == "yes"
    assert (
        app._detect_dnssec_mode("DNSSEC setting: allow-downgrade") == "allow-downgrade"
    )
    assert app._detect_dnssec_mode("DNSSEC setting: no") == "no"
    assert app._detect_dnssec_mode("DNSSEC supported: yes") == "unknown"


def test_render_dnssec_mode_dropin_updates_or_inserts_dnssec_line():
    app = netmon.App.__new__(netmon.App)
    app.settings = {"dnssec_mode": "strict"}

    rendered = app._render_dnssec_mode_dropin(
        "# Managed by NetMon\n[Resolve]\nDNS=1.1.1.1#cloudflare-dns.com\nDNSOverTLS=yes\nDomains=~.\n"
    )

    assert "DNSSEC=yes" in rendered
    assert rendered.count("DNSSEC=") == 1

    rendered2 = app._render_dnssec_mode_dropin(
        "# Managed by NetMon\n[Resolve]\nDNS=1.1.1.1#cloudflare-dns.com\nDNSOverTLS=yes\nDNSSEC=allow-downgrade\nDomains=~.\n"
    )
    assert "DNSSEC=yes" in rendered2
    assert "DNSSEC=allow-downgrade" not in rendered2


def test_get_preferred_dnssec_mode_prefers_current_ui_value_over_settings():
    app = netmon.App.__new__(netmon.App)
    app.settings = {"dnssec_mode": "strict"}
    app.var_dnssec_mode = DummyVar("standard")

    assert app.get_preferred_dnssec_mode() == "standard"


def test_show_dns_repair_message_no_longer_pushes_to_chad():
    app = netmon.App.__new__(netmon.App)
    outputs = []
    chad = []
    app.chad_analysis_status_var = DummyVar()
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.append_to_chad_output = lambda title, text: chad.append((title, text))

    app._show_dns_repair_message("DNS Leak Repair", "repair text")

    assert outputs == [("repair text", True)]
    assert chad == []
    assert app.chad_analysis_status_var.get() == "DNS Leak Repair"


def test_update_dns_controls_state_disables_manual_controls_with_vpn():
    app = netmon.App.__new__(netmon.App)
    app.is_dot_active = lambda: False
    app.dns_combo = DummyWidget()
    app.btn_dns_apply = DummyWidget()
    app.btn_dot_on = DummyWidget()
    app.btn_dot_off = DummyWidget()
    app.dns_control_hint_var = DummyVar()
    app.is_vpn_active_for_dns_ui = lambda: True

    app.update_dns_controls_state()

    assert app.dns_combo.config["state"] == "disabled"
    assert app.btn_dns_apply.config["state"] == "disabled"
    assert app.btn_dot_on.config["state"] == "disabled"
    assert app.btn_dot_off.config["state"] == "normal"
    assert "VPN aktiv" in app.dns_control_hint_var.get()


def test_update_dns_controls_state_disables_manual_controls_during_transition():
    app = netmon.App.__new__(netmon.App)
    app.is_dot_active = lambda: False
    app.dns_combo = DummyWidget()
    app.btn_dns_apply = DummyWidget()
    app.btn_dot_on = DummyWidget()
    app.btn_dot_off = DummyWidget()
    app.dns_control_hint_var = DummyVar()
    app.is_vpn_active_for_dns_ui = lambda: False
    app._dns_runtime_transition_active = lambda: True

    app.update_dns_controls_state()

    assert app.dns_combo.config["state"] == "disabled"
    assert app.btn_dns_apply.config["state"] == "disabled"
    assert app.btn_dot_on.config["state"] == "disabled"
    assert app.btn_dot_off.config["state"] == "normal"
    assert "VPN/DNS-Wechsel läuft" in app.dns_control_hint_var.get()


def test_apply_dns_blocks_when_vpn_active(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    outputs = []
    logs = []
    warnings = []
    status_refreshes = []

    app.is_vpn_active_for_dns_ui = lambda: True
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: outputs.append(text)
    app.log_safe = logs.append
    app.after = lambda delay, callback: callback()
    app.update_dns_controls_state = lambda: None
    # This test checks the VPN lock, not the external DNS status collector.
    app.refresh_dns_policy_status = lambda: status_refreshes.append(True)

    monkeypatch.setattr(
        netmon.messagebox,
        "showwarning",
        lambda title, message, parent=None: warnings.append((title, message)),
    )

    assert app.apply_dns() is False
    assert warnings and warnings[0][0] == "DNS gesperrt"
    assert "Status: blockiert" in outputs[0]
    assert logs == ["DNS anwenden blockiert: VPN aktiv"]
    assert status_refreshes == [True]


def test_apply_dns_accepts_vpn_dns_silently_in_stealth_auto_mode(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    warnings = []
    refreshes = []
    state_updates = []

    app.is_vpn_active_for_dns_ui = lambda: True
    app.dns_choice = DummyVar("System (DHCP/auto)")
    app.isp_stealth_enabled = DummyVar(True)
    app.isp_stealth_running = True
    app.log_safe = logs.append
    app.refresh_dns_policy_status = lambda: refreshes.append(True)
    app.update_dns_controls_state_safe = lambda: state_updates.append(True)

    monkeypatch.setattr(
        netmon.messagebox,
        "showwarning",
        lambda title, message, parent=None: warnings.append((title, message)),
    )

    assert app.apply_dns() is True
    assert warnings == []
    assert logs == ["DNS wird im Stealthmodus vom VPN-Profil verwaltet."]
    assert refreshes == [True]
    assert state_updates == [True]


def test_enforce_dns_clean_skips_dnssec_confirmation_for_background_apply():
    app = netmon.App.__new__(netmon.App)
    apply_calls = []

    app._auto_dns_control_available = lambda: True
    app.is_vpn_active = lambda: False
    app.get_selected_user_dns = lambda: ["9.9.9.9"]
    app._manual_dns_choice = lambda: "9.9.9.9"
    app.apply_dns = lambda **kwargs: apply_calls.append(kwargs) or True

    success, result = app.enforce_dns_clean()

    assert success is True
    assert "User DNS erzwingen" in result
    assert apply_calls == [
        {
            "choice": "9.9.9.9",
            "refresh_ui": False,
            "update_choice_var": False,
            "confirm_dnssec": False,
        }
    ]


def test_apply_dns_blocks_during_dns_runtime_transition(
    monkeypatch, passive_dns_status, tmp_path
):
    app = netmon.App.__new__(netmon.App)
    outputs = []
    logs = []
    warnings = []

    app.is_vpn_active_for_dns_ui = lambda: False
    app._dns_runtime_transition_active = lambda: True
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: outputs.append(text)
    app.log_safe = logs.append
    app.update_dns_controls_state_safe = lambda: None
    app.dns_resolver_status_var = DummyVar()
    app.dns_conflict_status_var = DummyVar()
    # The status parser receives an explicit synthetic inventory and drop-in.
    service = app._dns_control_service()
    service.get_wireguard_interfaces = lambda: set()
    service.dot_dropin_path = str(tmp_path / "absent-netmon-dot.conf")

    monkeypatch.setattr(
        netmon.messagebox,
        "showwarning",
        lambda title, message, parent=None: warnings.append((title, message)),
    )

    assert app.apply_dns() is False
    assert warnings and warnings[0][0] == "DNS gesperrt"
    assert "VPN-/DNS-Wechsel läuft" in outputs[0]
    assert logs == ["DNS anwenden blockiert: VPN-/DNS-Wechsel läuft"]
    assert passive_dns_status == [(["resolvectl", "status"], 8)]
    assert app.dns_resolver_status_var.get() == "Aktiver Resolver: System (192.0.2.53)"
    assert app.dns_conflict_status_var.get() == "Konflikte: keine"


def test_apply_dns_reports_control_layer_target_errors(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.is_dot_active = lambda: False
    outputs = []
    logs = []

    app.is_vpn_active_for_dns_ui = lambda: False
    app.dns_choice = DummyVar("Cloudflare (1.1.1.1)")
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: outputs.append(text)
    app.log_safe = logs.append
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None

    monkeypatch.setattr(
        netmon.dns_controller,
        "apply_dns_profile_choice_via_control",
        lambda _app, choice: {
            "choice": choice,
            "servers": ["1.1.1.1", "1.0.0.1"],
            "success": False,
            "nm_details": ["Keine aktive physische LAN/WLAN-Connection gefunden."],
            "dropin_ok": True,
            "dropin_detail": "",
            "dropin_state": "geschrieben",
            "restart_ok": True,
            "restart_detail": "",
        },
    )

    assert app.apply_dns() is False
    assert "Keine aktive physische LAN/WLAN-Connection gefunden." in outputs[0]
    assert logs == ["DNS-Profil wird angewendet...", "DNS anwenden fehlgeschlagen"]


def test_apply_dns_refreshes_dns_guard_whitelist_and_check_on_success(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.is_dot_active = lambda: False
    logs = []
    events = []

    app.is_vpn_active_for_dns_ui = lambda: False
    app.dns_choice = DummyVar("84.200.69.80#DNS.Watch")
    app.custom_dns_profile_choices = []
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: None
    app.log_safe = logs.append
    app.refresh_dns_policy_status = lambda: events.append("status")
    app.update_dns_controls_state_safe = lambda: events.append("controls")
    app.refresh_safe = lambda: events.append("refresh")
    app.rebuild_dns_guard_whitelist = lambda: events.append("whitelist")
    app.run_dns_guard_check_once = lambda auto_repair=False: events.append(
        ("guard", auto_repair)
    )
    app.dns_consistency_check_async = lambda force=False: events.append(
        ("consistency", force)
    )
    app._collect_dot_status = lambda run_test=False: {"enabled": False}
    app._show_dot_status_result = lambda status, **kwargs: events.append(
        ("dot-status", status.get("enabled"), kwargs)
    )

    monkeypatch.setattr(
        netmon.dns_controller,
        "apply_dns_profile_choice_via_control",
        lambda _app, choice: {
            "choice": choice,
            "servers": ["84.200.69.80#DNS.Watch"],
            "success": True,
            "nm_details": ["ok"],
            "dropin_ok": True,
            "dropin_detail": "",
            "dropin_state": "geschrieben",
            "restart_ok": True,
            "restart_detail": "",
        },
    )

    assert app.apply_dns() is True
    assert "DNS-Profil angewendet: 84.200.69.80#DNS.Watch" in logs
    assert (
        "dot-status",
        False,
        {"startup": True, "show_output": False, "emit_chad_warning": False},
    ) in events
    assert "whitelist" in events
    assert ("guard", False) in events
    assert ("consistency", True) in events


def test_dns_consistency_result_with_hostname_does_not_switch_to_dns_tab(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    selects = []

    app.dns_consistency_enabled = True
    app.dns_consistency_running = False
    app.last_dns_consistency_ts = 0.0
    app.last_dns_consistency_ok = None
    app.dns_choice = DummyVar("84.200.69.80#DNS.Watch")
    app.killswitch_is_on = lambda: False
    app.active_wg_profile = lambda: None
    app.after = lambda delay, callback: callback()
    app.log = lambda _msg: None
    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: selects.append(tab)}
    )()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: None

    monkeypatch.setattr(netmon, "DNS_PROFILES", {"System (DHCP/auto)": None})
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name in {"dig", "curl"})
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    def fake_run_cmd(args, timeout=0, text=True):
        if args[:5] == ["dig", "+time=2", "+tries=1", "+short", "A"]:
            return 0, "93.184.216.34\n"
        if args[:4] == ["curl", "-fsS", "--max-time", "4"]:
            return 0, "ok"
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    app.dns_consistency_check_async(force=True)

    assert selects == []


def test_apply_dns_aborts_when_dnssec_strict_confirmation_is_declined():
    app = netmon.App.__new__(netmon.App)
    app.is_dot_active = lambda: False
    app.refresh_dns_policy_status = lambda: None
    outputs = []
    logs = []

    app.is_vpn_active_for_dns_ui = lambda: False
    app.dns_choice = DummyVar("Cloudflare (1.1.1.1)")
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: outputs.append(text)
    app.log_safe = logs.append
    app.update_dns_controls_state_safe = lambda: None
    app.confirm_dnssec_mode_activation = lambda action: False

    assert app.apply_dns() is False
    assert "DNSSEC Strict Mode wurde nicht bestätigt" in outputs[0]
    assert logs == ["DNS anwenden abgebrochen: DNSSEC Strict Mode nicht bestätigt"]


def test_enable_dot_async_aborts_when_dnssec_strict_confirmation_is_declined():
    app = netmon.App.__new__(netmon.App)
    outputs = []
    logs = []

    app.dot_running = False
    app.update_dns_controls_state_safe = lambda: None
    app.is_vpn_dns_active = lambda: (False, "")
    app.confirm_dnssec_mode_activation = lambda action: False
    app.ensure_sudo_session = lambda reason: (_ for _ in ()).throw(
        AssertionError("sudo must not be requested when confirmation is declined")
    )
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.log_safe = logs.append

    app.enable_dot_async()

    assert outputs == [
        (
            "=== DNS over TLS ===\n\n"
            "Status: abgebrochen\n"
            "Grund: DNSSEC Strict Mode wurde nicht bestätigt.",
            False,
        )
    ]
    assert logs == ["DoT-Aktivierung abgebrochen: DNSSEC Strict Mode nicht bestätigt"]


def test_apply_dnssec_mode_async_skips_when_no_netmon_dropin_exists(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    outputs = []
    logs = []
    tab_calls = []

    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: tab_calls.append(tab)}
    )()
    app.tab_dns = "dns-tab"
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.log_safe = logs.append
    app.after = lambda delay, callback: callback()
    app.confirm_dnssec_mode_activation = lambda action: True
    app.ensure_sudo_session = lambda reason: True
    app._read_dot_dropin = lambda: ""
    app.check_dnssec_status = lambda: ("allow-downgrade", "")
    app.settings = {"dnssec_mode": "standard"}
    app.dnssec_target_mode_var = DummyVar("")
    app.dnssec_system_mode_var = DummyVar("")

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    app.apply_dnssec_mode_async()

    assert tab_calls == ["dns-tab", "dns-tab"]
    assert "[System]" in outputs[-1][0]
    assert "○ Modus vorgemerkt" in outputs[-1][0]
    assert logs == [
        "DNSSEC-Modus anwenden gestartet",
        "DNSSEC-Modus anwenden abgeschlossen",
    ]


def test_apply_dnssec_mode_async_uses_current_ui_mode_when_switching_to_standard(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    outputs = []
    writes = []
    saves = []

    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = "dns-tab"
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.log_safe = lambda _msg: None
    app.after = lambda delay, callback: callback()
    app.confirm_dnssec_mode_activation = lambda action: True
    app.ensure_sudo_session = lambda reason: True
    app._read_dot_dropin = (
        lambda: "# Managed by NetMon\n[Resolve]\nDNS=1.1.1.1#cloudflare-dns.com\n"
        "DNSOverTLS=yes\nDNSSEC=yes\nDomains=~.\n"
    )
    app._write_dot_dropin_text = lambda content: writes.append(content) or (
        True,
        content,
    )
    app._restart_resolved_for_dns_policy = lambda: (True, "")
    app._restore_dot_dropin_backup = lambda text: (True, text)
    app.check_dnssec_status = lambda: ("allow-downgrade", "")
    app.update_dnssec_mode_status_labels = lambda mode=None: None
    app.save_settings = lambda log_success=False: saves.append(log_success)
    app.settings = {"dnssec_mode": "strict"}
    app.var_dnssec_mode = DummyVar("standard")

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    app.apply_dnssec_mode_async()

    assert writes
    assert "DNSSEC=allow-downgrade" in writes[0]
    assert "DNSSEC=yes" not in writes[0]
    assert app.settings["dnssec_mode"] == "standard"
    assert saves == [False]
    assert "✔ DNSSEC-Modus angewendet" in outputs[-1][0]


def test_apply_dnssec_mode_async_aborts_when_confirmation_is_declined():
    app = netmon.App.__new__(netmon.App)
    outputs = []
    logs = []
    tab_calls = []

    app.nb = type(
        "DummyNotebook", (), {"select": lambda self, tab: tab_calls.append(tab)}
    )()
    app.tab_dns = "dns-tab"
    app.update_dns_output = lambda text, append=False: outputs.append((text, append))
    app.log_safe = logs.append
    app.confirm_dnssec_mode_activation = lambda action: False

    app.apply_dnssec_mode_async()

    assert tab_calls == ["dns-tab"]
    assert "DNSSEC Strict Mode wurde nicht bestätigt" in outputs[0][0]
    assert logs == [
        "DNSSEC-Modus anwenden abgebrochen: DNSSEC Strict Mode nicht bestätigt"
    ]


def test_on_vpn_connected_skips_without_sudo_nopasswd():
    app = netmon.App.__new__(netmon.App)
    logs = []
    outputs = []

    app.log_safe = logs.append
    app.update_dns_output = lambda text, append=False: outputs.append(text)
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state = lambda: None
    app._auto_dns_control_available = lambda: False

    app.on_vpn_connected()

    assert logs[0] == "VPN erkannt -> DNS wird bereinigt"
    assert "sudo -n ist nicht verfügbar" in outputs[0]


def test_initial_dns_cleanup_can_defer_followup_when_sudo_is_unavailable():
    app = netmon.App.__new__(netmon.App)
    logs = []
    events = []

    app._auto_dns_control_available = lambda: False
    app.log_safe = logs.append
    app.rebuild_dns_guard_whitelist = lambda: events.append("whitelist")
    app.run_dns_guard_check_once = lambda: events.append("guard")
    app.update_dns_controls_state_safe = lambda: events.append("ui")

    app.initial_dns_cleanup(defer_followup=True)

    assert logs == ["DNS-Startbereinigung übersprungen: sudo -n nicht verfügbar"]
    assert events == []


def test_start_dns_startup_sequence_schedules_ordered_steps():
    app = netmon.App.__new__(netmon.App)
    scheduled = []
    events = []

    app.after = lambda delay, callback: scheduled.append((delay, callback))
    app.set_dns_guard_state = lambda state, **kwargs: events.append(
        ("state", state, kwargs.get("log_message"))
    )
    app.update_dns_controls_state = lambda: events.append("ui")
    app._run_dns_startup_cleanup_step = lambda: events.append("cleanup")
    app._run_dns_startup_dot_step = lambda: events.append("dot")
    app._run_dns_startup_policy_step = lambda: events.append("policy")
    app._finalize_dns_startup_sequence = lambda: events.append("finalize")
    app.dns_guard_ui_loop = lambda: events.append("guard_ui_loop")
    app.monitor_vpn_changes = lambda: events.append("monitor")
    app.dns_guard_loop = lambda: events.append("guard_loop")

    app.start_dns_startup_sequence()

    assert app.dns_startup_sequence_running is True
    assert events[:2] == [
        ("state", "transition", "DNS-Startsequenz: Initialisierung läuft"),
        "ui",
    ]
    assert [delay for delay, _callback in scheduled] == [
        0,
        700,
        1500,
        2400,
        2600,
        3200,
        3800,
    ]

    for _delay, callback in scheduled:
        callback()

    assert events[2:] == [
        "cleanup",
        "dot",
        "policy",
        "finalize",
        "guard_ui_loop",
        "monitor",
        "guard_loop",
    ]


def test_run_dns_startup_cleanup_step_restores_fallback_when_needed():
    app = netmon.App.__new__(netmon.App)
    events = []

    app.initial_dns_cleanup = lambda defer_followup=False: events.append(
        ("cleanup", defer_followup)
    )
    app._restore_isp_dns_on_startup_if_needed = lambda: events.append("fallback")

    app._run_dns_startup_cleanup_step()

    assert events == [("cleanup", True), "fallback"]


def test_finalize_dns_startup_sequence_refreshes_and_clears_transition():
    app = netmon.App.__new__(netmon.App)
    events = []

    app.dns_startup_sequence_running = True
    app.dns_guard_transition_until = 10**12
    app.refresh_dns_policy_status = lambda: events.append("status")
    app.update_dns_controls_state = lambda: events.append("ui")
    app.rebuild_dns_guard_whitelist = lambda: events.append("whitelist")
    app.run_dns_guard_check_once = lambda: events.append("guard")
    app.update_dns_guard_indicator = lambda: events.append("indicator")

    app._finalize_dns_startup_sequence()

    assert app.dns_startup_sequence_running is False
    assert app.dns_guard_transition_until == 0.0
    assert events == ["status", "ui", "whitelist", "guard", "indicator"]


def test_monitor_vpn_changes_triggers_connect_and_disconnect():
    app = netmon.App.__new__(netmon.App)
    events = []
    scheduled = []
    states = iter([True, False])

    app.last_vpn_state = False
    app.get_vpn_state = lambda: next(states)
    app.on_vpn_state_changed = lambda active: events.append(("state", active))
    app.update_dns_controls_state = lambda: events.append("ui")
    app.after = lambda delay, callback: scheduled.append((delay, callback))
    app.log_debug_safe = lambda msg: None

    app.monitor_vpn_changes()
    app.monitor_vpn_changes()

    assert events == [
        ("state", True),
        "ui",
        ("state", False),
        "ui",
    ]
    assert app.last_vpn_state is False
    assert scheduled and all(delay == 3000 for delay, _cb in scheduled)


def test_monitor_vpn_changes_defers_during_dns_runtime_transition():
    app = netmon.App.__new__(netmon.App)
    events = []
    scheduled = []

    app._dns_runtime_transition_active = lambda: True
    app.get_vpn_state = lambda: (_ for _ in ()).throw(
        AssertionError("vpn state must not be queried during transition")
    )
    app.on_vpn_state_changed = lambda active: events.append(("state", active))
    app.update_dns_controls_state = lambda: events.append("ui")
    app.after = lambda delay, callback: scheduled.append((delay, callback))
    app.log_debug_safe = lambda msg: None

    app.monitor_vpn_changes()

    assert events == ["ui"]
    assert scheduled and scheduled[-1][0] == 3000


def test_dns_is_clean_uses_allowed_whitelist():
    app = netmon.App.__new__(netmon.App)

    assert app.dns_is_clean(["10.2.0.1"], ["10.2.0.1", "2a07:b944::2:1"]) is True
    assert app.dns_is_clean(["10.2.0.1", "1.1.1.1"], ["10.2.0.1"]) is False
    assert (
        app.dns_is_clean(
            ["1.1.1.1#cloudflare-dns.com", "1.0.0.1#cloudflare-dns.com"],
            ["1.1.1.1", "1.0.0.1"],
        )
        is True
    )
    assert app.dns_is_clean(["10.2.0.1"], []) is False


def test_get_selected_dot_dns_includes_hostname_variants():
    app = netmon.App.__new__(netmon.App)
    app.dot_choice = DummyVar("Cloudflare")

    assert app.get_selected_dot_dns() == [
        "1.1.1.1",
        "1.0.0.1",
        "1.1.1.1#cloudflare-dns.com",
        "1.0.0.1#cloudflare-dns.com",
    ]


def test_dns_guard_loop_enforces_when_dirty():
    app = netmon.App.__new__(netmon.App)
    app.is_dot_active = lambda: False
    app.is_vpn_active = lambda: False
    events = []
    scheduled = []

    app.dns_guard_enabled_var = DummyVar(True)
    app.dns_guard_state = ""
    app.last_dns_guard_state = None
    app.dns_guard_check_running = False
    app.last_dns_guard_repair_ts = 0.0
    app.dns_guard_transition_until = 0.0
    app.get_current_dns = lambda: ["10.2.0.1", "1.1.1.1"]
    app.rebuild_dns_guard_whitelist = lambda: ["10.2.0.1"]
    app.log_safe = lambda msg: events.append(("log", msg))
    app.enforce_dns_clean = lambda: (True, "guard fixed")
    app.update_dns_output = lambda text, append=False: events.append(
        ("output", text, append)
    )
    app.after = lambda delay, callback: scheduled.append((delay, callback))
    app.log_debug_safe = lambda msg: None
    app.dns_guard_status_var = DummyVar()
    app.dns_guard_last_action_var = DummyVar()
    app.set_light = lambda _light, color: events.append(("light", color))

    app.dns_guard_loop()

    assert ("log", "DNS Guard: Abweichung erkannt") in events
    assert ("log", "DNS Guard: Inkonsistenz erkannt → Auto-Korrektur") in events
    assert ("output", "guard fixed", True) in events
    assert app.dns_guard_status_var.get() == "DNS Guard: aktiv / korrigiert"
    assert app.dns_guard_last_action_var.get().startswith("Letzte Korrektur: ")
    assert scheduled and scheduled[-1][0] == 5000


def test_dns_guard_loop_stays_in_transition_during_runtime_transition():
    app = netmon.App.__new__(netmon.App)
    scheduled = []
    states = []

    app._dns_runtime_transition_active = lambda: True
    app.run_dns_guard_check_once = lambda auto_repair=True: (_ for _ in ()).throw(
        AssertionError("dns guard check must not run during runtime transition")
    )
    app.set_dns_guard_state = lambda state: states.append(state)
    app.after = lambda delay, callback: scheduled.append((delay, callback))
    app.log_debug_safe = lambda msg: None

    app.dns_guard_loop()

    assert states == ["transition"]
    assert scheduled and scheduled[-1][0] == 5000


def test_get_dns_guard_status_states():
    app = netmon.App.__new__(netmon.App)
    app.dns_guard_enabled_var = DummyVar(False)
    app.dns_guard_state = ""
    app.dns_guard_transition_until = 0.0
    app.get_current_dns = lambda: ["10.2.0.1"]
    app.get_allowed_dns = lambda: ["10.2.0.1"]

    assert app.get_dns_guard_status() == "off"

    app.dns_guard_enabled_var = DummyVar(True)
    app.get_current_dns = lambda: []
    assert app.get_dns_guard_status() == "unknown"

    app.get_current_dns = lambda: ["10.2.0.1"]
    app.get_allowed_dns = lambda: ["10.2.0.1"]
    assert app.get_dns_guard_status() == "ok"

    app.get_allowed_dns = lambda: []
    assert app.get_dns_guard_status() == "unknown"

    app.get_allowed_dns = lambda: ["10.2.0.1"]
    app.get_current_dns = lambda: ["1.1.1.1"]
    assert app.get_dns_guard_status() == "problem"

    app.dns_guard_transition_until = 10**12
    assert app.get_dns_guard_status() == "transition"


def test_update_dns_guard_indicator_sets_label_and_light():
    app = netmon.App.__new__(netmon.App)
    colors = []
    app.dns_guard_enabled_var = DummyVar(True)
    app.dns_guard_state = ""
    app.dns_guard_transition_until = 0.0
    app.dns_guard_label = DummyLabel()
    app.dns_guard_status_var = DummyVar()
    app.dns_guard_indicator = (object(), object(), app.dns_guard_label)
    app.set_light = lambda _light, color: colors.append(color)
    app.get_current_dns = lambda: ["10.2.0.1"]
    app.get_allowed_dns = lambda: ["10.2.0.1"]

    assert app.update_dns_guard_indicator() == "ok"
    assert colors[-1] == "green"
    assert app.dns_guard_label.config["text"] == "DNS Guard: aktiv (OK)"

    app.get_current_dns = lambda: ["1.1.1.1"]
    app.get_allowed_dns = lambda: ["10.2.0.1"]
    assert app.update_dns_guard_indicator() == "problem"
    assert colors[-1] == "red"

    app.dns_guard_transition_until = 10**12
    assert app.update_dns_guard_indicator() == "transition"
    assert colors[-1] == "yellow"
    assert app.dns_guard_label.config["text"] == "DNS Guard: Wechsel wird geprüft"


def test_rebuild_dns_guard_whitelist_switches_between_vpn_and_manual():
    app = netmon.App.__new__(netmon.App)
    app.is_vpn_active = lambda: True
    app.is_dot_active = lambda: False
    app.get_active_vpn_dns = lambda: ["10.2.0.1", "2a07:b944::2:1"]
    app.get_selected_user_dns = lambda: ["1.1.1.1"]
    app.get_selected_dot_dns = lambda: ["9.9.9.9"]
    app.get_current_dns = lambda: ["9.9.9.9"]

    assert app.rebuild_dns_guard_whitelist() == ["10.2.0.1", "2a07:b944::2:1"]
    assert app.get_allowed_dns() == ["10.2.0.1", "2a07:b944::2:1"]

    app.is_vpn_active = lambda: False
    assert app.rebuild_dns_guard_whitelist() == ["1.1.1.1"]
    assert app.get_allowed_dns() == ["1.1.1.1"]

    app.is_dot_active = lambda: True
    assert app.rebuild_dns_guard_whitelist() == ["9.9.9.9"]
    assert app.get_allowed_dns() == ["9.9.9.9"]


def test_set_dns_guard_state_logs_only_on_changes():
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.log_safe = logs.append
    app.dns_guard_state = "off"
    app.last_dns_guard_state = None
    app.dns_guard_status_var = DummyVar()
    app.dns_guard_last_action_var = DummyVar()
    app.update_dns_guard_indicator = lambda: None

    app.set_dns_guard_state("ok", log_message="DNS Guard: OK")
    app.set_dns_guard_state("ok", log_message="DNS Guard: OK")
    app.set_dns_guard_state("problem", log_message="DNS Guard: Problem")

    assert logs == ["DNS Guard: OK", "DNS Guard: Problem"]


def test_run_dns_guard_check_once_respects_transition_and_no_repair():
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.dns_guard_enabled_var = DummyVar(True)
    app.dns_guard_state = ""
    app.last_dns_guard_state = None
    app.dns_guard_transition_until = 10**12
    app.dns_guard_check_running = False
    app.dns_guard_status_var = DummyVar()
    app.dns_guard_last_action_var = DummyVar()
    app.log_safe = logs.append
    app.update_dns_guard_indicator = lambda: None
    app.enforce_dns_clean = lambda: (_ for _ in ()).throw(
        AssertionError("repair must not run during transition")
    )

    app.run_dns_guard_check_once(auto_repair=True)

    assert app.dns_guard_status_var.get() == "DNS Guard: Wechsel wird geprüft"
    assert logs == ["DNS Guard: Wechsel wird geprüft"] or logs == []


def test_run_dns_guard_check_once_marks_dot_profile_ok():
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.dns_guard_enabled_var = DummyVar(True)
    app.dns_guard_state = ""
    app.last_dns_guard_state = None
    app.dns_guard_transition_until = 0.0
    app.dns_guard_check_running = False
    app.dns_guard_status_var = DummyVar()
    app.dns_guard_last_action_var = DummyVar()
    app.log_safe = logs.append
    app.update_dns_guard_indicator = lambda: None
    app.rebuild_dns_guard_whitelist = lambda: [
        "1.1.1.1",
        "1.0.0.1",
        "1.1.1.1#cloudflare-dns.com",
        "1.0.0.1#cloudflare-dns.com",
    ]
    app.get_current_dns = lambda: ["1.1.1.1#cloudflare-dns.com", "1.0.0.1"]
    app.is_vpn_active = lambda: False
    app.is_dot_active = lambda: True

    app.run_dns_guard_check_once()

    assert app.dns_guard_status_var.get() == "DNS Guard: aktiv (DoT-Resolver OK)"
    assert logs == ["DNS Guard: OK"]


def test_run_dns_guard_check_once_marks_unknown_when_target_dns_is_missing():
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.dns_guard_enabled_var = DummyVar(True)
    app.dns_guard_state = ""
    app.last_dns_guard_state = None
    app.dns_guard_transition_until = 0.0
    app.dns_guard_check_running = False
    app.dns_guard_status_var = DummyVar()
    app.dns_guard_last_action_var = DummyVar()
    app.log_safe = logs.append
    app.update_dns_guard_indicator = lambda: None
    app.rebuild_dns_guard_whitelist = lambda: []
    app.get_current_dns = lambda: ["10.2.0.1"]
    app.is_vpn_active = lambda: True
    app.is_dot_active = lambda: False

    app.run_dns_guard_check_once()

    assert app.dns_guard_status_var.get() == "DNS Guard: aktiv / VPN-DNS unklar"
    assert logs == ["DNS Guard: DNS-Ziel unklar"]


def test_schedule_dns_finalize_after_vpn_profile_switch_coalesces_callbacks():
    app = netmon.App.__new__(netmon.App)
    scheduled = []
    calls = []

    app.after = lambda delay, callback: scheduled.append((delay, callback))
    app.finalize_dns_after_vpn_profile_switch = lambda: calls.append("finalized")

    app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=1000)
    first_callback = scheduled[-1][1]
    app._schedule_dns_finalize_after_vpn_profile_switch(delay_ms=1000)
    second_callback = scheduled[-1][1]

    first_callback()
    second_callback()

    assert calls == ["finalized"]


def test_run_dns_guard_check_once_marks_dot_profile_mismatch():
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.dns_guard_enabled_var = DummyVar(True)
    app.dns_guard_state = ""
    app.last_dns_guard_state = None
    app.dns_guard_transition_until = 0.0
    app.dns_guard_check_running = False
    app.dns_guard_status_var = DummyVar()
    app.dns_guard_last_action_var = DummyVar()
    app.log_safe = logs.append
    app.update_dns_guard_indicator = lambda: None
    app.rebuild_dns_guard_whitelist = lambda: [
        "1.1.1.1",
        "1.0.0.1",
        "1.1.1.1#cloudflare-dns.com",
        "1.0.0.1#cloudflare-dns.com",
    ]
    app.get_current_dns = lambda: ["9.9.9.9"]
    app.is_vpn_active = lambda: False
    app.is_dot_active = lambda: True

    app.run_dns_guard_check_once()

    assert app.dns_guard_status_var.get() == "DNS Guard: Problem (DoT-DNS abweichend)"
    assert logs == ["DNS Guard: Abweichung erkannt"]


def test_update_ufw_logging_light_maps_levels(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.l_ufw_log = object()
    app.ufw_logging_status_var = DummyVar()
    app.set_light = lambda _light, color: colors.append(color)
    app.security_events = []
    app._active_ufw_portscan_ip = lambda: None
    app.security_level_var = DummyVar()
    levels = iter(
        [
            "OFF",
            "LOW",
            "MEDIUM",
            "HIGH",
            "LOW",
            "–",
        ]
    )
    app._security_query_log_level = lambda: next(levels)

    for _ in range(6):
        app.update_ufw_logging_light()

    assert colors == ["gray", "yellow", "green", "green", "yellow", "gray"]
    assert app.ufw_logging_status_var.get() == "UFW Logging: –"
    assert app.security_level_var.get() == "Logging: –"


def test_update_ufw_logging_light_uses_command_instead_of_cache(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.l_ufw_log = object()
    app.ufw_logging_status_var = DummyVar()
    app.security_log_level = "HIGH"
    app.set_light = lambda _light, color: colors.append(color)
    app.security_events = []
    app._active_ufw_portscan_ip = lambda: None
    app.security_level_var = DummyVar()
    app._security_query_log_level = lambda: "OFF"

    app.update_ufw_logging_light()

    assert colors == ["gray"]
    assert app.ufw_logging_status_var.get() == "UFW Logging: OFF"
    assert app.security_level_var.get() == "Logging: OFF"


def test_update_ufw_logging_light_falls_back_without_sudo(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.l_ufw_log = object()
    app.ufw_logging_status_var = DummyVar()
    app.set_light = lambda _light, color: colors.append(color)
    app.security_events = []
    app._active_ufw_portscan_ip = lambda: None
    app.security_level_var = DummyVar()
    app._security_query_log_level = lambda: "HIGH"

    app.update_ufw_logging_light()

    assert colors == ["green"]
    assert app.ufw_logging_status_var.get() == "UFW Logging: HIGH"


def test_update_ufw_logging_light_marks_portscan_red(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.l_ufw_log = object()
    app.ufw_logging_status_var = DummyVar()
    app.set_light = lambda _light, color: colors.append(color)
    app.security_events = [
        {
            "type": "Portscan-Verdacht",
            "src": "185.123.45.67",
            "epoch": 1000.0,
        }
    ]
    app._security_query_log_level = lambda: "HIGH"
    app.security_level_var = DummyVar()

    monkeypatch.setattr(netmon.time, "time", lambda: 1010.0)

    app.update_ufw_logging_light()

    assert colors == ["red"]
    assert app.ufw_logging_status_var.get() == "Portscan von IP: 185.123.45.67"
    assert app.security_level_var.get() == "Logging: HIGH"


def test_parse_ufw_logging_level_parses_on_high():
    app = netmon.App.__new__(netmon.App)
    assert (
        app._parse_ufw_logging_level("Status: active\nLogging: on (high)\n") == "HIGH"
    )


def test_parse_ufw_logging_level_parses_german_medium():
    app = netmon.App.__new__(netmon.App)
    assert (
        app._parse_ufw_logging_level("Status: aktiv\nProtokollierung: ein (mittel)\n")
        == "MEDIUM"
    )


def test_parse_ufw_logging_level_parses_german_on_high():
    app = netmon.App.__new__(netmon.App)
    assert (
        app._parse_ufw_logging_level("Status: aktiv\nProtokollierung: on (high)\n")
        == "HIGH"
    )


def test_refresh_security_log_level_updates_security_label(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.security_level_var = DummyVar()
    app.security_log_level = "-"
    app.log = lambda _msg: None
    app.tr = lambda _key, text: text
    app._security_query_log_level = lambda: "MEDIUM"

    level = app.refresh_security_log_level()

    assert level == "MEDIUM"
    assert app.security_log_level == "MEDIUM"
    assert app.security_level_var.get() == "Logging: MEDIUM"


def test_security_set_ufw_logging_high_refreshes_light(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.ensure_sudo_session = lambda _prompt: True
    app.log = logs.append
    app.log_safe = logs.append
    app.security_monitoring = False
    app._security_update_status = lambda color: calls.append(("status", color))
    app._security_query_log_level = lambda: "HIGH"
    app.update_ufw_logging_light = lambda: calls.append("ufw-light")
    app.after = lambda delay, callback: (calls.append(("after", delay)), callback())

    monkeypatch.setattr(
        netmon.firewall_controller,
        "run_cmd",
        lambda args, timeout=0, text=True: (
            (0, "Status: active\nLogging: off\n")
            if args == ["ufw", "status", "verbose"]
            else (0, "ok")
        ),
    )

    netmon.firewall_controller.security_set_ufw_logging_high(app)

    assert app.security_log_level == "HIGH"
    assert ("status", "gray") in calls
    assert ("after", 500) in calls
    assert "ufw-light" in calls
    assert logs == ["Security: UFW Logging auf HIGH gesetzt."]


def test_set_ufw_logging_refreshes_light(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.ensure_sudo_session = lambda _prompt: True
    app.log_safe = logs.append
    app.update_ufw_logging_light = lambda: calls.append("ufw-light")
    app.after = lambda delay, callback: (calls.append(("after", delay)), callback())

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        netmon,
        "run_cmd",
        lambda args, timeout=0, text=True: (0, "ok"),
    )

    app.set_ufw_logging("low")

    assert logs == ["Security: UFW Logging auf LOW gesetzt"]
    assert ("after", 500) in calls
    assert "ufw-light" in calls


def test_set_dns_guard_enabled_updates_vars_and_indicator():
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.dns_guard_enabled = False
    app.dns_guard_enabled_var = DummyVar(False)
    app.var_dns_guard_enabled = DummyVar(False)
    app.save_privacy_config = lambda: calls.append("save")
    app.log_safe = logs.append
    app.update_dns_guard_indicator = lambda: calls.append("indicator")
    app.after = lambda delay, callback: (calls.append(("after", delay)), callback())

    app.set_dns_guard_enabled(True)

    assert app.dns_guard_enabled is True
    assert app.dns_guard_enabled_var.get() is True
    assert app.var_dns_guard_enabled.get() is True
    assert "save" in calls
    assert ("after", 300) in calls
    assert "indicator" in calls
    assert logs == ["DNS Guard aktiviert."]


def test_show_firewall_status_clean_switches_to_log_and_runs_status():
    app = netmon.App.__new__(netmon.App)
    calls = []

    class DummyNotebook:
        def select(self, tab):
            calls.append(("select", tab))

    app.nb = DummyNotebook()
    app.tab_log = object()
    app.log_overlay_active = True
    app.toggle_log_overlay = lambda: calls.append("toggle-overlay")
    app.clear_log = lambda: calls.append("clear-log")
    app.fw_status = lambda: calls.append("fw-status")
    app._append_firewall_log_link = lambda: calls.append("firewall-link")
    app.log_safe = lambda msg: calls.append(("log", msg))

    app.show_firewall_status_clean()

    assert calls == [
        ("select", app.tab_log),
        "toggle-overlay",
        "clear-log",
        "fw-status",
        "firewall-link",
    ]


def test_append_firewall_log_link_opens_firewall_tab():
    app = netmon.App.__new__(netmon.App)
    calls = []

    class DummyText:
        def __init__(self):
            self.text = ""
            self.tags = {}
            self.bindings = {}
            self.cursor = "xterm"

        def index(self, marker):
            if marker == "end-1c":
                return "1.0"
            if marker == "end-2c":
                return f"1.{len('Jump to Firewall')}"
            raise AssertionError(marker)

        def insert(self, _index, value):
            self.text += value

        def tag_add(self, tag_name, start, end):
            self.tags[tag_name] = {"range": (start, end)}

        def tag_configure(self, tag_name, **kwargs):
            self.tags.setdefault(tag_name, {}).update(kwargs)

        def tag_bind(self, tag_name, sequence, callback):
            self.bindings[(tag_name, sequence)] = callback

        def configure(self, **kwargs):
            if "cursor" in kwargs:
                self.cursor = kwargs["cursor"]

        def see(self, _index):
            return None

    app.text = DummyText()
    app.tab_firewall = object()
    app._select_security_tab = lambda tab: calls.append(("select-security", tab))

    assert app._append_firewall_log_link() is True
    assert "Jump to Firewall" in app.text.text

    click_binding = next(
        callback
        for (tag_name, sequence), callback in app.text.bindings.items()
        if sequence == "<Button-1>" and tag_name.startswith("log_link_")
    )
    click_binding(None)

    assert calls == [("select-security", app.tab_firewall)]


def test_dns_action_prepares_tab_before_running_action():
    app = netmon.App.__new__(netmon.App)
    calls = []

    class DummyNotebook:
        def select(self, tab):
            calls.append(("select", tab))

    app.nb = DummyNotebook()
    app.tab_dns = object()
    app.clear_dns_output = lambda: calls.append("clear-dns")
    app.log_safe = lambda msg: calls.append(("log", msg))

    app._dns_action(lambda: calls.append("dns-action"))

    assert calls == [
        ("select", app.tab_dns),
        "clear-dns",
        "dns-action",
    ]


def test_dot_action_prepares_tab_before_running_action():
    app = netmon.App.__new__(netmon.App)
    calls = []

    class DummyNotebook:
        def select(self, tab):
            calls.append(("select", tab))

    app.nb = DummyNotebook()
    app.tab_dns = object()
    app.clear_dns_output = lambda: calls.append("clear-dns")
    app.log_safe = lambda msg: calls.append(("log", msg))

    app._dot_action(lambda: calls.append("dot-action"))

    assert calls == [
        ("select", app.tab_dns),
        "clear-dns",
        "dot-action",
    ]


def test_vpn_profile_helpers_use_existing_vpn_paths():
    app = netmon.App.__new__(netmon.App)
    calls = []

    app.wg_profiles = ["alpha", "beta"]
    app.refresh_wg_profiles = lambda: calls.append("refresh")
    app.active_wg_profile = lambda: "beta"
    app._base_wg_profile_name = lambda profile: (profile or "").strip()
    app.vpn_switch = lambda profile: calls.append(("switch", profile))
    app.vpn_off = lambda: calls.append("disconnect")

    assert app.get_available_vpn_profiles() == ["alpha", "beta"]
    assert app.get_current_vpn_profile() == "beta"

    app.switch_vpn_profile("alpha")
    app.disconnect_vpn()

    assert calls == ["refresh", ("switch", "alpha"), "disconnect"]


def test_update_primary_vpn_form_controls_skips_destroyed_widgets():
    class DeadWidget:
        def winfo_exists(self):
            return False

        def __setitem__(self, key, value):
            raise AssertionError(f"unexpected widget write: {key}={value}")

    class AliveWidget:
        def __init__(self):
            self.values = None

        def winfo_exists(self):
            return True

        def __setitem__(self, key, value):
            if key != "values":
                raise KeyError(key)
            self.values = value

    app = netmon.App.__new__(netmon.App)
    app.wg_profiles = ["alpha", "beta"]
    app.primary_vpn_1_profile_combo = DeadWidget()
    app.primary_vpn_2_profile_combo = AliveWidget()

    netmon.vpn_controller.update_primary_vpn_form_controls(app)

    assert app.primary_vpn_2_profile_combo.values == ["alpha", "beta"]


def test_set_light_accepts_vpn_indicator_tuple_with_label():
    app = netmon.App.__new__(netmon.App)

    class DummyCanvas:
        def __init__(self):
            self.calls = []

        def itemconfig(self, item, **kwargs):
            self.calls.append((item, kwargs))

    canvas = DummyCanvas()
    light = (canvas, "dot-id", object())

    app.set_light(light, "green")

    assert canvas.calls == [("dot-id", {"fill": "green"})]


def test_run_security_monitor_menu_action_refreshes_light():
    app = netmon.App.__new__(netmon.App)
    calls = []

    app.security_monitoring = False
    app._security_update_status = lambda color: calls.append(("status", color))
    app.after = lambda delay, callback: (calls.append(("after", delay)), callback())

    def start_monitoring():
        calls.append("start")
        app.security_monitoring = True

    app._run_security_monitor_menu_action(start_monitoring)

    assert "start" in calls
    assert ("after", 500) in calls
    assert ("status", "green") in calls


def test_refresh_updates_ufw_logging_light(passive_dns_status, passive_dns_service):
    app = netmon.App.__new__(netmon.App)
    passive_dns_service(app)
    colors = []
    calls = []

    app.check_internet = lambda: True
    app.active_wg_profile = lambda: None
    app.check_ufw_active = lambda: True
    app.check_ssh_rule_active = lambda: True
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda light, color: colors.append((light, color))
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ufw_log = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: ""
    app.get_default_iface = lambda: "enp4s0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_guard_transition_until = 0.0
    app.dns_policy_running = False
    app.dot_running = False
    app.internet_fail_streak = 0
    app.update_ufw_logging_light = lambda: calls.append("ufw-log")

    app.refresh()

    assert calls == ["ufw-log"]
    assert passive_dns_status == [(["resolvectl", "status"], 6)]


def test_refresh_sets_firewall_gray_when_ufw_status_is_not_readable_yet():
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.check_internet = lambda: True
    app.active_wg_profile = lambda: None
    app._read_ufw_status = lambda verbose=False: (1, "")
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda light, color: colors.append((light, color))
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ufw_log = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: ""
    app.get_default_iface = lambda: "enp4s0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_guard_transition_until = 0.0
    app.dns_policy_running = False
    app.dot_running = False
    app.internet_fail_streak = 0
    app.update_ufw_logging_light = lambda: None
    app.update_vpn_status_text = lambda: None

    app.refresh()

    fw_colors = [color for light, color in colors if light is app.l_fw]
    ks_colors = [color for light, color in colors if light is app.l_ks]
    ssh_colors = [color for light, color in colors if light is app.l_ssh]
    assert fw_colors == ["gray"]
    assert ks_colors == ["gray"]
    assert ssh_colors == ["gray"]


def test_refresh_no_longer_starts_dns_consistency_loop(
    passive_dns_status, passive_dns_service
):
    app = netmon.App.__new__(netmon.App)
    passive_dns_service(app)
    app._security_query_log_level = lambda: "LOW"
    calls = []

    app.check_internet = lambda: True
    app.active_wg_profile = lambda: None
    app.check_ufw_active = lambda: True
    app.check_ssh_rule_active = lambda: True
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda *args, **kwargs: None
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: ""
    app.get_default_iface = lambda: "enp4s0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_consistency_enabled = True
    app.dns_consistency_check_async = lambda force=False: calls.append(force)
    app.dns_guard_transition_until = 0.0
    app.dns_policy_running = False
    app.dot_running = False

    app.refresh()

    assert calls == []
    assert passive_dns_status == [(["resolvectl", "status"], 6)]


def test_refresh_sets_internet_warning_on_first_failure_and_red_after_second(
    passive_dns_status, passive_dns_service
):
    app = netmon.App.__new__(netmon.App)
    passive_dns_service(app)
    app._security_query_log_level = lambda: "LOW"
    colors = []

    app.check_internet = lambda: False
    app.active_wg_profile = lambda: None
    app.check_ufw_active = lambda: True
    app.check_ssh_rule_active = lambda: True
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda light, color: colors.append((light, color))
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: ""
    app.get_default_iface = lambda: "enp4s0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_guard_transition_until = 0.0
    app.dns_policy_running = False
    app.dot_running = False
    app.internet_fail_streak = 0

    app.refresh()
    app.refresh()

    inet_colors = [color for light, color in colors if light is app.l_inet]
    assert inet_colors[0] == "yellow"
    assert inet_colors[1] == "red"
    assert passive_dns_status == [(["resolvectl", "status"], 6)] * 2


def test_refresh_sets_internet_transition_yellow_during_dns_transition(
    passive_dns_status, passive_dns_service
):
    app = netmon.App.__new__(netmon.App)
    passive_dns_service(app)
    app._security_query_log_level = lambda: "LOW"
    colors = []

    app.check_internet = lambda: False
    app.active_wg_profile = lambda: None
    app.check_ufw_active = lambda: True
    app.check_ssh_rule_active = lambda: True
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda light, color: colors.append((light, color))
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: ""
    app.get_default_iface = lambda: "enp4s0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_guard_transition_until = 10**12
    app.dns_policy_running = False
    app.dot_running = False
    app.internet_fail_streak = 0

    app.refresh()

    inet_colors = [color for light, color in colors if light is app.l_inet]
    assert inet_colors == ["yellow"]
    assert "Internet TRANSITION" in app.status_text.values["text"]
    assert passive_dns_status == [(["resolvectl", "status"], 6)]


def test_refresh_keeps_internet_yellow_while_suspend_is_pending():
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.check_internet = lambda: True
    app.active_wg_profile = lambda: None
    app.check_ufw_active = lambda: True
    app.check_ssh_rule_active = lambda: True
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda light, color: colors.append((light, color))
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_ufw_logging_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: ""
    app.get_default_iface = lambda: "enp4s0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_guard_transition_until = 0.0
    app.dns_policy_running = False
    app.dot_running = False
    app.internet_fail_streak = 0
    app.internet_suspend_requested = True
    app.internet_suspend_until = 10**12
    app._local_internet_available_for_suspend = lambda: True
    app.update_vpn_status_text = lambda: None
    app.log = lambda _msg: None

    app.refresh()

    inet_colors = [color for light, color in colors if light is app.l_inet]
    assert inet_colors == ["yellow"]
    assert "Internet TRANSITION" in app.status_text.values["text"]
    assert app.internet_suspend_requested is True


def test_refresh_sets_internet_gray_when_suspend_detects_network_is_off():
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.check_internet = lambda: True
    app.active_wg_profile = lambda: None
    app.check_ufw_active = lambda: True
    app.check_ssh_rule_active = lambda: True
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda light, color: colors.append((light, color))
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_ufw_logging_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: ""
    app.get_default_iface = lambda: "enp4s0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_guard_transition_until = 0.0
    app.dns_policy_running = False
    app.dot_running = False
    app.internet_fail_streak = 0
    app.internet_suspend_requested = True
    app.internet_suspend_until = 10**12
    app.internet_suspend_logged_reactivation = False
    app._local_internet_available_for_suspend = lambda: False
    app.update_vpn_status_text = lambda: None
    app.log = lambda _msg: None

    app.refresh()

    inet_colors = [color for light, color in colors if light is app.l_inet]
    assert inet_colors == ["gray"]
    assert "Internet AUS" in app.status_text.values["text"]
    assert app.internet_suspend_requested is False


def test_update_vpn_status_text_shows_live_ip_and_country_when_active():
    app = netmon.App.__new__(netmon.App)
    app.vpn_status_text_var = DummyVar()
    app.is_vpn_active = lambda: True
    app.public_ip = "198.51.100.42"
    app.country = "DE"

    app.update_vpn_status_text()

    assert app.vpn_status_text_var.get() == "VPN: aktiv | IP: 198.51.100.42 | Land: DE"


def test_update_vpn_status_text_hides_ip_and_country_when_vpn_is_off():
    app = netmon.App.__new__(netmon.App)
    app.vpn_status_text_var = DummyVar()
    app.is_vpn_active = lambda: False
    app.public_ip = "198.51.100.42"
    app.country = "DE"

    app.update_vpn_status_text()

    assert app.vpn_status_text_var.get() == "VPN: aus | IP: - | Land: -"


def test_vpn_ip_country_refresh_is_debounced_and_forced_after_route_change():
    app = netmon.App.__new__(netmon.App)
    after_calls = []
    refresh_calls = []
    app.last_ip_ts = 123.0
    app._vpn_ip_refresh_generation = 0
    app.after = lambda delay, callback: after_calls.append((delay, callback))
    app.ip_country_async = lambda force=False: refresh_calls.append(force)

    app._schedule_vpn_ip_country_refresh(delay_ms=750)
    app._schedule_vpn_ip_country_refresh(delay_ms=900)

    assert app.last_ip_ts == 0.0
    assert [delay for delay, _callback in after_calls] == [750, 900]

    after_calls[0][1]()
    after_calls[1][1]()

    assert refresh_calls == [True]


def test_forced_ip_country_refresh_waits_for_running_request(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    thread_targets = []
    after_calls = []

    class CapturingThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            thread_targets.append(self.target)

    monkeypatch.setattr(netmon.threading, "Thread", CapturingThread)
    monkeypatch.setattr(
        netmon,
        "run_cmd",
        lambda _args, timeout=0: (0, "198.51.100.42"),
    )

    app.ip_country_running = False
    app.last_ip_ts = 0.0
    app.auto_external_checks = DummyVar(True)
    app._fetch_country_from_ipinfo = lambda timeout_s=3: ("DE", "")
    app._update_ip_country_ui = lambda: None
    app.after = lambda delay, callback: after_calls.append((delay, callback))

    app.ip_country_async(force=False)
    app.ip_country_async(force=True)

    assert len(thread_targets) == 1
    assert app._ip_country_force_pending is True

    thread_targets[0]()
    assert app.ip_country_running is False

    assert len(after_calls) == 2
    pending_force_callback = after_calls[-1][1]
    pending_force_callback()

    assert len(thread_targets) == 2
    assert app.ip_country_running is True


def test_refresh_updates_vpn_status_text():
    app = netmon.App.__new__(netmon.App)
    colors = []
    calls = []

    app.check_internet = lambda: True
    app.active_wg_profile = lambda: "wg-de"
    app.check_ufw_active = lambda: True
    app.check_ssh_rule_active = lambda: True
    app.killswitch_is_on = lambda: False
    app.update_ipv6_controls_state = lambda: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app.sync_vpn_profile_form_selection = lambda: None
    app.update_dns_header = lambda: None
    app.update_wg_rates = lambda: None
    app.set_light = lambda light, color: colors.append((light, color))
    app.l_inet = object()
    app.l_vpn = object()
    app.l_fw = object()
    app.l_ssh = object()
    app.l_ks = object()
    app.l_ipv6 = object()
    app.dns_choice = DummyVar("Cloudflare")
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app._update_dns_consistency_light = lambda: None
    app._update_dot_light = lambda: None
    app.update_ufw_logging_light = lambda: None
    app.update_vpn_slot_buttons = lambda: None
    app.refresh_vpn_slots_table = lambda: None
    app.ip_country_async = lambda force=False: None
    app.whoami_async = lambda force=False: None
    app.get_wg_iface = lambda: "wg0"
    app.get_default_iface = lambda: "wg0"
    app.profile_supports_ipv6 = lambda profile: False
    app.ipv6_is_disabled = lambda: False
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.info = DummyVar()
    app.wg_rx_rate = 0.0
    app.wg_tx_rate = 0.0
    app.public_ip = "198.51.100.42"
    app.country = "DE"
    app.isp_stealth_enabled = DummyVar(False)
    app.status_text = DummyTkLabel()
    app.refresh_dns_policy_status = lambda: None
    app.refresh_security_summary = lambda: None
    app.update_dns_controls_state = lambda: None
    app.update_ipv6_controls_state_safe = lambda: None
    app.system_monitor_refresh = lambda: None
    app.dns_guard_transition_until = 0.0
    app.dns_policy_running = False
    app.dot_running = False
    app.internet_fail_streak = 0
    app.update_vpn_status_text = lambda: calls.append("vpn-status")

    app.refresh()

    assert calls == ["vpn-status"]


def test_fix_dns_conflicts_async_only_evaluates(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []

    app.dns_policy_running = False
    app.nb = type("DummyNotebook", (), {"select": lambda self, tab: None})()
    app.tab_dns = object()
    app.log_safe = logs.append
    app._run_dns_policy_action = lambda startup=False, repair_only=False: calls.append(
        (startup, repair_only)
    )
    app.ensure_sudo_session = lambda reason: (_ for _ in ()).throw(
        AssertionError("sudo must not be requested for pure DNS status evaluation")
    )

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    app.fix_dns_conflicts_async()

    assert calls == [(False, True)]
    assert logs == ["DNS-Status wird bewertet"]


def test_update_dot_light_marks_vpn_states():
    app = netmon.App.__new__(netmon.App)
    colors = []

    app.l_dot = object()
    app.set_light = lambda _light, color: colors.append(color)
    app.dot_last_test_ok = None
    app.dot_enabled = True
    app.dot_vpn_dns_active = True
    app.dot_vpn_conflict = False

    app._update_dot_light()
    assert colors[-1] == "green"

    app.dot_enabled = False
    app._update_dot_light()
    assert colors[-1] == "yellow"

    app.dot_vpn_conflict = True
    app._update_dot_light()
    assert colors[-1] == "red"


def test_restore_isp_dns_after_vpn_uses_cloudflare_fallback():
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.settings = {}
    app.dns_choice = DummyVar("System (DHCP/auto)")
    app.custom_dns_profile_choices = []
    app.is_vpn_active = lambda: False
    app._auto_dns_control_available = lambda: True
    app.apply_dns = lambda **kwargs: calls.append(kwargs) or True
    app.log_safe = logs.append

    assert app._restore_isp_dns_after_vpn_switch() is True
    assert calls == [
        {
            "choice": "Cloudflare (1.1.1.1)",
            "refresh_ui": False,
            "update_choice_var": True,
            "confirm_dnssec": False,
        }
    ]
    assert logs == ["DNS nach VPN-Aus gesetzt: Cloudflare (1.1.1.1)"]


def test_restore_isp_dns_after_vpn_prefers_selected_dns_choice():
    app = netmon.App.__new__(netmon.App)
    calls = []

    app.settings = {"isp_dns_fallback_profile": "Cloudflare (1.1.1.1)"}
    app.dns_choice = DummyVar("Quad9 (malware-blocking)")
    app.custom_dns_profile_choices = []
    app.is_vpn_active = lambda: False
    app._auto_dns_control_available = lambda: True
    app.apply_dns = lambda **kwargs: calls.append(kwargs) or True
    app.log_safe = lambda _message: None

    assert app._restore_isp_dns_after_vpn_switch() is True
    assert calls[0]["choice"] == "Quad9 (malware-blocking)"


def test_restore_isp_dns_after_vpn_skips_during_internet_vpn_restore():
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.internet_vpn_restore_active = True
    app.settings = {}
    app.dns_choice = DummyVar("System (DHCP/auto)")
    app.custom_dns_profile_choices = []
    app.is_vpn_active = lambda: False
    app._auto_dns_control_available = lambda: True
    app.apply_dns = lambda **kwargs: calls.append(kwargs) or True
    app.log_network_debug = logs.append

    assert app._restore_isp_dns_after_vpn_switch() is False
    assert calls == []
    assert logs == ["[DEBUG] DNS nach VPN-Aus übersprungen: Internet-AN-Restore aktiv."]


def test_apply_automatic_dns_restore_choice_bypasses_ui_lock_during_transition():
    app = netmon.App.__new__(netmon.App)
    calls = []

    app._dns_runtime_transition_active = lambda: True
    app._set_dns_choice_safe = lambda choice: calls.append(("set", choice))
    app._apply_dns_profile_choice_via_control = lambda choice: calls.append(
        ("control", choice)
    ) or {"success": True}
    app.refresh_dns_policy_status = lambda: calls.append(("refresh", None))
    app.apply_dns = lambda **kwargs: calls.append(("apply_dns", kwargs)) or False
    app.log_safe = lambda _message: None

    assert app._apply_automatic_dns_restore_choice("Cloudflare (1.1.1.1)") is True
    assert calls == [
        ("set", "Cloudflare (1.1.1.1)"),
        ("control", "Cloudflare (1.1.1.1)"),
        ("refresh", None),
    ]


def test_restore_isp_dns_on_startup_uses_fallback_without_active_dns(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    debug_logs = []
    calls = []

    app.is_vpn_active = lambda: False
    app._auto_dns_control_available = lambda: True
    app._parse_active_dns_servers = lambda _out: []
    app._restore_isp_dns_after_vpn_switch = lambda: calls.append("restore") or True
    app.log_safe = logs.append
    app.log_network_debug = debug_logs.append

    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "resolvectl")
    monkeypatch.setattr(netmon, "run_cmd", lambda args, timeout=0: (0, "Global\n"))

    assert app._restore_isp_dns_on_startup_if_needed() is True
    assert calls == ["restore"]
    assert logs == [
        "DNS-Startup-Fallback wird angewendet: keine aktiven DNS-Server erkannt."
    ]
    assert debug_logs == []


def test_restore_isp_dns_on_startup_skips_when_dns_already_present(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    debug_logs = []
    calls = []

    app.is_vpn_active = lambda: False
    app._auto_dns_control_available = lambda: True
    app._parse_active_dns_servers = lambda _out: ["1.1.1.1"]
    app._restore_isp_dns_after_vpn_switch = lambda: calls.append("restore") or True
    app.log_network_debug = debug_logs.append

    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "resolvectl")
    monkeypatch.setattr(
        netmon, "run_cmd", lambda args, timeout=0: (0, "DNS Servers: 1.1.1.1")
    )

    assert app._restore_isp_dns_on_startup_if_needed() is False
    assert calls == []
    assert debug_logs == [
        "[DEBUG] DNS-Startup-Fallback übersprungen: aktive DNS-Server vorhanden."
    ]
