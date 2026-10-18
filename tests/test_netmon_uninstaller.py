import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "netmon_uninstall_menu.sh"


def _run_uninstaller_function(function_body, *, home_dir, documents_dir):
    command = f"""
source "$1"
TEST_HOME="$2"
TEST_DOCUMENTS="$3"
target_home() {{ printf '%s\\n' "$TEST_HOME"; }}
collect_document_root_dirs() {{ printf '%s\\n' "$TEST_DOCUMENTS"; }}
{function_body}
"""
    return subprocess.run(
        [
            "bash",
            "-c",
            command,
            "netmon-uninstall-test",
            str(SCRIPT),
            str(home_dir),
            str(documents_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_remove_user_data_preserves_secure_browser_directory(tmp_path):
    home_dir = tmp_path / "home"
    documents_dir = home_dir / "Dokumente"
    secure_dir = documents_dir / "NetMon" / "Secure Browser"
    config_dir = documents_dir / "NetMon" / "Config"
    secure_dir.mkdir(parents=True)
    config_dir.mkdir()
    (secure_dir / "keep.txt").write_text("keep", encoding="utf-8")
    (config_dir / "remove.txt").write_text("remove", encoding="utf-8")

    result = _run_uninstaller_function(
        "remove_user_data ja",
        home_dir=home_dir,
        documents_dir=documents_dir,
    )

    assert result.returncode == 0, result.stderr
    assert (secure_dir / "keep.txt").is_file()
    assert not config_dir.exists()


def test_remove_secure_browsers_removes_document_storage_and_menu_entry(tmp_path):
    home_dir = tmp_path / "home"
    documents_dir = home_dir / "Dokumente"
    secure_dir = documents_dir / "NetMon" / "Secure Browser"
    secure_dir.mkdir(parents=True)
    unrelated = home_dir / "Programme" / "firefox-personal"
    unrelated.mkdir(parents=True)
    app_dir = home_dir / ".local" / "share" / "applications"
    app_dir.mkdir(parents=True)
    menu_entry = app_dir / "netmon-secure-browser-test.desktop"
    menu_entry.write_text(
        "[Desktop Entry]\nName=Test\nComment=NetMon Secure Browser fuer Test\n",
        encoding="utf-8",
    )

    result = _run_uninstaller_function(
        "remove_secure_browsers",
        home_dir=home_dir,
        documents_dir=documents_dir,
    )

    assert result.returncode == 0, result.stderr
    assert not secure_dir.exists()
    assert unrelated.is_dir()
    assert not menu_entry.exists()


def test_forged_user_state_cannot_select_nm_deletions(tmp_path, monkeypatch):
    import json

    home = tmp_path / "home"
    config = home / ".config" / "netmon"
    config.mkdir(parents=True)
    identity = "11111111-2222-4333-8444-555555555555"
    (config / "netmon_vpn_slots.json").write_text(
        json.dumps(
            [
                {
                    "profile": "foreign-work",
                    "uuid": identity,
                    "owner": "netmon-wireguard-created-v1",
                }
            ]
        )
    )
    (config / "netmon_privacy.json").write_text(
        json.dumps(
            {
                "nm_last_import": {
                    "connections": ["foreign-work"],
                    "owned_connections": [{"uuid": identity, "receipt_id": "f" * 32}],
                }
            }
        )
    )
    calls = tmp_path / "calls"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_nm = bin_dir / "nmcli"
    fake_nm.write_text(
        f'#!/bin/sh\nprintf "NM %s\\n" "$*" >> "{calls}"\nprintf "foreign-work:wireguard\\n"\n'
    )
    fake_nm.chmod(0o700)
    fake_python = bin_dir / "fake-python"
    fake_python.write_text(f'#!/bin/sh\nprintf "PROTECTED-CLEANUP\\n" >> "{calls}"\n')
    fake_python.chmod(0o700)
    # Test-only script copy: intercept the fixed privileged interpreter. Never
    # invoke an installed helper (even if the test host has NetMon installed).
    script = tmp_path / "uninstaller.sh"
    script.write_text(
        SCRIPT.read_text().replace("/usr/bin/python3 -I -c", f'"{fake_python}" -I -c')
    )
    monkeypatch.setattr(__import__(__name__, fromlist=["SCRIPT"]), "SCRIPT", script)
    monkeypatch.setenv("PATH", str(bin_dir) + ":/usr/bin:/bin")
    result = _run_uninstaller_function(
        "remove_netmon_nm_connections", home_dir=home, documents_dir=home / "Documents"
    )
    assert result.returncode == 0, result.stderr
    assert calls.read_text() == "PROTECTED-CLEANUP\n"


def test_user_wireguard_cleanup_preserves_all_system_profiles(tmp_path):
    home = tmp_path / "home"
    config = home / ".config" / "netmon"
    config.mkdir(parents=True)
    (config / "netmon_vpn_slots.json").write_text('[{"profile":"foreign-work"}]')
    system = tmp_path / "etc-wireguard"
    system.mkdir()
    profile = system / "foreign-work.conf"
    profile.write_text("keep")
    result = _run_uninstaller_function(
        f'NETMON_WIREGUARD_ROOT="{system}"\nremove_netmon_wireguard_artifacts',
        home_dir=home,
        documents_dir=home / "Documents",
    )
    assert result.returncode == 0, result.stderr
    assert profile.read_text() == "keep"
    assert not (config / "netmon_vpn_slots.json").exists()


def test_main_cleanup_disabled_and_cancel_preserve_nm_and_other_removal(tmp_path):
    # Override every effectful function; exercise real prompts/control flow only.
    command = """
source "$1"
ensure_root() { :; }
detect_netmon_language() { NETMON_LANG_CODE=en; }
ensure_netmon_not_running() { :; }
pause_before_exit() { :; }
remove_netmon_nm_connections() { printf 'NM-CLEANUP\\n'; }
purge_netmon_package() { printf 'PACKAGE-REMOVED\\n'; }
main
"""
    for execute, expect_package in [("y", True), ("n", False)]:
        answers = ["y", "n", "n", "n", "n", "n", "n", "n", "n", "n", execute]
        result = subprocess.run(
            ["bash", "-c", command, "test", str(SCRIPT)],
            input="\n".join(answers) + "\n",
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "NM-CLEANUP" not in result.stdout
        assert ("PACKAGE-REMOVED" in result.stdout) == expect_package


def test_privileged_launcher_validates_before_exec(monkeypatch, capsys):
    import os
    from pathlib import Path
    import stat
    import sys
    from io import StringIO
    from types import SimpleNamespace

    source = SCRIPT.read_text()
    launcher = source.split("if /usr/bin/python3 -I -c '\n", 1)[1].split(
        "\n'; then", 1
    )[0]
    # Execute the actual guard with a synthetic filesystem view. Neither the
    # interpreter nor a privileged installed script is executed by this test.
    launcher = launcher.replace("from pathlib import Path", "")
    helper = "/usr/lib/netmon/netmon/core/nm_ownership.py"
    for damage in [
        None,
        "helper_symlink",
        "parent_symlink",
        "owner",
        "writable",
        "hardlink",
        "missing",
    ]:
        calls = []

        class FakePath:
            def __init__(self, path):
                self.path = str(path)

            @property
            def parents(self):
                return [FakePath(p) for p in Path(self.path).parents]

            def __eq__(self, other):
                return self.path == other.path

            def __str__(self):
                return self.path

            def lstat(self):
                is_file = self.path == helper
                mode = (stat.S_IFREG | 0o644) if is_file else (stat.S_IFDIR | 0o755)
                if (damage == "helper_symlink" and is_file) or (
                    damage == "parent_symlink" and self.path == "/usr/lib/netmon"
                ):
                    mode = stat.S_IFLNK | 0o777
                if damage == "writable" and is_file:
                    mode |= 0o020
                if damage == "missing" and is_file:
                    raise FileNotFoundError()
                return SimpleNamespace(
                    st_uid=1000 if damage == "owner" and is_file else 0,
                    st_mode=mode,
                    st_nlink=2 if damage == "hardlink" and is_file else 1,
                )

        monkeypatch.setattr(
            os, "execv", lambda executable, args: calls.append((executable, args))
        )
        monkeypatch.setattr(sys, "stdin", StringIO("yes\n"))
        if damage is None:
            exec(compile(launcher, "synthetic-launcher", "exec"), {"Path": FakePath})
            assert calls == [
                ("/usr/bin/python3", ["/usr/bin/python3", "-I", helper, "cleanup"])
            ]
            assert sys.stdin.readline() == "yes\n"
        else:
            try:
                exec(
                    compile(launcher, "synthetic-launcher", "exec"), {"Path": FakePath}
                )
            except SystemExit as result:
                assert result.code == 0
            assert not calls
            assert "retained" in capsys.readouterr().out
