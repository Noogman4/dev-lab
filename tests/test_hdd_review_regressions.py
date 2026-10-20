"""HDD review regressions: synthetic devices and command fakes exclusively."""

from copy import deepcopy
from types import SimpleNamespace
import threading

import pytest

from netmon.features import hdd_controller as controller
from netmon.services import hdd_mount_service as service
from tests.test_hdd_mount_security import DEVICE, MAPPER
from tests.test_hdd_mount_security import kernel as kernel
from tests.test_hdd_mount_security import mount_app as mount_app
from tests.test_hdd_mount_security import unmount_app as unmount_app

REAL_THREAD = threading.Thread


def crypt_device(kernel, state):
    kernel.node["fstype"] = "crypto_LUKS"
    kernel.node["children"] = [
        {
            "path": MAPPER,
            "type": "crypt",
            "fstype": "ext4",
            "uuid": "clear-uuid",
            "maj:min": "253:0",
        }
    ]
    state.row.update(source=MAPPER, uuid="clear-uuid", **{"maj:min": "253:0"})


@pytest.mark.parametrize(
    "outcome",
    [
        "missing",
        "not-closed",
        "closed",
        "failed",
        "failed-empty",
        "changed",
        "orphan",
        "stat-present",
        "error",
    ],
)
def test_close_requires_actual_mapper_disappearance(
    kernel, unmount_app, monkeypatch, outcome
):
    crypt_device(kernel, unmount_app)
    monkeypatch.setattr(service.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(
        controller,
        "has_cmd",
        lambda tool: not (outcome == "missing" and tool == "cryptsetup"),
    )

    def mutate(args):
        if outcome == "changed" and args[:3] == ["sudo", "-n", "umount"]:
            kernel.node["uuid"] = "replacement"
        if "cryptsetup" not in args:
            return
        if outcome == "error":
            raise OSError("synthetic close error")
        if outcome == "failed":
            unmount_app.result = (1, "synthetic busy")
        if outcome == "failed-empty":
            unmount_app.result = (1, "")
        if outcome in {"closed", "orphan", "stat-present"}:
            child = kernel.node.pop("children")[0]
            if outcome == "orphan":
                kernel.roots.append(child)
            if outcome != "stat-present":
                kernel.stats.pop(MAPPER, None)

    unmount_app.on_command = mutate
    controller.hdd_unmount_async(unmount_app.app, 0)
    logs = unmount_app.app.logs
    assert any("unmount successful" in line for line in logs)
    assert any("LUKS closed:" in line for line in logs) is (outcome == "closed")
    assert any("LUKS close failed" in line for line in logs) is (outcome != "closed")
    if outcome in {"missing", "changed"}:
        assert not any("cryptsetup" in command for command in unmount_app.effects)


@pytest.mark.parametrize("action", ["mount", "unmount"])
def test_no_inventory_or_effects_before_worker(
    kernel, unmount_app, monkeypatch, action
):
    if action == "mount":
        monkeypatch.setattr(service, "run_hdd_command", kernel.runner)
    pending = []

    class DeferredThread:
        def __init__(self, target, **kwargs):
            pending.append(target)

        def start(self):
            pass

    monkeypatch.setattr(controller.threading, "Thread", DeferredThread)
    getattr(controller, f"hdd_{action}_async")(unmount_app.app, 0)
    assert not kernel.calls and not unmount_app.effects and not unmount_app.auth
    assert len(pending) == 1
    pending[0]()
    assert kernel.calls


@pytest.mark.parametrize("action", ["mount", "unmount"])
def test_blocked_inventory_leaves_ui_caller_free(
    kernel, unmount_app, monkeypatch, action
):
    entered = threading.Event()
    release = threading.Event()
    workers = []
    ui_ident = threading.get_ident()
    original = kernel.runner if action == "mount" else service.run_hdd_command

    def runner(args, **kwargs):
        assert threading.get_ident() != ui_ident
        if args[0] == "lsblk":
            entered.set()
            assert release.wait(3)
        return original(args, **kwargs)

    def thread(target, **kwargs):
        worker = REAL_THREAD(target=target, **kwargs)
        workers.append(worker)
        return worker

    monkeypatch.setattr(service, "run_hdd_command", runner)
    monkeypatch.setattr(controller.threading, "Thread", thread)
    callbacks = []
    unmount_app.app.after = lambda _delay, fn: callbacks.append(fn)
    try:
        getattr(controller, f"hdd_{action}_async")(unmount_app.app, 0)
        assert entered.wait(3)
        assert workers[0].is_alive()  # Main thread can still handle UI work.
    finally:
        release.set()
        for worker in workers:
            worker.join(3)
            assert not worker.is_alive()
    for callback in callbacks:
        callback()


@pytest.mark.parametrize("stage", ["scan", "state", "render"])
def test_refresh_error_releases_latch_and_preserves_live_inventory(monkeypatch, stage):
    old_map = {"old": {"device": "old"}}
    app = SimpleNamespace(
        hdd_slots=[{"device": "old"}],
        detected_disks_by_device=old_map,
        hdd_refresh_running=False,
        logs=[],
        hdd_slot_states=[],
    )
    app.log = app.logs.append
    app.after = lambda _delay, fn: fn()

    def fail():
        raise ValueError("synthetic refresh failure")

    app.scan_hdds = fail if stage == "scan" else lambda: [{"device": "new"}]

    def state(snapshot, _idx):
        assert app.detected_disks_by_device is old_map
        assert snapshot.detected_disks_by_device is not old_map
        if stage == "state":
            fail()
        return {"configured": False}

    monkeypatch.setattr(controller, "hdd_collect_slot_state", state)
    monkeypatch.setattr(
        controller,
        "refresh_hdd_table",
        lambda *_a, **_k: fail() if stage == "render" else None,
    )
    monkeypatch.setattr(controller, "hdd_apply_slot_lights", lambda *_a: None)

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(controller.threading, "Thread", Immediate)
    controller.hdd_refresh_async(app)
    assert app.hdd_refresh_running is False
    if stage != "render":
        assert app.detected_disks_by_device is old_map
    assert any("fehlgeschlagen" in line for line in app.logs)
    app.logs.clear()
    controller.hdd_refresh_async(app)
    assert app.logs  # A subsequent refresh is attempted rather than blocked.


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        {"slot": True},
        {"slot": 1.5},
        {"slot": "oops"},
        {"slot": 2, "custom_name": 7},
        {"slot": 2, "device": []},
        {"slot": 2, "device_uuid": None},
        {"slot": 2, "mountpoint": False},
        {"slot": 2, "auto_mount": "false"},
        {"slot": 2, "auto_mount": 1},
    ],
)
def test_invalid_slot_does_not_discard_following_valid_entries(tmp_path, bad):
    import json

    path = tmp_path / "slots.json"
    path.write_text(
        json.dumps(
            [
                {"slot": 1, "custom_name": "first"},
                bad,
                {"slot": "3", "custom_name": "last", "auto_mount": False},
            ]
        )
    )
    logs = []
    app = SimpleNamespace(hdd_config_path=str(path), log=logs.append)
    slots = controller.load_hdd_slots_config(app)
    assert slots[0]["custom_name"] == "first"
    assert slots[1]["auto_mount"] is False
    assert slots[2]["custom_name"] == "last"
    assert any("übersprungen" in line for line in logs)


