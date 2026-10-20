"""Synthetic website/process tests; no production services or browser launches."""

import errno
import importlib.util
import json
import os
import shlex
import shutil
import socket
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "site_server", ROOT / "scripts/netmon_site_server.py"
)
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


@pytest.fixture(autouse=True)
def restore_umask():
    old = os.umask(0o077)
    yield
    os.umask(old)


@pytest.fixture
def website(tmp_path, monkeypatch):
    root = tmp_path / "synthetic-site"
    (root / "scripts").mkdir(parents=True)
    (root / "site").mkdir()
    (root / "site/index.html").write_text("SYNTHETIC-NETMON-WEBSITE")
    shutil.copyfile(ROOT / "Makefile", root / "Makefile")
    for name in ("netmon_site_server.py", "open_netmon_site.sh", "stop_netmon_site.sh"):
        shutil.copyfile(ROOT / "scripts" / name, root / "scripts" / name)
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    # Keep wrapper and direct helper calls on the identical interpreter argv.
    # A symlink alone would change sys.executable and fail exact identity checks.
    python = bindir / "python3"
    python.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} "$@"\n')
    python.chmod(0o700)
    browser = bindir / "xdg-open"
    browser.write_text('#!/bin/sh\nprintf "%s" "$1" > "$BROWSER_CAPTURE"\n')
    browser.chmod(0o700)
    monkeypatch.setattr(helper, "ROOT", root)
    monkeypatch.setattr(helper, "__file__", str(root / "scripts/netmon_site_server.py"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    # The website is synthetic and all connections are to its loopback listener.
    monkeypatch.setenv("NETMON_TEST_ISOLATED", "1")
    monkeypatch.setenv("BROWSER_CAPTURE", str(tmp_path / "browser-url"))
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    monkeypatch.setenv("NETMON_SITE_PORT", str(port))
    yield root, runtime, port
    run(root, "stop")


def run(root, action):
    return subprocess.run(
        [sys.executable, str(root / "scripts/netmon_site_server.py"), action],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def state_dir():
    with helper.runtime_directory() as (_, path):
        return Path(path)


def test_original_pid_attack_terminates_only_synthetic_child(tmp_path):
    original = subprocess.check_output(
        [
            "git",
            "show",
            "d4e40ad6262fe73a58ea0e930d41b12df874f66d:scripts/stop_netmon_site.sh",
        ],
        cwd=ROOT,
        text=True,
    )
    # Preserve the vulnerable production logic, relocate its global file for isolation.
    pidfile = tmp_path / "injected.pid"
    script = tmp_path / "old-stop.sh"
    script.write_text(
        original.replace("/tmp/netmon_site_http_server.pid", str(pidfile))
    )
    with subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"]
    ) as victim:
        try:
            pidfile.write_text(str(victim.pid))
            result = subprocess.run(
                ["bash", str(script)], capture_output=True, timeout=5, check=False
            )
            assert result.returncode == 0
            assert victim.wait(timeout=3) == -15
        finally:
            if victim.poll() is None:
                victim.terminate()
                victim.wait(timeout=3)


def test_full_lifecycle_and_browser_wrapper(website):
    root, _, port = website
    result = subprocess.run(
        ["bash", str(root / "scripts/open_netmon_site.sh")],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    expected = f"http://127.0.0.1:{port}/site/index.html"
    assert expected in result.stdout
    assert Path(os.environ["BROWSER_CAPTURE"]).read_text() == expected
    with socket.create_connection(("127.0.0.1", port), timeout=3) as client:
        client.sendall(b"GET /site/index.html HTTP/1.0\r\nHost: localhost\r\n\r\n")
        response = b""
        while block := client.recv(4096):
            response += block
    assert b"200 OK" in response
    assert b"SYNTHETIC-NETMON-WEBSITE" in response
    directory = state_dir()
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for name in ("manager.lock", "server.json", "server.log"):
        assert stat.S_IMODE((directory / name).stat().st_mode) == 0o600
    assert run(root, "start").returncode == 0
    result = subprocess.run(
        ["bash", str(root / "scripts/stop_netmon_site.sh")],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", port))
    assert run(root, "stop").returncode == 0
    assert run(root, "start").returncode == 0  # safely starts again


def test_pid_files_cannot_select_a_target(website):
    root, _, _ = website
    with subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"]
    ) as victim:
        try:
            directory = state_dir()
            (directory / "server.pid").write_text(str(victim.pid))
            (directory / "netmon_site_http_server.pid").write_text(str(victim.pid))
            assert run(root, "stop").returncode == 0
            assert victim.poll() is None
        finally:
            victim.terminate()
            victim.wait(timeout=3)
    for path in (ROOT / "scripts").glob("*netmon_site*"):
        assert "/tmp/netmon_site_http_server.pid" not in path.read_text()


@pytest.mark.parametrize("mode", [0o777, 0o755, 0o710])
def test_insecure_runtime_parent_rejected(website, mode):
    root, runtime, _ = website
    runtime.chmod(mode)
    try:
        assert run(root, "start").returncode != 0
        assert list(runtime.iterdir()) == []
    finally:
        runtime.chmod(0o700)


@pytest.mark.parametrize("mode", [0o777, 0o755, 0o710])
def test_insecure_private_directory_rejected(website, mode):
    root, _, _ = website
    directory = state_dir()
    directory.chmod(mode)
    try:
        assert run(root, "start").returncode != 0
        assert list(directory.iterdir()) == []
    finally:
        directory.chmod(0o700)


@pytest.mark.parametrize("component", ["parent", "private", "intermediate"])
def test_runtime_symlinks_rejected(website, tmp_path, monkeypatch, component):
    root, runtime, _ = website
    if component == "private":
        directory = state_dir()
        directory.rmdir()
        target = tmp_path / "target"
        target.mkdir(mode=0o700)
        directory.symlink_to(target)
    else:
        link = tmp_path / "runtime-link"
        link.symlink_to(runtime)
        target = runtime
        monkeypatch.setenv(
            "XDG_RUNTIME_DIR",
            str(link / "child") if component == "intermediate" else str(link),
        )
    assert run(root, "start").returncode != 0
    assert list(target.iterdir()) == []


@pytest.mark.parametrize("name", ["manager.lock", "server.json", "server.log"])
@pytest.mark.parametrize(
    "kind", ["symlink", "hardlink", "fifo", "directory", "mode", "foreign"]
)
def test_unsafe_entries_fail_closed(website, tmp_path, name, kind):
    root, _, _ = website
    target = tmp_path / "victim"
    target.write_text("KEEP")
    entry = state_dir() / name
    if kind == "symlink":
        entry.symlink_to(target)
    elif kind == "hardlink":
        os.link(target, entry)
    elif kind == "fifo":
        os.mkfifo(entry, 0o600)
    elif kind == "directory":
        entry.mkdir()
    else:
        entry.write_text("KEEP")
        entry.chmod(0o666 if kind == "mode" else 0o600)
        if kind == "foreign":
            try:
                os.chown(entry, 65534, 65534)
            except OSError as error:
                if error.errno not in (errno.EINVAL, errno.EPERM):
                    raise
                pytest.skip("Second UID unavailable in this container")
    before = entry.lstat()
    result = run(root, "start")
    assert result.returncode != 0, result.stdout
    assert entry.lstat().st_ino == before.st_ino
    assert target.read_text() == "KEEP"


@pytest.mark.parametrize("value", ["0", "-1", "65536", "-999", "1;kill", "١٢", "", "a"])
def test_invalid_port_is_rejected(website, monkeypatch, value):
    root, _, _ = website
    monkeypatch.setenv("NETMON_SITE_PORT", value)
    result = run(root, "start")
    assert result.returncode != 0
    assert "http://" not in result.stdout
    assert not (state_dir() / "server.log").exists()


def test_occupied_port_does_not_register_foreign_listener(website):
    root, _, port = website
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", port))
        listener.listen()
        assert run(root, "start").returncode != 0
        assert run(root, "stop").returncode == 0
        assert listener.fileno() >= 0


def test_concurrent_starts_and_stops(website):
    root, _, _ = website
    for action in ("start", "stop"):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(
                pool.map(lambda _, current=action: run(root, current), range(4))
            )
        assert all(r.returncode == 0 for r in results), [r.stderr for r in results]


def test_different_port_is_rejected_without_stopping_server(website, monkeypatch):
    root, _, port = website
    assert run(root, "start").returncode == 0
    monkeypatch.setenv("NETMON_SITE_PORT", str(port + 1 if port < 65535 else port - 1))
    assert run(root, "start").returncode != 0
    assert run(root, "stop").returncode == 0


def test_missing_runtime_fails_without_fallback(website, monkeypatch):
    root, runtime, _ = website
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime / "missing"))
    assert run(root, "start").returncode != 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("pid", 0),
        ("pid", -1),
        ("pid", True),
        ("pid", "123"),
        ("start", "bad"),
        ("port", 0),
        ("port", True),
        ("ready_fd", 1),
        ("root", "/elsewhere"),
    ],
)
def test_invalid_state_rejected(website, field, value):
    root, _, port = website
    record = {
        "pid": 99,
        "start": "123",
        "boot": helper.boot_id(),
        "port": port,
        "root": str(root),
        "ready_fd": 7,
    }
    record[field] = value
    (state_dir() / "server.json").write_text(json.dumps(record))
    assert run(root, "stop").returncode != 0


