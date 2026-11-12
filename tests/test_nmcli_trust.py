"""Synthetic NetworkManager identities; installed nmcli/sudo are never run."""

import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

from netmon.core import command, tooling, trusted_sudo
from netmon.services.dns_control_service import DNSControlService

REAL_UUID = "12345678-1234-5678-9012-123456789abc"
FAKE_UUID = "87654321-4321-8765-2109-cba987654321"
TARGET = ("eth0", "Wired")
PROPS = ("ipv4.ignore-auto-dns", "ipv6.ignore-auto-dns", "ipv4.dns", "ipv6.dns")


@pytest.fixture
def protected_layout(monkeypatch):
    original = os.lstat

    def info(path, *args, **kwargs):
        entry = original(path, *args, **kwargs)
        if os.fspath(path) in {
            "/",
            "/usr",
            "/usr/bin",
            "/usr/bin/sudo",
            "/usr/bin/nmcli",
        }:
            values = list(entry)
            values[4] = 0  # Model host root ownership inside the user namespace.
            return os.stat_result(values)
        return entry

    monkeypatch.setattr(trusted_sudo.os, "lstat", info)
    return info


@pytest.mark.parametrize("unsafe_before_write", [False, True])
def test_path_fake_cannot_choose_uuid_sent_to_privileged_nmcli(
    tmp_path, monkeypatch, protected_layout, unsafe_before_write
):
    state_path = tmp_path / "fake-state.json"
    state_path.write_text(json.dumps(["no", "no", "8.8.8.8", ""]))
    marker = tmp_path / "fake-executed"
    fake = tmp_path / "nmcli"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\nfrom pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "if sys.argv[1] == '-t':\n"
        "    print('Wired:eth0:802-3-ethernet')\n"
        "elif sys.argv[2] == 'GENERAL.CON-UUID':\n"
        f"    print({FAKE_UUID!r})\n"
        "else:\n"
        f"    props = json.loads(Path({str(state_path)!r}).read_text())\n"
        f"    print('\\n'.join([{FAKE_UUID!r}, 'eth0', '802-3-ethernet', *props]))\n"
    )
    fake.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("DBUS_SYSTEM_BUS_ADDRESS", "unix:path=/attacker/bus")
    original_run = subprocess.run
    calls, writes = [], []
    real_props = ["no", "no", "8.8.8.8", ""]
    active_reads = 0
    refuse_nmcli = False

    def info(path, *args, **kwargs):
        entry = protected_layout(path, *args, **kwargs)
        if os.fspath(path) == "/usr/bin/nmcli" and refuse_nmcli:
            values = list(entry)
            values[0] |= 0o020
            return os.stat_result(values)
        return entry

    monkeypatch.setattr(trusted_sudo.os, "lstat", info)

    def run(args, **kwargs):
        nonlocal active_reads, refuse_nmcli
        args = list(args)
        calls.append((args, kwargs.get("env")))
        if args[0] == "nmcli":
            # Faithfully model PATH lookup, then execute only our harmless fake.
            search = (kwargs.get("env") or os.environ)["PATH"]
            assert shutil.which("nmcli", path=search) == str(fake)
            return original_run([str(fake), *args[1:]], **kwargs)
        if args[0] == "/usr/bin/nmcli":
            assert kwargs["env"] == trusted_sudo.sudo_environment()
            if args[1] == "-t":
                out = "Wired:eth0:802-3-ethernet\n"
            elif args[2] == "GENERAL.CON-UUID":
                out = REAL_UUID + "\n"
                active_reads += 1
                if unsafe_before_write and active_reads == 2:
                    refuse_nmcli = True
            else:
                out = (
                    "\n".join([REAL_UUID, "eth0", "802-3-ethernet", *real_props]) + "\n"
                )
            return subprocess.CompletedProcess(args, 0, out)
        if args[0] == "/usr/bin/sudo":
            assert kwargs["env"] == trusted_sudo.sudo_environment()
            assert args[2] in {"nmcli", "/usr/bin/nmcli"}
            assert args[5] == "uuid"
            writes.append(args)
            if args[4] == "mod":
                values = dict(zip(PROPS, real_props))
                values.update(zip(args[7::2], args[8::2]))
                real_props[:] = [values[key] for key in PROPS]
                state_path.write_text(json.dumps(real_props))
            return subprocess.CompletedProcess(args, 0, "")
        pytest.fail(f"Unmodelled command: {args}")

    monkeypatch.setattr(command.subprocess, "run", run)
    service = DNSControlService(
        command.run_cmd,
        tooling.has_cmd,
        dot_dropin_path=str(tmp_path / "unused.conf"),
        dot_dropin_dir=str(tmp_path),
    )
    targets = service.active_nm_dns_targets()
    ok, details = service.apply_nm_dns_policy_to_targets(
        ignore_auto_dns=True, targets=targets
    )
    if unsafe_before_write:
        assert not ok and details
        assert writes == [], "Unsafe executable reached a root mutation"
    else:
        assert ok, details
        assert len(writes) == 2
        assert {args[6] for args in writes} == {REAL_UUID}, writes
        assert all(args[2] == "/usr/bin/nmcli" for args in writes)
    assert not marker.exists(), "PATH-precedent nmcli was executed"
    assert all(env == trusted_sudo.sudo_environment() for _args, env in calls)


