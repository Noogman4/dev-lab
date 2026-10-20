"""M-02 B-03/B-04/B-05: local HTTP and isolated filesystem regressions."""

import http.client
import io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import socket
from pathlib import Path
import threading
from types import SimpleNamespace
import warnings
import zipfile

import pytest

from netmon import netmon_projectm_sidecar as sidecar
from netmon.core import projectm_archive as archive_limits
from netmon.core import projectm_import_plan as plans
from netmon.core import projectm_transport as transport

SYNC_FLATPAK = sidecar._sync_projectm_flatpak_playlist_file


@pytest.fixture
def app(tmp_path, monkeypatch):
    presets = tmp_path / "Presets"
    old = presets / "Downloaded Packs" / "Pack"
    old.mkdir(parents=True)
    (old / "existing.milk").write_bytes(b"existing")
    monkeypatch.setattr(
        sidecar, "_sync_projectm_flatpak_playlist_file", lambda *_: None
    )
    return SimpleNamespace(
        radio_projectm_preset_dir=str(presets), netmon_state_dir=str(tmp_path / "state")
    )


def write_archive(tmp_path, names):
    path = tmp_path / "pack.zip"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(path, "w") as archive:
            for name in names:
                archive.writestr(name, b"preset")
    return path


def install(app, path):
    return sidecar.install_projectm_preset_archive(app, str(path), "Pack")


@pytest.fixture
def http_server(monkeypatch):
    state = SimpleNamespace(
        requests=[],
        sent=0,
        location=None,
        headers=[],
        response_payload=b"preset",
        status=200,
        redirect_status=302,
    )

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *_):
            pass

        def do_GET(self):
            state.requests.append((self.path, dict(self.headers)))
            if self.path.startswith("/chain/"):
                number = int(self.path.rsplit("/", 1)[1])
                self.send_response(302)
                self.send_header(
                    "Location", f"/chain/{number - 1}" if number else "/pack"
                )
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if self.path == "/redirect":
                self.send_response(state.redirect_status)
                if state.location is not None:
                    self.send_header("Location", state.location)
                for key, value in state.headers:
                    self.send_header(key, value)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if self.path == "/redirect-large":
                self.send_response(302)
                self.send_header("Location", "/pack")
                self.send_header("Content-Length", str(256 * 1024 * 1024 + 1))
                self.end_headers()
                self.connection.settimeout(0.5)
                try:
                    while state.sent <= 256 * 1024 * 1024:
                        self.wfile.write(b"x" * 16384)
                        state.sent += 16384
                except (OSError, ConnectionError):
                    pass
                return
            self.send_response(state.status)
            self.send_header("Content-Length", str(len(state.response_payload)))
            self.end_headers()
            self.wfile.write(state.response_payload)

    # These resource-limit tests deliberately use a local server. Destination
    # enforcement is tested separately without this fixture's resolver override.
    monkeypatch.setattr(
        transport,
        "_public_addresses",
        lambda host, port: socket.getaddrinfo(host, port, type=socket.SOCK_STREAM),
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    state.url = f"http://127.0.0.1:{server.server_port}"
    try:
        yield state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_redirect_body_is_never_read(http_server, tmp_path, monkeypatch):
    original_read = http.client.HTTPResponse.read

    def guarded_read(response, amount=None):
        assert response.status != 302, "Redirect body must be closed without reading"
        assert amount is not None and 0 < amount <= 65536
        return original_read(response, amount)

    monkeypatch.setattr(http.client.HTTPResponse, "read", guarded_read)
    monkeypatch.setattr(archive_limits.tempfile, "tempdir", str(tmp_path))
    with archive_limits.download_preset_archive(
        http_server.url + "/redirect-large"
    ) as path:
        assert Path(path).read_bytes() == b"preset"
    assert [path for path, _ in http_server.requests] == ["/redirect-large", "/pack"]
    assert http_server.sent < 256 * 1024 * 1024
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))


