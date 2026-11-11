"""Private-network HTTP/PulseAudio integration probe for run_isolated_suite.py.

A trusted coordinator first creates a private network/user namespace. The test
services and real mpv then run in separate first-level Bubblewrap sandboxes.
The playback command and filesystem grants are not relaxed. No host audio,
external network, package install, persistent mount or system service is used.
"""

import array
import ast
import binascii
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import math
import os
from pathlib import Path
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
import traceback
import wave
import zlib
import zipfile

sys.pycache_prefix = "/nonexistent"
os.environ["PYTHONPYCACHEPREFIX"] = "/nonexistent"

ENV = {
    "PATH": "/usr/bin:/bin",
    "LC_ALL": "C.UTF-8",
    "HOME": "/nonexistent",
    "PYTHONPYCACHEPREFIX": "/nonexistent",
}
TEST_HOST = "93.184.216.34"  # Assigned only to the verified private loopback.
TEST_WRONG_HOST = "93.184.216.35"


def _preset_zip():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(
            zipfile.ZipInfo("Scene/one.milk", (2020, 1, 1, 0, 0, 0)),
            b"[preset00]\nfRating=1.0\n",
        )
    return output.getvalue()


def _logo_png():
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\0\xff\0\0\xff\0\xff\0\0"))
        + chunk(b"IEND", b"")
    )


PW_CONFIG = """
context.properties = { core.daemon = true core.name = pipewire-0 support.dbus = false }
context.spa-libs = {
    audio.convert.* = audioconvert/libspa-audioconvert
    support.* = support/libspa-support
}
context.modules = [
    { name = libpipewire-module-protocol-native }
    { name = libpipewire-module-metadata }
    { name = libpipewire-module-spa-node-factory }
    { name = libpipewire-module-client-node }
    { name = libpipewire-module-client-device }
    { name = libpipewire-module-access }
    { name = libpipewire-module-adapter }
    { name = libpipewire-module-link-factory }
    { name = libpipewire-module-session-manager }
]
context.objects = [
    { factory = spa-node-factory args = {
        factory.name = support.node.driver node.name = Dummy-Driver
        node.group = pipewire.dummy priority.driver = 20000
    } }
]
"""
PULSE_CONFIG = """
context.properties = { support.dbus = false }
context.spa-libs = {
    audio.convert.* = audioconvert/libspa-audioconvert
    support.* = support/libspa-support
}
context.modules = [
    { name = libpipewire-module-protocol-native }
    { name = libpipewire-module-client-node }
    { name = libpipewire-module-adapter }
    { name = libpipewire-module-metadata }
    { name = libpipewire-module-protocol-pulse }
]
pulse.properties = {
    server.address = [ "unix:/work/runtime/pulse/native" ]
    pulse.allow-module-loading = false
}
pulse.cmd = [
    { cmd = "load-module" args = "module-null-sink sink_name=netmon_test" }
]
"""


def _write_json(path, value):
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _wait(predicate, timeout=8):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for controlled test state")


def _tone(seconds=20):
    target = io.BytesIO()
    samples = array.array(
        "h",
        (
            int(8000 * math.sin(2 * math.pi * 440 * n / 8000))
            for n in range(8000 * seconds)
        ),
    )
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(target, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(samples.tobytes())
    return target.getvalue()


def _drop_namespace_caps():
    """Discard only this coordinator's temporary namespace capabilities."""
    import ctypes

    class Header(ctypes.Structure):
        _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]

    class Caps(ctypes.Structure):
        _fields_ = [
            ("effective", ctypes.c_uint32),
            ("permitted", ctypes.c_uint32),
            ("inheritable", ctypes.c_uint32),
        ]

    header = Header(0x20080522, 0)
    values = (Caps * 2)()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.capset(ctypes.byref(header), ctypes.byref(values)) != 0:
        raise OSError(ctypes.get_errno(), "Unable to discard test namespace caps")
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(("CapEff:", "CapPrm:", "CapInh:", "CapAmb:")):
            assert int(line.split()[1], 16) == 0


