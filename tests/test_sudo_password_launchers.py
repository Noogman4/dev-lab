"""Password-bearing sudo paths outside the main dialog stay on the trusted binary."""

import os
import stat
import subprocess
from types import SimpleNamespace

import pytest

from netmon import netmon_radio_app
from netmon.netmon_radio_app import NetMonRadioApp
from netmon.services import hdd_mount_service as service


@pytest.fixture
def layout(monkeypatch):
    nodes = {
        path: SimpleNamespace(st_uid=0, st_mode=stat.S_IFDIR | 0o755)
        for path in ("/", "/usr", "/usr/bin")
    }
    for name in ("bash", "env", "sudo", "xterm"):
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


def _poison_user_paths(monkeypatch, tmp_path):
    marker = tmp_path / "captured"
    for directory in ("path-bin", "home/.local/bin", "home/bin"):
        target = tmp_path / directory
        target.mkdir(parents=True)
        fake = target / "sudo"
        fake.write_text(f"#!/bin/sh\necho captured > {marker}\n")
        fake.chmod(0o755)
    profile = tmp_path / "home/.profile"
    profile.write_text('PATH="$HOME/.local/bin:$HOME/bin:$PATH"\n')
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("PATH", f"{tmp_path / 'path-bin'}:{os.environ['PATH']}")
    monkeypatch.setenv("BASH_ENV", str(profile))
    return marker


def test_radio_terminal_uses_protected_launcher(layout):
    command = NetMonRadioApp._build_external_terminal_command(
        object(), "sudo apt install -y projectm"
    )

    assert command[:3] == ["/usr/bin/xterm", "-e", "/usr/bin/env"]
    assert "-i" in command and "--noprofile" in command and "--norc" in command
    assert "-lc" not in command
    assert command[-1].startswith('sudo() { /usr/bin/sudo "$@"; }; readonly -f sudo;')


def test_radio_terminal_fails_closed_on_unsafe_sudo(layout):
    layout["/usr/bin/sudo"].st_uid = 1000

    assert NetMonRadioApp._build_external_terminal_command(object(), "true") is None


@pytest.mark.skipif(
    not all(os.access(p, os.X_OK) for p in ("/usr/bin/env", "/usr/bin/bash")),
    reason="system shell layout unavailable",
)
def test_poisoned_user_paths_never_receive_radio_install_password(
    monkeypatch, tmp_path, layout
):
    marker = _poison_user_paths(monkeypatch, tmp_path)
    command = NetMonRadioApp._build_external_terminal_command(
        object(), "type -t sudo; declare -f sudo"
    )
    shell = command[command.index("/usr/bin/env") :]

    result = subprocess.run(
        shell,
        env=netmon_radio_app.terminal_environment(),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0] == "function"
    assert "/usr/bin/sudo" in result.stdout
    assert not marker.exists()


def test_hdd_password_sudo_uses_trusted_binary(monkeypatch):
    calls = []
    monkeypatch.setattr(
        service.trusted_sudo, "trusted_sudo_path", lambda: "/trusted/sudo"
    )

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(service.subprocess, "run", run)

    assert service.run_hdd_command(["sudo", "-S", "-v"], input_text="pw\n")[0] == 0
    assert calls[0][0] == ["/trusted/sudo", "-S", "-v"]
    assert calls[0][1]["env"]["PATH"] == "/usr/sbin:/usr/bin:/sbin:/bin"


def test_hdd_password_never_reaches_unsafe_sudo(monkeypatch):
    def unsafe():
        raise PermissionError("Unsafe system sudo path")

    monkeypatch.setattr(service.trusted_sudo, "trusted_sudo_path", unsafe)
    monkeypatch.setattr(
        service.subprocess,
        "run",
        lambda *a, **k: pytest.fail("password reached an untrusted sudo"),
    )

    rc, _out = service.run_hdd_command(["sudo", "-S", "-v"], input_text="pw\n")
    assert rc == 1
