"""Plain/extended M3U station files share preview, archive and duplicate handling."""

from unittest.mock import Mock

import pytest

from netmon.core import radio_station_import as source
from netmon.features import radio_station_import_controller as controller
from netmon.features import radio_controller as radio
from tests.test_radio_xspf_import import importer as importer


@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r"])
def test_plain_urls_work_without_header_or_metadata(separator):
    rows, counts = source.parse_m3u(
        separator.join(
            [
                "# exported radio list",
                "",
                "http://example.com:9012",
                "https://example.org/live",
            ]
        ).encode()
    )
    assert [row["name"] for row in rows] == ["example.com", "example.org"]
    assert all(row["category"] == "M3U-Import" and row["custom"] for row in rows)
    assert counts == {"tracks": 2, "duplicates": 0, "skipped": 0}


def test_extended_utf8_names_quotes_commas_and_directives_are_data():
    payload = '\ufeff#EXTM3U\n#EXTINF:-1 tvg-logo="https://example.com/a,b.png" group-title="Pop",Ä Radio, live\n#EXTVLCOPT:input-slave=file:///etc/passwd\nhttps://example.com/live?one=1&two=2\n#EXTINF:-1,Second\nhttps://example.org/live\n'.encode()
    rows, _ = source.parse_m3u(payload, utf8_only=True)
    assert rows[0] == {
        "name": "Ä Radio, live",
        "url": "https://example.com/live?one=1&two=2",
        "category": "M3U-Import",
        "custom": True,
    }
    assert len(rows) == 2 and rows[1]["name"] == "Second"
    assert "favicon" not in rows[0]


@pytest.mark.parametrize("suffix", [".m3u", ".m3u8", ".M3U", ".M3U8"])
def test_file_dispatch_and_archive_keep_format(tmp_path, suffix):
    path = tmp_path / ("radio" + suffix)
    payload = b"#EXTM3U\n#EXTINF:-1,Test\nhttps://example.com/live\n"
    path.write_bytes(payload)
    content, rows, _ = source.read_station_file(path)
    archived = source.archive_station_file(content, path, tmp_path / "Senderimporte")
    assert rows[0]["name"] == "Test"
    assert (
        archived.suffix == suffix.lower() and archived.read_bytes() == path.read_bytes()
    )


def test_legacy_m3u_uses_latin1_but_m3u8_requires_utf8(tmp_path):
    payload = "#EXTM3U\n#EXTINF:-1,Älterer Sender\nhttps://example.com/live\n".encode(
        "latin-1"
    )
    path = tmp_path / "radio.m3u"
    path.write_bytes(payload)
    assert source.read_station_file(path)[1][0]["name"] == "Älterer Sender"
    path8 = tmp_path / "radio.m3u8"
    path8.write_bytes(payload)
    with pytest.raises(ValueError, match="UTF-8"):
        source.read_station_file(path8)
    with pytest.raises(ValueError, match="UTF-8"):
        source.parse_m3u(b"\xef\xbb\xbf" + payload)


@pytest.mark.parametrize(
    "line",
    [
        "file:///etc/passwd",
        "/home/user/audio.mp3",
        "../audio.mp3",
        "C:\\Music\\song.mp3",
        "--script=payload.lua",
        "https://user:secret@example.com/live",
        "https://example.com/live.m3u8",
        "https://example.com/list.xspf",
        "https://example.com:65536/live",
    ],
)
def test_unsupported_entries_are_skipped_without_affecting_valid_station(line):
    rows, counts = source.parse_m3u(
        (line + "\n#EXTINF:-1,Good\nhttps://example.com/live\n").encode()
    )
    assert len(rows) == 1 and rows[0]["name"] == "Good"
    assert counts == {"tracks": 2, "skipped": 1, "duplicates": 0}


