"""Native replacement probes under the actual internal display/reader grants."""

from contextlib import ExitStack
import fcntl
import json
import os
from pathlib import Path
import socket
import subprocess


def check(session, output):
    from netmon.core import projectm_display as display, projectm_pixels as pixels
    from netmon.core import projectm_frontend as frontend, radio_sandbox as sandbox
    from projectm_display_probe import BOUNDARY, compile_probe
    from projectm_frontend_probe import check_boundary as renderer_boundary

    private = output / "gx11-private-key"
    private.write_text("SYNTHETIC PRIVATE KEY")
    fd = os.open(private, os.O_RDONLY)
    inherited = fcntl.fcntl(fd, fcntl.F_DUPFD, 200)
    os.close(fd)
    os.set_inheritable(inherited, True)
    abstract = "gx11-" + str(os.getpid())
    audio = output / "gx11-audio-canary"
    # This is the fixture's private UI Xvfb, never a real desktop.
    outer = "/tmp/.X11-unix/X" + os.environ["DISPLAY"].split(":")[1].split(".")[0]
    values_by_role = {}
    try:
        with ExitStack() as stack:
            tcp = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            ab = stack.enter_context(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
            ac = stack.enter_context(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
            tcp.bind(("127.0.0.1", 0))
            ab.bind("\0" + abstract)
            ac.bind(str(audio))
            for listener in (tcp, ab, ac):
                listener.listen(2)
            for family, target, listener in (
                (socket.AF_INET, tcp.getsockname(), tcp),
                (socket.AF_UNIX, "\0" + abstract, ab),
                (socket.AF_UNIX, str(audio), ac),
            ):
                with socket.socket(family, socket.SOCK_STREAM) as client:
                    client.settimeout(0.2)
                    client.connect(target)
                    accepted, _ = listener.accept()
                    accepted.close()
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(0.2)
                client.connect(outer)
            source = BOUNDARY.replace(
                'unix_socket("/tmp/.X11-unix/X0",0)',
                f"unix_socket({json.dumps(outer)},0)",
            )
            for token, value in {
                "__PORT__": tcp.getsockname()[1],
                "__PRIVATE__": str(private),
                "__AUTH__": os.environ["XAUTHORITY"],
                "__AUDIO__": str(audio),
                "__ABSTRACT__": abstract,
                "__FD__": inherited,
            }.items():
                source = source.replace(token, json.dumps(value))
            cfile, binary = output / "gx11-boundary.c", output / "gx11-boundary"
            cfile.write_text(source)
            compile_probe(cfile, binary, output, sandbox)
            for role in ("internal-display", "pixel-reader"):
                with session.display.display_binding() as (descriptor, auth):
                    if role == "internal-display":
                        stdlib, files = display._runtime()
                        command = display._command(
                            Path(session.display.temporary.name), stdlib, files, auth
                        )
                        executable = display.XVFB
                        inherited_handles = (auth,)
                        memory = 2 * 1024**3
                    else:
                        command = pixels._command(
                            Path(session.pixels.temporary.name),
                            pixels._runtime(),
                            descriptor,
                            auth,
                        )
                        executable = sandbox.FFMPEG
                        inherited_handles = (descriptor, auth)
                        memory = 768 * 1024**2
                    index = command.index(str(executable.resolve(strict=True)))
                    assert command[index - 1] == "--ro-bind"
                    command[index] = str(binary)
                    completed = subprocess.run(
                        command,
                        env={**sandbox._ENV, "NETMON_DISPLAY_SECRET": "PRIVATE"},
                        cwd="/",
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        timeout=5,
                        pass_fds=inherited_handles,
                        close_fds=True,
                        check=True,
                    )
                values = json.loads(completed.stdout)
                expected = {key: 0 for key in values}
                expected.update(
                    no_new_privs=1, private_write=1, private_socket=1, memory=memory
                )
                if role == "internal-display":
                    expected.update(server_cookie=1, shell=1)
                else:
                    expected.update(client_cookie=1)
                assert values == expected, (role, values, expected)
                values_by_role[role] = {
                    "measured": values,
                    "worker_limits_retained": True,
                    "outer_private_ui_x_denied": True,
                    "argv": command,
                }
        values_by_role["renderer"] = renderer_boundary(
            frontend, session, output, sandbox
        )
        return values_by_role
    finally:
        os.close(inherited)
