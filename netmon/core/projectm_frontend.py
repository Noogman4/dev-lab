"""Optional projectM 3 PCM capsule using only private NetMon samples and display.

Prototype for the installed projectM 3.1.13 Flatpak payload and host Qt5.
No flatpak run, host audio, original user configuration, GPU or fallback start.
The UI integration is deliberately separate from this owned session boundary.
"""

from functools import lru_cache
import json
import hashlib
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import tempfile
import threading
import time

from netmon.core import projectm_profile as profiles

from netmon.core import (
    projectm_pcm,
    projectm_native,
    projectm_display,
    projectm_pixels,
    radio_sandbox as sandbox,
)
from netmon.core import projectm_archive as archive, projectm_zip
from netmon.core.archive_limits import ByteBudget, copy_limited
from netmon.core.projectm_import_plan import MAX_OUTPUT_DIRECTORIES, MAX_OUTPUT_OBJECTS

PAYLOAD = Path("/var/lib/flatpak/app/net.sourceforge.projectM/current/active/files")
UPSTREAM_COMMIT = "521eff97a5b9603ef9db58fcef4e8f1c87fae2b6"
WORKER = Path(__file__).with_name("projectm_frontend_worker.py")


def snapshot_presets(source, destination, *, playlist=None, choices=None):
    """Copy bounded regular media through directory handles; never expose its parent."""
    budget = ByteBudget(archive.MAX_TOTAL_BYTES)
    counts = {"objects": 0, "directories": 0, "files": 0, "presets": 0}
    allowed = projectm_zip.PRESET_EXTENSIONS | projectm_zip.ASSET_EXTENSIONS

    def walk(descriptor, target, depth):
        if depth > 32:
            raise ValueError("Preset staging depth exceeded.")
        with os.scandir(descriptor) as entries:
            for entry in entries:
                # Existing scan cache contains links; stage originals exactly once.
                if entry.name == ".netmon_projectm_flat_scan_v1":
                    continue
                counts["objects"] += 1
                if counts["objects"] > MAX_OUTPUT_OBJECTS:
                    raise ValueError("Preset staging object budget exceeded.")
                info = entry.stat(follow_symlinks=False)
                path = target / entry.name
                if stat.S_ISDIR(info.st_mode):
                    counts["directories"] += 1
                    if counts["directories"] > MAX_OUTPUT_DIRECTORIES:
                        raise ValueError("Preset staging directory budget exceeded.")
                    child = os.open(
                        entry.name,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                        dir_fd=descriptor,
                    )
                    try:
                        path.mkdir(mode=0o700)
                        walk(child, path, depth + 1)
                    finally:
                        os.close(child)
                elif stat.S_ISLNK(info.st_mode):
                    raise ValueError("Preset staging refuses symbolic links.")
                elif path.suffix.lower() in allowed:
                    fd = os.open(
                        entry.name,
                        os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                        dir_fd=descriptor,
                    )
                    with os.fdopen(fd, "rb") as handle:
                        current = os.fstat(handle.fileno())
                        if not stat.S_ISREG(current.st_mode) or current.st_nlink != 1:
                            raise ValueError(
                                "Preset staging requires a single regular file."
                            )
                        counts["files"] += 1
                        if counts["files"] > archive.MAX_MEMBERS:
                            raise ValueError("Preset staging file budget exceeded.")
                        with path.open("xb") as output:
                            copy_limited(
                                handle, output, archive.MAX_FILE_BYTES, budget=budget
                            )
                    counts["presets"] += (
                        path.suffix.lower() in projectm_zip.PRESET_EXTENSIONS
                    )
                    if (
                        playlist is not None
                        and path.suffix.lower() in projectm_zip.PRESET_EXTENSIONS
                    ):
                        counts["objects"] += 1
                        if counts["objects"] > MAX_OUTPUT_OBJECTS:
                            raise ValueError("Preset staging object budget exceeded.")
                        prefix = hashlib.sha256(
                            os.fsencode(path.relative_to(destination))
                        ).hexdigest()
                        name = prefix + path.suffix.lower()
                        (playlist / name).symlink_to(os.path.relpath(path, playlist))
                        if choices is not None:
                            choices.append((str(path.relative_to(destination)), name))

    descriptor = os.open(
        source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    )
    try:
        destination.mkdir(mode=0o700)
        if playlist is not None:
            playlist.mkdir(mode=0o700)
            counts["objects"] += 1
            counts["directories"] += 1
        walk(descriptor, destination, 0)
        if not counts["presets"]:
            raise ValueError("No regular projectM presets selected.")
        return {**counts, "bytes": budget.used}
    finally:
        os.close(descriptor)


