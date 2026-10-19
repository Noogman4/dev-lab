"""Synthetic kernel inventory and command fakes only: never mount a real device."""

import copy
import json
import os
import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon.features import hdd_controller as controller
from netmon.services import hdd_mount_service as service

DEVICE = "/dev/netmon_test_disk"
MAPPER = "/dev/netmon_test_clear"
UUID = "synthetic-uuid"
FSTAB_DEVICE = "/dev/netmon_system_disk"
REAL_HDD_RUNNER = service.run_hdd_command


@pytest.fixture
def kernel(monkeypatch, tmp_path):
    node = {
        "name": DEVICE,
        "path": DEVICE,
        "type": "part",
        "fstype": "ext4",
        "uuid": UUID,
        "maj:min": "8:17",
    }
    state = SimpleNamespace(
        roots=[
            node,
            {
                "path": FSTAB_DEVICE,
                "type": "part",
                "fstype": "ext4",
                "uuid": "system-uuid",
                "maj:min": "8:1",
            },
        ],
        calls=[],
        inventory_rc=0,
        raw=None,
        fstab=(
            0,
            json.dumps({"filesystems": [{"source": FSTAB_DEVICE, "fstype": "ext4"}]}),
        ),
        mount_rc=0,
        unlock_rc=0,
        on_command=None,
        stats={
            DEVICE: (stat.S_IFBLK, os.makedev(8, 17)),
            MAPPER: (stat.S_IFBLK, os.makedev(253, 0)),
            FSTAB_DEVICE: (stat.S_IFBLK, os.makedev(8, 1)),
        },
        key=None,
        fstab_owner=0,
    )
    # Synthetic table only; root ownership is simulated, never changed on disk.
    table = tmp_path / "system-fstab"
    table.write_text(f"{FSTAB_DEVICE} /mnt/other ext4 defaults 0 0\n")
    table.chmod(0o600)
    state.table = table
    monkeypatch.setattr(service, "_SYSTEM_FSTAB", str(table))
    original_stat = os.stat
    original_fstat = os.fstat
    table_number = (original_stat(table).st_dev, original_stat(table).st_ino)

    def trusted_table_stat(info):
        if (info.st_dev, info.st_ino) != table_number:
            return info
        fields = (
            "st_dev",
            "st_ino",
            "st_mode",
            "st_uid",
            "st_size",
            "st_mtime_ns",
            "st_ctime_ns",
        )
        result = SimpleNamespace(**{name: getattr(info, name) for name in fields})
        result.st_uid = state.fstab_owner
        return result

    def fake_fstat(fd):
        return trusted_table_stat(original_fstat(fd))

    def fake_stat(path, *args, **kwargs):
        key = str(path)
        if kwargs.get("follow_symlinks", True) and os.path.islink(path):
            key = os.path.realpath(path)
        if key in state.stats:
            mode, number = state.stats[key]
            return SimpleNamespace(st_mode=mode, st_rdev=number)
        return trusted_table_stat(original_stat(path, *args, **kwargs))

    def runner(args, timeout=0):
        state.calls.append(args)
        if state.on_command:
            state.on_command(args)
        if args[0] == "lsblk":
            return state.inventory_rc, (
                state.raw
                if state.raw is not None
                else json.dumps({"blockdevices": state.roots})
            )
        if args[0] == "findmnt":
            return state.fstab
        assert args[:2] in (["udisksctl", "mount"], ["udisksctl", "unlock"])
        assert "--block-device" in args
        if args[1] == "unlock":
            key = Path(args[args.index("--key-file") + 1])
            state.key = key
            assert stat.S_IMODE(original_stat(key).st_mode) == 0o600
            assert key.read_text() == "test-passphrase"
            if state.unlock_rc == 0:
                node["children"] = [
                    {
                        "name": MAPPER,
                        "path": MAPPER,
                        "type": "crypt",
                        "fstype": "ext4",
                        "uuid": "clear-uuid",
                        "maj:min": "253:0",
                    }
                ]
            return state.unlock_rc, "synthetic unlock result"
        return state.mount_rc, "synthetic mount result"

    monkeypatch.setattr(service.os, "stat", fake_stat)
    monkeypatch.setattr(service.os, "fstat", fake_fstat)
    state.runner = runner
    state.node = node
    return state


def privileged_calls(kernel):
    return [args for args in kernel.calls if args[0] not in {"lsblk", "findmnt"}]


def make_app(kernel):
    slot = {
        "slot": 1,
        "device": DEVICE,
        "device_uuid": UUID,
        "mountpoint": "/mnt/ignored-config",
        "custom_name": "Synthetic",
    }
    disk = {"device": DEVICE, "uuid": UUID}
    app = SimpleNamespace(
        hdd_slots=[slot],
        detected_disks=[disk],
        detected_disks_by_device={DEVICE: disk},
        logs=[],
        refreshed=[],
    )
    app.log = app.logs.append
    app.tr = lambda _key, fallback: fallback
    app.after = lambda _delay, fn: fn()
    app.hdd_refresh_async = lambda: app.refreshed.append(True)
    app.hdd_info_async = lambda *_a, **_kw: None
    app.ensure_sudo_session = lambda *_a: pytest.fail("Must not acquire sudo session")
    return app


@pytest.fixture
def mount_app(kernel, monkeypatch):
    app = make_app(kernel)
    # App's legacy forwarding mutates this display helper; restore it on teardown.
    monkeypatch.setattr(controller, "run_cmd", kernel.runner)
    monkeypatch.setattr(service, "run_hdd_command", kernel.runner)
    monkeypatch.setattr(controller, "has_cmd", lambda _name: True)

    class ImmediateThread:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(controller.threading, "Thread", ImmediateThread)
    return app


def test_regular_filesystem_mount_uses_only_udisks_and_fixed_options(kernel, mount_app):
    controller.hdd_mount_async(mount_app, 0)
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
    assert mount_app.refreshed == [True]
    assert any("desktop-integriert" in msg for msg in mount_app.logs)


@pytest.mark.parametrize("missing", ["udisksctl", "lsblk", "findmnt"])
def test_missing_required_tool_has_no_fallback(kernel, mount_app, monkeypatch, missing):
    monkeypatch.setattr(controller, "has_cmd", lambda name: name != missing)
    controller.hdd_mount_async(mount_app, 0)
    assert not kernel.calls
    assert any("required" in msg for msg in mount_app.logs)


