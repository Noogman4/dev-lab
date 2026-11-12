"""Swap resize must not let a replaced pathname redirect root writes.

The root-only parts (swapoff/swapon) are simulated; directory pinning,
exclusive creation, allocation and the real mkswap run on the test's files.
"""

import os
import stat
import subprocess
import sys

import pytest

from netmon.core import swap_resize


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


def test_root_command_runs_self_contained_source_in_isolated_python():
    argv = swap_resize.root_command("/swapfile", 8)
    assert argv[:5] == ["sudo", "-n", "/usr/bin/python3", "-I", "-c"]
    assert argv[6:] == ["resize", "/swapfile", "8"]
    # The source must run standalone (stdlib only) and refuse without root.
    result = subprocess.run(
        [sys.executable, "-I", "-c", argv[5], *argv[6:]],
        capture_output=True,
        text=True,
        timeout=20,
        cwd="/",
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
    )
    if os.geteuid() != 0:
        assert result.returncode == 2
        assert "root" in result.stderr


def test_app_resize_job_uses_single_pinned_root_process():
    import inspect

    from netmon.app import App

    source = inspect.getsource(App.resize_swap_async)
    assert "swap_resize.root_command(swapfile, target_gib)" in source
    assert "swap_resize.precheck(swapfile)" in source
    for path_command in ('"rm"', '"fallocate"', '"chmod"', "of={swapfile}"):
        assert path_command not in source
