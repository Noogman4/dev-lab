from netmon.features import speedtest_controller
from netmon.modules.speedtest import (
    format_speedtest_summary,
    format_speedtest_table,
    list_speedtest_servers,
    normalize_speedtest_server_id,
    parse_speedtest_servers,
    run_speedtest,
)
from types import SimpleNamespace


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_speedtest_history_path_uses_documents_logs_and_migrates_state_file(
    monkeypatch, tmp_path
):
    docs_logs_dir = tmp_path / "Documents" / "NetMon" / "Logs"
    state_logs_dir = tmp_path / "state" / "logs"
    state_logs_dir.mkdir(parents=True)
    legacy_history = state_logs_dir / "speedtest_history.jsonl"
    legacy_history.write_text('{"timestamp":"2026-06-07 10:00:00"}\n', encoding="utf-8")

    monkeypatch.setattr(
        speedtest_controller,
        "get_netmon_documents_subdir",
        lambda *parts: str(docs_logs_dir),
    )
    app = SimpleNamespace(netmon_state_dir=str(tmp_path / "state"))

    path = speedtest_controller.speedtest_history_path(app)

    assert path == str(docs_logs_dir / "speedtest_history.jsonl")
    assert (docs_logs_dir / "speedtest_history.jsonl").read_text(encoding="utf-8") == (
        '{"timestamp":"2026-06-07 10:00:00"}\n'
    )


def test_run_speedtest_prefers_ookla_cli_and_parses_values():
    calls = []

    def fake_has_cmd(name):
        return name == "speedtest"

    def fake_run_cmd(args, timeout=120):
        calls.append((tuple(args), timeout))
        payload = (
            '{"ping":{"latency":41.2,"jitter":8.1},'
            '"download":{"bandwidth":4050000},'
            '"upload":{"bandwidth":1460000}}'
        )
        return 0, payload

    result, err = run_speedtest(fake_run_cmd, fake_has_cmd, timeout=77)

    assert err is None
    assert result["tool"] == "speedtest"
    assert result["ping_ms"] == 41.2
    assert result["jitter_ms"] == 8.1
    assert round(result["download_mbps"], 1) == 32.4
    assert round(result["upload_mbps"], 1) == 11.7
    assert calls and calls[0][0][0] == "speedtest"


def test_run_speedtest_falls_back_to_speedtest_cli():
    def fake_has_cmd(name):
        return name == "speedtest-cli"

    def fake_run_cmd(args, timeout=120):
        payload = '{"ping":21.3,"download":40200000,"upload":11700000}'
        return 0, payload

    result, err = run_speedtest(fake_run_cmd, fake_has_cmd)

    assert err is None
    assert result["tool"] == "speedtest-cli"
    assert round(result["download_mbps"], 1) == 40.2
    assert round(result["upload_mbps"], 1) == 11.7


def test_run_speedtest_normalizes_server_id_label_before_cli_call():
    calls = []

    def fake_run_cmd(args, timeout=120):
        calls.append(tuple(args))
        return 0, '{"ping":21.3,"download":40200000,"upload":11700000}'

    result, err = run_speedtest(
        fake_run_cmd,
        lambda name: name == "speedtest-cli",
        server_id="ID 44081",
    )

    assert err is None
    assert result is not None
    assert calls == [("speedtest-cli", "--json", "--secure", "--server", "44081")]


def test_run_speedtest_uses_ookla_server_id_option():
    calls = []

    def fake_run_cmd(args, timeout=120):
        calls.append(tuple(args))
        return (
            0,
            '{"ping":{"latency":21.3},"download":{"bandwidth":1},'
            '"upload":{"bandwidth":1}}',
        )

    result, err = run_speedtest(
        fake_run_cmd,
        lambda name: name == "speedtest",
        server_id="18667",
    )

    assert err is None
    assert result is not None
    assert calls[0][-1] == "--server-id=18667"


