"""Untrusted catalog strings cannot forge new diagnostic records."""

import json
import re
from types import SimpleNamespace

import pytest

from netmon.app import App
from netmon import netmon_radio_app as ui
from netmon.core import log_redaction as redact, private_logs
from netmon.features import radio_controller as radio

SEPARATORS = ["\r", "\n", "\r\n", "\v", "\f", "\x85", "\u2028", "\u2029"]
STAMP = "[2099-01-01 00:00:00]"
SECRET = "SYNTHETIC_LOG_SECRET"


def assert_one_record(text):
    assert len(text.splitlines()) == 1
    assert not any(char in text.rstrip("\n") for char in "\r\n\v\f\x85\u2028\u2029")


@pytest.mark.parametrize("separator", SEPARATORS)
def test_record_encoder_escapes_forged_timestamp_and_preserves_unicode(separator):
    message = "Radio ÄÖü 日本語 🎵" + separator + STAMP + " [ERROR] forged"
    result = redact.format_log_message(message)
    assert_one_record(result)
    assert "ÄÖü 日本語 🎵" in result
    assert not re.search(r"(?m)^\[2099-", result)
    assert redact.format_log_message(result) == result


@pytest.mark.parametrize("separator", SEPARATORS)
def test_split_writes_publish_one_private_physical_record(tmp_path, separator):
    path = tmp_path / "logs" / "record.log"
    with private_logs.open_private_log(path) as output:
        output.write("[2000-01-01 00:00:00] station")
        for char in separator:
            output.write(char)
        output.flush()
        assert path.read_bytes() == b""
        output.writelines([STAMP, " [ERROR] forged", "\n"])
    result = path.read_text()
    assert_one_record(result)
    assert result.endswith("\n")
    assert len(re.findall(r"(?m)^\[\d{4}-", result)) == 1
    assert path.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    "value",
    [
        "password=" + SECRET,
        "Authorization: Bearer\n" + SECRET,
        "Authorization: Basic " + SECRET,
        "Cookie: session=" + SECRET,
        "Set-Cookie: session=" + SECRET,
        "https://user:" + SECRET + "@example.com/",
        "api_key=" + SECRET,
        "-----BEGIN PRIVATE KEY-----\n" + SECRET + "\n-----END PRIVATE KEY-----",
    ],
)
def test_redaction_precedes_control_encoding(value, tmp_path):
    result = redact.format_log_message(value)
    assert SECRET not in result
    assert_one_record(result)
    path = tmp_path / "logs" / "record.log"
    with private_logs.open_private_log(path) as output:
        output.write(value + "\n")
    assert SECRET not in path.read_text()
    assert_one_record(path.read_text())


def test_pretty_json_log_remains_valid_and_one_record(tmp_path):
    value = {"name": "Ä 日本語\x85\u2028\u2029", "password": SECRET}
    path = tmp_path / "logs" / "json.log"
    with private_logs.open_private_log(path) as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    result = path.read_text()
    assert_one_record(result)
    assert json.loads(result) == {"name": value["name"], "password": "[REDACTED]"}


def test_encoding_expansion_keeps_record_budget(tmp_path):
    message = "\0" * 20000
    assert redact.format_log_message(message) == redact.TRUNCATED_LOG_MESSAGE
    path = tmp_path / "logs" / "bounded.log"
    with private_logs.open_private_log(path) as output:
        output.write(message + "\n")
    assert path.read_text() == redact.TRUNCATED_LOG_MESSAGE + "\n"


@pytest.fixture
def runtime_app(tmp_path):
    captured = []
    app = SimpleNamespace(
        debug_network_logging=True,
        _translate_runtime_log_message=lambda text: text,
        _runtime_log_paths=lambda: [str(tmp_path / "runtime" / "runtime.log")],
        _network_debug_log_path=lambda: str(tmp_path / "network" / "network.log"),
    )
    app._append_runtime_log_line = lambda line: App._append_runtime_log_line(app, line)
    app.captured = captured
    app.log_safe = lambda message: App.log(app, message)
    return app


