import json
from datetime import datetime

from netmon.features import security_monitoring_controller
from tools.netmon_security_parser import NetmonSecurityParser
from tools.netmon_security_store import NetmonSecurityStore


def test_security_parser_aggregates_local_dns_block():
    parser = NetmonSecurityParser()
    aggregated = {}
    dedup = {}

    line = (
        "Apr 1 12:00:00 host kernel: [UFW BLOCK] IN=eth0 OUT= "
        "SRC=192.168.1.10 DST=192.168.1.2 LEN=60 PROTO=UDP DPT=53"
    )

    event = parser.parse_ufw_block_line(
        line,
        aggregated=aggregated,
        dedup_cache=dedup,
        is_local_or_lan_ip_fn=lambda ip: ip.startswith("192.168."),
    )

    assert event is None
    assert aggregated.get("DNS") == 1


def test_security_parser_deduplicates_external_block():
    parser = NetmonSecurityParser()
    aggregated = {}
    dedup = {}
    line = (
        "Apr 1 12:00:00 host kernel: [UFW BLOCK] IN=eth0 OUT= "
        "SRC=8.8.8.8 DST=192.168.1.2 LEN=60 PROTO=TCP DPT=443"
    )

    ev1 = parser.parse_ufw_block_line(
        line,
        aggregated=aggregated,
        dedup_cache=dedup,
        is_local_or_lan_ip_fn=lambda _ip: False,
    )
    ev2 = parser.parse_ufw_block_line(
        line,
        aggregated=aggregated,
        dedup_cache=dedup,
        is_local_or_lan_ip_fn=lambda _ip: False,
    )

    assert ev1 is not None
    assert ev1["type"] == "UFW BLOCK"
    assert ev1["external"] is True
    assert ev2 is None


def test_security_store_filter_stats_and_portscan_detection():
    store = NetmonSecurityStore()
    base = [
        {
            "time": "2026-01-01 00:00:00",
            "type": "UFW BLOCK",
            "src": "1.2.3.4",
            "port": "22",
            "proto": "TCP",
            "level": "L1 INFO",
            "epoch": 0.0,
            "external": True,
        },
        {
            "time": "2026-01-01 00:00:01",
            "type": "Portscan-Verdacht",
            "src": "1.2.3.4",
            "port": "3",
            "proto": "-",
            "level": "L3 ALERT",
            "epoch": 0.0,
            "external": True,
        },
    ]

    assert len(store.filtered_events(base, "all", limit=50)) == 2
    assert len(store.filtered_events(base, "portscan", limit=50)) == 1

    total, block, scan, top_ip, top_port = store.compute_stats(base)
    assert (total, block, scan, top_ip, top_port) == (2, 1, 1, "1.2.3.4", "22")

    now_events = []
    for i in range(6):
        now_events.append(
            {
                "time": "2026-01-01 00:00:00",
                "type": "UFW BLOCK",
                "src": "9.9.9.9",
                "port": str(1000 + i),
                "proto": "TCP",
                "epoch": __import__("time").time(),
                "external": True,
            }
        )

    findings = store.detect_portscan(now_events, {})
    assert findings
    assert findings[0]["type"] == "Portscan-Verdacht"
    assert findings[0]["src"] == "9.9.9.9"


def test_security_file_events_get_distinct_keys_for_distinct_occurrences():
    first = security_monitoring_controller.security_create_file_event(
        "FILE MODIFIED",
        "/tmp/demo",
        "sha1|10|1.0",
    )
    second = security_monitoring_controller.security_create_file_event(
        "FILE MODIFIED",
        "/tmp/demo",
        "sha2|10|2.0",
    )

    assert first["key"] != second["key"]


def test_security_input_access_events_get_distinct_keys_for_repeated_access():
    first = security_monitoring_controller.security_create_input_access_event(
        "INPUT ACCESS START",
        "/dev/input/event0",
        "123",
        "python",
        "start|python|/dev/input/event0|123|1",
    )
    second = security_monitoring_controller.security_create_input_access_event(
        "INPUT ACCESS START",
        "/dev/input/event0",
        "123",
        "python",
        "start|python|/dev/input/event0|123|2",
    )

    assert first["key"] != second["key"]


def test_scan_integrity_changes_ignores_netmon_self_managed_files(tmp_path):
    config_dir = tmp_path / "config"
    state_dir = tmp_path / "state"
    watch_dir = tmp_path / "watch"
    config_dir.mkdir()
    state_dir.mkdir()
    watch_dir.mkdir()

    privacy_path = config_dir / "netmon_privacy.json"
    app_path = watch_dir / "app.py"
    privacy_path.write_text('{"mode": "on"}\n', encoding="utf-8")
    app_path.write_text("print('v1')\n", encoding="utf-8")

    class DummyApp:
        netmon_state_dir = str(state_dir)
        privacy_config_path = str(privacy_path)
        security_baseline_path = str(state_dir / "security_baseline.json")
        clamav_findings_path = str(state_dir / "clamav_findings.json")
        vpn_config_path = str(config_dir / "vpn_slots.json")
        primary_vpn_config_path = str(config_dir / "primary_vpn_slots.json")
        link_config_path = str(config_dir / "link_slots.json")
        hdd_config_path = str(config_dir / "hdd_slots.json")
        integrity_baseline = {}

        def _integrity_watch_files(self):
            return [str(privacy_path), str(app_path)]

        def hash_file_sha256(self, path):
            return security_monitoring_controller.hash_file_sha256(path)

        def _security_create_file_event(self, kind, path, token):
            return security_monitoring_controller.security_create_file_event(
                kind, path, token
            )

    app = DummyApp()
    security_monitoring_controller.build_integrity_baseline(app)

    privacy_path.write_text('{"mode": "off"}\n', encoding="utf-8")
    app_path.write_text("print('v2')\n", encoding="utf-8")

    events = security_monitoring_controller.scan_integrity_changes(app)

    assert [event["type"] for event in events] == ["FILE MODIFIED"]
    assert str(app_path) in events[0]["raw"]


def test_scan_integrity_changes_ignores_deleted_netmon_config_files(tmp_path):
    config_dir = tmp_path / "config"
    state_dir = tmp_path / "state"
    watch_dir = tmp_path / "watch"
    config_dir.mkdir()
    state_dir.mkdir()
    watch_dir.mkdir()

    hdd_path = config_dir / "netmon_hdd_slots.json"
    app_path = watch_dir / "app.py"
    hdd_path.write_text('{"slots": []}\n', encoding="utf-8")
    app_path.write_text("print('v1')\n", encoding="utf-8")

    class DummyApp:
        netmon_config_dir = str(config_dir)
        netmon_state_dir = str(state_dir)
        hdd_config_path = str(hdd_path)
        security_baseline_path = str(state_dir / "security_baseline.json")
        integrity_baseline = {}

        def _integrity_watch_files(self):
            return [str(hdd_path), str(app_path)]

        def hash_file_sha256(self, path):
            return security_monitoring_controller.hash_file_sha256(path)

        def _security_create_file_event(self, kind, path, token):
            return security_monitoring_controller.security_create_file_event(
                kind, path, token
            )

    app = DummyApp()
    security_monitoring_controller.build_integrity_baseline(app)

    hdd_path.unlink()
    app_path.write_text("print('v2')\n", encoding="utf-8")

    events = security_monitoring_controller.scan_integrity_changes(app)

    assert [event["type"] for event in events] == ["FILE MODIFIED"]
    assert str(app_path) in events[0]["raw"]


def test_security_integrity_ignore_path_keeps_non_netmon_paths_visible(tmp_path):
    config_dir = tmp_path / "config"
    state_dir = tmp_path / "state"
    other_path = tmp_path / "other.conf"
    config_dir.mkdir()
    state_dir.mkdir()
    other_path.write_text("demo\n", encoding="utf-8")

    class DummyApp:
        netmon_config_dir = str(config_dir)
        netmon_state_dir = str(state_dir)

    app = DummyApp()

    assert (
        security_monitoring_controller.security_integrity_ignore_path(
            app, str(other_path)
        )
        is False
    )


def test_security_integrity_ignored_paths_collects_known_explicit_paths():
    app = type(
        "DummyApp",
        (),
        {
            "vpn_config_path": "/tmp/vpn.json",
            "privacy_config_path": "/tmp/privacy.json",
            "security_baseline_path": "/tmp/security.json",
        },
    )()

    assert security_monitoring_controller._security_integrity_ignored_paths(app) == {
        "/tmp/vpn.json",
        "/tmp/privacy.json",
        "/tmp/security.json",
    }


def test_security_integrity_ignored_paths_skips_empty_values():
    app = type(
        "DummyApp",
        (),
        {
            "vpn_config_path": "",
            "privacy_config_path": None,
            "security_baseline_path": "   ",
        },
    )()

    assert (
        security_monitoring_controller._security_integrity_ignored_paths(app) == set()
    )


def test_path_is_dir_or_child_matches_same_dir_and_nested_file():
    assert security_monitoring_controller._path_is_dir_or_child(
        "/tmp/config",
        "/tmp/config",
    )
    assert security_monitoring_controller._path_is_dir_or_child(
        "/tmp/config/file.json",
        "/tmp/config",
    )


def test_path_is_dir_or_child_rejects_empty_and_prefix_collisions():
    assert not security_monitoring_controller._path_is_dir_or_child(
        "/tmp/config-file",
        "/tmp/config",
    )
    assert not security_monitoring_controller._path_is_dir_or_child(
        "/tmp/config",
        "",
    )


def test_integrity_watch_files_set_normalizes_and_filters_values():
    app = type(
        "DummyApp",
        (),
        {
            "_integrity_watch_files": staticmethod(
                lambda: ["~/watch.txt", "", None, "  ", "/tmp/keep.txt"]
            )
        },
    )()

    result = security_monitoring_controller._integrity_watch_files_set(app)

    assert "/tmp/keep.txt" in result
    assert (
        security_monitoring_controller.os.path.abspath(
            security_monitoring_controller.os.path.expanduser("~/watch.txt")
        )
        in result
    )
    assert len(result) == 2


def test_integrity_watch_files_set_returns_empty_on_exception():
    app = type(
        "DummyApp",
        (),
        {
            "_integrity_watch_files": staticmethod(
                lambda: (_ for _ in ()).throw(OSError("boom"))
            )
        },
    )()

    assert security_monitoring_controller._integrity_watch_files_set(app) == set()


def test_integrity_normalized_path_expands_user_and_makes_absolute(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "expanduser",
        lambda path: path.replace("~", "/home/test"),
    )
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "abspath",
        lambda path: f"/abs/{path.lstrip('/')}",
    )

    assert security_monitoring_controller._integrity_normalized_path("~/watch.txt") == (
        "/abs/home/test/watch.txt"
    )


def test_integrity_normalized_path_preserves_already_absolute_path(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "expanduser",
        lambda path: path,
    )
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "abspath",
        lambda path: path,
    )

    assert (
        security_monitoring_controller._integrity_normalized_path("/tmp/watch.txt")
        == "/tmp/watch.txt"
    )


def test_integrity_path_allowed_rejects_paths_outside_watch_set(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "security_integrity_ignore_path",
        lambda *_args: False,
    )

    assert not security_monitoring_controller._integrity_path_allowed(
        object(),
        "/tmp/other.txt",
        {"/tmp/keep.txt"},
    )


def test_integrity_path_allowed_rejects_ignored_watch_paths(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "security_integrity_ignore_path",
        lambda _app, path: path == "/tmp/keep.txt",
    )

    assert not security_monitoring_controller._integrity_path_allowed(
        object(),
        "/tmp/keep.txt",
        {"/tmp/keep.txt"},
    )


def test_sanitize_integrity_entry_keeps_relative_paths_as_is():
    entry = {"sha": "abc"}

    assert security_monitoring_controller._sanitize_integrity_entry(
        object(),
        " relative.txt ",
        entry,
        set(),
    ) == ("relative.txt", entry)


def test_sanitize_integrity_entry_skips_disallowed_absolute_paths(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_integrity_normalized_path",
        lambda path: path,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_integrity_path_allowed",
        lambda *_args: False,
    )

    assert (
        security_monitoring_controller._sanitize_integrity_entry(
            object(),
            "/tmp/blocked.txt",
            {"sha": "abc"},
            {"/tmp/blocked.txt"},
        )
        is None
    )


def test_integrity_entries_differ_detects_sha_size_or_mtime_changes():
    base = {"sha": "a", "size": 1, "mtime": 10.0}

    assert security_monitoring_controller._integrity_entries_differ(
        base, {"sha": "b", "size": 1, "mtime": 10.0}
    )
    assert security_monitoring_controller._integrity_entries_differ(
        base, {"sha": "a", "size": 2, "mtime": 10.0}
    )
    assert security_monitoring_controller._integrity_entries_differ(
        base, {"sha": "a", "size": 1, "mtime": 10.1}
    )


def test_integrity_entries_differ_ignores_tiny_mtime_deltas():
    assert not security_monitoring_controller._integrity_entries_differ(
        {"sha": "a", "size": 1, "mtime": 10.0},
        {"sha": "a", "size": 1, "mtime": 10.0000005},
    )


def test_append_modified_integrity_event_appends_when_entry_changed(monkeypatch):
    events = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_integrity_entry",
        lambda mapping, _path: (
            {"old": True} if mapping == "baseline" else {"new": True}
        ),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_integrity_entries_differ",
        lambda old, cur: old == {"old": True} and cur == {"new": True},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_integrity_change_event",
        lambda sink, _app, kind, path, cur: sink.append((kind, path, cur)),
    )

    security_monitoring_controller._append_modified_integrity_event(
        events,
        object(),
        "baseline",
        "current",
        "/tmp/watch.txt",
    )

    assert events == [("FILE MODIFIED", "/tmp/watch.txt", {"new": True})]


def test_append_modified_integrity_event_skips_missing_or_unchanged_entries(
    monkeypatch,
):
    events = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_integrity_entry",
        lambda mapping, _path: {} if mapping == "baseline" else {"new": True},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_integrity_change_event",
        lambda sink, *_args: sink.append("unexpected"),
    )

    security_monitoring_controller._append_modified_integrity_event(
        events,
        object(),
        "baseline",
        "current",
        "/tmp/watch.txt",
    )

    assert events == []


def test_append_integrity_event_for_path_uses_entry_from_mapping(monkeypatch):
    events = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_integrity_entry",
        lambda mapping, path: {"mapping": mapping, "path": path},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_integrity_change_event",
        lambda sink, _app, kind, path, entry: sink.append((kind, path, entry)),
    )

    security_monitoring_controller._append_integrity_event_for_path(
        events,
        object(),
        {"watched.txt": {"sha": "abc"}},
        "FILE NEW",
        "watched.txt",
    )

    assert events == [
        (
            "FILE NEW",
            "watched.txt",
            {"mapping": {"watched.txt": {"sha": "abc"}}, "path": "watched.txt"},
        )
    ]


def test_append_integrity_event_for_path_passes_empty_entry_through(monkeypatch):
    events = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_integrity_entry",
        lambda _mapping, _path: {},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_integrity_change_event",
        lambda sink, _app, kind, path, entry: sink.append((kind, path, entry)),
    )

    security_monitoring_controller._append_integrity_event_for_path(
        events,
        object(),
        {},
        "FILE DELETED",
        "missing.txt",
    )

    assert events == [("FILE DELETED", "missing.txt", {})]


def test_finish_scan_integrity_changes_stores_current_baseline_and_returns_events(
    monkeypatch,
):
    calls = []
    app = object()
    current = {"watched.txt": {"sha": "abc"}}
    events = [{"type": "FILE NEW"}]

    monkeypatch.setattr(
        security_monitoring_controller,
        "_store_integrity_baseline",
        lambda current_app, baseline: calls.append((current_app, baseline)),
    )

    assert (
        security_monitoring_controller._finish_scan_integrity_changes(
            app,
            current,
            events,
        )
        is events
    )
    assert calls == [(app, current)]


def test_finish_scan_integrity_changes_preserves_empty_event_list(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_store_integrity_baseline",
        lambda *_args: None,
    )

    events = []

    assert (
        security_monitoring_controller._finish_scan_integrity_changes(
            object(),
            {},
            events,
        )
        is events
    )


def test_device_paths_in_returns_filtered_joined_paths(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path, "isdir", lambda _p: True
    )
    monkeypatch.setattr(
        security_monitoring_controller.os,
        "listdir",
        lambda _p: ["event0", "event1", "note.txt"],
    )

    assert security_monitoring_controller._device_paths_in(
        "/dev/input",
        lambda path: path.endswith("event0") or path.endswith("event1"),
    ) == [
        "/dev/input/event0",
        "/dev/input/event1",
    ]


def test_device_paths_in_returns_empty_on_directory_error(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path, "isdir", lambda _p: True
    )
    monkeypatch.setattr(
        security_monitoring_controller.os,
        "listdir",
        lambda _p: (_ for _ in ()).throw(OSError("boom")),
    )

    assert (
        security_monitoring_controller._device_paths_in(
            "/dev/input",
            lambda _path: True,
        )
        == []
    )


def test_sorted_device_watch_paths_sorts_and_deduplicates_entries():
    assert security_monitoring_controller._sorted_device_watch_paths(
        ["/b", "/a", "/b"]
    ) == ["/a", "/b"]


def test_sorted_device_watch_paths_handles_empty_values():
    assert security_monitoring_controller._sorted_device_watch_paths([]) == []
    assert security_monitoring_controller._sorted_device_watch_paths(None) == []


def test_device_input_watch_paths_reads_dev_input_entries(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_paths_in",
        lambda directory, exists_fn: calls.append((directory, exists_fn))
        or ["/dev/input/event0"],
    )

    assert security_monitoring_controller._device_input_watch_paths() == [
        "/dev/input/event0"
    ]
    assert calls == [("/dev/input", security_monitoring_controller.os.path.exists)]


def test_device_input_watch_paths_preserves_empty_results(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_paths_in",
        lambda _directory, _exists_fn: [],
    )

    assert security_monitoring_controller._device_input_watch_paths() == []


def test_device_sysfs_watch_paths_reads_sys_class_input_entries(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_paths_in",
        lambda directory, exists_fn: calls.append((directory, exists_fn))
        or ["/sys/class/input/mouse0"],
    )

    assert security_monitoring_controller._device_sysfs_watch_paths() == [
        "/sys/class/input/mouse0"
    ]
    assert calls == [
        ("/sys/class/input", security_monitoring_controller.os.path.islink)
    ]


def test_device_sysfs_watch_paths_preserves_empty_results(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_paths_in",
        lambda _directory, _exists_fn: [],
    )

    assert security_monitoring_controller._device_sysfs_watch_paths() == []


def test_collected_device_watch_paths_combines_both_sources(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_paths_in",
        lambda directory, _exists_fn: {
            "/dev/input": ["/dev/input/event0"],
            "/sys/class/input": ["/sys/class/input/mouse0"],
        }[directory],
    )

    assert security_monitoring_controller._collected_device_watch_paths() == [
        "/dev/input/event0",
        "/sys/class/input/mouse0",
    ]


def test_collected_device_watch_paths_handles_empty_sources(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_paths_in",
        lambda _directory, _exists_fn: [],
    )

    assert security_monitoring_controller._collected_device_watch_paths() == []


def test_append_device_event_for_path_uses_device_type_from_mapping(monkeypatch):
    events = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_type",
        lambda mapping, path: {"mapping": mapping, "path": path},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_device_change_event",
        lambda sink, _app, kind, change, path, device_type: sink.append(
            (kind, change, path, device_type)
        ),
    )

    security_monitoring_controller._append_device_event_for_path(
        events,
        object(),
        {"/dev/input/event0": "input-event"},
        "DEVICE NEW",
        "new",
        "/dev/input/event0",
    )

    assert events == [
        (
            "DEVICE NEW",
            "new",
            "/dev/input/event0",
            {
                "mapping": {"/dev/input/event0": "input-event"},
                "path": "/dev/input/event0",
            },
        )
    ]


def test_append_device_event_for_path_passes_default_device_type_through(monkeypatch):
    events = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_type",
        lambda _mapping, _path: "unknown",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_device_change_event",
        lambda sink, _app, kind, change, path, device_type: sink.append(
            (kind, change, path, device_type)
        ),
    )

    security_monitoring_controller._append_device_event_for_path(
        events,
        object(),
        {},
        "DEVICE REMOVED",
        "removed",
        "/dev/input/event9",
    )

    assert events == [("DEVICE REMOVED", "removed", "/dev/input/event9", "unknown")]


def test_append_device_events_for_paths_sorts_and_forwards_each_path(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_device_event_for_path",
        lambda events, app, mapping, kind, change, path: calls.append(
            (events, app, mapping, kind, change, path)
        ),
    )

    events = []
    app = object()
    mapping = {"a": "type"}

    security_monitoring_controller._append_device_events_for_paths(
        events,
        app,
        mapping,
        "DEVICE NEW",
        "new",
        {"/dev/input/event2", "/dev/input/event1"},
    )

    assert calls == [
        (events, app, mapping, "DEVICE NEW", "new", "/dev/input/event1"),
        (events, app, mapping, "DEVICE NEW", "new", "/dev/input/event2"),
    ]


def test_append_device_events_for_paths_handles_empty_paths(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_device_event_for_path",
        lambda *_args: calls.append("called"),
    )

    security_monitoring_controller._append_device_events_for_paths(
        [],
        object(),
        {},
        "DEVICE REMOVED",
        "removed",
        [],
    )

    assert calls == []


def test_append_device_change_events_delegates_added_and_removed_paths(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_device_events_for_paths",
        lambda events, app, mapping, kind, change, paths: calls.append(
            (events, app, mapping, kind, change, paths)
        ),
    )

    events = []
    app = object()
    current = {"new": "state"}
    baseline = {"old": "state"}

    security_monitoring_controller._append_device_change_events(
        events,
        app,
        current,
        baseline,
        {"/dev/input/event2"},
        {"/dev/input/event1"},
    )

    assert calls == [
        (events, app, current, "DEVICE NEW", "new", {"/dev/input/event2"}),
        (events, app, baseline, "DEVICE REMOVED", "removed", {"/dev/input/event1"}),
    ]


def test_append_device_change_events_handles_empty_added_and_removed_paths(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_device_events_for_paths",
        lambda *_args: calls.append("called"),
    )

    security_monitoring_controller._append_device_change_events(
        [],
        object(),
        {},
        {},
        set(),
        set(),
    )

    assert calls == ["called", "called"]


def test_device_change_path_sets_returns_added_and_removed_paths():
    assert security_monitoring_controller._device_change_path_sets(
        {"/dev/input/event0": "old", "/dev/input/event1": "same"},
        {"/dev/input/event1": "same", "/dev/input/event2": "new"},
    ) == (
        {"/dev/input/event0", "/dev/input/event1"},
        {"/dev/input/event1", "/dev/input/event2"},
        {"/dev/input/event2"},
        {"/dev/input/event0"},
    )


def test_device_change_path_sets_handles_empty_mappings():
    assert security_monitoring_controller._device_change_path_sets(None, {}) == (
        set(),
        set(),
        set(),
        set(),
    )


def test_device_scan_context_returns_current_baseline_and_diff_sets(monkeypatch):
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_current_device_state",
        lambda current_app: {"/dev/input/event1": "same", "/dev/input/event2": "new"},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_baseline",
        lambda current_app: {"/dev/input/event0": "old", "/dev/input/event1": "same"},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_change_path_sets",
        lambda baseline, current: (
            set(baseline),
            set(current),
            {"/dev/input/event2"},
            {"/dev/input/event0"},
        ),
    )

    assert security_monitoring_controller._device_scan_context(app) == (
        {"/dev/input/event1": "same", "/dev/input/event2": "new"},
        {"/dev/input/event0": "old", "/dev/input/event1": "same"},
        {"/dev/input/event2"},
        {"/dev/input/event0"},
    )


def test_device_scan_context_handles_empty_current_and_baseline(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_current_device_state",
        lambda _app: {},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_baseline",
        lambda _app: {},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_change_path_sets",
        lambda baseline, current: (set(), set(), set(), set()),
    )

    assert security_monitoring_controller._device_scan_context(object()) == (
        {},
        {},
        set(),
        set(),
    )


def test_append_unique_security_events_appends_only_new_keys():
    app = type(
        "DummyApp",
        (),
        {
            "security_event_keys": {"keep"},
            "security_events": [{"key": "keep"}],
        },
    )()

    security_monitoring_controller._append_unique_security_events(
        app,
        [{"key": "keep"}, {"key": "new"}],
    )

    assert app.security_event_keys == {"keep", "new"}
    assert app.security_events == [{"key": "keep"}, {"key": "new"}]


def test_append_unique_security_events_handles_empty_event_list():
    app = type(
        "DummyApp",
        (),
        {"security_event_keys": set(), "security_events": []},
    )()

    security_monitoring_controller._append_unique_security_events(app, [])

    assert app.security_event_keys == set()
    assert app.security_events == []


def test_security_scan_alert_state_prioritizes_portscan_alert():
    assert security_monitoring_controller._security_scan_alert_state(
        [{"key": "ufw"}],
        [{"key": "scan"}],
        [],
        [],
        [],
    ) == ("red", "Portscan-Verdacht")


def test_security_scan_alert_state_returns_yellow_for_custom_events():
    assert security_monitoring_controller._security_scan_alert_state(
        [],
        [],
        [{"key": "file"}],
        [],
        [],
    ) == ("yellow", "Datei-/Geräte-Änderung")


