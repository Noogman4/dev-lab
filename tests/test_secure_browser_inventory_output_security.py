"""Inventory outputs must never follow shared temporary paths or linked targets."""

import contextlib
import io
import json
import os
import stat
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon.modules.secure_browser.service import SecureBrowserService
from tools.secure_browser_manager import browser_container_builder as builder

MODES = [
    [],
    ["--list-installed"],
    ["--register-existing"],
    ["--refresh-existing"],
    ["--repair-policy"],
    ["--cleanup-menu"],
    ["--uninstall", "missing"],
]


@pytest.fixture
def inventory_case(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    monkeypatch.setattr(builder, "DEFAULT_PROFILE_BASE_DIRS", [tmp_path / "profiles"])
    service = SecureBrowserService()
    monkeypatch.setattr(
        service, "get_default_base_dir", lambda: tmp_path / "containers"
    )
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"unchanged sentinel")
    legacy = tmp_path / service.RUNTIME_INVENTORY_FILENAME
    legacy.symlink_to(sentinel)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {"containers": [{"name": "Test", "allowed_domains": ["example.invalid"]}]}
        ),
        encoding="utf-8",
    )
    return service, sentinel, legacy, config


def _command(service, config, mode):
    return ["python3", str(service.tool_script), "--config", str(config), *mode]


@pytest.mark.parametrize("mode", MODES)
def test_service_inventory_ignores_legacy_symlink(
    inventory_case, tmp_path, monkeypatch, mode
):
    service, sentinel, legacy, config = inventory_case
    before = config.read_bytes()
    observed = []

    def run(command, **kwargs):
        inventory = Path(command[command.index("--inventory") + 1])
        observed.append(inventory)
        assert inventory.parent.parent == tmp_path
        assert stat.S_IMODE(inventory.parent.stat().st_mode) == 0o700
        assert not inventory.exists()
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            rc = builder.main(command[2:], applications_dir=tmp_path / "applications")
        assert inventory.read_text(encoding="utf-8").startswith(
            "# Firefox Container Inventory"
        )
        assert stat.S_IMODE(inventory.stat().st_mode) == 0o600
        return SimpleNamespace(
            returncode=rc, stdout=output.getvalue(), stderr=error.getvalue()
        )

    monkeypatch.setattr("netmon.modules.secure_browser.service.subprocess.run", run)
    result = service._run_builder_command(_command(service, config, mode))
    assert result["returncode"] == (1 if "--uninstall" in mode else 0)
    assert result["ok"] is ("--uninstall" not in mode)
    assert sentinel.read_bytes() == b"unchanged sentinel"
    assert legacy.is_symlink()
    assert config.read_bytes() == before
    assert len(observed) == 1
    assert not observed[0].parent.exists()


@pytest.mark.parametrize("mode", MODES)
def test_cli_rejects_linked_inventory_before_actions(inventory_case, tmp_path, mode):
    _, sentinel, legacy, config = inventory_case
    before = config.read_bytes()
    with pytest.raises((OSError, ValueError)):
        builder.main(
            [
                "--base-dir",
                str(tmp_path / "containers"),
                "--inventory",
                str(legacy),
                "--config",
                str(config),
                *mode,
            ],
            applications_dir=tmp_path / "applications",
        )
    assert sentinel.read_bytes() == b"unchanged sentinel"
    assert legacy.is_symlink()
    assert config.read_bytes() == before


