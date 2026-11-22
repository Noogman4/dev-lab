"""Real private filesystem round-trips, malformed inventories and preview races."""

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon import app as app_module
from netmon.core import user_backup as backup, user_files
from netmon.core.wireguard_import import ProfileSnapshot
from netmon.features import radio_controller
from netmon.services.linux_help_reading_service import ReadingState
from netmon.services import linux_help_library_service as help_library


def put(path, payload):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_bytes(payload if isinstance(payload, bytes) else payload.encode())
    path.chmod(0o600)
    return path


def json_file(path, value):
    return put(path, json.dumps(value))


@pytest.fixture
def data(tmp_path, monkeypatch):
    home = tmp_path / "old-user"
    home.mkdir(mode=0o700)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(home / "Dokumente"))
    for variable, child in [
        ("XDG_CONFIG_HOME", ".config"),
        ("XDG_STATE_HOME", ".local/state"),
        ("XDG_DATA_HOME", ".local/share"),
    ]:
        monkeypatch.setenv(variable, str(home / child))
    root = home / "Dokumente/NetMon"
    (home / "Dokumente").mkdir(mode=0o700)
    root.mkdir(mode=0o700)
    json_file(
        root / "Config/config.json",
        {"theme": "dark", "language": "de", "marker": "preserved"},
    )
    json_file(
        root / "Config/netmon_privacy.json",
        {
            "log_overlay_image_path": str(root / "Log-Pics/test.png"),
            "wg_import_dir": str(root / "WireGuard"),
            "url": "https://example.invalid/",
            "external": "/mnt/personal",
        },
    )
    station = {
        "id": "test-station",
        "name": "Test Station",
        "url": "https://example.invalid/live",
        "custom": True,
    }
    json_file(root / "Radio/radio_db.json", [station])
    json_file(root / "Radio/radio_favorites.json", [station])
    json_file(
        root / "Radio/radio_settings.json",
        {
            "recordings_dir": str(root / "Radio/Aufnahmen"),
            "playlists_dir": str(root / "Radio/Playlisten"),
            "playlist_path": str(root / "Radio/Playlisten/test.m3u"),
        },
    )
    put(root / "Radio/Aufnahmen/test.mp3", b"synthetic audio, never played")
    put(root / "Radio/Playlisten/test.m3u", "#EXTM3U\nhttps://example.invalid/live\n")
    put(root / "WireGuard/test.conf", b"[Interface]\nAddress=192.0.2.2/32\n")
    put(root / "Log-Pics/test.png", b"synthetic image")
    json_file(root / "LinuxHelp/reading.json", {"version": 1, "entries": {}})
    json_file(root / "Security/baseline.json", {"version": 1, "entries": []})
    put(root / "Logs/runtime.log", "historical log")
    (root / "empty").mkdir(mode=0o700)
    parent = tmp_path / "external-backups"
    parent.mkdir(mode=0o700)
    target_parent = tmp_path / "new-user/Documents"
    target_parent.mkdir(mode=0o700, parents=True)
    # All ancestors in private fixtures must have deployment-safe rights.
    target_parent.parent.chmod(0o700)
    return SimpleNamespace(
        root=root, parent=parent, target=target_parent / "NetMon", station=station
    )


@pytest.fixture
def exported(data):
    return backup.export_backup(data.root, data.parent)


def manifest(path):
    return json.loads((path / backup.MANIFEST).read_text())


def change_manifest(path, mutate):
    value = manifest(path)
    mutate(value)
    json_file(path / backup.MANIFEST, value)


def test_export_has_versioned_exact_inventory_and_private_output(data, exported):
    info = manifest(exported)
    assert info["format"] == backup.FORMAT
    assert info["format_version"] == info["data_version"] == 1
    assert info["app_version"] == app_module.NETMON_APP_VERSION
    assert info["source_root"] == str(data.root)
    assert info["kind"] == "full"
    assert "empty" in info["directories"]
    for entry in info["files"]:
        source, copied = data.root / entry["path"], exported / "NetMon" / entry["path"]
        assert source.read_bytes() == copied.read_bytes()
        assert hashlib.sha256(copied.read_bytes()).hexdigest() == entry["sha256"]
        assert entry["size"] == copied.stat().st_size
        assert copied.stat().st_mode & 0o777 == 0o600
    assert exported.stat().st_mode & 0o777 == 0o700


