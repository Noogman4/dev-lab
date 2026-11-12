"""Private library copies using synthetic keys, no real VPN/NM or host files."""

import os
from pathlib import Path

import pytest

from netmon.core import wireguard_import as wg
from netmon.features import vpn_controller as vpn
from test_wireguard_import_security import (
    SAFE,
    HOOK,
    app as app,
    store as store,
    profile,
    enter,
)


@pytest.mark.parametrize("mode", [0o600, 0o664, 0o666])
@pytest.mark.parametrize("route", ["folder", "dialog", "referenced", "direct"])
def test_confirmed_copy_imports_private_bytes_and_preserves_download(
    app, tmp_path, monkeypatch, mode, route
):
    source = profile(tmp_path, data=SAFE)
    source.chmod(mode)
    original = source.read_bytes(), source.stat().st_mode, source.stat().st_ino
    enter(app, source, route, monkeypatch)
    copied = app.managed_directory / "work.conf"
    assert copied.read_bytes() == SAFE
    assert copied.stat().st_mode & 0o777 == 0o600
    assert copied.stat().st_nlink == 1
    assert (
        source.read_bytes(),
        source.stat().st_mode,
        source.stat().st_ino,
    ) == original
    assert len(app.dialogs) == 1
    assert "Originaldateien bleiben unverändert" in app.dialogs[0]
    assert str(app.managed_directory) in app.dialogs[0]
    assert not app.warnings
    assert "L04_SYNTHETIC_NEVER_EXECUTE" not in " ".join(
        app.dialogs + app.logs + app.warnings
    )
    if route == "folder":
        assert (app.directory / "work.conf").read_bytes() == SAFE
    else:
        assert app.imported == [(SAFE, 0o600, 0o700)]


@pytest.mark.parametrize("closed", [False, True])
def test_declined_or_closed_confirmation_creates_no_copy(
    app, tmp_path, monkeypatch, closed
):
    source = profile(tmp_path)
    source.chmod(0o664)

    def confirm(*_a, **_kw):
        if closed:
            raise RuntimeError("GUI closed")
        return False

    monkeypatch.setattr(vpn.messagebox, "askyesno", confirm)
    enter(app, source, "folder", monkeypatch)
    assert not app.managed_directory.exists()
    assert not app.operations
    assert source.stat().st_mode & 0o777 == 0o664


@pytest.mark.parametrize("kind", ["different", "symlink", "hardlink", "permissions"])
def test_existing_library_file_is_never_overwritten(app, tmp_path, monkeypatch, kind):
    source = profile(tmp_path)
    app.managed_directory.mkdir(parents=True)
    target = profile(app.managed_directory, data=HOOK if kind == "different" else SAFE)
    if kind == "symlink":
        target.unlink()
        target.symlink_to(source)
    elif kind == "hardlink":
        os.link(target, tmp_path / "another-link")
    elif kind == "permissions":
        target.chmod(0o644)
    before = target.read_bytes(), target.lstat().st_mode, target.lstat().st_ino
    enter(app, source, "folder", monkeypatch)
    assert not app.operations
    assert (
        target.read_bytes(),
        target.lstat().st_mode,
        target.lstat().st_ino,
    ) == before
    assert not list(app.managed_directory.glob(".netmon-import-*"))


def test_identical_private_copy_is_reused_without_replacement(tmp_path):
    source = profile(tmp_path)
    directory = tmp_path / "library"
    first = wg.ProfileSnapshot.read(source, for_copy=True).copy_to(directory)
    ino = Path(first.source).stat().st_ino
    second = wg.ProfileSnapshot.read(source, for_copy=True).copy_to(directory)
    assert Path(second.source).stat().st_ino == ino
    assert first.sha256 == second.sha256


@pytest.mark.parametrize("failure", ["write", "flush", "corrupt"])
def test_failed_copy_never_publishes_incomplete_profile(tmp_path, monkeypatch, failure):
    source = profile(tmp_path)
    snapshot = wg.ProfileSnapshot.read(source, for_copy=True)
    directory = tmp_path / "library"
    original_write = wg.os.write

    def write(fd, data):
        if failure == "write":
            raise OSError("private test write failure")
        return original_write(fd, b"x" * len(data))

    if failure in {"write", "corrupt"}:
        monkeypatch.setattr(wg.os, "write", write)
    else:
        monkeypatch.setattr(
            wg.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError("flush failure"))
        )
    with pytest.raises((OSError, ValueError)):
        snapshot.copy_to(directory)
    assert not list(directory.iterdir())
    assert source.read_bytes() == SAFE


def test_short_writes_and_permissive_umask_still_make_exact_0600_copy(
    tmp_path, monkeypatch
):
    source = profile(tmp_path)
    original_write = wg.os.write
    monkeypatch.setattr(wg.os, "write", lambda fd, data: original_write(fd, data[:2]))
    previous = os.umask(0)
    try:
        copied = wg.ProfileSnapshot.read(source, for_copy=True).copy_to(
            tmp_path / "library"
        )
    finally:
        os.umask(previous)
    assert Path(copied.source).read_bytes() == SAFE
    assert Path(copied.source).stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("changed", ["original", "copy"])
def test_mutation_after_copy_cannot_change_reviewed_import(app, tmp_path, changed):
    source = profile(tmp_path)
    source.chmod(0o664)
    snapshots = vpn._prepare_wireguard_imports(app, [str(source)])
    target = source if changed == "original" else Path(snapshots[0].source)
    target.write_bytes(HOOK)
    with pytest.raises(ValueError):
        vpn._verify_import_snapshot(snapshots[0])
    assert not app.operations


