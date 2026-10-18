"""L-02: real local PHP HTTP, ephemeral credentials, synthetic private state."""

import http.client
import json
from pathlib import Path
import secrets
import shutil
import subprocess

import pytest

from scripts.check_download_stats_readiness import (
    IP_MARKER,
    MARKER,
    ReadinessError,
    check_local_readiness,
    local_php_server,
    prepare_site,
    request,
)
from tests.test_download_statistics import php as php

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def auth_site(tmp_path):
    path = prepare_site(ROOT / "site", tmp_path)
    return tmp_path, path


def assert_denied(response, code, site):
    status, headers, body = response
    assert status == code
    assert body == (b"Statistics unavailable\n" if code == 503 else b"Forbidden\n")
    assert "no-store" in headers["cache-control"]
    assert headers["pragma"] == "no-cache"
    assert headers["referrer-policy"] == "no-referrer"
    for private in (MARKER.encode(), IP_MARKER.encode(), str(site).encode()):
        assert private not in body


@pytest.mark.parametrize("token", [None, "", " ", "\t\n", " invalid ", "x" * 513])
def test_missing_or_invalid_server_token_never_discloses_existing_stats(
    php, auth_site, token
):
    directory, path = auth_site
    before = path.read_bytes()
    with local_php_server(php, directory, token) as port:
        assert_denied(request(port), 503, directory)
        assert_denied(
            request(
                port, headers={"Authorization": "Bearer " + secrets.token_urlsafe(32)}
            ),
            503,
            directory,
        )
    assert path.read_bytes() == before
    assert not path.with_suffix(".json.lock").exists()


@pytest.mark.parametrize(
    "kind",
    [
        "absent",
        "empty",
        "wrong",
        "basic",
        "double-space",
        "comma",
        "oversized",
        "tab",
        "scheme-only",
    ],
)
def test_invalid_client_credentials_are_generic_403(php, auth_site, kind):
    directory, path = auth_site
    token = secrets.token_urlsafe(32)
    values = {
        "empty": "",
        "wrong": "Bearer " + secrets.token_urlsafe(32),
        "basic": "Basic " + token,
        "double-space": "Bearer  " + token,
        "comma": "Bearer " + token + ", Bearer " + token,
        "oversized": "Bearer " + "x" * 513,
        "tab": "Bearer\t" + token,
        "scheme-only": "Bearer",
    }
    headers = {} if kind == "absent" else {"Authorization": values[kind]}
    before = path.read_bytes()
    with local_php_server(php, directory, token) as port:
        assert_denied(request(port, headers=headers), 403, directory)
    assert path.read_bytes() == before
    assert not list(directory.rglob(".netmon-json-*"))


def test_valid_bearer_reads_stats_without_echoing_credentials(php, auth_site):
    directory, path = auth_site
    token = secrets.token_urlsafe(32)
    before = path.read_bytes()
    with local_php_server(php, directory, token) as port:
        status, headers, body = request(
            port, headers={"aUtHoRiZaTiOn": "bEaReR " + token}
        )
    assert status == 200
    assert MARKER.encode() in body and IP_MARKER.encode() in body
    assert "no-store" in headers["cache-control"]
    assert headers["referrer-policy"] == "no-referrer"
    assert token.encode() not in body
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "query",
    [
        "token=",
        "token[]=x",
        "token[deep][a]=x",
        "token=wrong",
        "token=first&token=second",
    ],
)
@pytest.mark.parametrize("with_bearer", [False, True])
def test_url_token_forms_are_not_a_compatibility_bypass(
    php, auth_site, query, with_bearer
):
    directory, _ = auth_site
    token = secrets.token_urlsafe(32)
    headers = {"Authorization": "Bearer " + token} if with_bearer else {}
    with local_php_server(php, directory, token) as port:
        assert_denied(
            request(port, "/download-stats.php?" + query, headers), 403, directory
        )


def test_duplicate_wrong_authorization_headers_do_not_authenticate(php, auth_site):
    directory, _ = auth_site
    token = secrets.token_urlsafe(32)
    with local_php_server(php, directory, token) as port:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            conn.putrequest("GET", "/download-stats.php")
            conn.putheader("Authorization", "Bearer " + secrets.token_urlsafe(32))
            conn.putheader("Authorization", "Bearer " + secrets.token_urlsafe(32))
            conn.endheaders()
            response = conn.getresponse()
            result = (
                response.status,
                {k.lower(): v for k, v in response.getheaders()},
                response.read(),
            )
        finally:
            conn.close()
        assert_denied(result, 403, directory)


@pytest.fixture
def sapi_server(php, auth_site):
    directory, _ = auth_site
    source = (ROOT / "site/download-lib.php").read_text()
    (directory / "sapi-lib.php").write_text(
        source.replace(
            "declare(strict_types=1);",
            "declare(strict_types=1);\nnamespace SapiFixture;",
            1,
        )
    )
    (directory / "sapi.php").write_text("""<?php
namespace SapiFixture;
function getallheaders() { return $GLOBALS["fixture"]["headers"] ?? []; }
require __DIR__ . "/sapi-lib.php";
$fixture = json_decode(file_get_contents("php://input"), true, 16, JSON_THROW_ON_ERROR);
$_SERVER = $fixture["server"] ?? [];
$_GET = $fixture["query"] ?? [];
netmon_require_stats_token($fixture["config"]);
echo "authorized";
""")
    with local_php_server(php, directory, None) as port:
        yield port, directory


