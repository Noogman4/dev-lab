"""Regression evidence for F1–F8; all system operations use a strict model."""

import inspect
import json
from pathlib import Path
import threading

import pytest

from netmon.services.dns_control_service import DNSControlService
from tools import netmon

UUID = "12345678-1234-5678-9012-123456789abc"
TARGET = ("eth0", "Wired")
PROPS = ("ipv4.ignore-auto-dns", "ipv6.ignore-auto-dns", "ipv4.dns", "ipv6.dns")


def resolved(
    *,
    ethernet="",
    domain="",
    vpn_domain="~.",
    vpn_dns="10.64.0.1",
    global_dns="",
    global_domain="",
    vpn=True,
    default="yes",
):
    text = f"Global\n    DNS Servers: {global_dns}\n    DNS Domain: {global_domain}\n"
    text += (
        f"Link 2 (eth0)\n    Current Scopes: DNS\n    DefaultRoute setting: {default}\n"
        f"    DNS Servers: {ethernet}\n    DNS Domain: {domain}\n"
    )
    if vpn:
        text += (
            f"Link 3 (wg0)\n    Current Scopes: DNS\n    Protocols: +DefaultRoute\n"
            f"    DNS Servers: {vpn_dns}\n    DNS Domain: {vpn_domain}\n"
        )
    return text


class Variable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Model:
    def __init__(self, tmp_path):
        self.path = tmp_path / "netmon-dot.conf"
        self.text = resolved()
        self.inventory = {"wg0"}
        self.status_code = 0
        self.props = dict(zip(PROPS, ("yes", "yes", "", "")))
        self.reads = 0
        self.fail_read = None
        self.on_modify = None
        self.on_up = None
        self.on_remove = None
        self.clock = 1000
        self.commands = []
        self.service = DNSControlService(
            self.run,
            lambda cmd: cmd in {"nmcli", "wg", "resolvectl"},
            dot_dropin_path=str(self.path),
            dot_dropin_dir=str(tmp_path),
        )
        self.service.get_wireguard_interfaces = lambda: self.inventory

    def dirty(self):
        self.text = resolved(ethernet="192.168.0.1", domain="~.")
        self.props.update(dict(zip(PROPS, ("no", "no", "8.8.8.8", ""))))

    @property
    def writes(self):
        return [(now, cmd) for now, cmd in self.commands if cmd[0] == "sudo"]

    def run(self, cmd, **_kwargs):
        cmd = list(cmd)
        self.commands.append((self.clock - 1000, cmd))
        if cmd == ["resolvectl", "status"]:
            return self.status_code, self.text
        if cmd == ["wg", "show", "interfaces"]:
            return (
                (1, "unavailable")
                if self.inventory is None
                else (0, " ".join(self.inventory))
            )
        if cmd[:2] == ["nmcli", "-g"]:
            if cmd[2] == "GENERAL.CON-UUID":
                return 0, UUID + "\n"
            assert cmd[3:6] == ["con", "show", "id"], cmd
            self.reads += 1
            if self.reads == self.fail_read:
                return 1, "simulated readback failure"
            return (
                0,
                "\n".join([UUID, "eth0", "802-3-ethernet", *self.props.values()])
                + "\n",
            )
        if cmd[:5] == ["sudo", "-n", "nmcli", "con", "mod"]:
            offset = 7 if cmd[5] == "uuid" else 6
            self.props.update(zip(cmd[offset::2], cmd[offset + 1 :: 2]))
            if self.on_modify:
                self.on_modify()
            return 0, ""
        if cmd[:5] == ["sudo", "-n", "nmcli", "con", "up"]:
            if self.on_up:
                self.on_up()
            else:
                self.text = resolved()
            return 0, ""
        if cmd == ["sudo", "-n", "rm", "-f", str(self.path)]:
            self.path.unlink(missing_ok=True)
            if self.on_remove:
                self.on_remove()
            return 0, ""
        if cmd == ["sudo", "-n", "systemctl", "restart", "systemd-resolved"]:
            return 0, ""
        raise AssertionError(f"Unmodelled operation: {cmd}")


