import threading

from tools import netmon


class DummyWidget:
    def __init__(self):
        self.state = None
        self.text = ""

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "text" in kwargs:
            self.text = kwargs["text"]

    config = configure


class DestroyedWidget(DummyWidget):
    def winfo_exists(self):
        return 0

    def configure(self, **kwargs):
        raise RuntimeError('invalid command name ".!label"')

    config = configure


class BrokenConfigWidget(DummyWidget):
    def winfo_exists(self):
        return 1

    def configure(self, **kwargs):
        raise RuntimeError('invalid command name ".!label"')

    config = configure


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_profile_supports_ipv6_detects_address_dns_allowedips_and_endpoint(monkeypatch):
    app = netmon.App.__new__(netmon.App)

    configs = {
        "addr": "[Interface]\nAddress = 10.0.0.2/32, fd00::2/128\n",
        "dns": "[Interface]\nDNS = 1.1.1.1, 2606:4700:4700::1111\n",
        "allowed": "[Peer]\nAllowedIPs = 0.0.0.0/0, ::/0\n",
        "endpoint": "[Peer]\nEndpoint = [2001:db8::1]:51820\n",
        "ipv4only": "[Interface]\nAddress = 10.0.0.2/32\nDNS = 1.1.1.1\n[Peer]\nAllowedIPs = 0.0.0.0/0\nEndpoint = 198.51.100.10:51820\n",
    }

    def fake_run_cmd(args, timeout=0, text=True):
        profile = args[-1].split("/")[-1].replace(".conf", "")
        return 0, configs[profile]

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app.profile_supports_ipv6("addr") is True
    assert app.profile_supports_ipv6("dns") is True
    assert app.profile_supports_ipv6("allowed") is True
    assert app.profile_supports_ipv6("endpoint") is True
    assert app.profile_supports_ipv6("ipv4only") is False


def test_update_ipv6_controls_state_keeps_left_buttons_enabled_for_active_ipv4_only_vpn():
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.btn_ipv6_on = DummyWidget()
    app.btn_ipv6_off = DummyWidget()
    app.ipv6_controls_hint = DummyWidget()
    app.cb_privacy_ipv6 = DummyWidget()
    app.privacy_ipv6_hint = DummyWidget()
    app.isp_stealth_vpn_profile = DummyVar("proton")
    app.isp_stealth_vpn_choice = DummyVar("Proton CH")
    app.active_wg_profile = lambda: "wg0"
    app._privacy_vpn_profile_from_value = lambda value: "proton"
    app.profile_supports_ipv6 = lambda profile: False

    app.update_ipv6_controls_state()

    assert app.btn_ipv6_on.state == "normal"
    assert app.btn_ipv6_off.state == "normal"
    assert app.cb_privacy_ipv6.state == "disabled"
    assert (
        app.ipv6_controls_hint.text
        == "IPv6 Status:\nSystem:        aktiv\nVPN-Profil:    nutzt nur IPv4"
    )
    assert app.privacy_ipv6_hint.text == "Aktives VPN-Profil nutzt nur IPv4"


def test_update_ipv6_controls_state_keeps_left_buttons_enabled_without_active_vpn():
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.btn_ipv6_on = DummyWidget()
    app.btn_ipv6_off = DummyWidget()
    app.ipv6_controls_hint = DummyWidget()
    app.cb_privacy_ipv6 = DummyWidget()
    app.privacy_ipv6_hint = DummyWidget()
    app.isp_stealth_vpn_profile = DummyVar("proton")
    app.isp_stealth_vpn_choice = DummyVar("Proton CH")
    app.active_wg_profile = lambda: None
    app._privacy_vpn_profile_from_value = lambda value: "proton"
    app.profile_supports_ipv6 = lambda profile: False

    app.update_ipv6_controls_state()

    assert app.btn_ipv6_on.state == "normal"
    assert app.btn_ipv6_off.state == "normal"
    assert app.cb_privacy_ipv6.state == "disabled"
    assert (
        app.ipv6_controls_hint.text
        == "IPv6 Status:\nSystem:        aktiv\nVPN-Profil:    kein aktives Profil"
    )
    assert app.privacy_ipv6_hint.text == "Gewaehltes Privacy-VPN-Profil nutzt nur IPv4"