def test_run_speedtest_retries_fixed_legacy_server_without_secure():
    calls = []

    def fake_run_cmd(args, timeout=120):
        calls.append(tuple(args))
        if "--secure" in args:
            return 1, "ERROR: No matched servers: 18667"
        return 0, '{"ping":21.3,"download":40200000,"upload":11700000}'

    result, err = run_speedtest(
        fake_run_cmd,
        lambda name: name == "speedtest-cli",
        server_id="18667",
    )

    assert err is None
    assert result is not None
    assert calls == [
        ("speedtest-cli", "--json", "--secure", "--server", "18667"),
        ("speedtest-cli", "--json", "--server", "18667"),
    ]


def test_run_speedtest_returns_error_when_no_cli_found():
    result, err = run_speedtest(lambda *_args, **_kwargs: (1, "x"), lambda _n: False)

    assert result is None
    assert "Kein Speedtest-CLI gefunden" in err


def test_parse_speedtest_servers_reads_ookla_json_with_location():
    servers = parse_speedtest_servers(
        '{"servers":[{"id":12345,"name":"Example Net",'
        '"location":"Ulm","country":"Germany","host":"speed.example"}]}'
    )

    assert servers == [
        {
            "id": "12345",
            "name": "Example Net",
            "location": "Ulm",
            "country": "Germany",
            "distance": "",
            "host": "speed.example",
        }
    ]


def test_parse_speedtest_servers_reads_speedtest_cli_list_with_distance():
    servers = parse_speedtest_servers(
        "12345) Example Net (Ulm, Germany) [12.34 km]\n"
        "67890) Other Provider (Augsburg, Germany) [67.8 km]"
    )

    assert servers[0] == {
        "id": "12345",
        "name": "Example Net",
        "location": "Ulm",
        "country": "Germany",
        "distance": "12.34 km",
        "host": "",
    }
    assert servers[1]["location"] == "Augsburg"


def test_list_speedtest_servers_falls_back_to_list_command_and_limits_results():
    calls = []

    def fake_run_cmd(args, timeout=60):
        calls.append((tuple(args), timeout))
        if args == ["speedtest", "--list"]:
            return (
                0,
                "12345) Example Net (Ulm, Germany) [12.34 km]\n"
                "67890) Other Provider (Augsburg, Germany) [67.8 km]",
            )
        return 1, "unsupported option"

    servers, error = list_speedtest_servers(
        fake_run_cmd,
        lambda name: name == "speedtest",
        timeout=33,
        limit=1,
    )

    assert error is None
    assert [server["id"] for server in servers] == ["12345"]
    assert calls[-1] == (("speedtest", "--list"), 33)


def test_list_speedtest_servers_reports_missing_cli():
    servers, error = list_speedtest_servers(
        lambda *_args, **_kwargs: (1, "unexpected"),
        lambda _name: False,
    )

    assert servers == []
    assert "Kein Speedtest-CLI" in error


def test_speedtest_server_log_line_contains_id_provider_and_place():
    app = SimpleNamespace(tr=lambda _key, default: default)

    line = speedtest_controller._speedtest_server_log_line(
        app,
        {
            "id": "12345",
            "name": "Example Net",
            "location": "Ulm",
            "country": "Germany",
            "distance": "12.34 km",
        },
    )

    assert line == (
        "ID 12345 | Anbieter: Example Net | Ort: Ulm, Germany" " | Entfernung: 12.34 km"
    )


def test_normalize_speedtest_server_id_accepts_id_label_and_log_line():
    assert normalize_speedtest_server_id("44081") == "44081"
    assert normalize_speedtest_server_id("ID 44081") == "44081"
    assert normalize_speedtest_server_id("Server-ID: 44081") == "44081"
    assert normalize_speedtest_server_id("ID 44081 | Anbieter: Example") == "44081"
    assert (
        normalize_speedtest_server_id(
            "[2026-07-17 16:39:59] ID 44081 | Anbieter: Example"
        )
        == "44081"
    )