@pytest.mark.parametrize("count", [500, 1000])
def test_duplicate_names_have_linear_filesystem_work(app, tmp_path, monkeypatch, count):
    path = write_archive(tmp_path, ["same.milk"] * count)
    original_exists = os.path.lexists
    original_open = open
    operations = 0

    def lexists(path):
        nonlocal operations
        if str(path).endswith(".milk"):
            operations += 1
        return original_exists(path)

    def counted_open(path, mode="r", *args, **kwargs):
        nonlocal operations
        if mode == "xb":
            operations += 1
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(sidecar.os.path, "lexists", lexists)
    monkeypatch.setattr(sidecar, "open", counted_open, raising=False)
    result = install(app, path)
    assert result["imported_presets"] == count
    print(f"{count} duplicate names: {operations} filesystem probes/exclusive opens")
    assert (
        operations <= count * 4
    ), f"{count} names required {operations} filesystem checks"
    assert (
        Path(app.radio_projectm_preset_dir) / "Downloaded Packs/Pack/existing.milk"
    ).read_bytes() == b"existing"


def test_implicit_directories_are_rejected_before_creation(app, tmp_path, monkeypatch):
    names = [
        "/".join([f"branch{i}", *[f"d{depth}" for depth in range(30)], "one.milk"])
        for i in range(100)
    ]
    directories = {
        "/".join(name.split("/")[:depth]) for name in names for depth in range(1, 32)
    }
    assert len(directories) == 3100
    path = write_archive(tmp_path, names)
    original = os.mkdir
    created = []

    def mkdir(path, *args, **kwargs):
        if "Pack_2" in str(path):
            created.append(str(path))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(sidecar.os, "mkdir", mkdir)
    with pytest.raises(ValueError, match="object|director"):
        install(app, path)
    assert created == []
    root = Path(app.radio_projectm_preset_dir) / "Downloaded Packs"
    assert sorted(path.name for path in root.iterdir()) == ["Pack"]
    assert (root / "Pack/existing.milk").read_bytes() == b"existing"


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_supported_redirects_use_fresh_requests(
    http_server, tmp_path, monkeypatch, status
):
    http_server.redirect_status = status
    # A different origin (host spelling) must not inherit cookies or credentials.
    http_server.location = http_server.url.replace("127.0.0.1", "localhost") + "/pack"
    http_server.headers = [("Set-Cookie", "secret=token")]
    with archive_limits.download_preset_archive(http_server.url + "/redirect") as path:
        assert Path(path).read_bytes() == b"preset"
    for _, headers in http_server.requests:
        assert not {key.lower() for key in headers} & {
            "authorization",
            "proxy-authorization",
            "cookie",
            "referer",
        }


@pytest.mark.parametrize(
    "count,accepted", [(0, True), (4, True), (5, False), (12, False)]
)
def test_redirect_chain_limit(http_server, count, accepted):
    if accepted:
        with archive_limits.download_preset_archive(
            http_server.url + f"/chain/{count}"
        ) as path:
            assert Path(path).read_bytes() == b"preset"
    else:
        with pytest.raises(ValueError, match="Too many"):
            with archive_limits.download_preset_archive(
                http_server.url + f"/chain/{count}"
            ):
                pytest.fail("Excessive redirects must not reach the importer")
    assert len(http_server.requests) <= transport.MAX_REDIRECTS + 1


@pytest.mark.parametrize(
    "target",
    [
        "/redirect",
        "/redirect#again",
        "file:///etc/passwd",
        "ftp://127.0.0.1/file",
        "http:///missing-host",
        "http://user:secret@127.0.0.1/pack",
        "http://127.0.0.1:99999/pack",
        "http://[broken/pack",
        "http://127.0.0.1/has space",
    ],
)
def test_loops_and_invalid_targets_fail_closed(
    http_server, tmp_path, monkeypatch, target
):
    http_server.location = target
    monkeypatch.setattr(archive_limits.tempfile, "tempdir", str(tmp_path))
    with pytest.raises(ValueError):
        with archive_limits.download_preset_archive(http_server.url + "/redirect"):
            pytest.fail("Invalid target accepted")
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))
    assert len(http_server.requests) == 1


