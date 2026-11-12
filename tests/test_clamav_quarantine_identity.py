"""ClamAV quarantine/restore stay bound to the scanned objects (ddd6ca23 #5)."""

import errno
import json
import os
from types import SimpleNamespace

import pytest

from netmon.core import quarantine_fs as qfs
from netmon.features import clamav_controller as controller


@pytest.fixture
def home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "share").mkdir(parents=True)
    (home / ".ssh").mkdir()
    (home / ".config" / "autostart").mkdir(parents=True)
    (home / ".ssh" / "id_ed25519").write_text("PRIVATE")
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def qdir(home):
    return str(home / ".netmon_quarantine")


def _infected(home, name="evil.bin", content="X5O!"):
    path = home / "share" / name
    path.write_text(content)
    return path


def _identity(path):
    return qfs.record_identity(str(path))


# --- quarantine_fs.quarantine_file ---------------------------------------


def test_quarantine_moves_the_scanned_file_into_a_private_directory(home, qdir):
    path = _infected(home)
    identity = _identity(path)

    qpath, origin = qfs.quarantine_file(str(path), qdir, "evil__q.bin", identity)

    assert not path.exists()
    assert open(qpath).read() == "X5O!"
    assert os.stat(qdir).st_mode & 0o777 == 0o700
    assert origin == qfs.directory_identity(os.stat(home / "share"))


def test_leaf_swapped_for_symlink_to_private_file_is_rejected(home, qdir):
    path = _infected(home)
    identity = _identity(path)
    path.unlink()
    path.symlink_to(home / ".ssh" / "id_ed25519")

    with pytest.raises(qfs.UnsafePath):
        qfs.quarantine_file(str(path), qdir, "evil__q.bin", identity)
    assert (home / ".ssh" / "id_ed25519").read_text() == "PRIVATE"
    assert path.is_symlink()


def test_parent_swapped_for_symlink_is_rejected(home, qdir):
    victim = home / ".ssh" / "id_ed25519"
    identity = _identity(victim)
    (home / "share").rename(home / "share.old")
    (home / "share").symlink_to(home / ".ssh")

    with pytest.raises(qfs.UnsafePath):
        qfs.quarantine_file(str(home / "share" / "id_ed25519"), qdir, "id__q", identity)
    assert victim.read_text() == "PRIVATE"


def test_replaced_or_modified_file_is_rejected(home, qdir):
    path = _infected(home)
    identity = _identity(path)
    path.unlink()
    path.write_text("different file, same name")

    with pytest.raises(qfs.UnsafePath, match="seit dem Scan"):
        qfs.quarantine_file(str(path), qdir, "evil__q.bin", identity)
    assert path.exists()


def test_hardlinks_and_special_files_are_rejected(home, qdir):
    path = _infected(home)
    os.link(path, home / "share" / "second-name")
    with pytest.raises(qfs.UnsafePath, match="Hardlinks"):
        qfs.quarantine_file(str(path), qdir, "evil__q.bin")

    fifo = home / "share" / "pipe"
    os.mkfifo(fifo)
    with pytest.raises(qfs.UnsafePath, match="keine reguläre Datei"):
        qfs.quarantine_file(str(fifo), qdir, "pipe__q")


def test_cross_device_quarantine_copies_and_unlinks_exactly(home, qdir, monkeypatch):
    path = _infected(home)
    identity = _identity(path)

    def no_rename(*_args, **_kwargs):
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    monkeypatch.setattr(qfs.os, "rename", no_rename)
    qpath, _origin = qfs.quarantine_file(str(path), qdir, "evil__q.bin", identity)

    assert not path.exists()
    assert open(qpath).read() == "X5O!"
    assert os.stat(qpath).st_mode & 0o777 == 0o600


def test_existing_quarantine_name_is_never_overwritten(home, qdir):
    path = _infected(home)
    os.makedirs(qdir, mode=0o700)
    (open(os.path.join(qdir, "taken"), "w")).close()
    with pytest.raises(qfs.UnsafePath, match="existiert bereits"):
        qfs.quarantine_file(str(path), qdir, "taken")
    assert path.exists()


def test_quarantine_dir_must_be_private(home, qdir):
    os.makedirs(qdir, mode=0o755)
    os.chmod(qdir, 0o755)
    with pytest.raises(qfs.UnsafePath, match="nicht privat"):
        qfs.quarantine_file(str(_infected(home)), qdir, "x")


# --- quarantine_fs.restore_file ------------------------------------------


def _quarantined(home, qdir):
    path = _infected(home)
    qpath, origin = qfs.quarantine_file(str(path), qdir, "evil__q.bin", _identity(path))
    return path, qpath, origin


def _restore(home, qdir, qpath, original, origin=None):
    return qfs.restore_file(
        qpath,
        qdir,
        str(original),
        home_root=str(home),
        fallback_dir=str(home / "NetMon-Restored"),
        origin=origin,
        stamp="STAMP",
    )


def test_restore_returns_to_the_recorded_directory(home, qdir):
    path, qpath, origin = _quarantined(home, qdir)
    restored, fallback = _restore(home, qdir, qpath, path, origin)
    assert (restored, fallback) == (str(path), False)
    assert path.read_text() == "X5O!"
    assert not os.path.exists(qpath)


def test_restore_never_overwrites(home, qdir):
    path, qpath, origin = _quarantined(home, qdir)
    path.write_text("new legitimate file")
    restored, _ = _restore(home, qdir, qpath, path, origin)
    assert restored == str(home / "share" / "evil__restored__STAMP.bin")
    assert path.read_text() == "new legitimate file"