def test_unrecognised_regular_image_from_json_rejected_before_privilege(
    tmp_path, kernel, mount_app
):
    image = tmp_path / "crafted.img"
    image.write_bytes(b"synthetic filesystem image")
    config = tmp_path / "slots.json"
    config.write_text(
        json.dumps([{"slot": 1, "device": str(image), "device_uuid": UUID}])
    )
    mount_app.hdd_config_path = str(config)
    mount_app.hdd_slots = controller.load_hdd_slots_config(mount_app)
    controller.hdd_mount_async(mount_app, 0)
    assert not kernel.calls
    mount_app.hdd_slots[0]["device_uuid"] = "attacker-image-uuid"
    kernel.calls.clear()
    controller.hdd_mount_async(mount_app, 0)
    assert not kernel.calls


@pytest.mark.parametrize("change", ["uuid", "regular", "character", "number", "loop"])
def test_invalid_live_device_never_reaches_mount(kernel, mount_app, change):
    before = copy.deepcopy(mount_app.hdd_slots)
    if change == "uuid":
        kernel.node["uuid"] = "replacement"
    elif change == "loop":
        kernel.node["type"] = "loop"
    elif change == "number":
        kernel.node["maj:min"] = "8:99"
    else:
        kernel.stats[DEVICE] = (
            stat.S_IFREG if change == "regular" else stat.S_IFCHR,
            os.makedev(8, 17),
        )
    controller.hdd_mount_async(mount_app, 0)
    assert not privileged_calls(kernel)
    assert mount_app.hdd_slots == before


def test_cached_uuid_mismatch_stops_without_rewriting_slot(kernel, mount_app):
    mount_app.detected_disks_by_device[DEVICE]["uuid"] = "different-disk"
    before = copy.deepcopy(mount_app.hdd_slots)
    controller.hdd_mount_async(mount_app, 0)
    assert not kernel.calls
    assert mount_app.hdd_slots == before


def test_missing_saved_uuid_requires_explicit_reassignment(kernel, mount_app):
    mount_app.hdd_slots[0]["device_uuid"] = ""
    controller.hdd_mount_async(mount_app, 0)
    assert not kernel.calls
    assert mount_app.hdd_slots[0]["device_uuid"] == ""


def test_path_renumbering_resolves_uuid_without_mutating_slot(kernel, mount_app):
    mount_app.hdd_slots[0]["device"] = "/dev/old_name"
    controller.hdd_mount_async(mount_app, 0)
    assert privileged_calls(kernel)[0][3] == DEVICE
    assert mount_app.hdd_slots[0]["device"] == "/dev/old_name"


@pytest.mark.parametrize(
    "raw", ["{", "{}", '{"blockdevices":null}', '{"blockdevices":[null]}']
)
def test_malformed_inventory_fails_closed(kernel, raw):
    kernel.raw = raw
    with pytest.raises(service.MountPolicyError):
        service.inspect_device(DEVICE, UUID, kernel.runner)
    assert not privileged_calls(kernel)


def test_inventory_command_failure_stops(kernel):
    kernel.inventory_rc = 1
    with pytest.raises(service.MountPolicyError):
        service.inspect_device(DEVICE, UUID, kernel.runner)


def test_uuid_clone_is_rejected(kernel):
    other = dict(kernel.node, path="/dev/another_disk")
    kernel.roots.append(other)
    with pytest.raises(service.MountPolicyError, match="ambiguous"):
        service.inspect_device(DEVICE, UUID, kernel.runner)


def test_partition_under_loop_is_rejected(kernel):
    kernel.roots = [{"path": "/dev/loop0", "type": "loop", "children": [kernel.node]}]
    with pytest.raises(service.MountPolicyError, match="ancestry"):
        service.inspect_device(DEVICE, UUID, kernel.runner)


@pytest.mark.parametrize("fstab", [(0, '{"filesystems":[]}'), (2, "error"), (1, "bad")])
def test_fstab_or_unverifiable_mount_policy_stops(kernel, fstab):
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    kernel.fstab = fstab
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize("change", ["uuid", "number", "source"])
def test_substitution_after_fstab_check_aborts(kernel, change):
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)

    def mutate(args):
        if args[0] == "findmnt":
            if change == "source":
                kernel.node["fstype"] = "crypto_LUKS"
            elif change == "number":
                kernel.stats[DEVICE] = (stat.S_IFBLK, os.makedev(8, 99))
                kernel.node["maj:min"] = "8:99"
            else:
                kernel.node["uuid"] = "changed"

    kernel.on_command = mutate
    with pytest.raises(service.MountPolicyError):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


def test_udisks_failure_does_not_fall_back_to_root_mount(kernel, mount_app):
    kernel.mount_rc = 1
    controller.hdd_mount_async(mount_app, 0)
    assert len(privileged_calls(kernel)) == 1
    assert any("mount failed" in msg for msg in mount_app.logs)


def test_luks_unlock_then_mount_bound_child(kernel, mount_app, monkeypatch):
    kernel.node["fstype"] = "crypto_LUKS"
    monkeypatch.setattr(
        controller.simpledialog, "askstring", lambda *_a, **_k: "test-passphrase"
    )
    controller.hdd_mount_async(mount_app, 0)
    commands = privileged_calls(kernel)
    assert commands[0][:4] == ["udisksctl", "unlock", "--block-device", DEVICE]
    assert commands[1] == [
        "udisksctl",
        "mount",
        "--block-device",
        MAPPER,
        "--options",
        "nodev,nosuid,noexec",
    ]
    assert not kernel.key.exists()
    assert all("test-passphrase" not in args for args in kernel.calls)


def test_luks_unlock_failure_cleans_key_and_never_mounts(
    kernel, mount_app, monkeypatch
):
    kernel.node["fstype"] = "crypto_LUKS"
    kernel.unlock_rc = 1
    monkeypatch.setattr(
        controller.simpledialog, "askstring", lambda *_a, **_k: "test-passphrase"
    )
    controller.hdd_mount_async(mount_app, 0)
    assert [args[1] for args in privileged_calls(kernel)] == ["unlock"]
    assert not kernel.key.exists()


