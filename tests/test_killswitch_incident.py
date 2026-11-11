"""2026-10-31 incident: real controllers, historical functions, simulated UFW.

No installed NetMon, host firewall, network service, or real profile is used.
"""

import ast
from copy import deepcopy
from pathlib import Path
import subprocess
import threading
from types import MethodType, SimpleNamespace

import pytest

from netmon.features import firewall_controller as firewall
from netmon.features import vpn_controller as vpn
from test_killswitch_failure_recovery import Ufw
from test_killswitch_failure_recovery import (
    simulated_snapshot_transport as simulated_snapshot_transport,
    synthetic_kernel_links as synthetic_kernel_links,
)
from tools import netmon


class IncidentFirewall(Ufw):
    """Extend the existing ordered IPv4/IPv6 model to cover ordinary OFF."""

    def run(self, args, timeout=0, text=True):
        assert args[:3] == ["sudo", "-n", "ufw"]
        command = args[3:]
        if command == ["status", "numbered"] and not self.app.ufw_lock.locked():
            # OFF's final diagnostic is intentionally outside the mutation lock.
            with self.app.ufw_lock:
                return super().run(args, timeout=timeout, text=text)
        if command[:2] != ["delete", "allow"]:
            return super().run(args, timeout=timeout, text=text)
        assert self.app.ufw_lock.locked()
        self.calls.append(command)
        self.count += 1
        direction = command[2].upper()
        if command[3:4] == ["on"]:
            target, source = "Anywhere", f"Anywhere on {command[4]}"
        elif command[3:4] == ["to"]:
            target, source = f"{command[4]} {command[6]}/udp", "Anywhere"
        else:
            target, source = command[3], "Anywhere"
        candidate = ("ALLOW", direction, target, source)
        for rules in self.rules.values():
            if candidate in rules:
                rules.remove(candidate)
        return 0, "simulated"


def app_context(model):
    """New application memory over the same persistent simulated firewall."""
    app = SimpleNamespace(
        ufw_lock=threading.Lock(),
        get_wg_interfaces=lambda: ["wg0"],
        get_killswitch_vpn_profiles=list,
        list_wg_profiles=list,
        get_killswitch_vpn_endpoints=lambda: [("203.0.113.1", "51820")],
        log_safe=model.logs.append,
        log_debug=lambda *args: None,
        log_debug_safe=lambda *args: None,
        log_network_debug=lambda *args: None,
        refresh_safe=lambda: None,
        tr=lambda key, fallback: fallback,
        run_cmd=model.run,
        _network_service=lambda: None,
        _read_ufw_status=model.status,
        resolve_profile_family_runtime=lambda *args, **kw: {},
        resolve_runtime_vpn_profile=lambda *args, **kw: "",
        _ufw_status_is_active=firewall.ufw_status_is_active,
        _ufw_default_policy_matches=firewall.ufw_default_policy_matches,
        _ufw_has_interface_rule=firewall.ufw_has_interface_rule,
        _ufw_has_endpoint_rule=firewall.ufw_has_endpoint_rule,
    )
    app._verify_killswitch_rules = lambda *a, **kw: firewall.verify_killswitch_rules(
        app, *a, **kw
    )
    for name in (
        "_try_begin_network_operation",
        "_end_network_operation",
        "_recover_firewall_preserving_killswitch",
        "_recover_firewall_after_killswitch_failure",
        "_killswitch_on_sync",
        "killswitch_is_on",
    ):
        setattr(app, name, MethodType(getattr(netmon.App, name), app))
    model.app = app
    return app


def configured_model(state):
    model = IncidentFirewall()
    model.defaults["outgoing"] = "allow"
    if state == "on":
        model.defaults["outgoing"] = "deny"
        for rules in model.rules.values():
            rules.remove(("ALLOW", "OUT", "443/tcp", "Anywhere"))
            for iface in ("lo", "wg0"):
                for direction in ("IN", "OUT"):
                    rules.append(
                        ("ALLOW", direction, "Anywhere", f"Anywhere on {iface}")
                    )
            rules.append(("ALLOW", "OUT", "203.0.113.1 51820/udp", "Anywhere"))
    elif state == "unreadable":
        model.bad_status = True
    elif state == "emergency":
        model.defaults["outgoing"] = "deny"
        for rules in model.rules.values():
            rules[:0] = [
                ("DENY", "IN", "Anywhere", "Anywhere"),
                ("DENY", "OUT", "Anywhere", "Anywhere"),
            ]
    return model