def test_missing_and_ambiguous_location_rejected(http_server):
    for location, headers in [(None, []), ("/pack", [("Location", "/other")])]:
        http_server.location = location
        http_server.headers = headers
        with pytest.raises(ValueError, match="ambiguous"):
            with archive_limits.download_preset_archive(http_server.url + "/redirect"):
                pytest.fail("Invalid redirect accepted")


def test_redirect_connection_failure_cleans_up(http_server, tmp_path, monkeypatch):
    # A bound but non-listening socket reliably rejects the redirected connection.
    import socket

    with socket.socket() as closed_listener:
        closed_listener.bind(("127.0.0.1", 0))
        http_server.location = (
            f"http://127.0.0.1:{closed_listener.getsockname()[1]}/pack"
        )
        monkeypatch.setattr(archive_limits.tempfile, "tempdir", str(tmp_path))
        with pytest.raises(OSError):
            with archive_limits.download_preset_archive(http_server.url + "/redirect"):
                pytest.fail("Connection failure accepted")
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))


def test_time_budget_checked_across_redirects_and_reads(monkeypatch):
    from email.message import Message

    clock = [0.0]
    monkeypatch.setattr(transport.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(transport, "MAX_DOWNLOAD_SECONDS", 2)

    class Response(io.BytesIO):
        status = 302
        headers = Message()
        headers["Location"] = "/next"

    def slow_open(*_args, **_kwargs):
        clock[0] += 3
        return Response()

    monkeypatch.setattr(
        transport, "_build_opener", lambda: SimpleNamespace(open=slow_open)
    )
    with pytest.raises(TimeoutError):
        with transport.open_preset_response("http://example.invalid/", timeout=30):
            pytest.fail("Exceeded deadline")
    response = transport._TimedResponse(
        SimpleNamespace(headers={}, read1=io.BytesIO(b"data").read1), deadline=2
    )
    with pytest.raises(TimeoutError):
        response.read(1)


@pytest.mark.parametrize("budget,accepted", [(9, False), (10, True)])
def test_total_object_boundary_counts_files_directories_and_flat_entries(
    app, tmp_path, monkeypatch, budget, accepted
):
    # Three roots + two directories + two files + three links (one existing preset).
    path = write_archive(tmp_path, ["a/one.milk", "b/two.milk"])
    monkeypatch.setattr(plans, "MAX_OUTPUT_OBJECTS", budget)
    if accepted:
        assert install(app, path)["imported_presets"] == 2
    else:
        with pytest.raises(ValueError, match="object budget"):
            install(app, path)
        assert not (
            Path(app.radio_projectm_preset_dir) / "Downloaded Packs/Pack_2"
        ).exists()


def test_shared_ancestors_count_once_and_directory_boundary(app, tmp_path, monkeypatch):
    path = write_archive(
        tmp_path, ["root/shared/a.milk", "root/shared/b.milk", "root/other/c.milk"]
    )
    monkeypatch.setattr(plans, "MAX_OUTPUT_DIRECTORIES", 5)
    assert install(app, path)["imported_presets"] == 3
    monkeypatch.setattr(plans, "MAX_OUTPUT_DIRECTORIES", 4)
    with pytest.raises(ValueError, match="directory object"):
        install(app, path)
    assert not (
        Path(app.radio_projectm_preset_dir) / "Downloaded Packs/Pack_3"
    ).exists()


def test_runtime_budget_rechecked_and_rolls_back(app, tmp_path, monkeypatch):
    path = write_archive(tmp_path, ["a/one.milk", "b/two.milk"])
    original_create = plans.ObjectBudget.create

    def lower_limit(budget, kind, key):
        if kind == "file":
            monkeypatch.setattr(plans, "MAX_OUTPUT_OBJECTS", 2)
        return original_create(budget, kind, key)

    monkeypatch.setattr(plans.ObjectBudget, "create", lower_limit)
    with pytest.raises(ValueError, match="object"):
        install(app, path)
    root = Path(app.radio_projectm_preset_dir) / "Downloaded Packs"
    assert sorted(item.name for item in root.iterdir()) == ["Pack"]


def test_names_reserve_directories_and_generated_suffixes(app, tmp_path):
    path = write_archive(
        tmp_path,
        ["x.milk", "x.milk", "x_2.milk", "x.milk/inside.milk", "other/one.milk"],
    )
    result = install(app, path)
    root = Path(result["target_dir"])
    assert (root / "x.milk/inside.milk").read_bytes() == b"preset"
    assert len(list(root.rglob("*.milk"))) == 6  # five files plus the .milk directory
    assert result["imported_files"] == 5


def test_unicode_aliases_and_component_lengths(app, tmp_path):
    path = write_archive(
        tmp_path,
        ["café.milk", "cafe\u0301.milk", "a" * 250 + ".milk", "a" * 250 + ".milk"],
    )
    result = install(app, path)
    root = Path(result["target_dir"])
    assert len(list(root.iterdir())) == 4
    assert all(len(os.fsencode(item.name)) <= 255 for item in root.iterdir())
    path = write_archive(tmp_path, ["a" * 251 + ".milk"])
    with pytest.raises(ValueError, match="path component"):
        install(app, path)


def test_deep_valid_pack_and_ignored_directory_fanout(app, tmp_path):
    path = write_archive(
        tmp_path,
        [
            "first/" + "/".join(f"d{i}" for i in range(30)) + "/one.milk",
            "second/two.milk",
            *[f"ignored/{i}/readme.txt" for i in range(100)],
        ],
    )
    result = install(app, path)
    assert result["imported_presets"] == 2
    assert not (Path(result["target_dir"]) / "ignored").exists()


def test_final_response_limit_after_redirect(http_server, tmp_path, monkeypatch):
    http_server.location = "/pack"
    http_server.response_payload = b"x" * 4096
    monkeypatch.setattr(archive_limits, "MAX_DOWNLOAD_BYTES", 1024)
    monkeypatch.setattr(archive_limits.tempfile, "tempdir", str(tmp_path))
    with pytest.raises(ValueError, match="compressed byte limit"):
        with archive_limits.download_preset_archive(http_server.url + "/redirect"):
            pytest.fail("Oversized final answer accepted")
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))


