"""ICY parser bounds, bounded process replies and stale callback rejection."""

import io
import json
import threading
from types import SimpleNamespace
import time

import pytest

from netmon.core import radio_fetch as fetch
from netmon.core import radio_sandbox as sandbox
from netmon.features import radio_controller as radio


@pytest.mark.parametrize("source", ["radio", "local"])
def test_metadata_worker_starts_only_after_queued_player_publication(
    monkeypatch, tmp_path, source
):
    callbacks, observed = [], []
    process = object()
    station = {
        "id": "station-1",
        "name": "Station 1",
        "url": "https://example.com/live.mp3",
    }
    app = SimpleNamespace(
        radio_proc=None,
        radio_current_station_id="old",
        radio_volume_var=SimpleNamespace(get=lambda: 50),
    )

    monitoring, release, metadata = (
        threading.Event(),
        threading.Event(),
        threading.Event(),
    )

    def monitor(*_args):
        monitoring.set()
        assert release.wait(3)

    monkeypatch.setattr(radio, "_wait_for_radio_process", monitor)
    monkeypatch.setattr(radio, "radio_available", lambda _: True)
    monkeypatch.setattr(radio, "_resolve_target_station", lambda *a, **k: station)
    monkeypatch.setattr(radio, "_start_radio_playback", lambda *a, **k: process)
    monkeypatch.setattr(
        radio, "_schedule_ui", lambda _, callback: callbacks.append(callback) or True
    )
    monkeypatch.setattr(
        radio,
        "_poll_radio_metadata",
        lambda target, child: observed.append(
            (target.radio_proc is child, target.radio_current_station_id)
        )
        or metadata.set(),
    )
    for name in (
        "stop_radio_playback",
        "_cleanup_radio_ipc_path",
        "save_radio_settings",
        "update_radio_header",
        "refresh_radio_station_table",
        "refresh_radio_favorites_list",
        "refresh_radio_source_ui",
        "_set_radio_light",
        "_set_radio_station_text",
        "set_radio_status",
        "_set_radio_title_text",
    ):
        monkeypatch.setattr(radio, name, lambda *a, **k: None)
    if source == "radio":
        assert radio.play_radio_station(app, "station-1")
    else:
        path = tmp_path / "selected.wav"
        path.write_bytes(b"synthetic selected file")
        assert radio._play_local_audio_file(
            app, str(path), station_name="Local", title_text="Local title"
        )
    try:
        assert monitoring.wait(2)
        assert observed == [], "metadata ran before the queued player existed in the UI"
        for callback in list(callbacks):
            callback()
        assert metadata.wait(2)
        assert observed == [(True, "station-1" if source == "radio" else "")]
    finally:
        release.set()
        assert app.radio_playback_request.done.wait(2)


class Response:
    def __init__(self, body, interval="8", fragment=3):
        self.body = io.BytesIO(body)
        self.interval = interval
        self.fragment = fragment
        self.read_bytes = 0

    def getheader(self, key):
        assert key == "icy-metaint"
        return self.interval

    def read1(self, size):
        assert 0 < size <= 4096
        value = self.body.read(min(size, self.fragment))
        self.read_bytes += len(value)
        return value


