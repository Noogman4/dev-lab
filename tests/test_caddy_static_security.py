"""Static export/policy checks and optional real Caddy tests; synthetic state only."""

import http.client
import importlib.util
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import time
from types import SimpleNamespace
from urllib.parse import quote, unquote
import posixpath

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "caddy_export", ROOT / "scripts/export_netmon_caddy_site.py"
)
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)
CANARY = b"SYNTHETIC-PRIVATE-CADDY-CANARY"
PRIVATE_PATHS = [
    "download-config.php",
    "download-lib.php",
    "download-stats.php",
    "download.php",
    "data/download-stats.json",
    "data/download-stats.json.lock",
    "data/new-file.html",
    "data/new/nested.json",
    ".htaccess",
    ".env",
    ".git/config",
    "htaccess",
    "Caddyfile",
    "README.md",
    "DEPLOY_HTTPS.md",
    "config.json",
    "private.html",
    "new.PHP",
    "new.php8",
    "new.phtml",
    "new.phar",
    "new.php.bak",
    "screenshots/leak.php.png",
    "dist/private-config.json",
    "verify/private.key",
]
ENCODED_PRIVATE_PATHS = [
    "/site/download%2dconfig%2ephp",
    "/%73ite/%64ata/download-stats.json",
    "/site/%2e%2e/site/download-lib.php",
    "/download-config.php/extra",
    "/site/new.PHP5",
    "/data%2fnew-file.html",
    "/.%65nv",
    "/verify/%2e%2e/data/download-stats.json",
    "/site/%252eenv",
]


@pytest.fixture
def bundle(tmp_path):
    source = tmp_path / "public_html"
    source.mkdir()
    # Existing public content, plus synthetic release artefacts. No package build.
    for file in (ROOT / "site").rglob("*"):
        path = file.relative_to(ROOT / "site").as_posix()
        if file.is_file() and exporter.is_public(path):
            target = source / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(file.read_bytes())
    config = (ROOT / "site/download-config.php").read_bytes()
    (source / "download-config.php").write_bytes(config)
    targets = exporter.download_targets(config.decode())
    for target in targets.values():
        path = source / target[1:]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"SYNTHETIC-PUBLIC-ARTIFACT\n")
    for path in PRIVATE_PATHS:
        if path == "download-config.php":
            continue
        file = source / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(CANARY)
    return source, tmp_path / "public", targets


def test_original_configuration_exposes_existing_private_files_by_static_resolution(
    tmp_path,
):
    # This is a configuration/filesystem proof, explicitly NOT a Caddy runtime.
    original = subprocess.check_output(
        ["git", "show", "87dca86203b6a31daeb397a96f9c7b3dbfcbfc0d:site/Caddyfile"],
        cwd=ROOT,
        text=True,
    )
    assert "root * /srv/netmonroots" in original
    assert "file_server" in original and "php_fastcgi" not in original
    assert "try_files {path} {path}/ /site/index.html" in original
    assert "respond" not in original and "hide" not in original
    for path in PRIVATE_PATHS:
        file = tmp_path / "site" / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(CANARY)
        # First try_files candidate exists and is the statically served file.
        assert (tmp_path / ("/site/" + path).lstrip("/")).read_bytes() == CANARY


@pytest.mark.parametrize("path", PRIVATE_PATHS)
def test_private_paths_never_enter_export_or_caddy_allowlist(bundle, path):
    source, public, _ = bundle
    exporter.export_site(source, public)
    assert not (public / path).exists()
    assert not exporter.is_public(path)
    assert not exporter.is_public("site/" + path)
    assert CANARY not in b"".join(
        p.read_bytes() for p in public.rglob("*") if p.is_file()
    )


@pytest.mark.parametrize("path", ENCODED_PRIVATE_PATHS)
def test_decoded_and_normalized_private_paths_are_not_public(path):
    # Policy-level check only; actual HTTP decoding is covered by the optional
    # Caddy runtime below, not by a substitute HTTP server.
    decoded = posixpath.normpath(unquote(path))
    if decoded.startswith("/site/"):
        decoded = decoded[5:]
    assert not exporter.is_public(decoded.lstrip("/"))


