"""Real signed backups and hostile tar members through both public restore paths."""

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile

import pytest

from scripts import dev_lab_backup as helper

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
STAMP = "2026-10-17-123600"


def run_script(name, *args, input=None):
    return subprocess.run(
        ["bash", str(SCRIPTS / name), *map(str, args)],
        input=input,
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


@pytest.fixture(scope="session")
def backup_keys(tmp_path_factory):
    if shutil.which("minisign") is None:
        pytest.skip("minisign is required for real authenticated backup tests")
    directory = tmp_path_factory.mktemp("backup-trust-anchor")
    key, public = directory / "backup.key", directory / "backup.pub"
    subprocess.run(
        ["minisign", "-G", "-W", "-s", str(key), "-p", str(public)],
        capture_output=True,
        check=True,
    )
    return key, public


@pytest.fixture
def layout(tmp_path):
    project, home = tmp_path / "project", tmp_path / "home"
    values = {
        project / "README.md": b"project data\n",
        project / "AGENTS.md": b"trusted instructions\n",
        project / ".vscode/settings.json": b"{}\n",
        home / ".vscode-server/data/Machine/settings.json": b"machine settings\n",
        home / ".vscode-server/data/User/settings.json": b"user settings\n",
        home / ".codex/config.toml": b"model = 'test'\n",
        home / ".bashrc": b"# trusted shell settings\n",
        home / ".profile": b"# trusted profile\n",
    }
    for path, value in values.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    (project / "empty").mkdir()
    return project, home, values


def location_args(layout):
    project, home, _ = layout
    return ["--project-root", project, "--home-root", home]


@pytest.fixture
def valid_backup(tmp_path, layout, backup_keys):
    secret, public = backup_keys
    output = tmp_path / "backups"
    result = run_script(
        "backup_dev_lab.sh",
        "--output-dir",
        output,
        "--signing-key",
        secret,
        *location_args(layout),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    (backup,) = output.iterdir()
    return backup, public


def restore_args(backup, public, layout, target=None):
    args = [
        "--backup-dir",
        backup,
        "--trusted-public-key",
        public,
        *location_args(layout),
    ]
    if target is not None:
        args.extend(["--restore-root", target])
    return args


def sign_manifest(backup, secret, manifest):
    path = backup / "manifest.json"
    path.write_text(json.dumps(manifest))
    signature = backup / "manifest.json.minisig"
    subprocess.run(
        ["minisign", "-S", "-s", str(secret), "-m", str(path), "-x", str(signature)],
        capture_output=True,
        check=True,
    )


def forged_backup(tmp_path, backup_keys, archives):
    """Sign even hostile inventories: a valid signature must not waive path policy."""
    backup = tmp_path / "crafted"
    backup.mkdir()
    inventory = []
    for category, members in archives:
        archive = backup / f"{helper.PREFIXES[category]}-{STAMP}.tar.gz"
        records = []
        with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as output:
            for item, data, declared in members:
                output.addfile(item, io.BytesIO(data) if data else None)
                records.append(
                    declared
                    or {
                        "path": item.name.rstrip("/") if item.isdir() else item.name,
                        "type": "directory" if item.isdir() else "file",
                        "size": item.size,
                        "sha256": (
                            None if item.isdir() else hashlib.sha256(data).hexdigest()
                        ),
                        "mode": 0o700 if item.isdir() else 0o600 | (item.mode & 0o100),
                    }
                )
        payload = archive.read_bytes()
        inventory.append(
            {
                "name": archive.name,
                "category": category,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "members": records,
            }
        )
    sign_manifest(
        backup, backup_keys[0], {"format": helper.FORMAT, "archives": inventory}
    )
    return backup, backup_keys[1]


def tar_file(name, data=b"attacker data\n", **kwargs):
    item = tarfile.TarInfo(name)
    item.mode = 0o644
    item.size = len(data)
    for key, value in kwargs.items():
        setattr(item, key, value)
    return item, data, None


def allowed_file(category, layout):
    project, home, _ = layout
    return (
        {
            "project": project / "payload",
            "vscode": project / ".vscode/payload",
            "configs": home / ".codex/payload",
        }[category]
        .relative_to("/")
        .as_posix()
    )


@pytest.mark.parametrize("category", ["project", "vscode", "configs"])
@pytest.mark.parametrize("full", [False, True], ids=["selective", "full"])
@pytest.mark.parametrize("dry_run", [False, True], ids=["restore", "dry-run"])
def test_cron_payload_is_rejected_for_every_category_and_flow(
    tmp_path, layout, backup_keys, category, full, dry_run
):
    backup, public = forged_backup(
        tmp_path, backup_keys, [(category, [tar_file("etc/cron.d/payload")])]
    )
    target = tmp_path / "restore"
    args = restore_args(backup, public, layout, target)
    if dry_run:
        args.append("--dry-run")
    script = (
        "restore_dev_lab_backup.sh" if full else "restore_selected_dev_lab_backup.sh"
    )
    result = run_script(script, *args, *([] if full else [f"--{category}"]))

    assert result.returncode == 2
    assert "nicht erlaubt" in result.stderr
    assert not target.exists()


@pytest.mark.parametrize(
    "name",
    [
        "/etc/cron.d/payload",
        "../outside",
        "etc/../payload",
        "a//b",
        "./payload",
        "a\\b",
        "a\nb",
    ],
)
@pytest.mark.parametrize("full", [False, True])
def test_absolute_traversal_and_ambiguous_paths_fail_closed(
    tmp_path, layout, backup_keys, name, full
):
    backup, public = forged_backup(
        tmp_path, backup_keys, [("project", [tar_file(name)])]
    )
    target = tmp_path / "restore"
    script = (
        "restore_dev_lab_backup.sh" if full else "restore_selected_dev_lab_backup.sh"
    )
    result = run_script(
        script,
        *restore_args(backup, public, layout, target),
        *([] if full else ["--project"]),
    )

    assert result.returncode == 2
    assert not target.exists()


@pytest.mark.parametrize(
    "kind",
    [
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
        tarfile.FIFOTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
    ],
)
@pytest.mark.parametrize("category", ["project", "vscode", "configs"])
@pytest.mark.parametrize("full", [False, True])
def test_allowed_names_cannot_authorize_links_or_special_files(
    tmp_path, layout, backup_keys, kind, category, full
):
    name = allowed_file(category, layout)
    item, _, _ = tar_file(name, b"", type=kind, linkname="/etc/cron.d/payload")
    # Lie in the signed inventory; inspect the actual tar type independently.
    declared = {
        "path": name,
        "type": "file",
        "size": 0,
        "sha256": hashlib.sha256(b"").hexdigest(),
        "mode": 0o600,
    }
    backup, public = forged_backup(
        tmp_path, backup_keys, [(category, [(item, b"", declared)])]
    )
    target = tmp_path / "restore"
    script = (
        "restore_dev_lab_backup.sh" if full else "restore_selected_dev_lab_backup.sh"
    )
    result = run_script(
        script,
        *restore_args(backup, public, layout, target),
        *([] if full else [f"--{category}"]),
    )

    assert result.returncode == 2
    assert "verboten" in result.stderr
    assert not target.exists()


def test_valid_full_backup_restores_exact_files_and_empty_directories(
    tmp_path, layout, valid_backup
):
    backup, public = valid_backup
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout, target)
    )

    assert result.returncode == 0, result.stdout + result.stderr
    expected = {
        path.relative_to("/").as_posix(): value for path, value in layout[2].items()
    }
    actual = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    }
    assert actual == expected
    assert (target / (layout[0] / "empty").relative_to("/")).is_dir()
    assert stat.S_IMODE(target.stat().st_mode) == 0o700
    assert all(
        stat.S_IMODE(path.stat().st_mode) == 0o600
        for path in target.rglob("*")
        if path.is_file()
    )


