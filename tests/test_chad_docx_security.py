"""Bounded DOCX imports; synthetic documents only, no host or online operations."""

import io
import stat
import struct
from types import SimpleNamespace
import warnings
import zipfile

import docx
import pytest

from netmon.core import docx_archive as limits
from netmon.features import chad_controller as chad


@pytest.fixture
def app():
    return SimpleNamespace(tr=lambda key, fallback: fallback)


def pack(tmp_path, entries, *, compression=zipfile.ZIP_STORED):
    path = tmp_path / "fixture.docx"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w", compression=compression) as archive:
            for name, data in entries:
                archive.writestr(name, data)
    return path


def rejects_before_reader(monkeypatch, app, path):
    def forbidden(*args, **kwargs):
        pytest.fail("Unvalidated DOCX reached python-docx")

    monkeypatch.setattr(chad, "parse_docx_snapshot", forbidden)
    result = chad.extract_docx_text_for_chad(app, str(path))
    assert result.startswith("Error while reading DOCX:")


@pytest.mark.parametrize("compression", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
def test_real_document_preserves_paragraphs_tables_and_unicode(
    tmp_path, app, compression
):
    document = docx.Document()
    document.add_paragraph("Synthetischer Text: Grüße")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Links"
    table.cell(0, 1).text = "Rechts"
    original = io.BytesIO()
    document.save(original)
    with zipfile.ZipFile(original) as archive:
        entries = [(item.filename, archive.read(item)) for item in archive.infolist()]
    path = pack(tmp_path, entries, compression=compression)
    assert chad.extract_docx_text_for_chad(app, str(path)) == (
        "Synthetischer Text: Grüße\nLinks | Rechts"
    )


def test_reader_receives_checked_snapshot_even_after_source_replacement(
    tmp_path, app, monkeypatch
):
    path = tmp_path / "fixture.docx"
    document = docx.Document()
    document.add_paragraph("Checked snapshot")
    document.save(path)
    original = chad.parse_docx_snapshot
    streams = []

    def read_snapshot(payload):
        assert isinstance(payload, bytes)
        path.write_bytes(b"attacker replacement")
        streams.append(payload)
        return original(payload)

    monkeypatch.setattr(chad, "parse_docx_snapshot", read_snapshot)
    assert chad.extract_docx_text_for_chad(app, str(path)) == "Checked snapshot"
    assert len(streams) == 1


@pytest.mark.parametrize(
    "name",
    [
        "/absolute.xml",
        "../outside.xml",
        "word/../outside.xml",
        "word//document.xml",
        "word//",
        "./word/document.xml",
        "word\\document.xml",
        "C:/word/document.xml",
        "word/bad\n.xml",
        "word/\u200b.xml",
        "/".join(["deep"] * 17),
        "a" * 513,
    ],
)
def test_unsafe_names_never_reach_reader(tmp_path, monkeypatch, app, name):
    path = pack(tmp_path, [(name, b"")])
    rejects_before_reader(monkeypatch, app, path)


@pytest.mark.parametrize("names", [("same.xml", "same.xml"), ("word", "word/")])
def test_duplicate_files_or_directory_aliases_are_rejected(
    tmp_path, monkeypatch, app, names
):
    path = pack(tmp_path, [(name, b"") for name in names])
    rejects_before_reader(monkeypatch, app, path)


@pytest.mark.parametrize(
    "kind", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFDIR]
)
def test_special_or_inconsistent_types_are_rejected(tmp_path, monkeypatch, app, kind):
    entry = zipfile.ZipInfo("word/document.xml")
    entry.create_system = 3
    entry.external_attr = (kind | 0o600) << 16
    path = pack(tmp_path, [(entry, b"payload")])
    rejects_before_reader(monkeypatch, app, path)


@pytest.mark.parametrize("compression", [zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA])
def test_unsupported_compression_rejected(tmp_path, monkeypatch, app, compression):
    path = pack(tmp_path, [("word/document.xml", b"text")], compression=compression)
    rejects_before_reader(monkeypatch, app, path)


