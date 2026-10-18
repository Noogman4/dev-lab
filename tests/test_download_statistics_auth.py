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
// Explicit raw-query metadata for normal simulated SAPI requests. Tests can
// suppress this default to exercise a missing QUERY_STRING representation.
if (!($fixture["missing_query_metadata"] ?? false)) {
    $_SERVER += ["QUERY_STRING" => ""];
}
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


def test_r1_exact_max_input_vars_boundary_rejects_truncated_url_token(php, auth_site):
    directory, path = auth_site
    token = secrets.token_urlsafe(32)
    # The 1001st key must not need to survive PHP's automatic input parsing.
    query = "&".join(f"p{i}=x" for i in range(1000)) + "&token=synthetic-url-token"
    (directory / "input-probe.php").write_text("""<?php
header("Content-Type: application/json");
echo json_encode(["limit" => (int) ini_get("max_input_vars"),
    "count" => count($_GET), "parsed_token" => array_key_exists("token", $_GET),
    "raw_token" => strpos($_SERVER["QUERY_STRING"], "token=") !== false]);
""")
    before = path.read_bytes()
    with local_php_server(php, directory, token, max_input_vars=1000) as port:
        proof = json.loads(request(port, "/input-probe.php?" + query)[2])
        assert proof == {
            "limit": 1000,
            "count": 1000,
            "parsed_token": False,
            "raw_token": True,
        }
        assert_denied(
            request(
                port,
                "/download-stats.php?" + query,
                {"Authorization": "Bearer " + token},
            ),
            403,
            directory,
        )
    assert path.read_bytes() == before
    assert not path.with_suffix(".json.lock").exists()


@pytest.mark.parametrize("limit", [1, 10, 1000])
@pytest.mark.parametrize("position", ["first", "middle", "last"])
def test_r1_token_positions_cannot_hide_behind_input_limit(
    php, auth_site, limit, position
):
    directory, _ = auth_site
    token = secrets.token_urlsafe(32)
    pairs = [f"p{i}=x" for i in range(limit)]
    pairs.insert(
        {"first": 0, "middle": limit // 2, "last": limit}[position],
        "token=synthetic-url-token",
    )
    with local_php_server(php, directory, token, max_input_vars=limit) as port:
        assert_denied(
            request(
                port,
                "/download-stats.php?" + "&".join(pairs),
                {"Authorization": "Bearer " + token},
            ),
            403,
            directory,
        )


@pytest.mark.parametrize(
    "query",
    [
        "token=first&token=second",
        "%74oken=x",
        "to%6ben=x",
        "%2574oken=x",
        "token%5B%5D=x",
        "token%00=x",
        "token%20=x",
        "token[]=x",
        "t=1;token=x",
        "t=1%3Btoken=x",
        "t=1%26token=x",
        "t=1&&token=x",
        "t=1&%74oken=x",
        "TOKEN=x",
        "t=1&t=2",
        "t%3D1",
        "t=%31",
        "t=+1",
        "t=1&",
        "t=1;",
        "t=",
        "t[]=1",
        "t=1%00",
        "%",
        "t=1%0A",
        "t=" + "1" * 21,
        "x=" + "a" * 6000,
    ],
)
@pytest.mark.parametrize("separator", ["&", "&;"])
def test_r1_encoded_ambiguous_and_long_queries_fail_closed(
    php, auth_site, query, separator
):
    directory, _ = auth_site
    token = secrets.token_urlsafe(32)
    with local_php_server(php, directory, token, arg_separator=separator) as port:
        assert_denied(
            request(
                port,
                "/download-stats.php?" + query,
                {"Authorization": "Bearer " + token},
            ),
            403,
            directory,
        )


@pytest.mark.parametrize("limit", [1, 10, 1000])
@pytest.mark.parametrize("query", ["", "t=1", "t=1720000000000", "t=" + "9" * 20])
def test_r1_supported_queries_retain_bearer_requirement(php, auth_site, limit, query):
    directory, path = auth_site
    token = secrets.token_urlsafe(32)
    before = path.read_bytes()
    url = "/download-stats.php" + ("?" + query if query else "")
    with local_php_server(php, directory, token, max_input_vars=limit) as port:
        assert_denied(request(port, url), 403, directory)
        assert_denied(
            request(
                port, url, {"Authorization": "Bearer " + secrets.token_urlsafe(32)}
            ),
            403,
            directory,
        )
        status, headers, body = request(port, url, {"Authorization": "Bearer " + token})
        assert status == 200
        assert MARKER.encode() in body and IP_MARKER.encode() in body
        assert "no-store" in headers["cache-control"]
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "raw", [None, False, [], {}, 123, "t=1&token=x", "t=" + "1" * 100000]
)
def test_r1_invalid_raw_query_metadata_is_denied(sapi_server, raw):
    token = secrets.token_urlsafe(32)
    payload = {
        "config": {"stats_token": token},
        "server": {"HTTP_AUTHORIZATION": "Bearer " + token, "QUERY_STRING": raw},
    }
    assert_denied(sapi_request(sapi_server, payload), 403, sapi_server[1])


@pytest.mark.parametrize(
    "uri", [None, False, "", "/sapi.php?token=x", "/sapi.php??", "/" + "x" * 2048]
)
def test_r1_missing_raw_query_requires_unambiguous_request_uri(sapi_server, uri):
    token = secrets.token_urlsafe(32)
    payload = {
        "config": {"stats_token": token},
        "missing_query_metadata": True,
        "server": {"HTTP_AUTHORIZATION": "Bearer " + token, "REQUEST_URI": uri},
    }
    assert_denied(sapi_request(sapi_server, payload), 403, sapi_server[1])


