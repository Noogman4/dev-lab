"""The stream fixture must fail before any command on an unsafe network."""

import io
import json
import wave
import subprocess
import sys
from pathlib import Path

import pytest

import radio_stream_probe as probe


def test_generated_stream_contains_audio_not_silence():
    with wave.open(io.BytesIO(probe._tone()), "rb") as sound:
        assert sound.getnframes() / sound.getframerate() >= 10
        assert any(sound.readframes(sound.getnframes()))


@pytest.mark.parametrize("unsafe", ["same_namespace", "host_interfaces"])
@pytest.mark.parametrize("projectm", [False, True])
def test_unsafe_network_is_rejected_before_commands(
    monkeypatch, tmp_path, unsafe, projectm
):
    root = tmp_path / "source"
    subject = root / "netmon/core/radio_sandbox.py"
    subject.parent.mkdir(parents=True)
    subject.write_text("# synthetic source, must never be executed\n")
    output = tmp_path / "evidence"
    output.mkdir()
    monkeypatch.setattr(probe.os, "readlink", lambda _path: "net:[test]")
    monkeypatch.setattr(
        probe.socket, "if_nameindex", lambda: [(1, "lo"), (2, "host-interface")]
    )
    monkeypatch.setattr(
        probe.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("Command on unverified network"),
    )
    parent = "net:[test]" if unsafe == "same_namespace" else "net:[parent]"
    assert probe._worker(root, output, parent, gui=projectm, projectm=projectm) == 1
    result = json.loads((output / "radio-stream-result.json").read_text())
    assert result["status"] == "failed"
    assert result["checks"] == []
    assert not (output / "runtime").exists()


@pytest.mark.parametrize("other", ["--radio-gui-probe", "--projectm-ui-probe"])
def test_active_handover_mode_rejects_other_native_modes_before_execution(other):
    starter = Path(__file__).with_name("run_isolated_suite.py")
    result = subprocess.run(
        [sys.executable, "-B", str(starter), "--radio-projectm-handover-probe", other],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 2
    assert "error:" in result.stderr
