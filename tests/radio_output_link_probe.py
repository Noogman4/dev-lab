"""Private PipeWire link-idempotence probe, via existing isolated starter.

Reuses a frozen, previously tested server fixture read-only. All pw-dump and
pw-link tools run inside that server's capsule. No host audio or restart.
"""

from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import traceback


def run(root, output):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from netmon.core import radio_fifo_output as fifo

    fixture = (
        root / "backups/netmon-gpacat-step3-integration-20261109-claude/probe_base.py"
    )
    spec = importlib.util.spec_from_file_location("private_radio_link_fixture", fixture)
    base = importlib.util.module_from_spec(spec)
    argv = sys.argv
    try:
        sys.argv = [str(fixture), "unused-output"]
        spec.loader.exec_module(base)
    finally:
        sys.argv = argv
    base.OUT = output  # no writes into the frozen fixture
    result = {"status": "error", "host_audio": False, "host_restart": False}
    probe = None
    calls = []
    try:
        with ExitStack() as cleanup:
            name = cleanup.enter_context(
                tempfile.TemporaryDirectory(prefix="rlink-", dir="/tmp/user/1000")
            )
            probe = base.Probe(Path(name))

            def close_probe():
                result["remaining_owned_processes"] = probe.close()
                if result["remaining_owned_processes"]:
                    result["status"] = "cleanup-error"

            cleanup.callback(close_probe)
            probe.start_server()

            def routed(argv, *, timeout):
                assert argv[0] in {str(fifo.PW_DUMP), str(fifo.PW_LINK)}
                rc, out, err = probe.tool(Path(argv[0]).name, argv[1:], timeout=timeout)
                calls.append({"argv": argv, "rc": rc, "stderr": err})
                return rc, out

            def ready():
                g = probe.dump()
                try:
                    tunnel = fifo.find_tunnel(g, Path(base.FIFO_CAPSULE))
                    sink = fifo.default_sink(g)
                    if (
                        len(fifo._ports(g, tunnel, "out")) >= 2
                        and len(fifo._ports(g, sink, "in")) >= 2
                    ):
                        return g
                except fifo.RadioOutputError:
                    return None
                return None

            initial = base.until(ready)
            (output / "graph-before.json").write_text(json.dumps(initial, indent=2))
            linked = fifo.link(Path(base.FIFO_CAPSULE), routed)
            assert fifo.verify(linked, routed)
            existing = probe.dump()
            (output / "graph-existing.json").write_text(json.dumps(existing, indent=2))
            # Tools have already exited: successful links remain in the server.
            result["initial_pairs"] = linked.pairs
            duplicate_rc, _out = routed(
                [str(fifo.PW_LINK), *map(str, linked.pairs[0])], timeout=3
            )
            result["raw_duplicate_rc"] = duplicate_rc
            assert duplicate_rc != 0
            before_calls = len(calls)
            try:
                second = fifo.link(Path(base.FIFO_CAPSULE), routed)
            except fifo.RadioOutputError as exc:
                result.update(
                    {
                        "status": "reproduced-existing-link-failure",
                        "second_start_error": str(exc),
                    }
                )
            else:
                assert second == linked
                assert fifo.verify(second, routed)
                assert not any(
                    c["argv"][0] == str(fifo.PW_LINK) for c in calls[before_calls:]
                )
                result["second_start_reused_both"] = True
                assert fifo.unlink(second, routed)
                assert not fifo.verify(second, routed)
                # Leave just the left channel as an orphan, then complete it.
                assert (
                    routed([str(fifo.PW_LINK), *map(str, linked.pairs[0])], timeout=3)[
                        0
                    ]
                    == 0
                )
                before_calls = len(calls)
                completed = fifo.link(Path(base.FIFO_CAPSULE), routed)
                assert fifo.verify(completed, routed)
                made = [
                    c["argv"][1:]
                    for c in calls[before_calls:]
                    if c["argv"][0] == str(fifo.PW_LINK)
                ]
                assert made == [list(map(str, linked.pairs[1]))]
                assert fifo.unlink(completed, routed)
                result.update(
                    {
                        "status": "passed",
                        "partial_link_completed": True,
                        "links_removed_after_stop": True,
                    }
                )
    except Exception:
        result["error"] = traceback.format_exc()
    result["tool_calls"] = calls
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1
