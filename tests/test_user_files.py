"""Central personal paths and copy-only first-use migration with private fixtures."""

import json

import pytest

from netmon.core import state, user_files
from netmon.services.linux_help_reading_service import ReadingState


@pytest.fixture
def home(tmp_path, monkeypatch):
    root = tmp_path / "home"
    root.mkdir(mode=0o700)
    (root / "Dokumente").mkdir(mode=0o700)
    monkeypatch.setenv("HOME", str(root))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(root / ".config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(root / ".local/state"))
    monkeypatch.setenv("XDG_DATA_HOME", str(root / ".local/share"))
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(root / "Dokumente"))
    user_files._PREPARED.clear()
    return root


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data if isinstance(data, bytes) else data.encode())
    return path


def test_system_user_dirs_setting_wins_and_resolution_itself_does_not_create(
    home, monkeypatch
):
    monkeypatch.delenv("XDG_DOCUMENTS_DIR")
    put(home / ".config/user-dirs.dirs", 'XDG_DOCUMENTS_DIR="$HOME/Dokumente"\n')
    (home / "Documents").mkdir()
    assert state.netmon_documents_path() == str(home / "Dokumente/NetMon")
    assert not (home / "Dokumente/NetMon").exists()
    assert state.get_netmon_documents_dir() == str(home / "Dokumente/NetMon")
    assert state.get_netmon_config_dir() == str(home / "Dokumente/NetMon/Config")
    assert state.get_netmon_wireguard_dir() == str(home / "Dokumente/NetMon/WireGuard")


def test_german_locale_fresh_profile_does_not_create_english_documents(
    home, monkeypatch
):
    monkeypatch.delenv("XDG_DOCUMENTS_DIR")
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    assert state.get_netmon_documents_dir() == str(home / "Dokumente/NetMon")
    assert not (home / "Documents").exists()


def test_configured_custom_document_folder_with_spaces_is_central(home, monkeypatch):
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(home / "Meine Daten"))
    assert state.get_netmon_documents_dir() == str(home / "Meine Daten/NetMon")
    assert state.get_netmon_fun_dir() == str(
        home / "Meine Daten/NetMon/Fun/code_the_classics"
    )


def test_migration_copies_all_persistent_sources_and_preserves_originals(home):
    originals = {
        "Documents/NetMon/Config/config.json": b'{"theme":"dark"}',
        "Documents/NetMon/Radio/radio_db.json": b'[{"name":"Station"}]',
        ".config/netmon/linux_help_commands.json": b"[]",
        ".local/share/netmon/fun/code_the_classics/game/main.py": b'print("not executed")',
        ".local/state/netmon/captures/trace.pcap": b"capture fixture",
        ".local/state/netmon/radio_recordings/demo.mp3": b"audio fixture",
        ".local/state/netmon/linux_help_reading.json": b'{"version":1,"entries":{}}',
        ".local/state/netmon/netmon_radio_app.log": b"radio log fixture",
        "Bilder/Log-Pics/custom.jpg": b"image fixture",
    }
    expected = [
        "Config/config.json",
        "Radio/radio_db.json",
        "Config/linux_help_commands.json",
        "Fun/code_the_classics/game/main.py",
        "Captures/trace.pcap",
        "Radio/Aufnahmen/demo.mp3",
        "LinuxHelp/reading.json",
        "Logs/netmon_radio_app.log",
        "Log-Pics/custom.jpg",
    ]
    for path, data in originals.items():
        put(home / path, data)
    put(home / ".local/state/netmon/radio_ipc.key", "runtime only")
    target = home / "Dokumente/NetMon"
    report = user_files.migrate_user_files(target, assets=False)
    assert report["complete"] and not report["errors"]
    for old, new in zip(originals, expected):
        assert (
            (home / old).read_bytes() == (target / new).read_bytes() == originals[old]
        )
        assert (target / new).stat().st_mode & 0o777 == 0o600
    assert not list(target.rglob("radio_ipc.key"))
    assert (target / "Config").stat().st_mode & 0o777 == 0o700
    assert (target / "WireGuard").is_dir()


def test_conflicts_keep_destination_and_recoverable_source_copy(home):
    target = home / "Dokumente/NetMon"
    put(target / "Config/config.json", '{"theme":"new"}')
    original = put(home / "Documents/NetMon/Config/config.json", '{"theme":"old"}')
    report = user_files.migrate_user_files(target, assets=False)
    assert report["complete"] and len(report["conflicts"]) == 1
    assert json.loads((target / "Config/config.json").read_text()) == {"theme": "new"}
    assert (target / report["conflicts"][0]).read_bytes() == original.read_bytes()