def test_security_scan_orchestration_collects_all_event_groups(monkeypatch):
    app = type(
        "DummyApp",
        (),
        {
            "scan_integrity_changes": lambda self: [{"key": "file"}],
            "scan_device_changes": lambda self: [{"key": "device"}],
            "scan_input_access_changes": lambda self: [{"key": "input"}],
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_scan_ufw_security_events",
        lambda current_app: [{"key": "ufw"}],
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_scan_portscan_findings",
        lambda current_app: [{"key": "scan"}],
    )

    assert security_monitoring_controller._security_scan_orchestration(app) == (
        [{"key": "ufw"}],
        [{"key": "scan"}],
        [{"key": "file"}],
        [{"key": "device"}],
        [{"key": "input"}],
    )


def test_security_scan_orchestration_preserves_empty_groups(monkeypatch):
    app = type(
        "DummyApp",
        (),
        {
            "scan_integrity_changes": lambda self: [],
            "scan_device_changes": lambda self: [],
            "scan_input_access_changes": lambda self: [],
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_scan_ufw_security_events",
        lambda current_app: [],
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_scan_portscan_findings",
        lambda current_app: [],
    )

    assert security_monitoring_controller._security_scan_orchestration(app) == (
        [],
        [],
        [],
        [],
        [],
    )


def test_log_harmless_rst_events_logs_first_five_and_summary():
    logs = []
    app = type("DummyApp", (), {"log": logs.append})()
    events = [{"summary": f"rst-{idx}"} for idx in range(6)]

    security_monitoring_controller._log_harmless_rst_events(app, events)

    assert logs == [
        "rst-0",
        "rst-1",
        "rst-2",
        "rst-3",
        "rst-4",
        "[INFO] harmless return traffic (RST): 6 Ereignisse",
    ]


def test_log_harmless_rst_events_uses_default_message_when_summary_missing():
    logs = []
    app = type("DummyApp", (), {"log": logs.append})()

    security_monitoring_controller._log_harmless_rst_events(app, [{"type": "RST"}])

    assert logs == ["[INFO] harmless return traffic (RST)"]


def test_finish_security_poll_cycle_refreshes_status_and_reschedules(monkeypatch):
    calls = []
    after_calls = []

    app = type(
        "DummyApp",
        (),
        {
            "security_monitoring": True,
            "security_scan_running": True,
            "_security_poll_async": object(),
            "_security_update_status": lambda self, color: calls.append(
                ("status", color)
            ),
            "after": lambda self, delay, callback: after_calls.append(
                (delay, callback)
            ),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_security_table_callback_safe",
        lambda current_app: calls.append(("refresh", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_log_harmless_rst_events",
        lambda current_app, events: calls.append(("rst", events)),
    )

    security_monitoring_controller._finish_security_poll_cycle(
        app, "yellow", [{"summary": "rst"}]
    )

    assert calls == [
        ("refresh", app),
        ("rst", [{"summary": "rst"}]),
        ("status", "yellow"),
    ]
    assert app.security_scan_running is False
    assert after_calls == [(5000, app._security_poll_async)]


def test_finish_security_scan_now_refreshes_ui_and_logs_new_events(monkeypatch):
    after_calls = []
    logs = []
    calls = []

    app = type(
        "DummyApp",
        (),
        {
            "after": lambda self, delay, callback: after_calls.append(
                (delay, callback)
            ),
            "log_safe": logs.append,
            "_refresh_security_table_safe": lambda self: calls.append("refresh"),
            "_security_update_status": lambda self, color: calls.append(
                ("status", color)
            ),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_unique_security_events",
        lambda current_app, events: calls.append(("append", events)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_app_callback",
        lambda current_app, name: (
            (lambda: None) if name == "refresh_connected_device_table" else None
        ),
    )

    security_monitoring_controller._finish_security_scan_now(
        app,
        [{"key": "new"}],
        "green",
    )

    assert ("append", [{"key": "new"}]) in calls
    assert "refresh" in calls
    assert logs == ["Security-Scan: 1 neue Events"]
    assert len(after_calls) == 2
    assert after_calls[0][0] == 0
    assert after_calls[1][0] == 0


def test_refresh_security_table_state_sets_meta_and_visible_events(monkeypatch):
    app = type(
        "DummyApp",
        (),
        {
            "security_table_row_meta": {"old": {"kind": "event"}},
            "security_visible_events": [{"type": "old"}],
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "security_filtered_events",
        lambda current_app: [{"type": "new"}],
    )

    visible = security_monitoring_controller._refresh_security_table_state(app)

    assert visible == [{"type": "new"}]
    assert app.security_visible_events == [{"type": "new"}]
    assert app.security_table_row_meta == {}


def test_append_security_aggregate_rows_inserts_only_positive_all_filter_rows():
    class DummyTable:
        def __init__(self):
            self.insert_calls = []

        def insert(self, parent, where, iid=None, values=()):
            self.insert_calls.append((parent, where, iid, values))

    app = type(
        "DummyApp",
        (),
        {
            "security_filter_mode": "all",
            "security_aggregated": {"DNS": 2, "EMPTY": 0},
            "security_table_row_meta": {},
        },
    )()
    table = DummyTable()

    security_monitoring_controller._append_security_aggregate_rows(app, table)

    assert table.insert_calls == [
        (
            "",
            "end",
            "agg-0",
            ("-", "Aggregiert DNS", "-", "2", "-", "INFO", "AGGREGATED"),
        )
    ]
    assert app.security_table_row_meta == {
        "agg-0": {"kind": "aggregate", "raw": "Aggregierte interne Events: DNS = 2"}
    }


def test_append_security_event_rows_inserts_rows_and_meta():
    class DummyTable:
        def __init__(self):
            self.insert_calls = []

        def insert(self, parent, where, iid=None, values=()):
            self.insert_calls.append((parent, where, iid, values))

    app = type("DummyApp", (), {"security_table_row_meta": {}})()
    table = DummyTable()
    events = [
        {
            "time": "2026-06-06 12:00:00",
            "type": "UFW BLOCK",
            "src": "1.2.3.4",
            "port": "22",
            "proto": "TCP",
            "level": "WARN",
            "action": "BLOCK",
        }
    ]

    security_monitoring_controller._append_security_event_rows(app, table, events)

    assert table.insert_calls == [
        (
            "",
            "end",
            "sec-0",
            (
                "2026-06-06 12:00:00",
                "UFW BLOCK",
                "1.2.3.4",
                "22",
                "TCP",
                "WARN",
                "BLOCK",
            ),
        )
    ]
    assert app.security_table_row_meta == {"sec-0": {"kind": "event", "index": 0}}


def test_refresh_security_table_view_clears_then_appends_and_updates_stats(monkeypatch):
    calls = []

    class DummyTable:
        def get_children(self):
            return ("old-0", "old-1")

        def delete(self, item):
            calls.append(("delete", item))

    app = type("DummyApp", (), {"security_table": DummyTable()})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_security_aggregate_rows",
        lambda current_app, table: calls.append(("aggregates", current_app, table)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_security_event_rows",
        lambda current_app, table, visible_events: calls.append(
            ("events", current_app, table, visible_events)
        ),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "security_update_stats_view",
        lambda current_app: calls.append(("stats", current_app)),
    )

    security_monitoring_controller._refresh_security_table_view(
        app,
        [{"type": "UFW BLOCK"}],
    )

    assert calls == [
        ("delete", "old-0"),
        ("delete", "old-1"),
        ("aggregates", app, app.security_table),
        ("events", app, app.security_table, [{"type": "UFW BLOCK"}]),
        ("stats", app),
    ]


def test_mark_security_scan_running_sets_running_flag():
    app = type("DummyApp", (), {"security_scan_running": False})()

    assert security_monitoring_controller._mark_security_scan_running(app) is True
    assert app.security_scan_running is True


def test_mark_security_scan_running_rejects_existing_run():
    app = type("DummyApp", (), {"security_scan_running": True})()

    assert security_monitoring_controller._mark_security_scan_running(app) is False
    assert app.security_scan_running is True


def test_run_security_poll_job_appends_events_updates_alarm_and_schedules_finish(
    monkeypatch,
):
    after_calls = []
    finish_calls = []
    app = type(
        "DummyApp",
        (),
        {
            "security_events": [],
            "security_event_keys": set(),
            "security_last_alarm": "–",
            "after": lambda self, delay, callback: after_calls.append(
                (delay, callback)
            ),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_scan_orchestration",
        lambda current_app: (
            [{"key": "ufw", "type": "HARMLESS RETURN TRAFFIC"}],
            [{"key": "scan"}],
            [],
            [],
            [],
        ),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_unique_security_events",
        lambda current_app, events: current_app.security_events.extend(events),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_scan_alert_state",
        lambda *_args: ("red", "Portscan-Verdacht"),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_finish_security_poll_cycle",
        lambda current_app, color, harmless_rst_events: finish_calls.append(
            (current_app, color, harmless_rst_events)
        ),
    )

    security_monitoring_controller._run_security_poll_job(app)

    assert app.security_last_alarm == "Portscan-Verdacht"
    assert after_calls and after_calls[0][0] == 0
    after_calls[0][1]()
    assert finish_calls == [
        (app, "red", [{"key": "ufw", "type": "HARMLESS RETURN TRAFFIC"}])
    ]


def test_run_security_poll_job_preserves_alarm_when_no_new_alarm(monkeypatch):
    after_calls = []
    finish_calls = []
    app = type(
        "DummyApp",
        (),
        {
            "security_events": [],
            "security_event_keys": set(),
            "security_last_alarm": "Bestehend",
            "after": lambda self, delay, callback: after_calls.append(
                (delay, callback)
            ),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_scan_orchestration",
        lambda current_app: ([], [], [], [], []),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_unique_security_events",
        lambda current_app, events: None,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_scan_alert_state",
        lambda *_args: ("green", None),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_finish_security_poll_cycle",
        lambda current_app, color, harmless_rst_events: finish_calls.append(
            (current_app, color, harmless_rst_events)
        ),
    )

    security_monitoring_controller._run_security_poll_job(app)

    assert app.security_last_alarm == "Bestehend"
    after_calls[0][1]()
    assert finish_calls == [(app, "green", [])]


def test_ensure_security_log_level_uses_refresh_when_available(monkeypatch):
    app = type("DummyApp", (), {"log": lambda self, message: None})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_security_log_level_safe",
        lambda current_app, log_failures: True,
    )

    security_monitoring_controller._ensure_security_log_level(app)

    assert not hasattr(app, "security_log_level")


def test_ensure_security_log_level_sets_fallback_and_logs(monkeypatch):
    logs = []
    app = type(
        "DummyApp",
        (),
        {
            "log": logs.append,
            "tr": staticmethod(lambda _key, text: text),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_security_log_level_safe",
        lambda current_app, log_failures: False,
    )

    security_monitoring_controller._ensure_security_log_level(app)

    assert app.security_log_level == "–"
    assert logs == ["Security: Log-Level-Abfrage nicht verfügbar, Fallback '–'."]


def test_finish_security_start_monitoring_logs_updates_status_and_polls():
    calls = []
    app = type(
        "DummyApp",
        (),
        {
            "log": calls.append,
            "tr": staticmethod(lambda _key, text: text),
            "_security_update_status": lambda self, color: calls.append(
                ("status", color)
            ),
            "_security_poll_async": lambda self: calls.append("poll"),
        },
    )()

    security_monitoring_controller._finish_security_start_monitoring(app)

    assert calls == [
        "Security Monitoring gestartet.",
        ("status", "green"),
        "poll",
    ]


def test_finish_security_input_access_scan_appends_logs_and_refreshes(monkeypatch):
    calls = []
    logs = []
    app = type(
        "DummyApp",
        (),
        {
            "log_safe": logs.append,
            "_refresh_security_table_safe": lambda self: calls.append("refresh"),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_unique_security_events",
        lambda current_app, events: calls.append(("append", events)),
    )

    security_monitoring_controller._finish_security_input_access_scan(
        app,
        [{"key": "input"}],
    )

    assert calls == [("append", [{"key": "input"}]), "refresh"]
    assert logs == ["Input-Zugriffscheck: 1 neue Events"]


def test_begin_security_scan_returns_false_and_logs_when_already_running():
    logs = []
    app = type(
        "DummyApp",
        (),
        {"security_scan_running": True, "log": logs.append},
    )()

    assert security_monitoring_controller._begin_security_scan(app) is False
    assert logs == ["Security-Scan läuft bereits."]


def test_begin_security_scan_sets_running_flag_for_new_scan():
    app = type(
        "DummyApp", (), {"security_scan_running": False, "log": lambda *_: None}
    )()

    assert security_monitoring_controller._begin_security_scan(app) is True
    assert app.security_scan_running is True


def test_start_security_scan_thread_starts_daemon_thread(monkeypatch):
    calls = []

    class DummyThread:
        def __init__(self, target, daemon):
            calls.append(("init", target, daemon))
            self.target = target

        def start(self):
            calls.append(("start", self.target))

    monkeypatch.setattr(security_monitoring_controller.threading, "Thread", DummyThread)

    def job():
        return None

    security_monitoring_controller._start_security_scan_thread(job)

    assert calls == [("init", job, True), ("start", job)]


def test_run_security_input_access_scan_job_logs_error_and_finishes(monkeypatch):
    logs = []
    calls = []
    app = type(
        "DummyApp",
        (),
        {
            "security_scan_running": True,
            "scan_input_access_changes": lambda self: (_ for _ in ()).throw(
                RuntimeError("boom")
            ),
            "log_safe": logs.append,
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_finish_security_input_access_scan",
        lambda current_app, events: calls.append((current_app, events)),
    )

    security_monitoring_controller._run_security_input_access_scan_job(app)

    assert logs == ["Input-Zugriffscheck fehlgeschlagen: boom"]
    assert app.security_scan_running is False
    assert calls == [(app, [])]


def test_finish_scan_device_changes_stores_current_baseline_and_returns_events(
    monkeypatch,
):
    calls = []
    app = object()
    current = {"/dev/input/event0": "input-event"}
    events = [{"type": "DEVICE NEW"}]

    monkeypatch.setattr(
        security_monitoring_controller,
        "_store_device_baseline",
        lambda current_app, baseline: calls.append((current_app, baseline)),
    )

    assert (
        security_monitoring_controller._finish_scan_device_changes(
            app,
            current,
            events,
        )
        is events
    )
    assert calls == [(app, current)]


def test_finish_scan_device_changes_preserves_empty_event_list(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_store_device_baseline",
        lambda *_args: None,
    )

    events = []

    assert (
        security_monitoring_controller._finish_scan_device_changes(
            object(),
            {},
            events,
        )
        is events
    )


def test_device_name_is_input_event_detects_event_prefix():
    assert security_monitoring_controller._device_name_is_input_event("event0")
    assert security_monitoring_controller._device_name_is_input_event("event-kbd")


def test_device_name_is_input_event_rejects_non_event_names():
    assert not security_monitoring_controller._device_name_is_input_event("mouse0")
    assert not security_monitoring_controller._device_name_is_input_event("keyboard0")


def test_device_name_is_mouse_detects_mouse_substring():
    assert security_monitoring_controller._device_name_is_mouse("mouse0")
    assert security_monitoring_controller._device_name_is_mouse("usb-mouse-device")


def test_device_name_is_mouse_rejects_non_mouse_names():
    assert not security_monitoring_controller._device_name_is_mouse("event0")
    assert not security_monitoring_controller._device_name_is_mouse("keyboard0")


def test_device_name_is_keyboard_detects_keyboard_markers():
    assert security_monitoring_controller._device_name_is_keyboard("kbd0")
    assert security_monitoring_controller._device_name_is_keyboard("usb-keyboard")


def test_device_name_is_keyboard_rejects_non_keyboard_names():
    assert not security_monitoring_controller._device_name_is_keyboard("event0")
    assert not security_monitoring_controller._device_name_is_keyboard("mouse0")


def test_device_type_for_name_detects_known_device_markers():
    assert (
        security_monitoring_controller._device_type_for_name("event0") == "input-event"
    )
    assert (
        security_monitoring_controller._device_type_for_name("usb-keyboard")
        == "keyboard"
    )


def test_device_type_for_name_falls_back_to_hid():
    assert security_monitoring_controller._device_type_for_name("mouse0") == "mouse"
    assert security_monitoring_controller._device_type_for_name("hidraw0") == "hid"


def test_load_security_baseline_prunes_ignored_and_stale_integrity_entries(tmp_path):
    config_dir = tmp_path / "config"
    state_dir = tmp_path / "state"
    config_dir.mkdir()
    state_dir.mkdir()

    hdd_path = config_dir / "netmon_hdd_slots.json"
    app_path = tmp_path / "watch_app.py"
    desktop_link = tmp_path / "Verknuepfung mit netmon_app.py"
    baseline_path = state_dir / "security_baseline.json"

    hdd_path.write_text('{"slots": []}\n', encoding="utf-8")
    app_path.write_text("print('ok')\n", encoding="utf-8")
    desktop_link.write_text("shortcut\n", encoding="utf-8")

    baseline_path.write_text(
        json.dumps(
            {
                "integrity": {
                    str(hdd_path): {"sha": "a", "size": 1, "mtime": 1.0},
                    str(desktop_link): {"sha": "b", "size": 1, "mtime": 1.0},
                    str(app_path): {"sha": "c", "size": 1, "mtime": 1.0},
                },
                "device": {},
                "input_access": {},
            }
        ),
        encoding="utf-8",
    )

    class DummyApp:
        netmon_config_dir = str(config_dir)
        netmon_state_dir = str(state_dir)
        hdd_config_path = str(hdd_path)
        security_baseline_path = str(baseline_path)
        integrity_baseline = {}
        device_baseline = {}
        input_access_baseline = {}
        tr = staticmethod(lambda _key, text: text)

        def _integrity_watch_files(self):
            return [str(hdd_path), str(app_path)]

        def log(self, message):
            logs.append(message)

    logs = []
    app = DummyApp()

    assert security_monitoring_controller.load_security_baseline(app) is True
    assert app.integrity_baseline == {
        str(app_path): {"sha": "c", "size": 1, "mtime": 1.0}
    }
    assert logs == ["Security: Baseline bereinigt (2 NetMon-/Alt-Einträge entfernt)."]


def test_restore_security_baselines_restores_sanitized_state(monkeypatch):
    app = type("DummyApp", (), {})()
    data = {
        "integrity": {"watched.txt": {"sha": "abc"}},
        "device": {"/dev/input/event0": "input-event"},
        "input_access": {"/dev/input/event0": {"123": "python"}},
    }
    captured = {}

    monkeypatch.setattr(
        security_monitoring_controller,
        "sanitize_integrity_baseline",
        lambda restore_app, raw_integrity: captured.setdefault(
            "sanitize_args", (restore_app, raw_integrity)
        )
        and {"clean.txt": {"sha": "clean"}},
    )

    raw_integrity = security_monitoring_controller._restore_security_baselines(
        app, data
    )

    assert raw_integrity == {"watched.txt": {"sha": "abc"}}
    assert captured["sanitize_args"] == (
        app,
        {"watched.txt": {"sha": "abc"}},
    )
    assert app.integrity_baseline == {"clean.txt": {"sha": "clean"}}
    assert app.device_baseline == {"/dev/input/event0": "input-event"}
    assert app.input_access_baseline == {"/dev/input/event0": {"123": "python"}}


def test_restore_security_baselines_uses_safe_defaults(monkeypatch):
    app = type("DummyApp", (), {})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "sanitize_integrity_baseline",
        lambda _app, raw_integrity: {"raw": raw_integrity},
    )

    raw_integrity = security_monitoring_controller._restore_security_baselines(app, {})

    assert raw_integrity == {}
    assert app.integrity_baseline == {"raw": {}}
    assert app.device_baseline == {}
    assert app.input_access_baseline == {}


def test_security_baseline_pruned_log_message_formats_count():
    class DummyApp:
        @staticmethod
        def tr(_key, text):
            return text

    assert (
        security_monitoring_controller._security_baseline_pruned_log_message(
            DummyApp(), 3
        )
        == "Security: Baseline bereinigt (3 NetMon-/Alt-Einträge entfernt)."
    )


def test_security_baseline_pruned_log_message_uses_translation_result():
    class DummyApp:
        @staticmethod
        def tr(_key, _text):
            return "Bereinigt: {count}"

    assert (
        security_monitoring_controller._security_baseline_pruned_log_message(
            DummyApp(), 5
        )
        == "Bereinigt: 5"
    )


def test_security_baseline_rebuilt_log_message_uses_default_text():
    class DummyApp:
        @staticmethod
        def tr(_key, text):
            return text

    assert (
        security_monitoring_controller._security_baseline_rebuilt_log_message(
            DummyApp()
        )
        == "Security: Baseline (File+Device+Input) neu erstellt."
    )


def test_security_baseline_rebuilt_log_message_uses_translation_result():
    class DummyApp:
        @staticmethod
        def tr(_key, _text):
            return "Neu aufgebaut"

    assert (
        security_monitoring_controller._security_baseline_rebuilt_log_message(
            DummyApp()
        )
        == "Neu aufgebaut"
    )


def test_run_security_baseline_build_runs_build_and_finish_steps(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_build_all_security_baselines",
        lambda current_app: calls.append(("build", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_finish_security_build_baseline",
        lambda current_app: calls.append(("finish", current_app)),
    )

    assert security_monitoring_controller._run_security_baseline_build(app) is None
    assert calls == [("build", app), ("finish", app)]


def test_finish_security_build_baseline_delegates_to_rebuild_followups(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_run_security_baseline_rebuild_followups",
        lambda current_app: calls.append(current_app),
    )

    assert security_monitoring_controller._finish_security_build_baseline(app) is None
    assert calls == [app]


def test_run_security_baseline_rebuild_followups_preserves_execution_order(
    monkeypatch,
):
    calls = []
    app = type("DummyApp", (), {"log": lambda self, message: calls.append(message)})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_save_security_baseline_callback_safe",
        lambda current_app: calls.append(("save", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_connected_devices_safe",
        lambda current_app: calls.append(("devices", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_rebuilt_log_message",
        lambda current_app: "rebuilt",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_security_table_callback_safe",
        lambda current_app: calls.append(("table", current_app)),
    )

    assert (
        security_monitoring_controller._run_security_baseline_rebuild_followups(app)
        is None
    )
    assert calls == [
        ("save", app),
        ("devices", app),
        "rebuilt",
        ("table", app),
    ]


def test_security_baseline_save_error_message_formats_error():
    assert (
        security_monitoring_controller._security_baseline_save_error_message("kaputt")
        == "Security-Baseline speichern fehlgeschlagen: kaputt"
    )


def test_security_baseline_save_error_message_accepts_exception():
    assert (
        security_monitoring_controller._security_baseline_save_error_message(
            RuntimeError("boom")
        )
        == "Security-Baseline speichern fehlgeschlagen: boom"
    )


def test_log_security_baseline_pruned_if_needed_logs_removed_entries(monkeypatch):
    calls = []
    app = type("DummyApp", (), {"integrity_baseline": {"keep.txt": {"sha": "x"}}})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_app_logger",
        lambda _app: calls.append,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_pruned_log_message",
        lambda _app, count: f"removed:{count}",
    )

    security_monitoring_controller._log_security_baseline_pruned_if_needed(
        app,
        {
            "keep.txt": {"sha": "x"},
            "gone.txt": {"sha": "y"},
            "old.txt": {"sha": "z"},
        },
    )

    assert calls == ["removed:2"]


def test_log_security_baseline_pruned_if_needed_skips_when_nothing_removed(
    monkeypatch,
):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_app_logger",
        lambda _app: lambda _message: (_ for _ in ()).throw(
            AssertionError("logger should not be called")
        ),
    )

    app = type(
        "DummyApp",
        (),
        {"integrity_baseline": {"keep.txt": {"sha": "x"}, "old.txt": {"sha": "z"}}},
    )()

    security_monitoring_controller._log_security_baseline_pruned_if_needed(
        app,
        {"keep.txt": {"sha": "x"}, "old.txt": {"sha": "z"}},
    )


def test_load_security_baseline_data_reads_json_from_file(tmp_path):
    path = tmp_path / "baseline.json"
    path.write_text('{"integrity": {"a": 1}}', encoding="utf-8")

    assert security_monitoring_controller._load_security_baseline_data(str(path)) == {
        "integrity": {"a": 1}
    }


def test_load_security_baseline_data_preserves_empty_mapping(tmp_path):
    path = tmp_path / "baseline.json"
    path.write_text("{}", encoding="utf-8")

    assert security_monitoring_controller._load_security_baseline_data(str(path)) == {}


def test_build_all_security_baselines_runs_all_builders_in_order():
    calls = []

    class DummyApp:
        def build_integrity_baseline(self):
            calls.append("integrity")

        def build_device_baseline(self):
            calls.append("device")

        def build_input_access_baseline(self):
            calls.append("input")

    security_monitoring_controller._build_all_security_baselines(DummyApp())

    assert calls == ["integrity", "device", "input"]


def test_build_all_security_baselines_runs_input_builder_last():
    calls = []

    class DummyApp:
        def build_integrity_baseline(self):
            calls.append("integrity")

        def build_device_baseline(self):
            calls.append("device")

        def build_input_access_baseline(self):
            calls.append("input")

    security_monitoring_controller._build_all_security_baselines(DummyApp())

    assert calls[-1] == "input"


def test_finish_security_build_baseline_runs_save_refresh_log_and_refresh(
    monkeypatch,
):
    calls = []
    app = type("DummyApp", (), {"log": lambda self, message: calls.append(message)})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_save_security_baseline_callback_safe",
        lambda _app: calls.append("save") or True,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_connected_devices_safe",
        lambda _app: calls.append("devices") or True,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_rebuilt_log_message",
        lambda _app: "rebuilt",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_security_table_callback_safe",
        lambda _app: calls.append("table") or True,
    )

    security_monitoring_controller._finish_security_build_baseline(app)

    assert calls == ["save", "devices", "rebuilt", "table"]


def test_finish_security_build_baseline_logs_even_without_callbacks(monkeypatch):
    calls = []
    app = type("DummyApp", (), {"log": lambda self, message: calls.append(message)})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_save_security_baseline_callback_safe",
        lambda _app: False,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_connected_devices_safe",
        lambda _app: False,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_rebuilt_log_message",
        lambda _app: "rebuilt",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_security_table_callback_safe",
        lambda _app: False,
    )

    security_monitoring_controller._finish_security_build_baseline(app)

    assert calls == ["rebuilt"]


def test_export_security_logs_counts_portscan_case_insensitively(tmp_path, monkeypatch):
    exported = {}

    def fake_open(path, mode="r", encoding=None):
        class CaptureFile:
            def __init__(self):
                self.parts = []

            def write(self, data):
                self.parts.append(data)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                exported["path"] = path
                exported["text"] = "".join(self.parts)
                return False

        return CaptureFile()

    monkeypatch.setattr(
        security_monitoring_controller,
        "security_export_dir",
        lambda: str(tmp_path),
    )
    monkeypatch.setattr("builtins.open", fake_open)

    class DummyApp:
        security_monitoring = False
        security_log_level = "-"
        security_last_alarm = "–"
        security_aggregated = {}
        security_events = [{"type": "Portscan-Verdacht", "raw": "demo"}]

        def tr(self, _key, default):
            return default

        def log(self, _message):
            pass

    security_monitoring_controller.export_security_logs(DummyApp())

    assert "Portscan-Verdacht: 1" in exported["text"]


def test_on_security_event_select_shows_aggregate_details():
    class DummyTable:
        def selection(self):
            return ("agg-0",)

    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    class DummyApp:
        security_table = DummyTable()
        security_detail = DummyDetail()
        security_visible_events = [{"raw": "ECHTES EVENT"}]
        security_table_row_meta = {
            "agg-0": {"kind": "aggregate", "raw": "Aggregierte interne Events: DNS = 2"}
        }

    app = DummyApp()
    security_monitoring_controller.on_security_event_select(app)

    assert app.security_detail.text == "Aggregierte interne Events: DNS = 2"


def test_on_security_event_select_shows_visible_event_details():
    class DummyTable:
        def selection(self):
            return ("sec-0",)

    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    class DummyApp:
        security_table = DummyTable()
        security_detail = DummyDetail()
        security_visible_events = [{"raw": "ECHTES EVENT"}]
        security_table_row_meta = {"sec-0": {"kind": "event", "index": 0}}

    app = DummyApp()
    security_monitoring_controller.on_security_event_select(app)

    assert app.security_detail.text == "ECHTES EVENT"


def test_show_selected_security_event_sets_detail_and_returns_true(monkeypatch):
    calls = []
    app = object()
    table = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_selected_security_event_text",
        lambda current_app, current_table: calls.append(
            ("text", current_app, current_table)
        )
        or "DETAIL",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_set_security_detail_text",
        lambda current_app, text: calls.append(("set", current_app, text)),
    )

    assert (
        security_monitoring_controller._show_selected_security_event(app, table) is True
    )
    assert calls == [("text", app, table), ("set", app, "DETAIL")]


def test_show_selected_security_event_returns_false_without_text(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_selected_security_event_text",
        lambda _app, _table: "",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_set_security_detail_text",
        lambda *_args: (_ for _ in ()).throw(AssertionError("should not set detail")),
    )

    assert (
        security_monitoring_controller._show_selected_security_event(
            object(),
            object(),
        )
        is False
    )


def test_selected_security_event_text_uses_selected_aggregate_row():
    class DummyTable:
        def selection(self):
            return ("agg-0",)

    app = type("DummyApp", (), {})()
    app.security_visible_events = [{"raw": "ECHTES EVENT"}]
    app.security_table_row_meta = {
        "agg-0": {"kind": "aggregate", "raw": "Aggregierte interne Events: DNS = 2"}
    }

    assert (
        security_monitoring_controller._selected_security_event_text(
            app,
            DummyTable(),
        )
        == "Aggregierte interne Events: DNS = 2"
    )


def test_selected_security_event_text_returns_empty_without_selection():
    class DummyTable:
        def selection(self):
            return ()

    app = type("DummyApp", (), {})()
    app.security_visible_events = [{"raw": "ECHTES EVENT"}]
    app.security_table_row_meta = {"sec-0": {"kind": "event", "index": 0}}

    assert (
        security_monitoring_controller._selected_security_event_text(
            app,
            DummyTable(),
        )
        == ""
    )


def test_selected_table_row_index_parses_expected_suffix():
    assert security_monitoring_controller._selected_table_row_index("sec-7") == 7
    assert security_monitoring_controller._selected_table_row_index("dev-0") == 0


def test_selected_table_row_index_returns_none_for_invalid_values():
    assert security_monitoring_controller._selected_table_row_index("") is None
    assert security_monitoring_controller._selected_table_row_index("broken") is None


def test_security_monitoring_log_message_maps_known_states():
    assert (
        security_monitoring_controller._security_monitoring_log_message(
            "already_running"
        )
        == "Security Monitoring läuft bereits."
    )
    assert (
        security_monitoring_controller._security_monitoring_log_message("started")
        == "Security Monitoring gestartet."
    )
    assert (
        security_monitoring_controller._security_monitoring_log_message("stopped")
        == "Security Monitoring gestoppt."
    )


def test_security_monitoring_log_message_uses_unknown_fallback():
    assert (
        security_monitoring_controller._security_monitoring_log_message("mystery")
        == "Security Monitoring unbekannt."
    )


def test_security_scan_log_message_maps_known_states():
    assert (
        security_monitoring_controller._security_scan_log_message("already_running")
        == "Security-Scan läuft bereits."
    )


def test_security_scan_log_message_uses_unknown_fallback():
    assert (
        security_monitoring_controller._security_scan_log_message("mystery")
        == "Security-Scan unbekannt."
    )


def test_security_monitoring_status_text_returns_aktiv_for_true():
    assert (
        security_monitoring_controller._security_monitoring_status_text(True) == "AKTIV"
    )


def test_security_monitoring_status_text_returns_aus_for_false():
    assert (
        security_monitoring_controller._security_monitoring_status_text(False) == "AUS"
    )


def test_security_status_text_formats_prefix_and_value():
    assert security_monitoring_controller._security_status_text("Logging", "LOW") == (
        "Logging: LOW"
    )


def test_security_status_text_preserves_numeric_values():
    assert security_monitoring_controller._security_status_text("Events", 3) == (
        "Events: 3"
    )


def test_security_header_lines_return_title_divider_and_blank_line():
    assert security_monitoring_controller._security_header_lines("Title", 4) == [
        "Title",
        "====",
        "",
    ]


def test_security_header_lines_clamp_negative_width_to_empty_divider():
    assert security_monitoring_controller._security_header_lines("Title", -1) == [
        "Title",
        "",
        "",
    ]


def test_security_event_field_returns_existing_value():
    assert (
        security_monitoring_controller._security_event_field(
            {"type": "UFW BLOCK"}, "type"
        )
        == "UFW BLOCK"
    )


def test_security_event_field_returns_safe_default():
    assert security_monitoring_controller._security_event_field({}, "type") == "-"


def test_security_event_summary_line_formats_expected_fields():
    assert security_monitoring_controller._security_event_summary_line(
        {
            "time": "2026-01-01 00:00:00",
            "type": "UFW BLOCK",
            "level": "L2 WARN",
            "src": "9.9.9.9",
            "port": "22",
            "proto": "TCP",
            "action": "BLOCK",
        }
    ) == (
        "- Zeit=2026-01-01 00:00:00; Typ=UFW BLOCK; Level=L2 WARN; "
        "Quelle=9.9.9.9; Port=22; Proto=TCP; Aktion=BLOCK"
    )


def test_security_event_summary_line_omits_proto_when_disabled():
    assert (
        security_monitoring_controller._security_event_summary_line(
            {"time": "2026-01-01", "type": "demo", "action": "ok"},
            include_proto=False,
        )
        == "- Zeit=2026-01-01; Typ=demo; Level=-; Quelle=-; Port=-; Aktion=ok"
    )


def test_security_export_event_table_line_formats_expected_fields():
    assert (
        security_monitoring_controller._security_export_event_table_line(
            {
                "time": "2026-01-01 00:00:00",
                "type": "UFW BLOCK",
                "src": "9.9.9.9",
                "port": "22",
                "proto": "TCP",
                "level": "L2 WARN",
                "action": "BLOCK",
            }
        )
        == "2026-01-01 00:00:00 | UFW BLOCK | 9.9.9.9 | 22 | TCP | L2 WARN | BLOCK\n"
    )


def test_security_export_event_table_line_uses_safe_defaults():
    assert (
        security_monitoring_controller._security_export_event_table_line({})
        == "- | - | - | - | - | - | -\n"
    )


def test_security_export_event_detail_header_line_formats_index_and_fields():
    assert (
        security_monitoring_controller._security_export_event_detail_header_line(
            3,
            {
                "time": "2026-01-01 00:00:00",
                "type": "UFW BLOCK",
            },
        )
        == "[3] 2026-01-01 00:00:00 UFW BLOCK\n"
    )


def test_security_export_event_detail_header_line_uses_safe_defaults():
    assert (
        security_monitoring_controller._security_export_event_detail_header_line(1, {})
        == "[1] - -\n"
    )


def test_security_export_event_raw_block_uses_raw_value_with_spacing():
    assert (
        security_monitoring_controller._security_export_event_raw_block(
            {"raw": "demo line"}
        )
        == "demo line\n\n"
    )


def test_security_export_event_raw_block_uses_safe_default():
    assert (
        security_monitoring_controller._security_export_event_raw_block({}) == "-\n\n"
    )


def test_security_export_aggregate_line_formats_category_and_count():
    assert (
        security_monitoring_controller._security_export_aggregate_line("UFW BLOCK", 7)
        == "Aggregiert UFW BLOCK: 7\n"
    )


def test_security_export_aggregate_line_preserves_generic_values():
    assert (
        security_monitoring_controller._security_export_aggregate_line("", None)
        == "Aggregiert : None\n"
    )


def test_security_export_count_block_appends_newline():
    assert (
        security_monitoring_controller._security_export_count_block(
            "Externe UFW-Blocks", 4
        )
        == "Externe UFW-Blocks: 4\n"
    )


def test_security_export_count_block_reuses_count_line_format():
    assert (
        security_monitoring_controller._security_export_count_block("", None)
        == ": None\n"
    )


def test_security_export_event_table_header_line_matches_expected_columns():
    assert (
        security_monitoring_controller._security_export_event_table_header_line()
        == "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n"
    )


def test_security_export_event_table_header_line_has_seven_columns():
    assert (
        security_monitoring_controller._security_export_event_table_header_line().count(
            "|"
        )
        == 6
    )


def test_security_export_time_line_formats_timestamp():
    assert (
        security_monitoring_controller._security_export_time_line("2026-06-06 12:34:56")
        == "Exportzeit: 2026-06-06 12:34:56\n"
    )


def test_security_export_time_line_preserves_empty_timestamp():
    assert (
        security_monitoring_controller._security_export_time_line("")
        == "Exportzeit: \n"
    )


def test_security_export_status_block_appends_newline():
    assert (
        security_monitoring_controller._security_export_status_block(
            "Monitoring-Status: AKTIV"
        )
        == "Monitoring-Status: AKTIV\n"
    )


def test_security_export_status_block_preserves_empty_text():
    assert security_monitoring_controller._security_export_status_block("") == "\n"


def test_security_export_status_blocks_format_expected_lines():
    assert security_monitoring_controller._security_export_status_blocks(
        True, "HIGH", 7
    ) == (
        "Monitoring-Status: AKTIV\n",
        "UFW Logging-Level: HIGH\n",
        "Anzahl Events: 7\n",
    )


def test_security_export_status_blocks_handle_falsey_values():
    assert security_monitoring_controller._security_export_status_blocks(
        False, "", 0
    ) == (
        "Monitoring-Status: AUS\n",
        "UFW Logging-Level: \n",
        "Anzahl Events: 0\n",
    )


def test_security_export_path_joins_directory_and_stamp():
    assert (
        security_monitoring_controller._security_export_path(
            "/tmp/export", "2026-06-06_12-34-56"
        )
        == "/tmp/export/netmon_security_log_2026-06-06_12-34-56.txt"
    )


def test_security_export_path_allows_empty_stamp():
    assert (
        security_monitoring_controller._security_export_path("/tmp/export", "")
        == "/tmp/export/netmon_security_log_.txt"
    )


def test_security_export_dir_candidates_return_expected_desktop_paths():
    assert security_monitoring_controller._security_export_dir_candidates(
        "/home/demo"
    ) == (
        "/home/demo/Schreibtisch",
        "/home/demo/Desktop",
    )


def test_security_export_dir_candidates_preserve_home_prefix():
    de_path, en_path = security_monitoring_controller._security_export_dir_candidates(
        "/tmp/base"
    )
    assert de_path.startswith("/tmp/base/")
    assert en_path.startswith("/tmp/base/")


def test_security_export_datetime_formats_return_stamp_and_display_time():
    assert security_monitoring_controller._security_export_datetime_formats(
        security_monitoring_controller.datetime(2026, 6, 6, 12, 34, 56)
    ) == (
        "2026-06-06_12-34-56",
        "2026-06-06 12:34:56",
    )


def test_security_export_datetime_formats_preserve_zero_padding():
    assert security_monitoring_controller._security_export_datetime_formats(
        security_monitoring_controller.datetime(2026, 1, 2, 3, 4, 5)
    ) == (
        "2026-01-02_03-04-05",
        "2026-01-02 03:04:05",
    )


def test_security_export_success_message_formats_path():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._security_export_success_message(
            DummyApp(), "/tmp/export.txt"
        )
        == "Security-Logs exportiert: /tmp/export.txt"
    )


def test_security_export_success_message_allows_empty_path():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._security_export_success_message(DummyApp(), "")
        == "Security-Logs exportiert: "
    )


def test_security_export_failure_log_message_formats_error():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._security_export_failure_log_message(
            DummyApp(), "boom"
        )
        == "Security-Export fehlgeschlagen: boom"
    )


def test_security_export_failure_log_message_allows_empty_error():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._security_export_failure_log_message(
            DummyApp(), ""
        )
        == "Security-Export fehlgeschlagen: "
    )


def test_security_export_failure_dialog_message_formats_error():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._security_export_failure_dialog_message(
            DummyApp(), "boom"
        )
        == "Export fehlgeschlagen:\nboom"
    )


def test_security_export_failure_dialog_message_allows_empty_error():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._security_export_failure_dialog_message(
            DummyApp(), ""
        )
        == "Export fehlgeschlagen:\n"
    )


def test_security_export_dialog_title_uses_default_text():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._security_export_dialog_title(DummyApp())
        == "Security Export"
    )


def test_security_export_dialog_title_returns_translated_value():
    class DummyApp:
        def tr(self, key, default):
            assert key == "security_export_title"
            assert default == "Security Export"
            return "Sicherheits-Export"

    assert (
        security_monitoring_controller._security_export_dialog_title(DummyApp())
        == "Sicherheits-Export"
    )


def test_security_export_failure_dialog_args_return_title_and_message():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert security_monitoring_controller._security_export_failure_dialog_args(
        DummyApp(), "boom"
    ) == (
        "Security Export",
        "Export fehlgeschlagen:\nboom",
    )


def test_security_export_failure_dialog_args_allow_empty_error():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert security_monitoring_controller._security_export_failure_dialog_args(
        DummyApp(), ""
    ) == (
        "Security Export",
        "Export fehlgeschlagen:\n",
    )


def test_security_export_failure_messages_return_title_body_and_log():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert security_monitoring_controller._security_export_failure_messages(
        DummyApp(), "boom"
    ) == (
        "Security Export",
        "Export fehlgeschlagen:\nboom",
        "Security-Export fehlgeschlagen: boom",
    )


def test_security_export_failure_messages_allow_empty_error():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert security_monitoring_controller._security_export_failure_messages(
        DummyApp(), ""
    ) == (
        "Security Export",
        "Export fehlgeschlagen:\n",
        "Security-Export fehlgeschlagen: ",
    )


def test_security_export_header_block_matches_expected_text():
    assert (
        security_monitoring_controller._security_export_header_block()
        == "NetMon Security Export\n========================\n"
    )


def test_security_export_header_block_has_three_lines():
    assert (
        len(security_monitoring_controller._security_export_header_block().splitlines())
        == 2
    )


def test_security_export_summary_section_block_matches_expected_text():
    assert (
        security_monitoring_controller._security_export_summary_section_block()
        == "SECURITY SUMMARY\n--------------------\n"
    )


def test_security_export_summary_section_block_has_two_lines():
    assert security_monitoring_controller._security_export_summary_section_block().splitlines() == [
        "SECURITY SUMMARY",
        "--------------------",
    ]


def test_security_export_events_section_block_matches_expected_text():
    assert (
        security_monitoring_controller._security_export_events_section_block()
        == "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n"
    )


def test_security_export_events_section_block_has_two_lines():
    assert security_monitoring_controller._security_export_events_section_block().splitlines() == [
        "SECURITY EVENTS",
        "------------------------------------------------------------------------------------------------------------------------",
    ]


def test_security_export_details_section_block_matches_expected_text():
    assert (
        security_monitoring_controller._security_export_details_section_block()
        == "DETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n"
    )


def test_security_export_details_section_block_has_two_lines():
    assert security_monitoring_controller._security_export_details_section_block().splitlines() == [
        "DETAIL / ROHDATEN",
        "------------------------------------------------------------------------------------------------------------------------",
    ]


def test_security_export_details_section_with_spacing_matches_expected_text():
    assert (
        security_monitoring_controller._security_export_details_section_with_spacing()
        == "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n"
    )


def test_security_export_details_section_with_spacing_starts_with_blank_line():
    assert security_monitoring_controller._security_export_details_section_with_spacing().startswith(
        "\n"
    )


def test_security_export_summary_count_blocks_format_expected_counts():
    assert security_monitoring_controller._security_export_summary_count_blocks(
        [
            {"type": "UFW BLOCK"},
            {"type": "Portscan-Verdacht"},
            {"type": "FILE MODIFIED"},
            {"type": "DEVICE CHANGED"},
            {"type": "INPUT ACCESS"},
        ]
    ) == (
        "Externe UFW-Blocks: 1\n",
        "Portscan-Verdacht: 1\n",
        "Dateiänderungen: 1\n",
        "Device-Änderungen: 1\n",
        "Input-Access: 1\n",
    )


def test_security_export_summary_count_blocks_handle_empty_events():
    assert security_monitoring_controller._security_export_summary_count_blocks([]) == (
        "Externe UFW-Blocks: 0\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
    )


def test_security_export_aggregate_blocks_preserve_order_and_values():
    assert security_monitoring_controller._security_export_aggregate_blocks(
        {"DNS": 2, "SSH": 1}
    ) == (
        "Aggregiert DNS: 2\n",
        "Aggregiert SSH: 1\n",
    )


def test_security_export_aggregate_blocks_handle_empty_mapping():
    assert security_monitoring_controller._security_export_aggregate_blocks({}) == ()


def test_security_export_event_detail_blocks_preserve_order_and_content():
    assert security_monitoring_controller._security_export_event_detail_blocks(
        [
            {"time": "2026-01-01 00:00:00", "type": "UFW BLOCK", "raw": "first"},
            {"time": "2026-01-01 00:00:01", "type": "PORTSCAN", "raw": "second"},
        ]
    ) == (
        "[1] 2026-01-01 00:00:00 UFW BLOCK\n",
        "first\n\n",
        "[2] 2026-01-01 00:00:01 PORTSCAN\n",
        "second\n\n",
    )


def test_security_export_event_detail_blocks_handle_empty_events():
    assert security_monitoring_controller._security_export_event_detail_blocks([]) == ()


def test_security_export_event_blocks_include_section_header_and_rows():
    assert security_monitoring_controller._security_export_event_blocks(
        [{"time": "2026-01-01", "type": "UFW BLOCK"}]
    ) == (
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
        "2026-01-01 | UFW BLOCK | - | - | - | - | -\n",
    )


def test_security_export_event_blocks_handle_empty_events():
    assert security_monitoring_controller._security_export_event_blocks([]) == (
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
    )


def test_security_export_details_blocks_include_section_and_entries():
    assert security_monitoring_controller._security_export_details_blocks(
        [{"time": "2026-01-01", "type": "UFW BLOCK", "raw": "demo"}]
    ) == (
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
        "[1] 2026-01-01 UFW BLOCK\n",
        "demo\n\n",
    )


def test_security_export_details_blocks_handle_empty_events():
    assert security_monitoring_controller._security_export_details_blocks([]) == (
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
    )


def test_security_export_summary_blocks_include_section_counts_and_aggregates():
    assert security_monitoring_controller._security_export_summary_blocks(
        [{"type": "UFW BLOCK"}, {"type": "FILE CHANGED"}],
        {"UFW BLOCK": 1, "FILE CHANGED": 1},
    ) == (
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 1\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 1\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "Aggregiert UFW BLOCK: 1\n",
        "Aggregiert FILE CHANGED: 1\n",
        "\n",
    )


def test_security_export_summary_blocks_handle_empty_inputs():
    assert security_monitoring_controller._security_export_summary_blocks([], {}) == (
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 0\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "\n",
    )


def test_security_export_intro_blocks_include_header_status_and_alarm():
    assert security_monitoring_controller._security_export_intro_blocks(
        "2026-06-06 12:34:56", True, "high", 3, "Portscan-Verdacht"
    ) == (
        "NetMon Security Export\n========================\n",
        "Exportzeit: 2026-06-06 12:34:56\n",
        "Monitoring-Status: AKTIV\n",
        "UFW Logging-Level: high\n",
        "Anzahl Events: 3\n",
        "Letzter Alarm: Portscan-Verdacht\n\n",
    )


def test_security_export_intro_blocks_handle_falsey_values():
    assert security_monitoring_controller._security_export_intro_blocks(
        "", False, "", 0, "–"
    ) == (
        "NetMon Security Export\n========================\n",
        "Exportzeit: \n",
        "Monitoring-Status: AUS\n",
        "UFW Logging-Level: \n",
        "Anzahl Events: 0\n",
        "Letzter Alarm: –\n\n",
    )


def test_security_export_content_blocks_include_summary_events_and_details():
    assert security_monitoring_controller._security_export_content_blocks(
        [{"time": "2026-01-01", "type": "UFW BLOCK", "raw": "demo"}],
        {"UFW BLOCK": 1},
    ) == (
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 1\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "Aggregiert UFW BLOCK: 1\n",
        "\n",
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
        "2026-01-01 | UFW BLOCK | - | - | - | - | -\n",
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
        "[1] 2026-01-01 UFW BLOCK\n",
        "demo\n\n",
    )


def test_security_export_content_blocks_handle_empty_inputs():
    assert security_monitoring_controller._security_export_content_blocks([], {}) == (
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 0\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "\n",
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
    )


def test_security_export_blocks_include_intro_and_content():
    assert security_monitoring_controller._security_export_blocks(
        "2026-06-06 12:34:56",
        True,
        "high",
        1,
        "Portscan-Verdacht",
        [{"time": "2026-01-01", "type": "UFW BLOCK", "raw": "demo"}],
        {"UFW BLOCK": 1},
    ) == (
        "NetMon Security Export\n========================\n",
        "Exportzeit: 2026-06-06 12:34:56\n",
        "Monitoring-Status: AKTIV\n",
        "UFW Logging-Level: high\n",
        "Anzahl Events: 1\n",
        "Letzter Alarm: Portscan-Verdacht\n\n",
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 1\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "Aggregiert UFW BLOCK: 1\n",
        "\n",
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
        "2026-01-01 | UFW BLOCK | - | - | - | - | -\n",
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
        "[1] 2026-01-01 UFW BLOCK\n",
        "demo\n\n",
    )


def test_security_export_blocks_handle_empty_inputs():
    assert security_monitoring_controller._security_export_blocks(
        "", False, "", 0, "–", [], {}
    ) == (
        "NetMon Security Export\n========================\n",
        "Exportzeit: \n",
        "Monitoring-Status: AUS\n",
        "UFW Logging-Level: \n",
        "Anzahl Events: 0\n",
        "Letzter Alarm: –\n\n",
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 0\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "\n",
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
    )


def test_security_export_target_returns_path_and_display_time():
    assert security_monitoring_controller._security_export_target(
        datetime(2026, 6, 6, 12, 34, 56), "/tmp/export"
    ) == (
        "/tmp/export/netmon_security_log_2026-06-06_12-34-56.txt",
        "2026-06-06 12:34:56",
    )


def test_security_export_target_preserves_nested_export_dir():
    assert security_monitoring_controller._security_export_target(
        datetime(2026, 1, 2, 3, 4, 5), "/tmp/security/logs"
    ) == (
        "/tmp/security/logs/netmon_security_log_2026-01-02_03-04-05.txt",
        "2026-01-02 03:04:05",
    )


def test_security_export_write_context_uses_target_and_blocks(monkeypatch):
    calls = []
    app = object()
    moment = datetime(2026, 6, 6, 13, 15, 0)

    monkeypatch.setattr(
        security_monitoring_controller,
        "security_export_dir",
        lambda: calls.append("dir") or "/tmp/export",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_export_target",
        lambda current_moment, export_dir: calls.append(
            ("target", current_moment, export_dir)
        )
        or ("/tmp/export/out.txt", "2026-06-06 13:15:00"),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_export_blocks_for_app",
        lambda current_app, export_time: calls.append(
            ("blocks", current_app, export_time)
        )
        or ("header\n",),
    )

    assert security_monitoring_controller._security_export_write_context(
        app, moment
    ) == (
        "/tmp/export/out.txt",
        ("header\n",),
    )
    assert calls == [
        "dir",
        ("target", moment, "/tmp/export"),
        ("blocks", app, "2026-06-06 13:15:00"),
    ]


def test_security_export_blocks_for_app_include_current_app_values():
    class DummyApp:
        security_monitoring = True
        security_log_level = "high"
        security_last_alarm = "Portscan-Verdacht"
        security_events = [{"time": "2026-01-01", "type": "UFW BLOCK", "raw": "demo"}]
        security_aggregated = {"UFW BLOCK": 1}

    assert security_monitoring_controller._security_export_blocks_for_app(
        DummyApp(), "2026-06-06 12:34:56"
    ) == (
        "NetMon Security Export\n========================\n",
        "Exportzeit: 2026-06-06 12:34:56\n",
        "Monitoring-Status: AKTIV\n",
        "UFW Logging-Level: high\n",
        "Anzahl Events: 1\n",
        "Letzter Alarm: Portscan-Verdacht\n\n",
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 1\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "Aggregiert UFW BLOCK: 1\n",
        "\n",
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
        "2026-01-01 | UFW BLOCK | - | - | - | - | -\n",
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
        "[1] 2026-01-01 UFW BLOCK\n",
        "demo\n\n",
    )


def test_security_export_blocks_for_app_handle_missing_values():
    class DummyApp:
        security_events = []

    assert security_monitoring_controller._security_export_blocks_for_app(
        DummyApp(), ""
    ) == (
        "NetMon Security Export\n========================\n",
        "Exportzeit: \n",
        "Monitoring-Status: AUS\n",
        "UFW Logging-Level: \n",
        "Anzahl Events: 0\n",
        "Letzter Alarm: –\n\n",
        "SECURITY SUMMARY\n--------------------\n",
        "Externe UFW-Blocks: 0\n",
        "Portscan-Verdacht: 0\n",
        "Dateiänderungen: 0\n",
        "Device-Änderungen: 0\n",
        "Input-Access: 0\n",
        "\n",
        "SECURITY EVENTS\n------------------------------------------------------------------------------------------------------------------------\n",
        "Zeit | Typ | Quelle-IP | Ziel-Port | Protokoll | Level | Aktion\n",
        "\nDETAIL / ROHDATEN\n------------------------------------------------------------------------------------------------------------------------\n",
    )


def test_security_export_blocks_for_app_uses_reporting_context(monkeypatch):
    calls = []
    app = object()
    context = {
        "monitoring_active": True,
        "event_count": 2,
        "last_alarm": "Neue Events",
        "events": [{"type": "UFW BLOCK"}],
        "aggregated": {"DNS": 1},
    }

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_reporting_context",
        lambda current_app: calls.append(("context", current_app)) or context,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_log_level",
        lambda current_app, default="-": calls.append(("level", current_app, default))
        or "LOW",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_export_blocks",
        lambda export_time, monitoring_active, logging_level, event_count, last_alarm, events, aggregated: calls.append(
            (
                "blocks",
                export_time,
                monitoring_active,
                logging_level,
                event_count,
                last_alarm,
                events,
                aggregated,
            )
        )
        or ("ok",),
    )

    assert security_monitoring_controller._security_export_blocks_for_app(
        app, "2026-06-06 13:00:00"
    ) == ("ok",)
    assert calls == [
        ("context", app),
        ("level", app, ""),
        (
            "blocks",
            "2026-06-06 13:00:00",
            True,
            "LOW",
            2,
            "Neue Events",
            [{"type": "UFW BLOCK"}],
            {"DNS": 1},
        ),
    ]


def test_security_export_success_logs_message():
    logs = []

    class DummyApp:
        def tr(self, _key, default):
            return default

        def log(self, message):
            logs.append(message)

    security_monitoring_controller._security_export_success(
        DummyApp(), "/tmp/export/netmon_security_log.txt"
    )

    assert logs == ["Security-Logs exportiert: /tmp/export/netmon_security_log.txt"]


def test_write_security_export_opens_file_and_writes_blocks(monkeypatch):
    exported = {}

    def fake_open(path, mode="r", encoding=None):
        exported["open"] = (path, mode, encoding)

        class CaptureFile:
            def write(self, data):
                exported.setdefault("parts", []).append(data)

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        return CaptureFile()

    monkeypatch.setattr("builtins.open", fake_open)

    security_monitoring_controller._write_security_export(
        "/tmp/export/out.txt",
        ("one\n", "two\n"),
    )

    assert exported == {
        "open": ("/tmp/export/out.txt", "w", "utf-8"),
        "parts": ["one\n", "two\n"],
    }


def test_run_security_export_uses_write_context_and_writer(monkeypatch):
    calls = []
    app = object()
    moment = datetime(2026, 6, 6, 13, 20, 0)

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_export_write_context",
        lambda current_app, current_moment: calls.append(
            ("context", current_app, current_moment)
        )
        or ("/tmp/export/out.txt", ("header\n",)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_write_security_export",
        lambda path, blocks: calls.append(("write", path, blocks)),
    )

    assert (
        security_monitoring_controller._run_security_export(app, moment)
        == "/tmp/export/out.txt"
    )
    assert calls == [
        ("context", app, moment),
        ("write", "/tmp/export/out.txt", ("header\n",)),
    ]


def test_security_export_failure_shows_dialog_and_logs(monkeypatch):
    calls = []
    logs = []

    def fake_showerror(title, message, parent=None):
        calls.append((title, message, parent))

    monkeypatch.setattr(
        security_monitoring_controller.messagebox, "showerror", fake_showerror
    )

    class DummyApp:
        def tr(self, _key, default):
            return default

        def log(self, message):
            logs.append(message)

    app = DummyApp()
    security_monitoring_controller._security_export_failure(app, "boom")

    assert calls == [("Security Export", "Export fehlgeschlagen:\nboom", app)]
    assert logs == ["Security-Export fehlgeschlagen: boom"]


def test_export_security_logs_uses_run_export_and_success(monkeypatch):
    calls = []
    app = object()
    moment = datetime(2026, 6, 6, 13, 30, 0)

    monkeypatch.setattr(
        security_monitoring_controller,
        "datetime",
        type(
            "DummyDateTime",
            (),
            {"now": staticmethod(lambda: moment)},
        ),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_run_security_export",
        lambda current_app, current_moment: calls.append(
            ("run", current_app, current_moment)
        )
        or "/tmp/export/out.txt",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_export_success",
        lambda current_app, path: calls.append(("success", current_app, path)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_export_failure",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("failure should not be called")
        ),
    )

    assert security_monitoring_controller.export_security_logs(app) is None
    assert calls == [
        ("run", app, moment),
        ("success", app, "/tmp/export/out.txt"),
    ]


def test_security_export_write_blocks_writes_all_blocks_in_order():
    class DummyHandle:
        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    handle = DummyHandle()

    security_monitoring_controller._security_export_write_blocks(
        handle, ("one\n", "two\n", "three\n")
    )

    assert handle.parts == ["one\n", "two\n", "three\n"]


def test_security_export_write_blocks_ignores_empty_blocks_sequence():
    class DummyHandle:
        def __init__(self):
            self.parts = []

        def write(self, text):
            self.parts.append(text)

    handle = DummyHandle()

    security_monitoring_controller._security_export_write_blocks(handle, ())

    assert handle.parts == []


def test_append_security_section_appends_blank_line_and_title():
    lines = ["Header"]

    security_monitoring_controller._append_security_section(lines, "Details")

    assert lines == ["Header", "", "Details"]


def test_append_security_section_preserves_existing_empty_lines():
    lines = ["Header", ""]

    security_monitoring_controller._append_security_section(lines, "Details")

    assert lines == ["Header", "", "", "Details"]


def test_security_export_count_line_formats_label_and_count():
    assert (
        security_monitoring_controller._security_export_count_line(
            "Externe UFW-Blocks", 2
        )
        == "Externe UFW-Blocks: 2"
    )


def test_security_export_count_line_accepts_zero():
    assert (
        security_monitoring_controller._security_export_count_line(
            "Portscan-Verdacht", 0
        )
        == "Portscan-Verdacht: 0"
    )


def test_security_export_section_lines_return_title_and_divider():
    assert security_monitoring_controller._security_export_section_lines(
        "SECURITY SUMMARY", 4
    ) == ["SECURITY SUMMARY", "----"]


def test_security_export_section_lines_clamp_negative_width():
    assert security_monitoring_controller._security_export_section_lines(
        "SECURITY EVENTS", -1
    ) == ["SECURITY EVENTS", ""]


def test_security_export_section_block_joins_lines_with_trailing_newline():
    assert (
        security_monitoring_controller._security_export_section_block(
            "SECURITY SUMMARY", 4
        )
        == "SECURITY SUMMARY\n----\n"
    )


def test_security_export_section_block_handles_negative_width():
    assert (
        security_monitoring_controller._security_export_section_block(
            "DETAIL / ROHDATEN", -1
        )
        == "DETAIL / ROHDATEN\n\n"
    )


def test_security_export_last_alarm_block_appends_double_newline():
    assert (
        security_monitoring_controller._security_export_last_alarm_block(
            "Neue BLOCK-Events"
        )
        == "Letzter Alarm: Neue BLOCK-Events\n\n"
    )


def test_security_export_last_alarm_block_preserves_dash_default():
    assert (
        security_monitoring_controller._security_export_last_alarm_block("–")
        == "Letzter Alarm: –\n\n"
    )


def test_security_monitoring_status_line_uses_default_prefix():
    assert (
        security_monitoring_controller._security_monitoring_status_line(True)
        == "Monitoring: AKTIV"
    )


def test_security_monitoring_status_line_accepts_custom_prefix():
    assert (
        security_monitoring_controller._security_monitoring_status_line(
            False, "Monitoring-Status"
        )
        == "Monitoring-Status: AUS"
    )


def test_security_last_alarm_text_formats_value():
    assert (
        security_monitoring_controller._security_last_alarm_text("Neue BLOCK-Events")
        == "Letzter Alarm: Neue BLOCK-Events"
    )


def test_security_last_alarm_text_preserves_dash_default():
    assert (
        security_monitoring_controller._security_last_alarm_text("–")
        == "Letzter Alarm: –"
    )


def test_security_logging_level_text_uses_default_prefix():
    assert (
        security_monitoring_controller._security_logging_level_text("LOW")
        == "Logging: LOW"
    )


def test_security_logging_level_text_accepts_custom_prefix():
    assert (
        security_monitoring_controller._security_logging_level_text(
            "HIGH", "UFW Logging-Level"
        )
        == "UFW Logging-Level: HIGH"
    )


def test_security_events_count_text_uses_default_prefix():
    assert security_monitoring_controller._security_events_count_text(3) == "Events: 3"


def test_security_events_count_text_accepts_custom_prefix():
    assert (
        security_monitoring_controller._security_events_count_text(7, "Anzahl Events")
        == "Anzahl Events: 7"
    )


def test_security_status_values_return_expected_status_texts():
    assert security_monitoring_controller._security_status_values(
        True, "LOW", 3, "Neue BLOCK-Events"
    ) == (
        "Monitoring: AKTIV",
        "Logging: LOW",
        "Events: 3",
        "Letzter Alarm: Neue BLOCK-Events",
    )


def test_security_status_values_preserve_falsey_inputs():
    assert security_monitoring_controller._security_status_values(
        False, "", 0, "–"
    ) == (
        "Monitoring: AUS",
        "Logging: ",
        "Events: 0",
        "Letzter Alarm: –",
    )


def test_security_runtime_context_uses_safe_defaults():
    assert security_monitoring_controller._security_runtime_context(object()) == {
        "monitoring_active": False,
        "logging_level": "-",
        "event_count": 0,
        "last_alarm": "–",
    }


def test_security_update_status_uses_runtime_context(monkeypatch):
    calls = []
    app = type(
        "DummyApp",
        (),
        {
            "l_sec": object(),
            "set_light": lambda self, widget, color: calls.append(
                ("light", widget, color)
            ),
            "security_status_var": type(
                "Var", (), {"set": lambda self, value: calls.append(("status", value))}
            )(),
            "security_level_var": type(
                "Var", (), {"set": lambda self, value: calls.append(("level", value))}
            )(),
            "security_count_var": type(
                "Var", (), {"set": lambda self, value: calls.append(("count", value))}
            )(),
            "security_alarm_var": type(
                "Var", (), {"set": lambda self, value: calls.append(("alarm", value))}
            )(),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_security_log_level_safe",
        lambda current_app, *, log_failures=False: calls.append(
            ("refresh", current_app, log_failures)
        ),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_runtime_context",
        lambda current_app: {
            "monitoring_active": True,
            "logging_level": "LOW",
            "event_count": 4,
            "last_alarm": "Alarm",
        },
    )

    security_monitoring_controller.security_update_status(app, "yellow")

    assert calls == [
        ("refresh", app, False),
        ("light", app.l_sec, "yellow"),
        ("status", "Monitoring: AKTIV"),
        ("level", "Logging: LOW"),
        ("count", "Events: 4"),
        ("alarm", "Letzter Alarm: Alarm"),
    ]


def test_security_filter_log_message_maps_known_modes():
    assert (
        security_monitoring_controller._security_filter_log_message("portscan")
        == "Security-Filter: Nur Portscan."
    )
    assert (
        security_monitoring_controller._security_filter_log_message("relevant")
        == "Security-Filter: Nur Warnungen/Alarme."
    )
    assert (
        security_monitoring_controller._security_filter_log_message("external")
        == "Security-Filter: Nur externe UFW-Blocks."
    )


def test_security_filter_log_message_falls_back_to_all_message():
    assert (
        security_monitoring_controller._security_filter_log_message("all")
        == "Security-Filter: Alle Events."
    )
    assert (
        security_monitoring_controller._security_filter_log_message("mystery")
        == "Security-Filter: Alle Events."
    )


def test_security_connected_devices_log_message_formats_positive_count():
    assert (
        security_monitoring_controller._security_connected_devices_log_message(2)
        == "Security: 2 verbundene Geräte angezeigt."
    )


def test_security_connected_devices_log_message_clamps_negative_count():
    assert (
        security_monitoring_controller._security_connected_devices_log_message(-1)
        == "Security: 0 verbundene Geräte angezeigt."
    )


def test_security_table_refreshed_log_message_matches_expected_text():
    assert (
        security_monitoring_controller._security_table_refreshed_log_message()
        == "Security-Tabelle aktualisiert."
    )


def test_security_table_refreshed_log_message_mentions_tabelle():
    assert "Tabelle" in (
        security_monitoring_controller._security_table_refreshed_log_message()
    )


def test_security_views_cleared_log_message_matches_expected_text():
    assert (
        security_monitoring_controller._security_views_cleared_log_message()
        == "Guards-Tab: Ansichten geleert."
    )


def test_security_views_cleared_log_message_mentions_ansichten():
    assert "Ansichten" in (
        security_monitoring_controller._security_views_cleared_log_message()
    )


def test_security_views_cleared_detail_text_matches_expected_text():
    assert (
        security_monitoring_controller._security_views_cleared_detail_text()
        == "Ansichten im Guards-Tab wurden geleert."
    )


def test_security_views_cleared_detail_text_mentions_ansichten():
    assert "Ansichten" in (
        security_monitoring_controller._security_views_cleared_detail_text()
    )


def test_security_clear_events_title_matches_expected_text():
    assert (
        security_monitoring_controller._security_clear_events_title()
        == "Security-Events leeren"
    )


def test_security_clear_events_body_mentions_fortfahren():
    body = security_monitoring_controller._security_clear_events_body()

    assert "Security-Events" in body
    assert "Fortfahren?" in body


def test_security_clear_events_dialog_args_use_default_texts():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert security_monitoring_controller._security_clear_events_dialog_args(
        DummyApp()
    ) == (
        "Security-Events leeren",
        "Die aktuell angezeigten Security-Events werden entfernt.\n\nFortfahren?",
    )


def test_security_clear_events_dialog_args_use_translated_values():
    class DummyApp:
        def tr(self, key, default):
            return {
                "security_clear_title": "Titel",
                "security_clear_body": "Body",
            }.get(key, default)

    assert security_monitoring_controller._security_clear_events_dialog_args(
        DummyApp()
    ) == ("Titel", "Body")


def test_confirm_security_clear_events_skips_dialog_without_confirm(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.messagebox,
        "askyesno",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("dialog should not open")
        ),
    )

    assert (
        security_monitoring_controller._confirm_security_clear_events(
            type("DummyApp", (), {"security_events": [{"type": "UFW BLOCK"}]})(),
            False,
        )
        is True
    )


def test_confirm_security_clear_events_logs_cancelled_message(monkeypatch):
    calls = []
    logs = []
    app = type(
        "DummyApp",
        (),
        {
            "security_events": [{"type": "UFW BLOCK"}],
            "tr": lambda self, _key, default: default,
            "log": logs.append,
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_clear_events_dialog_args",
        lambda current_app: calls.append(("args", current_app)) or ("Titel", "Body"),
    )
    monkeypatch.setattr(
        security_monitoring_controller.messagebox,
        "askyesno",
        lambda title, body, parent=None: calls.append((title, body, parent)) or False,
    )

    assert (
        security_monitoring_controller._confirm_security_clear_events(app, True)
        is False
    )
    assert calls == [("args", app), ("Titel", "Body", app)]
    assert logs == ["Security-Events leeren abgebrochen."]


def test_reset_security_event_state_clears_event_related_values():
    class DummyApp:
        security_events = [{"type": "UFW BLOCK"}]
        security_event_keys = {"event-1"}
        security_visible_events = [{"type": "UFW BLOCK"}]
        security_last_portscan_alert = {"1.2.3.4": 3}
        security_aggregated = {"DNS": 2}
        security_dedup_cache = {"cache": 1}
        security_last_alarm = "Neue BLOCK-Events"

    app = DummyApp()
    security_monitoring_controller._reset_security_event_state(app)

    assert app.security_events == []
    assert app.security_event_keys == set()
    assert app.security_visible_events == []
    assert app.security_last_portscan_alert == {}
    assert app.security_aggregated == {}
    assert app.security_dedup_cache == {}
    assert app.security_last_alarm == "–"


def test_reset_security_event_state_preserves_object_identity_outside_reset_fields():
    class DummyApp:
        security_events = [{"type": "demo"}]
        security_event_keys = {"x"}
        security_visible_events = [{"type": "demo"}]
        security_last_portscan_alert = {"src": 1}
        security_aggregated = {"DNS": 1}
        security_dedup_cache = {"seen": True}
        security_last_alarm = "Alarm"
        untouched = "keep"

    app = DummyApp()
    security_monitoring_controller._reset_security_event_state(app)

    assert app.untouched == "keep"


def test_security_clear_events_status_color_returns_green_when_monitoring():
    class DummyApp:
        security_monitoring = True

    assert (
        security_monitoring_controller._security_clear_events_status_color(DummyApp())
        == "green"
    )


def test_security_clear_events_status_color_returns_gray_when_not_monitoring():
    class DummyApp:
        security_monitoring = False

    assert (
        security_monitoring_controller._security_clear_events_status_color(DummyApp())
        == "gray"
    )


def test_reset_security_view_state_clears_visible_events_and_row_meta():
    class DummyApp:
        security_visible_events = [{"raw": "demo"}]
        security_table_row_meta = {"sec-0": {"kind": "event", "index": 0}}
        input_access_row_meta = {"input-0": {"path": "/dev/input/event0"}}

    app = DummyApp()
    security_monitoring_controller._reset_security_view_state(app)

    assert app.security_visible_events == []
    assert app.security_table_row_meta == {}
    assert app.input_access_row_meta == {}


def test_reset_security_view_state_preserves_other_fields():
    class DummyApp:
        security_visible_events = [{"raw": "demo"}]
        security_table_row_meta = {"sec-0": {"kind": "event", "index": 0}}
        input_access_row_meta = {"input-0": {"path": "/dev/input/event0"}}
        untouched = "keep"

    app = DummyApp()
    security_monitoring_controller._reset_security_view_state(app)

    assert app.untouched == "keep"


def test_clear_security_view_tables_clears_all_known_tables():
    class DummyTable:
        def __init__(self):
            self.deleted = []

        def get_children(self):
            return ("row-1", "row-2")

        def delete(self, *items):
            self.deleted.extend(items)

    class DummyApp:
        security_table = DummyTable()
        security_devices_table = DummyTable()
        input_access_table = DummyTable()

    app = DummyApp()
    security_monitoring_controller._clear_security_view_tables(app)

    assert app.security_table.deleted == ["row-1", "row-2"]
    assert app.security_devices_table.deleted == ["row-1", "row-2"]
    assert app.input_access_table.deleted == ["row-1", "row-2"]


def test_clear_security_view_tables_ignores_missing_tables():
    class DummyApp:
        security_table = None
        security_devices_table = None
        input_access_table = None

    security_monitoring_controller._clear_security_view_tables(DummyApp())


def test_run_security_clear_events_resets_refreshes_updates_and_logs(monkeypatch):
    calls = []
    app = type(
        "DummyApp",
        (),
        {
            "security_detail": type(
                "Detail",
                (),
                {"delete": lambda self, start, end: calls.append((start, end))},
            )(),
            "tr": lambda self, _key, default: default,
            "log": lambda self, message: calls.append(("log", message)),
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_reset_security_event_state",
        lambda current_app: calls.append(("reset", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "refresh_security_table",
        lambda current_app: calls.append(("refresh", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_clear_events_status_color",
        lambda current_app: calls.append(("color", current_app)) or "gray",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "security_update_status",
        lambda current_app, color: calls.append(("status", current_app, color)),
    )

    assert security_monitoring_controller._run_security_clear_events(app) is None
    assert calls == [
        ("reset", app),
        ("1.0", "end"),
        ("refresh", app),
        ("color", app),
        ("status", app, "gray"),
        ("log", "Security-Events geleert."),
    ]


def test_run_security_clear_views_runs_clear_reset_and_finish(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_clear_security_view_tables",
        lambda current_app: calls.append(("clear", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_reset_security_view_state",
        lambda current_app: calls.append(("reset", current_app)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_finish_security_clear_views",
        lambda current_app: calls.append(("finish", current_app)),
    )

    assert security_monitoring_controller._run_security_clear_views(app) is None
    assert calls == [("clear", app), ("reset", app), ("finish", app)]


def test_security_view_tables_returns_known_tables():
    security_table = object()
    devices_table = object()
    input_table = object()
    app = type(
        "DummyApp",
        (),
        {
            "security_table": security_table,
            "security_devices_table": devices_table,
            "input_access_table": input_table,
        },
    )()

    assert security_monitoring_controller._security_view_tables(app) == (
        security_table,
        devices_table,
        input_table,
    )


def test_security_view_tables_returns_none_for_missing_tables():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_view_tables(app) == (
        None,
        None,
        None,
    )


def test_clear_input_access_table_deletes_all_children():
    class DummyTable:
        def __init__(self):
            self.deleted = []

        def get_children(self):
            return ("input-0", "input-1")

        def delete(self, *items):
            self.deleted.extend(items)

    table = DummyTable()
    security_monitoring_controller._clear_input_access_table(table)

    assert table.deleted == ["input-0", "input-1"]


def test_input_access_table_children_returns_list_copy():
    class DummyTable:
        @staticmethod
        def get_children():
            return ("input-0", "input-1")

    children = security_monitoring_controller._input_access_table_children(DummyTable())

    assert children == ["input-0", "input-1"]
    assert isinstance(children, list)


def test_input_access_table_children_handles_no_children():
    class DummyTable:
        @staticmethod
        def get_children():
            return ()

    assert (
        security_monitoring_controller._input_access_table_children(DummyTable()) == []
    )


def test_clear_input_access_table_ignores_table_errors():
    class BrokenTable:
        def get_children(self):
            raise RuntimeError("broken")

        def delete(self, *items):
            raise RuntimeError("broken")

    security_monitoring_controller._clear_input_access_table(BrokenTable())


def test_insert_input_access_row_inserts_expected_values():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, values=()):
            self.calls.append((parent, where, values))
            return "input-0"

    table = DummyTable()
    row_id = security_monitoring_controller._insert_input_access_row(
        table,
        {
            "device": "USB Keyboard",
            "process": "python",
            "pid": "1234",
            "type": "input-event",
            "status": "bekannt",
            "path": "/dev/input/event0",
        },
    )

    assert row_id == "input-0"
    assert table.calls == [
        (
            "",
            "end",
            (
                "USB Keyboard",
                "python",
                "1234",
                "input-event",
                "bekannt",
                "/dev/input/event0",
            ),
        )
    ]


def test_insert_input_access_row_uses_safe_defaults():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, values=()):
            self.calls.append((parent, where, values))
            return "input-1"

    table = DummyTable()
    security_monitoring_controller._insert_input_access_row(table, {})

    assert table.calls == [("", "end", ("-", "-", "-", "-", "-", "-"))]


def test_input_access_row_insert_values_returns_formatted_columns():
    assert security_monitoring_controller._input_access_row_insert_values(
        {
            "device": "USB Keyboard",
            "process": "python",
            "pid": "1234",
            "type": "input-event",
            "status": "bekannt",
            "path": "/dev/input/event0",
        }
    ) == (
        "USB Keyboard",
        "python",
        "1234",
        "input-event",
        "bekannt",
        "/dev/input/event0",
    )


def test_input_access_row_insert_values_uses_safe_defaults():
    assert security_monitoring_controller._input_access_row_insert_values({}) == (
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    )


def test_input_access_row_insert_position_uses_tree_insert_defaults():
    assert security_monitoring_controller._input_access_row_insert_position() == (
        "",
        "end",
    )


def test_input_access_row_insert_position_is_stable():
    first = security_monitoring_controller._input_access_row_insert_position()
    second = security_monitoring_controller._input_access_row_insert_position()

    assert first == second == ("", "end")


def test_tree_insert_position_uses_tree_insert_defaults():
    assert security_monitoring_controller._tree_insert_position() == (
        "",
        "end",
    )


def test_tree_insert_position_is_stable():
    first = security_monitoring_controller._tree_insert_position()
    second = security_monitoring_controller._tree_insert_position()

    assert first == second == ("", "end")


def test_input_access_row_insert_spec_combines_position_and_config():
    parent, where, config = (
        security_monitoring_controller._input_access_row_insert_spec(
            {"device": "USB Keyboard", "path": "/dev/input/event0"}
        )
    )

    assert (parent, where) == ("", "end")
    assert config == {
        "values": ("USB Keyboard", "-", "-", "-", "-", "/dev/input/event0")
    }


def test_input_access_row_insert_spec_preserves_explicit_row_fields():
    parent, where, config = (
        security_monitoring_controller._input_access_row_insert_spec(
            {
                "device": "USB Mouse",
                "process": "python",
                "pid": "123",
                "type": "mouse",
                "status": "bekannt",
                "path": "/dev/input/mouse0",
            }
        )
    )

    assert (parent, where) == ("", "end")
    assert config == {
        "values": (
            "USB Mouse",
            "python",
            "123",
            "mouse",
            "bekannt",
            "/dev/input/mouse0",
        )
    }


def test_input_access_row_insert_config_wraps_values_tuple():
    assert security_monitoring_controller._input_access_row_insert_config(
        ("USB Keyboard", "-", "-", "-", "-", "/dev/input/event0")
    ) == {
        "values": ("USB Keyboard", "-", "-", "-", "-", "/dev/input/event0"),
    }


def test_input_access_row_insert_config_preserves_empty_tuple():
    assert security_monitoring_controller._input_access_row_insert_config(()) == {
        "values": ()
    }


def test_input_access_row_field_returns_existing_value():
    assert (
        security_monitoring_controller._input_access_row_field(
            {"device": "USB Keyboard"}, "device"
        )
        == "USB Keyboard"
    )


def test_input_access_row_field_preserves_get_semantics():
    assert security_monitoring_controller._input_access_row_field({}, "device") == "-"
    assert (
        security_monitoring_controller._input_access_row_field(
            {"device": None}, "device"
        )
        is None
    )


def test_input_access_row_values_returns_expected_tuple():
    assert security_monitoring_controller._input_access_row_values(
        {
            "device": "USB Keyboard",
            "process": "python",
            "pid": "1234",
            "type": "input-event",
            "status": "bekannt",
            "path": "/dev/input/event0",
        }
    ) == (
        "USB Keyboard",
        "python",
        "1234",
        "input-event",
        "bekannt",
        "/dev/input/event0",
    )


def test_input_access_row_values_uses_safe_defaults():
    assert security_monitoring_controller._input_access_row_values({}) == (
        "-",
        "-",
        "-",
        "-",
        "-",
        "-",
    )


def test_store_input_access_row_meta_copies_row_into_app_mapping():
    app = type("DummyApp", (), {"input_access_row_meta": {}})()
    row = {"device": "USB Keyboard", "path": "/dev/input/event0"}

    security_monitoring_controller._store_input_access_row_meta(app, "input-0", row)

    assert app.input_access_row_meta == {
        "input-0": {"device": "USB Keyboard", "path": "/dev/input/event0"}
    }
    assert app.input_access_row_meta["input-0"] is not row


def test_store_input_access_row_meta_overwrites_existing_entry():
    app = type(
        "DummyApp",
        (),
        {"input_access_row_meta": {"input-0": {"device": "Old"}}},
    )()

    security_monitoring_controller._store_input_access_row_meta(
        app,
        "input-0",
        {"device": "New", "path": "/dev/input/event1"},
    )

    assert app.input_access_row_meta == {
        "input-0": {"device": "New", "path": "/dev/input/event1"}
    }


def test_populate_input_access_table_inserts_rows_and_stores_meta():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, values=()):
            row_id = f"input-{len(self.calls)}"
            self.calls.append((parent, where, values))
            return row_id

    app = type("DummyApp", (), {"input_access_row_meta": {}})()
    table = DummyTable()

    security_monitoring_controller._populate_input_access_table(
        app,
        table,
        [
            {"device": "USB Keyboard", "path": "/dev/input/event0"},
            {"device": "USB Mouse", "path": "/dev/input/event1"},
        ],
    )

    assert table.calls == [
        ("", "end", ("USB Keyboard", "-", "-", "-", "-", "/dev/input/event0")),
        ("", "end", ("USB Mouse", "-", "-", "-", "-", "/dev/input/event1")),
    ]
    assert app.input_access_row_meta == {
        "input-0": {"device": "USB Keyboard", "path": "/dev/input/event0"},
        "input-1": {"device": "USB Mouse", "path": "/dev/input/event1"},
    }


def test_input_access_table_rows_returns_copy_of_rows():
    rows = [{"device": "USB Keyboard"}, {"device": "USB Mouse"}]

    extracted = security_monitoring_controller._input_access_table_rows(rows)

    assert extracted == rows
    assert extracted is not rows


def test_input_access_table_rows_handles_empty_rows():
    assert security_monitoring_controller._input_access_table_rows([]) == []
    assert security_monitoring_controller._input_access_table_rows(None) == []


def test_populate_input_access_table_ignores_empty_rows():
    class DummyTable:
        def insert(self, *_args, **_kwargs):
            raise AssertionError("insert should not be called")

    app = type("DummyApp", (), {"input_access_row_meta": {}})()

    security_monitoring_controller._populate_input_access_table(app, DummyTable(), [])
    security_monitoring_controller._populate_input_access_table(app, DummyTable(), None)

    assert app.input_access_row_meta == {}


def test_input_access_row_insert_kwargs_builds_values_payload():
    assert security_monitoring_controller._input_access_row_insert_kwargs(
        {"device": "USB Keyboard", "path": "/dev/input/event0"}
    ) == {
        "values": ("USB Keyboard", "-", "-", "-", "-", "/dev/input/event0"),
    }


def test_input_access_row_insert_kwargs_uses_explicit_row_fields():
    assert security_monitoring_controller._input_access_row_insert_kwargs(
        {
            "device": "USB Mouse",
            "process": "python",
            "pid": "123",
            "type": "mouse",
            "status": "bekannt",
            "path": "/dev/input/mouse0",
        }
    ) == {
        "values": (
            "USB Mouse",
            "python",
            "123",
            "mouse",
            "bekannt",
            "/dev/input/mouse0",
        ),
    }


def test_input_access_row_meta_value_returns_row_copy():
    row = {"device": "USB Keyboard", "path": "/dev/input/event0"}

    copied = security_monitoring_controller._input_access_row_meta_value(row)

    assert copied == row
    assert copied is not row


def test_input_access_row_meta_value_handles_empty_row():
    assert security_monitoring_controller._input_access_row_meta_value({}) == {}


def test_input_access_row_meta_update_builds_single_entry_mapping():
    row = {"device": "USB Keyboard", "path": "/dev/input/event0"}

    update = security_monitoring_controller._input_access_row_meta_update(
        "input-0", row
    )

    assert update == {"input-0": row}
    assert update["input-0"] is not row


def test_input_access_row_meta_update_handles_empty_row():
    assert security_monitoring_controller._input_access_row_meta_update(
        "input-1", {}
    ) == {"input-1": {}}


def test_append_input_access_row_inserts_and_stores_meta():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, values=()):
            self.calls.append((parent, where, values))
            return "input-0"

    app = type("DummyApp", (), {"input_access_row_meta": {}})()
    table = DummyTable()

    security_monitoring_controller._append_input_access_row(
        app,
        table,
        {"device": "USB Keyboard", "path": "/dev/input/event0"},
    )

    assert table.calls == [
        ("", "end", ("USB Keyboard", "-", "-", "-", "-", "/dev/input/event0"))
    ]
    assert app.input_access_row_meta == {
        "input-0": {"device": "USB Keyboard", "path": "/dev/input/event0"}
    }


def test_append_input_access_row_overwrites_existing_meta_for_same_row_id():
    class DummyTable:
        def insert(self, _parent, _where, values=()):
            return "input-0"

    app = type(
        "DummyApp",
        (),
        {"input_access_row_meta": {"input-0": {"device": "Old"}}},
    )()

    security_monitoring_controller._append_input_access_row(
        app,
        DummyTable(),
        {"device": "New", "path": "/dev/input/event1"},
    )

    assert app.input_access_row_meta == {
        "input-0": {"device": "New", "path": "/dev/input/event1"}
    }


def test_inserted_input_access_row_id_returns_inserted_row_id():
    class DummyTable:
        def insert(self, _parent, _where, values=()):
            return "input-7"

    assert (
        security_monitoring_controller._inserted_input_access_row_id(
            DummyTable(),
            {"device": "USB Keyboard", "path": "/dev/input/event0"},
        )
        == "input-7"
    )


def test_inserted_input_access_row_id_preserves_row_forwarding():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, values=()):
            self.calls.append((parent, where, values))
            return "input-1"

    table = DummyTable()

    security_monitoring_controller._inserted_input_access_row_id(
        table,
        {"device": "USB Mouse", "path": "/dev/input/event1"},
    )

    assert table.calls == [
        ("", "end", ("USB Mouse", "-", "-", "-", "-", "/dev/input/event1"))
    ]


def test_log_input_access_refresh_result_logs_message_when_enabled():
    class DummyApp:
        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()
    security_monitoring_controller._log_input_access_refresh_result(
        app, 3, enabled=True
    )

    assert app.logs == ["Input-Zugriffe geprüft: 3 aktiver Zugriff(e)."]


def test_log_input_access_refresh_result_skips_logging_when_disabled():
    class DummyApp:
        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()
    security_monitoring_controller._log_input_access_refresh_result(
        app, 3, enabled=False
    )

    assert app.logs == []


def test_input_access_refresh_log_message_includes_count():
    assert (
        security_monitoring_controller._input_access_refresh_log_message(3)
        == "Input-Zugriffe geprüft: 3 aktiver Zugriff(e)."
    )


def test_input_access_refresh_log_message_preserves_zero_count():
    assert (
        security_monitoring_controller._input_access_refresh_log_message(0)
        == "Input-Zugriffe geprüft: 0 aktiver Zugriff(e)."
    )


def test_input_access_inventory_error_message_includes_exception_text():
    assert (
        security_monitoring_controller._input_access_inventory_error_message(
            RuntimeError("scan failed")
        )
        == "Security: Input-Access-Inventar fehlgeschlagen: scan failed"
    )


def test_input_access_inventory_error_message_accepts_plain_values():
    assert (
        security_monitoring_controller._input_access_inventory_error_message("boom")
        == "Security: Input-Access-Inventar fehlgeschlagen: boom"
    )


def test_input_access_scan_error_message_formats_action_and_error():
    assert (
        security_monitoring_controller._input_access_scan_error_message(
            "Baseline", RuntimeError("kaputt")
        )
        == "Security: Input-Access-Baseline fehlgeschlagen: kaputt"
    )


def test_input_access_scan_error_message_accepts_plain_values():
    assert (
        security_monitoring_controller._input_access_scan_error_message("Scan", "boom")
        == "Security: Input-Access-Scan fehlgeschlagen: boom"
    )


def test_refresh_connected_devices_safe_calls_refresh_callback():
    calls = []

    class DummyApp:
        def refresh_connected_device_table(self):
            calls.append("refreshed")

    assert (
        security_monitoring_controller._refresh_connected_devices_safe(DummyApp())
        is True
    )
    assert calls == ["refreshed"]


def test_refresh_connected_devices_safe_handles_missing_callback():
    assert (
        security_monitoring_controller._refresh_connected_devices_safe(object())
        is False
    )


def test_refresh_security_table_callback_safe_calls_refresh_callback():
    calls = []

    class DummyApp:
        def _refresh_security_table(self):
            calls.append("refreshed")

    assert (
        security_monitoring_controller._refresh_security_table_callback_safe(DummyApp())
        is True
    )
    assert calls == ["refreshed"]


def test_refresh_security_table_callback_safe_handles_missing_callback():
    assert (
        security_monitoring_controller._refresh_security_table_callback_safe(object())
        is False
    )


def test_save_security_baseline_callback_safe_calls_save_callback():
    calls = []

    class DummyApp:
        def _save_security_baseline(self):
            calls.append("saved")

    assert (
        security_monitoring_controller._save_security_baseline_callback_safe(DummyApp())
        is True
    )
    assert calls == ["saved"]


def test_save_security_baseline_callback_safe_handles_missing_callback():
    assert (
        security_monitoring_controller._save_security_baseline_callback_safe(object())
        is False
    )


def test_input_access_scan_state_or_log_returns_scan_result():
    class DummyApp:
        def _scan_input_access_state(self):
            return {"/dev/input/event0": {"123": "python"}}

        def log(self, _message):
            raise AssertionError("log should not be called")

    assert security_monitoring_controller._input_access_scan_state_or_log(
        DummyApp()
    ) == {"/dev/input/event0": {"123": "python"}}


def test_input_access_scan_state_or_log_logs_and_returns_none_on_error():
    class DummyApp:
        def __init__(self):
            self.logs = []

        def _scan_input_access_state(self):
            raise RuntimeError("scan failed")

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()

    assert security_monitoring_controller._input_access_scan_state_or_log(app) is None
    assert app.logs == ["Security: Input-Access-Inventar fehlgeschlagen: scan failed"]


def test_input_access_path_context_returns_device_type_and_processes():
    class DummyApp:
        @staticmethod
        def _device_type_from_path(path):
            return {"path": path}.get("path") and "input-event"

    assert security_monitoring_controller._input_access_path_context(
        DummyApp(),
        {"/dev/input/event0": {"123": "python"}},
        "/dev/input/event0",
    ) == (
        security_monitoring_controller._device_display_name("/dev/input/event0"),
        "input-event",
        {"123": "python"},
    )


def test_input_access_path_context_uses_empty_processes_by_default():
    class DummyApp:
        @staticmethod
        def _device_type_from_path(_path):
            return ""

    assert security_monitoring_controller._input_access_path_context(
        DummyApp(),
        {},
        "/dev/input/event1",
    ) == (
        security_monitoring_controller._device_display_name("/dev/input/event1"),
        "",
        {},
    )


def test_input_access_rows_for_current_path_returns_rows_from_context():
    class DummyApp:
        @staticmethod
        def _device_type_from_path(_path):
            return "input-event"

        @staticmethod
        def _security_input_access_whitelisted(process_name, pid):
            return (process_name, pid) == ("python", 3)

    assert security_monitoring_controller._input_access_rows_for_current_path(
        DummyApp(),
        {"/dev/input/event0": {"20": "bash", "3": "python"}},
        "/dev/input/event0",
    ) == [
        {
            "device": security_monitoring_controller._device_display_name(
                "/dev/input/event0"
            ),
            "process": "python",
            "pid": "3",
            "type": "input-event",
            "status": "bekannt",
            "path": "/dev/input/event0",
        },
        {
            "device": security_monitoring_controller._device_display_name(
                "/dev/input/event0"
            ),
            "process": "bash",
            "pid": "20",
            "type": "input-event",
            "status": "prüfen",
            "path": "/dev/input/event0",
        },
    ]


def test_input_access_rows_for_current_path_handles_missing_processes():
    class DummyApp:
        @staticmethod
        def _device_type_from_path(_path):
            return ""

        @staticmethod
        def _security_input_access_whitelisted(_process_name, _pid):
            raise AssertionError("whitelist should not be called")

    assert (
        security_monitoring_controller._input_access_rows_for_current_path(
            DummyApp(),
            {},
            "/dev/input/event1",
        )
        == []
    )


def test_input_access_sorted_paths_returns_sorted_keys():
    assert security_monitoring_controller._input_access_sorted_paths(
        {"/dev/input/event2": {}, "/dev/input/event0": {}, "/dev/input/event1": {}}
    ) == [
        "/dev/input/event0",
        "/dev/input/event1",
        "/dev/input/event2",
    ]


def test_input_access_sorted_paths_handles_missing_values():
    assert security_monitoring_controller._input_access_sorted_paths(None) == []
    assert security_monitoring_controller._input_access_sorted_paths({}) == []


def test_input_access_pid_number_returns_int_for_digit_strings():
    assert security_monitoring_controller._input_access_pid_number("1234", None) == 1234


def test_input_access_pid_number_returns_default_for_non_digits():
    assert security_monitoring_controller._input_access_pid_number("abc", 0) == 0
    assert security_monitoring_controller._input_access_pid_number("", None) is None


def test_input_access_sorted_process_items_orders_by_numeric_pid():
    assert security_monitoring_controller._input_access_sorted_process_items(
        {"20": "bash", "3": "python", "100": "ssh"}
    ) == [("3", "python"), ("20", "bash"), ("100", "ssh")]


def test_input_access_sorted_process_items_handles_missing_values():
    assert security_monitoring_controller._input_access_sorted_process_items(None) == []
    assert security_monitoring_controller._input_access_sorted_process_items(
        {"abc": "weird", "": "empty", "7": "ok"}
    ) == [("abc", "weird"), ("", "empty"), ("7", "ok")]


def test_input_access_inventory_rows_for_path_builds_sorted_rows():
    class DummyApp:
        @staticmethod
        def _security_input_access_whitelisted(process_name, pid):
            return (process_name, pid) == ("python", 3)

    assert security_monitoring_controller._input_access_inventory_rows_for_path(
        DummyApp(),
        "/dev/input/event0",
        "USB Keyboard",
        "input-event",
        {"20": "bash", "3": "python"},
    ) == [
        {
            "device": "USB Keyboard",
            "process": "python",
            "pid": "3",
            "type": "input-event",
            "status": "bekannt",
            "path": "/dev/input/event0",
        },
        {
            "device": "USB Keyboard",
            "process": "bash",
            "pid": "20",
            "type": "input-event",
            "status": "prüfen",
            "path": "/dev/input/event0",
        },
    ]


def test_input_access_inventory_rows_for_path_handles_empty_processes():
    class DummyApp:
        @staticmethod
        def _security_input_access_whitelisted(_process_name, _pid):
            raise AssertionError("whitelist check should not be called")

    assert (
        security_monitoring_controller._input_access_inventory_rows_for_path(
            DummyApp(),
            "/dev/input/event1",
            "USB Mouse",
            "mouse",
            None,
        )
        == []
    )


def test_input_access_whitelist_status_uses_normalized_pid():
    class DummyApp:
        @staticmethod
        def _security_input_access_whitelisted(process_name, pid):
            return (process_name, pid) == ("python", 7)

    assert (
        security_monitoring_controller._input_access_whitelist_status(
            DummyApp(), "python", "7"
        )
        is True
    )


def test_input_access_whitelist_status_returns_false_for_non_matches():
    class DummyApp:
        @staticmethod
        def _security_input_access_whitelisted(_process_name, _pid):
            return ""

    assert (
        security_monitoring_controller._input_access_whitelist_status(
            DummyApp(), "bash", "abc"
        )
        is False
    )


def test_input_access_process_row_builds_known_row_from_whitelist_status():
    class DummyApp:
        @staticmethod
        def _security_input_access_whitelisted(process_name, pid):
            return (process_name, pid) == ("python", 7)

    assert security_monitoring_controller._input_access_process_row(
        DummyApp(),
        "/dev/input/event0",
        "USB Keyboard",
        "input-event",
        "7",
        "python",
    ) == {
        "device": "USB Keyboard",
        "process": "python",
        "pid": "7",
        "type": "input-event",
        "status": "bekannt",
        "path": "/dev/input/event0",
    }


def test_input_access_process_row_builds_review_row_for_non_whitelisted_process():
    class DummyApp:
        @staticmethod
        def _security_input_access_whitelisted(_process_name, _pid):
            return False

    assert security_monitoring_controller._input_access_process_row(
        DummyApp(),
        "/dev/input/event1",
        "USB Mouse",
        "mouse",
        "abc",
        "bash",
    ) == {
        "device": "USB Mouse",
        "process": "bash",
        "pid": "abc",
        "type": "mouse",
        "status": "prüfen",
        "path": "/dev/input/event1",
    }


def test_input_access_status_label_returns_known_for_whitelisted_processes():
    assert security_monitoring_controller._input_access_status_label(True) == "bekannt"


def test_input_access_status_label_returns_review_for_unknown_processes():
    assert security_monitoring_controller._input_access_status_label(False) == "prüfen"


def test_input_access_table_returns_existing_table():
    table = object()
    app = type("DummyApp", (), {"input_access_table": table})()

    assert security_monitoring_controller._input_access_table(app) is table


def test_input_access_table_returns_none_when_missing():
    app = object()

    assert security_monitoring_controller._input_access_table(app) is None


def test_refresh_input_access_table_if_present_skips_missing_table(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_input_access_table",
        lambda _app: None,
    )

    called = []
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_input_access_table_rows",
        lambda *_args: called.append("rows"),
    )

    security_monitoring_controller._refresh_input_access_table_if_present(
        object(), [{"device": "USB Keyboard"}]
    )

    assert called == []


def test_refresh_input_access_table_if_present_refreshes_existing_table(monkeypatch):
    table = object()
    monkeypatch.setattr(
        security_monitoring_controller,
        "_input_access_table",
        lambda _app: table,
    )

    calls = []
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_input_access_table_rows",
        lambda app, current_table, rows: calls.append((app, current_table, rows)),
    )

    app = object()
    rows = [{"device": "USB Mouse"}]

    security_monitoring_controller._refresh_input_access_table_if_present(app, rows)

    assert calls == [(app, table, rows)]


def test_reset_input_access_row_meta_clears_existing_mapping():
    app = type(
        "DummyApp",
        (),
        {"input_access_row_meta": {"input-0": {"path": "/dev/input/event0"}}},
    )()

    security_monitoring_controller._reset_input_access_row_meta(app)

    assert app.input_access_row_meta == {}


def test_reset_input_access_row_meta_replaces_mapping_object():
    original = {"input-0": {"path": "/dev/input/event0"}}
    app = type("DummyApp", (), {"input_access_row_meta": original})()

    security_monitoring_controller._reset_input_access_row_meta(app)

    assert app.input_access_row_meta == {}
    assert app.input_access_row_meta is not original


def test_refresh_input_access_table_rows_clears_and_populates_table():
    class DummyTable:
        def __init__(self):
            self.deleted = []
            self.calls = []

        def get_children(self):
            return ("input-old",)

        def delete(self, *items):
            self.deleted.extend(items)

        def insert(self, parent, where, values=()):
            row_id = f"input-{len(self.calls)}"
            self.calls.append((parent, where, values))
            return row_id

    app = type(
        "DummyApp",
        (),
        {"input_access_row_meta": {"input-old": {"path": "/dev/input/event0"}}},
    )()
    table = DummyTable()

    security_monitoring_controller._refresh_input_access_table_rows(
        app,
        table,
        [{"device": "USB Keyboard", "path": "/dev/input/event0"}],
    )

    assert table.deleted == ["input-old"]
    assert table.calls == [
        ("", "end", ("USB Keyboard", "-", "-", "-", "-", "/dev/input/event0"))
    ]
    assert app.input_access_row_meta == {
        "input-0": {"device": "USB Keyboard", "path": "/dev/input/event0"}
    }


def test_refresh_input_access_table_rows_handles_empty_rows_after_reset():
    class DummyTable:
        def __init__(self):
            self.deleted = []

        def get_children(self):
            return ("input-old", "input-older")

        def delete(self, *items):
            self.deleted.extend(items)

        def insert(self, *_args, **_kwargs):
            raise AssertionError("insert should not be called")

    app = type(
        "DummyApp",
        (),
        {"input_access_row_meta": {"input-old": {"path": "/dev/input/event0"}}},
    )()
    table = DummyTable()

    security_monitoring_controller._refresh_input_access_table_rows(app, table, [])

    assert table.deleted == ["input-old", "input-older"]
    assert app.input_access_row_meta == {}


def test_input_access_inventory_row_builds_expected_values():
    assert security_monitoring_controller._input_access_inventory_row(
        "/dev/input/event0",
        "USB Keyboard",
        "input-event",
        "1234",
        "python",
        True,
    ) == {
        "device": "USB Keyboard",
        "process": "python",
        "pid": "1234",
        "type": "input-event",
        "status": "bekannt",
        "path": "/dev/input/event0",
    }


def test_input_access_inventory_row_uses_safe_defaults_for_missing_values():
    assert security_monitoring_controller._input_access_inventory_row(
        "/dev/input/event1",
        "USB Mouse",
        "",
        "",
        "",
        False,
    ) == {
        "device": "USB Mouse",
        "process": "-",
        "pid": "-",
        "type": "-",
        "status": "prüfen",
        "path": "/dev/input/event1",
    }


def test_connected_device_status_label_returns_known_for_baseline_devices():
    assert (
        security_monitoring_controller._connected_device_status_label(
            {"known_in_baseline": True}
        )
        == "bekannt"
    )


def test_connected_device_known_in_baseline_returns_true_for_baseline_devices():
    assert (
        security_monitoring_controller._connected_device_known_in_baseline(
            {"known_in_baseline": True}
        )
        is True
    )


def test_connected_device_known_in_baseline_returns_false_by_default():
    assert (
        security_monitoring_controller._connected_device_known_in_baseline({}) is False
    )


def test_connected_device_field_returns_existing_value():
    assert (
        security_monitoring_controller._connected_device_field(
            {"name": "USB Keyboard"}, "name", "Unbekannt"
        )
        == "USB Keyboard"
    )


def test_connected_device_field_returns_default_for_missing_values():
    assert (
        security_monitoring_controller._connected_device_field({}, "name", "Unbekannt")
        == "Unbekannt"
    )


def test_connected_device_field_lines_return_expected_values():
    assert security_monitoring_controller._connected_device_field_lines(
        {
            "type": "input-event",
            "path": "/dev/input/event0",
            "sys_name": "event0",
            "vendor": "046d",
            "product": "c31c",
            "bustype": "USB",
            "phys": "usb-0000:00:14.0-1/input0",
            "uniq": "abc123",
        }
    ) == [
        "Typ: input-event",
        "Pfad: /dev/input/event0",
        "Kennung: event0",
        "Vendor-ID: 046d",
        "Product-ID: c31c",
        "Bus-Typ: USB",
        "Phys: usb-0000:00:14.0-1/input0",
        "Unique-ID: abc123",
    ]


def test_connected_device_field_lines_return_safe_defaults():
    assert security_monitoring_controller._connected_device_field_lines({}) == [
        "Typ: unknown",
        "Pfad: -",
        "Kennung: -",
        "Vendor-ID: -",
        "Product-ID: -",
        "Bus-Typ: -",
        "Phys: -",
        "Unique-ID: -",
    ]


def test_connected_device_name_returns_existing_value():
    assert (
        security_monitoring_controller._connected_device_name({"name": "USB Keyboard"})
        == "USB Keyboard"
    )


def test_connected_device_name_returns_safe_default():
    assert security_monitoring_controller._connected_device_name({}) == "Unbekannt"


def test_normalized_security_state_trims_and_lowercases_values():
    assert (
        security_monitoring_controller._normalized_security_state(" Started ")
        == "started"
    )


def test_normalized_security_state_returns_empty_string_by_default():
    assert security_monitoring_controller._normalized_security_state(None) == ""


def test_normalized_security_filter_mode_returns_given_mode():
    assert (
        security_monitoring_controller._normalized_security_filter_mode("portscan")
        == "portscan"
    )


def test_normalized_security_filter_mode_defaults_to_all():
    assert (
        security_monitoring_controller._normalized_security_filter_mode(None) == "all"
    )


def test_security_filter_label_or_default_returns_known_label():
    assert (
        security_monitoring_controller._security_filter_label_or_default("external")
        == "Nur externe UFW-Blocks"
    )


def test_security_filter_label_or_default_uses_given_fallback():
    assert (
        security_monitoring_controller._security_filter_label_or_default(
            "mystery", "Alle Events"
        )
        == "Alle Events"
    )


def test_connected_device_status_label_returns_new_by_default():
    assert security_monitoring_controller._connected_device_status_label({}) == "neu"


def test_connected_device_row_tags_returns_known_tag_for_baseline_devices():
    assert security_monitoring_controller._connected_device_row_tags(
        {"known_in_baseline": True}
    ) == ("device_known",)


def test_connected_device_row_tags_returns_new_tag_by_default():
    assert security_monitoring_controller._connected_device_row_tags({}) == (
        "device_new",
    )


def test_connected_device_row_values_formats_expected_columns():
    assert security_monitoring_controller._connected_device_row_values(
        {
            "name": "USB Keyboard",
            "type": "input-event",
            "vendor": "046d",
            "product": "c31c",
            "known_in_baseline": True,
            "path": "/dev/input/event0",
        }
    ) == ("USB Keyboard", "input-event", "046d", "c31c", "bekannt", "/dev/input/event0")


def test_connected_device_row_values_use_safe_defaults():
    assert security_monitoring_controller._connected_device_row_values({}) == (
        "Unbekannt",
        "unknown",
        "-",
        "-",
        "neu",
        "-",
    )


def test_connected_device_row_insert_values_returns_formatted_columns():
    assert security_monitoring_controller._connected_device_row_insert_values(
        {
            "name": "USB Keyboard",
            "type": "input-event",
            "vendor": "046d",
            "product": "c31c",
            "known_in_baseline": True,
            "path": "/dev/input/event0",
        }
    ) == ("USB Keyboard", "input-event", "046d", "c31c", "bekannt", "/dev/input/event0")


def test_connected_device_row_insert_values_uses_safe_defaults():
    assert security_monitoring_controller._connected_device_row_insert_values({}) == (
        "Unbekannt",
        "unknown",
        "-",
        "-",
        "neu",
        "-",
    )


def test_connected_device_row_insert_iid_uses_formatted_row_id():
    assert security_monitoring_controller._connected_device_row_insert_iid(2) == "dev-2"


def test_connected_device_row_insert_iid_preserves_negative_indices():
    assert (
        security_monitoring_controller._connected_device_row_insert_iid(-1) == "dev--1"
    )


def test_connected_device_row_insert_position_uses_tree_insert_defaults():
    assert security_monitoring_controller._connected_device_row_insert_position() == (
        "",
        "end",
    )


def test_connected_device_row_insert_position_is_stable():
    first = security_monitoring_controller._connected_device_row_insert_position()
    second = security_monitoring_controller._connected_device_row_insert_position()

    assert first == second == ("", "end")


def test_connected_device_row_insert_spec_combines_position_and_config():
    parent, where, config = (
        security_monitoring_controller._connected_device_row_insert_spec(
            2,
            {
                "name": "USB Mouse",
                "path": "/dev/input/mouse0",
                "sys_name": "mouse0",
                "type": "mouse",
                "known_in_baseline": False,
            },
        )
    )

    assert (parent, where) == ("", "end")
    assert config == {
        "iid": "dev-2",
        "values": ("USB Mouse", "mouse", "-", "-", "neu", "/dev/input/mouse0"),
        "tags": ("device_new",),
    }


def test_connected_device_row_insert_spec_preserves_known_device_values():
    parent, where, config = (
        security_monitoring_controller._connected_device_row_insert_spec(
            0,
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
            },
        )
    )

    assert (parent, where) == ("", "end")
    assert config == {
        "iid": "dev-0",
        "values": (
            "USB Keyboard",
            "input-event",
            "-",
            "-",
            "bekannt",
            "/dev/input/event0",
        ),
        "tags": ("device_known",),
    }


def test_connected_device_row_insert_config_wraps_iid_values_and_tags():
    assert security_monitoring_controller._connected_device_row_insert_config(
        "dev-2",
        ("USB Mouse", "mouse", "-", "-", "neu", "/dev/input/mouse0"),
        ("device_new",),
    ) == {
        "iid": "dev-2",
        "values": ("USB Mouse", "mouse", "-", "-", "neu", "/dev/input/mouse0"),
        "tags": ("device_new",),
    }


def test_connected_device_row_insert_config_preserves_empty_tags():
    assert security_monitoring_controller._connected_device_row_insert_config(
        "dev-0",
        (),
        (),
    ) == {
        "iid": "dev-0",
        "values": (),
        "tags": (),
    }


def test_connected_device_row_insert_tags_returns_known_tag():
    assert security_monitoring_controller._connected_device_row_insert_tags(
        {"known_in_baseline": True}
    ) == ("device_known",)


def test_connected_device_row_insert_tags_returns_new_tag_by_default():
    assert security_monitoring_controller._connected_device_row_insert_tags({}) == (
        "device_new",
    )


def test_security_events_cleared_log_message_matches_expected_text():
    assert (
        security_monitoring_controller._security_events_cleared_log_message()
        == "Security-Events geleert."
    )


def test_security_events_cleared_log_message_mentions_events():
    assert "Events" in (
        security_monitoring_controller._security_events_cleared_log_message()
    )


def test_security_events_clear_cancelled_log_message_matches_expected_text():
    assert (
        security_monitoring_controller._security_events_clear_cancelled_log_message()
        == "Security-Events leeren abgebrochen."
    )


def test_security_events_clear_cancelled_log_message_mentions_abgebrochen():
    assert "abgebrochen" in (
        security_monitoring_controller._security_events_clear_cancelled_log_message()
    )


def test_security_open_tab_refreshes_connected_devices():
    calls = []

    class DummyApp:
        tab_security = "security-tab"

        def _select_security_tab(self, tab):
            calls.append(("select", tab))

        def refresh_connected_device_table(self):
            calls.append(("refresh_devices", True))

    security_monitoring_controller.security_open_tab(DummyApp())

    assert calls == [("select", "security-tab"), ("refresh_devices", True)]


def test_security_refresh_table_action_refreshes_connected_devices():
    calls = []

    class DummyApp:
        security_table = type(
            "DummyTable",
            (),
            {"get_children": lambda self: (), "delete": lambda self, _item: None},
        )()
        security_filter_mode = "all"
        security_aggregated = {}
        security_visible_events = []
        security_events = []
        security_stat_total_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_block_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_scan_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_top_ip_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_top_port_var = type(
            "Var", (), {"set": lambda self, value: None}
        )()
        security_store = None

        def _security_store(self):
            return None

        def refresh_connected_device_table(self):
            calls.append("refresh_devices")

        def log(self, message):
            calls.append(message)

        def tr(self, _key, default):
            return default

    security_monitoring_controller.security_refresh_table_action(DummyApp())

    assert "refresh_devices" in calls
    assert "Security-Tabelle aktualisiert." in calls


def test_finish_security_refresh_table_action_refreshes_devices_and_logs():
    calls = []

    class DummyApp:
        def refresh_connected_device_table(self):
            calls.append("refresh_devices")

        def log(self, message):
            calls.append(message)

        def tr(self, _key, default):
            return default

    security_monitoring_controller._finish_security_refresh_table_action(DummyApp())

    assert calls == ["refresh_devices", "Security-Tabelle aktualisiert."]


def test_apply_security_filter_sets_mode_refreshes_and_logs():
    calls = []

    class DummyApp:
        security_table = type(
            "DummyTable",
            (),
            {"get_children": lambda self: (), "delete": lambda self, _item: None},
        )()
        security_filter_mode = "all"
        security_aggregated = {}
        security_visible_events = []
        security_events = []
        security_stat_total_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_block_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_scan_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_top_ip_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_top_port_var = type(
            "Var", (), {"set": lambda self, value: None}
        )()
        security_store = None

        def _security_store(self):
            return None

        def log(self, message):
            calls.append(message)

        def tr(self, _key, default):
            return default

    app = DummyApp()
    security_monitoring_controller._apply_security_filter(
        app,
        "external",
        "security_log_filter_external",
        "Security-Filter: Nur externe UFW-Blocks.",
    )

    assert app.security_filter_mode == "external"
    assert calls == ["Security-Filter: Nur externe UFW-Blocks."]


def test_run_security_filter_action_sets_mode_refreshes_and_logs(monkeypatch):
    calls = []
    app = type(
        "DummyApp",
        (),
        {
            "security_filter_mode": "all",
            "log": lambda self, message: calls.append(("log", message)),
            "tr": lambda self, _key, default: default,
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "refresh_security_table",
        lambda current_app: calls.append(("refresh", current_app)),
    )

    assert (
        security_monitoring_controller._run_security_filter_action(
            app,
            "external",
            "security_log_filter_external",
            "Security-Filter: Nur externe UFW-Blocks.",
        )
        is None
    )
    assert app.security_filter_mode == "external"
    assert calls == [
        ("refresh", app),
        ("log", "Security-Filter: Nur externe UFW-Blocks."),
    ]


def test_apply_security_filter_falls_back_to_all_for_empty_mode():
    calls = []

    class DummyApp:
        security_table = type(
            "DummyTable",
            (),
            {"get_children": lambda self: (), "delete": lambda self, _item: None},
        )()
        security_filter_mode = "portscan"
        security_aggregated = {}
        security_visible_events = []
        security_events = []
        security_stat_total_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_block_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_scan_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_top_ip_var = type("Var", (), {"set": lambda self, value: None})()
        security_stat_top_port_var = type(
            "Var", (), {"set": lambda self, value: None}
        )()
        security_store = None

        def _security_store(self):
            return None

        def log(self, message):
            calls.append(message)

        def tr(self, _key, default):
            return default

    app = DummyApp()
    security_monitoring_controller._apply_security_filter(
        app,
        "",
        "security_log_filter_all",
        "Security-Filter: Alle Events.",
    )

    assert app.security_filter_mode == "all"
    assert calls == ["Security-Filter: Alle Events."]


def test_security_filter_apply_spec_returns_expected_tuple_for_known_mode():
    assert security_monitoring_controller._security_filter_apply_spec("external") == (
        "external",
        "security_log_filter_external",
        "Security-Filter: Nur externe UFW-Blocks.",
    )


def test_security_filter_apply_spec_falls_back_to_all_for_unknown_mode():
    assert security_monitoring_controller._security_filter_apply_spec("mystery") == (
        "all",
        "security_log_filter_all",
        "Security-Filter: Alle Events.",
    )


def test_security_clear_views_resets_tables_and_detail_text():
    class DummyTable:
        def __init__(self):
            self.deleted = []

        def get_children(self):
            return ("row-1", "row-2")

        def delete(self, *items):
            self.deleted.extend(items)

    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

    class DummyApp:
        security_table = DummyTable()
        security_devices_table = DummyTable()
        input_access_table = DummyTable()
        security_detail = DummyDetail()
        security_visible_events = [{"raw": "demo"}]
        security_table_row_meta = {"sec-0": {"kind": "event", "index": 0}}
        input_access_row_meta = {"input-0": {"path": "/dev/input/event0"}}

        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()
    security_monitoring_controller.security_clear_views(app)

    assert app.security_visible_events == []
    assert app.security_table_row_meta == {}
    assert app.input_access_row_meta == {}
    assert app.security_detail.text == "Ansichten im Guards-Tab wurden geleert."
    assert app.logs == ["Guards-Tab: Ansichten geleert."]


def test_finish_security_clear_views_updates_detail_and_logs():
    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    class DummyApp:
        security_detail = DummyDetail()

        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()
    security_monitoring_controller._finish_security_clear_views(app)

    assert app.security_detail.text == "Ansichten im Guards-Tab wurden geleert."
    assert app.logs == ["Guards-Tab: Ansichten geleert."]


def test_finish_security_clear_views_logs_even_without_detail_widget():
    class DummyApp:
        security_detail = None

        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()
    security_monitoring_controller._finish_security_clear_views(app)

    assert app.logs == ["Guards-Tab: Ansichten geleert."]


def test_build_security_chad_summary_includes_executive_sections():
    class DummyStore:
        @staticmethod
        def compute_stats(events):
            return len(events), 2, 1, "9.9.9.9", "22"

    class DummyApp:
        security_store = DummyStore()
        security_events = [
            {
                "time": "2026-01-01 00:00:00",
                "type": "UFW BLOCK",
                "src": "9.9.9.9",
                "port": "22",
                "proto": "TCP",
                "level": "L2 WARN",
                "action": "BLOCK",
                "external": True,
            },
            {
                "time": "2026-01-01 00:00:01",
                "type": "Portscan-Verdacht",
                "src": "9.9.9.9",
                "port": "4",
                "proto": "-",
                "level": "L3 ALERT",
                "action": "SUSPECT",
                "external": True,
            },
        ]
        security_visible_events = list(security_events)
        security_aggregated = {"DNS": 2}
        security_filter_mode = "relevant"
        security_monitoring = True
        security_log_level = "LOW"
        security_last_alarm = "Portscan-Verdacht"
        integrity_baseline = {"a": {"sha": "x"}}
        device_baseline = {"/dev/input/event1": "input-event"}
        input_access_baseline = {"/dev/input/event1": {"123": "python"}}

    summary = security_monitoring_controller.build_security_chad_summary(DummyApp())

    assert "Executive Summary:" in summary
    assert "- Risiko-Einschätzung: Hoch" in summary
    assert "Sofortmaßnahmen für Chad:" in summary
    assert "Baseline- und Kontextstatus:" in summary
    assert "Wichtigste relevante Events:" in summary
    assert "Letzte externe Events:" in summary
    assert "Letzte Gesamt-Events:" in summary
    assert "Aggregierte interne Kategorien: DNS=2" in summary


def test_build_security_chad_summary_reports_low_risk_when_no_findings():
    class DummyApp:
        security_store = None
        security_events = []
        security_visible_events = []
        security_aggregated = {}
        security_filter_mode = "all"
        security_monitoring = False
        security_log_level = "-"
        security_last_alarm = "–"
        integrity_baseline = {}
        device_baseline = {}
        input_access_baseline = {}

    summary = security_monitoring_controller.build_security_chad_summary(DummyApp())

    assert "- Risiko-Einschätzung: Niedrig" in summary
    assert "Keine akuten Security-Hinweise sichtbar" in summary


def test_build_security_chad_curated_summary_omits_technical_sections():
    class DummyStore:
        @staticmethod
        def compute_stats(events):
            return len(events), 1, 0, "8.8.8.8", "443"

    class DummyApp:
        security_store = DummyStore()
        security_events = [
            {
                "time": "2026-01-01 00:00:00",
                "type": "UFW BLOCK",
                "src": "8.8.8.8",
                "port": "443",
                "proto": "TCP",
                "level": "L2 WARN",
                "action": "BLOCK",
                "external": True,
            }
        ]
        security_visible_events = list(security_events)
        security_aggregated = {}
        security_filter_mode = "all"
        security_monitoring = True
        security_log_level = "LOW"
        security_last_alarm = "Neue BLOCK-Events"
        integrity_baseline = {}
        device_baseline = {}
        input_access_baseline = {}

    summary = security_monitoring_controller.build_security_chad_curated_summary(
        DummyApp()
    )

    assert "Executive Summary:" in summary
    assert "Wichtigste relevante Events:" in summary
    assert "Letzte externe Events:" not in summary
    assert "Letzte Gesamt-Events:" not in summary


def test_security_summary_context_uses_safe_defaults():
    app = type("DummyApp", (), {})()

    context = security_monitoring_controller._security_summary_context(app)

    assert context == {
        "aggregated": {},
        "filter_mode": "all",
        "monitoring_active": False,
        "logging_level": "-",
        "last_alarm": "–",
        "integrity_baseline": {},
        "device_baseline": {},
        "input_access_baseline": {},
    }


def test_security_reporting_context_returns_detached_event_lists():
    app = type("DummyApp", (), {})()
    app.security_events = [{"type": "UFW BLOCK"}]
    app.security_visible_events = [{"type": "Portscan-Verdacht"}]

    context = security_monitoring_controller._security_reporting_context(app)
    context["events"].append({"type": "FILE geändert"})
    context["visible_events"].append({"type": "DEVICE neu"})

    assert app.security_events == [{"type": "UFW BLOCK"}]
    assert app.security_visible_events == [{"type": "Portscan-Verdacht"}]


def test_security_summary_context_uses_reporting_context_fields(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_reporting_context",
        lambda _app: {
            "events": [{"type": "UFW BLOCK"}],
            "visible_events": [{"type": "UFW BLOCK"}],
            "aggregated": {"DNS": 2},
            "filter_mode": "relevant",
            "monitoring_active": True,
            "logging_level": "LOW",
            "event_count": 7,
            "last_alarm": "Alarm",
            "integrity_baseline": {"a": 1},
            "device_baseline": {"b": 2},
            "input_access_baseline": {"c": 3},
        },
    )

    assert security_monitoring_controller._security_summary_context(object()) == {
        "aggregated": {"DNS": 2},
        "filter_mode": "relevant",
        "monitoring_active": True,
        "logging_level": "LOW",
        "last_alarm": "Alarm",
        "integrity_baseline": {"a": 1},
        "device_baseline": {"b": 2},
        "input_access_baseline": {"c": 3},
    }


def test_security_events_returns_detached_event_list():
    app = type("DummyApp", (), {})()
    app.security_events = [{"type": "UFW BLOCK"}]

    events = security_monitoring_controller._security_events(app)
    events.append({"type": "Portscan-Verdacht"})

    assert app.security_events == [{"type": "UFW BLOCK"}]


def test_security_event_count_returns_number_of_events():
    app = type(
        "DummyApp",
        (),
        {"security_events": [{"type": "UFW BLOCK"}, {"type": "Portscan-Verdacht"}]},
    )()

    assert security_monitoring_controller._security_event_count(app) == 2


def test_security_event_count_handles_missing_events():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_event_count(app) == 0


def test_security_aggregated_returns_detached_mapping():
    app = type("DummyApp", (), {"security_aggregated": {"DNS": 2}})()

    aggregated = security_monitoring_controller._security_aggregated(app)
    aggregated["DNS"] = 3

    assert app.security_aggregated == {"DNS": 2}


def test_security_aggregated_handles_missing_state():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_aggregated(app) == {}


def test_security_last_alarm_returns_current_alarm():
    app = type("DummyApp", (), {"security_last_alarm": "Neue BLOCK-Events"})()

    assert (
        security_monitoring_controller._security_last_alarm(app) == "Neue BLOCK-Events"
    )


def test_security_last_alarm_handles_missing_or_empty_alarm():
    empty_app = type("DummyApp", (), {"security_last_alarm": ""})()
    missing_app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_last_alarm(empty_app) == "–"
    assert security_monitoring_controller._security_last_alarm(missing_app) == "–"


def test_security_log_level_returns_current_level():
    app = type("DummyApp", (), {"security_log_level": "LOW"})()

    assert security_monitoring_controller._security_log_level(app) == "LOW"


def test_security_log_level_handles_missing_or_empty_level():
    empty_app = type("DummyApp", (), {"security_log_level": ""})()
    missing_app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_log_level(empty_app) == "-"
    assert security_monitoring_controller._security_log_level(missing_app) == "-"


def test_device_baseline_returns_detached_mapping():
    app = type(
        "DummyApp", (), {"device_baseline": {"/dev/input/event0": "input-event"}}
    )()

    baseline = security_monitoring_controller._device_baseline(app)
    baseline["/dev/input/event0"] = "changed"

    assert app.device_baseline == {"/dev/input/event0": "input-event"}


def test_device_baseline_handles_missing_state():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._device_baseline(app) == {}


def test_store_device_baseline_stores_and_returns_mapping():
    app = type("DummyApp", (), {})()
    baseline = {"/dev/input/event0": "input-event"}

    stored = security_monitoring_controller._store_device_baseline(app, baseline)

    assert stored == baseline
    assert app.device_baseline == baseline


def test_store_device_baseline_preserves_same_object():
    app = type("DummyApp", (), {})()
    baseline = {}

    stored = security_monitoring_controller._store_device_baseline(app, baseline)

    assert stored is baseline
    assert app.device_baseline is baseline


def test_integrity_baseline_returns_detached_mapping():
    app = type("DummyApp", (), {"integrity_baseline": {"a": {"sha": "x"}}})()

    baseline = security_monitoring_controller._integrity_baseline(app)
    baseline["a"] = {"sha": "changed"}

    assert app.integrity_baseline == {"a": {"sha": "x"}}


def test_integrity_baseline_handles_missing_state():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._integrity_baseline(app) == {}


def test_store_integrity_baseline_stores_and_returns_mapping():
    app = type("DummyApp", (), {})()
    baseline = {"watched.txt": {"sha": "abc"}}

    stored = security_monitoring_controller._store_integrity_baseline(app, baseline)

    assert stored == baseline
    assert app.integrity_baseline == baseline


def test_store_integrity_baseline_preserves_same_object():
    app = type("DummyApp", (), {})()
    baseline = {}

    stored = security_monitoring_controller._store_integrity_baseline(app, baseline)

    assert stored is baseline
    assert app.integrity_baseline is baseline


def test_input_access_baseline_returns_detached_mapping():
    app = type(
        "DummyApp",
        (),
        {"input_access_baseline": {"/dev/input/event0": {"123": "python"}}},
    )()

    baseline = security_monitoring_controller._input_access_baseline(app)
    baseline["/dev/input/event0"] = {"321": "bash"}

    assert app.input_access_baseline == {"/dev/input/event0": {"123": "python"}}


def test_input_access_baseline_handles_missing_state():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._input_access_baseline(app) == {}


def test_store_input_access_baseline_stores_and_returns_mapping():
    app = type("DummyApp", (), {})()
    baseline = {"/dev/input/event0": {"123": "python"}}

    stored = security_monitoring_controller._store_input_access_baseline(app, baseline)

    assert stored == baseline
    assert app.input_access_baseline == baseline


def test_store_input_access_baseline_preserves_same_object():
    app = type("DummyApp", (), {})()
    baseline = {}

    stored = security_monitoring_controller._store_input_access_baseline(app, baseline)

    assert stored is baseline
    assert app.input_access_baseline is baseline


def test_input_access_processes_returns_detached_process_mapping():
    processes = security_monitoring_controller._input_access_processes(
        {"/dev/input/event0": {"123": "python"}},
        "/dev/input/event0",
    )
    processes["321"] = "bash"

    assert security_monitoring_controller._input_access_processes(
        {"/dev/input/event0": {"123": "python"}},
        "/dev/input/event0",
    ) == {"123": "python"}


def test_input_access_processes_handles_missing_path_and_mapping():
    assert security_monitoring_controller._input_access_processes({}, "/missing") == {}
    assert (
        security_monitoring_controller._input_access_processes(None, "/missing") == {}
    )


def test_device_type_returns_current_type():
    assert (
        security_monitoring_controller._device_type(
            {"/dev/input/event0": "input-event"},
            "/dev/input/event0",
        )
        == "input-event"
    )


def test_device_type_handles_missing_or_empty_values():
    assert security_monitoring_controller._device_type({}, "/missing") == "unknown"
    assert (
        security_monitoring_controller._device_type(
            {"/dev/input/event0": ""},
            "/dev/input/event0",
        )
        == "unknown"
    )


def test_integrity_entry_token_returns_sha_size_mtime_token():
    assert (
        security_monitoring_controller._integrity_entry_token(
            {"sha": "abc", "size": 42, "mtime": 1.5}
        )
        == "abc|42|1.5"
    )


def test_integrity_entry_token_handles_missing_values():
    assert security_monitoring_controller._integrity_entry_token({}) == "||"
    assert security_monitoring_controller._integrity_entry_token(None) == "||"


def test_integrity_entry_returns_detached_mapping():
    entry = security_monitoring_controller._integrity_entry(
        {"watched.txt": {"sha": "abc", "size": 42, "mtime": 1.5}},
        "watched.txt",
    )
    entry["sha"] = "changed"

    assert security_monitoring_controller._integrity_entry(
        {"watched.txt": {"sha": "abc", "size": 42, "mtime": 1.5}},
        "watched.txt",
    ) == {"sha": "abc", "size": 42, "mtime": 1.5}


def test_integrity_entry_handles_missing_path_and_mapping():
    assert security_monitoring_controller._integrity_entry({}, "missing.txt") == {}
    assert security_monitoring_controller._integrity_entry(None, "missing.txt") == {}


def test_mapping_paths_returns_key_set():
    assert security_monitoring_controller._mapping_paths({"a": 1, "b": 2}) == {
        "a",
        "b",
    }


def test_mapping_paths_handles_missing_and_empty_mapping():
    assert security_monitoring_controller._mapping_paths({}) == set()
    assert security_monitoring_controller._mapping_paths(None) == set()


def test_mapping_path_sets_returns_old_and_new_path_sets():
    assert security_monitoring_controller._mapping_path_sets(
        {"a": 1, "b": 2},
        {"b": 3, "c": 4},
    ) == ({"a", "b"}, {"b", "c"})


def test_mapping_path_sets_handles_missing_mappings():
    assert security_monitoring_controller._mapping_path_sets(None, {}) == (set(), set())


def test_input_access_change_token_formats_change_payload():
    assert (
        security_monitoring_controller._input_access_change_token(
            "start",
            "python",
            "/dev/input/event0",
            "123",
            999,
        )
        == "start|python|/dev/input/event0|123|999"
    )


def test_input_access_change_token_handles_plain_values():
    assert (
        security_monitoring_controller._input_access_change_token(
            "stop",
            "-",
            "/dev/input/event1",
            "-",
            "token",
        )
        == "stop|-|/dev/input/event1|-|token"
    )


def test_append_input_access_change_event_appends_created_event():
    class DummyApp:
        @staticmethod
        def _security_create_input_access_event(kind, path, pid, pname, token):
            return {
                "kind": kind,
                "path": path,
                "pid": pid,
                "pname": pname,
                "token": token,
            }

    events = []

    security_monitoring_controller._append_input_access_change_event(
        events,
        DummyApp(),
        "INPUT ACCESS START",
        "start",
        "/dev/input/event0",
        "123",
        "python",
        999,
    )

    assert events == [
        {
            "kind": "INPUT ACCESS START",
            "path": "/dev/input/event0",
            "pid": "123",
            "pname": "python",
            "token": "start|python|/dev/input/event0|123|999",
        }
    ]


def test_append_input_access_change_event_handles_plain_values():
    class DummyApp:
        @staticmethod
        def _security_create_input_access_event(kind, path, pid, pname, token):
            return (kind, path, pid, pname, token)

    events = []

    security_monitoring_controller._append_input_access_change_event(
        events,
        DummyApp(),
        "INPUT ACCESS STOP",
        "stop",
        "/dev/input/event1",
        "-",
        "-",
        "token",
    )

    assert events == [
        (
            "INPUT ACCESS STOP",
            "/dev/input/event1",
            "-",
            "-",
            "stop|-|/dev/input/event1|-|token",
        )
    ]


def test_append_integrity_change_event_appends_created_event():
    class DummyApp:
        @staticmethod
        def _security_create_file_event(kind, path, token):
            return {"kind": kind, "path": path, "token": token}

    events = []

    security_monitoring_controller._append_integrity_change_event(
        events,
        DummyApp(),
        "FILE NEW",
        "watched.txt",
        {"sha": "abc", "size": 42, "mtime": 1.5},
    )

    assert events == [
        {"kind": "FILE NEW", "path": "watched.txt", "token": "abc|42|1.5"}
    ]


def test_append_integrity_change_event_handles_missing_values():
    class DummyApp:
        @staticmethod
        def _security_create_file_event(kind, path, token):
            return (kind, path, token)

    events = []

    security_monitoring_controller._append_integrity_change_event(
        events,
        DummyApp(),
        "FILE DELETED",
        "missing.txt",
        {},
    )

    assert events == [("FILE DELETED", "missing.txt", "||")]


def test_append_device_change_event_appends_created_event():
    class DummyApp:
        @staticmethod
        def _security_create_device_event(kind, path, device_type, token):
            return {
                "kind": kind,
                "path": path,
                "device_type": device_type,
                "token": token,
            }

    events = []

    security_monitoring_controller._append_device_change_event(
        events,
        DummyApp(),
        "DEVICE NEW",
        "new",
        "/dev/input/event0",
        "input-event",
    )

    assert events == [
        {
            "kind": "DEVICE NEW",
            "path": "/dev/input/event0",
            "device_type": "input-event",
            "token": "new|input-event",
        }
    ]


def test_append_device_change_event_handles_plain_values():
    class DummyApp:
        @staticmethod
        def _security_create_device_event(kind, path, device_type, token):
            return (kind, path, device_type, token)

    events = []

    security_monitoring_controller._append_device_change_event(
        events,
        DummyApp(),
        "DEVICE REMOVED",
        "removed",
        "/dev/input/event1",
        "unknown",
    )

    assert events == [
        ("DEVICE REMOVED", "/dev/input/event1", "unknown", "removed|unknown")
    ]


def test_integrity_file_entry_returns_sha_size_mtime_mapping():
    class DummyApp:
        @staticmethod
        def hash_file_sha256(path):
            return f"sha:{path}"

    stat_result = type("Stat", (), {"st_size": 42, "st_mtime": 1.5})()

    assert security_monitoring_controller._integrity_file_entry(
        DummyApp(),
        "watched.txt",
        stat_result,
    ) == {
        "sha": "sha:watched.txt",
        "size": 42,
        "mtime": 1.5,
    }


def test_integrity_file_entry_preserves_zero_values():
    class DummyApp:
        @staticmethod
        def hash_file_sha256(_path):
            return ""

    stat_result = type("Stat", (), {"st_size": 0, "st_mtime": 0.0})()

    assert security_monitoring_controller._integrity_file_entry(
        DummyApp(),
        "empty.txt",
        stat_result,
    ) == {
        "sha": "",
        "size": 0,
        "mtime": 0.0,
    }


def test_integrity_scan_state_collects_existing_non_ignored_files(tmp_path):
    keep_path = tmp_path / "keep.txt"
    ignored_path = tmp_path / "ignored.txt"
    keep_path.write_text("keep\n", encoding="utf-8")
    ignored_path.write_text("ignore\n", encoding="utf-8")

    class DummyApp:
        @staticmethod
        def _integrity_watch_files():
            return [str(keep_path), str(ignored_path)]

        @staticmethod
        def hash_file_sha256(path):
            return f"sha:{path}"

        netmon_config_dir = ""
        netmon_state_dir = ""

    state = security_monitoring_controller._integrity_scan_state(DummyApp())

    assert str(keep_path) in state
    assert str(ignored_path) in state
    assert state[str(keep_path)]["sha"] == f"sha:{keep_path}"


def test_integrity_scan_state_skips_ignored_missing_and_broken_files(
    tmp_path, monkeypatch
):
    keep_path = tmp_path / "keep.txt"
    ignored_path = tmp_path / "ignored.txt"
    broken_path = tmp_path / "broken.txt"
    keep_path.write_text("keep\n", encoding="utf-8")
    ignored_path.write_text("ignore\n", encoding="utf-8")
    broken_path.write_text("broken\n", encoding="utf-8")

    real_stat = security_monitoring_controller.os.stat

    def fake_stat(path, *args, **kwargs):
        if path == str(broken_path):
            raise OSError("broken")
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(security_monitoring_controller.os, "stat", fake_stat)
    monkeypatch.setattr(
        security_monitoring_controller,
        "security_integrity_ignore_path",
        lambda _app, path: path == str(ignored_path),
    )

    class DummyApp:
        @staticmethod
        def _integrity_watch_files():
            return [
                str(keep_path),
                str(ignored_path),
                str(broken_path),
                str(tmp_path / "missing.txt"),
            ]

        @staticmethod
        def hash_file_sha256(path):
            return f"sha:{path}"

    assert security_monitoring_controller._integrity_scan_state(DummyApp()) == {
        str(keep_path): {
            "sha": f"sha:{keep_path}",
            "size": keep_path.stat().st_size,
            "mtime": keep_path.stat().st_mtime,
        }
    }


def test_device_type_for_path_returns_device_type_text():
    class DummyApp:
        @staticmethod
        def _device_type_from_path(path):
            return f"type:{path}"

    assert (
        security_monitoring_controller._device_type_for_path(
            DummyApp(), "/dev/input/event0"
        )
        == "type:/dev/input/event0"
    )


def test_device_type_for_path_normalizes_non_string_values():
    class DummyApp:
        @staticmethod
        def _device_type_from_path(_path):
            return 7

    assert (
        security_monitoring_controller._device_type_for_path(
            DummyApp(), "/dev/input/event1"
        )
        == "7"
    )


def test_device_watch_paths_for_returns_app_watch_paths():
    class DummyApp:
        @staticmethod
        def _device_watch_paths():
            return ["/dev/input/event0", "/sys/class/input/mouse0"]

    assert security_monitoring_controller._device_watch_paths_for(DummyApp()) == [
        "/dev/input/event0",
        "/sys/class/input/mouse0",
    ]


def test_device_watch_paths_for_preserves_empty_watch_paths():
    class DummyApp:
        @staticmethod
        def _device_watch_paths():
            return []

    assert security_monitoring_controller._device_watch_paths_for(DummyApp()) == []


def test_device_type_mapping_builds_mapping_from_watch_paths():
    class DummyApp:
        @staticmethod
        def _device_watch_paths():
            return ["/dev/input/event0", "/sys/class/input/mouse0"]

        @staticmethod
        def _device_type_from_path(path):
            return f"type:{path.rsplit('/', 1)[-1]}"

    assert security_monitoring_controller._device_type_mapping(DummyApp()) == {
        "/dev/input/event0": "type:event0",
        "/sys/class/input/mouse0": "type:mouse0",
    }


def test_device_type_mapping_handles_empty_watch_paths():
    class DummyApp:
        @staticmethod
        def _device_watch_paths():
            return []

        @staticmethod
        def _device_type_from_path(_path):
            raise AssertionError("device type lookup should not be called")

    assert security_monitoring_controller._device_type_mapping(DummyApp()) == {}


def test_connected_device_entry_builds_expected_mapping(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_display_name",
        lambda path: f"name:{path}",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_type_for_path",
        lambda _app, path: f"type:{path}",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_metadata",
        lambda path: {"vendor": f"vendor:{path}", "product": "-"},
    )

    entry = security_monitoring_controller._connected_device_entry(
        object(),
        "/dev/input/event0",
        "event0",
        "/dev/input/event0",
        {"/dev/input/event0": "input-event"},
    )

    assert entry == {
        "name": "name:/dev/input/event0",
        "path": "/dev/input/event0",
        "sys_name": "event0",
        "type": "type:/dev/input/event0",
        "known_in_baseline": True,
        "vendor": "vendor:/dev/input/event0",
        "product": "-",
    }


def test_connected_device_entry_marks_missing_baseline_as_unknown(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_display_name",
        lambda _path: "USB Device",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_type_for_path",
        lambda _app, _path: "hid",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_metadata",
        lambda _path: {},
    )

    entry = security_monitoring_controller._connected_device_entry(
        object(),
        "/sys/class/input/event0",
        "event0",
        "/dev/input/event0",
        {},
    )

    assert entry["known_in_baseline"] is False
    assert entry["path"] == "/dev/input/event0"


def test_preferred_connected_device_path_prefers_existing_dev_input_path():
    assert (
        security_monitoring_controller._preferred_connected_device_path(
            "/sys/class/input/event0",
            {"path": "/dev/input/event0"},
        )
        == "/dev/input/event0"
    )


def test_preferred_connected_device_path_prefers_current_dev_input_path():
    assert (
        security_monitoring_controller._preferred_connected_device_path(
            "/dev/input/event1",
            {"path": "/sys/class/input/event1"},
        )
        == "/dev/input/event1"
    )


def test_device_base_name_returns_stripped_basename():
    assert (
        security_monitoring_controller._device_base_name(" /dev/input/event0 ".strip())
        == "event0"
    )


def test_device_base_name_handles_empty_values():
    assert security_monitoring_controller._device_base_name("") == ""
    assert security_monitoring_controller._device_base_name(None) == ""


def test_normalized_device_name_lowercases_stripped_basename():
    assert (
        security_monitoring_controller._normalized_device_name(
            " /dev/input/MOUSE0 ".strip()
        )
        == "mouse0"
    )


def test_normalized_device_name_handles_empty_values():
    assert security_monitoring_controller._normalized_device_name("") == ""
    assert security_monitoring_controller._normalized_device_name(None) == ""


def test_store_connected_device_uses_existing_entry_for_preferred_path(monkeypatch):
    app = object()
    devices = {"event0": {"path": "/dev/input/event0", "previous": True}}
    baseline = {"/dev/input/event0": "known"}
    captured = {}

    def fake_preferred_path(path, existing):
        captured["preferred_args"] = (path, existing)
        return "/dev/input/event0"

    def fake_entry(entry_app, path, base, preferred_path, entry_baseline):
        captured["entry_args"] = (
            entry_app,
            path,
            base,
            preferred_path,
            entry_baseline,
        )
        return {"path": preferred_path, "sys_name": base}

    monkeypatch.setattr(
        security_monitoring_controller,
        "_preferred_connected_device_path",
        fake_preferred_path,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_connected_device_entry",
        fake_entry,
    )

    security_monitoring_controller._store_connected_device(
        devices,
        app,
        "/sys/class/input/event0",
        "event0",
        baseline,
    )

    assert captured["preferred_args"] == (
        "/sys/class/input/event0",
        {"path": "/dev/input/event0", "previous": True},
    )
    assert captured["entry_args"] == (
        app,
        "/sys/class/input/event0",
        "event0",
        "/dev/input/event0",
        baseline,
    )
    assert devices["event0"] == {"path": "/dev/input/event0", "sys_name": "event0"}


def test_store_connected_device_creates_new_entry_for_unknown_base(monkeypatch):
    captured = {}

    def fake_preferred_path(path, existing):
        captured["preferred_args"] = (path, existing)
        return "/dev/input/event1"

    monkeypatch.setattr(
        security_monitoring_controller,
        "_preferred_connected_device_path",
        fake_preferred_path,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_connected_device_entry",
        lambda _app, _path, base, preferred_path, _baseline: {
            "sys_name": base,
            "path": preferred_path,
        },
    )

    devices = {}
    security_monitoring_controller._store_connected_device(
        devices,
        object(),
        "/dev/input/event1",
        "event1",
        {},
    )

    assert captured["preferred_args"] == ("/dev/input/event1", None)
    assert devices == {"event1": {"sys_name": "event1", "path": "/dev/input/event1"}}


def test_sorted_connected_device_inventory_orders_by_sys_name_key():
    devices = {
        "mouse0": {"sys_name": "mouse0"},
        "event0": {"sys_name": "event0"},
    }

    assert security_monitoring_controller._sorted_connected_device_inventory(
        devices
    ) == [
        {"sys_name": "event0"},
        {"sys_name": "mouse0"},
    ]


def test_sorted_connected_device_inventory_handles_empty_mapping():
    assert security_monitoring_controller._sorted_connected_device_inventory({}) == []


def test_scan_input_access_changes_skips_whitelisted_new_process(monkeypatch):
    class DummyApp:
        input_access_baseline = {}

        @staticmethod
        def _scan_input_access_state():
            return {"/dev/input/event0": {"7": "python"}}

        @staticmethod
        def _security_input_access_whitelisted(_process_name, _pid):
            raise AssertionError("direct whitelist call should not happen")

        @staticmethod
        def _security_create_input_access_event(*_args):
            raise AssertionError("event should not be created")

        @staticmethod
        def log(_message):
            raise AssertionError("log should not be called")

    monkeypatch.setattr(
        security_monitoring_controller,
        "_input_access_whitelist_status",
        lambda _app, process_name, pid: (process_name, pid) == ("python", "7"),
    )

    assert security_monitoring_controller.scan_input_access_changes(DummyApp()) == []


def test_scan_input_access_changes_uses_whitelist_helper_for_stopped_process(
    monkeypatch,
):
    class DummyApp:
        input_access_baseline = {"/dev/input/event0": {"9": "bash"}}

        @staticmethod
        def _scan_input_access_state():
            return {}

        @staticmethod
        def _security_input_access_whitelisted(_process_name, _pid):
            raise AssertionError("direct whitelist call should not happen")

        @staticmethod
        def _security_create_input_access_event(*_args):
            raise AssertionError("event should not be created")

        @staticmethod
        def log(_message):
            raise AssertionError("log should not be called")

    monkeypatch.setattr(
        security_monitoring_controller,
        "_input_access_whitelist_status",
        lambda _app, process_name, pid: (process_name, pid) == ("bash", "9"),
    )

    assert security_monitoring_controller.scan_input_access_changes(DummyApp()) == []


def test_scan_input_access_changes_uses_sorted_items_for_start_events(monkeypatch):
    class DummyApp:
        input_access_baseline = {}

        @staticmethod
        def _scan_input_access_state():
            return {"/dev/input/event0": {"abc": "shell", "2": "python"}}

        @staticmethod
        def log(_message):
            raise AssertionError("log should not be called")

    monkeypatch.setattr(
        security_monitoring_controller,
        "_input_access_whitelist_status",
        lambda *_args: False,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_input_access_change_event",
        lambda events, _app, _kind, _change, _path, pid, pname, _token: events.append(
            (pid, pname)
        ),
    )

    app = DummyApp()
    result = security_monitoring_controller.scan_input_access_changes(app)

    assert result == [("abc", "shell"), ("2", "python")]
    assert app.input_access_baseline == {
        "/dev/input/event0": {"abc": "shell", "2": "python"}
    }


def test_scan_input_access_changes_orders_stop_events_by_sorted_process_items(
    monkeypatch,
):
    class DummyApp:
        input_access_baseline = {"/dev/input/event0": {"abc": "shell", "2": "python"}}

        @staticmethod
        def _scan_input_access_state():
            return {}

        @staticmethod
        def log(_message):
            raise AssertionError("log should not be called")

    monkeypatch.setattr(
        security_monitoring_controller,
        "_input_access_whitelist_status",
        lambda *_args: False,
    )

    monkeypatch.setattr(
        security_monitoring_controller,
        "_append_input_access_change_event",
        lambda sink, _app, _kind, _change, _path, pid, pname, _token: sink.append(
            (pid, pname)
        ),
    )

    app = DummyApp()
    result = security_monitoring_controller.scan_input_access_changes(app)

    assert result == [("abc", "shell"), ("2", "python")]
    assert app.input_access_baseline == {}


def test_security_baseline_payload_returns_detached_baseline_mappings():
    app = type(
        "DummyApp",
        (),
        {
            "integrity_baseline": {"watched.txt": {"sha": "abc"}},
            "device_baseline": {"/dev/input/event0": "input-event"},
            "input_access_baseline": {"/dev/input/event0": {"123": "python"}},
        },
    )()

    payload = security_monitoring_controller._security_baseline_payload(
        app, "2026-06-06T12:00:00"
    )
    payload["integrity"]["watched.txt"] = {"sha": "changed"}
    payload["device"]["/dev/input/event0"] = "changed"
    payload["input_access"]["/dev/input/event0"] = {"321": "bash"}

    assert app.integrity_baseline == {"watched.txt": {"sha": "abc"}}
    assert app.device_baseline == {"/dev/input/event0": "input-event"}
    assert app.input_access_baseline == {"/dev/input/event0": {"123": "python"}}
    assert payload["ts"] == "2026-06-06T12:00:00"


def test_security_baseline_payload_handles_missing_state():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_baseline_payload(
        app, "2026-06-06T12:00:00"
    ) == {
        "integrity": {},
        "device": {},
        "input_access": {},
        "lynis_security_baseline": {},
        "ts": "2026-06-06T12:00:00",
    }


def test_current_security_baseline_payload_uses_current_iso_timestamp(monkeypatch):
    class DummyNow:
        def isoformat(self):
            return "2026-06-06T15:30:00"

    monkeypatch.setattr(
        security_monitoring_controller,
        "datetime",
        type("DummyDateTime", (), {"now": staticmethod(lambda: DummyNow())}),
    )

    app = type("DummyApp", (), {"integrity_baseline": {"a": {"sha": "1"}}})()

    assert security_monitoring_controller._current_security_baseline_payload(app) == {
        "integrity": {"a": {"sha": "1"}},
        "device": {},
        "input_access": {},
        "lynis_security_baseline": {},
        "ts": "2026-06-06T15:30:00",
    }


def test_current_security_baseline_payload_delegates_to_payload_helper(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "datetime",
        type(
            "DummyDateTime",
            (),
            {
                "now": staticmethod(
                    lambda: type(
                        "DummyNow",
                        (),
                        {"isoformat": lambda self: "2026-06-06T16:45:00"},
                    )()
                )
            },
        ),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_payload",
        lambda app, timestamp: calls.append((app, timestamp)) or {"ts": timestamp},
    )

    app = object()

    assert security_monitoring_controller._current_security_baseline_payload(app) == {
        "ts": "2026-06-06T16:45:00"
    }
    assert calls == [(app, "2026-06-06T16:45:00")]


def test_security_baseline_state_returns_detached_snapshot():
    app = type(
        "DummyApp",
        (),
        {
            "integrity_baseline": {"watched.txt": {"sha": "abc"}},
            "device_baseline": {"/dev/input/event0": "input-event"},
            "input_access_baseline": {"/dev/input/event0": {"123": "python"}},
        },
    )()

    snapshot = security_monitoring_controller._security_baseline_state(app)
    snapshot["integrity"]["watched.txt"] = {"sha": "changed"}
    snapshot["device"]["/dev/input/event0"] = "changed"
    snapshot["input_access"]["/dev/input/event0"] = {"999": "bash"}

    assert app.integrity_baseline == {"watched.txt": {"sha": "abc"}}
    assert app.device_baseline == {"/dev/input/event0": "input-event"}
    assert app.input_access_baseline == {"/dev/input/event0": {"123": "python"}}


def test_security_baseline_state_handles_missing_state():
    assert security_monitoring_controller._security_baseline_state(object()) == {
        "integrity": {},
        "device": {},
        "input_access": {},
    }


def test_write_security_baseline_uses_project_json_options(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "safe_write_json",
        lambda path, payload, indent, ensure_ascii: calls.append(
            (path, payload, indent, ensure_ascii)
        )
        or (True, None),
    )

    result = security_monitoring_controller._write_security_baseline(
        "/tmp/security.json",
        {"integrity": {"a": 1}},
    )

    assert result == (True, None)
    assert calls == [("/tmp/security.json", {"integrity": {"a": 1}}, 2, False)]


def test_write_security_baseline_returns_safe_write_result(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "safe_write_json",
        lambda *_args, **_kwargs: (False, "disk full"),
    )

    assert security_monitoring_controller._write_security_baseline(
        "/tmp/security.json",
        {"device": {}},
    ) == (False, "disk full")


def test_load_security_baseline_data_for_uses_current_baseline_path(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda current_app: calls.append(("path", current_app)) or "/tmp/security.json",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_security_baseline_data",
        lambda path: calls.append(("load", path)) or {"integrity": {"a": 1}},
    )

    assert security_monitoring_controller._load_security_baseline_data_for(app) == {
        "integrity": {"a": 1}
    }
    assert calls == [("path", app), ("load", "/tmp/security.json")]


def test_load_security_baseline_data_for_returns_loaded_mapping(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda _app: "/tmp/security.json",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_security_baseline_data",
        lambda _path: {"device": {"/dev/input/event0": "kbd"}},
    )

    assert security_monitoring_controller._load_security_baseline_data_for(
        object()
    ) == {"device": {"/dev/input/event0": "kbd"}}


def test_security_baseline_load_context_skips_missing_file(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_exists",
        lambda _app: False,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_security_baseline_data_for",
        lambda _app: (_ for _ in ()).throw(AssertionError("should not load")),
    )

    assert security_monitoring_controller._security_baseline_load_context(object()) == (
        False,
        None,
    )


def test_security_baseline_load_context_returns_loaded_data(monkeypatch):
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_exists",
        lambda current_app: True,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_security_baseline_data_for",
        lambda current_app: {"integrity": {"a": 1}},
    )

    assert security_monitoring_controller._security_baseline_load_context(app) == (
        True,
        {"integrity": {"a": 1}},
    )


def test_security_baseline_exists_checks_current_path(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda current_app: calls.append(("path", current_app)) or "/tmp/security.json",
    )
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "isfile",
        lambda path: calls.append(("isfile", path)) or True,
    )

    assert security_monitoring_controller._security_baseline_exists(app) is True
    assert calls == [("path", app), ("isfile", "/tmp/security.json")]


def test_security_baseline_exists_returns_false_for_missing_file(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda _app: "/tmp/missing.json",
    )
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "isfile",
        lambda _path: False,
    )

    assert security_monitoring_controller._security_baseline_exists(object()) is False


def test_restore_loaded_security_baseline_restores_then_logs(monkeypatch):
    calls = []
    app = object()
    data = {"integrity": {"a": 1}}

    monkeypatch.setattr(
        security_monitoring_controller,
        "_restore_security_baselines",
        lambda current_app, current_data: calls.append(
            ("restore", current_app, current_data)
        )
        or {"raw": True},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_log_security_baseline_pruned_if_needed",
        lambda current_app, raw_integrity: calls.append(
            ("log", current_app, raw_integrity)
        ),
    )

    assert (
        security_monitoring_controller._restore_loaded_security_baseline(app, data)
        is None
    )
    assert calls == [
        ("restore", app, data),
        ("log", app, {"raw": True}),
    ]


def test_restore_loaded_security_baseline_passes_restore_result_to_log(monkeypatch):
    forwarded = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_restore_security_baselines",
        lambda *_args: {"integrity": {"x": 1}},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_log_security_baseline_pruned_if_needed",
        lambda _app, raw_integrity: forwarded.append(raw_integrity),
    )

    security_monitoring_controller._restore_loaded_security_baseline(
        object(),
        {"integrity": {"x": 1}},
    )

    assert forwarded == [{"integrity": {"x": 1}}]


def test_load_existing_security_baseline_skips_when_file_is_missing(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_exists",
        lambda _app: False,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_security_baseline_data_for",
        lambda _app: calls.append("load") or {},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_restore_loaded_security_baseline",
        lambda *_args: calls.append("restore"),
    )

    assert (
        security_monitoring_controller._load_existing_security_baseline(object())
        is False
    )
    assert calls == []


def test_run_security_baseline_load_uses_context_and_pipeline(monkeypatch):
    calls = []
    app = object()
    context = (True, {"integrity": {"a": 1}})

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_load_context",
        lambda current_app: calls.append(("context", current_app)) or context,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_security_baseline_pipeline",
        lambda current_app, exists, data: calls.append(
            ("pipeline", current_app, exists, data)
        )
        or True,
    )

    assert security_monitoring_controller._run_security_baseline_load(app) is True
    assert calls == [
        ("context", app),
        ("pipeline", app, True, {"integrity": {"a": 1}}),
    ]