def test_configured_speedtest_server_id_normalizes_saved_value():
    app = SimpleNamespace(speedtest_server_id_var=DummyVar("ID 44081"))

    assert speedtest_controller.configured_speedtest_server_id(app) == "44081"


def test_normalize_speedtest_server_id_rejects_invalid_text():
    assert normalize_speedtest_server_id("Example 44081") == ""
    assert speedtest_controller.normalize_speedtest_server_id("--help") == ""


def test_prepare_speedtest_server_log_opens_and_clears_log():
    events = []
    log_tab = object()

    class DummyNotebook:
        def select(self, tab):
            events.append(("select", tab))

    app = SimpleNamespace(
        nb=DummyNotebook(),
        tab_log=log_tab,
        log_overlay_active=True,
        toggle_log_overlay=lambda: events.append("toggle_overlay"),
        clear_log=lambda: events.append("clear_log"),
    )

    speedtest_controller._prepare_speedtest_server_log(app)

    assert events == [("select", log_tab), "toggle_overlay", "clear_log"]


def test_format_speedtest_summary_human_readable():
    summary = format_speedtest_summary(
        {
            "ping_ms": 41.0,
            "jitter_ms": 8.0,
            "download_mbps": 32.4,
            "upload_mbps": 11.7,
        }
    )

    assert "Ping 41 ms" in summary
    assert "Jitter 8 ms" in summary
    assert "Download 32.4 Mbit/s" in summary
    assert "Upload 11.7 Mbit/s" in summary


def test_run_speedtest_parses_json_with_prefixed_text():
    def fake_has_cmd(name):
        return name == "speedtest"

    def fake_run_cmd(args, timeout=120):
        payload = (
            "Some preface line\n"
            '{"ping":{"latency":30.0,"jitter":5.0},"download":{"bandwidth":3000000},"upload":{"bandwidth":1000000}}\n'
            "trailing note"
        )
        return 0, payload

    result, err = run_speedtest(fake_run_cmd, fake_has_cmd)

    assert err is None
    assert round(result["download_mbps"], 1) == 24.0


def test_run_speedtest_tries_multiple_speedtest_command_variants():
    calls = []

    def fake_has_cmd(name):
        return name == "speedtest"

    def fake_run_cmd(args, timeout=120):
        calls.append(tuple(args))
        if args[:2] == ["speedtest", "--accept-license"]:
            return 1, "Unknown option --accept-license"
        if args == ["speedtest", "--format=json"]:
            return 1, "Unknown option --format"
        if args == ["speedtest", "--json", "--secure"]:
            return 0, '{"ping":25.0,"download":50000000,"upload":10000000}'
        return 1, "unexpected"

    result, err = run_speedtest(fake_run_cmd, fake_has_cmd)

    assert err is None
    assert result["tool"] == "speedtest"
    assert round(result["download_mbps"], 1) == 50.0
    assert len(calls) >= 3


def test_run_speedtest_includes_attempted_commands_in_error():
    def fake_has_cmd(name):
        return name in {"speedtest", "speedtest-cli"}

    def fake_run_cmd(args, timeout=120):
        return 0, "not json"

    result, err = run_speedtest(fake_run_cmd, fake_has_cmd)

    assert result is None
    assert "Versuchte Befehle:" in err
    assert "speedtest --format=json" in err
    assert "speedtest-cli --json --secure" in err


def test_format_speedtest_table_human_readable_grid():
    table = format_speedtest_table(
        {
            "tool": "speedtest",
            "ping_ms": 56.2,
            "jitter_ms": None,
            "download_mbps": 50.4,
            "upload_mbps": 11.8,
        }
    )

    assert "| Tool" in table
    assert "| Speedtest" in table
    assert "56 ms" in table
    assert "50.4 Mbit/s" in table
    assert "11.8 Mbit/s" in table