def app_for(model):
    app = netmon.App.__new__(netmon.App)
    app._dns_control_service = lambda: model.service
    app.dns_guard_enabled_var = Variable(True)
    app.dns_guard_status_var = Variable()
    app.dns_guard_last_action_var = Variable()
    app.dns_guard_transition_until = 0
    app.last_dns_guard_repair_ts = 0
    app.dns_guard_check_running = False
    app.logs = []
    app.errors = []
    app.log_safe = app.logs.append
    app.log_debug_safe = app.errors.append
    app.log_network_debug = app.logs.append
    app.update_dns_guard_indicator = lambda: None
    app.update_dns_output = lambda text, append=False: app.logs.append(text)
    app._auto_dns_control_available = lambda: True
    app._active_nm_dns_targets = lambda: [TARGET]
    app.get_selected_user_dns = lambda: ["9.9.9.9"]
    app.get_selected_dot_dns = lambda: ["9.9.9.9"]
    app._isp_dns_restore_choice_after_vpn = lambda: "System (DHCP/auto)"
    app._dns_runtime_transition_active = lambda: True
    app._set_dns_choice_safe = lambda _choice: None
    app.refresh_dns_policy_status = lambda: None
    return app


@pytest.fixture
def model(tmp_path):
    assert Path(netmon.__file__).resolve() == Path.cwd() / "netmon/app.py"
    return Model(tmp_path)


def public_query_targets(links):
    """Independent routing oracle for a query matching no specific domain."""
    roots = {
        name for name, domains, _default in links if "~." in domains or "." in domains
    }
    return roots or {name for name, _domains, default in links if default}


@pytest.mark.parametrize("domain", ["~lan.example", "lan.example"])
@pytest.mark.parametrize("address", ["192.168.0.1", "2001:db8::53"])
def test_f1_specific_domain_does_not_hide_parallel_default(model, domain, address):
    model.text = resolved(ethernet=address, domain=domain, vpn_domain="")
    assert public_query_targets([("eth0", [domain], True), ("wg0", [], True)]) == {
        "eth0",
        "wg0",
    }
    report = model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())
    assert report["conflict"] and report["leak"] and not report["only_vpn_dns"]
    app = app_for(model)
    app.run_dns_guard_check_once()
    assert app.dns_guard_state == "problem" and not model.writes


def test_f1_global_search_domain_does_not_hide_general_dns(model):
    model.text = resolved(
        global_dns="1.1.1.1", global_domain="lan.example", vpn_domain=""
    )
    assert model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())[
        "conflict"
    ]


@pytest.mark.parametrize("default", ["yes", "no"])
@pytest.mark.parametrize("vpn_domain", ["~.", ".", "~corp.example"])
def test_f1_legitimate_split_dns_preserved(model, default, vpn_domain):
    model.text = resolved(
        ethernet="192.168.0.1",
        domain="~lan.example",
        vpn_domain=vpn_domain,
        default=default,
    )
    if vpn_domain == "~corp.example":
        model.text = model.text.replace(
            "Protocols: +DefaultRoute", "Protocols: -DefaultRoute"
        )
    report = model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())
    exposed = vpn_domain == "~corp.example" and default == "yes"
    assert report["conflict"] is exposed
    assert not report["policy_unknown"]
    assert model.service.apply_vpn_dns_policy(targets=[TARGET])[0] is not exposed
    assert not model.writes


def test_f1_split_default_conflict_is_explicitly_unresolved_without_mutation(model):
    model.text = resolved(
        ethernet="192.168.0.1",
        domain="~lan.example",
        vpn_domain="~corp.example",
        default="yes",
    )
    policy = model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())
    assert policy["conflict"] and "eth0" in policy["repair_ifaces"]
    assert "eth0" in policy["split_ifaces"]

    app = app_for(model)
    calls = []
    app._apply_nm_dns_policy_to_targets = lambda **_kwargs: calls.append("nm") or (
        True,
        [],
    )
    ok, report = model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)

    assert not ok
    assert "Parallele Default-DNS-Route" in report
    assert "Split-DNS bleibt erhalten" in report
    ok_again, repeated = model.service.apply_vpn_dns_policy(
        targets=[TARGET], automatic=True
    )
    assert not ok_again and "Wiederholung unterdrückt" in repeated
    assert not calls and not model.writes


@pytest.mark.parametrize(
    "text",
    [
        "Global\n    DNS Servers: 1.1.1.1\n",
        resolved(vpn=False),
        "Global\nLink 3 officevpn\n    DNS Servers: 10.64.0.1\n",
    ],
)
def test_f2_inventory_contradiction_blocks_restore(model, text):
    model.inventory = {"officevpn"}
    model.text = text
    app = app_for(model)
    calls = []
    app._apply_automatic_dns_restore_choice = (
        lambda choice: calls.append(choice) or True
    )
    assert model.service.read_dns_snapshot()["vpn_state"] == "unknown"
    assert app.is_vpn_active() is None
    assert not app._restore_isp_dns_after_vpn_switch()
    assert not calls and not model.writes


