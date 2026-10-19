import inspect
import json
import os
import subprocess
import threading

import pytest

from netmon.config.constants import VPN_SLOT_COUNT
from netmon.features import vpn_controller
from tools import netmon


@pytest.fixture
def strict_subprocess_guard(monkeypatch):
    attempted = []

    def forbidden(*args, **kwargs):
        attempted.append((args, kwargs))
        pytest.fail(f"Unexpected system command in isolated VPN-slot test: {args!r}")

    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, forbidden)
    for name in ("system", "popen", "posix_spawn", "posix_spawnp"):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, forbidden)
    yield
    assert not attempted, "A system-command attempt was swallowed by application code"


@pytest.fixture(autouse=True)
def private_profile_creation():
    # Synthetic secret-bearing profiles should have deployment-safe permissions.
    previous = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous)


class DummyWidget:
    def __init__(self):
        self.text = ""

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyMenu:
    def __init__(self, _widget=None, tearoff=0):
        self.entries = []

    def add_command(self, label, command):
        self.entries.append(
            {"kind": "command", "label": label, "command": command, "state": "normal"}
        )

    def add_separator(self):
        self.entries.append({"kind": "separator"})

    def index(self, value):
        if value == "end":
            return len(self.entries) - 1
        raise ValueError(value)

    def entryconfigure(self, index, state=None):
        if state is not None:
            self.entries[index]["state"] = state


def test_run_async_catches_background_exceptions(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.log = logs.append
    app.log_debug_safe = logs.append

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target is not None:
                self.target()

    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    app.run_async(
        lambda: (_ for _ in ()).throw(RuntimeError("boom")), job_name="vpn test"
    )

    assert any("Async-Job Fehler [vpn test]: boom" in entry for entry in logs)


def test_async_job_label_uses_function_name_when_available():
    app = netmon.App.__new__(netmon.App)

    def sample_job():
        return None

    assert app._async_job_label(sample_job) == "sample_job"
    assert app._async_job_label(lambda: None) == "unbenannter Async-Job"


def test_load_vpn_slots_config_reads_saved_slots(tmp_path):
    app = netmon.App.__new__(netmon.App)
    app.vpn_config_path = str(tmp_path / "netmon_vpn_slots.json")
    app.log = lambda message: None
    Path = __import__("pathlib").Path
    Path(app.vpn_config_path).write_text(
        json.dumps(
            [
                {"slot": 1, "custom_name": "Proton CH", "profile": "proton__ipv4"},
                {"slot": 2, "custom_name": "Proton DE", "profile": "proton-de"},
            ]
        )
    )

    slots = app.load_vpn_slots_config()

    assert slots[0] == {"slot": 1, "custom_name": "Proton CH", "profile": "proton"}
    assert slots[1] == {"slot": 2, "custom_name": "Proton DE", "profile": "proton-de"}
    assert slots[4] == {"slot": 5, "custom_name": "", "profile": ""}
    assert VPN_SLOT_COUNT == 10
    assert len(slots) == 10
    assert slots[9] == {"slot": 10, "custom_name": "", "profile": ""}


def test_ensure_netmon_wireguard_profiles_dir_uses_documents_dir_and_migrates(
    monkeypatch, tmp_path
):
    docs_dir = tmp_path / "Documents" / "NetMon"
    legacy_dir = tmp_path / "legacy" / "wireguard"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "demo.conf").write_text("[Interface]\nAddress = 10.0.0.2/32\n")
    monkeypatch.setattr(
        vpn_controller,
        "get_netmon_documents_dir",
        lambda: str(docs_dir),
    )
    monkeypatch.setattr(
        vpn_controller,
        "_legacy_netmon_wireguard_profiles_dir",
        lambda: str(legacy_dir),
    )

    result = vpn_controller.ensure_netmon_wireguard_profiles_dir()

    assert result == str(docs_dir / "WireGuard")
    assert (docs_dir / "WireGuard" / "demo.conf").is_file()


def test_update_vpn_slot_buttons_sets_labels_and_colors():
    app = netmon.App.__new__(netmon.App)
    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work VPN", "profile": "proton"},
        {"slot": 2, "custom_name": "", "profile": "proton-de"},
        {"slot": 3, "custom_name": "", "profile": ""},
    ]
    app.vpn_slot_buttons = [DummyWidget(), DummyWidget(), DummyWidget()]
    app.vpn_slot_lights = ["light-1", "light-2", "light-3"]
    app.active_wg_profile = lambda: "proton"
    app.wg_profiles = ["proton", "proton-de"]
    app.profile_supports_ipv6 = lambda profile: profile == "proton"

    colors = []
    app.set_light = lambda light, color: colors.append((light, color))

    app.update_vpn_slot_buttons()

    assert [widget.text for widget in app.vpn_slot_buttons] == [
        "Work VPN",
        "proton-de",
        "VPN 3 frei",
    ]
    assert colors == [("light-1", "green"), ("light-2", "red"), ("light-3", "gray")]


def test_open_vpn_slot_logs_free_slot():
    app = netmon.App.__new__(netmon.App)
    logs = []
    tab_calls = []

    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": ""}]
    app.log = logs.append
    app.nb = type("Notebook", (), {"select": lambda self, tab: tab_calls.append(tab)})()
    app.tab_vpn_slots = "vpn-tab"
    app.load_vpn_slot_into_form = lambda slot_no: tab_calls.append(slot_no)

    app.open_vpn_slot(0)

    assert logs == ["VPN-Slot 1 ist frei."]
    assert tab_calls == ["vpn-tab", 1]


def test_get_wg_import_dir_defaults_to_netmon_documents_wireguard(
    monkeypatch, tmp_path
):
    app = netmon.App.__new__(netmon.App)
    app.privacy_config = {}
    monkeypatch.setattr(
        vpn_controller,
        "ensure_netmon_wireguard_profiles_dir",
        lambda: str(tmp_path / "Documents" / "NetMon" / "WireGuard"),
    )

    assert app.get_wg_import_dir() == str(
        tmp_path / "Documents" / "NetMon" / "WireGuard"
    )


