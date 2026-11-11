"""Native Tk buttons/original handlers and real private projectM; no host app."""

import array
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback

sys.pycache_prefix = "/nonexistent"
os.environ["PYTHONPYCACHEPREFIX"] = "/nonexistent"


def exercise(root, output):
    import tkinter as tk
    from tkinter import ttk

    sys.path.insert(0, str(root))
    from netmon import netmon_radio_app as ui, netmon_projectm_sidecar as sidecar
    from netmon.core import radio_sandbox as sandbox, projectm_frontend as frontend

    result = {
        "status": "failed",
        "checks": [],
        "host_netmon_started": False,
        "real_desktop": False,
        "host_audio": False,
        "complete_gui_acceptance": False,
    }
    app = playback = relay = None
    feeder = None
    stop = threading.Event()
    release_start = threading.Event()
    release_start.set()
    release_stop = threading.Event()
    release_stop.set()
    entered = threading.Event()
    original_start, original_prepare = frontend.start, frontend.prepare
    from netmon.core import projectm_display as display, projectm_pixels as pixels

    original_host = display._host
    display._host = lambda: (_ for _ in ()).throw(AssertionError("outer X requested"))
    original_popen = subprocess.Popen
    commands = []
    capsules = []
    calls = []
    ticks = []
    callback_errors = []
    log = (output / "projectm-ui-processes.log").open("w")
    try:
        assert os.environ.get("XAUTHORITY") and os.environ["DISPLAY"].startswith(":")
        result["source_sha256"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "netmon/netmon_projectm_sidecar.py",
                "netmon/netmon_radio_app.py",
                "netmon/features/radio_controller.py",
                "netmon/core/projectm_frontend.py",
                "netmon/core/projectm_frontend_worker.py",
                "netmon/core/projectm_pcm.py",
                "netmon/core/projectm_pcm_worker.py",
                "netmon/core/projectm_native.py",
                "netmon/native/projectm_pcm/pcm_renderer.cpp",
                "netmon/native/projectm_pcm/build/pcm-renderer",
                "netmon/native/projectm_pcm/build/build.json",
                "netmon/core/projectm_display.py",
                "netmon/core/radio_sandbox.py",
                "tests/projectm_ui_probe.py",
                "tests/run_isolated_suite.py",
                "netmon/core/projectm_pixels.py",
                "netmon/core/projectm_pixel_worker.py",
                "netmon/core/projectm_display_worker.py",
                "netmon/ui/projectm_pixel_window.py",
                "tests/projectm_gx11_boundary.py",
            )
        }
        stdlib, files, payload = frontend._runtime()
        result["runtime_sha256"] = {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(files) | {p for p, _ in payload})
        }
        result["runtime_sha256"].update(
            {
                str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in set(display._runtime()[1]) | set(pixels._runtime()[1])
            }
        )

        class LoggedPopen(original_popen):
            def __init__(self, command, *args, **kwargs):
                if Path(command[0]).name in {
                    "sudo",
                    "pkexec",
                    "flatpak",
                    "systemctl",
                    "nmcli",
                    "ufw",
                }:
                    raise AssertionError("Forbidden native UI launch")
                if command[0] == str(sandbox.BWRAP):
                    kwargs["stderr"] = log
                    commands.append(command)
                super().__init__(command, *args, **kwargs)
                if command[0] == str(sandbox.BWRAP):
                    log.write(f"OWNED {self.pid}: {command[-1]}\n")
                    log.flush()

        subprocess.Popen = LoggedPopen

        temporary = tempfile.TemporaryDirectory(prefix="pcm-ui-", dir=output)
        directory = Path(temporary.name)
        sandbox._prepare_directory(directory)
        (directory / "tap").mkdir(mode=0o700)
        pcm_stdlib, pcm_files = sandbox._pcm_runtime()
        relay = subprocess.Popen(
            sandbox._pcm_command(directory, pcm_stdlib, pcm_files),
            env=sandbox._ENV,
            cwd="/",
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=log,
            close_fds=True,
            bufsize=0,
        )
        playback = sandbox.SandboxProcess(relay, temporary, pcm_process=relay)
        samples = array.array(
            "h",
            (int(5000 * math.sin(n * 2 * math.pi * 440 / 48000)) for n in range(9600)),
        ).tobytes()

        def feed():
            try:
                while not stop.is_set():
                    for offset in range(0, len(samples), 3840):
                        if stop.is_set():
                            return
                        relay.stdin.write(samples[offset : offset + 3840])
                        stop.wait(0.02)
            except (OSError, ValueError):
                pass

        feeder = threading.Thread(target=feed, daemon=True)
        feeder.start()
        presets = output / "ui-presets"
        presets.mkdir()
        (presets / "pack").mkdir()
        from projectm_pixel_probe import PRESET

        (presets / "pack/synthetic.milk").write_text(PRESET)

        def prepared(*args, **kwargs):
            entered.set()
            assert release_start.wait(8), "Startup test gate expired"
            return original_prepare(*args, **kwargs)

        frontend.prepare = prepared

        def start(*args, **kwargs):
            calls.append(threading.get_ident())
            session = original_start(*args, **kwargs)
            capsules.append(session)
            raw_stop = session.stop

            def held_stop():
                assert release_stop.wait(8), "Cleanup test gate expired"
                raw_stop()

            session.stop = held_stop
            return session

        frontend.start = start

        class Fixture(tk.Tk):
            _refresh_projectm_status = ui.NetMonRadioApp._refresh_projectm_status
            open_projectm_visualizer_test = (
                ui.NetMonRadioApp.open_projectm_visualizer_test
            )
            close_projectm_visualizer_test = (
                ui.NetMonRadioApp.close_projectm_visualizer_test
            )
            _timestamp_text = ui.NetMonRadioApp._timestamp_text

            def tr(self, _key, default=None):
                return default or _key

            def log_safe(self, _message):
                pass

            def _refresh_radio_miniplayer_content(self):
                pass

        app = Fixture()
        app.title("Private projectM UI fixture")
        app.report_callback_exception = lambda *args: callback_errors.append(
            str(args[1])
        )
        ui._init_radio_ui_projectm_runtime_state(app)
        app.radio_proc = playback
        app.radio_stop_requested = False
        app.radio_projectm_preset_dir = str(presets)
        app._projectm_detected_status = sidecar.ProjectMSidecarStatus(
            True,
            True,
            False,
            "fixture",
            "fixture",
            backend_label="Installed Qt5 payload",
        )
        app._projectm_probe_time = time.monotonic()
        for name in ("status", "meta", "history", "install", "preset", "preset_hint"):
            setattr(app, "radio_projectm_" + name + "_var", tk.StringVar(app))
        app.radio_projectm_last_started_at = app.radio_projectm_last_stopped_at = ""
        button = ttk.Button(
            app, text="Start projectM", command=app.open_projectm_visualizer_test
        )
        button.pack()
        stop_button = ttk.Button(
            app, text="Stop projectM", command=app.close_projectm_visualizer_test
        )
        stop_button.pack()
        ttk.Label(app, textvariable=app.radio_projectm_status_var).pack()

        def heartbeat():
            ticks.append(time.monotonic())
            app.after(10, heartbeat)

        app.after(10, heartbeat)

        def wait_for(predicate, timeout=15):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                app.update()
                if predicate():
                    return
                time.sleep(0.01)
            raise AssertionError("Native Tk UI deadline")

        release_start.clear()
        entered.clear()
        before = time.monotonic()
        button.invoke()
        assert time.monotonic() - before < 0.3
        request = app.radio_projectm_proc
        wait_for(entered.is_set)
        initial = len(ticks)
        wait_for(lambda: len(ticks) >= initial + 8)
        before = time.monotonic()
        stop_button.invoke()
        assert time.monotonic() - before < 0.3
        assert request.cancelled.is_set() and request.pid == 0
        release_start.set()
        wait_for(request.done.is_set)
        assert not capsules and not app.radio_projectm_last_started_at
        result["checks"].append(
            "real Tk Start/Stop handlers stay responsive during blocked private preparation; stopped generation never publishes a renderer"
        )

        button.invoke()
        request = app.radio_projectm_proc
        wait_for(lambda: request.snapshot()[0] == "running")
        wait_for(lambda: bool(app.radio_projectm_last_started_at))
        assert request.thread.is_alive() and calls[-1] != threading.get_ident()
        session = capsules[-1]
        assert (
            session.process.poll() is None
            and session.pcm.process.poll() is None
            and session.display.process.poll() is None
        )
        result["checks"].append(
            "real Tk handler starts real PCM projectM with private NetMon audio/display; owner thread stays alive after button callback returns"
        )

        window = app._projectm_pixel_window
        wait_for(lambda: window.displayed >= 30)
        from PIL import ImageTk, ImageGrab

        first = ImageTk.getimage(window.photo).tobytes()
        frames_before = request.frames.received
        time.sleep(0.5)  # Intentional fixture-only UI pause.
        assert request.frames.received > frames_before + 5
        assert request.frames.dropped > 5
        wait_for(lambda: window.displayed >= 90)
        assert ImageTk.getimage(window.photo).tobytes() != first
        ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
            output / "gx11-private-ui.png"
        )
        result["pixels"] = {
            "received": request.frames.received,
            "displayed": window.displayed,
            "dropped": request.frames.dropped,
            "ui_pause_seconds": 0.5,
        }
        from projectm_gx11_boundary import check as boundary

        result["boundary"] = boundary(session, output)
        result["checks"].append(
            "original Tk handler displays changing fixed pixels; slow UI drops old frames; all three capsule roles deny outer private UI X/audio/secrets/network"
        )
        assert all(
            "/run/host.auth" not in cmd and "/tmp/.X11-unix/X0" not in cmd
            for cmd in commands
        )
        result["commands"] = commands
        ticks.clear()

        release_stop.clear()
        stop_button.invoke()
        old = request
        button.invoke()
        new = app.radio_projectm_proc
        initial = len(ticks)
        wait_for(lambda: len(ticks) >= initial + 8)
        assert new is not old and len(capsules) == 1 and not old.done.is_set()
        release_stop.set()
        wait_for(lambda: new.snapshot()[0] == "running")
        assert old.done.is_set() and len(capsules) == 2
        assert session.process.poll() is not None and relay.poll() is None
        result["checks"].append(
            "rapid Stop/Start waits for real previous capsule cleanup and does not overlap PCM taps"
        )

        assert sidecar.invalidate_projectm_playback(app, playback)
        app.radio_proc = None
        wait_for(new.done.is_set)
        assert capsules[-1].process.poll() is not None and relay.poll() is None
        result["checks"].append(
            "playback revocation closes its visualization while the independent PCM fixture remains alive"
        )

        app.radio_proc = playback
        release_start.clear()
        entered.clear()
        button.invoke()
        last = app.radio_projectm_proc
        wait_for(entered.is_set)
        app._radio_panel_destroying = True
        stop_button.invoke()
        assert not vars(app).get("_projectm_status_after")
        app.destroy()
        app = None
        release_start.set()
        assert last.done.wait(5)
        assert len(capsules) == 2 and last.pid == 0 and relay.poll() is None
        result["checks"].append(
            "widget destruction cancels pending generation and its Tk timer without a late renderer or callback"
        )
        assert not callback_errors, callback_errors
        result["button_start_seconds_upper_bound"] = 0.3
        result["status"] = "passed"
    except Exception:
        result["error"] = traceback.format_exc()
        if app is not None:
            request = vars(app).get("radio_projectm_proc")
            if request is not None:
                result["request_at_failure"] = request.snapshot()
    finally:
        release_start.set()
        release_stop.set()
        if app is not None:
            sidecar.stop_projectm_sidecar(app)
            request = vars(app).get("radio_projectm_proc")
            if request is not None:
                request.done.wait(5)
            app.destroy()
        for session in capsules:
            session.stop()
        stop.set()
        if playback is not None:
            playback.kill()
            playback.wait(timeout=3)
        if feeder is not None:
            feeder.join(timeout=2)
        if relay is not None:
            relay.stdin.close()
        frontend.start, frontend.prepare = original_start, original_prepare
        subprocess.Popen = original_popen
        display._host = original_host
        log.close()
    (output / "projectm-ui-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"runtime_sha256", "commands", "boundary"}
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "passed" else 1


def coordinator(root, output, parent_net):
    assert os.readlink("/proc/self/ns/net") != parent_net
    assert [name for _, name in socket.if_nameindex()] == ["lo"]
    subprocess.run(
        ["/usr/sbin/ip", "link", "set", "lo", "up"],
        env={"PATH": "/usr/bin:/bin"},
        capture_output=True,
        check=True,
        timeout=3,
    )
    from radio_stream_probe import _drop_namespace_caps

    _drop_namespace_caps()
    for name in ("home", "runtime", "config", "cache", "state", "data"):
        (output / name).mkdir(mode=0o700)
    env = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C.UTF-8",
        "HOME": str(output / "home"),
        "TMPDIR": str(output),
        "XDG_RUNTIME_DIR": str(output / "runtime"),
        "XDG_CONFIG_HOME": str(output / "config"),
        "XDG_CACHE_HOME": str(output / "cache"),
        "XDG_STATE_HOME": str(output / "state"),
        "XDG_DATA_HOME": str(output / "data"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPYCACHEPREFIX": "/nonexistent",
    }
    command = [
        "/usr/bin/xvfb-run",
        "-a",
        "-e",
        str(output / "ui-xvfb.log"),
        "-s",
        "-screen 0 1280x1024x24 -nolisten tcp -extension GLX",
        str(root / ".venv/bin/python"),
        "-B",
        str(Path(__file__).resolve()),
        "--exercise",
        str(root),
        str(output),
    ]
    completed = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=60
    )
    (output / "ui-coordinator.log").write_text(completed.stdout + completed.stderr)
    print(completed.stdout + completed.stderr)
    return completed.returncode


def run(root, output):
    print("Private projectM UI evidence:", output, flush=True)
    command = [
        "/usr/bin/unshare",
        "--user",
        "--map-current-user",
        "--keep-caps",
        "--net",
        "--fork",
        "--kill-child=KILL",
        str(root / ".venv/bin/python"),
        "-B",
        str(Path(__file__).resolve()),
        "--coordinator",
        str(root),
        str(output),
        os.readlink("/proc/self/ns/net"),
    ]
    completed = subprocess.run(
        command,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": "/nonexistent"},
        cwd=root,
        capture_output=True,
        text=True,
        timeout=70,
    )
    (output / "coordinator.log").write_text(completed.stdout + completed.stderr)
    print(completed.stdout + completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--coordinator":
        raise SystemExit(coordinator(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]))
    if len(sys.argv) == 4 and sys.argv[1] == "--exercise":
        raise SystemExit(exercise(Path(sys.argv[2]), Path(sys.argv[3])))
    raise SystemExit("Use tests/run_isolated_suite.py --projectm-ui-probe")
