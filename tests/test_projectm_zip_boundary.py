"""ZIP worker wire validation, selected-file snapshot and transactional import."""

import io
import json
import os
from pathlib import Path
import struct
import warnings
from types import SimpleNamespace
import zipfile

import pytest

from netmon import netmon_projectm_sidecar as sidecar
from netmon.core import projectm_zip as wire
from netmon.core import radio_sandbox as sandbox
from netmon.core.archive_limits import ByteBudget
from netmon.core.projectm_import_plan import ImportPlan


def make_zip(path, entries=None):
    with warnings.catch_warnings(), zipfile.ZipFile(path, "w") as archive:
        warnings.filterwarnings(
            "ignore", message="Duplicate name:.*", category=UserWarning
        )
        for name, data in entries or [
            ("Folder/one.milk", b"preset"),
            ("Folder/pic.png", b"opaque asset"),
        ]:
            archive.writestr(name, data)
    return path


def encoded(tmp_path, entries=None):
    path = make_zip(tmp_path / "input.zip", entries)
    with (tmp_path / "bundle").open("w+b") as handle:
        wire.encode_archive(path, handle)
        handle.seek(0)
        return path, handle.read()


def bundle(rows, payload=b""):
    data = bytearray(wire.MAGIC + struct.pack(">I", len(rows)))
    for row in rows:
        raw = json.dumps(row).encode()
        data.extend(struct.pack(">I", len(raw)))
        data.extend(raw)
    return bytes(data) + payload + wire.END


ROW = {"parts": ["one.milk"], "size": 3, "compressed": 3, "method": 0}


def test_wire_keeps_existing_naming_assets_and_payloads_without_parent_zip(
    tmp_path, monkeypatch
):
    path, data = encoded(
        tmp_path,
        [
            ("Folder/one.milk", b"first"),
            ("Folder/one.milk", b"second"),
            ("Folder/pic.png", b"asset"),
            ("Folder/no.exe", b"ignored"),
        ],
    )
    monkeypatch.setattr(
        zipfile, "ZipFile", lambda *_a, **_k: pytest.fail("parent ZIP parser")
    )
    with (tmp_path / "raw").open("w+b") as handle:
        handle.write(data)
        handle.seek(0)
        prepared = wire.PreparedArchive(handle, path.stat().st_size)
        plan = ImportPlan(
            prepared.members,
            wire.PRESET_EXTENSIONS,
            wire.PRESET_EXTENSIONS | wire.ASSET_EXTENSIONS,
        )
        values = {}
        budget = ByteBudget(1024)
        for item in plan.files:
            output = io.BytesIO()
            prepared.copy_member(item.member, output, budget)
            values["/".join(item.parts)] = output.getvalue()
    assert values == {
        "one.milk": b"first",
        "one_2.milk": b"second",
        "pic.png": b"asset",
    }


@pytest.mark.parametrize(
    "row",
    [
        {**ROW, "parts": ["..", "one.milk"]},
        {**ROW, "parts": ["/one.milk"]},
        {**ROW, "parts": ["C:", "one.milk"]},
        {**ROW, "parts": ["bad\\name.milk"]},
        {**ROW, "parts": ["one\0.milk"]},
        {**ROW, "parts": [1]},
        {**ROW, "size": True},
        {**ROW, "compressed": 0},
        {**ROW, "method": 99},
        {**ROW, "size": -1},
        {**ROW, "link": "private"},
    ],
)
def test_parent_rejects_malicious_worker_paths_sizes_and_fields(tmp_path, row):
    path = tmp_path / "wire"
    path.write_bytes(bundle([row], b"abc"))
    with path.open("rb") as handle, pytest.raises((ValueError, TypeError)):
        wire.PreparedArchive(handle, 100)


@pytest.mark.parametrize(
    "data",
    [
        b"unknown",
        wire.MAGIC + struct.pack(">I", 50001),
        wire.MAGIC + struct.pack(">II", 1, wire.MAX_ROW_BYTES + 1),
        bundle([ROW], b"ab"),
        bundle([ROW], b"abcd"),
        bundle([ROW], b"abc")[:-1],
    ],
)
def test_parent_rejects_unknown_excessive_or_incomplete_protocol(tmp_path, data):
    path = tmp_path / "wire"
    path.write_bytes(data)
    with path.open("rb") as handle, pytest.raises(ValueError):
        wire.PreparedArchive(handle, 100)