def storage_app(monkeypatch, success):
    app = SimpleNamespace(
        hdd_slots=controller.default_hdd_slots(),
        hdd_config_path="/synthetic/config",
        hdd_name_dirty=True,
        hdd_last_loaded_name="previous",
        logs=[],
    )
    app.log = app.logs.append
    app.tr = lambda _key, fallback: fallback
    app.hdd_slots[0].update(device="/dev/old", custom_name="previous")
    app.hdd_table = SimpleNamespace(selection=lambda: [DEVICE])
    app.hdd_slot_choice = SimpleNamespace(get=lambda: "1")
    app.hdd_custom_name_var = SimpleNamespace(get=lambda: "edited name")
    app.detected_disks_by_device = {DEVICE: {"device": DEVICE, "uuid": "test-uuid"}}
    monkeypatch.setattr(
        controller,
        "safe_write_json",
        lambda *_a, **_kw: (success, "synthetic disk full"),
    )
    for name in ["refresh_hdd_table", "update_hdd_buttons", "hdd_sync_auto_mount_ui"]:
        monkeypatch.setattr(controller, name, lambda *_a, **_kw: None)
    app.hdd_refresh_async = lambda: None
    return app


@pytest.mark.parametrize("success", [False, True])
def test_assignment_only_clears_dirty_state_after_successful_save(monkeypatch, success):
    app = storage_app(monkeypatch, success)
    before = deepcopy(app.hdd_slots)
    controller.assign_selected_disk_to_slot(app)
    assert app.hdd_config_dirty is not success
    assert app.hdd_name_dirty is not success
    assert any("Zuordnung übernommen" in line for line in app.logs) is success
    if not success:
        assert app.hdd_slots == before
        assert app.hdd_last_loaded_name == "previous"
        assert app.hdd_custom_name_var.get() == "edited name"