@pytest.mark.parametrize("kind", ["leaf", "parent", "dangling", "hardlink"])
def test_writer_rejects_unsafe_output(tmp_path, kind):
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"unchanged sentinel")
    output = tmp_path / "inventory.md"
    if kind == "parent":
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "inventory.md").write_bytes(b"outside inventory")
        directory = tmp_path / "linked"
        directory.symlink_to(outside, target_is_directory=True)
        output = directory / "inventory.md"
    elif kind == "hardlink":
        os.link(sentinel, output)
    else:
        output.symlink_to(sentinel if kind == "leaf" else tmp_path / "missing")
    with pytest.raises((OSError, ValueError)):
        builder.write_inventory(output, tmp_path, [])
    assert sentinel.read_bytes() == b"unchanged sentinel"
    if kind == "parent":
        assert (outside / "inventory.md").read_bytes() == b"outside inventory"
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("umask", [0, 0o022, 0o077])
def test_regular_cli_inventory_and_existing_permissions(tmp_path, monkeypatch, umask):
    monkeypatch.setattr(builder, "DEFAULT_PROFILE_BASE_DIRS", [tmp_path / "profiles"])
    output = tmp_path / "inventory.md"
    previous = os.umask(umask)
    try:
        assert (
            builder.main(
                [
                    "--base-dir",
                    str(tmp_path / "containers"),
                    "--inventory",
                    str(output),
                    "--list-installed",
                ],
                applications_dir=tmp_path / "applications",
            )
            == 0
        )
        assert stat.S_IMODE(output.stat().st_mode) == 0o600
        output.chmod(0o640)
        builder.write_inventory(output, tmp_path, [])
        assert stat.S_IMODE(output.stat().st_mode) == 0o640
    finally:
        os.umask(previous)
    assert output.read_text(encoding="utf-8").startswith(
        "# Firefox Container Inventory"
    )
    assert not list(tmp_path.glob(".netmon-*.tmp"))


def test_parent_exchange_does_not_redirect_inventory(tmp_path, monkeypatch):
    parent = tmp_path / "output"
    parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "inventory.md"
    sentinel.write_bytes(b"unchanged sentinel")
    original = builder._maintenance_write_at

    def swap(directory, name, content, **kwargs):
        parent.rename(tmp_path / "original-output")
        parent.symlink_to(outside, target_is_directory=True)
        return original(directory, name, content, **kwargs)

    monkeypatch.setattr(builder, "_maintenance_write_at", swap)
    builder.write_inventory(parent / "inventory.md", tmp_path, [])
    assert sentinel.read_bytes() == b"unchanged sentinel"
    assert (tmp_path / "original-output" / "inventory.md").is_file()


def test_leaf_exchange_during_publication_does_not_follow_link(tmp_path, monkeypatch):
    output = tmp_path / "inventory.md"
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"unchanged sentinel")
    original = os.replace

    def swap(source, target, **kwargs):
        output.symlink_to(sentinel)
        return original(source, target, **kwargs)

    monkeypatch.setattr(builder.os, "replace", swap)
    builder.write_inventory(output, tmp_path, [])
    assert sentinel.read_bytes() == b"unchanged sentinel"
    assert not output.is_symlink()


@pytest.mark.parametrize("failure", ["fsync", "replace"])
def test_failed_write_preserves_existing_inventory_and_cleans_temporary(
    tmp_path, monkeypatch, failure
):
    output = tmp_path / "inventory.md"
    output.write_bytes(b"original inventory")

    def fail(*args, **kwargs):
        raise OSError("injected inventory failure")

    monkeypatch.setattr(builder.os, failure, fail)
    with pytest.raises(OSError, match="injected inventory failure"):
        builder.write_inventory(output, tmp_path, [])
    assert output.read_bytes() == b"original inventory"
    assert not list(tmp_path.glob(".netmon-*.tmp"))


@pytest.mark.parametrize("failure", ["exit", "launch"])
def test_service_cleans_inventory_after_child_failure(
    inventory_case, monkeypatch, failure
):
    service, sentinel, _, config = inventory_case
    paths = []

    def run(command, **kwargs):
        output = Path(command[command.index("--inventory") + 1])
        paths.append(output)
        output.write_bytes(b"partial inventory")
        if failure == "launch":
            raise OSError("injected launch failure")
        return SimpleNamespace(returncode=1, stdout="", stderr="failed")

    monkeypatch.setattr("netmon.modules.secure_browser.service.subprocess.run", run)
    if failure == "launch":
        with pytest.raises(OSError, match="injected launch failure"):
            service._run_builder_command(_command(service, config, []))
    else:
        result = service._run_builder_command(_command(service, config, []))
        assert result["ok"] is False
        assert result["stderr"] == "failed"
    assert paths and all(not path.parent.exists() for path in paths)
    assert sentinel.read_bytes() == b"unchanged sentinel"


