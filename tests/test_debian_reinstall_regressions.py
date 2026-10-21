"""Reinstall recovery with synthetic NetworkManager and private GUI settings."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(
    os.environ.get("NETMON_REINSTALL_TEST_ROOT", Path(__file__).resolve().parents[1])
)


@pytest.fixture(params=["postinst", "prerm"])
def lifecycle(request, tmp_path):
    source = (ROOT / "scripts/build_netmon_deb.sh").read_text()
    match = re.search(
        rf'^cat > "\$PKG_DIR/DEBIAN/{request.param}" <<\'EOF\'\n(.*?)^EOF$',
        source,
        re.M | re.S,
    )
    assert match
    state = tmp_path / "state"
    state.mkdir()
    snapshot = state / "install-dns-nm.state"
    contents = "11111111-1111-4111-8111-111111111111|192.0.2.53|yes\n22222222-2222-4222-8222-222222222222||\n"
    snapshot.write_text(contents)
    text = match[1].replace('"/var/lib/netmon"', f'"{state}"')
    text = text.replace('"/etc/skel"', f'"{tmp_path / "skel"}"')
    text = text.replace(
        '"/usr/share/netmon/assets/log-pics"', f'"{tmp_path / "no-assets"}"'
    )
    script = tmp_path / request.param
    script.write_text(text)
    commands = tmp_path / "commands"
    commands.mkdir()
    fake = commands / "nmcli"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json,os,sys\n"
        "with open(os.environ['CALLS'],'a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')\n"
        "from pathlib import Path\n"
        "state = Path(os.environ['RECOVERY_STATE'])\n"
        "if os.environ.get('CLEANUP_FAILURE'): state.parent.chmod(0o500)\n"
        "marker = Path(os.environ['MUTATION_MARKER'])\n"
        "if os.environ.get('MUTATE') and not marker.exists():\n"
        "    payload = bytes.fromhex(os.environ['MUTATE'])\n"
        "    if os.environ.get('REPLACE_STATE'):\n"
        "        changed = state.with_name('replacement.state'); changed.write_bytes(payload); changed.replace(state)\n"
        "    else: state.write_bytes(payload)\n"
        "    marker.write_text('changed')\n"
        "fail = os.environ.get('FAIL')\n"
        "sys.exit(91 if fail and fail in sys.argv and '22222222-2222-4222-8222-222222222222' in sys.argv else 0)\n"
    )
    fake.chmod(0o700)
    desktop = commands / "update-desktop-database"
    desktop.write_text("#!/bin/sh\nexit 0\n")
    desktop.chmod(0o700)
    for tool in ("mkdir", "find", "basename", "cp", "rm", "rmdir"):
        (commands / tool).symlink_to(Path("/usr/bin") / tool)
    calls = tmp_path / "calls"

    def run(fail="", action=None, cleanup_failure=False, mutation=None, replace=False):
        env = dict(
            os.environ,
            PATH=str(commands),
            FAIL=fail,
            CALLS=str(calls),
            RECOVERY_STATE=str(snapshot),
            MUTATION_MARKER=str(tmp_path / "mutated"),
            CLEANUP_FAILURE="1" if cleanup_failure else "",
            MUTATE=mutation.hex() if mutation is not None else "",
            REPLACE_STATE="1" if replace else "",
        )
        old_mode = snapshot.parent.stat().st_mode & 0o777
        result = subprocess.run(
            [
                "/bin/sh",
                str(script),
                action or ("configure" if request.param == "postinst" else "remove"),
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )
        snapshot.parent.chmod(old_mode)
        recorded = (
            [json.loads(line) for line in calls.read_text().splitlines()]
            if calls.exists()
            else []
        )
        return result, recorded

    return run, snapshot, contents, fake, request.param


def test_dns_restore_success_removes_only_recovery_state(lifecycle):
    run, snapshot, _contents, _fake, _name = lifecycle
    unrelated = snapshot.parent / "unrelated-state"
    unrelated.write_text("keep")
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert not snapshot.exists()
    assert unrelated.read_text() == "keep"
    assert [
        "connection",
        "modify",
        "uuid",
        "11111111-1111-4111-8111-111111111111",
        "ipv4.dns",
        "192.0.2.53",
        "ipv4.ignore-auto-dns",
        "yes",
    ] in calls
    assert [
        "connection",
        "modify",
        "uuid",
        "22222222-2222-4222-8222-222222222222",
        "ipv4.dns",
        "",
        "ipv4.ignore-auto-dns",
        "no",
    ] in calls
    assert ["connection", "up", "uuid", "22222222-2222-4222-8222-222222222222"] in calls


@pytest.mark.parametrize("failure", ["show", "modify", "up"])
def test_dns_restore_failure_keeps_entire_snapshot_and_reports(lifecycle, failure):
    run, snapshot, contents, _fake, _name = lifecycle
    result, calls = run(failure)
    assert result.returncode != 0
    assert snapshot.read_text() == contents
    assert str(snapshot) in result.stderr
    assert "DNS" in result.stderr
    if failure == "modify":
        assert [
            "connection",
            "up",
            "uuid",
            "22222222-2222-4222-8222-222222222222",
        ] not in calls
    # A later successful invocation can retry using the original full snapshot.
    result, _calls = run()
    assert result.returncode == 0, result.stderr
    assert not snapshot.exists()


def test_dns_without_nmcli_keeps_snapshot_and_reports(lifecycle):
    run, snapshot, contents, fake, _name = lifecycle
    fake.unlink()
    result, calls = run()
    assert result.returncode != 0
    assert snapshot.read_text() == contents
    assert str(snapshot) in result.stderr
    assert "nmcli" in result.stderr
    assert calls == []


def test_dns_state_cleanup_failure_is_reported(lifecycle):
    run, snapshot, contents, _fake, _name = lifecycle
    result, _calls = run(cleanup_failure=True)
    assert result.returncode != 0
    assert snapshot.read_text() == contents
    assert str(snapshot) in result.stderr


def test_dns_last_record_without_newline_is_restored(lifecycle):
    run, snapshot, contents, _fake, _name = lifecycle
    snapshot.write_text(contents.rstrip("\n"))
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert ["connection", "up", "uuid", "22222222-2222-4222-8222-222222222222"] in calls
    assert not snapshot.exists()


def test_dns_without_snapshot_does_not_touch_network(lifecycle):
    run, snapshot, _contents, _fake, _name = lifecycle
    snapshot.unlink()
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert calls == []


@pytest.mark.parametrize("lifecycle", ["prerm"], indirect=True)
def test_prerm_upgrade_does_not_restore(lifecycle):
    run, snapshot, contents, _fake, _name = lifecycle
    result, calls = run(action="upgrade")
    assert result.returncode == 0, result.stderr
    assert calls == []
    assert snapshot.read_text() == contents


@pytest.mark.parametrize("lifecycle", ["prerm"], indirect=True)
def test_prerm_deconfigure_keeps_snapshot_on_failure(lifecycle):
    run, snapshot, contents, _fake, _name = lifecycle
    result, _calls = run("up", action="deconfigure")
    assert result.returncode != 0
    assert snapshot.read_text() == contents
    result, _calls = run(action="deconfigure")
    assert result.returncode == 0, result.stderr
    assert not snapshot.exists()


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


# Exact three inputs from the independent review, for both maintainer scripts.
@pytest.mark.parametrize(
    "damaged",
    [
        b"|203.0.113.99|yes\n22222222-2222-4222-8222-222222222222|198.51.100.53|yes\n",
        b"11111111-1111-4111-8111-111111111111\n22222222-2222-4222-8222-222222222222|198.51.100.53|yes\n",
        b"11111111-1111-4111-8111-111111111111",
    ],
)
def test_independent_corruption_reproductions_are_rejected(lifecycle, damaged):
    run, snapshot, _contents, _fake, _name = lifecycle
    snapshot.write_bytes(damaged)
    result, calls = run()
    assert result.returncode != 0
    assert snapshot.read_bytes() == damaged
    assert str(snapshot) in result.stderr
    assert calls == []


@pytest.mark.parametrize(
    "damaged",
    [
        b"11111111-1111-4111-8111-111111111111",
        b"|192.0.2.1|yes",
        b"11111111-1111-4111-8111-111111111111|192.0.2.1",
        b"11111111-1111-4111-8111-111111111111|192.0.2.1|yes|extra",
        b"11111111-1111-4111-8111-111111111111|||",
        b"",
        b"  |192.0.2.1|yes",
        b"11111111-1111-4111-8111-111111111111|192.0.2.1\0|yes",
        b"11111111-1111-4111-8111-111111111111|\xff|yes",
        b"11111111-1111-4111-8111-111111111111|192.0.2.1|yes\r",
    ],
)
def test_entire_snapshot_is_validated_before_any_connection_change(lifecycle, damaged):
    run, snapshot, _contents, _fake, _name = lifecycle
    contents = (
        b"11111111-1111-4111-8111-111111111111|192.0.2.53|yes\n"
        + damaged
        + b"\n22222222-2222-4222-8222-222222222222||\n"
    )
    snapshot.write_bytes(contents)
    result, calls = run()
    assert result.returncode != 0
    assert snapshot.read_bytes() == contents
    assert str(snapshot) in result.stderr
    assert calls == [], "Even the valid first record must not reach nmcli"


@pytest.mark.parametrize(
    "dns,ignore",
    [
        ("", ""),
        ("", "no"),
        ("192.0.2.1", ""),
        ("192.0.2.1", "yes"),
        ("192.0.2.1,198.51.100.53", "yes"),
        ("192.0.2.1 198.51.100.53", "no"),
    ],
)
def test_complete_legacy_record_preserves_explicit_empty_values(lifecycle, dns, ignore):
    run, snapshot, _contents, _fake, _name = lifecycle
    snapshot.write_text(
        f"11111111-1111-4111-8111-111111111111|{dns}|{ignore}"
    )  # Complete record, no final LF.
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert calls == [
        ["connection", "show", "uuid", "11111111-1111-4111-8111-111111111111"],
        [
            "connection",
            "modify",
            "uuid",
            "11111111-1111-4111-8111-111111111111",
            "ipv4.dns",
            dns,
            "ipv4.ignore-auto-dns",
            ignore or "no",
        ],
        ["connection", "up", "uuid", "11111111-1111-4111-8111-111111111111"],
    ]
    assert not snapshot.exists()


def test_empty_legacy_snapshot_contains_no_connections(lifecycle):
    # The old installer used touch before enumerating active connections.
    run, snapshot, _contents, _fake, _name = lifecycle
    snapshot.write_bytes(b"")
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert calls == []
    assert not snapshot.exists()


A = "11111111-1111-4111-8111-111111111111"
C = "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA"


@pytest.mark.parametrize(
    "identifier",
    [
        "",
        "lab-uplink",
        A.replace("-", ""),
        "{" + A + "}",
        "urn:uuid:" + A,
        A[:-1],
        A + "f",
        A[:-1] + "g",
        " " + A,
        A + " ",
    ],
)
def test_v3_invalid_uuid_rejects_entire_snapshot(lifecycle, identifier):
    run, snapshot, _contents, _fake, _name = lifecycle
    original = f"{A}|192.0.2.1|yes\n{identifier}|192.0.2.2|no\n".encode()
    snapshot.write_bytes(original)
    result, calls = run()
    assert result.returncode != 0
    assert snapshot.read_bytes() == original
    assert calls == []


@pytest.mark.parametrize(
    "first,second,dns",
    [(A, A, "192.0.2.1"), (A, A, "192.0.2.2"), (C, C.lower(), "192.0.2.1")],
)
def test_v3_identical_conflicting_and_case_duplicates_are_rejected(
    lifecycle, first, second, dns
):
    run, snapshot, _contents, _fake, _name = lifecycle
    original = f"{first}|192.0.2.1|yes\n{second}|{dns}|yes\n".encode()
    snapshot.write_bytes(original)
    result, calls = run()
    assert result.returncode != 0
    assert "duplicate UUID" in result.stderr
    assert snapshot.read_bytes() == original
    assert calls == []


@pytest.mark.parametrize("identifier", [A, C])
def test_v3_every_nm_call_uses_uuid_selector(lifecycle, identifier):
    run, snapshot, _contents, _fake, _name = lifecycle
    snapshot.write_text(f"{identifier}|192.0.2.1|yes\n")
    result, calls = run()
    assert result.returncode == 0, result.stderr
    assert [c[1] for c in calls] == ["show", "modify", "up"]
    assert all(c[2:4] == ["uuid", identifier.lower()] for c in calls)
    assert not snapshot.exists()


@pytest.mark.parametrize("replace", [False, True])
@pytest.mark.parametrize(
    "changed",
    [
        f"{A}|192.0.2.1|yes\n",
        f"{A}|192.0.2.2|no\n",
        "22222222-2222-4222-8222-222222222222|192.0.2.3|yes\n",
    ],
)
def test_v3_changed_or_replaced_state_is_retained(lifecycle, replace, changed):
    run, snapshot, _contents, _fake, _name = lifecycle
    snapshot.write_text(f"{A}|192.0.2.1|yes\n")
    result, calls = run(mutation=changed.encode(), replace=replace)
    assert result.returncode != 0
    assert "recovery state changed" in result.stderr
    assert snapshot.read_bytes() == changed.encode()
    assert all(c[3] == A for c in calls), "Only the validated snapshot may reach nmcli"


def test_v3_missing_uuid_cannot_fall_back_to_profile_name(lifecycle):
    run, snapshot, _contents, fake, _name = lifecycle
    # Model a NAME equal to A, but no connection with UUID A.
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json,os,sys\n"
        "with open(os.environ['CALLS'],'a') as f:f.write(json.dumps(sys.argv[1:])+'\\n')\n"
        "sys.exit(10 if sys.argv[3:4]==['uuid'] else 0)\n"
    )
    original = f"{A}|192.0.2.1|yes\n"
    snapshot.write_text(original)
    result, calls = run()
    assert result.returncode != 0
    assert snapshot.read_text() == original
    assert calls == [["connection", "show", "uuid", A]]


def test_v3_directory_lock_serializes_cooperating_access(lifecycle):
    import concurrent.futures
    import fcntl
    import time

    run, snapshot, _contents, fake, name = lifecycle
    script = fake.parent.parent / name
    ready = fake.parent.parent / "lock-ready"
    text = script.read_text()
    hook = "        fcntl.flock(directory_fd, fcntl.LOCK_EX)"
    assert text.count(hook) == 1
    script.write_text(
        text.replace(hook, f"        open({str(ready)!r}, 'w').close()\n" + hook)
    )
    descriptor = os.open(snapshot.parent, os.O_RDONLY | os.O_DIRECTORY)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        worker = executor.submit(run)
        try:
            deadline = time.monotonic() + 10
            while not ready.exists():
                assert time.monotonic() < deadline, "Worker did not reach lock"
                time.sleep(0.01)
            assert not worker.done()
            assert not (fake.parent.parent / "calls").exists()
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
        result, calls = worker.result(timeout=10)
    assert result.returncode == 0, result.stderr
    assert len([c for c in calls if c[1] == "modify"]) == 2
    assert not snapshot.exists()
    assert snapshot.parent.is_dir(), "The shared lock directory must remain stable"
