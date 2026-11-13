"""Pre-quarantine import and clean release use synthetic files only."""

import hashlib
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from netmon import app as app_module
from netmon.core import download_scan_fs as dfs
from netmon.features import clamav_controller as controller


@pytest.fixture
def workspace(tmp_path):
    temporary = tmp_path / "pre-quarantine"
    temporary.mkdir(mode=0o700)
    target = tmp_path / "Downloads"
    target.mkdir()
    app = app_module.App.__new__(app_module.App)
    app._normalized_download_scan_temp_dir = lambda: str(temporary)
    app._normalized_download_scan_target_dir = lambda: str(target)
    app.download_scan_auto_move_var = SimpleNamespace(get=lambda: True)
    app.download_scan_ask_before_move_var = SimpleNamespace(get=lambda: False)
    app.log_safe = lambda *_: None
    return app, temporary, target


def test_import_does_not_write_through_dangling_destination_symlink(
    workspace, tmp_path
):
    app, temporary, _target = workspace
    source = tmp_path / "download.bin"
    source.write_bytes(b"download content")
    victim = tmp_path / "private-file"
    (temporary / source.name).symlink_to(victim)
    imported, _origin = app._download_scan_import_file_to_temp(str(source))
    assert not victim.exists(), "Import followed a planted destination symlink"
    assert open(imported, "rb").read() == b"download content"


