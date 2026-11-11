"""Experimental internal Xvfb -> sandboxed pixel reader -> bounded raw pipe.

No production UI integration; never opens an outer X socket or host audio.
Only reachable through the existing isolated launcher.
"""

import array
from contextlib import ExitStack
import hashlib
import fcntl
import json
import math
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from unittest.mock import patch

sys.pycache_prefix = "/nonexistent"
os.environ["PYTHONPYCACHEPREFIX"] = "/nonexistent"
from projectm_pixel_protocol import collect, WIDTH, HEIGHT, FRAME_BYTES  # noqa: E402

SERVER = Path(__file__).with_name("projectm_pixel_server.py")
XVFB = Path("/usr/bin/Xvfb")
CAPTURE = r"""
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <arpa/inet.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <time.h>
static int limit(int name, rlim_t maximum){
 struct rlimit r;if(getrlimit(name,&r))return 1;
 if(r.rlim_cur!=RLIM_INFINITY&&r.rlim_cur<maximum)maximum=r.rlim_cur;
 if(r.rlim_max!=RLIM_INFINITY&&r.rlim_max<maximum)maximum=r.rlim_max;
 r.rlim_cur=r.rlim_max=maximum;return setrlimit(name,&r);
}
int main(void){
 if(limit(RLIMIT_AS,512ULL*1024*1024)||limit(RLIMIT_CPU,12)||limit(RLIMIT_NOFILE,64)||limit(RLIMIT_FSIZE,16*1024*1024))return 2;
 Display*d=XOpenDisplay(NULL);if(!d)return 3;
 Window root=DefaultRootWindow(d);XWindowAttributes a;
 if(!XGetWindowAttributes(d,root,&a)||a.width!=640||a.height!=480)return 4;
 /* Position only the private fixture window once; never an outer X client. */
 Window rr,parent,*children=NULL;unsigned count=0;
 if(!XQueryTree(d,root,&rr,&parent,&children,&count)||count>16)return 10;
 for(unsigned n=0;n<count;n++){
  XWindowAttributes w;if(XGetWindowAttributes(d,children[n],&w)&&w.map_state==IsViewable)
   XMoveResizeWindow(d,children[n],0,0,640,480);
 }
 if(children)XFree(children);XSync(d,False);
 unsigned char *rgba=malloc(640*480*4);if(!rgba)return 5;
 setvbuf(stdout,NULL,_IONBF,0);if(fwrite("NMPX01\0",1,7,stdout)!=7)return 6;
 for(uint32_t frame=0;frame<24;frame++){
  XImage*i=XGetImage(d,root,0,0,640,480,AllPlanes,ZPixmap);if(!i)return 7;
  if(i->width!=640||i->height!=480||i->depth!=24||i->bits_per_pixel!=32||
     i->bytes_per_line!=640*4||i->red_mask!=0xff0000||i->green_mask!=0xff00||i->blue_mask!=0xff)return 8;
  for(int y=0;y<480;y++)for(int x=0;x<640;x++){
   unsigned long p=XGetPixel(i,x,y);size_t n=(y*640+x)*4;
   rgba[n]=(p>>16)&255;rgba[n+1]=(p>>8)&255;rgba[n+2]=p&255;rgba[n+3]=255;
  }
  XDestroyImage(i);uint32_t sequence=htonl(frame);
  if(fwrite(&sequence,1,4,stdout)!=4||fwrite(rgba,1,640*480*4,stdout)!=640*480*4)return 9;
  struct timespec delay={0,100000000};nanosleep(&delay,NULL);
 }
 free(rgba);XCloseDisplay(d);return 0;
}
"""

