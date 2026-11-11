"""Private Tk pixel presentation exercise; backend never gets its X authority."""

import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import threading
import time
import traceback

sys.pycache_prefix = "/nonexistent"
os.environ["PYTHONPYCACHEPREFIX"] = "/nonexistent"


def backend(root, output, delay):
    from projectm_pixel_benchmark import END, MAGIC
    import projectm_pixel_probe as probe

    output.mkdir(mode=0o700)
    result = {"status": "failed", "checks": [], "owned_wrappers_reaped": True}
    result["ui_probe_source_sha256"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in ("tests/projectm_pixel_ui_probe.py", "tests/projectm_pixel_view.py")
    }
    cancel = threading.Event()

    def control():
        os.read(sys.stdin.fileno(), 1)
        cancel.set()

    threading.Thread(target=control, daemon=True).start()
    count = 0

    def frame(data):
        nonlocal count
        if not count:
            sys.stdout.buffer.write(MAGIC)
        sys.stdout.buffer.write(struct.pack(">IQ", count, time.monotonic_ns()))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
        count += 1

    try:
        if cancel.wait(delay):
            raise InterruptedError("Cancelled before preparation")
        probe.exercise(
            root, output, result, benchmark_fps=30, frame_sink=frame, cancel=cancel
        )
        sys.stdout.buffer.write(struct.pack(">IQ", END, 0))
        sys.stdout.buffer.flush()
        result["status"] = "passed"
    except InterruptedError:
        result["status"] = "cancelled"
    except Exception:
        result["error"] = traceback.format_exc()
    result["forwarded_frames"] = count
    (output / "backend-result.json").write_text(json.dumps(result, indent=2) + "\n")
    return int(result["status"] == "failed")