def test_luks_dialog_device_substitution_rejected_before_unlock(
    kernel, mount_app, monkeypatch
):
    kernel.node["fstype"] = "crypto_LUKS"

    def replace_device(*_a, **_kw):
        kernel.node["uuid"] = "replacement-after-dialog"
        return "test-passphrase"

    monkeypatch.setattr(controller.simpledialog, "askstring", replace_device)
    controller.hdd_mount_async(mount_app, 0)
    assert not privileged_calls(kernel)


def test_luks_cancel_has_no_privileged_operations(kernel, mount_app, monkeypatch):
    kernel.node["fstype"] = "crypto_LUKS"
    monkeypatch.setattr(controller.simpledialog, "askstring", lambda *_a, **_k: None)
    controller.hdd_mount_async(mount_app, 0)
    assert not privileged_calls(kernel)


def test_unrelated_cached_mapper_cannot_be_mounted(kernel, mount_app):
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
    mount_app._hdd_find_mount_source = lambda _d: "/dev/unrelated"
    mount_app._hdd_luks_info_for_device = lambda _d: {"mapper_path": "/dev/unrelated"}
    controller.hdd_mount_async(mount_app, 0)
    assert privileged_calls(kernel)[0][3] == MAPPER


def test_actual_app_entrypoint_uses_policy(kernel, mount_app, monkeypatch):
    from tools import netmon

    monkeypatch.setattr(netmon, "run_cmd", kernel.runner)
    monkeypatch.setattr(netmon, "has_cmd", lambda _name: True)
    netmon.App.hdd_mount_async(mount_app, 0)
    assert privileged_calls(kernel)[0] == [
        "udisksctl",
        "mount",
        "--block-device",
        DEVICE,
        "--options",
        "nodev,nosuid,noexec",
    ]


def test_existing_undetected_path_is_not_rebound_to_another_device(
    kernel, mount_app, monkeypatch
):
    mount_app.hdd_slots[0]["device"] = "/dev/shm/synthetic.img"
    exists = os.path.exists
    monkeypatch.setattr(
        controller.os.path,
        "exists",
        lambda path: True if path == "/dev/shm/synthetic.img" else exists(path),
    )
    controller.hdd_mount_async(mount_app, 0)
    assert not kernel.calls


def test_symlink_resolving_outside_dev_is_rejected(kernel, monkeypatch):
    realpath = os.path.realpath
    monkeypatch.setattr(
        service.os.path,
        "realpath",
        lambda path: "/tmp/image" if path == DEVICE else realpath(path),
    )
    with pytest.raises(service.MountPolicyError, match="below /dev"):
        service.inspect_device(DEVICE, UUID, kernel.runner)
    assert not privileged_calls(kernel)


