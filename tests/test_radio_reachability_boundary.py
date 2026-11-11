"""Reachability status semantics and process boundary, without external network."""

import http.client
import json
import socket
import time
from types import SimpleNamespace

import pytest

from netmon.core import radio_fetch as fetch
from netmon.core import radio_sandbox as sandbox
from netmon.features import radio_controller as radio


@pytest.fixture(autouse=True)
def restore_header_limits(monkeypatch):
    for name in ("_MAXLINE", "_MAXHEADERS"):
        monkeypatch.setattr(http.client, name, getattr(http.client, name))


def response_fixture(monkeypatch, statuses):
    records = []
    monkeypatch.setattr(
        fetch, "resolve_public", lambda *_: [(socket.AF_INET, ("93.184.216.34", 80))]
    )

    def opened(scheme, host, port, plan):
        value = statuses[len(records)]
        record = {"closed": False, "host": host}
        records.append(record)

        def request(method, path, **kwargs):
            record.update(method=method, path=path, **kwargs)

        def getresponse():
            if isinstance(value, Exception):
                raise value
            status, headers = value
            return SimpleNamespace(
                status=status,
                getheader=headers.get,
                read1=lambda *_: pytest.fail("Probe must not read a body"),
                close=lambda: record.update(response_closed=True),
            )

        return SimpleNamespace(
            request=request,
            getresponse=getresponse,
            close=lambda: record.update(closed=True),
        )

    monkeypatch.setattr(fetch, "open_connection", opened)
    return records


@pytest.mark.parametrize("mode", sorted(fetch.PROBE_MODES))
@pytest.mark.parametrize(
    "status", [200, 204, 206, 401, 403, 405, 406, 416, 404, 500, 503]
)
def test_status_mapping_needs_no_body_and_always_closes(monkeypatch, mode, status):
    records = response_fixture(monkeypatch, [(status, {})])
    result = fetch.probe_reachability("https://radio.example/live", mode=mode)
    expected = status in {200, 204, 206, 401, 403, 405, 406} or (
        status == 416 and mode != "probe-source"
    )
    assert result is expected
    assert records[0]["closed"] and records[0]["response_closed"]
    headers = records[0]["headers"]
    assert (headers.get("Range") == "bytes=0-0") is (mode == "probe-station-range")
    assert headers["Icy-MetaData"] == ("1" if mode == "probe-station-range" else "0")
    assert "Authorization" not in headers and "Cookie" not in headers


@pytest.mark.parametrize(
    "line,expected",
    [
        ("ICY 200 OK\r\n", True),
        ("ICY 403 Forbidden", True),
        ("ICY 416 Range", True),
        ("ICY 503 Failed", False),
        ("ICY broken", None),
        ("ICY 200 OK\r\nInjected: bad", None),
        ("HTTP/broken", None),
        ("ICY 999 invalid", None),
    ],
)
def test_legacy_icy_requires_valid_status_and_only_station_probe(
    monkeypatch, line, expected
):
    records = response_fixture(monkeypatch, [http.client.BadStatusLine(line)])
    assert (
        fetch.probe_reachability("http://radio.example/live", mode="probe-station")
        is expected
    )
    assert records[0]["closed"]
    response_fixture(monkeypatch, [http.client.BadStatusLine(line)])
    assert (
        fetch.probe_reachability("http://radio.example/live", mode="probe-source")
        is None
    )


def test_probe_can_check_playlist_headers_without_enabling_playlist_playback(
    monkeypatch,
):
    records = response_fixture(
        monkeypatch,
        [
            (302, {"Location": "/list.m3u8"}),
            (200, {"Content-Type": "application/vnd.apple.mpegurl"}),
        ],
    )
    assert (
        fetch.probe_reachability("https://radio.example/start", mode="probe-source")
        is True
    )
    assert records[1]["path"] == "/list.m3u8"
    with pytest.raises(fetch.SourceError):
        fetch.parse_url("https://radio.example/list.m3u8")


