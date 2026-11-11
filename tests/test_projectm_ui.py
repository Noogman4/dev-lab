"""Tk-facing callbacks only use cached state and never join a capsule worker."""

import threading
import time
import sys
import subprocess
import py_compile
import os
from types import MethodType, SimpleNamespace

import pytest

from netmon import netmon_projectm_sidecar as sidecar, netmon_radio_app as ui


class Variable:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


@pytest.fixture
def app(monkeypatch):
    # Existing status/timer models do not construct Tk; real windows are tested separately.
    monkeypatch.setattr(ui.projectm_pixel_window, "ensure", lambda *_: None)
    data = SimpleNamespace(
        radio_projectm_proc=None,
        radio_projectm_last_started_at="",
        radio_projectm_last_stopped_at="",
        _projectm_status_after=None,
        _projectm_observed_request=None,
        _projectm_closing=False,
        callbacks={},
        cancelled=[],
    )
    for name in ("status", "meta", "history", "install", "preset", "preset_hint"):
        setattr(data, "radio_projectm_" + name + "_var", Variable())
    data.tr = lambda key, default=None: default or key
    data.log_safe = lambda _: None
    data._timestamp_text = lambda: "STAMP"
    data._refresh_radio_miniplayer_content = lambda: None
    data.winfo_exists = lambda: True

    def after(_delay, callback):
        key = str(len(data.callbacks) + 1)
        data.callbacks[key] = callback
        return key

    data.after = after
    data.after_cancel = lambda key: data.cancelled.append(key)
    for name in (
        "_refresh_projectm_status",
        "open_projectm_visualizer_test",
        "close_projectm_visualizer_test",
    ):
        setattr(data, name, MethodType(getattr(ui.NetMonRadioApp, name), data))
    return data


def state(**kwargs):
    return {
        "status_text": "STATE",
        "polling": True,
        "phase": "starting",
        "pid": 0,
        **kwargs,
    }


def test_refresh_schedules_only_one_poll_and_never_marks_pending_as_started(
    app, monkeypatch
):
    monkeypatch.setattr(sidecar, "describe_projectm_sidecar_runtime", lambda _: state())
    app._refresh_projectm_status()
    app._refresh_projectm_status()
    assert len(app.callbacks) == 1 and app._projectm_status_after == "1"
    assert not app.radio_projectm_last_started_at


def test_callback_reads_current_request_instead_of_publishing_old_result(
    app, monkeypatch
):
    observed = []

    def describe(value):
        observed.append(value.radio_projectm_proc)
        return state()

    monkeypatch.setattr(sidecar, "describe_projectm_sidecar_runtime", describe)
    old = object()
    app.radio_projectm_proc = old
    app._refresh_projectm_status()
    newer = object()
    app.radio_projectm_proc = newer
    app.callbacks["1"]()
    assert observed == [old, newer]


def test_start_history_only_changes_after_current_request_is_running(app, monkeypatch):
    request = object()
    app.radio_projectm_proc = request
    monkeypatch.setattr(
        sidecar,
        "describe_projectm_sidecar_runtime",
        lambda _: state(phase="running", running=True),
    )
    app._refresh_projectm_status()
    assert app.radio_projectm_last_started_at == "STAMP"
    app._timestamp_text = lambda: "LATER"
    app._refresh_projectm_status()
    assert app.radio_projectm_last_started_at == "STAMP"
    monkeypatch.setattr(
        sidecar,
        "describe_projectm_sidecar_runtime",
        lambda _: state(phase="stopped", polling=False),
    )
    app._refresh_projectm_status()
    assert app.radio_projectm_last_stopped_at == "LATER"


@pytest.mark.parametrize("closing", ["_projectm_closing", "_radio_panel_destroying"])
def test_close_cancels_timer_and_queued_callback_cannot_touch_destroyed_widget(
    app, monkeypatch, closing
):
    calls = []
    monkeypatch.setattr(sidecar, "describe_projectm_sidecar_runtime", lambda _: state())
    monkeypatch.setattr(
        sidecar, "stop_projectm_sidecar", lambda _: calls.append("cancel") or True
    )
    app._refresh_projectm_status()
    setattr(app, closing, True)
    assert app.close_projectm_visualizer_test()
    assert calls == ["cancel"] and app.cancelled == ["1"]
    app.callbacks["1"]()
    assert len(app.callbacks) == 1 and not vars(app).get("_projectm_status_after")


