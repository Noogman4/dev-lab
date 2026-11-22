"""Runs only inside the private server capsule; no host sockets or devices.

Trusted fixture tools (pw-dump, pw-link, pw-cat observer) run here as children,
so the private core sees their real PIDs. Commands arrive as JSON lines from
the trusted coordinator on stdin; output goes to files in the private runtime.
"""

import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

ended = False
TOOLS = Path("/run/private-audio/tools")
ALLOWED = {
    "/usr/bin/pw-dump",
    "/usr/bin/pw-link",
    "/usr/bin/pw-cat",
    "/usr/bin/pipewire",
}


def stop(*_):
    global ended
    ended = True


signal.signal(signal.SIGTERM, stop)
children = []
background = []
try:
    env = dict(os.environ)
    TOOLS.mkdir(mode=0o700)
    children.append(
        subprocess.Popen(
            ["/usr/bin/pipewire", "-c", "/etc/netmon-audio/pipewire.conf"], env=env
        )
    )
    deadline = time.monotonic() + 8
    while not Path("/run/private-audio/pipewire-0").is_socket():
        if ended or children[0].poll() is not None or time.monotonic() > deadline:
            print("FAILED " + json.dumps(children[0].poll()), flush=True)
            raise RuntimeError("private core not ready")
        time.sleep(0.02)
    children.append(
        subprocess.Popen(
            ["/usr/bin/wireplumber", "-c", "/etc/netmon-audio/wireplumber.conf"],
            env=env,
        )
    )
    print("READY", flush=True)
    selector = selectors.DefaultSelector()
    selector.register(sys.stdin, selectors.EVENT_READ)
    while not ended:
        if any(p.poll() is not None for p in children):
            raise RuntimeError(
                "server dependency ended: "
                + repr([(p.args[0], p.returncode) for p in children])
            )
        if not selector.select(0.05):
            continue
        line = sys.stdin.readline()
        if not line:
            break
        request = json.loads(line)
        argv = request["argv"]
        assert argv[0] in ALLOWED, argv
        out = (TOOLS / (str(int(request["id"])) + ".out")).open("wb")
        err = (TOOLS / (str(int(request["id"])) + ".err")).open("wb")
        tool_env = {**env, "PIPEWIRE_CONFIG_NAME": "client.conf", "PIPEWIRE_DEBUG": "2"}
        p = subprocess.Popen(
            argv, env=tool_env, stdin=subprocess.DEVNULL, stdout=out, stderr=err
        )
        out.close()
        err.close()
        if request.get("background"):
            background.append(p)
            reply = {"id": request["id"], "started": True}
        else:
            try:
                rc = p.wait(timeout=float(request.get("timeout", 4)))
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=2)
                rc = "timeout"
            reply = {"id": request["id"], "rc": rc}
        print(json.dumps(reply), flush=True)
finally:
    for p in reversed(background + children):
        if p.poll() is None:
            p.terminate()
    for p in reversed(background + children):
        try:
            p.wait(timeout=2)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=2)
