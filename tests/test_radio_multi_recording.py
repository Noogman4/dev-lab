"""Concurrent private recording files, fail-closed preflight and bounded metadata."""

import io
import json
import os
from pathlib import Path
import threading
import time
from types import SimpleNamespace

import pytest

from netmon.core import radio_fetch as fetch, radio_sandbox as sandbox
from netmon.core import radio_multi_recording as multi
from netmon.core.utils import protect_user_json_writes


def station(number):
    return {
        "id": f"sender-{number}",
        "name": f"Sender {number}",
        "url": f"https://example.invalid/{number}",
        "bitrate": 128,
    }


def wait_for(predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < deadline, "recording state did not settle"
        time.sleep(0.01)


class FakeRecording:
    def __init__(self, url, path, *, slow=False, fail_after=None):
        self.output_path = str(path)
        self.started = time.monotonic()
        self.result = None
        self.closed = False
        self.slow = slow
        self.fail_after = fail_after
        self.title = url.rsplit("/", 1)[1]
        self.sent = False
        Path(path).write_bytes(b"synthetic MP3")
        Path(path).chmod(0o600)

    def poll(self):
        if (
            self.fail_after is not None
            and time.monotonic() - self.started >= self.fail_after
        ):
            self.result = 2
        return self.result

    def progress(self):
        elapsed = time.monotonic() - self.started
        return (0 if self.slow else elapsed), int(elapsed * 24000)

    def take_titles(self):
        if self.sent:
            return []
        self.sent = True
        return ["Künstler – Titel " + self.title]

    def terminate(self):
        self.closed = True
        if self.result is None:
            self.result = 0
        with open(self.output_path, "ab") as handle:
            handle.write(b";flushed")

    def kill(self):
        self.result = -9
        self.closed = True

    def wait(self, timeout=None):
        assert self.result is not None
        return self.result


@pytest.fixture
def mode_factory():
    modes = []

    def make(count=2, *, starter=None):
        processes = []

        def start(url, path, **kwargs):
            assert kwargs["metadata"] is True
            proc = FakeRecording(url, path)
            processes.append(proc)
            return proc

        mode = multi.MultiRecording(start=starter or start, check_seconds=0.7)
        for number in range(count):
            mode.add(station(number))
        modes.append(mode)
        return mode, processes

    yield make
    for mode in modes:
        mode.stop()
        wait_for(lambda: not mode.busy)


def test_ten_parallel_streams_write_separate_audio_metadata_and_flush(
    mode_factory, tmp_path
):
    mode, processes = mode_factory(10)
    mode.start(tmp_path, 1)
    wait_for(lambda: all(row["status"] == "recording" for row in mode.snapshot()[0]))
    assert mode.active_count == 10 and len(processes) == 10
    assert "geprüft" in mode.snapshot()[1]
    assert len(list(tmp_path.glob("*.mp3"))) == len(list(tmp_path.glob("*.json"))) == 10
    mode.stop()
    wait_for(lambda: not mode.busy)
    assert all(process.closed for process in processes)
    assert not list(tmp_path.glob(".netmon-*"))
    for path in tmp_path.glob("*.json"):
        meta = json.loads(path.read_text())
        assert meta["ended_at"] and meta["status"] == "stopped"
        assert meta["titles"][0]["title"].endswith(meta["station_id"].split("-")[-1])
        audio = tmp_path / meta["audio_file"]
        assert audio.read_bytes().endswith(b"flushed")
        assert audio.stat().st_mode & 0o777 == path.stat().st_mode & 0o777 == 0o600


def test_selection_duplicate_limit_and_total_with_single_recording(
    mode_factory, tmp_path
):
    mode, _ = mode_factory(10)
    mode.add(station(0))
    assert len(mode.snapshot()[0]) == 10
    with pytest.raises(ValueError):
        mode.add(station(10))
    with pytest.raises(ValueError):
        mode.start(tmp_path, 1, external_count=1)
    assert not mode.busy and not list(tmp_path.iterdir())
    mode.remove("sender-9")
    mode.start(tmp_path, 1, external_count=1)
    with pytest.raises(ValueError):
        mode.start(tmp_path, 1)
    with pytest.raises(ValueError):
        mode.remove("sender-0")


@pytest.mark.parametrize("kind", ["slow", "start-error", "early-eof"])
def test_failed_simultaneous_check_publishes_nothing_and_cleans_all(
    mode_factory, tmp_path, kind
):
    processes = []

    def start(url, path, **kwargs):
        if url.endswith("/1") and kind == "start-error":
            raise OSError("private URL must not reach UI")
        proc = FakeRecording(
            url,
            path,
            slow=url.endswith("/1") and kind == "slow",
            fail_after=0.04 if kind == "early-eof" and url.endswith("/1") else None,
        )
        processes.append(proc)
        return proc

    mode, _ = mode_factory(starter=start)
    mode.start(tmp_path, 1)
    wait_for(lambda: not mode.busy)
    assert all(process.closed for process in processes)
    assert list(tmp_path.iterdir()) == []
    assert "private URL" not in mode.snapshot()[1]
    assert all(row["status"] == "cancelled" for row in mode.snapshot()[0])


def test_stop_during_late_start_cancels_without_ui_wait_or_orphan(
    mode_factory, tmp_path
):
    entered, release = threading.Event(), threading.Event()
    processes = []

    def start(url, path, **kwargs):
        entered.set()
        assert release.wait(3)
        proc = FakeRecording(url, path)
        processes.append(proc)
        return proc

    mode, _ = mode_factory(1, starter=start)
    mode.start(tmp_path, 1)
    assert entered.wait(1)
    began = time.monotonic()
    mode.stop()
    assert time.monotonic() - began < 0.1 and mode.busy
    release.set()
    wait_for(lambda: not mode.busy)
    assert all(process.closed for process in processes)
    assert not list(tmp_path.iterdir())


def test_one_failed_or_stopped_stream_does_not_stop_other(mode_factory, tmp_path):
    mode, processes = mode_factory()
    mode.start(tmp_path, 1)
    wait_for(lambda: all(row["status"] == "recording" for row in mode.snapshot()[0]))
    failed = next(process for process in processes if process.title == "0")
    surviving = next(process for process in processes if process.title == "1")
    failed.result = 2
    wait_for(lambda: any(row["status"] == "failed" for row in mode.snapshot()[0]))
    assert mode.busy and surviving.result is None
    mode.stop("sender-1")
    wait_for(lambda: not mode.busy)
    assert {row["status"] for row in mode.snapshot()[0]} == {"failed", "stopped"}


def test_time_limit_and_json_completion(mode_factory, tmp_path, monkeypatch):
    real_clock = time.monotonic
    monkeypatch.setattr(
        multi, "time", SimpleNamespace(monotonic=lambda: real_clock() * 60)
    )
    mode, processes = mode_factory(1)
    mode.start(tmp_path, 1)
    wait_for(lambda: not mode.busy)
    assert processes[0].closed
    meta = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert (
        meta["status"] == "finished"
        and meta["reason"] == "Maximale Aufnahmezeit erreicht."
    )


def test_low_disk_before_start_and_restore_freeze_prevent_children(
    mode_factory, tmp_path, monkeypatch
):
    mode, processes = mode_factory()
    monkeypatch.setattr(
        multi.shutil, "disk_usage", lambda _path: SimpleNamespace(free=1)
    )
    with pytest.raises(ValueError, match="Speicher"):
        mode.start(tmp_path, 1)
    assert not processes and not mode.busy
    protect_user_json_writes(tmp_path)
    try:
        with pytest.raises(PermissionError):
            mode.start(tmp_path, 1)
    finally:
        protect_user_json_writes(tmp_path, enabled=False)


def test_metadata_write_failure_stops_only_affected_recording(
    mode_factory, tmp_path, monkeypatch
):
    original = multi.safe_write_json
    monkeypatch.setattr(
        multi,
        "safe_write_json",
        lambda path, *a, **k: (
            (False, "test") if "Sender_0_" in str(path) else original(path, *a, **k)
        ),
    )
    mode, processes = mode_factory()
    mode.start(tmp_path, 1)
    wait_for(lambda: any(row["status"] == "failed" for row in mode.snapshot()[0]))
    assert mode.busy
    assert any(process.closed for process in processes)
    assert any(not process.closed for process in processes)


class Response(io.BytesIO):
    length = None

    def __init__(self, data, interval="4"):
        super().__init__(data)
        self.interval = interval

    def getheader(self, key):
        return self.interval if key == "icy-metaint" else None

    def read1(self, size):
        return self.read(min(size, 3))  # exercise fragmented network reads


def icy_block(title):
    payload = ("StreamTitle='" + title + "';").encode()
    payload += b"\0" * (-len(payload) % 16)
    return bytes([len(payload) // 16]) + payload


def test_record_stream_strips_icy_and_returns_own_bounded_title(monkeypatch):
    clock = iter([0, 2, 4])
    monkeypatch.setattr(fetch.time, "monotonic", lambda: next(clock))
    source = Response(
        b"abcd"
        + icy_block("Grüße – Künstler")
        + b"efgh"
        + icy_block("Titel zwei")
        + b"ijkl"
        + b"\0"
    )
    audio, replies = io.BytesIO(), []
    fetch._recording_body(source, audio, replies.append)
    assert audio.getvalue() == b"abcdefghijkl"
    assert [json.loads(reply)["title"] for reply in replies] == [
        "Grüße – Künstler",
        "Titel zwei",
    ]
    assert all(len(reply) < 4096 for reply in replies)


@pytest.mark.parametrize("interval", ["-1", "2000000", "bad", "00000000"])
def test_record_stream_rejects_invalid_metadata_interval(interval):
    with pytest.raises(fetch.SourceError):
        fetch._recording_body(
            Response(b"audio", interval), io.BytesIO(), lambda _data: None
        )


@pytest.mark.parametrize("interval", [None, "0"])
def test_record_stream_without_titles_is_valid_audio(interval):
    out = io.BytesIO()
    fetch._recording_body(
        Response(b"plain audio", interval),
        out,
        lambda _data: pytest.fail("invented title"),
    )
    assert out.getvalue() == b"plain audio"


def test_metadata_from_same_source_pipe_is_validated_and_reaped(tmp_path):
    import subprocess

    progress_read, progress_write = os.pipe()
    meta_read, meta_write = os.pipe()
    os.set_blocking(progress_read, False)
    os.set_blocking(meta_read, False)
    temporary = __import__("tempfile").TemporaryDirectory(dir=tmp_path)
    source = subprocess.Popen([str(sandbox.PYTHON), "-c", "import time;time.sleep(30)"])
    encoder = subprocess.Popen(
        [str(sandbox.PYTHON), "-c", "import time;time.sleep(30)"]
    )
    proc = sandbox.RecordingProcess(
        encoder,
        source,
        temporary,
        str(tmp_path / "synthetic.mp3"),
        progress_read,
        meta_read,
    )
    try:
        os.write(meta_write, b'{"title":"Own station title"}\n')
        assert proc.poll() is None
        assert proc.take_titles() == ["Own station title"]
        os.write(meta_write, b'{"title":false}\n')
        assert proc.wait(timeout=3) != 0
        assert encoder.poll() is not None and source.poll() is not None
    finally:
        proc.kill()
        proc.wait(timeout=3)
        os.close(progress_write)
        os.close(meta_write)


def test_saved_settings_are_bounded_and_never_autostart():
    settings = multi.saved_settings(
        {
            "multi_recording_minutes": "bad",
            "multi_recording_station_ids": ["same", "same", 3]
            + [str(n) for n in range(30)],
        }
    )
    assert settings["multi_recording_minutes"] == 60
    assert len(settings["multi_recording_station_ids"]) == 10
    assert multi.MultiRecording().busy is False


def test_record_mode_keeps_redirect_policy_and_requests_icy_on_each_hop(monkeypatch):
    import test_radio_fetch as policy

    for name in ("_MAXLINE", "_MAXHEADERS"):
        monkeypatch.setattr(fetch.http.client, name, getattr(fetch.http.client, name))
    responses = [
        policy.Response(302, {"Location": "https://cdn.example/live"}),
        policy.Response(
            headers={"icy-metaint": "4"}, body=b"abcd" + icy_block("Own title")
        ),
    ]
    connections, resolutions = policy.setup_transfers(monkeypatch, responses)
    audio, titles = io.BytesIO(), []
    fetch.transfer(
        "https://radio.example/live", audio, mode="record", metadata=titles.append
    )
    assert audio.getvalue() == b"abcd"
    assert json.loads(titles[0])["title"] == "Own title"
    assert len(resolutions) == 2
    assert all(
        connection["headers"]["Icy-MetaData"] == "1" for connection in connections
    )
    assert all(connection["closed"] for connection in connections)


@pytest.mark.parametrize(
    "location",
    [
        "https://127.0.0.1/private",
        "http://radio.example/live",
        "file:///etc/passwd",
        "https://u:p@example.com/live",
    ],
)
def test_record_mode_refuses_bad_redirect_before_next_connection(monkeypatch, location):
    import test_radio_fetch as policy

    for name in ("_MAXLINE", "_MAXHEADERS"):
        monkeypatch.setattr(fetch.http.client, name, getattr(fetch.http.client, name))
    connections, _ = policy.setup_transfers(
        monkeypatch, [policy.Response(302, {"Location": location})]
    )
    with pytest.raises(fetch.SourceError):
        fetch.transfer("https://radio.example/live", io.BytesIO(), mode="record")
    assert len(connections) == 1


def test_recording_metadata_channel_wiring_and_real_child_cleanup(
    tmp_path, monkeypatch
):
    """Real child pipes with synthetic executables; no codec/security proof."""
    monkeypatch.setattr(sandbox, "recording_available", lambda: True)
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    profiles = []
    monkeypatch.setattr(
        sandbox,
        "_limited",
        lambda command, profile: profiles.append(profile) or command,
    )
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))
    monkeypatch.setattr(sandbox, "_runtime_files", lambda *_a, **_k: ())
    commands = []

    def source(directory, *_args):
        script = (
            "import os,sys,time;"
            f"fd=os.open({str(directory/'metadata')!r},os.O_WRONLY);"
            'os.write(fd,b\'{"title":"Synthetic station title"}\\n\');'
            "sys.stdout.buffer.write(b'M');sys.stdout.buffer.flush();time.sleep(30)"
        )
        command = [str(sandbox.PYTHON), "-c", script, "--"]
        commands.append(command)
        return command

    def encoder(directory, *_args):
        script = (
            "import os,sys;sys.stdin.buffer.read(1);"
            f"fd=os.open({str(directory/'progress')!r},os.O_WRONLY);"
            "os.write(1,b'encoded');os.write(fd,b'out_time_us=100000\\ntotal_size=7\\nprogress=continue\\n');"
            "sys.stdin.buffer.read();os.write(1,b'flushed')"
        )
        return [str(sandbox.PYTHON), "-c", script]

    monkeypatch.setattr(sandbox, "_fetch_command", source)
    monkeypatch.setattr(sandbox, "_recording_sandbox_command", encoder)
    proc = sandbox.start_recording(
        "https://example.com/live?private-token",
        tmp_path / "audio.mp3",
        work_root=tmp_path,
        metadata=True,
    )
    try:
        assert proc.ready and proc.take_titles() == ["Synthetic station title"]
        assert "/run/record-metadata" in commands[0]
        assert "private-token" not in " ".join(commands[0])
        assert profiles == ["fetch", "encoder"]
        proc.terminate()
        assert proc.wait(timeout=3) == 0
        assert Path(proc.output_path).read_bytes() == b"encodedflushed"
        assert (
            proc._source_process.poll() is not None and proc._process.poll() is not None
        )
        assert not list(tmp_path.glob("record-*"))
    finally:
        proc.kill()
        proc.wait(timeout=3)
