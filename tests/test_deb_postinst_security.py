"""Generate maintainer scripts without building/installing a package or using root."""

import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "main": ("build_netmon_deb.sh", "/usr/share/netmon/assets/log-pics"),
    "dark": ("build_netmon_dark_deb.sh", "/opt/netmon-dark/assets/log-pics"),
}


@pytest.fixture(params=VARIANTS, ids=VARIANTS)
def package(request, tmp_path):
    name = request.param
    builder, assets = VARIANTS[name]
    source = (ROOT / "scripts" / builder).read_text()
    # Execute only the literal, quoted postinst emitter, never the build script.
    match = re.search(
        r'^cat > "\$PKG_DIR/DEBIAN/postinst" <<\'([A-Z]+)\'\n(.*?)^\1$',
        source,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    staging = tmp_path / "package"
    (staging / "DEBIAN").mkdir(parents=True)
    result = subprocess.run(
        ["bash", "-c", 'PKG_DIR="$1"\n' + match[0], "emit-postinst", str(staging)],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    postinst = staging / "DEBIAN/postinst"
    assert postinst.read_text() == match[2]
    return name, source, postinst, staging / assets.lstrip("/"), assets


def _manifest(root):
    """Record synthetic files and links without following directory symlinks."""
    result = {}
    for directory, directories, files in os.walk(root, followlinks=False):
        for path in [
            Path(directory),
            *(Path(directory) / n for n in directories + files),
        ]:
            info = path.lstat()
            content = None
            if stat.S_ISLNK(info.st_mode):
                content = os.readlink(path)
            elif stat.S_ISREG(info.st_mode):
                content = hashlib.sha256(path.read_bytes()).hexdigest()
            result[str(path.relative_to(root))] = (
                info.st_ino,
                info.st_mode,
                info.st_uid,
                info.st_gid,
                info.st_nlink,
                info.st_mtime_ns,
                info.st_ctime_ns,
                content,
            )
    return result


def _simulate_postinst(package, tmp_path, home, *, skel_documents="Documents"):
    name, _source, postinst, assets, original_assets = package
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "new.png").write_bytes(b"synthetic new image")
    (assets / "keep.jpg").write_bytes(b"package image must not replace user image")
    skel = tmp_path / "skel"
    skeleton_images = skel / skel_documents / "NetMon/Log-Pics"
    skeleton_images.mkdir(parents=True)
    (skeleton_images / "keep.jpg").write_bytes(b"existing skeleton image")
    state = tmp_path / "system-state"
    state.mkdir()
    translated = postinst.read_text()
    assert translated.count(f'ASSET_DIR="{original_assets}"') == 1
    assert translated.count('seed_netmon_log_pics_for_home "/etc/skel"') == 1
    translated = translated.replace(original_assets, str(assets))
    translated = translated.replace('"/etc/skel"', f'"{skel}"')
    if name == "main":
        assert translated.count('NETMON_STATE_DIR="/var/lib/netmon"') == 1
        translated = translated.replace('"/var/lib/netmon"', f'"{state}"')
    script = tmp_path / "simulated-postinst.sh"
    script.write_text(translated)
    commands = tmp_path / "commands"
    commands.mkdir()
    calls = tmp_path / "calls"
    # Child shell commands cannot use the pytest Popen guard. Intercept every
    # account/ownership/host-service command in this reviewed script explicitly.
    responses = {
        "getent": 'printf "synthetic:x:1000:1000:Test:%s:/bin/false\\n" "$TEST_USER_HOME"',
        "chown": ":",
        "nmcli": "exit 90",
        "update-desktop-database": ":",
    }
    for command, response in responses.items():
        fake = commands / command
        fake.write_text(
            f'#!/bin/sh\nprintf "{command}\\n" >> "$TEST_CALLS"\n{response}\n'
        )
        fake.chmod(0o700)
    env = dict(os.environ)
    env.update(
        PATH=f"{commands}:/usr/bin:/bin",
        SUDO_USER="synthetic",
        HOME=str(home),
        TEST_USER_HOME=str(home),
        TEST_CALLS=str(calls),
    )
    result = subprocess.run(
        ["/bin/sh", str(script), "configure"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return calls.read_text().splitlines(), skeleton_images


def test_generated_postinst_has_no_sudo_user_or_ownership_operations(package):
    _name, _source, postinst, _assets, _original_assets = package
    text = postinst.read_text()
    assert "SUDO_USER" not in text
    assert "USER_HOME" not in text
    assert "getent" not in text
    assert not re.search(r"\b(?:chown|chgrp)\b", text)
    assert 'seed_netmon_log_pics_for_home "/etc/skel"' in text
    assert 'documents_root_for_home "$HOME_DIR"' in text
    assert "update-desktop-database /usr/share/applications" in text


def test_builder_and_generated_postinst_are_syntactically_valid(package):
    name, _source, postinst, _assets, _original_assets = package
    builder = ROOT / "scripts" / VARIANTS[name][0]
    for interpreter, script in (("bash", builder), ("/bin/sh", postinst)):
        result = subprocess.run(
            [interpreter, "-n", str(script)], capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, result.stderr


def test_real_asset_copy_fragment_keeps_system_package_images(package, tmp_path):
    name, source, _postinst, assets, _original_assets = package
    fixture = tmp_path / "source"
    images = fixture / "tools/Log-Pics"
    images.mkdir(parents=True)
    expected = {
        "one.png": b"png fixture",
        "two.JPG": b"jpg fixture",
        "three.jpeg": b"jpeg fixture",
    }
    for filename, content in expected.items():
        (images / filename).write_bytes(content)
    assets.mkdir(parents=True)
    if name == "main":
        functions = []
        for function in ("copy_tree", "copy_tree_if_exists"):
            match = re.search(rf"^{function}\(\) \{{\n.*?^\}}", source, re.M | re.S)
            assert match is not None
            functions.append(match[0])
        copy = 'copy_tree_if_exists "$ROOT_DIR/tools/Log-Pics" "$ASSETS_ROOT/log-pics"'
        assert source.count(copy) == 1
        body = "\n".join(functions) + "\n" + copy
        setup = 'ASSETS_ROOT="$2"\n'
        destination = assets.parent
    else:
        body = source.split("# Optional seed images for Log overlay\n", 1)[1].split(
            "# Launcher (dark test)", 1
        )[0]
        assert '"$PKG_DIR/opt/netmon-dark/assets/log-pics/"' in body
        setup = 'PKG_DIR="$2"\n'
        destination = assets.parents[3]
    result = subprocess.run(
        [
            "bash",
            "-c",
            'set -eu\nROOT_DIR="$1"\n' + setup + body,
            "copy-system-assets",
            str(fixture),
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert {p.name: p.read_bytes() for p in assets.iterdir()} == expected


@pytest.mark.parametrize("documents", ["Documents", "Dokumente"])
@pytest.mark.parametrize(
    "layout",
    [
        "directory",
        "documents-link",
        "netmon-link",
        "images-link",
        "file-link",
        "dangling-file-link",
    ],
)
def test_simulated_postinst_preserves_user_files_and_symlink_targets(
    package, tmp_path, documents, layout
):
    users = tmp_path / "users"
    home = users / "home"
    home.mkdir(parents=True)
    victim = users / "symlink-target"
    victim.mkdir()
    doc = home / documents
    if layout == "documents-link":
        doc.symlink_to(victim, target_is_directory=True)
    else:
        doc.mkdir()
    netmon = doc / "NetMon"
    if layout == "netmon-link":
        netmon.symlink_to(victim, target_is_directory=True)
    else:
        netmon.mkdir()
    images = netmon / "Log-Pics"
    if layout == "images-link":
        images.symlink_to(victim, target_is_directory=True)
    else:
        images.mkdir()
    if layout == "file-link":
        target = victim / "existing-image"
        target.write_bytes(b"user-owned image sentinel")
        (images / "keep.jpg").symlink_to(target)
    else:
        (images / "keep.jpg").write_bytes(b"user-owned image sentinel")
    if layout == "dangling-file-link":
        (images / "new.png").symlink_to(victim / "must-not-be-created")
    (home / "unrelated.txt").write_bytes(b"unrelated user data")
    before = _manifest(users)
    calls, _skeleton = _simulate_postinst(package, tmp_path, home)
    assert _manifest(users) == before
    assert calls == ["update-desktop-database"]


@pytest.mark.parametrize("documents", ["Documents", "Dokumente"])
def test_skeleton_seed_and_desktop_refresh_remain_functional(
    package, tmp_path, documents
):
    home = tmp_path / "untouched-home"
    home.mkdir()
    before = _manifest(home)
    calls, skeleton = _simulate_postinst(
        package, tmp_path, home, skel_documents=documents
    )
    assert calls == ["update-desktop-database"]
    assert (skeleton / "new.png").read_bytes() == b"synthetic new image"
    assert (skeleton / "keep.jpg").read_bytes() == b"existing skeleton image"
    assert _manifest(home) == before