@pytest.mark.parametrize("status", [300, 304, 305, 400, 404, 500])
def test_unsupported_http_status_fails_without_body_reads(http_server, status):
    http_server.status = status
    with pytest.raises(ValueError, match="HTTP"):
        with archive_limits.download_preset_archive(http_server.url + "/pack"):
            pytest.fail("HTTP error accepted")


def test_directory_budget_boundary_and_flat_pack_capacity():
    def parsed(count, nested):
        return [
            (
                zipfile.ZipInfo(f"{i}.milk"),
                [f"d{i}", "one.milk"] if nested else [f"{i}.milk"],
            )
            for i in range(count)
        ]

    plan = plans.ImportPlan(parsed(2045, True), {".milk"}, {".milk"})
    assert plan.budget.directories == plans.MAX_OUTPUT_DIRECTORIES == 2048
    with pytest.raises(ValueError, match="directory object"):
        plans.ImportPlan(parsed(2046, True), {".milk"}, {".milk"})
    flat = plans.ImportPlan(
        parsed(archive_limits.MAX_MEMBERS, False), {".milk"}, {".milk"}
    )
    assert len(flat.files) == 50_000
    assert len(flat.budget.planned) == plans.MAX_OUTPUT_OBJECTS == 100_003


def test_top_level_stripping_collision_is_budgeted(app, tmp_path, monkeypatch):
    path = write_archive(tmp_path, ["one.milk", "folder/one.milk"])
    monkeypatch.setattr(plans, "MAX_OUTPUT_OBJECTS", 8)
    result = install(app, path)
    assert sorted(item.name for item in Path(result["target_dir"]).iterdir()) == [
        "one.milk",
        "one_2.milk",
    ]


