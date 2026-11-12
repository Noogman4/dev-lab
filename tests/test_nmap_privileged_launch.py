"""Privileged Nmap presets must never resolve sudo or nmap through PATH."""

import os
import stat

import pytest

import netmon.app as app_module
from netmon.app import App
from netmon.core import trusted_sudo


class Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class ImmediateThread:
    def __init__(self, target=None, daemon=None, **_kwargs):
        self.target = target

    def start(self):
        self.target()


class FakeProc:
    def __init__(self):
        self.returncode = 0

    def communicate(self, timeout=None):
        return "Nmap done: 1 IP address (1 host up)\n", None


def _planted_path(tmp_path):
    planted = tmp_path / "planted-bin"
    planted.mkdir()
    for name in ("sudo", "nmap"):
        wrapper = planted / name
        wrapper.write_text(f'#!/bin/sh\ntouch "{tmp_path}/{name}-ran"\n')
        wrapper.chmod(0o755)
    return planted


def _app(preset):
    app = App.__new__(App)
    app.__dict__.update(
        nmap_running=False,
        nmap_cancel_requested=False,
        nmap_active_process=None,
        nmap_manual_target_var=Var("192.0.2.10"),
        nmap_target=Var(""),
        nmap_preset=Var(preset),
        nmap_summary_var=Var(""),
        nmap_status_var=Var(""),
        nmap_error_var=Var(""),
        log=lambda _message: None,
        tr=lambda _key, fallback="": fallback,
        ensure_sudo_session=lambda _reason="": True,
        _set_nmap_running_state=lambda *_a, **_k: None,
        _display_nmap_preset_label=lambda key: key,
        after=lambda _delay, _callback: None,
    )
    return app


@pytest.mark.parametrize("preset", ["aggressive", "udp_basis"])
def test_privileged_preset_ignores_path_planted_sudo_and_nmap(
    monkeypatch, tmp_path, preset
):
    planted = _planted_path(tmp_path)
    monkeypatch.setenv("PATH", f"{planted}:{os.environ.get('PATH', '')}")
    monkeypatch.setenv("NMAPDIR", str(planted))
    monkeypatch.setenv("LD_PRELOAD", str(planted / "evil.so"))
    launched = []

    def fake_popen(cmd, **kwargs):
        launched.append((list(cmd), kwargs))
        return FakeProc()

    monkeypatch.setattr(app_module, "has_cmd", lambda _name: True)
    monkeypatch.setattr(app_module.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    App.nmap_async(_app(preset))

    assert len(launched) == 1
    cmd, kwargs = launched[0]
    assert cmd[:6] == [
        "/usr/bin/sudo",
        "-n",
        "--",
        "/usr/bin/nmap",
        "--datadir",
        "/usr/share/nmap",
    ]
    assert cmd[-2:] == ["--", "192.0.2.10"]
    assert not any(str(planted) in part for part in cmd)
    env = kwargs["env"]
    assert env["PATH"] == "/usr/sbin:/usr/bin:/sbin:/bin"
    assert not {"NMAPDIR", "LD_PRELOAD", "HOME"} & env.keys()
    assert kwargs["cwd"] == "/"
    assert not (tmp_path / "sudo-ran").exists()
    assert not (tmp_path / "nmap-ran").exists()


def test_unprivileged_preset_still_runs_as_the_user(monkeypatch):
    launched = []
    monkeypatch.setattr(app_module, "has_cmd", lambda _name: True)
    monkeypatch.setattr(
        app_module.subprocess,
        "Popen",
        lambda cmd, **kwargs: launched.append((list(cmd), kwargs)) or FakeProc(),
    )
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)

    App.nmap_async(_app("quick"))

    cmd, kwargs = launched[0]
    assert cmd[0] == "nmap" and "sudo" not in " ".join(cmd)
    assert "env" not in kwargs


@pytest.mark.parametrize(
    "unsafe",
    ["/usr/bin/nmap", "/usr/share/nmap", "/usr/share"],
)
def test_untrusted_nmap_binary_or_data_directory_is_refused(monkeypatch, unsafe):
    real_lstat = os.lstat

    class Info:
        def __init__(self, info):
            self.st_mode = info.st_mode
            self.st_uid = 1000

    def lstat(path):
        info = real_lstat(path)
        return Info(info) if path == unsafe else info

    if not os.path.exists(unsafe):
        pytest.skip(f"{unsafe} not installed")
    monkeypatch.setattr(trusted_sudo.os, "lstat", lstat)
    with pytest.raises(PermissionError):
        trusted_sudo.privileged_nmap_command(["-sU"], "192.0.2.10")


def test_group_writable_data_directory_is_refused(monkeypatch):
    real_lstat = os.lstat

    class Info:
        def __init__(self, info):
            self.st_mode = info.st_mode | stat.S_IWGRP
            self.st_uid = info.st_uid

    monkeypatch.setattr(
        trusted_sudo.os,
        "lstat",
        lambda path: (
            Info(real_lstat(path)) if path == "/usr/share/nmap" else real_lstat(path)
        ),
    )
    if not os.path.isdir("/usr/share/nmap"):
        pytest.skip("nmap data directory not installed")
    with pytest.raises(PermissionError):
        trusted_sudo.trusted_nmap_datadir()


def test_privileged_run_gets_clean_environment_and_root_cwd(monkeypatch):
    seen = {}

    def fake_popen(cmd, **kwargs):
        seen.update(kwargs)
        return FakeProc()

    monkeypatch.setattr(app_module.subprocess, "Popen", fake_popen)
    app = _app("aggressive")
    rc, _out, state = App._run_nmap_with_timeout(
        app, ["/usr/bin/sudo", "-n", "--", "/usr/bin/nmap"], 5, privileged=True
    )
    assert (rc, state) == (0, "ok")
    assert seen["cwd"] == "/"
    assert seen["env"] == trusted_sudo.sudo_environment()
    assert seen["stdin"] is app_module.subprocess.DEVNULL