def test_load_security_baseline_pipeline_skips_restore_when_missing():
    calls = []

    assert (
        security_monitoring_controller._load_security_baseline_pipeline(
            object(),
            False,
            {"integrity": {"a": 1}},
        )
        is False
    )
    assert calls == []


def test_load_security_baseline_pipeline_restores_when_present(monkeypatch):
    calls = []
    app = object()
    data = {"integrity": {"a": 1}}

    monkeypatch.setattr(
        security_monitoring_controller,
        "_restore_loaded_security_baseline",
        lambda current_app, current_data: calls.append((current_app, current_data)),
    )

    assert (
        security_monitoring_controller._load_security_baseline_pipeline(
            app,
            True,
            data,
        )
        is True
    )
    assert calls == [(app, data)]


def test_load_existing_security_baseline_loads_and_restores_when_present(monkeypatch):
    calls = []
    app = object()
    data = {"integrity": {"a": 1}}

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_exists",
        lambda current_app: calls.append(("exists", current_app)) or True,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_security_baseline_data_for",
        lambda current_app: calls.append(("load", current_app)) or data,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_restore_loaded_security_baseline",
        lambda current_app, current_data: calls.append(
            ("restore", current_app, current_data)
        ),
    )

    assert security_monitoring_controller._load_existing_security_baseline(app) is True
    assert calls == [
        ("exists", app),
        ("load", app),
        ("restore", app, data),
    ]


