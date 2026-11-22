from contextlib import ExitStack, contextmanager
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace

import pytest

from netmon.modules.secure_browser import (
    container_launcher,
    container_migration,
    sandbox,
    session,
)
from netmon.modules.secure_browser.service import SecureBrowserService
from tools.secure_browser_manager import browser_container_builder as builder


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://user@host.test/",
        "https://[bad",
        "https://host.test:0/",
        "https://host.test/\n",
        "https://ho%73t.test/",
    ],
)
def test_url_validation_rejects_non_web_and_ambiguous_authorities(url):
    with pytest.raises(sandbox.BrowserSandboxError):
        sandbox._check_url(url)


def test_plan_uses_private_paths_and_starts_firefox_without_capabilities():
    url = "https://host.test/article?a=3&b=5#text"
    sandbox._check_url(url)
    command = sandbox._sandbox_command(
        3, 4, 5, "/test/wayland", "/test/dbus", url, {"resolv.conf": 6}
    )
    assert command[:4] == [
        sandbox._BWRAP,
        "--unshare-user",
        "--unshare-net",
        "--unshare-pid",
    ]
    mounts = [
        (command[i + 1], command[i + 2])
        for i, flag in enumerate(command)
        if flag in {"--bind", "--bind-fd"}
    ]
    assert mounts == [("4", "/home/browser/profile"), ("5", "/home/browser/Downloads")]
    assert command[command.index("--cap-drop") + 1] == "ALL"
    assert not {
        "--cap-add",
        "--uid",
        "--gid",
        "DISPLAY",
        "XAUTHORITY",
        "/tmp/.X11-unix",
    }.intersection(command)
    assert command[command.index("/run/browser/wayland-0") - 2 :][:3] == [
        "--ro-bind",
        "/test/wayland",
        "/run/browser/wayland-0",
    ]
    assert command[-6:] == [
        "--",
        "/browser/firefox",
        "--profile",
        "/home/browser/profile",
        "--new-tab",
        url,
    ]


def test_browser_branding_is_mounted_read_only_inside_the_sandbox():
    command = sandbox._sandbox_command(
        3,
        4,
        5,
        "/test/wayland",
        "/test/dbus",
        "https://example.org/",
        {},
        chrome=(6, 7),
    )
    chrome = command.index("/home/browser/profile/chrome")
    icon = command.index("/etc/netmon-browser.png")
    assert chrome > command.index("/home/browser/profile")
    assert command[chrome - 2 : chrome] == ["--ro-bind-fd", "6"]
    assert command[icon - 2 : icon] == ["--ro-bind-data", "7"]


def test_secure_browser_pilot_preserves_profile_and_domain_policy(tmp_path):
    source = tmp_path / "firefox-source"
    source.mkdir()
    (source / "firefox").touch(mode=0o755)
    spec = builder.ContainerSpec(
        name="Pilot",
        path=tmp_path / "Pilot",
        allowed_domains=["example.test"],
        source_firefox_dir=source,
        icon_mode="default",
        sandboxed=True,
    )
    menu = builder.create_container(spec, tmp_path / "applications")
    start = spec.path / "start.sh"
    policies_path = spec.path / "policies.json"
    original = policies_path.read_bytes()
    loaded = container_launcher._container_policies(spec.path)["policies"]
    assert loaded["WebsiteFilter"] == json.loads(original)["policies"]["WebsiteFilter"]
    assert loaded["DefaultDownloadDirectory"] == "${home}/Downloads"
    assert policies_path.read_bytes() == original
    assert builder.SANDBOX_MODULE in start.read_text()
    assert builder.parse_desktop_exec_target(menu) == start
    found = builder.discover_container(spec.path / "firefox" / "firefox")
    assert found.profile_path == spec.path / "profile"
    assert (
        builder.build_existing_start_script(found, found.profile_path)
        == start.read_text()
    )

    policies_path.write_text('{"policies": {}}')
    with pytest.raises(sandbox.BrowserSandboxError, match="aktiven Domainfilter"):
        container_launcher._container_policies(spec.path)


def test_secure_browser_starts_its_policy_homepage_without_netmon_chrome():
    command = sandbox._sandbox_command(
        3,
        4,
        5,
        "/test/wayland",
        "/test/dbus",
        None,
        {"firefox/policies/policies.json": 6},
    )
    assert command[-5:] == [
        "--",
        "/browser/firefox",
        "--profile",
        "/home/browser/profile",
        "--no-remote",
    ]
    assert "/etc/firefox/policies/policies.json" in command
    assert "/home/browser/profile/chrome" not in command