@pytest.mark.parametrize("kind", ["symlink", "writable"])
def test_unsafe_destination_directory_is_refused(tmp_path, kind):
    source = profile(tmp_path)
    directory = tmp_path / "library"
    if kind == "symlink":
        other = tmp_path / "elsewhere"
        other.mkdir()
        directory.symlink_to(other, target_is_directory=True)
    else:
        directory.mkdir(mode=0o777)
        directory.chmod(0o777)
    with pytest.raises((OSError, ValueError)):
        wg.ProfileSnapshot.read(source, for_copy=True).copy_to(directory)
    assert not list(directory.iterdir())


def test_concurrent_destination_creation_is_retained(tmp_path, monkeypatch):
    source = profile(tmp_path)
    directory = tmp_path / "library"
    link = wg.os.link

    def competing(*args, **kwargs):
        profile(directory, data=HOOK)
        return link(*args, **kwargs)

    monkeypatch.setattr(wg.os, "link", competing)
    with pytest.raises(FileExistsError):
        wg.ProfileSnapshot.read(source, for_copy=True).copy_to(directory)
    assert (directory / "work.conf").read_bytes() == HOOK
    assert not list(directory.glob(".netmon-import-*"))


def test_existing_library_source_is_imported_without_copy(app, tmp_path):
    app.managed_directory.mkdir(parents=True)
    source = profile(app.managed_directory)
    ino = source.stat().st_ino
    snapshots = vpn._prepare_wireguard_imports(app, [str(source)])
    assert snapshots[0].source == str(source)
    assert not snapshots[0].for_copy
    assert source.stat().st_ino == ino


def test_preview_does_not_relax_normal_read_or_accept_foreign_owner(
    tmp_path, monkeypatch
):
    source = profile(tmp_path)
    source.chmod(0o664)
    with pytest.raises(wg.ProfilePermissionsError):
        wg.ProfileSnapshot.read(source)
    monkeypatch.setattr(wg.os, "geteuid", lambda: os.getuid() + 1)
    with pytest.raises(ValueError):
        wg.ProfileSnapshot.read(source, for_copy=True)


def test_private_library_under_shared_documents_parent(tmp_path):
    source = profile(tmp_path)
    parent = tmp_path / "Documents"
    parent.mkdir()
    parent.chmod(0o770)
    copied = wg.ProfileSnapshot.read(source, for_copy=True).copy_to(
        parent / "WireGuard"
    )
    assert Path(copied.source).read_bytes() == SAFE
    assert Path(copied.source).stat().st_mode & 0o777 == 0o600
    assert Path(copied.source).parent.stat().st_mode & 0o777 == 0o700
    assert parent.stat().st_mode & 0o777 == 0o770


def test_system_library_is_created_private_even_with_permissive_umask(
    tmp_path, monkeypatch
):
    from netmon.core import state

    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(tmp_path / "Documents"))
    previous = os.umask(0)
    try:
        directory = Path(state.get_netmon_wireguard_dir())
    finally:
        os.umask(previous)
    assert directory.stat().st_mode & 0o777 == 0o700


def test_real_tk_confirmation_and_copy_under_private_xvfb(tmp_path, monkeypatch):
    import tkinter as tk
    from PIL import ImageGrab

    root = tk.Tk()
    root.withdraw()
    root.log = lambda _message: None
    root.tr = lambda _key, fallback: fallback
    directory = tmp_path / "Documents" / "NetMon" / "WireGuard"
    monkeypatch.setattr(
        vpn, "ensure_netmon_wireguard_profiles_dir", lambda: str(directory)
    )
    source = profile(tmp_path, "Irland")
    source.chmod(0o664)
    observed = {}

    def accept():
        name = ".__tk__messagebox"
        if root.tk.call("winfo", "exists", name):
            root.update_idletasks()
            width, height = [
                int(root.tk.call("winfo", key, name)) for key in ("width", "height")
            ]
            x, y = [int(root.tk.call("winfo", key, name)) for key in ("rootx", "rooty")]
            observed["width"] = width
            observed["height"] = height
            observed["requested_width"] = int(root.tk.call("winfo", "reqwidth", name))
            observed["requested_height"] = int(root.tk.call("winfo", "reqheight", name))
            observed["text"] = root.tk.call(name + ".msg", "cget", "-text")
            for choice in ("yes", "no"):
                button = name + "." + choice
                bx, by, bw, bh = [
                    int(root.tk.call("winfo", key, button))
                    for key in ("x", "y", "width", "height")
                ]
                assert 0 <= bx and bx + bw <= width
                assert 0 <= by and by + bh <= height
            ImageGrab.grab((x, y, x + width, y + height)).save(
                "/work/wg-import-confirmation-v18.png"
            )
            root.tk.call("set", "::tk::Priv(button)", "yes")
        else:
            root.after(50, accept)

    root.after(100, accept)
    timeout = root.after(5000, lambda: root.tk.call("set", "::tk::Priv(button)", "no"))
    try:
        snapshots = vpn._prepare_wireguard_imports(root, [str(source)])
        assert snapshots
        assert observed["width"] >= observed["requested_width"]
        assert observed["height"] >= observed["requested_height"]
        assert "Originaldateien bleiben unverändert" in observed["text"]
        assert "0600" in observed["text"] and str(directory) in observed["text"]
        assert Path(snapshots[0].source).read_bytes() == SAFE
        assert Path(snapshots[0].source).stat().st_mode & 0o777 == 0o600
        assert source.stat().st_mode & 0o777 == 0o664
    finally:
        root.after_cancel(timeout)
        root.destroy()
