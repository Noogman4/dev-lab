"""Private outer Xvfb and internal graphics probe; never uses the real desktop."""

import hashlib
import fcntl
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import traceback

sys.pycache_prefix = "/nonexistent"
os.environ["PYTHONPYCACHEPREFIX"] = "/nonexistent"
BOUNDARY = r"""
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
int readable(const char *p){int f=open(p,O_RDONLY);if(f<0)return 0;close(f);return 1;}
int exists(const char *p){return access(p,F_OK)==0;}
int connects(int family,const void *address,socklen_t length){
 int s=socket(family,SOCK_STREAM|SOCK_NONBLOCK,0);if(s<0)return 0;
 int r=connect(s,address,length);if(r<0&&errno==EINPROGRESS){struct pollfd p={s,POLLOUT,0};
  int error=1;socklen_t n=sizeof(error);r=poll(&p,1,150)>0&&getsockopt(s,SOL_SOCKET,SO_ERROR,&error,&n)==0&&error==0?0:-1;}
 close(s);return r==0;
}
int unix_socket(const char *p,int abstract){struct sockaddr_un a={.sun_family=AF_UNIX};
 size_t n=strlen(p);if(n+1>=sizeof(a.sun_path))return 0;
 memcpy(a.sun_path+abstract,p,n+1);return connects(AF_UNIX,&a,offsetof(struct sockaddr_un,sun_path)+n+1);}
int main(void){
 struct sockaddr_in tcp={.sin_family=AF_INET,.sin_port=htons(__PORT__),.sin_addr.s_addr=htonl(INADDR_LOOPBACK)};
 char status[8192]={0};int f=open("/proc/self/status",O_RDONLY);if(f<0)return 2;
 if(read(f,status,sizeof(status)-1)<1)return 3;close(f);
 unsigned long caps=1;char *cp=strstr(status,"CapEff:");if(cp)sscanf(cp,"CapEff: %lx",&caps);
 struct rlimit memory;if(getrlimit(RLIMIT_AS,&memory))return 4;
 f=open("/tmp/.X11-unix/renderer-canary",O_WRONLY|O_CREAT,0600);int write_ok=f>=0;if(f>=0)close(f);
 printf("{\"private_file\":%d,\"original_auth\":%d,\"audio_canary\":%d,\"tcp\":%d,\"abstract\":%d,"
 "\"inherited_fd\":%d,\"secret_env\":%d,\"outer_socket\":%d,\"private_socket\":%d,"
 "\"outer_cookie\":%d,\"client_cookie\":%d,\"server_cookie\":%d,\"shell\":%d,\"devices\":%d,"
 "\"dbus\":%d,\"user_runtime\":%d,\"control\":%d,\"sudo\":%d,\"nested_userns\":%d,"
 "\"caps\":%lu,\"no_new_privs\":%d,\"private_write\":%d,\"memory\":%llu}\n",
 readable(__PRIVATE__),readable(__AUTH__),unix_socket(__AUDIO__,0),connects(AF_INET,&tcp,sizeof(tcp)),unix_socket(__ABSTRACT__,1),
 fcntl(__FD__,F_GETFD)>=0,getenv("NETMON_DISPLAY_SECRET")!=NULL,
 unix_socket("/tmp/.X11-unix/X0",0),unix_socket("/tmp/.X11-unix/X1",0),readable("/run/host.auth"),
 readable("/run/client.auth"),readable("/run/private.auth"),exists("/bin/sh"),exists("/dev/dri")||exists("/dev/snd"),
 exists("/run/dbus"),exists("/run/user"),exists("/run/control"),exists("/usr/bin/sudo"),unshare(CLONE_NEWUSER)==0,
 caps,strstr(status,"NoNewPrivs:\t1")!=NULL,write_ok,(unsigned long long)memory.rlim_cur);
 return 0;
}
"""


def compile_probe(source, executable, output, sandbox, libraries=()):
    build = subprocess.run(
        [
            "/usr/bin/gcc",
            str(source),
            "-O2",
            "-Wall",
            "-Wextra",
            "-include",
            "stddef.h",
            *libraries,
            "-o",
            str(executable),
        ],
        env=sandbox._ENV,
        cwd="/",
        capture_output=True,
        timeout=15,
    )
    (output / (source.stem + "-build.log")).write_bytes(build.stdout + build.stderr)
    assert build.returncode == 0, "Probe build failed"