def controlled_worker(monkeypatch, tmp_path, program):
    children = []
    real = sandbox.subprocess.Popen
    monkeypatch.setattr(sandbox.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(sandbox, "_zip_runtime", lambda: (tmp_path, ()))

    def command(directory, _stdlib, _runtime):
        assert (directory / "archive.zip").stat().st_mode & 0o777 == 0o600
        assert (directory / "archive.zip").read_bytes() == (
            tmp_path / "input.zip"
        ).read_bytes()
        return [str(sandbox.PYTHON), "-I", "-S", "-B", "-c", program]

    def spawn(args, **kwargs):
        assert kwargs["close_fds"] and kwargs["stdin"] == sandbox.subprocess.DEVNULL
        assert "pass_fds" not in kwargs
        child = real(args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(sandbox, "_zip_command", command)
    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    return children


def test_default_import_uses_snapshot_worker_and_never_parent_zip(
    tmp_path, monkeypatch
):
    path, data = encoded(tmp_path)
    original = path.read_bytes()
    children = controlled_worker(
        monkeypatch, tmp_path, f"import os;os.write(1,{data!r})"
    )
    monkeypatch.setattr(
        zipfile, "ZipFile", lambda *_a, **_k: pytest.fail("parent ZIP parser")
    )
    monkeypatch.setattr(
        sidecar, "_sync_projectm_flatpak_playlist_file", lambda *_a: None
    )
    root = tmp_path / "Presets"
    app = SimpleNamespace(
        radio_projectm_preset_dir=str(root), netmon_state_dir=str(tmp_path / "state")
    )
    result = sidecar.install_projectm_preset_archive(app, str(path), pack_name="Pack")
    assert result["imported_presets"] == 1 and result["imported_assets"] == 1
    assert (Path(result["target_dir"]) / "one.milk").read_bytes() == b"preset"
    assert path.read_bytes() == original
    assert all(child.poll() == 0 for child in children)
    assert not list(tmp_path.glob("preset-zip-*"))


@pytest.mark.parametrize("failure", ["exit", "wire", "size", "write"])
def test_failure_preserves_old_pack_and_cleans_all_staging(
    tmp_path, monkeypatch, failure
):
    path, data = encoded(tmp_path)
    program = f"import os;os.write(1,{data!r})"
    if failure == "exit":
        program += ";raise SystemExit(2)"
    elif failure == "wire":
        program = "import os;os.write(1,b'invalid')"
    elif failure == "size":
        program = f"import os;os.ftruncate(1,{wire.MAX_WIRE_BYTES+1})"
    children = controlled_worker(monkeypatch, tmp_path, program)
    root = tmp_path / "Presets"
    old = root / "Downloaded Packs" / "Pack"
    old.mkdir(parents=True)
    (old / "old.milk").write_bytes(b"KEEP")
    app = SimpleNamespace(
        radio_projectm_preset_dir=str(root), netmon_state_dir=str(tmp_path / "state")
    )
    monkeypatch.setattr(
        sidecar, "_sync_projectm_flatpak_playlist_file", lambda *_a: None
    )
    if failure == "write":
        original_open = open

        def opened(name, mode="r", **kwargs):
            if mode == "xb":
                raise OSError("disk error")
            return original_open(name, mode, **kwargs)

        monkeypatch.setattr(sidecar, "open", opened, raising=False)
    with pytest.raises((sandbox.RadioSandboxError, ValueError, OSError)):
        sidecar.install_projectm_preset_archive(app, str(path), pack_name="Pack")
    assert (old / "old.milk").read_bytes() == b"KEEP"
    assert sorted(item.name for item in old.parent.iterdir()) == ["Pack"]
    assert not list(tmp_path.glob("preset-zip-*"))
    assert all(child.poll() is not None for child in children)


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_input_is_only_a_selected_regular_file(tmp_path, monkeypatch, kind):
    monkeypatch.setattr(sandbox, "_zip_runtime", lambda: (tmp_path, ()))
    path = tmp_path / "input.zip"
    if kind == "symlink":
        real = tmp_path / "real"
        real.write_bytes(b"ZIP")
        path.symlink_to(real)
    else:
        os.mkfifo(path)
    with pytest.raises((OSError, sandbox.RadioSandboxError)):
        with sandbox.prepared_preset_bundle(path):
            pytest.fail("unsafe input accepted")


def test_zip_command_mounts_only_snapshot_and_fixed_modules(tmp_path):
    sandbox._prepare_directory(tmp_path)
    command = sandbox._zip_command(tmp_path, Path("/usr/lib/python3.12"), ())
    assert "--unshare-net" in command and "--disable-userns" in command
    for path in ("/run/control", "/run/request.json", "/run/audio/pulse"):
        assert path not in command
    assert [
        "--ro-bind",
        str(tmp_path / "archive.zip"),
        "/media/archive.zip",
    ] == command[
        command.index(str(tmp_path / "archive.zip"))
        - 1 : command.index(str(tmp_path / "archive.zip"))
        + 2
    ]
    assert str(tmp_path) not in command
