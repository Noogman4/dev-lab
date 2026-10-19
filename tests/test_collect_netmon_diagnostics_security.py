"""Isolated regression tests: no real process, socket or kernel diagnostics."""

import errno
import importlib.util
import io
import os
import stat
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "diagnostics_output", ROOT / "scripts/diagnostics_output.py"
)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)


@pytest.fixture(autouse=True)
def restore_umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)


@pytest.fixture
def fake_environment(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    for name in ("ps", "ss", "journalctl", "dmesg", "hostname", "uname", "date"):
        command = bindir / name
        command.write_text("#!/bin/sh\nprintf 'SYNTHETIC-DIAGNOSTIC\\n'\n")
        command.chmod(0o755)
    return dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", TMPDIR=str(tmp_path))


def run_script(script, env, *args):
    return subprocess.run(
        ["bash", str(script), *map(str, args)],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_original_follows_symlink(tmp_path, fake_environment):
    old = subprocess.check_output(
        ["git", "show", "c6a6c5bf:scripts/collect_netmon_diagnostics.sh"], cwd=ROOT
    )
    script = tmp_path / "original.sh"
    script.write_bytes(old)
    victim = tmp_path / "victim"
    victim.write_text("KEEP")
    target = tmp_path / "output"
    target.symlink_to(victim)
    result = run_script(script, fake_environment, target)
    assert result.returncode == 0
    assert "SYNTHETIC-DIAGNOSTIC" in victim.read_text()
    assert victim.read_text() != "KEEP"


def test_default_is_private_and_unpredictable(tmp_path, fake_environment):
    paths = []
    for _ in range(2):
        result = run_script(
            ROOT / "scripts/collect_netmon_diagnostics.sh", fake_environment
        )
        assert result.returncode == 0, result.stderr
        path = Path(result.stdout.strip().removeprefix("Diagnostics written to "))
        assert path.parent.parent == tmp_path
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
        assert "SYNTHETIC-DIAGNOSTIC" in path.read_text()
        assert "Listening Sockets" in path.read_text()
        paths.append(path)
    assert paths[0] != paths[1]


@pytest.mark.parametrize(
    "kind", ["file", "foreign", "symlink", "dangling", "fifo", "directory", "hardlink"]
)
def test_existing_target_is_never_opened(tmp_path, fake_environment, kind):
    victim = tmp_path / "victim"
    victim.write_text("KEEP")
    target = tmp_path / "output"
    if kind in ("file", "foreign"):
        target.write_text("KEEP")
        if kind == "foreign":
            if os.geteuid() != 0:
                pytest.skip("Requires chown in isolated temporary directory")
            try:
                os.chown(target, 65534, 65534)
            except OSError as error:
                if error.errno in (errno.EINVAL, errno.EPERM):
                    pytest.skip("Container has no mapped second UID for real chown")
                raise
    elif kind == "symlink":
        target.symlink_to(victim)
    elif kind == "dangling":
        target.symlink_to(tmp_path / "missing")
    elif kind == "fifo":
        os.mkfifo(target)
    elif kind == "directory":
        target.mkdir()
    else:
        os.link(victim, target)
    before = target.lstat()
    result = run_script(
        ROOT / "scripts/collect_netmon_diagnostics.sh", fake_environment, target
    )
    assert result.returncode != 0
    assert "Diagnostics written to" not in result.stdout
    assert target.lstat().st_ino == before.st_ino
    assert victim.read_text() == "KEEP"
    if kind in ("file", "foreign", "hardlink"):
        assert target.read_text() == "KEEP"


def test_explicit_output_and_missing_parents(tmp_path, fake_environment):
    target = tmp_path / "new dir" / "output.txt"
    result = run_script(
        ROOT / "scripts/collect_netmon_diagnostics.sh", fake_environment, target
    )
    assert result.returncode == 0, result.stderr
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert "SYNTHETIC-DIAGNOSTIC" in target.read_text()
    assert list(target.parent.iterdir()) == [target]


@pytest.mark.parametrize("symlink", [False, True])
def test_publication_race_preserves_other_file(tmp_path, monkeypatch, symlink):
    target = tmp_path / "output"
    original_link = writer.os.link

    def race(*args, **kwargs):
        if symlink:
            target.symlink_to(tmp_path / "race-victim")
            (tmp_path / "race-victim").write_text("RACE-WINNER")
        else:
            target.write_text("RACE-WINNER")
        return original_link(*args, **kwargs)

    monkeypatch.setattr(writer.os, "link", race)
    with pytest.raises(FileExistsError):
        writer.write_diagnostics(io.BytesIO(b"PRIVATE"), target)
    assert target.read_text() == "RACE-WINNER"
    expected = {target, tmp_path / "race-victim"} if symlink else {target}
    assert set(tmp_path.iterdir()) == expected


def test_write_failure_does_not_publish(tmp_path):
    class BrokenStream:
        def read(self, size):
            raise OSError("synthetic read failure")

    target = tmp_path / "output"
    with pytest.raises(OSError, match="synthetic"):
        writer.write_diagnostics(BrokenStream(), target)
    assert list(tmp_path.iterdir()) == []


def test_missing_python_is_failure(tmp_path, fake_environment):
    env = dict(fake_environment, PATH=str(tmp_path / "bin"))
    result = subprocess.run(
        ["/bin/bash", str(ROOT / "scripts/collect_netmon_diagnostics.sh")],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "Diagnostics written to" not in result.stdout


def test_fsync_failure_does_not_publish(tmp_path, monkeypatch):
    def fail(fd):
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(writer.os, "fsync", fail)
    with pytest.raises(OSError, match="synthetic fsync"):
        writer.write_diagnostics(io.BytesIO(b"PRIVATE"), tmp_path / "output")
    assert list(tmp_path.iterdir()) == []


def test_parallel_publication_has_exactly_one_winner(tmp_path, fake_environment):
    target = tmp_path / "output"
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(
                lambda _: run_script(
                    ROOT / "scripts/collect_netmon_diagnostics.sh",
                    fake_environment,
                    target,
                ),
                range(4),
            )
        )
    assert sum(result.returncode == 0 for result in results) == 1
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert set(tmp_path.iterdir()) == {tmp_path / "bin", target}