def test_write_current_security_baseline_uses_path_payload_and_writer(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda current_app: calls.append(("path", current_app)) or "/tmp/security.json",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_current_security_baseline_payload",
        lambda current_app: calls.append(("payload", current_app)) or {"ts": "now"},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_write_security_baseline",
        lambda path, payload: calls.append(("write", path, payload)) or (True, None),
    )

    assert security_monitoring_controller._write_current_security_baseline(app) == (
        True,
        None,
    )
    assert calls == [
        ("path", app),
        ("payload", app),
        ("write", "/tmp/security.json", {"ts": "now"}),
    ]


def test_security_baseline_write_context_returns_path_and_payload(monkeypatch):
    app = object()
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda current_app: calls.append(("path", current_app)) or "/tmp/security.json",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_current_security_baseline_payload",
        lambda current_app: calls.append(("payload", current_app)) or {"ts": "now"},
    )

    assert security_monitoring_controller._security_baseline_write_context(app) == (
        "/tmp/security.json",
        {"ts": "now"},
    )
    assert calls == [("path", app), ("payload", app)]


def test_write_current_security_baseline_returns_writer_result(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda _app: "/tmp/security.json",
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_current_security_baseline_payload",
        lambda _app: {"integrity": {}},
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_write_security_baseline",
        lambda _path, _payload: (False, "io error"),
    )

    assert security_monitoring_controller._write_current_security_baseline(
        object()
    ) == (
        False,
        "io error",
    )


