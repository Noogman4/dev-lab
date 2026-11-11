"""Tk refresh stall fix: one ufw snapshot per cycle, sudo backoff, nvidia-smi memory."""

import time

import pytest

import netmon.app as netmon
from netmon.features import firewall_controller as fc


def make_app(outputs):
    app = netmon.App.__new__(netmon.App)
    calls = []

    def run_cmd(cmd, timeout=0, text=True):
        calls.append(list(cmd))
        return outputs[min(len(calls), len(outputs)) - 1]

    app.run_cmd = run_cmd
    app.calls = calls
    return app


SUDO_EN = (1, "sudo: a password is required")
SUDO_DE = (1, "sudo: Ein Passwort ist notwendig")
ACTIVE = (0, "Status: active\n")


@pytest.mark.parametrize("failure", [SUDO_EN, SUDO_DE])
def test_sudo_password_failure_pauses_only_passive_refresh_reads(failure):
    app = make_app([failure, ACTIVE])
    fc.begin_refresh_scope(app)
    try:
        assert fc.read_ufw_status(app) == failure
        assert fc.sudo_status_backoff_active(app)
    finally:
        fc.end_refresh_scope(app)
    # Later refresh cycles skip the failing sudo while the pause lasts.
    for _ in range(5):
        fc.begin_refresh_scope(app)
        try:
            assert fc.read_ufw_status(app) == (1, "")
            assert fc.read_ufw_status(app, verbose=True) == (1, "")
        finally:
            fc.end_refresh_scope(app)
    assert len(app.calls) == 1
    # Bounded: after it expires the refresh reads again.
    app._ufw_sudo_backoff_until = time.monotonic() - 1
    fc.begin_refresh_scope(app)
    try:
        assert fc.read_ufw_status(app) == ACTIVE
        assert not fc.sudo_status_backoff_active(app)
    finally:
        fc.end_refresh_scope(app)
    assert len(app.calls) == 2


def test_explicit_reads_ignore_the_pause_and_a_live_success_clears_it():
    # Codex review R-2: reconcile/auth flows must read live right away.
    app = make_app([SUDO_EN, ACTIVE])
    fc.begin_refresh_scope(app)
    try:
        fc.read_ufw_status(app)
    finally:
        fc.end_refresh_scope(app)
    assert "_ufw_sudo_backoff_until" in app.__dict__
    assert not fc.sudo_status_backoff_active(app)  # outside any refresh
    assert fc.read_ufw_status(app) == ACTIVE and len(app.calls) == 2
    assert "_ufw_sudo_backoff_until" not in app.__dict__


@pytest.mark.parametrize(
    "failure",
    [(1, "ERROR: You need to be root to run this script"), (1, ""), (124, "x")],
)
def test_other_failures_do_not_start_a_backoff(failure):
    app = make_app([failure])
    fc.begin_refresh_scope(app)
    try:
        assert fc.read_ufw_status(app) == failure
    finally:
        fc.end_refresh_scope(app)
    assert fc.read_ufw_status(app) == failure
    assert "_ufw_sudo_backoff_until" not in app.__dict__ and len(app.calls) == 2


def test_backoff_duration_is_short_and_success_clears_it():
    assert 10 <= fc.SUDO_STATUS_BACKOFF_SECONDS <= 60
    app = make_app([SUDO_EN])
    fc.read_ufw_status(app)
    assert "_ufw_sudo_backoff_until" in app.__dict__
    fc.note_ufw_status_result(app, 0, "Status: inactive")
    assert "_ufw_sudo_backoff_until" not in app.__dict__


def test_refresh_scope_shares_one_snapshot_per_flavour():
    app = make_app([ACTIVE, (0, "Status: active\nLogging: on (low)\n")])
    fc.begin_refresh_scope(app)
    try:
        assert fc.read_ufw_status(app) == ACTIVE
        assert fc.read_ufw_status(app) == ACTIVE
        assert len(app.calls) == 1
        verbose = fc.read_ufw_status(app, verbose=True)
        assert "Logging" in verbose[1] and len(app.calls) == 2
        assert fc.read_ufw_status(app, verbose=True) == verbose
        assert len(app.calls) == 2
    finally:
        fc.end_refresh_scope(app)
    fc.read_ufw_status(app)
    assert len(app.calls) == 3  # outside a cycle every read is live