def test_f2_resolved_wireguard_missing_from_confirmed_inventory_is_unknown(model):
    model.inventory = set()
    app = app_for(model)
    called = []
    app._apply_automatic_dns_restore_choice = (
        lambda choice: called.append(choice) or True
    )

    assert model.service.read_dns_snapshot()["vpn_state"] == "unknown"
    assert app.is_vpn_active() is None
    assert not app._restore_isp_dns_after_vpn_switch()
    assert not called and not model.writes


@pytest.mark.parametrize(
    "address", ["not-an-address", "999.999.999.999", "2001:db8:::53"]
)
@pytest.mark.parametrize("vpn", [True, False])
def test_f3_invalid_ip_cannot_be_healthy(model, address, vpn):
    model.inventory = {"wg0"} if vpn else set()
    model.text = resolved(vpn_dns=address, ethernet="" if vpn else address, vpn=vpn)
    report = model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())
    assert report["policy_unknown"]
    app = app_for(model)
    app.get_selected_user_dns = lambda: [address]
    app.run_dns_guard_check_once(auto_repair=True)
    assert app.dns_guard_state == "unknown" and not model.writes


@pytest.mark.parametrize(
    "flags",
    [
        "+DefaultRoute -DefaultRoute",
        "-DefaultRoute +DefaultRoute",
        "+DefaultRoute\n    DefaultRoute setting: no",
    ],
)
def test_f3_contradictory_routes_are_unknown(model, flags):
    model.text = resolved().replace("Protocols: +DefaultRoute", "Protocols: " + flags)
    assert model.service.evaluate_dns_snapshot(model.service.read_dns_snapshot())[
        "policy_unknown"
    ]


def test_f4_explicit_retry_completes_own_modify_after_readback_failure(model):
    model.dirty()
    model.fail_read = 3
    assert not model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert len(model.writes) == 1
    assert model.service.apply_vpn_dns_policy(targets=[TARGET])[0]
    assert [cmd[4] for _now, cmd in model.writes] == ["mod", "up"]
    assert not model.service._nm_activation_pending


def test_f5_profile_change_reopens_retry_without_loop(model, monkeypatch):
    model.inventory = set()
    model.text = resolved(vpn=False, global_dns="1.1.1.1")
    app = app_for(model)
    calls = []
    app.enforce_dns_clean = lambda: (calls.append(model.clock) or False, "not healed")
    monkeypatch.setattr(netmon.time, "time", lambda: model.clock)
    for now in [1000, 1035, 1070]:
        model.clock = now
        if now == 1035:
            model.props["ipv4.dns"] = "8.8.8.8"
        app.run_dns_guard_check_once(auto_repair=True)
    assert calls == [1000, 1035]
    assert app.dns_guard_state == "problem" and not app.errors


class ObservedLock:
    def __init__(self, waiting):
        self.lock = threading.RLock()
        self.waiting = waiting

    def acquire(self, *args, **kwargs):
        if threading.current_thread().name == "restore":
            self.waiting.set()
        return self.lock.acquire(*args, **kwargs)

    def release(self):
        self.lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_args):
        self.release()


def test_f6_stale_restore_cannot_overlap_vpn_repair(model):
    model.dirty()
    choice_entered, release_choice = threading.Event(), threading.Event()
    modified, release_repair = threading.Event(), threading.Event()
    waiting = threading.Event()
    model.service.dns_mutation_lock = ObservedLock(waiting)
    app = app_for(model)
    app.is_vpn_active = lambda: (
        False if not modified.is_set() else netmon.App.is_vpn_active(app)
    )

    def choose():
        choice_entered.set()
        assert release_choice.wait(10)
        return "System (DHCP/auto)"

    app._isp_dns_restore_choice_after_vpn = choose
    calls, outcomes, errors = [], {}, []

    def restore_write(_choice):
        calls.append("restore while vpn repair")
        waiting.set()  # The V1 path does not acquire the shared lock.
        return {"success": True}

    app._apply_dns_profile_choice_via_control = restore_write

    def pause_modify():
        modified.set()
        assert release_repair.wait(10)

    model.on_modify = pause_modify

    def worker(name, callback):
        try:
            outcomes[name] = callback()
        except BaseException as exc:
            errors.append(exc)

    restore = threading.Thread(
        name="restore",
        target=worker,
        args=("restore", app._restore_isp_dns_after_vpn_switch),
    )
    repair = threading.Thread(
        name="repair",
        target=worker,
        args=("repair", lambda: model.service.apply_vpn_dns_policy(targets=[TARGET])),
    )
    try:
        restore.start()
        assert choice_entered.wait(10)
        repair.start()
        assert modified.wait(10)
        release_choice.set()
        assert waiting.wait(10)
    finally:
        release_choice.set()
        release_repair.set()
        restore.join(10)
        if repair.ident is not None:
            repair.join(10)
    assert not restore.is_alive() and not repair.is_alive() and not errors
    assert not calls and outcomes["restore"] is False
    assert outcomes["repair"][0]


