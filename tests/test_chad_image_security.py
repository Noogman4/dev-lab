"""Synthetic image imports/uploads only; API transport is always a fake."""

import base64
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
import io
import os
from pathlib import Path
import stat
from types import SimpleNamespace

from PIL import Image
import pytest

from netmon.core import image_snapshot as images
from netmon.features import chad_controller as chad
from netmon.services import ai_online_service as online


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def importer(home, monkeypatch, chad_image_snapshot):
    path = home / "chosen.png"
    path.write_bytes(chad_image_snapshot.data)
    output, statuses = [], []
    app = SimpleNamespace(
        tr=lambda _key, default: default,
        chad_pending_files=[],
        chad_chat_history=[],
        chad_chat_status_var=SimpleNamespace(set=statuses.append),
    )
    monkeypatch.setattr(chad, "ensure_chad_enabled", lambda _app: True)
    monkeypatch.setattr(chad.filedialog, "askopenfilename", lambda **_kw: str(path))
    monkeypatch.setattr(chad.messagebox, "askyesno", lambda *_a, **_kw: True)
    monkeypatch.setattr(
        chad, "append_to_chad_output", lambda _app, _title, text: output.append(text)
    )
    return SimpleNamespace(path=path, app=app, output=output, statuses=statuses)


def invoke(service, method, files):
    value = (
        "describe" if method == "analyze" else [{"role": "user", "content": "describe"}]
    )
    return getattr(service, method)(value, files=files)


@pytest.mark.parametrize("method", ["analyze", "chat"])
@pytest.mark.parametrize(
    "replacement", ["symlink", "overwrite", "grow", "delete", "parent"]
)
def test_imported_bytes_survive_path_changes_without_reopening(
    importer, home, monkeypatch, method, replacement
):
    selected = importer.path
    if replacement == "parent":
        directory = home / "shared"
        directory.mkdir()
        selected = directory / selected.name
        importer.path.rename(selected)
        monkeypatch.setattr(
            chad.filedialog, "askopenfilename", lambda **_kw: str(selected)
        )
    expected = selected.read_bytes()
    chad.import_file_to_chad_chat(importer.app)
    assert len(importer.app.chad_pending_files) == 1
    attachment = importer.app.chad_pending_files[0]
    assert attachment["size"] == len(expected)
    assert str(selected) in importer.output[-1]
    assert "captured image copy" in importer.output[-1]
    with pytest.raises(FrozenInstanceError):
        attachment["snapshot"].data = b"changed"

    private = home / "private.png"
    stream = io.BytesIO()
    Image.new("RGB", (2, 2), "blue").save(stream, format="PNG")
    private.write_bytes(stream.getvalue())
    if replacement == "parent":
        selected.parent.rename(home / "retired")
        selected.parent.symlink_to(home / "private-dir", target_is_directory=True)
    else:
        selected.unlink()
        if replacement == "symlink":
            selected.symlink_to(private)
        elif replacement == "overwrite":
            selected.write_bytes(private.read_bytes())
        elif replacement == "grow":
            with selected.open("wb") as handle:
                handle.truncate(images.MAX_IMAGE_BYTES + 1)
    # Even altered path metadata cannot change the uploaded captured object.
    attachment["path"] = str(private)
    service = online.AiOnlineService()
    service.api_key = "synthetic-key"
    payloads = []
    monkeypatch.setattr(
        service,
        "_post_json",
        lambda _url, _headers, payload, **_kw: (
            payloads.append(payload) or 200,
            '{"output_text":"ok"}',
        ),
    )

    def no_reopen(_path):
        pytest.fail("queued image pathname was reopened during upload")

    monkeypatch.setattr(online, "snapshot_image", no_reopen)
    assert invoke(service, method, importer.app.chad_pending_files) == (True, "ok")
    data_url = payloads[0]["input"][-1]["content"][-1]["image_url"]
    assert base64.b64decode(data_url.split(",", 1)[1]) == expected
    assert base64.b64decode(data_url.split(",", 1)[1]) != private.read_bytes()


@pytest.mark.parametrize(
    "kind",
    ["symlink", "parent_link", "fifo", "directory", "empty", "not_image", "oversized"],
)
def test_import_rejects_unsafe_objects_without_queueing(importer, home, kind):
    original = importer.path.read_bytes()
    importer.path.unlink()
    if kind == "symlink":
        target = home / "target.png"
        target.write_bytes(original)
        importer.path.symlink_to(target)
    elif kind == "parent_link":
        target = home / "target"
        target.mkdir()
        (target / "inner.png").write_bytes(original)
        importer.path.symlink_to(target)
        # Exercise a linked ancestor directly as well as the GUI leaf.
        with pytest.raises(OSError):
            images.snapshot_image(str(importer.path / "inner.png"))
    elif kind == "fifo":
        os.mkfifo(importer.path)
    elif kind == "directory":
        importer.path.mkdir()
    elif kind == "oversized":
        with importer.path.open("wb") as handle:
            handle.truncate(images.MAX_IMAGE_BYTES + 1)
    else:
        importer.path.write_bytes(b"" if kind == "empty" else b"not an image")
    chad.import_file_to_chad_chat(importer.app)
    assert importer.app.chad_pending_files == []
    assert importer.statuses[-1].startswith("Error during file import:")


