"""User-selected structured imports are bounded before parsing; local files only."""

import csv
import io
import json
import os
import zipfile
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from netmon import app as app_module
from netmon.core import docx_archive
from netmon.core import import_limits as limits
from netmon.features import chad_controller as chad
from netmon.features import linux_help_controller as linux_help
from netmon.features import radio_controller as radio
from netmon.features import security_audit_controller as audit


class Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


# --- shared helper -----------------------------------------------------------


def test_bounded_read_accepts_exact_limit_and_rejects_one_more(tmp_path):
    path = tmp_path / "data.bin"
    path.write_bytes(b"x" * 10)
    assert limits.read_bounded_bytes(path, 10) == b"x" * 10
    with pytest.raises(limits.ImportLimitError, match="größer"):
        limits.read_bounded_bytes(path, 9)


def test_bounded_read_counts_real_bytes_not_only_stat(tmp_path, monkeypatch):
    path = tmp_path / "grows.bin"
    path.write_bytes(b"x" * 20)
    real_fstat = os.fstat
    calls = []

    def shrunk(fd):
        result = real_fstat(fd)
        calls.append(fd)
        if len(calls) == 1:
            values = list(result)
            values[6] = 5  # st_size claims 5 bytes
            return os.stat_result(values)
        return result

    monkeypatch.setattr(limits.os, "fstat", shrunk)
    with pytest.raises(limits.ImportLimitError):
        limits.read_bounded_bytes(path, 10)


def test_bounded_read_refuses_symlink_fifo_and_directory(tmp_path):
    target = tmp_path / "target.json"
    target.write_text("{}")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    fifo = tmp_path / "pipe.json"
    os.mkfifo(fifo)
    for path in (link, fifo, tmp_path):
        with pytest.raises(limits.ImportLimitError):
            limits.read_bounded_bytes(path, 1024)


def test_bounded_read_refuses_invalid_utf8(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(limits.ImportLimitError, match="utf-8"):
        limits.read_bounded_text(path, 1024)


def test_json_container_budget_ignores_brackets_inside_strings(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps({"text": "[" * 500 + "{" * 500, "list": [1, 2]}))
    assert limits.load_bounded_json(path, 4096, max_containers=2)["list"] == [1, 2]
    path.write_text(json.dumps([[] for _ in range(50)]))
    with pytest.raises(limits.ImportLimitError, match="Strukturen"):
        limits.load_bounded_json(path, 4096, max_containers=50)


def test_json_deep_nesting_is_an_import_error(tmp_path):
    path = tmp_path / "deep.json"
    path.write_text("[" * 100_000 + "]" * 100_000)
    with pytest.raises(limits.ImportLimitError, match="verschachtelt"):
        limits.load_bounded_json(path, 1024 * 1024, max_containers=10**6)


def test_bounded_list_rejects_overflow_and_non_lists():
    assert limits.bounded_list(None, 1) == []
    assert limits.bounded_list([1, 2], 2) == [1, 2]
    with pytest.raises(limits.ImportLimitError, match="mehr als 2"):
        limits.bounded_list([1, 2, 3], 2)
    with pytest.raises(limits.ImportLimitError, match="keine Liste"):
        limits.bounded_list("abc", 10)


# --- Linux help CSV / XLSX ---------------------------------------------------


def linux_help_app(tmp_path):
    return SimpleNamespace(
        linux_help_status_var=SimpleNamespace(set=Mock()),
        linux_help_data_path=str(tmp_path / "commands.json"),
        linux_help_glossary_path=str(tmp_path / "missing-glossary.json"),
        linux_help_data=[],
        tr=lambda key, fallback: fallback,
    )


def write_csv(path, rows, header=("category", "name", "cmd")):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)


