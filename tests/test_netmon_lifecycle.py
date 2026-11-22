"""Local lifecycle fixtures; apt, privilege changes and host cleanup stay mocked."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

import pytest

from netmon.core import lifecycle, user_backup

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/netmon_uninstall_menu.sh"


def shell(body, *, inputs="", env=None, script=SCRIPT):
    clean = {k: v for k, v in os.environ.items() if not k.startswith("SUDO_")}
    clean.update(env or {})
    return subprocess.run(
        ["/bin/bash", "-p", "-c", 'source "$1"\n' + body, "fixture", str(script)],
        input=inputs,
        env=clean,
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.fixture
def profile(tmp_path, monkeypatch):
    home = tmp_path / "home with spaces"
    config = home / ".config"
    config.mkdir(mode=0o700, parents=True)
    documents = home / "Meine Unterlagen"
    source = documents / "NetMon"
    (source / "Config").mkdir(mode=0o700, parents=True)
    (source / "Config/config.json").write_text('{"language":"de","fixture":"kept"}')
    (source / "WireGuard").mkdir(mode=0o700)
    (source / "WireGuard/fixture.conf").write_text("synthetic profile")
    (config / "user-dirs.dirs").write_text(
        'XDG_DOCUMENTS_DIR="$HOME/Meine Unterlagen"\n'
    )
    monkeypatch.setenv("HOME", str(home))
    return home, documents, source


def test_saved_xdg_setting_ignores_environment_and_exports_verified_full_backup(
    profile, monkeypatch
):
    home, documents, source = profile
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", "/untrusted/environment")
    monkeypatch.setenv("XDG_CONFIG_HOME", "/untrusted/config")
    assert lifecycle.document_root() == documents
    receipt = lifecycle.backup_for_update(documents / "NetMon-Sicherungen")
    plan = user_backup.preview_restore(receipt["backup"], home / "new-install/NetMon")
    assert plan.kind == "full"
    assert receipt["files_verified"] == 2
    assert receipt["manifest_sha256"] == plan.manifest_sha256
    assert (
        source / "Config/config.json"
    ).read_text() == '{"language":"de","fixture":"kept"}'
    assert os.environ["XDG_DOCUMENTS_DIR"] == "/untrusted/environment"


def test_update_rejected_when_exported_payload_cannot_be_verified(profile, monkeypatch):
    _, documents, source = profile
    export = user_backup.export_backup

    def damage(*args, **kwargs):
        backup = export(*args, **kwargs)
        (backup / "NetMon/Config/config.json").write_text('{"damaged":true}')
        return backup

    monkeypatch.setattr(user_backup, "export_backup", damage)
    with pytest.raises(user_backup.BackupError, match="Prüfsumme"):
        lifecycle.backup_for_update(documents / "NetMon-Sicherungen")
    assert json.loads((source / "Config/config.json").read_text())["fixture"] == "kept"


def test_no_backup_directory_is_created_inside_active_data(profile):
    _, _, source = profile
    parent = source / "must-not-be-created"
    with pytest.raises(ValueError, match="ausserhalb"):
        lifecycle.backup_for_update(parent)
    assert not parent.exists()


def test_backup_parent_redirect_cannot_create_a_folder_in_active_profile(profile):
    home, _, source = profile
    alias = home / "redirect"
    alias.symlink_to(source, target_is_directory=True)
    with pytest.raises(OSError):
        lifecycle.backup_for_update(alias / "must-not-be-created")
    assert not (source / "must-not-be-created").exists()


@pytest.mark.parametrize(
    "entry,expected",
    [
        ("1\n", "update"),
        ("2\n", "keep"),
        ("\n", "keep"),
        ("3\n", "delete"),
        ("0\n", "cancel"),
        ("", "cancel"),
    ],
)
def test_operation_selection_and_eof(entry, expected):
    result = shell("select_operation", inputs=entry)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


@pytest.mark.parametrize("position", range(5))
def test_keep_mode_rejects_each_conflicting_data_deletion(position):
    choices = ["nein"] * 5
    choices[position] = "ja"
    result = shell("validate_uninstall_choices keep " + " ".join(choices))
    assert result.returncode != 0
    assert "Widersprüchliche Auswahl" in result.stderr


def test_keep_mode_never_offers_or_executes_profile_deletion(profile):
    home, _, source = profile
    body = f"""
