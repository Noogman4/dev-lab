"""Offscreen EGL renderer: one DRM render node, fixed RGBA pipe, no desktop."""

from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
from types import SimpleNamespace

from netmon.core import projectm_profile as profiles, radio_sandbox as sandbox

GL = Path("/usr/lib/x86_64-linux-gnu")
VENDOR = Path("/usr/share/glvnd/egl_vendor.d/50_mesa.json")
# Shared EGL interface; proprietary NVIDIA needs a separately tested device profile.
DRIVERS = {
    ("0x1002", "amdgpu"): "radeonsi",
    ("0x8086", "i915"): "iris",
    ("0x8086", "xe"): "iris",
    ("0x10de", "nouveau"): "nouveau",
}


class CleanupError(sandbox.RadioSandboxError):
    """A failed GPU cleanup must never be followed by a second renderer."""


@dataclass(frozen=True)
class Device:
    path: str
    sysfs: str
    vendor: str
    driver: str
    dri: str
    major: int
    minor: int


def inspect_device(path):
    path = Path(path)
    if path.parent != Path("/dev/dri") or not re.fullmatch(
        r"renderD[0-9]{3,5}", path.name
    ):
        raise ValueError("Ungültiger GPU-Render-Knoten.")
    info = path.lstat()
    if (
        not stat.S_ISCHR(info.st_mode)
        or os.major(info.st_rdev) != 226
        or os.minor(info.st_rdev) < 128
    ):
        raise ValueError("Ungültiger GPU-Gerätetyp.")
    device = (Path("/sys/class/drm") / path.name / "device").resolve(strict=True)
    if not device.is_relative_to("/sys/devices"):
        raise ValueError("Ungültige GPU-Zuordnung.")
    vendor = (device / "vendor").read_text().strip()
    driver = (device / "driver").resolve(strict=True).name
    dri = DRIVERS.get((vendor, driver))
    if (
        not dri
        or not (GL / "dri" / (dri + "_dri.so")).is_file()
        or not VENDOR.is_file()
    ):
        raise ValueError("Kein unterstütztes GPU-Treiberprofil verfügbar.")
    if not os.access(path, os.R_OK | os.W_OK):
        raise ValueError("Kein Zugriff auf den GPU-Render-Knoten.")
    return Device(
        str(path),
        str(device),
        vendor,
        driver,
        dri,
        os.major(info.st_rdev),
        os.minor(info.st_rdev),
    )


def candidate():
    devices = []
    for path in sorted(Path("/dev/dri").glob("renderD*")):
        try:
            devices.append(inspect_device(path))
        except (OSError, ValueError):
            continue
    if len(devices) != 1:
        raise sandbox.RadioSandboxError(
            "Keine eindeutige unterstützte GPU verfügbar."
            if not devices
            else "Mehrere GPUs verfügbar; automatische Gerätewahl abgelehnt."
        )
    return devices[0]


@lru_cache(maxsize=4)
def _runtime(dri):
    from netmon.core import projectm_frontend as frontend, projectm_native

    _stdlib, files, payload = frontend._runtime()
    executable = projectm_native.gpu_artifact(frontend._payload())
    files = set(files)
    for path in (
        GL / "libEGL.so.1",
        GL / "libEGL_mesa.so.0",
        GL / "dri" / (dri + "_dri.so"),
    ):
        files.update(sandbox._runtime_files(path, allow_static_extension=True))
    if len(files) > 512:
        raise sandbox.RadioSandboxError("GPU-Laufzeit überschreitet die Grenze.")
    return tuple(sorted(files)), tuple(
        (
            executable if target == "/app/bin/pcm-renderer" else source,
            "/app/bin/egl-renderer" if target == "/app/bin/pcm-renderer" else target,
        )
        for source, target in payload
    )


