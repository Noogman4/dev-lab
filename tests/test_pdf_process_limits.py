"""Crafted PDFs are parsed only in a bounded child, never in the desktop."""

import io
import os
import resource
import sys
import time
from types import SimpleNamespace
import zlib

import pytest

PyPDF2 = pytest.importorskip("PyPDF2")
from PyPDF2 import PdfWriter  # noqa: E402
from PyPDF2.generic import (  # noqa: E402
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)

from netmon.core import pdf_process as process  # noqa: E402
from netmon.core import pdf_worker as worker  # noqa: E402
from netmon.features import chad_controller as chad  # noqa: E402

APP = SimpleNamespace(tr=lambda _key, fallback: fallback)


def _page(writer, content: bytes):
    writer.add_blank_page(width=200, height=200)
    page = writer.pages[-1]
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    stream.set_data(content)
    page[NameObject("/Contents")] = stream


def pdf_bytes(*contents: bytes) -> bytes:
    writer = PdfWriter()
    for content in contents:
        _page(writer, content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def text_page(text: str) -> bytes:
    return f"BT /F1 12 Tf 10 100 Td ({text}) Tj ET".encode("latin-1")


def flate_bomb(expanded_bytes: int) -> bytes:
    """A one-page PDF whose content stream inflates to expanded_bytes."""
    compressor = zlib.compressobj(9)
    chunk = b" " * (1024 * 1024)
    parts = [compressor.compress(b"BT /F1 12 Tf 10 100 Td (bomb) Tj ET\n")]
    for _ in range(expanded_bytes // len(chunk)):
        parts.append(compressor.compress(chunk))
    parts.append(compressor.flush())
    compressed = b"".join(parts)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents 4 0 R"
        b" /Resources << /Font << /F1 << /Type /Font /Subtype /Type1"
        b" /BaseFont /Helvetica >> >> >> >>",
        b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(compressed)
        + compressed
        + b"\nendstream",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % number + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1))
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, xref)
    )
    return out.getvalue()


def test_regular_pdf_text_is_extracted_in_the_worker(tmp_path):
    path = tmp_path / "regular.pdf"
    path.write_bytes(pdf_bytes(text_page("first page"), text_page("second page")))
    text = chad.extract_pdf_text_for_chad(APP, str(path))
    assert "--- Page 1 ---\nfirst page" in text
    assert "--- Page 2 ---\nsecond page" in text
    assert "(truncated)" not in text


def test_decompression_bomb_fails_in_the_child_without_growing_the_desktop(
    tmp_path,
):
    payload = flate_bomb(2 * 1024 * 1024 * 1024)
    assert len(payload) < worker.MAX_INPUT_BYTES
    path = tmp_path / "bomb.pdf"
    path.write_bytes(payload)
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    started = time.monotonic()
    text = chad.extract_pdf_text_for_chad(APP, str(path))
    assert text.startswith("Error while reading PDF:")
    assert time.monotonic() - started < worker.MAX_WALL_SECONDS + 5
    grown_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - before
    assert grown_kib < 64 * 1024, "PDF content was inflated in the desktop process"


def test_page_and_character_budgets_truncate_inside_the_worker():
    many = pdf_bytes(*(text_page(f"page {n}") for n in range(1, 41)))
    pages, truncated = process.parse_pdf_snapshot(many)
    assert [number for number, _ in pages] == list(range(1, 31))
    assert truncated is True

    long_text = "A" * 60_000
    heavy = pdf_bytes(*(text_page(long_text) for _ in range(3)))
    pages, truncated = process.parse_pdf_snapshot(heavy)
    assert sum(len(text) for _, text in pages) == worker.MAX_TEXT_CHARS
    assert truncated is True


def test_truncated_pdf_gets_a_marker(tmp_path):
    path = tmp_path / "many.pdf"
    path.write_bytes(pdf_bytes(*(text_page(f"p{n}") for n in range(35))))
    assert chad.extract_pdf_text_for_chad(APP, str(path)).endswith(
        "--- (truncated) ---\n\n"
    )


def test_oversized_or_symlinked_files_never_reach_the_parser(tmp_path, monkeypatch):
    monkeypatch.setattr(
        process.subprocess,
        "Popen",
        lambda *_a, **_k: pytest.fail("parser started for a refused file"),
    )
    big = tmp_path / "big.pdf"
    big.write_bytes(b"%PDF-1.4\n" + b"0" * worker.MAX_INPUT_BYTES)
    assert "größer als" in chad.extract_pdf_text_for_chad(APP, str(big))
    target = tmp_path / "target.pdf"
    target.write_bytes(pdf_bytes(text_page("x")))
    link = tmp_path / "link.pdf"
    link.symlink_to(target)
    assert chad.extract_pdf_text_for_chad(APP, str(link)).startswith(
        "Error while reading PDF:"
    )