def test_registered_unrelated_process_survives(website):
    root, _, port = website
    with subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], cwd=root
    ) as victim:
        try:
            record = {
                "pid": victim.pid,
                "start": helper.start_time(victim.pid),
                "boot": helper.boot_id(),
                "port": port,
                "root": str(root),
                "ready_fd": 7,
            }
            (state_dir() / "server.json").write_text(json.dumps(record))
            assert run(root, "stop").returncode != 0
            assert victim.poll() is None
        finally:
            victim.terminate()
            victim.wait(timeout=3)


@pytest.mark.parametrize("field", ["start", "boot"])
def test_stale_identity_never_signals_process(website, field):
    root, _, _ = website
    assert run(root, "start").returncode == 0
    path = state_dir() / "server.json"
    original = path.read_text()
    record = json.loads(original)
    record[field] = "0"
    path.write_text(json.dumps(record))
    try:
        result = run(root, "stop")
        assert result.returncode == (1 if field == "start" else 0)
        with socket.create_connection(("127.0.0.1", record["port"]), timeout=3):
            pass
    finally:
        path.write_text(original)


def test_pidfd_used_for_signal_and_handle_closed(website, monkeypatch):
    root, _, _ = website
    assert run(root, "start").returncode == 0
    send_signal = helper.signal.pidfd_send_signal
    handles = []

    def capture(fd, signum):
        assert "pidfd" in os.readlink(f"/proc/self/fd/{fd}")
        handles.append((fd, signum))
        return send_signal(fd, signum)

    def reject_numeric_kill(*args):
        pytest.fail("Numeric PID kill must never be used for registered processes")

    monkeypatch.setattr(helper.signal, "pidfd_send_signal", capture)
    monkeypatch.setattr(helper.os, "kill", reject_numeric_kill)
    helper.main("stop")
    assert [sig for _, sig in handles] == [0, helper.signal.SIGTERM]
    for fd, _ in handles:
        with pytest.raises(OSError):
            os.fstat(fd)