def test_preview_is_read_only_and_new_home_paths_are_adapted(data, exported):
    before = (exported / "NetMon/Config/netmon_privacy.json").read_bytes()
    plan = backup.preview_restore(exported, data.target)
    assert not data.target.exists()
    assert (exported / "NetMon/Config/netmon_privacy.json").read_bytes() == before
    assert any(
        e.path == "Config/netmon_privacy.json" and e.adapted for e in plan.entries
    )
    assert all(
        e.action == "archive"
        for e in plan.entries
        if e.path.startswith(("Security/", "Logs/"))
    )


def test_restore_loads_actual_settings_radio_reading_and_private_wg(
    data, exported, monkeypatch
):
    reading = ReadingState(data.root / "LinuxHelp/reading.json")
    entry = {"id": "ls", "name": "ls", "cmd": "ls"}
    reading.change(entry, read=True)
    exported = backup.export_backup(data.root, data.parent)
    report_path, report = backup.restore_backup(
        backup.preview_restore(exported, data.target)
    )
    assert report["complete"] and report_path.is_file()
    assert (data.target / "empty").is_dir()
    assert not (data.target / "Security/baseline.json").exists()
    assert not (data.target / "Logs/runtime.log").exists()
    assert (report_path.parent / "Pruefreferenzen/Security/baseline.json").is_file()
    app = app_module.App.__new__(app_module.App)
    app.netmon_config_path = str(data.target / "Config/config.json")
    app.privacy_config_path = str(data.target / "Config/netmon_privacy.json")
    app.settings = {}
    app.load_settings()
    assert app.settings["theme"] == "dark" and app.settings["marker"] == "preserved"
    privacy = app.load_privacy_config()
    assert privacy["wg_import_dir"] == str(data.target / "WireGuard")
    assert Path(privacy["log_overlay_image_path"]).is_file()
    assert (
        privacy["external"] == "/mnt/personal"
        and privacy["url"] == "https://example.invalid/"
    )
    radio_app = SimpleNamespace(
        radio_db_path=str(data.target / "Radio/radio_db.json"),
        radio_favorites_path=str(data.target / "Radio/radio_favorites.json"),
    )
    assert radio_controller.load_radio_db(radio_app)[0]["id"] == data.station["id"]
    assert radio_controller.load_favorites(radio_app)[0]["id"] == data.station["id"]
    assert ReadingState(data.target / "LinuxHelp/reading.json").get(entry)["read"]
    assert (
        ProfileSnapshot.read(data.target / "WireGuard/test.conf").data
        == (data.root / "WireGuard/test.conf").read_bytes()
    )
    assert json.loads((data.target / "Radio/radio_settings.json").read_text())[
        "recordings_dir"
    ] == str(data.target / "Radio/Aufnahmen")


def test_personal_markdown_and_bookmark_survive_backup_to_new_home(
    data, tmp_path, monkeypatch
):
    current = [data.root]

    def subdir(*parts):
        path = current[0].joinpath(*parts)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        return str(path)

    monkeypatch.setattr(help_library, "get_netmon_documents_subdir", subdir)
    source = tmp_path / "my-help.md"
    original = "# Eigene Hilfe\n\n```sh\nprintf '%s' 'Grüße'\n```\n"
    source.write_text(original)
    metadata = help_library.import_linux_help_markdown(source)
    entry = {
        "entry_type": "command",
        "id": "my_help",
        "name": metadata["title"],
        "cmd": "",
        "category": "Eigene",
        "markdown_id": metadata["id"],
    }
    json_file(data.root / "Config/linux_help_commands.json", [entry])
    json_file(data.root / "Config/linux_help_glossary.json", {"entries": []})
    reading = ReadingState(data.root / "LinuxHelp/reading.json")
    reading.change(entry, read=True, bookmark={"tab": "documentation", "position": 0.5})
    exported = backup.export_backup(data.root, data.parent)
    _, report = backup.restore_backup(backup.preview_restore(exported, data.target))
    assert report["complete"]
    current[0] = data.target
    restored = help_library.get_linux_help_document_by_id(metadata["id"])
    assert restored["markdown_path"].startswith(str(data.target) + "/")
    assert Path(restored["markdown_path"]).read_text() == original
    assert any(
        block.kind == "code"
        for block in help_library.load_linux_help_markdown(restored).blocks
    )
    from netmon.features import linux_help_controller as help_controller

    app = SimpleNamespace(
        linux_help_data_path=str(data.target / "Config/linux_help_commands.json"),
        linux_help_glossary_path=str(data.target / "Config/linux_help_glossary.json"),
        linux_help_glossary_seed_path="",
    )
    help_controller.load_linux_help_data(app)
    linked = help_controller.get_linux_help_command_by_id(app, "my_help")
    assert linked["markdown_id"] == metadata["id"]
    assert help_controller.load_entry_document(linked).blocks[0].text == "Eigene Hilfe"
    assert ReadingState(data.target / "LinuxHelp/reading.json").get(entry) == {
        "read": True,
        "bookmark": {"tab": "documentation", "position": 0.5},
    }