@pytest.mark.parametrize("path", ["/", "/usr", "/usr/bin", "/usr/bin/nmcli"])
@pytest.mark.parametrize(
    "defect", ["owner", "group_write", "world_write", "symlink", "type"]
)
def test_nmcli_requires_protected_executable_and_ancestors(
    monkeypatch, protected_layout, path, defect
):
    def info(candidate, *args, **kwargs):
        entry = protected_layout(candidate, *args, **kwargs)
        if os.fspath(candidate) != path:
            return entry
        values = list(entry)
        if defect == "owner":
            values[4] = 1000
        elif defect == "group_write":
            values[0] |= 0o020
        elif defect == "world_write":
            values[0] |= 0o002
        elif defect == "symlink":
            values[0] = stat.S_IFLNK | 0o777
        else:
            values[0] = (
                stat.S_IFDIR | 0o755
                if candidate == "/usr/bin/nmcli"
                else stat.S_IFREG | 0o755
            )
        return os.stat_result(values)

    monkeypatch.setattr(trusted_sudo.os, "lstat", info)
    with pytest.raises(PermissionError):
        trusted_sudo.trusted_nmcli_path()
    assert tooling.get_cmd_path("nmcli") == ""


@pytest.mark.parametrize("defect", ["missing", "not-executable"])
@pytest.mark.parametrize("runner", [command.run_cmd, command.run_cmd_with_input])
@pytest.mark.parametrize("privileged", [False, True])
def test_unusable_nmcli_never_falls_back_to_path(
    monkeypatch, tmp_path, protected_layout, defect, runner, privileged
):
    fake = tmp_path / "nmcli"
    fake.write_text("synthetic PATH-precedent tool")
    fake.chmod(0o700)
    monkeypatch.setenv("PATH", str(tmp_path))

    def info(path, *args, **kwargs):
        if os.fspath(path) == "/usr/bin/nmcli" and defect == "missing":
            raise FileNotFoundError(path)
        entry = protected_layout(path, *args, **kwargs)
        if os.fspath(path) == "/usr/bin/nmcli":
            values = list(entry)
            values[0] &= ~0o111
            return os.stat_result(values)
        return entry

    monkeypatch.setattr(trusted_sudo.os, "lstat", info)
    monkeypatch.setattr(
        command.subprocess, "run", lambda *_a, **_kw: pytest.fail("Unsafe spawn")
    )
    args = ["nmcli", "con", "show"]
    if privileged:
        args = ["sudo", "-n", *args]
    assert runner(args)[0] != 0
    assert tooling.get_cmd_path("nmcli") == ""


@pytest.mark.parametrize("runner", [command.run_cmd, command.run_cmd_with_input])
@pytest.mark.parametrize(
    "args,index",
    [
        (["nmcli", "con", "show"], 0),
        (["/attacker/nmcli", "con", "show"], 0),
        (["sudo", "-n", "nmcli", "con", "show"], 2),
        (["/attacker/sudo", "-n", "--", "/attacker/nmcli", "con", "show"], 3),
        (["sudo", "--non-interactive", "--", "nmcli", "con", "show"], 3),
        (["sudo", "-S", "-H", "nmcli", "con", "show"], 3),
    ],
)
def test_nmcli_readers_and_writers_share_identity_and_minimal_environment(
    monkeypatch, protected_layout, runner, args, index
):
    for name in (
        "PATH",
        "LD_PRELOAD",
        "GIO_EXTRA_MODULES",
        "DBUS_SYSTEM_BUS_ADDRESS",
        "LC_ALL",
    ):
        monkeypatch.setenv(name, "/attacker/environment")
    calls = []

    def run(argv, **kwargs):
        calls.append(argv)
        assert argv[index] == "/usr/bin/nmcli"
        if index:
            assert argv[0] == "/usr/bin/sudo"
        assert kwargs["env"] == {
            "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
            "LANG": "C",
            "LC_ALL": "C",
        }
        return subprocess.CompletedProcess(argv, 0, "ok")

    monkeypatch.setattr(command.subprocess, "run", run)
    assert runner(args) == (0, "ok")
    assert len(calls) == 1
    assert tooling.get_cmd_path("nmcli") == "/usr/bin/nmcli"


def test_sudo_option_argument_is_not_treated_as_a_command(protected_layout):
    assert trusted_sudo.trusted_command_args(["sudo", "-u", "nmcli", "echo", "ok"]) == [
        "/usr/bin/sudo",
        "-u",
        "nmcli",
        "echo",
        "ok",
    ]
