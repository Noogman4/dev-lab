"""M-03: passive discovery must never execute untrusted container content."""

import os
import shlex
import sqlite3
import subprocess

import pytest

from netmon.modules.secure_browser.manager import SecureBrowserManager
from netmon.modules.secure_browser.service import SecureBrowserService
from tools.secure_browser_manager import browser_container_builder as builder


@pytest.fixture
def container(tmp_path):
    root = tmp_path / "containers" / "firefox-GitHub"
    binary = root / "firefox" / "firefox"
    binary.parent.mkdir(parents=True)
    sentinel = tmp_path / "executed"
    binary.write_text(
        "#!/bin/sh\nprintf executed > "
        + shlex.quote(str(sentinel))
        + '\nprintf "Mozilla Firefox 999.0\\n"\n',
        encoding="utf-8",
    )
    binary.chmod(0o700)
    return root, binary, sentinel


def metadata(binary, version="140.0.2"):
    path = binary.parent / "application.ini"
    path.write_text(
        f"[App]\nName=Firefox\nVendor=Mozilla\nVersion={version}\n", encoding="utf-8"
    )
    return path


@pytest.mark.parametrize("version", ["140.0.2", "128.14.0esr", "143.0a1", "142.0b12"])
def test_passive_metadata_and_sentinel(container, version):
    root, binary, sentinel = container
    metadata(binary, version)
    found = builder.discover_existing_containers(root.parent)
    assert len(found) == 1
    assert found[0].binary_path == binary
    assert found[0].version == version
    assert not sentinel.exists()


@pytest.mark.parametrize(
    "content",
    [
        None,
        b"",
        b"not ini",
        b"\xff",
        b"[App]\nName=Firefox\n",
        b"[App]\nName=NotFirefox\nVersion=140.0\n",
        b"[App]\nName=Firefox\nVendor=Other\nVersion=140.0\n",
        b"[App]\nName=Firefox\nVersion=140.0\nVersion=999.0\n",
        b"[App]\nName=Firefox\nVersion=140.0\n[App]\nVersion=999.0\n",
        b"[DEFAULT]\nVersion=140.0\n[App]\nName=Firefox\n",
        b"[App]\nName=Firefox\nVersion=Mozilla Firefox 140.0\n",
        b"[App]\nName=Firefox\nVersion=140.0;echo bad\n",
        b"[App]\nName=Firefox\nVersion=140.0\n continuation\n",
        b"[App]\nName=Firefox\nVersion=140.0\x00\n",
        b"[App]\nName=Firefox\nVersion=9999.0\n",
        b"[App]\nName=Firefox\nVersion=" + b"1." * 100 + b"1\n",
    ],
)
def test_missing_corrupt_or_conflicting_metadata_is_unknown(container, content):
    root, binary, sentinel = container
    if content is not None:
        (binary.parent / "application.ini").write_bytes(content)
    assert builder.discover_container(binary).version == "unbekannt"
    assert not sentinel.exists()


def test_oversized_metadata_rejected_before_read(container, monkeypatch):
    _, binary, sentinel = container
    path = metadata(binary)
    path.write_bytes(b"x" * (builder.MAX_VERSION_FILE_SIZE + 1))

    def forbidden(*args, **kwargs):
        pytest.fail("Oversized metadata must not be opened")

    monkeypatch.setattr(builder.os, "fdopen", forbidden)
    assert builder.read_firefox_version(binary) == "unbekannt"
    assert not sentinel.exists()


@pytest.mark.parametrize(
    "kind", ["symlink", "broken-link", "fifo", "directory", "socket"]
)
def test_special_metadata_never_opened(container, tmp_path, monkeypatch, kind):
    import socket

    _, binary, sentinel = container
    target = binary.parent / "application.ini"
    sock = None
    if kind == "symlink":
        external = tmp_path / "outside.ini"
        external.write_text("[App]\nName=Firefox\nVersion=140.0\n")
        target.symlink_to(external)
    elif kind == "broken-link":
        target.symlink_to(tmp_path / "missing")
    elif kind == "fifo":
        os.mkfifo(target)
    elif kind == "directory":
        target.mkdir()
    else:
        sock = socket.socket(socket.AF_UNIX)
        # Bind through a directory descriptor to stay below sun_path length.
        with builder.open_scan_directory(binary.parent) as descriptor:
            sock.bind(f"/proc/self/fd/{descriptor}/application.ini")
    original = builder.os.open

    def guarded(path, flags, *args, **kwargs):
        assert str(path) != "application.ini", "Special metadata must not be opened"
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(builder.os, "open", guarded)
    try:
        assert builder.read_firefox_version(binary) == "unbekannt"
        assert not sentinel.exists()
    finally:
        if sock:
            sock.close()