def check_boundary(display, sandbox, session, output, auth):
    private = output / "display-private-key"
    private.write_text("SYNTHETIC PRIVATE KEY")
    descriptor = os.open(private, os.O_RDONLY)
    inherited = fcntl.fcntl(descriptor, fcntl.F_DUPFD, 200)
    os.close(descriptor)
    os.set_inheritable(inherited, True)
    abstract = "netmon-private-display-" + str(os.getpid())
    outside = output / "display-pulse-canary"
    measured = {}
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
            pulse.bind(str(outside))
            pulse.listen(2)
            for family, address, listener in (
                (socket.AF_INET, tcp.getsockname(), tcp),
                (socket.AF_UNIX, "\0" + abstract, ab),
                (socket.AF_UNIX, str(outside), pulse),
            ):
                with socket.socket(family, socket.SOCK_STREAM) as control:
                    control.settimeout(0.2)
                    control.connect(address)
                    accepted, _ = listener.accept()
                    accepted.close()
            source = BOUNDARY
            for token, value in {
                "__PORT__": tcp.getsockname()[1],
                "__PRIVATE__": str(private),
                "__AUTH__": str(auth),
                "__AUDIO__": str(outside),
                "__ABSTRACT__": abstract,
                "__FD__": inherited,
            }.items():
                source = source.replace(token, json.dumps(value))
            cfile = output / "boundary.c"
            cfile.write_text(source)
            compiled = output / "boundary-probe"
            compile_probe(cfile, compiled, output, sandbox)
            for role in ("renderer", "internal-display"):
                with tempfile.TemporaryDirectory(
                    prefix=role + "-boundary-", dir=output
                ) as name:
                    directory = Path(name)
                    sandbox._prepare_directory(directory)
                    if role == "renderer":
                        with session.display_binding() as (fd, cookie):
                            command = client_command(
                                display,
                                sandbox,
                                session,
                                directory,
                                display.GLXINFO,
                                fd,
                                cookie,
                                replace=compiled,
                            )
                            result = subprocess.run(
                                command,
                                env={
                                    **sandbox._ENV,
                                    "NETMON_DISPLAY_SECRET": "PRIVATE",
                                },
                                cwd="/",
                                stdin=subprocess.DEVNULL,
                                capture_output=True,
                                timeout=5,
                                close_fds=True,
                                pass_fds=(fd, cookie),
                                check=True,
                            )
                        assert not (
                            session.socket_path.parent / "renderer-canary"
                        ).exists()
                    else:
                        (directory / "x11").mkdir(mode=0o700)
                        private_auth = display._sealed_auth(b"p" * 16, "1")
                        try:
                            stdlib, files = display._runtime()
                            command = display._command(
                                directory,
                                stdlib,
                                files,
                                private_auth,
                            )
                            index = command.index(
                                str(display.XVFB.resolve(strict=True))
                            )
                            assert command[index - 1] == "--ro-bind"
                            command[index] = str(compiled)
                            result = subprocess.run(
                                command,
                                env={
                                    **sandbox._ENV,
                                    "NETMON_DISPLAY_SECRET": "PRIVATE",
                                },
                                cwd="/",
                                stdin=subprocess.DEVNULL,
                                capture_output=True,
                                timeout=5,
                                close_fds=True,
                                pass_fds=(private_auth,),
                                check=True,
                            )
                        finally:
                            for handle in (private_auth,):
                                os.close(handle)
                        assert (directory / "x11/renderer-canary").exists()
                    values = json.loads(result.stdout)
                    expected = {key: 0 for key in values}
                    expected.update(no_new_privs=1, private_write=1)
                    if role == "renderer":
                        expected.update(
                            private_socket=1, client_cookie=1, memory=values["memory"]
                        )
                    else:
                        expected.update(
                            server_cookie=1,
                            shell=1,
                            memory=2 * 1024**3,
                        )
                    assert values == expected, (role, values, expected)
                    measured[role] = values
        return measured
    finally:
        os.close(inherited)