def _payload():
    root = PAYLOAD.resolve(strict=True)
    base = Path("/var/lib/flatpak/app/net.sourceforge.projectM/x86_64/stable")
    if (
        root.parent.parent != base
        or root.name != "files"
        or not re.fullmatch(r"[0-9a-f]{64}", root.parent.name)
    ):
        raise sandbox.RadioSandboxError("Nicht unterstützter projectM-Paketpfad.")
    manifest = root / "manifest.json"
    with manifest.open("rb") as handle:
        data = handle.read(65537)
    if len(data) > 65536:
        raise sandbox.RadioSandboxError("projectM-Manifest überschreitet die Grenze.")
    plan = json.loads(data)
    modules = plan.get("modules", [])
    if plan.get("command") != "projectM-pulseaudio" or not any(
        m.get("name") == "projectm"
        and any(s.get("commit") == UPSTREAM_COMMIT for s in m.get("sources", []))
        for m in modules
    ):
        raise sandbox.RadioSandboxError("Nicht unterstützter projectM-Quellstand.")
    return root


@lru_cache(maxsize=1)
def _runtime():
    root = _payload()
    executable = projectm_native.artifact(root)
    stdlib, python = sandbox._pcm_runtime()
    files = set(python) | set(projectm_display._software_files())
    payload = {(executable, "/app/bin/pcm-renderer")}
    # Only our verified local artifact reaches ldd, never preset/media paths.
    result = subprocess.run(
        ["/usr/bin/ldd", str(executable)],
        env={**sandbox._ENV, "LD_LIBRARY_PATH": str(root / "lib")},
        cwd="/",
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or re.fullmatch(r"linux-vdso\S* \(0x[0-9a-fA-F]+\)", line):
            continue
        match = re.fullmatch(r"(?:\S+ => )?(/\S+) \(0x[0-9a-fA-F]+\)", line)
        if not match:
            raise sandbox.RadioSandboxError("Unvollständige projectM-Laufzeit.")
        path = Path(match[1])
        resolved = path.resolve(strict=True)
        if path.is_relative_to(root / "lib") and resolved.is_relative_to(root / "lib"):
            payload.add((resolved, "/app/lib/" + path.name))
        elif str(path).startswith(
            ("/lib/", "/lib64/", "/usr/lib/", "/usr/lib64/")
        ) and str(resolved).startswith(
            ("/lib/", "/lib64/", "/usr/lib/", "/usr/lib64/")
        ):
            files.add(path)
        else:
            raise sandbox.RadioSandboxError("Unerwartete projectM-Bibliothek.")
    for name in ("Vera.ttf", "VeraMono.ttf"):
        payload.add(
            (root / "share/projectM/fonts" / name, "/app/share/projectM/fonts/" + name)
        )
    if (
        len(files) > 512
        or any(not p.is_file() for p in files)
        or any(not p.is_file() for p, _ in payload)
    ):
        raise sandbox.RadioSandboxError("Unvollständige projectM-Laufzeit.")
    return stdlib, tuple(sorted(files)), tuple(sorted(payload))


def prepare(
    directory,
    preset_dir,
    *,
    resolution=profiles.DEFAULT,
    preset_name=None,
    cpu_profile=profiles.DEFAULT_CPU,
    backend="cpu",
    visual_eq=profiles.NEUTRAL_EQ,
):
    profile = profiles.resolve(resolution)
    cpu = profiles.resolve_cpu(cpu_profile)
    eq_record = profiles.encode_visual_eq(visual_eq)
    if backend not in {"cpu", "gpu"}:
        raise ValueError("Ungültiger projectM-Renderweg.")
    sandbox._prepare_directory(directory)
    choices = []
    counts = snapshot_presets(
        preset_dir,
        directory / "presets",
        playlist=directory / "playlist",
        choices=choices,
    )
    choices.sort(key=lambda item: (item[0].casefold(), item[0]))
    (directory / "preset-list").write_text(
        "".join(name + "\n" for _label, name in choices), encoding="ascii"
    )
    counts["preset_choices"] = tuple(label for label, _name in choices)
    selected = (
        counts["preset_choices"].index(preset_name)
        if preset_name in counts["preset_choices"]
        else None
    )
    value = 0xFFFFFFFF if selected is None else selected
    (directory / "preset-selection").write_bytes(
        struct.pack(">II", value, value ^ 0xFFFFFFFF)
    )
    counts["selected_preset"] = selected
    # Visualizer-only EQ, read-only in the renderer; the owner pwrites updates.
    (directory / "visual-eq").write_bytes(eq_record)
    (directory / "config.inp").write_text(f"""Mesh X = {220 if backend == 'gpu' else 32}
Mesh Y = {125 if backend == 'gpu' else 24}
FPS = {30 if backend == 'gpu' else cpu.fps}
Window Width = {profile.width}
Window Height = {profile.height}
Texture Size = {profile.texture}
Fullscreen = false
Preset Duration = 30
Smooth Transition Duration = 2
Preset Path = /media/playlist
Title Font = /app/share/projectM/fonts/Vera.ttf
Menu Font = /app/share/projectM/fonts/VeraMono.ttf
""")
    (directory / "fonts.conf").write_text(
        '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd">'
        "<fontconfig><dir>/app/share/projectM/fonts</dir>"
        "<cachedir>/tmp/font-cache</cachedir></fontconfig>"
    )
    return counts


def _command(
    directory,
    plan,
    display_fd,
    auth_fd,
    resolution=profiles.DEFAULT,
    cpu_profile=profiles.DEFAULT_CPU,
):
    profile = profiles.resolve(resolution)
    cpu = profiles.resolve_cpu(cpu_profile)
    stdlib, files, payload = plan
    command = sandbox._sandbox_command(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/frontend-worker.py",
            "--cpu-profile",
            cpu.key,
            "--resolution",
            profile.key,
        ],
        directory,
        files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    extra = [
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(WORKER),
        "/run/frontend-worker.py",
        "--ro-bind",
        str(Path(profiles.__file__)),
        "/run/projectm-profile.py",
        "--ro-bind-fd",
        str(display_fd),
        "/tmp/.X11-unix/X1",
        "--ro-bind-data",
        str(auth_fd),
        "/run/client.auth",
        "--ro-bind",
        str(directory / "presets"),
        "/media/presets",
        "--ro-bind",
        str(directory / "playlist"),
        "/media/playlist",
        "--ro-bind",
        str(directory / "preset-list"),
        "/media/preset-list",
        "--ro-bind",
        str(directory / "preset-selection"),
        "/run/preset-selection",
        "--ro-bind",
        str(directory / "visual-eq"),
        "/run/visual-eq",
    ]
    for source, target in payload:
        extra += ["--ro-bind", str(source), target]
    extra += ["--ro-bind", str(directory / "config.inp"), "/media/config.inp"]
    extra += ["--ro-bind", str(directory / "fonts.conf"), "/etc/fonts/fonts.conf"]
    environment = {
        "DISPLAY": ":1",
        "XAUTHORITY": "/run/client.auth",
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "GALLIUM_DRIVER": "llvmpipe",
        "LP_NUM_THREADS": str(cpu.threads),
        "LD_LIBRARY_PATH": "/app/lib",
        "FONTCONFIG_FILE": "/etc/fonts/fonts.conf",
    }
    for name, value in environment.items():
        extra += ["--setenv", name, value]
    command[command.index("--") : command.index("--")] = extra
    return command


class FrontendSession:
    def __init__(
        self,
        process,
        pcm,
        display,
        temporary,
        pixels=None,
        *,
        presets=(),
        selection_fd=None,
        resolution=profiles.DEFAULT,
        selected_preset=None,
        cpu_profile=profiles.DEFAULT_CPU,
        backend="cpu",
        eq_fd=None,
        visual_eq=profiles.NEUTRAL_EQ,
    ):
        self.resolution = profiles.resolve(resolution).key
        self.eq_fd = eq_fd
        self.visual_eq = profiles.validate_visual_eq(visual_eq)
        self.cpu_profile = profiles.resolve_cpu(cpu_profile).key
        self.backend = backend
        self.selected_preset = selected_preset
        self.presets = presets
        self.selection_fd = selection_fd
        self.pixels = pixels
        self.process, self.pcm, self.display, self.temporary = (
            process,
            pcm,
            display,
            temporary,
        )
        self.pid = process.pid
        self.sandbox_state = "started"
        self.runtime_verified = False
        self._result = None
        self._lock = threading.RLock()
        self._ended = threading.Event()
        self.thread = threading.Thread(
            target=self._watch, name="projectm-frontend", daemon=True
        )
        self.thread.start()

    def _watch(self):
        while not self._ended.wait(0.1):
            if self.poll() is not None:
                return

    def poll(self):
        with self._lock:
            if self._result is not None:
                return self._result
            result = self.process.poll()
            if (
                self.pcm.poll() is not None
                or self.display is not None
                and self.display.poll() is not None
                or self.pixels is not None
                and self.pixels.poll() is not None
            ):
                result = 2
            if result is not None:
                self._stop(result)
            return self._result

    def _stop(self, result):
        self._ended.set()
        errors = []
        for action in (
            lambda: _stop_process(self.process),
            lambda: self.pixels.stop() if self.pixels is not None else None,
            self.pcm.stop,
            lambda: self.display.stop() if self.display is not None else None,
            self._close_selection,
            self._close_eq,
            self.temporary.cleanup,
        ):
            try:
                action()
            except Exception as error:
                errors.append(error)
        self._result = 2 if errors else result
        if errors:
            raise RuntimeError("projectM-Bereinigung fehlgeschlagen") from errors[0]

    def stop(self):
        with self._lock:
            if self._result is None:
                self._stop(0)
        if threading.current_thread() is not self.thread:
            self.thread.join(timeout=1)

    def _close_selection(self):
        if self.selection_fd is not None:
            descriptor, self.selection_fd = self.selection_fd, None
            os.close(descriptor)

    def _close_eq(self):
        if self.eq_fd is not None:
            descriptor, self.eq_fd = self.eq_fd, None
            os.close(descriptor)

    def set_visual_eq(self, eq):
        """Owner-thread only: fixed 8-byte visualizer EQ record, no reply."""
        record = profiles.encode_visual_eq(eq)
        with self._lock:
            if self._result is not None or self.eq_fd is None:
                raise RuntimeError("Visualisierung ist beendet.")
            if os.pwrite(self.eq_fd, record, 0) != 8:
                raise OSError("Klangeinstellung unvollständig.")
            self.visual_eq = eq

    def select_preset(self, index):
        """Owner-thread only: fixed-size one-way index, no renderer reply."""
        if index is not None and (
            type(index) is not int or not 0 <= index < len(self.presets)
        ):
            raise ValueError("Ungültiges Preset.")
        with self._lock:
            if self._result is not None or self.selection_fd is None:
                raise RuntimeError("Visualisierung ist beendet.")
            value = 0xFFFFFFFF if index is None else index
            if (
                os.pwrite(
                    self.selection_fd, struct.pack(">II", value, value ^ 0xFFFFFFFF), 0
                )
                != 8
            ):
                raise OSError("Preset-Auswahl unvollständig.")


def start(
    playback,
    preset_dir,
    *,
    work_root=None,
    cancelled=lambda: False,
    resolution=profiles.DEFAULT,
    preset_name=None,
    cpu_profile=profiles.DEFAULT_CPU,
    backend="cpu",
    visual_eq=profiles.NEUTRAL_EQ,
):
    profile = profiles.resolve(resolution)
    cpu = profiles.resolve_cpu(cpu_profile)
    profiles.resolve_backend(backend)
    profiles.validate_visual_eq(visual_eq)
    gpu_error = ""
    if backend != "cpu":
        from netmon.core import projectm_gpu

        try:
            return projectm_gpu.start(
                playback,
                preset_dir,
                work_root=work_root,
                cancelled=cancelled,
                resolution=resolution,
                preset_name=preset_name,
                cpu_profile=cpu_profile,
                visual_eq=visual_eq,
            )
        except Exception as error:
            if (
                backend == "gpu"
                or cancelled()
                or isinstance(error, projectm_gpu.CleanupError)
            ):
                raise
            gpu_error = str(error)[:256]

    def checkpoint():
        if cancelled():
            raise sandbox.RadioSandboxError("projectM-Start wurde entwertet.")

    checkpoint()
    if not isinstance(playback, sandbox.SandboxProcess):
        raise sandbox.RadioSandboxError(
            "projectM benötigt aktive geschützte NetMon-Wiedergabe."
        )
    # D-Q1: no user manager, no resource limits, no projectM capsules.
    sandbox._require_quota_manager()
    plan = _runtime()
    checkpoint()
    temporary = tempfile.TemporaryDirectory(prefix="projectm-frontend-", dir=work_root)
    pcm = display = process = pixels = None
    selection_fd = eq_fd = None
    try:
        directory = Path(temporary.name)
        counts = prepare(
            directory,
            preset_dir,
            resolution=profile.key,
            preset_name=preset_name,
            cpu_profile=cpu.key,
            visual_eq=visual_eq,
        )
        selection_fd = os.open(
            directory / "preset-selection", os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        )
        eq_fd = os.open(
            directory / "visual-eq", os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        )
        checkpoint()
        pcm = projectm_pcm.start(playback, work_root=work_root)
        checkpoint()
        display = projectm_display.start(work_root=work_root, resolution=profile.key)
        checkpoint()
        with display.display_binding() as (display_fd, auth_fd):
            process = subprocess.Popen(
                sandbox._limited(
                    _command(
                        directory, plan, display_fd, auth_fd, profile.key, cpu.key
                    ),
                    cpu.quota,
                ),
                env=sandbox._quota_env(),
                cwd="/",
                stdin=pcm.process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                pass_fds=(display_fd, auth_fd),
                bufsize=0,
            )
        pcm.process.stdout.close()
        deadline = time.monotonic() + 5
        os.set_blocking(process.stdout.fileno(), False)
        pixels = projectm_pixels.start(
            display, work_root=work_root, cancelled=cancelled, resolution=profile.key
        )
        status, marked_frame = bytearray(), None
        while True:
            checkpoint()
            try:
                data = os.read(process.stdout.fileno(), 257 - len(status))
            except BlockingIOError:
                data = None
            if data == b"":
                raise sandbox.RadioSandboxError("PCM-Renderer wurde vorzeitig beendet.")
            if data:
                status.extend(data)
            if len(status) > 256 or (b"\n" in status and status != b"NMPM1 READY\n"):
                raise sandbox.RadioSandboxError("Ungültige PCM-Renderer-Startantwort.")
            if status == b"NMPM1 READY\n" and marked_frame is None:
                marked_frame = pixels.frames.received
            if (
                process.poll() is not None
                or pcm.poll() is not None
                or pixels.poll() is not None
            ):
                raise sandbox.RadioSandboxError("Privater PCM-Verbund wurde beendet.")
            if marked_frame is not None and pixels.frames.received > marked_frame:
                break
            if time.monotonic() >= deadline:
                raise sandbox.RadioSandboxError(
                    "Privater PCM-Start hat die Frist überschritten."
                )
            time.sleep(0.02)
        checkpoint()
        session = FrontendSession(
            process,
            pcm,
            display,
            temporary,
            pixels=pixels,
            presets=counts["preset_choices"],
            resolution=profile.key,
            selected_preset=counts["selected_preset"],
            selection_fd=selection_fd,
            cpu_profile=cpu.key,
            eq_fd=eq_fd,
            visual_eq=visual_eq,
        )
        session.gpu_error = gpu_error
        selection_fd = eq_fd = None
        return session
    except Exception as start_error:
        # Every resource is attempted, including partially completed startups.
        cleanup_errors = []
        for action in (
            lambda: _stop_process(process),
            lambda: pixels.stop() if pixels else None,
            lambda: pcm.stop() if pcm else None,
            lambda: display.stop() if display else None,
            lambda: os.close(selection_fd) if selection_fd is not None else None,
            lambda: os.close(eq_fd) if eq_fd is not None else None,
            temporary.cleanup,
        ):
            try:
                action()
            except Exception as error:
                cleanup_errors.append(type(error).__name__ + ": " + str(error)[:256])
        if cleanup_errors:
            raise sandbox.RadioSandboxError(
                "projectM-Start fehlgeschlagen; Bereinigungsfehler: "
                + "; ".join(cleanup_errors)
            ) from start_error
        raise


def _stop_process(process):
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
    else:
        process.wait(timeout=2)
    if getattr(process, "stdout", None) is not None:
        process.stdout.close()
