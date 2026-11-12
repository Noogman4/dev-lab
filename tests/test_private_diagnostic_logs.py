"""Confidential log output under synthetic paths; never touch host logs."""

import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from netmon import main
from netmon.app import App
from netmon.core import crash, diagnostics, private_logs, state


@pytest.fixture
def log_case(tmp_path, monkeypatch):
    docs = tmp_path / "Documents" / "NetMon"
    runtime = tmp_path / "state" / "netmon"
    for parent in (docs.parent, docs, runtime.parent, runtime):
        parent.mkdir(mode=0o755, exist_ok=True)
        parent.chmod(0o755)
    app = SimpleNamespace(
        netmon_state_dir=str(runtime),
        debug_network_logging=True,
        log_safe=lambda *_args: None,
        log_debug_safe=lambda *_args: None,
        tr=lambda _key, fallback: fallback,
    )
    app._runtime_log_paths = lambda: [
        str(docs / "Logs" / "runtime.log"),
        str(runtime / "logs" / "runtime.log"),
    ]
    app._network_debug_log_path = lambda: str(runtime / "logs" / "network_debug.log")
    monkeypatch.setattr(main, "get_netmon_documents_dir", lambda: str(docs))
    monkeypatch.setattr(diagnostics, "get_netmon_documents_dir", lambda: str(docs))
    monkeypatch.setattr(diagnostics, "diagnostic_system_info", lambda: {})
    monkeypatch.setattr(
        crash, "CRASH_LOG_PATH", str(docs / "diagnostics" / "crash.log")
    )
    report = docs / "diagnostics" / "report.json"
    monkeypatch.setattr(
        diagnostics, "diagnostic_report_path", lambda _kind: str(report)
    )
    paths = {
        "runtime": [Path(path) for path in app._runtime_log_paths()],
        "runtime-clear": [Path(path) for path in app._runtime_log_paths()],
        "network": [Path(app._network_debug_log_path())],
        "network-clear": [Path(app._network_debug_log_path())],
        "port": [runtime / "logs" / "port_check_debug.log"],
        "startup": [docs / "diagnostics" / "startup_error.log"],
        "crash": [Path(crash.CRASH_LOG_PATH)],
        "report": [report],
    }

    def write(kind):
        if kind == "runtime":
            return App._append_runtime_log_line(app, "sensitive runtime detail")
        if kind == "runtime-clear":
            return App._clear_runtime_log_file(app)
        if kind == "network":
            return App.log_network_debug(app, "sensitive network detail")
        if kind == "network-clear":
            return App.clear_network_debug_log_file(app)
        if kind == "port":
            return App._append_port_check_debug_log(app, {"host": "example.invalid"})
        if kind == "startup":
            return main._write_startup_error_log("sensitive startup detail")
        if kind == "crash":
            error = RuntimeError("sensitive crash detail")
            return crash._append_crash_dump("test", type(error), error, None)
        return diagnostics.write_diagnostic_report(
            kind="test", title="sensitive report"
        )

    return SimpleNamespace(paths=paths, write=write)


CASES = [
    (kind, existing)
    for kind in (
        "runtime",
        "runtime-clear",
        "network",
        "network-clear",
        "port",
        "startup",
        "crash",
        "report",
    )
    for existing in (False, True)
    if not (kind == "report" and existing)
]


@pytest.mark.parametrize("kind,existing", CASES)
@pytest.mark.parametrize("umask", [0, 0o022, 0o077])
def test_actual_writers_enforce_private_modes(log_case, kind, existing, umask):
    paths = log_case.paths[kind]
    if existing:
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("previous entry\n")
            path.chmod(0o644)
            path.parent.chmod(0o777)
    previous = os.umask(umask)
    try:
        log_case.write(kind)
        assert os.umask(umask) == umask  # No process-wide umask adjustment.
    finally:
        os.umask(previous)
    for path in paths:
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
        if kind.endswith("-clear"):
            assert path.read_bytes() == b""
        elif existing:
            assert path.read_text().startswith("previous entry\n")
        else:
            assert path.read_bytes()