target_home() {{ printf '%s\\n' {shlex.quote(str(home))}; }}
ensure_root() {{ :; }}
detect_netmon_language() {{ NETMON_LANG_CODE=en; }}
check_firewall_transaction() {{ return 0; }}
ensure_netmon_not_running() {{ :; }}
pause_before_exit() {{ :; }}
purge_netmon_package() {{ printf 'PACKAGE-REMOVED\\n'; }}
run_checked_cleanup() {{ [[ "$1" == purge_netmon_package ]] || {{ printf FORBIDDEN; return 90; }}; "$@"; }}
main
"""
    result = shell(body, inputs="2\ny\nn\nn\nn\ny\n")
    assert result.returncode == 0, result.stderr
    assert "PACKAGE-REMOVED" in result.stdout and "FORBIDDEN" not in result.stdout
    assert "Also uninstall installed Secure Browsers?" not in result.stdout
    assert "Clean up user VPN" not in result.stdout
    assert (source / "WireGuard/fixture.conf").read_text() == "synthetic profile"
    assert json.loads((source / "Config/config.json").read_text())["fixture"] == "kept"


@pytest.mark.parametrize("mode", ["keep", "delete"])
def test_management_preselection_keeps_final_confirmation(profile, mode):
    home, _, source = profile
    body = f"""
target_home() {{ printf '%s\\n' {shlex.quote(str(home))}; }}
ensure_root() {{ [[ "$*" == '--mode {mode}' ]]; }}
detect_netmon_language() {{ NETMON_LANG_CODE=en; }}
check_firewall_transaction() {{ return 0; }}
pause_before_exit() {{ :; }}
select_operation() {{ printf 'UNEXPECTED-MENU' >&2; return 90; }}
run_checked_cleanup() {{ printf 'UNEXPECTED-CLEANUP' >&2; return 90; }}
main --mode {mode}
"""
    # Decline every prompt, including the final confirmation. Even delete mode
    # must leave all fixtures intact and must not offer the mode menu again.
    result = shell(body, inputs="n\n" * 12)
    assert result.returncode == 0, result.stderr
    assert "UNEXPECTED" not in result.stdout + result.stderr
    assert "Start execution now?" in result.stdout
    assert ("Also uninstall installed Secure Browsers?" in result.stdout) == (
        mode == "delete"
    )
    assert (source / "WireGuard/fixture.conf").read_text() == "synthetic profile"
    assert json.loads((source / "Config/config.json").read_text())["fixture"] == "kept"


@pytest.mark.parametrize(
    "arguments", ["--mode update", "--mode", "--mode delete extra", "--unknown"]
)
def test_invalid_management_preselection_stops_before_privilege_request(arguments):
    result = shell(
        "ensure_root() { printf 'UNEXPECTED-PRIVILEGE'; return 90; }\nmain " + arguments
    )
    assert result.returncode != 0
    assert "UNEXPECTED" not in result.stdout + result.stderr


def test_custom_documents_cleanup_is_unprivileged_and_preserves_external_backup(
    profile,
):
    home, documents, source = profile
    backup = documents / "NetMon-Sicherungen/backup/keep"
    backup.parent.mkdir(parents=True)
    backup.write_text("backup")
    body = f"""
target_home() {{ printf '%s\\n' {shlex.quote(str(home))}; }}
run_user_lifecycle() {{ printf '%s\\n' {shlex.quote(str(documents))}; }}
run_user_cleanup execute remove_user_data nein
"""
    result = shell(body)
    assert result.returncode == 0, result.stderr
    assert not source.exists()
    assert backup.read_text() == "backup"


def test_external_documents_are_reported_and_retained(profile, tmp_path):
    home, _, _ = profile
    outside = tmp_path / "external-documents"
    (outside / "NetMon").mkdir(parents=True)
    marker = outside / "NetMon/keep"
    marker.write_text("keep")
    result = shell(
        f"""
