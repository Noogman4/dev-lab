"""Probe fixtures must preserve ownership, private output and fail-closed start."""

import ast
import json
import os
from pathlib import Path
import threading
import time
from types import SimpleNamespace

import pytest

from netmon.core import radio_sandbox as sandbox
from netmon import netmon_radio_core as core
from radio_probe_output import PrivateOutput, install


def test_private_fifo_transfers_bytes_and_closes_duplicated_descriptor(tmp_path):
    output = PrivateOutput(tmp_path)
    assert not output.thread.daemon
    descriptor = os.dup(output.descriptor)
    try:
        output.handed_over()
        payload = bytes(range(256)) * 16
        assert os.write(descriptor, payload) == len(payload)
        deadline = time.monotonic() + 1
        while output.count != len(payload):
            assert time.monotonic() < deadline
            time.sleep(0.001)
        output.silence()
        output.silence()
    finally:
        os.close(descriptor)
        output.close()
    audit = json.loads(output.audit_path.read_text())
    assert json.loads(output.open_path.read_text())["audit"] == output.audit_path.name
    assert audit["bytes"] == 4096 and audit["events"] == ["silence", "close"]
    assert audit["reader_joined"] and audit["fifo_removed"] and audit["error"] is None


def test_fixture_does_not_bypass_unavailable_quota_manager(tmp_path, monkeypatch):
    media = tmp_path / "selected.wav"
    media.write_bytes(b"synthetic")
    monkeypatch.setattr(sandbox, "available", lambda: True)

    def unavailable():
        raise sandbox.RadioSandboxError("quota-manager-unavailable")

    monkeypatch.setattr(sandbox, "_require_quota_manager", unavailable)
    restore, outputs, audits = install(sandbox, tmp_path)
    try:
        with pytest.raises(
            sandbox.RadioSandboxError, match="quota-manager-unavailable"
        ):
            sandbox.start_playback(
                ["mpv", f"--input-ipc-server={sandbox.IPC_PATH}", "--", str(media)],
                ipc_root=tmp_path,
                local_file=media,
            )
        assert not outputs and not audits
    finally:
        restore()


def test_reader_start_failure_releases_fifo_fds_and_directory(tmp_path, monkeypatch):
    count = len(list(Path("/proc/self/fd").iterdir()))

    def refused(self):
        raise RuntimeError("synthetic-thread-start-failure")

    monkeypatch.setattr(threading.Thread, "start", refused)
    with pytest.raises(RuntimeError, match="synthetic-thread-start-failure"):
        PrivateOutput(tmp_path)
    assert not [path for path in tmp_path.glob("sink-*") if path.is_dir()]
    assert len(list(Path("/proc/self/fd").iterdir())) == count


def test_gui_snapshot_reads_markers_and_never_polls_processes(tmp_path, monkeypatch):
    source = Path(__file__).with_name("radio_gui_probe.py")
    function = next(
        n
        for n in ast.parse(source.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "_snapshot"
    )
    writes = []
    namespace = {
        "os": os,
        "time": time,
        "json": json,
        "WORK": tmp_path,
        "PROJECTM": False,
        "_read": lambda path: {},
        "_write": lambda path, value: writes.append(value),
    }
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"),
        namespace,
    )
    monkeypatch.setattr(core, "netmon_host_is_available", lambda: True)

    def forbidden():
        pytest.fail("UI snapshot polled/reaped a process owned by another thread")

    process = SimpleNamespace(
        pid=10,
        poll=forbidden,
        ipc_path="fixture.sock",
        _output=SimpleNamespace(count=8192),
        _output_gate=SimpleNamespace(done=threading.Event()),
        _pcm_process=SimpleNamespace(pid=11),
        _source_process=SimpleNamespace(pid=12),
    )
    recording = SimpleNamespace(
        pid=13, poll=forbidden, _source_process=SimpleNamespace(pid=14)
    )
    target = SimpleNamespace(
        radio_proc=process,
        radio_record_proc=recording,
        radio_playback_request=SimpleNamespace(finished=threading.Event()),
        radio_record_request=SimpleNamespace(done=threading.Event()),
        radio_current_station_id="fixture",
    )
    for name in [
        "radio_record_status_var",
        "radio_volume_var",
        "radio_volume_label_var",
        "radio_eq_bass_var",
        "radio_eq_mid_var",
        "radio_eq_treble_var",
        "radio_search_var",
        "radio_status_var",
        "radio_title_var",
    ]:
        setattr(target, name, SimpleNamespace(get=lambda: "fixture"))
    app = SimpleNamespace(radio_embedded_panel=target)
    result = namespace["_snapshot"](app, "host")
    assert result["playing"] and result["recording"] and result["fifo_bytes"] == 8192
    assert "audio_wrapper_pid" not in result
    target.radio_playback_request.finished.set()
    target.radio_record_request.done.set()
    result = namespace["_snapshot"](app, "host")
    assert not result["playing"] and not result["recording"]