@pytest.mark.parametrize(
    "url",
    ["http://127.0.0.1/private", "file:///etc/passwd", "rtsp://radio.example/live"],
)
def test_disallowed_targets_are_unknown_and_never_connected(monkeypatch, url):
    monkeypatch.setattr(
        fetch.socket,
        "getaddrinfo",
        lambda *_a, **_k: [
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 80))
        ],
    )
    monkeypatch.setattr(
        fetch, "open_connection", lambda *_: pytest.fail("forbidden target connected")
    )
    assert fetch.probe_reachability(url, mode="probe-station") is None


@pytest.mark.parametrize(
    "error,expected",
    [
        (fetch.ConnectionFailure("failed"), False),
        (socket.gaierror(), False),
        (TimeoutError(), False),
        (http.client.RemoteDisconnected(), False),
        (fetch.SourceError("refused"), None),
    ],
)
def test_transport_failure_is_distinct_from_policy_refusal(
    monkeypatch, error, expected
):
    def fail(*_args):
        raise error

    monkeypatch.setattr(fetch, "resolve_public", fail)
    assert (
        fetch.probe_reachability("http://radio.example/live", mode="probe-source")
        is expected
    )


def test_private_redirect_and_tls_downgrade_stay_unknown_before_second_connection(
    monkeypatch,
):
    for target in ("http://radio.example/live", "http://127.0.0.1/private"):
        records = response_fixture(monkeypatch, [(302, {"Location": target})])
        assert (
            fetch.probe_reachability("https://radio.example/live", mode="probe-station")
            is None
        )
        assert len(records) == 1 and records[0]["closed"]


def test_private_redirect_is_revalidated_without_tls_downgrade(monkeypatch):
    resolve = fetch.resolve_public
    records = response_fixture(
        monkeypatch, [(302, {"Location": "https://127.0.0.1/private"})]
    )
    monkeypatch.setattr(fetch, "resolve_public", resolve)
    monkeypatch.setattr(
        fetch.socket,
        "getaddrinfo",
        lambda host, port, **_k: [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                0,
                "",
                ("127.0.0.1" if host == "127.0.0.1" else "93.184.216.34", port),
            )
        ],
    )
    assert (
        fetch.probe_reachability("https://radio.example/live", mode="probe-station")
        is None
    )
    assert len(records) == 1 and records[0]["closed"]


def test_refused_pinned_connection_is_offline_and_closes_sockets(monkeypatch):
    closed = []

    def connect(_address):
        raise ConnectionRefusedError()

    monkeypatch.setattr(
        fetch.socket,
        "socket",
        lambda *_: SimpleNamespace(
            settimeout=lambda _: None,
            connect=connect,
            close=lambda: closed.append(True),
        ),
    )
    monkeypatch.setattr(
        fetch, "resolve_public", lambda *_: [(socket.AF_INET, ("93.184.216.34", 80))]
    )
    assert (
        fetch.probe_reachability("http://radio.example/live", mode="probe-station")
        is False
    )
    assert closed == [True]


