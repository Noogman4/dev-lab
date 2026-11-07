"""Native LUKS system mounts with synthetic devices, bus replies and passphrases."""

import copy
import json
import os
import stat
from types import SimpleNamespace

import pytest

from netmon.features import hdd_controller as controller
from netmon.services import hdd_mount_service as service
from tests.test_hdd_mount_security import DEVICE, MAPPER, UUID
from tests.test_hdd_mount_security import kernel as kernel
from tests.test_hdd_mount_security import mount_app as mount_app

INNER = "11111111-2222-3333-4444-555555555555"
ALIAS = "/dev/disk/by-uuid/" + INNER
TARGET = "/mnt/" + INNER
OBJECT = "/org/freedesktop/UDisks2/block_devices/synthetic"
OPTIONS = "nosuid,nodev,nofail,x-gvfs-show,noauto"
REAL_TARGET_BINDING = service._system_target_binding


def variant(value, kind="s"):
    return {"type": kind, "data": value}


def byte_path(value):
    return variant(list(value.encode()) + [0], "ay")


@pytest.fixture
def native(kernel, mount_app, monkeypatch):
    kernel.node["fstype"] = "crypto_LUKS"
    kernel.node["children"] = [
        {
            "path": MAPPER,
            "type": "crypt",
            "fstype": "ext4",
            "uuid": INNER,
            "maj:min": "253:0",
        }
    ]
    kernel.stats[ALIAS] = kernel.stats[MAPPER]
    realpath = os.path.realpath
    monkeypatch.setattr(
        service.os.path, "realpath", lambda p: MAPPER if p == ALIAS else realpath(p)
    )
    state = SimpleNamespace(
        fields=[ALIAS, TARGET, "auto", OPTIONS, "0", "0"],
        props={
            "Device": byte_path(MAPPER),
            "DeviceNumber": variant(os.makedev(253, 0), "t"),
            "IdUUID": variant(INNER),
            "IdType": variant("ext4"),
            "IdUsage": variant("filesystem"),
            "Symlinks": variant([list(ALIAS.encode()) + [0]], "aay"),
        },
        dialogs=[],
        bus_calls=[],
        target_nodes=((1, 42, stat.S_IFDIR | 0o755, 0),),
        live_target=TARGET,
        on_bus=None,
    )

    def write_entry():
        kernel.table.write_text(" ".join(state.fields) + "\n")
        kernel.fstab = (
            0,
            json.dumps(
                {
                    "filesystems": [
                        {
                            "source": state.fields[0],
                            "fstype": state.fields[2],
                        }
                    ]
                }
            ),
        )
        config = {
            k: byte_path(v)
            for k, v in zip(("fsname", "dir", "type", "opts"), state.fields[:4])
        }
        config.update(
            freq=variant(int(state.fields[4]), "i"),
            passno=variant(int(state.fields[5]), "i"),
        )
        state.props["Configuration"] = variant([["fstab", config]], "a(sa{sv})")

    def runner(args, **kwargs):
        if args[0] == "busctl":
            state.bus_calls.append(args)
            if state.on_bus:
                state.on_bus(args)
            if "ResolveDevice" in args:
                return 0, json.dumps({"type": "ao", "data": [[OBJECT]]})
            return 0, json.dumps({"type": "a{sv}", "data": [state.props]})
        if args[0] == "findmnt" and "--kernel" in args:
            kernel.calls.append(args)
            return 0, json.dumps(
                {
                    "filesystems": [
                        {
                            "source": MAPPER,
                            "target": state.live_target,
                            "uuid": INNER,
                            "maj:min": "253:0",
                        }
                    ]
                }
            )
        result = kernel.runner(args, **kwargs)
        if args[:2] == ["udisksctl", "unlock"] and result[0] == 0:
            kernel.node["children"][0]["uuid"] = INNER
        return result

    def ask(*args, **kwargs):
        state.dialogs.append((args, kwargs))
        pytest.fail(
            "Native system mounts must not ask for an extra NetMon confirmation"
        )

    write_entry()
    state.write_entry = write_entry
    state.runner = runner
    monkeypatch.setattr(
        service, "_system_target_binding", lambda target: state.target_nodes
    )
    monkeypatch.setattr(service, "run_hdd_command", runner)
    monkeypatch.setattr(controller.messagebox, "askyesno", ask)
    monkeypatch.setattr(
        controller.simpledialog, "askstring", lambda *a, **kw: "test-passphrase"
    )
    return state


def effects(kernel):
    return [c for c in kernel.calls if c[0] == "udisksctl"]


def identity(native):
    return service.inspect_device(DEVICE, UUID, native.runner)


