"""Uninstaller targets and privilege boundaries; no real package/system actions."""

import json
import os
from pathlib import Path
import shlex
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/netmon_uninstall_menu.sh"


def run_shell(body, *, env=None, script=SCRIPT):
    clean = {
        key: value for key, value in os.environ.items() if not key.startswith("SUDO_")
    }
    clean.update(env or {})
    return subprocess.run(
        ["/bin/bash", "-p", "-c", 'source "$1"\n' + body, "fixture", str(script)],
        env=clean,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


@pytest.fixture
def account(tmp_path):
    home = tmp_path / "home with spaces"
    home.mkdir()
    return home


def passwd_view(home):
    # Functions are explicit test doubles, not inherited environment functions.
    return r"""
getent() {
  [[ "$1" == passwd && ( "$2" == 1234 || "$2" == synthetic ) ]] || return 1
  printf 'synthetic:x:1234:1234:Test:%s:/bin/false\n' "$FIXTURE_HOME"
}
""" + f"FIXTURE_HOME={shlex.quote(str(home))}\n"


@pytest.mark.parametrize("override", ["other-package", "--purge", "netmon dark", ""])
def test_package_override_cannot_change_apt_target(override):
    result = run_shell(
        """
dpkg() { [[ "$*" == '-s netmon' ]]; }
apt-get() { printf 'apt %s\n' "$*"; }
purge_netmon_package
""",
        env={"NETMON_PACKAGE": override},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["apt remove -y netmon"]


def test_package_constant_cannot_be_reassigned_after_loading():
    result = run_shell("NETMON_PACKAGE=other\npurge_netmon_package")
    assert result.returncode != 0
    assert "readonly" in result.stderr


def test_home_and_documents_overrides_are_ignored(account, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    result = run_shell(
        passwd_view(account) + "target_home\ncollect_document_root_dirs",
        env={
            "SUDO_USER": "synthetic",
            "SUDO_UID": "1234",
            "HOME": str(outside),
            "XDG_DOCUMENTS_DIR": str(outside),
        },
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        str(account),
        str(account / "Documents"),
        str(account / "Dokumente"),
    ]


@pytest.mark.parametrize(
    "identity",
    [
        {"SUDO_USER": "synthetic"},
        {"SUDO_UID": "1234"},
        {"SUDO_UID": "not-an-id", "SUDO_USER": "synthetic"},
        {"SUDO_UID": "1234", "SUDO_USER": "different"},
        {"SUDO_UID": "9999", "SUDO_USER": "synthetic"},
    ],
)
def test_inconsistent_identity_never_uses_home_fallback(account, identity):
    result = run_shell(passwd_view(account) + "target_home", env=identity)
    assert result.returncode != 0
    assert result.stdout == ""


@pytest.mark.parametrize("kind", ["root", "relative", "missing", "symlink", "newline"])
def test_unsafe_passwd_home_is_rejected(account, tmp_path, kind):
    path = {
        "root": "/",
        "relative": "relative/home",
        "missing": str(tmp_path / "missing"),
        "symlink": str(tmp_path / "link"),
        "newline": str(account) + "\nother",
    }[kind]
    if kind == "symlink":
        Path(path).symlink_to(account, target_is_directory=True)
    result = run_shell(
        passwd_view(path) + "target_home",
        env={"SUDO_UID": "1234", "SUDO_USER": "synthetic"},
    )
    assert result.returncode != 0
    assert result.stdout == ""


def test_preview_shows_exact_targets_without_deleting(account):
    target = account / ".cache/netmon"
    target.mkdir(parents=True)
    sentinel = target / "keep"
    sentinel.write_bytes(b"unchanged")
    result = run_shell(
        passwd_view(account) + "run_user_cleanup preview remove_user_data ja",
        env={"SUDO_USER": "synthetic", "SUDO_UID": "1234"},
    )
    assert result.returncode == 0, result.stderr
    assert str(target) in result.stdout
    assert str(account / "Documents/NetMon") in result.stdout
    assert sentinel.read_bytes() == b"unchanged"


@pytest.mark.parametrize("component", ["Documents", ".cache", ".local", "target"])
def test_user_cleanup_refuses_symlink_escape(account, tmp_path, component):
    outside = tmp_path / "outside"
    sentinel = outside / "netmon/keep"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"unchanged")
    if component == "target":
        (account / ".cache").mkdir()
        (account / ".cache/netmon").symlink_to(
            outside / "netmon", target_is_directory=True
        )
    else:
        (account / component).symlink_to(outside, target_is_directory=True)
    result = run_shell(
        passwd_view(account) + "run_user_cleanup execute remove_user_data nein",
        env={"SUDO_USER": "synthetic", "SUDO_UID": "1234"},
    )
    assert result.returncode != 0
    assert "Unsicheres Benutzerziel" in result.stderr
    assert sentinel.read_bytes() == b"unchanged"


@pytest.mark.parametrize("mode", ["preview", "execute"])
def test_root_dispatch_drops_privileges_and_discards_environment(
    account, tmp_path, mode
):
    calls = tmp_path / "calls.json"
    fake = tmp_path / "fake-runuser"
    fake.write_text(
        "#!/usr/bin/python3\nimport json,sys\n"
        f'open({str(calls)!r}, "w").write(json.dumps(sys.argv[1:]))\n'
    )
    fake.chmod(0o700)
    copy = tmp_path / "uninstaller.sh"
    copy.write_text(SCRIPT.read_text().replace("/usr/sbin/runuser", str(fake)))
    result = run_shell(
        passwd_view(account) + """
is_root() { return 0; }
id() { [[ "$1" == -u ]] && printf '1234\n'; }
run_user_cleanup """ + mode + " remove_user_data ja",
        script=copy,
        env={
            "SUDO_USER": "synthetic",
            "SUDO_UID": "1234",
            "XDG_DOCUMENTS_DIR": "/outside",
        },
    )
    assert result.returncode == 0, result.stderr
    args = json.loads(calls.read_text())
    assert args[:6] == [
        "-u",
        "synthetic",
        "--",
        "/usr/bin/env",
        "-i",
        "PATH=/usr/sbin:/usr/bin:/sbin:/bin",
    ]
    assert "HOME=" + str(account) in args
    assert args[-7:] == [
        "/bin/bash",
        "-p",
        "/usr/bin/netmon-uninstall",
        "--user-cleanup",
        mode,
        "remove_user_data",
        "ja",
    ]
    assert not any("XDG_DOCUMENTS_DIR" in value for value in args)


def test_elevation_bootstrap_does_not_preserve_caller_targets(account, tmp_path):
    # Execute the actual fixed bootstrap at the test UID, replacing only the
    # final installed script with an environment recorder. No sudo is invoked.
    source = SCRIPT.read_text()
    bootstrap = source.split("exec /usr/bin/sudo -- /bin/bash -p -c '\n", 1)[1].split(
        "\n' netmon-uninstall", 1
    )[0]
    recorder = tmp_path / "recorder.sh"
    recorder.write_text(
        "/usr/bin/python3 -I -c 'import json,os; print(json.dumps(dict(os.environ)))'\n"
    )
    bootstrap = bootstrap.replace("/usr/bin/netmon-uninstall", str(recorder))
    env = dict(
        os.environ,
        HOME="/outside",
        NETMON_PACKAGE="other",
        XDG_DOCUMENTS_DIR="/outside",
        SUDO_USER="synthetic",
        SUDO_UID="1234",
        PYTHONPATH="/outside",
    )
    result = subprocess.run(
        ["/bin/bash", "-p", "-c", bootstrap, "fixture"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    received = json.loads(result.stdout)
    assert received["SUDO_USER"] == "synthetic"
    assert received["SUDO_UID"] == "1234"
    assert not set(received) & {
        "HOME",
        "XDG_DOCUMENTS_DIR",
        "NETMON_PACKAGE",
        "PYTHONPATH",
    }
    assert received["PATH"] == "/usr/sbin:/usr/bin:/sbin:/bin"


@pytest.mark.parametrize(
    "operation", ["reset_ufw", "purge_netmon_package", "main", "unknown"]
)
def test_private_user_entry_cannot_run_system_operations(operation):
    result = run_shell(
        "reset_ufw() { printf UNSAFE; }\n"
        "purge_netmon_package() { printf UNSAFE; }\n"
        f"main --user-cleanup execute {operation}"
    )
    assert result.returncode != 0
    assert "UNSAFE" not in result.stdout


def test_summary_lists_package_account_and_requested_targets(account):
    result = run_shell(
        passwd_view(account)
        + "print_summary ja ja nein nein nein nein nein nein nein nein",
        env={"SUDO_USER": "synthetic", "SUDO_UID": "1234", "NETMON_PACKAGE": "other"},
    )
    assert result.returncode == 0, result.stderr
    assert "Paket / package: netmon" in result.stdout
    assert "Benutzer / user: synthetic" in result.stdout
    assert "Home: " + str(account) in result.stdout
    assert str(account / ".local/share/applications/netmon.desktop") in result.stdout
    assert "other" not in result.stdout


@pytest.mark.parametrize("unsafe", [False, True])
def test_menu_previews_targets_before_confirmation_and_stops_on_unsafe_paths(
    account, tmp_path, unsafe
):
    cache = account / ".cache/netmon"
    cache.mkdir(parents=True)
    sentinel = cache / "keep"
    sentinel.write_bytes(b"unchanged")
    if unsafe:
        outside = tmp_path / "outside"
        outside.mkdir()
        (account / "Documents").symlink_to(outside, target_is_directory=True)
    body = passwd_view(account) + """
ensure_root() { :; }
detect_netmon_language() { NETMON_LANG_CODE=en; }
check_firewall_transaction() { return 0; }
pause_before_exit() { :; }
ensure_netmon_not_running() { printf UNSAFE; }
purge_netmon_package() { printf UNSAFE; }
main
"""
    env = dict(os.environ, SUDO_USER="synthetic", SUDO_UID="1234")
    result = subprocess.run(
        ["/bin/bash", "-p", "-c", 'source "$1"\n' + body, "fixture", str(SCRIPT)],
        input="y\ny\ny\nn\ny\nn\nn\nn\nn\nn\n",
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert "UNSAFE" not in result.stdout
    assert sentinel.read_bytes() == b"unchanged"
    if unsafe:
        assert result.returncode != 0
        assert "Start execution now?" not in result.stdout
    else:
        assert result.returncode == 0, result.stderr
        assert result.stdout.index(str(cache)) < result.stdout.index(
            "Start execution now?"
        )
        assert "Canceled." in result.stdout


@pytest.mark.parametrize(
    "operation",
    [
        "remove_user_launchers",
        "remove_user_data",
        "remove_secure_browsers",
        "remove_netmon_wireguard_artifacts",
    ],
)
def test_checked_user_cleanup_always_passes_through_privilege_drop(operation):
    result = run_shell(
        "check_firewall_transaction() { return 0; }\n"
        'run_user_cleanup() { printf "%s\\n" "$*"; }\n'
        + f"run_checked_cleanup {operation}"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "execute " + operation


def test_root_cannot_use_private_user_cleanup_entry():
    result = run_shell(
        "is_root() { return 0; }\n"
        "remove_user_data() { printf UNSAFE; }\n"
        "main --user-cleanup execute remove_user_data"
    )
    assert result.returncode != 0
    assert "UNSAFE" not in result.stdout


def test_hostile_path_and_shell_startup_are_not_used(tmp_path):
    commands = tmp_path / "commands"
    commands.mkdir()
    marker = tmp_path / "executed"
    for name in ("id", "getent", "realpath"):
        canary = commands / name
        canary.write_text(f"#!/bin/sh\nprintf executed > {shlex.quote(str(marker))}\n")
        canary.chmod(0o700)
    startup = tmp_path / "startup"
    startup.write_text(f"printf executed > {shlex.quote(str(marker))}\n")
    result = run_shell(
        "target_home",
        env={"PATH": str(commands), "BASH_ENV": str(startup), "HOME": "/outside"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() != "/outside"
    assert not marker.exists()