def test_worker_runs_with_hard_limits():
    code = (
        "import json,resource,runpy;"
        f"m=runpy.run_path({worker.__file__!r});m['apply_process_limits']();"
        "print(json.dumps({n:resource.getrlimit(getattr(resource,n))[1] for n in "
        "['RLIMIT_AS','RLIMIT_CPU','RLIMIT_NPROC','RLIMIT_FSIZE']}))"
    )
    import json
    import subprocess

    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        capture_output=True,
        timeout=10,
        check=True,
    )
    limits = json.loads(result.stdout)
    assert 0 < limits["RLIMIT_AS"] <= worker.MAX_MEMORY_BYTES
    assert 0 < limits["RLIMIT_CPU"] <= worker.MAX_CPU_SECONDS
    assert limits["RLIMIT_NPROC"] == 0
    assert 0 < limits["RLIMIT_FSIZE"] <= worker.MAX_REPLY_BYTES


def test_hanging_worker_is_killed_at_the_wall_clock_limit(monkeypatch):
    monkeypatch.setattr(process, "MAX_WALL_SECONDS", 1)
    monkeypatch.setattr(
        process,
        "_worker_command",
        lambda: [sys.executable, "-c", "import time; time.sleep(30)"],
    )
    started = time.monotonic()
    with pytest.raises(ValueError, match="time limit"):
        process.parse_pdf_snapshot(b"%PDF-1.4\n")
    assert time.monotonic() - started < 5


@pytest.mark.parametrize(
    "reply",
    [
        b"not json",
        b'{"pages": [], "truncated": 1}',
        b'{"pages": [[0, "x"]], "truncated": false}',
        b'{"pages": [[1, "x"]], "truncated": false, "extra": 1}',
        ('{"pages": [[1, "%s"]], "truncated": false}' % ("x" * 130_000)).encode(),
    ],
)
def test_malformed_worker_replies_are_rejected(monkeypatch, reply):
    script = f"import sys; sys.stdout.buffer.write({reply!r})"
    monkeypatch.setattr(
        process, "_worker_command", lambda: [sys.executable, "-c", script]
    )
    with pytest.raises(ValueError):
        process.parse_pdf_snapshot(b"%PDF-1.4\n")


def test_pdf_import_runs_off_the_tk_thread(monkeypatch):
    statuses, finished, threads = [], [], []
    app = SimpleNamespace(
        tr=lambda _key, default: default,
        chad_chat_status_var=SimpleNamespace(set=statuses.append),
        after=lambda _delay, callback: callback(),
    )

    class Deferred:
        def __init__(self, target, **_kwargs):
            self.target = target
            threads.append(self)

        def start(self):
            pass

    monkeypatch.setattr(chad, "threading", SimpleNamespace(Thread=Deferred))
    monkeypatch.setattr(
        chad, "extract_pdf_text_for_chad", lambda _app, _path: "pdf text"
    )
    monkeypatch.setattr(
        chad,
        "extract_docx_text_for_chad",
        lambda *_a: pytest.fail("wrong parser"),
    )
    monkeypatch.setattr(
        chad, "_finish_chad_text_import", lambda *args: finished.append(args[2:])
    )
    monkeypatch.setattr(chad, "call_in_ui_thread", lambda _app, fn: fn())

    chad._start_chad_docx_import(app, "crafted.pdf", 1234, ".pdf")
    # The click handler returned; nothing was parsed on the Tk thread.
    assert statuses == ["Reading PDF in a bounded parser process..."]
    assert finished == [] and app._chad_docx_import_running is True
    threads[0].target()
    assert finished == [(".pdf", 1234, "pdf text")]
    assert app._chad_docx_import_running is False


def test_import_dialog_routes_pdf_to_the_background_parser(monkeypatch, tmp_path):
    path = tmp_path / "doc.pdf"
    path.write_bytes(pdf_bytes(text_page("x")))
    started = []
    app = SimpleNamespace(
        tr=lambda _key, default, **_k: default,
        chad_chat_status_var=SimpleNamespace(set=lambda _v: None),
        chad_pending_files=[],
    )
    monkeypatch.setattr(chad, "ensure_chad_enabled", lambda _app: True)
    monkeypatch.setattr(chad.filedialog, "askopenfilename", lambda **_k: str(path))
    monkeypatch.setattr(chad.messagebox, "askyesno", lambda *_a, **_k: True)
    monkeypatch.setattr(
        chad,
        "extract_pdf_text_for_chad",
        lambda *_a: pytest.fail("PDF parsed synchronously in the dialog handler"),
    )
    monkeypatch.setattr(
        chad, "_start_chad_docx_import", lambda *args: started.append(args[1:])
    )
    chad.import_file_to_chad_chat(app)
    assert started == [(str(path), os.path.getsize(path), ".pdf")]