def test_unrelated_mapper_is_not_a_mount_candidate(kernel):
    kernel.node["fstype"] = "crypto_LUKS"
    kernel.roots.append(
        {
            "path": MAPPER,
            "type": "crypt",
            "fstype": "ext4",
            "uuid": "foreign",
            "maj:min": "253:0",
        }
    )
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    assert identity.source is None
    with pytest.raises(service.MountPolicyError, match="No unambiguous"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


def test_missing_filesystem_uuid_rejected_even_with_valid_luks_identity(kernel):
    kernel.node["fstype"] = "crypto_LUKS"
    kernel.node["children"] = [
        {
            "path": MAPPER,
            "type": "crypt",
            "fstype": "ext4",
            "uuid": "",
            "maj:min": "253:0",
        }
    ]
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    with pytest.raises(service.MountPolicyError, match="No unambiguous"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


def test_duplicate_cleartext_uuid_is_rejected(kernel):
    kernel.node["fstype"] = "crypto_LUKS"
    kernel.node["children"] = [
        {
            "path": MAPPER,
            "type": "crypt",
            "fstype": "ext4",
            "uuid": "cloned",
            "maj:min": "253:0",
        }
    ]
    kernel.roots.append({"path": "/dev/other", "uuid": "cloned"})
    with pytest.raises(service.MountPolicyError, match="Ambiguous filesystem"):
        service.inspect_device(DEVICE, UUID, kernel.runner)


def test_multiple_filesystems_require_partition_selection(kernel):
    kernel.node["fstype"] = ""
    partition = "/dev/netmon_test_partition"
    kernel.stats[partition] = (stat.S_IFBLK, os.makedev(8, 18))
    kernel.node["children"] = [
        {
            "path": partition,
            "type": "part",
            "fstype": "ext4",
            "uuid": "partition-uuid",
            "maj:min": "8:18",
        },
        {
            "path": MAPPER,
            "type": "part",
            "fstype": "ext4",
            "uuid": "second",
            "maj:min": "253:0",
        },
    ]
    with pytest.raises(service.MountPolicyError, match="Multiple filesystems"):
        service.inspect_device(DEVICE, UUID, kernel.runner)


def test_snapshot_is_rechecked_after_worker_delay(kernel, mount_app, monkeypatch):
    jobs = []

    class DelayedThread:
        def __init__(self, target, **_kwargs):
            jobs.append(target)

        def start(self):
            pass

    monkeypatch.setattr(controller.threading, "Thread", DelayedThread)
    controller.hdd_mount_async(mount_app, 0)
    kernel.node["uuid"] = "changed-after-worker-scheduled"
    jobs.pop()()
    assert not privileged_calls(kernel)


def test_slot_edit_after_scheduling_does_not_change_frozen_mount(
    kernel, mount_app, monkeypatch
):
    jobs = []

    class DelayedThread:
        def __init__(self, target, **_kwargs):
            jobs.append(target)

        def start(self):
            pass

    monkeypatch.setattr(controller.threading, "Thread", DelayedThread)
    controller.hdd_mount_async(mount_app, 0)
    mount_app.hdd_slots[0].update(device="/tmp/evil.img", device_uuid="replacement")
    jobs.pop()()
    assert privileged_calls(kernel)[0][3] == DEVICE


def test_unlock_oserror_cleans_temporary_keyfile(kernel):
    kernel.node["fstype"] = "crypto_LUKS"
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    keys = []

    def failing_runner(args, **kwargs):
        if args[:2] == ["udisksctl", "unlock"]:
            keys.append(Path(args[-1]))
            raise OSError("synthetic process failure")
        return kernel.runner(args, **kwargs)

    with pytest.raises(OSError):
        service.unlock_device(identity, "test-passphrase", failing_runner)
    assert len(keys) == 1 and not keys[0].exists()


def test_unlock_waits_for_verified_cleartext_device(kernel, monkeypatch):
    kernel.node["fstype"] = "crypto_LUKS"
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    original_runner = kernel.runner
    pending = []

    def delayed_runner(args, **kwargs):
        result = original_runner(args, **kwargs)
        if args[:2] == ["udisksctl", "unlock"]:
            pending.extend(kernel.node.pop("children"))
        return result

    def ready(_seconds):
        kernel.node["children"] = list(pending)

    monkeypatch.setattr(service.time, "sleep", ready)
    unlocked = service.unlock_device(identity, "test-passphrase", delayed_runner)
    assert unlocked.source.path == MAPPER
    assert [args[1] for args in privileged_calls(kernel)] == ["unlock"]


@pytest.mark.parametrize("override", ["empty", "missing", "foreign"])
def test_real_findmnt_cannot_redirect_trusted_fstab(
    kernel, monkeypatch, tmp_path, override
):
    from netmon.core.command import run_cmd as actual_command

    kernel.table.write_text(f"{DEVICE} /mnt/admin ext4 defaults,exec,suid,dev 0 0\n")
    other = tmp_path / "caller-fstab"
    if override != "missing":
        other.write_text(
            "" if override == "empty" else "tmpfs /tmp tmpfs defaults 0 0\n"
        )
    monkeypatch.setenv("LIBMOUNT_FSTAB", str(other))
    observations = []
    if override == "empty":
        # Reproduce the old decision: this response used to authorize mounting
        # even though the synthetic system table contains the selected device.
        assert actual_command(
            [
                "findmnt",
                "--fstab",
                "--evaluate",
                "--json",
                "--output",
                "SOURCE",
                "--source",
                DEVICE,
            ],
            timeout=8,
        ) == (1, "")

    def runner(args, **kwargs):
        if args[0] == "findmnt":
            assert args[args.index("--tab-file") + 1] == str(kernel.table)
            result = actual_command(args, **kwargs)  # reads synthetic text only
            observations.append(result)
            return result
        return kernel.runner(args, **kwargs)

    identity = service.inspect_device(DEVICE, UUID, runner)
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, runner)
    assert observations and observations[0][0] == 0
    assert DEVICE in observations[0][1]
    assert not privileged_calls(kernel)


@pytest.mark.parametrize("source", [DEVICE, f"UUID={UUID}"])
def test_system_fstab_matching_device_is_rejected(kernel, source):
    kernel.table.write_text(f"{source} /mnt/admin ext4 defaults 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": source, "fstype": "ext4"}]}),
    )
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize(
    "contents",
    [
        "broken entry\n",
        "tmpfs /tmp tmpfs defaults invalid 0\n",
        "tmpfs /tmp tmpfs defaults 0 0 extra\n",
        "tmpfs /tmp\\bad tmpfs defaults 0 0\n",
        "tmpfs /tmp tmpfs defaults\x00 0 0\n",
        "x" * 4097,
        "#" * (service._FSTAB_BYTES + 1),
        "tmpfs /tmp tmpfs defaults 0 0\n" * (service._FSTAB_ENTRIES + 1),
    ],
)
def test_malformed_or_oversized_system_fstab_aborts(kernel, contents):
    kernel.table.write_text(contents)
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize(
    "failure", ["missing", "symlink", "fifo", "writable", "owner", "read"]
)
def test_untrusted_or_unreadable_system_fstab_aborts(
    kernel, monkeypatch, tmp_path, failure
):
    if failure in {"missing", "symlink", "fifo"}:
        absent = tmp_path / "absent-fstab"
        if failure == "symlink":
            absent.symlink_to(kernel.table)
        elif failure == "fifo":
            os.mkfifo(absent)
        monkeypatch.setattr(service, "_SYSTEM_FSTAB", str(absent))
    elif failure == "writable":
        kernel.table.chmod(0o666)
    elif failure == "owner":
        kernel.fstab_owner = 1000
    else:
        original_read = os.read

        def unreadable(fd, length):
            if os.fstat(fd).st_ino == os.stat(kernel.table).st_ino:
                raise PermissionError("synthetic unreadable table")
            return original_read(fd, length)

        monkeypatch.setattr(service.os, "read", unreadable)
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize(
    "result",
    [
        (1, ""),
        (0, "not json"),
        (0, '{"filesystems":null}'),
        (0, '{"filesystems":[{"source":"UUID=unresolved"}]}'),
        (0, '{"filesystems":[{"source":"/dev/missing-fstab-device"}]}'),
        (0, '{"filesystems":[{"source":"dev/relative-device","fstype":"ext4"}]}'),
        (0, '{"filesystems":[{"source":"none","fstype":"ext4"}]}'),
    ],
)
def test_uncertain_system_fstab_evaluation_aborts(kernel, result):
    kernel.fstab = result
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


def test_changing_system_fstab_during_evaluation_aborts(kernel):
    def change(args):
        if args[0] == "findmnt":
            kernel.table.write_text("# changed after read\n")

    kernel.on_command = change
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize("source", ["none", "tmpfs"])
def test_valid_pseudo_filesystem_fstab_entry_does_not_block_other_device(
    kernel, source
):
    kernel.table.write_text(f"{source} /tmp tmpfs defaults 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": source, "fstype": "tmpfs"}]}),
    )
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    assert service.mount_device(identity, kernel.runner)[0] == 0
    assert privileged_calls(kernel)[0][-1] == "nodev,nosuid,noexec"


def test_valid_empty_fstab_does_not_consult_environment(kernel, monkeypatch):
    kernel.table.write_text("# intentionally empty system table\n")
    monkeypatch.setenv("LIBMOUNT_FSTAB", "/caller/controlled/missing")
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    assert service.mount_device(identity, kernel.runner)[0] == 0
    assert not any(args[0] == "findmnt" for args in kernel.calls)
    assert privileged_calls(kernel)[0][-1] == "nodev,nosuid,noexec"


