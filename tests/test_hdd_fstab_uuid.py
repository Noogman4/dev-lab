"""Synthetic device nodes, alias metadata and typed UDisks replies only."""

import json
import os
import stat
from types import SimpleNamespace

import pytest

from netmon.services import hdd_mount_service as service
from tests.test_hdd_mount_security import DEVICE, UUID
from tests.test_hdd_mount_security import kernel as kernel
from tests.test_hdd_mount_security import mount_app as mount_app

ABSENT_UUID = "8f6bf0dc-a7cb-41b7-a8be-293a345da986"
ABSENT = "/dev/disk/by-uuid/" + ABSENT_UUID
OBJECT = "/org/freedesktop/UDisks2/block_devices/synthetic"


def byte_string(value):
    return list(value.encode()) + [0]


@pytest.fixture
def absent(kernel, monkeypatch):
    kernel.table.write_text(
        f"{ABSENT} /mnt/absent auto nosuid,nodev,nofail,noauto 0 0\n"
    )
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": ABSENT, "fstype": "auto"}]}),
    )
    state = SimpleNamespace(
        calls=[],
        paths=[OBJECT],
        result=0,
        raw=None,
        on_read=None,
        dirs=((1, 2, 0o40755, 0),),
        props={
            "Device": {"type": "ay", "data": byte_string(DEVICE)},
            "DeviceNumber": {"type": "t", "data": os.makedev(8, 17)},
            "IdUUID": {"type": "s", "data": UUID},
            "IdType": {"type": "s", "data": "ext4"},
            "IdUsage": {"type": "s", "data": "filesystem"},
            "Symlinks": {
                "type": "aay",
                "data": [byte_string("/dev/disk/by-uuid/" + UUID)],
            },
            "Configuration": {"type": "a(sa{sv})", "data": []},
        },
    )

    def missing(path):
        assert path == ABSENT
        return state.dirs

    monkeypatch.setattr(service, "_missing_uuid_alias", missing, raising=False)

    def runner(args, **kwargs):
        if args[0] != "busctl":
            return kernel.runner(args, **kwargs)
        state.calls.append(args)
        if state.on_read:
            state.on_read(args)
        if state.raw is not None:
            return state.result, state.raw
        if "ResolveDevice" in args:
            return state.result, json.dumps({"type": "ao", "data": [state.paths]})
        assert "GetAll" in args and args[-1] == "org.freedesktop.UDisks2.Block"
        return state.result, json.dumps({"type": "a{sv}", "data": [state.props]})

    state.runner = runner
    return state


def mount(kernel, absent):
    return service.mount_device(
        service.inspect_device(DEVICE, UUID, absent.runner), absent.runner
    )


def effects(kernel):
    return [args for args in kernel.calls if args[0] not in {"findmnt", "lsblk"}]


def test_missing_foreign_uuid_with_server_proof_allows_only_safe_mount(kernel, absent):
    assert mount(kernel, absent)[0] == 0
    assert effects(kernel) == [
        [
            "udisksctl",
            "mount",
            "--block-device",
            DEVICE,
            "--options",
            "nodev,nosuid,noexec",
        ]
    ]
    assert len(absent.calls) == 4  # ResolveDevice + GetAll, checked twice.


def test_actual_controller_keeps_frozen_binding_and_feedback(
    kernel, absent, mount_app, monkeypatch
):
    from netmon.features import hdd_controller as controller

    monkeypatch.setattr(service, "run_hdd_command", absent.runner)
    controller.hdd_mount_async(mount_app, 0)
    assert effects(kernel)[0] == [
        "udisksctl",
        "mount",
        "--block-device",
        DEVICE,
        "--options",
        "nodev,nosuid,noexec",
    ]
    assert any("desktop-integriert" in line for line in mount_app.logs)


def test_uuid_case_difference_is_not_accepted_as_independence(kernel, absent):
    kernel.node["uuid"] = ABSENT_UUID.upper()
    identity = service.inspect_device(DEVICE, ABSENT_UUID.upper(), absent.runner)
    with pytest.raises(service.MountPolicyError):
        service.mount_device(identity, absent.runner)
    assert not effects(kernel) and not absent.calls