def historical_functions(revision, filename, names, namespace):
    source = subprocess.check_output(
        ["git", "show", f"{revision}:{filename}"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )
    selected = [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    assert {node.name for node in selected} == set(names)
    namespace = namespace.copy()
    exec(
        compile(
            ast.Module(body=selected, type_ignores=[]), f"{revision}:{filename}", "exec"
        ),
        namespace,
    )
    return namespace


@pytest.mark.parametrize("refresh_ui", [False, True])
@pytest.mark.parametrize("state", ["off", "on", "unreadable", "emergency"])
@pytest.mark.parametrize("target", ["", "proton-de"])
def test_invalid_vpn_target_preserves_both_firewall_families(state, target, refresh_ui):
    model = configured_model(state)
    app = app_context(model)
    before = deepcopy((model.active, model.defaults, model.rules))

    assert (
        vpn.vpn_switch(app, target, ensure_sudo=False, refresh_ui=refresh_ui) is False
    )

    assert model.calls == []
    assert (model.active, model.defaults, model.rules) == before
    assert not getattr(app, "killswitch_recovery_required", False)
    assert app._network_op_owner is None and app._network_op_depth == 0
    assert not app.ufw_lock.locked()
    assert not any("Killswitch AUS" in line for line in model.logs)


def test_historical_version_switch_explains_success_with_persistent_drops():
    historical_vpn = historical_functions(
        "edf4f32f", "netmon/features/vpn_controller.py", ["vpn_switch"], vars(vpn)
    )
    historical_off = historical_functions(
        "edf4f32f^",
        "netmon/features/firewall_controller.py",
        ["killswitch_off_sync", "verify_killswitch_rules"],
        vars(firewall),
    )
    model = configured_model("off")
    app = app_context(model)
    historical_app = historical_functions(
        "edf4f32f",
        "netmon/app.py",
        ["_recover_firewall_preserving_killswitch"],
        vars(netmon),
    )
    app._recover_firewall_preserving_killswitch = MethodType(
        historical_app["_recover_firewall_preserving_killswitch"], app
    )
    assert (
        historical_vpn["vpn_switch"](
            app, "proton-de", ensure_sudo=False, refresh_ui=False
        )
        is False
    )
    assert app.killswitch_recovery_required is True
    for rules in model.rules.values():
        for direction in ("IN", "OUT"):
            assert ("DENY", direction, "Anywhere", "Anywhere") in rules

    # Restart loses the in-memory recovery flag; old code sees persistent rules.
    app = app_context(model)
    assert not hasattr(app, "killswitch_recovery_required")
    app._verify_killswitch_rules = lambda *a, **kw: historical_off[
        "verify_killswitch_rules"
    ](app, *a, **kw)
    assert historical_off["killswitch_off_sync"](app, refresh_ui=False) is True
    for rules in model.rules.values():
        for direction in ("IN", "OUT"):
            assert ("DENY", direction, "Anywhere", "Anywhere") in rules
    assert any("Killswitch AUS" in line for line in model.logs)


def test_current_off_rejects_emergency_drops_even_after_restart():
    model = configured_model("emergency")
    app = app_context(model)
    assert not hasattr(app, "killswitch_recovery_required")
    assert firewall.killswitch_off_sync(app, refresh_ui=False) is False
    for rules in model.rules.values():
        for direction in ("IN", "OUT"):
            assert ("DENY", direction, "Anywhere", "Anywhere") in rules
    assert not any("Killswitch AUS" in line for line in model.logs)


def test_failed_cleanup_without_killswitch_preserves_firewall(monkeypatch):
    model = configured_model("off")
    app = app_context(model)
    app.resolve_profile_family_runtime = lambda *a, **kw: {"runtime_profile": "work"}
    app._wg_profile_path = lambda name: f"/synthetic/{name}.conf"
    app._check_wireguard_profile_for_multiple_endpoints = lambda *a: None
    app._network_service = lambda: SimpleNamespace(file_exists=lambda path: (0, ""))
    events = []
    app.prepare_dns_for_vpn_profile_switch = lambda: events.append("prepare DNS")

    def failed_cleanup(app):
        events.append("partially completed cleanup")
        return False

    monkeypatch.setattr(vpn, "cleanup_wireguard_interfaces", failed_cleanup)
    # Dispatch recovery through the model, not the file-existence-only service.
    monkeypatch.setattr(firewall, "_network_service_for", lambda app: None)
    assert vpn.vpn_switch(app, "work", ensure_sudo=False, refresh_ui=False) is False
    assert events == ["prepare DNS", "partially completed cleanup"]
    assert model.defaults["outgoing"] == "allow"
    assert not model.calls