def test_export_keeps_source_and_public_binary_bytes_and_download_targets(bundle):
    source, public, targets = bundle
    before = {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    exporter.export_site(source, public)
    assert before == {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    for path in public.rglob("*"):
        if path.is_file() and path.suffix != ".html":
            assert path.read_bytes() == (source / path.relative_to(public)).read_bytes()
    for target in targets.values():
        assert (public / target[1:]).is_file()
    for page in (
        "downloads.html",
        "en/downloads.html",
        "download1.html",
        "en/download1.html",
    ):
        text = (public / page).read_text()
        assert 'href="/download.php?' not in text
        assert targets["netmon-deb"] + "?dl=1" in text
        assert targets["sha256sums"] + "?dl=1" in text
    assert "download.php?id=" in (source / "downloads.html").read_text()


def test_signed_documentation_stays_byte_identical(bundle):
    source, public, targets = bundle
    path = targets["docs-html"][1:]
    content = b'<a href="/download.php?id=netmon-deb">Signed documentation example</a>'
    (source / path).write_bytes(content)
    exporter.export_site(source, public)
    for file in (source / "dist").rglob("*"):
        if file.is_file() and exporter.is_public(file.relative_to(source).as_posix()):
            assert (public / file.relative_to(source)).read_bytes() == file.read_bytes()
    assert (public / path).read_bytes() == content


def test_quoted_html_attributes_with_spacing_are_rewritten():
    targets = {"netmon-deb": "/dist/netmon_1_all.deb"}
    result = exporter.static_links(
        "<a HREF = '/download.php?id=netmon-deb'>x</a>", targets
    )
    assert "href='/dist/netmon_1_all.deb?dl=1'" in result


@pytest.mark.parametrize(
    "name", ["download-config.php", "index.html", "screenshots/escape.png"]
)
def test_export_does_not_follow_source_symlinks(bundle, tmp_path, name):
    source, public, _ = bundle
    outside = tmp_path / "outside"
    outside.write_bytes(CANARY)
    link = source / name
    if link.exists():
        link.unlink()
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)
    with pytest.raises((OSError, ValueError)):
        exporter.export_site(source, public)
    assert outside.read_bytes() == CANARY
    if public.exists():
        assert CANARY not in b"".join(
            p.read_bytes() for p in public.rglob("*") if p.is_file()
        )


def test_directory_symlink_cannot_publish_private_html(bundle, tmp_path):
    source, public, _ = bundle
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "index.html").write_bytes(CANARY)
    shutil.rmtree(source / "en")
    (source / "en").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlinks"):
        exporter.export_site(source, public)
    assert not (public / "en/index.html").exists()


def test_existing_output_is_never_merged_or_overwritten(bundle):
    source, public, _ = bundle
    public.mkdir()
    (public / "sentinel").write_bytes(CANARY)
    with pytest.raises(FileExistsError):
        exporter.export_site(source, public)
    assert list(public.iterdir()) == [public / "sentinel"]
    assert (public / "sentinel").read_bytes() == CANARY


def test_output_must_be_outside_source(bundle):
    source, _, _ = bundle
    with pytest.raises(ValueError):
        exporter.export_site(source, source / "nested")
    assert not (source / "nested").exists()


def test_missing_download_fails_export(bundle):
    source, public, targets = bundle
    (source / targets["netmon-deb"][1:]).unlink()
    with pytest.raises(ValueError, match="Incomplete"):
        exporter.export_site(source, public)


@pytest.mark.parametrize(
    "value", ["missing", "netmon-deb&id=sha256sums", "", "netmon-deb%00"]
)
def test_unknown_or_ambiguous_download_links_fail(value):
    with pytest.raises(ValueError):
        exporter.static_links(
            '<a href="/download.php?id=' + value + '">x</a>',
            {"netmon-deb": "/dist/netmon_1_all.deb"},
        )


