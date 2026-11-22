"""Swap resize must not let a replaced pathname redirect root writes.

The root-only parts (swapoff/swapon) are simulated; directory pinning,
exclusive creation, allocation and the real mkswap run on the test's files.
"""

import os
import stat
import subprocess
import sys

import pytest

from netmon.core import privilege_launcher, swap_resize, trusted_sudo


@pytest.fixture(autouse=True)
def trusted_system_layout(monkeypatch):
    """Model only system ownership; keep actual descriptors, modes and inodes."""
    lstat_original, fstat_original = os.lstat, os.fstat
    directories = {"/", "/usr", "/usr/sbin"}

    def root_owned(info):
        fields = list(info)
        fields[4] = 0
        return os.stat_result(fields)

    def lstat(path, *args, **kwargs):
        info = lstat_original(path, *args, **kwargs)
        if os.fsdecode(path) in directories | {swap_resize.MKSWAP}:
            return root_owned(info)
        return info

    def fstat(fd):
        info = fstat_original(fd)
        if os.readlink(f"/proc/self/fd/{fd}") in directories:
            return root_owned(info)
        return info

    monkeypatch.setattr(swap_resize.os, "lstat", lstat)
    monkeypatch.setattr(swap_resize.os, "fstat", fstat)


class FakeLibc:
    """Records swap syscalls and resolves the magic link like the kernel."""

    def __init__(self, active, *, on_swapoff=None, fail_swapon=False):
        self.calls = []
        self.active = active
        self.on_swapoff = on_swapoff
        self.fail_swapon = fail_swapon

    def _target(self, raw):
        path = os.fsdecode(raw)
        assert path.startswith("/proc/self/fd/"), "pathname must never be used"
        return os.readlink(path), os.stat(path)

    def swapoff(self, raw):
        target, info = self._target(raw)
        self.calls.append(("swapoff", target, info.st_ino))
        if self.on_swapoff:
            self.on_swapoff()
        return 0

    def swapon(self, raw, flags):
        target, info = self._target(raw)
        self.calls.append(("swapon", target, info.st_ino, flags))
        if self.fail_swapon:
            return -1
        self.active.append(target)
        return 0


@pytest.fixture
def swap_env(tmp_path, monkeypatch):
    """A pinned swap directory owned by the test user standing in for root."""
    swap_dir = tmp_path / "swapdir"
    swap_dir.mkdir(mode=0o755)
    swapfile = swap_dir / "swapfile"
    swapfile.write_bytes(b"old" * 1000)
    swapfile.chmod(0o600)
    path = str(swapfile)
    active = [path]
    proc_swaps = tmp_path / "proc_swaps"

    def write_proc_swaps():
        proc_swaps.write_text(
            "Filename\tType\tSize\tUsed\tPriority\n"
            + "".join(f"{p}\tfile\t4\t0\t-2\n" for p in active)
        )

    write_proc_swaps()
    monkeypatch.setattr(swap_resize, "_ROOT_UID", os.geteuid())
    monkeypatch.setattr(swap_resize, "GIB_BYTES", 1024 * 1024)

    def pinned_parent(requested):
        assert requested == path
        fd = os.open(str(swap_dir), swap_resize._DIR_FLAGS)
        return fd, "swapfile"

    monkeypatch.setattr(swap_resize, "open_trusted_parent", pinned_parent)
    return {
        "dir": swap_dir,
        "path": path,
        "active": active,
        "proc_swaps": proc_swaps,
        "write_proc_swaps": write_proc_swaps,
    }


def _resize(env, libc, gib=2, run=subprocess.run):
    def swap_off_then_record():
        env["active"].remove(env["path"])
        env["write_proc_swaps"]()

    original = libc.on_swapoff

    def on_swapoff():
        swap_off_then_record()
        if original:
            original()

    libc.on_swapoff = on_swapoff
    real_swapon = libc.swapon

    def swapon(raw, flags):
        rc = real_swapon(raw, flags)
        env["write_proc_swaps"]()
        return rc

    libc.swapon = swapon
    return swap_resize.resize(
        env["path"], gib, libc=libc, run=run, proc_swaps=str(env["proc_swaps"])
    )