def test_component_alias_keys_follow_platform_case_rules(monkeypatch):
    assert plans.path_key(("café",)) == plans.path_key(("cafe\u0301",))
    monkeypatch.setattr(plans.sys, "platform", "darwin")
    assert plans.path_key(("Texture.PNG",)) == plans.path_key(("texture.png",))


def test_directory_write_error_rolls_back(app, tmp_path, monkeypatch):
    path = write_archive(tmp_path, ["a/sub/one.milk", "b/two.milk"])
    original = os.mkdir

    def fail(path, *args, **kwargs):
        if str(path).endswith("/sub"):
            raise OSError("simulated directory write failure")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(sidecar.os, "mkdir", fail)
    with pytest.raises(OSError, match="simulated"):
        install(app, path)
    root = Path(app.radio_projectm_preset_dir) / "Downloaded Packs"
    assert sorted(item.name for item in root.iterdir()) == ["Pack"]


def test_exclusive_creation_never_overwrites_existing_file(app, tmp_path, monkeypatch):
    path = write_archive(tmp_path, ["one.milk"])
    original = open
    seen = []

    def raced_open(path, mode="r", *args, **kwargs):
        if mode == "xb":
            with original(path, "wb") as handle:
                handle.write(b"do not overwrite")
            try:
                return original(path, mode, *args, **kwargs)
            except FileExistsError:
                seen.append(Path(path).read_bytes())
                raise
        return original(path, mode, *args, **kwargs)

    monkeypatch.setattr(sidecar, "open", raced_open, raising=False)
    with pytest.raises(FileExistsError):
        install(app, path)
    assert seen == [b"do not overwrite"]
    root = Path(app.radio_projectm_preset_dir) / "Downloaded Packs"
    assert sorted(item.name for item in root.iterdir()) == ["Pack"]


def test_global_suffix_cursor_prevents_truncation_family_restarts():
    names = ["a" * 245 + f"{i:05d}.milk" for i in range(500)]
    entries = [(zipfile.ZipInfo(name), [name]) for name in names for _ in range(2)]
    plan = plans.ImportPlan(entries, {".milk"}, {".milk"})
    keys = {plans.path_key(item.parts) for item in plan.files}
    assert len(keys) == len(entries)
    assert all(len(os.fsencode(item.parts[-1])) <= 255 for item in plan.files)
    assert plan.next_suffix <= len(entries) + 2