def test_multi_recording_selection_audio_and_title_history_survive_restore(
    data, monkeypatch
):
    from netmon.features import radio_multi_recording_controller as multi_controller

    settings_path = data.root / "Radio/radio_settings.json"
    settings = json.loads(settings_path.read_text())
    settings.update(
        multi_recording_station_ids=[data.station["id"]], multi_recording_minutes=90
    )
    json_file(settings_path, settings)
    audio = put(data.root / "Radio/Aufnahmen/multi-test.mp3", b"synthetic recording")
    metadata = {
        "version": 1,
        "audio_file": audio.name,
        "station_id": data.station["id"],
        "titles": [{"offset_seconds": 3.5, "title": "Künstler – Titel"}],
    }
    sidecar = json_file(audio.with_suffix(".json"), metadata)
    original = sidecar.read_bytes()
    exported = backup.export_backup(data.root, data.parent)
    _, report = backup.restore_backup(backup.preview_restore(exported, data.target))
    assert report["complete"]
    restored_settings = json.loads(
        (data.target / "Radio/radio_settings.json").read_text()
    )
    assert restored_settings["multi_recording_minutes"] == 90
    assert (data.target / "Radio/Aufnahmen/multi-test.json").read_bytes() == original
    assert (
        data.target / "Radio/Aufnahmen/multi-test.mp3"
    ).read_bytes() == audio.read_bytes()
    app = SimpleNamespace(
        radio_settings=restored_settings,
        radio_db=[data.station],
        radio_favorites=[],
        radio_search_results=[],
    )
    mode = multi_controller.manager(app)
    assert not mode.busy
    assert [row["id"] for row in mode.snapshot()[0]] == [data.station["id"]]


def test_existing_conflicts_are_preserved_by_default(data, exported):
    original = json_file(data.target / "Config/config.json", {"theme": "light"})
    data.target.chmod(0o700)
    before = original.read_bytes(), original.stat().st_ino
    path, report = backup.restore_backup(backup.preview_restore(exported, data.target))
    assert (original.read_bytes(), original.stat().st_ino) == before
    assert (
        json.loads((path.parent / "Konflikte/Config/config.json").read_text())["theme"]
        == "dark"
    )
    assert any(e["action"] == "kept" for e in report["files"])


def test_explicit_replace_saves_exact_originals(data, exported):
    original = json_file(data.target / "Config/config.json", {"theme": "light"})
    data.target.chmod(0o700)
    before = original.read_bytes()
    path, report = backup.restore_backup(
        backup.preview_restore(exported, data.target), replace_conflicts=True
    )
    assert json.loads(original.read_text())["theme"] == "dark"
    assert (path.parent / "Originale/Config/config.json").read_bytes() == before
    assert any(e["action"] == "replaced" for e in report["files"])


def test_identical_file_is_not_replaced(data, exported):
    original = put(data.target / "Log-Pics/test.png", b"synthetic image")
    data.target.chmod(0o700)
    before = original.stat()
    _, report = backup.restore_backup(backup.preview_restore(exported, data.target))
    assert (
        original.stat().st_ino == before.st_ino
        and original.stat().st_mtime_ns == before.st_mtime_ns
    )
    assert (
        next(e for e in report["files"] if e["path"] == "Log-Pics/test.png")["action"]
        == "identical"
    )


