"""Privilege broker regressions using fakes; no installed broker is run."""

import os
import shlex
import stat
import subprocess
from types import SimpleNamespace

import pytest

from netmon.app import App
from netmon.core import privilege_launcher as launcher, rkhunter_manager, trusted_sudo
from netmon.ui.tabs.cleanup_assistant_tab import CleanupAssistantTab


@pytest.fixture
def layout(monkeypatch):
    nodes = {
        path: SimpleNamespace(st_uid=0, st_mode=stat.S_IFDIR | 0o755)
        for path in ("/", "/usr", "/usr/bin", "/etc", "/etc/alternatives")
    }
    for name in ("bash", "env", "sudo", "pkexec", "xterm"):
        nodes["/usr/bin/" + name] = SimpleNamespace(
            st_uid=0, st_mode=stat.S_IFREG | 0o755
        )
    original = os.lstat

    def info(path, *args, **kwargs):
        path = os.fspath(path)
        if path in nodes:
            return nodes[path]
        if path.startswith("/usr/bin/"):
            raise FileNotFoundError(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", info)
    return nodes


@pytest.fixture
def poisoned(monkeypatch, tmp_path):
    marker = tmp_path / "poison-ran"
    for name in ("sudo", "pkexec", "bash", "env", "xterm", "x-terminal-emulator"):
        path = tmp_path / name
        path.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\nexit 99\n")
        path.chmod(0o755)
    startup = tmp_path / "startup"
    startup.write_text(f"touch {shlex.quote(str(marker))}\n")
    monkeypatch.setenv("PATH", str(tmp_path))
    for key in ("BASH_ENV", "ENV", "LD_PRELOAD", "PYTHONPATH", "SUDO_ASKPASS"):
        monkeypatch.setenv(key, str(startup))
    return marker


@pytest.mark.parametrize("runner", ["rkhunter", "cleanup"])
def test_rkhunter_and_cleanup_ignore_poisoned_path(
    monkeypatch, poisoned, layout, runner
):
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        assert args[0] == "/usr/bin/sudo"
        assert kwargs["env"] == trusted_sudo.sudo_environment()
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    if runner == "rkhunter":
        assert rkhunter_manager.run_rkhunter_update() == (0, "ok")
        assert len(calls) == 1
        assert not poisoned.exists()
        return
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    approvals = []
    tab.app = SimpleNamespace(
        ensure_sudo_session=lambda reason: approvals.append(reason) or True
    )
    assert tab._run_sudo_cleanup_command(["apt", "clean"])["ok"]
    assert approvals == ["Cleanup Assistant"]
    assert len(calls) == 1
    assert not poisoned.exists()


@pytest.mark.parametrize("runner", ["rkhunter", "cleanup"])
def test_unsafe_sudo_fails_without_execution(monkeypatch, layout, runner):
    layout["/usr/bin/sudo"].st_uid = 1000
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("executed"))
    if runner == "rkhunter":
        assert rkhunter_manager.run_rkhunter_update()[0] != 0
    else:
        tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
        tab.app = SimpleNamespace(ensure_sudo_session=lambda reason: True)
        assert not tab._run_sudo_cleanup_command(["apt", "clean"])["ok"]


@pytest.mark.parametrize("polkit", [False, True])
def test_packet_repair_uses_clean_nonlogin_root_shell(layout, poisoned, polkit):
    args = launcher.packet_repair_command("echo fixed-script", polkit=polkit)
    assert args[:3] == [
        "/usr/bin/pkexec" if polkit else "/usr/bin/sudo",
        "/usr/bin/env",
        "-i",
    ]
    assert args[-5:] == [
        "/usr/bin/bash",
        "--noprofile",
        "--norc",
        "-c",
        "echo fixed-script",
    ]
    assert "PATH=/usr/sbin:/usr/bin:/sbin:/bin" in args
    assert not any("BASH_ENV=" in arg or "LD_PRELOAD=" in arg for arg in args)


@pytest.mark.parametrize("name", ["bash", "env", "pkexec", "xterm"])
@pytest.mark.parametrize("defect", ["owner", "writable", "fifo", "not_executable"])
def test_rejects_unsafe_system_program(layout, name, defect):
    info = layout["/usr/bin/" + name]
    if defect == "owner":
        info.st_uid = 1000
    elif defect == "writable":
        info.st_mode |= 0o020
    elif defect == "fifo":
        info.st_mode = stat.S_IFIFO | 0o755
    else:
        info.st_mode = stat.S_IFREG | 0o644
    with pytest.raises(PermissionError):
        launcher.trusted_system_executable(name)


