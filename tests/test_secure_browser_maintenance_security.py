"""Maintenance must not follow imported symlinks or mutate linked inodes."""

import os
import stat

import pytest

from netmon.modules.secure_browser.models import BrowserContainer
from netmon.modules.secure_browser.service import SecureBrowserService
from tools.secure_browser_manager import browser_container_builder as builder


@pytest.fixture
def maintenance(tmp_path, monkeypatch):
    root = tmp_path / "firefox-Test"
    (root / "firefox" / "distribution").mkdir(parents=True)
    (root / "firefox" / "firefox").write_text("")
    (root / "profile").mkdir()
    (root / "user.js").write_text('user_pref("test", true);')
    (root / "policies.json").write_text('{"policies": {}}')
    found = builder.discover_container(root / "firefox" / "firefox")
    found.domains = ["example.invalid"]
    container = BrowserContainer(
        name=root.name,
        path=root,
        binary_path=found.binary_path,
        profile_path=root / "profile",
        homepage_url="https://example.invalid",
        allowed_domains=["example.invalid"],
    )
    service = SecureBrowserService()
    service._tool_module = builder
    monkeypatch.setattr(
        builder, "prepare_container_icon", lambda spec: ("firefox", None)
    )
    victim = tmp_path / "outside"
    victim.write_bytes(b"outside sentinel")
    victim.chmod(0o640)
    return root, found, container, service, victim


@pytest.mark.parametrize(
    "operation,name",
    [
        ("refresh", "start.sh"),
        ("refresh", "launcher.desktop"),
        ("repair", "policies.json"),
        ("repair", "user.js"),
        ("repair", "firefox/distribution/policies.json"),
        ("repair", "profile/user.js"),
        ("save", "policies.json"),
        ("save", "firefox/distribution/policies.json"),
        ("lock", "child-lock.json"),
        ("lock", "browser_lock.py"),
        ("unlock", "child-lock.json"),
        ("unlock", "browser_lock.py"),
    ],
)
@pytest.mark.parametrize("dangling", [False, True])
def test_maintenance_rejects_linked_targets(
    maintenance, tmp_path, operation, name, dangling
):
    root, found, container, service, victim = maintenance
    target = root / name
    target.unlink(missing_ok=True)
    destination = victim if not dangling else tmp_path / "missing-outside"
    target.symlink_to(destination)
    before = victim.stat()
    lock = {"salt": "00" * 16, "password_hash": "00" * 32, "iterations": 200000}
    # Use the real validator's known accepted format from the manager.
    if operation == "lock":
        from netmon.modules.secure_browser.manager import SecureBrowserManager

        lock = SecureBrowserManager.create_child_lock_payload("testpasswort")
    with pytest.raises((OSError, ValueError)):
        if operation == "refresh":
            builder.refresh_existing_container(found, tmp_path / "applications")
        elif operation == "repair":
            builder.repair_existing_policy_container(found)
        elif operation == "save":
            service.save_policy_json(container, '{"policies": {}}')
        else:
            service.configure_container_child_lock(
                container, lock if operation == "lock" else None
            )
    assert victim.read_bytes() == b"outside sentinel"
    assert victim.stat().st_mode == before.st_mode
    assert target.is_symlink()
    if dangling:
        assert not destination.exists()


@pytest.mark.parametrize(
    "component", ["firefox", "profile", "backups", "browser-container-builder-backups"]
)
def test_maintenance_rejects_linked_directories(maintenance, tmp_path, component):
    root, found, container, service, victim = maintenance
    outside = tmp_path / "outside-directory"
    outside.mkdir()
    path = root / component
    if path.exists():
        path.rename(root / (component + "-original"))
    path.symlink_to(outside, target_is_directory=True)
    with pytest.raises((OSError, ValueError)):
        if component == "backups":
            service.save_policy_json(container, '{"policies": {}}')
        else:
            builder.repair_existing_policy_container(found)
    assert list(outside.iterdir()) == []
    assert victim.read_bytes() == b"outside sentinel"


def test_hardlink_rejected_without_changing_external_inode(tmp_path):
    victim = tmp_path / "victim"
    victim.write_bytes(b"sentinel")
    target = tmp_path / "target"
    os.link(victim, target)
    with pytest.raises(ValueError):
        builder.write_text(target, "replacement", executable=True)
    with pytest.raises(ValueError):
        builder.backup_existing_file(target)
    assert victim.read_bytes() == b"sentinel"
    assert not victim.stat().st_mode & stat.S_IXUSR