@pytest.fixture
def unmount_app(kernel, mount_app, monkeypatch, tmp_path):
    target = tmp_path / "actual-mounted-filesystem"
    target.mkdir()
    state = SimpleNamespace(
        app=mount_app,
        auth=[],
        effects=[],
        target=str(target),
        result=(0, "unmounted"),
        row={"source": DEVICE, "target": str(target), "uuid": UUID, "maj:min": "8:17"},
        findmnt_rc=0,
        raw=None,
        on_command=None,
    )
    original_runner = kernel.runner

    def runner(args, **kwargs):
        if state.on_command:
            state.on_command(args)
        if args[0] == "findmnt":
            kernel.calls.append(args)
            assert args[args.index("--tab-file") + 1] == "/proc/self/mountinfo"
            assert "--source" in args or "--mountpoint" in args
            return state.findmnt_rc, (
                state.raw
                if state.raw is not None
                else json.dumps({"filesystems": [state.row]})
            )
        if args[0] in {"sudo", "umount", "udisksctl", "cryptsetup"}:
            kernel.calls.append(args)
            state.effects.append(args)
            return state.result
        return original_runner(args, **kwargs)

    mount_app.ensure_sudo_session = lambda label: state.auth.append(label) or True
    # Deliberately deceptive display/cache helpers must never authorize unmount.
    mount_app._hdd_is_mounted = lambda *_a: (True, "/mnt/foreign")
    mount_app._hdd_find_mount_source = lambda *_a: "/dev/foreign"
    mount_app._hdd_luks_info_for_device = lambda *_a: {
        "is_luks": True,
        "mapper_name": "foreign",
    }
    monkeypatch.setattr(service, "run_hdd_command", runner)
    monkeypatch.setattr(
        controller,
        "_authorize_hdd_unmount",
        lambda app, _runner: app.ensure_sudo_session("HDD Unmount"),
    )
    state.runner = runner
    return state


@pytest.mark.parametrize(
    "failure", ["unknown", "empty-uuid", "cached-uuid", "live-uuid", "missing-device"]
)
def test_unmount_without_confirmed_identity_has_no_auth_or_effects(
    kernel, unmount_app, failure
):
    if failure == "unknown":
        unmount_app.app.detected_disks = []
        unmount_app.app.detected_disks_by_device = {}
    elif failure == "empty-uuid":
        unmount_app.app.hdd_slots[0]["device_uuid"] = ""
    elif failure == "cached-uuid":
        unmount_app.app.detected_disks_by_device[DEVICE]["uuid"] = "foreign"
    elif failure == "live-uuid":
        kernel.node["uuid"] = "foreign"
    else:
        del kernel.stats[DEVICE]
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert unmount_app.auth == []
    assert unmount_app.effects == []
    assert any("refused" in line for line in unmount_app.app.logs)


@pytest.mark.parametrize(
    "change",
    [
        "source",
        "uuid",
        "number",
        "root",
        "relative",
        "malformed",
        "multiple",
        "missing",
        "error",
        "symlink",
    ],
)
def test_foreign_or_uncertain_mount_has_no_auth_or_effects(
    unmount_app, tmp_path, change
):
    if change in {"source", "uuid"}:
        unmount_app.row[change] = "/dev/foreign" if change == "source" else "foreign"
    elif change == "number":
        unmount_app.row["maj:min"] = "8:99"
    elif change in {"root", "relative"}:
        unmount_app.row["target"] = "/" if change == "root" else "relative"
    elif change == "symlink":
        link = tmp_path / "alias"
        link.symlink_to(unmount_app.target, target_is_directory=True)
        unmount_app.row["target"] = str(link)
    elif change == "malformed":
        unmount_app.raw = "not json"
    elif change == "multiple":
        unmount_app.raw = json.dumps(
            {"filesystems": [unmount_app.row, unmount_app.row]}
        )
    elif change == "missing":
        unmount_app.raw = '{"filesystems":[]}'
    else:
        unmount_app.findmnt_rc = 1
        unmount_app.raw = ""
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert not unmount_app.auth
    assert not unmount_app.effects


def test_valid_unmount_uses_verified_live_target_not_config_or_display_cache(
    unmount_app,
):
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert unmount_app.auth == ["HDD Unmount"]
    assert unmount_app.effects == [["sudo", "-n", "umount", unmount_app.target]]
    assert unmount_app.app.refreshed == [True]
    assert any("successful" in line for line in unmount_app.app.logs)


@pytest.mark.parametrize(
    "change", ["target", "device", "target-lookup", "worker", "fallback"]
)
def test_mount_changes_abort_without_followup_operations(
    kernel, unmount_app, monkeypatch, change
):
    def mutate(args):
        if change == "target-lookup" and "--mountpoint" in args:
            unmount_app.row["source"] = "/dev/foreign"
        elif change == "fallback" and args[0] == "sudo":
            unmount_app.row["target"] = "/mnt/changed"

    unmount_app.on_command = mutate
    if change in {"target", "device"}:

        def auth(_label):
            if change == "target":
                unmount_app.row["target"] = "/mnt/changed"
            else:
                kernel.node["uuid"] = "changed"
            return True

        unmount_app.app.ensure_sudo_session = auth
    elif change == "fallback":
        unmount_app.result = (1, "synthetic busy")
    elif change == "worker":
        jobs = []

        class Delayed:
            def __init__(self, target, **_kw):
                jobs.append(target)

            def start(self):
                pass

        monkeypatch.setattr(controller.threading, "Thread", Delayed)
    controller.hdd_unmount_async(unmount_app.app, 0)
    if change == "worker":
        kernel.node["uuid"] = "changed while waiting"
        jobs.pop()()
    assert len(unmount_app.effects) == (1 if change == "fallback" else 0)
    assert not any("successful" in line for line in unmount_app.app.logs)


def test_unmount_failure_does_not_report_success(unmount_app):
    unmount_app.result = (1, "synthetic busy")
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert len(unmount_app.effects) == 4
    assert any("failed" in line for line in unmount_app.app.logs)
    assert not any("successful" in line for line in unmount_app.app.logs)


