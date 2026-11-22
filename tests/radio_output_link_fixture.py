"""Private PipeWire fixture for the output-link integration probe.

Extracted from the existing G-pacat probe. It creates only private server
capsules, runs tools inside them and stops children through OwnedProcess.
No host audio socket, device or service restart is available.
"""

import json
from pathlib import Path
import selectors
import subprocess
import sys
import time

from netmon.core import projectm_audio as audio, radio_sandbox as sandbox
from netmon.core.projectm_process import OwnedProcess

HERE = Path(__file__).resolve().parent
OUT = None  # Set by the probe before creating a fixture.
FIFO_CAPSULE = "/run/private-audio/fifo/radio.pcm"
TUNNEL = "netmon-radio-fifo"
SINK = "gp-sink"
MIXER = Path("/usr/lib/x86_64-linux-gnu/spa-0.2/audiomixer/libspa-audiomixer.so")
FORMAT = "S16LE" if sys.byteorder == "little" else "S16BE"


def until(predicate, timeout=8.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise TimeoutError("private probe deadline")


def server_conf():
    sinks = "".join(
        ' { factory = adapter args = { factory.name = support.null-audio-sink node.name = "'
        + name
        + '" media.class = Audio/Sink audio.position = [ FL FR ]'
        " adapter.auto-port-config = { mode = dsp monitor = true position = preserve } } }\n"
        for name in (SINK, "gp-other-sink")
    )
    return (
        "context.properties = { core.daemon = true core.name = pipewire-0 support.dbus = false }\n"
        + audio._spa()
        + f"""context.modules = [
 {{ name = libpipewire-module-protocol-native }}
 {{ name = libpipewire-module-metadata }}
 {{ name = libpipewire-module-spa-node-factory }}
 {{ name = libpipewire-module-client-node }}
 {{ name = libpipewire-module-access }}
 {{ name = libpipewire-module-adapter }}
 {{ name = libpipewire-module-link-factory }}
 {{ name = libpipewire-module-session-manager }}
 {{ name = libpipewire-module-pipe-tunnel args = {{
     tunnel.mode = playback
     remote.name = "internal"
     pipe.filename = "{FIFO_CAPSULE}"
     audio.format = {FORMAT}
     audio.rate = 48000
     audio.channels = 2
     audio.position = [ FL FR ]
     node.name = "{TUNNEL}"
     stream.props = {{ node.autoconnect = false }}
 }} }}
]
context.objects = [
 {{ factory = spa-node-factory args = {{ factory.name = support.node.driver node.name = Private-Driver node.group = pipewire.dummy priority.driver = 20000 }} }}
"""
        + sinks
        + "]\n"
    )


class Probe:
    def __init__(self, work):
        self.work = work
        self.processes = []
        self.owners = {}
        self.handles = []
        self.commands = []
        self.stops = []
        self.threads = []
        self.request_id = 0
        self.server_dir = work / "server"
        self.server_dir.mkdir()
        sandbox._prepare_directory(self.server_dir)
        (self.server_dir / "runtime").mkdir(mode=0o700)
        (self.server_dir / "runtime/fifo").mkdir(mode=0o700)
        (self.server_dir / "config").mkdir()
        self.stdlib, files, self.scripts = audio._runtime()
        files = set(files)
        files.update(sandbox._runtime_files(MIXER, allow_static_extension=True))
        for tool in ("pw-cat", "pw-dump", "pw-link"):
            files.update(sandbox._runtime_files(Path("/usr/bin") / tool))
        self.files = tuple(sorted(files))
        # The writer receives only the closure of cat: no PipeWire libraries.
        self.writer_files = tuple(sorted(sandbox._runtime_files(Path("/usr/bin/cat"))))
        configs = audio.configurations()
        (self.server_dir / "config/pipewire.conf").write_text(server_conf())
        (self.server_dir / "config/wireplumber.conf").write_text(
            configs["wireplumber.conf"]
        )
        (self.server_dir / "config/client.conf").write_text(
            "context.properties = { support.dbus = false }\n"
            + audio._spa()
            + audio._modules(("protocol-native", "client-node", "adapter", "metadata"))
        )
        for name in ("pipewire.conf", "wireplumber.conf", "client.conf"):
            (OUT / ("config-" + name)).write_text(
                (self.server_dir / "config" / name).read_text()
            )
        self.writer_dir = work / "writer"
        self.writer_dir.mkdir()
        sandbox._prepare_directory(self.writer_dir)

    def spawn(self, label, command, **kwargs):
        log = (OUT / (label + ".log")).open("ab")
        self.handles.append(log)
        p = subprocess.Popen(
            command,
            cwd="/",
            env=sandbox._ENV,
            stdin=kwargs.pop("stdin", subprocess.DEVNULL),
            stderr=log,
            bufsize=0,
            **kwargs,
        )
        self.processes.append(p)
        self.commands.append({"label": label, "argv": command})
        self.owners[id(p)] = OwnedProcess(p)
        return p

    def start_server(self):
        command = audio._command(self.server_dir, self.stdlib, self.files, self.scripts)
        index = command.index(str(audio.WORKER))
        command[index] = str(HERE / "radio_output_link_worker.py")
        command[command.index("--") : command.index("--")] = [
            "--setenv",
            "PIPEWIRE_DEBUG",
            "3",
            "--setenv",
            "WIREPLUMBER_DEBUG",
            "3",
        ]
        self.server = self.spawn(
            "server", command, stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        line = until(lambda: self.read_line(self.server.stdout), timeout=12)
        assert line == b"READY\n", line

    def read_line(self, handle):
        with selectors.DefaultSelector() as s:
            s.register(handle, selectors.EVENT_READ)
            return handle.readline() if s.select(0.05) else None

    def request(self, argv, background=False, timeout=4):
        self.request_id += 1
        rid = self.request_id
        self.commands.append({"label": "in-capsule-" + str(rid), "argv": argv})
        message = {"id": rid, "argv": argv, "background": background}
        message["timeout"] = timeout
        self.server.stdin.write((json.dumps(message) + "\n").encode())
        line = until(lambda: self.read_line(self.server.stdout), timeout=timeout + 4)
        reply = json.loads(line)
        assert reply["id"] == rid, reply
        return rid, reply

    def tool_path(self, rid, suffix):
        return self.server_dir / "runtime/tools" / (str(rid) + suffix)

    def tool(self, program, args, timeout=4):
        rid, reply = self.request(["/usr/bin/" + program, *args], timeout=timeout)
        text = self.tool_path(rid, ".out").read_bytes().decode(errors="replace")
        err = self.tool_path(rid, ".err").read_bytes().decode(errors="replace")
        return reply.get("rc"), text, err

    def dump(self):
        for attempt in range(6):
            rc, text, err = self.tool("pw-dump", [])
            assert rc == 0, (rc, err[:2000])
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                if attempt == 5:
                    raise
                time.sleep(0.05)

    def close(self):
        for e in self.stops:
            e.set()
        for thread in self.threads:
            thread.join(timeout=2)
        left = {}
        for p in reversed(self.processes):
            owner = self.owners[id(p)]
            try:
                owner.stop()
            except Exception as error:  # record, never signal foreign PIDs
                left[str(p.pid)] = repr(error)
            for h in (p.stdin, p.stdout, p.stderr):
                if h is not None:
                    try:
                        h.close()
                    except OSError:
                        pass
            if owner.pids:
                left[str(p.pid)] = sorted(owner.pids)
        for h in self.handles:
            h.close()
        (OUT / "commands.json").write_text(json.dumps(self.commands, indent=2) + "\n")
        tools = self.server_dir / "runtime/tools"
        if tools.is_dir():
            for item in sorted(tools.iterdir()):
                if item.suffix == ".err" and item.stat().st_size:
                    (OUT / ("tool-" + item.name)).write_bytes(item.read_bytes())
        return left