@pytest.mark.parametrize("field", ["port", "ready_fd"])
def test_command_identity_tampering_rejected(website, field):
    root, _, _ = website
    assert run(root, "start").returncode == 0
    path = state_dir() / "server.json"
    original = path.read_text()
    record = json.loads(original)
    record[field] = record[field] + 1 if record[field] < 65535 else 1
    path.write_text(json.dumps(record))
    try:
        assert run(root, "stop").returncode != 0
    finally:
        path.write_text(original)
    assert run(root, "start").returncode == 0


@pytest.mark.parametrize(
    "data", [b"x" * 4097, b"null", b"[]", b"{}", b"\xff", b"not-json"]
)
def test_bad_state_does_not_signal(website, data):
    root, _, _ = website
    path = state_dir() / "server.json"
    path.write_bytes(data)
    assert run(root, "stop").returncode != 0
    assert path.read_bytes() == data


def test_dead_process_state_is_cleared(website):
    root, _, port = website
    with subprocess.Popen([sys.executable, "-c", "pass"]) as child:
        pid = child.pid
        child.wait(timeout=3)
    record = {
        "pid": pid,
        "start": "0",
        "boot": helper.boot_id(),
        "port": port,
        "root": str(root),
        "ready_fd": 7,
    }
    path = state_dir() / "server.json"
    path.write_text(json.dumps(record))
    assert run(root, "stop").returncode == 0
    assert not path.exists()


def test_publication_failure_reaps_own_child(website, monkeypatch):
    _root, _, _ = website
    processes = []
    original = helper.subprocess.Popen

    def capture(*args, **kwargs):
        process = original(*args, **kwargs)
        processes.append(process)
        return process

    def fail(*args):
        raise OSError("synthetic state publication failure")

    monkeypatch.setattr(helper.subprocess, "Popen", capture)
    monkeypatch.setattr(helper, "publish_state", fail)
    with pytest.raises(OSError, match="synthetic"):
        helper.main("start")
    assert len(processes) == 1
    assert processes[0].poll() is not None
    assert not (state_dir() / "server.json").exists()