def test_missing_identity_reproduction_never_queries_foreign_ancestor(
    kernel, unmount_app
):
    app = unmount_app.app
    app.detected_disks = []
    app.detected_disks_by_device = {}
    app.hdd_slots[0].update(
        device="/dev/m4-missing",
        device_uuid="missing-uuid",
        mountpoint="/mnt/foreign-filesystem/subdirectory",
    )
    controller.hdd_unmount_async(app, 0)
    assert unmount_app.auth == []
    assert unmount_app.effects == []
    assert not any(args[0] == "findmnt" for args in kernel.calls)


@pytest.mark.parametrize(
    "bad_json",
    ['{"filesystems":[null]}', '{"filesystems":[{}]}', '{"filesystems":{}}', "[]"],
)
def test_invalid_unmount_metadata_never_reaches_auth(unmount_app, bad_json):
    unmount_app.raw = bad_json
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert unmount_app.auth == []
    assert unmount_app.effects == []


@pytest.mark.parametrize("change_after_unmount", [False, True])
def test_verified_luks_unmount_closes_only_live_bound_mapper(
    kernel, unmount_app, change_after_unmount
):
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
    unmount_app.row.update(source=MAPPER, uuid="clear-uuid", **{"maj:min": "253:0"})

    def mutate(args):
        if change_after_unmount and args[:3] == ["sudo", "-n", "umount"]:
            kernel.node["uuid"] = "changed before mapper close"

    unmount_app.on_command = mutate
    controller.hdd_unmount_async(unmount_app.app, 0)
    expected = [["sudo", "-n", "umount", unmount_app.target]]
    if not change_after_unmount:
        expected.append(["sudo", "-n", "cryptsetup", "luksClose", MAPPER])
    assert unmount_app.effects == expected
    assert not any("foreign" in " ".join(args) for args in unmount_app.effects)


def test_unmount_permission_denied_before_worker_has_no_effect(unmount_app):
    unmount_app.app.ensure_sudo_session = lambda _reason: False
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert unmount_app.effects == []


def test_frozen_unmount_slot_cannot_be_redirected_after_scheduling(
    unmount_app, monkeypatch
):
    jobs = []

    class Delayed:
        def __init__(self, target, **_kw):
            jobs.append(target)

        def start(self):
            pass

    monkeypatch.setattr(controller.threading, "Thread", Delayed)
    controller.hdd_unmount_async(unmount_app.app, 0)
    unmount_app.app.hdd_slots[0].update(
        device="/dev/foreign", device_uuid="foreign", mountpoint="/mnt/foreign"
    )
    jobs.pop()()
    assert unmount_app.effects == [["sudo", "-n", "umount", unmount_app.target]]


@pytest.mark.parametrize("stage", ["findmnt", "sudo"])
def test_unmount_process_error_stops_all_followup_operations(unmount_app, stage):
    def fail(args):
        if args[0] == stage:
            raise OSError("synthetic process error")

    unmount_app.on_command = fail
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert unmount_app.effects == []
    assert any("refused" in line for line in unmount_app.app.logs)


def test_invalid_utf8_system_fstab_is_not_ignored(kernel):
    kernel.table.write_bytes(b"# broken metadata\xff\n")
    identity = service.inspect_device(DEVICE, UUID, kernel.runner)
    with pytest.raises(service.MountPolicyError, match="fstab"):
        service.mount_device(identity, kernel.runner)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize("special", ["/dev/null", "/dev/zero"])
