"""Passive package lifecycle with synthetic legacy state and private GUI settings."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(
    os.environ.get("NETMON_REINSTALL_TEST_ROOT", Path(__file__).resolve().parents[1])
)
PHASES = [
    ("postinst", "configure"),
    ("postinst", "abort-upgrade"),
    ("prerm", "remove"),
    ("prerm", "deconfigure"),
    ("prerm", "upgrade"),
    ("prerm", "failed-upgrade"),
]
UUID = "12345678-1234-5678-9012-123456789abc"


def _state_manifest(root):
    """Compare bytes, links and metadata without opening special/link targets."""
    result = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for path in [Path(base), *(Path(base) / name for name in dirs + files)]:
            info = path.lstat()
            content = None
            if stat.S_ISLNK(info.st_mode):
                content = os.readlink(path)
            elif stat.S_ISREG(info.st_mode):
                try:
                    content = hashlib.sha256(path.read_bytes()).hexdigest()
                except PermissionError:
                    content = "unreadable"
            result[str(path.relative_to(root))] = (
                info.st_ino,
                info.st_mode,
                info.st_uid,
                info.st_gid,
                info.st_nlink,
                info.st_mtime_ns,
                info.st_ctime_ns,
                content,
            )
    return result


@pytest.fixture(params=PHASES, ids=["-".join(p) for p in PHASES])
def lifecycle(request, tmp_path):
    phase, argument = request.param
    source = (ROOT / "scripts/build_netmon_deb.sh").read_text()
    match = re.search(
        rf'^cat > "\$PKG_DIR/DEBIAN/{phase}" <<\'EOF\'\n(.*?)^EOF$',
        source,
        re.M | re.S,
    )
    assert match
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    snapshot = state / "install-dns-nm.state"
    snapshot.write_text(f"{UUID}|192.0.2.53|no\n")
    snapshot.chmod(0o600)
    (state / "unrelated-state").write_bytes(b"preserve unrelated state")
    for name in ("skel", "assets"):
        (tmp_path / name).mkdir()
    text = (
        match[1]
        .replace("/var/lib/netmon", str(state))
        .replace("/etc/skel", str(tmp_path / "skel"))
        .replace("/usr/share/netmon/assets/log-pics", str(tmp_path / "assets"))
    )
    script = tmp_path / phase
    script.write_text(text)
    commands = tmp_path / "commands"
    commands.mkdir()
    calls = tmp_path / "calls"
    for command in (
        "nmcli",
        "resolvectl",
        "systemctl",
        "ufw",
        "ip",
        "nft",
        "sudo",
        "service",
        "wg",
        "wg-quick",
        "update-desktop-database",
    ):
        fake = commands / command
        fake.write_text(
            f'#!/bin/sh\nprintf "%s %s\\n" "{command}" "$*" >> "$TEST_CALLS"\nexit 0\n'
        )
        fake.chmod(0o700)
    for tool in ("mkdir", "find", "basename", "cp"):
        (commands / tool).symlink_to(Path("/usr/bin") / tool)

    def run():
        before = calls.read_text().splitlines() if calls.exists() else []
        result = subprocess.run(
            ["/bin/sh", str(script), argument],
            capture_output=True,
            text=True,
            timeout=3,
            env=dict(os.environ, PATH=str(commands), TEST_CALLS=str(calls)),
        )
        recorded = calls.read_text().splitlines() if calls.exists() else []
        return result, recorded[len(before) :]

    return SimpleNamespace(
        run=run,
        snapshot=snapshot,
        state=state,
        tmp=tmp_path,
        fake_nmcli=commands / "nmcli",
        phase=phase,
    )


def _assert_passive_success(case, before):
    result, calls = case.run()
    assert result.returncode == 0, result.stderr
    assert calls == (
        ["update-desktop-database /usr/share/applications"]
        if case.phase == "postinst"
        else []
    )
    assert _state_manifest(case.state) == before


@pytest.mark.parametrize(
    "contents",
    [
        f"{UUID}|192.0.2.53|no\n".encode(),
        f"{UUID}|192.0.2.53|yes\n".encode(),
        f"{UUID}||\n".encode(),
        f"{UUID}|192.0.2.53|no".encode(),
        b"",
        b"not a recovery record",
        b"|192.0.2.1|yes\n",
        f"{UUID}|192.0.2.1|yes|extra\n".encode(),
        f"{UUID}|192.0.2.1|yes\n{UUID}|192.0.2.2|no\n".encode(),
        b"legacy\x00state\xff\r\n",
        b"x" * 65537,
    ],
    ids=[
        "auto-dns-no",
        "auto-dns-yes",
        "empty-fields",
        "no-final-lf",
        "empty",
        "invalid-record",
        "missing-uuid",
        "extra-fields",
        "duplicate-uuid",
        "binary",
        "large",
    ],
)
def test_legacy_state_is_preserved_without_interpretation(lifecycle, contents):
    lifecycle.snapshot.write_bytes(contents)
    _assert_passive_success(lifecycle, _state_manifest(lifecycle.state))


def test_missing_legacy_state_remains_absent(lifecycle):
    lifecycle.snapshot.unlink()
    _assert_passive_success(lifecycle, _state_manifest(lifecycle.state))


def test_package_lifecycle_needs_no_nmcli(lifecycle):
    lifecycle.fake_nmcli.rename(lifecycle.tmp / "disabled-nmcli")
    _assert_passive_success(lifecycle, _state_manifest(lifecycle.state))


@pytest.mark.parametrize(
    "kind", ["symlink", "dangling", "hardlink", "fifo", "directory", "unreadable"]
)
def test_legacy_path_types_are_untouched(lifecycle, kind):
    path = lifecycle.snapshot
    path.unlink()
    victim = lifecycle.tmp / "outside-state"
    victim.write_bytes(b"private external sentinel")
    if kind == "symlink":
        path.symlink_to(victim)
    elif kind == "dangling":
        path.symlink_to(lifecycle.tmp / "missing-target")
    elif kind == "hardlink":
        os.link(victim, path)
    elif kind == "fifo":
        os.mkfifo(path, 0o600)
    elif kind == "directory":
        path.mkdir()
        (path / "sentinel").write_bytes(b"keep")
    else:
        path.write_bytes(b"unreadable legacy state")
        path.chmod(0)
    victim_info = victim.stat()
    _assert_passive_success(lifecycle, _state_manifest(lifecycle.state))
    assert victim.read_bytes() == b"private external sentinel"
    assert victim.stat().st_ino == victim_info.st_ino
    assert victim.stat().st_ctime_ns == victim_info.st_ctime_ns
    if kind == "unreadable":
        path.chmod(0o600)
        assert path.read_bytes() == b"unreadable legacy state"


def test_package_lifecycle_does_not_wait_for_legacy_directory_lock(lifecycle):
    before = _state_manifest(lifecycle.state)
    descriptor = os.open(lifecycle.state, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        _assert_passive_success(lifecycle, before)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def test_repeated_package_callbacks_leave_legacy_state_unchanged(lifecycle):
    before = _state_manifest(lifecycle.state)
    _assert_passive_success(lifecycle, before)
    _assert_passive_success(lifecycle, before)


@pytest.mark.parametrize(
    "lifecycle", [("prerm", "remove"), ("prerm", "deconfigure")], indirect=True
)
@pytest.mark.parametrize("receipt", ["regular", "symlink"])
def test_refused_removal_preserves_dns_and_firewall_state(lifecycle, receipt):
    folder = lifecycle.state / "ufw-snapshot"
    folder.mkdir()
    path = folder / "state.json"
    victim = lifecycle.tmp / "firewall-receipt"
    victim.write_bytes(b"{}")
    if receipt == "symlink":
        path.symlink_to(victim)
    else:
        path.write_bytes(b"{}")
    before = _state_manifest(lifecycle.state)
    result, calls = lifecycle.run()
    assert result.returncode == 1
    assert "Firewall-Transaktion" in result.stderr
    assert calls == []
    assert _state_manifest(lifecycle.state) == before
    assert victim.read_bytes() == b"{}"


@pytest.mark.parametrize("lifecycle", [("postinst", "configure")], indirect=True)
def test_postinst_with_firewall_receipt_keeps_dns_unchanged(lifecycle):
    receipt = lifecycle.state / "ufw-snapshot"
    receipt.mkdir()
    (receipt / "state.json").write_bytes(b"{}")
    _assert_passive_success(lifecycle, _state_manifest(lifecycle.state))


GUI_DRIVER = r"""
import json, os
from pathlib import Path
from netmon.app import App
from netmon.main import _temporary_app_smoke_patches, _cancel_pending_after_callbacks
home = Path(os.environ['HOME'])
config = home / 'Documents/NetMon/Config'
settings = config / 'config.json'
privacy = config / 'netmon_privacy.json'
before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in (settings, privacy)}
with _temporary_app_smoke_patches(App):
    app = App()
    try:
        app.update_idletasks()
        app.update()
        assert app._app_theme['name'] == os.environ['EXPECTED_THEME'], app._app_theme['name']
        for path, (content, mtime) in before.items():
            if path == settings and os.environ.get('NEW_FIRST_SEEN'):
                saved = json.loads(path.read_text())
                assert saved['donation_popup_first_seen_at'] > 0
                for key, value in json.loads(content).items():
                    assert saved[key] == value, key
                continue
            assert path.read_bytes() == content, f'startup rewrote {path.name}'
            assert path.stat().st_mtime_ns == mtime, f'startup persisted {path.name}'
        if os.environ.get('SWITCH_THEME'):
            app.select_theme(os.environ['SWITCH_THEME'])
            assert app._app_theme['name'] == os.environ['SWITCH_THEME']
            assert json.loads(privacy.read_text())['theme'] == os.environ['SWITCH_THEME']
            assert json.loads(settings.read_text())['theme'] == os.environ['SWITCH_THEME']
            assert json.loads(privacy.read_text())['custom_privacy_marker'] == 'keep'
            assert not json.loads(privacy.read_text())['autostart']
    finally:
        _cancel_pending_after_callbacks(app)
        app.tk.call("destroy", ".")
