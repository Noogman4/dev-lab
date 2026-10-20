"""Execute generated backup.sh under hostile permissions and destination layouts."""

import os
from pathlib import Path
import stat
import subprocess
import tarfile

import pytest

from tools.secure_browser_manager import browser_container_builder as builder


@pytest.fixture
def container(tmp_path):
    root = tmp_path / "container with spaces"
    root.mkdir(mode=0o755)
    (root / "profile").mkdir()
    (root / "profile" / "cookies.sqlite").write_bytes(b"private session")
    for name in (
        "user.js",
        "policies.json",
        "README.md",
        "launcher.desktop",
        "start.sh",
    ):
        (root / name).write_text(name)
    spec = builder.ContainerSpec("firefox-Test", root, ["example.invalid"], None)
    (root / "backup.sh").write_text(builder.build_backup_script(spec))
    return root


def run_backup(root, mask=0o022):
    return subprocess.run(
        ["bash", str(root / "backup.sh")],
        check=False,
        capture_output=True,
        text=True,
        umask=mask,
        timeout=15,
    )


@pytest.mark.parametrize("mask", [0o000, 0o022, 0o077, 0o777])
@pytest.mark.parametrize("existing", [False, True])
def test_backup_private_and_complete(container, mask, existing):
    if existing:
        (container / "backups").mkdir(mode=0o755)
        (container / "backups").chmod(0o755)
    result = run_backup(container, mask)
    assert result.returncode == 0, result.stderr
    backups = container / "backups"
    assert stat.S_IMODE(backups.stat().st_mode) == 0o700
    archives = list(backups.glob("*/*.tar.gz"))
    assert len(archives) == 1
    archive = archives[0]
    assert stat.S_IMODE(archive.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(archive.stat().st_mode) == 0o600
    assert list(archive.parent.iterdir()) == [archive]
    with tarfile.open(archive) as saved:
        assert saved.extractfile("profile/cookies.sqlite").read() == b"private session"
        assert "start.sh" in saved.getnames()


@pytest.mark.parametrize("kind", ["symlink", "dangling", "file", "writable"])
def test_backup_rejects_unsafe_destination(container, tmp_path, kind):
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_bytes(b"unchanged")
    target = container / "backups"
    if kind in ("symlink", "dangling"):
        target.symlink_to(outside if kind == "symlink" else outside / "missing")
    elif kind == "file":
        target.write_bytes(b"unchanged")
    else:
        target.mkdir()
        target.chmod(0o777)
    before = outside.stat().st_mode
    result = run_backup(container)
    assert result.returncode != 0
    assert sentinel.read_bytes() == b"unchanged"
    assert outside.stat().st_mode == before
    assert list(outside.iterdir()) == [sentinel]


def test_backup_rejects_writable_container(container):
    container.chmod(0o777)
    assert run_backup(container).returncode != 0
    assert not (container / "backups").exists()


def test_failed_tar_leaves_no_partial_archive(container):
    (container / "README.md").unlink()
    result = run_backup(container)
    assert result.returncode != 0
    assert "Backup erstellt:" not in result.stdout
    assert not list((container / "backups").glob("*/*"))


def test_repeated_backups_do_not_overwrite(container):
    assert run_backup(container).returncode == 0
    first = next((container / "backups").glob("*/*.tar.gz"))
    before = first.read_bytes()
    assert run_backup(container).returncode == 0
    assert len(list((container / "backups").glob("*/*.tar.gz"))) == 2
    assert first.read_bytes() == before


@pytest.mark.parametrize("mask", [0o000, 0o002, 0o022, 0o027, 0o077])
def test_new_container_and_profile_private(tmp_path, monkeypatch, mask):
    source = tmp_path / "source"
    source.mkdir()
    (source / "firefox").write_text("binary")
    root = tmp_path / "container"
    spec = builder.ContainerSpec("firefox-Test", root, ["example.invalid"], source)
    monkeypatch.setattr(
        builder, "prepare_container_icon", lambda spec: ("firefox", None)
    )
    previous = os.umask(mask)
    try:
        launcher = builder.create_container(spec, tmp_path / "applications")
    finally:
        os.umask(previous)
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "profile").stat().st_mode) == 0o700
    assert (root / "profile" / "user.js").is_file()
    assert (root / "backup.sh").is_file()
    assert launcher.is_file()