target_home() {{ printf '%s\\n' {shlex.quote(str(home))}; }}
run_user_lifecycle() {{ printf '%s\\n' {shlex.quote(str(outside))}; }}
run_user_cleanup execute remove_user_data nein
"""
    )
    assert result.returncode == 0, result.stderr
    assert "manuell prüfen" in result.stderr
    assert marker.read_text() == "keep"


@pytest.fixture
def deb(tmp_path):
    package = tmp_path / "package/DEBIAN"
    package.mkdir(parents=True)
    package.chmod(0o755)
    (package / "control").write_text(
        "Package: netmon\nVersion: 99.0\nArchitecture: all\n"
        "Maintainer: Synthetic <fixture@example.invalid>\nDescription: synthetic fixture\n"
    )
    archive = tmp_path / "new version.deb"
    subprocess.run(
        ["dpkg-deb", "--build", str(package.parent), str(archive)],
        check=True,
        capture_output=True,
    )
    return archive


@pytest.mark.parametrize(
    "scenario",
    [
        "success",
        "backup-failed",
        "cancel",
        "wrong-package",
        "not-newer",
        "wrong-architecture",
        "apt-failed",
    ],
)
def test_update_uses_snapshot_backup_first_and_never_uninstalls(
    profile, deb, tmp_path, scenario
):
    home, documents, _ = profile
    staging = tmp_path / "staging"
    staging.mkdir()
    calls = tmp_path / "calls"
    body = f"""
ensure_netmon_not_running() {{ :; }}
check_firewall_transaction() {{ return 0; }}
mktemp() {{ /usr/bin/mktemp -d {shlex.quote(str(staging))}/update.XXXXXXXX; }}
dpkg-query() {{
  if [[ "$*" == *Status* ]]; then printf 'install ok installed'; else printf '1.0'; fi
}}
dpkg-deb() {{
  if [[ "$3" == Package && "$SCENARIO" == wrong-package ]]; then printf foreign; return; fi
  if [[ "$3" == Version && "$SCENARIO" == not-newer ]]; then printf '0.5'; return; fi
  if [[ "$3" == Architecture && "$SCENARIO" == wrong-architecture ]]; then printf 'unsupported-fixture'; return; fi
  /usr/bin/dpkg-deb "$@"
}}
run_user_lifecycle() {{
  if [[ "$1" == documents ]]; then printf '%s\\n' {shlex.quote(str(documents))}; return; fi
  printf 'BACKUP\\n' >> {shlex.quote(str(calls))}
  [[ "$SCENARIO" != backup-failed ]] || return 1
  /usr/bin/env -i HOME={shlex.quote(str(home))} PATH=/usr/bin:/bin TMPDIR=/tmp PYTHONPATH={shlex.quote(str(ROOT))} /usr/bin/python3 -m netmon.core.lifecycle "$@"
}}
apt-get() {{
  printf 'APT %s\\n' "$*" >> {shlex.quote(str(calls))}
  [[ "$*" == '--no-remove install --no-install-recommends '* ]] || return 92
  [[ "$SCENARIO" != apt-failed ]] || return 93
  /usr/bin/cmp -- {shlex.quote(str(deb))} "${{@: -1}}"
}}
run_checked_cleanup() {{ printf FORBIDDEN; return 94; }}
purge_netmon_package() {{ printf FORBIDDEN; return 94; }}
perform_update
"""
    answer = "n" if scenario == "cancel" else "y"
    result = shell(body, inputs=f"{deb}\n\n{answer}\n", env={"SCENARIO": scenario})
    content = calls.read_text() if calls.exists() else ""
    assert "FORBIDDEN" not in result.stdout
    assert not list(staging.iterdir())
    if scenario in {"success", "apt-failed"}:
        assert content.startswith(
            "BACKUP\nAPT --no-remove install --no-install-recommends "
        )
        assert "netmon.deb" in content
        assert result.returncode == (0 if scenario == "success" else 93), result.stderr
        assert list(
            (documents / "NetMon-Sicherungen").glob(
                "*/netmon_documents_backup_manifest.json"
            )
        )
    else:
        assert "APT" not in content
        assert result.returncode == (0 if scenario == "cancel" else 1), result.stderr


def test_package_snapshot_preserves_bytes_and_refuses_symlinks(deb, tmp_path):
    copy = tmp_path / "snapshot.deb"
    result = shell(
        f"stage_update_package {shlex.quote(str(deb))} {shlex.quote(str(copy))}"
    )
    assert result.returncode == 0, result.stderr
    assert copy.read_bytes() == deb.read_bytes()
    assert result.stdout.strip() == hashlib.sha256(deb.read_bytes()).hexdigest()
    link = tmp_path / "link.deb"
    link.symlink_to(deb)
    result = shell(
        f"stage_update_package {shlex.quote(str(link))} {shlex.quote(str(tmp_path / 'must-not-exist'))}"
    )
    assert result.returncode != 0
    assert not (tmp_path / "must-not-exist").exists()


def test_lifecycle_backup_launcher_drops_privileges_and_clears_environment(
    profile, tmp_path
):
    home, documents, _ = profile
    recorder = tmp_path / "record-runuser"
    recorder.write_text(
        "#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n"
    )
    recorder.chmod(0o700)
    script = tmp_path / "uninstaller.sh"
    script.write_text(SCRIPT.read_text().replace("/usr/sbin/runuser", str(recorder)))
    body = f"""