@pytest.mark.parametrize("locked", [False, True])
@pytest.mark.parametrize("source_form", ["alias", "tag"])
def test_native_mount_binds_real_flow_without_extra_confirmation(
    kernel, mount_app, native, locked, source_form
):
    before = copy.deepcopy(mount_app.hdd_slots)
    if locked:
        kernel.node.pop("children")
    if source_form == "tag":
        native.fields[0] = "UUID=" + INNER
        native.write_entry()
    controller.hdd_mount_async(mount_app, 0)
    assert effects(kernel)[-1] == ["udisksctl", "mount", "--block-device", MAPPER]
    assert len(effects(kernel)) == (2 if locked else 1)
    if locked:
        assert not kernel.key.exists()
    assert not native.dialogs
    assert any("system-mounted" in msg and OPTIONS in msg for msg in mount_app.logs)
    assert mount_app.hdd_slots == before
    controller.hdd_mount_async(mount_app, 0)
    assert not native.dialogs
    assert len(effects(kernel)) == (3 if locked else 2)


def test_default_service_still_refuses_system_mount(kernel, native):
    with pytest.raises(service.MountPolicyError, match="fstab-managed"):
        service.mount_device(identity(native), native.runner)
    assert not effects(kernel)


@pytest.mark.parametrize(
    "key,value",
    [
        ("Device", byte_path("/dev/foreign")),
        ("DeviceNumber", variant(999, "t")),
        ("IdUUID", variant("foreign")),
        ("IdType", variant("xfs")),
        ("IdUsage", variant("crypto")),
        ("Symlinks", variant([], "aay")),
        ("Configuration", variant([], "a(sa{sv})")),
        ("Configuration", variant(None, "s")),
    ],
)
def test_server_disagreement_refuses_before_mount(
    kernel, mount_app, native, key, value
):
    native.props[key] = value
    controller.hdd_mount_async(mount_app, 0)
    assert not native.dialogs and not effects(kernel)


@pytest.mark.parametrize("options", [OPTIONS + ",noexec", "nosuid,nodev,noauto,ro"])
def test_explicit_native_options_use_system_mount_without_popup(
    kernel, mount_app, native, options
):
    native.fields[3] = options
    native.write_entry()
    controller.hdd_mount_async(mount_app, 0)
    assert not native.dialogs and len(effects(kernel)) == 1
    assert "--options" not in effects(kernel)[0]


def test_malformed_server_reply_is_visible_and_has_no_effects(
    kernel, mount_app, native, monkeypatch
):
    runner = native.runner

    def malformed(args, **kwargs):
        return (0, "{") if args[0] == "busctl" else runner(args, **kwargs)

    monkeypatch.setattr(service, "run_hdd_command", malformed)
    controller.hdd_mount_async(mount_app, 0)
    assert not effects(kernel) and not native.dialogs
    assert any("unlocked" in msg for msg in mount_app.logs)


@pytest.mark.parametrize(
    "change",
    [
        "uuid",
        "number",
        "outer-inode",
        "inner-inode",
        "fstab-options",
        "fstab-target",
        "server-uuid",
        "server-config",
        "target-node",
        "child-source",
        "child-number",
    ],
)
def test_changes_between_inspection_and_mount_abort(
    kernel, mount_app, native, monkeypatch, change
):
    def mutate():
        if change == "uuid":
            kernel.node["uuid"] = "replacement"
        elif change == "number":
            kernel.stats[DEVICE] = (stat.S_IFBLK, os.makedev(8, 99))
        elif change in {"outer-inode", "inner-inode"}:
            original = service.os.stat
            path_changed = DEVICE if change == "outer-inode" else MAPPER

            def changed(path, *args, **kwargs):
                info = original(path, *args, **kwargs)
                if str(path) == path_changed:
                    return SimpleNamespace(
                        st_mode=info.st_mode,
                        st_rdev=info.st_rdev,
                        st_dev=info.st_dev,
                        st_ino=info.st_ino + 1,
                    )
                return info

            monkeypatch.setattr(service.os, "stat", changed)
        elif change == "fstab-options":
            native.fields[3] += ",noexec"
            native.write_entry()
        elif change == "fstab-target":
            native.fields[1] = "/mnt/replaced"
            native.write_entry()
        elif change == "server-uuid":
            native.props["IdUUID"] = variant("replacement")
        elif change == "server-config":
            native.props["Configuration"]["data"] = []
        elif change == "target-node":
            native.target_nodes = ((1, 99, stat.S_IFDIR | 0o755, 0),)
        elif change == "child-number":
            kernel.node["children"][0]["maj:min"] = "253:9"
        else:
            kernel.node["children"][0]["uuid"] = "replacement"

    prepare = service.prepare_system_mount
    inspections = 0

    def prepare_then_mutate(current, runner):
        nonlocal inspections
        plan = prepare(current, runner)
        inspections += 1
        if inspections == 1:
            mutate()
        return plan

    monkeypatch.setattr(service, "prepare_system_mount", prepare_then_mutate)
    controller.hdd_mount_async(mount_app, 0)
    assert not effects(kernel)
    assert any("unlocked" in msg for msg in mount_app.logs)


