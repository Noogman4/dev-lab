import json

from netmon.services.startup_guard_service import StartupGuardService


def test_collect_entries_and_baseline_roundtrip(tmp_path):
    user_autostart = tmp_path / "user_autostart"
    systemd_user = tmp_path / "systemd_user"
    user_autostart.mkdir()
    systemd_user.mkdir()

    desktop_file = user_autostart / "demo.desktop"
    desktop_file.write_text("[Desktop Entry]\nName=Demo\nExec=demo\n", encoding="utf-8")

    service_file = systemd_user / "demo.service"
    service_file.write_text("[Unit]\nDescription=Demo\n", encoding="utf-8")

    service = StartupGuardService(
        sources=[
            ("user_autostart", str(user_autostart / "*.desktop")),
            ("systemd_user", str(systemd_user / "*.service")),
        ]
    )

    entries = service.collect_entries()

    assert len(entries) == 2
    assert entries[0]["exists"] is True
    assert entries[0]["sha256"]
    assert entries[0]["mtime"] > 0
    assert entries[0]["size"] > 0

    baseline_path = tmp_path / "startup_guard_baseline.json"
    ok, err = service.save_baseline(str(baseline_path), entries)

    assert ok is True
    assert err == ""

    loaded = service.load_baseline(str(baseline_path))

    assert len(loaded["entries"]) == 2
    assert loaded["generated_at"]

    raw = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert len(raw["entries"]) == 2


def test_compare_to_baseline_detects_new_removed_and_changed(tmp_path):
    user_autostart = tmp_path / "user_autostart"
    user_autostart.mkdir()

    keep_file = user_autostart / "keep.desktop"
    keep_file.write_text("[Desktop Entry]\nName=Keep\n", encoding="utf-8")

    removed_file = user_autostart / "removed.desktop"
    removed_file.write_text("[Desktop Entry]\nName=Removed\n", encoding="utf-8")

    changed_file = user_autostart / "changed.desktop"
    changed_file.write_text("[Desktop Entry]\nName=Old\n", encoding="utf-8")

    service = StartupGuardService(
        sources=[("user_autostart", str(user_autostart / "*.desktop"))]
    )

    baseline_entries = service.collect_entries()
    baseline = {"entries": baseline_entries}

    removed_file.unlink()
    changed_file.write_text(
        "[Desktop Entry]\nName=New\nExec=/bin/true\n", encoding="utf-8"
    )
    new_file = user_autostart / "new.desktop"
    new_file.write_text("[Desktop Entry]\nName=New\n", encoding="utf-8")

    current_entries = service.collect_entries()
    result = service.compare_to_baseline(baseline, current_entries)

    assert [entry["name"] for entry in result["new"]] == ["new.desktop"]
    assert [entry["name"] for entry in result["removed"]] == ["removed.desktop"]
    assert result["changed"][0]["before"]["name"] == "changed.desktop"
    assert result["changed"][0]["after"]["name"] == "changed.desktop"
    assert [entry["name"] for entry in result["unchanged"]] == ["keep.desktop"]


def test_trustlist_roundtrip_and_compare_marks_matching_entry_trusted(tmp_path):
    user_autostart = tmp_path / "user_autostart"
    user_autostart.mkdir()

    trusted_file = user_autostart / "trusted.desktop"
    trusted_file.write_text("[Desktop Entry]\nName=Trusted\n", encoding="utf-8")

    service = StartupGuardService(
        sources=[("user_autostart", str(user_autostart / "*.desktop"))]
    )

    baseline = {"entries": []}
    current_entries = service.collect_entries()
    current_entry = current_entries[0]

    trustlist_path = tmp_path / "startup_guard_trustlist.json"
    ok, err = service.mark_trusted(
        current_entry["path"], current_entry, str(trustlist_path)
    )

    assert ok is True
    assert err == ""

    trustlist = service.load_trustlist(str(trustlist_path))
    assert current_entry["path"] in trustlist["trusted"]
    assert service.is_trusted(current_entry, trustlist) is True

    result = service.compare_to_baseline(baseline, current_entries, trustlist)

    assert result["new"] == []
    assert result["changed"] == []
    assert result["removed"] == []
    assert [entry["name"] for entry in result["trusted"]] == ["trusted.desktop"]


def test_trusted_entry_becomes_changed_again_after_hash_change(tmp_path):
    user_autostart = tmp_path / "user_autostart"
    user_autostart.mkdir()

    changed_file = user_autostart / "trusted.desktop"
    changed_file.write_text("[Desktop Entry]\nName=Old\n", encoding="utf-8")

    service = StartupGuardService(
        sources=[("user_autostart", str(user_autostart / "*.desktop"))]
    )

    baseline = {"entries": service.collect_entries()}
    original_entry = baseline["entries"][0]

    trustlist_path = tmp_path / "startup_guard_trustlist.json"
    ok, err = service.mark_trusted(
        original_entry["path"], original_entry, str(trustlist_path)
    )
    assert ok is True
    assert err == ""

    changed_file.write_text(
        "[Desktop Entry]\nName=New\nExec=/bin/true\n", encoding="utf-8"
    )
    current_entries = service.collect_entries()
    trustlist = service.load_trustlist(str(trustlist_path))
    result = service.compare_to_baseline(baseline, current_entries, trustlist)

    assert result["trusted"] == []
    assert len(result["changed"]) == 1
    assert result["changed"][0]["after"]["name"] == "trusted.desktop"


def test_reset_trustlist_clears_saved_entries(tmp_path):
    trustlist_path = tmp_path / "startup_guard_trustlist.json"
    service = StartupGuardService()

    ok, err = service.save_trustlist(
        str(trustlist_path),
        {"trusted": {"/tmp/demo.desktop": {"name": "demo.desktop"}}},
    )
    assert ok is True
    assert err == ""

    ok, err = service.reset_trustlist(str(trustlist_path))

    assert ok is True
    assert err == ""
    assert service.load_trustlist(str(trustlist_path)) == {"trusted": {}}
