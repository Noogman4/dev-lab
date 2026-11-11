"""Protected preset download; ZIP parsing deliberately remains a later boundary."""

from email.message import Message
import io
import json
import socket
import time

import pytest

from netmon.core import projectm_archive as archive
from netmon.core import radio_fetch as fetch
from netmon.core import radio_sandbox as sandbox


@pytest.fixture(autouse=True)
def restore_header_limits(monkeypatch):
    for name in ("_MAXLINE", "_MAXHEADERS"):
        monkeypatch.setattr(fetch.http.client, name, getattr(fetch.http.client, name))


class Response:
    def __init__(self, body=b"ZIP BYTES", *, status=200, headers=(), length=None):
        self.body = io.BytesIO(body)
        self.status = status
        self.headers = Message()
        self.length = length
        self.closed = False
        for key, value in headers:
            self.headers[key] = value

    def getheader(self, key):
        return self.headers.get(key)

    def read1(self, size):
        assert 0 < size <= 16384
        assert self.status == 200, "redirect body consumed"
        data = self.body.read(size)
        if self.length is not None:
            self.length -= len(data)
        return data

    def close(self):
        self.closed = True


def connections(monkeypatch, responses):
    records = []
    monkeypatch.setattr(
        fetch.socket,
        "getaddrinfo",
        lambda host, port, **_kw: [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                0,
                "",
                ("127.0.0.1" if host == "127.0.0.1" else "93.184.216.34", port),
            )
        ],
    )

    def opened(scheme, host, port, plan, **kwargs):
        response = responses[len(records)]
        record = {"host": host, "scheme": scheme, **kwargs}
        records.append(record)

        def request(method, path, **kwargs):
            record.update(method=method, path=path, **kwargs)

        return type(
            "Connection",
            (),
            {
                "request": staticmethod(request),
                "getresponse": staticmethod(lambda: response),
                "close": staticmethod(lambda: record.update(closed=True)),
            },
        )()

    monkeypatch.setattr(fetch, "open_connection", opened)
    return records


def test_preset_redirects_are_fresh_pinned_requests_without_body_reads(monkeypatch):
    responses = [
        Response(
            b"UNREAD",
            status=302,
            headers=[("Location", "https://cdn.example/pack#part")],
        ),
        Response(length=9, headers=[("Content-Length", "9")]),
    ]
    records = connections(monkeypatch, responses)
    output = io.BytesIO()
    fetch.transfer("https://example.com/a", output, mode="preset", idle_timeout=45)
    assert output.getvalue() == b"ZIP BYTES"
    assert records[1]["path"] == "/pack"
    assert all(
        r["headers"]["Accept"] == "application/zip"
        and r["headers"]["Accept-Encoding"] == "identity"
        and r["idle_timeout"] == 45
        and r["closed"]
        for r in records
    )
    assert all(
        "Cookie" not in r["headers"] and "Authorization" not in r["headers"]
        for r in records
    )


@pytest.mark.parametrize(
    "headers",
    [
        [("Content-Length", "268435457")],
        [("Content-Length", "x")],
        [("Content-Length", "9"), ("Content-Length", "9")],
        [("Content-Length", "9"), ("Transfer-Encoding", "chunked")],
        [("Content-Encoding", "gzip")],
        [("icy-metaint", "8")],
    ],
)
def test_preset_response_framing_and_early_limits_fail_closed(monkeypatch, headers):
    response = Response(headers=headers)
    connections(monkeypatch, [response])
    output = io.BytesIO()
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://example.com/pack", output, mode="preset")
    assert output.getvalue() == b"" and response.closed


def test_real_body_bytes_and_incomplete_length_are_checked(monkeypatch):
    monkeypatch.setattr(fetch, "MAX_PRESET_BODY_BYTES", 4)
    connections(monkeypatch, [Response(b"12345")])
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://example.com/pack", io.BytesIO(), mode="preset")
    connections(monkeypatch, [Response(b"abc", length=4)])
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://example.com/pack", io.BytesIO(), mode="preset")


@pytest.mark.parametrize(
    "target",
    [
        "http://example.com/pack",
        "https://127.0.0.1/pack",
        "file:///etc/passwd",
        "https://example.com/back\\slash",
        "https://user:pass@example.com/a",
    ],
)
def test_bad_redirect_never_opens_second_connection(monkeypatch, target):
    records = connections(
        monkeypatch, [Response(status=302, headers=[("Location", target)])]
    )
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://example.com/a", io.BytesIO(), mode="preset")
    assert len(records) == 1 and records[0]["closed"]


def test_redirect_loop_rejected_on_first_repeat(monkeypatch):
    records = connections(
        monkeypatch, [Response(status=302, headers=[("Location", "/a")])]
    )
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://example.com/a", io.BytesIO(), mode="preset")
    assert len(records) == 1