def test_run_security_baseline_save_uses_writer_result_and_pipeline(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_write_current_security_baseline",
        lambda current_app: calls.append(("write", current_app))
        or (False, "disk full"),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_save_security_baseline_pipeline",
        lambda current_app, ok, err: calls.append(("pipeline", current_app, ok, err))
        or False,
    )

    assert security_monitoring_controller._run_security_baseline_save(app) is False
    assert calls == [
        ("write", app),
        ("pipeline", app, False, "disk full"),
    ]


def test_save_security_baseline_pipeline_returns_true_without_logging(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_log_security_baseline_save_failure",
        lambda *_args: (_ for _ in ()).throw(AssertionError("should not log")),
    )

    assert (
        security_monitoring_controller._save_security_baseline_pipeline(
            object(),
            True,
            None,
        )
        is True
    )


def test_save_security_baseline_pipeline_logs_and_returns_false(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_log_security_baseline_save_failure",
        lambda current_app, error: calls.append((current_app, error)),
    )

    assert (
        security_monitoring_controller._save_security_baseline_pipeline(
            app,
            False,
            "disk full",
        )
        is False
    )
    assert calls == [(app, "disk full")]


def test_log_security_baseline_save_failure_formats_and_logs_message(monkeypatch):
    messages = []
    app = type(
        "DummyApp", (), {"log_debug": lambda self, message: messages.append(message)}
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_save_error_message",
        lambda error: f"ERR:{error}",
    )

    assert (
        security_monitoring_controller._log_security_baseline_save_failure(
            app, "kaputt"
        )
        is None
    )
    assert messages == ["ERR:kaputt"]


