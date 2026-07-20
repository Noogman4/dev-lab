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


def test_parse_ufw_structured_rule_extracts_out_interface_from_source_field():
    rule = firewall_controller.parse_ufw_structured_rule(
        "Anywhere ALLOW OUT Anywhere on CH-685"
    )

    assert rule["policy"] == "ALLOW"
    assert rule["direction"] == "OUT"
    assert rule["display"] == "Anywhere"
    assert rule["interface"] == "CH-685"
    assert rule["to"] == "Anywhere"
    assert rule["from"] == "Anywhere"


def test_format_ufw_rule_lines_formats_interface_rules_with_spacing():
    rules = [
        firewall_controller.parse_ufw_structured_rule(
            "Anywhere on lo ALLOW IN Anywhere"
        ),
        firewall_controller.parse_ufw_structured_rule(
            "Anywhere on CH-685 ALLOW IN Anywhere"
        ),
        firewall_controller.parse_ufw_structured_rule(
            "Anywhere (v6) on CH-685 ALLOW IN Anywhere (v6)"
        ),
    ]

    assert firewall_controller.format_ufw_rule_lines(rules) == [
        "ALLOW IN  Anywhere on CH-685",
        "ALLOW IN  Anywhere (v6) on CH-685",
        "ALLOW IN  Anywhere on lo",
    ]


def test_format_ufw_rule_lines_only_marks_true_duplicates():
    rules = [
        firewall_controller.parse_ufw_structured_rule(
            "Anywhere on CH-685 ALLOW IN Anywhere"
        ),
        firewall_controller.parse_ufw_structured_rule(
            "Anywhere on CH-685 ALLOW IN Anywhere"
        ),
        firewall_controller.parse_ufw_structured_rule(
            "Anywhere ALLOW OUT Anywhere on CH-685"
        ),
        firewall_controller.parse_ufw_structured_rule(
            "Anywhere (v6) on CH-685 ALLOW IN Anywhere (v6)"
        ),
    ]

    lines = firewall_controller.format_ufw_rule_lines(rules)

    assert "ALLOW IN  Anywhere on CH-685 [DUP x2]" in lines
    assert "ALLOW OUT Anywhere on CH-685" in lines
    assert "ALLOW IN  Anywhere (v6) on CH-685" in lines
    assert all("Anywhereon" not in line for line in lines)


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


def test_parse_firewall_listener_line_recognizes_netmon_cgroup_scope():
    app = netmon.App.__new__(netmon.App)

    row = app._parse_firewall_listener_line(
        "udp UNCONN 0 0 0.0.0.0:58452 0.0.0.0:* "
        "uid:1000 ino:12345 sk:1 cgroup:/user.slice/user-1000.slice/"
        "user@1000.service/app.slice/app-gnome-netmon-999.scope <->"
    )

    assert row == {
        "proto": "udp",
        "host": "0.0.0.0",
        "port": 58452,
        "process": "NetMon",
        "pid": "-",
        "cgroup": "/user.slice/user-1000.slice/user@1000.service/app.slice/app-gnome-netmon-999.scope",
        "scope": "external",
    }


def test_build_firewall_listener_assessment_marks_netmon_scope_as_self_check():
    app = netmon.App.__new__(netmon.App)
    app.lang = {}

    result = app._build_firewall_listener_assessment(
        {
            "proto": "udp",
            "host": "0.0.0.0",
            "port": 58452,
            "process": "NetMon",
            "pid": "-",
            "cgroup": "/user.slice/user-1000.slice/user@1000.service/app.slice/app-gnome-netmon-999.scope",
            "scope": "external",
        },
        [],
    )

    assert result == {
        "firewall": "self",
        "rating": "UDP-Port gehoert zu NetMon selbst, pruefen ob Bindung auf alle Interfaces noetig ist",
        "priority": "check",
    }


def test_describe_firewall_listener_owner_uses_netmon_app_scope():
    app = netmon.App.__new__(netmon.App)

    owner = app._describe_firewall_listener_owner(
        {
            "process": "NetMon",
            "pid": "-",
            "cgroup": "/user.slice/user-1000.slice/user@1000.service/app.slice/app-gnome-netmon-999.scope",
        }
    )

    assert owner == "NetMon app scope (app-gnome-netmon-999.scope, PID -)"


def test_build_firewall_transparency_report_includes_owner_note():
    app = netmon.App.__new__(netmon.App)
    app.lang = {}
    app._collect_firewall_transparency_snapshot = lambda: {
        "summary_lines": ["UFW: active", "NetMon eigene Listener: 1"],
        "rules": [],
        "listeners": [
            {
                "port": 58452,
                "proto": "udp",
                "process": "NetMon",
                "host": "0.0.0.0",
                "firewall": "self",
                "rating": "UDP-Port gehoert zu NetMon selbst, pruefen ob Bindung auf alle Interfaces noetig ist",
                "owner_note": "NetMon app scope (app-gnome-netmon-999.scope, PID -)",
            }
        ],
    }

    report = app.build_firewall_transparency_report()

    assert "NetMon eigene Listener: 1" in report
    assert "NetMon app scope (app-gnome-netmon-999.scope, PID -)" in report


def test_collect_firewall_transparency_snapshot_uses_german_defaults_for_ratings():
    app = netmon.App.__new__(netmon.App)
    app.lang = {}
    app._read_ufw_status = lambda verbose=True: (1, "")
    app._security_query_log_level = lambda: "LOW"
    app.__dict__["port_reality_last_scan"] = {}

    def fake_run_cmd(cmd, timeout=8):
        return (
            0,
            "tcp LISTEN 0 0 127.0.0.53%lo:53 0.0.0.0:* uid:991 ino:1 sk:1",
        )

    original = netmon.run_cmd
    netmon.run_cmd = fake_run_cmd
    try:
        snapshot = app._collect_firewall_transparency_snapshot()
    finally:
        netmon.run_cmd = original

    assert snapshot["last_check"] == "Noch kein Check"
    assert snapshot["listeners"][0]["rating"] == "nur lokal gebunden"


def test_collect_firewall_transparency_snapshot_uses_english_translations_when_loaded():
    app = netmon.App.__new__(netmon.App)
    app.lang = {
        "firewall_listener_last_check_none": "No check yet",
        "firewall_listener_rating_local_only": "bound locally only",
    }
    app._read_ufw_status = lambda verbose=True: (1, "")
    app._security_query_log_level = lambda: "LOW"
    app.__dict__["port_reality_last_scan"] = {}

    def fake_run_cmd(cmd, timeout=8):
        return (
            0,
            "tcp LISTEN 0 0 127.0.0.53%lo:53 0.0.0.0:* uid:991 ino:1 sk:1",
        )

    original = netmon.run_cmd
    netmon.run_cmd = fake_run_cmd
    try:
        snapshot = app._collect_firewall_transparency_snapshot()
    finally:
        netmon.run_cmd = original

    assert snapshot["last_check"] == "No check yet"
    assert snapshot["listeners"][0]["rating"] == "bound locally only"


def test_collect_firewall_transparency_snapshot_marks_auth_pending_without_sudo(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.lang = {}
    app._read_ufw_status = lambda verbose=True: (1, "")
    app._security_query_log_level = lambda: "LOW"
    app.__dict__["port_reality_last_scan"] = {}

    def fake_run_cmd(cmd, timeout=8):
        return (
            0,
            "tcp LISTEN 0 0 127.0.0.53%lo:53 0.0.0.0:* uid:991 ino:1 sk:1",
        )

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: False)

    snapshot = app._collect_firewall_transparency_snapshot()

    assert snapshot["status_label"] == "Autorisierung ausstehend"
