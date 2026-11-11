import pytest

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


def test_parse_ufw_structured_rule_formats_standard_port_display():
    rule = firewall_controller.parse_ufw_structured_rule("22/tcp ALLOW IN Anywhere")

    assert rule["category"] == "standard_port"
    assert rule["display"] == "22/tcp"
    assert rule["port"] == "22"
    assert rule["proto"] == "tcp"


def test_parse_ufw_structured_rule_formats_vpn_endpoint_display():
    rule = firewall_controller.parse_ufw_structured_rule(
        "66.234.146.66 51820/udp ALLOW OUT Anywhere"
    )

    assert rule["category"] == "vpn_endpoint"
    assert rule["display"] == "66.234.146.66:51820/udp"
    assert rule["ip"] == "66.234.146.66"
    assert rule["port"] == "51820"
    assert rule["proto"] == "udp"


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


def test_collect_firewall_transparency_snapshot_uses_german_defaults_for_ratings(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.lang = {}
    app._read_ufw_status = lambda verbose=True: (1, "")
    app._security_query_log_level = lambda: "LOW"
    app.__dict__["port_reality_last_scan"] = {}

    # Authorization is outside this synthetic snapshot/translation test.
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: False)

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


def test_collect_firewall_transparency_snapshot_uses_english_translations_when_loaded(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.lang = {
        "firewall_listener_last_check_none": "No check yet",
        "firewall_listener_rating_local_only": "bound locally only",
    }
    app._read_ufw_status = lambda verbose=True: (1, "")
    app._security_query_log_level = lambda: "LOW"
    app.__dict__["port_reality_last_scan"] = {}

    # Authorization is outside this synthetic snapshot/translation test.
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: False)

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


@pytest.mark.parametrize("ports", ["80,443", "6000:6007", "80,443,6000:6007"])
@pytest.mark.parametrize("endpoint", [False, True])
def test_multiport_display_consumers_preserve_the_expression(ports, endpoint):
    target = ("198.51.100.77 " if endpoint else "") + ports
    proto = "udp" if endpoint else "tcp"
    rule = firewall_controller.parse_ufw_structured_rule(
        f"{target}/{proto} ALLOW IN Anywhere"
    )
    assert rule["port"] == ports
    assert ports in "\n".join(firewall_controller.format_ufw_rule_lines([rule]))
    assert ports in firewall_controller.format_ufw_status_grouped(
        "active", "deny", "allow", [rule]
    )


@pytest.mark.parametrize("endpoint", [False, True])
def test_multiport_display_sorts_by_first_port_number(endpoint):
    prefix = "198.51.100.77 " if endpoint else ""
    proto = "udp" if endpoint else "tcp"
    expressions = ["6000:6007", "80,443", "22", "100,200:300"]
    rules = [
        firewall_controller.parse_ufw_structured_rule(
            f"{prefix}{p}/{proto} ALLOW IN Anywhere"
        )
        for p in expressions
    ]
    lines = firewall_controller.format_ufw_rule_lines(rules)
    assert [next(p for p in expressions if p in row) for row in lines] == [
        "22",
        "80,443",
        "100,200:300",
        "6000:6007",
    ]


@pytest.mark.parametrize("value", [None, "", "invalid"])
@pytest.mark.parametrize("category", ["standard_port", "vpn_endpoint"])
def test_port_sort_key_has_a_safe_fallback(value, category):
    rule = {"category": category, "port": value, "ip": "198.51.100.77"}
    key = firewall_controller.ufw_rule_sort_key(rule)
    assert key[0 if category == "standard_port" else 1] == 0


@pytest.mark.parametrize("mode", ["log", "log-all"])
@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("position", ["target", "source"])
def test_logging_suffix_keeps_interface_and_display_identity(mode, ipv6, position):
    suffix = " (v6)" if ipv6 else ""
    if position == "target":
        row = f"Anywhere{suffix} on wg0 ({mode}) ALLOW OUT Anywhere{suffix}"
    else:
        row = f"443/tcp{suffix} ALLOW OUT Anywhere{suffix} on wg0 ({mode})"
    rule = firewall_controller.parse_ufw_structured_rule(row)
    assert rule["interface"] == "wg0"
    assert rule["is_ipv6"] is ipv6
    assert rule["to"] == ("Anywhere" if position == "target" else "443/tcp")
    assert rule["from"] == "Anywhere"
    assert rule["raw"] == row
    assert rule["display"].endswith(f"({mode})")
    assert f"({mode})" in firewall_controller.format_ufw_rule_lines([rule])[0]


@pytest.mark.parametrize("mode", ["log", "log-all"])
@pytest.mark.parametrize("ipv6", [False, True])
@pytest.mark.parametrize("direction", ["IN", "OUT"])
def test_logged_global_block_has_clean_fields(mode, ipv6, direction):
    suffix = " (v6)" if ipv6 else ""
    rule = firewall_controller.parse_ufw_structured_rule(
        f"Anywhere{suffix} ({mode}) DENY {direction} Anywhere{suffix}"
    )
    assert rule["interface"] is None
    assert rule["to"] == rule["from"] == "Anywhere"
    assert firewall_controller._is_global_block(rule)


def test_logging_modes_remain_distinct_for_dedup_and_rule_selection():
    plain = firewall_controller.parse_ufw_structured_rule(
        "Anywhere on wg0 ALLOW OUT Anywhere"
    )
    logged = firewall_controller.parse_ufw_structured_rule(
        "Anywhere on wg0 (log) ALLOW OUT Anywhere"
    )
    log_all = firewall_controller.parse_ufw_structured_rule(
        "Anywhere on wg0 (log-all) ALLOW OUT Anywhere"
    )
    assert (
        len(
            {
                firewall_controller.ufw_rule_identity_key(r)
                for r in (plain, logged, log_all)
            }
        )
        == 3
    )
    assert not firewall_controller._firewall_rule_matches_selected(plain, logged)
    assert not firewall_controller._firewall_rule_matches_selected(logged, log_all)
    rows = firewall_controller.format_ufw_rule_lines([plain, logged, log_all, logged])
    assert len(rows) == 3
    assert sum("DUP x2" in row for row in rows) == 1
    assert any("(log)" in row and "DUP x2" in row for row in rows)