@pytest.mark.parametrize(
    "raw,uri,query",
    [
        ("", "/sapi.php?token=x", {}),
        ("t=1", "/sapi.php?t=1&token=x", {"t": "1"}),
        ("t=1", "/sapi.php", {"t": "1"}),
        ("", "/sapi.php#token=x", {}),
        ("", [], {}),
        ("", "/sapi.php\x00", {}),
    ],
)
def test_r1_conflicting_request_metadata_is_denied(sapi_server, raw, uri, query):
    token = secrets.token_urlsafe(32)
    payload = {
        "config": {"stats_token": token},
        "query": query,
        "server": {
            "HTTP_AUTHORIZATION": "Bearer " + token,
            "QUERY_STRING": raw,
            "REQUEST_URI": uri,
        },
    }
    assert_denied(sapi_request(sapi_server, payload), 403, sapi_server[1])


@pytest.mark.parametrize("with_query", [False, True])
def test_r1_consistent_request_metadata_is_accepted(sapi_server, with_query):
    token = secrets.token_urlsafe(32)
    payload = {
        "config": {"stats_token": token},
        "query": {"t": "1"} if with_query else {},
        "server": {
            "HTTP_AUTHORIZATION": "Bearer " + token,
            "QUERY_STRING": "t=1" if with_query else "",
            "REQUEST_URI": "/sapi.php?t=1" if with_query else "/sapi.php",
        },
    }
    status, _, body = sapi_request(sapi_server, payload)
    assert status == 200 and body == b"authorized"


@pytest.mark.parametrize(
    "url", ["/download-stats.php", "/download-stats.php?", "/download-stats.php?t=123"]
)
@pytest.mark.parametrize(
    "credentials", ["valid", "missing-client", "wrong-client", "missing-server"]
)
def test_f1_actual_http_empty_query_and_bearer_contract(
    php, auth_site, url, credentials
):
    directory, path = auth_site
    page = directory / "download-stats.php"
    # Observe the real request in the copied page, before its original guard.
    # No Authorization/environment values are captured or returned.
    probe = """file_put_contents(__DIR__ . "/request-metadata.json", json_encode([
        "query_present" => array_key_exists("QUERY_STRING", $_SERVER),
        "query" => $_SERVER["QUERY_STRING"] ?? null,
        "uri" => $_SERVER["REQUEST_URI"], "get" => $_GET]));"""
    page.write_text(
        page.read_text().replace(
            "declare(strict_types=1);", "declare(strict_types=1);\n" + probe, 1
        )
    )
    token = secrets.token_urlsafe(32)
    headers = (
        {}
        if credentials == "missing-client"
        else {
            "Authorization": "Bearer "
            + (secrets.token_urlsafe(32) if credentials == "wrong-client" else token)
        }
    )
    before = path.read_bytes()
    with local_php_server(
        php, directory, None if credentials == "missing-server" else token
    ) as port:
        response = request(port, url, headers)
    metadata = json.loads((directory / "request-metadata.json").read_text())
    assert metadata == {
        "query_present": url.endswith("t=123"),
        "query": "t=123" if url.endswith("t=123") else None,
        "uri": url,
        "get": {"t": "123"} if url.endswith("t=123") else [],
    }
    if credentials == "valid":
        status, response_headers, body = response
        assert status == 200
        assert MARKER.encode() in body and IP_MARKER.encode() in body
        assert "no-store" in response_headers["cache-control"]
    else:
        assert_denied(
            response, 503 if credentials == "missing-server" else 403, directory
        )
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "suffix",
    [
        "?token=abc",
        "??token=abc",
        "??",
        "???",
        "?t=123?",
        "?t=123?token=abc",
        "?%3F",
        "?&",
        "?=",
        "?%00",
    ],
)
def test_f1_actual_http_nonempty_or_multiple_query_markers_are_denied(
    php, auth_site, suffix
):
    directory, _ = auth_site
    token = secrets.token_urlsafe(32)
    with local_php_server(php, directory, token) as port:
        assert_denied(
            request(
                port,
                "/download-stats.php" + suffix,
                {"Authorization": "Bearer " + token},
            ),
            403,
            directory,
        )


@pytest.mark.parametrize("query_present", [False, True])
@pytest.mark.parametrize("uri", ["/sapi.php", "/sapi.php?"])
def test_f1_empty_query_sapi_representations(sapi_server, query_present, uri):
    token = secrets.token_urlsafe(32)
    server = {"HTTP_AUTHORIZATION": "Bearer " + token, "REQUEST_URI": uri}
    if query_present:
        server["QUERY_STRING"] = ""
    payload = {
        "config": {"stats_token": token},
        "missing_query_metadata": True,
        "server": server,
    }
    status, _, body = sapi_request(sapi_server, payload)
    assert status == 200 and body == b"authorized"


@pytest.mark.parametrize(
    "uri,parsed",
    [
        ("/sapi.php?t=123", {}),
        ("/sapi.php??", {}),
        ("/sapi.php??token=abc", {}),
        ("/sapi.php?token=abc", {}),
        ("/sapi.php?", {"t": "123"}),
        ("/" + "x" * 2047 + "?", {}),
    ],
)
def test_f1_missing_query_does_not_override_content_or_budget(sapi_server, uri, parsed):
    token = secrets.token_urlsafe(32)
    payload = {
        "config": {"stats_token": token},
        "query": parsed,
        "missing_query_metadata": True,
        "server": {"HTTP_AUTHORIZATION": "Bearer " + token, "REQUEST_URI": uri},
    }
    assert_denied(sapi_request(sapi_server, payload), 403, sapi_server[1])
