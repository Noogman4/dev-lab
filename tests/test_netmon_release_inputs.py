"""Exercise source-opening races and staging boundaries without release keys."""

import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def copier(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "release_input_copier", ROOT / "scripts/copy_netmon_release_input.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def inputs(tmp_path):
    root = tmp_path / "repo"
    source = root / "site/download.php"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"workspace content")
    staging = root / "dist/.release-work/build"
    staging.mkdir(parents=True)
    return root, source, staging, staging / source.name


def test_source_link_inserted_at_open_is_rejected(
    copier, inputs, tmp_path, monkeypatch
):
    root, source, staging, destination = inputs
    external = tmp_path / "private-data"
    external.write_bytes(b"must never be published")
    actual_open = os.open

    def swap_at_open(path, flags, *args, **kwargs):
        if path == source.name and flags & os.O_NONBLOCK:
            source.unlink()
            source.symlink_to(external)
        return actual_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(copier.os, "open", swap_at_open)
    with pytest.raises(OSError):
        copier.copy_input(root, source, staging, destination)
    assert not destination.exists()
    assert external.read_bytes() == b"must never be published"


def test_open_source_directory_stays_bound_after_swap(
    copier, inputs, tmp_path, monkeypatch
):
    root, source, staging, destination = inputs
    external = tmp_path / "external-site"
    external.mkdir()
    (external / source.name).write_bytes(b"must never be published")
    actual_open = os.open

    def swap_after_open(path, flags, *args, **kwargs):
        descriptor = actual_open(path, flags, *args, **kwargs)
        if path == "site":
            source.parent.rename(root / "original-site")
            source.parent.symlink_to(external, target_is_directory=True)
        return descriptor

    monkeypatch.setattr(copier.os, "open", swap_after_open)
    copier.copy_input(root, source, staging, destination)
    assert destination.read_bytes() == b"workspace content"


def test_symlink_above_staging_root_is_rejected(copier, inputs, tmp_path):
    root, source, staging, destination = inputs
    external = tmp_path / "external-work"
    staging.parent.rename(external)
    staging.parent.symlink_to(external, target_is_directory=True)
    with pytest.raises(OSError):
        copier.copy_input(root, source, staging, destination)
    assert not (external / staging.name / destination.name).exists()


def test_fifo_input_is_rejected_without_blocking(copier, inputs):
    root, source, staging, destination = inputs
    source.unlink()
    os.mkfifo(source)
    with pytest.raises(ValueError, match="regular file"):
        copier.copy_input(root, source, staging, destination)
    assert not destination.exists()


@pytest.mark.parametrize("boundary", ["source", "destination", "parent-traversal"])
def test_copy_cannot_escape_declared_roots(copier, inputs, tmp_path, boundary):
    root, source, staging, destination = inputs
    external = tmp_path / "outside"
    external.write_bytes(b"external content")
    if boundary == "source":
        source = external
    elif boundary == "destination":
        destination = root / "outside-staging"
    else:
        destination = staging / "../outside-staging"
    with pytest.raises(ValueError):
        copier.copy_input(root, source, staging, destination)
    assert external.read_bytes() == b"external content"
    assert not destination.exists()
