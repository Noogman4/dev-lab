import types

from netmon.features import hdd_controller
from netmon.services import hdd_mount_service
from tools import netmon


def test_selected_hdd_slot_helpers_validate_slot_choice():
    app = netmon.App.__new__(netmon.App)
    app.hdd_slots = [
        {"slot": 1, "device": "/dev/sda"},
        {"slot": 2, "device": "/dev/sdb"},
    ]
    app.hdd_slot_choice = types.SimpleNamespace(get=lambda: "2")

    slot_no, slot = hdd_controller._selected_hdd_slot(app)

    assert slot_no == 2
    assert slot is app.hdd_slots[1]

    app.hdd_slot_choice = types.SimpleNamespace(get=lambda: "99")

    slot_no, slot = hdd_controller._selected_hdd_slot(app)

    assert slot_no == 0
    assert slot is None


def test_clear_hdd_slot_fields_resets_assignment_values():
    slot = {
        "slot": 1,
        "device": "/dev/sdb",
        "device_uuid": "uuid-1",
        "mountpoint": "/mnt/media",
        "custom_name": "Media",
    }

    hdd_controller._clear_hdd_slot_fields(slot)

    assert slot == {
        "slot": 1,
        "device": "",
        "device_uuid": "",
        "mountpoint": "",
        "custom_name": "",
        "auto_mount": False,
    }


def test_hdd_slot_has_assignment_checks_relevant_fields():
    assert hdd_controller._hdd_slot_has_assignment({}) is False
    assert (
        hdd_controller._hdd_slot_has_assignment(
            {
                "device": "",
                "device_uuid": "",
                "mountpoint": "/mnt/media",
                "custom_name": "",
            }
        )
        is True
    )


def test_clear_device_slot_assignments_only_clears_matching_device():
    app = netmon.App.__new__(netmon.App)
    app.hdd_slots = [
        {
            "slot": 1,
            "device": "/dev/sdb",
            "device_uuid": "uuid-1",
            "mountpoint": "/mnt/media",
            "custom_name": "Media",
        },
        {
            "slot": 2,
            "device": "/dev/sdc",
            "device_uuid": "uuid-2",
            "mountpoint": "/mnt/backup",
            "custom_name": "Backup",
        },
    ]

    hdd_controller._clear_device_slot_assignments(app, "/dev/sdb")

    assert app.hdd_slots[0] == {
        "slot": 1,
        "device": "",
        "device_uuid": "",
        "mountpoint": "",
        "custom_name": "",
        "auto_mount": False,
    }
    assert app.hdd_slots[1]["device"] == "/dev/sdc"


def test_load_hdd_slots_config_reads_auto_mount_flag(tmp_path):
    app = netmon.App.__new__(netmon.App)
    app.hdd_config_path = str(tmp_path / "hdd_slots.json")
    app.log = lambda _message: None
    app.hdd_slots = []
    app.hdd_info_auto_mount_var = None

    app.hdd_config_path = str(tmp_path / "hdd_slots.json")
    app.hdd_config_path and (tmp_path / "hdd_slots.json").write_text(
        '[{"slot": 1, "device": "/dev/sdb1", "auto_mount": true}]',
        encoding="utf-8",
    )

    slots = hdd_controller.load_hdd_slots_config(app)

    assert slots[0]["device"] == "/dev/sdb1"
    assert slots[0]["auto_mount"] is True