DRAW = r"""
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <GL/gl.h>
#include <GL/glx.h>
#include <stdio.h>
#include <unistd.h>
int main(void) {
 Display *d=XOpenDisplay(NULL);if(!d)return 2;
 int attrs[]={GLX_RGBA,GLX_DOUBLEBUFFER,GLX_RED_SIZE,8,GLX_GREEN_SIZE,8,GLX_BLUE_SIZE,8,None};
 XVisualInfo *v=glXChooseVisual(d,DefaultScreen(d),attrs);if(!v)return 3;
 XSetWindowAttributes a={0};a.colormap=XCreateColormap(d,RootWindow(d,v->screen),v->visual,AllocNone);
 Window w=XCreateWindow(d,RootWindow(d,v->screen),0,0,320,240,0,v->depth,InputOutput,v->visual,CWColormap,&a);
 XStoreName(d,w,"NetMon private software draw");XMapWindow(d,w);XSync(d,False);
 GLXContext c=glXCreateContext(d,v,0,True);if(!c||!glXMakeCurrent(d,w,c))return 4;
 unsigned char r[4]={0},b[4]={0};glViewport(0,0,320,240);
 glClearColor(1,0,0,1);glClear(GL_COLOR_BUFFER_BIT);glReadPixels(1,1,1,1,GL_RGBA,GL_UNSIGNED_BYTE,r);glXSwapBuffers(d,w);
 glClearColor(0,0,1,1);glClear(GL_COLOR_BUFFER_BIT);glReadPixels(1,1,1,1,GL_RGBA,GL_UNSIGNED_BYTE,b);glXSwapBuffers(d,w);XSync(d,False);
 if(r[0]<250||r[1]>5||r[2]>5||b[0]>5||b[1]>5||b[2]<250)return 5;
 puts("{\"frames\":2,\"red\":[255,0,0],\"blue\":[0,0,255]}");fflush(stdout);
 for(;;){glClear(GL_COLOR_BUFFER_BIT);glXSwapBuffers(d,w);XSync(d,False);usleep(30000);}
}
"""


def client_command(
    display, sandbox, session, directory, executable, display_fd, auth_fd, replace=None
):
    files = set(sandbox._runtime_files(executable)) | set(display._software_files())
    cmd = sandbox._sandbox_command(
        [str(executable)] + (["-B"] if executable == display.GLXINFO else []),
        directory,
        tuple(sorted(files)),
        None,
        local_file=None,
        catalog_parser=True,
    )
    if replace is not None:
        # Only replace the trusted test executable contents; preserve all grants.
        index = cmd.index(str(executable.resolve(strict=True)))
        assert cmd[index - 1] == "--ro-bind"
        cmd[index] = str(replace)
    extra = [
        "--ro-bind-fd",
        str(display_fd),
        "/tmp/.X11-unix/X1",
        "--ro-bind-data",
        str(auth_fd),
        "/run/client.auth",
    ]
    for key, value in {
        "DISPLAY": ":1",
        "XAUTHORITY": "/run/client.auth",
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "GALLIUM_DRIVER": "llvmpipe",
        "LP_NUM_THREADS": "2",
    }.items():
        extra += ["--setenv", key, value]
    cmd[cmd.index("--") : cmd.index("--")] = extra
    return cmd


def read_line(process):
    import selectors

    data = bytearray()
    deadline = time.monotonic() + 5
    with selectors.DefaultSelector() as selected:
        selected.register(process.stdout, selectors.EVENT_READ)
        while time.monotonic() < deadline and len(data) < 1024:
            if not selected.select(0.05):
                continue
            chunk = os.read(process.stdout.fileno(), 1024 - len(data))
            if not chunk:
                break
            data.extend(chunk)
            if b"\n" in data:
                return json.loads(data)
    raise AssertionError("Private frame readback missing")


def _wait(predicate, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.03)
    raise AssertionError("Private display deadline")