def test_cancelled_import_keeps_queue_empty(importer, monkeypatch):
    monkeypatch.setattr(chad.messagebox, "askyesno", lambda *_a, **_kw: False)
    chad.import_file_to_chad_chat(importer.app)
    assert importer.app.chad_pending_files == []


def test_image_queue_has_an_explicit_limit(importer):
    for _ in range(images.MAX_IMAGE_ATTACHMENTS):
        chad.import_file_to_chad_chat(importer.app)
    assert len(importer.app.chad_pending_files) == images.MAX_IMAGE_ATTACHMENTS
    chad.import_file_to_chad_chat(importer.app)
    assert len(importer.app.chad_pending_files) == images.MAX_IMAGE_ATTACHMENTS
    assert "limit exceeded" in importer.statuses[-1]


@pytest.mark.parametrize("method", ["analyze", "chat"])
@pytest.mark.parametrize(
    "case", ["legacy_path", "fake_snapshot", "too_many", "total_bytes"]
)
def test_invalid_attachments_fail_before_encoding_or_transport(
    home, monkeypatch, chad_image_snapshot, method, case
):
    attachment = {"type": "image", "snapshot": chad_image_snapshot}
    files = [attachment]
    if case == "legacy_path":
        files = [{"type": "image", "path": str(home / "private.png")}]
    elif case == "fake_snapshot":
        files = [{"type": "image", "snapshot": {"data": b"fake"}}]
    elif case == "too_many":
        files = [attachment] * (images.MAX_IMAGE_ATTACHMENTS + 1)
    else:
        monkeypatch.setattr(
            images, "MAX_TOTAL_IMAGE_BYTES", len(chad_image_snapshot.data) - 1
        )
    service = online.AiOnlineService()
    service.api_key = "synthetic-key"
    monkeypatch.setattr(
        service,
        "image_to_data_url",
        lambda _image: pytest.fail("invalid attachments reached encoding"),
    )
    monkeypatch.setattr(
        service,
        "_post_json",
        lambda *_a, **_kw: pytest.fail("invalid attachments reached the API"),
    )
    success, _error = invoke(service, method, files)
    assert success is False


def test_replaced_parent_stays_bound_to_open_directory(
    home, monkeypatch, chad_image_snapshot
):
    directory = home / "shared"
    directory.mkdir()
    (directory / "image.png").write_bytes(chad_image_snapshot.data)
    outside = home / "other"
    outside.mkdir()
    (outside / "image.png").write_bytes(b"not the selected image")
    original_open = images._open_directory

    def replace_after_open(parent, name):
        descriptor = original_open(parent, name)
        if name == "shared":
            directory.rename(home / "old")
            directory.symlink_to(outside, target_is_directory=True)
        return descriptor

    monkeypatch.setattr(images, "_open_directory", replace_after_open)
    assert (
        images.snapshot_image(str(directory / "image.png")).data
        == chad_image_snapshot.data
    )


def test_change_during_read_is_rejected(home, monkeypatch, chad_image_snapshot):
    path = home / "image.png"
    path.write_bytes(chad_image_snapshot.data)
    original_stat = images.os.fstat
    calls = []

    def changed(descriptor):
        entry = original_stat(descriptor)
        calls.append(True)
        return SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600,
            st_size=entry.st_size,
            st_mtime_ns=entry.st_mtime_ns,
            st_ctime_ns=entry.st_ctime_ns + int(len(calls) > 1),
        )

    monkeypatch.setattr(images.os, "fstat", changed)
    with pytest.raises(ValueError, match="changed while reading"):
        images.snapshot_image(str(path))


def test_growing_file_cannot_force_an_unbounded_read(
    home, monkeypatch, chad_image_snapshot
):
    path = home / "image.png"
    path.write_bytes(chad_image_snapshot.data)
    cap = 256
    monkeypatch.setattr(images, "MAX_IMAGE_BYTES", cap)
    original_fdopen = images.os.fdopen
    requested = []

    @contextmanager
    def growing_fdopen(descriptor, mode):
        with original_fdopen(descriptor, mode) as source:

            def read(size):
                requested.append(size)
                with path.open("ab") as writer:
                    writer.write(b"x" * 1024)
                return source.read(size)

            yield SimpleNamespace(fileno=source.fileno, read=read)

    monkeypatch.setattr(images.os, "fdopen", growing_fdopen)
    with pytest.raises(ValueError, match="exceeded its limit"):
        images.snapshot_image(str(path))
    assert requested == [cap + 1]


def test_image_dimensions_are_bounded(home, monkeypatch):
    stream = io.BytesIO()
    Image.new("RGB", (8, 8)).save(stream, format="PNG")
    monkeypatch.setattr(images, "MAX_IMAGE_PIXELS", 32)
    with pytest.raises(ValueError, match="dimensions"):
        images.ImageSnapshot(str(home / "large.png"), stream.getvalue())


def test_mime_comes_from_content_and_snapshot_does_not_log_bytes(
    home, chad_image_snapshot
):
    path = home / "misnamed.jpg"
    path.write_bytes(chad_image_snapshot.data)
    snapshot = images.snapshot_image(str(path))
    assert snapshot.mime_type == "image/png"
    assert repr(snapshot.data) not in repr(snapshot)
