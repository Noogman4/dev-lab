"""Passive retries are bounded; security decisions keep reading live."""

import json
import threading
from types import SimpleNamespace

import pytest

import netmon.app as netmon
from netmon.core import command, passive_sudo as ps, ufw_snapshot
from netmon.features import firewall_controller as fc, vpn_controller as vc
from netmon.features.security_monitoring_controller import _core as security


@pytest.fixture
def clock(monkeypatch):
    now = [100.0]
    monkeypatch.setattr(ps.time, "monotonic", lambda: now[0])
    return now


def profile_app(path):
    app = netmon.App.__new__(netmon.App)
    app._wg_profile_path = lambda name: str(path / f"{name}.conf")
    return app


def test_password_failure_stops_all_passive_readers_and_retries_after_pause(
    monkeypatch, tmp_path, clock
):
    app = profile_app(tmp_path)
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return 1, "sudo: a password is required" if args[0] == "sudo" else "denied"

    app.run_cmd = run
    monkeypatch.setattr(vc, "run_cmd", run)
    monkeypatch.setattr(security, "run_cmd", run)
    monkeypatch.setattr(command, "run_cmd_with_input", run)
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)
    snapshots = ufw_snapshot.UfwSnapshotClient()
    fc.begin_refresh_scope(app)
    try:
        assert fc.read_ufw_status(app)[0] == 1
    finally:
        fc.end_refresh_scope(app)
    for tick in range(1, 10):
        clock[0] = 100 + tick * 3
        with ps.observation(app):
            assert snapshots.state() == "unknown"
            assert fc.read_ufw_status(app) == ps.UNAVAILABLE
        assert vc.profile_ipv6_display_state(app, "Irland") is None
        assert security.read_ufw_log_tail(app=app) == []
    assert len([args for args in calls if args[0] == "sudo"]) == 1
    clock[0] = 131
    with ps.observation(app):
        assert snapshots.state() == "unknown"
    assert len([args for args in calls if args[0] == "sudo"]) == 2


@pytest.mark.parametrize("source", ["helper", "profile", "tail"])
def test_auth_failure_from_each_source_pauses_other_sources(
    source, monkeypatch, tmp_path, clock
):
    app = profile_app(tmp_path)
    calls = []

    def fail(args, **kwargs):
        calls.append(args)
        return 1, "sudo: Ein Passwort ist notwendig"

    monkeypatch.setattr(command, "run_cmd_with_input", fail)
    monkeypatch.setattr(vc, "run_cmd", fail)
    monkeypatch.setattr(security, "run_cmd", fail)
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)
    if source == "helper":
        with ps.observation(app):
            assert ufw_snapshot.UfwSnapshotClient().state() == "unknown"
    elif source == "profile":
        assert vc.profile_ipv6_display_state(app, "Irland") is None
    else:
        assert security.read_ufw_log_tail(app=app) == []
    assert ps.paused(app)
    app.run_cmd = lambda *a, **kw: pytest.fail("sudo during auth pause")
    with ps.observation(app):
        assert fc.read_ufw_status(app) == ps.UNAVAILABLE


def test_passive_workers_share_the_ui_ufw_snapshot(monkeypatch, clock):
    app = netmon.App.__new__(netmon.App)
    calls = []
    app.run_cmd = lambda args, **kw: calls.append(args) or (
        0,
        "Status: active\nLogging: on (high)",
    )
    fc.begin_refresh_scope(app)
    try:
        assert fc.read_ufw_status(app)[0] == 0
    finally:
        fc.end_refresh_scope(app)
    seen = []

    def worker():
        with ps.observation(app):
            seen.append(fc.read_ufw_status(app, verbose=True))

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(3)
    assert not thread.is_alive()
    assert seen[0][0] == 0
    assert app.refresh_security_log_level() == "HIGH"
    assert len(calls) == 1
    clock[0] += 3
    assert app.refresh_security_log_level() == "HIGH"
    assert len(calls) == 2
    fc.read_ufw_status(app, verbose=True)  # explicit verification ignores TTL
    assert len(calls) == 3


def test_busy_observer_does_not_block_tk_or_explicit_reads(clock):
    app = SimpleNamespace()
    entered, release = threading.Event(), threading.Event()

    def blocked():
        entered.set()
        assert release.wait(3)
        return 0, "Status: active"

    thread = threading.Thread(target=lambda: ps.read(app, "background", blocked))
    thread.start()
    try:
        assert entered.wait(3)
        assert (
            ps.read(app, "ufw-status", lambda: pytest.fail("overlap")) == ps.UNAVAILABLE
        )
        app.run_cmd = lambda *a, **kw: (0, "Status: inactive")
        assert fc.read_ufw_status(app) == (0, "Status: inactive")
    finally:
        release.set()
        thread.join(3)