def test_prepare_documents_config_path_migrates_legacy_file(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "config"
    legacy_dir.mkdir(parents=True)
    legacy_file = legacy_dir / "netmon_privacy.json"
    legacy_file.write_text('{"mode":"safe"}', encoding="utf-8")
    target_dir = tmp_path / "Documents" / "NetMon" / "Config"
    monkeypatch.setattr(
        netmon,
        "get_netmon_documents_subdir",
        lambda *parts: str(target_dir),
    )

    target_path = netmon._prepare_documents_config_path(
        str(legacy_dir),
        "netmon_privacy.json",
    )

    assert target_path == str(target_dir / "netmon_privacy.json")
    assert (target_dir / "netmon_privacy.json").read_text(
        encoding="utf-8"
    ) == '{"mode":"safe"}'


def test_app_init_uses_documents_config_paths_for_slots_and_privacy():
    init_source = inspect.getsource(netmon.App.__init__)

    assert "_prepare_documents_config_path(" in init_source
    assert "self.linux_help_data_path = _prepare_documents_config_path(" in init_source
    assert "self.hdd_config_path = _prepare_documents_config_path(" in init_source
    assert "self.link_config_path = _prepare_documents_config_path(" in init_source
    assert "self.vpn_config_path = _prepare_documents_config_path(" in init_source
    assert (
        "self.primary_vpn_config_path = _prepare_documents_config_path(" in init_source
    )
    assert "self.privacy_config_path = _prepare_documents_config_path(" in init_source
    assert "self.netmon_config_path = _prepare_documents_config_path(" in init_source
    assert "self.ai_config_path = _prepare_documents_config_path(" in init_source


def test_prepare_documents_data_path_migrates_legacy_state_file(monkeypatch, tmp_path):
    legacy_dir = tmp_path / "state"
    legacy_dir.mkdir(parents=True)
    legacy_file = legacy_dir / "netmon_security_baseline.json"
    legacy_file.write_text('{"ts":"now"}', encoding="utf-8")
    target_dir = tmp_path / "Documents" / "NetMon" / "Security"
    monkeypatch.setattr(
        netmon,
        "get_netmon_documents_subdir",
        lambda *parts: str(target_dir),
    )

    target_path = netmon._prepare_documents_data_path(
        "Security",
        str(legacy_dir),
        "netmon_security_baseline.json",
    )

    assert target_path == str(target_dir / "netmon_security_baseline.json")
    assert (target_dir / "netmon_security_baseline.json").read_text(
        encoding="utf-8"
    ) == '{"ts":"now"}'


def test_app_init_uses_documents_security_paths():
    init_source = inspect.getsource(netmon.App.__init__)

    assert "self.clamav_findings_path = _prepare_documents_data_path(" in init_source
    assert "self.security_baseline_path = _prepare_documents_data_path(" in init_source
    assert '"Security",' in init_source


def test_app_init_uses_documents_security_guard_paths():
    init_source = inspect.getsource(netmon.App.__init__)

    assert (
        "self.startup_guard_baseline_path = _prepare_documents_data_path("
        in init_source
    )
    assert (
        "self.repository_guard_baseline_path = _prepare_documents_data_path("
        in init_source
    )
    assert (
        "self.repository_guard_trustlist_path = _prepare_documents_data_path("
        in init_source
    )
    assert (
        "self.startup_guard_trustlist_path = _prepare_documents_data_path("
        in init_source
    )
    assert (
        "self.process_guard_trustlist_path = _prepare_documents_data_path("
        in init_source
    )
    assert (
        "self.roots_baseline_guard_baseline_path = _prepare_documents_data_path("
        in init_source
    )
    assert (
        "self.roots_baseline_guard_whitelist_path = _prepare_documents_data_path("
        in init_source
    )
    assert (
        'self.packet_capture_dir = os.path.join(self.netmon_state_dir, "captures")'
        in init_source
    )


def test_open_vpn_slot_skips_restart_for_already_active_profile():
    app = netmon.App.__new__(netmon.App)
    logs = []
    refreshes = []

    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": "proton"}]
    app.wg_profiles = ["proton"]
    app.log = logs.append
    app.refresh_safe = lambda: refreshes.append(True)
    app.ensure_sudo_session = lambda label: True
    app.active_wg_profile = lambda: "proton"

    app.open_vpn_slot(0)

    assert logs == ["VPN-Profil bereits aktiv."]
    assert refreshes == [True]


def test_open_vpn_slot_switches_directly_to_new_profile_without_vpn_off(
    strict_subprocess_guard,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []

    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": "proton"}]
    app.wg_profiles = ["proton"]
    app.log = logs.append
    app.log_safe = logs.append
    app.refresh_safe = lambda: logs.append("refresh")
    app.ensure_sudo_session = lambda label: True
    app.active_wg_profile = lambda: "wg-old"
    app.run_async = lambda func: func()
    app.update_dns_controls_state_safe = lambda: None

    def fake_vpn_switch(profile, ensure_sudo=True, refresh_ui=True):
        calls.append(("switch", profile, ensure_sudo, refresh_ui))
        return True

    app.vpn_switch = fake_vpn_switch

    app.open_vpn_slot(0)

    assert calls == [("switch", "proton", False, False)]
    assert "VPN-Slot 1: proton gestartet." in logs


def test_start_vpn_slot_profile_sets_dns_transition_before_async_start():
    app = netmon.App.__new__(netmon.App)
    events = []

    app.log = lambda message: None
    app.ensure_sudo_session = lambda label: True
    app.active_wg_profile = lambda: "wg-old"
    app.set_dns_guard_state = lambda state: events.append(("state", state))
    app.update_dns_controls_state_safe = lambda: events.append("dns-ui")
    app.run_async = lambda func: events.append("run_async")

    assert app._start_vpn_slot_profile("proton", slot_no=1) is True
    assert events[:3] == [("state", "transition"), "dns-ui", "run_async"]
    assert app.dns_guard_transition_until > 0


class DummyCombo(dict):
    def winfo_exists(self):
        return True


def test_sync_vpn_profile_form_selection_clears_stale_profile_value():
    app = netmon.App.__new__(netmon.App)
    app.vpn_profile_var = DummyVar("proton")
    app.wg_profiles = ["wg-b"]

    app.sync_vpn_profile_form_selection()

    assert app.vpn_profile_var.get() == ""


def test_reload_wg_profiles_updates_vpn_slot_combo_and_views():
    app = netmon.App.__new__(netmon.App)
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    app.isp_stealth_vpn_combo = DummyCombo()
    calls = []
    app.sync_internal_ipv4_profiles = lambda log_failures=True: calls.append("sync")
    app.refresh_wg_profiles = lambda: setattr(app, "wg_profiles", ["wg-a", "wg-b"])
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")
    app.isp_stealth_vpn_profile = DummyVar("")
    app.isp_stealth_vpn_choice = DummyVar("")
    app.save_privacy_config = lambda: calls.append("save_privacy")
    app.update_ipv6_controls_state = lambda: calls.append("ipv6")
    logs = []
    app.log = logs.append

    app.reload_wg_profiles()

    assert app.vpn_profile_combo["values"] == ["wg-a", "wg-b"]
    assert calls[:3] == ["buttons", "table", "ipv6"]
    assert logs == ["WireGuard-Profile: wg-a, wg-b"]


def test_refresh_wg_profiles_updates_privacy_vpn_combo_on_startup():
    app = netmon.App.__new__(netmon.App)
    app.isp_stealth_vpn_combo = DummyCombo()
    app.isp_stealth_vpn_profile = DummyVar("")
    app.isp_stealth_vpn_choice = DummyVar("")
    app.primary_vpn_slots = []
    app.list_wg_profiles = lambda: ["wg-a", "wg-b"]
    app._base_wg_profile_name = lambda profile: profile
    app._privacy_vpn_label_for_profile = lambda profile: profile
    app.save_privacy_config = lambda: None
    app.log_safe = lambda _msg: None
    app.update_privacy_vpn_combo = (
        lambda: netmon.vpn_controller.update_privacy_vpn_combo(app)
    )

    app.refresh_wg_profiles()

    assert app.wg_profiles == ["wg-a", "wg-b"]
    assert app.isp_stealth_vpn_combo["values"] == ["wg-a", "wg-b"]


def test_get_nm_last_import_state_normalizes_invalid_session_values():
    app = netmon.App.__new__(netmon.App)
    app._nm_last_import_state = {
        "connections": [" wg-a ", "", None, "wg-b"],
        "source_files": [" /tmp/a.conf ", "", None],
        "imported_at": "7",
    }

    state = vpn_controller.get_nm_last_import_state(app)

    assert state == {
        "connections": ["wg-a", "wg-b"],
        "source_files": ["/tmp/a.conf"],
        "imported_at": 7,
    }


def test_set_nm_last_import_state_keeps_session_separate_without_saving():
    app = netmon.App.__new__(netmon.App)
    app.privacy_config = {"unrelated": "keep"}
    calls = []
    app.save_privacy_config = lambda: calls.append("save")

    state = vpn_controller.set_nm_last_import_state(
        app,
        {
            "connections": [" wg-a ", "", None],
            "source_files": [" /tmp/a.conf ", ""],
            "imported_at": "12",
        },
    )

    assert vpn_controller.get_nm_last_import_state(app) == state
    assert app.privacy_config == {"unrelated": "keep"}
    assert state == {
        "connections": ["wg-a"],
        "source_files": ["/tmp/a.conf"],
        "imported_at": 12,
    }
    assert calls == []


def test_set_vpn_backend_mode_creates_config_and_saves():
    app = netmon.App.__new__(netmon.App)
    calls = []
    app.save_privacy_config = lambda: calls.append("save")

    mode = vpn_controller.set_vpn_backend_mode(app, "networkmanager")

    assert mode == "wg-quick"
    assert app.__dict__["privacy_config"]["vpn_backend_mode"] == "wg-quick"
    assert calls == ["save"]


def test_get_wg_interfaces_and_active_profile_use_wg_show(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        return 0, "proton__ipv4 wg-slot\n"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app.get_wg_interfaces() == ["proton__ipv4", "wg-slot"]
    assert app.active_wg_profile() == "proton"
    assert calls == [["wg", "show", "interfaces"], ["wg", "show", "interfaces"]]


def test_cleanup_wireguard_interfaces_forces_delete_when_down_leaves_iface(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    debug_logs = []
    calls = []
    state = {"ifaces": ["wg-old", "wg-stuck"]}

    app._network_service = lambda: None
    app.log_safe = logs.append
    app.log_network_debug = debug_logs.append

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args in (
            ["wg", "show", "interfaces"],
            ["sudo", "-n", "wg", "show", "interfaces"],
        ):
            return 0, " ".join(state["ifaces"])
        if args == ["sudo", "-n", "wg-quick", "down", "wg-old"]:
            state["ifaces"] = [iface for iface in state["ifaces"] if iface != "wg-old"]
            return 0, "down old"
        if args == ["sudo", "-n", "wg-quick", "down", "wg-stuck"]:
            return 1, "still present"
        if args == ["sudo", "-n", "ip", "link", "delete", "wg-stuck"]:
            state["ifaces"] = [
                iface for iface in state["ifaces"] if iface != "wg-stuck"
            ]
            return 0, "deleted"
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    assert app.cleanup_wireguard_interfaces() is True
    assert calls == [
        ["wg", "show", "interfaces"],
        ["sudo", "-n", "wg-quick", "down", "wg-old"],
        ["sudo", "-n", "wg-quick", "down", "wg-stuck"],
        ["wg", "show", "interfaces"],
        ["sudo", "-n", "ip", "link", "delete", "wg-stuck"],
        ["wg", "show", "interfaces"],
    ]
    assert logs == [
        "WG Cleanup gestartet",
        "WG down: wg-old",
        "WG down: wg-stuck",
        "WG down Fehler (wg-stuck): rc=1",
        "still present",
        "WG forced delete: wg-stuck",
        "WG state clean",
    ]


def test_vpn_switch_runs_cleanup_before_starting_new_profile(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []

    app._try_begin_network_operation = lambda _label: True
    app._end_network_operation = lambda: calls.append("end")
    app.ensure_sudo_session = lambda _label: True
    app.debug_nm_state = None
    app.log_safe = logs.append
    app.log_debug = lambda *_args: None
    app.log_debug_safe = lambda *_args: None
    app.log_network_debug = lambda *_args: None
    app.tr = lambda _key, default=None: default or _key
    app.resolve_profile_family_runtime = lambda _target, log_missing=True: {
        "runtime_profile": "wg-new",
        "system_ipv6_disabled": False,
        "effective_ipv4_interface": "wg-new",
        "effective_ipv6_interface": None,
        "supports_ipv6": False,
    }
    app.resolve_runtime_vpn_profile = lambda _target, log_missing=True: "wg-new"
    app.get_wg_interfaces = lambda: ["wg-old"]
    app._network_service = lambda: None
    app._wg_profile_path = lambda profile: f"/etc/wireguard/{profile}.conf"
    app._check_wireguard_profile_for_multiple_endpoints = lambda *_args, **_kwargs: None
    app.prepare_dns_for_vpn_profile_switch = lambda: calls.append("dns")
    app._recover_firewall_after_killswitch_failure = lambda: calls.append("recover")
    app.refresh_safe = lambda: calls.append("refresh")
    app.refresh_wg_profiles = lambda: calls.append("profiles")
    app.update_primary_vpn_form_controls = lambda: calls.append("controls")
    app.sync_primary_vpn_form_selection = lambda: calls.append("selection")
    app.killswitch_is_on = lambda: False
    app._schedule_dns_finalize_after_vpn_profile_switch = (
        lambda delay_ms=2500: calls.append(("dns_finalize", delay_ms))
    )
    app.run_async = lambda func: calls.append("async")
    app.verify_vpn_exit_country = lambda _target: None
    app.update_ipv6_controls_state_safe = lambda: calls.append("ipv6")

    def fake_cleanup(_app):
        calls.append("cleanup")
        return True

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "test", "-f", "/etc/wireguard/wg-new.conf"]:
            return 0, ""
        if args == ["sudo", "-n", "wg-quick", "up", "wg-new"]:
            return 0, "up ok"
        raise AssertionError(f"Unexpected command: {args}")

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", fake_cleanup
    )

    assert app.vpn_switch("wg-new", ensure_sudo=False, refresh_ui=True) is True
    assert calls.index("cleanup") < calls.index(
        ["sudo", "-n", "wg-quick", "up", "wg-new"]
    )
    assert "profiles" in calls
    assert "ipv6" in calls
    assert "end" in calls
    assert any("VPN gestartet: wg-new" in entry for entry in logs)


def test_vpn_off_returns_false_when_cleanup_does_not_clear_interfaces(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app._try_begin_network_operation = lambda _label: True
    app._end_network_operation = lambda: calls.append("end")
    app.ensure_sudo_session = lambda _label: True
    app.debug_nm_state = None
    app.log_safe = logs.append
    app.refresh_safe = lambda: calls.append("refresh")

    monkeypatch.setattr(
        netmon.vpn_controller, "cleanup_wireguard_interfaces", lambda _app: False
    )

    assert app.vpn_off(ensure_sudo=False, refresh_ui=True) is False
    assert calls == ["refresh", "end"]
    assert not any("VPN deaktiviert." in entry for entry in logs)


def test_save_primary_vpn_slot_writes_config_and_updates_button_text(
    tmp_path, strict_subprocess_guard
):
    app = netmon.App.__new__(netmon.App)
    app.primary_vpn_config_path = str(tmp_path / "netmon_primary_vpn_slots.json")
    app.primary_vpn_slots = app._default_primary_vpn_slots()
    app.primary_vpn_1_name_var = DummyVar("Proton One")
    app.primary_vpn_1_profile_var = DummyVar("proton")
    app.primary_vpn_2_name_var = DummyVar("Proton Two")
    app.primary_vpn_2_profile_var = DummyVar("proton-de")
    app.btn_primary_vpn_1 = DummyWidget()
    app.btn_primary_vpn_2 = DummyWidget()
    app.log = lambda message: None
    app.update_primary_vpn_buttons = lambda: None
    app.run_async = lambda func: None

    app.save_primary_vpn_slot(1)

    loaded = json.loads(
        (__import__("pathlib").Path(app.primary_vpn_config_path).read_text())
    )
    assert loaded[0]["custom_name"] == "Proton One"
    assert loaded[0]["profile"] == "proton"


def test_update_primary_vpn_form_controls_updates_combobox_values():
    app = netmon.App.__new__(netmon.App)
    app.wg_profiles = ["wg-a", "wg-b"]
    app.primary_vpn_1_profile_combo = DummyCombo()
    app.primary_vpn_2_profile_combo = DummyCombo()

    app.update_primary_vpn_form_controls()

    assert app.primary_vpn_1_profile_combo["values"] == ["wg-a", "wg-b"]
    assert app.primary_vpn_2_profile_combo["values"] == ["wg-a", "wg-b"]


def test_import_wg_profiles_from_folder_updates_vpn_slot_combo_and_views(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    calls = []
    logs = []
    app.log = logs.append
    app.get_wg_import_dir = lambda: ""
    app.set_wg_import_dir = lambda folder: calls.append(("dir", folder))
    app.sync_internal_ipv4_profiles = lambda log_failures=True: calls.append("sync")
    app.refresh_wg_profiles = lambda: setattr(app, "wg_profiles", ["wg-imported"])
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")
    app.after = lambda delay, func: func()

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target is not None:
                self.target()

    monkeypatch.setattr(
        netmon.filedialog, "askopenfilenames", lambda **kwargs: ("/tmp/bad name.conf",)
    )
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)

    app.import_wg_profiles_from_folder()

    assert app.vpn_profile_combo["values"] == ["wg-imported"]
    assert calls == [("dir", "/tmp"), "sync", "buttons", "table"]
    assert "Übersprungen (ungültiger Profilname): bad name" in logs
    assert (
        "WireGuard-Import beendet: 0 importiert, 1 übersprungen, 0 fehlgeschlagen."
        in logs
    )


def test_collect_referenced_wg_profile_import_paths_uses_slots_primary_and_privacy():
    app = netmon.App.__new__(netmon.App)
    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work", "profile": "wg-one"},
        {"slot": 2, "custom_name": "", "profile": "wg-two"},
    ]
    app.primary_vpn_slots = [
        {"slot": 1, "custom_name": "Primary", "profile": "wg-two"},
        {"slot": 2, "custom_name": "Second", "profile": "wg-three"},
    ]
    app.privacy_config = {"vpn_profile": "wg-four"}
    app._wg_profile_path = lambda profile: f"/etc/wireguard/{profile}.conf"
    app._base_wg_profile_name = lambda value: netmon.App._base_wg_profile_name(
        app, value
    )
    app._privacy_vpn_profile_from_value = lambda value: value

    paths = app.collect_referenced_wg_profile_import_paths()

    assert paths == [
        ("wg-one", "/etc/wireguard/wg-one.conf"),
        ("wg-two", "/etc/wireguard/wg-two.conf"),
        ("wg-three", "/etc/wireguard/wg-three.conf"),
        ("wg-four", "/etc/wireguard/wg-four.conf"),
    ]


def test_open_vpn_slot_accepts_legacy_internal_ipv4_profile_name():
    app = netmon.App.__new__(netmon.App)
    started = []

    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": "proton__ipv4"}]
    app.wg_profiles = ["proton"]
    app.log = lambda message: None
    app._start_vpn_slot_profile = lambda profile, slot_no=None: started.append(
        (profile, slot_no)
    )

    app.open_vpn_slot(0)

    assert started == [("proton", 1)]


def test_open_vpn_slot_starts_existing_profile_even_when_profile_list_is_stale():
    app = netmon.App.__new__(netmon.App)
    logs = []
    started = []

    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": "proton"}]
    app.wg_profiles = []
    app.log = logs.append
    app._resolve_vpn_profile_input = lambda profile, refresh_profiles=False: "proton"
    app._wg_profile_exists = lambda profile: profile == "proton"
    app._start_vpn_slot_profile = lambda profile, slot_no=None: started.append(
        (profile, slot_no)
    )

    app.open_vpn_slot(0)

    assert logs == []
    assert started == [("proton", 1)]


def test_build_input_access_baseline_sets_state(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    app.input_access_baseline = {}
    app.security_input_access_whitelist = set()
    app._scan_input_access_state = lambda: {
        "/dev/input/event0": {"123": "testproc"},
        "/dev/input/event1": {"999": "another"},
    }

    baseline = app.build_input_access_baseline()
    assert baseline == app.input_access_baseline
    assert "/dev/input/event0" in baseline
    assert baseline["/dev/input/event0"]["123"] == "testproc"


def test_scan_input_access_changes_detects_events():
    app = netmon.App.__new__(netmon.App)
    app.input_access_baseline = {
        "/dev/input/event0": {"123": "testproc"},
    }
    app.security_input_access_whitelist = {"whitelisted"}

    app._scan_input_access_state = lambda: {
        "/dev/input/event0": {"123": "testproc", "456": "evil"},
        "/dev/input/event1": {"999": "other"},
    }

    events = app.scan_input_access_changes()
    types = [e["type"] for e in events]
    assert "INPUT ACCESS START" in types
    assert any("evil" in e["raw"] for e in events)
    assert any("event1" in e["raw"] for e in events)

    # now the baseline should be updated to current state
    assert "/dev/input/event1" in app.input_access_baseline


def test_scan_input_access_changes_skips_whitelisted_processes():
    app = netmon.App.__new__(netmon.App)
    app.input_access_baseline = {}
    app.security_input_access_whitelist = {"trusted"}

    app._scan_input_access_state = lambda: {
        "/dev/input/event0": {"200": "trusted"},
    }

    events = app.scan_input_access_changes()
    assert len(events) == 0


def test_open_vpn_slot_logs_missing_profile_and_opens_slot_tab(strict_subprocess_guard):
    app = netmon.App.__new__(netmon.App)
    logs = []
    tab_calls = []
    started = []

    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": "missing-profile"}]
    app.wg_profiles = ["proton"]
    app._wg_profile_exists = lambda profile: profile == "proton"
    app.list_wg_profiles = lambda: ["proton"]
    app.log = logs.append
    app.nb = type("Notebook", (), {"select": lambda self, tab: tab_calls.append(tab)})()
    app.tab_vpn_slots = "vpn-tab"
    app.load_vpn_slot_into_form = lambda slot_no: tab_calls.append(slot_no)
    app._start_vpn_slot_profile = lambda profile, slot_no=None: started.append(
        (profile, slot_no)
    )

    app.open_vpn_slot(0)

    assert logs == ["VPN-Slot 1: Profil 'missing-profile' nicht gefunden."]
    assert tab_calls == ["vpn-tab", 1]
    assert started == []


class DummyTable:
    def __init__(self):
        self.rows = {}
        self.selected = ()
        self.focused = None

    def selection(self):
        return self.selected

    def get_children(self):
        return tuple(self.rows.keys())

    def delete(self, item):
        self.rows.pop(item, None)

    def insert(self, parent, index, iid=None, values=()):
        self.rows[iid] = values

    def selection_set(self, iid):
        self.selected = (iid,)

    def focus(self, iid):
        self.focused = iid

    def item(self, iid, option=None):
        values = self.rows.get(iid, ())
        if option == "values":
            return values
        return {"values": values}


def test_refresh_vpn_slots_table_preserves_selection_without_leaving_refresh_flag():
    app = netmon.App.__new__(netmon.App)
    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work", "profile": "wg-v6"},
        {"slot": 2, "custom_name": "", "profile": "wg-v4"},
    ]
    app.vpn_table = DummyTable()
    app.vpn_table.rows = {"vpn-slot-1": (), "vpn-slot-2": ()}
    app.vpn_table.selected = ("vpn-slot-2",)
    app.active_wg_profile = lambda: ""
    app.wg_profiles = ["wg-v6", "wg-v4"]
    app.profile_supports_ipv6 = lambda profile: profile == "wg-v6"

    app.refresh_vpn_slots_table()

    assert app.vpn_table.selection() == ("vpn-slot-2",)
    assert app.vpn_table.focused == "vpn-slot-2"
    assert app._vpn_table_refreshing is False


def test_on_vpn_table_select_ignores_programmatic_refresh_selection():
    app = netmon.App.__new__(netmon.App)
    app._vpn_table_refreshing = True
    app.vpn_table = DummyTable()
    app.vpn_table.rows = {"vpn-slot-1": (1, "Work", "wg-v6", "bereit", "IPv6")}
    app.vpn_table.selected = ("vpn-slot-1",)
    calls = []
    app.load_vpn_slot_into_form = lambda slot_no: calls.append(slot_no)

    app.on_vpn_table_select()

    assert calls == []


def test_vpn_table_context_menu_offers_profile_delete_and_uses_existing_logic(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    events = []

    class DummyTable:
        def __init__(self):
            self.bound = {}
            self.selected = ("vpn-slot-2",)
            self.focused = None

        def selection(self):
            return self.selected

        def focus(self, row_id):
            self.focused = row_id

        def selection_set(self, row_id):
            self.selected = (row_id,)

        def identify_row(self, _y):
            return "vpn-slot-2"

        def bind(self, event, callback, add=None):
            self.bound[event] = callback

    monkeypatch.setattr(netmon.tk, "Menu", DummyMenu)

    app.vpn_table = DummyTable()
    app.attach_selection_copy_shortcuts = lambda *_args: None
    app.copy_treeview_selection_to_clipboard = lambda _table: None
    app.select_all_treeview_rows = lambda _table: None
    app._show_context_menu = lambda menu, _event: events.append(menu) or "shown"
    app.on_vpn_table_select = lambda _event=None: events.append("selected")
    app.delete_selected_vpn_profile = lambda: events.append("deleted")

    app.attach_simple_tree_context_menu(app.vpn_table)

    show_menu = app.vpn_table.bound["<Button-3>"]
    event = type("Event", (), {"y": 3})()
    assert show_menu(event) == "shown"

    menu = app.vpn_table._simple_context_menu
    delete_entry = next(
        entry
        for entry in menu.entries
        if entry.get("kind") == "command" and entry.get("label") == "Profil löschen"
    )
    delete_entry["command"]()

    assert events[0] is menu
    assert events[1:] == ["selected", "deleted"]


def test_apply_profile_ufw_rules_non_killswitch_uses_dedupe_wrapper_without_tk_getattr():
    app = netmon.App.__new__(netmon.App)
    logs = []
    debug_logs = []
    ensure_calls = []

    app.ufw_lock = threading.Lock()
    app.log = logs.append
    app.log_debug = debug_logs.append
    app.log_debug_safe = debug_logs.append
    app._network_service = lambda: None
    app._read_ufw_status = lambda verbose=True: (0, "Status: active")
    app._ufw_status_is_active = lambda _text: True
    app._ufw_existing_rule_keys = lambda _text: set()
    app.ensure_ufw_rule_exists = lambda rule, network_service=None, known_keys=None: (
        ensure_calls.append(rule),
        (True, True, "", known_keys if known_keys is not None else set()),
    )[1]
    app._dedupe_vpn_ufw_rules = lambda: 2

    assert (
        app._apply_profile_ufw_rules_non_killswitch(
            {"wg-slot"},
            {("198.51.100.10", "51820")},
        )
        is True
    )
    assert {"type": "interface", "iface": "wg-slot", "direction": "out"} in ensure_calls
    assert {"type": "interface", "iface": "wg-slot", "direction": "in"} in ensure_calls
    assert {"type": "endpoint", "ip": "198.51.100.10", "port": "51820"} in ensure_calls
    assert "UFW-Duplikate bereinigt: 2" in logs


def test_validate_manual_wireguard_form_requires_and_normalizes_address():
    app = netmon.App.__new__(netmon.App)
    app.manual_wg_profile_name_var = DummyVar("USA")
    app.manual_wg_private_key_var = DummyVar("A" * 43 + "=")
    app.manual_wg_public_key_var = DummyVar("B" * 43 + "=")
    app.manual_wg_endpoint_var = DummyVar("146.70.174.162:51820")
    app.manual_wg_address_var = DummyVar("10.2.0.2/32, 2a07:b944::2:2/128")
    app.manual_wg_allowed_ips_var = DummyVar("0.0.0.0/0, ::/0")
    app.manual_wg_dns_var = DummyVar("10.2.0.1, 2a07:b944::2:1")
    app.manual_wg_keepalive_var = DummyVar("25")
    app._is_internal_ipv4_profile = lambda profile: False
    app._is_valid_wireguard_key = lambda value: True
    app._parse_manual_wireguard_endpoint = lambda endpoint: (
        "146.70.174.162",
        "51820",
        "",
    )

    payload, err = app._validate_manual_wireguard_form()

    assert err == ""
    assert payload["address"] == "10.2.0.2/32, 2a07:b944::2:2/128"


def test_normalize_wireguard_key_strips_common_copy_paste_artifacts():
    app = netmon.App.__new__(netmon.App)

    normalized = app._normalize_wireguard_key(
        "= 6Mzvr485XQfi/zOXS0oRQVry0waf5ijvnTAn4xqO2CM="
    )

    assert normalized == "6Mzvr485XQfi/zOXS0oRQVry0waf5ijvnTAn4xqO2CM="


def test_validate_wireguard_key_value_returns_clear_message_for_bad_input():
    app = netmon.App.__new__(netmon.App)
    app._normalize_wireguard_key = lambda value: vpn_controller.normalize_wireguard_key(
        app, value
    )
    app._is_valid_wireguard_key = lambda value: vpn_controller.is_valid_wireguard_key(
        app, value
    )

    token, err = app._validate_wireguard_key_value("= falsch", "Public Key")

    assert token == ""
    assert "Public Key ungültig." in err
    assert "führendes '='" in err


def test_apply_manual_wireguard_profile_shows_compact_validation_error():
    app = netmon.App.__new__(netmon.App)
    status_calls = []
    logs = []
    focus_calls = []

    app._validate_manual_wireguard_form = lambda: (
        None,
        "Public Key ungültig. Bitte nur den reinen Base64-Key ohne führendes '=' oder zusätzliche Zeichen einfügen.",
    )
    app._set_manual_wg_status = lambda message, level="info": status_calls.append(
        (message, level)
    )
    app._manual_wireguard_error_widget_name = (
        lambda error_text: vpn_controller.manual_wireguard_error_widget_name(
            app, error_text
        )
    )
    app._focus_manual_wg_field = lambda widget_name: focus_calls.append(widget_name)
    app.log = logs.append

    app.apply_manual_wireguard_profile()

    assert status_calls == [
        (
            "Public Key ungültig. Bitte nur den reinen Base64-Key ohne führendes '=' oder zusätzliche Zeichen einfügen.",
            "error",
        )
    ]
    assert logs == [
        "Manuelle WireGuard-Konfiguration ungültig: Public Key ungültig. Bitte nur den reinen Base64-Key ohne führendes '=' oder zusätzliche Zeichen einfügen."
    ]
    assert focus_calls == ["manual_wg_public_key_entry"]


def test_build_manual_wireguard_config_text_includes_address():
    payload = {
        "private_key": "private",
        "public_key": "public",
        "endpoint": "146.70.174.162:51820",
        "address": "10.2.0.2/32, 2a07:b944::2:2/128",
        "allowed_ips": "0.0.0.0/0, ::/0",
        "dns": "10.2.0.1, 2a07:b944::2:1",
        "keepalive": "25",
    }

    text = vpn_controller.build_manual_wireguard_config_text(None, payload)

    assert "Address = 10.2.0.2/32, 2a07:b944::2:2/128" in text
    assert "DNS = 10.2.0.1, 2a07:b944::2:1" in text


def test_refresh_vpn_slots_table_shows_ipv4_ipv6_free_and_unknown():
    app = netmon.App.__new__(netmon.App)
    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work", "profile": "wg-v6"},
        {"slot": 2, "custom_name": "", "profile": "wg-v4"},
        {"slot": 3, "custom_name": "", "profile": ""},
        {"slot": 4, "custom_name": "Legacy", "profile": "wg-missing"},
    ]
    app.vpn_table = DummyTable()
    app.active_wg_profile = lambda: ""
    app.wg_profiles = ["wg-v6", "wg-v4"]
    app.profile_supports_ipv6 = lambda profile: profile == "wg-v6"

    app.refresh_vpn_slots_table()

    assert app.vpn_table.rows["vpn-slot-1"] == (1, "Work", "wg-v6", "bereit")
    assert app.vpn_table.rows["vpn-slot-2"] == (2, "-", "wg-v4", "bereit")
    assert app.vpn_table.rows["vpn-slot-3"] == (3, "-", "-", "frei")
    assert app.vpn_table.rows["vpn-slot-4"] == (4, "Legacy", "wg-missing", "fehlt")


def test_import_wg_profiles_from_folder_uses_initialdir_and_remembers_last_directory(
    monkeypatch,
    tmp_path,
):
    source = tmp_path / "wg-demo.conf"
    source.write_text("[Interface]\nAddress=10.0.0.1/32\n")
    app = netmon.App.__new__(netmon.App)
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    calls = []
    logs = []
    dialog_kwargs = {}
    app.log = logs.append
    app.get_wg_import_dir = lambda: "/start/here"
    app.set_wg_import_dir = lambda folder: calls.append(("dir", folder))
    app.sync_internal_ipv4_profiles = lambda log_failures=True: calls.append("sync")
    app.refresh_wg_profiles = lambda: setattr(app, "wg_profiles", ["wg-imported"])
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")
    app.after = lambda delay, func: func()

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target is not None:
                self.target()

    def fake_askopenfilenames(**kwargs):
        dialog_kwargs.update(kwargs)
        return (str(source),)

    def fake_run_cmd(args, timeout=0, text=True):
        return 0, "ok"

    monkeypatch.setattr(netmon.filedialog, "askopenfilenames", fake_askopenfilenames)
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    monkeypatch.setattr(vpn_controller.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(vpn_controller, "_owned_nm_command", lambda *a, **k: None)
    app.import_wg_profiles_from_folder()

    assert dialog_kwargs["initialdir"] == "/start/here"
    assert calls == [("dir", str(tmp_path)), "sync", "buttons", "table"]
    assert (
        "WireGuard-Import beendet: 1 importiert, 0 übersprungen, 0 fehlgeschlagen."
        in logs
    )


def test_wireguard_profile_hook_directives_detects_known_hooks(tmp_path):
    profile_path = tmp_path / "wg-hooks.conf"
    profile_path.write_text(
        "[Interface]\n"
        "Address = 10.0.0.2/32\n"
        "PostUp = iptables -A OUTPUT -j ACCEPT\n"
        "PreDown = iptables -D OUTPUT -j ACCEPT\n",
        encoding="utf-8",
    )

    directives = vpn_controller._wireguard_profile_hook_directives(str(profile_path))

    assert directives == ["PostUp", "PreDown"]


def test_warn_wireguard_import_hooks_shows_warning_and_logs(tmp_path, monkeypatch):
    profile_path = tmp_path / "wg-hooks.conf"
    profile_path.write_text(
        "[Peer]\nPostUp = echo demo\n",
        encoding="utf-8",
    )
    app = netmon.App.__new__(netmon.App)
    logs = []
    warnings = []
    app.log_safe = logs.append
    app.tr = lambda _key, fallback: fallback

    monkeypatch.setattr(
        vpn_controller.messagebox,
        "showwarning",
        lambda title, text, parent=None: warnings.append((title, text, parent)),
    )

    assert vpn_controller._warn_wireguard_import_hooks(app, [str(profile_path)]) is True
    assert warnings
    assert warnings[0][0] == "WireGuard Hook-Hinweis"
    assert "PostUp" in warnings[0][1]
    assert logs
    assert "Root-Rechten" in logs[0]


def test_import_wg_profiles_from_folder_warns_about_hook_directives(
    monkeypatch, tmp_path
):
    profile_path = tmp_path / "wg-hooks.conf"
    profile_path.write_text(
        "[Peer]\nPostDown = echo done\n",
        encoding="utf-8",
    )
    app = netmon.App.__new__(netmon.App)
    app.wg_profiles = []
    app.vpn_profile_combo = DummyCombo()
    calls = []
    logs = []
    warnings = []
    app.log = logs.append
    app.log_safe = logs.append
    app.get_wg_import_dir = lambda: str(tmp_path)
    app.set_wg_import_dir = lambda folder: calls.append(("dir", folder))
    app.sync_internal_ipv4_profiles = lambda log_failures=True: calls.append("sync")
    app.refresh_wg_profiles = lambda: setattr(app, "wg_profiles", ["wg-hooks"])
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")
    app.after = lambda delay, func: func()
    app.tr = lambda _key, fallback: fallback

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            if self.target is not None:
                self.target()

    monkeypatch.setattr(
        netmon.filedialog,
        "askopenfilenames",
        lambda **kwargs: (str(profile_path),),
    )
    monkeypatch.setattr(netmon.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        vpn_controller.messagebox,
        "showwarning",
        lambda title, text, parent=None: warnings.append((title, text, parent)),
    )

    def fake_run_cmd(args, timeout=0, text=True):
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    monkeypatch.setattr(vpn_controller.messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(vpn_controller, "_owned_nm_command", lambda *a, **k: None)
    app.import_wg_profiles_from_folder()

    assert warnings
    assert "PostDown" in warnings[0][1]
    assert (
        "WireGuard-Import beendet: 1 importiert, 0 übersprungen, 0 fehlgeschlagen."
        in logs
    )


def test_base_wg_profile_name_strips_internal_ipv4_suffix():
    app = netmon.App.__new__(netmon.App)

    assert app._base_wg_profile_name("proton__ipv4") == "proton"
    assert app._base_wg_profile_name(" user-vpn ") == "user-vpn"
    assert app._base_wg_profile_name("") == ""


def test_internal_ipv4_profile_candidates_keep_legacy_name_for_short_profile():
    app = netmon.App.__new__(netmon.App)

    assert app._internal_ipv4_profile_candidates("proton") == ["proton__ipv4"]


def test_internal_ipv4_profile_candidates_prefer_compact_name_for_long_profile():
    app = netmon.App.__new__(netmon.App)

    candidates = app._internal_ipv4_profile_candidates(
        "very-long-profile-name-for-wireguard"
    )

    assert len(candidates) == 2
    assert candidates[0].startswith("n4_")
    assert len(candidates[0]) <= 15
    assert candidates[1] == "very-long-profile-name-for-wireguard__ipv4"


def test_privacy_vpn_options_and_mappings_from_netmon_profiles():
    app = netmon.App.__new__(netmon.App)
    app.wg_profiles = ["proton", "user-vpn", "custom", "custom-other"]
    app.primary_vpn_slots = [
        {"slot": 1, "custom_name": "Proton CH", "profile": "proton"},
        {"slot": 2, "custom_name": "Duplicate", "profile": "custom"},
        {"slot": 3, "custom_name": "Duplicate", "profile": "custom-other"},
        {"slot": 4, "custom_name": "", "profile": "unused-slot"},
    ]

    options = app.get_privacy_vpn_options()
    assert options == [
        {"label": "Proton CH", "profile": "proton"},
        {"label": "user-vpn", "profile": "user-vpn"},
        {"label": "Duplicate", "profile": "custom"},
        {"label": "Duplicate (2)", "profile": "custom-other"},
    ]

    assert app._privacy_vpn_profile_from_value("Proton CH") == "proton"
    assert app._privacy_vpn_profile_from_value("user-vpn") == "user-vpn"
    assert app._privacy_vpn_profile_from_value("proton") == "proton"
    assert app._privacy_vpn_profile_from_value("unknown") == ""
    assert app._privacy_vpn_label_for_profile("proton") == "Proton CH"
    assert app._privacy_vpn_label_for_profile("user-vpn") == "user-vpn"
    assert app._privacy_vpn_label_for_profile("nonexistent") == ""


def test_security_integrity_baseline_and_scan(tmp_path):
    app = netmon.App.__new__(netmon.App)
    testfile = tmp_path / "cfg.conf"
    testfile.write_text("abc")
    app._integrity_watch_files = lambda: [str(testfile)]

    baseline = app.build_integrity_baseline()
    assert str(testfile) in baseline

    testfile.write_text("abcd")
    events = app.scan_integrity_changes()
    assert any(e["type"] == "FILE MODIFIED" for e in events)


def test_security_device_baseline_and_scan(tmp_path):
    app = netmon.App.__new__(netmon.App)
    path1 = str(tmp_path / "event1")
    path2 = str(tmp_path / "event2")
    (tmp_path / "event1").write_text("")
    app._device_watch_paths = lambda: [path1]

    baseline = app.build_device_baseline()
    assert path1 in baseline

    app._device_watch_paths = lambda: [path1, path2]
    events = app.scan_device_changes()
    assert any(e["type"] == "DEVICE NEW" for e in events)


def test_security_baseline_persistence(tmp_path):
    app = netmon.App.__new__(netmon.App)
    app.security_baseline_path = str(tmp_path / "security_base.json")
    app.integrity_baseline = {"a": {"sha": "x"}}
    app.device_baseline = {"/dev/input/event1": "input-event"}
    app.input_access_baseline = {"/dev/input/event1": {"123": "testproc"}}

    assert app._save_security_baseline()

    loaded_app = netmon.App.__new__(netmon.App)
    loaded_app.security_baseline_path = app.security_baseline_path
    assert loaded_app._load_security_baseline()
    assert loaded_app.integrity_baseline["a"]["sha"] == "x"
    assert loaded_app.device_baseline["/dev/input/event1"] == "input-event"


def test_save_primary_vpn_slot_updates_privacy_combobox_and_selection(
    strict_subprocess_guard,
):
    app = netmon.App.__new__(netmon.App)
    app.primary_vpn_slots = [
        {"slot": 1, "custom_name": "Proton CH", "profile": "proton"},
        {"slot": 2, "custom_name": "Proton DE", "profile": "proton-de"},
    ]
    app.primary_vpn_1_name_var = DummyVar("My CH")
    app.primary_vpn_1_profile_var = DummyVar("proton")
    app.primary_vpn_2_name_var = DummyVar("Proton DE")
    app.primary_vpn_2_profile_var = DummyVar("proton-de")
    app.wg_profiles = ["proton", "proton-de"]
    app.isp_stealth_enabled = DummyVar(False)
    app.isp_stealth_autostart = DummyVar(False)
    app.isp_stealth_disable_ipv6 = DummyVar(False)
    app.isp_stealth_enable_killswitch = DummyVar(False)
    app.isp_stealth_vpn_profile = DummyVar("proton")
    app.isp_stealth_vpn_choice = DummyVar("Proton CH")
    app.isp_stealth_dns_profile = DummyVar("System (DHCP/auto)")
    app.isp_stealth_vpn_combo = DummyCombo()
    app.save_primary_vpn_slots_config = lambda: None
    app.update_primary_vpn_buttons = lambda: None
    app.log = lambda _: None
    app.run_async = lambda func: None

    app.save_primary_vpn_slot(1)

    assert app.primary_vpn_slots[0]["custom_name"] == "My CH"
    assert app.isp_stealth_vpn_combo["values"] == ["My CH", "Proton DE"]
    assert app.isp_stealth_vpn_choice.get() == "My CH"
    assert app.isp_stealth_vpn_profile.get() == "proton"


def test_apply_privacy_config_sets_label_from_profile():
    app = netmon.App.__new__(netmon.App)
    app.primary_vpn_slots = [
        {"slot": 1, "custom_name": "Proton CH", "profile": "proton"},
        {"slot": 2, "custom_name": "Proton DE", "profile": "proton-de"},
    ]
    app.isp_stealth_enabled = DummyVar(False)
    app.isp_stealth_autostart = DummyVar(False)
    app.isp_stealth_disable_ipv6 = DummyVar(False)
    app.isp_stealth_enable_killswitch = DummyVar(False)
    app.isp_stealth_vpn_profile = DummyVar("")
    app.isp_stealth_vpn_choice = DummyVar("")
    app.isp_stealth_dns_profile = DummyVar("System (DHCP/auto)")

    app._apply_privacy_config_to_vars({"vpn_profile": "proton"})

    assert app.isp_stealth_vpn_profile.get() == "proton"
    assert app.isp_stealth_vpn_choice.get() == "Proton CH"


def test_verify_vpn_exit_country_logs_mismatch(monkeypatch):
    app = netmon.App.__new__(netmon.App)
    logs = []
    app.log_safe = logs.append
    app._base_wg_profile_name = lambda p: p
    app.public_ip = ""
    app.country = ""

    def fake_run_cmd(args, timeout=15, text=True):
        if "ifconfig.me" in args:
            return 0, "1.2.3.4"
        if "ipinfo.io/country" in args:
            return 0, "IE"
        return 1, ""

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)

    app.verify_vpn_exit_country("NL")

    assert any(
        "Warnung: Profilname 'NL' passt nicht zum realen Exit-Land 'IE'" in m
        for m in logs
    )


def test_check_wireguard_profile_for_multiple_endpoints_logs_warning(tmp_path):
    app = netmon.App.__new__(netmon.App)
    app._wg_profile_path = lambda profile: str(tmp_path / f"{profile}.conf")
    app.log_safe = lambda msg: logs.append(msg)

    path = tmp_path / "proton.conf"
    path.write_text("""
[Interface]
PrivateKey=abc

[Peer]
PublicKey=abc
Endpoint=1.1.1.1:51820
Endpoint=2.2.2.2:51820
""")
    logs = []

    app._check_wireguard_profile_for_multiple_endpoints("proton")

    assert any("enthält mehrere aktive Endpoint-Zeilen" in m for m in logs)


def test_list_wg_profiles_omits_missing_default_profiles():
    app = netmon.App.__new__(netmon.App)
    monkeypatch = __import__("pytest").MonkeyPatch()
    monkeypatch.setattr(
        netmon.vpn_controller,
        "list_wg_profile_files",
        lambda _app, include_internal=False: ["wg-a"],
    )
    monkeypatch.setattr(
        netmon.vpn_controller,
        "list_netmon_wg_profile_files",
        lambda _app, include_internal=False: ["wg-b"],
    )
    monkeypatch.setattr(
        netmon.vpn_controller, "get_nm_wireguard_profiles", lambda _app: ["wg-b"]
    )
    try:
        assert app.list_wg_profiles() == ["wg-a", "wg-b"]
    finally:
        monkeypatch.undo()


def test_assign_vpn_slot_rolls_back_when_save_fails(strict_subprocess_guard):
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.vpn_slot_choice = DummyVar("1")
    app.vpn_profile_var = DummyVar("proton")
    app.vpn_custom_name_var = DummyVar("Work")
    app.list_wg_profiles = lambda: ["proton", "wg-b"]
    app.vpn_slots = [
        {"slot": 1, "custom_name": "", "profile": ""},
        {"slot": 2, "custom_name": "Other", "profile": "wg-b"},
    ]
    app.log = logs.append
    app.save_vpn_slots_config = lambda: False
    app.load_vpn_slot_into_form = lambda slot_no: calls.append(("load_form", slot_no))
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")

    app.assign_vpn_slot()

    assert app.vpn_slots == [
        {"slot": 1, "custom_name": "", "profile": ""},
        {"slot": 2, "custom_name": "Other", "profile": "wg-b"},
    ]
    assert ("load_form", 1) in calls
    assert "buttons" in calls
    assert "table" in calls
    assert any("konnte nicht gespeichert" in entry for entry in logs)


def test_clear_vpn_slot_clears_profile_and_runs_firewall_cleanup_in_order():
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.vpn_slot_choice = DummyVar("1")
    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work", "profile": "proton"},
        {"slot": 2, "custom_name": "Other", "profile": "wg-b"},
    ]
    app.log = logs.append
    app.save_vpn_slots_config = lambda: calls.append("save_slots")

    app._collect_referenced_vpn_profiles = lambda include_active=True: (
        ["proton", "wg-b"] if app.vpn_slots[0]["profile"] else ["wg-b"]
    )
    app._collect_interface_rules_for_profiles = lambda profiles: (
        {"proton", "proton__ipv4", "wg-b", "wg-b__ipv4"}
        if "proton" in profiles
        else {"wg-b", "wg-b__ipv4"}
    )
    app._collect_endpoint_rules_for_profiles = lambda profiles: (
        {("1.1.1.1", "51820"), ("2.2.2.2", "443")}
        if "proton" in profiles
        else {("2.2.2.2", "443")}
    )
    app._reconcile_vpn_firewall_rules = (
        lambda **kwargs: calls.append(
            (
                "reconcile",
                sorted(kwargs["old_interfaces"]),
                sorted(kwargs["new_interfaces"]),
                sorted(kwargs["old_endpoints"]),
                sorted(kwargs["new_endpoints"]),
                kwargs.get("removed_profile"),
            )
        )
        or True
    )

    app.load_vpn_slot_into_form = lambda slot_no: calls.append(("load_form", slot_no))
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")

    app.clear_vpn_slot()

    assert app.vpn_slots[0] == {"slot": 1, "custom_name": "", "profile": ""}
    assert calls == [
        "save_slots",
        (
            "reconcile",
            ["proton", "proton__ipv4", "wg-b", "wg-b__ipv4"],
            ["wg-b", "wg-b__ipv4"],
            [("1.1.1.1", "51820"), ("2.2.2.2", "443")],
            [("2.2.2.2", "443")],
            "proton",
        ),
        ("load_form", 1),
        "buttons",
        "table",
    ]
    assert any("Profil 'proton' entfernt" in entry for entry in logs)
    assert "VPN-Slot 1 aufgehoben (proton)." in logs


def test_clear_vpn_slot_without_profile_keeps_old_behavior_without_firewall_cleanup():
    app = netmon.App.__new__(netmon.App)
    calls = []

    app.vpn_slot_choice = DummyVar("1")
    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": ""}]
    app.log = lambda message: calls.append(("log", message))
    app.save_vpn_slots_config = lambda: calls.append("save_slots")
    app._collect_referenced_vpn_profiles = lambda include_active=True: []
    app._collect_interface_rules_for_profiles = lambda profiles: set()
    app._collect_endpoint_rules_for_profiles = lambda profiles: set()
    app._reconcile_vpn_firewall_rules = (
        lambda **kwargs: calls.append(("reconcile", kwargs)) or True
    )
    app.load_vpn_slot_into_form = lambda slot_no: calls.append(("load_form", slot_no))
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")

    app.clear_vpn_slot()

    assert app.vpn_slots[0] == {"slot": 1, "custom_name": "", "profile": ""}
    assert not any(
        isinstance(entry, tuple) and entry and entry[0] == "reconcile"
        for entry in calls
    )


def test_clear_vpn_slot_rolls_back_when_save_fails_and_skips_reconcile():
    app = netmon.App.__new__(netmon.App)
    calls = []
    logs = []

    app.vpn_slot_choice = DummyVar("1")
    app.vpn_slots = [{"slot": 1, "custom_name": "Work", "profile": "proton"}]
    app.log = logs.append
    app.save_vpn_slots_config = lambda: False
    app._collect_referenced_vpn_profiles = lambda include_active=True: ["proton"]
    app._collect_interface_rules_for_profiles = lambda profiles: {
        "proton",
        "proton__ipv4",
    }
    app._collect_endpoint_rules_for_profiles = lambda profiles: {("1.1.1.1", "51820")}
    app._reconcile_vpn_firewall_rules = (
        lambda **kwargs: calls.append(("reconcile", kwargs)) or True
    )
    app.load_vpn_slot_into_form = lambda slot_no: calls.append(("load_form", slot_no))
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")

    app.clear_vpn_slot()

    assert app.vpn_slots[0] == {"slot": 1, "custom_name": "Work", "profile": "proton"}
    assert not any(
        isinstance(entry, tuple) and entry and entry[0] == "reconcile"
        for entry in calls
    )
    assert ("load_form", 1) in calls
    assert "buttons" in calls
    assert "table" in calls
    assert any("konnte nicht gelöscht" in entry for entry in logs)


def test_remove_firewall_rules_for_vpn_profile_skips_when_profile_is_still_used(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work", "profile": "proton"},
        {"slot": 2, "custom_name": "Backup", "profile": "proton"},
    ]
    app.log = logs.append
    app.ufw_lock = threading.Lock()

    def fail_run_cmd(args, timeout=0, text=True):
        raise AssertionError(args)

    monkeypatch.setattr(netmon, "run_cmd", fail_run_cmd)

    assert (
        app._remove_firewall_rules_for_vpn_profile("proton", removed_from_slot=1)
        is True
    )
    assert any(
        "wird noch in einem anderen VPN-Slot verwendet" in entry for entry in logs
    )


def test_remove_firewall_rules_for_vpn_profile_deletes_profile_specific_ufw_rules(
    monkeypatch,
    strict_subprocess_guard,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []

    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work", "profile": "proton"},
        {"slot": 2, "custom_name": "Other", "profile": "wg-b"},
    ]
    app.log = logs.append
    app.log_debug_safe = lambda msg: logs.append(f"debug:{msg}")
    app.ufw_lock = threading.Lock()
    app.ensure_sudo_session = lambda label: True

    endpoints = {
        "proton": ("1.1.1.1", "51820"),
        "proton__ipv4": ("1.1.1.1", "51820"),
        "wg-b": ("2.2.2.2", "443"),
    }
    app.parse_vpn_endpoint = lambda profile: endpoints.get(profile, (None, None))
    app.resolve_profile_family_runtime = lambda profile, log_missing=True: {
        "endpoint_profiles": [
            candidate
            for candidate in (profile, profile + "__ipv4")
            if candidate in endpoints
        ]
    }
    app._collect_referenced_vpn_profiles = lambda include_active=True: ["wg-b"]
    app._collect_interface_rules_for_profiles = lambda profiles: (
        {"proton", "proton__ipv4"} if "proton" in profiles else {"wg-b", "wg-b__ipv4"}
    )

    def fake_run_cmd(args, timeout=0, text=True):
        calls.append(args)
        if args == ["sudo", "-n", "ufw", "status"]:
            return 0, "Status: active"
        if args[:4] == ["sudo", "-n", "ufw", "delete"]:
            return 0, "Rule deleted"
        return 0, "ok"

    monkeypatch.setattr(netmon, "has_cmd", lambda cmd: cmd == "ufw")
    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)

    assert (
        app._remove_firewall_rules_for_vpn_profile("proton", removed_from_slot=1)
        is True
    )
    assert ["sudo", "-n", "ufw", "delete", "allow", "out", "on", "proton"] in calls
    assert ["sudo", "-n", "ufw", "delete", "allow", "in", "on", "proton"] in calls
    assert [
        "sudo",
        "-n",
        "ufw",
        "delete",
        "allow",
        "out",
        "on",
        "proton__ipv4",
    ] in calls
    assert ["sudo", "-n", "ufw", "delete", "allow", "in", "on", "proton__ipv4"] in calls
    assert [
        "sudo",
        "-n",
        "ufw",
        "delete",
        "allow",
        "out",
        "to",
        "1.1.1.1",
        "port",
        "51820",
        "proto",
        "udp",
    ] in calls
    assert any("Interface-Regeln entfernt" in entry for entry in logs)
    assert any("UDP-Endpoint-Regeln entfernt" in entry for entry in logs)


def test_delete_selected_vpn_profile_logs_if_matching_runtime_interface_remains(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []
    run_calls = []

    app.vpn_profile_var = DummyVar("proton")
    app.vpn_slot_choice = DummyVar("1")
    app.vpn_custom_name_var = DummyVar("")
    app.vpn_profile_combo = DummyCombo()
    app.vpn_slots = [{"slot": 1, "custom_name": "", "profile": ""}]
    app.wg_profiles = []
    app.log = logs.append
    app.ensure_sudo_session = lambda label: True
    app.active_wg_profile = lambda: "proton"
    active_connections = ["proton"]
    app.vpn_off = (
        lambda ensure_sudo=True, refresh_ui=True: calls.append(
            ("vpn_off", ensure_sudo, refresh_ui)
        )
        or True
    )
    app._wg_profile_exists = lambda profile: False
    app._wg_profile_path = lambda profile: f"/etc/wireguard/{profile}.conf"
    app.refresh_wg_profiles = lambda: setattr(app, "wg_profiles", [])
    app.load_vpn_slot_into_form = lambda slot_no: calls.append(("load_form", slot_no))
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")
    app.update_ipv6_controls_state = lambda: calls.append("ipv6")

    def fake_run_cmd(args, timeout=0, text=True):
        run_calls.append(args)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller,
        "get_active_nm_vpn_connections",
        lambda _app: list(active_connections),
    )
    monkeypatch.setattr(netmon.messagebox, "askyesno", lambda *args, **kwargs: True)

    app.delete_selected_vpn_profile()

    assert ("vpn_off", False, False) in calls
    assert not any(args[:4] == ["sudo", "-n", "rm", "-f"] for args in run_calls)
    assert (
        "Löschen abgebrochen: VPN-Verbindung für 'proton' ist noch aktiv: proton"
        in logs
    )


def test_delete_selected_vpn_profile_logs_when_no_profile_is_selected():
    app = netmon.App.__new__(netmon.App)
    logs = []
    app.vpn_profile_var = DummyVar("")
    app.log = logs.append

    app.delete_selected_vpn_profile()

    assert logs == ["Bitte erst ein WireGuard-Profil auswählen."]


def test_delete_selected_vpn_profile_uses_selected_table_row_when_form_is_empty(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    logs = []

    app.vpn_profile_var = DummyVar("")
    app.vpn_table = DummyTable()
    app.vpn_table.rows = {"vpn-slot-2": (2, "Other", "proton", "bereit")}
    app.vpn_table.selected = ("vpn-slot-2",)
    app.log = logs.append
    app.ensure_sudo_session = lambda label: False

    monkeypatch.setattr(netmon.messagebox, "askyesno", lambda *args, **kwargs: True)

    app.delete_selected_vpn_profile()

    assert app.vpn_profile_var.get() == "proton"
    assert logs == []


def test_delete_selected_vpn_profile_removes_files_clears_slots_and_refreshes(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []
    run_calls = []
    reconcile_calls = []

    app.vpn_profile_var = DummyVar("proton")
    app.vpn_slot_choice = DummyVar("1")
    app.vpn_custom_name_var = DummyVar("Keep")
    app.vpn_profile_combo = DummyCombo()
    app.vpn_slots = [
        {"slot": 1, "custom_name": "Work", "profile": "proton"},
        {"slot": 2, "custom_name": "Other", "profile": "wg-b"},
        {"slot": 3, "custom_name": "Legacy", "profile": "proton__ipv4"},
    ]
    app.primary_vpn_slots = [
        {"slot": 1, "custom_name": "Primary", "profile": "proton"},
        {"slot": 2, "custom_name": "Other Primary", "profile": "wg-b"},
    ]
    app.privacy_config = {"vpn_profile": "proton"}
    app.isp_stealth_vpn_profile = DummyVar("proton")
    app.isp_stealth_vpn_choice = DummyVar("Proton")
    app.wg_profiles = ["wg-b"]
    app.log = logs.append
    app.ensure_sudo_session = lambda label: True
    app.active_wg_profile = lambda: "proton"
    active_connections = {"value": ["proton"]}
    exists_state = {"value": {"proton", "proton__ipv4", "wg-b"}}
    app.vpn_off = lambda ensure_sudo=True, refresh_ui=True: (
        calls.append(("vpn_off", ensure_sudo, refresh_ui)),
        active_connections.__setitem__("value", []),
        True,
    )[-1]
    app._wg_profile_exists = lambda profile: profile in exists_state["value"]
    app._wg_profile_path = lambda profile: f"/etc/wireguard/{profile}.conf"
    app.save_vpn_slots_config = lambda: calls.append("save_slots")
    app.save_primary_vpn_slots_config = lambda: calls.append("save_primary_slots")
    app.save_privacy_config = lambda: calls.append("save_privacy")
    app.refresh_wg_profiles = lambda: setattr(
        app,
        "wg_profiles",
        [name for name in ["proton", "wg-b"] if name in exists_state["value"]],
    )
    app.load_vpn_slot_into_form = lambda slot_no: calls.append(("load_form", slot_no))
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")
    app.update_ipv6_controls_state = lambda: calls.append("ipv6")
    app.sync_vpn_profile_form_selection = lambda: calls.append("sync_form")

    profiles_state = [["proton", "wg-b"], ["wg-b"]]
    app._collect_referenced_vpn_profiles = lambda include_active=True: (
        profiles_state.pop(0) if len(profiles_state) > 1 else profiles_state[0]
    )
    app._collect_interface_rules_for_profiles = lambda profiles: (
        {"proton", "proton__ipv4", "wg-b", "wg-b__ipv4"}
        if "proton" in profiles
        else {"wg-b", "wg-b__ipv4"}
    )
    app._collect_endpoint_rules_for_profiles = lambda profiles: (
        {("1.1.1.1", "51820"), ("2.2.2.2", "443")}
        if "proton" in profiles
        else {("2.2.2.2", "443")}
    )
    app._reconcile_vpn_firewall_rules = (
        lambda **kwargs: reconcile_calls.append(
            (
                sorted(kwargs["old_interfaces"]),
                sorted(kwargs["new_interfaces"]),
                sorted(kwargs["old_endpoints"]),
                sorted(kwargs["new_endpoints"]),
                kwargs.get("removed_profile"),
            )
        )
        or True
    )

    def fake_run_cmd(args, timeout=0, text=True):
        run_calls.append(args)
        if args[:4] == ["sudo", "-n", "rm", "-f"]:
            target = args[-1].rsplit("/", 1)[-1].removesuffix(".conf")
            exists_state["value"].discard(target)
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(
        netmon.vpn_controller,
        "get_active_nm_vpn_connections",
        lambda _app: list(active_connections["value"]),
    )
    monkeypatch.setattr(netmon.messagebox, "askyesno", lambda *args, **kwargs: True)

    app.delete_selected_vpn_profile()

    assert calls[0] == ("vpn_off", False, False)
    assert ["sudo", "-n", "rm", "-f", "/etc/wireguard/proton.conf"] in run_calls
    assert ["sudo", "-n", "rm", "-f", "/etc/wireguard/proton__ipv4.conf"] in run_calls
    assert app.vpn_slots[0] == {"slot": 1, "custom_name": "", "profile": ""}
    assert app.vpn_slots[2] == {"slot": 3, "custom_name": "", "profile": ""}
    assert app.vpn_slots[1] == {"slot": 2, "custom_name": "Other", "profile": "wg-b"}
    assert app.primary_vpn_slots[0] == {"slot": 1, "custom_name": "", "profile": ""}
    assert app.primary_vpn_slots[1] == {
        "slot": 2,
        "custom_name": "Other Primary",
        "profile": "wg-b",
    }
    assert app.privacy_config["vpn_profile"] == ""
    assert app.isp_stealth_vpn_profile.get() == ""
    assert app.isp_stealth_vpn_choice.get() == ""
    assert app.vpn_profile_combo["values"] == ["wg-b"]
    assert app.vpn_profile_var.get() == ""
    assert "save_slots" in calls
    assert "save_primary_slots" in calls
    assert "save_privacy" in calls
    assert "sync_form" in calls
    assert ("load_form", 1) in calls
    assert "buttons" in calls
    assert "table" in calls
    assert "ipv6" in calls
    assert "Originalprofil gelöscht: proton" in logs
    assert "Interne IPv4-Kopie gelöscht: proton__ipv4" in logs
    assert "VPN-Slots bereinigt: 2" in logs
    assert "Primäre VPN-Slots bereinigt: 1" in logs
    assert "Privacy-VPN-Profil zurückgesetzt." in logs
    assert "WireGuard-Profil gelöscht: proton" in logs
    assert reconcile_calls == [
        (
            ["proton", "proton__ipv4", "wg-b", "wg-b__ipv4"],
            ["wg-b", "wg-b__ipv4"],
            [("1.1.1.1", "51820"), ("2.2.2.2", "443")],
            [("2.2.2.2", "443")],
            "proton",
        )
    ]


def test_delete_selected_vpn_profile_keeps_profile_visible_when_original_delete_fails(
    monkeypatch,
):
    app = netmon.App.__new__(netmon.App)
    logs = []
    calls = []
    run_calls = []
    reconcile_calls = []

    app.vpn_profile_var = DummyVar("proton")
    app.vpn_slot_choice = DummyVar("1")
    app.vpn_custom_name_var = DummyVar("Keep")
    app.vpn_profile_combo = DummyCombo()
    app.vpn_slots = [{"slot": 1, "custom_name": "Work", "profile": "proton"}]
    app.wg_profiles = ["proton"]
    exists_state = {"value": {"proton", "proton__ipv4"}}
    app.log = logs.append
    app.ensure_sudo_session = lambda label: True
    app.active_wg_profile = lambda: ""
    app.get_wg_interfaces = lambda: []
    app.vpn_off = (
        lambda ensure_sudo=True, refresh_ui=True: calls.append(
            ("vpn_off", ensure_sudo, refresh_ui)
        )
        or True
    )
    app._wg_profile_exists = lambda profile: profile in exists_state["value"]
    app._wg_profile_path = lambda profile: f"/etc/wireguard/{profile}.conf"
    app.save_vpn_slots_config = lambda: calls.append("save_slots")
    app.refresh_wg_profiles = lambda: setattr(
        app,
        "wg_profiles",
        [name for name in ["proton", "wg-b"] if name in exists_state["value"]],
    )
    app.load_vpn_slot_into_form = lambda slot_no: calls.append(("load_form", slot_no))
    app.update_vpn_slot_buttons = lambda: calls.append("buttons")
    app.refresh_vpn_slots_table = lambda: calls.append("table")
    app.update_ipv6_controls_state = lambda: calls.append("ipv6")
    app.sync_vpn_profile_form_selection = lambda: calls.append("sync_form")
    app._collect_referenced_vpn_profiles = lambda include_active=True: ["proton"]
    app._collect_interface_rules_for_profiles = lambda profiles: {
        "proton",
        "proton__ipv4",
    }
    app._collect_endpoint_rules_for_profiles = lambda profiles: {("1.1.1.1", "51820")}
    app._reconcile_vpn_firewall_rules = (
        lambda **kwargs: reconcile_calls.append(kwargs) or True
    )

    def fake_run_cmd(args, timeout=0, text=True):
        run_calls.append(args)
        if args[:4] == ["sudo", "-n", "rm", "-f"] and args[-1].endswith(
            "proton__ipv4.conf"
        ):
            exists_state["value"].discard("proton__ipv4")
        return 0, "ok"

    monkeypatch.setattr(netmon, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.vpn_controller, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(netmon.messagebox, "askyesno", lambda *args, **kwargs: True)

    app.delete_selected_vpn_profile()

    assert ["sudo", "-n", "rm", "-f", "/etc/wireguard/proton.conf"] in run_calls
    assert ["sudo", "-n", "rm", "-f", "/etc/wireguard/proton__ipv4.conf"] in run_calls
    assert app.vpn_slots[0] == {"slot": 1, "custom_name": "Work", "profile": "proton"}
    assert app.vpn_profile_combo["values"] == ["proton"]
    assert app.vpn_profile_var.get() == "proton"
    assert "save_slots" not in calls
    assert ("load_form", 1) not in calls
    assert "sync_form" in calls
    assert (
        "Originalprofil löschen fehlgeschlagen (proton): Datei existiert nach sudo rm weiterhin"
        in logs
    )
    assert "Interne IPv4-Kopie gelöscht: proton__ipv4" in logs
    assert "WireGuard-Profil gelöscht: proton" not in logs
    assert reconcile_calls == []