def test_atomic_state_publication_never_overwrites(website):
    state_dir()
    with helper.runtime_directory() as (directory, path):
        target = Path(path) / "server.json"
        target.write_text("KEEP")
        with pytest.raises(FileExistsError):
            helper.publish_state(directory, {"synthetic": True})
        assert target.read_text() == "KEEP"
        assert not list(Path(path).glob("state-*"))


def test_state_fsync_failure_leaves_no_state(website, monkeypatch):
    def fail(fd):
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(helper.os, "fsync", fail)
    with helper.runtime_directory() as (directory, path):
        with pytest.raises(OSError, match="synthetic"):
            helper.publish_state(directory, {"synthetic": True})
        assert list(Path(path).iterdir()) == []


@pytest.mark.parametrize("directory", [False, True])
def test_foreign_owner_validation(directory):
    info = type(
        "Info",
        (),
        {
            "st_mode": (stat.S_IFDIR | 0o700) if directory else (stat.S_IFREG | 0o600),
            "st_uid": os.geteuid() + 1,
            "st_nlink": 1,
        },
    )()
    with pytest.raises(PermissionError):
        helper.check_private(info, directory=directory)


def test_wrong_working_directory_rejected(website):
    root, _, port = website
    read_fd, write_fd = os.pipe()
    try:
        with subprocess.Popen(
            helper.server_command(port, write_fd),
            cwd=root.parent,
            pass_fds=(write_fd,),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) as process:
            os.close(write_fd)
            try:
                assert helper.select.select([read_fd], [], [], 5)[0]
                assert os.read(read_fd, 8) == b"OK"
                record = {
                    "pid": process.pid,
                    "start": helper.start_time(process.pid),
                    "boot": helper.boot_id(),
                    "port": port,
                    "root": str(root),
                    "ready_fd": write_fd,
                }
                with pytest.raises(PermissionError):
                    helper.process_handle(record)
                assert process.poll() is None
            finally:
                process.terminate()
                process.wait(timeout=3)
    finally:
        os.close(read_fd)


def test_target_exit_between_validation_and_signal_is_safe(website, monkeypatch):
    root, _, _ = website
    assert run(root, "start").returncode == 0
    original = helper.signal.pidfd_send_signal
    victims = []

    def race(fd, sig):
        if sig == helper.signal.SIGTERM:
            original(fd, sig)
            assert helper.select.select([fd], [], [], 3)[0]
            victims.append(
                subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"])
            )
            return original(fd, sig)  # ESRCH: the original handle stays dead.
        return original(fd, sig)

    monkeypatch.setattr(helper.signal, "pidfd_send_signal", race)
    try:
        helper.main("stop")
        assert len(victims) == 1
        assert victims[0].poll() is None
    finally:
        for victim in victims:
            victim.terminate()
            victim.wait(timeout=3)


def test_private_tmp_fallback_lifecycle(website, monkeypatch):
    root, _, _ = website
    info = Path("/tmp").stat()
    if info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o1777:
        pytest.skip(
            f"Isolated /tmp is UID {info.st_uid}, mode {stat.S_IMODE(info.st_mode):04o}; "
            "real fallback requires root-owned mode 1777"
        )
    monkeypatch.delenv("XDG_RUNTIME_DIR")
    directory = state_dir()
    try:
        assert directory.parent == Path("/tmp")
        assert directory.stat().st_uid == os.geteuid()
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        assert run(root, "start").returncode == 0
        assert run(root, "stop").returncode == 0
    finally:
        run(root, "stop")
        shutil.rmtree(directory)