def test_csv_import_keeps_dictreader_shape(tmp_path):
    path = tmp_path / "db.csv"
    path.write_text(
        "﻿category,name,cmd,info\r\nSystem,List,ls -la\r\n\r\n"
        'Net,"Ping, once",ping -c1 host,"multi\nline"\r\n',
        encoding="utf-8",
    )
    entries = linux_help.import_linux_help_csv(linux_help_app(tmp_path), path)
    assert sorted(item["cmd"] for item in entries) == ["ls -la", "ping -c1 host"]
    ping = next(item for item in entries if item["cmd"].startswith("ping"))
    assert ping["name"] == "Ping, once" and ping["info"] == "multi\nline"


@pytest.mark.parametrize("case", ["bytes", "rows", "columns", "cell"])
def test_csv_import_limits(tmp_path, monkeypatch, case):
    path = tmp_path / "db.csv"
    if case == "bytes":
        monkeypatch.setattr(linux_help, "MAX_SOURCE_CSV_BYTES", 64)
        write_csv(path, [("System", "List", "ls")] * 10)
    elif case == "rows":
        monkeypatch.setattr(linux_help, "MAX_SOURCE_ROWS", 3)
        write_csv(path, [("System", "List", "ls")] * 4)
    elif case == "columns":
        write_csv(path, [("System", "List", "ls")], header=[f"c{i}" for i in range(65)])
    else:
        monkeypatch.setattr(linux_help, "MAX_SOURCE_CELL_CHARS", 10)
        write_csv(path, [("System", "List", "x" * 11)])
    app = linux_help_app(tmp_path)
    with pytest.raises(limits.ImportLimitError):
        linux_help.import_linux_help_csv(app, path)
    assert app.linux_help_data == []


def test_csv_import_at_row_limit_is_accepted(tmp_path, monkeypatch):
    monkeypatch.setattr(linux_help, "MAX_SOURCE_ROWS", 3)
    path = tmp_path / "db.csv"
    write_csv(path, [("System", f"n{i}", f"echo {i}") for i in range(3)])
    assert len(linux_help.import_linux_help_csv(linux_help_app(tmp_path), path)) == 3


def xlsx_bytes(rows):
    openpyxl = pytest.importorskip("openpyxl")
    book = openpyxl.Workbook()
    for row in rows:
        book.active.append(list(row))
    stream = io.BytesIO()
    book.save(stream)
    book.close()
    return stream.getvalue()


def rewrite_member(raw, name, transform):
    source = zipfile.ZipFile(io.BytesIO(raw))
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            data = source.read(info)
            if info.filename == name:
                data = transform(data)
            target.writestr(info.filename, data)
    return output.getvalue()


def test_xlsx_decompression_bomb_never_reaches_openpyxl(tmp_path, monkeypatch):
    raw = xlsx_bytes([("category", "name", "cmd"), ("System", "List", "ls")])
    bomb = rewrite_member(
        raw,
        "xl/worksheets/sheet1.xml",
        lambda data: data.replace(b"</worksheet>", b" " * (4 * 1024 * 1024))
        + b"</worksheet>",
    )
    path = tmp_path / "bomb.xlsx"
    path.write_bytes(bomb)
    monkeypatch.setattr(
        linux_help, "load_workbook", Mock(side_effect=AssertionError("parsed"))
    )
    with pytest.raises(ValueError, match="XLSX member exceeds decompression limits"):
        linux_help.import_linux_help_csv(linux_help_app(tmp_path), path)


def test_xlsx_forged_dimension_is_rejected(tmp_path):
    raw = xlsx_bytes([("category", "name", "cmd"), ("System", "List", "ls")])
    forged = rewrite_member(
        raw,
        "xl/worksheets/sheet1.xml",
        lambda data: data.replace(b'ref="A1:C2"', b'ref="A1:XFD1048576"'),
    )
    assert forged != raw
    path = tmp_path / "forged.xlsx"
    path.write_bytes(forged)
    with pytest.raises(limits.ImportLimitError):
        linux_help.import_linux_help_csv(linux_help_app(tmp_path), path)


