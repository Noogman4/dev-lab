"""Synthetic scanners only, inside the existing isolated test runner."""

import math
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace

import pytest

from netmon.core import clamav_process as scan
from netmon.features import clamav_controller as controller
from netmon import app as app_module


def command(source):
    return [sys.executable, "-I", "-u", "-c", source]


@pytest.fixture
def processes():
    children = []
    yield children
    for child in children:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=2)


def run(source, processes, *, timeout=2, cancelled=lambda: False, progress=None):
    return scan.run_scan(
        command(source),
        timeout=timeout,
        cancelled=cancelled,
        started=processes.append,
        progress=progress,
    )


@pytest.mark.parametrize("code", [0, 1, 2])
def test_normal_exit_preserves_summary_and_all_findings(processes, code):
    progress = []
    result = run(
        "import sys; print('/safe: OK'); print('/bad: Test.Signature FOUND'); "
        "print('Scanned files: 2'); print('Infected files: 1'); sys.exit("
        + str(code)
        + ")",
        processes,
        progress=progress.append,
    )
    assert result.returncode == code
    assert not result.cancelled and not result.timed_out
    assert result.scanned == 2 and progress[-1] == 2
    assert controller.clamav_parse_scanned_files(result.output) == 2
    assert controller.clamav_parse_infected_count(result.output) == 1
    assert len(controller.clamav_extract_findings(result.output, "test", "now")) == 1
    assert processes[0].returncode == code and processes[0].stdout.closed


@pytest.mark.parametrize(
    "source",
    [
        "import time; time.sleep(60)",
        "import os,time; os.write(1,b'partial'); time.sleep(60)",
        "import os,time; os.close(1); os.close(2); time.sleep(60)",
        "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)",
    ],
)
def test_silent_partial_and_term_resistant_scanners_have_absolute_deadlines(
    processes, source
):
    before = time.monotonic()
    result = run(source, processes, timeout=0.2)
    assert result.returncode == 124 and result.timed_out and not result.cancelled
    assert time.monotonic() - before < 2
    assert processes[0].returncode is not None and processes[0].stdout.closed


def test_trickle_does_not_restart_deadline(processes):
    before = time.monotonic()
    result = run(
        "import os,time\nwhile True:\n os.write(1,b'x'); time.sleep(.02)",
        processes,
        timeout=0.2,
    )
    assert result.returncode == 124 and time.monotonic() - before < 2


@pytest.mark.parametrize(
    "source",
    [
        "import time; time.sleep(60)",
        "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)",
        "import os,time\nwhile True:\n os.write(1,b'x\\n'*100); time.sleep(.001)",
    ],
)
def test_cancel_terminates_and_reaps_even_silent_or_verbose_scanners(processes, source):
    start = time.monotonic()
    result = run(
        source, processes, timeout=3, cancelled=lambda: time.monotonic() - start > 0.1
    )
    assert result.cancelled and not result.timed_out
    assert result.returncode == -signal.SIGTERM
    assert time.monotonic() - start < 2
    assert processes[0].returncode is not None


@pytest.mark.parametrize("limit", ["line", "bytes", "findings"])
def test_resource_limit_is_failure_not_clean_or_nonfatal_completion(
    processes, monkeypatch, limit
):
    monkeypatch.setattr(scan, "MAX_OUTPUT_BYTES", 4096)
    monkeypatch.setattr(scan, "MAX_LINE_BYTES", 64)
    monkeypatch.setattr(scan, "MAX_FINDINGS", 3)
    source = {
        "line": "import os,time; os.write(1,b'x'*65); time.sleep(60)",
        "bytes": "import os,time; os.write(1,b'x\\n'*3000); time.sleep(60)",
        "findings": "import os,time; os.write(1,b'/bad: Sig FOUND\\n'*4); time.sleep(60)",
    }[limit]
    result = run(source, processes)
    assert result.returncode == scan.LIMIT_RETURN_CODE
    assert not result.cancelled and not result.timed_out
    assert "scan incomplete" in result.output
    assert "resource limit exceeded" in result.output
    assert not controller.clamav_allows_nonfatal_scan_completion(result.output, 0)
    assert len(result.output) < 5000
    assert processes[0].returncode is not None


