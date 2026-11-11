"""Public-target policy, redirect handling and pinned transport; no real network."""

import io
import json
import socket
from types import SimpleNamespace

import pytest

from netmon.core import radio_fetch as fetch

PUBLIC = "93.184.216.34"


@pytest.fixture(autouse=True)
def restore_header_limits(monkeypatch):
    # The production source has its own process; tests must restore the
    # process-global stdlib limits before other modules run in this suite.
    for name in ("_MAXLINE", "_MAXHEADERS"):
        monkeypatch.setattr(fetch.http.client, name, getattr(fetch.http.client, name))


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "rtsp://example.com/live",
        "rtmp://example.com/live",
        "data:audio/wav,abc",
        "http:///missing-host",
        "http://u:p@example.com/s",
        "http://u@example.com/s",
        "http://example.com:0/s",
        "http://example.com:65536/s",
        "http://example.com:x/s",
        "http://[::1%25lo]/s",
        "http://*.example/s",
        "http://example.com/s#part",
        "http://example.com/evil\r\nHost:x",
        " http://example.com/s",
        "http://example.com/white space",
        "",
        "https://example.com/s.m3u8",
        "https://example.com/s.%6d3u",
        "https://example.com/s.pls",
        "https://example.com/s.mpd",
    ],
)
def test_invalid_or_unsupported_source_fails_closed(url):
    with pytest.raises(fetch.SourceError):
        fetch.parse_url(url)


@pytest.mark.parametrize(
    "address",
    [
        "0.0.0.0",
        "127.0.0.1",
        "127.255.255.255",
        "10.1.2.3",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "100.127.255.254",
        "192.0.0.8",
        "192.88.99.1",
        "192.0.2.1",
        "198.18.0.1",
        "198.51.100.1",
        "203.0.113.1",
        "224.0.0.1",
        "255.255.255.255",
        "::",
        "::1",
        "fc00::1",
        "fe80::1",
        "ff02::1",
        "2001:db8::1",
        "::ffff:127.0.0.1",
        "::ffff:8.8.8.8",
        "64:ff9b::a00:1",
        "64:ff9b:1::a00:1",
        "2002:0808:0808::1",
        "2001::1",
        "not-an-address",
    ],
)
def test_local_special_and_transition_addresses_are_denied(address):
    assert not fetch.public_address(address)


@pytest.mark.parametrize("address", [PUBLIC, "8.8.8.8", "2606:4700:4700::1111"])
def test_public_addresses_are_eligible(address):
    assert fetch.public_address(address)


def answer(address, port=80):
    return (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))


@pytest.mark.parametrize(
    "answers", [[], [answer(PUBLIC), answer("127.0.0.1")], [answer(PUBLIC)] * 33]
)
def test_mixed_or_unbounded_dns_plan_is_refused(monkeypatch, answers):
    monkeypatch.setattr(fetch.socket, "getaddrinfo", lambda *_a, **_k: answers)
    with pytest.raises(fetch.SourceError):
        fetch.resolve_public("radio.example", 80)


def test_connect_uses_checked_sockaddr_without_dns_rebinding(monkeypatch):
    calls = []
    transport = SimpleNamespace(
        settimeout=lambda timeout: calls.append(("timeout", timeout)),
        connect=lambda address: calls.append(("connect", address)),
    )
    monkeypatch.setattr(fetch.socket, "socket", lambda *_a: transport)
    monkeypatch.setattr(
        fetch.socket, "getaddrinfo", lambda *_a, **_k: pytest.fail("second DNS lookup")
    )
    assert fetch.connect_pinned([(socket.AF_INET, (PUBLIC, 443))]) is transport
    assert calls == [("timeout", 5), ("connect", (PUBLIC, 443))]


