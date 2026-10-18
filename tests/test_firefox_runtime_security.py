"""Isolated L-03 tests: generated signing keys, fake HTTPS, no runtime execution."""

from email.message import Message
import hashlib
import io
import http.server
import http.client
import threading
from pathlib import Path
import shutil
import subprocess
import tarfile
from types import SimpleNamespace

import pytest

from netmon.core import firefox_runtime as runtime
from netmon.app import App, _extract_regular_tar_archive

URL = "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=de"
FINAL = "https://download-installer.cdn.mozilla.net/pub/firefox/releases/158.0/linux-x86_64/de/firefox-158.0.tar.xz"
ENTRY = "linux-x86_64/de/firefox-158.0.tar.xz"


class Response:
    def __init__(self, body=b"", status=200, headers=()):
        self.body = io.BytesIO(body)
        self.status = status
        self.headers = Message()
        for name, value in headers:
            self.headers[name] = value
        self.read_sizes = []
        self.closed = False

    def read1(self, size):
        assert 0 < size <= 64 * 1024
        assert self.status == 200, "Redirect body must never be read"
        self.read_sizes.append(size)
        return self.body.read(size)

    def close(self):
        self.closed = True


def wire(monkeypatch, responses):
    connections = []
    pending = iter(responses)

    class Connection:
        sock = None

        def __init__(self, host, timeout):
            self.host = host
            self.timeout = timeout
            self.closed = False
            connections.append(self)

        def request(self, method, path, headers):
            self.path = path
            assert method == "GET"
            assert set(headers) == {"User-Agent", "Accept-Encoding"}

        def getresponse(self):
            response = next(pending)
            if isinstance(response, Exception):
                raise response
            return response

        def close(self):
            self.closed = True

    monkeypatch.setattr(runtime.http.client, "HTTPSConnection", Connection)
    return connections


@pytest.mark.parametrize("length", [None, "1", "70000"])
def test_download_real_bytes_limit_cleanup(tmp_path, monkeypatch, length):
    headers = [] if length is None else [("Content-Length", length)]
    response = Response(b"a" * 70000, headers=headers)
    connections = wire(monkeypatch, [response])
    output = tmp_path / "archive"
    with pytest.raises(ValueError, match="gross"):
        runtime.download(URL, output, 65536)
    assert not output.exists()
    assert response.closed and all(c.closed for c in connections)


def test_redirect_bodies_not_read_and_multihop_success(tmp_path, monkeypatch):
    redirect = Response(b"a" * 100000, 302, [("Location", FINAL)])
    second = Response(b"ignored", 307, [("Location", "/final")])
    final = Response(b"safe", headers=[("Content-Length", "4")])
    connections = wire(monkeypatch, [redirect, second, final])
    output = tmp_path / "archive"
    assert runtime.download(URL, output, 5).endswith("/final")
    assert output.read_bytes() == b"safe"
    assert not redirect.read_sizes and not second.read_sizes
    assert all(c.closed for c in connections)


@pytest.mark.parametrize(
    "destination",
    [
        "http://archive.mozilla.org/a",
        "https://evil.invalid/a",
        "file:///tmp/a",
        "https://user@archive.mozilla.org/a",
        "https://archive.mozilla.org:444/a",
        "https://archive.mozilla.org/a#fragment",
        "https://archive.mozilla.org/a\n",
    ],
)
def test_untrusted_redirects_rejected(tmp_path, monkeypatch, destination):
    response = Response(b"do not read", 302, [("Location", destination)])
    connections = wire(monkeypatch, [response])
    with pytest.raises(ValueError):
        runtime.download(URL, tmp_path / "out", 100)
    assert len(connections) == 1 and response.closed


def test_redirect_loop(tmp_path, monkeypatch):
    response = Response(status=302, headers=[("Location", URL)])
    wire(monkeypatch, [response])
    with pytest.raises(ValueError, match="Schleife"):
        runtime.download(URL, tmp_path / "out", 10)


def test_redirect_limit(tmp_path, monkeypatch):
    responses = [
        Response(status=302, headers=[("Location", f"/next{i}")]) for i in range(6)
    ]
    connections = wire(monkeypatch, responses)
    with pytest.raises(ValueError, match="Redirect"):
        runtime.download(URL, tmp_path / "out", 10)
    assert len(connections) == 6 and all(r.closed for r in responses)


