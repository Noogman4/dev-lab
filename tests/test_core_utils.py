import json

from netmon.core import utils


def test_format_table_normalizes_rows_and_empty_body():
    assert utils.format_table(["Name", "Wert"], []) == (
        "Name | Wert\n" "-----+-----\n" "(keine Regeln)"
    )

    assert utils.format_table(["A", "B"], [[1], ["long", 23]]) == (
        "A    | B \n" "-----+---\n" "1    |   \n" "long | 23"
    )


def test_format_table_without_headers_returns_empty_string():
    assert utils.format_table([], [["ignored"]]) == ""
    assert utils.format_table(None, [["ignored"]]) == ""


def test_human_size_keeps_existing_display_contract():
    assert utils.human_size(None) == "\u2013"
    assert utils.human_size("bad") == "\u2013"
    assert utils.human_size(-1) == "0 B"
    assert utils.human_size(0) == "0 B"
    assert utils.human_size(1023) == "1023 B"
    assert utils.human_size(1024) == "1.0 KiB"
    assert utils.human_size(1024 * 1024 * 1.5) == "1.5 MiB"


def test_human_rate_keeps_existing_display_contract():
    assert utils.human_rate(-1) == "0 B/s"
    assert utils.human_rate(1023) == "1023 B/s"
    assert utils.human_rate(1024) == "1.0 KiB/s"
    assert utils.human_rate(1024 * 1024 * 2.25) == "2.2 MiB/s"


def test_safe_write_json_creates_parent_and_writes_payload(tmp_path):
    target = tmp_path / "nested" / "state.json"

    ok, err = utils.safe_write_json(target, {"alpha": 1, "beta": ["x"]})

    assert ok is True
    assert err == ""
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "alpha": 1,
        "beta": ["x"],
    }


def test_safe_write_json_removes_temp_file_after_serialization_error(tmp_path):
    target = tmp_path / "state.json"

    ok, err = utils.safe_write_json(target, {"bad": {object()}})

    assert ok is False
    assert "not JSON serializable" in err
    assert not target.exists()


def test_call_in_ui_thread_runs_directly_on_main_thread():
    calls = []

    class App:
        def after(self, *_args):
            raise AssertionError("after must not be used on the main thread")

    utils.call_in_ui_thread(App(), lambda: calls.append("called"))

    assert calls == ["called"]