def test_speedtest_warn_messages_reports_all_threshold_hits():
    warns = speedtest_controller.speedtest_warn_messages(
        {
            "download_mbps": 5.0,
            "upload_mbps": 0.5,
            "ping_ms": 200.0,
            "jitter_ms": 80.0,
        }
    )

    assert len(warns) == 4
    assert any("Download niedrig" in item for item in warns)
    assert any("Upload niedrig" in item for item in warns)
    assert any("Ping hoch" in item for item in warns)
    assert any("Jitter hoch" in item for item in warns)


def test_speedtest_warn_message_formats_value_and_threshold():
    assert (
        speedtest_controller._speedtest_warn_message(
            label="Download niedrig",
            value=5.0,
            threshold=10.0,
            unit="Mbit/s",
            decimals=1,
            comparison="<",
        )
        == "Download niedrig: 5.0 Mbit/s (< 10.0)"
    )


def test_speedtest_warn_triggered_supports_lower_and_higher_thresholds():
    assert speedtest_controller._speedtest_warn_triggered(5.0, 10.0, "<") is True
    assert speedtest_controller._speedtest_warn_triggered(20.0, 10.0, ">") is True


def test_speedtest_warn_triggered_returns_false_when_threshold_not_hit():
    assert speedtest_controller._speedtest_warn_triggered(10.0, 10.0, "<") is False
    assert speedtest_controller._speedtest_warn_triggered(10.0, 10.0, ">") is False


def test_speedtest_attempted_cli_extracts_trailing_command_list():
    assert (
        speedtest_controller._speedtest_attempted_cli(
            "Fehler beim Lauf.\nVersuchte Befehle: speedtest --format=json"
        )
        == "speedtest --format=json"
    )


def test_speedtest_attempted_cli_returns_empty_without_marker():
    assert (
        speedtest_controller._speedtest_attempted_cli("Fehler ohne Kommandohinweis")
        == ""
    )


def test_speedtest_failure_messages_include_cli_diagnosis_when_present():
    assert speedtest_controller._speedtest_failure_messages(
        "Fehler beim Lauf.\nVersuchte Befehle: speedtest --format=json"
    ) == [
        "Speedtest fehlgeschlagen: Fehler beim Lauf.\nVersuchte Befehle: speedtest --format=json",
        "Speedtest-Diagnose (CLI): speedtest --format=json",
    ]


def test_speedtest_failure_messages_return_only_failure_without_marker():
    assert speedtest_controller._speedtest_failure_messages(
        "Fehler ohne Kommandohinweis"
    ) == ["Speedtest fehlgeschlagen: Fehler ohne Kommandohinweis"]


def test_speedtest_status_message_returns_started_text():
    assert (
        speedtest_controller._speedtest_status_message("started")
        == "Speedtest gestartet..."
    )


def test_speedtest_status_message_returns_completed_text():
    assert (
        speedtest_controller._speedtest_status_message("completed")
        == "Speedtest abgeschlossen."
    )


def test_speedtest_warn_specs_define_expected_metric_order():
    assert speedtest_controller._speedtest_warn_specs() == (
        ("download_mbps", "Download niedrig", "download_mbps_min", "Mbit/s", 1, "<"),
        ("upload_mbps", "Upload niedrig", "upload_mbps_min", "Mbit/s", 1, "<"),
        ("ping_ms", "Ping hoch", "ping_ms_max", "ms", 0, ">"),
        ("jitter_ms", "Jitter hoch", "jitter_ms_max", "ms", 0, ">"),
    )


def test_speedtest_warn_messages_ignores_non_numeric_values():
    warns = speedtest_controller.speedtest_warn_messages(
        {
            "download_mbps": "5.0",
            "upload_mbps": None,
            "ping_ms": "200",
            "jitter_ms": object(),
        }
    )

    assert warns == []


