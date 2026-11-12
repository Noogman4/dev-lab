"""Bounded command database imports; synthetic files, no command execution."""

import io
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
from types import SimpleNamespace
import zipfile

import pytest

from netmon.core import linux_help_process as process
from netmon.core import linux_help_worker as worker
from netmon.core.import_limits import ImportLimitError
from netmon.features import linux_help_controller as controller
from tests.test_import_resource_limits import linux_help_app, xlsx_bytes, write_csv

REAL_POPEN = subprocess.Popen
REAL_THREAD = threading.Thread


@pytest.fixture
def app(tmp_path):
    result = linux_help_app(tmp_path)
    result.linux_help_data = [{"id": "existing", "cmd": "keep this entry"}]
    return result


@pytest.mark.parametrize("kind", ["csv", "xlsx"])
@pytest.mark.parametrize("budget", ["MAX_SOURCE_CELLS", "MAX_SOURCE_TEXT_CHARS"])
def test_total_budgets_reject_without_database_mutation(
    app, tmp_path, monkeypatch, kind, budget
):
    rows = [("System", f"n{i}", "echo " + "x" * 100) for i in range(4)]
    path = tmp_path / ("db." + kind)
    if kind == "csv":
        write_csv(path, rows)
    else:
        path.write_bytes(xlsx_bytes([("category", "name", "cmd"), *rows]))
    monkeypatch.setattr(controller, budget, 3 if budget.endswith("CELLS") else 150)
    before = list(app.linux_help_data)
    with pytest.raises(ImportLimitError):
        controller.import_linux_help_csv(app, path)
    assert app.linux_help_data == before


def shared_string_workbook():
    raw = xlsx_bytes(
        [("category", "name", "cmd"), *[("repeat", f"n{i}", "true") for i in range(5)]]
    )
    output = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(raw)) as source,
        zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as target,
    ):
        for item in source.infolist():
            data = source.read(item)
            if item.filename == "xl/worksheets/sheet1.xml":
                data = re.sub(
                    rb'<c r="(A[2-6])" t="inlineStr">.*?</c>',
                    rb'<c r="\1" t="s"><v>0</v></c>',
                    data,
                )
            if item.filename == "[Content_Types].xml":
                data = data.replace(
                    b"</Types>",
                    b'<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>',
                )
            target.writestr(item.filename, data)
        target.writestr(
            "xl/sharedStrings.xml",
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="5" uniqueCount="1"><si><t>'
            + "x" * 50_000
            + "</t></si></sst>",
        )
    return output.getvalue()


def test_shared_strings_count_each_expanded_use(app, tmp_path, monkeypatch):
    path = tmp_path / "repeated.xlsx"
    path.write_bytes(shared_string_workbook())
    # Each cell is below 64 KiB; repeated references exceed aggregate text.
    monkeypatch.setattr(controller, "MAX_SOURCE_TEXT_CHARS", 150_000)
    with pytest.raises(ImportLimitError, match="Gesamtgrenze fuer Text"):
        controller.import_linux_help_csv(app, path)
    assert app.linux_help_data[0]["id"] == "existing"


@pytest.mark.parametrize(
    "change",
    ["hidden-column", "sparse-row", "dimension", "row-number", "implicit-cells"],
)
def test_xlsx_coordinates_cannot_bypass_declared_dimensions(app, tmp_path, change):
    raw = xlsx_bytes([("category", "name", "cmd"), ("System", "n", "true")])
    output = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(raw)) as source,
        zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as target,
    ):
        for item in source.infolist():
            data = source.read(item)
            if item.filename == "xl/worksheets/sheet1.xml":
                if change == "hidden-column":
                    data = data.replace(b'r="C2"', b'r="XFD2"')
                elif change == "sparse-row":
                    data = data.replace(b'r="C2"', b'r="C1048576"')
                elif change == "row-number":
                    data = data.replace(b'<row r="2">', b'<row r="1048576">')
                elif change == "implicit-cells":
                    data = data.replace(
                        b"</row>", b'<c t="n"><v>1</v></c>' * 65 + b"</row>", 1
                    )
                else:
                    data = data.replace(b'ref="A1:C2"', b'ref="A1:XFD1048576"')
            target.writestr(item.filename, data)
    path = tmp_path / "bad.xlsx"
    path.write_bytes(output.getvalue())
    with pytest.raises(ImportLimitError):
        controller.import_linux_help_csv(app, path)
    assert app.linux_help_data[0]["id"] == "existing"