@pytest.mark.parametrize("mask", [0o200, 0o700, 0o777])
def test_creation_preserves_restrictive_owner_umask(tmp_path, mask):
    source = tmp_path / "source"
    source.mkdir()
    (source / "firefox").write_text("synthetic binary")
    root = tmp_path / "container"
    spec = builder.ContainerSpec("firefox-Test", root, ["example.invalid"], source)
    previous = os.umask(mask)
    try:
        with pytest.raises(PermissionError):
            builder.create_container(spec, tmp_path / "applications")
        assert stat.S_IMODE(root.stat().st_mode) == 0o700 & ~mask
        assert not (tmp_path / "applications").exists()
    finally:
        os.umask(previous)
        # Restore only this private fixture so pytest can remove it afterwards.
        root.chmod(0o700)


@pytest.mark.parametrize("stage", ["root", "profile"])
def test_creation_does_not_chmod_replaced_directory(tmp_path, monkeypatch, stage):
    source = tmp_path / "source"
    source.mkdir()
    (source / "firefox").write_text("synthetic non-executable browser")
    shared = tmp_path / "shared-parent"
    shared.mkdir(mode=0o777)
    shared.chmod(0o777)
    root = shared / "container"
    victim = tmp_path / "unrelated-owned-directory"
    victim.mkdir()
    victim.chmod(0o750)
    (victim / "firefox").mkdir()
    sentinel = victim / "sentinel"
    sentinel.write_bytes(b"must remain unchanged")
    real_mkdir = Path.mkdir
    selected = root if stage == "root" else root / "profile"
    swapped = []

    def mkdir(path, *args, **kwargs):
        result = real_mkdir(path, *args, **kwargs)
        if path == selected and not swapped:
            swapped.append(True)
            path.rename(path.with_name(path.name + "-original"))
            path.symlink_to(victim, target_is_directory=True)
        return result

    monkeypatch.setattr(Path, "mkdir", mkdir)
    spec = builder.ContainerSpec("firefox-Test", root, ["example.invalid"], source)
    with pytest.raises((OSError, ValueError)):
        builder.create_container(spec, tmp_path / "applications")
    assert swapped == [True]
    assert sentinel.read_bytes() == b"must remain unchanged"
    assert stat.S_IMODE(victim.stat().st_mode) == 0o750


def test_planted_archive_symlink_is_not_followed(container, tmp_path, monkeypatch):
    victim = tmp_path / "victim"
    victim.write_bytes(b"private sentinel")
    victim.chmod(0o640)
    commands = tmp_path / "commands"
    commands.mkdir()
    tar = commands / "tar"
    tar.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "stamp = os.listdir('backups')[0]\n"
        f"os.symlink({str(victim)!r}, 'backups/' + stamp + "
        "'/firefox-Test_profile_backup.tar.gz')\n"
        "os.write(1, b'archive bytes')\n"
    )
    tar.chmod(0o700)
    monkeypatch.setenv("PATH", str(commands) + os.pathsep + os.environ["PATH"])
    result = run_backup(container)
    assert result.returncode != 0
    assert "Backup erstellt:" not in result.stdout
    assert victim.read_bytes() == b"private sentinel"
    assert stat.S_IMODE(victim.stat().st_mode) == 0o640
    assert not list((container / "backups").glob("*/.profile-*"))


def test_archive_stays_on_open_directory_after_replacement(
    container, tmp_path, monkeypatch
):
    outside = tmp_path / "outside"
    outside.mkdir()
    commands = tmp_path / "commands"
    commands.mkdir()
    tar = commands / "tar"
    tar.write_text(
        "#!/usr/bin/env python3\n"
        "import os\n"
        "stamp = os.listdir('backups')[0]\n"
        "os.rename('backups/' + stamp, 'backups/moved')\n"
        f"os.symlink({str(outside)!r}, 'backups/' + stamp)\n"
        "os.write(1, b'archive bytes')\n"
    )
    tar.chmod(0o700)
    monkeypatch.setenv("PATH", str(commands) + os.pathsep + os.environ["PATH"])
    result = run_backup(container)
    assert result.returncode == 0, result.stderr
    assert list(outside.iterdir()) == []
    archive = container / "backups/moved/firefox-Test_profile_backup.tar.gz"
    assert archive.read_bytes() == b"archive bytes"
    assert stat.S_IMODE(archive.stat().st_mode) == 0o600
