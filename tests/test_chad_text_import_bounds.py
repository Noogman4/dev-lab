"""Chad text import reads one bounded regular file; synthetic files only."""

import os
import signal
from types import SimpleNamespace

import pytest

from netmon.core import image_snapshot as images
from netmon.features import chad_controller as chad


@pytest.fixture
def importer(tmp_path, monkeypatch):
    output, statuses, warnings = [], [], []
    app = SimpleNamespace(
        tr=lambda _key, default: default,
        chad_pending_files=[],
        chad_chat_history=[],
        chad_chat_status_var=SimpleNamespace(set=statuses.append),
    )
    selected = {"path": ""}
    monkeypatch.setattr(chad, "ensure_chad_enabled", lambda _app: True)
    monkeypatch.setattr(
        chad.filedialog, "askopenfilename", lambda **_kw: selected["path"]
    )
    monkeypatch.setattr(chad.messagebox, "askyesno", lambda *_a, **_kw: True)
    monkeypatch.setattr(
        chad.messagebox,
        "showwarning",
        lambda _title, body, **_kw: warnings.append(body),
    )
    monkeypatch.setattr(
        chad, "append_to_chad_output", lambda _app, _title, text: output.append(text)
    )

    def run(path):
        selected["path"] = str(path)
        # A blocking open/read must fail the test instead of hanging it.
        previous = signal.signal(signal.SIGALRM, _timeout)
        signal.alarm(5)
        try:
            chad.import_file_to_chad_chat(app)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous)

    return SimpleNamespace(
        app=app, output=output, statuses=statuses, warnings=warnings, run=run
    )


def _timeout(*_args):
    raise TimeoutError("import blocked")


def test_regular_text_file_is_imported(importer, tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("Resolver meldet SERVFAIL\n")
    importer.run(path)
    assert len(importer.app.chad_chat_history) == 1
    assert "Resolver meldet SERVFAIL" in importer.app.chad_chat_history[0]["content"]
    assert importer.warnings == []


def test_symlink_to_private_file_is_not_imported(importer, tmp_path):
    private = tmp_path / "id_private"
    private.write_text("PRIVATE CONTENT")
    link = tmp_path / "notes.txt"
    link.symlink_to(private)
    importer.run(link)
    assert importer.app.chad_chat_history == []
    assert importer.output == []
    assert "Symbolic links are not imported" in importer.warnings[0]


def test_symlink_to_endless_device_returns_without_reading(importer, tmp_path):
    link = tmp_path / "readme.txt"
    link.symlink_to("/dev/zero")
    importer.run(link)
    assert importer.app.chad_chat_history == []
    assert importer.warnings


def test_fifo_is_rejected_without_blocking(importer, tmp_path):
    fifo = tmp_path / "pipe.log"
    os.mkfifo(fifo)
    importer.run(fifo)
    assert importer.app.chad_chat_history == []
    assert "keine reguläre Datei" in importer.warnings[0]


def test_oversized_file_is_rejected_before_import(importer, tmp_path):
    path = tmp_path / "huge.log"
    with path.open("wb") as handle:
        handle.truncate(images.MAX_IMAGE_BYTES + 1)
    importer.run(path)
    assert importer.app.chad_chat_history == []
    assert "größer als" in importer.warnings[0]


def test_imported_bytes_come_from_the_single_bounded_read(
    importer, tmp_path, monkeypatch
):
    path = tmp_path / "notes.txt"
    path.write_text("captured")
    real_read = chad.read_bounded_bytes
    reads = []

    def read_once(target, max_bytes, **kwargs):
        reads.append((target, max_bytes))
        payload = real_read(target, max_bytes, **kwargs)
        path.write_text("replaced after the read")
        return payload

    monkeypatch.setattr(chad, "read_bounded_bytes", read_once)
    importer.run(path)
    assert reads == [(str(path), images.MAX_IMAGE_BYTES)]
    content = importer.app.chad_chat_history[0]["content"]
    assert "captured" in content and "replaced" not in content