def mutate(path, signature, offset, fmt, value):
    payload = bytearray(path.read_bytes())
    position = payload.index(signature)
    struct.pack_into(fmt, payload, position + offset, value)
    path.write_bytes(payload)


@pytest.mark.parametrize("flag", [0x01, 0x20, 0x40, 0x2000])
def test_encrypted_or_patched_member_rejected(tmp_path, monkeypatch, app, flag):
    path = pack(tmp_path, [("word/document.xml", b"text")])
    mutate(path, b"PK\x03\x04", 6, "<H", flag)
    mutate(path, b"PK\x01\x02", 8, "<H", flag)
    rejects_before_reader(monkeypatch, app, path)


def test_nul_in_original_zip_name_is_not_silently_truncated(tmp_path, monkeypatch, app):
    path = pack(tmp_path, [("word/document.xml", b"text")])
    path.write_bytes(
        path.read_bytes().replace(b"word/document.xml", b"word/\0ocument.xml")
    )
    rejects_before_reader(monkeypatch, app, path)


@pytest.mark.parametrize("method", ["stored", "deflated"])
def test_zip_bomb_ratio_rejected(tmp_path, monkeypatch, app, method):
    compression = zipfile.ZIP_DEFLATED if method == "deflated" else zipfile.ZIP_STORED
    path = pack(
        tmp_path, [("word/document.xml", b"x" * 65536)], compression=compression
    )
    if method == "stored":
        # Even a claimed compression ratio in stored metadata cannot authorize it.
        mutate(path, b"PK\x01\x02", 20, "<I", 1)
    rejects_before_reader(monkeypatch, app, path)


@pytest.mark.parametrize("budget", ["member", "total"])
@pytest.mark.parametrize("ignored", [False, True])
def test_all_parts_count_towards_declared_limits(
    tmp_path, monkeypatch, app, budget, ignored
):
    name = "ignored.bin" if ignored else "word/document.xml"
    path = pack(tmp_path, [(name, b"x" * 20), ("other.bin", b"y" * 20)])
    monkeypatch.setattr(limits, "MAX_MEMBER_BYTES", 19 if budget == "member" else 20)
    monkeypatch.setattr(limits, "MAX_TOTAL_BYTES", 39 if budget == "total" else 40)
    rejects_before_reader(monkeypatch, app, path)


def test_exact_member_total_and_count_limits_accept(tmp_path, monkeypatch):
    path = pack(tmp_path, [("one.bin", b"x" * 20), ("two.bin", b"y" * 20)])
    monkeypatch.setattr(limits, "MAX_MEMBER_BYTES", 20)
    monkeypatch.setattr(limits, "MAX_TOTAL_BYTES", 40)
    monkeypatch.setattr(limits, "MAX_MEMBERS", 2)
    with limits.open_validated_docx(path) as stream:
        assert stream.read() == path.read_bytes()


@pytest.mark.parametrize("forged", [False, True])
def test_excessive_or_forged_count_rejected_before_zipfile(
    tmp_path, monkeypatch, app, forged
):
    path = pack(tmp_path, [(f"part-{index}.xml", b"") for index in range(3)])
    monkeypatch.setattr(limits, "MAX_MEMBERS", 2)
    if forged:
        mutate(path, b"PK\x05\x06", 8, "<H", 1)
        mutate(path, b"PK\x05\x06", 10, "<H", 1)
    monkeypatch.setattr(
        limits.zipfile, "ZipFile", lambda *a, **kw: pytest.fail("premature ZIP parser")
    )
    rejects_before_reader(monkeypatch, app, path)


@pytest.mark.parametrize(
    "kind", ["empty", "not-zip", "zip64", "multidisk", "truncated"]
)
def test_bad_envelope_rejected_before_reader(tmp_path, monkeypatch, app, kind):
    path = pack(tmp_path, [] if kind == "empty" else [("word/document.xml", b"x")])
    if kind == "not-zip":
        path.write_bytes(b"not a docx")
    elif kind == "zip64":
        mutate(path, b"PK\x05\x06", 16, "<I", 0xFFFFFFFF)
    elif kind == "multidisk":
        mutate(path, b"PK\x05\x06", 4, "<H", 1)
    elif kind == "truncated":
        path.write_bytes(path.read_bytes()[:-10])
    rejects_before_reader(monkeypatch, app, path)