@pytest.mark.parametrize("target", ["binary", "firefox-dir", "container-dir"])
def test_symlinked_paths_are_not_trusted(container, tmp_path, target):
    root, binary, sentinel = container
    metadata(binary)
    if target == "binary":
        actual = binary.with_name("actual")
        binary.rename(actual)
        binary.symlink_to(actual)
    elif target == "firefox-dir":
        actual = root / "actual"
        binary.parent.rename(actual)
        (root / "firefox").symlink_to(actual, target_is_directory=True)
    else:
        actual = tmp_path / "actual-container"
        root.rename(actual)
        root.symlink_to(actual, target_is_directory=True)
    assert builder.read_firefox_version(binary) == "unbekannt"
    assert not builder.discover_existing_containers(root.parent)
    assert not sentinel.exists()


def test_metadata_ancestor_replaced_during_open_is_not_followed(container, monkeypatch):
    _, binary, sentinel = container
    path = metadata(binary)
    original = builder.os.open

    def raced(name, flags, *args, **kwargs):
        if name == "application.ini":
            path.rename(path.with_suffix(".old"))
            path.symlink_to(path.with_suffix(".old"))
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(builder.os, "open", raced)
    assert builder.read_firefox_version(binary) == "unbekannt"
    assert not sentinel.exists()


def test_multiple_nested_containers_and_symlink_cycle(container, tmp_path):
    root, binary, sentinel = container
    metadata(binary)
    second = root.parent / "nested" / "Other" / "firefox" / "firefox"
    second.parent.mkdir(parents=True)
    second.write_bytes(binary.read_bytes())
    second.chmod(0o700)
    metadata(second, "128.14.0esr")
    (root.parent / "loop").symlink_to(root.parent, target_is_directory=True)
    (root / "firefox" / "link").symlink_to(tmp_path, target_is_directory=True)
    found = builder.discover_existing_containers(root.parent)
    assert {c.name: c.version for c in found} == {
        "firefox-GitHub": "140.0.2",
        "Other": "128.14.0esr",
    }
    assert not sentinel.exists()