def test_pidfd_unavailable_fails_before_launch(website, monkeypatch):
    launched = []

    def unavailable(pid):
        raise OSError("pidfd unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(helper.os, "pidfd_open", unavailable)
        patch.setattr(helper.subprocess, "Popen", lambda *a, **kw: launched.append(a))
        with pytest.raises(OSError, match="pidfd unavailable"):
            helper.main("start")
    assert not launched


@pytest.fixture(params=["managed", "make"])
def public_preview(website, request):
    root, _, port = website
    if request.param == "managed":
        result = run(root, "start")
        assert result.returncode == 0, result.stderr
        yield root, port
    else:
        process = subprocess.Popen(
            ["make", "--no-print-directory", "site-serve"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            output = b""
            deadline = time.monotonic() + 5
            while f"http://127.0.0.1:{port}/site/index.html".encode() not in output:
                remaining = deadline - time.monotonic()
                assert remaining > 0, output
                assert helper.select.select([process.stdout], [], [], remaining)[0]
                block = os.read(process.stdout.fileno(), 4096)
                assert block, output
                output += block
            yield root, port
        finally:
            # Only our newly created isolated process group, never a stored PID.
            os.killpg(process.pid, helper.signal.SIGTERM)
            process.wait(timeout=5)
            process.stdout.close()


def http_request(port, path, method="GET"):
    with socket.create_connection(("127.0.0.1", port), timeout=3) as client:
        client.sendall(f"{method} {path} HTTP/1.0\r\nHost: localhost\r\n\r\n".encode())
        response = b""
        while block := client.recv(4096):
            response += block
    headers, body = response.split(b"\r\n\r\n", 1)
    status = int(headers.split(b" ", 2)[1])
    return status, body


def test_public_preview_assets_and_loopback_binding(public_preview):
    root, port = public_preview
    assets = {
        "index.html": "SYNTHETIC-NETMON-WEBSITE",
        "styles.css": "body {}",
        "app.js": "console.log('preview');",
        "latest-version.json": '{"version":"test"}',
        "robots.txt": "User-agent: *",
        "sitemap.xml": "<urlset/>",
        "LICENSE.txt": "PUBLIC-LICENSE",
        "THIRD_PARTY_NOTICES.md": "PUBLIC-NOTICES",
        "en/index.html": "ENGLISH-PREVIEW",
        "screenshots/example.png": "SYNTHETIC-IMAGE",
    }
    for name, content in assets.items():
        asset = root / "site" / name
        asset.parent.mkdir(parents=True, exist_ok=True)
        asset.write_text(content)
        for prefix in ("/", "/site/"):
            assert http_request(port, prefix + name + "?v=1") == (200, content.encode())
    assert http_request(port, "/")[0] == 200
    assert http_request(port, "/site/")[0] == 200
    assert http_request(port, "/en/") == (200, b"ENGLISH-PREVIEW")
    assert http_request(port, "/site/index.html", "HEAD") == (200, b"")
    listeners = [
        line.split()[1]
        for line in Path("/proc/net/tcp").read_text().splitlines()[1:]
        if line.split()[3] == "0A" and int(line.split()[1].split(":")[1], 16) == port
    ]
    assert listeners == [f"0100007F:{port:04X}"]


def test_public_preview_denies_private_files_and_traversal(public_preview):
    root, port = public_preview
    secret = "PRIVATE-PREVIEW-CANARY"
    private = [
        ".git/config",
        ".env",
        "private.html",
        "tests/private.html",
        "dist/private.html",
        "site/.env",
        "site/.git/config",
        "site/download-config.php",
        "site/download.php",
        "site/download-stats.php",
        "site/download-lib.php",
        "site/.htaccess",
        "site/htaccess",
        "site/Caddyfile",
        "site/data/download-stats.json",
        "site/data/private.html",
        "site/config.json",
        "site/README.md",
    ]
    for name in private:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(secret)
    for name in private:
        for method in ("GET", "HEAD"):
            assert http_request(port, "/" + name, method)[0] == 404, name
            if name.startswith("site/"):
                assert http_request(port, "/" + name[5:], method)[0] == 404, name
    paths = [
        "/scripts/",
        "/tests/",
        "/.git/",
        "/Makefile",
        "/site/screenshots/",
        "/site/../private.html",
        "/site/%2e%2e/private.html",
        "/site/%2E%2E%2fprivate.html",
        "/%2eenv",
        "/site/%2egit/config",
        "/site/..%5cprivate.html",
        "/site/%00.html",
        "/site/%ff.html",
        "/site//index.html",
        "/site/data/../index.html",
    ]
    (root / "site/screenshots").mkdir(exist_ok=True)
    for path in paths:
        status, body = http_request(port, path)
        assert status == 404, path
        assert secret.encode() not in body


def test_public_preview_denies_symlinks_and_special_files(public_preview):
    root, port = public_preview
    (root / "private.html").write_text("PRIVATE-PREVIEW-CANARY")
    (root / "site/linked.html").symlink_to(root / "private.html")
    (root / "site/linked-dir").symlink_to(root)
    (root / "site/internal.html").symlink_to(root / "site/index.html")
    os.mkfifo(root / "site/pipe.html", 0o600)
    (root / "site/directory.html").mkdir()
    for path in (
        "linked.html",
        "linked-dir/private.html",
        "internal.html",
        "pipe.html",
        "directory.html",
    ):
        assert http_request(port, "/site/" + path)[0] == 404, path
    # A symlink replacing the document root is also rejected.
    (root / "site").rename(root / "original-site")
    (root / "site").symlink_to(root / "original-site")
    assert http_request(port, "/site/index.html")[0] == 404