def test_capture_memory_and_tail_are_bounded_and_findings_not_lost():
    output = scan._Output()
    output.feed(b"/first: Sig FOUND\n")
    for _index in range(8000):
        output.feed(b"ordinary scan diagnostic line\n")
    output.feed(b"Scanned files: 8001\nInfected files: 1\n")
    output.finish()
    assert output.tail_size <= scan.TAIL_BYTES
    assert len(output.text().encode()) <= scan.TAIL_BYTES + scan.MAX_LINE_BYTES
    assert output.text().count("/first: Sig FOUND") == 1
    assert controller.clamav_parse_scanned_files(output.text()) == 8001


@pytest.mark.parametrize("split", range(1, 16))
def test_split_utf8_and_partial_final_line_are_parsed_once(split):
    data = "/ä: Sig FOUND\r\nScanned files: 1".encode()
    output = scan._Output()
    for index in range(0, len(data), split):
        output.feed(data[index : index + split])
    output.finish()
    assert output.scanned == 1
    assert output.text().count("/ä: Sig FOUND") == 1
    assert controller.clamav_parse_scanned_files(output.text()) == 1


def test_invalid_utf8_is_bounded_and_does_not_break_cleanup(processes):
    result = run("import os;os.write(1,b'\\xff\\n')", processes)
    assert result.returncode == 0 and "\ufffd" in result.output


@pytest.mark.parametrize("timeout", [0, -1, math.inf, -math.inf, math.nan, "invalid"])
def test_invalid_timeout_cannot_spawn(monkeypatch, timeout):
    monkeypatch.setattr(
        scan.subprocess, "Popen", lambda *_a, **_k: pytest.fail("spawn")
    )
    with pytest.raises(ValueError):
        scan.run_scan(
            [], timeout=timeout, cancelled=lambda: False, started=lambda _p: None
        )


@pytest.mark.parametrize("failure", ["started", "progress", "read", "selector"])
def test_callback_and_io_errors_cleanup_process_and_descriptors(
    processes, monkeypatch, failure
):
    def fail(*_args, **_kwargs):
        raise RuntimeError("synthetic failure")

    def started(process):
        processes.append(process)
        if failure == "started":
            fail()

    if failure == "read":
        original = os.read

        def read(fd, size):
            if processes and fd == processes[0].stdout.fileno():
                fail()
            return original(fd, size)

        monkeypatch.setattr(scan.os, "read", read)
    if failure == "selector":
        monkeypatch.setattr(scan.selectors, "DefaultSelector", fail)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        scan.run_scan(
            command("import time; print('/x: OK',flush=True); time.sleep(60)"),
            timeout=2,
            cancelled=lambda: False,
            started=started,
            progress=fail if failure == "progress" else None,
        )
    assert processes[0].returncode is not None and processes[0].stdout.closed


@pytest.mark.parametrize("leader_exits", [False, True])
def test_term_resistant_descendant_holding_stdout_is_killed(
    processes, tmp_path, leader_exits
):
    pidfile = tmp_path / "child.pid"
    source = (
        "import os,signal,time\n"
        "signal.signal(signal.SIGTERM,signal.SIG_IGN)\n"
        "pid=os.fork()\n"
        "if pid==0:\n time.sleep(60)\nelse:\n"
        f" open({str(pidfile)!r},'w').write(str(pid))\n"
        + (" os._exit(0)\n" if leader_exits else " time.sleep(60)\n")
    )
    result = run(source, processes, timeout=0.3)
    assert result.timed_out and result.returncode == 124
    child = int(pidfile.read_text())
    # SIGKILL delivery to an orphan can be scheduled just after leader wait().
    # Allow bounded scheduling time, never treating a live child as success.
    end = time.monotonic() + 1
    while True:
        try:
            status = Path(f"/proc/{child}/status").read_text()
        except FileNotFoundError:
            status = ""
        if not status or "State:\tZ" in status or time.monotonic() >= end:
            break
        time.sleep(0.01)
    assert not status or "State:\tZ" in status
    assert processes[0].returncode is not None