def test_speedtest_panel_var_items_map_values_to_expected_vars():
    assert speedtest_controller._speedtest_panel_var_items(
        {
            "ping": "41 ms",
            "jitter": "8 ms",
            "download": "32.4 Mbit/s",
            "upload": "11.7 Mbit/s",
            "timestamp": "2026-06-06 23:55:00",
        }
    ) == (
        ("speedtest_ping_var", "41 ms"),
        ("speedtest_jitter_var", "8 ms"),
        ("speedtest_download_var", "32.4 Mbit/s"),
        ("speedtest_upload_var", "11.7 Mbit/s"),
        ("speedtest_timestamp_var", "2026-06-06 23:55:00"),
    )


def test_speedtest_panel_var_items_use_safe_defaults():
    assert speedtest_controller._speedtest_panel_var_items({}) == (
        ("speedtest_ping_var", "-"),
        ("speedtest_jitter_var", "-"),
        ("speedtest_download_var", "-"),
        ("speedtest_upload_var", "-"),
        ("speedtest_timestamp_var", "Noch kein Speedtest durchgeführt"),
    )


def test_apply_speedtest_panel_values_sets_all_fields():
    app = type("DummyApp", (), {})()
    app.speedtest_ping_var = DummyVar("")
    app.speedtest_jitter_var = DummyVar("")
    app.speedtest_download_var = DummyVar("")
    app.speedtest_upload_var = DummyVar("")
    app.speedtest_timestamp_var = DummyVar("")

    speedtest_controller._apply_speedtest_panel_values(
        app,
        {
            "ping": "41 ms",
            "jitter": "8 ms",
            "download": "32.4 Mbit/s",
            "upload": "11.7 Mbit/s",
            "timestamp": "2026-06-06 23:55:00",
        },
    )

    assert app.speedtest_ping_var.get() == "41 ms"
    assert app.speedtest_jitter_var.get() == "8 ms"
    assert app.speedtest_download_var.get() == "32.4 Mbit/s"
    assert app.speedtest_upload_var.get() == "11.7 Mbit/s"
    assert app.speedtest_timestamp_var.get() == "2026-06-06 23:55:00"


def test_apply_speedtest_panel_values_uses_safe_defaults_for_missing_keys():
    app = type("DummyApp", (), {})()
    app.speedtest_ping_var = DummyVar("")
    app.speedtest_jitter_var = DummyVar("")
    app.speedtest_download_var = DummyVar("")
    app.speedtest_upload_var = DummyVar("")
    app.speedtest_timestamp_var = DummyVar("")

    speedtest_controller._apply_speedtest_panel_values(app, {})

    assert app.speedtest_ping_var.get() == "-"
    assert app.speedtest_jitter_var.get() == "-"
    assert app.speedtest_download_var.get() == "-"
    assert app.speedtest_upload_var.get() == "-"
    assert app.speedtest_timestamp_var.get() == "Noch kein Speedtest durchgeführt"


def test_update_speedtest_panel_formats_metrics_and_timestamp():
    app = type("DummyApp", (), {})()
    app.speedtest_ping_var = DummyVar("")
    app.speedtest_jitter_var = DummyVar("")
    app.speedtest_download_var = DummyVar("")
    app.speedtest_upload_var = DummyVar("")
    app.speedtest_timestamp_var = DummyVar("")

    speedtest_controller.update_speedtest_panel(
        app,
        {
            "ping_ms": 41.2,
            "jitter_ms": 8.1,
            "download_mbps": 32.4,
            "upload_mbps": 11.7,
            "timestamp": "2026-06-06 23:55:00",
        },
    )

    assert app.speedtest_ping_var.get() == "41 ms"
    assert app.speedtest_jitter_var.get() == "8 ms"
    assert app.speedtest_download_var.get() == "32.4 Mbit/s"
    assert app.speedtest_upload_var.get() == "11.7 Mbit/s"
    assert app.speedtest_timestamp_var.get() == "2026-06-06 23:55:00"