@pytest.mark.parametrize("attack", ["nodes", "depth", "doctype"])
def test_xml_structure_preflight_is_bounded(tmp_path, monkeypatch, attack):
    if attack == "nodes":
        monkeypatch.setattr(worker, "MAX_XML_NODES", 3)
        data = b"<root><a/><a/><a/></root>"
    elif attack == "depth":
        monkeypatch.setattr(worker, "MAX_XML_DEPTH", 3)
        data = b"<r><a><b><c/></b></a></r>"
    else:
        data = (
            b'<!DOCTYPE root [<!ENTITY e SYSTEM "file:///not-read">]><root>&e;</root>'
        )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("xl/test.xml", data)
    with pytest.raises(ValueError):
        worker.check_xlsx_xml(output.getvalue(), rows=10, columns=10)


def test_default_database_imports_in_real_worker(tmp_path):
    source = Path(controller.linux_help_csv_path())
    result = controller._load_linux_help_commands(source)
    assert len(result) > 500
    assert len({item["id"] for item in result}) == len(result)
    assert all(item["entry_type"] == "command" for item in result)


def test_worker_receives_immutable_selected_bytes(app, tmp_path, monkeypatch):
    path = tmp_path / "db.csv"
    write_csv(path, [("System", "original", "echo original")])
    original = process._worker_command

    def command(*args):
        write_csv(path, [("System", "replacement", "echo replacement")])
        return original(*args)

    monkeypatch.setattr(process, "_worker_command", command)
    result = controller.import_linux_help_csv(app, path)
    assert result[0]["cmd"] == "echo original"