@pytest.mark.parametrize(
    "damage", ["changed", "missing", "extra", "size", "duplicate", "extra-dir"]
)
def test_corruption_is_rejected_before_any_target_write(data, exported, damage):
    path = exported / "NetMon/Config/config.json"
    if damage == "changed":
        json_file(path, {"theme": "modified"})
    elif damage == "missing":
        path.rename(exported / "removed-file")
    elif damage == "extra":
        put(exported / "NetMon/unlisted", "unexpected")
    elif damage == "extra-dir":
        (exported / "NetMon/unlisted-dir").mkdir()
    elif damage == "size":
        change_manifest(exported, lambda m: m["files"][0].update(size=999))
    else:
        change_manifest(exported, lambda m: m["files"].append(dict(m["files"][0])))
    with pytest.raises(backup.BackupError):
        backup.preview_restore(exported, data.target)
    assert not data.target.exists()


@pytest.mark.parametrize(
    "path",
    [
        "../outside",
        "/tmp/outside",
        "Config/../outside",
        "Config//file",
        "Config/./file",
        "C:\\file",
        "Config/a\nfile",
        "Config/\x00file",
    ],
)
def test_manifest_path_traversal_rejected(data, exported, path):
    change_manifest(exported, lambda m: m["files"][0].update(path=path))
    with pytest.raises(backup.BackupError):
        backup.preview_restore(exported, data.target)
    assert not data.target.exists()


@pytest.mark.parametrize(
    "key,value",
    [
        ("format_version", 2),
        ("data_version", 2),
        ("data_version", True),
        ("source_root", "/"),
        ("format", "other"),
    ],
)
def test_unsupported_formats_fail_closed(data, exported, key, value):
    change_manifest(exported, lambda m: m.update({key: value}))
    with pytest.raises(backup.BackupError):
        backup.preview_restore(exported, data.target)


def test_app_version_is_separate_from_supported_data_version(data, exported):
    change_manifest(exported, lambda m: m.update(app_version="2.0.0"))
    plan = backup.preview_restore(exported, data.target)
    assert plan.app_version == "2.0.0"
    assert backup.restore_backup(plan)[1]["complete"]


def test_unversioned_legacy_backup_is_not_relabelled_as_verified(data, exported):
    json_file(exported / backup.MANIFEST, {"created_at": "old", "selection": []})
    with pytest.raises(backup.BackupError, match="altes Sicherungsformat"):
        backup.preview_restore(exported, data.target)


def test_duplicate_json_keys_rejected(data, exported):
    path = exported / backup.MANIFEST
    raw = path.read_text().replace(
        '"format_version": 1', '"format_version": 1, "format_version": 2'
    )
    put(path, raw)
    with pytest.raises(backup.BackupError):
        backup.preview_restore(exported, data.target)


@pytest.mark.parametrize("kind", ["symlink", "parent-symlink", "hardlink", "fifo"])
def test_unsafe_source_files_rejected_without_following(data, tmp_path, kind):
    path = data.root / "unsafe"
    sentinel = put(tmp_path / "sentinel", "unchanged")
    if kind == "symlink":
        path.symlink_to(sentinel)
    elif kind == "parent-symlink":
        path.symlink_to(sentinel.parent, target_is_directory=True)
    elif kind == "hardlink":
        os.link(sentinel, path)
    else:
        os.mkfifo(path)
    with pytest.raises(backup.BackupError):
        backup.export_backup(data.root, data.parent)
    assert sentinel.read_text() == "unchanged"


def test_technical_locks_old_reports_and_generated_links_are_explicitly_excluded(data):
    put(data.root / "Migration/old-report.json", "{}")
    put(data.root / "Wiederherstellungen/old/file", "archive")
    put(data.root / "Radio/.radio.lock", "runtime lock")
    generated = data.root / "projectM Visualizer/Presets/.netmon_projectm_flat_scan_v1"
    generated.mkdir(mode=0o700, parents=True)
    (generated / "link.milk").symlink_to(data.root / "absent.milk")
    result = backup.export_backup(data.root, data.parent)
    skipped = {item["path"] for item in manifest(result)["excluded"]}
    assert {
        "Migration",
        "Wiederherstellungen",
        "Radio/.radio.lock",
        "projectM Visualizer/Presets/.netmon_projectm_flat_scan_v1",
    } <= skipped
    assert backup.preview_restore(result, data.target)