def test_failed_clear_preserves_assignment_selection_and_dirty_state(monkeypatch):
    app = storage_app(monkeypatch, False)
    app.hdd_selected_device = "/dev/old"
    before = deepcopy(app.hdd_slots)
    assert controller.clear_slot_assignment(app) is False
    assert app.hdd_slots == before
    assert app.hdd_selected_device == "/dev/old"
    assert app.hdd_name_dirty is True
    assert not any("Zuordnung aufgehoben" in line for line in app.logs)


def test_failed_automount_save_restores_previous_setting(monkeypatch):
    app = storage_app(monkeypatch, False)
    app.hdd_selected_device = DEVICE
    app.hdd_slots[0].update(device=DEVICE, device_uuid="test-uuid")
    app.hdd_info_auto_mount_var = SimpleNamespace(get=lambda: True)
    assert controller.on_hdd_auto_mount_toggle(app) is False
    assert app.hdd_slots[0]["auto_mount"] is False
    assert app.hdd_config_dirty is True
    assert not any("automount enabled" in line for line in app.logs)


def test_secret_dialog_is_dispatched_to_ui_not_command_worker(monkeypatch):
    callbacks = []
    scheduled = threading.Event()
    result = []
    ui_ident = threading.get_ident()

    def after(_delay, callback):
        callbacks.append(callback)
        scheduled.set()

    app = SimpleNamespace(after=after)

    def ask(*_args, **_kwargs):
        assert threading.get_ident() == ui_ident
        return "synthetic passphrase"

    monkeypatch.setattr(controller.simpledialog, "askstring", ask)
    worker = REAL_THREAD(
        target=lambda: result.append(
            controller._ask_hdd_secret(app, "title", "prompt")
        ),
        daemon=True,
    )
    worker.start()
    try:
        assert scheduled.wait(3)
        assert worker.is_alive()
        callbacks.pop()()
    finally:
        # Always release the synthetic worker if a UI assertion fails.
        for callback in callbacks:
            callback()
        worker.join(3)
    assert not worker.is_alive()
    assert result == ["synthetic passphrase"]


def test_refresh_thread_start_failure_releases_latch(monkeypatch):
    app = SimpleNamespace(hdd_refresh_running=False, hdd_slots=[], logs=[])
    app.log = app.logs.append

    class UnavailableThread:
        def __init__(self, **kwargs):
            pass

        def start(self):
            raise RuntimeError("synthetic thread limit")

    monkeypatch.setattr(controller.threading, "Thread", UnavailableThread)
    controller.hdd_refresh_async(app)
    assert app.hdd_refresh_running is False
    assert any("synthetic thread limit" in line for line in app.logs)