def test_xlsx_row_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(linux_help, "MAX_SOURCE_ROWS", 2)
    path = tmp_path / "rows.xlsx"
    path.write_bytes(xlsx_bytes([("category", "name", "cmd")] + [("S", "n", "ls")] * 3))
    with pytest.raises(limits.ImportLimitError, match="Zeilen"):
        linux_help.import_linux_help_csv(linux_help_app(tmp_path), path)


def test_xlsx_and_docx_share_the_validator_with_own_labels(tmp_path):
    path = tmp_path / "empty.xlsx"
    path.write_bytes(b"not a zip")
    with pytest.raises(ValueError) as caught:
        with docx_archive.open_validated_xlsx(path):
            pass
    assert "DOCX" not in str(caught.value)


# --- Radio M3U ---------------------------------------------------------------


def test_m3u_valid_playlist_with_mixed_line_endings(tmp_path):
    path = tmp_path / "list.m3u"
    path.write_bytes(b"#EXTM3U\r\nhttp://a.example/1\rhttp://b.example/2\n\n#c\n")
    assert radio._read_m3u_playlist(str(path)) == [
        "http://a.example/1",
        "http://b.example/2",
    ]


@pytest.mark.parametrize("case", ["bytes", "entries", "line"])
def test_m3u_limits_reject_whole_playlist(tmp_path, monkeypatch, case):
    path = tmp_path / "list.m3u"
    if case == "bytes":
        monkeypatch.setattr(radio, "MAX_M3U_BYTES", 32)
        path.write_text("http://a.example/1\n" * 4)
    elif case == "entries":
        monkeypatch.setattr(radio, "MAX_M3U_ENTRIES", 3)
        path.write_text("http://a.example/1\n" * 4)
    else:
        monkeypatch.setattr(radio, "MAX_M3U_LINE_CHARS", 20)
        path.write_text("http://a.example/" + "x" * 10 + "\n")
    assert radio._read_m3u_playlist(str(path)) == []


# --- Security baseline transfer ------------------------------------------------


def baseline_package(rules=0):
    return {
        "schema": audit.SECURITY_BASELINE_TRANSFER_SCHEMA,
        "schema_version": audit.SECURITY_BASELINE_TRANSFER_SCHEMA_VERSION,
        "baseline": {"id": "imported"},
        "sysctl": {"entries": [{"key": "kernel.kptr_restrict", "expected": "2"}]},
        "ufw": {
            "default_incoming": "deny",
            "default_outgoing": "allow",
            "rules": [{}] * rules,
        },
    }


def test_baseline_transfer_file_size_is_bounded(tmp_path, monkeypatch):
    path = tmp_path / "transfer.json"
    path.write_text(json.dumps(baseline_package()))
    assert audit._read_security_baseline_transfer_package(str(path))["baseline"]
    monkeypatch.setattr(audit, "MAX_BASELINE_TRANSFER_BYTES", 64)
    with pytest.raises(limits.ImportLimitError):
        audit._read_security_baseline_transfer_package(str(path))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["ufw"].update(rules=[{}] * 5),
        lambda p: p["sysctl"].update(entries=[{}] * 5),
        lambda p: p.update(notes=["n"] * 5),
        lambda p: p["baseline"].update(roles=["r"] * 5),
        lambda p: p["ufw"].update(profile_targets=["t"] * 5),
    ],
)
def test_baseline_transfer_lists_are_bounded(monkeypatch, mutate):
    monkeypatch.setattr(audit, "MAX_BASELINE_TRANSFER_ITEMS", 4)
    payload = baseline_package()
    mutate(payload)
    with pytest.raises(limits.ImportLimitError, match="mehr als 4"):
        audit._validate_security_baseline_transfer_package(payload)


def test_baseline_transfer_import_reports_limit_without_state(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "MAX_BASELINE_TRANSFER_BYTES", 16)
    path = tmp_path / "transfer.json"
    path.write_text(json.dumps(baseline_package()))
    errors = []
    state = Mock()
    monkeypatch.setattr(audit, "_set_security_baseline_transfer_state", state)
    result = audit.import_security_baseline_transfer(
        SimpleNamespace(tr=lambda key, fallback: fallback),
        str(path),
        showerror_fn=lambda *args, **kwargs: errors.append(args),
    )
    assert result is False and errors
    state.assert_not_called()