def test_parallel_service_invocations_use_independent_outputs(
    inventory_case, monkeypatch
):
    service, sentinel, _, config = inventory_case
    barrier = threading.Barrier(6)
    outputs = []

    def run(command, **kwargs):
        output = Path(command[command.index("--inventory") + 1])
        outputs.append(output)
        builder.write_inventory(output, output.parent, [])
        barrier.wait(timeout=10)
        assert output.read_bytes().startswith(b"# Firefox Container Inventory")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("netmon.modules.secure_browser.service.subprocess.run", run)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(
            pool.map(
                lambda _: service._run_builder_command(_command(service, config, [])),
                range(6),
            )
        )
    assert all(result["ok"] for result in results)
    assert len(set(outputs)) == 6
    assert all(not path.parent.exists() for path in outputs)
    assert sentinel.read_bytes() == b"unchanged sentinel"


def test_preview_allocates_no_output(inventory_case, tmp_path, monkeypatch):
    service, sentinel, _, _ = inventory_case
    before = set(tmp_path.iterdir())
    apply = service.build_apply_preview(name="Test", target_dir=tmp_path / "Test")
    monkeypatch.setattr(service, "get_default_source_firefox_dir", lambda: None)
    create = service.build_create_preview(
        "Test",
        "https://example.invalid",
        ["example.invalid"],
        target_dir=tmp_path / "Test",
        menu_name="Test",
        new_tab_url="about:blank",
        icon_mode="auto",
    )
    assert set(tmp_path.iterdir()) == before
    assert sentinel.read_bytes() == b"unchanged sentinel"
    for preview in [create, apply]:
        assert "--inventory <temporary-inventory>" in preview["command"]
        assert service.RUNTIME_INVENTORY_FILENAME not in preview["command"]


def test_explicit_regular_inventory_is_retained(inventory_case, tmp_path, monkeypatch):
    service, _, _, config = inventory_case
    explicit = tmp_path / "explicit.md"

    def run(command, **kwargs):
        assert command.count("--inventory") == 1
        assert command[command.index("--inventory") + 1] == str(explicit)
        builder.write_inventory(explicit, tmp_path, [])
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("netmon.modules.secure_browser.service.subprocess.run", run)
    result = service._run_builder_command(
        [*_command(service, config, []), "--inventory", str(explicit)]
    )
    assert result["ok"]
    assert explicit.is_file()


@pytest.mark.parametrize(
    "mode",
    [
        ["--list-installed"],
        ["--refresh-existing", "--apply"],
        ["--register-existing", "--apply"],
        ["--repair-policy", "--apply"],
        ["--cleanup-menu", "--apply"],
    ],
)
def test_real_builder_child_uses_private_inventory(inventory_case, monkeypatch, mode):
    service, sentinel, _, config = inventory_case
    import subprocess

    original = subprocess.run
    outputs = []

    def run(command, **kwargs):
        output = Path(command[command.index("--inventory") + 1])
        outputs.append(output)
        assert stat.S_IMODE(output.parent.stat().st_mode) == 0o700
        return original(command, **kwargs)

    monkeypatch.setattr("netmon.modules.secure_browser.service.subprocess.run", run)
    before = config.read_bytes()
    result = service._run_builder_command(_command(service, config, mode))
    assert result["ok"], result["stderr"]
    assert "Inventory written to:" in result["stdout"]
    assert outputs and not outputs[0].parent.exists()
    assert sentinel.read_bytes() == b"unchanged sentinel"
    assert config.read_bytes() == before