@pytest.mark.parametrize(
    "target",
    [
        "/data/download-stats.json",
        "https://example.invalid/x",
        "/dist/../data/state.json",
        "/config.json",
    ],
)
def test_config_cannot_redirect_exported_links_to_private_targets(target):
    config = '"test" => ["label" => "x", "target" => "' + target + '"]'
    with pytest.raises(ValueError):
        exporter.download_targets(config)


def test_caddy_policy_has_literal_order_no_fallback_and_same_public_pattern():
    config = (ROOT / "site/Caddyfile").read_text()
    pattern = re.search(r"@public path_regexp public (.+)", config)[1]
    assert pattern == exporter.PUBLIC_PATH
    assert "root * /srv/netmonroots/public" in config
    assert "try_files" not in config and "php_fastcgi" not in config
    assert "browse" not in config
    route = config.split("\troute {", 1)[1]
    assert (
        route.index("respond @private 404")
        < route.index("uri /site/*")
        < route.index("file_server @public")
    )
    assert "not method GET HEAD" in config
    original = subprocess.check_output(
        ["git", "show", "87dca862:site/Caddyfile"], cwd=ROOT, text=True
    )
    assert (
        config.split("\nnetmonroots.com {\n", 1)[0]
        == original.split("\nnetmonroots.com {\n", 1)[0]
    )
    assert (
        config[config.index("\theader {") :] == original[original.index("\theader {") :]
    )


@pytest.mark.parametrize("mask", [0o000, 0o002, 0o022, 0o077])
def test_export_permissions_are_bounded_without_umask_or_chmod_changes(
    bundle, monkeypatch, mask
):
    source, public, targets = bundle
    change_mask = os.umask
    previous = change_mask(mask)

    def forbidden(*_args, **_kwargs):
        pytest.fail("Exporter must not change umask or chmod a path")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(exporter.os, "umask", forbidden)
            patch.setattr(exporter.os, "chmod", forbidden)
            exporter.export_site(source, public)
    finally:
        change_mask(previous)
    for path in [public, *public.rglob("*")]:
        info = path.stat()
        maximum = 0o755 if path.is_dir() else 0o644
        assert not stat.S_IMODE(info.st_mode) & ~maximum, (path, oct(info.st_mode))
        assert info.st_uid == os.geteuid()
    for target in targets.values():
        assert (public / target[1:]).read_bytes() == (source / target[1:]).read_bytes()


@pytest.mark.parametrize("mode", [0o777, 0o775])
def test_preexisting_unsafe_output_is_not_adopted_or_modified(bundle, mode):
    source, public, _ = bundle
    public.mkdir()
    public.chmod(mode)
    (public / "sentinel").write_bytes(CANARY)
    before = public.stat()
    with pytest.raises(FileExistsError):
        exporter.export_site(source, public)
    assert stat.S_IMODE(public.stat().st_mode) == stat.S_IMODE(before.st_mode)
    assert list(public.iterdir()) == [public / "sentinel"]
    assert (public / "sentinel").read_bytes() == CANARY


def test_output_symlink_is_not_adopted(bundle, tmp_path):
    source, public, _ = bundle
    victim = tmp_path / "victim"
    victim.mkdir(mode=0o750)
    (victim / "sentinel").write_bytes(CANARY)
    public.symlink_to(victim, target_is_directory=True)
    before = victim.stat()
    with pytest.raises(FileExistsError):
        exporter.export_site(source, public)
    assert victim.stat().st_mode == before.st_mode
    assert list(victim.iterdir()) == [victim / "sentinel"]
    assert (victim / "sentinel").read_bytes() == CANARY