PRESET = """[preset00]
fRating=3.0
fDecay=0.92
fGammaAdj=1.0
fVideoEchoZoom=1.0
fVideoEchoAlpha=0.0
nWaveMode=0
bAdditiveWaves=1
bWaveThick=1
fWaveAlpha=1.0
fWaveScale=1.0
wave_r=1.0
wave_g=0.2
wave_b=0.3
wave_x=0.5
wave_y=0.5
per_frame_1=wave_r=0.5+0.5*sin(time*3);wave_g=0.5+0.5*cos(time*2);
"""


def display_command(directory, stdlib, files, auth, sandbox):
    command = sandbox._sandbox_command(
        [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            "pycache_prefix=/nonexistent",
            "/run/pixel-server.py",
        ],
        directory,
        files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    extra = [
        "--bind",
        str(directory / "x11"),
        "/tmp/.X11-unix",
        "--ro-bind-data",
        str(auth),
        "/run/private.auth",
        "--ro-bind",
        str(stdlib),
        str(stdlib),
        "--ro-bind",
        str(SERVER),
        "/run/pixel-server.py",
        "--ro-bind",
        "/usr/share/X11/xkb",
        "/usr/share/X11/xkb",
    ]
    for key, value in {
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "GALLIUM_DRIVER": "llvmpipe",
        "LP_NUM_THREADS": "2",
    }.items():
        extra += ["--setenv", key, value]
    command[command.index("--") : command.index("--")] = extra
    return command


def display_runtime(sandbox, display):
    stdlib, python = sandbox._pcm_runtime()
    files = (
        set(python) | set(sandbox._runtime_files(XVFB)) | set(display._software_files())
    )
    for path in [
        Path("/usr/bin/xkbcomp"),
        Path("/bin/sh"),
        Path("/usr/lib/xorg/modules/extensions/libglx.so"),
    ]:
        files.update(sandbox._runtime_files(path, allow_static_extension=True))
    return stdlib, tuple(sorted(files))


def internal_display(output, sandbox, display, commands):
    stdlib, files = display_runtime(sandbox, display)
    temporary = tempfile.TemporaryDirectory(prefix="px-", dir=output)
    directory = Path(temporary.name)
    process = None
    descriptor = None
    auth = display._sealed_auth(secrets.token_bytes(16), "1")
    # Select the same cookie bytes from our sealed private record, no host file.
    cookie = display._cookie(os.pread(auth, 4096, 0), "1", b"unused")
    try:
        sandbox._prepare_directory(directory)
        (directory / "x11").mkdir(mode=0o700)
        command = display_command(directory, stdlib, files, auth, sandbox)
        commands.append({"role": "internal-display", "argv": command})
        process = subprocess.Popen(
            command,
            env=sandbox._ENV,
            cwd="/",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            close_fds=True,
            pass_fds=(auth,),
        )
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and process.poll() is None:
            try:
                descriptor = os.open(
                    directory / "x11/X1", os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC
                )
                display._handshake(descriptor, cookie)
                return display.DisplaySession(process, temporary, descriptor, cookie)
            except (
                FileNotFoundError,
                ConnectionRefusedError,
                socket.timeout,
                ValueError,
            ):
                if descriptor is not None:
                    os.close(descriptor)
                    descriptor = None
                time.sleep(0.03)
        raise RuntimeError("Internal Xvfb did not become ready")
    except Exception:
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
        if descriptor is not None:
            os.close(descriptor)
        temporary.cleanup()
        raise
    finally:
        os.close(auth)


def reader_plan(directory, binary, fd, auth, sandbox):
    files = tuple(path for path in sandbox._runtime_files(binary) if path != binary)
    command = sandbox._sandbox_command(
        ["/run/pixel-reader"],
        directory,
        files,
        None,
        local_file=None,
        catalog_parser=True,
    )
    extra = [
        "--ro-bind",
        str(binary),
        "/run/pixel-reader",
        "--ro-bind-fd",
        str(fd),
        "/tmp/.X11-unix/X1",
        "--ro-bind-data",
        str(auth),
        "/run/client.auth",
        "--setenv",
        "DISPLAY",
        ":1",
        "--setenv",
        "XAUTHORITY",
        "/run/client.auth",
    ]
    command[command.index("--") : command.index("--")] = extra
    return command


def reader_command(directory, binary, session, sandbox, display, commands):
    with session.display_binding() as (fd, auth):
        command = reader_plan(directory, binary, fd, auth, sandbox)
        commands.append({"role": "pixel-reader", "argv": command})
        return subprocess.Popen(
            command,
            env=sandbox._ENV,
            cwd="/",
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            close_fds=True,
            pass_fds=(fd, auth),
        )


def stop_child(process):
    if process is None:
        return
    if process.poll() is None:
        process.kill()
    process.wait(timeout=3)
    if process.stdout is not None:
        process.stdout.close()


def check_pixel_boundaries(
    output, session, binary, client, sandbox, display, frontend, commands
):
    """Substitute a fixed libc-only attacker probe, preserving role grants.

    These replacements measure capabilities, not the limits of the real worker.
    No real outer X server or real user secret is needed for these canaries.
    """
    from projectm_display_probe import BOUNDARY, compile_probe
    from projectm_frontend_probe import check_boundary as frontend_boundary

    private, auth_file = output / "pixel-private-key", output / "pixel-outer.auth"
    private.write_text("SYNTHETIC PRIVATE KEY")
    auth_file.write_text("SYNTHETIC OUTER COOKIE")
    descriptor = os.open(private, os.O_RDONLY)
    inherited = fcntl.fcntl(descriptor, fcntl.F_DUPFD, 200)
    os.close(descriptor)
    os.set_inheritable(inherited, True)
    abstract = "netmon-pixel-" + str(os.getpid())
    outer, audio = output / "outer-X-canary", output / "audio-canary"
    measured = {}
    try:
        with ExitStack() as stack:
            tcp = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            ab = stack.enter_context(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
            xcanary = stack.enter_context(
                socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            )
            acanary = stack.enter_context(
                socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            )
            tcp.bind(("127.0.0.1", 0))
            ab.bind("\0" + abstract)
            xcanary.bind(str(outer))
            acanary.bind(str(audio))
            for listener, family, target in [
                (tcp, socket.AF_INET, tcp.getsockname()),
                (ab, socket.AF_UNIX, "\0" + abstract),
                (xcanary, socket.AF_UNIX, str(outer)),
                (acanary, socket.AF_UNIX, str(audio)),
            ]:
                listener.listen(2)
                with socket.socket(family, socket.SOCK_STREAM) as control:
                    control.settimeout(0.2)
                    control.connect(target)
                    connected, _ = listener.accept()
                    connected.close()
            source = BOUNDARY.replace(
                'unix_socket("/tmp/.X11-unix/X0",0)',
                f"unix_socket({json.dumps(str(outer))},0)",
            )
            for token, value in {
                "__PORT__": tcp.getsockname()[1],
                "__PRIVATE__": str(private),
                "__AUTH__": str(auth_file),
                "__AUDIO__": str(audio),
                "__ABSTRACT__": abstract,
                "__FD__": inherited,
            }.items():
                source = source.replace(token, json.dumps(value))
            cfile, attacker = output / "pixel-boundary.c", output / "pixel-boundary"
            cfile.write_text(source)
            compile_probe(cfile, attacker, output, sandbox)
            stdlib, files = display_runtime(sandbox, display)
            for role in ("internal-display", "pixel-reader"):
                with session.display.display_binding() as (fd, auth):
                    if role == "internal-display":
                        command = display_command(
                            Path(session.display.temporary.name),
                            stdlib,
                            files,
                            auth,
                            sandbox,
                        )
                        command[command.index("--") + 1 :] = ["/run/pixel-boundary"]
                        extra = ["--ro-bind", str(attacker), "/run/pixel-boundary"]
                        command[command.index("--") : command.index("--")] = extra
                    else:
                        command = reader_plan(client, binary, fd, auth, sandbox)
                        index = command.index(str(binary))
                        assert command[index - 1] == "--ro-bind"
                        command[index] = str(attacker)
                    commands.append({"role": role + "-boundary", "argv": command})
                    completed = subprocess.run(
                        command,
                        env={**sandbox._ENV, "NETMON_DISPLAY_SECRET": "PRIVATE"},
                        cwd="/",
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        timeout=5,
                        close_fds=True,
                        pass_fds=(fd, auth),
                        check=True,
                    )
                values = json.loads(completed.stdout)
                expected = {key: 0 for key in values}
                expected.update(
                    no_new_privs=1,
                    private_write=1,
                    private_socket=1,
                    memory=values["memory"],
                )
                if role == "internal-display":
                    expected.update(server_cookie=1, shell=1)
                else:
                    expected.update(client_cookie=1)
                assert values == expected, (role, values, expected)
                measured[role] = {
                    "capabilities": values,
                    "real_worker_limits_measured": False,
                }
        # Existing exact renderer-grant probe, with only a synthetic outer-auth
        # path supplied to its fixture. It never opens a real desktop cookie.
        with patch.dict(os.environ, {"XAUTHORITY": str(auth_file)}):
            measured["renderer"] = frontend_boundary(frontend, session, output, sandbox)
        return measured
    finally:
        os.close(inherited)


def exercise(root, output, result, *, benchmark_fps=None, frame_sink=None, cancel=None):
    sys.path.insert(0, str(root))
    from netmon.core import (
        projectm_frontend as frontend,
        projectm_display as display,
        radio_sandbox as sandbox,
    )
    from projectm_display_probe import compile_probe
    from projectm_frontend_probe import wait_for

    def checkpoint():
        if cancel is not None and cancel.is_set():
            raise InterruptedError("Pixel probe cancelled")

    checkpoint()

    source_paths = [
        "tests/projectm_pixel_probe.py",
        "tests/projectm_pixel_server.py",
        "tests/projectm_pixel_protocol.py",
        "tests/run_isolated_suite.py",
        "netmon/core/projectm_frontend.py",
        "netmon/core/projectm_display.py",
        "netmon/core/projectm_audio.py",
        "netmon/core/radio_sandbox.py",
        "netmon/core/projectm_frontend_worker.py",
        "netmon/core/radio_pcm.py",
        "tests/projectm_display_probe.py",
        "tests/projectm_frontend_probe.py",
        "tests/radio_stream_probe.py",
    ]
    if benchmark_fps is not None:
        source_paths.append("tests/projectm_pixel_benchmark.py")
    result["source_sha256"] = {
        str(path): hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in source_paths
    }
    assert not os.environ.get("DISPLAY") and not os.environ.get("XAUTHORITY")
    original_popen = subprocess.Popen
    commands = result["commands"] = []
    owned = []
    stop = threading.Event()
    playback = session = reader = feeder = None
    with ExitStack() as stack:
        log = stack.enter_context((output / "pixel-processes.log").open("w"))

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
                    raise AssertionError("Forbidden prototype launch")
                if command[0] == str(sandbox.BWRAP):
                    kwargs["stderr"] = log
                super().__init__(command, *args, **kwargs)
                if command[0] == str(sandbox.BWRAP):
                    owned.append(self)
                    stack.callback(stop_child, self)

        stack.enter_context(patch.object(subprocess, "Popen", LoggedPopen))
        stack.enter_context(
            patch.object(display, "_host", side_effect=AssertionError("Outer X access"))
        )
        stack.enter_context(
            patch.object(
                display,
                "start",
                side_effect=lambda **_: internal_display(
                    output, sandbox, display, commands
                ),
            )
        )
        original_prepare = frontend.prepare

        def prepare(directory, presets):
            counts = original_prepare(directory, presets)
            path = directory / "config.inp"
            text = path.read_text().replace(
                "Preset Duration = 30", "Preset Duration = 1"
            )
            if benchmark_fps is not None:
                text = text.replace("FPS = 25", "FPS = 60")
            path.write_text(text)
            return counts

        stack.enter_context(patch.object(frontend, "prepare", prepare))
        temporary = tempfile.TemporaryDirectory(prefix="pcm-pixels-", dir=output)
        stack.callback(temporary.cleanup)
        directory = Path(temporary.name)
        sandbox._prepare_directory(directory)
        (directory / "tap").mkdir(mode=0o700)
        stdlib, runtime = sandbox._pcm_runtime()
        relay = subprocess.Popen(
            sandbox._pcm_command(directory, stdlib, runtime),
            env=sandbox._ENV,
            cwd="/",
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
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
        try:
            presets = output / "pixel-presets"
            presets.mkdir()
            (presets / "pack").mkdir()
            (presets / "pack/synthetic.milk").write_text(PRESET)
            plan = frontend._runtime()
            result["runtime_sha256"] = {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(set(plan[1]) | {p for p, _ in plan[2]})
            }
            result["runtime_sha256"].update(
                {
                    str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in display_runtime(sandbox, display)[1]
                }
            )
            result["runtime_manifest_scope"] = (
                "selected ELF/payload files; no complete stdlib/XKB or dependency attestation"
            )
            checkpoint()
            session = frontend.start(playback, presets, work_root=output)
            checkpoint()
            client = output / "pixel-client"
            client.mkdir()
            sandbox._prepare_directory(client)
            assert session.pcm.feed.forwarded > 0
            result["private_audio_audit"] = {
                "transport": "one-way-pcm",
                "pulse_socket": False,
            }
            result["checks"].append(
                "real projectM starts on internal Xvfb and private NetMon PCM; no outer X capability"
            )
            cfile, binary = output / "pixel-reader.c", output / "pixel-reader"
            receiver = collect
            if benchmark_fps is None:
                cfile.write_text(CAPTURE)
            else:
                from projectm_pixel_benchmark import capture_source, collect_timed

                cfile.write_text(capture_source(benchmark_fps))

                def receiver(child, callback, *, timeout=40):
                    return collect_timed(
                        child,
                        callback,
                        fps=benchmark_fps,
                        timeout=timeout,
                        cancel=cancel,
                    )

            compile_probe(
                cfile,
                binary,
                output,
                sandbox,
                ["/usr/lib/x86_64-linux-gnu/libX11.so.6"],
            )
            result["compiled_reader_sha256"] = hashlib.sha256(
                binary.read_bytes()
            ).hexdigest()
            result["runtime_sha256"].update(
                {
                    str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sandbox._runtime_files(binary)
                }
            )
            checkpoint()
            result["boundary"] = check_pixel_boundaries(
                output, session, binary, client, sandbox, display, frontend, commands
            )
            result["checks"].append(
                "internal display, pixel reader and renderer deny live outer-X/audio/file/network/FD canaries under their grant plans"
            )
            if cancel is not None:
                if cancel.wait(3):
                    checkpoint()
            else:
                time.sleep(3)
            checkpoint()
            reader = reader_command(
                client, binary, session.display, sandbox, display, commands
            )
            hashes, region_hashes, times = [], [], []

            def frame(data):
                checkpoint()
                assert len(data) == FRAME_BYTES
                if frame_sink is not None:
                    frame_sink(data)
                hashes.append(hashlib.sha256(data).hexdigest())
                interior = b"".join(
                    data[(y * WIDTH + 20) * 4 : (y * WIDTH + 600) * 4]
                    for y in range(120, 450)
                )
                region_hashes.append(hashlib.sha256(interior).hexdigest())
                times.append(time.monotonic())
                if len(hashes) in {1, 24}:
                    rgb = bytearray(WIDTH * HEIGHT * 3)
                    rgb[0::3], rgb[1::3], rgb[2::3] = data[0::4], data[1::4], data[2::4]
                    (output / f"pixel-frame-{len(hashes)}.ppm").write_bytes(
                        f"P6\n{WIDTH} {HEIGHT}\n255\n".encode() + rgb
                    )

            result["transport"] = receiver(reader, frame)
            assert reader.wait(timeout=2) == 0
            reader.stdout.close()
            reader = None
            assert len(set(region_hashes)) > 1, "Visualization interior did not change"
            result["transport"].update(
                frame_sha256=hashes,
                interior_sha256=region_hashes,
                configured_fps=benchmark_fps or 10,
                observed_fps=(len(times) - 1) / (times[-1] - times[0]),
            )
            result["checks"].append(
                "finite fixed-size RGBA stream passes bounded pipe parser; visualization interior changes"
            )
            reader = reader_command(
                client, binary, session.display, sandbox, display, commands
            )
            session.display.process.kill()
            try:
                receiver(reader, lambda _: None, timeout=3)
            except (ValueError, TimeoutError):
                pass
            else:
                raise AssertionError("Display loss produced a complete pixel stream")
            stop_child(reader)
            reader = None
            wait_for(lambda: session.process.poll() is not None)
            assert session.poll() != 0 and session.pcm.process.poll() is not None
            assert relay.poll() is None
            result["checks"].append(
                "internal display loss ends frontend/converter and pixel reader; original synthetic playback survives"
            )
        finally:
            stop_child(reader)
            if session is not None:
                session.stop()
            stop.set()
            if playback is not None:
                playback.kill()
                playback.wait(timeout=3)
            if feeder is not None:
                feeder.join(timeout=2)
            relay.stdin.close()
            for process in reversed(owned):
                stop_child(process)
            result["owned_wrappers_reaped"] = all(p.poll() is not None for p in owned)


def worker(root, output, parent_net, *, benchmark_fps=None):
    result = {
        "status": "failed",
        "checks": [],
        "prototype_only": True,
        "real_desktop": False,
        "host_audio": False,
        "outer_x_started": False,
        "security_acceptance": False,
        "production_ui_changed": False,
    }
    try:
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
        exercise(root, output, result, benchmark_fps=benchmark_fps)
        result["status"] = "passed"
    except Exception:
        result["error"] = traceback.format_exc()
    (output / "projectm-pixel-result.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in {"runtime_sha256", "commands"}
            },
            indent=2,
        )
    )
    return 0 if result["status"] == "passed" else 1


def run(root, output):
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
        "--worker",
        str(root),
        str(output),
        os.readlink("/proc/self/ns/net"),
    ]
    print("Private pixel prototype evidence:", output, flush=True)
    try:
        result = subprocess.run(
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
            timeout=90,
        )
    except subprocess.TimeoutExpired as exc:

        def text(value):
            return (
                value.decode(errors="replace")
                if isinstance(value, bytes)
                else value or ""
            )

        (output / "coordinator.log").write_text(text(exc.stdout) + text(exc.stderr))
        (output / "coordinator-timeout.json").write_text(
            json.dumps(
                {
                    "status": "failed",
                    "reason": "coordinator deadline",
                    "security_acceptance": False,
                }
            )
            + "\n"
        )
        print("Pixel prototype coordinator deadline; partial evidence retained.")
        return 1
    (output / "coordinator.log").write_text(result.stdout + result.stderr)
    print(result.stdout + result.stderr)
    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--benchmark-worker":
        raise SystemExit(
            worker(
                Path(sys.argv[2]),
                Path(sys.argv[3]),
                sys.argv[4],
                benchmark_fps=int(sys.argv[5]),
            )
        )
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        raise SystemExit(worker(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]))
    raise SystemExit("Use tests/run_isolated_suite.py --projectm-pixel-probe")