def test_refresh_unexpected_programming_error_is_reported_and_reraised(monkeypatch):
    app = SimpleNamespace(hdd_refresh_running=False, hdd_slots=[], logs=[])
    app.log = app.logs.append

    def fail():
        raise ZeroDivisionError("synthetic programming error")

    app.scan_hdds = fail

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(controller.threading, "Thread", Immediate)
    with pytest.raises(ZeroDivisionError):
        controller.hdd_refresh_async(app)
    assert app.hdd_refresh_running is False
    assert any("synthetic programming error" in line for line in app.logs)


def test_startup_does_not_unlock_luks_even_with_stale_display_cache(
    kernel, mount_app, monkeypatch
):
    kernel.node["fstype"] = "crypto_LUKS"
    monkeypatch.setattr(
        controller.simpledialog,
        "askstring",
        lambda *_a, **_kw: pytest.fail("No automatic passphrase prompt"),
    )
    controller.hdd_mount_async(mount_app, 0, select_tab=False, allow_unlock=False)
    assert not any(args[0] == "udisksctl" for args in kernel.calls)
    assert any("LUKS automount is disabled" in line for line in mount_app.logs)


@pytest.mark.parametrize("luks", [False, True])
def test_startup_uses_inventory_cache_when_slot_state_not_ready(
    kernel, mount_app, monkeypatch, luks
):
    mount_app.hdd_slots[0]["auto_mount"] = True
    mount_app.hdd_slot_states = [None]
    mount_app.detected_disks_by_device[DEVICE]["is_luks"] = luks
    calls = []
    monkeypatch.setattr(
        controller,
        "hdd_mount_async",
        lambda app, idx, **kwargs: calls.append((idx, kwargs)),
    )
    monkeypatch.setattr(controller, "save_hdd_config", lambda app: True)
    monkeypatch.setattr(
        controller,
        "hdd_collect_slot_state",
        lambda *_a: pytest.fail("No UI inventory query"),
    )
    controller.hdd_startup_auto_mount(mount_app)
    assert not kernel.calls
    if luks:
        assert calls == [] and mount_app.hdd_slots[0]["auto_mount"] is False
    else:
        assert calls == [(0, {"select_tab": False, "allow_unlock": False})]


@pytest.mark.parametrize("action", ["mount", "unmount"])
def test_selected_device_number_cannot_be_rebased_after_worker_wait(
    kernel, unmount_app, monkeypatch, action
):
    import os
    import stat

    pending = []

    class Deferred:
        def __init__(self, target, **kwargs):
            pending.append(target)

        def start(self):
            pass

    if action == "mount":
        monkeypatch.setattr(service, "run_hdd_command", kernel.runner)
    monkeypatch.setattr(controller.threading, "Thread", Deferred)
    getattr(controller, f"hdd_{action}_async")(unmount_app.app, 0)
    assert not kernel.calls and not unmount_app.effects and not unmount_app.auth
    assert len(pending) == 1
    # Same path and UUID; only the kernel device and its mount have changed.
    kernel.node["maj:min"] = "8:99"
    kernel.stats[DEVICE] = (stat.S_IFBLK, os.makedev(8, 99))
    unmount_app.row.update(target="/mnt/synthetic-replacement", **{"maj:min": "8:99"})
    pending.pop()()
    assert not unmount_app.effects
    assert not any(args[0] == "udisksctl" for args in kernel.calls)
    assert not unmount_app.auth
    assert any("rejected" in line or "refused" in line for line in unmount_app.app.logs)


