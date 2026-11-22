"""Firewall-view regressions from ss/UFW/WireGuard terminal findings.

All command output is synthetic. No firewall, VPN or network calls are run.
"""

import json
from pathlib import Path

import pytest

import netmon.app as netmon
from netmon.features import firewall_controller as fc
from netmon.services import firewall_listener_service as service


def rule(line):
    result = fc.parse_ufw_structured_rule(line)
    assert result is not None
    return result


def listener(host="0.0.0.0", port=60078, proto="udp", **kwargs):
    return {"host": host, "port": port, "proto": proto, **kwargs}


def collect_app(monkeypatch, *, rows="", rules="", language="de", wg="", root_ss=True):
    app = netmon.App.__new__(netmon.App)
    app.lang = json.loads(
        (Path(netmon.__file__).parent / "lang" / f"{language}.json").read_text()
    )
    app._read_ufw_status = lambda verbose=True: (
        0,
        "Status: active\nDefault: deny (incoming), allow (outgoing), disabled (routed)\n"
        "Logging: on (low)\n" + rules,
    )
    calls = []

    def run(cmd, timeout=0):
        calls.append(cmd)
        if cmd == ["sudo", "-n", "ss", "-lntupeH"]:
            return (0, rows) if root_ss else (1, "sudo: a password is required")
        if cmd in [["ss", "-lntupeH"], ["ss", "-lntupH"], ["ss", "-lntuH"]]:
            return 0, rows
        if cmd in [
            ["wg", "show", "all", "listen-port"],
            ["sudo", "-n", "wg", "show", "all", "listen-port"],
        ]:
            return 0, wg
        pytest.fail(f"Unexpected command: {cmd}")

    monkeypatch.setattr(netmon, "run_cmd", run)
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: False)
    return app, calls


@pytest.mark.parametrize("host", ["0.0.0.0", "::"])
def test_wildcard_binding_does_not_prove_reachability(monkeypatch, host):
    suffix = " (v6)" if host == "::" else ""
    local = f"[{host}]:60078" if host == "::" else f"{host}:60078"
    app, _ = collect_app(
        monkeypatch,
        rows=f'udp UNCONN 0 0 {local} *:* users:(("service",pid=123,fd=4))',
        rules=f"60078/udp{suffix} ALLOW IN Anywhere{suffix}",
    )
    snapshot = app._collect_firewall_transparency_snapshot()
    item = snapshot["listeners"][0]
    assert item["binding"] == "alle Schnittstellen"
    assert item["firewall"] == "IN ALLOW"
    assert item["firewall_detail"] == "UFW: ALLOW IN"
    assert item["reachability"] == "Erreichbarkeit: nicht getestet"
    assert "extern erreichbar" not in item["rating"]
    assert snapshot["external_open_count"] == 1  # config estimate, not test result


@pytest.mark.parametrize("host", ["0.0.0.0", "::"])
@pytest.mark.parametrize("direction", ["IN", "OUT"])
def test_interface_rule_is_not_a_global_allow(host, direction):
    suffix = " (v6)" if host == "::" else ""
    interface_rule = rule(
        f"Anywhere{suffix} on Irland ALLOW {direction} Anywhere{suffix}"
    )
    result = service.assess_inbound(
        listener(host), [interface_rule], status="active", default_in="DENY"
    )
    assert result["state"] == ("conditional" if direction == "IN" else "blocked")


@pytest.mark.parametrize(
    "interface,expected", [("Irland", "allowed"), ("CH-685", "blocked")]
)
def test_known_bound_interface_is_used(interface, expected):
    result = service.assess_inbound(
        listener("10.2.0.2", interface=interface),
        [rule("Anywhere on Irland ALLOW IN Anywhere")],
        status="active",
        default_in="DENY",
    )
    assert result["state"] == expected


@pytest.mark.parametrize("host,suffix", [("0.0.0.0", " (v6)"), ("::", "")])
def test_other_address_family_cannot_allow_a_listener(host, suffix):
    result = service.assess_inbound(
        listener(host),
        [rule(f"60078/udp{suffix} ALLOW IN Anywhere{suffix}")],
        status="active",
        default_in="DENY",
    )
    assert result["state"] == "blocked"


