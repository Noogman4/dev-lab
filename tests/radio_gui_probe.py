"""Real Tk radio widgets and handover methods, without App.__init__.

Invoked only by the isolated starter's private-network GUI mode. The NetMon
host is a small Tk fixture using selected original App methods. Standalone UI,
radio tab, handover files, playback worker and Bubblewrap remain real. Desktop
launcher selection and unrelated projectM status probes are outside this test.
"""

import ast
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import traceback
import signal
from radio_stream_probe import TEST_HOST
from types import SimpleNamespace
from radio_probe_output import install, scopes_gone

WORK = Path(os.environ["NETMON_RADIO_GUI_WORK"])
ROOT = Path(os.environ["NETMON_RADIO_GUI_ROOT"])
sys.path.insert(0, str(ROOT))
PROJECTM = os.environ.get("NETMON_RADIO_GUI_PROJECTM") == "1"
PROJECTM_SESSIONS = []
PROJECTM_TASKS = {}
PRIVATE_OUTPUTS = []


def _write(path, data):
    temporary = path.with_suffix(".new")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def _read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _wait(predicate, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("GUI test deadline; see live JSON and GUI logs")


def _alive(pid):
    import psutil

    try:
        return (
            psutil.Process(pid).is_running()
            and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
        )
    except psutil.NoSuchProcess:
        return False


def _install_guards(role):
    blocked = {
        "sudo",
        "pkexec",
        "doas",
        "nmcli",
        "ufw",
        "wg",
        "wg-quick",
        "systemctl",
        "service",
        "mount",
        "umount",
        "resolvectl",
        "iptables",
        "ip6tables",
        "nft",
        "apt",
        "apt-get",
        "pkill",
        "gtk-launch",
        "xdg-open",
        "flatpak",
    }
    original_popen = subprocess.Popen
    playback_log = (WORK / f"{role}-mpv.log").open("a")

    class GuardedPopen(original_popen):
        def __init__(self, command, *args, **kwargs):
            name = Path(command[0]).name
            readonly_flatpak = name == "flatpak" and command[1:] == ["list"]
            if kwargs.get("shell") or (name in blocked and not readonly_flatpak):
                _write(WORK / "guard-error.json", {"command": name})
                raise AssertionError("Unexpected command in GUI fixture")
            if name in {"bwrap", "systemd-run"} and "/usr/bin/mpv" in command:
                kwargs["stderr"] = playback_log
            super().__init__(command, *args, **kwargs)
            standalone = str(Path(__file__).resolve()) in command and name.startswith(
                "python"
            )
            if name in {"bwrap", "systemd-run"} or standalone:
                import psutil

                try:
                    born = psutil.Process(self.pid).create_time()
                except psutil.NoSuchProcess:
                    born = None
                with (WORK / "owned-wrappers.jsonl").open("a") as log:
                    log.write(
                        json.dumps(
                            {
                                "pid": self.pid,
                                "role": role,
                                "born": born,
                                "owner_pid": os.getpid(),
                                "kind": "standalone" if standalone else "bwrap",
                            }
                        )
                        + "\n"
                    )

    subprocess.Popen = GuardedPopen
    original_socket = socket.socket

    class GuardedSocket(original_socket):
        def connect(self, address):
            if self.family in (socket.AF_INET, socket.AF_INET6):
                private_fixture = address[0] == TEST_HOST and os.readlink(
                    "/proc/self/ns/net"
                ) == os.environ.get("NETMON_RADIO_GUI_NET_NS")
                if (
                    not ipaddress.ip_address(address[0]).is_loopback
                    and not private_fixture
                ):
                    _write(WORK / "guard-error.json", {"network": "non-loopback"})
                    raise AssertionError("Unexpected external connection")
            return super().connect(address)

    socket.socket = GuardedSocket


def _modules():
    from netmon import netmon_radio_app as ui
    from netmon import netmon_radio_core as core
    from netmon.features import radio_controller as radio
    from netmon.core import radio_sandbox as sandbox

    _restore, outputs, _audits = install(sandbox, WORK)
    PRIVATE_OUTPUTS.append((_restore, outputs, _audits))

    if not PROJECTM:
        # The existing baseline remains a radio-only transition test.
        ui.NetMonRadioApp._refresh_projectm_status = lambda _self: None
    else:
        from netmon.core import projectm_frontend as frontend
        from netmon import netmon_projectm_sidecar as sidecar

        frontend._payload()  # Real fixed installed deployment, never a substitute binary.
        sidecar.probe_projectm_package_candidates = lambda **_: {
            "flatpak_path": "/usr/bin/flatpak",
            "flatpak_projectm_installed": True,
            "installable": False,
            "install_strategy": "installed",
        }
        original_start = frontend.start

        def audited_start(*args, **kwargs):
            session = original_start(*args, **kwargs)
            try:
                assert session.pcm.feed.forwarded > 0
                assert session.pcm.process.poll() is None
                command = frontend._command(
                    Path(session.temporary.name), frontend._runtime(), 10, 11
                )
                assert "/run/audio/pulse" not in command
                assert not any("PULSE_" in x for x in command)
                session._test_audit = {
                    "transport": "one-way-pcm",
                    "pulse_socket": False,
                }
                PROJECTM_SESSIONS.append(session)
                return session
            except Exception:
                session.stop()
                raise

        frontend.start = audited_start
    original_builder = core.build_radio_wrapper_command

    def instrumented_command(**kwargs):
        kwargs["python_executable"] = sys.executable
        command = original_builder(**kwargs)
        command[1] = str(Path(__file__).resolve())
        command.insert(1, "-B")
        return command

    core.build_radio_wrapper_command = instrumented_command
    core._radio_launch_desktop_hint = lambda _environment: ""
    return ui, core, radio


def _snapshot(app, role, *, handled=0):
    from netmon import netmon_radio_core as core

    target = app.__dict__.get("radio_embedded_panel") if role == "host" else app
    process = target.__dict__.get("radio_proc") if target is not None else None
    result = {
        "pid": os.getpid(),
        "role": role,
        "handled": handled,
        "mode": app.__dict__.get("radio_launcher_mode", "standalone"),
        "playing": process is not None
        and not (
            target.__dict__.get("radio_playback_request")
            and target.radio_playback_request.finished.is_set()
        ),
        "wrapper_pid": process.pid if process is not None else 0,
        "fifo_bytes": process._output.count if process is not None else 0,
        "gate_done": (
            process._output_gate.done.is_set() if process is not None else True
        ),
        "quota_audit": (
            getattr(process, "_probe_quota", []) if process is not None else []
        ),
        "pcm_wrapper_pid": (process._pcm_process.pid if process is not None else 0),
        "source_wrapper_pid": (
            process._source_process.pid
            if process is not None and process._source_process is not None
            else 0
        ),
        "ipc_path": getattr(process, "ipc_path", "") if process is not None else "",
        "netmon_available": core.netmon_host_is_available(),
    }
    if PROJECTM:
        import psutil

        for session in PROJECTM_SESSIONS:
            for process in (
                session.process,
                session.pcm.process,
                session.display.process,
            ):
                try:
                    if process.poll() is not None:
                        continue
                    root = psutil.Process(process.pid)
                    for task in [root, *root.children(recursive=True)]:
                        born = task.create_time()
                        PROJECTM_TASKS[(task.pid, born)] = {
                            "pid": task.pid,
                            "born": born,
                        }
                except psutil.NoSuchProcess:
                    pass
        result["projectm_tasks"] = list(PROJECTM_TASKS.values())
        result["projectm_capsules"] = len(PROJECTM_SESSIONS)
        request = (
            vars(target).get("radio_projectm_proc") if target is not None else None
        )
        result["projectm_phase"] = (
            request.snapshot()[0] if request is not None else "none"
        )
        if PROJECTM_SESSIONS:
            latest = PROJECTM_SESSIONS[-1]
            result["projectm_audit"] = latest._test_audit
            result["projectm_roots"] = [
                p.pid
                for p in (
                    latest.process,
                    latest.pcm.process,
                    latest.display.process,
                    latest.pixels.process,
                )
            ]
            result["projectm_directories"] = [
                s.temporary.name
                for s in (latest, latest.pcm, latest.display, latest.pixels)
            ]
            window = (
                vars(target).get("_projectm_pixel_window")
                if target is not None
                else None
            )
            result["projectm_pixels_displayed"] = (
                window.displayed if window is not None else 0
            )
    if role == "standalone":
        result["attach_enabled"] = (
            str(app.radio_attach_button.cget("state")) != "disabled"
        )
        result["attach_status"] = app.radio_attach_status_var.get()
    if target is not None:
        recording = target.__dict__.get("radio_record_proc")
        request = target.__dict__.get("radio_record_request")
        result["recording"] = (
            recording is not None and request is not None and not request.done.is_set()
        )
        result["recording_pending"] = target.__dict__.get(
            "radio_record_starting", False
        )
        result["recording_pid"] = recording.pid if recording is not None else 0
        result["recording_source_pid"] = (
            recording._source_process.pid if recording is not None else 0
        )
        result["recording_path"] = target.__dict__.get("radio_last_record_path", "")
        result["recording_status"] = target.radio_record_status_var.get()
        result["preset_download_ok"] = target.__dict__.get(
            "_test_preset_download_ok", False
        )
        result["preset_files"] = target.__dict__.get("_test_preset_files", [])
        photo = target.__dict__.get("_radio_logo_photo")
        if target.__dict__.get("_radio_logo_loaded_key") and photo is not None:
            result["logo_dimensions"] = [photo.width(), photo.height()]
            result["logo_pixel"] = target.tk.call(str(photo), "get", 0, 0)
            result["logo_transparent"] = (
                target.tk.call(str(photo), "transparency", "get", 1, 0)
                if photo.width() == 2
                else None
            )
        result.update(
            {
                "station_id": target.radio_current_station_id,
                "volume": target.radio_volume_var.get(),
                "volume_label": target.radio_volume_label_var.get(),
                "eq": [
                    target.radio_eq_bass_var.get(),
                    target.radio_eq_mid_var.get(),
                    target.radio_eq_treble_var.get(),
                ],
                "search": target.radio_search_var.get(),
                "sandbox_state": target.__dict__.get("radio_sandbox_state", ""),
                "status": target.radio_status_var.get(),
                "title": target.radio_title_var.get(),
            }
        )
    previous = _read(WORK / f"{role}-live.json")
    if any(
        previous.get(key) != result.get(key)
        for key in ("pid", "mode", "playing", "wrapper_pid", "sandbox_state")
    ):
        with (WORK / "gui-events.jsonl").open("a") as log:
            log.write(json.dumps({"time": time.monotonic(), **result}) + "\n")
    _write(WORK / f"{role}-live.json", result)
    return result


def _ui_loop(role):
    import tkinter as tk
    from tkinter import ttk

    _install_guards(role)
    ui, core, radio = _modules()

    def callback_error(kind, value, trace):
        _write(
            WORK / "callback-error.json",
            {
                "role": role,
                "trace": "".join(traceback.format_exception(kind, value, trace)),
            },
        )

    if role == "standalone":
        started_from = "netmon_detach"
        if "--started-from" in sys.argv:
            started_from = sys.argv[sys.argv.index("--started-from") + 1]
        app = ui.NetMonRadioApp(started_from=started_from)
    else:
        from netmon.ui.tabs import radio_tab

        source_path = ROOT / "netmon/app.py"
        tree = ast.parse(source_path.read_text())
        app_class = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "App"
        )
        selected = {
            "open_radio_external_app",
            "reattach_radio_app",
            "_poll_radio_attach_request",
            "on_close",
            "_current_radio_theme_name",
            "_sync_radio_theme_to_current_theme",
        }
        methods = [
            node
            for node in app_class.body
            if isinstance(node, ast.FunctionDef) and node.name in selected
        ]
        assert len(methods) == len(selected)
        namespace = {
            "os": os,
            "json": json,
            "netmon_radio_core": core,
            "radio_controller": radio,
            "LIGHT_THEME": ui.LIGHT_THEME,
        }
        exec(
            compile(
                ast.Module(body=methods, type_ignores=[]), str(source_path), "exec"
            ),
            namespace,
        )

        class Host(tk.Tk):
            def __init__(self):
                super().__init__(className="NetMonRadioTestHost")
                self.title("Isolierter NetMon Radio-Testhost")
                self.geometry("1200x900")
                self._app_theme = dict(ui.DARK_THEME)
                self.settings = {"theme": "dark"}
                self.radio_settings = radio.default_radio_settings()
                self.radio_current_station_id = "sandbox-test"
                self.netmon_radio_core = core
                ui._init_radio_runtime_paths(self)
                self.tools_nb = ttk.Notebook(self)
                self.tools_nb.pack(fill="both", expand=True)
                assert core.write_netmon_host_state(os.getpid())
                if core.standalone_radio_is_running():
                    core.set_radio_detached_state(True)
                else:
                    core.write_radio_host_state(
                        mode="embedded", owner_pid=os.getpid(), started_from="netmon"
                    )
                    core.set_radio_detached_state(False)
                radio_tab.build_radio_tab(self)
                self.after(100, self._poll_radio_attach_request)

            def tr(self, _key, default=None):
                return default or _key

            def register_feature_button(self, *_args):
                pass

            def log_safe(self, message):
                print(message, flush=True)

            def _record_diagnostic_action(self, *_args, **_kwargs):
                pass

            def _log_radio_theme_diagnostic(self, _stage):
                pass

            def _normalize_theme_name(self, value):
                return value

            def apply_theme(self, name, **_kwargs):
                self._app_theme = dict(
                    ui.DARK_THEME if name == "dark" else ui.LIGHT_THEME
                )

            def save_settings(self):
                pass

            def stop_running_fun_game(self):
                pass

            def stop_radio(self):
                panel = self.__dict__.get("radio_embedded_panel")
                if panel is not None:
                    panel.stop_radio_playback(async_mode=False)

        for name in selected:
            setattr(Host, name, namespace[name])
        app = Host()

    app.report_callback_exception = callback_error
    handled = 0

    def heartbeat():
        nonlocal handled
        request = _read(WORK / f"{role}-request.json")
        if request.get("sequence", 0) > handled and (
            not PROJECTM or request.get("target_pid") == os.getpid()
        ):
            handled = request["sequence"]
            action = request["action"]
            target = app.radio_embedded_panel if role == "host" else app
            if action in {"projectm-start", "projectm-stop"}:
                method = (
                    "open_projectm_visualizer_test"
                    if action == "projectm-start"
                    else "close_projectm_visualizer_test"
                )
                pending = [target]
                buttons = []
                while pending:
                    widget = pending.pop()
                    pending.extend(widget.winfo_children())
                    if widget.winfo_class() == "TButton" and method in str(
                        widget.cget("command")
                    ):
                        buttons.append(widget)
                assert buttons, "Original projectM button missing"
                buttons[0].invoke()
            elif action == "station-change":
                radio.play_radio_station(target, request["station"])
            elif action == "play":
                panel = app.radio_embedded_panel
                panel.radio_volume_var.set(37)
                panel.on_radio_volume_preview()
                panel.radio_eq_bass_var.set(2)
                panel.radio_eq_mid_var.set(-1)
                panel.radio_eq_treble_var.set(3)
                panel.radio_search_var.set("Sandbox Test")
                panel.on_radio_eq_preview()
                app.radio_embedded_panel.radio_play()
            elif action == "detach":
                app.radio_embedded_panel.radio_detach_button.invoke()
            elif action == "record-start":
                app.radio_embedded_panel.start_radio_recording()
            elif action == "record-stop":
                app.radio_embedded_panel.stop_radio_recording()
            elif action == "record-pending":
                panel = app.radio_embedded_panel
                station = radio._resolve_target_station(panel, "sandbox-test")
                original_url = station["url"]
                station["url"] = (
                    f"http://{TEST_HOST}:{_read(WORK / 'ready.json')['port']}/hang"
                )
                try:
                    panel.start_radio_recording()
                finally:
                    station["url"] = original_url
            elif action == "preset-download":
                panel = app.radio_embedded_panel
                preset_root = Path(
                    ui.netmon_projectm_sidecar.get_projectm_preset_dir(panel)
                ).resolve()
                assert preset_root.is_relative_to(
                    WORK.resolve()
                ), "Preset fixture must stay inside private work directory"
                original_prompt = ui.simpledialog.askstring
                ui.simpledialog.askstring = (
                    lambda *_a, **_k: f"http://{TEST_HOST}:{_read(WORK / 'ready.json')['port']}/preset-good"
                )
                try:
                    panel._test_preset_download_ok = (
                        panel.download_projectm_preset_pack()
                    )
                finally:
                    ui.simpledialog.askstring = original_prompt
                panel._test_preset_files = [
                    str(path.relative_to(WORK))
                    for path in preset_root.rglob("one.milk")
                ]
            elif action == "attach":
                app.reattach_radio_app()
            elif action == "capture":
                from PIL import ImageGrab

                app.update_idletasks()
                ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
                    WORK / request["file"]
                )
            elif action == "close":
                app.on_close()
        _snapshot(app, role, handled=handled)
        app.after(100, heartbeat)

    app.after(100, heartbeat)
    app.mainloop()