def test_log_security_baseline_save_failure_passes_error_to_message_helper(
    monkeypatch,
):
    forwarded = []
    app = type("DummyApp", (), {"log_debug": lambda self, _message: None})()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_save_error_message",
        lambda error: forwarded.append(error) or "formatted",
    )

    security_monitoring_controller._log_security_baseline_save_failure(
        app,
        ValueError("disk full"),
    )

    assert len(forwarded) == 1
    assert isinstance(forwarded[0], ValueError)
    assert str(forwarded[0]) == "disk full"


def test_save_current_security_baseline_result_returns_true_without_logging(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_write_current_security_baseline",
        lambda _app: calls.append("write") or (True, None),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_log_security_baseline_save_failure",
        lambda *_args: calls.append("log"),
    )

    assert (
        security_monitoring_controller._save_current_security_baseline_result(object())
        is True
    )
    assert calls == ["write"]


def test_save_current_security_baseline_result_logs_and_returns_false(monkeypatch):
    calls = []
    app = object()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_write_current_security_baseline",
        lambda current_app: calls.append(("write", current_app)) or (False, "kaputt"),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_log_security_baseline_save_failure",
        lambda current_app, error: calls.append(("log", current_app, error)),
    )

    assert (
        security_monitoring_controller._save_current_security_baseline_result(app)
        is False
    )
    assert calls == [
        ("write", app),
        ("log", app, "kaputt"),
    ]


