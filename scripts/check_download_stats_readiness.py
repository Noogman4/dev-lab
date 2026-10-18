#!/usr/bin/env python3
"""Check copied PHP statistics locally, with ephemeral credentials and fake data."""

import argparse
from contextlib import contextmanager
import http.client
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
MARKER = "local-readiness-private-statistics"
IP_MARKER = "0123456789abcdef"


class ReadinessError(RuntimeError):
    """Only fixed, non-secret diagnostics may be shown by the CLI."""


@contextmanager
def local_php_server(php, directory, token, *, max_input_vars=1000, arg_separator="&"):
    # Never inherit a real deployment credential or CGI Authorization variable.
    env = {"PATH": os.defpath}
    if token is not None:
        env["NETMON_STATS_TOKEN"] = token
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    process = subprocess.Popen(
        [
            str(php),
            "-n",
            "-d",
            "display_errors=0",
            "-d",
            "log_errors=0",
            "-d",
            f"max_input_vars={int(max_input_vars)}",
            "-d",
            f"arg_separator.input={arg_separator}",
            "-S",
            f"127.0.0.1:{port}",
            "-t",
            str(directory),
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 5
        while True:
            if process.poll() is not None:
                raise ReadinessError("Local PHP server failed to start.")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                if time.monotonic() >= deadline:
                    raise ReadinessError("Local PHP startup timed out.") from None
                time.sleep(0.01)
        yield port
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def request(port, path="/download-stats.php", headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        body = response.read(256 * 1024 + 1)
        if len(body) > 256 * 1024:
            raise ReadinessError("Unexpectedly large local statistics response.")
        return response.status, {k.lower(): v for k, v in response.getheaders()}, body
    finally:
        connection.close()


def prepare_site(source, directory):
    directory = Path(directory)
    for name in ("download-lib.php", "download-config.php", "download-stats.php"):
        shutil.copyfile(Path(source) / name, directory / name)
    data = directory / "data"
    data.mkdir(mode=0o700)
    path = data / "download-stats.json"
    path.write_text(
        json.dumps(
            {
                "updated_at": MARKER,
                "total_downloads": 731,
                "files": {},
                "sources": {},
                "days": {},
                "recent_events": [{"ip_hash": IP_MARKER}],
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)
    return path


def check_response(response, status, *, authorized=False):
    actual, headers, body = response
    if actual != status:
        raise ReadinessError("Unexpected local authentication HTTP status.")
    if "no-store" not in headers.get("cache-control", "").lower():
        raise ReadinessError("Local authentication response is cacheable.")
    if headers.get("referrer-policy") != "no-referrer":
        raise ReadinessError("Local authentication response lacks referrer protection.")
    contains_data = MARKER.encode() in body and IP_MARKER.encode() in body
    if authorized:
        if not contains_data:
            raise ReadinessError(
                "Authorized local response lacks synthetic statistics."
            )
    elif body != (b"Statistics unavailable\n" if status == 503 else b"Forbidden\n"):
        raise ReadinessError("Local rejection response is not generic.")


def check_local_readiness(php, site_root=ROOT / "site"):
    # Only source files are copied. No real statistics or .htaccess are served.
    with tempfile.TemporaryDirectory(prefix="netmon-stats-readiness-") as tmp:
        directory = Path(tmp)
        path = prepare_site(site_root, directory)
        original = path.read_bytes()
        for unset in (None, "", "   "):
            with local_php_server(php, directory, unset) as port:
                check_response(request(port), 503)
        credential = secrets.token_urlsafe(32)
        with local_php_server(php, directory, credential) as port:
            check_response(request(port), 403)
            check_response(
                request(
                    port,
                    headers={"Authorization": "Bearer " + secrets.token_urlsafe(32)},
                ),
                403,
            )
            check_response(
                request(port, headers={"Authorization": "Bearer " + credential}),
                200,
                authorized=True,
            )
            check_response(
                request(
                    port,
                    "/download-stats.php?",
                    {"Authorization": "Bearer " + credential},
                ),
                200,
                authorized=True,
            )
            check_response(
                request(
                    port,
                    "/download-stats.php?t=1720000000000",
                    {"Authorization": "Bearer " + credential},
                ),
                200,
                authorized=True,
            )
            truncated = (
                "&".join(f"p{i}=x" for i in range(1000)) + "&token=synthetic-url-token"
            )
            check_response(
                request(
                    port,
                    "/download-stats.php?" + truncated,
                    {"Authorization": "Bearer " + credential},
                ),
                403,
            )
        if path.read_bytes() != original:
            raise ReadinessError("Readiness unexpectedly changed synthetic statistics.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--php", default=shutil.which("php"), help="Local PHP CLI executable"
    )
    args = parser.parse_args(argv)
    if not args.php:
        parser.error("PHP CLI required; use --php.")
    try:
        check_local_readiness(args.php)
    except (
        ReadinessError,
        OSError,
        subprocess.SubprocessError,
        http.client.HTTPException,
    ):
        print(
            "FAIL: local PHP statistics readiness; verify configuration and auth contract."
        )
        return 1
    print(
        "PASS: local PHP sees the synthetic token; missing config=503, denied=403, authorized=200."
    )
    print(
        "LOCAL ONLY: no verification of production cPanel, Apache, CGI, FPM or TLS configuration."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
