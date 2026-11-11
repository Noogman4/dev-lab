"""Only synthetic swaps, filesystems and mount commands; no host mutations."""

import json
import os
import stat
from types import SimpleNamespace

import pytest

from netmon.services import hdd_mount_service as service
from tests.test_hdd_mount_security import DEVICE, UUID, privileged_calls
from tests.test_hdd_mount_security import kernel as kernel


@pytest.fixture
def swap(kernel, monkeypatch, tmp_path):
    path = "/swapfile"
    kernel.table.write_text(f"{path} none swap sw 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": path, "fstype": "swap"}]}),
    )
    table = tmp_path / "proc-swaps"
    table.write_text("Filename Type Size Used Priority\n/swapfile file 4092 0 -2\n")
    monkeypatch.setattr(service, "_PROC_SWAPS", str(table), raising=False)
    info = SimpleNamespace(
        st_dev=os.makedev(8, 1),
        st_ino=123,
        st_mode=stat.S_IFREG | 0o600,
        st_uid=0,
        st_nlink=1,
        st_size=4194304,
        st_mtime_ns=1,
        st_ctime_ns=1,
    )
    monkeypatch.setattr(service, "_trusted_swap_file", lambda _p: info, raising=False)
    real_stat = service.os.stat
    monkeypatch.setattr(
        service.os,
        "stat",
        lambda p, *a, **kw: info if p == path else real_stat(p, *a, **kw),
    )
    return SimpleNamespace(info=info, table=table, path=path)


def mount(kernel):
    return service.mount_device(
        service.inspect_device(DEVICE, UUID, kernel.runner), kernel.runner
    )


def test_active_protected_swap_on_other_filesystem_allows_safe_mount(kernel, swap):
    assert mount(kernel)[0] == 0
    assert privileged_calls(kernel) == [
        [
            "udisksctl",
            "mount",
            "--block-device",
            DEVICE,
            "--options",
            "nodev,nosuid,noexec",
        ]
    ]


@pytest.mark.parametrize(
    "change",
    [
        "inactive",
        "partition",
        "duplicate",
        "malformed",
        "oversized",
        "unknown-backing",
        "same-backing",
        "cloned-backing",
        "inconsistent-parser",
        "bad-target",
        "bad-pass",
        "bad-option",
        "duplicate-option",
        "missing-backing-uuid",
        "swap-size",
        "duplicate-fstab",
    ],
)
def test_unsafe_or_unconfirmed_swap_refuses_without_effect(kernel, swap, change):
    if change == "inactive":
        swap.table.write_text("Filename Type Size Used Priority\n")
    elif change == "partition":
        swap.table.write_text(
            "Filename Type Size Used Priority\n/swapfile partition 4092 0 -2\n"
        )
    elif change == "duplicate":
        with swap.table.open("a") as stream:
            stream.write("/swapfile file 4092 0 -2\n")
    elif change == "malformed":
        swap.table.write_text("untrusted\n")
    elif change == "oversized":
        swap.table.write_bytes(b"x" * (1024 * 1024 + 1))
    elif change == "unknown-backing":
        swap.info.st_dev = os.makedev(0, 99)
    elif change == "same-backing":
        swap.info.st_dev = os.makedev(8, 17)
    elif change == "cloned-backing":
        kernel.roots[1]["uuid"] = UUID
    elif change == "inconsistent-parser":
        kernel.table.write_text("/different none swap sw 0 0\n")
    elif change == "bad-target":
        kernel.table.write_text("/swapfile /mnt/other swap sw 0 0\n")
    elif change == "bad-pass":
        kernel.table.write_text("/swapfile none swap sw 0 1\n")
    elif change == "bad-option":
        kernel.table.write_text("/swapfile none swap bind 0 0\n")
    elif change == "duplicate-option":
        kernel.table.write_text("/swapfile none swap sw,pri=1,pri=2 0 0\n")
    elif change == "missing-backing-uuid":
        kernel.roots[1]["uuid"] = None
    elif change == "swap-size":
        swap.info.st_size = 4096
    elif change == "duplicate-fstab":
        kernel.table.write_text("/swapfile none swap sw 0 0\n" * 2)
        kernel.fstab = (
            0,
            json.dumps(
                {"filesystems": [{"source": "/swapfile", "fstype": "swap"}] * 2}
            ),
        )
    with pytest.raises(service.MountPolicyError):
        mount(kernel)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize("change", ["file", "activation", "device"])
def test_swap_or_device_change_during_check_refuses(kernel, swap, monkeypatch, change):
    original = service._trusted_swap_file
    calls = []

    def changing(path):
        calls.append(path)
        if len(calls) == 2:
            if change == "file":
                swap.info.st_ino += 1
            elif change == "activation":
                swap.table.write_text("Filename Type Size Used Priority\n")
            else:
                kernel.node["uuid"] = "replacement"
        return original(path)

    monkeypatch.setattr(service, "_trusted_swap_file", changing)
    with pytest.raises(service.MountPolicyError):
        mount(kernel)
    assert not privileged_calls(kernel)


def test_swap_usage_counter_changes_do_not_invalidate_identity(
    kernel, swap, monkeypatch
):
    original = service._trusted_swap_file

    def used(path):
        swap.table.write_text(
            "Filename Type Size Used Priority\n/swapfile file 4092 10 -2\n"
        )
        return original(path)

    monkeypatch.setattr(service, "_trusted_swap_file", used)
    assert mount(kernel)[0] == 0


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "owner",
        "writable",
        "readable",
        "hardlink",
        "symlink",
        "directory",
        "ancestor-owner",
        "ancestor-writable",
    ],
)
def test_swap_path_walk_checks_every_component_without_reading_contents(
    monkeypatch, fault
):
    opened, closed = [], []
    infos = [
        SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0),
        SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0),
        SimpleNamespace(
            st_mode=stat.S_IFREG | 0o600, st_uid=0, st_nlink=1, st_size=4096
        ),
    ]
    if fault == "owner":
        infos[2].st_uid = 1000
    if fault == "writable":
        infos[2].st_mode |= 0o020
    if fault == "readable":
        infos[2].st_mode |= 0o004
    if fault == "hardlink":
        infos[2].st_nlink = 2
    if fault == "symlink":
        infos[2].st_mode = stat.S_IFLNK | 0o777
    if fault == "directory":
        infos[2].st_mode = stat.S_IFDIR | 0o700
    if fault == "ancestor-owner":
        infos[1].st_uid = 1000
    if fault == "ancestor-writable":
        infos[1].st_mode |= 0o002

    def open_path(path, flags, **kwargs):
        assert flags & os.O_PATH and flags & os.O_NOFOLLOW
        if opened:
            assert kwargs["dir_fd"] == len(opened) - 1
        opened.append(path)
        return len(opened) - 1

    monkeypatch.setattr(service.os, "open", open_path)
    monkeypatch.setattr(service.os, "fstat", lambda fd: infos[fd])
    monkeypatch.setattr(service.os, "close", closed.append)
    if fault:
        with pytest.raises(service.MountPolicyError):
            service._trusted_swap_file("/swap/swapfile")
    else:
        assert service._trusted_swap_file("/swap/swapfile") is infos[2]
    assert set(closed) == set(range(len(opened)))


@pytest.mark.parametrize(
    "path",
    [
        "relative",
        "/a/../swapfile",
        "/a//swapfile",
        "/a/./swapfile",
        "/swapfile\n",
        "/dev/swapfile",
    ],
)
def test_noncanonical_or_device_namespace_swap_path_refuses(path):
    with pytest.raises(service.MountPolicyError):
        service._trusted_swap_file(path)