def test_assign_disk_to_hdd_slot_prefers_live_mountpoint_then_existing_then_default():
    slot = {
        "slot": 1,
        "device": "",
        "device_uuid": "",
        "mountpoint": "/mnt/existing",
        "custom_name": "",
    }

    hdd_controller._assign_disk_to_hdd_slot(
        slot,
        "/dev/sdb",
        {"uuid": "uuid-1", "mountpoint": "/media/live"},
        "Media",
    )

    assert slot == {
        "slot": 1,
        "device": "/dev/sdb",
        "device_uuid": "uuid-1",
        "mountpoint": "/media/live",
        "custom_name": "Media",
    }

    slot = {
        "slot": 2,
        "device": "",
        "device_uuid": "",
        "mountpoint": "/mnt/existing",
        "custom_name": "",
    }

    hdd_controller._assign_disk_to_hdd_slot(
        slot,
        "/dev/sdc",
        {"uuid": "uuid-2", "mountpoint": ""},
        "",
    )

    assert slot["mountpoint"] == "/mnt/existing"


def test_hdd_find_mount_source_prefers_filesystem_child(monkeypatch):
    app = netmon.App.__new__(netmon.App)

    # App's compatibility wrapper assigns these module globals; restore them too.
    monkeypatch.setattr(hdd_controller, "run_cmd", hdd_controller.run_cmd)
    monkeypatch.setattr(hdd_controller, "has_cmd", hdd_controller.has_cmd)
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "lsblk")

    def fake_run_cmd(args, timeout=8, text=True):
        assert args == [
            "lsblk",
            "-J",
            "-p",
            "-o",
            "PATH,FSTYPE,TYPE",
            "/dev/sdb",
        ]
        return (
            0,
            """
{
  "blockdevices": [
    {
      "path": "/dev/sdb",
      "fstype": "",
      "type": "disk",
      "children": [
        {
          "path": "/dev/sdb1",
          "fstype": "ext4",
          "type": "part"
        }
      ]
    }
  ]
}
            """,
        )

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert app._hdd_find_mount_source("/dev/sdb") == "/dev/sdb1"


def test_hdd_info_async_selects_hdd_tab_immediately(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.hdd_slots = [
        {
            "slot": 1,
            "custom_name": "Media",
            "device": "/dev/sdb1",
            "device_uuid": "",
            "mountpoint": "/mnt/media",
        }
    ]
    app.hdd_slot_states = [None]
    app.tab_hdd = object()
    app.hdd_slot_choice = types.SimpleNamespace(set=lambda value: None)
    app.hdd_info_text = types.SimpleNamespace(
        delete=lambda *args: None,
        insert=lambda *args: None,
        see=lambda *args: None,
    )
    app.hdd_usage_canvas = types.SimpleNamespace(
        delete=lambda *args: None,
        winfo_width=lambda: 320,
        winfo_height=lambda: 30,
        create_rectangle=lambda *args, **kwargs: None,
        create_text=lambda *args, **kwargs: None,
    )
    app.set_light = lambda *args, **kwargs: None
    app.hdd_slot_lights = []
    app.hdd_slot_name_buttons = []
    app.hdd_custom_name_var = types.SimpleNamespace(set=lambda value: None)
    app.log = lambda message: None
    app.after = lambda delay, func: func()
    selected = []
    app._select_system_tab = lambda tab: selected.append(tab)

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        hdd_controller,
        "hdd_collect_slot_state",
        lambda _app, idx: {
            "slot": idx,
            "custom_name": "Media",
            "device": "/dev/sdb1",
            "mountpoint": "/mnt/media",
            "configured": True,
            "present": True,
            "mounted": False,
            "actual_target": "",
            "fstype": "ext4",
            "label": "Media",
            "model": "USB Disk",
            "size_bytes": 1024,
            "usage": None,
            "is_luks": False,
            "luks_locked": False,
            "luks_mapper_name": "",
            "luks_mapper_path": "",
        },
    )

    app.hdd_info_async(0)

    assert selected
    assert selected[0] is app.tab_hdd