def _worker(root, output, parent_net, frontend=False):
    result = {
        "status": "failed",
        "checks": [],
        "real_desktop": False,
        "host_audio": False,
        "hardware_gpu": False,
        "projectm_frontend": False,
        "security_acceptance": False,
    }
    host = session = None
    original_popen = subprocess.Popen
    handles = []
    try:
        assert os.readlink("/proc/self/ns/net") != parent_net
        assert [n for _, n in socket.if_nameindex()] == ["lo"]
        subprocess.run(
            ["/usr/sbin/ip", "link", "set", "lo", "up"],
            env={"PATH": "/usr/bin:/bin"},
            check=True,
            timeout=3,
        )
        from radio_stream_probe import _drop_namespace_caps

        _drop_namespace_caps()
        sys.path.insert(0, str(root))
        from netmon.core import projectm_display as display, radio_sandbox as sandbox

        stdlib, files = display._runtime()
        runtime = set(files) | set(sandbox._runtime_files(display.GLXINFO))
        result["runtime_sha256"] = {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(runtime)
        }
        result["runtime_manifest_scope"] = (
            "selected ELF files only; stdlib and xkb trees not fully manifested"
        )
        result["source_sha256"] = {
            f: hashlib.sha256((root / f).read_bytes()).hexdigest()
            for f in (
                "netmon/core/projectm_display.py",
                "netmon/core/projectm_display_worker.py",
                "netmon/core/radio_sandbox.py",
                "tests/projectm_display_probe.py",
                "tests/test_projectm_display.py",
                "tests/run_isolated_suite.py",
            )
        }

        host_dir = output / "outer-x11"
        host_dir.mkdir(mode=0o700)
        auth = output / "outer.auth"
        host_cookie = secrets.token_bytes(16)
        auth.write_bytes(display.auth_record(host_cookie, "8"))
        auth.chmod(0o600)
        log = (output / "outer.log").open("w")
        handles.append(log)
        command = [
            str(sandbox.BWRAP),
            "--unshare-user",
            "--unshare-pid",
            "--unshare-net",
            "--unshare-ipc",
            "--die-with-parent",
            "--new-session",
            "--cap-drop",
            "ALL",
            "--clearenv",
        ]
        for path in ("/usr", "/lib", "/lib64"):
            if Path(path).exists():
                command += ["--ro-bind", path, path]
        command += [
            "--symlink",
            "usr/bin",
            "/bin",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--dir",
            "/home/test",
            "--dir",
            "/etc",
            "--bind",
            str(host_dir),
            "/tmp/.X11-unix",
            "--ro-bind",
            str(auth),
            "/run/outer.auth",
            "--setenv",
            "PATH",
            "/usr/bin:/bin",
            "--setenv",
            "HOME",
            "/home/test",
            "--setenv",
            "LC_ALL",
            "C.UTF-8",
            "--",
            "/usr/bin/Xvfb",
            ":8",
            "-screen",
            "0",
            "1024x768x24",
            "-nolisten",
            "tcp",
            "-noreset",
            "-auth",
            "/run/outer.auth",
            "-extension",
            "GLX",
        ]
        host = subprocess.Popen(
            command,
            env=sandbox._ENV,
            cwd="/",
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            close_fds=True,
        )
        _wait(lambda: (host_dir / "X8").exists() or host.poll() is not None)
        assert host.poll() is None
        descriptor = os.open(host_dir / "X8", os.O_PATH | os.O_NOFOLLOW)
        try:
            display._handshake(descriptor, host_cookie)
        finally:
            os.close(descriptor)
        # Only substitute the selected test display; internal display/client grants stay exact.
        display.X11_DIR = host_dir
        os.environ.update(DISPLAY=":8", XAUTHORITY=str(auth))
        display_log = (output / "internal-display.log").open("w")
        handles.append(display_log)

        class LoggedPopen(original_popen):
            def __init__(self, args, *other, **kwargs):
                if args[0] == str(sandbox.BWRAP) and "/run/display-worker.py" in args:
                    kwargs["stderr"] = display_log
                super().__init__(args, *other, **kwargs)

        subprocess.Popen = LoggedPopen
        session = display.start(work_root=output)
        result["boundary"] = check_boundary(display, sandbox, session, output, auth)
        result["checks"].append(
            "renderer and internal display measured separately under their exact grants; neither receives outer X"
        )
        session.socket_path.rename(session.socket_path.with_name("original-X1"))
        session.socket_path.symlink_to(host_dir / "X8")
        with session.display_binding() as (display_fd, auth_fd):
            for cookie in (b"", host_cookie, b"x" * 16):
                try:
                    display._handshake(display_fd, cookie)
                except ValueError:
                    pass
                else:
                    raise AssertionError("Missing/wrong private auth accepted")
            with tempfile.TemporaryDirectory(prefix="gl-client-", dir=output) as name:
                client = Path(name)
                sandbox._prepare_directory(client)
                cmd = client_command(
                    display,
                    sandbox,
                    session,
                    client,
                    display.GLXINFO,
                    display_fd,
                    auth_fd,
                )
                probe = subprocess.run(
                    cmd,
                    env=sandbox._ENV,
                    cwd="/",
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=10,
                    close_fds=True,
                    pass_fds=(display_fd, auth_fd),
                )
                (output / "glxinfo.log").write_bytes(probe.stdout + probe.stderr)
                assert probe.returncode == 0, "Software GL failed; see glxinfo.log"
                assert b"llvmpipe" in probe.stdout.lower()
                result["software_gl"] = probe.stdout.decode(errors="replace")
        cfile = output / "draw.c"
        cfile.write_text(DRAW)
        compiled = output / "draw-probe"
        build = subprocess.run(
            [
                "/usr/bin/gcc",
                str(cfile),
                "-O2",
                "-Wall",
                "-Wextra",
                "/usr/lib/x86_64-linux-gnu/libX11.so.6",
                "/usr/lib/x86_64-linux-gnu/libGL.so.1",
                "-o",
                str(compiled),
            ],
            env=sandbox._ENV,
            cwd="/",
            capture_output=True,
            timeout=15,
        )
        (output / "build.log").write_bytes(build.stdout + build.stderr)
        assert build.returncode == 0
        with (
            session.display_binding() as (display_fd, auth_fd),
            tempfile.TemporaryDirectory(prefix="draw-client-", dir=output) as name,
        ):
            client = Path(name)
            sandbox._prepare_directory(client)
            cmd = client_command(
                display,
                sandbox,
                session,
                client,
                display.GLXINFO,
                display_fd,
                auth_fd,
                replace=compiled,
            )
            drawing = subprocess.Popen(
                cmd,
                env=sandbox._ENV,
                cwd="/",
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=display_log,
                close_fds=True,
                pass_fds=(display_fd, auth_fd),
            )
            try:
                result["frame_readback"] = read_line(drawing)
                assert result["frame_readback"]["frames"] == 2
                session.stop()
                assert drawing.wait(timeout=3) != 0
            finally:
                if drawing.poll() is None:
                    drawing.kill()
                    drawing.wait(timeout=2)
                drawing.stdout.close()
        result["checks"].extend(
            [
                "private display binding retains its inode after its filename is replaced by an outer-socket symlink",
                "real internal Xvfb authenticates with a distinct cookie; no/wrong/outer cookie rejected",
                "separate client creates software OpenGL 4.5 and draws red/blue frames with readback; no hardware GPU grants",
                "private display loss ends the active GL client",
            ]
        )
        session.stop()
        assert not session.socket_path.exists()
        assert host.poll() is None
        result["checks"].append(
            "stopping private display leaves the isolated outer Xvfb alive"
        )
        if frontend:
            from projectm_frontend_probe import check_frontend

            result["frontend"] = check_frontend(root, output)
            result["projectm_frontend"] = True
            result["checks"].extend(result["frontend"]["checks"])
        result["status"] = "passed"
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        if session is not None:
            session.stop()
        if host is not None:
            if host.poll() is None:
                host.terminate()
            try:
                host.wait(timeout=3)
            except subprocess.TimeoutExpired:
                host.kill()
                host.wait(timeout=2)
        subprocess.Popen = original_popen
        for handle in handles:
            handle.close()
    (output / "projectm-display-result.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    summary = {
        key: value
        for key, value in result.items()
        if key not in {"runtime_sha256", "software_gl"}
    }
    if "frontend" in summary:
        summary["frontend"] = {
            key: value
            for key, value in summary["frontend"].items()
            if key not in {"runtime_sha256", "source_outputs"}
        }
    print(json.dumps(summary, indent=2))
    return 0 if result["status"] == "passed" else 1


def run(root, output, *, frontend=False):
    cmd = [
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
        "--worker",
        str(root),
        str(output),
        os.readlink("/proc/self/ns/net"),
        "frontend" if frontend else "display",
    ]
    print("Private projectM display evidence:", output, flush=True)
    result = subprocess.run(
        cmd,
        cwd=root,
        env={"PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8", "HOME": "/nonexistent"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    (output / "coordinator.log").write_text(result.stdout + result.stderr)
    print(result.stdout + result.stderr)
    return result.returncode


if __name__ == "__main__":
    if (
        len(sys.argv) == 6
        and sys.argv[1] == "--worker"
        and sys.argv[5] in {"display", "frontend"}
    ):
        raise SystemExit(
            _worker(
                Path(sys.argv[2]),
                Path(sys.argv[3]),
                sys.argv[4],
                sys.argv[5] == "frontend",
            )
        )
    raise SystemExit("Use tests/run_isolated_suite.py --projectm-display-probe")
