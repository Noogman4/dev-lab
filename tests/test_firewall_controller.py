from netmon.features import firewall_controller
from tools import netmon


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_add_firewall_rule_form_values_normalize_blank_source_to_any():
    app = type("DummyApp", (), {})()
    app.add_firewall_rule_action_var = DummyVar("Erlauben")
    app.add_firewall_rule_direction_var = DummyVar("Eingehend")
    app.add_firewall_rule_protocol_var = DummyVar("TCP")
    app.add_firewall_rule_port_var = DummyVar("443")
    app.add_firewall_rule_source_var = DummyVar("   ")

    values = firewall_controller._add_firewall_rule_form_values(app)

    assert values == {
        "action_label": "Erlauben",
        "direction_label": "Eingehend",
        "protocol_label": "TCP",
        "port_text": "443",
        "source_text": "any",
    }


def test_add_firewall_rule_protocols_expand_tcp_udp_combo():
    assert firewall_controller._add_firewall_rule_protocols("TCP") == ("tcp",)
    assert firewall_controller._add_firewall_rule_protocols("UDP") == ("udp",)
    assert firewall_controller._add_firewall_rule_protocols("TCP + UDP") == (
        "tcp",
        "udp",
    )


def test_refresh_firewall_transparency_view_keeps_active_text_selection():
    app = netmon.App.__new__(netmon.App)

    class DummySummary:
        def __init__(self):
            self.calls = []

        def tag_ranges(self, tag):
            assert tag == "sel"
            return ("1.0", "1.4")

        def configure(self, **kwargs):
            self.calls.append(("configure", kwargs))

        def delete(self, start, end):
            self.calls.append(("delete", start, end))

        def insert(self, start, text):
            self.calls.append(("insert", start, text))

    app.firewall_tab_summary_text = DummySummary()
    app._collect_firewall_transparency_snapshot = lambda: {
        "status_label": "aktiv",
        "default_in": "deny",
        "default_out": "allow",
        "logging": "on",
        "rule_count": 3,
        "external_open_count": 0,
        "listener_count": 1,
        "last_check": "jetzt",
        "rules": [],
        "listeners": [],
        "summary_lines": ["A", "B"],
    }

    snapshot = app.refresh_firewall_transparency_view()

    assert snapshot["summary_lines"] == ["A", "B"]
    assert app.firewall_tab_summary_text.calls == []


def test_build_add_firewall_rule_command_args_uses_normalized_form_values():
    app = type("DummyApp", (), {})()
    app.add_firewall_rule_action_var = DummyVar("Blockieren")
    app.add_firewall_rule_direction_var = DummyVar("Ausgehend")
    app.add_firewall_rule_protocol_var = DummyVar("TCP + UDP")
    app.add_firewall_rule_port_var = DummyVar("53")
    app.add_firewall_rule_source_var = DummyVar("")

    validation, commands = firewall_controller._build_add_firewall_rule_command_args(
        app
    )

    assert validation["valid"] is True
    assert commands == [
        [
            "sudo",
            "-n",
            "ufw",
            "deny",
            "out",
            "proto",
            "tcp",
            "from",
            "any",
            "to",
            "any",
            "port",
            "53",
        ],
        [
            "sudo",
            "-n",
            "ufw",
            "deny",
            "out",
            "proto",
            "udp",
            "from",
            "any",
            "to",
            "any",
            "port",
            "53",
        ],
    ]