def test_parent_redirected_to_autostart_restores_into_fallback(home, qdir):
    path, qpath, origin = _quarantined(home, qdir)
    (home / "share").rename(home / "share.old")
    (home / "share").symlink_to(home / ".config" / "autostart")

    restored, fallback = _restore(home, qdir, qpath, path, origin)

    assert fallback is True
    assert restored == str(home / "NetMon-Restored" / "evil.bin")
    assert list((home / ".config" / "autostart").iterdir()) == []


def test_recreated_original_directory_restores_into_fallback(home, qdir):
    path, qpath, origin = _quarantined(home, qdir)
    (home / "share").rename(home / "share.old")
    (home / "share").mkdir()

    restored, fallback = _restore(home, qdir, qpath, path, origin)
    assert fallback is True
    assert not path.exists()
    assert os.path.dirname(restored) == str(home / "NetMon-Restored")


def test_missing_original_directory_is_created_without_following_links(home, qdir):
    path, qpath, _origin = _quarantined(home, qdir)
    original = home / "gone" / "deeper" / "evil.bin"
    restored, fallback = _restore(home, qdir, qpath, original)
    assert (restored, fallback) == (str(original), False)


def test_original_outside_home_restores_into_fallback(home, qdir, tmp_path):
    _path, qpath, _origin = _quarantined(home, qdir)
    restored, fallback = _restore(home, qdir, qpath, tmp_path / "etc" / "evil.bin")
    assert fallback is True
    assert restored.startswith(str(home / "NetMon-Restored"))


def test_cross_device_restore_copies_exclusively(home, qdir, monkeypatch):
    path, qpath, origin = _quarantined(home, qdir)

    def no_link(*_args, **_kwargs):
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    monkeypatch.setattr(qfs.os, "link", no_link)
    restored, _ = _restore(home, qdir, qpath, path, origin)
    assert restored == str(path)
    assert path.read_text() == "X5O!"
    assert not os.path.exists(qpath)


def test_restore_source_must_be_inside_the_quarantine(home, qdir):
    _path, _qpath, _origin = _quarantined(home, qdir)
    with pytest.raises(qfs.UnsafePath, match="außerhalb"):
        _restore(home, qdir, str(home / ".ssh" / "id_ed25519"), home / "x")


# --- controller -----------------------------------------------------------


def _app(qdir):
    app = SimpleNamespace(clamav_quarantine_dir=qdir, logs=[])
    app.log_safe = app.logs.append
    app._clamav_next_quarantine_path = (
        lambda src: controller.clamav_next_quarantine_path(app, src)
    )
    return app


def test_extracted_findings_record_the_scanned_identity(home):
    path = _infected(home)
    output = f"{path}: Eicar-Signature FOUND\n{home}/missing: X FOUND\n"
    found = controller.clamav_extract_findings(output, "test", "now")
    assert found[0]["identity"] == _identity(path)
    assert "identity" not in found[1]


def test_swapped_finding_is_not_quarantined_and_stays_open(home, qdir):
    path = _infected(home)
    [item] = controller.clamav_extract_findings(f"{path}: Eicar FOUND\n", "t", "now")
    path.unlink()
    path.symlink_to(home / ".ssh" / "id_ed25519")

    outcome = controller.clamav_quarantine_item(_app(qdir), item)

    assert outcome not in {"moved", "missing"}
    assert item["status"] == "found"
    assert (home / ".ssh" / "id_ed25519").read_text() == "PRIVATE"


def test_controller_round_trip_and_fallback_logging(home, qdir):
    path = _infected(home)
    [item] = controller.clamav_extract_findings(f"{path}: Eicar FOUND\n", "t", "now")
    app = _app(qdir)

    assert controller.clamav_quarantine_item(app, item) == "moved"
    assert item["status"] == "quarantine" and "quarantine_origin" in item
    (home / "share").rename(home / "share.old")
    (home / "share").symlink_to(home / ".config" / "autostart")

    assert controller.clamav_restore_item(app, item) == "restored"
    assert item["restore_path"].startswith(str(home / "NetMon-Restored"))
    assert any("Wiederhergestellt nach" in line for line in app.logs)
    assert list((home / ".config" / "autostart").iterdir()) == []


def test_controller_reports_missing_files(home, qdir):
    app = _app(qdir)
    item = {"path": str(home / "share" / "gone.bin"), "status": "found"}
    assert controller.clamav_quarantine_item(app, item) == "missing"
    assert item["status"] == "missing"
    outside = {"path": "/etc/passwd", "status": "found"}
    assert "außerhalb" in controller.clamav_quarantine_item(app, outside)


def test_load_keeps_valid_identities_only(tmp_path):
    path = tmp_path / "findings.json"
    path.write_text(
        json.dumps(
            [
                {
                    "path": "/home/u/a",
                    "identity": {"dev": 1, "ino": 2, "size": 3, "mtime_ns": 4},
                    "quarantine_origin": {"dev": 1, "ino": 9},
                },
                {"path": "/home/u/b", "identity": {"dev": "1", "ino": 2}},
                {"path": "/home/u/c", "identity": {"dev": True, "ino": 2}},
            ]
        )
    )
    app = SimpleNamespace(clamav_findings_path=str(path), log_debug=lambda _m: None)
    controller.load_clamav_findings(app)
    first, second, third = app.clamav_findings
    assert first["identity"] == {"dev": 1, "ino": 2, "size": 3, "mtime_ns": 4}
    assert first["quarantine_origin"] == {"dev": 1, "ino": 9}
    assert "identity" not in second and "identity" not in third