target_user() {{ printf synthetic; }}
target_home() {{ printf '%s\\n' {shlex.quote(str(home))}; }}
is_root() {{ return 0; }}
id() {{ printf 1234; }}
run_user_lifecycle backup --parent {shlex.quote(str(documents / 'NetMon-Sicherungen'))}
"""
    result = shell(
        body,
        env={"XDG_DOCUMENTS_DIR": "/outside", "PYTHONPATH": "/outside"},
        script=script,
    )
    assert result.returncode == 0, result.stderr
    args = json.loads(result.stdout)
    assert args[:5] == ["-u", "synthetic", "--", "/usr/bin/env", "-i"]
    assert "HOME=" + str(home) in args
    assert "/usr/bin/python3" in args and "-I" in args
    assert args[-3:] == ["backup", "--parent", str(documents / "NetMon-Sicherungen")]
    assert not any("XDG_" in a or "PYTHONPATH=" in a for a in args)


@pytest.mark.parametrize(
    "command",
    [
        "/usr/bin/python3 -m netmon",
        "/usr/bin/python3.12 -m netmon.main",
        "python3 /dev-lab/projects/dev-lab/netmon/app.py",
        "/usr/bin/python3 /usr/lib/netmon/netmon/main.py",
        "/usr/bin/python3 /usr/lib/netmon/netmon_radio_app.py",
    ],
)
def test_running_app_detection_includes_installed_and_development_launches(command):
    result = shell(
        f"""
ps() {{ return 0; }}
pgrep() {{ printf '%s\\n' {shlex.quote('900001 ' + command)} | grep -E -- "$2"; }}
find_running_netmon_processes || true
"""
    )
    assert result.returncode == 0, result.stderr
    assert command in result.stdout


@pytest.mark.parametrize("kind", ["empty", "directory", "fifo"])
def test_package_snapshot_refuses_special_or_empty_input(tmp_path, kind):
    source = tmp_path / "source"
    if kind == "empty":
        source.touch()
    elif kind == "directory":
        source.mkdir()
    else:
        os.mkfifo(source)
    target = tmp_path / "snapshot.deb"
    result = shell(
        f"stage_update_package {shlex.quote(str(source))} {shlex.quote(str(target))}"
    )
    assert result.returncode != 0
    assert not target.exists()