def test_output_root_swap_before_open_never_changes_victim(
    bundle, tmp_path, monkeypatch
):
    source, public, _ = bundle
    victim = tmp_path / "victim"
    victim.mkdir(mode=0o750)
    (victim / "sentinel").write_bytes(CANARY)
    before = victim.stat()
    mkdir = os.mkdir
    swapped = False

    def swap(name, *args, **kwargs):
        nonlocal swapped
        mkdir(name, *args, **kwargs)
        if name == public.name and kwargs.get("dir_fd") is not None:
            public.rename(tmp_path / "created-output")
            public.symlink_to(victim, target_is_directory=True)
            swapped = True

    monkeypatch.setattr(exporter.os, "mkdir", swap)
    with pytest.raises(OSError):
        exporter.export_site(source, public)
    assert swapped
    assert victim.stat().st_mode == before.st_mode
    assert list(victim.iterdir()) == [victim / "sentinel"]
    assert (victim / "sentinel").read_bytes() == CANARY


@pytest.mark.parametrize("kind", ["directory", "file"])
def test_output_path_swap_after_open_is_bound_and_aborts(
    bundle, tmp_path, monkeypatch, kind
):
    source, public, _ = bundle
    victim = tmp_path / "victim"
    if kind == "directory":
        victim.mkdir(mode=0o750)
        (victim / "sentinel").write_bytes(CANARY)
    else:
        victim.write_bytes(CANARY)
    before = victim.stat()
    open_file = os.open
    output_root = None
    swapped = False

    def swap(name, flags, *args, **kwargs):
        nonlocal output_root, swapped
        fd = open_file(name, flags, *args, **kwargs)
        if name == public.name and kwargs.get("dir_fd") is not None:
            output_root = fd
        target = "en" if kind == "directory" else "index.html"
        if name == target and kwargs.get("dir_fd") == output_root and not swapped:
            (public / target).rename(public / "original-held")
            (public / target).symlink_to(
                victim, target_is_directory=kind == "directory"
            )
            swapped = True
        return fd

    monkeypatch.setattr(exporter.os, "open", swap)
    with pytest.raises(ValueError, match="changed during creation"):
        exporter.export_site(source, public)
    assert swapped
    assert victim.stat().st_mode == before.st_mode
    if kind == "directory":
        assert list(victim.iterdir()) == [victim / "sentinel"]
        assert (victim / "sentinel").read_bytes() == CANARY
    else:
        assert victim.read_bytes() == CANARY


@pytest.mark.parametrize("kind", ["directory", "file"])
def test_output_creation_permission_failure_aborts(bundle, monkeypatch, kind):
    source, public, _ = bundle
    original = os.mkdir if kind == "directory" else os.open
    failed = False

    def deny(name, *args, **kwargs):
        nonlocal failed
        if kwargs.get("dir_fd") is not None and (
            name == "en" if kind == "directory" else args[0] & os.O_CREAT
        ):
            failed = True
            raise PermissionError("Synthetic output permission failure")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(exporter.os, "mkdir" if kind == "directory" else "open", deny)
    with pytest.raises(PermissionError, match="Synthetic"):
        exporter.export_site(source, public)
    assert failed


@pytest.mark.parametrize("kind", ["directory", "file"])
@pytest.mark.parametrize("failure", ["unverifiable", "unsafe-mode"])
def test_output_permission_verification_failure_aborts_and_closes_fd(
    bundle, monkeypatch, kind, failure
):
    source, public, _ = bundle
    open_file, fstat = os.open, os.fstat
    selected = None

    def opened(name, flags, *args, **kwargs):
        nonlocal selected
        fd = open_file(name, flags, *args, **kwargs)
        if kwargs.get("dir_fd") is not None and (
            name == public.name if kind == "directory" else flags & os.O_CREAT
        ):
            selected = fd
        return fd

    def checked(fd):
        info = fstat(fd)
        if fd != selected:
            return info
        if failure == "unverifiable":
            raise OSError("Synthetic permission verification failure")
        return SimpleNamespace(
            st_mode=info.st_mode | 0o022,
            st_uid=info.st_uid,
            st_nlink=info.st_nlink,
        )

    monkeypatch.setattr(exporter.os, "open", opened)
    monkeypatch.setattr(exporter.os, "fstat", checked)
    with pytest.raises(OSError if failure == "unverifiable" else ValueError):
        exporter.export_site(source, public)
    assert selected is not None
    with pytest.raises(OSError):
        fstat(selected)