@pytest.mark.parametrize("stage", ["scan", "report", "confirmation"])
@pytest.mark.parametrize("change", ["replacement", "symlink", "in-place"])
def test_replacement_after_scan_cannot_be_released_as_clean(
    workspace, monkeypatch, stage, change
):
    app, temporary, target = workspace
    source = temporary / "download.bin"
    source.write_bytes(b"synthetic clean bytes")
    replacement = temporary / "replacement"
    replacement.write_bytes(b"unscanned replacement")
    original_stat = source.stat()

    def mutate():
        if change == "replacement":
            replacement.replace(source)
        elif change == "symlink":
            source.unlink()
            source.symlink_to(replacement)
        else:
            source.write_bytes(b"unscanned replacement")
            os.utime(source, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

    statuses = []
    app.security_clamav_running = False
    app.tr = lambda _key, fallback: fallback
    app._download_scan_clamav_available = lambda: True
    app._set_download_scan_status = lambda **value: statuses.append(value)
    app._update_download_scan_result_text = lambda *_: None
    app._clamav_progress_start = lambda **_kw: None
    app._clamav_progress_update_safe = lambda *_: None
    app._clamav_progress_finish_safe = lambda: None
    app._clamav_database_args = lambda: []
    app._clamav_parse_infected_count = controller.clamav_parse_infected_count
    app._clamav_parse_scanned_files = controller.clamav_parse_scanned_files
    app._clamav_extract_findings = lambda *_a, **_kw: []
    app._clamav_replace_open_findings = lambda *_: None

    def write_report(*_args):
        if stage == "report":
            mutate()
        return ""

    app._download_scan_write_report = write_report
    if stage == "confirmation":
        app.download_scan_ask_before_move_var = SimpleNamespace(get=lambda: True)
        app._download_scan_confirm_move = lambda *_: (mutate(), True)[1]

    def scan(_command, **kwargs):
        if "stdin_fd" in kwargs:
            assert os.read(kwargs["stdin_fd"], 1024) == b"synthetic clean bytes"
        if stage == "scan":
            mutate()
        return 0, "Scanned files: 1\nInfected files: 0\n", False

    app._run_clamscan_with_cancel = scan

    class InlineThread:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(app_module.threading, "Thread", InlineThread)
    app._run_download_scan(str(source), target_kind="file")
    assert not (target / source.name).exists(), "Unscanned replacement was released"
    assert statuses[-1]["status"] != "🟢 clean"
    assert source.read_bytes() == b"unscanned replacement", statuses
    assert not app.security_clamav_running


@pytest.mark.parametrize(
    "unsafe", ["foreign-owner", "public-leaf", "public-parent", "symlink"]
)
def test_unsafe_staging_is_rejected_before_import(
    workspace, tmp_path, monkeypatch, unsafe
):
    app, temporary, _target = workspace
    source = tmp_path / "input.bin"
    source.write_bytes(b"synthetic input")
    if unsafe == "foreign-owner":
        original = os.fstat
        identity = temporary.stat()

        def foreign_owner(fd):
            entry = original(fd)
            if (entry.st_dev, entry.st_ino) == (identity.st_dev, identity.st_ino):
                values = list(entry)
                values[4] = os.getuid() + 1
                return os.stat_result(values)
            return entry

        monkeypatch.setattr(dfs.os, "fstat", foreign_owner)
    elif unsafe == "public-leaf":
        temporary.chmod(0o777)
    elif unsafe == "public-parent":
        tmp_path.chmod(0o777)
    else:
        original = tmp_path / "original"
        temporary.rename(original)
        temporary.symlink_to(original, target_is_directory=True)
    with pytest.raises(dfs.UnsafePath):
        app._download_scan_import_file_to_temp(str(source))
    assert source.read_bytes() == b"synthetic input"
    assert not list(temporary.iterdir())


def test_default_shared_fallback_is_scoped_to_current_user(monkeypatch):
    app = app_module.App.__new__(app_module.App)
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.setattr(
        app_module.prequarantine_mount, "active_mount_ready", lambda: False
    )
    monkeypatch.setattr(
        app_module.os.path, "isdir", lambda p: p in {"/dev/shm", "/tmp"}
    )
    app._download_scan_mount_has_option = lambda *_: False
    app._download_scan_path_is_ephemeral = lambda *_: True
    assert app._default_download_scan_temp_dir() == (
        f"/dev/shm/netmon_roots-{os.getuid()}/download_scan"
    )


def test_clean_release_copies_scanned_bytes_without_overwriting_links(
    workspace, tmp_path
):
    app, temporary, target = workspace
    source = temporary / "clean.bin"
    source.write_bytes(b"synthetic clean bytes")
    victim = tmp_path / "untouched"
    (target / source.name).symlink_to(victim)
    with dfs.open_scan_file(str(source)) as scanned:
        # Scanning consumes the descriptor; release must rewind that same FD.
        assert os.read(scanned.fd, 1024) == b"synthetic clean bytes"
        released = app._download_scan_maybe_move_clean_file(str(source), scanned)
    assert Path(released).read_bytes() == b"synthetic clean bytes"
    assert Path(released).stat().st_mode & 0o777 == 0o600
    assert not victim.exists()
    assert (target / source.name).is_symlink()
    assert not source.exists()
    assert not list(target.glob(".netmon-release-*"))


def test_file_changed_during_release_copy_is_not_published(workspace, monkeypatch):
    _app, temporary, target = workspace
    source = temporary / "clean.bin"
    source.write_bytes(b"original bytes")
    actual_copy = dfs._copy

    def changed_during_copy(src, dst):
        actual_copy(src, dst)
        source.write_bytes(b"changed bytes")

    monkeypatch.setattr(dfs, "_copy", changed_during_copy)
    with dfs.open_scan_file(str(source)) as scanned:
        with pytest.raises(dfs.UnsafePath):
            dfs.release_file(scanned, str(target))
    assert not list(target.iterdir())
    assert source.read_bytes() == b"changed bytes"


def test_target_created_at_publication_is_not_overwritten(workspace, monkeypatch):
    _app, temporary, target = workspace
    source = temporary / "clean.bin"
    source.write_bytes(b"scanned bytes")
    actual_link = os.link

    def collide(src, dst, **kwargs):
        if dst == source.name:
            (target / dst).write_bytes(b"existing download")
        return actual_link(src, dst, **kwargs)

    monkeypatch.setattr(dfs.os, "link", collide)
    with dfs.open_scan_file(str(source)) as scanned:
        released = dfs.release_file(scanned, str(target))
    assert (target / source.name).read_bytes() == b"existing download"
    assert Path(released).read_bytes() == b"scanned bytes"


def test_real_clamscan_reads_the_opened_descriptor_with_synthetic_database(
    workspace, tmp_path, monkeypatch
):
    scanner = shutil.which("clamscan")
    if not scanner:
        pytest.skip("clamscan not installed")
    app, temporary, _target = workspace
    source = temporary / "synthetic.bin"
    payload = b"Harmless NetMon synthetic signature test data. " * 4
    source.write_bytes(payload)
    database = tmp_path / "synthetic.hdb"
    database.write_text(
        f"{hashlib.md5(payload).hexdigest()}:{len(payload)}:NetMon.Synthetic\n"
    )
    certificates = tmp_path / "empty-certificates"
    certificates.mkdir()
    monkeypatch.setenv("CVD_CERTS_DIR", str(certificates))
    button_states = []
    app._set_clamav_abort_button_state = button_states.append
    with dfs.open_scan_file(str(source)) as scanned:
        rc, output, cancelled = app._run_clamscan_with_cancel(
            [
                scanner,
                "--database",
                str(database),
                "--infected",
                "-",
            ],
            stdin_fd=scanned.fd,
            timeout=15,
        )
        scanned.verify()
        assert rc == 1, output
        [finding] = controller.clamav_single_file_findings(
            output, scanned, "download_scan_file", "now"
        )
        assert finding["path"] == str(source)
        assert finding["signature"].startswith("NetMon.Synthetic")
        assert finding["identity"] == dfs.qfs.file_identity(os.fstat(scanned.fd))
    assert rc == 1, output
    assert "stdin: NetMon.Synthetic" in output
    assert "FOUND" in output
    assert not cancelled and app.clamav_active_process is None
    assert button_states == [True, False]


def test_mutable_output_temporary_name_cannot_publish_a_substitute(
    workspace, monkeypatch
):
    _app, temporary, target = workspace
    source = temporary / "clean.bin"
    source.write_bytes(b"scanned bytes")
    actual_copy = dfs._copy
    planted = []

    def substitute_output(src, dst):
        actual_copy(src, dst)
        path = next(target.glob(".netmon-release-*"))
        path.rename(target / "original-temporary")
        path.write_bytes(b"unscanned output substitute")
        planted.append(path)

    monkeypatch.setattr(dfs, "_copy", substitute_output)
    with dfs.open_scan_file(str(source)) as scanned:
        released = dfs.release_file(scanned, str(target))
    assert Path(released).read_bytes() == b"scanned bytes"
    assert planted[0].read_bytes() == b"unscanned output substitute"


def test_source_swap_at_publication_rolls_back_the_release(workspace, monkeypatch):
    _app, temporary, target = workspace
    source = temporary / "clean.bin"
    source.write_bytes(b"scanned bytes")
    substitute = temporary / "substitute"
    substitute.write_bytes(b"unscanned bytes")
    actual_link = os.link

    def swap_at_link(*args, **kwargs):
        actual_link(*args, **kwargs)
        substitute.replace(source)

    monkeypatch.setattr(dfs.os, "link", swap_at_link)
    with dfs.open_scan_file(str(source)) as scanned:
        with pytest.raises(dfs.UnsafePath):
            dfs.release_file(scanned, str(target))
    assert not list(target.iterdir())
    assert source.read_bytes() == b"unscanned bytes"


@pytest.mark.parametrize("operation", ["copy", "link"])
def test_release_io_failure_preserves_source_and_cleans_output(
    workspace, monkeypatch, operation
):
    _app, temporary, target = workspace
    source = temporary / "clean.bin"
    source.write_bytes(b"scanned bytes")

    def fail(*_args, **_kwargs):
        raise OSError("synthetic I/O failure")

    if operation == "copy":
        monkeypatch.setattr(dfs, "_copy", fail)
    else:
        monkeypatch.setattr(dfs.os, "link", fail)
    with dfs.open_scan_file(str(source)) as scanned:
        with pytest.raises(OSError):
            dfs.release_file(scanned, str(target))
    assert source.read_bytes() == b"scanned bytes"
    assert not list(target.iterdir())