@pytest.mark.parametrize("failure", [OSError("connection"), TimeoutError("timeout")])
def test_network_failure_cleanup(tmp_path, monkeypatch, failure):
    connections = wire(monkeypatch, [failure])
    with pytest.raises(OSError):
        runtime.download(URL, tmp_path / "out", 10)
    assert connections[0].closed and not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "headers",
    [
        [("Content-Length", "6")],
        [("Content-Length", "bad")],
        [("Content-Length", "2"), ("Content-Length", "2")],
        [("Content-Length", "2"), ("Transfer-Encoding", "chunked")],
        [("Content-Encoding", "gzip")],
    ],
)
def test_http_framing_failures(tmp_path, monkeypatch, headers):
    wire(monkeypatch, [Response(b"no", headers=headers)])
    with pytest.raises(ValueError):
        runtime.download(URL, tmp_path / "out", 100)
    assert not list(tmp_path.iterdir())


def test_total_time_limit_before_connection(tmp_path, monkeypatch):
    connections = wire(monkeypatch, [])
    with pytest.raises(TimeoutError):
        runtime.download(URL, tmp_path / "out", 100, deadline=0)
    assert not connections


def test_exclusive_download_does_not_remove_existing_file(tmp_path, monkeypatch):
    output = tmp_path / "existing"
    output.write_bytes(b"keep")
    wire(monkeypatch, [Response(b"new")])
    with pytest.raises(FileExistsError):
        runtime.download(URL, output, 100)
    assert output.read_bytes() == b"keep"