def queue_bound_request(kernel, state, monkeypatch, action):
    pending = []

    class Deferred:
        def __init__(self, target, **kwargs):
            pending.append(target)

        def start(self):
            pass

    if action == "mount":
        monkeypatch.setattr(service, "run_hdd_command", kernel.runner)
    monkeypatch.setattr(controller.threading, "Thread", Deferred)
    getattr(controller, f"hdd_{action}_async")(state.app, 0)
    return pending


def assert_no_hdd_effects(kernel, state):
    assert not state.effects and not state.auth
    assert not any(args[0] == "udisksctl" for args in kernel.calls)
    assert any("rejected" in line or "refused" in line for line in state.app.logs)


@pytest.mark.parametrize("action", ["mount", "unmount"])
@pytest.mark.parametrize(
    "failure",
    [
        "missing-node",
        "permission",
        "missing-number",
        "missing-node-device",
        "missing-inode",
        "invalid-number",
        "zero-number",
        "zero-inode",
        "not-block",
        "missing-uuid",
    ],
)
def test_incomplete_original_binding_never_schedules_worker(
    kernel, unmount_app, monkeypatch, action, failure
):
    import stat

    original_stat = controller.os.stat
    if failure == "missing-uuid":
        unmount_app.app.hdd_slots[0]["device_uuid"] = ""

    def stat_node(path, *args, **kwargs):
        if str(path) != DEVICE:
            return original_stat(path, *args, **kwargs)
        if failure == "missing-node":
            raise FileNotFoundError("synthetic removal")
        if failure == "permission":
            raise PermissionError("synthetic stat denial")
        values = vars(original_stat(path, *args, **kwargs)).copy()
        missing = {
            "missing-number": "st_rdev",
            "missing-node-device": "st_dev",
            "missing-inode": "st_ino",
        }.get(failure)
        if missing:
            del values[missing]
        if failure == "invalid-number":
            values["st_rdev"] = "8:17"
        if failure == "zero-number":
            values["st_rdev"] = 0
        if failure == "zero-inode":
            values["st_ino"] = 0
        if failure == "not-block":
            values["st_mode"] = stat.S_IFREG
        return SimpleNamespace(**values)

    monkeypatch.setattr(controller.os, "stat", stat_node)
    pending = queue_bound_request(kernel, unmount_app, monkeypatch, action)
    assert not pending and not kernel.calls
    assert_no_hdd_effects(kernel, unmount_app)


@pytest.mark.parametrize("action", ["mount", "unmount"])
@pytest.mark.parametrize(
    "change",
    [
        "inode",
        "node-device",
        "stat-denied",
        "inventory-error",
        "inventory-json",
        "during-inventory",
    ],
)
def test_bound_request_revalidation_failure_is_closed(
    kernel, unmount_app, monkeypatch, action, change
):
    import os
    import stat

    original_stat = controller.os.stat
    changed = [False]

    def stat_node(path, *args, **kwargs):
        if str(path) == DEVICE and changed[0] and change == "stat-denied":
            raise PermissionError("synthetic worker stat denial")
        info = original_stat(path, *args, **kwargs)
        if str(path) == DEVICE and changed[0] and change in {"inode", "node-device"}:
            values = vars(info).copy()
            values["st_ino" if change == "inode" else "st_dev"] += 1
            return SimpleNamespace(**values)
        return info

    monkeypatch.setattr(controller.os, "stat", stat_node)
    pending = queue_bound_request(kernel, unmount_app, monkeypatch, action)
    assert len(pending) == 1 and not kernel.calls
    changed[0] = True
    if change == "inventory-error":
        kernel.inventory_rc = 1
    elif change == "inventory-json":
        kernel.raw = "{"
    elif change == "during-inventory":

        def switch(args):
            if args[0] == "lsblk":
                kernel.node["maj:min"] = "8:99"
                kernel.stats[DEVICE] = (stat.S_IFBLK, os.makedev(8, 99))
                unmount_app.row["maj:min"] = "8:99"

        kernel.on_command = switch
    pending.pop()()
    assert_no_hdd_effects(kernel, unmount_app)