@pytest.mark.parametrize(
    "tail",
    [
        [
            OBJECT,
            "org.freedesktop.DBus.Properties",
            "Set",
            "ssv",
            service._UDISKS_BLOCK,
            "HintIgnore",
            "b",
            "true",
        ],
        [
            service._UDISKS_MANAGER,
            service._UDISKS + ".Manager",
            "LoopSetup",
            "ha{sv}",
            "0",
            "0",
        ],
        [OBJECT, "org.freedesktop.UDisks2.Filesystem", "Mount", "a{sv}", "0"],
        [OBJECT, "org.freedesktop.UDisks2.Filesystem", "Unmount", "a{sv}", "0"],
        [OBJECT, "org.freedesktop.DBus.Properties", "GetAll", "s", "other.service"],
    ],
)
def test_bus_tool_rejects_every_non_readonly_method(monkeypatch, tail):
    monkeypatch.setattr(
        service.subprocess,
        "run",
        lambda *a, **k: pytest.fail("forbidden method reached subprocess"),
    )
    with pytest.raises(service.MountPolicyError):
        service.run_hdd_command(service._BUS_PREFIX + tail)


def test_bus_reads_use_fixed_path_clean_environment_and_disable_activation(monkeypatch):
    calls = []
    monkeypatch.setenv("DBUS_SYSTEM_BUS_ADDRESS", "unix:path=/untrusted")

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="synthetic reply")

    monkeypatch.setattr(service.subprocess, "run", run)
    args = service._BUS_PREFIX + [
        OBJECT,
        "org.freedesktop.DBus.Properties",
        "GetAll",
        "s",
        service._UDISKS_BLOCK,
    ]
    assert service.run_hdd_command(args) == (0, "synthetic reply")
    assert calls[0][0][0] == "/usr/bin/busctl" and "--auto-start=no" in calls[0][0]
    assert calls[0][1]["env"] == {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
    }
    assert calls[0][1]["shell"] is False
    assert "--allow-interactive-authorization=no" in calls[0][0]


@pytest.mark.parametrize(
    "problem",
    [
        "server-alias",
        "uuid",
        "number",
        "device",
        "fstype",
        "usage",
        "configuration",
        "duplicate-object",
        "no-object",
        "bad-object",
        "missing-property",
        "wrong-type",
        "bad-bytes",
        "nul-bytes",
        "wrong-shape",
        "json",
        "duplicate-json",
        "failure",
        "timeout",
        "oversized",
        "live-foreign-uuid",
        "parser-disagreement",
    ],
)
def test_unknown_or_conflicting_uuid_proof_refuses(kernel, absent, problem):
    props = absent.props
    if problem == "server-alias":
        props["Symlinks"]["data"].append(byte_string(ABSENT))
    elif problem == "uuid":
        props["IdUUID"]["data"] = "replacement"
    elif problem == "number":
        props["DeviceNumber"]["data"] += 1
    elif problem == "device":
        props["Device"]["data"] = byte_string("/dev/foreign")
    elif problem == "fstype":
        props["IdType"]["data"] = "xfs"
    elif problem == "usage":
        props["IdUsage"]["data"] = "other"
    elif problem == "configuration":
        props["Configuration"]["data"] = [["fstab", {}]]
    elif problem == "duplicate-object":
        absent.paths *= 2
    elif problem == "no-object":
        absent.paths = []
    elif problem == "bad-object":
        absent.paths = ["/other/service"]
    elif problem == "missing-property":
        del props["Symlinks"]
    elif problem == "wrong-type":
        props["DeviceNumber"]["type"] = "s"
    elif problem == "bad-bytes":
        props["Symlinks"]["data"] = [[999, 0]]
    elif problem == "nul-bytes":
        props["Symlinks"]["data"] = [[47, 0, 47, 0]]
    elif problem == "wrong-shape":
        absent.raw = '{"type":"ao","data":[]}'
    elif problem == "json":
        absent.raw = "not json"
    elif problem == "duplicate-json":
        absent.raw = '{"type":"ao","data":[[]],"data":[["' + OBJECT + '"]]}'
    elif problem == "failure":
        absent.result = 1
    elif problem == "timeout":
        absent.result = 124
    elif problem == "oversized":
        absent.raw = "x" * (1024 * 1024 + 1)
    elif problem == "live-foreign-uuid":
        kernel.roots[1]["uuid"] = ABSENT_UUID
    elif problem == "parser-disagreement":
        kernel.table.write_text("/dev/other /mnt/absent auto defaults 0 0\n")
    with pytest.raises(service.MountPolicyError):
        mount(kernel, absent)
    assert not effects(kernel)