@pytest.mark.parametrize(
    "kind", ["backup-file", "manifest", "target-file", "new-target-appeared"]
)
def test_changed_preview_is_rejected_without_overwriting(data, exported, kind):
    existing = None
    if kind == "target-file":
        existing = json_file(data.target / "Config/config.json", {"theme": "old"})
        data.target.chmod(0o700)
    plan = backup.preview_restore(exported, data.target)
    if kind == "backup-file":
        put(exported / "NetMon/Log-Pics/test.png", "changed after preview")
    elif kind == "manifest":
        change_manifest(exported, lambda m: m.update(app_version="changed"))
    else:
        existing = json_file(
            data.target / "Config/config.json", {"theme": "concurrent"}
        )
        data.target.chmod(0o700)
    before = existing.read_bytes() if existing else None
    with pytest.raises(backup.BackupError):
        backup.restore_backup(plan, replace_conflicts=True)
    assert not (data.target / "WireGuard/test.conf").exists()
    if existing:
        assert existing.read_bytes() == before


@pytest.mark.parametrize("kind", ["file-symlink", "parent-symlink"])
def test_unsafe_target_never_receives_writes(data, exported, tmp_path, kind):
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    data.target.mkdir(mode=0o700)
    if kind == "parent-symlink":
        (data.target / "Config").symlink_to(outside, target_is_directory=True)
    else:
        (data.target / "Config").mkdir(mode=0o700)
        (data.target / "Config/config.json").symlink_to(outside / "sentinel")
    with pytest.raises((backup.BackupError, OSError)):
        backup.preview_restore(exported, data.target)
    assert list(outside.iterdir()) == []


def test_partial_export_has_same_payload_layout_and_does_not_import_other_areas(data):
    result = backup.export_backup(data.root, data.parent, selected=["Config"])
    assert manifest(result)["kind"] == "partial"
    assert (result / "NetMon/Config/config.json").is_file()
    assert not (result / "NetMon/Radio").exists()
    backup.restore_backup(backup.preview_restore(result, data.target))
    assert (data.target / "Config/config.json").is_file()
    assert not (data.target / "Radio").exists()


def test_restore_marker_prevents_legacy_data_resurrection(data, exported, monkeypatch):
    old = Path(os.environ["XDG_CONFIG_HOME"]) / "netmon/foreign.json"
    json_file(old, {"not_in_backup": True})
    backup.restore_backup(backup.preview_restore(exported, data.target))
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(data.target.parent))
    monkeypatch.setattr(user_files, "_asset_sources", lambda: None)
    user_files._PREPARED.clear()
    user_files.prepare_user_files()
    assert not (data.target / "Config/foreign.json").exists()


def test_corrupt_settings_cannot_silently_become_defaults(data):
    put(data.root / "Config/config.json", "{broken JSON")
    result = backup.export_backup(data.root, data.parent)
    with pytest.raises(backup.BackupError, match="JSON"):
        backup.preview_restore(result, data.target)


def test_executable_user_files_keep_owner_execution(data):
    source = put(data.root / "Fun/demo.py", "# Never execute")
    source.chmod(0o755)
    result = backup.export_backup(data.root, data.parent)
    backup.restore_backup(backup.preview_restore(result, data.target))
    assert (data.target / "Fun/demo.py").stat().st_mode & 0o777 == 0o700


def test_export_destination_cannot_be_inside_source(data):
    with pytest.raises(backup.BackupError, match="außerhalb"):
        backup.export_backup(data.root, data.root)


def test_bounds_fail_before_publishing_a_valid_manifest(data, monkeypatch):
    monkeypatch.setattr(backup, "MAX_TOTAL_BYTES", 1)
    with pytest.raises(backup.BackupError):
        backup.export_backup(data.root, data.parent)
    assert list(data.parent.iterdir()) == []