def packet(title):
    text = f"StreamTitle='{title}';".encode("utf-8")
    padded = text + b"\0" * (-len(text) % 16)
    return b"S" * 8 + bytes([len(padded) // 16]) + padded


def test_partial_reads_are_assembled_and_only_first_metadata_block_is_used():
    response = Response(packet("Artist - Track") + b"unread audio", fragment=1)
    assert fetch.read_icy_title(response) == "Artist - Track"
    assert response.read_bytes == len(packet("Artist - Track"))


def test_title_text_has_character_limit_and_no_control_or_bidi_characters():
    title = fetch.read_icy_title(Response(packet("A\n\x00\u202eB " + "X" * 1000)))
    assert title.startswith("A B ")
    assert len(title) == 512
    assert all(char.isprintable() for char in title)


@pytest.mark.parametrize("interval", ["-1", "0", "1x", "10000000", "1048577", "1 ", ""])
def test_invalid_interval_rejected_before_body_read(interval):
    response = Response(b"must not read", interval)
    with pytest.raises(fetch.SourceError):
        fetch.read_icy_title(response)
    assert response.read_bytes == 0


@pytest.mark.parametrize("body", [b"short", b"S" * 8, b"S" * 8 + b"\x02short"])
def test_truncated_audio_length_or_metadata_is_rejected(body):
    with pytest.raises(fetch.SourceError):
        fetch.read_icy_title(Response(body))


def test_absent_or_empty_metadata_returns_no_title():
    no_header = Response(b"unread audio", None)
    assert fetch.read_icy_title(no_header) == ""
    assert no_header.read_bytes == 0
    assert fetch.read_icy_title(Response(b"S" * 8 + b"\0")) == ""


def controlled_helper(monkeypatch, tmp_path, program):
    children = []
    real = sandbox.subprocess.Popen
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))

    def command(directory, _socket, _stdlib, _runtime):
        request = json.loads((directory / "request.json").read_text())
        assert request["mode"] == "icy"
        assert (directory / "request.json").stat().st_mode & 0o777 == 0o600
        return [str(sandbox.PYTHON), "-I", "-S", "-B", "-c", program]

    def spawn(arguments, **kwargs):
        assert "private-token" not in " ".join(arguments)
        assert kwargs["close_fds"]
        child = real(arguments, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(sandbox, "_fetch_command", command)
    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    return children


def test_parent_accepts_only_title_and_cleans_private_session(monkeypatch, tmp_path):
    children = controlled_helper(
        monkeypatch, tmp_path, 'print(\'{"title":"Artist - Track"}\')'
    )
    assert (
        sandbox.fetch_icy_title(
            "https://example.com/?private-token", timeout=1, work_root=tmp_path
        )
        == "Artist - Track"
    )
    assert all(child.poll() == 0 for child in children)
    assert not list(tmp_path.glob("icy-*"))


@pytest.mark.parametrize(
    "reply",
    [
        "[]",
        "not-json",
        '{"title":true}',
        '{"title":"x","extra":1}',
        json.dumps({"title": "X" * 513}),
        json.dumps({"title": "line\nbreak"}),
    ],
)
def test_parent_rejects_malformed_or_unbounded_reply(monkeypatch, tmp_path, reply):
    children = controlled_helper(monkeypatch, tmp_path, f"print({reply!r})")
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.fetch_icy_title("https://example.com/s", timeout=1, work_root=tmp_path)
    assert all(child.poll() is not None for child in children)
    assert not list(tmp_path.glob("icy-*"))


@pytest.mark.parametrize(
    "program",
    [
        'print(\'{"title":"spoof"}\'); raise SystemExit(2)',
        "import sys; sys.stdout.write('X' * 1000000)",
        "import time; time.sleep(10)",
    ],
)
def test_failure_flood_and_stall_reject_and_reap_helper(monkeypatch, tmp_path, program):
    children = controlled_helper(monkeypatch, tmp_path, program)
    started = time.monotonic()
    with pytest.raises(sandbox.RadioSandboxError):
        sandbox.fetch_icy_title(
            "https://example.com/s", timeout=0.15, work_root=tmp_path
        )
    assert time.monotonic() - started < 2
    assert all(child.poll() is not None for child in children)
    assert not list(tmp_path.glob("icy-*"))


def test_controller_failure_has_no_direct_urlopen_fallback(monkeypatch):
    def reject(*_args, **_kwargs):
        raise sandbox.RadioSandboxError("blocked")

    monkeypatch.setattr(sandbox, "fetch_icy_title", reject)
    monkeypatch.setattr(
        radio.urllib.request,
        "urlopen",
        lambda *_a, **_k: pytest.fail("direct network fallback"),
    )
    assert radio._fetch_icy_stream_title("https://example.com/s") == ""


@pytest.mark.parametrize("metadata", [True, False])
def test_oversized_url_refused_before_runtime_or_request_file(
    monkeypatch, tmp_path, metadata
):
    monkeypatch.setattr(sandbox, "available", lambda: True)
    monkeypatch.setattr(
        sandbox, "_fetch_runtime", lambda: pytest.fail("runtime prepared")
    )
    monkeypatch.setattr(sandbox, "_open_output", lambda: pytest.fail("output opened"))
    url = "https://example.com/" + "X" * 8192
    with pytest.raises(sandbox.RadioSandboxError):
        if metadata:
            sandbox.fetch_icy_title(url, work_root=tmp_path)
        else:
            sandbox.start_playback(
                ["mpv", f"--input-ipc-server={sandbox.IPC_PATH}", "--", url],
                ipc_root=tmp_path,
            )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("pipe_title", ["fd://0", "0"])
def test_pipe_title_does_not_suppress_icy_fallback(monkeypatch, pipe_title):
    app = SimpleNamespace(
        radio_current_station={"url": "https://example.com/s"},
        radio_proc=SimpleNamespace(_source_process=object()),
    )
    monkeypatch.setattr(
        radio,
        "_query_mpv_property",
        lambda _app, name: pipe_title if name.startswith("media-title") else "",
    )
    monkeypatch.setattr(radio, "_fetch_icy_stream_title", lambda _url: "Actual title")
    assert radio._read_radio_stream_title(app)[0] == "Actual title"


def test_real_zero_metadata_title_is_preserved(monkeypatch):
    app = SimpleNamespace(radio_proc=SimpleNamespace(_source_process=object()))
    monkeypatch.setattr(
        radio,
        "_query_mpv_property",
        lambda _app, name: {"title": "0"} if name == "metadata" else "",
    )
    monkeypatch.setattr(
        radio, "_fetch_icy_stream_title", lambda _url: pytest.fail("real title ignored")
    )
    assert radio._read_radio_stream_title(app)[0] == "0"


@pytest.mark.parametrize("switch_before_queue", [True, False])
def test_old_metadata_cannot_update_a_new_playback(monkeypatch, switch_before_queue):
    old, new = object(), object()
    app = SimpleNamespace(radio_proc=old, tr=lambda _key, default=None: default)
    queued, titles = [], []

    def read(_app):
        if switch_before_queue:
            app.radio_proc = new
        return "Old title", {}

    def queue(_app, callback):
        queued.append(callback)
        app.radio_proc = new

    monkeypatch.setattr(radio, "_read_radio_stream_title", read)
    monkeypatch.setattr(radio, "_schedule_ui", queue)
    monkeypatch.setattr(
        radio, "_set_radio_title_text", lambda _app, text: titles.append(text)
    )
    monkeypatch.setattr(radio.time, "sleep", lambda _seconds: None)
    radio._poll_radio_metadata(app, old)
    for callback in queued:
        callback()
    assert not titles
    assert bool(queued) != switch_before_queue
