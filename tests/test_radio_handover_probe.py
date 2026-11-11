"""The GUI fixture may only retain cleanup handles for its own validated children."""

import ast
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize(
    "case",
    [
        "valid",
        "birth_before",
        "foreign_parent",
        "birth_during_open",
        "owner_during_open",
        "vanished",
        "missing_birth",
    ],
)
def test_fixture_cleanup_rejects_reused_or_foreign_process_identity(tmp_path, case):
    source = Path(__file__).with_name("radio_gui_probe.py")
    scenario = next(
        n
        for n in ast.parse(source.read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == "_scenario"
    )
    function = next(
        n
        for n in scenario.body
        if isinstance(n, ast.FunctionDef) and n.name == "sync_owned"
    )
    entries = [{"pid": 20, "born": 101.0, "owner_pid": 10, "kind": "bwrap"}]
    data = {10: {"born": 100.0, "parent": 1}, 20: {"born": 101.0, "parent": 10}}
    if case == "birth_before":
        data[20]["born"] = 102.0
    if case == "foreign_parent":
        data[20]["parent"] = 99
    if case == "missing_birth":
        entries[0]["born"] = None
    (tmp_path / "owned-wrappers.jsonl").write_text(json.dumps(entries[0]) + "\n")

    class Gone(Exception):
        pass

    class Process:
        def __init__(self, pid):
            if case == "vanished" and pid == 20:
                raise Gone()
            self.pid, self.born = pid, data[pid]["born"]

        def create_time(self):
            return self.born

        def ppid(self):
            return data[self.pid]["parent"]

    handles, opened = [], []
    read, write = os.pipe()

    def pidfd_open(pid):
        opened.append(pid)
        if case == "birth_during_open":
            data[20]["born"] = 102.0
        if case == "owner_during_open":
            data[10]["born"] = 99.0
        fd = os.dup(read)
        handles.append(fd)
        return fd

    namespace = {
        "WORK": tmp_path,
        "json": json,
        "identities": {10: 100.0},
        "pidfds": {},
        "psutil": SimpleNamespace(Process=Process, NoSuchProcess=Gone),
        "os": SimpleNamespace(pidfd_open=pidfd_open, close=os.close),
    }
    exec(
        compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"),
        namespace,
    )
    try:
        namespace["sync_owned"]()
        assert bool(namespace["pidfds"]) == (case == "valid")
        assert len(opened) == (
            1 if case in {"valid", "birth_during_open", "owner_during_open"} else 0
        )
        for fd in handles:
            if fd not in namespace["pidfds"].values():
                with pytest.raises(OSError):
                    os.fstat(fd)
    finally:
        for fd in namespace["pidfds"].values():
            os.close(fd)
        os.close(read)
        os.close(write)