def controlled_source(monkeypatch, tmp_path, program):
    children = []
    real = sandbox.subprocess.Popen
    monkeypatch.setattr(sandbox.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))

    def command(directory, _audio, _stdlib, _runtime):
        request = json.loads((directory / "request.json").read_text())
        assert (
            request["mode"] == "preset"
            and request["url"] == "https://example.com/?private-token"
        )
        assert (directory / "request.json").stat().st_mode & 0o777 == 0o600
        assert _audio is None
        return [str(sandbox.PYTHON), "-I", "-S", "-B", "-c", program]

    def spawn(args, **kwargs):
        assert kwargs["close_fds"] and "private-token" not in " ".join(args)
        child = real(args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(sandbox, "_fetch_command", command)
    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    return children


def test_parent_streams_bounded_chunks_and_handles_short_file_writes(
    monkeypatch, tmp_path
):
    children = controlled_source(
        monkeypatch, tmp_path, "import os;os.write(1,b'abcdef')"
    )

    class ShortWriter(io.BytesIO):
        def write(self, data):
            return super().write(data[:2])

    output = ShortWriter()
    assert (
        sandbox.fetch_preset_archive(
            "https://example.com/?private-token", output, timeout=1, limit=6
        )
        == 6
    )
    assert output.getvalue() == b"abcdef"
    assert all(child.poll() == 0 and child.stdout.closed for child in children)
    assert not list(tmp_path.glob("preset-source-*"))


@pytest.mark.parametrize(
    "program",
    [
        "import os;os.write(1,b'X'*11)",
        "import os;os.write(1,b'abc');raise SystemExit(2)",
        "import time;time.sleep(10)",
        "import os,time;os.write(1,b'abc');os.close(1);time.sleep(10)",
    ],
)
def test_parent_rejects_overrun_failure_and_stalls_and_reaps(
    monkeypatch, tmp_path, program
):
    children = controlled_source(monkeypatch, tmp_path, program)
    began = time.monotonic()
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.fetch_preset_archive(
            "https://example.com/?private-token",
            io.BytesIO(),
            limit=10,
            timeout=0.2,
            total_timeout=0.3,
        )
    assert time.monotonic() - began < 3
    assert all(child.poll() is not None and child.stdout.closed for child in children)
    assert not list(tmp_path.glob("preset-source-*"))


def test_write_failure_reaps_source(monkeypatch, tmp_path):
    children = controlled_source(
        monkeypatch, tmp_path, "import os,time;os.write(1,b'abcdef');time.sleep(10)"
    )

    class BrokenWriter:
        def write(self, _data):
            return 0

    with pytest.raises(OSError):
        sandbox.fetch_preset_archive(
            "https://example.com/?private-token", BrokenWriter(), timeout=1
        )
    assert all(child.poll() is not None for child in children)


def test_regular_partial_data_does_not_extend_total_deadline(monkeypatch, tmp_path):
    children = controlled_source(
        monkeypatch,
        tmp_path,
        "import os,time\nfor _ in range(100):\n os.write(1,b'x');time.sleep(.05)",
    )
    output = io.BytesIO()
    began = time.monotonic()
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.fetch_preset_archive(
            "https://example.com/?private-token",
            output,
            timeout=0.4,
            total_timeout=0.5,
            limit=1000,
        )
    assert time.monotonic() - began < 2
    assert 0 < len(output.getvalue()) < 100
    assert all(child.poll() is not None for child in children)


@pytest.mark.parametrize("failure", [None, "source", "import"])
def test_protected_context_is_private_and_always_cleaned_without_legacy_fallback(
    monkeypatch, tmp_path, failure
):
    monkeypatch.setattr(archive.tempfile, "tempdir", str(tmp_path))
    monkeypatch.setattr(
        archive,
        "download_preset_archive",
        lambda *_a, **_k: pytest.fail("legacy fallback"),
    )

    def source(url, destination, **kwargs):
        assert url == "https://example.com/pack"
        assert kwargs == {
            "timeout": 45,
            "total_timeout": 300,
            "limit": archive.MAX_DOWNLOAD_BYTES,
        }
        destination.write(b"raw untrusted ZIP")
        if failure == "source":
            raise sandbox.RadioSandboxError("failed")

    monkeypatch.setattr(sandbox, "fetch_preset_archive", source)
    try:
        with archive.download_protected_preset_archive(
            "https://example.com/pack#part", timeout=45
        ) as path:
            assert failure != "source"
            from pathlib import Path

            assert Path(path).read_bytes() == b"raw untrusted ZIP"
            assert Path(path).stat().st_mode & 0o777 == 0o600
            if failure == "import":
                raise ValueError("bad ZIP")
    except (sandbox.RadioSandboxError, ValueError):
        assert failure is not None
    else:
        assert failure is None
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))
