"""Bounded synthetic DOCX workers; never change the test runner's rlimits."""

import io
import json
import resource
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import zipfile

import docx
from lxml import etree
import pytest

from netmon.core import docx_process as process
from netmon.core import docx_worker as worker
from netmon.features import chad_controller as chad


def stored_document(text):
    document = docx.Document()
    document.add_paragraph(text)
    compressed = io.BytesIO()
    document.save(compressed)
    output = io.BytesIO()
    with zipfile.ZipFile(compressed) as source, zipfile.ZipFile(output, "w") as target:
        for member in source.infolist():
            target.writestr(member.filename, source.read(member))
    return output.getvalue()


def probe_command(code):
    bootstrap = f"import runpy; m=runpy.run_path({worker.__file__!r}); m['apply_process_limits'](); "
    return [sys.executable, "-I", "-B", "-c", bootstrap + code]


def test_real_child_limits_and_parent_limits_unchanged():
    before = {
        name: resource.getrlimit(name)
        for name in (resource.RLIMIT_AS, resource.RLIMIT_CPU, resource.RLIMIT_NOFILE)
    }
    names = [
        "RLIMIT_AS",
        "RLIMIT_CPU",
        "RLIMIT_NOFILE",
        "RLIMIT_NPROC",
        "RLIMIT_FSIZE",
        "RLIMIT_CORE",
    ]
    code = f"import json,resource; print(json.dumps({{name:resource.getrlimit(getattr(resource,name)) for name in {names!r}}}))"
    result = subprocess.run(
        probe_command(code), capture_output=True, timeout=8, check=True
    )
    limits = json.loads(result.stdout)
    assert 0 < limits["RLIMIT_AS"][1] <= worker.MAX_MEMORY_BYTES
    assert 0 < limits["RLIMIT_CPU"][1] <= worker.MAX_CPU_SECONDS
    assert limits["RLIMIT_NOFILE"][1] <= 32
    assert limits["RLIMIT_NPROC"][1] == 0
    assert limits["RLIMIT_FSIZE"][1] <= worker.MAX_REPLY_BYTES
    assert limits["RLIMIT_CORE"][1] == 0
    assert before == {name: resource.getrlimit(name) for name in before}


def test_child_memory_limit_prevents_excessive_allocation():
    code = "\ntry:\n bytearray(2*m['MAX_MEMORY_BYTES'])\nexcept MemoryError:\n print('bounded')\nelse:\n raise AssertionError('memory limit failed')\n"
    result = subprocess.run(
        probe_command(code), capture_output=True, timeout=8, check=True
    )
    assert result.stdout.strip() == b"bounded"


def test_cpu_spin_is_terminated_by_kernel_limit():
    result = subprocess.run(
        probe_command("\nwhile True: pass\n"),
        capture_output=True,
        timeout=12,
        check=False,
    )
    assert result.returncode < 0