def test_secure_browser_tab_creates_a_sandboxed_browser_in_compatible_mode(
    tmp_path, monkeypatch
):
    runtime = tmp_path / "firefox-runtime"
    runtime.mkdir()
    for binary in ("firefox", "firefox-bin"):
        (runtime / binary).touch(mode=0o755)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(session, "FIREFOX_DIR", runtime)
    monkeypatch.setattr(session, "_managed_runtime", lambda path: path)
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setenv("DISPLAY", ":42")
    monkeypatch.setattr(session, "_WESTON", sys.executable)
    monkeypatch.setattr(sandbox, "_require_network_tools", lambda: None)
    service = SecureBrowserService()
    base = tmp_path / "containers"
    monkeypatch.setattr(service, "get_default_base_dir", lambda: base)
    container = base / "firefox-Test"
    options = {
        "name": container.name,
        "homepage_url": "https://example.test/",
        "allowed_domains": ["example.test"],
        "target_dir": container,
        "menu_name": "Test",
        "new_tab_url": "about:blank",
        "icon_mode": "default",
        "security_profile": "Compatible",
        "enable_website_filter": False,
    }

    result = service.execute_create_apply(**options)
    assert result["ok"], result
    starter = container / "start.sh"
    assert builder.detect_start_command(starter) == builder.SANDBOX_START_COMMAND
    (desktop,) = (home / ".local/share/applications").glob("*.desktop")
    assert builder.parse_desktop_exec_target(desktop) == starter
    policies = container_launcher._container_policies(container)["policies"]
    assert "WebsiteFilter" not in policies
    assert policies["DisableTelemetry"] is True