@pytest.mark.parametrize(
    "change",
    ["alias", "server-uuid", "object", "directory", "inventory", "fstab", "source"],
)
def test_uuid_proof_changes_between_checks_refuse(kernel, absent, change):
    def changed(args):
        if len(absent.calls) == 3:
            if change == "alias":
                absent.props["Symlinks"]["data"].append(byte_string(ABSENT))
            elif change == "server-uuid":
                absent.props["IdUUID"]["data"] = "replacement"
            elif change == "object":
                absent.paths = [OBJECT + "2"]
            elif change == "directory":
                absent.dirs = ((1, 99, 0o40755, 0),)
            elif change == "inventory":
                kernel.roots[1]["uuid"] = ABSENT_UUID
            elif change == "fstab":
                kernel.table.write_text(kernel.table.read_text() + "# changed\n")
            elif change == "source":
                kernel.node["uuid"] = "replacement"

    absent.on_read = changed
    with pytest.raises(service.MountPolicyError):
        mount(kernel, absent)
    assert not effects(kernel)


def test_existing_uuid_alias_to_selected_device_still_refuses(
    kernel, absent, monkeypatch
):
    # Existing aliases must follow the old complete block-identity checks.
    kernel.stats[ABSENT] = (stat.S_IFBLK, os.makedev(8, 17))
    realpath = service.os.path.realpath
    monkeypatch.setattr(
        service.os.path, "realpath", lambda p: DEVICE if p == ABSENT else realpath(p)
    )
    with pytest.raises(service.MountPolicyError):
        mount(kernel, absent)
    assert not effects(kernel) and not absent.calls


@pytest.mark.parametrize(
    "path",
    [
        "/dev/missing-source",
        "/dev/disk/by-uuid/bad",
        "/dev/disk/by-uuid/../bad",
        "UUID=" + ABSENT_UUID,
    ],
)
def test_other_unresolved_sources_keep_fail_closed(kernel, absent, path):
    kernel.table.write_text(f"{path} /mnt/absent auto defaults 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": path, "fstype": "auto"}]}),
    )
    with pytest.raises(service.MountPolicyError):
        mount(kernel, absent)
    assert not effects(kernel) and not absent.calls


@pytest.mark.parametrize(
    "fault", [None, "owner", "writable", "symlink", "present", "denied"]
)
def test_missing_alias_requires_trusted_pinned_parents_and_absent_leaf(
    monkeypatch, fault
):
    opened = []
    closed = []

    def open_dir(path, flags, **kwargs):
        assert flags & os.O_PATH and flags & os.O_NOFOLLOW and flags & os.O_DIRECTORY
        if opened:
            assert kwargs["dir_fd"] == len(opened) - 1
        opened.append(path)
        return len(opened) - 1

    def info(fd):
        mode = stat.S_IFDIR | 0o755
        if fd == 2 and fault == "writable":
            mode |= 0o002
        if fd == 2 and fault == "symlink":
            mode = stat.S_IFLNK | 0o777
        return SimpleNamespace(
            st_dev=1,
            st_ino=fd + 1,
            st_mode=mode,
            st_uid=1000 if fd == 2 and fault == "owner" else 0,
        )

    def leaf(path, **kwargs):
        assert path == ABSENT_UUID and kwargs == {"dir_fd": 3, "follow_symlinks": False}
        if fault == "denied":
            raise PermissionError("denied")
        if fault == "present":
            return SimpleNamespace(st_mode=stat.S_IFLNK)
        raise FileNotFoundError("absent")

    monkeypatch.setattr(service.os, "open", open_dir)
    monkeypatch.setattr(service.os, "fstat", info)
    monkeypatch.setattr(service.os, "stat", leaf)
    monkeypatch.setattr(service.os, "close", closed.append)
    if fault:
        with pytest.raises((service.MountPolicyError, OSError)):
            service._missing_uuid_alias(ABSENT)
    else:
        assert len(service._missing_uuid_alias(ABSENT)) == 4
    assert set(closed) == set(range(len(opened)))