def test_debian_alternatives_links_are_checked(monkeypatch, layout):
    links = {
        "/usr/bin/x-terminal-emulator": "/etc/alternatives/x-terminal-emulator",
        "/etc/alternatives/x-terminal-emulator": "/usr/bin/xterm",
    }
    for path in links:
        layout[path] = SimpleNamespace(st_uid=0, st_mode=stat.S_IFLNK | 0o777)
    monkeypatch.setattr(os, "readlink", lambda path: links[path])
    assert launcher.trusted_system_executable("x-terminal-emulator") == "/usr/bin/xterm"
    layout["/etc/alternatives"].st_mode |= 0o002
    with pytest.raises(PermissionError):
        launcher.trusted_system_executable("x-terminal-emulator")


@pytest.mark.parametrize(
    "name,option,string_arg",
    [
        ("x-terminal-emulator", "-e", False),
        ("gnome-terminal", "--", False),
        ("konsole", "-e", False),
        ("xfce4-terminal", "--command", True),
        ("mate-terminal", "--", False),
        ("lxterminal", "-e", True),
        ("xterm", "-e", False),
    ],
)
def test_terminal_variants_use_absolute_clean_shell(
    layout, poisoned, name, option, string_arg
):
    del layout["/usr/bin/xterm"]
    layout["/usr/bin/" + name] = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o755)
    args = launcher.maintenance_terminal_command("sudo apt clean")
    assert args[:2] == ["/usr/bin/" + name, option]
    shell = shlex.split(args[2]) if string_arg else args[2:]
    assert shell[:2] == ["/usr/bin/env", "-i"]
    assert shell[-5:-1] == ["/usr/bin/bash", "--noprofile", "--norc", "-c"]
    assert '/usr/bin/sudo "$@"' in shell[-1]
    assert not any(
        arg.startswith(("BASH_ENV=", "LD_PRELOAD=", "PYTHONPATH=")) for arg in shell
    )
    assert not poisoned.exists()


def test_shell_ignores_startup_and_path_even_after_path_change(
    monkeypatch, tmp_path, poisoned
):
    # Only a harmless shell and a synthetic broker execute in this test.
    approved = tmp_path / "approved"
    broker = tmp_path / "approved-sudo"
    broker.write_text(f"#!/bin/sh\nprintf approved > {shlex.quote(str(approved))}\n")
    broker.chmod(0o755)
    monkeypatch.setattr(launcher, "trusted_sudo_path", lambda: str(broker))
    monkeypatch.setattr(
        launcher, "trusted_system_executable", lambda name: "/usr/bin/" + name
    )
    script = f"PATH={shlex.quote(str(tmp_path))}; export PATH; sudo harmless-action"
    command = launcher.maintenance_terminal_command(script)[2:]
    env = os.environ.copy()
    env.pop("LD_PRELOAD", None)
    result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert approved.read_text() == "approved"
    assert not poisoned.exists()


def test_app_launch_passes_clean_environment(monkeypatch, layout, poisoned):
    app = App.__new__(App)
    calls = []
    monkeypatch.setattr(
        subprocess, "Popen", lambda args, **kwargs: calls.append((args, kwargs))
    )
    assert app._open_command_in_external_terminal("echo reviewed") == "/usr/bin/xterm"
    assert calls[0][1]["env"] == launcher.terminal_environment()
    assert "exec /usr/bin/bash --noprofile --norc" in calls[0][0][-1]
    assert not poisoned.exists()


def test_packet_repair_app_uses_validated_polkit(monkeypatch, layout, poisoned):
    import netmon.app as app_module

    app = App.__new__(App)
    app.show_dumpcap_permission_hint = lambda: None
    app.log_safe = lambda message: None
    monkeypatch.setattr(app_module.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(app_module.messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(app_module.os.path, "lexists", lambda path: True)
    calls = []
    monkeypatch.setattr(
        subprocess, "Popen", lambda args, **kw: calls.append((args, kw))
    )
    app.repair_packet_capture_permissions()
    assert len(calls) == 1
    assert calls[0][0][0] == "/usr/bin/pkexec"
    assert calls[0][1]["env"] == launcher.terminal_environment()
    assert "--noprofile" in calls[0][0] and "-lc" not in calls[0][0]
    assert not poisoned.exists()


def test_no_supported_protected_terminal_returns_none(layout):
    del layout["/usr/bin/xterm"]
    assert launcher.maintenance_terminal_command("sudo apt clean") is None


def test_symlink_cycle_is_rejected(monkeypatch, layout):
    layout["/usr/bin/xterm"].st_mode = stat.S_IFLNK | 0o777
    monkeypatch.setattr(os, "readlink", lambda path: "/usr/bin/xterm")
    with pytest.raises(PermissionError):
        launcher.trusted_system_executable("xterm")


def test_untrusted_terminal_link_is_rejected(monkeypatch, layout):
    layout["/usr/bin/xterm"].st_uid = 1000
    layout["/usr/bin/xterm"].st_mode = stat.S_IFLNK | 0o777
    monkeypatch.setattr(os, "readlink", lambda path: "/usr/bin/bash")
    with pytest.raises(PermissionError):
        launcher.trusted_system_executable("xterm")