@pytest.mark.parametrize(
    "categories", [("project",), ("vscode",), ("configs",), ("vscode", "configs")]
)
def test_selective_restore_writes_only_selected_category_paths(
    tmp_path, layout, valid_backup, categories
):
    backup, public = valid_backup
    target = tmp_path / "restore"
    result = run_script(
        "restore_selected_dev_lab_backup.sh",
        *restore_args(backup, public, layout, target),
        *[f"--{name}" for name in categories],
    )

    assert result.returncode == 0, result.stdout + result.stderr
    rules = helper.policy(layout[0], layout[1])
    for path in target.rglob("*"):
        if path.is_file():
            name = path.relative_to(target).as_posix()
            assert any(
                any(
                    name == source.relative_to("/").as_posix()
                    or (
                        subtree
                        and name.startswith(source.relative_to("/").as_posix() + "/")
                    )
                    for source, subtree in rules[category]
                )
                for category in categories
            )
            assert path.read_bytes() == (Path("/") / name).read_bytes()


def test_default_restore_creates_private_target_instead_of_using_original_paths(
    layout, valid_backup
):
    backup, public = valid_backup
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout)
    )

    assert result.returncode == 0, result.stdout + result.stderr
    target = Path(result.stdout.strip().split("Restore abgeschlossen. Ziel: ")[-1])
    try:
        assert target.name.startswith("dev-lab-restore-")
        assert target != Path("/")
        assert stat.S_IMODE(target.stat().st_mode) == 0o700
        assert all(path.read_bytes() == value for path, value in layout[2].items())
    finally:
        shutil.rmtree(target)