def exercise(root, output):
    import tkinter as tk
    from tkinter import ttk
    from projectm_pixel_view import PixelView

    assert os.environ.get("DISPLAY") and os.environ.get("XAUTHORITY")
    result = {
        "status": "failed",
        "checks": [],
        "real_desktop": False,
        "host_audio": False,
        "production_ui_changed": False,
        "security_acceptance": False,
        "complete_gui_acceptance": False,
        "source_sha256": {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "tests/projectm_pixel_view.py",
                "tests/projectm_pixel_ui_probe.py",
                "tests/run_isolated_suite.py",
            )
        },
    }
    app = tk.Tk()
    app.title("Private raw pixel UI fixture")
    callback_errors, ticks, requests, launches = [], [], [], []
    app.report_callback_exception = lambda *args: callback_errors.append(str(args[1]))
    status = tk.StringVar(app, "idle")
    label = ttk.Label(app)
    label.pack()
    ttk.Label(app, textvariable=status).pack()
    delay = 0

    def launch(generation):
        dest = output / f"generation-{generation}"
        launches.append(dest)
        # No DISPLAY/XAUTHORITY or inherited audio/secret descriptors in backend.
        return (
            [
                str(root / ".venv/bin/python"),
                "-B",
                "-X",
                "pycache_prefix=/nonexistent",
                str(Path(__file__).resolve()),
                "--backend",
                str(root),
                str(dest),
                str(delay),
            ],
            {
                "PATH": "/usr/bin:/bin",
                "HOME": "/nonexistent",
                "LC_ALL": "C.UTF-8",
                "PYTHONPYCACHEPREFIX": "/nonexistent",
            },
        )

    view = PixelView(app, label, status, launch)
    heartbeat_id = None

    def heartbeat():
        nonlocal heartbeat_id
        ticks.append(time.monotonic())
        heartbeat_id = app.after(10, heartbeat)

    def wait(predicate, timeout=70):
        deadline = time.monotonic() + timeout
        while not predicate():
            if time.monotonic() >= deadline:
                raise TimeoutError("Private pixel UI condition")
            app.update()
            time.sleep(0.002)
        app.update()

    try:
        heartbeat()
        # A delayed backend is stopped before it creates any media resources.
        delay = 2
        early = view.start()
        requests.append(early)
        started = time.monotonic()
        view.stop()
        result["early_stop_callback_ms"] = (time.monotonic() - started) * 1000
        assert result["early_stop_callback_ms"] < 100
        wait(early.done.is_set, 8)
        assert early.process is None or early.process.poll() is not None
        assert early.state == "cancelled" and not early.forced_kill
        result["checks"].append(
            "stop during preparation returns without waiting; owner reaps"
        )

        # Real renderer/reader -> fixed raw bytes -> trusted Tk PhotoImage.
        delay = 0
        request = view.start()
        requests.append(request)
        wait(lambda: request.displayed >= 30)
        assert view.photo.width() == 640 and view.photo.height() == 480
        view.latest_rgb.save(output / "ui-before-busy.ppm", format="PPM")
        before = request.frames.received
        dropped = request.frames.dropped
        time.sleep(0.5)  # Intentional slow UI; receiver must continue draining.
        assert request.frames.received > before + 5
        assert request.frames.dropped > dropped
        # Measured responsiveness below excludes this deliberate pause only.
        ticks.clear()
        wait(lambda: request.displayed >= 90)
        view.latest_rgb.save(output / "ui-after-busy.ppm", format="PPM")
        from PIL import ImageGrab

        # Captures only this probe's private Xvfb, never the real desktop.
        ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(output / "private-ui.png")
        assert (output / "ui-before-busy.ppm").read_bytes() != (
            output / "ui-after-busy.ppm"
        ).read_bytes()
        wait(request.done.is_set)
        assert request.state == "ended", request.error
        assert not request.forced_kill and request.frames.received == 900
        assert request.peak_buffer <= 640 * 480 * 4 + 12 + 65536
        result["display"] = {
            "received": request.frames.received,
            "displayed": request.displayed,
            "superseded_before_display": request.frames.dropped,
            "peak_parser_bytes": request.peak_buffer,
            "display_updates_per_second": (request.displayed - 1)
            / (request.display_times[-1] - request.display_times[0]),
            "heartbeat_max_gap_ms_after_deliberate_pause": max(
                b - a for a, b in zip(ticks, ticks[1:])
            )
            * 1000,
            "intentional_ui_pause_seconds": 0.5,
        }
        assert result["display"]["heartbeat_max_gap_ms_after_deliberate_pause"] < 200
        result["checks"].append(
            "real private projectM pixels displayed at Tk; busy UI keeps one latest frame and recovers"
        )
        result["checks"].append(
            "finite EOF updates terminal UI; no worker Tk calls/callback errors"
        )

        # Stop while streaming, skip an intermediate start, replace, close.
        old = view.start()
        requests.append(old)
        wait(lambda: old.displayed >= 3)
        started = time.monotonic()
        view.stop()
        middle = view.start()
        requests.append(middle)
        view.stop()
        newest = view.start()
        requests.append(newest)
        result["stop_start_callbacks_ms"] = (time.monotonic() - started) * 1000
        assert result["stop_start_callbacks_ms"] < 100
        wait(lambda: newest.displayed >= 3)
        assert old.done.is_set() and middle.done.is_set()
        assert old.state == middle.state == "cancelled"
        assert old.process.poll() is not None
        started = time.monotonic()
        view.close()
        result["close_callback_ms"] = (time.monotonic() - started) * 1000
        assert result["close_callback_ms"] < 100
        app.after_cancel(heartbeat_id)
        app.destroy()  # Owner cleanup must not require a living Tk interpreter.
        app = None
        assert newest.done.wait(20)
        assert newest.state == "cancelled" and newest.process.poll() is not None
        assert not any(r.forced_kill or r.error for r in requests), [
            (r.state, r.error) for r in requests
        ]
        result["checks"].append(
            "stop/restart/predecessor cleanup and close/destroy are asynchronous; no stale publication"
        )
        assert not callback_errors, callback_errors
        for dest in launches:
            path = dest / "backend-result.json"
            if path.exists():
                data = json.loads(path.read_text())
                assert data["owned_wrappers_reaped"]
                assert data["status"] in {"passed", "cancelled"}
                assert all(
                    hashlib.sha256((root / p).read_bytes()).hexdigest() == h
                    for p, h in data.get("source_sha256", {}).items()
                )
        result["status"] = "passed"
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        view.close()
        if app is not None:
            app.after_cancel(heartbeat_id)
            app.destroy()
        # Outside the event loop only, never in a user callback.
        for request in requests:
            request.cancel.set()
            if not request.done.wait(25):
                result["status"] = "failed"
                result["cleanup_error"] = "Pixel owner did not finish"
        result["requests"] = [
            {
                "generation": r.generation,
                "state": r.state,
                "error": r.error,
                "done": r.done.is_set(),
                "forced_kill": r.forced_kill,
            }
            for r in requests
        ]
    (output / "pixel-ui-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return int(result["status"] != "passed")


def coordinator(root, output, parent_net):
    assert os.readlink("/proc/self/ns/net") != parent_net
    assert [name for _, name in socket.if_nameindex()] == ["lo"]
    subprocess.run(
        ["/usr/sbin/ip", "link", "set", "lo", "up"],
        check=True,
        env={"PATH": "/usr/bin:/bin"},
        capture_output=True,
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
        "PYTHONPYCACHEPREFIX": "/nonexistent",
    }
    for key, name in (
        ("XDG_RUNTIME_DIR", "runtime"),
        ("XDG_CONFIG_HOME", "config"),
        ("XDG_CACHE_HOME", "cache"),
        ("XDG_STATE_HOME", "state"),
        ("XDG_DATA_HOME", "data"),
    ):
        env[key] = str(output / name)
    command = [
        "/usr/bin/xvfb-run",
        "-a",
        "-e",
        str(output / "ui-xvfb.log"),
        "-s",
        "-screen 0 1024x768x24 -nolisten tcp -extension GLX",
        str(root / ".venv/bin/python"),
        "-B",
        "-X",
        "pycache_prefix=/nonexistent",
        str(Path(__file__).resolve()),
        "--exercise",
        str(root),
        str(output),
    ]
    completed = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=160
    )
    (output / "ui-coordinator.log").write_text(completed.stdout + completed.stderr)
    print(completed.stdout + completed.stderr)
    return completed.returncode