def test_resize_recreates_file_through_descriptors(swap_env):
    libc = FakeLibc(swap_env["active"])

    assert _resize(swap_env, libc, gib=2) == 2 * 1024 * 1024

    info = os.stat(swap_env["path"])
    assert stat.S_IMODE(info.st_mode) == 0o600
    assert info.st_size == 2 * 1024 * 1024
    with open(swap_env["path"], "rb") as handle:
        assert b"old" not in handle.read(64)  # recreated, not reused
    with open(swap_env["path"], "rb") as handle:
        handle.seek(4096 - 10)
        assert handle.read(10) == b"SWAPSPACE2"  # real mkswap ran on the fd
    assert [c[0] for c in libc.calls] == ["swapoff", "swapon"]
    assert libc.calls[0][1] == swap_env["path"]
    assert libc.calls[1][1] == swap_env["path"]


def test_replaced_directory_cannot_redirect_root_writes(swap_env, tmp_path):
    """Attacker swaps the swap directory for a symlink right after swapoff."""
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "swapfile").write_bytes(b"precious")
    moved = tmp_path / "swapdir-moved"

    def replace_directory():
        os.rename(swap_env["dir"], moved)
        os.symlink(victim, swap_env["dir"])

    libc = FakeLibc(swap_env["active"], on_swapoff=replace_directory)
    with pytest.raises(swap_resize.SwapResizeError):
        # The pathname no longer leads to the new file, so activation via
        # /proc/swaps cannot be confirmed - but nothing was written there.
        _resize(swap_env, libc)

    assert (victim / "swapfile").read_bytes() == b"precious"
    assert sorted(os.listdir(victim)) == ["swapfile"]
    new_file = moved / "swapfile"
    assert new_file.stat().st_size == 2 * 1024 * 1024
    swapon = [c for c in libc.calls if c[0] == "swapon"][0]
    assert swapon[1] == str(new_file)


def test_symlinked_swap_file_is_refused_before_swapoff(swap_env, tmp_path):
    target = tmp_path / "elsewhere"
    target.write_bytes(b"x")
    os.unlink(swap_env["path"])
    os.symlink(target, swap_env["path"])
    libc = FakeLibc(swap_env["active"])

    with pytest.raises(swap_resize.SwapResizeError):
        _resize(swap_env, libc)
    assert libc.calls == []
    assert target.read_bytes() == b"x"


@pytest.mark.parametrize("fault", ["hardlink", "readable"])
def test_untrusted_swap_file_is_refused_before_swapoff(swap_env, tmp_path, fault):
    if fault == "hardlink":
        os.link(swap_env["path"], tmp_path / "second-link")
    else:
        os.chmod(swap_env["path"], 0o644)
    libc = FakeLibc(swap_env["active"])

    with pytest.raises(swap_resize.SwapResizeError):
        _resize(swap_env, libc)
    assert libc.calls == []


def test_inactive_path_is_refused_before_any_change(swap_env):
    swap_env["active"].clear()
    swap_env["write_proc_swaps"]()
    libc = FakeLibc(swap_env["active"])
    before = os.stat(swap_env["path"])

    with pytest.raises(swap_resize.SwapResizeError, match="keine aktive"):
        swap_resize.resize(
            swap_env["path"], 2, libc=libc, proc_swaps=str(swap_env["proc_swaps"])
        )
    assert libc.calls == []
    assert os.stat(swap_env["path"]).st_ino == before.st_ino


def test_mkswap_failure_reports_swap_off_and_removes_partial_file(swap_env):
    libc = FakeLibc(swap_env["active"])

    def failing_mkswap(*_args, **_kwargs):
        return subprocess.CompletedProcess([], 1, "", "mkswap: kaputt")

    with pytest.raises(swap_resize.SwapResizeError, match="Swap ist deaktiviert"):
        _resize(swap_env, libc, run=failing_mkswap)
    assert not os.path.lexists(swap_env["path"])
    assert [c[0] for c in libc.calls] == ["swapoff"]