def _command(directory, plan, device, resolution):
    profile = profiles.resolve(resolution)
    if inspect_device(device.path) != device:
        raise sandbox.RadioSandboxError("GPU-Geräteidentität hat sich geändert.")
    files, payload = plan
    command = sandbox._sandbox_command(
        ["/app/bin/egl-renderer", profile.key, "performance"],
        directory,
        files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    extra = []
    for source, target in payload:
        extra += ["--ro-bind", str(source), target]
    for name, target in (
        ("presets", "/media/presets"),
        ("playlist", "/media/playlist"),
        ("preset-list", "/media/preset-list"),
        ("preset-selection", "/run/preset-selection"),
        ("visual-eq", "/run/visual-eq"),
        ("config.inp", "/media/config.inp"),
        ("fonts.conf", "/etc/fonts/fonts.conf"),
    ):
        extra += ["--ro-bind", str(directory / name), target]
    drm = str(Path(device.sysfs) / "drm" / Path(device.path).name)
    extra += [
        "--dev-bind",
        device.path,
        device.path,
        "--ro-bind",
        device.sysfs,
        device.sysfs,
        "--symlink",
        drm,
        f"/sys/dev/char/{device.major}:{device.minor}",
        "--symlink",
        drm,
        f"/sys/class/drm/{Path(device.path).name}",
        "--ro-bind",
        str(VENDOR),
        "/run/mesa.json",
    ]
    ids = Path("/usr/share/libdrm/amdgpu.ids")
    if device.driver == "amdgpu" and ids.is_file():
        extra += ["--ro-bind", str(ids), str(ids)]
    for key, value in {
        "__EGL_VENDOR_LIBRARY_FILENAMES": "/run/mesa.json",
        "NETMON_GPU_NODE": device.path,
        "LD_LIBRARY_PATH": "/app/lib",
        "FONTCONFIG_FILE": "/etc/fonts/fonts.conf",
        "MESA_SHADER_CACHE_DISABLE": "true",
    }.items():
        extra += ["--setenv", key, value]
    command[command.index("--") : command.index("--")] = extra
    return command


def start(
    playback,
    preset_dir,
    *,
    work_root=None,
    cancelled=lambda: False,
    resolution=profiles.DEFAULT,
    preset_name=None,
    cpu_profile=profiles.DEFAULT_CPU,
    visual_eq=profiles.NEUTRAL_EQ,
):
    from netmon.core import projectm_frontend as frontend, projectm_pcm, projectm_pixels

    profile = profiles.resolve(resolution)
    profiles.resolve_cpu(cpu_profile)
    profiles.validate_visual_eq(visual_eq)
    if cancelled():
        raise sandbox.RadioSandboxError("GPU-Start wurde entwertet.")
    if not isinstance(playback, sandbox.SandboxProcess):
        raise sandbox.RadioSandboxError("GPU benötigt geschützte NetMon-Wiedergabe.")
    sandbox._require_quota_manager()
    device = candidate()
    plan = _runtime(device.dri)
    temporary = tempfile.TemporaryDirectory(prefix="projectm-gpu-", dir=work_root)
    pcm = process = pixels = None
    selection_fd = eq_fd = None
    try:
        directory = Path(temporary.name)
        counts = frontend.prepare(
            directory,
            preset_dir,
            resolution=profile.key,
            preset_name=preset_name,
            cpu_profile=cpu_profile,
            backend="gpu",
            visual_eq=visual_eq,
        )
        selection_fd = os.open(
            directory / "preset-selection", os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        )
        eq_fd = os.open(
            directory / "visual-eq", os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        )
        if cancelled():
            raise sandbox.RadioSandboxError("GPU-Start wurde entwertet.")
        pcm = projectm_pcm.start(playback, work_root=work_root)
        if cancelled():
            raise sandbox.RadioSandboxError("GPU-Start wurde entwertet.")
        process = subprocess.Popen(
            sandbox._limited(
                _command(directory, plan, device, profile.key), "pm-renderer"
            ),
            env=sandbox._quota_env(),
            cwd="/",
            stdin=pcm.process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            bufsize=0,
        )
        pcm.process.stdout.close()
        pixels = projectm_pixels.PixelStream(
            process,
            SimpleNamespace(cleanup=lambda: None),
            profile.key,
            owns_process=False,
            marker=f"NMPG1 {profile.key}\n".encode("ascii"),
        )
        deadline = time.monotonic() + 8
        while not pixels.ready.wait(0.05):
            if cancelled() or time.monotonic() >= deadline:
                raise sandbox.RadioSandboxError(
                    "GPU-Pixelstart hat die Frist überschritten."
                )
        if (
            cancelled()
            or process.poll() is not None
            or pcm.poll() is not None
            or pixels.error
            or not pixels.frames.received
        ):
            raise sandbox.RadioSandboxError(
                "GPU-Renderer nicht bereit: " + (pixels.error or "kein Hardwarebild")
            )
        session = frontend.FrontendSession(
            process,
            pcm,
            None,
            temporary,
            pixels=pixels,
            presets=counts["preset_choices"],
            selection_fd=selection_fd,
            resolution=profile.key,
            selected_preset=counts["selected_preset"],
            cpu_profile=cpu_profile,
            backend="gpu",
            eq_fd=eq_fd,
            visual_eq=visual_eq,
        )
        session.gpu_device = device
        selection_fd = eq_fd = None
        return session
    except Exception as error:
        failures = []
        for action in (
            lambda: frontend._stop_process(process),
            lambda: pixels.stop() if pixels is not None else None,
            lambda: pcm.stop() if pcm is not None else None,
            lambda: os.close(selection_fd) if selection_fd is not None else None,
            lambda: os.close(eq_fd) if eq_fd is not None else None,
            temporary.cleanup,
        ):
            try:
                action()
            except Exception as failure:
                failures.append(str(failure)[:128])
        if failures:
            raise CleanupError(
                "GPU-Bereinigung fehlgeschlagen: " + "; ".join(failures)
            ) from error
        raise