@pytest.mark.parametrize("action", ["mount", "unmount"])
def test_same_bound_device_still_completes_normally(
    kernel, unmount_app, monkeypatch, action
):
    pending = queue_bound_request(kernel, unmount_app, monkeypatch, action)
    assert len(pending) == 1 and not kernel.calls
    pending.pop()()
    if action == "mount":
        assert [args for args in kernel.calls if args[0] == "udisksctl"] == [
            [
                "udisksctl",
                "mount",
                "--block-device",
                DEVICE,
                "--options",
                "nodev,nosuid,noexec",
            ]
        ]
        assert any("desktop-integriert" in line for line in unmount_app.app.logs)
    else:
        assert unmount_app.effects == [["sudo", "-n", "umount", unmount_app.target]]
        assert any("unmount successful" in line for line in unmount_app.app.logs)


@pytest.mark.parametrize("action", ["mount", "unmount"])
@pytest.mark.parametrize("switch_alias", [False, True])
def test_alias_remains_bound_to_original_canonical_node(
    kernel, unmount_app, monkeypatch, action, switch_alias
):
    alias = "/dev/netmon_synthetic_alias"
    target = [DEVICE]
    original_realpath = controller.os.path.realpath
    original_stat = controller.os.stat
    monkeypatch.setattr(
        controller.os.path,
        "realpath",
        lambda path: target[0] if path == alias else original_realpath(path),
    )
    monkeypatch.setattr(
        controller.os,
        "stat",
        lambda path, *args, **kwargs: original_stat(
            target[0] if path == alias else path, *args, **kwargs
        ),
    )
    disk = {"device": alias, "uuid": unmount_app.app.hdd_slots[0]["device_uuid"]}
    unmount_app.app.hdd_slots[0]["device"] = alias
    unmount_app.app.detected_disks = [disk]
    unmount_app.app.detected_disks_by_device = {alias: disk}
    pending = queue_bound_request(kernel, unmount_app, monkeypatch, action)
    assert len(pending) == 1
    if switch_alias:
        target[0] = MAPPER
    pending.pop()()
    if switch_alias:
        assert_no_hdd_effects(kernel, unmount_app)
    else:
        assert any(
            "successful" in line or "desktop-integriert" in line
            for line in unmount_app.app.logs
        )


def test_request_binding_is_frozen_and_independent_of_slot_edits(kernel, mount_app):
    from dataclasses import FrozenInstanceError
    import os

    binding = controller._capture_hdd_request_device(
        DEVICE, mount_app.hdd_slots[0]["device_uuid"]
    )
    original_uuid = binding.uuid
    with pytest.raises(FrozenInstanceError):
        binding.number = os.makedev(8, 99)
    mount_app.hdd_slots[0].update(device="/dev/replacement", device_uuid="replacement")
    assert binding.path == DEVICE and binding.uuid == original_uuid
    assert binding.number == os.makedev(8, 17)


def test_node_replacement_during_passphrase_dialog_never_unlocks(
    kernel, mount_app, monkeypatch
):
    kernel.node["fstype"] = "crypto_LUKS"
    changed = [False]
    original_stat = controller.os.stat

    def stat_node(path, *args, **kwargs):
        info = original_stat(path, *args, **kwargs)
        if str(path) == DEVICE and changed[0]:
            return SimpleNamespace(**{**vars(info), "st_ino": info.st_ino + 1})
        return info

    def dialog(*args, **kwargs):
        changed[0] = True
        return "test-passphrase"

    monkeypatch.setattr(controller.os, "stat", stat_node)
    monkeypatch.setattr(controller.simpledialog, "askstring", dialog)
    controller.hdd_mount_async(mount_app, 0)
    assert not any(args[0] == "udisksctl" for args in kernel.calls)
    assert any("rejected" in line for line in mount_app.logs)