def test_wall_timeout_kills_and_reaps_worker(monkeypatch):
    monkeypatch.setattr(process, "MAX_WALL_SECONDS", 0.2)
    monkeypatch.setattr(
        process, "_worker_command", lambda: probe_command("import time; time.sleep(30)")
    )
    children = []
    original = process.subprocess.Popen

    def launch(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(process.subprocess, "Popen", launch)
    start = time.monotonic()
    with pytest.raises(ValueError, match="time limit"):
        process.parse_docx_snapshot(b"synthetic")
    assert time.monotonic() - start < 2
    assert len(children) == 1 and children[0].returncode is not None


def test_child_cannot_write_unbounded_reply(monkeypatch):
    monkeypatch.setattr(
        process,
        "_worker_command",
        lambda: probe_command(
            "import os; os.write(1,b'x'*(m['MAX_REPLY_BYTES']+4096))"
        ),
    )
    with pytest.raises(ValueError, match="resource limits|reply"):
        process.parse_docx_snapshot(b"synthetic")


@pytest.mark.parametrize(
    "reply",
    [
        b"[]",
        b"{}",
        b"not-json",
        b'{"text":1,"truncated":false}',
        b'{"text":"x","truncated":1}',
    ],
)
def test_parent_rejects_malformed_worker_reply(monkeypatch, reply):
    monkeypatch.setattr(
        process,
        "_worker_command",
        lambda: probe_command(f"import os; os.write(1,{reply!r})"),
    )
    with pytest.raises(ValueError, match="reply"):
        process.parse_docx_snapshot(b"synthetic")


def test_resource_setup_failure_aborts_before_input_or_parser(monkeypatch):
    def fail():
        raise OSError("synthetic unsupported limit")

    monkeypatch.setattr(worker, "apply_process_limits", fail)
    monkeypatch.setattr(
        worker,
        "parse_snapshot",
        lambda _payload: pytest.fail("parser ran without resource limits"),
    )
    assert worker.main() == 1


def test_worker_respects_stricter_inherited_limits(monkeypatch):
    applied = {}
    monkeypatch.setattr(resource, "getrlimit", lambda _name: (1, 2))
    monkeypatch.setattr(
        resource, "setrlimit", lambda name, values: applied.update({name: values})
    )
    worker.apply_process_limits()
    assert applied[resource.RLIMIT_AS] == (1, 1)
    assert applied[resource.RLIMIT_CPU] == (1, 1)
    assert applied[resource.RLIMIT_CORE] == (0, 0)


@pytest.mark.parametrize("kind", ["nodes", "depth", "doctype", "span"])
def test_xml_structure_is_checked_before_docx_parser(monkeypatch, kind):
    if kind == "nodes":
        monkeypatch.setattr(worker, "MAX_XML_NODES", 4)
        content = b"<root><a/><a/><a/><a/></root>"
    elif kind == "depth":
        monkeypatch.setattr(worker, "MAX_XML_DEPTH", 4)
        content = b"<a>" * 5 + b"</a>" * 5
    elif kind == "doctype":
        content = b'<!DOCTYPE root [<!ENTITY test "bounded">]><root>&test;</root>'
    else:
        content = b'<w:gridSpan xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" w:val="129"/>'
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("ignored.xml", content)
    monkeypatch.setattr(
        docx,
        "Document",
        lambda _input: pytest.fail("structure was not checked before python-docx"),
    )
    with pytest.raises(ValueError):
        worker.parse_snapshot(stream.getvalue())


def test_text_budget_stops_before_visiting_rest_of_document(monkeypatch):
    monkeypatch.setattr(worker, "MAX_TEXT_CHARS", 10)
    paragraph = etree.fromstring(
        b'<w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:r><w:t>abcdefghijklmnop</w:t></w:r></w:p>'
    )

    class Body:
        def iterchildren(self, _tag):
            yield paragraph
            pytest.fail("extraction continued after reaching the output budget")

    assert worker.extract_bounded_text(
        SimpleNamespace(element=SimpleNamespace(body=Body()))
    ) == ("abcdefghij", True)


def test_real_worker_caps_text_and_controller_adds_truncation_marker(tmp_path):
    path = tmp_path / "long.docx"
    path.write_bytes(stored_document("x" * 160_000))
    app = SimpleNamespace(tr=lambda _key, default: default)
    result = chad.extract_docx_text_for_chad(app, str(path))
    assert len(result) <= worker.MAX_TEXT_CHARS
    assert result.startswith("x" * 100) and result.endswith("--- (truncated) ---\n\n")


def test_real_worker_rejects_excessive_xml_nodes(tmp_path):
    original = stored_document("normal")
    stream = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(original)) as source,
        zipfile.ZipFile(stream, "w") as archive,
    ):
        for member in source.infolist():
            archive.writestr(member.filename, source.read(member))
        archive.writestr(
            "ignored.xml", b"<root>" + b"<x/>" * worker.MAX_XML_NODES + b"</root>"
        )
    path = tmp_path / "wide.docx"
    path.write_bytes(stream.getvalue())
    result = chad.extract_docx_text_for_chad(
        SimpleNamespace(tr=lambda _key, default: default), str(path)
    )
    assert result.startswith("Error while reading DOCX:")


