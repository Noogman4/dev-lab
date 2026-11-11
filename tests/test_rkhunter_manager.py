import os
import stat
from types import SimpleNamespace

import pytest

import netmon.core.rkhunter_manager as rkhunter_manager


@pytest.fixture
def system_paths(monkeypatch):
    """Model system metadata without depending on installed downloaders/root."""
    paths = {
        path: SimpleNamespace(st_uid=0, st_mode=stat.S_IFDIR | 0o755)
        for path in ("/", "/usr", "/usr/bin")
    }
    for path in ("/usr/bin/wget", "/usr/bin/curl"):
        paths[path] = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o755)
    real_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if os.fspath(path) in paths:
            info = paths[os.fspath(path)]
            if isinstance(info, OSError):
                raise info
            return info
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(rkhunter_manager.os, "lstat", fake_lstat)
    return paths


def test_preferred_web_cmd_prefers_wget(system_paths):
    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/wget"


def test_preferred_web_cmd_falls_back_to_curl(system_paths):
    system_paths["/usr/bin/wget"] = FileNotFoundError()
    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/curl"


def test_preferred_web_cmd_rejects_unsafe_wget_and_falls_back(system_paths):
    system_paths["/usr/bin/wget"].st_uid = 1000
    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/curl"


def test_preferred_web_cmd_returns_empty_without_safe_candidates(system_paths):
    system_paths["/usr/bin/wget"] = FileNotFoundError()
    system_paths["/usr/bin/curl"].st_mode |= 0o002
    assert rkhunter_manager._preferred_web_cmd() == ""


@pytest.mark.parametrize("prefix", ["/usr/bin/../..", "/usr/bin/./../..", ""])
def test_real_poisoned_path_cannot_supply_web_cmd(
    monkeypatch, tmp_path, system_paths, prefix
):
    # Reproduce shutil.which preserving a trusted-looking traversal spelling.
    attacker = tmp_path / "attacker-bin"
    attacker.mkdir()
    for name in ("wget", "curl"):
        executable = attacker / name
        executable.write_text("#!/bin/sh\nexit 99\n")
        executable.chmod(0o755)
    path_entry = prefix + str(attacker)
    monkeypatch.setenv("PATH", path_entry)
    assert rkhunter_manager.shutil.which("wget") == path_entry + "/wget"
    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/wget"


@pytest.mark.parametrize("component", ["/", "/usr", "/usr/bin", "/usr/bin/wget"])
@pytest.mark.parametrize(
    "bad", ["owner", "group_write", "world_write", "link", "fifo", "missing", "denied"]
)
def test_trusted_web_cmd_rejects_unsafe_file_or_ancestry(system_paths, component, bad):
    if bad in ("missing", "denied"):
        system_paths[component] = (
            FileNotFoundError() if bad == "missing" else PermissionError()
        )
    elif bad == "owner":
        system_paths[component].st_uid = 1000
    elif bad == "group_write":
        system_paths[component].st_mode |= 0o020
    elif bad == "world_write":
        system_paths[component].st_mode |= 0o002
    else:
        system_paths[component].st_mode = (
            stat.S_IFLNK if bad == "link" else stat.S_IFIFO
        ) | 0o755
    assert not rkhunter_manager._trusted_web_cmd("/usr/bin/wget")


@pytest.mark.parametrize("mode", [stat.S_IFREG | 0o644, stat.S_IFDIR | 0o755])
def test_trusted_web_cmd_requires_executable_regular_file(system_paths, mode):
    system_paths["/usr/bin/wget"].st_mode = mode
    assert not rkhunter_manager._trusted_web_cmd("/usr/bin/wget")


@pytest.mark.parametrize(
    "path",
    [
        "/usr/bin/../../tmp/wget",
        "/usr/bin/./wget",
        "/bin/wget",
        "/usr/local/bin/wget",
        "wget",
        "/usr/bin/wget-extra",
    ],
)
def test_trusted_web_cmd_requires_exact_allowlist(path):
    assert not rkhunter_manager._trusted_web_cmd(path)


def test_no_path_lookup_for_downloader(monkeypatch, system_paths):
    def forbidden_lookup(*args):
        pytest.fail("Downloader selection must not consult PATH")

    monkeypatch.setattr(rkhunter_manager.shutil, "which", forbidden_lookup)
    assert rkhunter_manager._preferred_web_cmd() == "/usr/bin/wget"


def test_repair_without_safe_downloader_does_not_write(monkeypatch, system_paths):
    system_paths["/usr/bin/wget"] = FileNotFoundError()
    system_paths["/usr/bin/curl"] = FileNotFoundError()
    original = "WEB_CMD=/tmp/attacker-bin/wget\nOTHER=keep\n"
    monkeypatch.setattr(rkhunter_manager, "_read_config", lambda path: (0, original))
    writes = []
    monkeypatch.setattr(
        rkhunter_manager, "_write_config", lambda *args: writes.append(args)
    )
    rc, out = rkhunter_manager.repair_config()
    assert rc != 0
    assert "System-Downloader" in out
    assert writes == []