def _services():
    work = Path("/work")
    assert not Path("/dev/snd").exists()
    assert not Path("/run/user").exists()
    assert os.readlink("/proc/self/ns/net") == os.environ["TEST_NET_NS"]
    environment = {
        **ENV,
        "HOME": "/work/home",
        "XDG_RUNTIME_DIR": "/work/runtime",
        "XDG_CONFIG_HOME": "/work/config",
        "PIPEWIRE_CONFIG_DIR": "/work/config",
        "PIPEWIRE_REMOTE": "pipewire-0",
        "WIREPLUMBER_CONFIG_DIR": "/work/config/wireplumber",
        "PULSE_SERVER": "unix:/work/runtime/pulse/native",
        "PULSE_CLIENTCONFIG": "/work/config/pulse-client.conf",
    }
    # GUI scenarios include real recording/cancellation and handovers; EOF of
    # the old 20-s fixture must not turn a live-handover test into a stopped one.
    payload = _tone(90 if os.environ.get("NETMON_PROBE_HTTP_ONLY") == "1" else 20)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= 1024:
                self.send_error(413)
                return
            (work / "catalog-post.json").write_bytes(self.rfile.read(length))
            self.do_GET()

        def do_GET(self):
            with (work / "http.log").open("a") as log:
                log.write(self.path + "\n")
            if self.path.startswith("/preset-"):
                if self.path in {
                    "/preset-redirect",
                    "/preset-private",
                    "/preset-loop",
                    "/preset-downgrade",
                }:
                    self.send_response(302)
                    target = "/preset-good"
                    if self.path == "/preset-private":
                        target = f"http://127.0.0.1:{private_server.server_port}/must-not-contact"
                    elif self.path == "/preset-loop":
                        target = "/preset-loop"
                    elif self.path == "/preset-downgrade":
                        target = f"http://{TEST_HOST}:{server.server_port}/preset-good"
                    self.send_header("Location", target)
                    self.end_headers()
                    return
                body = _preset_zip()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                length = (
                    256 * 1024 * 1024 + 1
                    if self.path == "/preset-large"
                    else len(body) + (10 if self.path == "/preset-cut" else 0)
                )
                self.send_header("Content-Length", str(length))
                if self.path == "/preset-duplicate":
                    self.send_header("Content-Length", str(length))
                if self.path == "/preset-gzip":
                    self.send_header("Content-Encoding", "gzip")
                self.end_headers()
                if self.path == "/preset-hang":
                    time.sleep(3)
                    return
                try:
                    self.wfile.write(body)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.path == "/recording-playlist":
                body = f"#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXTINF:10,\nhttp://127.0.0.1:{private_server.server_port}/must-not-contact\n#EXT-X-ENDLIST\n".encode()
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path.startswith("/logo-"):
                if self.path in {"/logo-private", "/logo-loop"}:
                    self.send_response(302)
                    self.send_header(
                        "Location",
                        (
                            "http://127.0.0.1/must-not-contact"
                            if self.path == "/logo-private"
                            else "/logo-loop"
                        ),
                    )
                    self.end_headers()
                    return
                body = b"invalid image" if self.path == "/logo-bad" else _logo_png()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header(
                    "Content-Length",
                    str(
                        1048577
                        if self.path == "/logo-large"
                        else len(body) + (10 if self.path == "/logo-cut" else 0)
                    ),
                )
                self.end_headers()
                if self.path == "/logo-hang":
                    time.sleep(3)
                    return
                try:
                    self.wfile.write(body)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.path.startswith("/probe-"):
                with (work / "probe-requests.jsonl").open("a") as log:
                    log.write(
                        json.dumps(
                            {
                                "path": self.path,
                                "range": self.headers.get("Range"),
                                "icy": self.headers.get("Icy-MetaData"),
                            }
                        )
                        + "\n"
                    )
                if self.path in {"/probe-icy", "/probe-malformed"}:
                    self.wfile.write(
                        b"ICY 200 OK\r\n\r\n"
                        if self.path == "/probe-icy"
                        else b"ICY nonsense\r\n\r\n"
                    )
                    self.wfile.flush()
                    self.close_connection = True
                    return
                status = {
                    "/probe-forbidden": 403,
                    "/probe-range": 416,
                    "/probe-missing": 404,
                }.get(self.path, 200)
                self.send_response(status)
                self.send_header("Content-Length", "999999999")
                self.end_headers()
                # No body: the probe must finish on headers, before this delay.
                time.sleep(3)
                return
            if self.path.startswith("/catalog-"):
                body = json.dumps(
                    [
                        {
                            "name": "Native Catalog",
                            "url": f"http://{TEST_HOST}:{server.server_port}/tone.wav",
                            "tags": "Test, Native",
                            "bitrate": 128,
                        }
                    ]
                ).encode()
                content_type = "application/json"
                if self.path == "/catalog-xml":
                    body = b"<directory><entry><server_name>Native XML</server_name><listen_url>https://example.com/live</listen_url><genre>Jazz</genre></entry></directory>"
                    content_type = "application/xml"
                elif self.path == "/catalog-bad":
                    body = b"[{"
                elif self.path == "/catalog-dtd":
                    body = b"<!DOCTYPE directory [<!ENTITY x SYSTEM 'file:///etc/passwd'>]><directory><entry><server_name>&x;</server_name></entry></directory>"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                length = len(body) + (10 if self.path == "/catalog-cut" else 0)
                if self.path == "/catalog-large":
                    length = 16 * 1024 * 1024 + 1
                self.send_header("Content-Length", str(length))
                self.end_headers()
                if self.path == "/catalog-hang":
                    time.sleep(3)
                    return
                try:
                    self.wfile.write(body)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.path == "/fail":
                self.send_error(503)
                return
            if self.path == "/hang":
                time.sleep(12)
                return
            if self.path.startswith("/icy-") or (
                self.path == "/tone.wav" and self.headers.get("Icy-MetaData") == "1"
            ):
                with (work / "icy-requests.jsonl").open("a") as log:
                    log.write(
                        json.dumps(
                            {"path": self.path, "icy": self.headers.get("Icy-MetaData")}
                        )
                        + "\n"
                    )
                metadata = b"StreamTitle='Private Test Artist - Test Track';"
                metadata += b"\0" * (-len(metadata) % 16)
                body = b"S" * 1024 + bytes([len(metadata) // 16]) + metadata
                interval = "1048577" if self.path == "/icy-large" else "1024"
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("icy-metaint", interval)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.path == "/icy-hang":
                    time.sleep(3)
                    return
                if self.path == "/icy-short":
                    body = body[:-10]
                try:
                    for offset in range(0, len(body), 7):
                        self.wfile.write(body[offset : offset + 7])
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                return
            if self.path in {"/redirect", "/redirect-private", "/redirect-loop"}:
                self.send_response(302)
                target = "/tone.wav"
                if self.path == "/redirect-private":
                    target = f"http://127.0.0.1:{private_server.server_port}/must-not-contact"
                elif self.path == "/redirect-loop":
                    target = "/redirect-loop"
                self.send_header("Location", target)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            limit = 16044 if self.path == "/cut" else len(payload)
            try:
                for offset in range(0, limit, 3200):
                    self.wfile.write(payload[offset : min(offset + 3200, limit)])
                    self.wfile.flush()
                    time.sleep(0.1)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer((TEST_HOST, 0), Handler)
    private_server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    secure_server = ThreadingHTTPServer((TEST_HOST, 0), Handler)
    wrong_server = ThreadingHTTPServer((TEST_WRONG_HOST, 0), Handler)
    logo_server = ThreadingHTTPServer((TEST_HOST, 80), Handler)
    logo_tls = ThreadingHTTPServer((TEST_HOST, 443), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(work / "tls-cert.pem"), str(work / "tls-key.pem"))
    secure_server.socket = context.wrap_socket(secure_server.socket, server_side=True)
    wrong_server.socket = context.wrap_socket(wrong_server.socket, server_side=True)
    logo_tls.socket = context.wrap_socket(logo_tls.socket, server_side=True)
    servers = [
        server,
        private_server,
        secure_server,
        wrong_server,
        logo_server,
        logo_tls,
    ]
    for current in servers:
        threading.Thread(target=current.serve_forever, daemon=True).start()
    children = []
    handles = []

    def launch(binary, config=None):
        handle = (work / f"{binary}.log").open("a")
        handles.append(handle)
        process = subprocess.Popen(
            [f"/usr/bin/{binary}"] + (["-c", config] if config else []),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=handle,
            stderr=handle,
        )
        children.append(process)
        return process

    def inputs():
        if core.poll() is not None:
            raise RuntimeError("Private PipeWire server exited; see its test log")
        result = subprocess.run(
            ["/usr/bin/pactl", "--format=json", "list", "sink-inputs"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=2,
        )
        return json.loads(result.stdout) if result.returncode == 0 else None

    try:
        if os.environ.get("NETMON_PROBE_HTTP_ONLY") == "1":
            _write_json(
                work / "ready.json",
                {
                    "port": server.server_port,
                    "tls_port": secure_server.server_port,
                    "wrong_tls_port": wrong_server.server_port,
                    "net_namespace": os.readlink("/proc/self/ns/net"),
                    "audio_server": False,
                },
            )
            while not (work / "stop").exists():
                time.sleep(0.05)
            return
        core = launch("pipewire", "pipewire.conf")
        _wait(lambda: (work / "runtime/pipewire-0").exists())
        launch("wireplumber")
        pulse = launch("pipewire-pulse", "pipewire-pulse.conf")
        _wait(lambda: inputs() is not None)

        def sinks_ready():
            result = subprocess.run(
                ["/usr/bin/pactl", "--format=json", "list", "sinks"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.returncode == 0 and json.loads(result.stdout)

        _wait(sinks_ready)
        _write_json(
            work / "ready.json",
            {
                "port": server.server_port,
                "tls_port": secure_server.server_port,
                "wrong_tls_port": wrong_server.server_port,
                "net_namespace": os.readlink("/proc/self/ns/net"),
            },
        )
        sequence = 0
        while not (work / "stop").exists():
            request = _read_json(work / "request.json")
            if request.get("sequence", 0) > sequence:
                sequence = request["sequence"]
                if request["audio"] == "off":
                    pulse.terminate()
                    pulse.wait(timeout=3)
                elif request["audio"] == "on":
                    pulse = launch("pipewire-pulse", "pipewire-pulse.conf")
                    _wait(lambda: inputs() is not None)
            _write_json(work / "audio.json", {"sequence": sequence, "inputs": inputs()})
            time.sleep(0.05)
    finally:
        for current in servers:
            current.shutdown()
            current.server_close()
        for process in reversed(children):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
        for handle in handles:
            handle.close()


def _ipc(process, command):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        # mpv's PCM driver writes blocks of 65536 frames (about 1.37 s at
        # 48 kHz). Backpressure can delay IPC while that write completes.
        client.settimeout(2.5)
        client.connect(process.ipc_path)
        client.sendall(
            json.dumps({"command": command, "request_id": 71}).encode() + b"\n"
        )
        with client.makefile("rb") as messages:
            for _ in range(20):
                response = json.loads(messages.readline(8192))
                if response.get("request_id") == 71:
                    return response
    raise AssertionError("No IPC reply")


def _worker(root, output, parent_net, *, gui=False, security=False, projectm=False):
    results = {
        "status": "failed",
        "host_network": False,
        "host_audio": False,
        "checks": [],
    }
    results["scope"] = (
        "private loopback HTTP and FIFO sink"
        if gui
        else "private loopback HTTP + isolated PipeWire-Pulse null sink"
    )
    results["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    sandbox_path = root / "netmon/core/radio_sandbox.py"
    results["source_sha256"] = hashlib.sha256(sandbox_path.read_bytes()).hexdigest()
    service = None
    active = None
    recording = None
    handles = []
    original_popen = subprocess.Popen
    original_read = os.read
    recording_init_restore = None
    try:
        current_net = os.readlink("/proc/self/ns/net")
        assert current_net != parent_net, "Refusing to alter host loopback"
        assert [name for _index, name in socket.if_nameindex()] == ["lo"]
        # The parent-side PCM API now imports its ordinary package module.
        # This coordinator loads sandbox.py by filename; children still get
        # only their explicit runtime/script mounts, never this sys.path.
        sys.path.insert(0, str(root))
        results["fetcher_sha256"] = hashlib.sha256(
            (root / "netmon/core/radio_fetch.py").read_bytes()
        ).hexdigest()
        results["catalog_sha256"] = hashlib.sha256(
            (root / "netmon/core/radio_catalog.py").read_bytes()
        ).hexdigest()
        results["pcm_source_sha256"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "netmon/core/radio_pcm.py",
                "tests/radio_pcm_probe.py",
                "netmon/core/projectm_audio.py",
                "tests/projectm_audio_probe.py",
            )
        }
        results["logo_source_sha256"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "netmon/core/radio_logo.py",
                "netmon/core/icon_http.py",
                "netmon/core/icon_payload.py",
                "netmon/netmon_radio_app.py",
            )
        }
        results["preset_policy_sha256"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "netmon/core/projectm_archive.py",
                "netmon/core/projectm_transport.py",
                "netmon/core/archive_limits.py",
                "netmon/app.py",
                "netmon/core/projectm_zip.py",
                "netmon/core/projectm_process.py",
                "netmon/core/projectm_import_plan.py",
                "netmon/netmon_projectm_sidecar.py",
            )
        }
        # This link belongs only to the just-verified private network namespace.
        subprocess.run(["/usr/sbin/ip", "link", "set", "lo", "up"], env=ENV, check=True)
        subprocess.run(
            ["/usr/sbin/ip", "address", "add", f"{TEST_HOST}/32", "dev", "lo"],
            env=ENV,
            check=True,
        )
        subprocess.run(
            ["/usr/sbin/ip", "address", "add", f"{TEST_WRONG_HOST}/32", "dev", "lo"],
            env=ENV,
            check=True,
        )
        # This sysctl belongs to the verified NEW network namespace above.
        # Preserve the production icon policy's mandatory default ports.
        Path("/proc/sys/net/ipv4/ip_unprivileged_port_start").write_text("0")
        # bwrap refuses unexpected inherited capabilities. These were needed
        # only to bring up the already-verified private loopback interface.
        _drop_namespace_caps()
        results["test_network_namespace"] = current_net
        from netmon.core import radio_sandbox as sandbox

        assert Path(sandbox.__file__).resolve() == sandbox_path.resolve()
        for name in ("runtime", "home", "config", "ipc"):
            (output / name).mkdir(mode=0o700)
        (output / "config/openssl.cnf").write_text(
            "[req]\ndistinguished_name=dn\n[dn]\n"
        )
        certificate = subprocess.run(
            [
                "/usr/bin/openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(output / "tls-key.pem"),
                "-out",
                str(output / "tls-cert.pem"),
                "-days",
                "1",
                "-subj",
                f"/CN={TEST_HOST}",
                "-addext",
                f"subjectAltName=IP:{TEST_HOST}",
                "-config",
                str(output / "config/openssl.cnf"),
            ],
            env=ENV,
            capture_output=True,
            text=True,
            timeout=15,
        )
        (output / "certificate.log").write_text(certificate.stdout + certificate.stderr)
        assert certificate.returncode == 0
        (output / "runtime/pulse").mkdir(mode=0o700)
        (output / "config/pipewire.conf").write_text(PW_CONFIG)
        (output / "config/pipewire-pulse.conf").write_text(PULSE_CONFIG)
        (output / "config/pulse-client.conf").write_text(
            "autospawn = no\nenable-shm = no\n"
        )
        shutil.copyfile(
            "/usr/share/pipewire/client.conf", output / "config/client.conf"
        )
        wp_config = output / "config/wireplumber"
        shutil.copytree("/usr/share/wireplumber", wp_config)
        wp_main = wp_config / "wireplumber.conf"
        bluetooth = "  { name = bluetooth.lua, type = config/lua }"
        assert (
            bluetooth in wp_main.read_text()
        ), "Expected installed WirePlumber 0.4 config"
        wp_main.write_text(wp_main.read_text().replace(bluetooth, ""))
        (wp_config / "main.lua.d/89-no-host-devices.lua").write_text(
            "alsa_monitor.enabled = false\n"
            "v4l2_monitor.enabled = false\n"
            "libcamera_monitor.enabled = false\n"
            'default_access.properties["enable-flatpak-portal"] = false\n'
        )
        (output / "passwd").write_text(
            f"test:x:{os.getuid()}:{os.getgid()}::/work/home:/nonexistent\n"
        )
        (output / "group").write_text(f"test:x:{os.getgid()}:\n")
        args = [
            "/usr/bin/bwrap",
            "--unshare-user",
            "--unshare-pid",
            "--unshare-ipc",
            "--unshare-uts",
            "--disable-userns",
            "--assert-userns-disabled",
            "--die-with-parent",
            "--new-session",
            "--cap-drop",
            "ALL",
            "--clearenv",
        ]
        if gui:
            args += ["--setenv", "NETMON_PROBE_HTTP_ONLY", "1"]
        for path in ("/usr", "/lib", "/lib64"):
            if Path(path).exists():
                args += ["--ro-bind", path, path]
        args += [
            "--symlink",
            "usr/bin",
            "/bin",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--dir",
            "/run",
            "--bind",
            str(output),
            "/work",
            "--ro-bind",
            str(Path(__file__).resolve()),
            "/probe/stream.py",
            "--ro-bind",
            str(output / "passwd"),
            "/etc/passwd",
            "--ro-bind",
            str(output / "group"),
            "/etc/group",
            "--chdir",
            "/work",
            "--setenv",
            "TEST_NET_NS",
            current_net,
            "--",
            "/usr/bin/python3",
            "-B",
            "/probe/stream.py",
            "--services",
        ]
        log = (output / "services.log").open("w")
        handles.append(log)
        service = subprocess.Popen(args, env=ENV, stdout=log, stderr=log)

        def services_ready():
            if service.poll() is not None:
                raise RuntimeError("Test services exited; see services.log")
            return _read_json(output / "ready.json")

        ready = _wait(services_ready)
        assert ready["net_namespace"] == current_net
        if security:
            from radio_security_probe import audit

            os.environ["XDG_RUNTIME_DIR"] = str(output / "runtime")
            results["scope"] = "adversarial test program under actual playback grants"
            results["security_review"] = audit(
                sandbox, output, f"http://{TEST_HOST}:{ready['port']}/tone.wav"
            )
            results["checks"] = results["security_review"]["checks"]
            results["security_acceptance"] = False
        elif gui:
            environment = {
                **ENV,
                "HOME": str(output / "home"),
                "TMPDIR": str(output / "home"),
                "XDG_RUNTIME_DIR": str(output / "runtime"),
                "XDG_CONFIG_HOME": str(output / "config"),
                "XDG_CACHE_HOME": str(output / "home/cache"),
                "XDG_STATE_HOME": str(output / "home/state"),
                "XDG_DATA_HOME": str(output / "home/data"),
                "XDG_DOCUMENTS_DIR": str(output / "home/documents"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "NETMON_RADIO_GUI_WORK": str(output),
                "NETMON_RADIO_GUI_ROOT": str(root),
                "NETMON_RADIO_GUI_NET_NS": current_net,
                "NETMON_RADIO_GUI_PROJECTM": "1" if projectm else "0",
            }
            command = [
                "/usr/bin/xvfb-run",
                "-a",
                "-e",
                str(output / "xvfb.log"),
                "-s",
                "-screen 0 1280x1024x24 -nolisten tcp -extension GLX",
                str(root / ".venv/bin/python"),
                "-B",
                str(root / "tests/radio_gui_probe.py"),
                "--scenario",
            ]
            gui_run = subprocess.run(
                command,
                env=environment,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=240 if projectm else 120,
            )
            (output / "gui-driver.log").write_text(gui_run.stdout + gui_run.stderr)
            assert gui_run.returncode == 0, "GUI probe failed; see gui-driver.log"
            gui_result = _read_json(output / "radio-gui-result.json")
            assert gui_result.get("status") == "passed"
            results["scope"] = (
                "Tk radio transitions with private HTTP and FIFO sink; real product quotas"
            )
            results["active_projectm"] = projectm
            results["checks"] = gui_result["checks"]
        else:
            os.environ["XDG_RUNTIME_DIR"] = str(output / "runtime")
            # Compile only the pure command builder, without importing the app.
            source = (root / "netmon/features/radio_controller.py").read_text()
            results["controller_sha256"] = hashlib.sha256(source.encode()).hexdigest()

            tree = ast.parse(source)
            command_function = next(
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "_mpv_command"
            )
            namespace = {}
            exec(
                compile(
                    ast.Module(body=[command_function], type_ignores=[]),
                    str(root),
                    "exec",
                ),
                namespace,
            )
            build_command = namespace["_mpv_command"]
            playback_log = (output / "mpv.log").open("w")
            handles.append(playback_log)
            pcm_log = (output / "pcm.log").open("w")
            handles.append(pcm_log)
            source_log = (output / "source.log").open("w")
            handles.append(source_log)
            parser_log = (output / "catalog-parser.log").open("w")
            handles.append(parser_log)
            zip_log = (output / "zip-worker.log").open("w")
            handles.append(zip_log)
            logo_log = (output / "logo.log").open("w")
            handles.append(logo_log)
            recording_log = (output / "recording-progress.log").open("wb")
            handles.append(recording_log)
            recording_errors = (output / "recording-errors.log").open("wb")
            handles.append(recording_errors)
            recording_streams = []
            original_recording_init = sandbox.RecordingProcess.__init__

            def observe_recording(owner, *args, **kwargs):
                original_recording_init(owner, *args, **kwargs)
                recording_streams.append(owner._progress_file)

            recording_init_restore = (sandbox.RecordingProcess, original_recording_init)
            sandbox.RecordingProcess.__init__ = observe_recording

            class LoggedPopen(original_popen):
                def __init__(self, args, *other, **kwargs):
                    if args[0] == str(sandbox.BWRAP) and str(sandbox.MPV) in args:
                        # Test-only diagnostics; command and path grants stay exact.
                        kwargs["stderr"] = playback_log
                    if args[0] == str(sandbox.BWRAP) and "/run/pcm.py" in args:
                        kwargs["stderr"] = pcm_log
                    if args[0] == str(sandbox.BWRAP) and "/run/fetch.py" in args:
                        kwargs["stderr"] = source_log
                    if args[0] == str(sandbox.BWRAP) and "/run/catalog.py" in args:
                        kwargs["stderr"] = parser_log
                    if args[0] == str(sandbox.BWRAP) and "/run/zip.py" in args:
                        kwargs["stderr"] = zip_log
                    if args[0] == str(sandbox.BWRAP) and "/run/logo.py" in args:
                        kwargs["stderr"] = logo_log
                    if args[0] == str(sandbox.BWRAP) and str(sandbox.FFMPEG) in args:
                        kwargs["stderr"] = recording_errors
                    super().__init__(args, *other, **kwargs)

            subprocess.Popen = LoggedPopen

            def read_progress(descriptor, size):
                data = original_read(descriptor, size)
                if any(
                    not stream.closed and stream.fileno() == descriptor
                    for stream in recording_streams
                ):
                    recording_log.write(data)
                    recording_log.flush()
                return data

            os.read = read_progress

            def start(route, *, url=None):
                command = build_command(
                    40,
                    url or f"http://{TEST_HOST}:{ready['port']}/{route}",
                    sandbox.IPC_PATH,
                )
                command.insert(-2, "--log-file=/run/control/decoder-debug.log")
                return sandbox.start_playback(
                    command,
                    ipc_root=output / "ipc",
                )

            def progress(process):
                log = Path(process.ipc_path).parent / "decoder-debug.log"
                if log.exists():
                    shutil.copyfile(log, output / "decoder-debug.log")
                if process.poll() is not None:
                    raise AssertionError("Test playback exited; see mpv.log")
                try:
                    response = _ipc(process, ["get_property", "time-pos"])
                    audio = _ipc(process, ["get_property", "current-ao"])
                    inputs = _read_json(output / "audio.json").get("inputs") or []
                    _write_json(
                        output / "playback-progress.json",
                        {
                            "time": response,
                            "ao": audio,
                            "inputs": inputs,
                        },
                    )
                    if (
                        response.get("error") == "success"
                        and isinstance(response.get("data"), (float, int))
                        and response["data"] > 1
                        and audio.get("data") == "pcm"
                        and any(
                            not item["corked"] and item["sink"] != 4294967295
                            for item in inputs
                        )
                    ):
                        return {
                            "time_pos": response["data"],
                            "audio_output": audio["data"],
                            "sink_inputs": inputs,
                        }
                except (OSError, ValueError):
                    pass
                return False

            active = start("tone.wav")
            results["playback"] = _wait(lambda: progress(active), timeout=12)
            results["pipe_media_title"] = _ipc(active, ["get_property", "media-title"])
            with active.open_pcm_tap() as tap:
                payloads = [tap.read() for _ in range(3)]
                assert all(len(payload) % 4 == 0 for payload in payloads)
                assert any(any(payload) for payload in payloads)
                results["pcm_live"] = {
                    "packets": len(payloads),
                    "bytes": sum(map(len, payloads)),
                }
            with active.open_pcm_tap() as tap:
                tap.read()
                before = _wait(lambda: progress(active))["time_pos"]
                time.sleep(0.4)
                _wait(lambda: (progress(active) or {}).get("time_pos", 0) > before)
            active.terminate()
            active.wait(timeout=4)
            active = None
            _wait(lambda: _read_json(output / "audio.json").get("inputs") == [])
            results["checks"].append(
                "HTTP stream decodes through real PulseAudio protocol to private null sink; stop releases sink input"
            )
            results["checks"].append(
                "live NetMon PCM tap returns bounded nonzero aligned samples; close/reopen and a stalled receiver preserve private-sink playback"
            )
            from projectm_audio_probe import check_source

            active = start("tone.wav")
            results["private_projectm_audio"] = check_source(output, active)
            active.terminate()
            active.wait(timeout=4)
            active = None
            results["checks"].append(
                "real HTTP/mpv NetMon PCM reaches the private projectM Pulse source; server-local module rights measured and audio capsule cleanup preserves playback"
            )
            from radio_pcm_probe import run as pcm_probe

            results["pcm_probe"] = pcm_probe(root, output, TEST_HOST, ready["port"])
            results["checks"].extend(
                [
                    "exact PCM relay copies one MiB unchanged with missing and stalled optional receiver; no optional backpressure",
                    "PCM compromise model retains real grants: private/control/audio/request files, TCP/abstract sockets, inherited secrets, writes and fork denied; only one-way tap granted",
                ]
            )
            active = start("tone.wav")
            _wait(lambda: progress(active), timeout=12)
            active._pcm_process.kill()
            assert active.wait(timeout=5) != 0
            assert active._audio_process.poll() is not None
            assert active._source_process.poll() is not None
            active = None
            _wait(lambda: _read_json(output / "audio.json").get("inputs") == [])
            results["checks"].append(
                "lost PCM relay ends decoder, audio and source and cleans its private session"
            )
            preset_url = f"http://{TEST_HOST}:{ready['port']}"
            preset_body = io.BytesIO()
            count = sandbox.fetch_preset_archive(
                preset_url + "/preset-redirect", preset_body
            )
            assert preset_body.getvalue() == _preset_zip() and count == len(
                _preset_zip()
            )
            for route in (
                "preset-private",
                "preset-loop",
                "preset-large",
                "preset-cut",
                "preset-duplicate",
                "preset-gzip",
                "preset-hang",
            ):
                try:
                    sandbox.fetch_preset_archive(
                        preset_url + "/" + route,
                        io.BytesIO(),
                        timeout=0.3 if route == "preset-hang" else 4,
                    )
                except sandbox.RadioSandboxError:
                    pass
                else:
                    raise AssertionError("Invalid preset response accepted: " + route)
            try:
                sandbox.fetch_preset_archive(
                    preset_url + "/preset-good", io.BytesIO(), limit=8
                )
            except sandbox.RadioSandboxError:
                pass
            else:
                raise AssertionError("Parent preset byte limit not enforced")
            results["preset_download"] = {
                "bytes": count,
                "sha256": hashlib.sha256(preset_body.getvalue()).hexdigest(),
            }
            results["checks"].append(
                "preset source streams exact ZIP bytes; private/loop/oversize/truncated/ambiguous/encoded/stalled responses and parent byte overrun fail closed"
            )
            from projectm_zip_probe import run as check_zip_worker

            results["zip_probe_sha256"] = hashlib.sha256(
                (root / "tests/projectm_zip_probe.py").read_bytes()
            ).hexdigest()
            results["zip_worker"] = check_zip_worker(
                root, output, TEST_HOST, ready["port"]
            )
            results["checks"].append(
                "offline ZIP worker imports presets/assets and preserves originals; CRC/traversal/link/ratio/object failures preserve old packs; full 50000-preset capacity retained"
            )
            results["checks"].append(
                "ZIP worker compromise model cannot access original/private files, writable snapshot/proc reopen, network/abstract sockets, inherited secrets or fork; memory/CPU/output limits apply"
            )

            recording_url = f"http://{TEST_HOST}:{ready['port']}/tone.wav"
            preserved = output / "capture.mp3"
            preserved.write_bytes(b"PREVIOUS RECORDING MUST STAY")
            recording = sandbox.start_recording(
                recording_url, preserved, work_root=output
            )
            captured = Path(recording.output_path)

            def enough_recorded():
                assert (
                    recording.poll() is None
                ), "recording ended before enough MP3 data"
                return captured.stat().st_size >= 72000

            _wait(enough_recorded, timeout=10)
            recording.terminate()
            assert recording.wait(timeout=4) == 0
            assert preserved.read_bytes() == b"PREVIOUS RECORDING MUST STAY"
            assert captured.name == "capture-001.mp3"
            assert captured.stat().st_mode & 0o777 == 0o600
            results["recording"] = {
                "path": captured.name,
                "bytes": captured.stat().st_size,
                "mode": "0600",
                "ready": recording.ready,
                "runtime_verified": recording.runtime_verified,
            }
            recording = None
            active = sandbox.start_playback(
                build_command(40, str(captured), sandbox.IPC_PATH),
                ipc_root=output / "ipc",
                local_file=captured,
            )
            _wait(lambda: progress(active), timeout=12)
            active.terminate()
            active.wait(timeout=4)
            active = None
            results["checks"].append(
                "real pipe-only ffmpeg records MP3 with 192k requested; graceful source EOF flushes; existing recording preserved, new 0600 file replays through protected mpv"
            )

            recording = sandbox.start_recording(
                recording_url, output / "interrupted.mp3", work_root=output
            )
            recording._source_process.kill()
            assert recording.wait(timeout=5) != 0
            recording = None
            recording = sandbox.start_recording(
                recording_url, output / "killed.mp3", work_root=output
            )
            recording.kill()
            assert recording.wait(timeout=4) != 0
            recording = None
            for name, url in (
                ("http-error", f"http://{TEST_HOST}:{ready['port']}/fail"),
                ("private", "http://127.0.0.1/private"),
                ("unsupported", "rtsp://example.com/live"),
                ("playlist", f"http://{TEST_HOST}:{ready['port']}/recording-playlist"),
                ("headers-pending", f"http://{TEST_HOST}:{ready['port']}/hang"),
            ):
                try:
                    recording = sandbox.start_recording(
                        url, output / (name + ".mp3"), work_root=output
                    )
                except sandbox.RadioSandboxError:
                    pass
                else:
                    raise AssertionError("failed recording start accepted: " + name)
            assert not any(path.is_dir() for path in output.glob("record-*"))
            assert (
                "/must-not-contact"
                not in (output / "http.log").read_text().splitlines()
            )
            results["checks"].append(
                "recording source loss and kill fail; HTTP/private/unsupported/disguised-playlist/stalled starts rejected, children and temporary sessions cleaned"
            )
            from radio_recording_probe import audit as audit_recording

            results["recording_probe_sha256"] = hashlib.sha256(
                (root / "tests/radio_recording_probe.py").read_bytes()
            ).hexdigest()
            results["ffmpeg_sha256"] = hashlib.sha256(
                sandbox.FFMPEG.read_bytes()
            ).hexdigest()

            results["recording_boundary"] = audit_recording(
                sandbox, output, recording_url
            )
            results["checks"].append(
                "compiled encoder probe under exact ffmpeg grants: no private/sibling/request/control/audio files, TCP/abstract sockets, inherited FD/environment or new user namespace; only chosen output FD and own progress FIFO granted"
            )

            logo_policy = sandbox._logo_policy()
            logo_url = f"http://{TEST_HOST}/logo-ok"
            logo_pixels = sandbox.fetch_logo(logo_url, work_root=output)
            frames = logo_policy.validate_pixels(logo_pixels)
            assert all(
                (width, height, pixels) == (2, 1, b"\xff\0\0\xff\0\xff\0\0")
                for width, height, pixels in frames
            )
            assert sandbox.decode_logo(_logo_png(), work_root=output) == logo_pixels
            for route in (
                "logo-bad",
                "logo-large",
                "logo-cut",
                "logo-hang",
                "logo-private",
                "logo-loop",
            ):
                try:
                    sandbox.fetch_logo(
                        f"http://{TEST_HOST}/{route}",
                        work_root=output,
                        timeout=0.3 if route == "logo-hang" else 4,
                    )
                except (sandbox.RadioSandboxError, ValueError):
                    pass
                else:
                    raise AssertionError("Invalid logo accepted: " + route)
            assert not any(path.is_dir() for path in output.glob("logo-*"))
            results["logo_pixels"] = [
                {"width": w, "height": h, "bytes": len(data)} for w, h, data in frames
            ]
            results["checks"].append(
                "separate logo source and offline Pillow decoder return raw RGBA; cached PNG converts offline; invalid/oversized/truncated/stalled/private/loop responses fail closed"
            )

            catalog_url = f"http://{TEST_HOST}:{ready['port']}"
            probe_results = {}
            for route, station, ranged, expected in (
                ("probe-body-hang", False, False, True),
                ("probe-forbidden", False, False, True),
                ("probe-range", True, True, True),
                ("probe-range", False, False, False),
                ("probe-missing", True, False, False),
                ("probe-icy", True, True, True),
                ("probe-icy", False, False, None),
                ("probe-malformed", True, False, None),
                ("redirect-private", True, True, None),
                ("redirect-loop", False, False, None),
            ):
                key = f"{route}:{station}:{ranged}"
                probe_results[key] = sandbox.probe_reachability(
                    catalog_url + "/" + route,
                    station=station,
                    ranged=ranged,
                    timeout=2,
                    work_root=output,
                )
                assert probe_results[key] is expected, (key, probe_results[key])
            assert (
                sandbox.probe_reachability(
                    "http://127.0.0.1:1/private", work_root=output, timeout=2
                )
                is None
            )
            assert (
                sandbox.probe_reachability(
                    "rtsp://example.com/unsupported", work_root=output, timeout=2
                )
                is None
            )
            try:
                sandbox.probe_reachability(
                    catalog_url + "/hang", timeout=0.3, work_root=output
                )
            except sandbox.RadioSandboxError:
                pass
            else:
                raise AssertionError("Stalled reachability probe exceeded deadline")
            assert not any(path.is_dir() for path in output.glob("probe-*"))
            probe_requests = [
                json.loads(line)
                for line in (output / "probe-requests.jsonl").read_text().splitlines()
            ]
            assert any(
                item["range"] == "bytes=0-0" and item["icy"] == "1"
                for item in probe_requests
            )
            results["reachability"] = probe_results
            results["checks"].append(
                "restricted reachability source: headers only, 403/416/404, strict legacy ICY, private/unsupported targets and redirect loop, deadline and cleanup"
            )
            catalog_rows = sandbox.fetch_catalog(
                catalog_url + "/catalog-json", post=True, work_root=output
            )
            assert catalog_rows[0]["name"] == "Native Catalog"
            assert json.loads((output / "catalog-post.json").read_text()) == {
                "hidebroken": True,
                "limit": 5000,
                "offset": 0,
            }
            xml_rows = sandbox.fetch_catalog(
                catalog_url + "/catalog-xml", kind="xml", work_root=output
            )
            assert xml_rows[0]["name"] == "Native XML"
            results["catalog_rows"] = {"json": catalog_rows, "xml": xml_rows}
            for route, kind in (
                ("catalog-bad", "json"),
                ("catalog-dtd", "xml"),
                ("catalog-cut", "json"),
                ("catalog-large", "json"),
                ("catalog-hang", "json"),
                ("redirect-private", "json"),
            ):
                try:
                    sandbox.fetch_catalog(
                        catalog_url + "/" + route,
                        kind=kind,
                        timeout=1 if route == "catalog-hang" else 4,
                        work_root=output,
                    )
                except sandbox.RadioSandboxError:
                    pass
                else:
                    raise AssertionError("Invalid catalog accepted: " + route)
            assert not any(path.is_dir() for path in output.glob("catalog-*"))
            results["checks"].append(
                "catalog POST/JSON and XML use separate source/parser; malformed, DTD, truncated, oversized, stalled and private redirect responses rejected"
            )

            # Model code execution after the parser's real limit setup. Only
            # the script contents change; namespace and path grants stay exact.
            private = output / "catalog-private.txt"
            private.write_text("SYNTHETIC PRIVATE DATA")
            catalog_text = sandbox.CATALOG.read_text()
            limit_function = next(
                node
                for node in ast.parse(catalog_text).body
                if isinstance(node, ast.FunctionDef)
                and node.name == "apply_process_limits"
            )
            probe_script = output / "catalog-boundary-probe.py"
            abstract_name = "catalog-" + output.name
            abstract_literal = repr("\0" + abstract_name)
            probe_script.write_text(
                "import json,os,socket,resource,sys\n"
                + ast.get_source_segment(catalog_text, limit_function)
                + "\napply_process_limits()\nsys.stdin.buffer.read(16*1024*1024+1)\n"
                + "def reach(address,family):\n s=socket.socket(family,socket.SOCK_STREAM)\n s.settimeout(.2)\n try:\n  s.connect(address)\n  return True\n except OSError:\n  return False\n finally:\n  s.close()\n"
                + f"r={{'tcp':reach(({TEST_HOST!r},{ready['port']}),socket.AF_INET),'unix':reach({abstract_literal},socket.AF_UNIX),'private':os.path.exists({str(private)!r}),'request':os.path.exists('/run/request.json'),'control':os.path.exists('/run/control'),'audio':os.path.exists('/run/audio/pulse'),'memory':resource.getrlimit(resource.RLIMIT_AS)[1],'cpu':resource.getrlimit(resource.RLIMIT_CPU)[1]}}\n"
                + "try:\n p=os.fork()\nexcept OSError:\n r['fork']=False\nelse:\n if p==0: os._exit(0)\n os.waitpid(p,0)\n r['fork']=True\n"
                + "print(json.dumps({'rows':[{'name':json.dumps(r),'url':'https://example.com/live'}]}))\n"
            )
            original_parser = sandbox._catalog_command

            def parser_probe(*args, **kwargs):
                command = original_parser(*args, **kwargs)
                for index in range(len(command) - 2):
                    if (
                        command[index] == "--ro-bind"
                        and command[index + 2] == "/run/catalog.py"
                    ):
                        command[index + 1] = str(probe_script)
                return command

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind("\0" + abstract_name)
                listener.listen(2)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as control:
                    control.connect("\0" + abstract_name)
                sandbox._catalog_command = parser_probe
                try:
                    report = json.loads(
                        sandbox.fetch_catalog(
                            catalog_url + "/catalog-json", work_root=output
                        )[0]["name"]
                    )
                finally:
                    sandbox._catalog_command = original_parser
            assert all(
                report[key] is False
                for key in (
                    "tcp",
                    "unix",
                    "private",
                    "request",
                    "control",
                    "audio",
                    "fork",
                )
            ), report
            assert 0 < report["memory"] <= 384 * 1024 * 1024 and 0 < report["cpu"] <= 8
            results["catalog_parser_boundary"] = report
            results["checks"].append(
                "parser probe cannot reach TCP/abstract services or private/control/audio paths; memory/CPU limits apply and fork is denied"
            )
            logo_text = sandbox.LOGO.read_text()
            logo_limit = next(
                node
                for node in ast.parse(logo_text).body
                if isinstance(node, ast.FunctionDef)
                and node.name == "apply_process_limits"
            )
            logo_probe = output / "logo-boundary-probe.py"
            body = probe_script.read_text()
            start_limit = body.index("def apply_process_limits")
            end_limit = body.index("\napply_process_limits()", start_limit)
            body = (
                body[:start_limit]
                + ast.get_source_segment(logo_text, logo_limit)
                + body[end_limit:]
            )
            body = body.replace(
                "apply_process_limits()\n", "apply_process_limits(decoder=True)\n"
            )
            body = (
                body[: body.index("print(json.dumps({'rows'")]
                + "import struct\np=json.dumps(r).encode();assert len(p)<=1024\np=p.ljust(1024,b'\\0')\nsys.stdout.buffer.write(b'NMRL1\\0'+(struct.pack('>HH',16,16)+p)*3)\n"
            )
            logo_probe.write_text(body)
            original_logo = sandbox._logo_command

            def logo_boundary(*args, **kwargs):
                command = original_logo(*args, **kwargs)
                if not kwargs["fetch"]:
                    for index in range(len(command) - 2):
                        if (
                            command[index] == "--ro-bind"
                            and command[index + 2] == "/run/logo.py"
                        ):
                            command[index + 1] = str(logo_probe)
                return command

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind("\0" + abstract_name)
                listener.listen(2)
                sandbox._logo_command = logo_boundary
                try:
                    report_pixels = sandbox.decode_logo(_logo_png(), work_root=output)
                finally:
                    sandbox._logo_command = original_logo
            logo_report = json.loads(
                logo_policy.validate_pixels(report_pixels)[0][2].rstrip(b"\0")
            )
            assert all(
                logo_report[key] is False
                for key in (
                    "tcp",
                    "unix",
                    "private",
                    "request",
                    "control",
                    "audio",
                    "fork",
                )
            ), logo_report
            assert (
                0 < logo_report["memory"] <= 384 * 1024 * 1024
                and 0 < logo_report["cpu"] <= 8
            )
            results["logo_decoder_boundary"] = logo_report
            results["checks"].append(
                "logo decoder probe retains exact grants and limits; TCP/abstract sockets, private/request/control/audio files and fork denied"
            )

            metadata_url = f"http://{TEST_HOST}:{ready['port']}/icy-title"
            results["icy_title"] = sandbox.fetch_icy_title(
                metadata_url, work_root=output
            )
            assert results["icy_title"] == "Private Test Artist - Test Track"
            for route in ("icy-large", "icy-short", "icy-hang", "redirect-private"):
                try:
                    sandbox.fetch_icy_title(
                        f"http://{TEST_HOST}:{ready['port']}/{route}",
                        timeout=0.3 if route == "icy-hang" else 4,
                        work_root=output,
                    )
                except sandbox.RadioSandboxError:
                    pass
                else:
                    raise AssertionError(f"Invalid metadata accepted: {route}")
            assert not any(path.is_dir() for path in output.glob("icy-*"))
            assert (
                "/must-not-contact"
                not in (output / "http.log").read_text().splitlines()
            )
            assert all(
                json.loads(line)["icy"] == "1"
                for line in (output / "icy-requests.jsonl").read_text().splitlines()
            )
            results["checks"].append(
                "separate ICY source returns bounded title; oversized, truncated, stalled and private redirect metadata fail closed"
            )

            def rejected(route, *, url=None):
                nonlocal active
                try:
                    active = start(route, url=url)
                except sandbox.RadioSandboxError:
                    pass
                else:
                    _wait(lambda: active.poll() is not None, timeout=8)
                    assert active.wait(timeout=2) != 0
                    active = None
                assert not list((output / "ipc").glob("play-*"))

            tls_url = f"https://{TEST_HOST}:{ready['tls_port']}/tone.wav"
            rejected("", url=tls_url)  # Self-signed certificate is not trusted.
            normal_files = sandbox._network_files

            def test_certificate_files():
                return tuple(
                    (
                        (
                            output / "tls-cert.pem"
                            if destination.endswith("ca-certificates.crt")
                            else source
                        ),
                        destination,
                    )
                    for source, destination in normal_files()
                )

            # Only the synthetic trust bundle changes, not the TLS checks.
            sandbox._network_files = test_certificate_files
            try:
                preset_tls = io.BytesIO()
                sandbox.fetch_preset_archive(
                    f"https://{TEST_HOST}:{ready['tls_port']}/preset-good", preset_tls
                )
                assert preset_tls.getvalue() == _preset_zip()
                try:
                    sandbox.fetch_preset_archive(
                        f"https://{TEST_HOST}:{ready['tls_port']}/preset-downgrade",
                        io.BytesIO(),
                    )
                except sandbox.RadioSandboxError:
                    pass
                else:
                    raise AssertionError("Preset TLS downgrade accepted")
                results["preset_tls"] = (
                    "trusted synthetic certificate, downgrade rejected"
                )
                assert (
                    sandbox.fetch_logo(f"https://{TEST_HOST}/logo-ok", work_root=output)
                    == logo_pixels
                )
                results["logo_tls"] = (
                    "trusted synthetic certificate with unchanged icon policy"
                )
                assert (
                    sandbox.probe_reachability(tls_url, timeout=2, work_root=output)
                    is True
                )
                assert (
                    sandbox.probe_reachability(
                        f"https://{TEST_WRONG_HOST}:{ready['wrong_tls_port']}/tone.wav",
                        timeout=2,
                        work_root=output,
                    )
                    is False
                )
                results["reachability_tls"] = {"trusted": True, "wrong_identity": False}
                active = start("", url=tls_url)
                results["tls_playback"] = _wait(lambda: progress(active), timeout=12)
                active.terminate()
                active.wait(timeout=4)
                active = None
                rejected(
                    "",
                    url=f"https://{TEST_WRONG_HOST}:{ready['wrong_tls_port']}/tone.wav",
                )
            finally:
                sandbox._network_files = normal_files
            results["checks"].append(
                "HTTPS verifies trust and peer identity; trusted synthetic certificate plays, wrong IP fails"
            )

            active = start("redirect")
            _wait(lambda: progress(active), timeout=12)
            active._source_process.kill()
            _wait(lambda: active.poll() is not None, timeout=5)
            assert active.wait(timeout=2) != 0
            active = None
            _wait(lambda: _read_json(output / "audio.json").get("inputs") == [])
            rejected("redirect-private")
            rejected("redirect-loop")
            assert (
                "/must-not-contact"
                not in (output / "http.log").read_text().splitlines()
            )
            results["checks"].append(
                "relative HTTP redirect plays; lost source ends playback; private redirect never contacted; redirect loop bounded"
            )

            selected = output / "local-tone.wav"
            selected.write_bytes(_tone())
            active = sandbox.start_playback(
                build_command(40, str(selected), sandbox.IPC_PATH),
                ipc_root=output / "ipc",
                local_file=selected,
            )
            results["local_playback"] = _wait(lambda: progress(active), timeout=12)
            # Exercise real output loss while the decoder is already playing.
            active._audio_process.kill()
            _wait(lambda: active.poll() is not None, timeout=5)
            assert active.wait(timeout=2) != 0
            active = None
            assert not list((output / "ipc").glob("play-*"))
            _wait(lambda: _read_json(output / "audio.json").get("inputs") == [])
            results["checks"].append(
                "local media uses the real PCM bridge; lost output ends decoder and cleans session"
            )

            active = start("tone.wav")
            _wait(lambda: progress(active), timeout=12)
            active.kill()
            active.wait(timeout=4)
            active = None
            _wait(lambda: _read_json(output / "audio.json").get("inputs") == [])
            assert not list((output / "ipc").glob("play-*"))
            results["checks"].append("kill ends decoder and real audio output together")

            for route in ("fail", "cut"):
                try:
                    active = start(route)
                except sandbox.RadioSandboxError:
                    # A fast HTTP error may correctly end mpv before its IPC
                    # handshake. This is a rejected start, not a playback success.
                    assert f"/{route}" in (output / "http.log").read_text().splitlines()
                    results[f"{route}_start"] = "rejected before IPC readiness"
                else:
                    _wait(lambda: active.poll() is not None, timeout=10)
                    results[f"{route}_exit"] = active.wait(timeout=2)
                active = None
                assert not list((output / "ipc").glob("play-*"))
                active = start("tone.wav")
                _wait(lambda: progress(active), timeout=12)
                active.terminate()
                active.wait(timeout=4)
                active = None
                results["checks"].append(
                    f"{route} response ends playback; fresh stream restarts"
                )

            active = start("hang")
            _wait(lambda: "/hang" in (output / "http.log").read_text().splitlines())
            began = time.monotonic()
            active.terminate()
            active.wait(timeout=4)
            results["stop_pending_seconds"] = time.monotonic() - began
            active = None
            results["checks"].append(
                "stop ends playback while HTTP headers are pending"
            )

            _write_json(output / "request.json", {"sequence": 1, "audio": "off"})
            _wait(lambda: _read_json(output / "audio.json").get("sequence") == 1)
            recording = sandbox.start_recording(
                recording_url, output / "without-audio.mp3", work_root=output
            )
            recording.terminate()
            assert recording.wait(timeout=4) == 0
            recording = None
            results["checks"].append(
                "recording needs no audio socket and succeeds while private Pulse server is stopped"
            )
            try:
                active = start("tone.wav")
                _wait(lambda: active.poll() is not None, timeout=10)
                active.wait(timeout=2)
                active = None
            except sandbox.RadioSandboxError:
                pass
            assert not list((output / "ipc").glob("play-*"))
            _write_json(output / "request.json", {"sequence": 2, "audio": "on"})
            _wait(lambda: _read_json(output / "audio.json").get("sequence") == 2)
            active = start("tone.wav")
            _wait(lambda: progress(active), timeout=12)
            active.terminate()
            active.wait(timeout=4)
            active = None
            results["checks"].append(
                "missing test audio stops protected playback; restarted server accepts fresh playback"
            )
        results["status"] = "passed"
    except Exception:
        results["error"] = traceback.format_exc()
    finally:
        subprocess.Popen = original_popen
        os.read = original_read
        if recording_init_restore is not None:
            recording_init_restore[0].__init__ = recording_init_restore[1]
        if recording is not None:
            recording.kill()
            recording.wait(timeout=4)
        if active is not None and active.poll() is None:
            active.kill()
            active.wait(timeout=4)
        if service is not None:
            (output / "stop").touch()
            try:
                service.wait(timeout=5)
            except subprocess.TimeoutExpired:
                service.kill()
                service.wait(timeout=3)
        for handle in handles:
            handle.close()
    _write_json(output / "radio-stream-result.json", results)
    print(json.dumps(results, indent=2), flush=True)
    return 0 if results["status"] == "passed" else 1


def run(root, output, *, gui=False, security=False, projectm=False):
    if projectm and not gui:
        raise ValueError("Active projectM handover requires the private GUI mode")
    for program in (
        "unshare",
        "ip",
        "pipewire",
        "pipewire-pulse",
        "wireplumber",
        "pactl",
    ):
        if shutil.which(program) is None:
            raise RuntimeError(
                f"Existing test tool missing: {program}; do not install automatically"
            )
    command = [
        "/usr/bin/unshare",
        "--user",
        "--map-current-user",
        "--keep-caps",
        "--net",
        "--fork",
        "--kill-child=KILL",
        str(root / ".venv/bin/python"),
        "-B",
        str(Path(__file__).resolve()),
        "--worker",
        str(root),
        str(output),
        os.readlink("/proc/self/ns/net"),
    ]
    if gui:
        command.append("--gui")
    if projectm:
        command.append("--projectm-handover")
    if security:
        command.append("--security")
    print(f"Private stream/audio evidence: {output}", flush=True)
    try:
        result = subprocess.run(
            command,
            env=ENV,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=270 if projectm else 150,
        )
    except subprocess.TimeoutExpired as exc:
        # subprocess.run kills unshare; --kill-child and --die-with-parent
        # then tear down the coordinator and its isolated child processes.
        raw = (exc.stdout or b"") + (exc.stderr or b"")
        (output / "coordinator.log").write_bytes(raw)
        _write_json(
            output / "radio-stream-result.json",
            {
                "status": "failed",
                "error": "Test coordinator deadline exceeded",
                "host_network": False,
                "host_audio": False,
            },
        )
        return 1
    (output / "coordinator.log").write_text(result.stdout + result.stderr)
    if result.returncode and not (output / "radio-stream-result.json").exists():
        _write_json(
            output / "radio-stream-result.json",
            {
                "status": "failed",
                "error": "Test namespace coordinator could not run; see coordinator.log",
                "host_network": False,
                "host_audio": False,
            },
        )
    print(result.stdout + result.stderr, end="", flush=True)
    return result.returncode


if __name__ == "__main__":
    if sys.argv[1:] == ["--services"]:
        _services()
    elif len(sys.argv) in (5, 6, 7) and sys.argv[1] == "--worker":
        assert sys.argv[5:] in (
            [],
            ["--gui"],
            ["--security"],
            ["--gui", "--projectm-handover"],
        )
        raise SystemExit(
            _worker(
                Path(sys.argv[2]),
                Path(sys.argv[3]),
                sys.argv[4],
                gui="--gui" in sys.argv[5:],
                security=sys.argv[5:] == ["--security"],
                projectm="--projectm-handover" in sys.argv[5:],
            )
        )
    else:
        raise SystemExit("Use tests/run_isolated_suite.py --radio-stream-probe")