@pytest.mark.parametrize("variable", ["BLKID_FILE", "BLKID_CONF"])
def test_original_blkid_cache_attacks_rejected_on_production_path(
    kernel, mount_app, monkeypatch, tmp_path, special, variable
):
    """Positive control reproduces the old resolution; the production path refuses."""
    import time

    from netmon.core.command import run_cmd as old_runner

    kernel.table.write_text(f"UUID={UUID} /mnt/admin ext4 dev,suid,exec 0 0\n")
    cache = tmp_path / "poisoned-blkid-cache"
    cache.write_text(
        f'<device DEVNO="{hex(os.stat(special).st_rdev)}" '
        f'TIME="{int(time.time())}" UUID="{UUID}" TYPE="ext4">{special}</device>\n'
    )
    conf = tmp_path / "poisoned-blkid.conf"
    conf.write_text(f"EVALUATE=scan\nSEND_UEVENT=no\nCACHE_FILE={cache}\n")
    for name in ("BLKID_FILE", "BLKID_CONF"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(variable, str(cache if variable == "BLKID_FILE" else conf))
    rc, out = old_runner(
        [
            "/usr/bin/findmnt",
            "--fstab",
            "--tab-file",
            str(kernel.table),
            "--evaluate",
            "--list",
            "--json",
            "--output",
            "SOURCE,FSTYPE",
        ],
        timeout=8,
    )
    assert rc == 0 and json.loads(out)["filesystems"][0]["source"] == special
    observations = []

    def runner(args, **kwargs):
        if args[0] == "findmnt":
            assert "--evaluate" not in args
            result = REAL_HDD_RUNNER(args, **kwargs)
            observations.append(result)
            return result
        return kernel.runner(args, **kwargs)

    monkeypatch.setattr(service, "run_hdd_command", runner)
    controller.hdd_mount_async(mount_app, 0)
    assert len(observations) == 1 and observations[0][0] == 0
    assert json.loads(observations[0][1])["filesystems"][0]["source"] == f"UUID={UUID}"
    assert not privileged_calls(kernel)
    assert any("fstab" in line for line in mount_app.logs)


def test_combined_blkid_and_libmount_overrides_cannot_replace_fstab(
    kernel, mount_app, monkeypatch, tmp_path
):
    kernel.table.write_text(f"UUID={UUID} /mnt/admin ext4 defaults 0 0\n")
    hostile = tmp_path / "caller-fstab"
    hostile.write_text("")
    for name in ("BLKID_FILE", "BLKID_CONF", "LIBMOUNT_FSTAB", "LIBMOUNT_MTAB"):
        monkeypatch.setenv(name, str(hostile))

    def runner(args, **kwargs):
        if args[0] == "findmnt":
            return REAL_HDD_RUNNER(args, **kwargs)
        return kernel.runner(args, **kwargs)

    monkeypatch.setattr(service, "run_hdd_command", runner)
    controller.hdd_mount_async(mount_app, 0)
    assert not privileged_calls(kernel)
    assert any("fstab" in line for line in mount_app.logs)


@pytest.mark.parametrize(
    "args, expected",
    [
        (["findmnt", "--version"], ["/usr/bin/findmnt", "--version"]),
        (["lsblk", "--version"], ["/usr/bin/lsblk", "--version"]),
        (["udisksctl", "mount"], ["/usr/bin/udisksctl", "mount"]),
        (["umount", "/mnt/test"], ["/usr/bin/umount", "/mnt/test"]),
        (
            ["cryptsetup", "luksClose", MAPPER],
            ["/usr/sbin/cryptsetup", "luksClose", MAPPER],
        ),
        (
            ["sudo", "-n", "umount", "/mnt/test"],
            ["/usr/bin/sudo", "-n", "/usr/bin/umount", "/mnt/test"],
        ),
        (
            ["sudo", "-n", "cryptsetup", "luksClose", MAPPER],
            ["/usr/bin/sudo", "-n", "/usr/sbin/cryptsetup", "luksClose", MAPPER],
        ),
        (["sudo", "-n", "true"], ["/usr/bin/sudo", "-n", "/usr/bin/true"]),
        (["sudo", "-S", "-v"], ["/usr/bin/sudo", "-S", "-v"]),
    ],
)
def test_hdd_runner_uses_fixed_paths_and_explicit_environment(
    monkeypatch, args, expected
):
    for name in (
        "PATH",
        "LD_PRELOAD",
        "LD_LIBRARY_PATH",
        "LD_AUDIT",
        "GLIBC_TUNABLES",
        "BLKID_FILE",
        "BLKID_CONF",
        "LIBMOUNT_FSTAB",
        "LIBMOUNT_MTAB",
        "LIBMOUNT_DEBUG",
        "LIBBLKID_DEBUG",
        "LIBSMARTCOLS_DEBUG",
        "DBUS_SYSTEM_BUS_ADDRESS",
        "DBUS_SESSION_BUS_ADDRESS",
        "PYTHONPATH",
        "GCONV_PATH",
        "LOCPATH",
        "LANG",
        "LC_ALL",
        "HOME",
        "SUDO_ASKPASS",
    ):
        monkeypatch.setenv(name, "/caller/controlled")
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout=" simulated result\n")

    monkeypatch.setattr(service.subprocess, "run", fake_run)
    assert REAL_HDD_RUNNER(args, timeout=7, input_text="synthetic secret\n") == (
        0,
        "simulated result",
    )
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv == expected
    assert kwargs["env"] == {
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
    }
    assert kwargs["shell"] is False and kwargs["timeout"] == 7
    assert kwargs["input"] == "synthetic secret\n"
    assert all("secret" not in arg for arg in argv)
    assert os.environ["BLKID_FILE"] == "/caller/controlled"


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["mount", DEVICE],
        ["/tmp/findmnt"],
        ["sudo", "mount"],
        ["sudo", "-n", "mount", DEVICE],
    ],
)
def test_hdd_runner_rejects_unknown_tools_before_execution(monkeypatch, args):
    monkeypatch.setattr(
        service.subprocess, "run", lambda *a, **kw: pytest.fail("must not execute")
    )
    with pytest.raises(service.MountPolicyError):
        REAL_HDD_RUNNER(args)


@pytest.mark.parametrize(
    "error", [FileNotFoundError("missing tool"), PermissionError("denied")]
)
def test_hdd_runner_process_errors_fail_closed(monkeypatch, error):
    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(service.subprocess, "run", fail)
    assert REAL_HDD_RUNNER(["findmnt"])[0] == 1


def test_hdd_runner_timeout_fails_closed(monkeypatch):
    def fail(*_args, **_kwargs):
        raise service.subprocess.TimeoutExpired("findmnt", 8)

    monkeypatch.setattr(service.subprocess, "run", fail)
    assert REAL_HDD_RUNNER(["findmnt"])[0] == 124


@pytest.mark.parametrize(
    "kind",
    [
        "null",
        "zero",
        "file",
        "directory",
        "missing",
        "fifo",
        "symlink-null",
        "symlink-file",
    ],
)
def test_fstab_requires_actual_block_device(kernel, tmp_path, kind):
    if kind in {"null", "zero"}:
        path = Path("/dev") / kind
    else:
        path = tmp_path / "bad-source"
        if kind == "file":
            path.write_text("image")
        elif kind == "directory":
            path.mkdir()
        elif kind == "fifo":
            os.mkfifo(path)
        elif kind.startswith("symlink"):
            target = Path("/dev/null")
            if kind == "symlink-file":
                target = tmp_path / "image"
                target.write_text("image")
            path.symlink_to(target)
    kernel.table.write_text(f"{path} /mnt/admin ext4 defaults 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": str(path), "fstype": "ext4"}]}),
    )
    with pytest.raises(service.MountPolicyError):
        service.mount_device(
            service.inspect_device(DEVICE, UUID, kernel.runner), kernel.runner
        )
    assert not privileged_calls(kernel)


@pytest.mark.parametrize(
    "tag",
    [
        FSTAB_DEVICE,
        "UUID=system-uuid",
        "LABEL=System",
        "PARTUUID=partition-id",
        "PARTLABEL=SystemPart",
    ],
)
def test_valid_fstab_block_identity_allows_unrelated_hdd(kernel, tag):
    system = kernel.roots[1]
    system.update(label="System", partuuid="partition-id", partlabel="SystemPart")
    kernel.table.write_text(f"{tag} /mnt/other ext4 defaults 0 0\n")
    kernel.fstab = (0, json.dumps({"filesystems": [{"source": tag, "fstype": "ext4"}]}))
    assert (
        service.mount_device(
            service.inspect_device(DEVICE, UUID, kernel.runner), kernel.runner
        )[0]
        == 0
    )
    assert privileged_calls(kernel)[0][-1] == "nodev,nosuid,noexec"


