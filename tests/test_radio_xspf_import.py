"""Local radio station files: bounded parsing, non-destructive persistence and UI."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import tkinter as tk
from tkinter import ttk
from xml.sax.saxutils import escape

import pytest

from netmon.core import radio_station_import as source
from netmon.features import radio_controller as radio
from netmon.features import radio_station_import_controller as controller
from netmon import netmon_radio_app as ui


def playlist(tracks, title="Playlist"):
    return (
        f'<playlist xmlns="http://xspf.org/ns/0/" version="1"><title>{escape(title)}</title><trackList>{tracks}</trackList></playlist>'
    ).encode()


def track(
    url="http://streams.example.com:9012", title="Mystery FM ✦ IBIZA Dance Radio"
):
    return f"<track><location>{escape(url)}</location><title>{escape(title)}</title></track>"


def test_sample_shape_becomes_named_custom_station_without_network():
    rows, counts = source.parse_xspf(playlist(track()))
    assert rows == [
        {
            "name": "Mystery FM ✦ IBIZA Dance Radio",
            "url": "http://streams.example.com:9012",
            "category": "XSPF-Import",
            "custom": True,
        }
    ]
    assert counts == {"tracks": 1, "skipped": 0, "duplicates": 0}


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "../local.mp3",
        "--script=/tmp/payload.lua",
        "javascript:alert(1)",
        "rtsp://example.com/live",
        "https://u:p@example.com/live",
        "https://example.com:0/live",
        "https://example.com:65536/live",
        "https://example.com/live#fragment",
        "https://example.com/a b",
        "https://example.com/list.%78spf",
        "https://example.com/live.m3u8",
        "https://example.com/list.pls",
        "https://evil.example\\@example.com/live",
    ],
)
def test_unsupported_streams_are_counted_and_never_forwarded(url):
    rows, counts = source.parse_xspf(
        playlist(track(url) + track("https://example.com/live"))
    )
    assert len(rows) == 1 and rows[0]["url"] == "https://example.com/live"
    assert counts["skipped"] == 1


def test_alternate_locations_choose_one_supported_stream_and_ignore_extensions():
    rows, _ = source.parse_xspf(
        playlist(
            '<track><location>file:///etc/passwd</location><location>https://example.com/live?a=1&amp;b=2</location><location>https://example.com/backup</location><extension application="http://example.com"><command>--script=payload.lua</command></extension></track>'
        )
    )
    assert rows[0]["url"] == "https://example.com/live?a=1&b=2"
    assert rows[0]["name"] == "Playlist"


def test_equivalent_urls_deduplicate_but_distinct_streams_and_queries_remain():
    rows, summary = source.parse_xspf(
        playlist(
            track("https://EXAMPLE.com:443/a")
            + track("https://example.com/a")
            + track("https://example.com/a?q=1")
            + track("https://example.com/b")
        )
    )
    assert len(rows) == 3 and summary["duplicates"] == 1
    merged, added, duplicates = source.merge_imported_stations(
        [
            {
                "id": "old",
                "url": "https://example.com/redirect",
                "url_resolved": "https://example.com/a",
            }
        ],
        rows,
    )
    assert added == 2 and duplicates == 1 and merged[0]["id"] == "old"
    assert len({row["id"] for row in merged}) == 3


def test_valid_prefixed_namespace_utf16_and_late_playlist_title():
    xml = '<?xml version="1.0" encoding="UTF-16"?><x:playlist xmlns:x="http://xspf.org/ns/0/" version="1"><x:trackList><x:track><x:location>https://example.com/live</x:location></x:track></x:trackList><x:title>Ä Radio</x:title></x:playlist>'
    rows, _ = source.parse_xspf(xml.encode("utf-16"))
    assert rows[0]["name"] == "Ä Radio"


@pytest.mark.parametrize(
    "payload",
    [
        b"<playlist/>",
        b'<playlist xmlns="http://xspf.org/ns/0/" version="0"/>',
        b"<other/>",
        b"<not-xml",
        playlist(""),
        playlist("<track/>"),
        playlist(track("file:///etc/passwd")),
    ],
)
def test_invalid_or_empty_document_rejects_whole_import(payload):
    with pytest.raises(ValueError):
        source.parse_xspf(payload)


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
def test_doctype_entities_external_fetch_and_expansion_are_rejected(encoding):
    xml = (
        '<?xml version="1.0" encoding="'
        + encoding
        + '"?><!DOCTYPE playlist [<!ENTITY injected SYSTEM "file:///etc/passwd">]><playlist xmlns="http://xspf.org/ns/0/" version="1"><title>&injected;</title><trackList>'
        + track()
        + "</trackList></playlist>"
    )
    with pytest.raises(ValueError, match="DTD"):
        source.parse_xspf(xml.encode(encoding))


@pytest.mark.parametrize(
    "limit,value,payload",
    [
        ("MAX_BYTES", 8, playlist(track())),
        ("MAX_TRACKS", 1, playlist(track() + track("https://example.com/second"))),
        ("MAX_NODES", 3, playlist(track())),
        ("MAX_DEPTH", 3, playlist(track())),
        ("MAX_FIELD_CHARS", 4, playlist(track())),
    ],
)
def test_resource_limits_fail_without_partial_result(
    monkeypatch, limit, value, payload
):
    monkeypatch.setattr(source, limit, value)
    with pytest.raises(ValueError):
        source.parse_xspf(payload)


def test_input_rejects_symlink_fifo_and_wrong_extension(tmp_path):
    import os

    path = tmp_path / "source.xspf"
    path.write_bytes(playlist(track()))
    link = tmp_path / "link.xspf"
    link.symlink_to(path)
    pipe = tmp_path / "pipe.xspf"
    os.mkfifo(pipe)
    for candidate in [link, pipe, tmp_path / "audio.mp3"]:
        with pytest.raises(ValueError):
            source.read_xspf(candidate)
    assert source.read_xspf(path)[0] == path.read_bytes()


def test_archive_keeps_exact_source_and_reuses_copy_without_overwrite(tmp_path):
    path = tmp_path / "source.xspf"
    payload = playlist(track())
    path.write_bytes(payload)
    folder = tmp_path / "Radio" / "Senderimporte"
    archive = source.archive_xspf(payload, path, folder)
    assert archive.read_bytes() == path.read_bytes() == payload
    assert archive.stat().st_mode & 0o777 == 0o600
    assert folder.stat().st_mode & 0o777 == 0o700
    assert source.archive_xspf(payload, path, folder) == archive
    archive.write_bytes(b"foreign data")
    with pytest.raises(ValueError):
        source.archive_xspf(payload, path, folder)
    assert archive.read_bytes() == b"foreign data"


def test_archive_refuses_directory_and_file_symlinks(tmp_path):
    payload = playlist(track())
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        source.archive_xspf(payload, "source.xspf", link)
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    name = f"source-{hashlib.sha256(payload).hexdigest()[:16]}.xspf"
    victim = tmp_path / "victim"
    victim.write_bytes(payload)
    (folder / name).symlink_to(victim)
    with pytest.raises(ValueError):
        source.archive_xspf(payload, "source.xspf", folder)
    assert victim.read_bytes() == payload


@pytest.fixture
def importer(tmp_path, monkeypatch):
    path = tmp_path / "source.xspf"
    path.write_bytes(playlist(track()))
    folder = tmp_path / "Radio" / "Senderimporte"
    app = SimpleNamespace(
        radio_db=[],
        radio_db_path=str(tmp_path / "db.json"),
        tr=lambda _key, fallback: fallback,
        radio_search_var=Mock(),
        radio_show_favorites_var=Mock(),
    )
    monkeypatch.setattr(controller, "station_import_folder", lambda: folder)
    monkeypatch.setattr(controller.messagebox, "askyesno", Mock(return_value=True))
    monkeypatch.setattr(radio, "refresh_radio_station_table", Mock())
    monkeypatch.setattr(radio, "set_radio_status", Mock())
    monkeypatch.setattr(
        radio,
        "play_radio_station",
        Mock(side_effect=AssertionError("playback forbidden")),
    )
    monkeypatch.setattr(
        controller.subprocess,
        "Popen",
        Mock(side_effect=AssertionError("process forbidden")),
    )
    return app, path, folder


def test_import_persists_and_restart_reads_one_station_even_after_repeat(importer):
    app, path, folder = importer
    assert controller.import_station_file_path(app, path)
    station = app.radio_db[0]
    assert station["custom"] and station["id"].startswith("xspf-")
    app.radio_search_var.set.assert_called_with(station["name"])
    assert radio.load_radio_db(app) == app.radio_db
    assert controller.import_station_file_path(app, path)
    assert len(app.radio_db) == 1 and len(list(folder.iterdir())) == 1
    assert path.exists()
    radio.play_radio_station.assert_not_called()
    controller.subprocess.Popen.assert_not_called()


def test_cancel_preserves_database_and_original_and_writes_no_archive(importer):
    app, path, folder = importer
    controller.messagebox.askyesno.return_value = False
    assert not controller.import_station_file_path(app, path)
    assert (
        not folder.exists() and not Path(app.radio_db_path).exists() and path.exists()
    )
    assert app.radio_db == []


def test_failed_database_write_is_honest_and_keeps_source_and_archive(
    importer, monkeypatch
):
    app, path, folder = importer
    monkeypatch.setattr(radio, "save_radio_db", lambda *a, **k: False)
    assert not controller.import_station_file_path(app, path)
    assert app.radio_db == [] and path.exists() and list(folder.glob("*.xspf"))
    assert "fehlgeschlagen" in radio.set_radio_status.call_args.args[1]
    assert "Dateikopie bleibt" in radio.set_radio_status.call_args.args[1]


def test_database_change_during_preview_blocks_stale_write(importer):
    app, path, folder = importer

    def confirm(*args, **kwargs):
        app.radio_db = [{"id": "parallel", "url": "https://example.com/new"}]
        return True

    controller.messagebox.askyesno.side_effect = confirm
    assert not controller.import_station_file_path(app, path)
    assert app.radio_db[0]["id"] == "parallel" and not folder.exists()


def test_running_catalog_import_blocks_station_file_before_read(importer):
    app, path, folder = importer
    app.radio_database_refresh_running = True
    assert not controller.import_station_file_path(app, path)
    controller.messagebox.askyesno.assert_not_called()
    assert not folder.exists()


def test_real_action_buttons_call_only_the_chosen_callback(monkeypatch):
    root = tk.Tk()
    root.geometry("650x160")
    app = SimpleNamespace(tr=lambda _key, fallback: fallback)
    choose = Mock()
    open_folder = Mock()
    monkeypatch.setattr(controller, "import_station_file_dialog", choose)
    monkeypatch.setattr(controller, "open_station_import_folder", open_folder)
    try:
        frame = ttk.Frame(root)
        frame.pack(fill="both", expand=True)
        ui._build_station_import_actions(app, frame)
        root.update()
        app.radio_xspf_import_button.invoke()
        choose.assert_called_once_with(app)
        open_folder.assert_not_called()
        app.radio_xspf_folder_button.invoke()
        open_folder.assert_called_once_with(app)
        for button in [app.radio_xspf_import_button, app.radio_xspf_folder_button]:
            assert button.winfo_ismapped()
            assert (
                button.winfo_rootx() + button.winfo_width()
                <= root.winfo_rootx() + root.winfo_width()
            )
    finally:
        root.destroy()


def test_catalog_update_preserves_imported_custom_station(tmp_path, monkeypatch):
    station = {
        "id": "imported",
        "name": "Import",
        "url": "https://example.com/import",
        "custom": True,
    }
    app = SimpleNamespace(
        radio_db=[station],
        radio_db_path=str(tmp_path / "db.json"),
        radio_db_meta_path=str(tmp_path / "meta.json"),
        log=Mock(),
    )
    monkeypatch.setattr(
        radio,
        "_radio_database_source_ids_for_download",
        lambda _app: ["radio_browser_api"],
    )
    monkeypatch.setattr(
        radio,
        "_download_radio_source_payload",
        lambda *a, **k: [
            {
                "id": "remote",
                "name": "New catalog",
                "url": "https://example.com/remote",
            },
            {"id": "alias", "name": "Same stream", "url": "https://example.com/remote"},
        ],
    )
    monkeypatch.setattr(radio, "_schedule_ui", lambda _app, callback: callback())
    monkeypatch.setattr(radio, "refresh_radio_ui", lambda _app: None)
    summary = Mock()
    monkeypatch.setattr(radio, "_show_radio_database_import_summary", summary)
    thread = radio.download_radio_db(app)
    thread.join(timeout=3)
    assert not thread.is_alive()
    saved = json.loads(Path(app.radio_db_path).read_text())
    assert {row["id"] for row in saved} == {"imported", "remote"}
    assert summary.call_args.args[1]["duplicates_removed"] == 1
    assert summary.call_args.args[1]["merged_total"] == 2
