"""Exact PCM relay grants, invoked by the private-network coordinator only."""

import ast
import fcntl
import json
import os
import socket
import subprocess
import sys


def run(root, output, host, port):
    sys.path.insert(0, str(root))
    from netmon.core import radio_sandbox as api, radio_pcm as pcm

    directory = output / "pcm-session"
    directory.mkdir(mode=0o700)
    api._prepare_directory(directory)
    (directory / "tap").mkdir(mode=0o700)
    stdlib, runtime = api._pcm_runtime()
    command = api._pcm_command(directory, stdlib, runtime)
    data = bytes(range(256)) * 4096
    for listening in (False, True):
        receiver = None
        if listening:
            receiver = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            receiver.bind(str(directory / "tap/pcm.sock"))
            receiver.settimeout(0.1)
        try:
            process = subprocess.run(
                command,
                cwd="/",
                env=api._ENV,
                input=data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                timeout=8,
            )
            body, error = process.stdout, process.stderr
            assert process.returncode == 0, error
            assert body == data
            if receiver is not None:
                queued = []
                offset = 0
                while True:
                    try:
                        packet = receiver.recv(pcm.MAX_PACKET + 1)
                    except socket.timeout:
                        break
                    sequence, payload = pcm.decode_packet(packet)
                    assert sequence == len(queued)
                    assert payload == data[offset : offset + len(payload)]
                    offset += len(payload)
                    queued.append(sequence)
                assert queued and len(queued) < len(data) // 4096
        finally:
            if receiver is not None:
                receiver.close()
                (directory / "tap/pcm.sock").unlink()
    report = {
        "bytes_exact_each": len(data),
        "absent_receiver": True,
        "stalled_receiver": True,
        "queued_packets": len(queued),
    }

    # Model a compromised relay: only replace the fixed script, retain grants.
    tree = ast.parse(api.PCM.read_text())
    limit = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "apply_process_limits"
    )
    private = output / "pcm-private-key"
    private.write_text("SYNTHETIC PCM SECRET")
    (directory / "request.json").write_text("PRIVATE REQUEST")
    abstract = "\0netmon-pcm-probe-" + str(os.getpid())
    script = output / "pcm-boundary-probe.py"
    script.write_text(
        "import json,os,socket,resource\n"
        + ast.unparse(limit)
        + "\napply_process_limits()\n"
        + "def attempt(action):\n"
        " try: action(); return True\n"
        " except OSError: return False\n" + "def connect(address, family):\n"
        " with socket.socket(family,socket.SOCK_STREAM) as s:\n"
        "  s.settimeout(0.2); s.connect(address)\n" + "def write_tap():\n"
        " with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as s:\n"
        "  s.sendto(b'INTENTIONAL PCM CHANNEL','/run/tap/pcm.sock')\n"
        + "r = {}\n"
        + f"r['private'] = attempt(lambda: open({str(private)!r}).read())\n"
        + "for name,path in [('control','/run/control/mpv.sock'),('audio','/run/audio/pulse'),('request','/run/request.json')]:\n"
        " r[name] = attempt(lambda: open(path).read())\n"
        + f"r['tcp'] = attempt(lambda: connect(({host!r},{port!r}),socket.AF_INET))\n"
        + f"r['abstract'] = attempt(lambda: connect({abstract!r},socket.AF_UNIX))\n"
        + "r['tap_write'] = attempt(write_tap)\n"
        "r['tap_create_file'] = attempt(lambda: open('/run/tap/unwanted','w').write('x'))\n"
        "r['secret_env'] = 'NETMON_PCM_SECRET' in os.environ\n"
        "r['inherited_fd'] = attempt(lambda: os.read(int(FD),1))\n"
        "r['memory'] = resource.getrlimit(resource.RLIMIT_AS)[0]\n"
        "try:\n"
        " child=os.fork()\n"
        " if child == 0: os._exit(0)\n"
        " os.waitpid(child,0);r['fork']=True\n"
        "except OSError: r['fork']=False\n"
        "print(json.dumps(r))\n"
    )
    descriptor = os.open(private, os.O_RDONLY)
    inherited = fcntl.fcntl(descriptor, fcntl.F_DUPFD, 200)
    os.close(descriptor)
    os.set_inheritable(inherited, True)
    script.write_text(script.read_text().replace("int(FD)", str(inherited)))
    command[command.index(str(api.PCM))] = str(script)
    previous = os.environ.get("NETMON_PCM_SECRET")
    os.environ["NETMON_PCM_SECRET"] = "SYNTHETIC ENV SECRET"
    try:
        with (
            socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
            socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as tap,
        ):
            listener.bind(abstract)
            listener.listen(1)
            tap.bind(str(directory / "tap/pcm.sock"))
            tap.settimeout(1)
            process = subprocess.run(
                command,
                cwd="/",
                env=api._ENV,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                timeout=8,
            )
            body, error = process.stdout, process.stderr
            assert process.returncode == 0, error
            measured = json.loads(body)
            assert measured.pop("tap_write") is True
            assert tap.recv(128) == b"INTENTIONAL PCM CHANNEL"
            assert measured.pop("memory") == 128 * 1024 * 1024
            assert not any(measured.values()), measured
            report["boundary"] = {
                **measured,
                "tap_write": True,
                "memory": 128 * 1024 * 1024,
            }
    finally:
        os.close(inherited)
        if previous is None:
            os.environ.pop("NETMON_PCM_SECRET", None)
        else:
            os.environ["NETMON_PCM_SECRET"] = previous
        (directory / "tap/pcm.sock").unlink(missing_ok=True)
    return report
