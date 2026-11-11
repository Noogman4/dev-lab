"""Real installed Qt projectM inside the already verified private test display."""

import array
import ctypes
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import socket
import struct
import tempfile
import threading
import time

CAPTURE = r"""
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdio.h>
int main(void){
 Display*d=XOpenDisplay(0);if(!d)return 2;
 Window w=DefaultRootWindow(d);XWindowAttributes a;if(!XGetWindowAttributes(d,w,&a))return 3;
 if(a.width<1||a.height<1||a.width>1024||a.height>768)return 4;
 XImage*i=XGetImage(d,w,0,0,a.width,a.height,AllPlanes,ZPixmap);if(!i)return 5;
 printf("P6\n%d %d\n255\n",a.width,a.height);
 for(int y=0;y<a.height;y++)for(int x=0;x<a.width;x++){
  unsigned long p=XGetPixel(i,x,y);unsigned char rgb[]={
   (p&i->red_mask)>>16,(p&i->green_mask)>>8,p&i->blue_mask};fwrite(rgb,1,3,stdout);}
 XDestroyImage(i);XCloseDisplay(d);return 0;
}
"""


def wait_for(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("Private frontend deadline")


def private_pulse(session, arguments, directory, sandbox):
    with session.pcm.socket_binding() as (source, descriptor):
        command = sandbox._sandbox_command(
            ["/usr/bin/pactl", *arguments],
            directory,
            sandbox._runtime_files(Path("/usr/bin/pactl")),
            source,
            local_file=None,
            audio_output=True,
        )
        result = subprocess.run(
            command,
            env=sandbox._ENV,
            cwd="/",
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=3,
            close_fds=True,
            pass_fds=(descriptor,),
            check=True,
        )
        assert len(result.stdout) < 65536
        return json.loads(result.stdout)


def check_boundary(frontend, session, output, sandbox):
    from projectm_display_probe import BOUNDARY, compile_probe

    outside = output / "frontend-private-key"
    outside.write_text("SYNTHETIC SECRET")
    fd = os.open(outside, os.O_RDONLY)
    inherited = fcntl.fcntl(fd, fcntl.F_DUPFD, 200)
    os.close(fd)
    os.set_inheritable(inherited, True)
    abstract = "netmon-frontend-" + str(os.getpid())
    audio_canary = output / "frontend-audio-canary"
    try:
        with (
            socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp,
            socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as ab,
            socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as pulse,
        ):
            tcp.bind(("127.0.0.1", 0))
            tcp.listen(2)
            ab.bind("\0" + abstract)
            ab.listen(2)
            pulse.bind(str(audio_canary))
            pulse.listen(2)
            for family, address, listener in (
                (socket.AF_INET, tcp.getsockname(), tcp),
                (socket.AF_UNIX, "\0" + abstract, ab),
                (socket.AF_UNIX, str(audio_canary), pulse),
            ):
                with socket.socket(family, socket.SOCK_STREAM) as control:
                    control.settimeout(0.2)
                    control.connect(address)
                    accepted, _ = listener.accept()
                    accepted.close()
            source = BOUNDARY
            for token, value in {
                "__PORT__": tcp.getsockname()[1],
                "__PRIVATE__": str(outside),
                "__AUTH__": os.environ["XAUTHORITY"],
                "__AUDIO__": str(audio_canary),
                "__ABSTRACT__": abstract,
                "__FD__": inherited,
            }.items():
                source = source.replace(token, json.dumps(value))
            source = source.replace(
                " return 0;\n}",
                ' if(!readable("/media/presets/pack/synthetic.milk"))return 6;\n'
                ' if(open("/media/presets/pack/synthetic.milk",O_WRONLY)>=0)return 7;\n'
                ' if(open("/media/config.inp",O_WRONLY)>=0)return 8;\n'
                ' if(exists("/run/audio/pulse")||getenv("PULSE_SERVER"))return 11;\n'
                " struct rlimit fsize,nofile;if(getrlimit(RLIMIT_FSIZE,&fsize)||getrlimit(RLIMIT_NOFILE,&nofile)||fsize.rlim_cur!=16777216||nofile.rlim_cur!=256)return 9;\n"
                " pid_t child=fork();if(child<0)return 10;if(child==0){for(;;)pause();}\n return 0;\n}",
            )
            cfile = output / "frontend-boundary.c"
            cfile.write_text(source)
            binary = output / "frontend-boundary"
            compile_probe(cfile, binary, output, sandbox)
            with session.display.display_binding() as (display_fd, auth_fd):
                plan = frontend._runtime()
                command = frontend._command(
                    Path(session.temporary.name), plan, display_fd, auth_fd
                )
                executable = next(
                    str(source)
                    for source, target in plan[2]
                    if target == "/app/bin/pcm-renderer"
                )
                index = command.index(executable)
                assert command[index - 1] == "--ro-bind"
                command[index] = str(binary)
                probe = subprocess.run(
                    command,
                    env={**sandbox._ENV, "NETMON_DISPLAY_SECRET": "PRIVATE"},
                    cwd="/",
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=5,
                    close_fds=True,
                    pass_fds=(display_fd, auth_fd),
                    check=True,
                )
            measured = json.loads(probe.stdout)
            expected = {key: 0 for key in measured}
            expected.update(
                private_socket=1,
                client_cookie=1,
                no_new_privs=1,
                private_write=1,
                memory=2 * 1024**3,
            )
            assert measured == expected, measured
            return {
                **measured,
                "private_audio_connected": False,
                "transport": "one-way-pcm",
                "preset_readable": True,
                "preset_and_config_read_only": True,
                "file_size_limit": 16777216,
                "open_file_limit": 256,
                "namespace_reaps_background_child": True,
            }
    finally:
        os.close(inherited)


def check_frontend(root, output):
    from netmon.core import (
        projectm_frontend as frontend,
        projectm_display as display,
        radio_sandbox as sandbox,
    )
    from projectm_display_probe import client_command, compile_probe

    result = {
        "checks": [],
        "real_desktop": False,
        "host_audio": False,
        "security_acceptance": False,
    }
    original_popen = subprocess.Popen
    original_prepare = frontend.prepare
    notify = ctypes.CDLL(None, use_errno=True)
    notify.inotify_init1.argtypes = [ctypes.c_int]
    notify.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
    watch = notify.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    assert watch >= 0
    watches = []
    stop = threading.Event()
    feeder = relay = playback = session = None
    log = (output / "frontend.log").open("w")
    try:

        def prepared(directory, preset_dir):
            counts = original_prepare(directory, preset_dir)
            # Only shorten the test's private preset timer, never host settings.
            config = directory / "config.inp"
            config.write_text(
                config.read_text().replace(
                    "Preset Duration = 30", "Preset Duration = 1"
                )
            )
            wd = notify.inotify_add_watch(
                watch, os.fsencode(directory / "presets/pack/synthetic.milk"), 1
            )
            assert wd >= 0
            watches.append(wd)
            return counts

        frontend.prepare = prepared

        class LoggedPopen(original_popen):
            def __init__(self, command, *args, **kwargs):
                if (
                    command[0] == str(sandbox.BWRAP)
                    and "/run/frontend-worker.py" in command
                ):
                    kwargs["stderr"] = log
                super().__init__(command, *args, **kwargs)

        subprocess.Popen = LoggedPopen
        result["source_sha256"] = {
            name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in (
                "netmon/core/projectm_frontend.py",
                "netmon/core/projectm_frontend_worker.py",
                "netmon/core/projectm_audio.py",
                "netmon/core/projectm_display.py",
                "netmon/core/radio_sandbox.py",
                "tests/projectm_frontend_probe.py",
                "tests/test_projectm_frontend.py",
                "tests/projectm_display_probe.py",
                "tests/run_isolated_suite.py",
            )
        }
        stdlib, files, payload = frontend._runtime()
        result["runtime_sha256"] = {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(files) | {p for p, _ in payload})
        }
        temporary = tempfile.TemporaryDirectory(prefix="pcm-source-", dir=output)
        directory = Path(temporary.name)
        sandbox._prepare_directory(directory)
        (directory / "tap").mkdir(mode=0o700)
        pcm_stdlib, pcm_files = sandbox._pcm_runtime()
        relay = subprocess.Popen(
            sandbox._pcm_command(directory, pcm_stdlib, pcm_files),
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=log,
            env=sandbox._ENV,
            cwd="/",
            close_fds=True,
            bufsize=0,
        )
        playback = sandbox.SandboxProcess(relay, temporary, pcm_process=relay)
        samples = array.array(
            "h",
            (
                v
                for n in range(4800)
                for v in (
                    int(5000 * math.sin(2 * math.pi * 440 * n / 48000)),
                    int(7000 * math.sin(2 * math.pi * 880 * n / 48000)),
                )
            ),
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
        presets = output / "frontend-presets"
        presets.mkdir()
        (presets / "pack").mkdir()
        (presets / "pack/synthetic.milk").write_text("""[preset00]
fRating=3.0
fDecay=0.92
fGammaAdj=1.0
fVideoEchoZoom=1.0
fVideoEchoAlpha=0.0
nVideoEchoOrientation=0
nWaveMode=0
bAdditiveWaves=1
bWaveDots=0
bWaveThick=1
fWaveAlpha=1.0
fWaveScale=1.0
fWaveSmoothing=0.0
wave_r=1.0
wave_g=0.2
wave_b=0.3
wave_x=0.5
wave_y=0.5
per_frame_1=wave_r=0.5+0.5*sin(time*3);wave_g=0.5+0.5*cos(time*2);
""")
        session = frontend.start(playback, presets, work_root=output)
        client = output / "frontend-client"
        client.mkdir()
        sandbox._prepare_directory(client)
        assert session.pcm.feed.forwarded > 0
        command = frontend._command(
            Path(session.temporary.name), frontend._runtime(), 10, 11
        )
        assert "/run/audio/pulse" not in command and not any(
            "PULSE_" in x for x in command
        )
        result["pcm_audit"] = {
            "forwarded_bytes": session.pcm.feed.forwarded,
            "pulse_socket": False,
        }
        result["checks"].append(
            "real PCM renderer accepts one-way NetMon samples; no audio-server capability"
        )
        cfile = output / "capture.c"
        cfile.write_text(CAPTURE)
        binary = output / "capture-probe"
        compile_probe(
            cfile, binary, output, sandbox, ["/usr/lib/x86_64-linux-gnu/libX11.so.6"]
        )
        frames = []
        time.sleep(3)
        for index in range(2):
            time.sleep(1)
            with session.display.display_binding() as (fd, auth):
                command = client_command(
                    display,
                    sandbox,
                    session.display,
                    client,
                    display.GLXINFO,
                    fd,
                    auth,
                    replace=binary,
                )
                captured = subprocess.run(
                    command,
                    env=sandbox._ENV,
                    cwd="/",
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=5,
                    pass_fds=(fd, auth),
                    close_fds=True,
                    check=True,
                )
            assert captured.stdout.startswith(b"P6\n640 480\n255\n")
            path = output / f"frontend-frame-{index}.ppm"
            path.write_bytes(captured.stdout)
            frames.append(hashlib.sha256(captured.stdout).hexdigest())
        assert frames[0] != frames[1], "Private frontend frames did not change"
        result["frame_sha256"] = frames
        events = os.read(watch, 4096)
        offset = 0
        accessed = False
        while offset < len(events):
            wd, mask, _cookie, length = struct.unpack_from("iIII", events, offset)
            assert not mask & 0x4000, "Preset watch overflow"
            accessed |= wd in watches and bool(mask & 1)
            offset += 16 + length
        assert accessed, "Staged synthetic preset was not read"
        result["staged_preset_accessed"] = True
        result["fixture_preset_duration_seconds"] = 1
        result["checks"].append(
            "real projectM private-display frames captured and changing; synthetic preset and synthetic PCM only"
        )
        result["boundary"] = check_boundary(frontend, session, output, sandbox)
        result["checks"].append(
            "exact frontend grants deny outer X, host-audio canary, files, network, secrets and helpers; own private X and stdin PCM allowed and staged media/config read-only"
        )
        session.stop()
        assert session.poll() == 0 and relay.poll() is None
        assert not Path(session.temporary.name).exists()
        result["checks"].append(
            "frontend stop reaps its renderer/converter/display and leaves original PCM playback alive"
        )
        session = frontend.start(playback, presets, work_root=output)
        session.pcm.process.kill()
        wait_for(lambda: session.process.poll() is not None)
        assert session.poll() != 0 and session.process.poll() is not None
        assert session.display.process.poll() is not None and relay.poll() is None
        result["checks"].append(
            "PCM converter loss ends renderer and display without stopping original playback"
        )
        session = frontend.start(playback, presets, work_root=output)
        session.display.process.kill()
        wait_for(lambda: session.process.poll() is not None)
        assert (
            session.poll() != 0
            and session.pcm.process.poll() is not None
            and relay.poll() is None
        )
        result["checks"].append(
            "private display loss ends renderer and converter without stopping original playback"
        )
        session = frontend.start(playback, presets, work_root=output)
        playback.terminate()
        playback.wait(timeout=3)
        wait_for(lambda: session.process.poll() is not None)
        assert (
            session.poll() is not None
            and session.pcm.process.poll() is not None
            and session.display.process.poll() is not None
        )
        result["checks"].append(
            "original playback end invalidates its private visualization; no host-audio fallback"
        )
        return result
    finally:
        if session is not None:
            session.stop()
        stop.set()
        if playback is not None:
            playback.kill()
            playback.wait(timeout=3)
        if feeder is not None:
            feeder.join(timeout=2)
        if relay is not None:
            relay.stdin.close()
        subprocess.Popen = original_popen
        frontend.prepare = original_prepare
        os.close(watch)
        log.close()