def test_tls_checks_original_hostname_on_pinned_socket(monkeypatch):
    calls = []
    raw = SimpleNamespace(close=lambda: calls.append("raw closed"))
    secured = SimpleNamespace(settimeout=lambda timeout: calls.append(timeout))
    monkeypatch.setattr(fetch, "connect_pinned", lambda plan: raw)

    def context(**kwargs):
        assert kwargs == {"cafile": "/etc/ssl/certs/ca-certificates.crt"}

        def wrap(transport, *, server_hostname):
            assert transport is raw
            assert server_hostname == "radio.example"
            return secured

        return SimpleNamespace(wrap_socket=wrap)

    monkeypatch.setattr(fetch.ssl, "create_default_context", context)
    connection = fetch.open_connection("https", "radio.example", 443, [])
    connection.connect()
    assert connection.sock is secured
    assert calls == [10]


class Response:
    def __init__(self, status=200, headers=None, body=b"AUDIO", length=0):
        self.status = status
        self.headers = headers or {}
        self.body = io.BytesIO(body)
        self.length = length
        self.closed = False

    def getheader(self, name):
        return self.headers.get(name)

    def read1(self, size):
        assert size <= 16384
        return self.body.read(size)

    def close(self):
        self.closed = True


def setup_transfers(monkeypatch, responses):
    connections, resolutions = [], []

    def resolve(host, port, **kwargs):
        resolutions.append((host, port))
        return [answer("127.0.0.1" if host == "127.0.0.1" else PUBLIC, port)]

    monkeypatch.setattr(fetch.socket, "getaddrinfo", resolve)

    def opened(scheme, host, port, plan):
        response = responses[len(connections)]
        record = {"host": host, "scheme": scheme, "closed": False}

        def request(method, path, headers):
            record.update(method=method, path=path, headers=headers)

        def close():
            record["closed"] = True

        connections.append(record)
        return SimpleNamespace(
            request=request, getresponse=lambda: response, close=close
        )

    monkeypatch.setattr(fetch, "open_connection", opened)
    return connections, resolutions


def test_relative_and_cross_host_redirects_revalidate_without_copying_cookies(
    monkeypatch,
):
    responses = [
        Response(302, {"Location": "/new"}),
        Response(
            307, {"Location": "https://cdn.example/live", "Set-Cookie": "secret=x"}
        ),
        Response(),
    ]
    connections, resolutions = setup_transfers(monkeypatch, responses)
    output = io.BytesIO()
    fetch.transfer("https://radio.example/start?token=private", output)
    assert output.getvalue() == b"AUDIO"
    assert resolutions == [
        ("radio.example", 443),
        ("radio.example", 443),
        ("cdn.example", 443),
    ]
    assert connections[1]["path"] == "/new"
    assert all(record["closed"] for record in connections)
    assert all(response.closed for response in responses)
    assert all(
        record["method"] == "GET"
        and "Cookie" not in record["headers"]
        and "Authorization" not in record["headers"]
        for record in connections
    )