def test_snapshot_mutation_and_explicit_state_ignore_passive_pause(monkeypatch, clock):
    app = SimpleNamespace()
    ps.note_result(app, 1, "sudo: a password is required")
    calls = []
    monkeypatch.setattr(ufw_snapshot, "trusted_helper_available", lambda: True)

    def run(args, **kw):
        operation = args[-1]
        calls.append(operation)
        response = {"protocol": ufw_snapshot.PROTOCOL}
        if operation == "capabilities":
            response["prepared_commands"] = True
        else:
            response["state"] = "off"
        return 0, json.dumps(response)

    monkeypatch.setattr(command, "run_cmd_with_input", run)
    snapshots = ufw_snapshot.UfwSnapshotClient()
    assert snapshots.state() == "off"
    with ps.observation(app):
        assert snapshots.state() == "unknown"
        snapshots.restore()
    assert calls == ["state", "capabilities", "restore"]


def test_ipv6_cache_contains_only_metadata_and_explicit_read_stays_live(
    monkeypatch, tmp_path, clock
):
    app = profile_app(tmp_path)
    path = tmp_path / "Irland.conf"
    path.write_text("synthetic fixture identity")
    calls = []
    config = "PrivateKey = SYNTHETIC-SECRET\nAddress = fd00::2/128\n"

    def run(args, **kwargs):
        calls.append(args)
        return 0, config

    monkeypatch.setattr(vc, "run_cmd", run)
    assert vc.profile_ipv6_display_state(app, "Irland") is True
    for _ in range(5):
        assert vc.profile_ipv6_display_state(app, "Irland") is True
    assert len(calls) == 1
    assert "SYNTHETIC-SECRET" not in repr(app.__dict__)
    assert app.profile_supports_ipv6("Irland") is True
    assert len(calls) == 2
    path.write_text("changed fixture identity with different length")
    assert vc.profile_ipv6_display_state(app, "Irland") is True
    assert len(calls) == 3
    clock[0] += 31
    assert vc.profile_ipv6_display_state(app, "Irland") is True
    assert len(calls) == 4
    assert vc.profile_ipv6_display_state(app, "Other") is True
    assert len(calls) == 5


@pytest.mark.parametrize("method", ["ensure_sudo_session", "setup_sudo_auth"])
@pytest.mark.parametrize("already_valid", [True, False])
def test_conscious_auth_resets_pause_and_metadata_cache(
    method, already_valid, monkeypatch, clock
):
    app = netmon.App.__new__(netmon.App)
    app.log = lambda *a: None
    app.tr = lambda key, default: default
    ps.note_result(app, 1, "sudo: a password is required")
    app._profile_ipv6_display_sample = ("old", 100, False)
    monkeypatch.setattr(netmon, "has_cmd", lambda *a: True)
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: already_valid)
    monkeypatch.setattr(netmon, "renew_sudo_timestamp", lambda *a: True)
    getattr(app, method)()
    assert not ps.paused(app)
    assert "_profile_ipv6_display_sample" not in app.__dict__


def test_automatic_dns_probe_skips_known_missing_auth(monkeypatch, clock):
    app = netmon.App.__new__(netmon.App)
    ps.note_result(app, 1, "sudo: a password is required")
    monkeypatch.setattr(netmon, "has_cmd", lambda *a: True)
    monkeypatch.setattr(
        netmon, "check_sudo_nopasswd", lambda: pytest.fail("auth probe")
    )
    assert app._auto_dns_control_available() is False


def test_killswitch_timer_marks_its_worker_as_passive(monkeypatch, clock):
    app = netmon.App.__new__(netmon.App)
    observers = []

    real_thread = threading.Thread
    workers = []

    def make_thread(**kwargs):
        worker = real_thread(**kwargs)
        workers.append(worker)
        return worker

    def state(current):
        observers.append(ps.current_app())
        return "unknown"

    monkeypatch.setattr(fc.threading, "Thread", make_thread)
    monkeypatch.setattr(fc, "killswitch_state", state)
    assert fc.cached_killswitch_state(app) == "unknown"
    workers[0].join(3)
    assert not workers[0].is_alive()
    assert observers == [app]
    assert ps.current_app() is None
    assert not app._killswitch_status_worker


def test_failed_conscious_auth_preserves_the_pause(monkeypatch, clock):
    app = netmon.App.__new__(netmon.App)
    app.log = lambda *a: None
    ps.note_result(app, 1, "sudo: a password is required")
    monkeypatch.setattr(netmon, "has_cmd", lambda *a: True)
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: False)
    monkeypatch.setattr(netmon, "renew_sudo_timestamp", lambda *a: False)
    assert app.ensure_sudo_session() is False
    assert ps.paused(app)


def test_unknown_profile_read_is_shown_as_unknown_in_ipv6_controls(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.active_wg_profile = lambda: "Irland"
    app.ipv6_is_disabled = lambda: False
    app.get_wg_iface = lambda: "wg0"
    app.ipv6_runtime_available_on_iface = lambda iface: False
    app.profile_supports_ipv6 = lambda profile: None
    app._wg_profile_path = lambda name: "/synthetic/profile"
    app.cb_privacy_ipv6 = SimpleNamespace(configure=lambda **kw: state.update(kw))
    state, hint = {}, {}
    app.privacy_ipv6_hint = SimpleNamespace(configure=lambda **kw: hint.update(kw))
    app.update_ipv6_controls_state()
    assert state["state"] == "disabled"
    assert "unbekannt" in hint["text"]
    assert "keine IPv6-Unterstützung" not in hint["text"]