def test_last_moment_file_link_cannot_redirect_write(tmp_path, monkeypatch):
    target = tmp_path / "target"
    target.write_bytes(b"old")
    victim = tmp_path / "victim"
    victim.write_bytes(b"outside")
    replace = os.replace

    def race(source, destination, **kwargs):
        target.unlink()
        target.symlink_to(victim)
        return replace(source, destination, **kwargs)

    monkeypatch.setattr(builder.os, "replace", race)
    builder.write_text(target, "new", executable=True)
    assert target.read_text() == "new"
    assert not target.is_symlink()
    assert victim.read_bytes() == b"outside"
    assert not victim.stat().st_mode & stat.S_IXUSR


def test_parent_substitution_uses_open_directory(tmp_path, monkeypatch):
    parent = tmp_path / "container"
    parent.mkdir()
    target = parent / "target"
    target.write_bytes(b"old")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "target").write_bytes(b"outside")
    replace = os.replace
    moved = tmp_path / "moved"

    def race(source, destination, **kwargs):
        parent.rename(moved)
        parent.symlink_to(outside, target_is_directory=True)
        return replace(source, destination, **kwargs)

    monkeypatch.setattr(builder.os, "replace", race)
    builder.write_text(target, "new")
    assert (moved / "target").read_text() == "new"
    assert (outside / "target").read_bytes() == b"outside"


def test_backup_destination_symlink_rejected(tmp_path):
    source = tmp_path / "source"
    source.write_bytes(b"source")
    victim = tmp_path / "victim"
    victim.write_bytes(b"outside")
    backup = tmp_path / "backup"
    backup.symlink_to(victim)
    with pytest.raises(ValueError):
        builder.backup_existing_file(source, backup)
    assert victim.read_bytes() == b"outside"


@pytest.mark.parametrize("kind", ["fifo", "directory"])
def test_special_maintenance_targets_rejected(tmp_path, kind):
    target = tmp_path / "target"
    if kind == "fifo":
        os.mkfifo(target)
    else:
        target.mkdir()
    with pytest.raises(ValueError):
        builder.write_text(target, "replacement")
    with pytest.raises(ValueError):
        builder.backup_existing_file(target)


def test_root_symlink_substituted_after_discovery(maintenance, tmp_path):
    root, found, _container, _service, _victim = maintenance
    root.rename(tmp_path / "original")
    outside = tmp_path / "outside-tree"
    outside.mkdir()
    (outside / "start.sh").write_bytes(b"outside")
    root.symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        builder.refresh_existing_container(found, tmp_path / "applications")
    assert (outside / "start.sh").read_bytes() == b"outside"
    assert sorted(p.name for p in outside.iterdir()) == ["start.sh"]


def test_dotdot_maintenance_path_rejected(tmp_path):
    (tmp_path / "container").mkdir()
    with pytest.raises(ValueError):
        builder.write_text(tmp_path / "container" / ".." / "outside", "escape")
    assert not (tmp_path / "outside").exists()


def test_preapply_backup_rejects_linked_root(tmp_path):
    base = tmp_path / "containers"
    base.mkdir()
    outside = tmp_path / "outside-backups"
    outside.mkdir()
    (base / "browser-container-builder-backups").symlink_to(
        outside, target_is_directory=True
    )
    with pytest.raises(OSError):
        builder.create_builder_backup(base, tmp_path / "missing.md", [], ["plan"])
    assert list(outside.iterdir()) == []


def test_preapply_backup_rejects_timestamp_link_before_open(tmp_path, monkeypatch):
    base = tmp_path / "containers"
    base.mkdir()
    outside = tmp_path / "outside-backups"
    outside.mkdir()
    (outside / "plan.json").write_bytes(b"foreign plan")
    mkdir = os.mkdir

    def substitute(path, *args, **kwargs):
        result = mkdir(path, *args, **kwargs)
        if os.path.basename(os.fspath(path)).startswith("20"):
            parent = kwargs.get("dir_fd")
            os.rename(
                os.fspath(path),
                os.fspath(path) + "-original",
                src_dir_fd=parent,
                dst_dir_fd=parent,
            )
            os.symlink(outside, path, dir_fd=parent)
        return result

    monkeypatch.setattr(builder.os, "mkdir", substitute)
    with pytest.raises(OSError):
        builder.create_builder_backup(base, tmp_path / "missing.md", [], ["plan"])
    assert (outside / "plan.json").read_bytes() == b"foreign plan"
    assert sorted(p.name for p in outside.iterdir()) == ["plan.json"]