def test_speedtest_panel_values_return_empty_defaults_without_result():
    assert speedtest_controller._speedtest_panel_values(None) == {
        "ping": "-",
        "jitter": "-",
        "download": "-",
        "upload": "-",
        "timestamp": "Noch kein Speedtest durchgeführt",
    }


def test_speedtest_empty_panel_values_return_expected_defaults():
    assert speedtest_controller._speedtest_empty_panel_values() == {
        "ping": "-",
        "jitter": "-",
        "download": "-",
        "upload": "-",
        "timestamp": "Noch kein Speedtest durchgeführt",
    }


def test_speedtest_empty_panel_values_return_detached_dict():
    values = speedtest_controller._speedtest_empty_panel_values()
    values["ping"] = "changed"

    assert speedtest_controller._speedtest_empty_panel_values()["ping"] == "-"


def test_speedtest_panel_value_text_formats_existing_metric():
    assert (
        speedtest_controller._speedtest_panel_value_text(
            {"ping_ms": 41.2},
            "ping_ms",
            speedtest_controller._speedtest_ms_text,
        )
        == "41 ms"
    )


def test_speedtest_panel_value_text_uses_placeholder_for_missing_metric():
    assert (
        speedtest_controller._speedtest_panel_value_text(
            {},
            "download_mbps",
            speedtest_controller._speedtest_mbps_text,
        )
        == "-"
    )


def test_speedtest_panel_values_format_result_fields():
    assert speedtest_controller._speedtest_panel_values(
        {
            "ping_ms": 41.2,
            "jitter_ms": 8.1,
            "download_mbps": 32.4,
            "upload_mbps": 11.7,
            "timestamp": "2026-06-06 23:55:00",
        }
    ) == {
        "ping": "41 ms",
        "jitter": "8 ms",
        "download": "32.4 Mbit/s",
        "upload": "11.7 Mbit/s",
        "timestamp": "2026-06-06 23:55:00",
    }


def test_speedtest_history_log_fields_format_numeric_and_missing_values():
    assert speedtest_controller._speedtest_history_log_fields(
        {
            "timestamp": "2026-06-06 23:55:00",
            "ping_ms": 15.2,
            "jitter_ms": None,
            "download_mbps": 120.4,
            "upload_mbps": 5.2,
        }
    ) == {
        "timestamp": "2026-06-06 23:55:00",
        "ping": "15",
        "jitter": "-",
        "download": "120.4",
        "upload": "5.2",
    }


def test_speedtest_history_log_fields_fall_back_to_placeholders():
    assert speedtest_controller._speedtest_history_log_fields({}) == {
        "timestamp": "-",
        "ping": "-",
        "jitter": "-",
        "download": "-",
        "upload": "-",
    }


def test_speedtest_history_metric_text_formats_requested_precision():
    assert speedtest_controller._speedtest_history_metric_text(15.2, 0) == "15"
    assert speedtest_controller._speedtest_history_metric_text(5.2, 1) == "5.2"


def test_speedtest_history_metric_text_uses_placeholder_for_none():
    assert speedtest_controller._speedtest_history_metric_text(None, 0) == "-"
    assert speedtest_controller._speedtest_history_metric_text(None, 1) == "-"


def test_speedtest_history_log_parts_format_expected_segments():
    assert speedtest_controller._speedtest_history_log_parts(
        {
            "timestamp": "2026-06-06 23:55:00",
            "ping": "15",
            "jitter": "-",
            "download": "120.4",
            "upload": "5.2",
        }
    ) == (
        "2026-06-06 23:55:00",
        "Ping 15 ms",
        "Jitter - ms",
        "DL 120.4",
        "UL 5.2",
    )


def test_speedtest_history_log_parts_use_safe_defaults():
    assert speedtest_controller._speedtest_history_log_parts({}) == (
        "-",
        "Ping - ms",
        "Jitter - ms",
        "DL -",
        "UL -",
    )