def test_refresh_snapshot_is_invisible_to_other_threads():
    # Codex review R-3: a worker must not get the display snapshot.
    import threading

    app = make_app([ACTIVE, (0, "Status: inactive\n")])
    fc.begin_refresh_scope(app)
    try:
        assert fc.read_ufw_status(app) == ACTIVE
        seen = []
        worker = threading.Thread(target=lambda: seen.append(fc.read_ufw_status(app)))
        worker.start()
        worker.join(5)
        assert seen == [(0, "Status: inactive\n")] and len(app.calls) == 2
        assert fc.refresh_scope(app) is not None
    finally:
        fc.end_refresh_scope(app)
    assert fc.refresh_scope(app) is None


def test_end_scope_from_other_thread_does_not_remove_it():
    import threading

    app = make_app([ACTIVE])
    fc.begin_refresh_scope(app)
    try:
        worker = threading.Thread(target=lambda: fc.end_refresh_scope(app))
        worker.start()
        worker.join(5)
        assert fc.refresh_scope(app) is not None
    finally:
        fc.end_refresh_scope(app)


def test_refresh_sets_and_removes_the_scope_even_on_error():
    app = netmon.App.__new__(netmon.App)
    seen = []

    def lights():
        seen.append(fc.refresh_scope(app))
        raise RuntimeError("controlled")

    app._refresh_lights = lights
    with pytest.raises(RuntimeError):
        app.refresh()
    assert seen == [{}] and "_ufw_status_scope" not in app.__dict__


def test_log_level_query_skips_sudo_during_backoff_and_plain_ufw_as_user(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    app.log = lambda *_: None
    calls = []

    def run_cmd(cmd, timeout=0):
        calls.append(list(cmd))
        return SUDO_EN

    monkeypatch.setattr(netmon, "run_cmd", run_cmd)
    monkeypatch.setattr(netmon.os, "geteuid", lambda: 1000)
    fc.begin_refresh_scope(app)
    try:
        assert app._security_query_log_level() == "–"
        assert calls == [["sudo", "-n", "ufw", "status", "verbose"]]
        assert fc.sudo_status_backoff_active(app)
        assert app._security_query_log_level() == "–"
        assert len(calls) == 1  # nothing ran during the backoff in a refresh
    finally:
        fc.end_refresh_scope(app)
    # Explicit (non-refresh) queries, e.g. the security tab, stay live.
    assert app._security_query_log_level() == "–"
    assert len(calls) == 2


def test_log_level_query_still_parses_a_working_sudo(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.log = lambda *_: None
    monkeypatch.setattr(
        netmon,
        "run_cmd",
        lambda cmd, timeout=0: (0, "Status: active\nLogging: on (medium)\n"),
    )
    monkeypatch.setattr(netmon.os, "geteuid", lambda: 1000)
    assert app._security_query_log_level().lower().startswith("on") or (
        app._security_query_log_level() != "–"
    )


def test_log_level_query_tries_plain_ufw_only_as_root(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.log = lambda *_: None
    calls = []

    def run_cmd(cmd, timeout=0):
        calls.append(list(cmd))
        return (1, "ERROR: You need to be root")

    monkeypatch.setattr(netmon, "run_cmd", run_cmd)
    monkeypatch.setattr(netmon.os, "geteuid", lambda: 0)
    app._security_query_log_level()
    assert [c[0] for c in calls] == ["sudo", "ufw"]


def test_nvidia_smi_failure_is_remembered(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "nvidia-smi")
    monkeypatch.setattr(
        netmon, "run_cmd", lambda cmd, timeout=0: calls.append(cmd) or (9, "")
    )
    monkeypatch.setattr(
        netmon.psutil, "sensors_temperatures", lambda fahrenheit=False: {}
    )
    first = app._read_gpu_temp()
    second = app._read_gpu_temp()
    assert len(calls) == 1 and first == second
    app._nvidia_smi_retry_at = time.monotonic() - 1
    app._read_gpu_temp()
    assert len(calls) == 2


def test_nvidia_smi_success_is_used_and_not_suppressed(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    monkeypatch.setattr(netmon, "has_cmd", lambda name: name == "nvidia-smi")
    monkeypatch.setattr(
        netmon, "run_cmd", lambda cmd, timeout=0: calls.append(cmd) or (0, "55\n")
    )
    assert app._read_gpu_temp() == ("nvidia-smi", 55.0)
    assert app._read_gpu_temp() == ("nvidia-smi", 55.0)
    assert len(calls) == 2 and "_nvidia_smi_retry_at" not in app.__dict__