@pytest.fixture(scope="module")
def signing_keys(tmp_path_factory):
    if not shutil.which("gpg") or not shutil.which("gpgv"):
        pytest.skip("GnuPG required for real synthetic signatures")
    homes = []
    keys = []
    try:
        for index in range(2):
            home = tmp_path_factory.mktemp(f"l03-signing-{index}")
            home.chmod(0o700)
            homes.append(home)
            prefix = [
                "gpg",
                "--no-options",
                "--homedir",
                str(home),
                "--batch",
                "--pinentry-mode",
                "loopback",
                "--passphrase",
                "",
            ]
            subprocess.run(
                prefix
                + [
                    "--quick-generate-key",
                    f"Synthetic L03 {index} <l03-{index}@example.invalid>",
                    "rsa2048",
                    "sign",
                    "1d",
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )
            listing = subprocess.check_output(
                prefix + ["--with-colons", "--list-keys"], text=True
            )
            fingerprint = next(
                line.split(":")[9]
                for line in listing.splitlines()
                if line.startswith("fpr:")
            )
            key = subprocess.check_output(prefix + ["--export", fingerprint])
            key_path = home / "public.gpg"
            key_path.write_bytes(key)
            keys.append(
                (prefix, fingerprint, key_path, hashlib.sha256(key).hexdigest())
            )
        yield keys
    finally:
        for home in homes:
            subprocess.run(
                ["gpgconf", "--homedir", str(home), "--kill", "gpg-agent"],
                capture_output=True,
                timeout=10,
            )


@pytest.fixture
def signed_package(tmp_path, monkeypatch, signing_keys):
    sentinel = tmp_path / "NEVER-EXECUTE"
    payload = f'#!/bin/sh\ntouch "{sentinel}"\n'.encode()
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:xz") as packed:
        info = tarfile.TarInfo("firefox/firefox")
        info.size = len(payload)
        info.mode = 0o777
        packed.addfile(info, io.BytesIO(payload))
    content = stream.getvalue()
    manifest = f"{hashlib.sha256(content).hexdigest()}  {ENTRY}\n".encode()
    prefix, fingerprint, key_path, key_hash = signing_keys[0]
    manifest_path = tmp_path / "sign-input"
    manifest_path.write_bytes(manifest)

    def sign(data, index=0):
        manifest_path.write_bytes(data)
        signature_path = tmp_path / "sign-output"
        subprocess.run(
            signing_keys[index][0]
            + [
                "--yes",
                "--digest-algo",
                "SHA256",
                "--detach-sign",
                "--output",
                str(signature_path),
                str(manifest_path),
            ],
            check=True,
            capture_output=True,
            timeout=20,
        )
        return signature_path.read_bytes()

    package = {
        "archive": content,
        "SHA256SUMS": manifest,
        "SHA256SUMS.asc": sign(manifest),
        "sign": sign,
    }
    monkeypatch.setattr(runtime, "KEYRING", key_path)
    monkeypatch.setattr(runtime, "KEYRING_SHA256", key_hash)
    monkeypatch.setattr(runtime, "PRIMARY_FINGERPRINT", fingerprint)
    monkeypatch.setattr(runtime, "SIGNER_FINGERPRINT", fingerprint)
    requested = []

    def download(url, destination, limit, **_kwargs):
        requested.append(url)
        value = package["archive"] if url == URL else package[url.rsplit("/", 1)[-1]]
        if isinstance(value, Exception):
            raise value
        if len(value) > limit:
            raise ValueError("zu gross")
        Path(destination).write_bytes(value)
        return FINAL if url == URL else url

    monkeypatch.setattr(runtime, "download", download)
    package.update(sentinel=sentinel, payload=payload, requested=requested)
    return package


def import_app(target):
    app = SimpleNamespace(_secure_browser_firefox_target_dir=lambda: str(target))
    return App._import_secure_browser_firefox_archive_from_url(app, URL)


def test_real_signature_success_actual_app_import_never_executes(
    tmp_path, signed_package
):
    target = tmp_path / "runtime" / "firefox"
    assert import_app(target) == str(target)
    assert (target / "firefox").read_bytes() == signed_package["payload"]
    assert (target / "firefox").stat().st_mode & 0o777 == 0o755
    assert not signed_package["sentinel"].exists()
    assert list(target.parent.iterdir()) == [target]
    assert len(signed_package["requested"]) == 3


@pytest.mark.parametrize(
    "attack",
    [
        "archive",
        "manifest",
        "signature",
        "foreign",
        "missing",
        "duplicate",
        "wrong-signer",
        "wrong-primary",
        "wrong-anchor",
        "no-proof",
        "no-manifest",
    ],
)
def test_authentication_failures_never_extract(
    tmp_path, monkeypatch, signed_package, attack
):
    if attack == "archive":
        signed_package["archive"] += b"tampered after metadata signing"
    elif attack == "manifest":
        signed_package["SHA256SUMS"] += b"tampered"
    elif attack == "signature":
        signed_package["SHA256SUMS.asc"] = b"corrupt"
    elif attack == "foreign":
        signed_package["SHA256SUMS.asc"] = signed_package["sign"](
            signed_package["SHA256SUMS"], 1
        )
    elif attack in {"missing", "duplicate"}:
        data = (
            signed_package["SHA256SUMS"].replace(ENTRY.encode(), b"wrong-file")
            if attack == "missing"
            else signed_package["SHA256SUMS"] * 2
        )
        signed_package["SHA256SUMS"] = data
        signed_package["SHA256SUMS.asc"] = signed_package["sign"](data)
    elif attack == "no-manifest":
        signed_package["SHA256SUMS"] = OSError("missing manifest")
    elif attack == "no-proof":
        signed_package["SHA256SUMS.asc"] = OSError("missing proof")
    else:
        monkeypatch.setattr(
            runtime,
            {
                "wrong-signer": "SIGNER_FINGERPRINT",
                "wrong-primary": "PRIMARY_FINGERPRINT",
                "wrong-anchor": "KEYRING_SHA256",
            }[attack],
            "0" * 64,
        )
    target = tmp_path / "runtime" / "firefox"

    def forbidden(*_args):
        pytest.fail("Unauthenticated archive reached extraction")

    with pytest.raises((ValueError, OSError)):
        runtime.install(URL, target, forbidden)
    assert not target.exists() and not list(target.parent.iterdir())
    assert not signed_package["sentinel"].exists()


@pytest.mark.parametrize("existing", ["directory", "empty", "file", "symlink"])
def test_existing_target_never_changed(tmp_path, signed_package, existing):
    parent = tmp_path / "runtime"
    parent.mkdir()
    target = parent / "firefox"
    if existing in {"directory", "empty"}:
        target.mkdir()
        if existing == "directory":
            (target / "keep").write_bytes(b"old")
    elif existing == "file":
        target.write_bytes(b"old")
    else:
        target.symlink_to(tmp_path / "nonexistent")
    with pytest.raises(FileExistsError):
        import_app(target)
    assert not signed_package["requested"]
    assert target.is_symlink() or target.exists()
    if existing == "directory":
        assert (target / "keep").read_bytes() == b"old"


def test_target_created_during_import_never_overwritten(
    tmp_path, monkeypatch, signed_package
):
    target = tmp_path / "runtime" / "firefox"
    original = runtime._publish_no_replace

    def race(source, destination):
        target.mkdir()
        (target / "keep").write_bytes(b"other-install")
        return original(source, destination)

    monkeypatch.setattr(runtime, "_publish_no_replace", race)
    with pytest.raises(FileExistsError):
        import_app(target)
    assert (target / "keep").read_bytes() == b"other-install"
    assert list(target.parent.iterdir()) == [target]


@pytest.mark.parametrize("phase", ["extract", "rename", "limit"])
def test_install_failure_cleans_staging(tmp_path, monkeypatch, signed_package, phase):
    target = tmp_path / "runtime" / "firefox"

    def failing_extract(archive, directory):
        (directory / "partial").write_bytes(b"partial")
        raise OSError("synthetic extraction write failure")

    if phase == "rename":
        monkeypatch.setattr(
            runtime,
            "_publish_no_replace",
            lambda *_: (_ for _ in ()).throw(OSError("rename")),
        )
    extractor = failing_extract if phase == "extract" else _extract_regular_tar_archive
    if phase == "limit":

        def extractor(archive, directory):
            return _extract_regular_tar_archive(archive, directory, max_total_size=1)

    with pytest.raises((OSError, ValueError)):
        runtime.install(URL, target, extractor)
    assert not target.exists() and not list(target.parent.iterdir())


def test_missing_gpgv_fails_before_download(tmp_path, monkeypatch, signed_package):
    monkeypatch.setattr(runtime.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="gpgv"):
        import_app(tmp_path / "runtime" / "firefox")
    assert not signed_package["requested"]


def test_key_resource_is_packaged_and_public():
    key_path = Path(runtime.__file__).with_name("mozilla-release.gpg")
    assert hashlib.sha256(key_path.read_bytes()).hexdigest() == runtime.KEYRING_SHA256
    configuration = Path("pyproject.toml").read_text()
    assert '"netmon.core" = ["mozilla-release.gpg"]' in configuration


def test_real_local_http_redirect_body_is_not_drained(tmp_path, monkeypatch):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/archive":
                self.send_response(200)
                self.send_header("Content-Length", "4")
                self.end_headers()
                self.wfile.write(b"safe")
            else:
                self.send_response(302)
                self.send_header("Location", "https://archive.mozilla.org/archive")
                self.send_header("Content-Length", str(1024 * 1024 * 1024))
                self.end_headers()
                # A huge declared body whose sender never provides EOF must not
                # delay the next request. This is a genuine HTTPResponse.
                try:
                    self.wfile.write(b"x" * 128 * 1024)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        def log_message(self, *_args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    real_http = http.client.HTTPConnection

    def local_connection(host, timeout):
        assert host in runtime.ALLOWED_HOSTS
        return real_http("127.0.0.1", server.server_port, timeout=timeout)

    monkeypatch.setattr(runtime.http.client, "HTTPSConnection", local_connection)
    try:
        output = tmp_path / "out"
        assert runtime.download(URL, output, 4).endswith("/archive")
        assert output.read_bytes() == b"safe"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("operation", ["write", "flush"])
def test_download_io_failure_removes_partial(tmp_path, monkeypatch, operation):
    wire(monkeypatch, [Response(b"abc")])
    original = open

    class Output:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.handle.close()

        def write(self, data):
            if operation == "write":
                return 0
            return self.handle.write(data)

        def flush(self):
            raise OSError("synthetic flush failure")

    def failing_open(path, mode):
        return Output(original(path, mode))

    monkeypatch.setattr(runtime, "open", failing_open, raising=False)
    with pytest.raises(OSError):
        runtime.download(URL, tmp_path / "out", 10)
    assert not list(tmp_path.iterdir())


def test_partial_writes_are_completed(tmp_path, monkeypatch):
    wire(monkeypatch, [Response(b"abcdef")])
    original = open

    class Output:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.handle.close()

        def write(self, data):
            return self.handle.write(data[:1])

        def flush(self):
            self.handle.flush()

    monkeypatch.setattr(
        runtime, "open", lambda path, mode: Output(original(path, mode)), raising=False
    )
    output = tmp_path / "out"
    runtime.download(URL, output, 10)
    assert output.read_bytes() == b"abcdef"


@pytest.mark.parametrize("version", ["157.0", "158.0esr", "158.0b1"])
def test_release_selection_rejects_unsupported_or_old(
    tmp_path, monkeypatch, signed_package, version
):
    original = runtime.download

    def old(url, destination, limit, **kwargs):
        result = original(url, destination, limit, **kwargs)
        return result.replace("158.0", version)

    monkeypatch.setattr(runtime, "download", old)
    with pytest.raises(ValueError, match="stabiles Release"):
        import_app(tmp_path / "runtime" / "firefox")
    assert len(signed_package["requested"]) == 1


def test_parent_symlink_rejected(tmp_path, signed_package):
    actual = tmp_path / "actual"
    actual.mkdir()
    link = tmp_path / "link"
    link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlinks"):
        import_app(link / "firefox")
    assert not signed_package["requested"] and not list(actual.iterdir())


def test_tamper_after_successful_metadata_verification(
    tmp_path, monkeypatch, signed_package
):
    verify = runtime._verify_manifest

    def tamper(directory, gpgv):
        verify(directory, gpgv)
        with (directory / "runtime.tar.xz").open("ab") as archive:
            archive.write(b"tampered after authenticating metadata")

    monkeypatch.setattr(runtime, "_verify_manifest", tamper)
    with pytest.raises(ValueError, match="SHA256"):
        import_app(tmp_path / "runtime" / "firefox")
    assert not list((tmp_path / "runtime").iterdir())


@pytest.mark.parametrize(
    "name,limit",
    [
        ("archive", "MAX_ARCHIVE_BYTES"),
        ("SHA256SUMS", "MAX_MANIFEST_BYTES"),
        ("SHA256SUMS.asc", "MAX_SIGNATURE_BYTES"),
    ],
)
def test_each_download_has_its_own_budget(
    tmp_path, monkeypatch, signed_package, name, limit
):
    monkeypatch.setattr(runtime, limit, len(signed_package[name]) - 1)
    with pytest.raises(ValueError, match="gross"):
        import_app(tmp_path / "runtime" / "firefox")
    assert not list((tmp_path / "runtime").iterdir())


def test_verifier_timeout_cleans_private_staging(tmp_path, monkeypatch, signed_package):
    def fail(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("gpgv", 20)

    # Signing fixture already completed: only verification is fault-injected.
    monkeypatch.setattr(runtime.subprocess, "run", fail)
    with pytest.raises(subprocess.TimeoutExpired):
        import_app(tmp_path / "runtime" / "firefox")
    assert not list((tmp_path / "runtime").iterdir())


@pytest.mark.parametrize("kind", ["traversal", "link", "special", "members"])
def test_authenticated_unsafe_archives_still_rejected(tmp_path, signed_package, kind):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:xz") as archive:
        info = tarfile.TarInfo(
            "../escaped" if kind == "traversal" else "firefox/firefox"
        )
        if kind == "link":
            info.type = tarfile.SYMTYPE
            info.linkname = "/bin/sh"
        elif kind == "special":
            info.type = tarfile.FIFOTYPE
        archive.addfile(info)
    content = stream.getvalue()
    manifest = f"{hashlib.sha256(content).hexdigest()}  {ENTRY}\n".encode()
    signed_package.update(archive=content, SHA256SUMS=manifest)
    signed_package["SHA256SUMS.asc"] = signed_package["sign"](manifest)

    def extract(archive, directory):
        _extract_regular_tar_archive(
            archive, directory, max_members=0 if kind == "members" else 100_000
        )

    with pytest.raises(ValueError):
        runtime.install(URL, tmp_path / "runtime" / "firefox", extract)
    assert not (tmp_path / "escaped").exists()
    assert not list((tmp_path / "runtime").iterdir())


def test_component_installer_uses_authenticated_app_path(tmp_path, signed_package):
    app = SimpleNamespace(
        _import_secure_browser_firefox_archive_from_url=lambda url: import_app(
            tmp_path / "runtime" / "firefox"
        )
    )
    result = App._install_selected_file_features(app, ["secure_browser_firefox_source"])
    assert result == [
        ("secure_browser_firefox_source", str(tmp_path / "runtime" / "firefox"))
    ]
    assert not signed_package["sentinel"].exists()


def test_new_target_parent_is_private(tmp_path, signed_package):
    target = tmp_path / "runtime" / "firefox"
    import_app(target)
    assert target.parent.stat().st_mode & 0o077 == 0


def test_signed_manifest_allows_other_platform_paths_with_spaces(
    tmp_path, signed_package
):
    # Mozilla publishes all platforms in one manifest; DMG names contain spaces.
    manifest = (
        signed_package["SHA256SUMS"]
        + ("0" * 64 + "  mac/de/Firefox 158.0.dmg\n").encode()
    )
    signed_package["SHA256SUMS"] = manifest
    signed_package["SHA256SUMS.asc"] = signed_package["sign"](manifest)
    target = tmp_path / "runtime" / "firefox"
    import_app(target)
    assert (target / "firefox").read_bytes() == signed_package["payload"]