def test_preapply_backup_keeps_all_outputs_on_open_directory(tmp_path, monkeypatch):
    import io
    import tarfile

    base = tmp_path / "containers"
    base.mkdir()
    inventory = tmp_path / "inventory.md"
    inventory.write_bytes(b"captured inventory")
    outside = tmp_path / "outside-backups"
    outside.mkdir()
    (outside / "plan.json").write_bytes(b"foreign plan")
    write_at = builder._maintenance_write_at
    moved = tmp_path / "original-backup"
    switched = False

    def substitute(directory, name, content, **kwargs):
        nonlocal switched
        if not switched:
            switched = True
            backup = next((base / "browser-container-builder-backups").iterdir())
            backup.rename(moved)
            backup.symlink_to(outside, target_is_directory=True)
            inventory.write_bytes(b"changed inventory")
        return write_at(directory, name, content, **kwargs)

    monkeypatch.setattr(builder, "_maintenance_write_at", substitute)
    builder.create_builder_backup(base, inventory, [], ["dry run"])
    assert (outside / "plan.json").read_bytes() == b"foreign plan"
    assert sorted(p.name for p in outside.iterdir()) == ["plan.json"]
    assert (moved / "inventory.md").read_bytes() == b"captured inventory"
    with tarfile.open(
        fileobj=io.BytesIO((moved / "pre_apply_snapshot.tar.gz").read_bytes())
    ) as archive:
        assert set(archive.getnames()) == {"plan.json", "dry_run.txt", "inventory.md"}
        for member in archive.getmembers():
            assert member.isfile()
            assert (
                archive.extractfile(member).read() == (moved / member.name).read_bytes()
            )


def menu_fixture(tmp_path):
    applications = tmp_path / "applications"
    applications.mkdir()
    root = tmp_path / "firefox-Test"
    spec = builder.ContainerSpec(
        name="firefox-Test",
        path=root,
        source_firefox_dir=None,
        allowed_domains=["example.invalid"],
    )
    old = applications / "old.desktop"
    old.write_text(f'[Desktop Entry]\nName=Old\nExec="{root / "start.sh"}"\n')
    return applications, spec, old


def test_menu_cleanup_parent_swap_does_not_delete_foreign_entry(tmp_path, monkeypatch):
    applications, spec, old = menu_fixture(tmp_path)
    outside = tmp_path / "outside-menu"
    outside.mkdir()
    foreign = outside / old.name
    foreign.write_bytes(b"foreign desktop")
    moved = tmp_path / "original-menu"
    unlink = os.unlink

    def substitute(name, **kwargs):
        if os.fspath(name) in (old.name, str(old)):
            applications.rename(moved)
            applications.symlink_to(outside, target_is_directory=True)
        return unlink(name, **kwargs)

    monkeypatch.setattr(builder.os, "unlink", substitute)
    builder.remove_conflicting_menu_entries(
        spec, applications, applications / "current.desktop"
    )
    assert foreign.read_bytes() == b"foreign desktop"
    assert not (moved / old.name).exists()


@pytest.mark.parametrize("replacement", ["file", "symlink"])
def test_menu_cleanup_preserves_replaced_candidate(tmp_path, monkeypatch, replacement):
    applications, spec, old = menu_fixture(tmp_path)
    foreign = tmp_path / "foreign.desktop"
    foreign.write_bytes(b"foreign desktop")
    parse = builder._parse_desktop_exec_text

    def substitute(text):
        old.unlink()
        if replacement == "symlink":
            old.symlink_to(foreign)
        else:
            old.write_bytes(b"unrelated replacement")
        return parse(text)

    monkeypatch.setattr(builder, "_parse_desktop_exec_text", substitute)
    builder.remove_conflicting_menu_entries(
        spec, applications, applications / "current.desktop"
    )
    assert os.path.lexists(old)
    assert foreign.read_bytes() == b"foreign desktop"
    if replacement == "file":
        assert old.read_bytes() == b"unrelated replacement"