@pytest.mark.parametrize("fault", ["owner", "writable", "symlink"])
def test_untrusted_mkswap_is_refused_before_swapoff(swap_env, monkeypatch, fault):
    original = os.lstat

    def untrusted(path, *args, **kwargs):
        info = original(path, *args, **kwargs)
        if os.fsdecode(path) != swap_resize.MKSWAP:
            return info
        fields = list(info)
        if fault == "owner":
            fields[4] = 1000
        elif fault == "writable":
            fields[0] |= stat.S_IWGRP
        else:
            fields[0] = stat.S_IFLNK | 0o777
        return os.stat_result(fields)

    monkeypatch.setattr(swap_resize.os, "lstat", untrusted)
    libc = FakeLibc(swap_env["active"])
    with pytest.raises(swap_resize.SwapResizeError, match="Unsicher"):
        _resize(swap_env, libc)
    assert libc.calls == []


@pytest.mark.parametrize(
    "path",
    [
        "relative",
        "/",
        "/a/../swapfile",
        "/a//swapfile",
        "/a/./swapfile",
        "/swapfile\n",
        "/dev/swapfile",
        "/proc/self/fd/3",
        "/sys/swapfile",
    ],
)
def test_noncanonical_or_virtual_paths_are_refused(path):
    with pytest.raises(swap_resize.SwapResizeError):
        swap_resize.validate_path(path)


@pytest.mark.parametrize("value", ["0", "65", "-1", "08", "4.0", "x", ""])
def test_size_outside_range_is_refused(value):
    with pytest.raises(swap_resize.SwapResizeError):
        swap_resize.validate_gib(value)


def test_user_owned_ancestor_is_refused(tmp_path):
    path = tmp_path / "swapfile"
    path.write_bytes(b"x")
    with pytest.raises(swap_resize.SwapResizeError, match="root"):
        swap_resize.open_trusted_parent(str(path))


def test_root_owned_directories_are_pinned_without_following_links():
    fd, name = swap_resize.open_trusted_parent("/usr/swapfile")
    try:
        assert name == "swapfile"
        assert os.path.samestat(os.fstat(fd), os.stat("/usr"))
    finally:
        os.close(fd)
    if os.path.islink("/lib"):
        with pytest.raises(OSError):
            swap_resize.open_trusted_parent("/lib/swapfile")


def test_precheck_refuses_user_writable_location(tmp_path):
    path = tmp_path / "swapfile"
    path.write_bytes(b"x")
    with pytest.raises(swap_resize.SwapResizeError):
        swap_resize.precheck(str(path))


def test_proc_swaps_paths_are_unescaped(tmp_path):
    table = tmp_path / "swaps"
    table.write_text(
        "Filename\tType\tSize\tUsed\tPriority\n"
        "/swap\\040dir/swapfile file 4 0 -2\n"
        "/dev/sda2 partition 4 0 -3\n"
    )
    assert swap_resize.active_swap_files(str(table)) == {"/swap dir/swapfile"}


@pytest.fixture
def installed_helper(tmp_path, monkeypatch):
    helper = tmp_path / "swap_resize.py"
    helper.write_text("# Installed file fixture\n", encoding="utf-8")
    helper.chmod(0o644)

    def trusted_parent(path):
        assert path == "/usr/lib/netmon/netmon/core/swap_resize.py"
        return os.open(tmp_path, swap_resize._DIR_FLAGS), helper.name

    monkeypatch.setattr(swap_resize, "open_trusted_parent", trusted_parent)
    monkeypatch.setattr(swap_resize, "_ROOT_UID", os.geteuid())
    return helper


@pytest.mark.parametrize("unsafe", ["missing", "owner", "mode", "symlink", "hardlink"])
def test_installed_helper_refuses_unsafe_file(installed_helper, monkeypatch, unsafe):
    if unsafe == "missing":
        installed_helper.unlink()
    elif unsafe == "owner":
        monkeypatch.setattr(swap_resize, "_ROOT_UID", os.geteuid() + 1)
    elif unsafe == "mode":
        installed_helper.chmod(0o664)
    elif unsafe == "symlink":
        original = installed_helper.with_suffix(".original")
        installed_helper.rename(original)
        installed_helper.symlink_to(original)
    elif unsafe == "hardlink":
        os.link(installed_helper, installed_helper.with_suffix(".alias"))

    with pytest.raises(swap_resize.SwapResizeError, match="Swap-Helfer"):
        swap_resize.trusted_helper_path()


