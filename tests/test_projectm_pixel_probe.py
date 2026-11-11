"""Bounded experimental pixel protocol, process deadlines and launch separation."""

import json
from pathlib import Path
import struct
import subprocess
import sys
import time

import pytest

import projectm_pixel_probe as probe
from projectm_pixel_protocol import CHUNK, FRAME_BYTES, MAGIC, FrameDecoder, collect


def feed(decoder, data):
    frames = []
    for offset in range(0, len(data), CHUNK):
        frames.extend(decoder.feed(data[offset : offset + CHUNK]))
    return frames


def test_fixed_frames_accept_fragmented_headers_and_exact_body():
    decoder = FrameDecoder(2)
    for byte in MAGIC:
        assert decoder.feed(bytes([byte])) == []
    image = bytes(range(256)) * (FRAME_BYTES // 256)
    assert feed(
        decoder, struct.pack(">I", 0) + image + struct.pack(">I", 1) + image
    ) == [image, image]
    decoder.finish()
    assert decoder.count == 2 and decoder.peak <= FRAME_BYTES + CHUNK + 4


@pytest.mark.parametrize("frames", [0, 25, True, "1", None])
def test_trusted_frame_budget_is_strictly_bounded(frames):
    with pytest.raises(ValueError):
        FrameDecoder(frames)


@pytest.mark.parametrize(
    "bad", [b"not pixels", MAGIC + b"\0\0\0\1", b"X" * (CHUNK + 1)]
)
def test_bad_signature_sequence_or_chunk_is_rejected(bad):
    with pytest.raises(ValueError):
        FrameDecoder(1).feed(bad)


@pytest.mark.parametrize(
    "body", [b"", MAGIC[:3], MAGIC, MAGIC + b"\0\0\0\0" + b"x" * 100]
)
def test_eof_with_incomplete_frame_fails(body):
    decoder = FrameDecoder(1)
    feed(decoder, body)
    with pytest.raises(ValueError):
        decoder.finish()


def test_extra_data_after_exact_frame_count_is_rejected():
    decoder = FrameDecoder(1)
    feed(decoder, MAGIC + b"\0\0\0\0" + b"x" * FRAME_BYTES)
    with pytest.raises(ValueError):
        decoder.feed(b"trailing")


@pytest.mark.parametrize(
    "program,expected",
    [
        ("import time; time.sleep(10)", TimeoutError),
        ("import sys; sys.stdout.buffer.write(b'X'*1000000)", ValueError),
        (
            "import sys; sys.stdout.buffer.write(b'NMPX01\\0'+b'\\0'*4+b'x'*1024)",
            ValueError,
        ),
    ],
)
def test_stall_flood_and_partial_eof_have_bounded_failure(program, expected):
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            program,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    started = time.monotonic()
    try:
        with pytest.raises(expected):
            collect(
                process,
                lambda _: pytest.fail("invalid frame emitted"),
                frames=1,
                timeout=0.2,
            )
    finally:
        probe.stop_child(process)
    assert process.poll() is not None and time.monotonic() - started < 2


@pytest.mark.parametrize("unsafe", ["same_namespace", "host_interfaces"])
def test_pixel_probe_rejects_unsafe_namespace_before_commands(
    monkeypatch, tmp_path, unsafe
):
    monkeypatch.setattr(probe.os, "readlink", lambda _: "net:[test]")
    monkeypatch.setattr(
        probe.socket, "if_nameindex", lambda: [(1, "lo"), (2, "host-if")]
    )
    monkeypatch.setattr(
        probe.subprocess, "run", lambda *_a, **_k: pytest.fail("unsafe command")
    )
    parent = "net:[test]" if unsafe == "same_namespace" else "net:[other]"
    assert probe.worker(tmp_path, tmp_path, parent) == 1
    result = json.loads((tmp_path / "projectm-pixel-result.json").read_text())
    assert result["status"] == "failed" and not result["checks"]


@pytest.mark.parametrize(
    "other",
    [
        "--projectm-display-probe",
        "--projectm-ui-probe",
        "--radio-gui-probe",
        "--radio-projectm-handover-probe",
        "--probe",
    ],
)
def test_pixel_mode_rejects_other_launch_modes(other):
    path = Path(__file__).with_name("run_isolated_suite.py")
    result = subprocess.run(
        [sys.executable, "-B", str(path), "--projectm-pixel-probe", other],
        capture_output=True,
        text=True,
        timeout=4,
    )
    assert result.returncode == 2 and "error:" in result.stderr


def test_internal_display_plan_has_no_outer_display_binding(tmp_path):
    from netmon.core import radio_sandbox as sandbox

    command = probe.display_command(
        tmp_path, Path("/usr/lib/python3.12"), (), 21, sandbox
    )
    assert "--unshare-net" in command and "--unshare-ipc" in command
    assert "--ro-bind-fd" not in command
    assert "/run/host.auth" not in command and "/tmp/.X11-unix/X0" not in command
    assert "DISPLAY" not in command and "XAUTHORITY" not in command
    assert command[
        command.index("--ro-bind-data") + 1 : command.index("--ro-bind-data") + 3
    ] == ["21", "/run/private.auth"]


def test_reader_plan_has_only_private_x_and_no_host_audio(tmp_path, monkeypatch):
    from netmon.core import radio_sandbox as sandbox

    binary = tmp_path / "reader"
    monkeypatch.setattr(sandbox, "_runtime_files", lambda _: (binary,))
    command = probe.reader_plan(tmp_path, binary, 22, 23, sandbox)
    assert command[command.index("--") + 1 :] == ["/run/pixel-reader"]
    assert command.count("--ro-bind-fd") == 1
    assert command[
        command.index("--ro-bind-fd") + 1 : command.index("--ro-bind-fd") + 3
    ] == ["22", "/tmp/.X11-unix/X1"]
    assert "/tmp/.X11-unix/X0" not in command and "/run/host.auth" not in command
    assert "/run/audio/pulse" not in command and "PULSE_SERVER" not in command


@pytest.mark.parametrize("prior", [-1, 128 * 1024**2])
def test_internal_server_preserves_lower_inherited_limits(monkeypatch, prior):
    import projectm_pixel_server as server

    bounds, executions = [], []
    monkeypatch.setattr(server.sys, "argv", ["pixel-server"])
    monkeypatch.setattr(server.resource, "getrlimit", lambda _: (prior, prior))
    monkeypatch.setattr(
        server.resource, "setrlimit", lambda name, value: bounds.append((name, value))
    )
    monkeypatch.setattr(server.os, "umask", lambda _: None)
    monkeypatch.setattr(
        server.os, "execv", lambda path, args: executions.append((path, args))
    )
    server.main()
    memory = dict(bounds)[server.resource.RLIMIT_AS]
    assert memory == ((2 * 1024**3,) * 2 if prior == -1 else (prior, prior))
    assert executions[0][0] == "/usr/bin/Xvfb" and executions[0][1][1] == ":1"


def test_internal_server_refuses_unexpected_arguments(monkeypatch):
    import projectm_pixel_server as server

    monkeypatch.setattr(server.sys, "argv", ["pixel-server", "--unexpected"])
    monkeypatch.setattr(
        server.os, "execv", lambda *_: pytest.fail("unexpected server execution")
    )
    assert server.main() == 2


def test_valid_pipe_frame_is_received_and_child_reaped():
    program = (
        "import sys;sys.stdout.buffer.write(b'NMPX01\\0'+b'\\0'*4+b'x'*(640*480*4))"
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "-c",
            program,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    frames = []
    try:
        result = collect(
            process, lambda image: frames.append(len(image)), frames=1, timeout=2
        )
        assert result["frames"] == 1 and frames == [FRAME_BYTES]
        assert process.wait(timeout=1) == 0
    finally:
        probe.stop_child(process)


def test_coordinator_deadline_retains_partial_output(monkeypatch, tmp_path):
    def timeout(*_a, **_k):
        raise subprocess.TimeoutExpired(
            "controlled", 90, output=b"partial stdout", stderr=b"partial stderr"
        )

    monkeypatch.setattr(probe.subprocess, "run", timeout)
    assert probe.run(tmp_path, tmp_path) == 1
    assert (tmp_path / "coordinator.log").read_text() == "partial stdoutpartial stderr"
    data = json.loads((tmp_path / "coordinator-timeout.json").read_text())
    assert data["status"] == "failed" and not data["security_acceptance"]