def test_speedtest_history_limit_uses_safe_default_and_minimum():
    app = type("DummyApp", (), {})()

    assert speedtest_controller._speedtest_history_limit(app) == 5

    app.speedtest_history_limit = 0
    assert speedtest_controller._speedtest_history_limit(app) == 1

    app.speedtest_history_limit = "7"
    assert speedtest_controller._speedtest_history_limit(app) == 7


def test_speedtest_trimmed_records_for_app_uses_app_limit():
    app = type("DummyApp", (), {})()
    app.speedtest_history_limit = 2

    assert speedtest_controller._speedtest_trimmed_records_for_app(
        app,
        [{"i": 1}, {"i": 2}, {"i": 3}],
    ) == [{"i": 2}, {"i": 3}]


def test_speedtest_trimmed_records_for_app_uses_safe_default_limit():
    app = type("DummyApp", (), {})()

    assert speedtest_controller._speedtest_trimmed_records_for_app(
        app,
        [{"i": 1}],
    ) == [{"i": 1}]


def test_speedtest_trimmed_history_keeps_latest_entries():
    records = [{"i": 1}, {"i": 2}, {"i": 3}]

    assert speedtest_controller._speedtest_trimmed_history(records, 2) == [
        {"i": 2},
        {"i": 3},
    ]


def test_speedtest_trimmed_history_uses_safe_minimum():
    records = [{"i": 1}, {"i": 2}]

    assert speedtest_controller._speedtest_trimmed_history(records, 0) == [{"i": 2}]
    assert speedtest_controller._speedtest_trimmed_history([], 3) == []


def test_speedtest_history_window_uses_trimmed_records():
    app = type("DummyApp", (), {})()
    app.speedtest_history_limit = 2
    app.speedtest_history = [{"i": 1}, {"i": 2}, {"i": 3}]

    assert speedtest_controller._speedtest_history_window(app) == [
        {"i": 2},
        {"i": 3},
    ]


def test_speedtest_history_window_uses_safe_limit_default():
    app = type("DummyApp", (), {})()
    app.speedtest_history = [{"i": 1}]

    assert speedtest_controller._speedtest_history_window(app) == [{"i": 1}]


def test_speedtest_history_list_returns_detached_copy():
    history = [{"i": 1}]

    copied = speedtest_controller._speedtest_history_list(history)
    copied.append({"i": 2})

    assert history == [{"i": 1}]
    assert copied == [{"i": 1}, {"i": 2}]


def test_speedtest_history_list_uses_empty_default():
    assert speedtest_controller._speedtest_history_list(None) == []


def test_append_speedtest_history_uses_safe_default_limit(tmp_path):
    app = type("DummyApp", (), {})()
    app.netmon_state_dir = str(tmp_path)
    app.speedtest_history = []
    app.log_debug_safe = lambda *_args, **_kwargs: None

    for index in range(6):
        speedtest_controller.append_speedtest_history(
            app,
            {
                "timestamp": f"2026-06-06 23:5{index}:00",
                "download_mbps": float(index),
            },
        )

    assert len(app.speedtest_history) == 5
    assert app.speedtest_history[0]["timestamp"] == "2026-06-06 23:51:00"
    assert app.speedtest_last_result["timestamp"] == "2026-06-06 23:55:00"


def test_speedtest_history_messages_return_empty_state_message():
    assert speedtest_controller._speedtest_history_messages([]) == [
        "Speedtest-Verlauf: noch keine Einträge."
    ]


def test_speedtest_history_message_lines_return_empty_state_message():
    assert speedtest_controller._speedtest_history_message_lines([]) == [
        "Speedtest-Verlauf: noch keine Einträge."
    ]


def test_speedtest_empty_history_message_matches_expected_text():
    assert (
        speedtest_controller._speedtest_empty_history_message()
        == "Speedtest-Verlauf: noch keine Einträge."
    )


def test_speedtest_empty_history_message_mentions_verlauf():
    message = speedtest_controller._speedtest_empty_history_message()

    assert "Verlauf" in message