@pytest.mark.parametrize(
    "kind",
    [
        "runtime",
        "runtime-clear",
        "network",
        "network-clear",
        "port",
        "startup",
        "crash",
        "report",
    ],
)
@pytest.mark.parametrize("attack", ["symlink", "hardlink", "fifo", "parent"])
def test_actual_writers_refuse_unsafe_destinations(log_case, tmp_path, kind, attack):
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("untouched")
    sentinel.chmod(0o644)
    for index, path in enumerate(log_case.paths[kind]):
        path.parent.mkdir(parents=True, exist_ok=True)
        if attack == "parent":
            outside = tmp_path / f"outside-{index}"
            outside.mkdir()
            (outside / path.name).write_text("untouched")
            path.parent.rmdir()
            path.parent.symlink_to(outside, target_is_directory=True)
        elif attack == "symlink":
            path.symlink_to(sentinel)
        elif attack == "hardlink":
            os.link(sentinel, path)
        else:
            os.mkfifo(path)
    log_case.write(kind)  # Logging fails safely rather than breaking the app.
    assert sentinel.read_text() == "untouched"
    assert stat.S_IMODE(sentinel.stat().st_mode) == 0o644
    if attack == "parent":
        for index, path in enumerate(log_case.paths[kind]):
            assert (
                tmp_path / f"outside-{index}" / path.name
            ).read_text() == "untouched"


@pytest.mark.parametrize(
    "getter",
    [
        state.get_netmon_state_dir,
        state.get_netmon_documents_dir,
    ],
)
def test_netmon_roots_are_private_without_chmodding_user_parent(
    tmp_path, monkeypatch, getter
):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(tmp_path))
    tmp_path.chmod(0o755)
    previous = os.umask(0)
    try:
        path = Path(getter())
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
        path.chmod(0o755)
        assert getter() == str(path)
        assert stat.S_IMODE(path.stat().st_mode) == 0o700
    finally:
        os.umask(previous)
    assert stat.S_IMODE(tmp_path.stat().st_mode) == 0o755


@pytest.mark.parametrize("mode", ["a", "w"])
@pytest.mark.parametrize("replacement", ["symlink", "regular"])
def test_leaf_exchange_is_rejected_before_chmod_or_truncate(
    tmp_path, monkeypatch, mode, replacement
):
    output = tmp_path / "log"
    output.write_text("original")
    victim = tmp_path / "victim"
    victim.write_text("victim")
    victim.chmod(0o644)
    original_open = os.open

    def swap(name, flags, *args, **kwargs):
        if name == output.name:
            output.unlink()
            if replacement == "symlink":
                output.symlink_to(victim)
            else:
                victim.rename(output)
        return original_open(name, flags, *args, **kwargs)

    monkeypatch.setattr(private_logs.os, "open", swap)
    with pytest.raises(OSError):
        with private_logs.open_private_log(output, mode) as log:
            log.write("must not write")
    remaining = victim if replacement == "symlink" else output
    assert remaining.read_text() == "victim"
    assert stat.S_IMODE(remaining.stat().st_mode) == 0o644


def test_directory_exchange_cannot_redirect_output(tmp_path, monkeypatch):
    folder = tmp_path / "logs"
    folder.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "runtime.log"
    victim.write_text("untouched")
    original = private_logs._open_file

    def swap(directory, name, mode):
        folder.rename(tmp_path / "held")
        folder.symlink_to(outside, target_is_directory=True)
        return original(directory, name, mode)

    monkeypatch.setattr(private_logs, "_open_file", swap)
    with private_logs.open_private_log(folder / "runtime.log") as output:
        output.write("private")
    assert victim.read_text() == "untouched"
    assert (tmp_path / "held" / "runtime.log").read_text() == "private"