@pytest.mark.parametrize(
    "policy,expected",
    [("DENY", "blocked"), ("REJECT", "blocked"), ("ALLOW", "allowed")],
)
def test_default_in_policy_is_used_without_explicit_rules(policy, expected):
    result = service.assess_inbound(listener(), [], status="active", default_in=policy)
    assert result == {"state": expected, "basis": "default", "policy": policy}


@pytest.mark.parametrize(
    "status,expected", [("unknown", "unknown"), ("inactive", "inactive")]
)
def test_unreadable_or_disabled_ufw_cannot_confirm_filtering(status, expected):
    result = service.assess_inbound(
        listener(),
        [rule("60078/udp ALLOW IN Anywhere")],
        status=status,
        default_in="DENY",
    )
    assert result["state"] == expected


@pytest.mark.parametrize(
    "source", ["192.0.2.0/24", "10.2.0.1", "Anywhere 1000:2000/udp"]
)
def test_source_restrictions_are_conditional(source):
    result = service.assess_inbound(
        listener(),
        [rule(f"60078/udp ALLOW IN {source}")],
        status="active",
        default_in="DENY",
    )
    assert result["state"] == "conditional"


@pytest.mark.parametrize(
    "host,expected",
    [("0.0.0.0", "conditional"), ("192.0.2.5", "allowed"), ("192.0.2.6", "blocked")],
)
def test_destination_restrictions_are_respected(host, expected):
    result = service.assess_inbound(
        listener(host),
        [rule("192.0.2.5 60078/udp ALLOW IN Anywhere")],
        status="active",
        default_in="DENY",
    )
    assert result["state"] == expected


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("DENY", "ALLOW", "blocked"),
        ("REJECT", "ALLOW", "blocked"),
        ("ALLOW", "DENY", "allowed"),
        ("LIMIT", "ALLOW", "limited"),
    ],
)
def test_rule_order_is_preserved(first, second, expected):
    result = service.assess_inbound(
        listener(),
        [
            rule(f"60078/udp {first} IN Anywhere"),
            rule(f"60078/udp {second} IN Anywhere"),
        ],
        status="active",
        default_in="DENY",
    )
    assert result["state"] == expected


def test_conditional_deny_before_allow_keeps_uncertainty():
    result = service.assess_inbound(
        listener(),
        [rule("60078/udp DENY IN 192.0.2.0/24"), rule("60078/udp ALLOW IN Anywhere")],
        status="active",
        default_in="DENY",
    )
    assert result["state"] == "conditional"


@pytest.mark.parametrize(
    "expression,port,expected",
    [("80,443", 443, True), ("6000:6007", 6004, True), ("6000:6007", 6008, False)],
)
def test_port_lists_and_ranges(expression, port, expected):
    result = service.assess_inbound(
        listener(port=port),
        [rule(f"{expression}/udp ALLOW IN Anywhere")],
        status="active",
        default_in="DENY",
    )
    assert (result["state"] == "allowed") is expected


def test_unresolved_application_profile_remains_conditional():
    result = service.assess_inbound(
        listener(),
        [rule("OpenSSH ALLOW IN Anywhere")],
        status="active",
        default_in="DENY",
    )
    assert result["state"] == "conditional"


@pytest.mark.parametrize("root_ss", [True, False])
def test_ss_process_name_and_pid_survive_metadata_and_fallback(monkeypatch, root_ss):
    row = 'udp UNCONN 0 0 127.0.0.53%lo:53 0.0.0.0:* users:(("systemd-resolve",pid=991,fd=12)) uid:991 ino:123 sk:42 cgroup:/system.slice/systemd-resolved.service <->'
    app, calls = collect_app(monkeypatch, rows=row, root_ss=root_ss)
    snapshot = app._collect_firewall_transparency_snapshot()
    item = snapshot["listeners"][0]
    assert item["process"] == "systemd-resolve"
    assert item["pid"] == "991"
    assert item["scope"] == "local only"
    assert calls[0] == ["sudo", "-n", "ss", "-lntupeH"]
    assert snapshot["listener_source"] == (
        "sudo ss" if root_ss else "ss (unprivileged)"
    )


def test_ss_metadata_is_never_a_process_name_or_suspicion(monkeypatch):
    app, _ = collect_app(
        monkeypatch,
        rows="udp UNCONN 0 0 0.0.0.0:61001 *:* uid:991 ino:123 sk:42 cgroup:/system.slice/example.service <->",
    )
    item = app._collect_firewall_transparency_snapshot()["listeners"][0]
    assert item["process"] == "-" and item["pid"] == "-"
    assert item["priority"] == "ok"
    assert item["owner_note"] == "cgroup example.service"