def test_interrupted_publication_never_overwrites_original(data, exported, monkeypatch):
    plan = backup.preview_restore(exported, data.target)
    original = backup.os.link

    def fail_in_target(src, dst, **kwargs):
        directory = os.readlink(f"/proc/self/fd/{kwargs['dst_dir_fd']}")
        if dst == "test.conf" and directory.startswith(str(data.target)):
            raise OSError("synthetic write failure")
        return original(src, dst, **kwargs)

    monkeypatch.setattr(backup.os, "link", fail_in_target)
    with pytest.raises(backup.BackupError, match="nicht vollständig"):
        backup.restore_backup(plan)
    assert not (data.target / "WireGuard/test.conf").exists()
    reports = list((data.target / "Wiederherstellungen").glob("*/bericht.json"))
    assert len(reports) == 1
    assert json.loads(reports[0].read_text())["complete"] is False
    assert not list(data.target.rglob(".netmon-backup-*"))


def test_staging_failure_cannot_leave_canonical_partial_files(
    data, exported, monkeypatch
):
    plan = backup.preview_restore(exported, data.target)
    original = backup._copy_new
    count = 0

    def fail_during_staging(source, destination, expected, mode=0o600, **kwargs):
        nonlocal count
        count += 1
        if count == 3:
            raise OSError("synthetic staging failure")
        return original(source, destination, expected, mode, **kwargs)

    monkeypatch.setattr(backup, "_copy_new", fail_during_staging)
    with pytest.raises(OSError, match="staging failure"):
        backup.restore_backup(plan)
    assert not data.target.exists()


def test_restore_run_collision_never_overwrites_existing_report(
    data, exported, monkeypatch
):
    monkeypatch.setattr(backup, "_stamp", lambda: "fixed-test-run")
    path, _ = backup.restore_backup(backup.preview_restore(exported, data.target))
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        backup.restore_backup(backup.preview_restore(exported, data.target))
    assert path.read_bytes() == before


def test_internal_path_key_collision_is_rejected(data):
    old, new = str(data.root / "same"), str(data.target / "same")
    json_file(data.root / "Config/collision.json", {old: "old", new: "new"})
    result = backup.export_backup(data.root, data.parent)
    with pytest.raises(ValueError):
        backup.preview_restore(result, data.target)
    assert not data.target.exists()


def test_changed_source_during_export_has_no_valid_manifest(data, monkeypatch):
    original = backup._copy_new
    changed = False

    def mutate_after_copy(source, destination, expected, mode=0o600, **kwargs):
        nonlocal changed
        original(source, destination, expected, mode, **kwargs)
        if not changed:
            changed = True
            source.write_bytes(b"changed after initial copy")

    monkeypatch.setattr(backup, "_copy_new", mutate_after_copy)
    with pytest.raises(backup.BackupError, match="Quellordner"):
        backup.export_backup(data.root, data.parent)
    assert not list(data.parent.rglob(backup.MANIFEST))


@pytest.mark.parametrize("external", [False, True])
def test_media_folder_survives_save_restart_and_backup_restore(data, external):
    media = (data.parent / "external-media") if external else data.root / "Radio/Medien"
    put(media / "music.mp3", b"synthetic, never played")

    def radio_app(root):
        return SimpleNamespace(
            radio_db_path=str(root / "Radio/radio_db.json"),
            radio_favorites_path=str(root / "Radio/radio_favorites.json"),
            radio_settings_path=str(root / "Radio/radio_settings.json"),
        )

    app = radio_app(data.root)
    radio_controller.load_radio_runtime(app)
    radio_controller._set_radio_folder_browser_mode_and_path(app, "system", str(media))
    saved = json.loads(Path(app.radio_settings_path).read_text())
    assert saved["system_folder_path"] == str(media)
    restarted = radio_app(data.root)
    radio_controller.load_radio_runtime(restarted)
    assert restarted.radio_system_folder_path == str(media)
    exported = backup.export_backup(data.root, data.parent, selected=["Radio"])
    backup.restore_backup(backup.preview_restore(exported, data.target))
    restored = radio_app(data.target)
    radio_controller.load_radio_runtime(restored)
    expected = media if external else data.target / "Radio/Medien"
    assert restored.radio_system_folder_path == str(expected)
    assert (expected / "music.mp3").is_file()
    # External music stays external; its saved path never expands backup scope.
    if external:
        assert not (exported / "NetMon/external-media").exists()
    radio_controller._set_radio_folder_browser_mode_and_path(restored, "recordings", "")
    assert json.loads(Path(restored.radio_settings_path).read_text())[
        "system_folder_path"
    ] == str(expected)


