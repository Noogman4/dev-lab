"""Real offline ZIP worker and exact-grant compromise model, private fixtures only."""

import ast
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import stat
import sys
import zipfile


def run(root, output, host, port):
    sys.path.insert(0, str(root))
    from netmon.core import radio_sandbox as api, projectm_zip as wire
    from netmon import netmon_projectm_sidecar as sidecar
    from netmon.core.projectm_import_plan import ImportPlan

    presets = output / "zip-presets"
    old = presets / "Downloaded Packs" / "Pack"
    old.mkdir(parents=True)
    (old / "keep.milk").write_bytes(b"KEEP")
    app = type(
        "ZipApp",
        (),
        {
            "radio_projectm_preset_dir": str(presets),
            "netmon_state_dir": str(output / "zip-state"),
        },
    )()
    good = output / "selected.zip"
    with zipfile.ZipFile(good, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Folder/one.milk", b"[preset00]\nfRating=1\n")
        archive.writestr("Folder/texture.png", b"OPAQUE ASSET")
    original = hashlib.sha256(good.read_bytes()).hexdigest()
    result = sidecar.install_projectm_preset_archive(app, str(good), "Pack")
    assert result["imported_presets"] == 1 and result["imported_assets"] == 1
    assert (
        Path(result["target_dir"]) / "one.milk"
    ).read_bytes() == b"[preset00]\nfRating=1\n"
    assert original == hashlib.sha256(good.read_bytes()).hexdigest()
    assert (old / "keep.milk").read_bytes() == b"KEEP"
    cases = {}
    corrupt = bytearray(good.read_bytes())
    # Keep the deflated stream valid but falsify its expected CRC in both headers.
    corrupt[14] ^= 1
    corrupt[corrupt.index(b"PK\x01\x02") + 16] ^= 1
    bad = output / "crc.zip"
    bad.write_bytes(corrupt)
    cases["crc"] = bad
    for name in ("traversal", "symlink", "ratio", "objects"):
        path = output / (name + ".zip")
        with zipfile.ZipFile(path, "w") as archive:
            if name == "traversal":
                archive.writestr("../outside.milk", b"bad")
            elif name == "symlink":
                info = zipfile.ZipInfo("link.milk")
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, b"../outside")
            elif name == "ratio":
                archive.writestr(
                    "bomb.milk", b"A" * 100000, compress_type=zipfile.ZIP_DEFLATED
                )
            else:
                for index in range(100):
                    archive.writestr(
                        "/".join(
                            [f"b{index}", *[f"d{d}" for d in range(30)], "one.milk"]
                        ),
                        b"",
                    )
        cases[name] = path
    before = sorted(str(p.relative_to(presets)) for p in presets.rglob("*"))
    for name, path in cases.items():
        try:
            sidecar.install_projectm_preset_archive(app, str(path), name)
        except api.RadioSandboxError:
            pass
        else:
            raise AssertionError("invalid ZIP accepted: " + name)
        assert before == sorted(str(p.relative_to(presets)) for p in presets.rglob("*"))
    assert not (output / "outside.milk").exists()

    # Preserve the full 50,000-preset planning capacity without publishing them.
    capacity = output / "capacity.zip"
    with zipfile.ZipFile(capacity, "w") as archive:
        for index in range(50000):
            archive.writestr(f"p{index:05d}.milk", b"")
    with wire.prepared_archive(capacity) as prepared:
        plan = ImportPlan(
            prepared.members,
            wire.PRESET_EXTENSIONS,
            wire.PRESET_EXTENSIONS | wire.ASSET_EXTENSIONS,
        )
        assert len(plan.files) == 50000 and len(plan.budget.planned) == 100003
    report = {"real_import": result, "rejected": list(cases), "capacity": 50000}

    # Replace only script contents, retain the actual limits, namespace and binds.
    script = output / "zip-boundary-probe.py"
    text = api.PRESET_ZIP.read_text()
    limit = next(
        node
        for node in ast.parse(text).body
        if isinstance(node, ast.FunctionDef) and node.name == "apply_process_limits"
    )
    private = output / "zip-private-key"
    private.write_text("SYNTHETIC PRIVATE DATA")
    name = "zip-" + output.name
    with (
        private.open("rb") as secret,
        socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener,
    ):
        secret_fd = fcntl.fcntl(secret.fileno(), fcntl.F_DUPFD, 200)
        os.set_inheritable(secret_fd, True)
        listener.bind("\0" + name)
        listener.listen(2)
        program = (
            "import os,socket,resource,json,struct,sys\nMAX_WIRE_BYTES="
            + str(wire.MAX_WIRE_BYTES)
            + "\n"
            + ast.get_source_segment(text, limit)
            + "\napply_process_limits()\n"
        )
        program += "def reachable(address,family):\n s=socket.socket(family,socket.SOCK_STREAM)\n s.settimeout(.2)\n try:\n  s.connect(address);return True\n except OSError:return False\n finally:s.close()\n"
        program += "def writable(path):\n try:\n  f=os.open(path,os.O_WRONLY);os.close(f);return True\n except OSError:return False\n"
        program += f"r={{'private':os.path.exists({str(private)!r}),'original':os.path.exists({str(good)!r}),'archive_write':writable('/media/archive.zip'),'tcp':reachable(({host!r},{port}),socket.AF_INET),'abstract':reachable({chr(0)+name!r},socket.AF_UNIX),'request':os.path.exists('/run/request.json'),'control':os.path.exists('/run/control'),'audio':os.path.exists('/run/audio/pulse'),'secret_env':'RADIO_ZIP_FAKE_KEY' in os.environ}}\n"
        program += "with open('/media/archive.zip','rb') as h:r['archive_read']=bool(h.read(4));r['proc_reopen_write']=writable('/proc/self/fd/'+str(h.fileno()))\n"
        program += f"try:os.fstat({secret_fd});r['inherited_fd']=True\nexcept OSError:r['inherited_fd']=False\n"
        program += "try:p=os.fork()\nexcept OSError:r['fork']=False\nelse:\n if p==0:os._exit(0)\n os.waitpid(p,0);r['fork']=True\n"
        program += "r.update(memory=resource.getrlimit(resource.RLIMIT_AS)[1],cpu=resource.getrlimit(resource.RLIMIT_CPU)[1],filesize=resource.getrlimit(resource.RLIMIT_FSIZE)[1])\np=json.dumps(r).encode();row=json.dumps({'parts':['probe.milk'],'size':len(p),'compressed':10,'method':8}).encode();sys.stdout.buffer.write(b'NMPZ1\\0'+struct.pack('>II',1,len(row))+row+p+b'NMPZ-END\\0')\n"
        script.write_text(program)
        original_command = api._zip_command

        def substitute(*args):
            command = original_command(*args)
            for i in range(len(command) - 2):
                if command[i] == "--ro-bind" and command[i + 2] == "/run/zip.py":
                    command[i + 1] = str(script)
            return command

        old_environment = os.environ.get("RADIO_ZIP_FAKE_KEY")
        os.environ["RADIO_ZIP_FAKE_KEY"] = "SYNTHETIC KEY"
        api._zip_command = substitute
        try:
            with wire.prepared_archive(good) as prepared:
                from netmon.core.archive_limits import ByteBudget

                data = io.BytesIO()
                prepared.copy_member(prepared.members[0][0], data, ByteBudget(10000))
                boundary = json.loads(data.getvalue())
        finally:
            api._zip_command = original_command
            os.close(secret_fd)
            if old_environment is None:
                os.environ.pop("RADIO_ZIP_FAKE_KEY", None)
            else:
                os.environ["RADIO_ZIP_FAKE_KEY"] = old_environment
    assert all(
        boundary[key] is False
        for key in (
            "private",
            "original",
            "archive_write",
            "proc_reopen_write",
            "tcp",
            "abstract",
            "request",
            "control",
            "audio",
            "secret_env",
            "inherited_fd",
            "fork",
        )
    ), boundary
    assert boundary["archive_read"] is True
    assert (
        0 < boundary["memory"] <= 512 * 1024 * 1024
        and 0 < boundary["cpu"] <= 30
        and 0 < boundary["filesize"] <= wire.MAX_WIRE_BYTES
    )
    assert original == hashlib.sha256(good.read_bytes()).hexdigest()
    report["boundary"] = boundary
    return report