"""


@pytest.mark.parametrize(
    "settings_theme,privacy_theme,expected,switch",
    [
        ("dark", "dark", "dark", "light"),
        ("light", "light", "light", "dark"),
        ("beige", "beige", "beige", "pop"),
        (None, None, "dark", ""),
        ("dark", None, "dark", ""),
        (None, "dark", "dark", ""),
        ("light", "dark", "dark", ""),
        ("dark", "light", "light", ""),
        ("invalid", "invalid", "light", ""),
        (None, {"invalid": True}, "light", ""),
    ],
)
def test_retained_gui_preferences_are_read_only_until_explicit_change(
    tmp_path, settings_theme, privacy_theme, expected, switch
):
    home = tmp_path / "home"
    config = home / "Documents/NetMon/Config"
    config.mkdir(parents=True)
    settings = {
        "language": "de",
        "custom_preservation_marker": "keep",
        "donation_popup_first_seen_at": 1000,
    }
    privacy = {
        "enabled": False,
        "autostart": False,
        "dns_guard_enabled": False,
        "log_overlay_active": True,
        "log_overlay_image_path": "",
        "custom_privacy_marker": "keep",
    }
    if settings_theme is not None:
        settings["theme"] = settings_theme
    if privacy_theme is not None:
        privacy["theme"] = privacy_theme
    (config / "config.json").write_text(json.dumps(settings))
    (config / "netmon_privacy.json").write_text(json.dumps(privacy))
    env = dict(
        os.environ,
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / ".config"),
        XDG_STATE_HOME=str(home / ".local/state"),
        XDG_CACHE_HOME=str(home / ".cache"),
        EXPECTED_THEME=expected,
        SWITCH_THEME=switch,
        PYTHONPATH=str(ROOT),
    )
    result = subprocess.run(
        [sys.executable, "-B", "-c", GUI_DRIVER],
        cwd=home,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_first_seen_initialization_is_saved_once_after_preferences_load(
    tmp_path, theme
):
    home = tmp_path / "home"
    config = home / "Documents/NetMon/Config"
    config.mkdir(parents=True)
    (config / "config.json").write_text(json.dumps({"theme": theme, "language": "de"}))
    (config / "netmon_privacy.json").write_text(
        json.dumps({"theme": theme, "enabled": False, "autostart": False})
    )
    env = dict(
        os.environ,
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / ".config"),
        XDG_STATE_HOME=str(home / ".local/state"),
        XDG_CACHE_HOME=str(home / ".cache"),
        EXPECTED_THEME=theme,
        NEW_FIRST_SEEN="1",
        SWITCH_THEME="",
        PYTHONPATH=str(ROOT),
    )
    for first_launch in (True, False):
        if not first_launch:
            env.pop("NEW_FIRST_SEEN")
        result = subprocess.run(
            [sys.executable, "-B", "-c", GUI_DRIVER],
            cwd=home,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