def test_hdd_info_async_can_suppress_slot_log(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.hdd_slots = [
        {
            "slot": 1,
            "custom_name": "Media",
            "device": "/dev/sdb1",
            "device_uuid": "",
            "mountpoint": "/mnt/media",
        }
    ]
    app.hdd_slot_states = [None]
    app.tab_hdd = object()
    app.hdd_info_text = types.SimpleNamespace(
        delete=lambda *args: None,
        insert=lambda *args: None,
        see=lambda *args: None,
    )
    app.hdd_usage_canvas = types.SimpleNamespace(
        delete=lambda *args: None,
        winfo_width=lambda: 320,
        winfo_height=lambda: 30,
        create_rectangle=lambda *args, **kwargs: None,
        create_text=lambda *args, **kwargs: None,
    )
    app.hdd_info_auto_mount_var = types.SimpleNamespace(set=lambda _value: None)
    app.hdd_info_auto_mount_hint_var = types.SimpleNamespace(set=lambda _value: None)
    app.hdd_info_auto_mount_check = types.SimpleNamespace(
        configure=lambda **_kwargs: None
    )
    app.set_light = lambda *args, **kwargs: None
    app.hdd_slot_lights = []
    app.hdd_slot_name_buttons = []
    app.log = lambda message: (_ for _ in ()).throw(AssertionError(message))
    app.after = lambda delay, func: func()
    app._select_system_tab = lambda _tab: None

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        hdd_controller,
        "hdd_collect_slot_state",
        lambda _app, idx: {
            "slot": idx,
            "custom_name": "Media",
            "device": "/dev/sdb1",
            "mountpoint": "/mnt/media",
            "configured": True,
            "present": True,
            "mounted": False,
            "actual_target": "",
            "fstype": "ext4",
            "label": "Media",
            "model": "USB Disk",
            "size_bytes": 1024,
            "usage": None,
            "is_luks": False,
            "luks_locked": False,
            "luks_mapper_name": "",
            "luks_mapper_path": "",
        },
    )

    app.hdd_info_async(0, log_event=False)