@pytest.mark.parametrize(
    "body",
    [
        "#EXTM3U\n#EXTINF:-1,Missing\n",
        "#EXTINF:-1,One\n#EXTINF:-1,Two\nhttps://example.com/live",
        "#EXTINF:broken,One\nhttps://example.com/live",
        "#EXTINF:-1\nhttps://example.com/live",
        '#EXTINF:-1 tvg-name="unclosed,One\nhttps://example.com/live',
        "#EXTM3U\n#EXTM3U\nhttps://example.com/live",
        "https://example.com/live\n#EXTM3U\n",
        "#EXTM3U\n",
        "",
        "\x00https://example.com/live",
    ],
)
def test_malformed_or_empty_list_is_rejected_as_a_whole(body):
    with pytest.raises(ValueError):
        source.parse_m3u(body.encode())


@pytest.mark.parametrize(
    "tag",
    [
        "#EXT-X-TARGETDURATION:8",
        "#EXT-X-STREAM-INF:BANDWIDTH=128000",
        '#EXT-X-KEY:METHOD=AES-128,URI="file:///secret"',
        "#EXT-X-ENDLIST",
    ],
)
def test_hls_is_rejected_even_after_a_valid_looking_stream(tag):
    with pytest.raises(ValueError, match="HLS"):
        source.parse_m3u(
            ("#EXTM3U\nhttps://example.com/segment.ts\n" + tag).encode(), utf8_only=True
        )


@pytest.mark.parametrize(
    "limit,value,body",
    [
        ("MAX_BYTES", 8, "https://example.com/live"),
        ("MAX_TRACKS", 1, "https://example.com/one\nhttps://example.com/two"),
        ("MAX_FIELD_CHARS", 16, "#" + ("x" * 17) + "\nhttps://example.com/live"),
    ],
)
def test_bounds_fail_without_partial_rows(monkeypatch, limit, value, body):
    monkeypatch.setattr(source, limit, value)
    with pytest.raises(ValueError):
        source.parse_m3u(body.encode())


def test_plain_and_extended_equivalent_origins_are_deduplicated():
    rows, counts = source.parse_m3u(
        b"#EXTM3U\n#EXTINF:-1,First\nhttps://EXAMPLE.com:443/live\nhttps://example.com/live\nhttps://example.com/live?q=1"
    )
    assert len(rows) == 2 and rows[0]["name"] == "First" and counts["duplicates"] == 1


def test_m3u_import_shares_xspf_preview_persistence_and_cross_format_dedup(importer):
    app, xspf, folder = importer
    assert controller.import_station_file_path(app, xspf)
    path = xspf.with_suffix(".m3u8")
    path.write_text(
        "#EXTM3U\n#EXTINF:-1,Same stream under another name\nhttp://STREAMS.example.com:9012/\n#EXTINF:-1,New station\nhttps://example.org/live\n"
    )
    assert controller.import_station_file_path(app, path)
    assert len(app.radio_db) == 2
    assert {p.suffix for p in folder.iterdir()} == {".xspf", ".m3u8"}
    assert radio.load_radio_db(app) == app.radio_db
    assert "1 doppelt" in radio.set_radio_status.call_args.args[1]
    radio.play_radio_station.assert_not_called()
    controller.subprocess.Popen.assert_not_called()


def test_hls_import_rejection_keeps_database_and_archive_unchanged(importer):
    app, xspf, folder = importer
    path = xspf.with_suffix(".m3u8")
    path.write_text(
        "#EXTM3U\n#EXT-X-TARGETDURATION:8\n#EXTINF:8,\nhttps://example.com/segment.ts"
    )
    assert not controller.import_station_file_path(app, path)
    assert app.radio_db == [] and not folder.exists()
    controller.messagebox.askyesno.assert_not_called()
    assert "HLS" in radio.set_radio_status.call_args.args[1]


def test_dialog_advertises_all_supported_suffixes_and_cancel_has_no_import(
    importer, monkeypatch
):
    app, _path, _folder = importer
    choose = Mock(return_value="")
    monkeypatch.setattr(controller.filedialog, "askopenfilename", choose)
    assert not controller.import_station_file_dialog(app)
    filters = repr(choose.call_args.kwargs["filetypes"])
    assert all(
        ext in filters
        for ext in ["*.xspf", "*.m3u", "*.m3u8", "*.M3U8", "*.pls", "*.PLS"]
    )
    controller.messagebox.askyesno.assert_not_called()