def test_elapsed_budget_accumulates_across_redirects(monkeypatch):
    from email.message import Message

    clock = [0.0]
    calls = []
    monkeypatch.setattr(transport.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(transport, "MAX_DOWNLOAD_SECONDS", 2)

    class Response(io.BytesIO):
        status = 302

        def __init__(self):
            super().__init__()
            self.headers = Message()
            self.headers["Location"] = f"/next/{len(calls)}"

    def open_response(_request, *, timeout):
        calls.append(timeout)
        clock[0] += 0.75
        return Response()

    monkeypatch.setattr(
        transport, "_build_opener", lambda: SimpleNamespace(open=open_response)
    )
    with pytest.raises(TimeoutError):
        with transport.open_preset_response("http://example.invalid/", timeout=30):
            pytest.fail("Accumulated redirect deadline accepted")
    assert calls == [2, 1.25, 0.5]


def test_elapsed_budget_checked_after_partial_body_read(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(transport.time, "monotonic", lambda: clock[0])

    def read1(_size):
        clock[0] += 0.75
        return b"partial"

    response = transport._TimedResponse(
        SimpleNamespace(headers={}, read1=read1), deadline=1
    )
    assert response.read(64) == b"partial"
    with pytest.raises(TimeoutError):
        response.read(64)


def test_flat_scan_write_failure_rolls_back_auxiliary_objects(
    app, tmp_path, monkeypatch
):
    path = write_archive(tmp_path, ["one.milk"])

    def fail_symlink(*_args, **_kwargs):
        raise OSError("simulated unavailable symlinks")

    def fail_copy(_source, destination, *_args, **_kwargs):
        destination.write(b"partial")
        raise OSError("simulated cache write failure")

    monkeypatch.setattr(plans.os, "symlink", fail_symlink)
    monkeypatch.setattr(plans, "copy_limited", fail_copy)
    with pytest.raises(OSError, match="cache write"):
        install(app, path)
    root = Path(app.radio_projectm_preset_dir)
    assert not (root / sidecar.PROJECTM_FLAT_SCAN_SUBDIR).exists()
    assert sorted(item.name for item in (root / "Downloaded Packs").iterdir()) == [
        "Pack"
    ]
    assert (root / "Downloaded Packs/Pack/existing.milk").read_bytes() == b"existing"


@pytest.mark.parametrize("limit,accepted", [(8, True), (7, False)])
def test_flat_copy_fallback_has_its_own_byte_budget(
    app, tmp_path, monkeypatch, limit, accepted
):
    path = write_archive(tmp_path, ["one.milk"])

    def no_symlinks(*_args, **_kwargs):
        raise OSError("simulated unsupported symlinks")

    monkeypatch.setattr(plans.os, "symlink", no_symlinks)
    monkeypatch.setattr(plans, "MAX_FILE_BYTES", limit)
    if accepted:
        assert install(app, path)["imported_presets"] == 1
        flat = Path(app.radio_projectm_preset_dir) / sidecar.PROJECTM_FLAT_SCAN_SUBDIR
        assert len(list(flat.iterdir())) == 2
    else:
        with pytest.raises(ValueError, match="byte limit"):
            install(app, path)
        assert not (
            Path(app.radio_projectm_preset_dir) / sidecar.PROJECTM_FLAT_SCAN_SUBDIR
        ).exists()
        assert not (
            Path(app.radio_projectm_preset_dir) / "Downloaded Packs/Pack_2"
        ).exists()


def test_flatpak_playlist_does_not_repeat_unbudgeted_scan(app, tmp_path, monkeypatch):
    path = write_archive(tmp_path, ["one.milk"])
    calls = []
    original = sidecar._sync_projectm_flat_scan_dir

    def counted_scan(*args, **kwargs):
        calls.append(kwargs.get("import_plan"))
        return original(*args, **kwargs)

    config = tmp_path / "flatpak.conf"
    monkeypatch.setattr(sidecar, "_sync_projectm_flatpak_playlist_file", SYNC_FLATPAK)
    monkeypatch.setattr(sidecar, "_sync_projectm_flat_scan_dir", counted_scan)
    monkeypatch.setattr(
        sidecar,
        "get_projectm_sidecar_status",
        lambda **_: SimpleNamespace(backend_label="Flatpak"),
    )
    monkeypatch.setattr(
        sidecar, "_projectm_flatpak_config_files", lambda: [str(config)]
    )
    assert install(app, path)["imported_presets"] == 1
    assert len(calls) == 1 and calls[0] is not None
    assert sidecar.PROJECTM_FLAT_SCAN_SUBDIR in config.read_text()


def test_legacy_migration_rolls_back_on_later_import_error(app, tmp_path, monkeypatch):
    legacy = Path(app.netmon_state_dir) / "projectm_presets"
    legacy.mkdir(parents=True)
    (legacy / "legacy.milk").write_bytes(b"legacy")
    path = write_archive(tmp_path, ["one.milk"])

    def fail_scan(*_args, **_kwargs):
        raise OSError("simulated scan failure")

    monkeypatch.setattr(sidecar, "_sync_projectm_flat_scan_dir", fail_scan)
    with pytest.raises(OSError, match="scan failure"):
        install(app, path)
    root = Path(app.radio_projectm_preset_dir)
    assert not (root / "legacy.milk").exists()
    assert (legacy / "legacy.milk").read_bytes() == b"legacy"
    assert sorted(item.name for item in (root / "Downloaded Packs").iterdir()) == [
        "Pack"
    ]