@pytest.mark.parametrize("new_state", ["active", "unknown"])
def test_f6_restore_rechecks_after_waiting(model, new_state):
    model.inventory = set()
    model.text = resolved(vpn=False)
    waiting = threading.Event()
    lock = ObservedLock(waiting)
    model.service.dns_mutation_lock = lock
    app = app_for(model)
    calls = []
    app._apply_dns_profile_choice_via_control = (
        lambda _choice: calls.append("write") or waiting.set() or {"success": True}
    )
    results = []
    thread = threading.Thread(
        name="restore",
        target=lambda: results.append(
            app._apply_automatic_dns_restore_choice("System (DHCP/auto)")
        ),
    )
    with lock:
        thread.start()
        try:
            assert waiting.wait(10)
            model.inventory = {"wg0"} if new_state == "active" else None
            model.text = resolved(vpn=new_state == "active")
        finally:
            pass
    thread.join(10)
    assert not thread.is_alive()
    assert not calls and results == [False]


@pytest.mark.parametrize("vpn_after_wait", [True, None])
def test_f6_manual_dns_waits_for_shared_lock_then_rechecks_vpn(model, vpn_after_wait):
    waiting = threading.Event()
    owner_entered, release_owner = threading.Event(), threading.Event()

    class ManualObservedLock:
        def __init__(self):
            self.lock = threading.RLock()

        def acquire(self, *args, **kwargs):
            if threading.current_thread().name == "manual-dns":
                waiting.set()
            return self.lock.acquire(*args, **kwargs)

        def release(self):
            self.lock.release()

        def __enter__(self):
            self.acquire()
            return self

        def __exit__(self, *_args):
            self.release()

    lock = ManualObservedLock()
    model.service.dns_mutation_lock = lock
    state = {"vpn": False}
    app = app_for(model)
    app._dns_control_service = lambda: model.service
    app.is_vpn_active = lambda: state["vpn"] if state["vpn"] is not None else None
    app._dns_runtime_transition_active = lambda: False
    app._dns_controls_locked = lambda: (False, "")
    app._set_dns_choice_safe = lambda _choice: None
    app.nb = type("Notebook", (), {"select": lambda _self, _tab: None})()
    app.tab_dns = object()
    app.tr = lambda _key, fallback: fallback
    app.log_safe = lambda *_args: None
    app.update_dns_output = lambda *_args, **_kwargs: None
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None
    mutations = []
    app._apply_nm_dns_policy_to_targets = lambda **_kwargs: mutations.append("nm") or (
        True,
        [],
    )
    app._remove_manual_dns_dropin = lambda: mutations.append("dropin") or (True, "")
    app._restart_resolved_for_dns_policy = lambda: mutations.append("restart") or (
        True,
        "",
    )
    result = []

    def hold_shared_mutation_lock():
        with lock:
            owner_entered.set()
            assert release_owner.wait(5)

    owner = threading.Thread(target=hold_shared_mutation_lock, name="vpn-repair")
    manual = threading.Thread(
        target=lambda: result.append(
            netmon.dns_controller.apply_dns(
                app,
                choice="System (DHCP/auto)",
                confirm_dnssec=False,
                refresh_ui=False,
            )
        ),
        name="manual-dns",
    )
    owner.start()
    assert owner_entered.wait(2)
    manual.start()
    try:
        assert waiting.wait(2)
        state["vpn"] = vpn_after_wait
    finally:
        release_owner.set()
        owner.join(5)
        manual.join(5)
    assert not owner.is_alive() and not manual.is_alive()
    assert result == [False]
    assert mutations == [] and not model.writes