def sapi_request(server, payload):
    port, _ = server
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(
            "POST",
            "/sapi.php",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        return (
            response.status,
            {k.lower(): v for k, v in response.getheaders()},
            response.read(),
        )
    finally:
        conn.close()


@pytest.mark.parametrize(
    "value", [None, False, True, 0, 123, [], {}, ["x"], "\x00", "x\r\ny"]
)
def test_unexpected_config_types_fail_closed_without_warnings(sapi_server, value):
    result = sapi_request(sapi_server, {"config": {"stats_token": value}})
    assert_denied(result, 503, sapi_server[1])


@pytest.mark.parametrize(
    "representation",
    [
        "HTTP_AUTHORIZATION",
        "REDIRECT_HTTP_AUTHORIZATION",
        "getallheaders",
        "consistent-all",
    ],
)
def test_supported_sapi_header_representations(sapi_server, representation):
    token = secrets.token_urlsafe(32)
    auth = "Bearer " + token
    payload = {"config": {"stats_token": token}, "server": {}, "headers": {}}
    if representation in ("HTTP_AUTHORIZATION", "REDIRECT_HTTP_AUTHORIZATION"):
        payload["server"][representation] = auth
    elif representation == "getallheaders":
        payload["headers"]["aUtHoRiZaTiOn"] = auth
    else:
        payload["server"] = {
            "HTTP_AUTHORIZATION": auth,
            "REDIRECT_HTTP_AUTHORIZATION": auth,
        }
        payload["headers"]["Authorization"] = auth
    status, headers, body = sapi_request(sapi_server, payload)
    assert status == 200 and body == b"authorized"
    assert "no-store" in headers["cache-control"]


@pytest.mark.parametrize(
    "kind",
    [
        "conflict",
        "empty-primary",
        "array",
        "object",
        "number",
        "control",
        "query-array",
        "spoofed-forwarding",
        "duplicate-case",
    ],
)
def test_manipulated_sapi_values_do_not_authorize(sapi_server, kind):
    token = secrets.token_urlsafe(32)
    auth = "Bearer " + token
    payload = {
        "config": {"stats_token": token},
        "server": {"HTTP_AUTHORIZATION": auth},
        "headers": {},
    }
    if kind == "conflict":
        payload["server"]["REDIRECT_HTTP_AUTHORIZATION"] = (
            "Bearer " + secrets.token_urlsafe(32)
        )
    elif kind == "empty-primary":
        payload["server"] = {
            "HTTP_AUTHORIZATION": "",
            "REDIRECT_HTTP_AUTHORIZATION": auth,
        }
    elif kind in ("array", "object", "number", "control"):
        payload["server"]["HTTP_AUTHORIZATION"] = {
            "array": [auth],
            "object": {"value": auth},
            "number": 0,
            "control": auth + "\r\nX-Test: x",
        }[kind]
    elif kind == "query-array":
        payload["query"] = {"token": [token]}
    elif kind == "spoofed-forwarding":
        payload["server"] = {
            "HTTP_REDIRECT_HTTP_AUTHORIZATION": auth,
            "HTTP_X_AUTHORIZATION": auth,
            "REMOTE_USER": token,
        }
    else:
        payload["headers"] = {
            "Authorization": auth,
            "authorization": "Bearer " + secrets.token_urlsafe(32),
        }
    assert_denied(sapi_request(sapi_server, payload), 403, sapi_server[1])


def test_local_readiness_uses_production_config_in_isolation(php):
    check_local_readiness(php)


def test_readiness_cli_reports_no_production_guarantee(php):
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/check_download_stats_readiness.py"),
            "--php",
            php,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0
    assert "LOCAL ONLY" in result.stdout
    assert not result.stderr


@pytest.mark.parametrize(
    "fault", ["unguarded", "missing-env", "no-client-check", "cache"]
)
def test_readiness_detects_broken_deployment_contract(php, tmp_path, fault):
    for name in ("download-lib.php", "download-config.php", "download-stats.php"):
        shutil.copyfile(ROOT / "site" / name, tmp_path / name)
    if fault == "unguarded":
        path = tmp_path / "download-stats.php"
        path.write_text(
            path.read_text().replace("netmon_require_stats_token($config);", "")
        )
    elif fault == "missing-env":
        path = tmp_path / "download-config.php"
        path.write_text(
            path.read_text().replace('getenv("NETMON_STATS_TOKEN")', "false")
        )
    else:
        path = tmp_path / "download-lib.php"
        source = path.read_text()
        if fault == "cache":
            source = source.replace(
                "no-store, no-cache, must-revalidate, max-age=0", "public"
            )
        else:
            source = source.replace(
                "$provided === null || !hash_equals($token, $provided)", "false"
            )
        path.write_text(source)
    with pytest.raises(ReadinessError):
        check_local_readiness(php, tmp_path)