def test_update_ipv6_controls_state_ignores_destroyed_hint_widgets():
    app = netmon.App.__new__(netmon.App)
    app.ufw_lock = threading.Lock()
    app.btn_ipv6_on = DummyWidget()
    app.btn_ipv6_off = DummyWidget()
    app.ipv6_controls_hint = DestroyedWidget()
    app.cb_privacy_ipv6 = DummyWidget()
    app.privacy_ipv6_hint = BrokenConfigWidget()
    app.isp_stealth_vpn_profile = DummyVar("proton")
    app.isp_stealth_vpn_choice = DummyVar("Proton CH")
    app.active_wg_profile = lambda: None
    app._privacy_vpn_profile_from_value = lambda value: "proton"
    app.profile_supports_ipv6 = lambda profile: False

    app.update_ipv6_controls_state()

    assert app.btn_ipv6_on.state == "normal"
    assert app.btn_ipv6_off.state == "normal"
    assert app.cb_privacy_ipv6.state == "disabled"


def test_build_ipv4_only_wg_profile_content_filters_ipv6_tokens():
    app = netmon.App.__new__(netmon.App)
    app._read_wg_profile_text = lambda profile: (
        0,
        """[Interface]
Address = 10.0.0.2/32, fd00::2/128
DNS = 1.1.1.1, 2606:4700:4700::1111
[Peer]
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = 198.51.100.10:51820
""",
    )

    content, reason = app.build_ipv4_only_wg_profile_content("wg-mixed")

    assert reason == ""
    assert content == """[Interface]
Address = 10.0.0.2/32
DNS = 1.1.1.1
[Peer]
AllowedIPs = 0.0.0.0/0
Endpoint = 198.51.100.10:51820
"""


def test_resolve_runtime_vpn_profile_uses_internal_ipv4_copy_when_ipv6_is_disabled():
    app = netmon.App.__new__(netmon.App)
    app.ipv6_is_disabled = lambda: True
    app._wg_profile_exists = lambda profile: profile == "wg-slot__ipv4"
    app.ensure_internal_ipv4_profile = lambda profile, log_failures=True: False
    app.log_safe = lambda message: None

    assert app.resolve_runtime_vpn_profile("wg-slot") == "wg-slot__ipv4"


def test_resolve_runtime_vpn_profile_logs_when_no_ipv4_copy_is_available():
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.ipv6_is_disabled = lambda: True
    app._wg_profile_exists = lambda profile: False
    app.ensure_internal_ipv4_profile = lambda profile, log_failures=True: False
    app.log_safe = logs.append

    assert app.resolve_runtime_vpn_profile("wg-ipv6") == ""
    assert logs == [
        "VPN Start abgebrochen: Fuer Profil 'wg-ipv6' ist keine interne IPv4-only Kopie verfuegbar.",
        "Bitte IPv6 aktivieren oder ein Profil mit nutzbaren IPv4-Eintraegen verwenden.",
    ]


def test_vpn_switch_uses_ipv4_runtime_profile_when_ipv6_is_disabled(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    refreshes = []
    run_calls = []

    app.ensure_sudo_session = lambda label: True
    app.ipv6_is_disabled = lambda: True
    app.profile_supports_ipv6 = lambda profile: True
    app._wg_profile_exists = lambda profile: profile in {
        "wg-old",
        "wg-ipv6",
        "wg-ipv6__ipv4",
    }
    app.log_safe = logs.append
    app.log_debug = lambda *args: None
    app.log_debug_safe = lambda *args: None
    app.refresh_safe = lambda: refreshes.append(True)
    app.get_wg_iface = lambda: ""
    app.get_wg_interfaces = lambda: ["wg-old"]
    app.refresh_wg_profiles = lambda: refreshes.append("profiles")
    app.update_ipv6_controls_state_safe = lambda: refreshes.append("ipv6")
    app.killswitch_is_on = lambda: False
    app.prepare_dns_for_vpn_profile_switch = lambda: []
    app._schedule_dns_finalize_after_vpn_profile_switch = lambda delay_ms=2500: None
    app.run_async = lambda func: func()
    app.verify_vpn_exit_country = lambda profile: None
    app.update_primary_vpn_form_controls = lambda: None
    app.sync_primary_vpn_form_selection = lambda: None
    app._check_wireguard_profile_for_multiple_endpoints = lambda *args: None

    def fake_run_cmd(args, timeout=0, text=True):
        run_calls.append(args)
        return 0, ""

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app.vpn_switch("wg-ipv6", ensure_sudo=False, refresh_ui=True) is True
    assert [
        "sudo",
        "-n",
        "test",
        "-f",
        "/etc/wireguard/wg-ipv6__ipv4.conf",
    ] in run_calls
    assert ["sudo", "-n", "wg-quick", "down", "wg-old"] in run_calls
    assert ["sudo", "-n", "wg-quick", "up", "wg-ipv6__ipv4"] in run_calls
    assert "VPN gestartet: wg-ipv6" in logs
    assert refreshes == ["profiles", "ipv6", True]