@pytest.mark.parametrize(
    "problem",
    [
        "unknown-tag",
        "ambiguous-label",
        "duplicate-uuid",
        "wrong-number",
        "wrong-fstype",
        "contradictory-path",
        "no-uuid",
        "loop",
        "unresolved-path",
    ],
)
def test_fstab_identity_conflicts_abort(kernel, problem):
    system = kernel.roots[1]
    tag = "UUID=system-uuid"
    fstype = "ext4"
    if problem == "unknown-tag":
        tag = "UUID=missing"
    elif problem == "ambiguous-label":
        tag = "LABEL=duplicate"
        system["label"] = kernel.node["label"] = "duplicate"
    elif problem == "duplicate-uuid":
        kernel.node["uuid"] = "system-uuid"
        # The selected disk still has a separate identity for this table check.
    elif problem == "wrong-number":
        system["maj:min"] = "8:99"
    elif problem == "wrong-fstype":
        fstype = "xfs"
    elif problem == "contradictory-path":
        kernel.roots.append({**system, "uuid": "different"})
    elif problem == "no-uuid":
        system["uuid"] = ""
        tag = FSTAB_DEVICE
    elif problem == "loop":
        kernel.roots[1] = {"path": "/dev/loop0", "type": "loop", "children": [system]}
    else:
        tag = "/dev/missing-system-source"
    kernel.table.write_text(f"{tag} /mnt/other {fstype} defaults 0 0\n")
    kernel.fstab = (0, json.dumps({"filesystems": [{"source": tag, "fstype": fstype}]}))
    source = service.DeviceIdentity(DEVICE, UUID, os.makedev(8, 17), "part", "ext4")
    with pytest.raises(service.MountPolicyError):
        service._check_system_fstab(source, kernel.runner)
    assert not privileged_calls(kernel)


def test_legacy_app_runner_cannot_authorize_mount(kernel, mount_app, monkeypatch):
    monkeypatch.setattr(
        controller, "run_cmd", lambda *a, **kw: pytest.fail("legacy runner used")
    )
    controller.hdd_mount_async(mount_app, 0)
    assert privileged_calls(kernel)[0][:2] == ["udisksctl", "mount"]


@pytest.mark.parametrize("stage", ["table-query", "table-inventory"])
@pytest.mark.parametrize("rc", [1, 2, 124, -1])
def test_fstab_tool_failure_never_reaches_mount(kernel, stage, rc):
    def runner(args, **kwargs):
        if stage == "table-query" and args[0] == "findmnt":
            return rc, "unreliable output"
        if stage == "table-inventory" and args[0] == "lsblk":
            return rc, "unreliable output"
        return kernel.runner(args, **kwargs)

    source = service.DeviceIdentity(DEVICE, UUID, os.makedev(8, 17), "part", "ext4")
    with pytest.raises(service.MountPolicyError):
        service._check_system_fstab(source, runner)
    assert not privileged_calls(kernel)


@pytest.mark.parametrize("scenario", ["already-valid", "password", "cancel", "denied"])
def test_hdd_unmount_authorization_uses_controlled_runner(monkeypatch, scenario):
    calls = []
    app = SimpleNamespace(log=lambda _message: None)
    monkeypatch.setattr(
        controller.simpledialog,
        "askstring",
        lambda *a, **kw: None if scenario == "cancel" else "synthetic password",
    )

    def runner(args, **kwargs):
        calls.append((args, kwargs))
        if args == ["sudo", "-n", "true"]:
            return (0 if scenario == "already-valid" else 1), ""
        assert args == ["sudo", "-S", "-v"]
        assert kwargs["input_text"] == "synthetic password\n"
        return (0 if scenario == "password" else 1), ""

    assert controller._authorize_hdd_unmount(app, runner) is (
        scenario in {"already-valid", "password"}
    )
    expected = {"already-valid": 1, "password": 2, "cancel": 1, "denied": 4}[scenario]
    assert len(calls) == expected


def test_valid_fstab_device_symlink_is_verified(kernel, tmp_path):
    alias = tmp_path / "device-alias"
    alias.symlink_to(FSTAB_DEVICE)
    kernel.table.write_text(f"{alias} /mnt/other ext4 defaults 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": str(alias), "fstype": "ext4"}]}),
    )
    assert (
        service.mount_device(
            service.inspect_device(DEVICE, UUID, kernel.runner), kernel.runner
        )[0]
        == 0
    )


@pytest.mark.parametrize("switch", ["alias", "number"])
def test_fstab_device_switch_during_stat_is_rejected(
    kernel, monkeypatch, tmp_path, switch
):
    alias = tmp_path / "device-alias"
    alias.symlink_to(FSTAB_DEVICE)
    original_stat = service.os.stat
    calls = 0

    def change(path, *args, **kwargs):
        nonlocal calls
        result = original_stat(path, *args, **kwargs)
        if str(path) == FSTAB_DEVICE:
            calls += 1
            if calls == 1:
                if switch == "alias":
                    # Replace only our synthetic symlink; never a system path.
                    replacement = tmp_path / "new-alias"
                    replacement.symlink_to(DEVICE)
                    replacement.replace(alias)
                else:
                    kernel.stats[FSTAB_DEVICE] = (stat.S_IFBLK, os.makedev(8, 2))
                    kernel.roots[1]["maj:min"] = "8:2"
        return result

    monkeypatch.setattr(service.os, "stat", change)
    kernel.table.write_text(f"{alias} /mnt/other ext4 defaults 0 0\n")
    kernel.fstab = (
        0,
        json.dumps({"filesystems": [{"source": str(alias), "fstype": "ext4"}]}),
    )
    with pytest.raises(service.MountPolicyError):
        service.mount_device(
            service.inspect_device(DEVICE, UUID, kernel.runner), kernel.runner
        )
    assert not privileged_calls(kernel)


@pytest.mark.parametrize(
    "field,value", [("uuid", "contradiction"), ("fstype", "xfs"), ("maj:min", "8:99")]
)
def test_contradictory_selected_device_descriptions_fail_closed(kernel, field, value):
    kernel.roots.append({**kernel.node, field: value})
    with pytest.raises(service.MountPolicyError):
        service.inspect_device(DEVICE, UUID, kernel.runner)
    assert not privileged_calls(kernel)
