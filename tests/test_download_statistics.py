"""M-01: real PHP, isolated state, injected I/O failures and concurrent workers."""

import base64
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]


def b64(value):
    if isinstance(value, str):
        value = value.encode()
    return base64.b64encode(value).decode("ascii")


@pytest.fixture(scope="session")
def php():
    executable = os.environ.get("NETMON_TEST_PHP") or shutil.which("php")
    if not executable:
        pytest.skip("PHP CLI required; optionally set NETMON_TEST_PHP")
    subprocess.run([executable, "-n", "-v"], capture_output=True, check=True)
    return executable


@pytest.fixture
def app(tmp_path):
    app = tmp_path / "app"
    data = app / "data"
    data.mkdir(parents=True, mode=0o700)
    for filename in ("download.php", "download-lib.php", "download-stats.php"):
        shutil.copyfile(ROOT / "site" / filename, app / filename)
    for filename in ("download_driver.php", "download_faults.php"):
        shutil.copyfile(ROOT / "tests" / "php" / filename, app / filename)
    subject = (app / "download-lib.php").read_text()
    (app / "fault-library.php").write_text(
        subject.replace(
            "declare(strict_types=1);",
            'declare(strict_types=1);\nnamespace NetmonTest;\nrequire __DIR__ . "/download_faults.php";',
            1,
        )
    )
    seed = {
        "updated_at": "2026-10-01T12:00:00+00:00",
        "total_downloads": 7,
        "files": {
            "artifact": {
                "label": "Test artifact",
                "target": "/artifact.bin",
                "count": 7,
                "last_download_at": "2026-10-01T12:00:00+00:00",
                "sources": {"seed": 7},
                "days": {"2026-10-01": 7},
            }
        },
        "sources": {"seed": 7},
        "days": {"2026-10-01": 7},
        "recent_events": [{"timestamp": "2026-10-01T12:00:00+00:00", "source": "seed"}],
    }
    path = data / "stats.json"
    path.write_text(json.dumps(seed, indent=2))
    path.chmod(0o600)
    (app / "artifact.bin").write_bytes(b"valid download bytes\n")
    config = {
        "stats_path": str(path),
        "max_recent_events": 200,
        "stats_token": "isolated-test-token",
        "downloads": {
            "artifact": {"label": "Test artifact", "target": "/artifact.bin"},
            "missing": {"label": "Missing artifact", "target": "/missing.bin"},
        },
    }
    (app / "download-config.php").write_text(
        f'<?php return json_decode(base64_decode("{b64(json.dumps(config))}"), true);'
    )
    return app, path, seed


def driver_arguments(php, app, **payload):
    directory, path, _ = app
    payload = {"path": str(path), **payload}
    if payload.get("fault"):
        payload.update(library="fault-library.php", namespace="NetmonTest\\")
    return [php, "-n", str(directory / "download_driver.php"), b64(json.dumps(payload))]