@pytest.mark.parametrize("interface,port", [("Irland", 60078), ("vpn-new42", 48129)])
def test_wireguard_is_dynamic_and_covers_both_families(monkeypatch, interface, port):
    rows = f"udp UNCONN 0 0 0.0.0.0:{port} *:* ino:123 sk:1\nudp UNCONN 0 0 [::]:{port} *:* ino:124 sk:2"
    app, calls = collect_app(monkeypatch, rows=rows, wg=f"{interface}\t{port}\n")
    snapshot = app._collect_firewall_transparency_snapshot()
    assert len(snapshot["listeners"]) == 2
    for item in snapshot["listeners"]:
        assert item["process"] == "WireGuard"
        assert item["wireguard_interfaces"] == (interface,)
        assert interface in item["owner_note"]
        assert "Listen-Port" in item["owner_note"]
        assert item["priority"] == "ok"
        assert item["reachability"] == "Erreichbarkeit: nicht getestet"
    assert [cmd for cmd in calls if "wg" in cmd] == [
        ["wg", "show", "all", "listen-port"]
    ]
    assert all("dump" not in cmd and "cat" not in cmd for cmd in calls)


def test_wireguard_port_match_does_not_replace_a_known_process_or_tcp(monkeypatch):
    app, _ = collect_app(
        monkeypatch,
        wg="wg9 60078",
        rows=(
            'udp UNCONN 0 0 0.0.0.0:60078 *:* users:(("other",pid=2,fd=4))\n'
            "tcp LISTEN 0 0 0.0.0.0:60078 *:* ino:1\n"
            "udp UNCONN 0 0 0.0.0.0:60079 *:* ino:2"
        ),
    )
    items = app._collect_firewall_transparency_snapshot()["listeners"]
    assert not any(item.get("wireguard_interfaces") for item in items)
    assert {item["process"] for item in items} == {"other", "-"}


def test_wireguard_read_only_sudo_fallback_uses_only_listen_port(monkeypatch):
    app, calls = collect_app(
        monkeypatch,
        wg="dynamic-wg 48119",
        rows="udp UNCONN 0 0 0.0.0.0:48119 *:* ino:1",
    )
    original = netmon.run_cmd

    def run(cmd, timeout=0):
        if cmd == ["wg", "show", "all", "listen-port"]:
            calls.append(cmd)
            return 1, "Operation not permitted"
        return original(cmd, timeout=timeout)

    monkeypatch.setattr(netmon, "run_cmd", run)
    item = app._collect_firewall_transparency_snapshot()["listeners"][0]
    assert item["process"] == "WireGuard"
    assert calls[-1] == ["sudo", "-n", "wg", "show", "all", "listen-port"]


def test_ss_fallback_after_unsupported_or_unparseable_output(monkeypatch):
    app, _ = collect_app(monkeypatch)
    calls = []

    def run(cmd, timeout=0):
        calls.append(cmd)
        if cmd[0] == "sudo":
            return 1, "sudo: a password is required"
        if cmd == ["ss", "-lntupeH"]:
            return 0, "unexpected output without socket columns"
        assert cmd == ["ss", "-lntupH"]
        return (
            0,
            'tcp LISTEN 0 0 127.0.0.53:53 *:* users:(("systemd-resolve",pid=99,fd=2))',
        )

    monkeypatch.setattr(netmon, "run_cmd", run)
    snapshot = app._collect_firewall_transparency_snapshot()
    assert snapshot["listener_readable"]
    assert snapshot["listeners"][0]["process"] == "systemd-resolve"
    assert len(calls) == 3
    assert any("unprivilegiertem ss" in line for line in snapshot["summary_lines"])


def test_failed_ss_is_reported_as_unknown_not_no_listeners(monkeypatch):
    app, _ = collect_app(monkeypatch)
    monkeypatch.setattr(netmon, "run_cmd", lambda *a, **kw: (1, "not available"))
    snapshot = app._collect_firewall_transparency_snapshot()
    assert snapshot["listeners"] == [] and not snapshot["listener_readable"]
    assert any(
        "bestätigt keine Abwesenheit" in line for line in snapshot["summary_lines"]
    )