def test_detect_update_failure_matches_invalid_web_cmd_message():
    output = 'Invalid WEB_CMD configuration option: Relative pathname: "/usr/bin/wget"'

    assert rkhunter_manager.detect_update_failure(output) is True


def test_repair_config_content_replaces_targets_and_preserves_other_lines():
    repaired = rkhunter_manager._repair_config_content(
        "UPDATE_MIRRORS=0\n"
        "  MIRRORS_MODE = 1\n"
        "# keep comment\n"
        "WEB_CMD=/bin/false\n"
        "OTHER=keep\n",
        {
            "UPDATE_MIRRORS": "1",
            "MIRRORS_MODE": "0",
            "WEB_CMD": "/usr/bin/wget",
        },
    )

    assert repaired == (
        "UPDATE_MIRRORS=1\n"
        "MIRRORS_MODE=0\n"
        "# keep comment\n"
        "WEB_CMD=/usr/bin/wget\n"
        "OTHER=keep\n"
    )


def test_repair_config_content_appends_missing_targets_in_order():
    repaired = rkhunter_manager._repair_config_content(
        "OTHER=keep\n",
        {
            "UPDATE_MIRRORS": "1",
            "MIRRORS_MODE": "0",
            "WEB_CMD": "/usr/bin/wget",
        },
    )

    assert repaired == (
        "OTHER=keep\n" "UPDATE_MIRRORS=1\n" "MIRRORS_MODE=0\n" "WEB_CMD=/usr/bin/wget\n"
    )


def test_run_rkhunter_propupd_uses_fixed_noninteractive_sudo_command(monkeypatch):
    calls = []

    def fake_run_cmd(args, timeout):
        calls.append((args, timeout))
        if args[:3] == ["sudo", "-n", "cp"]:
            return 0, "backup"
        return 0, "updated"

    monkeypatch.setattr(rkhunter_manager, "_run_cmd", fake_run_cmd)

    assert rkhunter_manager.run_rkhunter_propupd(timeout=90) == (
        0,
        "backup\nupdated",
    )
    assert calls == [
        (
            [
                "sudo",
                "-n",
                "cp",
                "-a",
                "/var/lib/rkhunter/db/rkhunter.dat",
                "/var/lib/rkhunter/db/rkhunter.dat.netmon.bak",
            ],
            20,
        ),
        (["sudo", "-n", "rkhunter", "--propupd"], 90),
    ]


def test_restore_property_database_uses_fixed_allowlisted_paths(monkeypatch):
    calls = []

    def fake_run_cmd(args, timeout):
        calls.append((args, timeout))
        return 0, "restored"

    monkeypatch.setattr(rkhunter_manager, "_run_cmd", fake_run_cmd)

    assert rkhunter_manager.restore_property_database() == (0, "restored")
    assert calls == [
        (
            [
                "sudo",
                "-n",
                "test",
                "-f",
                "/var/lib/rkhunter/db/rkhunter.dat.netmon.bak",
            ],
            10,
        ),
        (
            [
                "sudo",
                "-n",
                "cp",
                "-a",
                "/var/lib/rkhunter/db/rkhunter.dat.netmon.bak",
                "/var/lib/rkhunter/db/rkhunter.dat",
            ],
            20,
        ),
    ]


def test_restore_property_database_reports_missing_netmon_backup(monkeypatch):
    calls = []

    def fake_run_cmd(args, timeout):
        calls.append((args, timeout))
        if args[:3] == ["sudo", "-n", "test"]:
            return 1, ""
        return 0, "restored"

    monkeypatch.setattr(rkhunter_manager, "_run_cmd", fake_run_cmd)

    rc, out = rkhunter_manager.restore_property_database()

    assert rc == 2
    assert "Kein NetMon-Backup" in out
    assert calls == [
        (
            [
                "sudo",
                "-n",
                "test",
                "-f",
                "/var/lib/rkhunter/db/rkhunter.dat.netmon.bak",
            ],
            10,
        )
    ]


def test_repair_config_replaces_invalid_web_cmd(monkeypatch, system_paths):
    written = {}

    monkeypatch.setattr(
        rkhunter_manager,
        "_read_config",
        lambda path: (
            0,
            "UPDATE_MIRRORS=0\nMIRRORS_MODE=1\nWEB_CMD=/bin/false\nOTHER=keep\n",
        ),
    )

    def fake_write(config_text, config_path):
        written["text"] = config_text
        written["path"] = config_path
        return 0, ""

    monkeypatch.setattr(rkhunter_manager, "_write_config", fake_write)

    rc, out = rkhunter_manager.repair_config("/etc/rkhunter.conf")

    assert rc == 0
    assert out == ""
    assert written["path"] == "/etc/rkhunter.conf"
    assert "UPDATE_MIRRORS=1\n" in written["text"]
    assert "MIRRORS_MODE=0\n" in written["text"]
    assert "WEB_CMD=/usr/bin/wget\n" in written["text"]
    assert "OTHER=keep\n" in written["text"]