def test_load_security_baseline_result_returns_delegate_result(monkeypatch):
    app = object()
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_existing_security_baseline",
        lambda current_app: calls.append(current_app) or True,
    )

    assert security_monitoring_controller._load_security_baseline_result(app) is True
    assert calls == [app]


def test_load_security_baseline_result_returns_false_on_exception(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_load_existing_security_baseline",
        lambda _app: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert (
        security_monitoring_controller._load_security_baseline_result(object()) is False
    )


def test_integrity_watch_base_files_returns_fixed_watch_list():
    app = type(
        "DummyApp",
        (),
        {
            "vpn_config_path": "/tmp/vpn.json",
            "primary_vpn_config_path": "/tmp/primary.json",
            "link_config_path": "/tmp/link.json",
            "privacy_config_path": "/tmp/privacy.json",
            "hdd_config_path": "/tmp/hdd.json",
            "security_baseline_path": "/tmp/security.json",
            "clamav_findings_path": "/tmp/clamav.json",
        },
    )()

    assert security_monitoring_controller._integrity_watch_base_files(
        app,
        "/tmp/app.py",
    ) == [
        "/tmp/vpn.json",
        "/tmp/primary.json",
        "/tmp/link.json",
        "/tmp/privacy.json",
        "/tmp/hdd.json",
        "/tmp/security.json",
        "/tmp/clamav.json",
        "/tmp/app.py",
    ]


def test_integrity_watch_base_files_uses_current_baseline_path(monkeypatch):
    app = type(
        "DummyApp",
        (),
        {
            "vpn_config_path": "vpn",
            "primary_vpn_config_path": "primary",
            "link_config_path": "link",
            "privacy_config_path": "privacy",
            "hdd_config_path": "hdd",
            "clamav_findings_path": "clamav",
        },
    )()

    monkeypatch.setattr(
        security_monitoring_controller,
        "_security_baseline_path",
        lambda current_app: "/tmp/override.json" if current_app is app else "",
    )

    assert security_monitoring_controller._integrity_watch_base_files(app, "app.py")[
        5
    ] == ("/tmp/override.json")


def test_integrity_watch_wireguard_files_returns_only_real_files(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path, "isdir", lambda _p: True
    )
    monkeypatch.setattr(
        security_monitoring_controller.os,
        "listdir",
        lambda _p: ["wg0.conf", "notes.txt", "subdir"],
    )
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "isfile",
        lambda path: path.endswith("wg0.conf") or path.endswith("notes.txt"),
    )

    assert security_monitoring_controller._integrity_watch_wireguard_files(
        "/etc/wireguard"
    ) == [
        "/etc/wireguard/wg0.conf",
        "/etc/wireguard/notes.txt",
    ]


def test_integrity_watch_wireguard_files_returns_empty_on_error(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path, "isdir", lambda _p: True
    )
    monkeypatch.setattr(
        security_monitoring_controller.os,
        "listdir",
        lambda _p: (_ for _ in ()).throw(OSError("boom")),
    )

    assert (
        security_monitoring_controller._integrity_watch_wireguard_files(
            "/etc/wireguard"
        )
        == []
    )


def test_integrity_watch_app_file_path_points_to_netmon_app(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "dirname",
        lambda _path: "/repo/netmon/features",
    )

    assert security_monitoring_controller._integrity_watch_app_file_path() == (
        "/repo/netmon/app.py"
    )


def test_integrity_watch_app_file_path_returns_absolute_path(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "dirname",
        lambda _path: "netmon/features",
    )
    monkeypatch.setattr(
        security_monitoring_controller.os.path,
        "abspath",
        lambda path: f"/abs/{path}",
    )

    assert security_monitoring_controller._integrity_watch_app_file_path() == (
        "/abs/netmon/features/../app.py"
    )


def test_security_baseline_path_returns_current_path():
    app = type("DummyApp", (), {"security_baseline_path": "/tmp/security.json"})()

    assert (
        security_monitoring_controller._security_baseline_path(app)
        == "/tmp/security.json"
    )


def test_security_baseline_path_handles_missing_value():
    assert security_monitoring_controller._security_baseline_path(object()) == ""


def test_security_filter_mode_returns_current_mode():
    app = type("DummyApp", (), {"security_filter_mode": "external"})()

    assert security_monitoring_controller._security_filter_mode(app) == "external"


def test_security_filter_mode_handles_missing_or_empty_mode():
    empty_app = type("DummyApp", (), {"security_filter_mode": ""})()
    missing_app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_filter_mode(empty_app) == "all"
    assert security_monitoring_controller._security_filter_mode(missing_app) == "all"


def test_app_list_value_returns_detached_list_copy():
    app = type("DummyApp", (), {"security_events": [{"type": "UFW BLOCK"}]})()

    events = security_monitoring_controller._app_list_value(app, "security_events")
    events.append({"type": "Portscan-Verdacht"})

    assert app.security_events == [{"type": "UFW BLOCK"}]


def test_app_list_value_handles_missing_and_empty_values():
    app = type("DummyApp", (), {"security_visible_events": []})()

    assert security_monitoring_controller._app_list_value(app, "missing_events") == []
    assert (
        security_monitoring_controller._app_list_value(app, "security_visible_events")
        == []
    )


def test_app_dict_value_returns_detached_dict_copy():
    app = type("DummyApp", (), {"security_aggregated": {"ufw": 1}})()

    aggregated = security_monitoring_controller._app_dict_value(
        app, "security_aggregated"
    )
    aggregated["ufw"] = 2

    assert app.security_aggregated == {"ufw": 1}


def test_app_dict_value_handles_missing_and_empty_values():
    app = type("DummyApp", (), {"integrity_baseline": {}})()

    assert security_monitoring_controller._app_dict_value(app, "missing_dict") == {}
    assert (
        security_monitoring_controller._app_dict_value(app, "integrity_baseline") == {}
    )


def test_app_str_value_returns_stringified_value():
    app = type("DummyApp", (), {"security_log_level": 7})()

    assert (
        security_monitoring_controller._app_str_value(app, "security_log_level", "-")
        == "7"
    )


def test_app_str_value_handles_missing_and_empty_values():
    app = type("DummyApp", (), {"security_last_alarm": ""})()

    assert (
        security_monitoring_controller._app_str_value(app, "missing_alarm", "–") == "–"
    )
    assert (
        security_monitoring_controller._app_str_value(app, "security_last_alarm", "–")
        == "–"
    )


def test_app_widget_value_returns_existing_widget():
    widget = object()
    app = type("DummyApp", (), {"security_table": widget})()

    assert (
        security_monitoring_controller._app_widget_value(app, "security_table")
        is widget
    )


def test_app_widget_value_returns_none_when_missing():
    app = type("DummyApp", (), {})()

    assert (
        security_monitoring_controller._app_widget_value(app, "missing_widget") is None
    )


def test_security_table_returns_existing_table():
    table = object()
    app = type("DummyApp", (), {"security_table": table})()

    assert security_monitoring_controller._security_table(app) is table


def test_security_table_returns_none_when_missing():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._security_table(app) is None


def test_app_bool_value_returns_booleanized_value():
    app = type("DummyApp", (), {"security_monitoring": 1})()

    assert (
        security_monitoring_controller._app_bool_value(app, "security_monitoring")
        is True
    )


def test_app_bool_value_handles_missing_and_falsey_values():
    app = type("DummyApp", (), {"security_monitoring": 0})()

    assert security_monitoring_controller._app_bool_value(app, "missing_bool") is False
    assert (
        security_monitoring_controller._app_bool_value(app, "security_monitoring")
        is False
    )


def test_security_monitoring_active_returns_true_for_enabled_state():
    app = type("DummyApp", (), {"security_monitoring": 1})()

    assert security_monitoring_controller._security_monitoring_active(app) is True


def test_security_monitoring_active_returns_false_for_missing_or_disabled_state():
    disabled_app = type("DummyApp", (), {"security_monitoring": 0})()
    missing_app = type("DummyApp", (), {})()

    assert (
        security_monitoring_controller._security_monitoring_active(disabled_app)
        is False
    )
    assert (
        security_monitoring_controller._security_monitoring_active(missing_app) is False
    )


def test_security_filter_label_maps_known_and_unknown_modes():
    assert security_monitoring_controller._security_filter_label("all") == "Alle Events"
    assert (
        security_monitoring_controller._security_filter_label("portscan")
        == "Nur Portscan"
    )
    assert (
        security_monitoring_controller._security_filter_label("relevant")
        == "Nur Warnungen/Alarme"
    )
    assert (
        security_monitoring_controller._security_filter_label("external")
        == "Nur externe UFW-Blocks"
    )
    assert (
        security_monitoring_controller._security_filter_label("unknown") == "Unbekannt"
    )


def test_security_event_level_normalizes_missing_and_mixed_case_values():
    assert security_monitoring_controller._security_event_level({}) == ""
    assert (
        security_monitoring_controller._security_event_level({"level": "l3 alert"})
        == "L3 ALERT"
    )


def test_security_event_is_relevant_covers_level_and_portscan_paths():
    assert security_monitoring_controller._security_event_is_relevant(
        {"level": "L2 WARN"}
    )
    assert security_monitoring_controller._security_event_is_relevant(
        {"level": "l3 alert"}
    )
    assert security_monitoring_controller._security_event_is_relevant(
        {"level": "critical"}
    )
    assert security_monitoring_controller._security_event_is_relevant(
        {"type": "Portscan-Verdacht"}
    )
    assert (
        security_monitoring_controller._security_event_is_relevant(
            {"level": "info", "type": "UFW BLOCK"}
        )
        is False
    )


def test_security_summary_counts_clamps_negative_values():
    assert security_monitoring_controller._security_summary_counts(
        portscan_count=-2,
        block_count=-1,
        relevant_count=3,
    ) == {
        "portscan_count": 0,
        "block_count": 0,
        "relevant_count": 3,
    }


def test_security_summary_risk_label_covers_thresholds():
    assert (
        security_monitoring_controller._security_summary_risk_label(
            portscan_count=1,
            block_count=0,
            relevant_count=0,
        )
        == "Hoch"
    )
    assert (
        security_monitoring_controller._security_summary_risk_label(
            portscan_count=0,
            block_count=10,
            relevant_count=0,
        )
        == "Mittel"
    )
    assert (
        security_monitoring_controller._security_summary_risk_label(
            portscan_count=0,
            block_count=1,
            relevant_count=0,
        )
        == "Niedrig bis mittel"
    )
    assert (
        security_monitoring_controller._security_summary_risk_label(
            portscan_count=0,
            block_count=0,
            relevant_count=0,
        )
        == "Niedrig"
    )


def test_security_summary_immediate_actions_uses_safe_default_without_findings():
    assert security_monitoring_controller._security_summary_immediate_actions(
        portscan_count=0,
        block_count=0,
        relevant_count=0,
    ) == [
        "Keine akuten Security-Hinweise sichtbar; Baseline aktuell halten und Monitoring weiterlaufen lassen."
    ]


def test_security_selected_event_text_prefers_aggregate_and_visible_event():
    app = type("DummyApp", (), {})()
    app.security_visible_events = [{"raw": "ECHTES EVENT"}]

    assert (
        security_monitoring_controller._security_selected_event_text(
            app,
            "agg-0",
            {"kind": "aggregate", "raw": "Aggregierte interne Events: DNS = 2"},
        )
        == "Aggregierte interne Events: DNS = 2"
    )
    assert (
        security_monitoring_controller._security_selected_event_text(
            app,
            "sec-0",
            {"kind": "event", "index": 0},
        )
        == "ECHTES EVENT"
    )


def test_connected_device_detail_text_formats_baseline_label():
    text = security_monitoring_controller._connected_device_detail_text(
        {
            "name": "USB Keyboard",
            "path": "/dev/input/event0",
            "sys_name": "event0",
            "type": "input-event",
            "known_in_baseline": True,
            "vendor": "046d",
            "product": "c31c",
            "bustype": "0011",
            "phys": "usb-1",
            "uniq": "-",
        }
    )

    assert "=== Verbundenes Gerät ===" in text
    assert "USB Keyboard" in text
    assert "Vendor-ID: 046d" in text
    assert "Baseline: bekannt" in text


def test_connected_device_inventory_entry_lines_format_device_block():
    assert security_monitoring_controller._connected_device_inventory_entry_lines(
        2,
        {
            "name": "USB Mouse",
            "path": "/dev/input/mouse0",
            "sys_name": "mouse0",
            "type": "mouse",
            "known_in_baseline": False,
            "vendor": "1d57",
            "product": "ad02",
            "bustype": "0003",
            "phys": "usb-2",
            "uniq": "-",
        },
    ) == [
        "[2] USB Mouse",
        "Typ: mouse",
        "Pfad: /dev/input/mouse0",
        "Kennung: mouse0",
        "Vendor-ID: 1d57",
        "Product-ID: ad02",
        "Bus-Typ: 0003",
        "Phys: usb-2",
        "Unique-ID: -",
        "Baseline: neu/nicht in Baseline",
        "",
    ]


def test_connected_device_inventory_entry_lines_use_safe_defaults():
    assert security_monitoring_controller._connected_device_inventory_entry_lines(
        1, {}
    ) == [
        "[1] Unbekannt",
        "Typ: unknown",
        "Pfad: -",
        "Kennung: -",
        "Vendor-ID: -",
        "Product-ID: -",
        "Bus-Typ: -",
        "Phys: -",
        "Unique-ID: -",
        "Baseline: neu/nicht in Baseline",
        "",
    ]


def test_connected_device_inventory_header_lines_format_counts():
    assert security_monitoring_controller._connected_device_inventory_header_lines(
        [{"name": "USB Keyboard"}, {"name": "USB Mouse"}],
        {"/dev/input/event0": "input-event"},
    ) == [
        "=== Aktuell verbundene Geräte ===",
        "",
        "Anzahl erkannter Geräte: 2",
        "Device-Baseline Einträge: 1",
        "",
    ]


def test_connected_device_inventory_header_lines_use_safe_defaults():
    assert security_monitoring_controller._connected_device_inventory_header_lines(
        None, None
    ) == [
        "=== Aktuell verbundene Geräte ===",
        "",
        "Anzahl erkannter Geräte: 0",
        "Device-Baseline Einträge: 0",
        "",
    ]


def test_connected_device_inventory_empty_message_returns_expected_text():
    assert (
        security_monitoring_controller._connected_device_inventory_empty_message()
        == "Keine verbundenen Geräte erkannt."
    )


def test_connected_device_inventory_body_lines_format_multiple_entries():
    assert security_monitoring_controller._connected_device_inventory_body_lines(
        [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
                "vendor": "046d",
                "product": "c31c",
                "bustype": "0011",
                "phys": "usb-1",
                "uniq": "-",
            },
            {
                "name": "USB Mouse",
                "path": "/dev/input/mouse0",
                "sys_name": "mouse0",
                "type": "mouse",
                "known_in_baseline": False,
                "vendor": "1d57",
                "product": "ad02",
                "bustype": "0003",
                "phys": "usb-2",
                "uniq": "-",
            },
        ]
    ) == [
        "[1] USB Keyboard",
        "Typ: input-event",
        "Pfad: /dev/input/event0",
        "Kennung: event0",
        "Vendor-ID: 046d",
        "Product-ID: c31c",
        "Bus-Typ: 0011",
        "Phys: usb-1",
        "Unique-ID: -",
        "Baseline: bekannt",
        "",
        "[2] USB Mouse",
        "Typ: mouse",
        "Pfad: /dev/input/mouse0",
        "Kennung: mouse0",
        "Vendor-ID: 1d57",
        "Product-ID: ad02",
        "Bus-Typ: 0003",
        "Phys: usb-2",
        "Unique-ID: -",
        "Baseline: neu/nicht in Baseline",
        "",
    ]


def test_connected_device_inventory_body_lines_return_empty_for_missing_inventory():
    assert (
        security_monitoring_controller._connected_device_inventory_body_lines(None)
        == []
    )


def test_connected_device_inventory_lines_include_empty_message_for_empty_inventory():
    assert security_monitoring_controller._connected_device_inventory_lines(
        [],
        {},
    ) == [
        "=== Aktuell verbundene Geräte ===",
        "",
        "Anzahl erkannter Geräte: 0",
        "Device-Baseline Einträge: 0",
        "",
        "Keine verbundenen Geräte erkannt.",
    ]


def test_connected_device_inventory_lines_include_body_for_devices():
    assert security_monitoring_controller._connected_device_inventory_lines(
        [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
                "vendor": "046d",
                "product": "c31c",
                "bustype": "0011",
                "phys": "usb-1",
                "uniq": "-",
            }
        ],
        {"/dev/input/event0": "input-event"},
    ) == [
        "=== Aktuell verbundene Geräte ===",
        "",
        "Anzahl erkannter Geräte: 1",
        "Device-Baseline Einträge: 1",
        "",
        "[1] USB Keyboard",
        "Typ: input-event",
        "Pfad: /dev/input/event0",
        "Kennung: event0",
        "Vendor-ID: 046d",
        "Product-ID: c31c",
        "Bus-Typ: 0011",
        "Phys: usb-1",
        "Unique-ID: -",
        "Baseline: bekannt",
        "",
    ]


def test_connected_device_inventory_text_adds_trailing_newline():
    assert (
        security_monitoring_controller._connected_device_inventory_text(
            ["Header", "", "Body"]
        )
        == "Header\n\nBody\n"
    )


def test_connected_device_inventory_text_trims_trailing_blank_lines():
    assert (
        security_monitoring_controller._connected_device_inventory_text(
            ["Header", "Body", "", ""]
        )
        == "Header\nBody\n"
    )


