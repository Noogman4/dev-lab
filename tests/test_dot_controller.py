from datetime import datetime

from netmon.features import dot_controller


class DummyVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_vpn_dns_active_state_prefers_app_callback():
    app = type(
        "DummyApp",
        (),
        {"is_vpn_dns_active": lambda self: (True, "callback-result")},
    )()

    assert dot_controller._vpn_dns_active_state(app) == (True, "callback-result")


def test_vpn_dns_active_state_falls_back_to_controller_helper(monkeypatch):
    monkeypatch.setattr(
        dot_controller,
        "is_vpn_dns_active",
        lambda app: (False, "fallback-result"),
    )
    app = type("DummyApp", (), {})()

    assert dot_controller._vpn_dns_active_state(app) == (False, "fallback-result")


def test_confirm_dot_activation_defaults_to_true_without_callback():
    app = type("DummyApp", (), {})()

    assert dot_controller._confirm_dot_activation(app, "DoT aktivieren") is True


def test_confirm_dot_activation_uses_app_callback():
    calls = []
    app = type(
        "DummyApp",
        (),
        {
            "confirm_dnssec_mode_activation": lambda self, action: calls.append(action)
            or False
        },
    )()

    assert dot_controller._confirm_dot_activation(app, "DoT aktivieren") is False
    assert calls == ["DoT aktivieren"]


def test_resolved_dot_profile_name_prefers_dropin_servers():
    profile = dot_controller._resolved_dot_profile_name(
        {"servers": ["1.1.1.1", "1.0.0.1"]},
        {"servers": ["9.9.9.9", "149.112.112.112"]},
    )

    assert profile == "Cloudflare"


def test_resolved_dot_profile_name_uses_status_servers_when_dropin_empty():
    profile = dot_controller._resolved_dot_profile_name(
        {"servers": []},
        {"servers": ["9.9.9.9", "149.112.112.112"]},
    )

    assert profile == "Quad9"


def test_resolved_dot_mode_falls_back_from_dropin_to_status():
    assert (
        dot_controller._resolved_dot_mode({"mode": "–"}, {"mode": "opportunistic"})
        == "opportunistic"
    )
    assert dot_controller._resolved_dot_mode({"mode": "yes"}, {"mode": "no"}) == "yes"


def test_dot_profile_server_and_mode_text_helpers():
    assert dot_controller._dot_profile_text("Cloudflare") == "Profil: Cloudflare"
    assert dot_controller._dot_server_text(["1.1.1.1", "1.0.0.1"]) == (
        "Server: 1.1.1.1, 1.0.0.1"
    )
    assert dot_controller._dot_server_text([]) == "Server: –"
    assert dot_controller._dot_mode_text("yes") == "Modus: yes"
    assert dot_controller._dot_mode_text("") == "Modus: –"


def test_dot_last_test_text_formats_timestamp():
    assert dot_controller._dot_last_test_text(
        1710000000
    ) == "Letzter Test: " + datetime.fromtimestamp(1710000000).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def test_dot_status_text_marks_enabled_unknown_as_active():
    app = type("DummyApp", (), {"dot_enabled": True, "dot_vpn_conflict": False})()

    assert dot_controller._dot_status_text(app, None) == "DoT: aktiv"


def test_dot_test_hint_text_warns_for_unclear_or_failed_runtime_test():
    assert (
        dot_controller._dot_test_hint_text(
            {"enabled": True, "text": "Test: unklar\nResolver-Abfrage: Timeout"}
        )
        == "Hinweis: Für den DoT-Test Killswitch kurz AUS schalten."
    )
    assert (
        dot_controller._dot_test_hint_text(
            {"enabled": True, "text": "Test: fehlgeschlagen\nTLS-Probe: fehlgeschlagen"}
        )
        == "Hinweis: Für den DoT-Test Killswitch kurz AUS schalten."
    )
    assert dot_controller._dot_test_hint_text({"enabled": True, "text": "Test: erfolgreich"}) == ""


def test_collect_dot_status_treats_timeouts_as_unclear(monkeypatch):
    app = type(
        "DummyApp",
        (),
        {
            "__dict__": {},
            "_dns_control_service": lambda self: None,
            "detect_vpn_active": lambda self, _text: False,
        },
    )()

    monkeypatch.setattr(
        dot_controller,
        "dot_preflight",
        lambda: {
            "checks": {"systemctl": True, "resolvectl": True},
            "resolved_active": True,
            "resolved_state": "active",
        },
    )
    monkeypatch.setattr(
        dot_controller,
        "read_dot_dropin",
        lambda _app: "[Resolve]\nDNS=1.1.1.1#cloudflare-dns.com\nDNSOverTLS=yes\n",
    )
    monkeypatch.setattr(
        dot_controller,
        "detect_netmon_dot_dropin_conflict",
        lambda _app: (True, ""),
    )

    def fake_run_cmd(args, timeout=0):
        if args == ["resolvectl", "dns"]:
            return 0, "Global: 1.1.1.1#cloudflare-dns.com"
        if args == ["resolvectl", "status"]:
            return 0, "DNSOverTLS setting: yes\nCurrent DNS Server: 1.1.1.1#cloudflare-dns.com"
        if args == ["resolvectl", "query", "example.com"]:
            return 124, "Command timed out"
        raise AssertionError(args)

    monkeypatch.setattr(dot_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        dot_controller,
        "dot_tls_probe",
        lambda _server, _hostname, timeout=4: (
            False,
            "TLS-Verbindung zu 1.1.1.1:853 fehlgeschlagen: timed out",
        ),
    )

    status = dot_controller.collect_dot_status(app, run_test=True)

    assert status["enabled"] is True
    assert status["ok"] is None
    assert "Test: unklar" in status["text"]
    assert "Resolver-Abfrage: Timeout" in status["text"]
    assert "TLS-Probe: Timeout" in status["text"]