def invoke(php, app, **payload):
    result = subprocess.run(
        driver_arguments(php, app, **payload),
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == "", result.stderr
    return json.loads(result.stdout)


def assert_no_temporary_files(app):
    directory, _, _ = app
    assert not list(directory.parent.rglob(".netmon-json-*"))


@pytest.mark.parametrize(
    "field", ["source", "referrer", "lang", "accept", "remote_addr"]
)
@pytest.mark.parametrize(
    "invalid", [b"\xff", b"a\xc3(b", b"\xed\xa0\x80", b"\xf0(\x8c("]
)
def test_invalid_utf8_never_damages_statistics(php, app, field, invalid):
    result = invoke(php, app, **{field: b64(invalid)})
    stats = json.loads(app[1].read_bytes())

    assert result["saved"] is True
    assert stats["total_downloads"] == 8
    assert stats["files"]["artifact"]["count"] == 8
    assert stats["sources"]["seed"] == 7
    assert stats["recent_events"][1] == app[2]["recent_events"][0]
    event = stats["recent_events"][0]
    if field in ("source", "referrer", "lang"):
        assert "\ufffd" in event[field]
    assert set(stats) == set(app[2])
    assert_no_temporary_files(app)


@pytest.mark.parametrize(
    "value",
    [b"x" * 10000, b"\xff" * 10000, ("€" * 3000).encode(), ("😀" * 2000).encode()],
)
def test_telemetry_is_bounded_in_utf8_bytes_after_normalization(php, app, value):
    result = invoke(
        php,
        app,
        **{
            field: b64(value)
            for field in ("source", "referrer", "lang", "accept", "remote_addr")
        },
    )
    assert result["saved"] is True
    stats = json.loads(app[1].read_bytes())
    event = stats["recent_events"][0]
    assert len(event["source"].encode()) <= 256
    assert len(event["referrer"].encode()) <= 2048
    assert len(event["lang"].encode()) <= 8
    assert len(event["ip_hash"]) == 16
    assert all(len(source.encode()) <= 256 for source in stats["sources"])
    assert stats["sources"][event["source"]] == 1


@pytest.mark.parametrize("action", ["serialize-error", "invalid-state"])
def test_serialization_failure_preserves_exact_previous_file(php, app, action):
    original = app[1].read_bytes()
    inode = app[1].stat().st_ino
    result = invoke(php, app, action=action)

    assert result["saved"] is False
    assert app[1].read_bytes() == original
    assert app[1].stat().st_ino == inode
    assert_no_temporary_files(app)


@pytest.mark.parametrize(
    "fault",
    [
        "write-fail",
        "phantom-write",
        "zero-write",
        "partial-fail",
        "flush-fail",
        "sync-fail",
        "close-fail",
        "rename-fail",
        "temp-fail",
        "temp-fallback",
        "lock-fail",
        "temp-symlink",
        "temp-dangling-symlink",
    ],
)
def test_io_failure_preserves_state_and_cleans_temporary_files(php, app, fault):
    if fault == "sync-fail":
        available = subprocess.check_output(
            [php, "-n", "-r", 'echo function_exists("fsync") ? "1" : "0";']
        )
        if available != b"1":
            pytest.skip("fsync not available before PHP 8.1")
    original = app[1].read_bytes()
    inode = app[1].stat().st_ino
    victim = app[0].parent / "outside.json"
    if fault != "temp-dangling-symlink":
        victim.write_bytes(b"unmodified outside data")
    result = invoke(php, app, fault=fault, victim=str(victim))

    assert result["saved"] is False
    assert app[1].read_bytes() == original
    assert app[1].stat().st_ino == inode
    if victim.exists():
        assert victim.read_bytes() == b"unmodified outside data"
    else:
        assert fault == "temp-dangling-symlink"
    assert_no_temporary_files(app)
    lock = Path(str(app[1]) + ".lock")
    assert stat.S_IMODE(lock.stat().st_mode) == 0o600


def test_partial_writes_are_retried_until_all_bytes_are_saved(php, app):
    result = invoke(php, app, fault="partial-success", source=b64("complete"))

    assert result["saved"] is True
    stats = json.loads(app[1].read_bytes())
    assert stats["total_downloads"] == 8
    assert stats["recent_events"][0]["source"] == "complete"
    assert_no_temporary_files(app)


def test_unlocked_readers_only_observe_complete_json_during_slow_writes(php, app):
    process = subprocess.Popen(
        driver_arguments(php, app, fault="slow-partial-success"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    observations = 0
    try:
        deadline = time.monotonic() + 10
        while process.poll() is None:
            stats = json.loads(app[1].read_bytes())
            assert stats["total_downloads"] in (7, 8)
            observations += 1
            assert time.monotonic() < deadline, "writer stalled"
            time.sleep(0.001)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stdout + stderr
        assert stderr == ""
        assert json.loads(stdout)["saved"] is True
        assert observations > 1
        assert json.loads(app[1].read_bytes())["total_downloads"] == 8
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
    assert_no_temporary_files(app)


def test_parallel_processes_do_not_lose_updates_after_rename(php, app):
    ready = app[0].parent / "start"
    workers, iterations = 8, 20
    processes = [
        subprocess.Popen(
            driver_arguments(
                php,
                app,
                start=str(ready),
                iterations=iterations,
                source=b64(f"worker-{index}"),
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(workers)
    ]
    try:
        ready.touch()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            outputs = list(
                pool.map(lambda process: process.communicate(timeout=20), processes)
            )
        for process, (stdout, stderr) in zip(processes, outputs):
            assert process.returncode == 0, stdout + stderr
            assert stderr == ""
            assert json.loads(stdout)["saved"] is True
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()
    stats = json.loads(app[1].read_bytes())
    assert stats["total_downloads"] == 7 + workers * iterations
    assert stats["files"]["artifact"]["count"] == 7 + workers * iterations
    for index in range(workers):
        assert stats["sources"][f"worker-{index}"] == iterations
        assert stats["files"]["artifact"]["sources"][f"worker-{index}"] == iterations
    assert sum(stats["days"].values()) == 7 + workers * iterations
    assert len(stats["recent_events"]) == 1 + workers * iterations
    assert_no_temporary_files(app)


def test_data_inode_changes_but_lock_inode_stays_stable(php, app):
    initial_data = app[1].stat().st_ino
    assert invoke(php, app)["saved"] is True
    first_data = app[1].stat().st_ino
    lock = Path(str(app[1]) + ".lock")
    lock_inode = lock.stat().st_ino
    assert invoke(php, app)["saved"] is True

    assert initial_data != first_data != app[1].stat().st_ino
    assert lock.stat().st_ino == lock_inode


@pytest.mark.parametrize("mode", [0o600, 0o640, 0o400])
def test_existing_restrictive_permissions_are_never_broadened(php, app, mode):
    app[1].chmod(mode)
    assert invoke(php, app)["saved"] is True
    assert stat.S_IMODE(app[1].stat().st_mode) == mode & 0o600
    assert stat.S_IMODE(Path(str(app[1]) + ".lock").stat().st_mode) == 0o600


@pytest.mark.parametrize(
    "unsafe",
    [
        "data-symlink",
        "lock-symlink",
        "data-hardlink",
        "directory-symlink",
        "writable-directory",
    ],
)
def test_unsafe_storage_paths_are_refused(php, app, unsafe):
    original = app[1].read_bytes()
    victim = app[0].parent / "outside.json"
    victim.write_bytes(b"outside sentinel")
    if unsafe == "data-symlink":
        app[1].unlink()
        app[1].symlink_to(victim)
    elif unsafe == "lock-symlink":
        Path(str(app[1]) + ".lock").symlink_to(victim)
    elif unsafe == "data-hardlink":
        victim.unlink()
        os.link(app[1], victim)
    elif unsafe == "directory-symlink":
        actual = app[0].parent / "moved-data"
        app[1].parent.rename(actual)
        app[1].parent.symlink_to(actual, target_is_directory=True)
    else:
        app[1].parent.chmod(0o777)
    result = invoke(php, app)

    assert result["saved"] is False
    assert victim.read_bytes() == (
        original if unsafe == "data-hardlink" else b"outside sentinel"
    )
    assert app[1].read_bytes() == (
        b"outside sentinel" if unsafe == "data-symlink" else original
    )
    assert_no_temporary_files(app)


@pytest.mark.parametrize("raw", [b"", b"not JSON", b'{"truncated":', b'{"bad":"\xff"}'])
def test_existing_corrupt_state_is_preserved_instead_of_reset(php, app, raw):
    app[1].write_bytes(raw)
    result = invoke(php, app)

    assert result["saved"] is False
    assert app[1].read_bytes() == raw
    assert_no_temporary_files(app)


def test_new_store_is_initialized_privately_and_recent_event_limit_is_retained(
    php, app
):
    app[1].unlink()
    app[1].parent.rmdir()
    result = invoke(php, app, iterations=30, max_events=20, source=b64("new"))

    assert result["saved"] is True
    stats = json.loads(app[1].read_bytes())
    assert stats["total_downloads"] == 30
    assert len(stats["recent_events"]) == 20
    assert stat.S_IMODE(app[1].parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(app[1].stat().st_mode) == 0o600


@pytest.fixture
def http_server(php, app):
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    process = subprocess.Popen(
        [php, "-n", "-S", f"127.0.0.1:{port}", "-t", str(app[0])],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 5
        while True:
            if process.poll() is not None:
                pytest.fail(process.stderr.read().decode())
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                if time.monotonic() >= deadline:
                    pytest.fail("isolated PHP HTTP server did not start")
                time.sleep(0.01)
        yield port
    finally:
        process.terminate()
        process.communicate(timeout=5)


def http_request(port, path, headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_actual_download_redirects_and_stats_page_still_work(http_server, app):
    status, headers, _ = http_request(
        http_server,
        "/download.php?id=artifact&src=%FFdownload&lang=de",
        {"Referer": "https://example.test/\xff"},
    )
    assert status == 302
    assert headers["Location"] == "/artifact.bin?dl=1"
    assert "no-store" in headers["Cache-Control"]
    status, _, body = http_request(http_server, headers["Location"])
    assert status == 200
    assert body == b"valid download bytes\n"
    stats = json.loads(app[1].read_bytes())
    assert stats["total_downloads"] == 8
    assert stats["recent_events"][0]["source"] == "\ufffddownload"
    assert stats["recent_events"][0]["referrer"] == "https://example.test/\ufffd"
    assert http_request(http_server, "/download-stats.php")[0] == 403
    status, _, body = http_request(
        http_server, "/download-stats.php?token=isolated-test-token"
    )
    assert status == 200
    assert b"Test artifact" in body
    assert b"8</span>" in body


@pytest.mark.parametrize(
    "query", ["id=unknown", "id=missing", "id[]=artifact", "id=" + "x" * 200]
)
def test_invalid_or_unavailable_download_does_not_change_stats(http_server, app, query):
    original = app[1].read_bytes()
    assert http_request(http_server, "/download.php?" + query)[0] == 404
    assert app[1].read_bytes() == original


def test_array_telemetry_is_safe_and_language_header_fallback_is_preserved(
    http_server, app
):
    status, _, _ = http_request(
        http_server,
        "/download.php?id=artifact&src[]=bad&lang[]=bad",
        {"Accept-Language": "en-US,en;q=0.9"},
    )
    assert status == 302
    event = json.loads(app[1].read_bytes())["recent_events"][0]
    assert event["source"] == ""
    assert event["lang"] == "en"


def test_failed_statistics_write_does_not_break_download(http_server, app):
    original = app[1].read_bytes()
    Path(str(app[1]) + ".lock").touch(mode=0o600)
    app[1].parent.chmod(0o500)
    try:
        if os.access(app[1].parent, os.W_OK):
            pytest.skip("current user can bypass directory write permissions")
        assert http_request(http_server, "/download.php?id=artifact&src=test")[0] == 302
        assert app[1].read_bytes() == original
    finally:
        app[1].parent.chmod(0o700)
    assert_no_temporary_files(app)