def test_original_settings_are_saved_before_known_path_rewrites(home):
    target = home / "Dokumente/NetMon"
    source = home / "Documents/NetMon/Config/netmon_privacy.json"
    raw = json.dumps(
        {
            "log_overlay_image_path": "/usr/share/netmon/assets/log-pics/Netmon.png",
            "log_overlay_last_dir": str(home / "Bilder/Log-Pics"),
            "recordings_dir": str(home / ".local/state/netmon/radio_recordings"),
            "unchanged": "https://example.com/live",
        }
    ).encode()
    put(source, raw)
    report = user_files.migrate_user_files(target, assets=False)
    assert report["complete"] and len(report["rewritten"]) == 1
    new = json.loads((target / "Config/netmon_privacy.json").read_text())
    assert new["log_overlay_image_path"] == str(target / "Log-Pics/Netmon.png")
    assert new["log_overlay_last_dir"] == str(target / "Log-Pics")
    assert new["recordings_dir"] == str(target / "Radio/Aufnahmen")
    assert new["unchanged"] == "https://example.com/live"
    assert (
        source.read_bytes()
        == (target / "Migration/Originale/Config/netmon_privacy.json").read_bytes()
        == raw
    )


def test_completed_migration_does_not_resurrect_deleted_files(home):
    target = home / "Dokumente/NetMon"
    put(home / "Documents/NetMon/Config/reset.json", "{}")
    first = user_files.migrate_user_files(target, assets=False)
    (target / "Config/reset.json").unlink()
    second = user_files.migrate_user_files(target, assets=False)
    assert (
        first["copied"] == second["copied"]
        and not (target / "Config/reset.json").exists()
    )


def test_identical_existing_file_is_not_replaced(home):
    target = home / "Dokumente/NetMon"
    put(home / "Documents/NetMon/Config/same.json", "{}")
    existing = put(target / "Config/same.json", "{}")
    before = existing.stat()
    report = user_files.migrate_user_files(target, assets=False)
    assert report["complete"] and report["identical"] == 1 and not report["conflicts"]
    assert (
        existing.stat().st_ino == before.st_ino
        and existing.stat().st_mtime_ns == before.st_mtime_ns
    )


def test_symlink_source_is_reported_without_reading_target(home):
    outside = put(home / "outside.json", '{"private":"fixture"}')
    link = home / "Documents/NetMon/Config/link.json"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)
    target = home / "Dokumente/NetMon"
    report = user_files.migrate_user_files(target, assets=False)
    assert str(link) in report["skipped"] and not (target / "Config/link.json").exists()
    assert outside.read_text() == '{"private":"fixture"}'


def test_target_symlink_never_receives_source_writes(home):
    target = home / "Dokumente/NetMon"
    outside = home / "outside"
    outside.mkdir()
    (target / "Config").mkdir(parents=True)
    (target / "Config/link.json").symlink_to(outside / "sentinel.json")
    put(home / "Documents/NetMon/Config/link.json", '{"fixture":true}')
    report = user_files.migrate_user_files(target, assets=False)
    assert not (outside / "sentinel.json").exists()
    assert not report["complete"]  # Path rewrite refuses the linked settings file.


def test_reading_progress_is_personal_data_in_linux_help(home):
    user_files.migrate_user_files(home / "Dokumente/NetMon", assets=False)
    progress = ReadingState()
    entry = {"id": "ls", "name": "ls", "cmd": "ls", "entry_type": "command"}
    progress.change(entry, read=True)
    assert progress._path() == home / "Dokumente/NetMon/LinuxHelp/reading.json"
    assert ReadingState().get(entry)["read"] is True


def test_log_pics_are_seeded_without_replacing_custom_images(home, monkeypatch):
    assets = home / "package-assets"
    put(assets / "Netmon.png", "package image")
    put(assets / "second.jpg", "other image")
    monkeypatch.setattr(user_files, "_asset_sources", lambda: assets)
    target = home / "Dokumente/NetMon"
    custom = put(target / "Log-Pics/Netmon.png", "user image")
    report = user_files.migrate_user_files(target)
    assert report["complete"] and custom.read_text() == "user image"
    assert (target / "Log-Pics/second.jpg").read_text() == "other image"
    assert not report["conflicts"]


def test_index_key_collision_does_not_silently_discard_settings(home):
    target = home / "Dokumente/NetMon"
    old = home / "Documents/NetMon/a"
    new = target / "a"
    raw = json.dumps({str(old): "legacy", str(new): "current"})
    put(home / "Documents/NetMon/Config/collision.json", raw)
    report = user_files.migrate_user_files(target, assets=False)
    assert not report["complete"]
    assert (target / "Config/collision.json").read_text() == raw


def test_error_during_copy_never_publishes_partial_target(home, monkeypatch):
    target = home / "Dokumente/NetMon"
    put(home / "Documents/NetMon/Radio/data.bin", "fixture")

    def fail(*args, **kwargs):
        raise OSError("synthetic publication failure")

    monkeypatch.setattr(user_files.os, "link", fail)
    report = user_files.migrate_user_files(target, assets=False)
    assert not report["complete"] and not (target / "Radio/data.bin").exists()
    assert not list(target.rglob(".netmon-copy-*"))


def test_unreadable_source_tree_does_not_claim_complete_migration(home, monkeypatch):
    put(home / "Documents/NetMon/Config/config.json", "{}")

    def unreadable(source, *, followlinks, onerror):
        onerror(PermissionError("synthetic unreadable source"))
        return iter(())

    monkeypatch.setattr(user_files.os, "walk", unreadable)
    report = user_files.migrate_user_files(home / "Dokumente/NetMon", assets=False)
    assert not report["complete"]
    assert any("unreadable source" in item["error"] for item in report["errors"])