@pytest.mark.parametrize("host", ["224.0.0.251", "239.1.2.3", "ff02::fb%eth0"])
def test_multicast_precedes_allow_and_is_not_notable(monkeypatch, host):
    local = f"[{host}]:5353" if ":" in host else f"{host}:5353"
    suffix = " (v6)" if ":" in host else ""
    app, _ = collect_app(
        monkeypatch,
        rows=f'udp UNCONN 0 0 {local} *:* users:(("brave",pid=123,fd=4))',
        rules=f"5353/udp{suffix} ALLOW IN Anywhere{suffix}",
    )
    snapshot = app._collect_firewall_transparency_snapshot()
    item = snapshot["listeners"][0]
    assert item["scope"] == "multicast" and item["binding"] == "Multicast"
    assert item["priority"] == "ok"
    assert "Multicast" in item["rating"]
    assert snapshot["external_open_count"] == 0
    assert "Auffällig: 0" in snapshot["summary_lines"]


@pytest.mark.parametrize("language", ["de", "en"])
def test_rule_counters_use_semantics_before_translation(monkeypatch, language):
    app, _ = collect_app(
        monkeypatch,
        language=language,
        rules=(
            "22/tcp ALLOW IN Anywhere\n"
            "25/tcp DENY IN Anywhere\n"
            "26/tcp REJECT IN Anywhere\n"
            "80/tcp LIMIT IN Anywhere\n"
            "53/udp ALLOW OUT Anywhere\n"
            "Anywhere on Irland ALLOW IN Anywhere\n"
        ),
    )
    snapshot = app._collect_firewall_transparency_snapshot()
    lines = snapshot["summary_lines"]
    assert snapshot["rule_count"] == 6
    assert "Default IN: DENY" in lines
    assert (
        "Explizite DENY/REJECT-Regeln: 2"
        if language == "de"
        else "Explicit DENY/REJECT rules: 2"
    ) in lines
    assert (
        "Globale IN-Erlaubnisse: 1" if language == "de" else "Global IN allows: 1"
    ) in lines


def test_zero_explicit_blocks_does_not_hide_default_deny(monkeypatch):
    app, _ = collect_app(monkeypatch)
    lines = app._collect_firewall_transparency_snapshot()["summary_lines"]
    assert "Default IN: DENY" in lines
    assert "Explizite DENY/REJECT-Regeln: 0" in lines


class Table:
    def __init__(self):
        self.rows = []

    def get_children(self):
        return ()

    def delete(self, *args):
        self.rows.clear()

    def insert(self, parent, position, *, values):
        self.rows.append(values)
        return str(len(self.rows))


def test_tables_and_report_show_direction_interface_and_separate_reachability(
    monkeypatch,
):
    app, _ = collect_app(
        monkeypatch,
        rules="Anywhere on Irland ALLOW IN Anywhere\nAnywhere ALLOW OUT Anywhere on CH-685",
        rows='tcp LISTEN 0 0 0.0.0.0:8080 *:* users:(("web",pid=10,fd=4))',
    )
    app.firewall_rules_table, app.firewall_listeners_table = Table(), Table()
    app.on_firewall_rule_select = lambda: None
    app.refresh_firewall_transparency_view()
    rows = app.firewall_rules_table.rows
    assert rows[0][0] == "ALLOW IN" and "on Irland" in rows[0][1]
    assert rows[1][0] == "ALLOW OUT" and "on CH-685" in rows[1][1]
    assert "alle Schnittstellen" in app.firewall_listeners_table.rows[0][4]
    assert "nicht getestet" in app.firewall_listeners_table.rows[0][6]
    report = app.build_firewall_transparency_report()
    assert "IN via Irland" in report and "OUT via CH-685" in report
    assert "Erreichbarkeit: nicht getestet" in report


def test_unrelated_port_test_does_not_confirm_listener_reachability(monkeypatch):
    app, _ = collect_app(
        monkeypatch, rows='tcp LISTEN 0 0 0.0.0.0:443 *:* users:(("web",pid=10,fd=4))'
    )
    app.port_reality_last_scan = {
        "host": "unrelated.example",
        "ts": 100,
        "results": [{"port": 443, "state": "open"}],
    }
    snapshot = app._collect_firewall_transparency_snapshot()
    assert snapshot["listeners"][0]["reachability"] == "Erreichbarkeit: nicht getestet"
    assert any(
        "keine Zuordnung zu lokalen Listenern" in line
        for line in snapshot["summary_lines"]
    )