@pytest.mark.parametrize("behavior", ["silent", "partial", "cpu", "memory", "output"])
def test_worker_failure_budgets_preserve_database_and_reap(
    app, tmp_path, monkeypatch, behavior
):
    path = tmp_path / "db.csv"
    write_csv(path, [("System", "n", "true")])
    prefix = (
        "import sys;sys.path.insert(0,"
        + repr(str(Path(__file__).resolve().parents[1]))
        + ");from netmon.core.linux_help_worker import apply_limits;apply_limits();"
    )
    scripts = {
        "silent": "import time;time.sleep(60)",
        "partial": "import os,time;os.write(1,b'{');time.sleep(60)",
        "cpu": prefix + 'exec("while True: pass")',
        "memory": prefix + "data=bytearray(1024*1024*1024)",
        "output": prefix + "import os;exec(\"while True: os.write(1,b'x'*65536)\")",
    }
    monkeypatch.setattr(
        process,
        "_worker_command",
        lambda *_args: [sys.executable, "-I", "-u", "-c", scripts[behavior]],
    )
    monkeypatch.setattr(
        process, "MAX_WALL_SECONDS", 0.15 if behavior in {"silent", "partial"} else 6
    )
    children = []

    def launch(*args, **kwargs):
        child = REAL_POPEN(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(process.subprocess, "Popen", launch)
    with pytest.raises(ImportLimitError):
        controller.import_linux_help_csv(app, path)
    assert app.linux_help_data[0]["id"] == "existing"
    assert children[0].returncode is not None


@pytest.mark.parametrize(
    "reply",
    [
        b"not-json",
        b"[]",
        b'{"commands":{}}',
        b'{"commands":[{}]}',
        b'{"error":[]}',
        b'{"extra":1,"commands":[]}',
    ],
)
def test_invalid_worker_replies_never_replace_data(app, tmp_path, monkeypatch, reply):
    path = tmp_path / "db.csv"
    write_csv(path, [("System", "n", "true")])
    monkeypatch.setattr(
        process,
        "_worker_command",
        lambda *_args: [
            sys.executable,
            "-I",
            "-c",
            "import sys;sys.stdout.buffer.write(" + repr(reply) + ")",
        ],
    )
    with pytest.raises(ImportLimitError):
        controller.import_linux_help_csv(app, path)
    assert app.linux_help_data[0]["id"] == "existing"


def test_reply_byte_limit_checked_before_json(app, tmp_path, monkeypatch):
    path = tmp_path / "db.csv"
    write_csv(path, [("System", "n", "true")])
    monkeypatch.setattr(process, "MAX_REPLY_BYTES", 64)
    monkeypatch.setattr(
        process,
        "_worker_command",
        lambda *_a: [sys.executable, "-I", "-c", "print('x'*65)"],
    )
    with pytest.raises(ImportLimitError, match="Ausgabegrenze"):
        controller.import_linux_help_csv(app, path)


def test_resource_limits_are_set_before_parser_import(tmp_path):
    script = (
        "import sys,json,resource;sys.path.insert(0,"
        + repr(str(Path(__file__).resolve().parents[1]))
        + ");from netmon.core import linux_help_worker as w;w.apply_limits();print(json.dumps([resource.getrlimit(x)[0] for x in (resource.RLIMIT_AS,resource.RLIMIT_CPU,resource.RLIMIT_FSIZE,resource.RLIMIT_NPROC)]))"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        capture_output=True,
        text=True,
        timeout=3,
        check=True,
    )
    memory, cpu, output, processes = json.loads(result.stdout)
    assert memory <= worker.MAX_MEMORY_BYTES and cpu <= worker.MAX_CPU_SECONDS
    assert output <= worker.MAX_REPLY_BYTES and processes == 0


@pytest.mark.parametrize("result", ["success", "error", "edited"])
def test_import_dialog_parses_off_ui_and_publishes_only_complete_result(
    app, tmp_path, monkeypatch, result
):
    callbacks = queue.Queue()
    entered = threading.Event()
    release = threading.Event()
    threads = []
    saved = []
    app.after = lambda _delay, callback: callbacks.put(callback)
    for name in (
        "linux_help_category_var",
        "linux_help_source_var",
        "linux_help_risk_filter_var",
    ):
        setattr(app, name, SimpleNamespace(set=lambda _value: None))
    monkeypatch.setattr(
        controller.filedialog, "askopenfilename", lambda **_kw: str(tmp_path / "db.csv")
    )
    for name in (
        "rebuild_linux_help_indexes",
        "sync_linux_help_form_categories",
        "refresh_linux_help_list",
        "update_linux_help_notes",
    ):
        monkeypatch.setattr(controller, name, lambda *_a, **_kw: None)
    monkeypatch.setattr(
        controller, "save_linux_help_data", lambda *_a, **_kw: saved.append(True)
    )

    def parse(_path):
        assert threading.current_thread() is not threading.main_thread()
        entered.set()
        assert release.wait(3)
        if result == "error":
            raise ImportLimitError("Import: synthetic failure")
        return [{"id": "new", "cmd": "true"}]

    monkeypatch.setattr(controller, "_load_linux_help_commands", parse)

    def launch(**kwargs):
        thread = REAL_THREAD(**kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr(controller, "threading", SimpleNamespace(Thread=launch))
    controller.linux_help_import_csv_dialog(app)
    try:
        assert entered.wait(3)
        assert app.linux_help_data[0]["id"] == "existing"
        assert app.linux_help_import_running
        # Busy re-entry must not start another dialog/worker.
        controller.linux_help_import_csv_dialog(app)
        assert len(threads) == 1
        if result == "edited":
            app.linux_help_data[0]["cmd"] = "edited while importing"
    finally:
        release.set()
        threads[0].join(3)
    assert not threads[0].is_alive()
    callbacks.get(timeout=3)()
    assert not app.linux_help_import_running
    assert saved == ([True] if result == "success" else [])
    assert app.linux_help_data[0]["id"] == (
        "new" if result == "success" else "existing"
    )
