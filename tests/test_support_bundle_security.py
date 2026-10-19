"""Synthetic support-export attacks; no real user files or host commands."""

import json
import os
import zipfile

import pytest

from netmon.core import diagnostics
from netmon.core import support_bundle as bundle


def write_private(path, data):
    path.write_bytes(data)
    path.chmod(0o600)


@pytest.fixture
def export_tree(monkeypatch, tmp_path):
    docs = tmp_path / "Documents" / "NetMon"
    reports = docs / "diagnostics"
    logs = docs / "Logs"
    state = tmp_path / "state"
    for directory in (reports, logs, state / "logs", docs / "support"):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    monkeypatch.setattr(bundle, "get_netmon_documents_dir", lambda: str(docs))
    monkeypatch.setattr(bundle, "diagnostic_reports_dir", lambda: str(reports))
    monkeypatch.setattr(diagnostics, "diagnostic_reports_dir", lambda: str(reports))
    monkeypatch.setattr(bundle, "get_netmon_documents_subdir", lambda *_: str(logs))
    monkeypatch.setattr(bundle, "get_netmon_state_dir", lambda: str(state))
    secret = tmp_path / "private.txt"
    write_private(secret, b"SYNTHETIC-PRIVATE-CONTENT")
    return docs, reports, logs, state, secret


def archived_bytes():
    path = bundle.create_support_package()
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


@pytest.mark.parametrize("slot", range(6))
def test_every_candidate_symlink_is_excluded(export_tree, slot):
    _docs, reports, logs, state, secret = export_tree
    paths = [
        reports / "netmon-report.json",
        reports / "startup_error.log",
        reports / "crash.log",
        logs / "runtime.log",
        state / "logs" / "runtime.log",
        state / "logs" / "network_debug.log",
    ]
    paths[slot].symlink_to(secret)
    content = archived_bytes()
    assert not any(secret.read_bytes() in value for value in content.values())
    assert json.loads(content["manifest.json"])["files"] == []


def test_latest_report_ignores_newer_symlink(export_tree):
    _, reports, _, _, secret = export_tree
    legitimate = reports / "netmon-old.json"
    write_private(legitimate, b"{}")
    os.utime(legitimate, (1, 1))
    (reports / "netmon-new.json").symlink_to(secret)
    assert diagnostics.latest_diagnostic_report_path() == str(legitimate)


@pytest.mark.parametrize("directory", ["diagnostics", "Logs", "state-logs", "ancestor"])
def test_directory_symlinks_are_excluded(export_tree, directory, monkeypatch):
    docs, reports, logs, state, secret = export_tree
    external = secret.parent / "external"
    external.mkdir(mode=0o700)
    write_private(external / "crash.log", secret.read_bytes())
    write_private(external / "runtime.log", secret.read_bytes())
    target = {
        "diagnostics": reports,
        "Logs": logs,
        "state-logs": state / "logs",
        "ancestor": docs,
    }[directory]
    target.rename(target.with_name(target.name + "-original"))
    target.symlink_to(external, target_is_directory=True)
    if directory == "ancestor":
        (external / "diagnostics").mkdir(mode=0o700)
        write_private(external / "diagnostics" / "crash.log", secret.read_bytes())
        # Keep output separate: this test targets source-directory traversal.
        output = secret.parent / "output"
        output.mkdir(mode=0o700)
        monkeypatch.setattr(
            bundle, "support_package_path", lambda: str(output / "bundle.zip")
        )
    assert not any(secret.read_bytes() in value for value in archived_bytes().values())


def test_hardlink_is_excluded(export_tree):
    _, reports, _, _, secret = export_tree
    os.link(secret, reports / "crash.log")
    assert not any(secret.read_bytes() in value for value in archived_bytes().values())


@pytest.mark.parametrize("mode", [0o666, 0o620])
def test_writable_by_others_is_excluded(export_tree, mode):
    _, reports, _, _, _ = export_tree
    path = reports / "crash.log"
    write_private(path, b"untrusted")
    path.chmod(mode)
    assert "files/crash.log" not in archived_bytes()


def test_fifo_is_excluded(export_tree):
    _, reports, _, _, _ = export_tree
    os.mkfifo(reports / "crash.log")
    assert "files/crash.log" not in archived_bytes()


def test_swap_after_discovery_cannot_redirect_export(export_tree, monkeypatch):
    _, reports, _, _, secret = export_tree
    path = reports / "crash.log"
    write_private(path, b"safe")
    original = bundle.support_bundle_inputs

    def discover_then_swap():
        candidates = original()
        path.unlink()
        path.symlink_to(secret)
        return candidates

    monkeypatch.setattr(bundle, "support_bundle_inputs", discover_then_swap)
    assert not any(secret.read_bytes() in value for value in archived_bytes().values())


def test_swap_after_manifest_uses_open_descriptor(export_tree, monkeypatch):
    _, reports, _, _, secret = export_tree
    path = reports / "crash.log"
    write_private(path, b"safe")
    original = bundle.build_support_manifest

    def manifest_then_swap(**kwargs):
        manifest = original(**kwargs)
        path.unlink()
        path.symlink_to(secret)
        return manifest

    monkeypatch.setattr(bundle, "build_support_manifest", manifest_then_swap)
    content = archived_bytes()
    assert content["files/crash.log"] == b"safe"


def test_unapproved_path_is_excluded_even_from_discovery(export_tree, monkeypatch):
    *_, secret = export_tree
    monkeypatch.setattr(bundle, "support_bundle_inputs", lambda: [str(secret)])
    assert not any(secret.read_bytes() in value for value in archived_bytes().values())