def controlled_helper(monkeypatch, tmp_path, program):
    children = []
    real = sandbox.subprocess.Popen
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))

    def command(directory, audio_socket, _stdlib, _runtime):
        request = json.loads((directory / "request.json").read_text())
        assert request == {
            "url": "https://example.com/?private-token",
            "mode": "probe-station-range",
        }
        assert audio_socket is None
        assert (directory / "request.json").stat().st_mode & 0o777 == 0o600
        assert directory.stat().st_mode & 0o777 == 0o700
        return [str(sandbox.PYTHON), "-I", "-S", "-B", "-c", program]

    def spawn(arguments, **kwargs):
        assert "private-token" not in " ".join(arguments)
        assert kwargs["close_fds"] and kwargs["stdin"] == sandbox.subprocess.DEVNULL
        child = real(arguments, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(sandbox, "_fetch_command", command)
    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    return children


@pytest.mark.parametrize("value", [True, False, None])
def test_parent_accepts_tristate_and_reaps_process(monkeypatch, tmp_path, value):
    reply = json.dumps({"reachable": value})
    children = controlled_helper(monkeypatch, tmp_path, f"print({reply!r})")
    assert (
        sandbox.probe_reachability(
            "https://example.com/?private-token",
            station=True,
            ranged=True,
            work_root=tmp_path,
            timeout=1,
        )
        is value
    )
    assert all(child.poll() == 0 and child.stdout.closed for child in children)
    assert not list(tmp_path.glob("probe-*"))


@pytest.mark.parametrize(
    "program",
    [
        'print("not-json")',
        'print("[]")',
        "print('{\"reachable\":1}')",
        'print(\'{"reachable":"yes"}\')',
        'print(\'{"reachable":true,"extra":1}\')',
        'print("X" * 513)',
        "print('{\"reachable\":true}');raise SystemExit(2)",
        "import time;time.sleep(10)",
        "import time;print('{\"reachable\":true}',flush=True);time.sleep(10)",
    ],
)
def test_bad_stalled_or_failed_reply_is_rejected_and_child_reaped(
    monkeypatch, tmp_path, program
):
    children = controlled_helper(monkeypatch, tmp_path, program)
    began = time.monotonic()
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.probe_reachability(
            "https://example.com/?private-token",
            station=True,
            ranged=True,
            work_root=tmp_path,
            timeout=0.15,
        )
    assert time.monotonic() - began < 3
    assert all(child.poll() is not None and child.stdout.closed for child in children)
    assert not list(tmp_path.glob("probe-*"))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"station": 1},
        {"ranged": True},
        {"timeout": 0},
        {"timeout": float("nan")},
        {"timeout": 11},
    ],
)
def test_invalid_request_rejected_before_runtime_preparation(monkeypatch, kwargs):
    monkeypatch.setattr(
        sandbox, "_fetch_runtime", lambda: pytest.fail("preflight reached")
    )
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.probe_reachability("https://example.com/", **kwargs)


@pytest.mark.parametrize(
    "results,expected",
    [
        ([False] * 4, False),
        ([None, False, False, False], None),
        ([None, False, True], True),
    ],
)
def test_controller_keeps_candidate_order_retries_and_tristate_without_urlopen(
    monkeypatch, results, expected
):
    calls = []
    values = iter(results)

    def probe(url, **kwargs):
        calls.append((url, kwargs["ranged"]))
        return next(values)

    monkeypatch.setattr(radio.radio_sandbox, "probe_reachability", probe)
    monkeypatch.setattr(
        radio.urllib.request,
        "urlopen",
        lambda *_a, **_k: pytest.fail("direct network fallback"),
    )
    assert (
        radio._probe_radio_station_reachability(
            {
                "url_resolved": "https://resolved.example/live",
                "url": "https://original.example/live",
            }
        )
        is expected
    )
    assert (
        calls
        == [
            ("https://resolved.example/live", True),
            ("https://resolved.example/live", False),
            ("https://original.example/live", True),
            ("https://original.example/live", False),
        ][: len(results)]
    )


def test_failed_sandbox_stays_unknown_for_source_and_station(monkeypatch):
    def fail(*_a, **_k):
        raise sandbox.RadioSandboxError("unavailable")

    monkeypatch.setattr(radio.radio_sandbox, "probe_reachability", fail)
    monkeypatch.setattr(
        radio.urllib.request,
        "urlopen",
        lambda *_a, **_k: pytest.fail("direct fallback"),
    )
    assert (
        radio._probe_radio_station_reachability({"url": "https://example.com/live"})
        is None
    )
    assert radio._probe_radio_database_source_reachability("radio_browser_api") is None
    assert radio._probe_radio_database_source_reachability("unknown") is None
