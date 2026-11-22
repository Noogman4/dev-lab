"""Exercise the real folder callback with legacy Radio permissions; no desktop launch."""

import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from netmon import netmon_radio_core as core
from netmon.features import radio_controller as radio
from netmon.features import radio_station_import_controller as controller


@pytest.fixture
def radio_documents(tmp_path, monkeypatch):
    documents = tmp_path / "NetMon"
    documents.mkdir(mode=0o750)
    documents.chmod(0o750)
    monkeypatch.setattr(core, "get_netmon_documents_dir", lambda: str(documents))
    monkeypatch.setattr(controller.subprocess, "Popen", Mock())
    monkeypatch.setattr(radio, "set_radio_status", Mock())
    return documents


def test_real_folder_action_repairs_legacy_radio_mode_only(radio_documents):
    root = radio_documents / "Radio"
    root.mkdir(mode=0o770)
    root.chmod(0o770)
    sentinel = root / "radio_db.json"
    sentinel.write_bytes(b'["existing sender data"]')
    sentinel.chmod(0o640)
    before = sentinel.stat()
    app = SimpleNamespace()
    assert controller.open_station_import_folder(app)
    folder = root / "Senderimporte"
    assert root.stat().st_mode & 0o777 == 0o700
    assert folder.stat().st_mode & 0o777 == 0o700
    assert radio_documents.stat().st_mode & 0o777 == 0o750
    assert sentinel.read_bytes() == b'["existing sender data"]'
    assert sentinel.stat().st_mode == before.st_mode
    assert sentinel.stat().st_ino == before.st_ino
    controller.subprocess.Popen.assert_called_once()
    assert controller.subprocess.Popen.call_args.args[0] == [
        "/usr/bin/xdg-open",
        str(folder),
    ]
    radio.set_radio_status.assert_not_called()


def test_new_radio_directory_is_private_with_permissive_umask(radio_documents):
    previous = os.umask(0o002)
    try:
        assert controller.open_station_import_folder(SimpleNamespace())
    finally:
        os.umask(previous)
    assert (radio_documents / "Radio").stat().st_mode & 0o777 == 0o700
    assert (radio_documents / "Radio" / "Senderimporte").stat().st_mode & 0o777 == 0o700


def test_radio_directory_symlink_is_rejected_without_changing_target(
    radio_documents, tmp_path
):
    target = tmp_path / "foreign"
    target.mkdir()
    target.chmod(0o770)
    (radio_documents / "Radio").symlink_to(target, target_is_directory=True)
    assert not controller.open_station_import_folder(SimpleNamespace())
    assert target.stat().st_mode & 0o777 == 0o770 and list(target.iterdir()) == []
    controller.subprocess.Popen.assert_not_called()
    assert "konnte nicht geöffnet werden" in radio.set_radio_status.call_args.args[1]


def test_regular_file_at_radio_path_is_not_overwritten(radio_documents):
    path = radio_documents / "Radio"
    path.write_bytes(b"keep me")
    assert not controller.open_station_import_folder(SimpleNamespace())
    assert path.read_bytes() == b"keep me"
    controller.subprocess.Popen.assert_not_called()


def test_archive_import_works_with_existing_group_writable_radio_folder(
    radio_documents, tmp_path, monkeypatch
):
    root = radio_documents / "Radio"
    root.mkdir()
    root.chmod(0o770)
    selected = tmp_path / "station.pls"
    payload = b"[playlist]\nFile1=https://example.com/live\nTitle1=Test\nNumberOfEntries=1\nVersion=2\n"
    selected.write_bytes(payload)
    app = SimpleNamespace(
        radio_db=[],
        radio_db_path=str(root / "radio_db.json"),
        tr=lambda key, fallback: fallback,
    )
    monkeypatch.setattr(controller.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(radio, "refresh_radio_station_table", Mock())
    assert controller.import_station_file_path(app, selected)
    assert app.radio_db[0]["name"] == "Test"
    assert (
        list((root / "Senderimporte").glob("*.pls"))[0].read_bytes()
        == selected.read_bytes()
        == payload
    )
    assert radio.load_radio_db(app) == app.radio_db
    controller.subprocess.Popen.assert_not_called()