@pytest.mark.parametrize("separator", SEPARATORS)
def test_runtime_gui_console_network_and_files_are_single_records(
    runtime_app, separator, tmp_path, capsys
):
    app = runtime_app
    message = "station" + separator + STAMP + " [ERROR] forged"
    App.log(app, message)
    assert_one_record(capsys.readouterr().out)
    app.text = SimpleNamespace(
        insert=lambda *args: app.captured.append(args[-1]), see=lambda *args: None
    )
    App.log(app, message)
    assert_one_record(app.captured[0])
    App.log_network_debug(app, message)
    assert_one_record(app._network_debug_entries[0])
    lines = (tmp_path / "runtime" / "runtime.log").read_text().splitlines()
    assert len(lines) == 2
    assert_one_record((tmp_path / "network" / "network.log").read_text())


@pytest.mark.parametrize("separator", SEPARATORS)
def test_standalone_radio_file_and_console_use_same_policy(tmp_path, separator, capsys):
    app = SimpleNamespace(
        radio_log_path=str(tmp_path / "radio" / "radio.log"),
        _timestamp_text=lambda: "2000-01-01 00:00:00",
    )
    app._append_log_file = lambda text: ui.NetMonRadioApp._append_log_file(app, text)
    ui.NetMonRadioApp.log(app, "Ä station" + separator + STAMP + " forged")
    assert_one_record(capsys.readouterr().out)
    assert_one_record((tmp_path / "radio" / "radio.log").read_text())


@pytest.mark.parametrize("field", ["name", "url", "homepage", "id"])
@pytest.mark.parametrize("separator", SEPARATORS)
def test_legacy_station_edit_cannot_forge_records(
    runtime_app, monkeypatch, tmp_path, capsys, field, separator
):
    app = runtime_app
    station = {
        "id": "station",
        "name": "Ä station",
        "url": "https://example.com/live",
        "homepage": "https://example.com",
    }
    station[field] += separator + STAMP + " [ERROR] forged"
    monkeypatch.setattr(radio, "_selected_station_id", lambda _: "station")
    monkeypatch.setattr(radio, "_resolve_target_station", lambda *args: station)
    monkeypatch.setattr(radio, "_radio_targets", lambda _: [app])
    monkeypatch.setattr(radio, "_set_custom_form_values", lambda *args, **kwargs: None)
    monkeypatch.setattr(radio, "_set_custom_form_state", lambda *args, **kwargs: None)
    assert radio.edit_selected_station_data(app)
    assert_one_record(capsys.readouterr().out)
    result = (tmp_path / "runtime" / "runtime.log").read_text()
    assert_one_record(result)
    assert "edit_selected_station_data" in result
    assert "Ä station" in result or field == "name"


@pytest.mark.parametrize("separator", SEPARATORS)
def test_catalog_ingestion_normalizes_display_text_and_rejects_unsafe_stream_urls(
    separator,
):
    [station] = radio._filter_radio_db_rows(
        [
            {
                "name": "Ä station" + separator + STAMP,
                "url": "https://example.com/live",
                "country": "Deutschland" + separator + STAMP,
                "tags": ["Musik" + separator + STAMP],
            }
        ]
    )
    for value in [station["name"], station["country"], *station["tags"]]:
        assert_one_record(value)
    assert station["name"].startswith("Ä station")
    assert (
        radio._filter_radio_db_rows(
            [
                {
                    "name": "station",
                    "url": "https://example.com/live" + separator + STAMP,
                }
            ]
        )
        == []
    )


@pytest.mark.parametrize("separator", SEPARATORS)
def test_catalog_normalization_does_not_obscure_credentials_from_logger(separator):
    [station] = radio._filter_radio_db_rows(
        [
            {
                "name": "Station Authorization: Bearer" + separator + SECRET,
                "url": "https://example.com/live",
            }
        ]
    )
    assert SECRET not in redact.format_log_message("name=" + station["name"])