def test_valid_dry_run_authenticates_everything_without_creating_target(
    tmp_path, layout, valid_backup
):
    backup, public = valid_backup
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh",
        *restore_args(backup, public, layout, target),
        "--dry-run",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "keine Zieldateien" in result.stdout
    assert not target.exists()


@pytest.mark.parametrize(
    "damage",
    [
        "manifest",
        "signature",
        "missing-manifest",
        "missing-signature",
        "archive",
        "extra-archive",
    ],
)
def test_unauthenticated_or_substituted_backups_never_touch_target(
    tmp_path, layout, valid_backup, damage
):
    backup, public = valid_backup
    if damage == "manifest":
        (backup / "manifest.json").write_bytes(b"{}")
    elif damage == "signature":
        (backup / "manifest.json.minisig").write_bytes(b"broken")
    elif damage.startswith("missing-"):
        (
            backup
            / (
                "manifest.json"
                if damage == "missing-manifest"
                else "manifest.json.minisig"
            )
        ).unlink()
    elif damage == "archive":
        archive = next(backup.glob("*.tar.gz"))
        archive.write_bytes(b"substituted tarball")
    else:
        (backup / "other.tar.gz").write_bytes(b"unknown")
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout, target)
    )

    assert result.returncode == 2
    assert not target.exists()


def test_key_shipped_inside_backup_is_not_a_trust_anchor(
    tmp_path, layout, valid_backup
):
    backup, public = valid_backup
    supplied_key = backup / "backup.pub"
    shutil.copyfile(public, supplied_key)
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, supplied_key, layout, target)
    )

    assert result.returncode == 2
    assert "ausserhalb" in result.stderr
    assert not target.exists()


@pytest.mark.parametrize(
    "unsafe", ["root-symlink", "ancestor-symlink", "file-symlink", "file-hardlink"]
)
@pytest.mark.parametrize("dry_run", [False, True])
def test_preexisting_links_cannot_redirect_writes(
    tmp_path, layout, valid_backup, unsafe, dry_run
):
    backup, public = valid_backup
    target, outside = tmp_path / "restore", tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_bytes(b"unchanged")
    if unsafe == "root-symlink":
        target.symlink_to(outside, target_is_directory=True)
    else:
        target.mkdir()
        destination = target / (layout[0] / "README.md").relative_to("/")
        destination.parent.mkdir(parents=True)
        if unsafe == "ancestor-symlink":
            destination.parent.rmdir()
            destination.parent.symlink_to(outside, target_is_directory=True)
        elif unsafe == "file-symlink":
            destination.symlink_to(sentinel)
        else:
            os.link(sentinel, destination)
    result = run_script(
        "restore_dev_lab_backup.sh",
        *restore_args(backup, public, layout, target),
        *(["--dry-run"] if dry_run else []),
    )

    assert result.returncode == 2
    assert sentinel.read_bytes() == b"unchanged"
    assert list(outside.iterdir()) == [sentinel]


def test_all_archives_are_validated_before_overwriting_existing_files(
    tmp_path, layout, backup_keys
):
    good_name = (layout[0] / "README.md").relative_to("/").as_posix()
    bad_name = allowed_file("configs", layout)
    bad, _, _ = tar_file(
        bad_name, b"", type=tarfile.SYMTYPE, linkname="/etc/cron.d/payload"
    )
    backup, public = forged_backup(
        tmp_path,
        backup_keys,
        [("project", [tar_file(good_name)]), ("configs", [(bad, b"", None)])],
    )
    target = tmp_path / "restore"
    existing = target / good_name
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"keep original")
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout, target)
    )

    assert result.returncode == 2
    assert existing.read_bytes() == b"keep original"


@pytest.mark.parametrize("full", [False, True])
def test_slash_target_is_rejected_without_privileged_mode(layout, valid_backup, full):
    backup, public = valid_backup
    script = (
        "restore_dev_lab_backup.sh" if full else "restore_selected_dev_lab_backup.sh"
    )
    result = run_script(
        script,
        *restore_args(backup, public, layout, Path("/")),
        *([] if full else ["--project"]),
    )

    assert result.returncode == 2
    assert "--restore-original-paths" in result.stderr


def test_original_paths_mode_requires_privileged_invocation(
    layout, valid_backup, monkeypatch
):
    backup, public = valid_backup
    monkeypatch.setattr(helper.os, "geteuid", lambda: 1000)
    assert (
        helper.main(
            [
                "restore",
                "--all",
                "--restore-original-paths",
                *map(str, restore_args(backup, public, layout)),
            ]
        )
        == 2
    )