@pytest.mark.parametrize(
    "options",
    [
        "defaults",
        "nosuid,nodev,noauto,exec",
        "nosuid,nodev,noauto,suid",
        "nosuid,nodev,noauto,dev",
        "nosuid,nodev,noauto,user",
        "nosuid,nodev,noauto,bind",
        "nosuid,nodev,noauto,nosuid",
        "nosuid,nodev",
        "nosuid,nodev,noauto,ro,rw",
        "nosuid,nodev,noauto,unknown",
    ],
)
def test_unsupported_options_never_prompt_or_mount(kernel, mount_app, native, options):
    native.fields[3] = options
    native.write_entry()
    controller.hdd_mount_async(mount_app, 0)
    assert not native.dialogs and not effects(kernel)


@pytest.mark.parametrize(
    "field,value",
    [
        (0, MAPPER),
        (1, "/"),
        (1, "/mnt/other"),
        (2, "xfs"),
        (4, "1"),
        (5, "2"),
    ],
)
def test_unsupported_system_entry_refused(kernel, native, field, value):
    native.fields[field] = value
    native.write_entry()
    with pytest.raises(service.MountPolicyError):
        service.prepare_system_mount(identity(native), native.runner)
    assert not effects(kernel)


@pytest.mark.parametrize("duplicate", ["source", "target"])
def test_duplicate_entry_refused(kernel, native, duplicate):
    extra = list(native.fields)
    if duplicate == "target":
        extra[0], extra[2] = "tmpfs", "tmpfs"
    kernel.table.write_text(kernel.table.read_text() + " ".join(extra) + "\n")
    rows = json.loads(kernel.fstab[1])["filesystems"]
    rows.append({"source": extra[0], "fstype": extra[2]})
    kernel.fstab = (0, json.dumps({"filesystems": rows}))
    with pytest.raises(service.MountPolicyError):
        service.prepare_system_mount(identity(native), native.runner)
    assert not effects(kernel)


def test_mount_failure_has_no_fallback_and_explains_open_state(
    kernel, mount_app, native
):
    kernel.mount_rc = 1
    controller.hdd_mount_async(mount_app, 0)
    assert len(effects(kernel)) == 1
    assert any("unlocked" in msg and "mount failed" in msg for msg in mount_app.logs)


def test_post_mount_target_mismatch_is_not_reported_as_success(
    kernel, mount_app, native
):
    native.live_target = "/mnt/foreign"
    controller.hdd_mount_async(mount_app, 0)
    assert len(effects(kernel)) == 1
    assert not any("system-mounted" in msg for msg in mount_app.logs)
    assert any("not confirmed" in msg for msg in mount_app.logs)


def test_native_luks_automount_never_prompts(kernel, mount_app, native):
    controller.hdd_mount_async(mount_app, 0, allow_unlock=False)
    assert not effects(kernel) and not native.dialogs


def test_non_luks_system_device_cannot_get_native_plan(kernel, native):
    kernel.node["fstype"] = "ext4"
    kernel.node.pop("children")
    current = identity(native)
    assert service.prepare_system_mount(current, native.runner) is None
    with pytest.raises(service.MountPolicyError):
        service.mount_device(current, native.runner, system_mount=True)
    assert not effects(kernel)


@pytest.mark.parametrize(
    "failure", [None, "owner", "group-write", "other-write", "symlink", "missing"]
)
def test_target_binding_requires_trusted_existing_directories(monkeypatch, failure):
    opened, closed = [], []

    def open_dir(path, flags, **kwargs):
        assert flags & os.O_PATH and flags & os.O_DIRECTORY and flags & os.O_NOFOLLOW
        assert kwargs == ({"dir_fd": len(opened) + 10} if opened else {})
        if path == INNER and failure in {"symlink", "missing"}:
            raise OSError("synthetic nofollow directory failure")
        opened.append(path)
        return len(opened) + 10

    def metadata(fd):
        return SimpleNamespace(
            st_dev=1,
            st_ino=fd,
            st_uid=1000 if failure == "owner" else 0,
            st_mode=stat.S_IFDIR
            | (
                0o775
                if failure == "group-write"
                else 0o757 if failure == "other-write" else 0o755
            ),
        )

    monkeypatch.setattr(service.os, "open", open_dir)
    monkeypatch.setattr(service.os, "fstat", metadata)
    monkeypatch.setattr(service.os, "close", closed.append)
    if failure:
        with pytest.raises((service.MountPolicyError, OSError)):
            REAL_TARGET_BINDING(TARGET)
    else:
        assert len(REAL_TARGET_BINDING(TARGET)) == 3
        assert opened == ["/", "mnt", INNER]
    assert closed == list(reversed(range(11, 11 + len(opened))))