# --- Theme Studio ----------------------------------------------------------------


def theme_app(tmp_path, monkeypatch, path):
    monkeypatch.setattr(
        app_module.filedialog, "askopenfilename", lambda **kwargs: str(path)
    )
    fake = SimpleNamespace(
        theme_studio_status_var=Var(),
        tr=lambda key, fallback: fallback,
        _ensure_theme_studio_profiles_dir=lambda: str(tmp_path),
        apply_theme_studio_settings=Mock(),
    )
    return fake


def test_theme_file_over_limit_is_not_parsed(tmp_path, monkeypatch):
    path = tmp_path / "theme.json"
    path.write_text(json.dumps({"profile_name": "x" * (256 * 1024)}))
    fake = theme_app(tmp_path, monkeypatch, path)
    assert app_module.App.load_theme_studio_profile(fake) is False
    assert "Theme laden fehlgeschlagen" in fake.theme_studio_status_var.get()
    fake.apply_theme_studio_settings.assert_not_called()


def test_theme_file_with_many_structures_is_refused(tmp_path, monkeypatch):
    path = tmp_path / "theme.json"
    path.write_text(json.dumps({"accent": [[]] * 2000}))
    fake = theme_app(tmp_path, monkeypatch, path)
    assert app_module.App.load_theme_studio_profile(fake) is False
    assert "Strukturen" in fake.theme_studio_status_var.get()


# --- Chad analysis ------------------------------------------------------------------


def chad_app(monkeypatch, path):
    monkeypatch.setattr(chad, "ensure_chad_enabled", lambda app: True)
    monkeypatch.setattr(chad, "log_chad_error", lambda *args: None)
    monkeypatch.setattr(
        chad,
        "filedialog",
        SimpleNamespace(askopenfilename=lambda **kwargs: str(path)),
    )
    return SimpleNamespace(
        chad_analysis_status_var=Var(),
        chad_analysis_source_var=Var(),
        chad_chat_history=["old"],
        chad_output_entries=["old"],
        chad_analysis_current_prompt="old",
        chad_online_result="old",
        tr=lambda key, fallback=None: fallback or key,
    )


@pytest.mark.parametrize("suffix", [".json", ".txt"])
def test_chad_analysis_file_over_limit_keeps_state(tmp_path, monkeypatch, suffix):
    monkeypatch.setattr(chad, "MAX_CHAD_ANALYSIS_BYTES", 64)
    path = tmp_path / ("analysis" + suffix)
    path.write_text(json.dumps({"transcript": "x" * 100}))
    app = chad_app(monkeypatch, path)
    chad.load_chad_analysis_from_file(app)
    assert "konnte nicht geladen werden" in app.chad_analysis_status_var.get()
    assert app.chad_chat_history == ["old"] and app.chad_online_result == "old"


@pytest.mark.parametrize("field", ["chat_history", "output_entries"])
def test_chad_analysis_lists_are_bounded(tmp_path, monkeypatch, field):
    monkeypatch.setattr(chad, "MAX_CHAD_ANALYSIS_ITEMS", 3)
    path = tmp_path / "analysis.json"
    path.write_text(json.dumps({field: ["x"] * 4}))
    app = chad_app(monkeypatch, path)
    chad.load_chad_analysis_from_file(app)
    assert "mehr als 3" in app.chad_analysis_status_var.get()
    assert app.chad_chat_history == ["old"]


def test_chad_analysis_non_object_json_is_refused(tmp_path, monkeypatch):
    path = tmp_path / "analysis.json"
    path.write_text("[1, 2]")
    app = chad_app(monkeypatch, path)
    chad.load_chad_analysis_from_file(app)
    assert "kein JSON-Objekt" in app.chad_analysis_status_var.get()