@pytest.mark.parametrize(
    "change",
    [
        "disconnect",
        "unknown",
        "vpn_dns",
        "foreign_dropin",
        "global_dns",
        "physical_route",
    ],
)
def test_f7_activation_invalidates_followup_plan(model, change):
    model.dirty()
    model.path.write_text("[Resolve]\nDNS=1.1.1.1\nDNSOverTLS=yes\n")

    def changed():
        if change == "foreign_dropin":
            model.path.write_text("[Resolve]\nDNS=9.9.9.9\n")
        elif change == "vpn_dns":
            model.text = resolved(vpn_dns="10.65.0.1")
        elif change == "global_dns":
            model.text = resolved(global_dns="8.8.8.8")
        elif change == "physical_route":
            model.text = resolved(
                ethernet="192.168.0.1", domain="~corp.example", default="yes"
            )
        else:
            model.text = resolved(vpn=False)
            model.inventory = set() if change == "disconnect" else None

    model.on_up = changed
    assert not model.service.apply_vpn_dns_policy(targets=[TARGET], automatic=True)[0]
    assert [cmd[4] for _now, cmd in model.writes] == ["mod", "up"]
    assert model.path.exists()


def test_f7_disconnect_after_removal_defers_restart(model):
    model.dirty()
    model.path.write_text("[Resolve]\nDNS=1.1.1.1\nDNSOverTLS=yes\n")

    def disconnect():
        model.inventory = set()
        model.text = resolved(vpn=False)

    model.on_remove = disconnect
    assert not model.service.apply_vpn_dns_policy(targets=[TARGET])[0]
    assert not any("restart" in cmd for _now, cmd in model.writes)
    assert model.service._resolved_reload_pending


@pytest.mark.parametrize("state,nm_result", [(None, []), (False, None), (None, None)])
def test_f8_unknown_does_not_disable_killswitch(model, monkeypatch, state, nm_result):
    app = app_for(model)
    app.privacy_config = {}
    app._network_operation_active_elsewhere = lambda: False
    app.killswitch_is_on = lambda: True
    app.get_wg_interfaces = lambda: []
    app.is_vpn_active = lambda: state
    calls = []
    app.killswitch_off = lambda **kwargs: calls.append(kwargs) or True
    monkeypatch.setattr(
        netmon.vpn_controller,
        "get_active_nm_wireguard_connections",
        lambda _app, **_kwargs: nm_result,
    )
    monkeypatch.setattr(
        netmon.vpn_controller,
        "get_active_nm_vpn_connections",
        lambda _app, **_kwargs: nm_result,
    )
    monkeypatch.setattr(netmon, "check_sudo_nopasswd", lambda: True)
    assert not app.repair_orphaned_killswitch_on_startup()
    assert not calls


@pytest.mark.parametrize(
    "provider", ["get_active_nm_wireguard_connections", "get_active_nm_vpn_connections"]
)
@pytest.mark.parametrize("rc,out", [(1, "unavailable"), (0, "malformed")])
def test_f8_strict_nm_provider_preserves_unknown(model, monkeypatch, provider, rc, out):
    monkeypatch.setattr(netmon.vpn_controller, "has_cmd", lambda _cmd: True)
    monkeypatch.setattr(
        netmon.vpn_controller, "run_cmd", lambda *_args, **_kwargs: (rc, out)
    )
    callback = getattr(netmon.vpn_controller, provider)
    assert callback(app_for(model), strict=True) is None
    assert callback(app_for(model)) == []


@pytest.mark.parametrize("scheduler", [False, True])
@pytest.mark.parametrize("violation", [False, True])
def test_clock_0_35_70(model, monkeypatch, scheduler, violation):
    """Same controlled clock/model on baseline, V1 and V2, without real sleep."""
    modern = (
        "automatic" in inspect.signature(model.service.apply_vpn_dns_policy).parameters
    )
    model.text = resolved(global_dns="1.1.1.1")
    if violation:
        model.dirty()
    app = app_for(model)
    app._dns_runtime_transition_active = lambda: False
    monkeypatch.setattr(netmon, "run_cmd", model.run)
    monkeypatch.setattr(netmon.time, "time", lambda: model.clock)

    def activation():
        model.clock += 5

    model.on_up = activation
    queued = []
    app.after = lambda ms, cb: queued.append((model.clock + ms / 1000, cb))
    if scheduler:
        app.dns_guard_loop()
        while queued:
            due, callback = queued.pop(0)
            if due > 1070:
                break
            model.clock = due
            callback()
    else:
        for now in [1000, 1035, 1070]:
            model.clock = now
            app.run_dns_guard_check_once(auto_repair=True)
    print(
        "CLOCK",
        json.dumps(
            {
                "modern": modern,
                "scheduler": scheduler,
                "violation": violation,
                "writes": model.writes,
                "state": app.dns_guard_state,
            }
        ),
    )
    assert not app.errors
    if modern:
        assert len(model.writes) == (2 if violation else 0)
        assert app.dns_guard_state == ("problem" if violation else "ok")
    else:
        assert len(model.writes) == 21
        assert [now for now, cmd in model.writes if "up" in cmd] == [0, 35, 70]