@pytest.mark.parametrize("discard", [False, True])
def test_docx_import_keeps_ui_responsive_and_applies_only_live_result(
    monkeypatch, discard
):
    entered, release = threading.Event(), threading.Event()
    queued, results, statuses, threads = [], [], [], []
    app = SimpleNamespace(
        tr=lambda _key, default: default,
        chad_chat_status_var=SimpleNamespace(set=statuses.append),
        after=lambda _delay, callback: queued.append(callback),
    )

    def parse(_app, _path):
        entered.set()
        assert release.wait(3)
        return "captured text"

    def launch(*args, **kwargs):
        thread = threading.Thread(*args, **kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr(chad, "threading", SimpleNamespace(Thread=launch))
    monkeypatch.setattr(chad, "extract_docx_text_for_chad", parse)
    monkeypatch.setattr(
        chad, "_finish_chad_text_import", lambda *_args: results.append(_args[-1])
    )
    try:
        chad._start_chad_docx_import(app, "synthetic.docx", 1)
        assert entered.wait(1)
        assert app._chad_docx_import_running and not results
        if discard:
            app._chad_docx_import_token = None
    finally:
        release.set()
        for thread in threads:
            thread.join(3)
    assert len(queued) == 1 and not threads[0].is_alive()
    queued[0]()
    assert results == ([] if discard else ["captured text"])
    assert app._chad_docx_import_running is False


def test_thread_start_failure_releases_import_guard(monkeypatch):
    app = SimpleNamespace(
        tr=lambda _key, default: default,
        chad_chat_status_var=SimpleNamespace(set=lambda _value: None),
    )

    class Unavailable:
        def __init__(self, **_kwargs):
            pass

        def start(self):
            raise RuntimeError("synthetic thread limit")

    monkeypatch.setattr(chad, "threading", SimpleNamespace(Thread=Unavailable))
    with pytest.raises(RuntimeError):
        chad._start_chad_docx_import(app, "synthetic.docx", 1)
    assert app._chad_docx_import_running is False
    assert app._chad_docx_import_token is None


def test_pending_import_blocks_second_dialog_and_worker(monkeypatch):
    statuses = []
    app = SimpleNamespace(
        _chad_docx_import_running=True,
        tr=lambda _key, default: default,
        chad_chat_status_var=SimpleNamespace(set=statuses.append),
    )
    monkeypatch.setattr(chad, "ensure_chad_enabled", lambda _app: True)
    monkeypatch.setattr(
        chad.filedialog,
        "askopenfilename",
        lambda **_kw: pytest.fail("second import started"),
    )
    chad.import_file_to_chad_chat(app)
    assert statuses == ["Reading DOCX in a bounded parser process..."]


def test_unexpected_background_failure_releases_guard_without_chat_mutation(
    monkeypatch,
):
    statuses = []
    app = SimpleNamespace(
        tr=lambda _key, default: default,
        chad_chat_status_var=SimpleNamespace(set=statuses.append),
    )

    class Immediate:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    def fail(*_args):
        raise RuntimeError("synthetic parser failure")

    monkeypatch.setattr(chad, "threading", SimpleNamespace(Thread=Immediate))
    monkeypatch.setattr(chad, "extract_docx_text_for_chad", fail)
    monkeypatch.setattr(
        chad,
        "_finish_chad_text_import",
        lambda *_args: pytest.fail("failed document reached chat"),
    )
    chad._start_chad_docx_import(app, "synthetic.docx", 1)
    assert app._chad_docx_import_running is False
    assert statuses[-1].startswith("Error during file import:")