def test_repeated_service_refresh_reports_and_previews_are_passive(
    container, tmp_path, monkeypatch
):
    root, binary, sentinel = container
    metadata(binary)
    profile = root / "profile"
    profile.mkdir()
    (profile / "prefs.js").write_text("// profile")
    (root / "user.js").write_text(
        'user_pref("browser.startup.homepage", "https://github.com");'
    )
    (root / "policies.json").write_text('{"policies": {}}')
    (root / "start.sh").write_text(
        f'#!/bin/sh\nexec "{binary}" --no-remote --profile "{profile}"\n'
    )
    (root / "launcher.desktop").write_text(
        f'[Desktop Entry]\nExec={root / "start.sh"}\n'
    )
    # Both executable artifacts would create the sentinel if invoked.
    (root / "start.sh").chmod(0o700)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    service = SecureBrowserService()
    module = service._load_tool_module()
    monkeypatch.setattr(service, "get_default_base_dir", lambda: root.parent)
    monkeypatch.setattr(module, "DEFAULT_PROFILE_BASE_DIRS", [tmp_path / "profiles"])
    monkeypatch.setattr(module, "DEFAULT_APPLICATIONS_DIR", tmp_path / "applications")
    manager = SecureBrowserManager(service=service)

    def forbidden(*args, **kwargs):
        pytest.fail("Passive inventory attempted to launch a process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    for _ in range(3):
        containers = manager.scan_inventory()
        assert len(containers) == 1
        current = containers[0]
        assert current.profile_path == profile
        assert current.homepage_url == "https://github.com"
        assert "start.sh: OK" in service.verify_container(current)
        assert service.read_container_artifacts(current)["start.sh"].startswith(
            "#!/bin/sh"
        )
        assert service.inspect_launchers(current)["launcher.desktop"]["Exec"] == str(
            root / "start.sh"
        )
        assert service.read_policy_json(current)
        assert "Menüeintrag fehlt" in service.derive_risk_hints(current)
        assert service.run_register_existing_dry_run(container_name=current.name)
        assert service.run_refresh_existing_dry_run(container_name=current.name)
    assert {p: p.read_bytes() for p in root.rglob("*") if p.is_file()} == before
    assert not sentinel.exists()


def test_profile_correlation_and_risks_are_preserved(container, tmp_path):
    root, binary, sentinel = container
    renamed = root.with_name("firefox-chatgpt")
    root.rename(renamed)
    root = renamed
    profiles = tmp_path / "profiles"
    profile = profiles / "default"
    profile.mkdir(parents=True)
    (profile / "prefs.js").write_text("// https://chatgpt.com/")
    connection = sqlite3.connect(profile / "places.sqlite")
    connection.execute("CREATE TABLE moz_places (url TEXT, last_visit_date INTEGER)")
    connection.execute(
        "INSERT INTO moz_places VALUES (?, ?)", ("https://chatgpt.com/login", 1)
    )
    connection.commit()
    connection.close()
    found = builder.discover_existing_containers(root.parent)
    builder.correlate_profiles(found, builder.discover_firefox_profiles([profiles]))
    assert found[0].correlated_profile_path == profile
    assert found[0].start_script_suggestion
    assert "Keine user.js erkannt." in found[0].risk_hints
    assert "Keine policies.json erkannt." in found[0].risk_hints
    assert not sentinel.exists()


@pytest.mark.parametrize("limit", ["entries", "depth", "containers", "text"])
def test_inventory_resource_limits_fail_explicitly(container, monkeypatch, limit):
    root, binary, sentinel = container
    if limit == "entries":
        monkeypatch.setattr(builder, "MAX_SCAN_ENTRIES", 1)
    elif limit == "depth":
        monkeypatch.setattr(builder, "MAX_SCAN_DEPTH", 1)
    elif limit == "containers":
        monkeypatch.setattr(builder, "MAX_SCAN_CONTAINERS", 0)
    else:
        (root / "user.js").write_text("// https://github.com/")
        monkeypatch.setattr(builder, "MAX_SCAN_TEXT_BYTES", 1)
    with pytest.raises(ValueError, match="budget exceeded; scan incomplete"):
        builder.discover_existing_containers(root.parent)
    assert not sentinel.exists()


def test_service_artifacts_reject_large_files_and_links(container, tmp_path):
    root, binary, sentinel = container
    service = SecureBrowserService()
    (root / "start.sh").write_bytes(b"x" * (builder.MAX_SCAN_FILE_SIZE + 1))
    target = tmp_path / "outside.desktop"
    target.write_text("[Desktop Entry]\nExec=untrusted\n")
    (root / "launcher.desktop").symlink_to(target)
    assert service._read_preview(root / "start.sh") == "(leer oder nicht sicher lesbar)"
    assert service._parse_desktop_entry(root / "launcher.desktop") == {}
    assert not sentinel.exists()


def test_read_budget_applies_even_when_size_metadata_is_stale(container, monkeypatch):
    from types import SimpleNamespace

    _, binary, sentinel = container
    path = metadata(binary)
    path.write_bytes(b"x" * (builder.MAX_VERSION_FILE_SIZE + 1))
    original_stat, original_fstat = os.stat, os.fstat

    def stale(result):
        return SimpleNamespace(
            st_mode=result.st_mode,
            st_dev=result.st_dev,
            st_ino=result.st_ino,
            st_size=0,
            st_mtime_ns=result.st_mtime_ns,
            st_ctime_ns=result.st_ctime_ns,
        )

    def stat_file(name, *args, **kwargs):
        result = original_stat(name, *args, **kwargs)
        return stale(result) if name == "application.ini" else result

    monkeypatch.setattr(builder.os, "stat", stat_file)
    monkeypatch.setattr(builder.os, "fstat", lambda fd: stale(original_fstat(fd)))
    assert builder.read_firefox_version(binary) == "unbekannt"
    assert not sentinel.exists()


def test_open_parent_descriptor_cannot_be_redirected_to_other_metadata(
    container, tmp_path, monkeypatch
):
    root, binary, sentinel = container
    metadata(binary)
    other = tmp_path / "other"
    other.mkdir()
    (other / "application.ini").write_text("[App]\nName=Firefox\nVersion=999.0\n")
    original = os.open

    def raced(name, flags, *args, **kwargs):
        if name == "application.ini":
            binary.parent.rename(root / "original-firefox")
            binary.parent.symlink_to(other, target_is_directory=True)
        return original(name, flags, *args, **kwargs)

    monkeypatch.setattr(builder.os, "open", raced)
    # The parent FD was already opened; the attacker cannot substitute "999.0".
    assert builder.read_firefox_version(binary) == "140.0.2"
    assert not sentinel.exists()


def test_profile_symlink_loop_does_not_abort_inventory(container):
    root, binary, sentinel = container
    loop = root / "loop"
    loop.symlink_to(loop)
    (root / "start.sh").write_text(f'firefox --profile "{loop}"\n')
    assert builder.discover_container(binary).profile_path is None
    assert not sentinel.exists()


def test_cli_inventory_export_is_passive_and_labels_untrusted_metadata(
    container, tmp_path, monkeypatch
):
    root, binary, sentinel = container
    metadata(binary)
    monkeypatch.setattr(builder, "DEFAULT_PROFILE_BASE_DIRS", [tmp_path / "profiles"])
    output = tmp_path / "inventory.md"
    assert (
        builder.main(
            [
                "--base-dir",
                str(root.parent),
                "--inventory",
                str(output),
                "--list-installed",
            ],
            applications_dir=tmp_path / "applications",
        )
        == 0
    )
    text = output.read_text()
    assert "140.0.2" in text and "kein Echtheitsnachweis" in text
    assert not sentinel.exists()