def test_corrupt_crc_in_ignored_part_is_checked(tmp_path, monkeypatch, app):
    path = pack(tmp_path, [("ignored.bin", b"original payload")])
    path.write_bytes(
        path.read_bytes().replace(b"original payload", b"modified payload")
    )
    rejects_before_reader(monkeypatch, app, path)


def test_actual_stream_overrun_rejected_independently_of_metadata(
    tmp_path, monkeypatch, app
):
    path = pack(tmp_path, [("ignored.bin", b"1234")])
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *a, **kw: io.BytesIO(b"12345"))
    rejects_before_reader(monkeypatch, app, path)


def test_actual_short_stream_rejected(tmp_path, monkeypatch, app):
    path = pack(tmp_path, [("ignored.bin", b"1234")])
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *a, **kw: io.BytesIO(b"123"))
    rejects_before_reader(monkeypatch, app, path)


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory", "oversize"])
def test_unsafe_or_excessive_input_rejected_without_parsing(
    tmp_path, monkeypatch, app, kind
):
    path = tmp_path / "fixture.docx"
    if kind == "symlink":
        source = tmp_path / "other.docx"
        source.write_bytes(b"not read")
        path.symlink_to(source)
    elif kind == "fifo":
        limits.os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    else:
        with path.open("wb") as stream:
            stream.truncate(limits.MAX_ARCHIVE_BYTES + 1)
    rejects_before_reader(monkeypatch, app, path)


def test_compressed_limit_also_bounds_read_when_stat_is_stale(
    tmp_path, monkeypatch, app
):
    path = tmp_path / "fixture.docx"
    path.write_bytes(b"x" * 101)
    monkeypatch.setattr(limits, "MAX_ARCHIVE_BYTES", 100)
    original = limits.os.fstat

    def stale(fd):
        info = original(fd)
        return SimpleNamespace(
            st_mode=info.st_mode, st_size=0, st_mtime_ns=0, st_ctime_ns=0
        )

    monkeypatch.setattr(limits.os, "fstat", stale)
    rejects_before_reader(monkeypatch, app, path)


def test_docx_dependency_missing_keeps_existing_message(tmp_path, monkeypatch, app):
    monkeypatch.setattr(chad, "docx", None)
    assert chad.extract_docx_text_for_chad(
        app, str(tmp_path / "missing.docx")
    ).startswith("DOCX support missing:")


@pytest.mark.parametrize("valid", [False, True])
def test_actual_import_adds_only_valid_documents_to_chat_context(
    tmp_path, monkeypatch, app, valid
):
    path = tmp_path / "fixture.docx"
    if valid:
        document = docx.Document()
        document.add_paragraph("Synthetic chat context")
        document.save(path)
    else:
        path = pack(
            tmp_path,
            [("word/document.xml", b"x" * 65536)],
            compression=zipfile.ZIP_DEFLATED,
        )
    notices, statuses = [], []

    class Immediate:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(chad, "threading", SimpleNamespace(Thread=Immediate))
    app.chad_chat_history = []
    app.chad_chat_status_var = SimpleNamespace(set=statuses.append)
    monkeypatch.setattr(chad, "ensure_chad_enabled", lambda app: True)
    monkeypatch.setattr(chad.filedialog, "askopenfilename", lambda **kwargs: str(path))
    monkeypatch.setattr(chad.messagebox, "askyesno", lambda *a, **kw: True)
    monkeypatch.setattr(
        chad, "append_to_chad_output", lambda app, title, text: notices.append(text)
    )
    chad.import_file_to_chad_chat(app)
    if valid:
        assert len(app.chad_chat_history) == 1
        assert "Synthetic chat context" in app.chad_chat_history[0]["content"]
        assert statuses[-1].startswith("File imported:")
    else:
        assert app.chad_chat_history == []
        assert statuses[-1].startswith("Error while reading DOCX:")
        assert notices == [statuses[-1]]