def test_accepted_pending_start_returns_without_claiming_started(app, monkeypatch):
    monkeypatch.setattr(
        sidecar,
        "launch_projectm_sidecar",
        lambda _: sidecar.ProjectMSidecarStatus(
            True, False, False, "private", "pending", starting=True
        ),
    )
    monkeypatch.setattr(sidecar, "describe_projectm_sidecar_runtime", lambda _: state())
    assert app.open_projectm_visualizer_test()
    assert not app.radio_projectm_last_started_at


def test_rejected_start_reports_reason_and_never_claims_success(app, monkeypatch):
    monkeypatch.setattr(
        sidecar,
        "launch_projectm_sidecar",
        lambda _: sidecar.ProjectMSidecarStatus(
            False, False, False, "private", "REJECTED"
        ),
    )
    monkeypatch.setattr(
        sidecar, "describe_projectm_sidecar_runtime", lambda _: state(polling=False)
    )
    assert not app.open_projectm_visualizer_test()
    assert app.radio_projectm_status_var.get() == "REJECTED"


def test_slow_package_discovery_is_single_background_job_and_status_does_not_write_presets(
    tmp_path, monkeypatch
):
    entered, release = threading.Event(), threading.Event()
    calls = []
    app = SimpleNamespace(radio_projectm_preset_dir=str(tmp_path))

    def probe(**kwargs):
        calls.append(threading.get_ident())
        entered.set()
        assert release.wait(3)

    monkeypatch.setattr(sidecar, "probe_projectm_package_candidates", probe)
    monkeypatch.setattr(
        sidecar,
        "get_projectm_sidecar_status",
        lambda **_: sidecar.ProjectMSidecarStatus(
            True, True, False, "fixture", "FOUND"
        ),
    )
    monkeypatch.setattr(
        sidecar,
        "ensure_projectm_preset_dir",
        lambda *_: pytest.fail("Status may not synchronize preset files"),
    )
    try:
        before = time.monotonic()
        first = sidecar.describe_projectm_sidecar_runtime(app)
        assert time.monotonic() - before < 0.2 and first["polling"]
        assert entered.wait(1)
        sidecar.describe_projectm_sidecar_runtime(app)
        assert len(calls) == 1 and calls[0] != threading.get_ident()
    finally:
        release.set()
    deadline = time.monotonic() + 2
    while vars(app).get("_projectm_probe_pending") and time.monotonic() < deadline:
        time.sleep(0.01)
    assert sidecar.describe_projectm_sidecar_runtime(app)["installed"]


def test_failed_metadata_probe_is_cached_instead_of_endless_retry(
    tmp_path, monkeypatch
):
    app = SimpleNamespace(radio_projectm_preset_dir=str(tmp_path))

    def fail(**_):
        raise RuntimeError("synthetic metadata failure")

    monkeypatch.setattr(sidecar, "probe_projectm_package_candidates", fail)
    sidecar.describe_projectm_sidecar_runtime(app)
    deadline = time.monotonic() + 2
    while vars(app).get("_projectm_probe_pending") and time.monotonic() < deadline:
        time.sleep(0.01)
    result = sidecar.describe_projectm_sidecar_runtime(app)
    assert not result["polling"] and "fehlgeschlagen" in result["status_text"]


def test_metadata_thread_failure_is_reported_without_stuck_polling(
    tmp_path, monkeypatch
):
    app = SimpleNamespace(radio_projectm_preset_dir=str(tmp_path))

    def fail(*_):
        raise RuntimeError("synthetic thread failure")

    monkeypatch.setattr(threading.Thread, "start", fail)
    result = sidecar.describe_projectm_sidecar_runtime(app)
    assert not result["polling"] and "nicht gestartet" in result["status_text"]


def test_isolated_python_ignores_a_stale_synthetic_cache(tmp_path):
    assert sys.pycache_prefix == "/nonexistent"
    source = tmp_path / "cache_fixture.py"
    source.write_text("value='OLD'\n")
    # Construct an inert stale fixture in its usual cache location, not in the repo.
    cached = (
        tmp_path / "__pycache__" / f"cache_fixture.{sys.implementation.cache_tag}.pyc"
    )
    py_compile.compile(str(source), cfile=str(cached), doraise=True)
    before = source.stat()
    source.write_text("value='NEW'\n")
    os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
    child = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import sys;sys.path.insert(0,sys.argv[1]);import cache_fixture;print(cache_fixture.value,sys.pycache_prefix)",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    assert child.stdout.strip() == "NEW /nonexistent"