@pytest.fixture
def caddy():
    executable = shutil.which("caddy")
    if not executable:
        pytest.skip(
            "Caddy unavailable: no real Caddy adaptation/HTTP validation performed"
        )
    return executable


def test_real_caddy_adapts_configuration(caddy, tmp_path):
    result = subprocess.run(
        [
            caddy,
            "adapt",
            "--config",
            str(ROOT / "site/Caddyfile"),
            "--adapter",
            "caddyfile",
        ],
        capture_output=True,
        text=True,
        timeout=20,
        env=dict(
            os.environ, XDG_CONFIG_HOME=str(tmp_path), XDG_DATA_HOME=str(tmp_path)
        ),
    )
    assert result.returncode == 0, result.stderr


def test_real_caddy_denies_private_paths_and_serves_public_content(
    caddy, bundle, tmp_path
):
    source, public, targets = bundle
    exporter.export_site(source, public)
    # Deliberate misdeployment canaries test the independent Caddy protection too.
    for name in PRIVATE_PATHS:
        file = public / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(CANARY)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    body = (ROOT / "site/Caddyfile").read_text().split("\nnetmonroots.com {\n", 1)[1]
    config = tmp_path / "Caddyfile"
    config.write_text(
        "{\n admin off\n auto_https off\n}\nhttp://127.0.0.1:"
        + str(port)
        + " {\n"
        + body.replace("/srv/netmonroots/public", str(public))
    )
    env = dict(os.environ, XDG_CONFIG_HOME=str(tmp_path), XDG_DATA_HOME=str(tmp_path))
    checked = subprocess.run(
        [caddy, "validate", "--config", str(config), "--adapter", "caddyfile"],
        capture_output=True,
        text=True,
        timeout=20,
        env=env,
    )
    assert checked.returncode == 0, checked.stderr

    def request(path, method="GET"):
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
        try:
            conn.request(method, path)
            response = conn.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            conn.close()

    with (tmp_path / "caddy.log").open("w") as log:
        process = subprocess.Popen(
            [caddy, "run", "--config", str(config), "--adapter", "caddyfile"],
            stdout=log,
            stderr=log,
            env=env,
        )
        try:
            end = time.monotonic() + 5
            while True:
                try:
                    assert request("/")[0] == 200
                    break
                except OSError:
                    if process.poll() is not None or time.monotonic() > end:
                        pytest.fail("Caddy did not start; inspect caddy.log")
                    time.sleep(0.02)
            for name in PRIVATE_PATHS:
                for prefix in ("/", "/site/"):
                    for path in (
                        prefix + name,
                        prefix + quote(name, safe="").replace("php", "%70hp"),
                    ):
                        for method in ("GET", "HEAD", "POST", "OPTIONS", "PROPFIND"):
                            status, data, _ = request(path, method)
                            assert status == 404, (path, method, status)
                            assert CANARY not in data
            for path in [
                "/",
                "/site/index.html",
                "/en/",
                "/styles.css",
                "/app.js",
                *targets.values(),
            ]:
                status, data, headers = request(path)
                assert status == 200, (path, status)
                assert CANARY not in data
                assert headers.get("X-Content-Type-Options") == "nosniff"
            assert request("/index.html", "POST")[0] == 405
            for path in (
                "/screenshots/",
                "/dist/",
                "/site/data/",
                "/missing",
                "/site/%2e%2e/site/download-config.php",
                "/%64ata/download-stats.json",
                *ENCODED_PRIVATE_PATHS,
            ):
                assert request(path)[0] == 404, path
        finally:
            process.terminate()
            process.wait(timeout=5)