def test_speedtest_history_header_message_matches_expected_text():
    assert (
        speedtest_controller._speedtest_history_header_message()
        == "Speedtest-Verlauf (letzte Ergebnisse):"
    )


def test_speedtest_history_header_message_mentions_ergebnisse():
    message = speedtest_controller._speedtest_history_header_message()

    assert "Ergebnisse" in message


def test_speedtest_history_messages_return_header_and_lines():
    messages = speedtest_controller._speedtest_history_messages(
        [
            {
                "timestamp": "2026-06-06 23:50:00",
                "ping_ms": 15.2,
                "jitter_ms": None,
                "download_mbps": 120.4,
                "upload_mbps": 21.0,
            }
        ]
    )

    assert messages[0] == "Speedtest-Verlauf (letzte Ergebnisse):"
    assert (
        messages[1]
        == "2026-06-06 23:50:00 | Ping 15 ms | Jitter - ms | DL 120.4 | UL 21.0"
    )


def test_speedtest_history_message_lines_return_header_and_lines():
    messages = speedtest_controller._speedtest_history_message_lines(
        [
            {
                "timestamp": "2026-06-06 23:50:00",
                "ping_ms": 15.2,
                "jitter_ms": None,
                "download_mbps": 120.4,
                "upload_mbps": 21.0,
            }
        ]
    )

    assert messages[0] == "Speedtest-Verlauf (letzte Ergebnisse):"
    assert (
        messages[1]
        == "2026-06-06 23:50:00 | Ping 15 ms | Jitter - ms | DL 120.4 | UL 21.0"
    )


def test_speedtest_result_debug_messages_return_json_summary_and_table():
    result = {
        "tool": "speedtest",
        "ping_ms": 41.2,
        "download_mbps": 32.4,
    }

    messages = speedtest_controller._speedtest_result_debug_messages(
        result,
        lambda item: f"summary:{item['tool']}",
        lambda item: f"table:{item['download_mbps']}",
    )

    assert messages == [
        '{"tool": "speedtest", "ping_ms": 41.2, "download_mbps": 32.4}',
        "summary:speedtest",
        "table:32.4",
    ]


def test_speedtest_result_debug_messages_preserve_non_ascii_json():
    messages = speedtest_controller._speedtest_result_debug_messages(
        {"status": "größer"},
        lambda _item: "summary",
        lambda _item: "table",
    )

    assert messages[0] == '{"status": "größer"}'


def test_speedtest_internal_debug_message_formats_tool_and_history_size():
    assert (
        speedtest_controller._speedtest_internal_debug_message(
            {"tool": "speedtest"},
            5,
        )
        == "Speedtest intern: tool=speedtest history=5"
    )


def test_speedtest_internal_debug_message_uses_dash_for_missing_tool():
    assert (
        speedtest_controller._speedtest_internal_debug_message(
            {},
            0,
        )
        == "Speedtest intern: tool=- history=0"
    )


def test_show_speedtest_history_formats_windowed_lines_without_limit():
    messages = []
    app = type("DummyApp", (), {})()
    app.speedtest_history = [
        {
            "timestamp": "2026-06-06 23:50:00",
            "ping_ms": 15.2,
            "jitter_ms": None,
            "download_mbps": 120.4,
            "upload_mbps": 21.0,
        },
        {
            "timestamp": "2026-06-06 23:55:00",
            "ping_ms": None,
            "jitter_ms": 3.4,
            "download_mbps": None,
            "upload_mbps": 5.2,
        },
    ]
    app.log = messages.append

    speedtest_controller.show_speedtest_history(app)

    assert messages[0] == "Speedtest-Verlauf (letzte Ergebnisse):"
    assert (
        messages[1]
        == "2026-06-06 23:50:00 | Ping 15 ms | Jitter - ms | DL 120.4 | UL 21.0"
    )
    assert (
        messages[2] == "2026-06-06 23:55:00 | Ping - ms | Jitter 3 ms | DL - | UL 5.2"
    )