def test_connected_device_inventory_context_returns_inventory_and_baseline(
    monkeypatch,
):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [{"name": "USB Keyboard"}],
    )

    class DummyApp:
        device_baseline = {"/dev/input/event0": "input-event"}

    assert security_monitoring_controller._connected_device_inventory_context(
        DummyApp()
    ) == ([{"name": "USB Keyboard"}], {"/dev/input/event0": "input-event"})


def test_connected_device_inventory_context_uses_safe_default_baseline(
    monkeypatch,
):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [],
    )

    class DummyApp:
        pass

    assert security_monitoring_controller._connected_device_inventory_context(
        DummyApp()
    ) == ([], {})


def test_connected_device_table_tag_colors_uses_theme_values():
    app = type(
        "DummyApp",
        (),
        {"_app_theme": {"success": "#00aa00", "warning": "#cc8800"}},
    )()

    assert security_monitoring_controller._connected_device_table_tag_colors(app) == (
        "#00aa00",
        "#cc8800",
    )


def test_connected_device_table_tag_colors_uses_safe_defaults():
    app = object()

    assert security_monitoring_controller._connected_device_table_tag_colors(app) == (
        "#1a7f37",
        "#9a6700",
    )


def test_connected_device_table_tag_configs_builds_known_and_new_specs():
    assert security_monitoring_controller._connected_device_table_tag_configs(
        "#00aa00", "#cc8800"
    ) == (
        ("device_known", {"foreground": "#00aa00"}),
        ("device_new", {"foreground": "#cc8800"}),
    )


def test_connected_device_table_tag_configs_preserves_empty_colors():
    assert security_monitoring_controller._connected_device_table_tag_configs(
        "", ""
    ) == (
        ("device_known", {"foreground": ""}),
        ("device_new", {"foreground": ""}),
    )


def test_connected_device_table_tag_config_builds_foreground_mapping():
    assert security_monitoring_controller._connected_device_table_tag_config(
        "device_known", "#00aa00"
    ) == ("device_known", {"foreground": "#00aa00"})


def test_connected_device_table_tag_config_preserves_empty_color():
    assert security_monitoring_controller._connected_device_table_tag_config(
        "device_new", ""
    ) == ("device_new", {"foreground": ""})


def test_clear_connected_device_table_deletes_all_children():
    class DummyTable:
        def __init__(self):
            self.deleted = []

        def get_children(self):
            return ("dev-0", "dev-1")

        def delete(self, item):
            self.deleted.append(item)

    table = DummyTable()
    security_monitoring_controller._clear_connected_device_table(table)

    assert table.deleted == ["dev-0", "dev-1"]


def test_connected_device_table_children_returns_list_copy():
    class DummyTable:
        @staticmethod
        def get_children():
            return ("dev-0", "dev-1")

    children = security_monitoring_controller._connected_device_table_children(
        DummyTable()
    )

    assert children == ["dev-0", "dev-1"]
    assert isinstance(children, list)


def test_connected_device_table_children_handles_no_children():
    class DummyTable:
        @staticmethod
        def get_children():
            return ()

    assert (
        security_monitoring_controller._connected_device_table_children(DummyTable())
        == []
    )


def test_clear_connected_device_table_skips_when_no_children():
    class DummyTable:
        def __init__(self):
            self.deleted = []

        def get_children(self):
            return ()

        def delete(self, item):
            self.deleted.append(item)

    table = DummyTable()
    security_monitoring_controller._clear_connected_device_table(table)

    assert table.deleted == []


def test_insert_connected_device_row_inserts_expected_values_and_tags():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, iid=None, values=(), tags=()):
            self.calls.append(
                {
                    "parent": parent,
                    "where": where,
                    "iid": iid,
                    "values": values,
                    "tags": tags,
                }
            )

    table = DummyTable()
    security_monitoring_controller._insert_connected_device_row(
        table,
        2,
        {
            "name": "USB Mouse",
            "path": "/dev/input/mouse0",
            "sys_name": "mouse0",
            "type": "mouse",
            "known_in_baseline": False,
            "vendor": "1d57",
            "product": "ad02",
            "bustype": "0003",
            "phys": "usb-2",
            "uniq": "-",
        },
    )

    assert table.calls == [
        {
            "parent": "",
            "where": "end",
            "iid": "dev-2",
            "values": (
                "USB Mouse",
                "mouse",
                "1d57",
                "ad02",
                "neu",
                "/dev/input/mouse0",
            ),
            "tags": ("device_new",),
        }
    ]


def test_insert_connected_device_row_uses_known_tag_for_baseline_device():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, iid=None, values=(), tags=()):
            self.calls.append((iid, values, tags))

    table = DummyTable()
    security_monitoring_controller._insert_connected_device_row(
        table,
        0,
        {
            "name": "USB Keyboard",
            "path": "/dev/input/event0",
            "sys_name": "event0",
            "type": "input-event",
            "known_in_baseline": True,
        },
    )

    assert table.calls == [
        (
            "dev-0",
            ("USB Keyboard", "input-event", "-", "-", "bekannt", "/dev/input/event0"),
            ("device_known",),
        )
    ]


def test_connected_device_row_id_formats_index_as_expected():
    assert security_monitoring_controller._connected_device_row_id(0) == "dev-0"
    assert security_monitoring_controller._connected_device_row_id(7) == "dev-7"


def test_connected_device_row_id_preserves_negative_indices():
    assert security_monitoring_controller._connected_device_row_id(-1) == "dev--1"


def test_connected_device_row_insert_kwargs_builds_insert_payload():
    device = {
        "name": "USB Mouse",
        "path": "/dev/input/mouse0",
        "sys_name": "mouse0",
        "type": "mouse",
        "known_in_baseline": False,
    }

    assert security_monitoring_controller._connected_device_row_insert_kwargs(
        2, device
    ) == {
        "iid": "dev-2",
        "values": ("USB Mouse", "mouse", "-", "-", "neu", "/dev/input/mouse0"),
        "tags": ("device_new",),
    }


def test_connected_device_row_insert_kwargs_uses_known_device_tag():
    device = {
        "name": "USB Keyboard",
        "path": "/dev/input/event0",
        "sys_name": "event0",
        "type": "input-event",
        "known_in_baseline": True,
    }

    assert security_monitoring_controller._connected_device_row_insert_kwargs(
        0, device
    ) == {
        "iid": "dev-0",
        "values": (
            "USB Keyboard",
            "input-event",
            "-",
            "-",
            "bekannt",
            "/dev/input/event0",
        ),
        "tags": ("device_known",),
    }


def test_append_connected_device_row_inserts_expected_row():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, iid=None, values=(), tags=()):
            self.calls.append((parent, where, iid, values, tags))

    table = DummyTable()
    security_monitoring_controller._append_connected_device_row(
        table,
        2,
        {
            "name": "USB Mouse",
            "path": "/dev/input/mouse0",
            "sys_name": "mouse0",
            "type": "mouse",
            "known_in_baseline": False,
        },
    )

    assert table.calls == [
        (
            "",
            "end",
            "dev-2",
            ("USB Mouse", "mouse", "-", "-", "neu", "/dev/input/mouse0"),
            ("device_new",),
        )
    ]


def test_append_connected_device_row_uses_known_tag_for_baseline_device():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, iid=None, values=(), tags=()):
            self.calls.append((iid, values, tags))

    table = DummyTable()
    security_monitoring_controller._append_connected_device_row(
        table,
        0,
        {
            "name": "USB Keyboard",
            "path": "/dev/input/event0",
            "sys_name": "event0",
            "type": "input-event",
            "known_in_baseline": True,
        },
    )

    assert table.calls == [
        (
            "dev-0",
            ("USB Keyboard", "input-event", "-", "-", "bekannt", "/dev/input/event0"),
            ("device_known",),
        )
    ]


def test_connected_device_inventory_items_enumerates_inventory():
    inventory = [{"name": "USB Keyboard"}, {"name": "USB Mouse"}]

    assert security_monitoring_controller._connected_device_inventory_items(
        inventory
    ) == [(0, {"name": "USB Keyboard"}), (1, {"name": "USB Mouse"})]


def test_connected_device_inventory_items_handles_empty_inventory():
    assert security_monitoring_controller._connected_device_inventory_items([]) == []
    assert security_monitoring_controller._connected_device_inventory_items(None) == []


def test_populate_connected_device_table_inserts_all_inventory_rows():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, iid=None, values=(), tags=()):
            self.calls.append((iid, values, tags))

    table = DummyTable()
    security_monitoring_controller._populate_connected_device_table(
        table,
        [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
            },
            {
                "name": "USB Mouse",
                "path": "/dev/input/mouse0",
                "sys_name": "mouse0",
                "type": "mouse",
                "known_in_baseline": False,
                "vendor": "1d57",
                "product": "ad02",
            },
        ],
    )

    assert table.calls == [
        (
            "dev-0",
            ("USB Keyboard", "input-event", "-", "-", "bekannt", "/dev/input/event0"),
            ("device_known",),
        ),
        (
            "dev-1",
            ("USB Mouse", "mouse", "1d57", "ad02", "neu", "/dev/input/mouse0"),
            ("device_new",),
        ),
    ]


def test_populate_connected_device_table_skips_empty_inventory():
    class DummyTable:
        def __init__(self):
            self.calls = []

        def insert(self, parent, where, iid=None, values=(), tags=()):
            self.calls.append((iid, values, tags))

    table = DummyTable()
    security_monitoring_controller._populate_connected_device_table(table, [])

    assert table.calls == []


def test_connected_device_table_inventory_returns_and_stores_inventory(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [{"name": "USB Keyboard"}],
    )

    app = type("DummyApp", (), {})()

    inventory = security_monitoring_controller._connected_device_table_inventory(app)

    assert inventory == [{"name": "USB Keyboard"}]
    assert app.connected_devices_inventory == [{"name": "USB Keyboard"}]


def test_connected_device_table_inventory_stores_empty_inventory(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [],
    )

    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._connected_device_table_inventory(app) == []
    assert app.connected_devices_inventory == []


def test_current_connected_device_inventory_returns_inventory(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [{"name": "USB Keyboard"}],
    )

    assert security_monitoring_controller._current_connected_device_inventory(
        object()
    ) == [{"name": "USB Keyboard"}]


def test_current_connected_device_inventory_preserves_empty_inventory(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [],
    )

    assert (
        security_monitoring_controller._current_connected_device_inventory(object())
        == []
    )


def test_store_connected_device_inventory_returns_and_stores_inventory():
    app = type("DummyApp", (), {"connected_devices_inventory": []})()
    inventory = [{"name": "USB Keyboard"}]

    assert (
        security_monitoring_controller._store_connected_device_inventory(app, inventory)
        == inventory
    )
    assert app.connected_devices_inventory == inventory


def test_store_connected_device_inventory_preserves_same_object():
    inventory = [{"name": "USB Mouse"}]
    app = type("DummyApp", (), {"connected_devices_inventory": None})()

    stored = security_monitoring_controller._store_connected_device_inventory(
        app, inventory
    )

    assert stored is inventory
    assert app.connected_devices_inventory is inventory


def test_connected_device_table_returns_existing_table():
    table = object()
    app = type("DummyApp", (), {"security_devices_table": table})()

    assert security_monitoring_controller._connected_device_table(app) is table


def test_connected_device_table_returns_none_when_missing():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._connected_device_table(app) is None


def test_refresh_connected_device_table_view_calls_helpers_in_order(monkeypatch):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_configure_connected_device_table_tags",
        lambda app, table: calls.append(("configure", app, table)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_clear_connected_device_table",
        lambda table: calls.append(("clear", table)),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_populate_connected_device_table",
        lambda table, inventory: calls.append(("populate", table, inventory)),
    )

    app = object()
    table = object()
    inventory = [{"name": "USB Keyboard"}]

    security_monitoring_controller._refresh_connected_device_table_view(
        app, table, inventory
    )

    assert calls == [
        ("configure", app, table),
        ("clear", table),
        ("populate", table, inventory),
    ]


def test_refresh_connected_device_table_view_passes_empty_inventory_to_populate(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        security_monitoring_controller,
        "_configure_connected_device_table_tags",
        lambda app, table: calls.append("configure"),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_clear_connected_device_table",
        lambda table: calls.append("clear"),
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "_populate_connected_device_table",
        lambda table, inventory: calls.append(("populate", inventory)),
    )

    security_monitoring_controller._refresh_connected_device_table_view(
        object(), object(), []
    )

    assert calls == ["configure", "clear", ("populate", [])]


def test_refresh_connected_device_table_if_present_skips_missing_table(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_connected_device_table",
        lambda _app: None,
    )

    called = []
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_connected_device_table_view",
        lambda *_args: called.append("view"),
    )

    security_monitoring_controller._refresh_connected_device_table_if_present(
        object(), [{"name": "USB Keyboard"}]
    )

    assert called == []


def test_refresh_connected_device_table_if_present_refreshes_existing_table(
    monkeypatch,
):
    table = object()
    monkeypatch.setattr(
        security_monitoring_controller,
        "_connected_device_table",
        lambda _app: table,
    )

    calls = []
    monkeypatch.setattr(
        security_monitoring_controller,
        "_refresh_connected_device_table_view",
        lambda app, current_table, inventory: calls.append(
            (app, current_table, inventory)
        ),
    )

    app = object()
    inventory = [{"name": "USB Mouse"}]

    security_monitoring_controller._refresh_connected_device_table_if_present(
        app, inventory
    )

    assert calls == [(app, table, inventory)]


def test_connected_device_inventory_text_for_formats_empty_inventory():
    assert (
        security_monitoring_controller._connected_device_inventory_text_for([], {})
        == "=== Aktuell verbundene Geräte ===\n\nAnzahl erkannter Geräte: 0\n"
        "Device-Baseline Einträge: 0\n\nKeine verbundenen Geräte erkannt.\n"
    )


def test_connected_device_inventory_text_for_formats_device_inventory():
    assert (
        security_monitoring_controller._connected_device_inventory_text_for(
            [
                {
                    "name": "USB Keyboard",
                    "path": "/dev/input/event0",
                    "sys_name": "event0",
                    "type": "input-event",
                    "known_in_baseline": True,
                    "vendor": "046d",
                    "product": "c31c",
                    "bustype": "0011",
                    "phys": "usb-1",
                    "uniq": "-",
                }
            ],
            {"/dev/input/event0": "input-event"},
        )
        == "=== Aktuell verbundene Geräte ===\n\nAnzahl erkannter Geräte: 1\n"
        "Device-Baseline Einträge: 1\n\n[1] USB Keyboard\nTyp: input-event\n"
        "Pfad: /dev/input/event0\nKennung: event0\nVendor-ID: 046d\n"
        "Product-ID: c31c\nBus-Typ: 0011\nPhys: usb-1\nUnique-ID: -\n"
        "Baseline: bekannt\n"
    )


def test_format_connected_device_inventory_uses_empty_message(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [],
    )

    class DummyApp:
        device_baseline = {}

    text = security_monitoring_controller.format_connected_device_inventory(DummyApp())

    assert "=== Aktuell verbundene Geräte ===" in text
    assert "Keine verbundenen Geräte erkannt." in text


def test_connected_device_baseline_text_returns_known_label():
    assert (
        security_monitoring_controller._connected_device_baseline_text(
            {"known_in_baseline": True}
        )
        == "Baseline: bekannt"
    )


def test_connected_device_baseline_text_returns_new_label_by_default():
    assert (
        security_monitoring_controller._connected_device_baseline_text({})
        == "Baseline: neu/nicht in Baseline"
    )


def test_set_security_detail_text_writes_text_when_widget_exists():
    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    app = type("DummyApp", (), {})()
    app.security_detail = DummyDetail()

    security_monitoring_controller._set_security_detail_text(app, "demo text")

    assert app.security_detail.text == "demo text"


def test_set_security_detail_text_returns_safely_without_widget():
    app = type("DummyApp", (), {})()

    assert security_monitoring_controller._set_security_detail_text(app, "demo") is None


def test_set_security_detail_text_safe_writes_text_when_possible():
    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    app = type("DummyApp", (), {})()
    app.security_detail = DummyDetail()

    assert (
        security_monitoring_controller._set_security_detail_text_safe(app, "demo")
        is True
    )
    assert app.security_detail.text == "demo"


def test_set_security_detail_text_safe_returns_false_on_widget_error():
    class BrokenDetail:
        def delete(self, *_args):
            raise RuntimeError("broken")

    app = type("DummyApp", (), {})()
    app.security_detail = BrokenDetail()

    assert (
        security_monitoring_controller._set_security_detail_text_safe(app, "demo")
        is False
    )


def test_selected_connected_device_returns_selected_inventory_item():
    class DummyTable:
        def selection(self):
            return ("dev-0",)

    app = type("DummyApp", (), {})()
    app.connected_devices_inventory = [{"name": "USB Keyboard"}]

    assert security_monitoring_controller._selected_connected_device(
        app, DummyTable()
    ) == {"name": "USB Keyboard"}


def test_selected_connected_device_returns_none_for_invalid_index():
    class DummyTable:
        def selection(self):
            return ("dev-1",)

    app = type("DummyApp", (), {})()
    app.connected_devices_inventory = [{"name": "USB Keyboard"}]

    assert (
        security_monitoring_controller._selected_connected_device(app, DummyTable())
        is None
    )


def test_prepare_security_chad_curated_analysis_uses_short_title(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        security_monitoring_controller,
        "build_security_chad_curated_summary",
        lambda _app: "short summary",
    )

    class DummyApp:
        def prepare_chad_analysis(self, title, raw_text):
            captured["title"] = title
            captured["raw_text"] = raw_text

    security_monitoring_controller.prepare_security_chad_curated_analysis(DummyApp())

    assert captured["title"] == "Security Kurzcheck"
    assert captured["raw_text"] == "short summary"


def test_prepare_security_chad_analysis_uses_default_title(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        security_monitoring_controller,
        "build_security_chad_summary",
        lambda _app: "full summary",
    )

    class DummyApp:
        def prepare_chad_analysis(self, title, raw_text):
            captured["title"] = title
            captured["raw_text"] = raw_text

    security_monitoring_controller.prepare_security_chad_analysis(DummyApp())

    assert captured["title"] == "Security Analyse"
    assert captured["raw_text"] == "full summary"


def test_prepare_security_chad_technical_analysis_uses_deep_title(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        security_monitoring_controller,
        "build_security_chad_summary",
        lambda _app: "deep summary",
    )

    class DummyApp:
        def prepare_chad_analysis(self, title, raw_text):
            captured["title"] = title
            captured["raw_text"] = raw_text

    security_monitoring_controller.prepare_security_chad_technical_analysis(DummyApp())

    assert captured["title"] == "Security Tiefenanalyse"
    assert captured["raw_text"] == "deep summary"


def test_prepare_security_chad_analysis_helper_uses_builder_result():
    captured = {}

    class DummyApp:
        def prepare_chad_analysis(self, title, raw_text):
            captured["title"] = title
            captured["raw_text"] = raw_text

    security_monitoring_controller._prepare_security_chad_analysis(
        DummyApp(),
        "Security Titel",
        lambda _app: "builder summary",
    )

    assert captured == {
        "title": "Security Titel",
        "raw_text": "builder summary",
    }


def test_connected_device_inventory_prefers_dev_input_paths(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "_device_display_name",
        lambda path: f"name:{path.rsplit('/', 1)[-1]}",
    )

    class DummyApp:
        device_baseline = {"/dev/input/event0": "input-event"}

        def _device_watch_paths(self):
            return [
                "/sys/class/input/event0",
                "/dev/input/event0",
                "/sys/class/input/mouse0",
            ]

        def _device_type_from_path(self, path):
            return "mouse" if path.endswith("mouse0") else "input-event"

    inventory = security_monitoring_controller.connected_device_inventory(DummyApp())

    assert inventory[0]["path"] == "/dev/input/event0"
    assert inventory[0]["known_in_baseline"] is True
    assert any(item["sys_name"] == "mouse0" for item in inventory)


def test_security_show_connected_devices_renders_full_inventory(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
            },
            {
                "name": "USB Mouse",
                "path": "/dev/input/mouse0",
                "sys_name": "mouse0",
                "type": "mouse",
                "known_in_baseline": False,
            },
        ],
    )

    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    logs = []

    class DummyApp:
        device_baseline = {"/dev/input/event0": "input-event"}
        security_detail = DummyDetail()
        log = logs.append

        def tr(self, _key, default):
            return default

    app = DummyApp()
    security_monitoring_controller.security_show_connected_devices(app)

    assert "=== Aktuell verbundene Geräte ===" in app.security_detail.text
    assert "USB Keyboard" in app.security_detail.text
    assert "USB Mouse" in app.security_detail.text
    assert "Baseline: bekannt" in app.security_detail.text
    assert "Baseline: neu/nicht in Baseline" in app.security_detail.text
    assert logs == ["Security: 2 verbundene Geräte angezeigt."]


def test_finish_security_show_connected_devices_updates_detail_and_logs():
    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    logs = []

    class DummyApp:
        security_detail = DummyDetail()
        log = logs.append

        def tr(self, _key, default):
            return default

    app = DummyApp()
    security_monitoring_controller._finish_security_show_connected_devices(
        app,
        "Inventartext\n",
        [{"name": "USB Keyboard"}, {"name": "USB Mouse"}],
    )

    assert app.security_detail.text == "Inventartext\n"
    assert logs == ["Security: 2 verbundene Geräte angezeigt."]


def test_finish_security_show_connected_devices_logs_zero_for_empty_inventory():
    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    logs = []

    class DummyApp:
        security_detail = DummyDetail()
        log = logs.append

        def tr(self, _key, default):
            return default

    app = DummyApp()
    security_monitoring_controller._finish_security_show_connected_devices(
        app,
        "Keine Geräte\n",
        [],
    )

    assert app.security_detail.text == "Keine Geräte\n"
    assert logs == ["Security: 0 verbundene Geräte angezeigt."]


def test_connected_device_display_payload_returns_inventory_and_text(monkeypatch):
    inventory = [{"name": "USB Keyboard"}]

    monkeypatch.setattr(
        security_monitoring_controller,
        "refresh_connected_device_table",
        lambda _app: inventory,
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "format_connected_device_inventory",
        lambda _app: "Inventartext\n",
    )

    assert security_monitoring_controller._connected_device_display_payload(
        object()
    ) == (
        inventory,
        "Inventartext\n",
    )


def test_connected_device_display_payload_keeps_empty_inventory_text(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "refresh_connected_device_table",
        lambda _app: [],
    )
    monkeypatch.setattr(
        security_monitoring_controller,
        "format_connected_device_inventory",
        lambda _app: "Keine Geräte\n",
    )

    assert security_monitoring_controller._connected_device_display_payload(
        object()
    ) == ([], "Keine Geräte\n")


def test_refresh_connected_device_table_populates_rows(monkeypatch):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
                "vendor": "046d",
                "product": "c31c",
                "bustype": "0011",
                "phys": "usb-1",
                "uniq": "-",
            }
        ],
    )

    class DummyTable:
        def __init__(self):
            self.rows = {}
            self.tags = {}

        def get_children(self):
            return tuple(self.rows)

        def delete(self, item):
            self.rows.pop(item, None)

        def tag_configure(self, tag_name, **kwargs):
            self.tags[tag_name] = kwargs

        def insert(self, _parent, _where, iid=None, values=(), tags=()):
            self.rows[iid] = values
            self.tags[f"{iid}:row"] = tags

    class DummyApp:
        security_devices_table = DummyTable()
        _app_theme = {"success": "#00aa00", "warning": "#cc8800"}

    app = DummyApp()
    inventory = security_monitoring_controller.refresh_connected_device_table(app)

    assert len(inventory) == 1
    assert app.connected_devices_inventory[0]["name"] == "USB Keyboard"
    assert app.security_devices_table.rows["dev-0"][0] == "USB Keyboard"
    assert app.security_devices_table.rows["dev-0"][4] == "bekannt"
    assert app.security_devices_table.tags["device_known"]["foreground"] == "#00aa00"
    assert app.security_devices_table.tags["dev-0:row"] == ("device_known",)


def test_refresh_connected_device_table_marks_new_devices_with_warning_tag(
    monkeypatch,
):
    monkeypatch.setattr(
        security_monitoring_controller,
        "connected_device_inventory",
        lambda _app: [
            {
                "name": "USB Mouse",
                "path": "/dev/input/mouse0",
                "sys_name": "mouse0",
                "type": "mouse",
                "known_in_baseline": False,
                "vendor": "1d57",
                "product": "ad02",
                "bustype": "0003",
                "phys": "usb-2",
                "uniq": "-",
            }
        ],
    )

    class DummyTable:
        def __init__(self):
            self.rows = {}
            self.tags = {}

        def get_children(self):
            return tuple(self.rows)

        def delete(self, item):
            self.rows.pop(item, None)

        def tag_configure(self, tag_name, **kwargs):
            self.tags[tag_name] = kwargs

        def insert(self, _parent, _where, iid=None, values=(), tags=()):
            self.rows[iid] = values
            self.tags[f"{iid}:row"] = tags

    class DummyApp:
        security_devices_table = DummyTable()
        _app_theme = {"success": "#00aa00", "warning": "#cc8800"}

    app = DummyApp()
    security_monitoring_controller.refresh_connected_device_table(app)

    assert app.security_devices_table.rows["dev-0"][4] == "neu"
    assert app.security_devices_table.tags["device_new"]["foreground"] == "#cc8800"
    assert app.security_devices_table.tags["dev-0:row"] == ("device_new",)


def test_finish_connected_device_select_writes_detail_text():
    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    app = type("DummyApp", (), {"security_detail": DummyDetail()})()
    security_monitoring_controller._finish_connected_device_select(
        app, "Gerätedetails\n"
    )

    assert app.security_detail.text == "Gerätedetails\n"


def test_finish_connected_device_select_is_safe_without_detail_widget():
    app = type("DummyApp", (), {})()

    assert (
        security_monitoring_controller._finish_connected_device_select(
            app, "Gerätedetails\n"
        )
        is None
    )


def test_connected_device_display_log_text_formats_positive_count():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._connected_device_display_log_text(
            DummyApp(), [{"name": "USB Keyboard"}, {"name": "USB Mouse"}]
        )
        == "Security: 2 verbundene Geräte angezeigt."
    )


def test_connected_device_display_log_text_formats_zero_count():
    class DummyApp:
        def tr(self, _key, default):
            return default

    assert (
        security_monitoring_controller._connected_device_display_log_text(
            DummyApp(), []
        )
        == "Security: 0 verbundene Geräte angezeigt."
    )


def test_on_connected_device_select_shows_device_details():
    class DummyTable:
        def selection(self):
            return ("dev-0",)

    class DummyDetail:
        def __init__(self):
            self.text = ""

        def delete(self, *_args):
            self.text = ""

        def insert(self, _index, value):
            self.text += value

        def see(self, _index):
            pass

    class DummyApp:
        security_devices_table = DummyTable()
        security_detail = DummyDetail()
        connected_devices_inventory = [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
                "vendor": "046d",
                "product": "c31c",
                "bustype": "0011",
                "phys": "usb-1",
                "uniq": "-",
            }
        ]

    app = DummyApp()
    security_monitoring_controller.on_connected_device_select(app)

    assert "=== Verbundenes Gerät ===" in app.security_detail.text
    assert "USB Keyboard" in app.security_detail.text
    assert "Vendor-ID: 046d" in app.security_detail.text
    assert "Baseline: bekannt" in app.security_detail.text


def test_selected_connected_device_text_returns_detail_text_for_selection():
    class DummyTable:
        def selection(self):
            return ("dev-0",)

    class DummyApp:
        connected_devices_inventory = [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
                "vendor": "046d",
                "product": "c31c",
                "bustype": "0011",
                "phys": "usb-1",
                "uniq": "-",
            }
        ]

    text = security_monitoring_controller._selected_connected_device_text(
        DummyApp(), DummyTable()
    )

    assert "=== Verbundenes Gerät ===" in text
    assert "USB Keyboard" in text


def test_selected_connected_device_selection_text_uses_app_table():
    class DummyTable:
        def selection(self):
            return ("dev-0",)

    class DummyApp:
        security_devices_table = DummyTable()
        connected_devices_inventory = [
            {
                "name": "USB Keyboard",
                "path": "/dev/input/event0",
                "sys_name": "event0",
                "type": "input-event",
                "known_in_baseline": True,
                "vendor": "046d",
                "product": "c31c",
                "bustype": "0011",
                "phys": "usb-1",
                "uniq": "-",
            }
        ]

    text = security_monitoring_controller._selected_connected_device_selection_text(
        DummyApp()
    )

    assert "=== Verbundenes Gerät ===" in text
    assert "USB Keyboard" in text


def test_selected_connected_device_selection_text_returns_empty_without_table():
    class DummyApp:
        connected_devices_inventory = []

    assert (
        security_monitoring_controller._selected_connected_device_selection_text(
            DummyApp()
        )
        == ""
    )


def test_selected_connected_device_text_returns_empty_without_selection():
    class DummyTable:
        def selection(self):
            return ()

    class DummyApp:
        connected_devices_inventory = []

    assert (
        security_monitoring_controller._selected_connected_device_text(
            DummyApp(), DummyTable()
        )
        == ""
    )