def test_icy_mode_requests_metadata_on_each_redirect_and_returns_only_json_title(
    monkeypatch,
):
    metadata = b"StreamTitle='Artist - Track';"
    padded = metadata + b"\0" * (-len(metadata) % 16)
    responses = [
        Response(302, {"Location": "/new"}),
        Response(
            headers={"icy-metaint": "8"},
            body=b"S" * 8 + bytes([len(padded) // 16]) + padded,
        ),
    ]
    connections, _ = setup_transfers(monkeypatch, responses)
    destination = io.BytesIO()
    fetch.transfer("https://radio.example/live", destination, mode="icy")
    assert json.loads(destination.getvalue()) == {"title": "Artist - Track"}
    assert all(
        connection["headers"]["Icy-MetaData"] == "1" for connection in connections
    )
    assert all(response.closed for response in responses)


@pytest.mark.parametrize(
    "target",
    [
        "https://127.0.0.1/private",
        "file:///etc/passwd",
        "http://public.example/live",
        "https://u:p@radio.example/live",
        "\nhttps://radio.example/live",
    ],
)
def test_bad_redirect_is_rejected_before_a_second_connection(monkeypatch, target):
    connections, _resolutions = setup_transfers(
        monkeypatch, [Response(302, {"Location": target})]
    )
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://radio.example/live", io.BytesIO())
    assert len(connections) == 1 and connections[0]["closed"]


def test_redirects_have_a_fixed_bound(monkeypatch):
    responses = [Response(302, {"Location": "/again"}) for _ in range(6)]
    connections, _ = setup_transfers(monkeypatch, responses)
    with pytest.raises(fetch.SourceError, match="redirect"):
        fetch.transfer("http://radio.example/live", io.BytesIO())
    assert len(connections) == 6
    assert all(response.closed for response in responses)


@pytest.mark.parametrize(
    "response",
    [
        Response(503),
        Response(206),
        Response(headers={"Content-Type": "application/vnd.apple.mpegurl"}),
        Response(headers={"Content-Type": "audio/x-scpls; charset=utf-8"}),
        Response(headers={"icy-metaint": "8192"}),
        Response(headers={"Content-Encoding": "gzip"}),
        Response(body=b"", length=100),
    ],
)
def test_http_errors_unsupported_bodies_and_truncation_fail_closed(
    monkeypatch, response
):
    setup_transfers(monkeypatch, [response])
    with pytest.raises(fetch.SourceError):
        fetch.transfer("http://radio.example/live", io.BytesIO())
    assert response.closed


def test_icy_metaint_zero_means_no_interleaved_metadata(monkeypatch):
    # Real rautemusik response: "icy-metaint: 0" with a plain audio body.
    response = Response(headers={"icy-metaint": "0"}, body=b"PLAINAUDIO")
    setup_transfers(monkeypatch, [response])
    output = io.BytesIO()
    fetch.transfer("https://radio.example/live", output)
    assert output.getvalue() == b"PLAINAUDIO"
    assert response.closed


@pytest.mark.parametrize("value", ["00", "1", " 8 ", "-0"])
def test_any_other_metaint_still_refused_in_stream_mode(monkeypatch, value):
    response = Response(headers={"icy-metaint": value})
    setup_transfers(monkeypatch, [response])
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://radio.example/live", io.BytesIO())


# -- G-Quota: self-limits of the fetch helper --------------------------------


@pytest.mark.parametrize(
    "mode,cpu", [("stream", None), ("icy", 30), ("probe-station", 30), ("preset", 120)]
)
def test_fetch_helper_limits_itself_before_network(mode, cpu):
    import subprocess
    import sys
    from pathlib import Path

    script = f"""
import json, os, resource, threading
from netmon.core import radio_fetch
radio_fetch.apply_process_limits({mode!r})
limits = {{n: resource.getrlimit(getattr(resource, n))[1] for n in
          ("RLIMIT_AS", "RLIMIT_NOFILE", "RLIMIT_FSIZE", "RLIMIT_CORE",
           "RLIMIT_NPROC", "RLIMIT_CPU")}}
try:
    threading.Thread(target=lambda: None).start(); thread = "started"
except RuntimeError:
    thread = "refused"
try:
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0); fork = "started"
except OSError:
    fork = "refused"
print(json.dumps({{"limits": limits, "thread": thread, "fork": fork}}))
"""
    out = subprocess.run(
        [sys.executable, "-B", "-X", "pycache_prefix=/nonexistent", "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    ).stdout
    result = json.loads(out)
    limits = result["limits"]
    assert limits["RLIMIT_AS"] <= 256 * 1024 * 1024
    assert limits["RLIMIT_NOFILE"] <= 64
    assert limits["RLIMIT_FSIZE"] <= 1024 * 1024
    assert limits["RLIMIT_CORE"] == 0 and limits["RLIMIT_NPROC"] == 0
    if cpu is None:
        assert limits["RLIMIT_CPU"] == -1  # streams: bounded by the scope quota
    else:
        assert 0 < limits["RLIMIT_CPU"] <= cpu
    assert result["thread"] == "refused" and result["fork"] == "refused"


def test_fetch_main_applies_limits_before_any_network_call():
    import ast
    import inspect

    body = ast.parse(inspect.getsource(fetch.main)).body[0].body[0].body
    names = [
        node.value.func.id
        for node in ast.walk(ast.Module(body=body, type_ignores=[]))
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
    ]
    assert names[0] == "apply_process_limits"
    assert names.index("apply_process_limits") < names.index("transfer")