def _scenario():
    import psutil
    from netmon import netmon_radio_core as core
    from netmon.features import radio_controller as radio
    from radio_stream_probe import _ipc

    results = {
        "status": "failed",
        "checks": [],
        "observations": [],
        "host_netmon_started": False,
        "active_projectm": PROJECTM,
        "audio_transport": "real product PCM gate and private FIFO reader",
        "pipewire_graph_tested": False,
    }
    results["scope"] = "original radio widgets and handover methods in a Tk fixture"
    results["complete_gui_acceptance"] = False
    files = [
        "netmon/core/radio_sandbox.py",
        "netmon/core/radio_pcm.py",
        "netmon/core/projectm_profile.py",
        "netmon/core/radio_fetch.py",
        "netmon/core/radio_catalog.py",
        "netmon/core/radio_logo.py",
        "netmon/core/icon_http.py",
        "netmon/core/icon_payload.py",
        "netmon/core/projectm_archive.py",
        "netmon/core/projectm_zip.py",
        "netmon/core/projectm_process.py",
        "netmon/core/projectm_import_plan.py",
        "netmon/netmon_projectm_sidecar.py",
        "netmon/core/projectm_transport.py",
        "netmon/core/archive_limits.py",
        "netmon/app.py",
        "netmon/netmon_radio_app.py",
        "netmon/netmon_radio_core.py",
        "netmon/features/radio_controller.py",
        "netmon/ui/tabs/radio_tab.py",
        "tests/radio_gui_probe.py",
        "tests/radio_probe_output.py",
        "tests/radio_stream_probe.py",
        "tests/run_isolated_suite.py",
    ]
    if PROJECTM:
        files.extend(
            [
                "netmon/core/projectm_frontend.py",
                "netmon/core/projectm_frontend_worker.py",
                "netmon/core/projectm_pcm.py",
                "netmon/core/projectm_pcm_worker.py",
                "netmon/core/projectm_native.py",
                "netmon/native/projectm_pcm/pcm_renderer.cpp",
                "netmon/native/projectm_pcm/build/pcm-renderer",
                "netmon/native/projectm_pcm/build/build.json",
                "netmon/core/projectm_display.py",
                "netmon/core/projectm_display_worker.py",
                "netmon/core/projectm_pixels.py",
                "netmon/core/projectm_pixel_worker.py",
                "netmon/ui/projectm_pixel_window.py",
                "tests/projectm_frontend_probe.py",
                "tests/radio_stream_probe.py",
                "tests/run_isolated_suite.py",
            ]
        )
    results["source_sha256"] = {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files
    }
    hosts = []
    standalone_pids = set()
    wrapper_pids = set()
    log_handles = []
    sequence = 0
    identities = {}
    pidfds = {}

    def sync_owned():
        path = WORK / "owned-wrappers.jsonl"
        if not path.exists():
            return
        entries = [json.loads(line) for line in path.read_text().splitlines()]
        for _ in range(2):
            for entry in entries:
                pid, born, owner = (
                    entry["pid"],
                    entry.get("born"),
                    entry.get("owner_pid"),
                )
                key = (pid, born)
                if born is None or key in pidfds or owner not in identities:
                    continue
                descriptor = None
                try:
                    process = psutil.Process(pid)
                    if (
                        process.create_time() != born
                        or process.ppid() != owner
                        or psutil.Process(owner).create_time() != identities[owner]
                    ):
                        continue
                    descriptor = os.pidfd_open(pid)
                    verified = psutil.Process(pid)
                    if (
                        verified.create_time() != born
                        or verified.ppid() != owner
                        or psutil.Process(owner).create_time() != identities[owner]
                    ):
                        os.close(descriptor)
                        continue
                    pidfds[key] = descriptor
                    if entry.get("kind") == "standalone":
                        identities[pid] = born
                except (psutil.NoSuchProcess, ProcessLookupError):
                    if descriptor is not None:
                        os.close(descriptor)

    def same_task(task):
        try:
            process = psutil.Process(task["pid"])
            return (
                process.create_time() == task["born"]
                and process.status() != psutil.STATUS_ZOMBIE
            )
        except psutil.NoSuchProcess:
            return False

    def projectm_running(role):
        data = _read(WORK / f"{role}-live.json")
        sync_owned()
        if data.get("projectm_phase") != "running" or not data.get("projectm_tasks"):
            return False
        if not all(_alive(pid) for pid in data.get("projectm_roots", [])):
            return False
        if not data.get("projectm_pixels_displayed"):
            return False
        assert data["projectm_audit"] == {
            "transport": "one-way-pcm",
            "pulse_socket": False,
        }
        return data

    def projectm_gone(data):
        sync_owned()
        return all(not same_task(task) for task in data["projectm_tasks"]) and all(
            not Path(p).exists() for p in data["projectm_directories"]
        )

    def host():
        for name in ("host-request.json", "host-live.json"):
            (WORK / name).unlink(missing_ok=True)
        log = (WORK / f"host-{len(hosts) + 1}.log").open("w")
        log_handles.append(log)
        process = subprocess.Popen(
            [sys.executable, "-B", str(Path(__file__).resolve()), "--host"],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
        hosts.append(process)
        identities[process.pid] = psutil.Process(process.pid).create_time()
        _wait(lambda: _read(WORK / "host-live.json").get("pid") == process.pid)
        return process

    def command(action, *, role="host", **extra):
        nonlocal sequence
        sequence += 1
        _write(
            WORK / f"{role}-request.json",
            {
                "sequence": sequence,
                "action": action,
                "target_pid": _read(WORK / f"{role}-live.json").get("pid"),
                **extra,
            },
        )
        if action != "close":
            _wait(lambda: _read(WORK / f"{role}-live.json").get("handled") == sequence)

    def playback(role, station_id="sandbox-test"):
        sync_owned()
        data = _read(WORK / f"{role}-live.json")
        if not data.get("playing") or not _alive(data.get("pid", 0)):
            return False
        try:
            reply = _ipc(
                SimpleNamespace(ipc_path=data["ipc_path"]), ["get_property", "time-pos"]
            )
            if (
                reply.get("error") != "success"
                or not isinstance(reply.get("data"), (int, float))
                or reply["data"] < 0.3
            ):
                return False
            player = SimpleNamespace(ipc_path=data["ipc_path"])
            volume = _ipc(player, ["get_property", "volume"])
            filters = _ipc(player, ["get_property", "af"])
            if volume.get("error") != "success" or filters.get("error") != "success":
                return False
            assert volume["data"] == 37
            assert "equalizer" in json.dumps(filters["data"])
            data["decoder_volume"] = volume["data"]
            data["decoder_filters"] = filters["data"]
        except (OSError, ValueError):
            return False
        if data["station_id"] != station_id:
            return False
        assert data["volume"] == 37
        assert data["volume_label"] == "37%"
        assert data["eq"] == [2, -1, 3]
        assert data["search"] == "Sandbox Test"
        assert data["sandbox_state"] == "started"
        if data.get("logo_dimensions") != [2, 1]:
            return False
        assert data["logo_pixel"] == [255, 0, 0]
        assert data["logo_transparent"] == 1
        wrapper_pids.add(data["wrapper_pid"])
        if data["fifo_bytes"] < 4096 or data["gate_done"]:
            return False
        assert len(data["quota_audit"]) == 3
        assert _alive(data["pcm_wrapper_pid"])
        wrapper_pids.add(data["pcm_wrapper_pid"])
        if data["source_wrapper_pid"]:
            wrapper_pids.add(data["source_wrapper_pid"])
        data["time_pos"] = reply["data"]
        return data

    def detached():
        command("detach")
        state = _wait(lambda: playback("standalone"))
        standalone_pids.add(state["pid"])
        _wait(lambda: _read(WORK / "host-live.json").get("mode") == "detached")
        return state

    def attached(standalone):
        command("attach")
        state = _wait(lambda: playback("host"))
        _wait(lambda: not _alive(standalone["pid"]))
        assert core.read_radio_host_state()["launcher_state"] == "embedded_active"
        return state

    try:
        paths = core.build_radio_paths()
        port = _read(WORK / "ready.json")["port"]
        station = {
            "id": "sandbox-test",
            "name": "Sandbox Test",
            "url": f"http://{TEST_HOST}:{port}/tone.wav",
            "favicon": f"http://{TEST_HOST}/logo-ok",
            "category": "Test",
        }
        stations = [station]
        if PROJECTM:
            stations.append(
                {**station, "id": "sandbox-test-2", "name": "Sandbox Test Two"}
            )
        for path in (
            paths.radio_db_path,
            paths.radio_stations_path,
            paths.radio_favorites_path,
        ):
            _write(Path(path), stations)
        settings = radio.default_radio_settings()
        settings.update(
            {
                "theme": "dark",
                "volume": 37,
                "eq_bass": 2,
                "eq_mid": -1,
                "eq_treble": 3,
                "last_station_id": "sandbox-test",
                "last_search": "Sandbox Test",
            }
        )
        _write(Path(paths.radio_settings_path), settings)

        first_host = host()
        command("preset-download")
        preset_state = _wait(
            lambda: (
                data
                if (data := _read(WORK / "host-live.json")).get("preset_download_ok")
                else False
            )
        )
        assert preset_state["preset_files"]
        results["preset_files"] = preset_state["preset_files"]
        results["checks"].append(
            "radio UI downloads synthetic ZIP through protected source and offline ZIP worker into private fixture preset directory; no visualizer launch"
        )
        command("play")
        embedded = _wait(lambda: playback("host"))
        _wait(
            lambda: "Private Test Artist - Test Track"
            in _read(WORK / "host-live.json").get("title", ""),
            timeout=18,
        )
        results["icy_title_display"] = _read(WORK / "host-live.json")["title"]
        results["checks"].append(
            "real Tk displays bounded raw RGBA logo with red and transparent pixels in embedded/standalone handovers"
        )
        if PROJECTM:
            command("projectm-start")
            first_visual = _wait(lambda: projectm_running("host"), timeout=25)
            results["observations"].append(
                {"stage": "embedded projectM", **first_visual}
            )
            command("station-change", station="sandbox-test-2")
            _wait(lambda: playback("host", "sandbox-test-2"))
            _wait(lambda: projectm_gone(first_visual))
            assert _read(WORK / "host-live.json")["projectm_phase"] in {
                "stopped",
                "error",
            }
            command("station-change", station="sandbox-test")
            embedded = _wait(lambda: playback("host"))
            command("projectm-start")
            embedded_visual = _wait(lambda: projectm_running("host"), timeout=25)
            results["checks"].append(
                "real embedded projectM consumes the private HTTP/mpv NetMon source; actual station change reaps its old renderer/audio/display without automatic restart"
            )
        command("record-start")
        record_state = _wait(
            lambda: (
                data
                if (data := _read(WORK / "host-live.json")).get("recording")
                else False
            )
        )
        recorded_path = Path(record_state["recording_path"])
        _wait(lambda: recorded_path.exists() and recorded_path.stat().st_size > 30000)
        command("record-stop")
        _wait(
            lambda: not _alive(record_state["recording_pid"])
            and not _alive(record_state["recording_source_pid"])
        )
        _wait(
            lambda: _read(WORK / "host-live.json").get("recording_status")
            == "Aufnahme gestoppt."
        )
        assert recorded_path.stat().st_size > 30000
        results["recording_file"] = {
            "bytes": recorded_path.stat().st_size,
            "mode": oct(recorded_path.stat().st_mode & 0o777),
        }
        command("record-pending")
        _wait(lambda: "/hang" in (WORK / "http.log").read_text().splitlines())
        command("record-stop")
        _wait(
            lambda: (
                not (data := _read(WORK / "host-live.json")).get("recording_pending")
                and data.get("recording_status") == "Aufnahme gestoppt."
            ),
            timeout=8,
        )
        assert (
            _read(WORK / "host-live.json")["recording_status"] == "Aufnahme gestoppt."
        )
        results["checks"].append(
            "Tk recording starts after encoder progress, stops and flushes; cancelling a real pending HTTP start leaves stop status and no late process"
        )
        command("record-start")
        detach_recording = _wait(
            lambda: (
                data
                if (data := _read(WORK / "host-live.json")).get("recording")
                else False
            )
        )
        command("capture", file="gui-embedded.png")
        external = detached()
        if PROJECTM:
            _wait(lambda: projectm_gone(embedded_visual))
            assert _read(WORK / "standalone-live.json").get("projectm_phase") == "none"
            command("projectm-start", role="standalone")
            external_visual = _wait(lambda: projectm_running("standalone"), timeout=25)
            results["checks"].append(
                "detach ends embedded projectM and all observed tasks/private directories; original standalone projectM button starts a new private source consumer"
            )
        _wait(lambda: not _alive(embedded["wrapper_pid"]))
        _wait(
            lambda: not _alive(detach_recording["recording_pid"])
            and not _alive(detach_recording["recording_source_pid"])
        )
        results["checks"].append(
            "detaching retains previous behavior: recording ends, encoder/source are reaped and standalone playback resumes"
        )
        results["checks"].append(
            "real radio widgets detach: selected station, volume, EQ and search preserved; old sandbox ends"
        )
        attached(external)
        if PROJECTM:
            _wait(lambda: projectm_gone(external_visual))
            assert _read(WORK / "host-live.json")["projectm_phase"] in {
                "none",
                "stopped",
                "error",
            }
            results["checks"].append(
                "attach ends standalone renderer/audio/display and its observed descendants; embedded playback resumes without adopting a foreign generation"
            )
        results["checks"].append(
            "real standalone attach request restores embedded playback and ends standalone process"
        )
        external = detached()
        if PROJECTM:
            command("projectm-start", role="standalone")
            surviving_visual = _wait(lambda: projectm_running("standalone"), timeout=25)
        initial_position = external["time_pos"]
        command("capture", file="gui-detached.png")
        command("close")
        first_host.wait(timeout=8)
        assert _alive(external["pid"])
        continued = _wait(
            lambda: (
                data
                if (data := playback("standalone"))
                and data["time_pos"] > initial_position + 0.3
                else False
            )
        )
        results["continued_after_host_exit"] = continued
        if PROJECTM:
            alive_visual = _wait(lambda: projectm_running("standalone"))
            assert alive_visual["projectm_roots"] == surviving_visual["projectm_roots"]
            assert all(same_task(task) for task in surviving_visual["projectm_tasks"])
            results["checks"].append(
                "closing original host preserves the same standalone projectM renderer/audio/display and its advancing HTTP/mpv playback"
            )
        assert not core.netmon_host_is_available()
        assert core.read_radio_host_state()["owner_pid"] == external["pid"]

        def host_inactive_status():
            state = _read(WORK / "standalone-live.json")
            if state and not state["netmon_available"] and not state["attach_enabled"]:
                return state
            return False

        stopped_host_status = _wait(host_inactive_status)
        results["host_unavailable_status"] = stopped_host_status
        results["checks"].append(
            "standalone GUI and owned sandbox keep playing after original host process exits"
        )

        second_host = host()
        _wait(lambda: _read(WORK / "host-live.json").get("mode") == "detached")
        assert core.netmon_host_is_available()
        assert core.read_netmon_host_state()["pid"] == second_host.pid
        assert core.read_radio_host_state()["owner_pid"] == external["pid"]
        _wait(
            lambda: (
                _read(WORK / "standalone-live.json").get("netmon_available")
                and _read(WORK / "standalone-live.json").get("attach_enabled")
            )
        )
        attached(external)
        if PROJECTM:
            _wait(lambda: projectm_gone(surviving_visual))
            command("projectm-start")
            closing_visual = _wait(lambda: projectm_running("host"), timeout=25)
            results["checks"].append(
                "new host reattaches active standalone projectM by ending that generation before starting a new embedded one"
            )
        results["checks"].append(
            "new test host reattaches the surviving standalone radio"
        )
        command("close")
        second_host.wait(timeout=8)
        if PROJECTM:
            _wait(lambda: projectm_gone(closing_visual))
            results["checks"].append(
                "embedded host close reaps the active projectM generation and all observed tasks/private session directories"
            )
        assert not core.netmon_host_is_available()
        wrapper_pids.update(
            json.loads(line)["pid"]
            for line in (WORK / "owned-wrappers.jsonl").read_text().splitlines()
        )
        _wait(lambda: all(not _alive(pid) for pid in wrapper_pids | standalone_pids))
        assert not (WORK / "callback-error.json").exists()
        assert not (WORK / "guard-error.json").exists()
        results["checks"].append(
            "embedded host close leaves no tracked decoder, PCM relay, source or standalone; FIFO readers joined"
        )
        results["status"] = "passed"
    except Exception:
        results["error"] = traceback.format_exc()
    finally:
        sync_owned()
        for process in hosts:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=3)
        for descriptor in pidfds.values():
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            except ProcessLookupError:
                pass
            finally:
                os.close(descriptor)
        for handle in log_handles:
            handle.close()
        try:
            from netmon.core import radio_sandbox as sandbox

            entries = []
            for path in WORK.glob("scope-audit-*.json"):
                entries.extend(json.loads(path.read_text()))
            assert entries, "no real scope/limit audit recorded"
            results["scopes_after"] = scopes_gone(sandbox, entries)
            sinks = [json.loads(path.read_text()) for path in WORK.glob("sink-*.json")]
            opened = [
                json.loads(path.read_text()) for path in WORK.glob("opened-sink-*.json")
            ]
            assert len(sinks) == len(opened), "missing FIFO reader completion audit"
            assert {item["audit"] for item in opened} == {
                path.name for path in WORK.glob("sink-*.json")
            }
            assert not [
                path for path in WORK.glob("sink-*") if path.is_dir()
            ], "unclosed private FIFO sink"
            assert sinks and all(
                s["reader_joined"] and s["fifo_removed"] and not s["error"]
                for s in sinks
            )
            results["fifo_sinks"] = sinks
            results["fifo_opened"] = len(opened)
        except Exception:
            results["status"] = "failed"
            results["cleanup_error"] = traceback.format_exc()
        results["sources_unchanged_after"] = all(
            hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value
            for name, value in results["source_sha256"].items()
        )
        if not results["sources_unchanged_after"]:
            results["status"] = "failed"
    _write(WORK / "radio-gui-result.json", results)
    print(json.dumps(results, indent=2), flush=True)
    return 0 if results["status"] == "passed" else 1


if __name__ == "__main__":
    if "--scenario" in sys.argv:
        raise SystemExit(_scenario())
    try:
        _ui_loop("host" if "--host" in sys.argv else "standalone")
    except Exception:
        _write(
            WORK / "gui-start-error.json",
            {"pid": os.getpid(), "trace": traceback.format_exc()},
        )
        raise
