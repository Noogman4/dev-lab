"""Credential-boundary regressions; never invoke installed sudo."""

import stat
import sys
from types import SimpleNamespace

import pytest

from netmon.core import command, tooling, trusted_sudo


@pytest.fixture
def safe_layout(monkeypatch):
    def info(path):
        return SimpleNamespace(
            st_uid=0,
            st_mode=(
                stat.S_IFREG | 0o4755
                if path == "/usr/bin/sudo"
                else stat.S_IFDIR | 0o755
            ),
        )

    monkeypatch.setattr(trusted_sudo.os, "lstat", info)
    return info


@pytest.mark.parametrize("path", ["/", "/usr", "/usr/bin", "/usr/bin/sudo"])
@pytest.mark.parametrize(
    "defect", ["owner", "group_write", "world_write", "symlink", "wrong_type"]
)
def test_rejects_unsafe_layout(monkeypatch, safe_layout, path, defect):
    def info(candidate):
        result = safe_layout(candidate)
        if candidate == path:
            if defect == "owner":
                result.st_uid = 1000
            elif defect == "wrong_type":
                result.st_mode = stat.S_IFIFO | 0o755
            elif defect == "symlink":
                result.st_mode = stat.S_IFLNK | 0o777
            else:
                result.st_mode |= 0o020 if defect == "group_write" else 0o002
        return result

    monkeypatch.setattr(trusted_sudo.os, "lstat", info)
    with pytest.raises(PermissionError):
        trusted_sudo.trusted_sudo_path()
    assert not tooling.has_cmd("sudo")


def test_accepts_protected_layout(safe_layout):
    assert trusted_sudo.trusted_sudo_path() == "/usr/bin/sudo"
    assert tooling.get_cmd_path("sudo") == "/usr/bin/sudo"


def test_poisoned_path_never_receives_password(monkeypatch, tmp_path, safe_layout):
    fake = tmp_path / "sudo"
    fake.write_text("#!/bin/sh\nexit 99\n")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("LD_PRELOAD", "/attacker/plugin.so")
    monkeypatch.setenv("SUDO_ASKPASS", str(fake))
    calls = []

    def run(args, **kwargs):
        assert args[0] == "/usr/bin/sudo"
        assert kwargs["env"] == trusted_sudo.sudo_environment()
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0 if "-S" in args else 1, stdout="")

    monkeypatch.setattr(command.subprocess, "run", run)
    monkeypatch.setitem(
        sys.modules,
        "tkinter",
        SimpleNamespace(
            simpledialog=SimpleNamespace(
                askstring=lambda *a, **k: "synthetic-password"
            ),
            messagebox=SimpleNamespace(showerror=lambda *a, **k: None),
        ),
    )
    assert command.renew_sudo_timestamp()
    assert calls[0][0] == ["/usr/bin/sudo", "-n", "/usr/bin/true"]
    assert calls[1][1]["input"] == "synthetic-password\n"


@pytest.mark.parametrize("runner", [command.run_cmd, command.run_cmd_with_input])
def test_generic_runner_uses_boundary(monkeypatch, safe_layout, runner):
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="ok")

    monkeypatch.setattr(command.subprocess, "run", run)
    assert runner(["sudo", "-n", "true"]) == (0, "ok")
    assert calls[0][0][0] == "/usr/bin/sudo"
    assert calls[0][1]["env"] == trusted_sudo.sudo_environment()


def test_missing_sudo_never_prompts_or_executes(monkeypatch):
    def missing(*a, **k):
        raise FileNotFoundError("sudo unavailable")

    def forbidden(*a, **k):
        pytest.fail("unsafe executable or password dialog reached")

    monkeypatch.setattr(trusted_sudo.os, "lstat", missing)
    monkeypatch.setattr(command.subprocess, "run", forbidden)
    monkeypatch.setitem(
        sys.modules,
        "tkinter",
        SimpleNamespace(
            simpledialog=SimpleNamespace(askstring=forbidden),
            messagebox=None,
        ),
    )
    assert not command.renew_sudo_timestamp()
    assert not command.check_sudo_nopasswd()
    assert command.run_cmd(["sudo", "true"])[0] == 1
    assert command.run_cmd_with_input(["sudo", "true"])[0] == 1


def test_revalidates_after_password_dialog(monkeypatch, safe_layout):
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1, stdout="")

    def prompt(*a, **k):
        def missing(*a, **k):
            raise FileNotFoundError("sudo disappeared")

        monkeypatch.setattr(trusted_sudo.os, "lstat", missing)
        return "synthetic-password"

    monkeypatch.setattr(command.subprocess, "run", run)
    monkeypatch.setitem(
        sys.modules,
        "tkinter",
        SimpleNamespace(
            simpledialog=SimpleNamespace(askstring=prompt),
            messagebox=SimpleNamespace(showerror=lambda *a, **k: None),
        ),
    )
    assert not command.renew_sudo_timestamp()
    assert len(calls) == 1
    assert "-S" not in calls[0]


def test_nonexecutable_sudo_is_rejected(monkeypatch, safe_layout):
    def info(path):
        result = safe_layout(path)
        if path == "/usr/bin/sudo":
            result.st_mode &= ~0o111
        return result

    monkeypatch.setattr(trusted_sudo.os, "lstat", info)
    with pytest.raises(PermissionError):
        trusted_sudo.trusted_sudo_path()


@pytest.mark.parametrize("runner", [command.run_cmd, command.run_cmd_with_input])
def test_unprivileged_commands_keep_environment(monkeypatch, runner):
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="ok")

    monkeypatch.setattr(command.subprocess, "run", run)
    assert runner(["echo", "ok"]) == (0, "ok")
    assert calls[0][0] == ["echo", "ok"]
    assert calls[0][1]["env"] is None


@pytest.mark.parametrize("answer", [None, "synthetic-password"])
def test_cancel_or_failed_password_does_not_authorize(monkeypatch, safe_layout, answer):
    calls = []
    prompts = []

    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=1, stdout="")

    def prompt(*a, **k):
        prompts.append(True)
        return answer

    monkeypatch.setattr(command.subprocess, "run", run)
    monkeypatch.setitem(
        sys.modules,
        "tkinter",
        SimpleNamespace(
            simpledialog=SimpleNamespace(askstring=prompt),
            messagebox=SimpleNamespace(showerror=lambda *a, **k: None),
        ),
    )
    assert not command.renew_sudo_timestamp()
    assert len(prompts) == (1 if answer is None else 3)
    assert len(calls) == (1 if answer is None else 4)