def run(root, output):
    print("Private pixel UI evidence:", output, flush=True)
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
        "-X",
        "pycache_prefix=/nonexistent",
        str(Path(__file__).resolve()),
        "--coordinator",
        str(root),
        str(output),
        os.readlink("/proc/self/ns/net"),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            env={
                "PATH": "/usr/bin:/bin",
                "LC_ALL": "C.UTF-8",
                "HOME": "/nonexistent",
                "PYTHONPYCACHEPREFIX": "/nonexistent",
            },
            capture_output=True,
            text=True,
            timeout=175,
        )
    except subprocess.TimeoutExpired as exc:

        def text(value):
            return (
                value.decode(errors="replace")
                if isinstance(value, bytes)
                else value or ""
            )

        (output / "coordinator.log").write_text(text(exc.stdout) + text(exc.stderr))
        (output / "timeout.json").write_text(
            '{"status":"failed","reason":"coordinator timeout"}\n'
        )
        return 1
    (output / "coordinator.log").write_text(completed.stdout + completed.stderr)
    print(completed.stdout + completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--backend":
        raise SystemExit(
            backend(Path(sys.argv[2]), Path(sys.argv[3]), float(sys.argv[4]))
        )
    if len(sys.argv) == 5 and sys.argv[1] == "--coordinator":
        raise SystemExit(coordinator(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]))
    if len(sys.argv) == 4 and sys.argv[1] == "--exercise":
        raise SystemExit(exercise(Path(sys.argv[2]), Path(sys.argv[3])))
    raise SystemExit("Use tests/run_isolated_suite.py --projectm-pixel-ui-probe")