def test_secure_browser_migration_backs_up_closed_profile_before_switching(
    tmp_path, monkeypatch
):
    runtime = tmp_path / "firefox-source"
    runtime.mkdir()
    (runtime / "firefox").touch(mode=0o755)
    (runtime / "application.ini").write_text(
        "[App]\nVersion=153.7.0\nBuildID=20261103151912\n"
    )
    spec = builder.ContainerSpec(
        name="Migration",
        path=tmp_path / "Migration",
        allowed_domains=["example.test"],
        source_firefox_dir=runtime,
        icon_mode="default",
    )
    desktop = builder.create_container(spec, tmp_path / "applications")
    profile = spec.path / "profile"
    (profile / ".parentlock").touch()
    compatibility = profile / "compatibility.ini"
    compatibility.write_text(
        "[Compatibility]\nLastVersion=153.7.1_20261103151912/20261103151912\n"
    )
    marker = profile / "fixture.txt"
    marker.write_text("Existing profile data")
    original = (spec.path / "start.sh").read_bytes()
    original_desktop = desktop.read_bytes()
    monkeypatch.setattr(
        container_migration.session, "_managed_runtime", lambda _: runtime
    )
    monkeypatch.setattr(
        container_migration.session, "_check_display_requirements", lambda: None
    )
    monkeypatch.setattr(sandbox, "_require_network_tools", lambda: None)

    with pytest.raises(sandbox.BrowserSandboxError, match="älter als das Profil"):
        container_migration.migrate_container(spec.path, apply=True)
    compatibility.write_text(
        "[Compatibility]\nLastVersion=153.7.0_20261103151912/20261103151912\n"
    )
    container_migration.migrate_container(spec.path)
    assert not (spec.path / "backups").exists()
    assert (spec.path / "start.sh").read_bytes() == original

    with subprocess.Popen(
        [
            sys.executable,
            "-B",
            "-c",
            "import fcntl, sys; f = open(sys.argv[1], 'r+'); fcntl.lockf(f, fcntl.LOCK_EX); print('locked', flush=True); sys.stdin.read()",
            str(profile / ".parentlock"),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as locked:
        try:
            assert locked.stdout.readline().strip() == b"locked"
            with pytest.raises(sandbox.BrowserSandboxError, match="noch geöffnet"):
                container_migration.migrate_container(spec.path, apply=True)
        finally:
            locked.stdin.close()

    container_migration.migrate_container(spec.path, apply=True)
    (archive,) = (spec.path / "backups").glob("*/*.tar.gz")
    assert archive.stat().st_mode & 0o077 == 0
    with tarfile.open(archive, "r:gz") as saved:
        assert saved.extractfile("start.sh").read() == original
        assert saved.extractfile("profile/fixture.txt").read() == marker.read_bytes()
    assert (
        builder.detect_start_command(spec.path / "start.sh")
        == builder.SANDBOX_START_COMMAND
    )
    assert desktop.read_bytes() == original_desktop


@pytest.mark.parametrize("network_outcome", ["ready", "failed", "lost"])
def test_browser_waits_for_isolated_network_without_fallback(
    monkeypatch, network_outcome
):
    calls = []

    class Browser:
        def poll(self):
            assert os.read(self.start_fd, 1) == b"1"
            if network_outcome == "lost":
                return None
            return 0

    class Network:
        started = False

        def poll(self):
            if network_outcome == "failed" or (
                network_outcome == "lost" and self.started
            ):
                return 1
            self.started = True
            return None

    browser = Browser()

    def user_namespace(_stack, pid):
        assert pid == 2001
        return 3001, 3002

    @contextmanager
    def process(args, fds):
        calls.append(args[0])
        if args[0] == sandbox._BWRAP:
            info_fd, start_fd = fds
            os.write(info_fd, json.dumps({"child-pid": 2001}).encode())
            browser.start_fd = os.dup(start_fd)
            try:
                yield browser
            finally:
                if network_outcome == "failed":
                    assert not select.select([browser.start_fd], [], [], 0)[0]
                os.close(browser.start_fd)
        else:
            assert args[:5] == [
                sandbox._NSENTER,
                "--user=/proc/self/fd/3002",
                "--preserve-credentials",
                "--",
                sandbox._SLIRP,
            ]
            assert "--disable-host-loopback" in args and "--enable-seccomp" in args
            assert "--enable-sandbox" in args and "--netns-type=path" in args
            assert args[-2:] == ["/proc/self/fd/3001", "tap0"]
            assert fds[-2:] == (3001, 3002)
            assert not select.select([browser.start_fd], [], [], 0)[0]
            if network_outcome != "failed":
                os.write(fds[0], b"1")
            yield Network()

    monkeypatch.setattr(sandbox, "_network_user_namespace", user_namespace)
    monkeypatch.setattr(sandbox, "_process", process)

    def start_and_poll():
        with (
            ExitStack() as stack,
            sandbox._networked_browser(stack, [sandbox._BWRAP], ()) as processes,
        ):
            assert sandbox._browser_running(*processes) is False

    if network_outcome == "ready":
        start_and_poll()
    else:
        with pytest.raises(sandbox.BrowserSandboxError, match="Browser-Netzwerk"):
            start_and_poll()
    assert calls == [sandbox._BWRAP, sandbox._NSENTER]


def test_launcher_declines_the_regular_session_bus_before_starting(monkeypatch):
    monkeypatch.setattr(sandbox.os, "getuid", lambda: 1001)
    monkeypatch.setattr(
        subprocess, "Popen", lambda *_a, **_kw: pytest.fail("Started a browser")
    )
    with pytest.raises(sandbox.BrowserSandboxError, match="eigenen D-Bus"):
        sandbox.run_link(
            Path("/firefox"),
            Path("/netmon"),
            Path("/wayland"),
            Path("/run/user/1001/bus"),
            "https://example.test/",
        )


def test_missing_network_tool_fails_before_starting_any_process(monkeypatch):
    monkeypatch.setattr(sandbox.os, "getuid", lambda: 1001)
    monkeypatch.setattr(
        sandbox.os, "access", lambda path, _mode: path == sandbox._BWRAP
    )
    monkeypatch.setattr(
        subprocess, "Popen", lambda *_a, **_kw: pytest.fail("Started a browser")
    )
    with pytest.raises(sandbox.BrowserSandboxError, match="slirp4netns"):
        sandbox.run_link(
            Path("/firefox"),
            Path("/netmon"),
            Path("/wayland"),
            Path("/netmon/session/private-bus"),
            "https://example.test/",
        )


@pytest.fixture
def x11_runtime(monkeypatch):
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    monkeypatch.setenv("DISPLAY", ":42")
    monkeypatch.setenv("XAUTHORITY", "/test/Xauthority")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr(session, "_WESTON", sys.executable)
    with tempfile.TemporaryDirectory(prefix="netmon-x11-") as directory:
        monkeypatch.setenv("XDG_RUNTIME_DIR", directory)
        yield Path(directory)


def test_x11_display_socket_lifetime_and_environment(x11_runtime, monkeypatch):
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/test/desktop-bus")
    process = SimpleNamespace(poll=lambda: None)

    @contextmanager
    def fake_weston(command, fds, *, env):
        assert command[:6] == [
            session._SETPRIV,
            "--no-new-privs",
            "--pdeathsig",
            "TERM",
            session._WESTON,
            "--backend=x11-backend.so",
        ]
        assert set(command[6:-1]) == {
            "--shell=kiosk-shell.so",
            "--no-config",
            "--use-pixman",
            "--idle-time=0",
            "--socket=wayland-0",
        }
        assert not fds
        runtime = Path(env["XDG_RUNTIME_DIR"])
        assert command[-1] == f"--log={runtime / 'weston.log'}"
        assert runtime.parent == x11_runtime
        assert runtime.stat().st_mode & 0o777 == 0o700
        assert env == {
            **sandbox._HOST_ENV,
            "DISPLAY": ":42",
            "XAUTHORITY": "/test/Xauthority",
            "XDG_RUNTIME_DIR": str(runtime),
        }
        with socket.socket(socket.AF_UNIX) as server:
            server.bind(str(runtime / "wayland-0"))
            server.listen(1)
            yield process

    branded = []
    monkeypatch.setattr(sandbox, "_process", fake_weston)
    monkeypatch.setattr(
        session,
        "_brand_weston_window",
        lambda log, title, _env: branded.append((log, title)),
    )
    with session._display_socket() as (path, display):
        assert path.is_socket()
        assert display is process
        assert branded == [(path.with_name("weston.log"), "NetmonRoots Browser")]
    assert not path.parent.exists()


def test_native_wayland_wins_over_x11(x11_runtime, monkeypatch):
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-native")
    monkeypatch.setattr(
        sandbox, "_process", lambda *_a, **_kw: pytest.fail("Started Weston")
    )
    expected = x11_runtime / "wayland-native"
    with socket.socket(socket.AF_UNIX) as server:
        server.bind(str(expected))
        session._check_display_requirements()
        with session._display_socket() as (path, display):
            assert path == expected
            assert display is None
        assert path.is_socket()


def test_x11_display_reports_missing_weston(x11_runtime, monkeypatch):
    monkeypatch.setattr(session, "_WESTON", str(x11_runtime / "weston"))
    with pytest.raises(session.X11DisplayError, match="fehlt weston"):
        session._check_display_requirements()
    with pytest.raises(session.X11DisplayError, match="fehlt weston"):
        with session._display_socket():
            pytest.fail("Started without Weston")
    assert not list(x11_runtime.iterdir())


@pytest.mark.parametrize(
    ("status", "timeout", "match"),
    [(1, 12, "Status 1"), (None, 0, "keinen Wayland-Socket")],
)
def test_failed_x11_display_cleans_up(x11_runtime, monkeypatch, status, timeout, match):
    closed = []

    @contextmanager
    def fake_weston(_command, _fds, *, env):
        try:
            yield SimpleNamespace(poll=lambda: status)
        finally:
            closed.append(Path(env["XDG_RUNTIME_DIR"]))

    monkeypatch.setattr(sandbox, "_process", fake_weston)
    monkeypatch.setattr(sandbox, "_START_TIMEOUT", timeout)
    with pytest.raises(session.X11DisplayError, match=match):
        with session._display_socket():
            pytest.fail("Started without a display")
    assert len(closed) == 1 and not closed[0].exists()


def test_x11_metadata_targets_only_the_window_reported_by_weston(tmp_path, monkeypatch):
    log = tmp_path / "weston.log"
    log.write_text("[10:00:00.000] x11 output 1024x600, window id 2097157\n")
    calls = []

    def runner(command, **kwargs):
        assert kwargs["env"] == {"DISPLAY": ":42"}
        calls.append(command)

    monkeypatch.setattr(session.subprocess, "run", runner)
    session._brand_weston_window(log, "NetmonRoots Browser", {"DISPLAY": ":42"})
    [command] = calls
    assert command[:3] == ["/usr/bin/python3", "-I", "-B"]
    assert Path(command[3]).name == "x11_window.py"
    assert command[4:] == [
        "2097157",
        "NetmonRoots Browser",
        str(sandbox._BROWSER_ICON),
    ]


def test_x11_metadata_skips_a_log_without_a_window_id(tmp_path, monkeypatch):
    log = tmp_path / "weston.log"
    log.write_text("Unrelated compositor log entry\n")
    monkeypatch.setattr(
        session.subprocess, "run", lambda *_a, **_kw: pytest.fail("Changed a window")
    )
    session._brand_weston_window(log, "NetmonRoots Browser", {})