def test_regular_report_and_log_are_preserved(export_tree):
    _, reports, _, _, _ = export_tree
    write_private(reports / "netmon-good.json", b'{"ok":true}')
    write_private(reports / "crash.log", b"normal log")
    content = archived_bytes()
    assert content["files/netmon-good.json"] == b'{"ok":true}'
    assert content["files/crash.log"] == b"normal log"


@pytest.mark.parametrize("replacement", ["symlink", "fifo", "regular"])
def test_swap_between_stat_and_open_is_rejected(export_tree, monkeypatch, replacement):
    _, reports, _, _, secret = export_tree
    path = reports / "crash.log"
    write_private(path, b"safe")
    real_open = os.open
    swapped = False

    def swap_on_open(name, flags, *args, **kwargs):
        nonlocal swapped
        if name == "crash.log" and not swapped:
            swapped = True
            # Keep the old inode allocated so it cannot be reused by the test.
            path.rename(reports / "old.log")
            if replacement == "symlink":
                path.symlink_to(secret)
            elif replacement == "fifo":
                os.mkfifo(path)
            else:
                write_private(path, secret.read_bytes())
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(bundle.os, "open", swap_on_open)
    with pytest.raises(OSError), bundle._open_support_input(str(path)):
        pytest.fail("Raced-in file was accepted")
    assert swapped


def test_directory_swap_after_stat_keeps_original_directory(export_tree, monkeypatch):
    _, reports, _, _, secret = export_tree
    path = reports / "crash.log"
    write_private(path, b"safe")
    external = secret.parent / "external"
    external.mkdir(mode=0o700)
    write_private(external / "crash.log", secret.read_bytes())
    real_open = os.open

    def swap_on_open(name, flags, *args, **kwargs):
        if name == "crash.log":
            reports.rename(reports.with_name("old-reports"))
            reports.symlink_to(external, target_is_directory=True)
        return real_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(bundle.os, "open", swap_on_open)
    with bundle._open_support_input(str(path)) as source:
        assert source.read() == b"safe"


def test_foreign_owner_is_rejected(export_tree, monkeypatch):
    from types import SimpleNamespace

    _, reports, _, _, _ = export_tree
    path = reports / "crash.log"
    write_private(path, b"foreign")
    real_stat = os.stat

    def foreign_stat(name, *args, **kwargs):
        info = real_stat(name, *args, **kwargs)
        if name == "crash.log":
            return SimpleNamespace(
                st_mode=info.st_mode, st_nlink=1, st_uid=os.geteuid() + 1
            )
        return info

    monkeypatch.setattr(bundle.os, "stat", foreign_stat)
    assert "files/crash.log" not in archived_bytes()


def test_group_writable_directory_is_rejected(export_tree):
    _, reports, _, _, _ = export_tree
    write_private(reports / "crash.log", b"untrusted")
    reports.chmod(0o775)
    assert "files/crash.log" not in archived_bytes()


def test_missing_no_follow_support_fails_closed(export_tree, monkeypatch):
    _, reports, _, _, _ = export_tree
    write_private(reports / "crash.log", b"safe")
    monkeypatch.delattr(bundle.os, "O_NOFOLLOW")
    assert bundle.support_bundle_inputs() == []
    with pytest.raises(OSError, match="no-follow"):
        bundle.create_support_package()


@pytest.mark.parametrize("existing", ["symlink", "regular"])
def test_output_never_overwrites_existing_file(export_tree, monkeypatch, existing):
    docs, _, _, _, secret = export_tree
    output = docs / "support" / "collision.zip"
    if existing == "symlink":
        output.symlink_to(secret)
    else:
        output.write_bytes(b"existing archive")
    monkeypatch.setattr(bundle, "support_package_path", lambda: str(output))
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        bundle.create_support_package()
    assert output.read_bytes() == before
    assert secret.read_bytes() == b"SYNTHETIC-PRIVATE-CONTENT"


def test_zip_output_is_private(export_tree):
    output = bundle.create_support_package()
    assert os.stat(output).st_mode & 0o777 == 0o600


def test_new_output_directory_is_private_with_permissive_umask(
    export_tree, monkeypatch
):
    docs, _, _, _, _ = export_tree
    monkeypatch.setattr(bundle, "get_netmon_documents_dir", lambda: str(docs / "fresh"))
    previous_umask = os.umask(0)
    try:
        output = bundle.create_support_package()
    finally:
        os.umask(previous_umask)
    assert os.stat(os.path.dirname(output)).st_mode & 0o777 == 0o700
    assert os.stat(output).st_mode & 0o777 == 0o600


def test_existing_group_writable_output_directory_is_rejected(export_tree):
    docs, _, _, _, _ = export_tree
    target = docs / "support"
    target.chmod(0o770)
    with pytest.raises(OSError, match="unsafe ownership or permissions"):
        bundle.create_support_package()
    assert target.stat().st_mode & 0o777 == 0o770
    assert list(target.iterdir()) == []


def test_output_directory_symlink_is_rejected(export_tree):
    docs, _, _, _, secret = export_tree
    target = docs / "support"
    target.rename(docs / "original-support")
    external = secret.parent / "output"
    external.mkdir(mode=0o700)
    target.symlink_to(external, target_is_directory=True)
    with pytest.raises(OSError):
        bundle.create_support_package()
    assert target.is_symlink()
    assert list(external.iterdir()) == []