@pytest.mark.parametrize("foreign", ["file", "directory"])
def test_foreign_owner_is_rejected_without_chmod(tmp_path, monkeypatch, foreign):
    output = tmp_path / "logs" / "runtime.log"
    output.parent.mkdir()
    output.write_text("untouched")
    output.chmod(0o644)
    selected = output if foreign == "file" else output.parent
    inode = selected.stat().st_ino
    original = os.fstat

    def fake_owner(fd):
        info = original(fd)
        if info.st_ino == inode:
            fields = list(info)
            fields[4] = os.geteuid() + 1
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(private_logs.os, "fstat", fake_owner)
    with pytest.raises(PermissionError):
        with private_logs.open_private_log(output, "w"):
            pytest.fail("Foreign destination was opened")
    assert output.read_text() == "untouched"
    assert stat.S_IMODE(output.stat().st_mode) == 0o644


def test_failed_permission_tightening_does_not_truncate(tmp_path, monkeypatch):
    output = tmp_path / "log"
    output.write_text("untouched")
    original = os.fchmod

    def fail_file(fd, mode):
        if stat.S_ISREG(os.fstat(fd).st_mode):
            raise PermissionError("synthetic chmod failure")
        return original(fd, mode)

    monkeypatch.setattr(private_logs.os, "fchmod", fail_file)
    with pytest.raises(PermissionError):
        with private_logs.open_private_log(output, "w"):
            pytest.fail("Unsafe truncation")
    assert output.read_text() == "untouched"


@pytest.mark.parametrize("kind", ["file", "symlink", "hardlink"])
def test_report_publication_never_replaces_existing_names(tmp_path, kind):
    output = tmp_path / "report.json"
    victim = tmp_path / "victim"
    victim.write_text("untouched")
    if kind == "file":
        output.write_text("original report")
    elif kind == "symlink":
        output.symlink_to(victim)
    else:
        os.link(victim, output)
    with pytest.raises(FileExistsError):
        private_logs.write_private_diagnostic_json(output, {"secret": "data"})
    assert victim.read_text() == "untouched"
    assert output.read_text() == ("original report" if kind == "file" else "untouched")
    assert not list(tmp_path.glob(".netmon-diagnostic-*.tmp"))


def test_report_publication_race_and_failure_leave_no_partial_output(
    tmp_path, monkeypatch
):
    output = tmp_path / "report.json"
    victim = tmp_path / "victim"
    victim.write_text("untouched")
    original = os.link

    def replace_destination(*args, **kwargs):
        output.symlink_to(victim)
        return original(*args, **kwargs)

    monkeypatch.setattr(private_logs.os, "link", replace_destination)
    with pytest.raises(FileExistsError):
        private_logs.write_private_diagnostic_json(output, {"secret": "data"})
    assert victim.read_text() == "untouched"
    assert not list(tmp_path.glob(".netmon-diagnostic-*.tmp"))


def test_report_fsync_failure_does_not_publish(tmp_path, monkeypatch):
    def fail(_fd):
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(private_logs.os, "fsync", fail)
    with pytest.raises(OSError):
        private_logs.write_private_diagnostic_json(tmp_path / "report.json", {})
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "special", ["root", "parent", "writable-ancestor", "repeated-name"]
)
def test_unsafe_directory_requests_never_change_ancestors(tmp_path, special):
    if special == "root":
        target = Path("/")
    elif special == "parent":
        target = tmp_path / ".." / "escape"
    else:
        parent = tmp_path / ("logs" if special == "repeated-name" else "shared")
        parent.mkdir()
        parent.chmod(0o777)
        target = parent / "logs"
    with pytest.raises(PermissionError):
        private_logs.ensure_private_log_directory(target)
    if special in {"writable-ancestor", "repeated-name"}:
        assert stat.S_IMODE(parent.stat().st_mode) == 0o777


def test_private_report_retains_valid_json(tmp_path):
    output = tmp_path / "report.json"
    private_logs.write_private_diagnostic_json(output, {"detail": "äöü"})
    assert json.loads(output.read_text()) == {"detail": "äöü"}


def test_new_state_ancestors_are_private_under_zero_umask(tmp_path, monkeypatch):
    base = tmp_path / "new-xdg-state"
    monkeypatch.setenv("XDG_STATE_HOME", str(base))
    previous = os.umask(0)
    try:
        path = Path(state.get_netmon_state_dir())
    finally:
        os.umask(previous)
    assert stat.S_IMODE(base.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o700