@pytest.mark.parametrize("wrapper", ["cancel", "progress"])
@pytest.mark.parametrize(
    "outcome", ["success", "timeout", "cancel", "limit", "launch-error"]
)
def test_controller_wrappers_restore_state_and_preserve_result_shape(
    monkeypatch, wrapper, outcome
):
    states = []
    app = SimpleNamespace(
        _set_clamav_abort_button_state=states.append, clamav_cancel_requested=False
    )

    def execute(_command, **kwargs):
        if outcome == "launch-error":
            raise OSError("synthetic launch failure")
        kwargs["started"](SimpleNamespace(pid=123))
        assert app.clamav_active_process.pid == 123
        if outcome == "cancel":
            app.clamav_cancel_requested = True
            assert kwargs["cancelled"]()
        return scan.ScanResult(
            {"success": 0, "timeout": 124, "cancel": -15, "limit": 125}[outcome],
            "output",
            outcome == "cancel",
            outcome == "timeout",
            5,
        )

    monkeypatch.setattr(controller.clamav_process, "run_scan", execute)
    method = (
        controller.run_clamscan_with_cancel
        if wrapper == "cancel"
        else controller.run_clamscan_with_progress
    )
    if outcome == "launch-error":
        with pytest.raises(OSError):
            method(app, ["synthetic"])
    else:
        result = method(app, ["synthetic"])
        assert len(result) == (3 if wrapper == "cancel" else 5)
        assert (
            result[0]
            == {"success": 0, "timeout": 124, "cancel": -15, "limit": 125}[outcome]
        )
    assert states == [True, False]
    assert app.clamav_active_process is None and app.clamav_cancel_requested is False


def test_abort_only_requests_worker_cleanup(monkeypatch):
    logs = []
    app = SimpleNamespace(
        security_clamav_running=True, clamav_cancel_requested=False, log=logs.append
    )
    monkeypatch.setattr(
        os, "killpg", lambda *_a: pytest.fail("UI must not signal processes")
    )
    controller.clamav_abort_scan(app)
    assert app.clamav_cancel_requested and logs


@pytest.mark.parametrize("rc", [124, scan.LIMIT_RETURN_CODE])
def test_download_scan_cannot_report_clean_after_deadline_or_resource_limit(
    tmp_path, monkeypatch, rc
):
    target = tmp_path / "synthetic-download"
    target.write_text("not scanned by a real antivirus")
    statuses, messages = [], []
    app = SimpleNamespace(
        security_clamav_running=False,
        tr=lambda _key, fallback: fallback,
        _download_scan_clamav_available=lambda: True,
        _set_download_scan_status=lambda **kw: statuses.append(kw),
        _update_download_scan_result_text=messages.append,
        _clamav_progress_start=lambda **_kw: None,
        _clamav_progress_update_safe=lambda _count: None,
        _clamav_progress_finish_safe=lambda: None,
        _clamav_database_args=lambda: [],
        _run_clamscan_with_cancel=lambda *_a, **_kw: (
            rc,
            "Scanned files: 10\nInfected files: 0\nresource limit exceeded",
            False,
        ),
        _clamav_parse_infected_count=controller.clamav_parse_infected_count,
        _clamav_parse_scanned_files=controller.clamav_parse_scanned_files,
        _clamav_allows_nonfatal_scan_completion=controller.clamav_allows_nonfatal_scan_completion,
        _clamav_extract_error_message=controller.clamav_extract_error_message,
        _download_scan_maybe_move_clean_file=lambda _p: pytest.fail(
            "Unsafe clean-file move"
        ),
    )

    class InlineThread:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(app_module, "threading", SimpleNamespace(Thread=InlineThread))
    app_module.App._run_download_scan(app, str(target), target_kind="file")
    assert not app.security_clamav_running
    assert statuses[-1]["result"] == (
        "Scan-Zeitlimit erreicht" if rc == 124 else "ClamAV-Fehler"
    )
    assert not any("completed" in item.get("log_message", "") for item in statuses)
    assert target.exists()