def test_on_hdd_table_select_loads_info_for_selected_device(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.detected_disks_by_device = {
        "/dev/sdb1": {
            "device": "/dev/sdb1",
            "label": "Media",
            "mountpoint": "/media/test/Media",
        }
    }
    app.hdd_slots = []
    app.hdd_name_editing = False
    app.hdd_name_dirty = False
    app.hdd_slot_choice = types.SimpleNamespace(set=lambda value: None)
    app.hdd_custom_name_var = types.SimpleNamespace(set=lambda value: None)
    app.hdd_last_loaded_name = ""
    app._hdd_name_programmatic_update = False

    class DummyTable:
        def selection(self):
            return ("/dev/sdb1",)

    app.hdd_table = DummyTable()

    seen = []
    monkeypatch.setattr(
        hdd_controller,
        "hdd_info_for_device_async",
        lambda current_app, device, log_event=True: seen.append(
            (current_app, device, log_event)
        ),
    )

    hdd_controller.on_hdd_table_select(app)

    assert app.hdd_selected_device == "/dev/sdb1"
    assert seen == [(app, "/dev/sdb1", True)]


def test_on_hdd_table_select_suppresses_log_for_programmatic_refresh(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.detected_disks_by_device = {
        "/dev/sdb1": {
            "device": "/dev/sdb1",
            "label": "Media",
            "mountpoint": "/media/test/Media",
        }
    }
    app.hdd_slots = []
    app.hdd_name_editing = False
    app.hdd_name_dirty = False
    app.hdd_slot_choice = types.SimpleNamespace(set=lambda value: None)
    app.hdd_custom_name_var = types.SimpleNamespace(set=lambda value: None)
    app.hdd_last_loaded_name = ""
    app._hdd_name_programmatic_update = False
    app._hdd_programmatic_selection = True

    class DummyTable:
        def selection(self):
            return ("/dev/sdb1",)

    app.hdd_table = DummyTable()

    seen = []
    monkeypatch.setattr(
        hdd_controller,
        "hdd_info_for_device_async",
        lambda current_app, device, log_event=True: seen.append(
            (current_app, device, log_event)
        ),
    )

    hdd_controller.on_hdd_table_select(app)

    assert seen == [(app, "/dev/sdb1", False)]


def test_on_hdd_table_select_suppresses_log_for_refresh_reselection(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.detected_disks_by_device = {
        "/dev/sdb1": {
            "device": "/dev/sdb1",
            "label": "Media",
            "mountpoint": "/media/test/Media",
        }
    }
    app.hdd_slots = []
    app.hdd_name_editing = False
    app.hdd_name_dirty = False
    app.hdd_slot_choice = types.SimpleNamespace(set=lambda value: None)
    app.hdd_custom_name_var = types.SimpleNamespace(set=lambda value: None)
    app.hdd_last_loaded_name = ""
    app._hdd_name_programmatic_update = False
    app._hdd_programmatic_selection = False
    app._hdd_suppress_next_selection_log_for = "/dev/sdb1"

    class DummyTable:
        def selection(self):
            return ("/dev/sdb1",)

    app.hdd_table = DummyTable()

    seen = []
    monkeypatch.setattr(
        hdd_controller,
        "hdd_info_for_device_async",
        lambda current_app, device, log_event=True: seen.append(
            (current_app, device, log_event)
        ),
    )

    hdd_controller.on_hdd_table_select(app)

    assert seen == [(app, "/dev/sdb1", False)]
    assert app._hdd_suppress_next_selection_log_for is None


def test_on_hdd_table_select_suppresses_log_for_same_displayed_device(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.detected_disks_by_device = {
        "/dev/sdb1": {
            "device": "/dev/sdb1",
            "label": "Media",
            "mountpoint": "/media/test/Media",
        }
    }
    app.hdd_slots = []
    app.hdd_name_editing = False
    app.hdd_name_dirty = False
    app.hdd_slot_choice = types.SimpleNamespace(set=lambda value: None)
    app.hdd_custom_name_var = types.SimpleNamespace(set=lambda value: None)
    app.hdd_last_loaded_name = ""
    app._hdd_name_programmatic_update = False
    app.hdd_info_selected_device = "/dev/sdb1"

    class DummyTable:
        def selection(self):
            return ("/dev/sdb1",)

    app.hdd_table = DummyTable()

    seen = []
    monkeypatch.setattr(
        hdd_controller,
        "hdd_info_for_device_async",
        lambda current_app, device, log_event=True: seen.append(
            (current_app, device, log_event)
        ),
    )

    hdd_controller.on_hdd_table_select(app)

    assert seen == [(app, "/dev/sdb1", False)]


def test_hdd_info_for_device_async_does_not_select_hdd_tab(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.tab_hdd = object()
    app.hdd_info_text = types.SimpleNamespace(
        delete=lambda *args: None,
        insert=lambda *args: None,
        see=lambda *args: None,
    )
    app.hdd_usage_canvas = types.SimpleNamespace(
        delete=lambda *args: None,
        winfo_width=lambda: 320,
        winfo_height=lambda: 30,
        create_rectangle=lambda *args, **kwargs: None,
        create_text=lambda *args, **kwargs: None,
    )
    app.hdd_info_auto_mount_var = types.SimpleNamespace(set=lambda _value: None)
    app.hdd_info_auto_mount_hint_var = types.SimpleNamespace(set=lambda _value: None)
    app.hdd_info_auto_mount_check = types.SimpleNamespace(
        configure=lambda **_kwargs: None
    )
    app.hdd_slots = []
    app.hdd_selected_device = None
    app.hdd_info_selected_device = ""
    app._hdd_auto_mount_programmatic_update = False
    app.log = lambda _message: None
    app.after = lambda _delay, func: func()
    selected = []
    app._select_system_tab = lambda tab: selected.append(tab)

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        hdd_controller,
        "hdd_collect_device_state",
        lambda _app, _device: {
            "device": "/dev/sdb1",
            "mountpoint": "/mnt/media",
            "mounted": False,
            "usage": None,
            "is_luks": False,
            "luks_locked": False,
            "label": "Media",
            "model": "",
            "fstype": "ext4",
            "size_bytes": 1024,
            "actual_target": "",
            "custom_name": "",
        },
    )

    hdd_controller.hdd_info_for_device_async(app, "/dev/sdb1")

    assert selected == []


def test_on_hdd_auto_mount_toggle_updates_selected_slot(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.hdd_selected_device = "/dev/sdb1"
    app.hdd_slots = [
        {
            "slot": 1,
            "custom_name": "Media",
            "device": "/dev/sdb1",
            "device_uuid": "",
            "mountpoint": "/mnt/media",
            "auto_mount": False,
        }
    ]
    app.detected_disks_by_device = {
        "/dev/sdb1": {
            "device": "/dev/sdb1",
            "label": "Media",
            "mountpoint": "/mnt/media",
            "is_luks": False,
        }
    }
    app.hdd_info_auto_mount_var = types.SimpleNamespace(
        get=lambda: True, set=lambda _v: None
    )
    app.hdd_info_auto_mount_hint_var = types.SimpleNamespace(set=lambda _v: None)
    app.hdd_info_auto_mount_check = types.SimpleNamespace(
        configure=lambda **_kwargs: None
    )
    app._hdd_auto_mount_programmatic_update = False
    app.log = lambda _message: None

    saved = []
    monkeypatch.setattr(
        hdd_controller, "save_hdd_config", lambda current_app: saved.append(current_app)
    )

    hdd_controller.on_hdd_auto_mount_toggle(app)

    assert app.hdd_slots[0]["auto_mount"] is True
    assert saved == [app]


def test_hdd_sync_auto_mount_ui_disables_luks_devices(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.hdd_slots = [
        {
            "slot": 1,
            "custom_name": "Vault",
            "device": "/dev/sdb",
            "device_uuid": "",
            "mountpoint": "/mnt/vault",
            "auto_mount": True,
        }
    ]
    app.detected_disks_by_device = {
        "/dev/sdb": {
            "device": "/dev/sdb",
            "label": "Vault",
            "mountpoint": "",
            "is_luks": True,
            "luks_locked": True,
        }
    }

    seen = {"enabled": None, "hint": None, "state": None}
    app.hdd_info_auto_mount_var = types.SimpleNamespace(
        set=lambda value: seen.__setitem__("enabled", value)
    )
    app.hdd_info_auto_mount_hint_var = types.SimpleNamespace(
        set=lambda value: seen.__setitem__("hint", value)
    )
    app.hdd_info_auto_mount_check = types.SimpleNamespace(
        configure=lambda **kwargs: seen.__setitem__("state", kwargs.get("state"))
    )
    app._hdd_auto_mount_programmatic_update = False
    app.log = lambda _message: None

    saved = []
    monkeypatch.setattr(
        hdd_controller, "save_hdd_config", lambda current_app: saved.append(current_app)
    )

    hdd_controller.hdd_sync_auto_mount_ui(
        app,
        {
            "device": "/dev/sdb",
            "is_luks": True,
            "mountpoint": "/mnt/vault",
        },
    )

    assert app.hdd_slots[0]["auto_mount"] is False
    assert seen["enabled"] is False
    assert seen["state"] == "disabled"
    assert "LUKS" in seen["hint"]
    assert saved == [app]


def test_hdd_startup_auto_mount_schedules_only_non_luks_slots(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.hdd_slots = [
        {
            "slot": 1,
            "custom_name": "Media",
            "device": "/dev/sdb1",
            "device_uuid": "",
            "mountpoint": "/mnt/media",
            "auto_mount": True,
        },
        {
            "slot": 2,
            "custom_name": "Vault",
            "device": "/dev/sdc",
            "device_uuid": "",
            "mountpoint": "/mnt/vault",
            "auto_mount": True,
        },
    ]
    app.log = lambda _message: None
    calls = []
    app.after = lambda _delay, func: func()

    monkeypatch.setattr(
        hdd_controller,
        "hdd_collect_slot_state",
        lambda _app, idx: {"is_luks": idx == 1},
    )
    monkeypatch.setattr(
        hdd_controller, "hdd_mount_async", lambda _app, idx: calls.append(idx)
    )
    monkeypatch.setattr(hdd_controller, "save_hdd_config", lambda _app: None)

    hdd_controller.hdd_startup_auto_mount(app)

    assert calls == [0]
    assert app.hdd_slots[1]["auto_mount"] is False


def test_hdd_unmount_async_uses_resolved_mount_source_and_actual_target(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.hdd_slots = [
        {
            "slot": 1,
            "custom_name": "Media",
            "device": "/dev/sdb",
            "device_uuid": "synthetic-disk-uuid",
            "mountpoint": "/mnt/media",
        }
    ]
    logs = []
    calls = []
    disk = {"device": "/dev/sdb", "uuid": "synthetic-disk-uuid"}
    app.detected_disks = [disk]
    app.detected_disks_by_device = {"/dev/sdb": disk}
    identity = hdd_mount_service.MountIdentity(
        hdd_mount_service.DeviceIdentity(
            "/dev/sdb", "synthetic-disk-uuid", 1, "disk", ""
        ),
        hdd_mount_service.DeviceIdentity(
            "/dev/sdb1", "synthetic-fs-uuid", 2, "part", "ext4"
        ),
    )
    checks = []

    def inspect(device, uuid, runner):
        assert (device, uuid) == ("/dev/sdb", "synthetic-disk-uuid")
        return identity

    def verified_mount(current, runner):
        assert current == identity
        checks.append(True)
        return "/media/test/Media"

    # This UI/fallback unit test simulates policy results; the security tests
    # exercise the actual inventory and exact mount verification separately.
    monkeypatch.setattr(hdd_mount_service, "inspect_device", inspect)
    monkeypatch.setattr(hdd_mount_service, "verified_mount_target", verified_mount)

    app.ensure_sudo_session = lambda _label: True
    monkeypatch.setattr(
        hdd_controller,
        "_authorize_hdd_unmount",
        lambda current_app, _runner: current_app.ensure_sudo_session("HDD Unmount"),
    )
    app._slot_display_name = lambda idx: "Media"
    app._hdd_resolve_slot_device = lambda slot: (
        slot["device"],
        {"device": slot["device"]},
    )
    app.hdd_slot_configured = lambda slot: True
    app._hdd_luks_info_for_device = lambda device: {"is_luks": False, "mapper_name": ""}
    app._hdd_find_mount_source = lambda device: "/dev/sdb1"
    app._hdd_is_mounted = lambda device, mountpoint: (True, "/media/test/Media")
    app.hdd_refresh_async = lambda: logs.append("refresh")
    app.hdd_info_async = lambda idx: logs.append(f"info:{idx}")
    app.log = logs.append
    app.after = lambda delay, func: func()

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "udisksctl")

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args[:4] == ["sudo", "-n", "umount", "/media/test/Media"]:
            return 1, "busy"
        if args[:4] == ["sudo", "-n", "umount", "/dev/sdb1"]:
            return 1, "not mounted"
        if args[:2] == ["umount", "/media/test/Media"]:
            return 1, "still busy"
        return 0, "ok"

    monkeypatch.setattr(hdd_mount_service, "run_hdd_command", fake_run_cmd)

    app.hdd_unmount_async(0)

    assert calls == [
        ["sudo", "-n", "umount", "/media/test/Media"],
        ["sudo", "-n", "umount", "/dev/sdb1"],
        ["umount", "/media/test/Media"],
        ["udisksctl", "unmount", "-b", "/dev/sdb1"],
    ]
    assert len(checks) == 5  # initial binding plus each attempted unmount