def test_root_command_runs_only_the_installed_helper(installed_helper, monkeypatch):
    monkeypatch.setattr(swap_resize, "__file__", "/unavailable-checkout/swap_resize.py")
    monkeypatch.setattr(trusted_sudo, "trusted_sudo_path", lambda: "/usr/bin/sudo")
    monkeypatch.setattr(
        privilege_launcher, "trusted_system_executable", lambda name: "/usr/bin/" + name
    )

    argv = swap_resize.root_command("/swapfile", 8)
    assert argv == [
        "/usr/bin/sudo",
        "-n",
        "--",
        "/usr/bin/python3",
        "-I",
        "/usr/lib/netmon/netmon/core/swap_resize.py",
        "resize",
        "/swapfile",
        "8",
    ]


def test_helper_runs_standalone_and_refuses_without_root():
    if os.geteuid() == 0:
        pytest.skip("This probe intentionally runs unprivileged")
    result = subprocess.run(
        [sys.executable, "-I", swap_resize.__file__, "resize", "/swapfile", "8"],
        capture_output=True,
        text=True,
        timeout=20,
        cwd="/",
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
    )
    assert result.returncode == 2
    assert "root" in result.stderr


def test_app_blocks_resize_without_trusted_helper_before_sudo(monkeypatch):
    from netmon import app as app_module

    app = app_module.App.__new__(app_module.App)
    warnings = []
    app._detect_supported_swapfile = lambda: "/swapfile"
    app.log_safe = lambda _message: None
    app.ensure_sudo_session = lambda *_args: pytest.fail("Unexpected sudo request")

    def unsafe_parent(_path):
        raise PermissionError("Writable ancestor")

    monkeypatch.setattr(swap_resize, "open_trusted_parent", unsafe_parent)
    monkeypatch.setattr(
        app_module.simpledialog,
        "askinteger",
        lambda *_args, **_kwargs: pytest.fail("Unexpected size prompt"),
    )
    monkeypatch.setattr(
        app_module.messagebox,
        "showwarning",
        lambda _title, message, **_kwargs: warnings.append(message),
    )

    app.resize_swap_async()

    assert len(warnings) == 1 and "Swap-Helfer" in warnings[0]


def test_app_restores_swap_controls_if_helper_is_later_unavailable(monkeypatch):
    from netmon import app as app_module

    app = app_module.App.__new__(app_module.App)
    logs = []
    buttons = []
    app._detect_supported_swapfile = lambda: "/swapfile"
    app._read_swapfile_size_bytes = lambda _path: 1024**3
    app._read_swap_usage = lambda: (0, 0, 0)
    app._read_ram_available_bytes = lambda: 0
    app._confirm_danger_action = lambda *_args, **_kwargs: True
    app.ensure_sudo_session = lambda _reason: True
    app._set_swap_action_buttons_enabled = buttons.append
    app.log_safe = logs.append
    app.after = lambda _delay, callback: callback()

    def helper_disappeared(_path, _gib):
        raise swap_resize.SwapResizeError("Helper unavailable")

    class ImmediateThread:
        def __init__(self, *, target, daemon):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(swap_resize, "trusted_helper_path", lambda: swap_resize.HELPER)
    monkeypatch.setattr(swap_resize, "precheck", lambda _path: None)
    monkeypatch.setattr(swap_resize, "root_command", helper_disappeared)
    monkeypatch.setattr(app_module.simpledialog, "askinteger", lambda *_a, **_k: 2)
    monkeypatch.setattr(app_module.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        app_module, "run_cmd", lambda *_a, **_k: pytest.fail("Unexpected root command")
    )

    app.resize_swap_async()

    assert buttons == [False, True]
    assert logs[-1] == "Swap resize failed: Helper unavailable"


def test_app_resize_job_uses_single_pinned_root_process():
    import inspect

    from netmon.app import App

    source = inspect.getsource(App.resize_swap_async)
    assert "swap_resize.root_command(swapfile, target_gib)" in source
    assert "swap_resize.precheck(swapfile)" in source
    for path_command in ('"rm"', '"fallocate"', '"chmod"', "of={swapfile}"):
        assert path_command not in source
