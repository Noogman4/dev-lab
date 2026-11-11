"""Frontend capabilities, bounded staging and fail-closed owned lifecycle."""

from contextlib import contextmanager
import os
from pathlib import Path
import resource
import threading
import time
from types import SimpleNamespace

import pytest

from netmon.core import projectm_frontend as frontend
from netmon.core import projectm_frontend_worker as worker
from netmon.core import radio_sandbox as sandbox
from test_radio_sandbox import Child


@pytest.fixture
def presets(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.milk").write_bytes(b"[preset00]\n")
    return source


def test_staging_copies_only_media_and_ignores_old_scan_cache(presets, tmp_path):
    (presets / "assets").mkdir()
    (presets / "assets/a.png").write_bytes(b"SYNTHETIC PNG")
    (presets / "ignored.conf").write_text("SECRET")
    cache = presets / ".netmon_projectm_flat_scan_v1"
    cache.mkdir()
    (cache / "a.milk").symlink_to(presets / "a.milk")
    destination = tmp_path / "snapshot"
    counts = frontend.snapshot_presets(presets, destination)
    assert counts["files"] == 2 and counts["presets"] == 1
    assert (destination / "a.milk").read_bytes() == b"[preset00]\n"
    assert (destination / "assets/a.png").is_file()
    assert not (destination / "ignored.conf").exists()
    assert not (destination / cache.name).exists()
    (presets / "a.milk").write_text("CHANGED")
    assert (destination / "a.milk").read_bytes() == b"[preset00]\n"


@pytest.mark.parametrize("kind", ["symlink", "directory_symlink", "hardlink", "fifo"])
def test_staging_rejects_aliases_or_special_media_without_blocking(
    presets, tmp_path, kind
):
    path = presets / "bad.milk"
    if kind == "symlink":
        path.symlink_to(presets / "a.milk")
    elif kind == "directory_symlink":
        path.symlink_to(presets, target_is_directory=True)
    elif kind == "hardlink":
        os.link(presets / "a.milk", path)
    else:
        os.mkfifo(path)
    with pytest.raises((ValueError, OSError)):
        frontend.snapshot_presets(presets, tmp_path / "snapshot")


@pytest.mark.parametrize(
    "budget", ["file", "total", "members", "objects", "directories", "depth"]
)
def test_staging_keeps_finite_resource_budgets(presets, tmp_path, monkeypatch, budget):
    if budget == "file":
        monkeypatch.setattr(frontend.archive, "MAX_FILE_BYTES", 2)
    elif budget == "total":
        monkeypatch.setattr(frontend.archive, "MAX_TOTAL_BYTES", 2)
    elif budget == "members":
        monkeypatch.setattr(frontend.archive, "MAX_MEMBERS", 0)
    elif budget == "objects":
        monkeypatch.setattr(frontend, "MAX_OUTPUT_OBJECTS", 0)
    elif budget == "directories":
        (presets / "sub").mkdir()
        monkeypatch.setattr(frontend, "MAX_OUTPUT_DIRECTORIES", 0)
    else:
        parent = presets
        for _ in range(33):
            parent = parent / "sub"
            parent.mkdir()
    with pytest.raises(ValueError):
        frontend.snapshot_presets(presets, tmp_path / "snapshot")


def test_staging_refuses_empty_library_and_symlink_root(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValueError):
        frontend.snapshot_presets(source, tmp_path / "empty")
    alias = tmp_path / "alias"
    alias.symlink_to(source, target_is_directory=True)
    with pytest.raises(OSError):
        frontend.snapshot_presets(alias, tmp_path / "snapshot")


def test_private_playlist_flattens_nested_presets_with_links_only_to_snapshot(
    presets, tmp_path
):
    (presets / "pack").mkdir()
    (presets / "pack/a.milk").write_text("NESTED")
    destination, playlist = tmp_path / "snapshot", tmp_path / "playlist"
    result = frontend.snapshot_presets(presets, destination, playlist=playlist)
    assert result["presets"] == 2
    links = list(playlist.iterdir())
    assert len(links) == 2 and len({x.name for x in links}) == 2
    assert all(
        x.is_symlink() and x.resolve().is_relative_to(destination) for x in links
    )
    assert {x.read_text() for x in links} == {"[preset00]\n", "NESTED"}


def test_staging_rechecks_file_after_entry_stat(presets, tmp_path, monkeypatch):
    original = os.open
    outside = tmp_path / "private"
    outside.write_text("SECRET")

    def replaced(path, flags, *args, **kwargs):
        if path == "a.milk":
            (presets / "a.milk").unlink()
            (presets / "a.milk").symlink_to(outside)
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(frontend.os, "open", replaced)
    with pytest.raises(OSError):
        frontend.snapshot_presets(presets, tmp_path / "snapshot")
    assert not (tmp_path / "snapshot/a.milk").exists()


def test_renderer_grants_only_private_capabilities_and_generated_config(
    tmp_path, presets
):
    directory = tmp_path / "session"
    directory.mkdir()
    frontend.prepare(directory, presets)
    command = frontend._command(
        directory, (Path("/usr/lib/python3.12"), (), ()), 10, 11
    )
    assert command[0] == str(sandbox.BWRAP) and "--unshare-net" in command
    assert "--ro-bind-fd" in command and "/run/audio/pulse" not in command
    assert "/run/client.auth" in command and "--ro-bind-data" in command
    assert "/media/presets" in command and str(presets) not in command
    assert "/run/host.auth" not in command and "/tmp/.X11-unix/X0" not in command
    assert not {
        "/dev/dri",
        "/dev/snd",
        "/run/user",
        "/run/control",
        "/bin/sh",
        "flatpak",
    } & set(command)
    assert not any("PULSE_" in value for value in command)
    assert not any("pulse.conf" in value for value in command)
    assert "/media/config.inp" in command


class Component(Child):
    def __init__(self, result=None):
        super().__init__(result)
        self.stops = 0
        self.pid = 401

    def stop(self):
        self.stops += 1
        self.result = 0


def test_session_monitor_reaps_dependencies_after_renderer_exit(tmp_path):
    process, audio, display = Component(), Component(), Component()
    cleaned = []
    session = frontend.FrontendSession(
        process, audio, display, SimpleNamespace(cleanup=lambda: cleaned.append(True))
    )
    process.result = 7
    deadline = time.monotonic() + 2
    while not session._ended.is_set() and time.monotonic() < deadline:
        time.sleep(0.02)
    session.thread.join(timeout=1)
    assert session.poll() == 7 and not session.thread.is_alive()
    assert audio.stops == display.stops == 1 and cleaned == [True]
    session.stop()
    assert cleaned == [True]


@pytest.mark.parametrize("failed", ["audio", "display"])
def test_dependency_loss_ends_only_the_owned_frontend(failed):
    process, audio, display = Component(), Component(), Component()
    session = frontend.FrontendSession(
        process, audio, display, SimpleNamespace(cleanup=lambda: None)
    )
    (audio if failed == "audio" else display).result = 2
    assert session.poll() == 2 and process.result is not None
    session.stop()
    assert not session.thread.is_alive()


def test_converter_failure_cannot_be_hidden_by_renderer_clean_pipe_eof():
    process, pcm, display = Component(0), Component(2), Component()
    session = frontend.FrontendSession(
        process, pcm, display, SimpleNamespace(cleanup=lambda: None)
    )
    assert session.poll() == 2
    session.stop()


@pytest.mark.parametrize(
    "failure",
    [
        "audio",
        "display",
        "popen",
        "immediate_exit",
        "cancel_audio",
        "cancel_display",
        "pixels",
        "cancel_pixels",
        "cleanup",
    ],
)
@pytest.mark.parametrize("cpu_profile", ["standard", "performance"])
def test_start_failure_cleans_started_components_and_never_falls_back(
    presets, tmp_path, monkeypatch, failure, cpu_profile
):
    # No user manager in the isolated suite; quota checks have own tests.
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    playback = sandbox.SandboxProcess(
        Child(), SimpleNamespace(name=str(tmp_path), cleanup=lambda: None)
    )
    audio, display, pixels = Component(), Component(), Component()
    cancelled = threading.Event()

    @contextmanager
    def binding():
        yield 10, 11

    display.display_binding = binding
    read_fd, write_fd = os.pipe()
    audio.process = SimpleNamespace(stdout=os.fdopen(read_fd, "rb", buffering=0))
    os.close(write_fd)
    counter = iter(range(1000))

    class Frames:
        @property
        def received(self):
            return next(counter)

    pixels.frames = Frames()
    launches = []

    def start_audio(*_, **__):
        if failure == "audio":
            raise RuntimeError("synthetic audio failure")
        if failure == "cancel_audio":
            cancelled.set()
        return audio

    def start_display(**_):
        if failure == "display":
            raise RuntimeError("synthetic display failure")
        if failure == "cancel_display":
            cancelled.set()
        return display

    def popen(command, **kwargs):
        launches.append(command)
        # G-Quota: renderer runs as systemd-run scope -> prlimit -> bwrap.
        assert command[0] == str(sandbox.SYSTEMD_RUN) and str(sandbox.BWRAP) in command
        from netmon.core.projectm_profile import resolve_cpu

        quota = resolve_cpu(cpu_profile).quota
        assert command[5].startswith(f"--unit=netmon-radio-{quota}-")
        assert f"CPUQuota={sandbox.QUOTAS[quota]['cpu']}%" in command
        assert set(kwargs["pass_fds"]) == {10, 11}
        if failure == "popen":
            raise OSError("synthetic bwrap failure")
        child = Component(
            None if failure in {"pixels", "cancel_pixels", "cleanup"} else 7
        )
        read_fd, write_fd = os.pipe()
        child.stdout = os.fdopen(read_fd, "rb", buffering=0)
        os.write(write_fd, b"NMPM1 READY\n")
        os.close(write_fd)
        return child

    def start_pixels(*_, **__):
        if failure in {"pixels", "cleanup"}:
            raise RuntimeError("synthetic pixel failure")
        if failure == "cancel_pixels":
            cancelled.set()
        return pixels

    if failure == "cleanup":
        original_stop = audio.stop

        def broken_stop():
            original_stop()
            raise OSError("controlled PCM cleanup failure")

        audio.stop = broken_stop
    monkeypatch.setattr(frontend, "_runtime", lambda: (tmp_path, (), ()))
    monkeypatch.setattr(frontend.projectm_pcm, "start", start_audio)
    monkeypatch.setattr(frontend.projectm_display, "start", start_display)
    monkeypatch.setattr(frontend.projectm_pixels, "start", start_pixels)
    monkeypatch.setattr(frontend.subprocess, "Popen", popen)
    monkeypatch.setattr(frontend.time, "sleep", lambda _: None)
    with pytest.raises((RuntimeError, OSError, sandbox.RadioSandboxError)) as error:
        frontend.start(
            playback,
            presets,
            work_root=tmp_path,
            cancelled=cancelled.is_set,
            cpu_profile=cpu_profile,
        )
    assert len(launches) == (
        1
        if failure in {"popen", "immediate_exit", "pixels", "cancel_pixels", "cleanup"}
        else 0
    )
    assert audio.stops == (failure != "audio")
    assert display.stops == (
        failure
        in {
            "popen",
            "immediate_exit",
            "cancel_display",
            "pixels",
            "cancel_pixels",
            "cleanup",
        }
    )
    assert pixels.stops == (failure in {"cancel_pixels", "immediate_exit"})
    if failure == "cleanup":
        assert "Bereinigungsfehler" in str(error.value)
    audio.process.stdout.close()
    assert not list(tmp_path.glob("projectm-frontend-*"))


def test_start_refuses_foreign_or_ended_playback_before_runtime_probe(monkeypatch):
    monkeypatch.setattr(frontend, "_runtime", lambda: pytest.fail("Runtime reached"))
    for playback in (None, Component()):
        with pytest.raises(sandbox.RadioSandboxError):
            frontend.start(playback, "unused")


def test_worker_keeps_stricter_inherited_limits(monkeypatch):
    calls = []
    monkeypatch.setattr(resource, "getrlimit", lambda name: (32, 64))
    monkeypatch.setattr(
        resource, "setrlimit", lambda name, value: calls.append((name, value))
    )
    worker.limits()
    assert calls == [
        (name, (32, 32))
        for name in (resource.RLIMIT_AS, resource.RLIMIT_FSIZE, resource.RLIMIT_NOFILE)
    ]


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin/pcm-renderer").write_text("ELF fixture")
    monkeypatch.setattr(
        frontend.projectm_native, "artifact", lambda _: tmp_path / "bin/pcm-renderer"
    )
    (tmp_path / "lib").mkdir()
    library = tmp_path / "lib/libprojectM.so.3"
    library.write_text("LIB fixture")
    fonts = tmp_path / "share/projectM/fonts"
    fonts.mkdir(parents=True)
    for name in ("Vera.ttf", "VeraMono.ttf"):
        (fonts / name).write_text("FONT fixture")
    monkeypatch.setattr(frontend, "_payload", lambda: tmp_path)
    monkeypatch.setattr(
        sandbox, "_pcm_runtime", lambda: (Path("/usr/lib/python3.12"), ())
    )
    monkeypatch.setattr(frontend.projectm_display, "_software_files", lambda: ())
    monkeypatch.setattr(sandbox, "_runtime_files", lambda *_, **__: ())
    frontend._runtime.cache_clear()
    yield tmp_path, library
    frontend._runtime.cache_clear()


def test_runtime_uses_only_fixed_installed_payload_and_clean_library_search(
    runtime, monkeypatch
):
    root, library = runtime

    def ldd(command, **kwargs):
        assert command == ["/usr/bin/ldd", str(root / "bin/pcm-renderer")]
        assert kwargs["env"] == {**sandbox._ENV, "LD_LIBRARY_PATH": str(root / "lib")}
        assert kwargs["cwd"] == "/" and kwargs["timeout"] == 10
        return SimpleNamespace(stdout=f"libprojectM.so.3 => {library} (0xabc)\n")

    monkeypatch.setattr(frontend.subprocess, "run", ldd)
    _, files, payload = frontend._runtime()
    assert files == ()
    assert (library, "/app/lib/libprojectM.so.3") in payload
    assert (root / "bin/pcm-renderer", "/app/bin/pcm-renderer") in payload


@pytest.mark.parametrize(
    "output",
    [
        "libprojectM.so.3 => not found",
        "unexpected output",
        "outside-package",
    ],
)
def test_runtime_rejects_unresolved_or_unexpected_library_plans(
    runtime, monkeypatch, output
):
    if output == "outside-package":
        private = runtime[0] / "private-key"
        private.write_text("SYNTHETIC SECRET")
        output = f"{private} (0xabc)"
    monkeypatch.setattr(
        frontend.subprocess, "run", lambda *_, **__: SimpleNamespace(stdout=output)
    )
    with pytest.raises(sandbox.RadioSandboxError):
        frontend._runtime()


def test_runtime_rejects_payload_library_alias_outside_fixed_package(
    runtime, tmp_path, monkeypatch
):
    root, library = runtime
    other = tmp_path / "private-library"
    other.write_text("PRIVATE")
    library.unlink()
    library.symlink_to(other)
    monkeypatch.setattr(
        frontend.subprocess,
        "run",
        lambda *_, **__: SimpleNamespace(
            stdout=f"libprojectM.so.3 => {library} (0xabc)\n"
        ),
    )
    with pytest.raises(sandbox.RadioSandboxError):
        frontend._runtime()


def test_projectm_start_without_user_manager_starts_nothing(presets, monkeypatch):
    monkeypatch.setattr(sandbox.os, "getuid", lambda: 2**31 - 7)
    monkeypatch.setattr(
        frontend.subprocess, "Popen", lambda *_a, **_k: pytest.fail("process started")
    )
    playback = sandbox.SandboxProcess(
        Child(), SimpleNamespace(name="/nonexistent", cleanup=lambda: None)
    )
    with pytest.raises(sandbox.RadioSandboxError, match="Ressourcengrenzen"):
        frontend.start(playback, presets)


@pytest.mark.parametrize(
    "profile,cpu,tasks",
    [
        ("pm-feeder", 50, 32),
        ("pm-display", 50, 16),
        ("pm-renderer", 200, 64),
        ("pm-renderer-performance", 300, 64),
        ("pm-pixels", 50, 32),
    ],
)
def test_projectm_quota_profiles_bound_every_capsule(profile, cpu, tasks):
    quota = sandbox.QUOTAS[profile]
    assert quota["cpu"] == cpu and quota["tasks"] == tasks
    # G1: Xvfb (and every projectM capsule) now has FSIZE and NOFILE bounds.
    assert quota["fsize"] == 16 << 20 and quota["nofile"] <= 256
    assert quota["tmpfs"] == 16 << 20


def test_all_four_projectm_capsules_start_via_limited():
    import inspect

    from netmon.core import projectm_display, projectm_pcm, projectm_pixels

    for module, profile in (
        (projectm_display, "pm-display"),
        (projectm_pcm, "pm-feeder"),
        (frontend, "pm-renderer"),
        (projectm_pixels, "pm-pixels"),
    ):
        source = inspect.getsource(module.start)
        # Both fixed renderer profiles are exercised through intercepted Popen
        # in the parametrized failure tests above, including the effective quota.
        selector = "cpu.quota" if module is frontend else f'"{profile}"'
        assert selector in source and "sandbox._limited(" in source
        assert "env=sandbox._quota_env()" in source
        assert "env=sandbox._ENV" not in source