def test_random_interval_and_history_survive_radio_backup_and_restore(data):
    def radio_app(root):
        return SimpleNamespace(
            radio_db_path=str(root / "Radio/radio_db.json"),
            radio_favorites_path=str(root / "Radio/radio_favorites.json"),
            radio_settings_path=str(root / "Radio/radio_settings.json"),
        )

    app = radio_app(data.root)
    radio_controller.load_radio_runtime(app)
    history = [
        {
            "selected_at": "2026-11-15T22:30:00+00:00",
            "station_id": "test-station",
            "name": "Test Station",
            "status": "stopped",
        }
    ]
    criteria = {
        "categories": ["rock", "chillout"],
        "minimum_bitrate": 128,
        "include_unknown": True,
    }
    app.radio_settings.update(
        random_interval_minutes=12, random_history=history, random_filter=criteria
    )
    assert radio_controller.save_radio_settings(app)
    exported = backup.export_backup(data.root, data.parent, selected=["Radio"])
    backup.restore_backup(backup.preview_restore(exported, data.target))
    restored = radio_app(data.target)
    radio_controller.load_radio_runtime(restored)
    assert restored.radio_settings["random_interval_minutes"] == 12
    assert restored.radio_settings["random_history"] == history
    assert restored.radio_settings["random_filter"] == criteria


@pytest.mark.parametrize("extension", [".m3u", ".m3u8", ".M3U"])
@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_restore_adapts_only_absolute_internal_playlist_entries(
    data, extension, newline
):
    song = data.root / "Radio/Aufnahmen/Musik mit ü.mp3"
    put(song, b"synthetic")
    playlist = data.root / ("Radio/Playlisten/Umzug" + extension)
    unchanged = [
        "#EXTM3U",
        "#EXTINF:1," + str(song),
        "../Aufnahmen/relative.mp3",
        "/mnt/externe Musik/song.mp3",
        str(data.root) + "-anderer-ordner/song.mp3",
        "https://example.invalid/stream?path=" + str(song),
        "",
    ]
    old_line = "  " + str(song) + "\t"
    raw = (newline.join([*unchanged, old_line]) + newline).encode("utf-8")
    put(playlist, raw)
    exported = backup.export_backup(data.root, data.parent, selected=["Radio"])
    relative = str(playlist.relative_to(data.root))
    plan = backup.preview_restore(exported, data.target)
    entry = next(item for item in plan.entries if item.path == relative)
    assert entry.adapted
    assert not data.target.exists()
    assert (exported / "NetMon" / relative).read_bytes() == raw
    backup.restore_backup(plan)
    expected_line = "  " + str(data.target / song.relative_to(data.root)) + "\t"
    expected = (newline.join([*unchanged, expected_line]) + newline).encode("utf-8")
    restored = data.target / relative
    assert restored.read_bytes() == expected
    assert song.read_bytes() == b"synthetic"
    assert (data.target / song.relative_to(data.root)).is_file()
    second = backup.preview_restore(exported, data.target)
    assert (
        next(item for item in second.entries if item.path == relative).action
        == "identical"
    )


def test_restore_keeps_unmapped_playlist_bytes_and_limits_transform_input(
    data, monkeypatch
):
    playlist = data.root / "Radio/Playlisten/raw.m3u"
    raw = b"#EXTM3U\r\n#caf\xe9\r\n/mnt/external/song.mp3\r\n"
    put(playlist, raw)
    exported = backup.export_backup(data.root, data.parent)
    plan = backup.preview_restore(exported, data.target)
    assert not next(
        item for item in plan.entries if item.path.endswith("raw.m3u")
    ).adapted
    backup.restore_backup(plan)
    assert (data.target / playlist.relative_to(data.root)).read_bytes() == raw
    monkeypatch.setattr(backup, "MAX_JSON_BYTES", 4)
    with pytest.raises(backup.BackupError, match="Playlistdatei"):
        backup._transform("Radio/Playlisten/raw.m3u", raw, str(data.root), data.target)
