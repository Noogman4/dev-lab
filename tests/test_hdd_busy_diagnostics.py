"""Busy observations against private proc fixtures and command fakes only."""

import os

import pytest

from netmon.features import hdd_controller as controller
from netmon.services import hdd_mount_service as service
from tests.test_hdd_action_feedback import feedback
from tests.test_hdd_mount_security import kernel as kernel
from tests.test_hdd_mount_security import mount_app as mount_app
from tests.test_hdd_mount_security import unmount_app as unmount_app


@pytest.fixture
def proc(tmp_path, monkeypatch):
    root = tmp_path / "proc"
    (root / "self/ns").mkdir(parents=True)
    (root / "self/ns/mnt").write_text("synthetic namespace")
    monkeypatch.setattr(service, "_PROC_ROOT", str(root), raising=False)
    return root


def process(root, pid, target, *, same_namespace=True, cwd=True, fd=True):
    directory = root / str(pid)
    (directory / "ns").mkdir(parents=True)
    if same_namespace:
        os.link(root / "self/ns/mnt", directory / "ns/mnt")
    else:
        (directory / "ns/mnt").write_text("another namespace")
    (directory / "comm").write_text("editor\n")
    (directory / "fd").mkdir()
    (directory / "cwd").symlink_to(target if cwd else "/other")
    if fd:
        (directory / "fd/5").symlink_to(target + "/file")
    return directory


def test_busy_process_evidence_uses_path_boundary_and_matching_namespace(proc):
    process(proc, 123, "/mnt/test")
    process(proc, 124, "/mnt/test-sibling")
    process(proc, 125, "/mnt/test", same_namespace=False)
    assert service._busy_process_references("/mnt/test") == ((123, "editor", "cwd,fd"),)


def test_inaccessible_or_disappeared_process_is_only_missing_evidence(proc):
    directory = process(proc, 123, "/mnt/test")
    (directory / "ns/mnt").unlink()
    assert service._busy_process_references("/mnt/test") == ()


def test_busy_process_budget_is_bounded(proc):
    for pid in range(100, 125):
        process(proc, pid, "/mnt/test")
    assert len(service._busy_process_references("/mnt/test")) == 20


def test_mount_dependencies_follow_parent_ids_not_path_prefix(proc):
    (proc / "self/mountinfo").write_text(
        "10 1 8:17 / /mnt/test rw - ext4 /dev/fake rw\n"
        "11 10 0:99 / /mnt/test/child rw - tmpfs none rw\n"
        "12 11 0:98 / /mnt/test/child/grandchild rw - tmpfs none rw\n"
        "13 1 0:97 / /mnt/test-sibling rw - tmpfs none rw\n"
    )
    assert service._busy_child_mounts("/mnt/test", os.makedev(8, 17)) == (
        "/mnt/test/child",
        "/mnt/test/child/grandchild",
    )


@pytest.mark.parametrize(
    "data",
    [
        "malformed",
        "10 1 8:99 / /mnt/test rw - ext4 /dev/fake rw\n",
        "x" * (1024 * 1024 + 1),
    ],
)
def test_invalid_mount_dependency_snapshot_refuses(proc, data):
    (proc / "self/mountinfo").write_text(data)
    with pytest.raises(service.MountPolicyError):
        service._busy_child_mounts("/mnt/test", os.makedev(8, 17))


@pytest.mark.parametrize(
    "result", [(((123, "editor", "cwd,fd"),), ("/mnt/test/child",)), ((), ())]
)
def test_busy_evidence_is_visible_without_new_mutations(
    unmount_app, monkeypatch, result
):
    status = feedback(unmount_app.app)
    unmount_app.result = (1, "target is busy")
    calls = []

    def diagnose(identity, target, runner):
        calls.append((identity, target))
        return result

    monkeypatch.setattr(service, "busy_mount_diagnostics", diagnose)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert len(calls) == 1 and calls[0][1] == unmount_app.target
    assert len(unmount_app.effects) == 4 and "successful" not in status.text
    assert "incomplete" in status.text
    if result[0]:
        assert "123/editor/cwd,fd" in status.text and "/mnt/test/child" in status.text
    else:
        assert "does not prove" in status.text
    assert not any(
        arg in {"-f", "-l", "--force", "--lazy", "kill"}
        for command in unmount_app.effects
        for arg in command
    )


def test_diagnostic_failure_does_not_hide_busy_failure(unmount_app, monkeypatch):
    status = feedback(unmount_app.app)
    unmount_app.result = (1, "target is busy")

    def deny(*_args):
        raise PermissionError("metadata access denied")

    monkeypatch.setattr(service, "busy_mount_diagnostics", deny)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert "target is busy" in status.text and "unavailable" in status.text
    assert len(unmount_app.effects) == 4


def test_successful_unmount_does_not_scan_processes(unmount_app, monkeypatch):
    monkeypatch.setattr(
        service, "busy_mount_diagnostics", lambda *a: pytest.fail("unneeded scan")
    )
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert len(unmount_app.effects) == 1


def test_complete_read_only_diagnostic_with_bound_synthetic_mount(proc, unmount_app):
    identity = service.inspect_device(
        unmount_app.app.hdd_slots[0]["device"],
        unmount_app.app.hdd_slots[0]["device_uuid"],
        service.run_hdd_command,
    )
    target = unmount_app.target
    (proc / "self/mountinfo").write_text(
        f"10 1 8:17 / {target} rw - ext4 /dev/fake rw\n"
    )
    process(proc, 123, target)
    assert service.busy_mount_diagnostics(
        identity, target, service.run_hdd_command
    ) == (((123, "editor", "cwd,fd"),), ())
    assert not unmount_app.effects


def test_device_change_discards_busy_evidence(kernel, unmount_app, monkeypatch):
    status = feedback(unmount_app.app)
    unmount_app.result = (1, "target is busy")

    def changed(*_args):
        path = unmount_app.app.hdd_slots[0]["device"]
        mode, number = kernel.stats[path]
        kernel.stats[path] = (mode, number + 1)
        return ((123, "discard-me", "cwd"),), ()

    monkeypatch.setattr(service, "busy_mount_diagnostics", changed)
    controller.hdd_unmount_async(unmount_app.app, 0)
    assert "unavailable" in status.text and "discard-me" not in status.text
    assert len(unmount_app.effects) == 4


@pytest.mark.parametrize("change_after", [False, True])
def test_busy_diagnostics_rechecks_mount_binding(
    unmount_app, monkeypatch, change_after
):
    identity = service.inspect_device(
        unmount_app.app.hdd_slots[0]["device"],
        unmount_app.app.hdd_slots[0]["device_uuid"],
        service.run_hdd_command,
    )
    calls = []

    def target(*args):
        calls.append(True)
        return unmount_app.target if change_after and len(calls) == 1 else "/changed"

    monkeypatch.setattr(service, "verified_mount_target", target)
    monkeypatch.setattr(service, "_busy_child_mounts", lambda *a: ())
    monkeypatch.setattr(service, "_busy_process_references", lambda *a: ())
    with pytest.raises(service.MountPolicyError, match="changed"):
        service.busy_mount_diagnostics(
            identity, unmount_app.target, service.run_hdd_command
        )
    assert not unmount_app.effects