def test_backup_creator_omits_links_and_special_files_and_never_archives_signing_key(
    tmp_path, layout, backup_keys
):
    project, _, _ = layout
    outside = tmp_path / "outside"
    outside.write_bytes(b"not in backup")
    (project / "symlink").symlink_to(outside)
    os.mkfifo(project / "fifo")
    os.link(project / "README.md", project / "hardlink-copy")
    script = project / "script.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o6755)
    secret, _ = backup_keys
    result = run_script(
        "backup_dev_lab.sh",
        "--signing-key",
        secret,
        "--output-dir",
        tmp_path / "backups",
        *location_args(layout),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for path in (tmp_path / "backups").glob("backup-*/*.tar.gz"):
        with tarfile.open(path) as archive:
            members = archive.getmembers()
        assert all(item.isfile() or item.isdir() for item in members)
        assert not any(
            item.name.endswith(("/symlink", "/fifo", "/backup.key")) for item in members
        )
        assert not any(item.mode & 0o7000 for item in members)


def test_key_required_before_backup_output_is_created(tmp_path):
    output = tmp_path / "backups"
    result = run_script("backup_dev_lab.sh", "--output-dir", output)

    assert result.returncode == 2
    assert not output.exists()


def test_legacy_unsigned_backup_is_rejected(tmp_path, layout, backup_keys):
    backup = tmp_path / "legacy"
    backup.mkdir()
    (backup / f"dev-lab-project-{STAMP}.tar.gz").write_bytes(b"untrusted legacy data")
    (backup / f"manifest-{STAMP}.txt").write_text("old informational manifest\n")
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh",
        *restore_args(backup, backup_keys[1], layout, target),
    )

    assert result.returncode == 2
    assert not target.exists()


def test_wrong_independent_public_key_rejects_even_valid_manifest(
    tmp_path, layout, valid_backup
):
    backup, _ = valid_backup
    other_key, other_public = tmp_path / "other.key", tmp_path / "other.pub"
    subprocess.run(
        ["minisign", "-G", "-W", "-s", str(other_key), "-p", str(other_public)],
        capture_output=True,
        check=True,
    )
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh",
        *restore_args(backup, other_public, layout, target),
    )

    assert result.returncode == 2
    assert "Minisign" in result.stderr
    assert not target.exists()


@pytest.mark.parametrize("field", ["path", "size", "sha256", "mode"])
def test_signed_inventory_must_match_actual_regular_files(
    tmp_path, layout, backup_keys, valid_backup, field
):
    backup, public = valid_backup
    manifest = json.loads((backup / "manifest.json").read_text())
    member = next(
        item for item in manifest["archives"][0]["members"] if item["type"] == "file"
    )
    if field == "path":
        member[field] += ".renamed"
    elif field == "size":
        member[field] += 1
    elif field == "sha256":
        member[field] = "0" * 64
    else:
        member[field] = 0o700
    sign_manifest(backup, backup_keys[0], manifest)
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout, target)
    )

    assert result.returncode == 2
    assert "Inventar" in result.stderr
    assert not target.exists()


@pytest.mark.parametrize("replacement", ["symlink", "fifo", "directory"])
def test_archive_input_must_be_regular_file_without_following_links(
    tmp_path, layout, valid_backup, replacement
):
    backup, public = valid_backup
    archive = next(backup.glob("*.tar.gz"))
    original = tmp_path / "original.tar.gz"
    archive.rename(original)
    if replacement == "symlink":
        archive.symlink_to(original)
    elif replacement == "fifo":
        os.mkfifo(archive)
    else:
        archive.mkdir()
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout, target)
    )

    assert result.returncode == 2
    assert not target.exists()


def test_duplicate_tar_members_are_rejected_even_if_manifest_omits_duplicate(
    tmp_path, layout, backup_keys
):
    name = allowed_file("project", layout)
    backup, public = forged_backup(
        tmp_path, backup_keys, [("project", [tar_file(name), tar_file(name)])]
    )
    manifest = json.loads((backup / "manifest.json").read_text())
    manifest["archives"][0]["members"].pop()
    sign_manifest(backup, backup_keys[0], manifest)
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout, target)
    )

    assert result.returncode == 2
    assert "Doppeltes" in result.stderr
    assert not target.exists()


def test_pax_path_override_cannot_escape_category(tmp_path, layout, backup_keys):
    name = allowed_file("project", layout)
    item, data, _ = tar_file(name)
    item.pax_headers = {"path": "etc/cron.d/payload"}
    backup, public = forged_backup(
        tmp_path, backup_keys, [("project", [(item, data, None)])]
    )
    target = tmp_path / "restore"
    result = run_script(
        "restore_dev_lab_backup.sh", *restore_args(backup, public, layout, target)
    )

    assert result.returncode == 2
    assert "nicht erlaubt" in result.stderr
    assert not target.exists()
