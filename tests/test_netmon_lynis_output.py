import pytest
import inspect

from netmon import app as netmon_app
from netmon.features import security_audit_controller
from netmon.ui.tabs import security_tabs


class DummyText:
    def __init__(self):
        self.value = ""
        self.state_changes = []

    def configure(self, **kwargs):
        self.state_changes.append(kwargs)

    def delete(self, *_args):
        self.value = ""

    def insert(self, *_args):
        self.value += _args[-1]

    def see(self, *_args):
        return None

    def index(self, _index):
        return "1.0" if not self.value else "2.0"


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class DummyButton:
    def __init__(self):
        self.last = {}

    def configure(self, **kwargs):
        self.last.update(kwargs)


class DummyTree:
    def __init__(self):
        self.rows = []
        self.selected = ()
        self.tags = {}

    def get_children(self):
        return list(range(len(self.rows)))

    def delete(self, item):
        index = int(item)
        if 0 <= index < len(self.rows):
            self.rows.pop(index)

    def insert(self, _parent, _index, values=(), tags=()):
        self.rows.append({"values": tuple(values), "tags": tuple(tags)})
        return str(len(self.rows) - 1)

    def selection(self):
        return self.selected

    def selection_set(self, item):
        self.selected = (str(item),)

    def index(self, item):
        return int(item)

    def tag_configure(self, tag_name, **kwargs):
        self.tags[tag_name] = kwargs


def test_strip_ansi_codes_removes_escape_sequences():
    raw = "\x1b[1;32mOK\x1b[0m\n\x1b[1;37mNICHT GEFUNDEN\x1b[0m"

    clean = netmon_app.strip_ansi_codes(raw)

    assert clean == "OK\nNICHT GEFUNDEN"


def test_normalize_lynis_output_removes_ansi_and_empty_lines():
    raw = "\x1b[1;32mOK\x1b[0m\n\nWarnung  \n\n"

    clean = netmon_app.normalize_lynis_output(raw)

    assert clean == "OK\nWarnung"


def test_lynis_running_reads_safe_default_state():
    app = type("DummyApp", (), {})()

    assert security_audit_controller._lynis_running(app) is False

    app.lynis_running = True
    assert security_audit_controller._lynis_running(app) is True


def test_lynis_summary_and_start_log_messages_match_modes():
    assert security_audit_controller._lynis_summary_text("quick") == (
        "Schnellaudit wird ausgeführt ..."
    )
    assert security_audit_controller._lynis_summary_text("full") == (
        "Vollständiger Sicherheitsscan wird ausgeführt ..."
    )
    assert security_audit_controller._lynis_start_log_message("quick") == (
        "Lynis Schnellaudit gestartet (ohne root)"
    )
    assert security_audit_controller._lynis_start_log_message("full") == (
        "Lynis Vollscan gestartet (sudo erforderlich)"
    )


def test_lynis_finish_log_message_covers_success_timeout_and_error():
    assert security_audit_controller._lynis_finish_log_message("quick", 0) == (
        "Lynis Schnellaudit abgeschlossen."
    )
    assert security_audit_controller._lynis_finish_log_message("full", 124) == (
        "Lynis Vollscan Timeout (rc=124)."
    )
    assert security_audit_controller._lynis_finish_log_message("full", 7) == (
        "Lynis Vollscan fehlgeschlagen (rc=7)."
    )


def test_lynis_summary_value_reads_colon_and_parenthesized_counts():
    output = "Hardening index : 88\nWarnings (3)\nSuggestions : 12\n"

    assert (
        security_audit_controller._lynis_summary_value(output, "Hardening index")
        == "88"
    )
    assert security_audit_controller._lynis_summary_value(output, "Warnings") == "3"
    assert security_audit_controller._lynis_summary_value(output, "Suggestions") == "12"


def test_lynis_summary_value_returns_dash_for_missing_or_invalid_values():
    assert (
        security_audit_controller._lynis_summary_value(
            "Hardening index : unknown\n", "Hardening index"
        )
        == "-"
    )
    assert (
        security_audit_controller._lynis_summary_value("Suggestions : 2\n", "Warnings")
        == "-"
    )
    assert security_audit_controller._lynis_summary_value("Warnings : 1\n", "") == "-"


def test_build_lynis_tab_attaches_baseline_copy_shortcuts_with_kind():
    source = inspect.getsource(netmon_app.App.build_lynis_tab)
    output_panel_source = inspect.getsource(security_tabs.build_lynis_output_panel)
    game_mode_source = inspect.getsource(netmon_app.App.enable_game_mode)
    game_mode_dialog_source = inspect.getsource(
        netmon_app.App._prompt_game_mode_ufw_exception_sets
    )
    game_mode_confirm_source = inspect.getsource(netmon_app.App.confirm_game_mode_apply)

    assert "lynis_sections = ttk.Notebook(self.tab_lynis)" in source
    assert 'text=self.tr("lynis_subtab_hardening", "Haertung")' in source
    assert (
        'self.attach_selection_copy_shortcuts(self.security_baseline_tree, "treeview")'
        in source
    )
    assert (
        'self.attach_selection_copy_shortcuts(self.security_baseline_detail_text, "text")'
        in source
    )
    assert "command=self.show_security_baseline_list_view" in source
    assert '"baseline_btn_back_to_entries"' in source
    assert '"Zurueck zu den Eintraegen"' in source
    assert "self.security_baseline_list_view = ttk.Frame(baseline_content)" in source
    assert "self.security_baseline_detail_view = ttk.Frame(baseline_content)" in source
    assert 'text=self.tr("baseline_profile_select_label", "Profilauswahl:")' in source
    assert "self.security_baseline_profile_combo = ttk.Combobox(" in source
    assert "self.apply_security_baseline_profile_choice(" in source
    assert "textvariable=self.lynis_hardening_index_var" in source
    assert "build_lynis_output_panel(self, audit_tab)" in source
    assert "textvariable=app.lynis_summary_var" in output_panel_source
    assert "app.lynis_text = tk.Text(" in output_panel_source
    assert "textvariable=self.security_baseline_transfer_var" in source
    assert "command=self.check_security_baseline_privileges" in source
    assert "command=self.apply_security_baseline_profile" in source
    assert "command=self.launch_timeshift_snapshot_tool" in source
    assert "command=self.apply_security_baseline_sysctl" in source
    assert "command=self.apply_security_baseline_ufw" in source
    assert "command=self.export_security_baseline_transfer" in source
    assert "command=self.import_security_baseline_transfer" in source
    assert "command=self.show_security_baseline_transfer_package" in source
    assert "command=self.show_security_baseline_transfer_comparison" in source
    assert "command=self.clear_security_baseline_transfer" in source
    assert "command=self.enable_game_mode" in source
    assert "command=self.disable_game_mode" in source
    assert "self.security_game_mode_preset_combo = ttk.Combobox(" in source
    assert "textvariable=self.security_game_mode_profile_hint_var" in source
    assert 'self._game_mode_preset_label("steam")' in source
    assert 'self._game_mode_preset_label("heroic")' in source
    assert 'self._game_mode_preset_label("lutris")' in source
    assert 'self._game_mode_preset_label("minecraft_lan")' in source
    assert "for column in range(4)" in source
    assert '"baseline_hardening_timeshift_hint"' in source
    assert "textvariable=self.security_baseline_optional_services_var" in source
    assert "textvariable=self.security_game_mode_status_var" in source
    assert "def confirm_game_mode_apply(" in game_mode_confirm_source
    assert "_prompt_game_mode_ufw_exception_sets(" in game_mode_source
    assert "self.confirm_game_mode_apply(" in game_mode_source
    assert '"game_mode_ufw_exceptions_prompt"' in game_mode_dialog_source
    assert '"game_mode_custom_host_port_title"' in game_mode_dialog_source


def test_right_quick_actions_source_contains_existing_setup_commands():
    with open("netmon/app.py", "r", encoding="utf-8") as handle:
        source = handle.read()

    assert 'text=self.tr("group_right_quick_actions", "Schnellzugriff")' in source
    assert "command=self.run_apt_update_in_terminal" in source
    assert "command=self.run_apt_upgrade_in_terminal" in source
    assert "command=self.reset_network_stack" in source
    assert "command=self.run_apt_autoremove_in_terminal" in source
    assert "command=self.restart_netmon_only" in source
    assert "command=self.run_menu_refresh_in_terminal" in source


def test_refresh_game_mode_status_updates_text_and_buttons():
    app = netmon_app.App.__new__(netmon_app.App)
    app.settings = {"security_game_mode_preset": "online"}
    app.security_game_mode_status_var = DummyVar("")
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.l_game_mode = object()
    seen = []
    app.set_light = lambda light, color: seen.append((light, color))
    app.game_mode_state = {
        "active": True,
        "preset_id": "online",
        "dns_guard_paused": True,
        "killswitch_paused": True,
        "ufw_logging_lowered": True,
        "dot_active": True,
        "vpn_active": False,
    }

    text = app.refresh_game_mode_status()

    assert "Spielmodus: aktiv" in text
    assert "DNS Guard pausiert" in text
    assert "Killswitch pausiert" in text
    assert "UFW Logging LOW" in text
    assert "DoT unveraendert" in text
    assert seen == [(app.l_game_mode, "green")]
    assert app.btn_security_game_mode_on.last["state"] == "disabled"
    assert app.btn_security_game_mode_off.last["state"] == "normal"


def test_enable_game_mode_with_preset_updates_selection_and_activates():
    app = netmon_app.App.__new__(netmon_app.App)
    app.settings = {"security_game_mode_preset": "online"}
    app.security_game_mode_preset_var = DummyVar("Online")
    app.security_game_mode_status_var = DummyVar("")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.game_mode_state = {}
    app.save_settings = lambda **_kwargs: None
    app.log_safe = lambda _msg: None
    app.refresh_game_mode_status = lambda: None
    app.enable_game_mode = lambda: True

    result = app.enable_game_mode_with_preset("steam")

    assert result is True
    assert app.settings["security_game_mode_preset"] == "steam"
    assert app.security_game_mode_preset_var.get() == "Steam"


def test_enable_game_mode_with_preset_switches_active_profile(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.settings = {"security_game_mode_preset": "online"}
    app.security_game_mode_preset_var = DummyVar("Online")
    app.security_game_mode_status_var = DummyVar("")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.game_mode_state = {"active": True, "preset_id": "online"}
    app.save_settings = lambda **_kwargs: None
    app.log_safe = lambda _msg: None
    app.refresh_game_mode_status = lambda: None
    seen = {"disable": 0, "enable": 0}
    app.disable_game_mode = (
        lambda: seen.__setitem__("disable", seen["disable"] + 1) or True
    )
    app.enable_game_mode = (
        lambda: seen.__setitem__("enable", seen["enable"] + 1) or True
    )

    result = app.enable_game_mode_with_preset("lutris")

    assert result is True
    assert seen == {"disable": 1, "enable": 1}
    assert app.settings["security_game_mode_preset"] == "lutris"
    assert app.security_game_mode_preset_var.get() == "Lutris"


def test_enable_game_mode_pauses_dns_guard_and_reduces_security_enforcement(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    seen = {"sudo": 0, "killswitch_off": 0, "ufw_logging": []}
    app.settings = {"security_game_mode_preset": "online"}
    app.tr = lambda _key, fallback, **_kwargs: fallback
    app.log_safe = logs.append
    app.security_game_mode_preset_var = DummyVar("Online")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.security_game_mode_status_var = DummyVar("")
    app.dns_guard_enabled_var = DummyVar(True)
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.ensure_sudo_session = (
        lambda _reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )
    app.killswitch_is_on = lambda: True
    app.killswitch_off = (
        lambda **_kwargs: seen.__setitem__("killswitch_off", seen["killswitch_off"] + 1)
        or True
    )
    app._security_query_log_level = lambda: "HIGH"
    app._set_ufw_logging_sync = (
        lambda level, **_kwargs: seen["ufw_logging"].append(level) or True
    )
    app.is_dot_active = lambda: True
    app.is_vpn_active = lambda: False
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None
    app.run_dns_guard_check_once = lambda: None
    app.update_dns_guard_indicator = lambda: None
    monkeypatch.setattr(netmon_app.messagebox, "askyesno", lambda *args, **kwargs: True)

    result = app.enable_game_mode()

    assert result is True
    assert seen["sudo"] == 1
    assert seen["killswitch_off"] == 0
    assert seen["ufw_logging"] == ["low"]
    assert app.dns_guard_enabled_var.get() is False
    assert app.game_mode_state["active"] is True
    assert app.game_mode_state["killswitch_paused"] is False
    assert app.game_mode_state["ufw_logging_lowered"] is True
    assert app.game_mode_state["preset_id"] == "online"
    assert "Spielmodus aktiviert." in logs


def test_enable_game_mode_singleplayer_keeps_dns_guard_and_killswitch(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    seen = {"sudo": 0, "killswitch_off": 0, "ufw_logging": []}
    app.settings = {"security_game_mode_preset": "singleplayer"}
    app.tr = lambda _key, fallback, **_kwargs: fallback
    app.log_safe = logs.append
    app.security_game_mode_preset_var = DummyVar("Singleplayer")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.security_game_mode_status_var = DummyVar("")
    app.dns_guard_enabled_var = DummyVar(True)
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.ensure_sudo_session = (
        lambda _reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )
    app.killswitch_is_on = lambda: True
    app.killswitch_off = (
        lambda **_kwargs: seen.__setitem__("killswitch_off", seen["killswitch_off"] + 1)
        or True
    )
    app._security_query_log_level = lambda: "HIGH"
    app._set_ufw_logging_sync = (
        lambda level, **_kwargs: seen["ufw_logging"].append(level) or True
    )
    app.is_dot_active = lambda: False
    app.is_vpn_active = lambda: False
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None
    app.run_dns_guard_check_once = lambda: None
    app.update_dns_guard_indicator = lambda: None
    monkeypatch.setattr(netmon_app.messagebox, "askyesno", lambda *args, **kwargs: True)

    result = app.enable_game_mode()

    assert result is True
    assert seen["sudo"] == 1
    assert seen["killswitch_off"] == 0
    assert seen["ufw_logging"] == ["low"]
    assert app.dns_guard_enabled_var.get() is True
    assert app.game_mode_state["dns_guard_paused"] is False
    assert app.game_mode_state["killswitch_paused"] is False
    assert app.game_mode_state["preset_id"] == "singleplayer"
    assert "Spielmodus aktiviert." in logs


def test_game_mode_preset_label_selection_maps_to_internal_id():
    app = netmon_app.App.__new__(netmon_app.App)
    app.settings = {"security_game_mode_preset": "online"}
    app.security_game_mode_preset_var = DummyVar("Steam")

    preset = app._active_game_mode_preset()

    assert preset["id"] == "steam"
    assert preset["label"] == "Steam"


def test_build_custom_game_mode_exception_set_builds_incoming_rules():
    app = netmon_app.App.__new__(netmon_app.App)

    result = app._build_custom_game_mode_exception_set("25565", "TCP + UDP")

    assert result["label"] == "Benutzerdefinierter Host-Port 25565"
    assert result["rules"] == [
        {
            "type": "standard_port",
            "direction": "in",
            "port": "25565",
            "proto": "tcp",
            "label": "Host-Port 25565/tcp",
        },
        {
            "type": "standard_port",
            "direction": "in",
            "port": "25565",
            "proto": "udp",
            "label": "Host-Port 25565/udp",
        },
    ]


def test_build_custom_game_mode_exception_set_includes_custom_label():
    app = netmon_app.App.__new__(netmon_app.App)

    result = app._build_custom_game_mode_exception_set(
        "27015",
        "TCP",
        "Valheim Host",
    )

    assert result["label"] == "Benutzerdefinierter Host-Port 27015 (Valheim Host)"
    assert result["rules"] == [
        {
            "type": "standard_port",
            "direction": "in",
            "port": "27015",
            "proto": "tcp",
            "label": "Host-Port 27015/tcp (Valheim Host)",
        }
    ]


def test_build_custom_game_mode_exception_set_rejects_invalid_port():
    app = netmon_app.App.__new__(netmon_app.App)

    assert app._build_custom_game_mode_exception_set("0", "TCP") is None
    assert app._build_custom_game_mode_exception_set("70000", "TCP") is None
    assert app._build_custom_game_mode_exception_set("abc", "UDP") is None


def test_enable_game_mode_steam_remote_play_applies_optional_ufw_exception_sets(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    seen = {"sudo": 0, "killswitch_off": 0, "ufw_logging": [], "ufw_rules": None}
    app.settings = {"security_game_mode_preset": "steam_remote_play"}
    app.tr = lambda _key, fallback, **_kwargs: fallback
    app.log_safe = logs.append
    app.security_game_mode_preset_var = DummyVar("Steam Remote Play")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.security_game_mode_status_var = DummyVar("")
    app.dns_guard_enabled_var = DummyVar(True)
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.ensure_sudo_session = (
        lambda _reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )
    app.killswitch_is_on = lambda: True
    app.killswitch_off = (
        lambda **_kwargs: seen.__setitem__("killswitch_off", seen["killswitch_off"] + 1)
        or True
    )
    app._security_query_log_level = lambda: "HIGH"
    app._set_ufw_logging_sync = (
        lambda level, **_kwargs: seen["ufw_logging"].append(level) or True
    )
    app._apply_game_mode_ufw_exception_rules = lambda rules: seen.__setitem__(
        "ufw_rules", list(rules)
    ) or (
        True,
        [{"direction": "out", "port": "5353", "proto": "udp"}],
        "",
    )
    app.is_dot_active = lambda: False
    app.is_vpn_active = lambda: False
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None
    app.run_dns_guard_check_once = lambda: None
    app.update_dns_guard_indicator = lambda: None
    monkeypatch.setattr(
        netmon_app.messagebox,
        "askyesno",
        lambda *args, **kwargs: True,
    )

    result = app.enable_game_mode()

    assert result is True
    assert seen["sudo"] == 1
    assert seen["killswitch_off"] == 1
    assert seen["ufw_logging"] == ["low"]
    assert isinstance(seen["ufw_rules"], list)
    assert len(seen["ufw_rules"]) >= 10
    assert "LAN Discovery" in app.game_mode_state["ufw_exception_sets"]
    assert "Steam Remote Play (Outbound)" in app.game_mode_state["ufw_exception_sets"]
    assert "Spielmodus aktiviert." in logs


def test_enable_game_mode_minecraft_lan_uses_lan_discovery_set(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    seen = {"sudo": 0, "killswitch_off": 0, "ufw_logging": [], "ufw_rules": None}
    app.settings = {"security_game_mode_preset": "minecraft_lan"}
    app.tr = lambda _key, fallback, **_kwargs: fallback
    app.log_safe = logs.append
    app.security_game_mode_preset_var = DummyVar("Minecraft LAN")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.security_game_mode_status_var = DummyVar("")
    app.dns_guard_enabled_var = DummyVar(True)
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.ensure_sudo_session = (
        lambda _reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )
    app.killswitch_is_on = lambda: True
    app.killswitch_off = (
        lambda **_kwargs: seen.__setitem__("killswitch_off", seen["killswitch_off"] + 1)
        or True
    )
    app._security_query_log_level = lambda: "HIGH"
    app._set_ufw_logging_sync = (
        lambda level, **_kwargs: seen["ufw_logging"].append(level) or True
    )
    app._apply_game_mode_ufw_exception_rules = lambda rules: seen.__setitem__(
        "ufw_rules", list(rules)
    ) or (True, [{"direction": "out", "port": "5353", "proto": "udp"}], "")
    app.is_dot_active = lambda: False
    app.is_vpn_active = lambda: False
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None
    app.run_dns_guard_check_once = lambda: None
    app.update_dns_guard_indicator = lambda: None
    monkeypatch.setattr(
        netmon_app.messagebox,
        "askyesno",
        lambda *args, **kwargs: True,
    )

    result = app.enable_game_mode()

    assert result is True
    assert seen["sudo"] == 1
    assert seen["killswitch_off"] == 1
    assert seen["ufw_logging"] == ["low"]
    assert seen["ufw_rules"] == [
        {
            "type": "standard_port",
            "direction": "out",
            "port": "5353",
            "proto": "udp",
            "label": "mDNS ausgehend",
        },
        {
            "type": "standard_port",
            "direction": "out",
            "port": "1900",
            "proto": "udp",
            "label": "SSDP ausgehend",
        },
    ]
    assert app.game_mode_state["preset_id"] == "minecraft_lan"
    assert app.game_mode_state["ufw_exception_sets"] == ["LAN Discovery"]
    assert "Spielmodus aktiviert." in logs


def test_enable_game_mode_aborts_when_exception_dialog_is_cancelled(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    seen = {"sudo": 0}
    app.settings = {"security_game_mode_preset": "minecraft_lan"}
    app.tr = lambda _key, fallback, **_kwargs: fallback
    app.log_safe = logs.append
    app.security_game_mode_preset_var = DummyVar("Minecraft LAN")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.security_game_mode_status_var = DummyVar("")
    app.dns_guard_enabled_var = DummyVar(True)
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.ensure_sudo_session = (
        lambda _reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )
    app.killswitch_is_on = lambda: True
    app._security_query_log_level = lambda: "HIGH"
    app.is_dot_active = lambda: False
    app.is_vpn_active = lambda: False
    app._prompt_game_mode_ufw_exception_sets = lambda **_kwargs: None
    monkeypatch.setattr(
        netmon_app.messagebox,
        "askyesno",
        lambda *args, **kwargs: True,
    )

    result = app.enable_game_mode()

    assert result is False
    assert seen["sudo"] == 0
    assert app.__dict__.get("game_mode_state", {}) == {}
    assert "Spielmodus abgebrochen: UFW-Ausnahmendialog geschlossen." in logs


def test_disable_game_mode_rolls_back_optional_ufw_exception_rules():
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    seen = {"sudo": 0, "killswitch_on": 0, "ufw_logging": [], "rollback_rules": None}
    app.settings = {"security_game_mode_preset": "steam_remote_play"}
    app.tr = lambda _key, fallback, **_kwargs: fallback
    app.log_safe = logs.append
    app.security_game_mode_preset_var = DummyVar("Steam Remote Play")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.security_game_mode_status_var = DummyVar("")
    app.dns_guard_enabled_var = DummyVar(False)
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.ensure_sudo_session = (
        lambda _reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )
    app.killswitch_is_on = lambda: False
    app.killswitch_on = (
        lambda **_kwargs: seen.__setitem__("killswitch_on", seen["killswitch_on"] + 1)
        or True
    )
    app._set_ufw_logging_sync = (
        lambda level, **_kwargs: seen["ufw_logging"].append(level) or True
    )
    app._rollback_game_mode_ufw_exception_rules = lambda rules: seen.__setitem__(
        "rollback_rules", list(rules)
    ) or (True, [])
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None
    app.run_dns_guard_check_once = lambda: None
    app.update_dns_guard_indicator = lambda: None
    app.game_mode_state = {
        "active": True,
        "preset_id": "steam_remote_play",
        "dns_guard_enabled": True,
        "killswitch_was_on": True,
        "killswitch_paused": True,
        "ufw_logging_level": "HIGH",
        "ufw_logging_lowered": True,
        "ufw_exception_sets": ["LAN Discovery"],
        "ufw_exception_rules_added": [
            {
                "direction": "out",
                "port": "5353",
                "proto": "udp",
                "type": "standard_port",
            }
        ],
    }

    result = app.disable_game_mode()

    assert result is True
    assert seen["sudo"] == 1
    assert seen["killswitch_on"] == 1
    assert seen["ufw_logging"] == ["high"]
    assert seen["rollback_rules"] == [
        {"direction": "out", "port": "5353", "proto": "udp", "type": "standard_port"}
    ]
    assert app.game_mode_state == {}
    assert "Spielmodus deaktiviert und vorheriger Zustand wiederhergestellt." in logs


def test_disable_game_mode_restores_previous_state():
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    seen = {"sudo": 0, "killswitch_on": 0, "ufw_logging": []}
    app.settings = {"security_game_mode_preset": "online"}
    app.tr = lambda _key, fallback, **_kwargs: fallback
    app.log_safe = logs.append
    app.security_game_mode_preset_var = DummyVar("Online")
    app.security_game_mode_profile_hint_var = DummyVar("")
    app.security_game_mode_status_var = DummyVar("")
    app.dns_guard_enabled_var = DummyVar(False)
    app.btn_security_game_mode_on = DummyButton()
    app.btn_security_game_mode_off = DummyButton()
    app.ensure_sudo_session = (
        lambda _reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )
    app.killswitch_is_on = lambda: False
    app.killswitch_on = (
        lambda **_kwargs: seen.__setitem__("killswitch_on", seen["killswitch_on"] + 1)
        or True
    )
    app._set_ufw_logging_sync = (
        lambda level, **_kwargs: seen["ufw_logging"].append(level) or True
    )
    app.refresh_dns_policy_status = lambda: None
    app.update_dns_controls_state_safe = lambda: None
    app.run_dns_guard_check_once = lambda: None
    app.update_dns_guard_indicator = lambda: None
    app.game_mode_state = {
        "active": True,
        "dns_guard_enabled": True,
        "killswitch_was_on": True,
        "killswitch_paused": True,
        "ufw_logging_level": "HIGH",
        "ufw_logging_lowered": True,
    }

    result = app.disable_game_mode()

    assert result is True
    assert seen["sudo"] == 1
    assert seen["killswitch_on"] == 1
    assert seen["ufw_logging"] == ["high"]
    assert app.dns_guard_enabled_var.get() is True
    assert app.game_mode_state == {}
    assert "Spielmodus deaktiviert und vorheriger Zustand wiederhergestellt." in logs


def test_ampel_source_contains_capture_light_and_navigation():
    with open("netmon/app.py", "r", encoding="utf-8") as handle:
        source = handle.read()

    assert 'self.l_capture = self.make_light(amp_extra, "Capture")' in source
    assert 'self._bind_light_click(self.l_capture, "capture")' in source
    assert "lambda e: self.show_capture_menu(e)" in source
    assert "def show_capture_menu(self, event):" in source
    assert 'label="Capture starten"' in source
    assert 'label="Capture stoppen"' in source
    assert 'label="In Wireshark öffnen"' in source
    assert 'elif key == "capture":' in source
    assert 'elif normalized in {"capture", "packet_capture"}:' in source


def test_ampel_source_contains_game_mode_light_and_navigation():
    with open("netmon/app.py", "r", encoding="utf-8") as handle:
        source = handle.read()

    assert 'self.l_game_mode = self.make_light(amp_extra, "Spielmodus")' in source
    assert 'self._bind_light_click(self.l_game_mode, "game_mode")' in source
    assert "lambda e: self.show_game_mode_menu(e)" in source
    assert "def show_game_mode_menu(self, event):" in source
    assert "label=self._game_mode_preset_label(preset_id)" in source
    assert "self.enable_game_mode_with_preset(selected_preset)" in source
    assert 'label="Spielemodus deaktivieren"' in source
    assert "def enable_game_mode_with_preset(self, preset_id):" in source
    assert 'elif key == "game_mode":' in source
    assert 'elif normalized == "game_mode":' in source


def test_check_security_baseline_privileges_reports_missing_privileged_session(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    logs = []
    app.log_safe = logs.append

    monkeypatch.setattr(
        security_audit_controller,
        "_detect_hardening_privilege_context",
        lambda _app=None: {
            "is_root": False,
            "has_sudo_session": False,
            "pkexec_authorized": False,
            "root_available": False,
            "source": "keine privilegierte Session",
        },
    )
    monkeypatch.setattr(
        security_audit_controller,
        "_baseline_checks",
        lambda _app=None: [
            {"title": "UFW aktiv", "requires_root_read": True},
            {"title": "Keine Konten ohne Passwort", "requires_root_read": True},
            {"title": "kernel.sysrq", "requires_root_read": False},
        ],
    )
    seen = {}

    result = security_audit_controller.check_security_baseline_privileges(
        app,
        showinfo_fn=lambda title, text, parent=None: seen.update(
            {"title": title, "text": text, "parent": parent}
        ),
    )

    assert result["root_context"]["root_available"] is False
    assert len(result["root_checks"]) == 2
    assert seen["title"] == "Root-Check fuer Baseline"
    assert "Root-Lesechecks verfuegbar: Nein" in seen["text"]
    assert "UFW aktiv" in seen["text"]
    assert "Keine Konten ohne Passwort" in seen["text"]
    assert seen["parent"] is app
    assert "root_available=False" in logs[-1]


def test_extract_lynis_issues_and_recommendations_filters_relevant_lines():
    app = netmon_app.App.__new__(netmon_app.App)
    raw = (
        "\x1b[1;32m[ OK ] Service gefunden\x1b[0m\n"
        "Warning: Firewall disabled\n"
        "Suggestion: Enable auditd\n"
        "Hardening index : 72\n"
        "Dateien gefunden: 3 verdächtige Dateien\n"
    )

    filtered = app.extract_lynis_issues_and_recommendations(raw)

    assert "Warning: Firewall disabled" in filtered
    assert "Suggestion: Enable auditd" in filtered
    assert "Hardening index : 72" in filtered
    assert "Dateien gefunden: 3 verdächtige Dateien" in filtered
    assert "[ OK ] Service gefunden" not in filtered


def test_lynis_issue_line_relevance_keeps_warning_suggestion_and_hardening():
    assert security_audit_controller._lynis_issue_line_is_relevant(
        "Warning: Firewall disabled"
    )
    assert security_audit_controller._lynis_issue_line_is_relevant(
        "Suggestion: Enable auditd"
    )
    assert security_audit_controller._lynis_issue_line_is_relevant(
        "Hardening index : 72"
    )


def test_lynis_issue_line_relevance_skips_generic_found_line():
    assert (
        security_audit_controller._lynis_issue_line_is_relevant(
            "[ OK ] Service gefunden"
        )
        is False
    )
    assert security_audit_controller._lynis_issue_line_is_relevant(
        "Dateien gefunden: 3 verdächtige Dateien"
    )


def test_lynis_relevant_issue_lines_preserves_order_and_line_text():
    lines = security_audit_controller._lynis_relevant_issue_lines(
        "[ OK ] Service gefunden\n"
        "Warning: Firewall disabled\n"
        "Suggestion: Enable auditd\n"
    )

    assert lines == ["Warning: Firewall disabled", "Suggestion: Enable auditd"]


def test_show_lynis_issues_only_updates_text_widget():
    app = netmon_app.App.__new__(netmon_app.App)
    app.lynis_last_output = "Warning: Firewall disabled\nOK"
    app.lynis_text = DummyText()
    app.log_messages = []
    app.log = app.log_messages.append

    app.show_lynis_issues_only()

    assert "Warning: Firewall disabled" in app.lynis_text.value
    assert "=== Lynis Probleme & Empfehlungen ===" in app.lynis_text.value


def test_show_lynis_full_output_restores_clean_output():
    app = netmon_app.App.__new__(netmon_app.App)
    app.lynis_last_output = "Warning: Firewall disabled\nSuggestion: Enable auditd"
    app.lynis_text = DummyText()

    app.show_lynis_full_output()

    assert app.lynis_text.value == app.lynis_last_output


def test_launch_timeshift_snapshot_tool_starts_launcher(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    app.tr = lambda _key, fallback: fallback
    app.log_safe = logs.append

    monkeypatch.setattr(
        netmon_app,
        "get_cmd_path",
        lambda name: "/usr/bin/timeshift-gtk" if name == "timeshift-gtk" else "",
    )
    launched = []
    monkeypatch.setattr(
        netmon_app.subprocess,
        "Popen",
        lambda cmd, stdout=None, stderr=None, start_new_session=None: launched.append(
            (cmd, start_new_session)
        ),
    )

    ok = app.launch_timeshift_snapshot_tool()

    assert ok is True
    assert launched == [(["timeshift-gtk"], True)]
    assert "Timeshift gestartet" in logs[-1]


def test_launch_timeshift_snapshot_tool_shows_info_when_missing(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []
    app.tr = lambda _key, fallback: fallback
    app.log_safe = logs.append

    monkeypatch.setattr(netmon_app, "get_cmd_path", lambda _name: "")
    seen = {"info": 0}
    monkeypatch.setattr(
        netmon_app.messagebox,
        "showinfo",
        lambda *args, **kwargs: seen.__setitem__("info", seen["info"] + 1),
    )

    ok = app.launch_timeshift_snapshot_tool()

    assert ok is False
    assert seen["info"] == 1
    assert "Timeshift-Launcher nicht gefunden" in logs[-1]


def test_check_timeshift_backup_status_reports_result(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.backup_timeshift_status_var = DummyVar()
    app.backup_last_snapshot_var = DummyVar()
    app.backup_root_status_var = DummyVar()
    app.backup_status_var = DummyVar()
    logs = []
    app.log_safe = logs.append

    def fake_refresh():
        app.backup_timeshift_status_var.set("Timeshift: nicht installiert")
        app.backup_last_snapshot_var.set("Letzter Snapshot: nicht erkannt")
        app.backup_root_status_var.set("Root: aktuell nicht aktiv")
        return True

    app.refresh_backup_overview = fake_refresh
    messages = []
    monkeypatch.setattr(
        netmon_app.messagebox,
        "showinfo",
        lambda title, message, parent=None: messages.append((title, message, parent)),
    )

    ok = app.check_timeshift_backup_status()

    assert ok is True
    assert app.backup_status_var.get() == (
        "Timeshift-Pruefung: Timeshift: nicht installiert"
    )
    assert "Timeshift-Pruefung im Backup-Tab" in logs[-1]
    assert messages[0][0] == "Timeshift pruefen"
    assert "Letzter Snapshot: nicht erkannt" in messages[0][1]


def test_build_settings_backup_tab_wires_timeshift_check_button():
    source = inspect.getsource(netmon_app.App._build_settings_backup_tab)

    assert '"backup_btn_check_timeshift"' in source
    assert "command=self.check_timeshift_backup_status" in source
    assert "btn_backup_timeshift_snapshots" not in source
    assert "btn_backup_timeshift_restore" not in source


def test_refresh_timeshift_launch_controls_disables_button_when_launcher_missing(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    app.btn_security_baseline_timeshift = DummyButton()

    monkeypatch.setattr(netmon_app, "get_cmd_path", lambda _name: "")

    app.refresh_timeshift_launch_controls()

    assert app.btn_security_baseline_timeshift.last["state"] == "disabled"


def test_refresh_timeshift_launch_controls_enables_button_when_launcher_exists(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    app.btn_security_baseline_timeshift = DummyButton()

    monkeypatch.setattr(
        netmon_app,
        "get_cmd_path",
        lambda name: (
            "/usr/bin/timeshift-launcher" if name == "timeshift-launcher" else ""
        ),
    )

    app.refresh_timeshift_launch_controls()

    assert app.btn_security_baseline_timeshift.last["state"] == "normal"


def test_security_baseline_transfer_directory_creates_configured_documents_folder(
    tmp_path,
):
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_transfer_dir = str(tmp_path / "Transferpakete")

    path = app._security_baseline_transfer_directory()

    assert path == str(tmp_path / "Transferpakete")
    assert (tmp_path / "Transferpakete").is_dir()


def test_transfer_dialogs_use_dedicated_documents_folder(monkeypatch, tmp_path):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_transfer_dir = str(tmp_path / "Transferpakete")

    seen = {}
    monkeypatch.setattr(
        security_audit_controller,
        "default_security_baseline_transfer_filename",
        lambda _app: "transfer.json",
    )
    monkeypatch.setattr(
        netmon_app.filedialog,
        "asksaveasfilename",
        lambda **kwargs: (seen.__setitem__("export", kwargs), "")[1],
    )
    monkeypatch.setattr(
        netmon_app.filedialog,
        "askopenfilename",
        lambda **kwargs: (seen.__setitem__("import", kwargs), "")[1],
    )

    assert app.export_security_baseline_transfer() is False
    assert app.import_security_baseline_transfer() is False
    assert seen["export"]["initialdir"] == str(tmp_path / "Transferpakete")
    assert seen["import"]["initialdir"] == str(tmp_path / "Transferpakete")
    assert (tmp_path / "Transferpakete").is_dir()


def test_finish_lynis_audit_stores_clean_output_and_updates_summary():
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []

    app.lynis_status_var = DummyVar()
    app.lynis_hardening_index_var = DummyVar()
    app.lynis_summary_var = DummyVar()
    app.dep_status = {"lynis": True}
    app.btn_lynis_quick = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()
    app.btn_lynis_full = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()
    app.update_lynis_output_calls = []
    app.update_lynis_output = (
        lambda text, append=False: app.update_lynis_output_calls.append((text, append))
    )
    app.log = logs.append

    app._finish_lynis_audit(
        0,
        "\x1b[1;32mWarning\x1b[0m\n\nSuggestions : 2\nHardening index : 88",
    )

    assert app.lynis_last_output == "Warning\nSuggestions : 2\nHardening index : 88"
    assert app.update_lynis_output_calls[0][0] == app.lynis_last_output
    assert app.lynis_status_var.get() == "abgeschlossen"
    assert app.lynis_hardening_index_var.get() == "Hardening Index: 88"
    assert app.lynis_last_result["suggestions"] == "2"
    assert app.lynis_last_result["hardening_index"] == "88"
    assert logs[-1] == "Lynis Schnellaudit abgeschlossen."


def test_run_security_baseline_checks_evaluates_special_cases(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_var = DummyVar()
    app.security_baseline_version_var = DummyVar()
    app.security_baseline_reference_var = DummyVar()
    app.security_baseline_date_var = DummyVar()
    app.security_baseline_last_check_var = DummyVar()
    app.security_baseline_status_var = DummyVar()
    app.security_baseline_lynis_summary_var = DummyVar()
    app.security_baseline_tree = DummyTree()
    app.security_baseline_detail_text = DummyText()
    app.lynis_last_result = {
        "hardening_index": "77",
        "warnings": "0",
        "tests": "248",
    }
    app.lynis_last_output = "Warning: Firewall disabled\nSuggestion: Enable AppArmor\nSecure Boot disabled\nrp_filter differs"
    app.logs = []
    app.log_safe = app.logs.append
    saved = {"count": 0}
    app._save_security_baseline = lambda: saved.__setitem__("count", saved["count"] + 1)
    home_command = _home_permissions_spec()["command"]
    apt_command = _apt_upgradable_spec()["command"]

    command_map = {
        "test -d /sys/firmware/efi && echo ja || echo nein": (0, "ja"),
        "grep -E 'password|pbkdf2' /boot/grub/grub.cfg >/dev/null 2>&1 && echo ja || echo nein": (
            0,
            "ja",
        ),
        "LANG=C LC_ALL=C mokutil --sb-state": (
            0,
            "SecureBoot disabled\nPlatform is in Setup Mode",
        ),
        "dpkg-query -W -f='${Status}' ufw 2>/dev/null": (0, "install ok installed"),
        "LANG=C LC_ALL=C ufw status": (0, "Status: active"),
        "LANG=C LC_ALL=C ufw status numbered": (
            0,
            "Status: active\n[ 1] 22/tcp ALLOW IN Anywhere",
        ),
        "dpkg-query -W -f='${Status}' fail2ban 2>/dev/null": (
            0,
            "install ok installed",
        ),
        "systemctl is-active fail2ban": (0, "active"),
        "test -f /etc/fail2ban/jail.local && echo ja || echo nein": (0, "ja"),
        "dpkg-query -W -f='${Status}' lynis 2>/dev/null": (0, "install ok installed"),
        "dpkg-query -W -f='${Status}' rkhunter 2>/dev/null": (
            0,
            "install ok installed",
        ),
        "dpkg-query -W -f='${Status}' clamav 2>/dev/null": (0, "install ok installed"),
        "dpkg-query -W -f='${Status}' apt-listchanges 2>/dev/null": (
            0,
            "install ok installed",
        ),
        "dpkg-query -W -f='${Status}' needrestart 2>/dev/null": (
            0,
            "install ok installed",
        ),
        "dpkg-query -W -f='${Status}' libpam-tmpdir 2>/dev/null": (
            0,
            "install ok installed",
        ),
        "dpkg-query -W -f='${Status}' debsums 2>/dev/null": (1, ""),
        "aa-status --enabled": (0, ""),
        "grep -RHE '^[[:space:]]*(UMASK|umask)[[:space:]]+[0-7]{3,4}([[:space:]]|$)' /etc/login.defs /etc/profile /etc/profile.d 2>/dev/null": (
            0,
            "/etc/login.defs:UMASK 027",
        ),
        "grep -R 'pam_pwquality\\|pam_cracklib' /etc/pam.d 2>/dev/null": (
            0,
            "pam_pwquality.so",
        ),
        "awk -F: '($2==\"\"){count++} END {print count+0}' /etc/shadow 2>/dev/null": (
            0,
            "0",
        ),
        "python3 - <<'PY'\nimport collections\nuid=collections.Counter()\ngid=collections.Counter()\nwith open('/etc/passwd', encoding='utf-8', errors='replace') as handle:\n    for line in handle:\n        parts=line.rstrip('\\n').split(':')\n        if len(parts) > 3:\n            uid[parts[2]] += 1\nwith open('/etc/group', encoding='utf-8', errors='replace') as handle:\n    for line in handle:\n        parts=line.rstrip('\\n').split(':')\n        if len(parts) > 2:\n            gid[parts[2]] += 1\nprint(sum(1 for value in uid.values() if value > 1) + sum(1 for value in gid.values() if value > 1))\nPY": (
            0,
            "0",
        ),
        home_command: (
            0,
            "750 happy happy /home/happy",
        ),
        "dpkg -l 2>/dev/null | awk '/^rc/ {count++} END {print count+0}'": (0, "2"),
        "stat -c '%a %U %G %n' /etc/passwd /etc/shadow /etc/sudoers 2>/dev/null": (
            0,
            "644 root root /etc/passwd\n640 root shadow /etc/shadow\n440 root root /etc/sudoers",
        ),
        apt_command: (
            0,
            "Listing...\ncurl/jammy-updates 7.81.0-1ubuntu1.21 amd64 [upgradable from: 7.81.0-1ubuntu1.20]",
        ),
        "sysctl -n kernel.kptr_restrict": (0, "2"),
        "sysctl -n kernel.sysrq": (0, "0"),
        "sysctl -n kernel.perf_event_paranoid": (0, "3"),
        "sysctl -n kernel.unprivileged_bpf_disabled": (0, "1"),
        "sysctl -n fs.protected_fifos": (0, "2"),
        "sysctl -n net.ipv4.conf.all.log_martians": (0, "1"),
        "sysctl -n net.ipv4.conf.default.log_martians": (0, "1"),
        "sysctl -n net.ipv4.conf.default.accept_source_route": (0, "0"),
        "sysctl -n net.ipv4.conf.all.rp_filter": (0, "2"),
        "sysctl -n net.ipv4.conf.default.rp_filter": (0, "1"),
    }

    def fake_run_cmd(cmd, timeout):
        assert cmd[:2] == ["bash", "-lc"]
        return command_map[cmd[2]]

    security_audit_controller.run_security_baseline_checks(
        app,
        run_cmd_fn=fake_run_cmd,
    )

    statuses = {item["id"]: item["status"] for item in app.security_baseline_results}
    assert statuses["boot.secure_boot_state"] == "Manuelle Pruefung erforderlich"
    assert statuses["sysctl.net.ipv4.conf.all.rp_filter"] == "Erfuellt"
    assert statuses["sysctl.net.ipv4.conf.default.rp_filter"] == "Bewusste Abweichung"
    assert statuses["tools.debsums_present"] == "Nicht anwendbar"
    assert statuses["pkg.dpkg_rc_residue_checked"] == "Manuelle Pruefung erforderlich"
    secure_boot = next(
        item
        for item in app.security_baseline_results
        if item["id"] == "boot.secure_boot_state"
    )
    assert "Secure Boot disabled" in secure_boot["lynis_reference"]
    assert "Gesamtstatus:" in app.security_baseline_status_var.get()
    assert app.security_baseline_lynis_summary_var.get() == (
        "Lynis: Index 77 | Warnungen 0 | Tests 248"
    )
    assert saved["count"] == 1
    assert app.logs[-1] == (
        "Security Baseline im Lynis-Tab lesend aktualisiert."
        " Privilegkontext: keine privilegierte Session."
    )


def test_security_baseline_ufw_status_parser_uses_english_status_lines_only():
    assert (
        security_audit_controller._parse_ufw_status_state("Status: active") == "active"
    )
    assert (
        security_audit_controller._parse_ufw_status_state("Status: inactive")
        == "inactive"
    )
    assert security_audit_controller._parse_ufw_status_state("Status: Aktiv") is None


def _ufw_active_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "fw.ufw_active"
    )


def _evaluate_ufw_active_output(rc, output):
    return security_audit_controller._evaluate_baseline_check(
        _ufw_active_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
    )


def _grub_password_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "boot.grub_password_protected"
    )


def _evaluate_grub_password_output(rc, output):
    return security_audit_controller._evaluate_baseline_check(
        _grub_password_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
    )


def test_ufw_active_root_error_requires_root_status():
    result = _evaluate_ufw_active_output(1, "ERROR: You need to be root")

    assert result["status"] == "Root-Rechte erforderlich"
    assert result["actual"] == "Root-Rechte fehlen"
    assert result["check_error"] == "ERROR: You need to be root"
    assert result["requires_root_read"] is True


def test_grub_password_check_without_match_is_not_fulfilled():
    result = _evaluate_grub_password_output(0, "nein")

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == "nein"


def test_grub_password_missing_config_is_not_applicable():
    result = _evaluate_grub_password_output(
        1,
        "Keine lesbare GRUB-Konfiguration unter /boot/grub/grub.cfg oder /boot/grub2/grub.cfg gefunden.",
    )

    assert result["status"] == "Nicht anwendbar"
    assert result["actual"] == "GRUB-Konfiguration nicht gefunden"
    assert "anderen Bootloader" in result["reason"]


def _ufw_rules_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "fw.ufw_rules_non_empty"
    )


def _evaluate_ufw_rules_output(rc, output):
    return security_audit_controller._evaluate_baseline_check(
        _ufw_rules_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
    )


def test_ufw_rules_active_with_one_numbered_rule_is_fulfilled():
    result = _evaluate_ufw_rules_output(
        0,
        "Status: active\n[ 1] Anywhere on CH-685        ALLOW IN    Anywhere",
    )

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "ja"
    assert result["ufw_active"] is True
    assert result["rule_count"] == 1
    assert result["rules_detected"] is True
    assert "Erkannte Regeln: 1" in result["detail_output"]


def test_ufw_rules_active_with_multiple_rules_counts_all_numbered_lines():
    result = _evaluate_ufw_rules_output(
        0,
        "\n".join(
            [
                "Status: active",
                "[ 1] Anywhere on CH-685        ALLOW IN    Anywhere",
                "[ 2] Anywhere                  ALLOW OUT   Anywhere on CH-685",
                "[10] 146.70.130.130 51820/udp ALLOW OUT   Anywhere",
            ]
        ),
    )

    assert result["status"] == "Erfuellt"
    assert result["rule_count"] == 3


def test_ufw_rules_active_with_ipv4_only_rules_is_fulfilled():
    result = _evaluate_ufw_rules_output(
        0,
        "Status: active\n[ 1] 89.222.96.158 51820/udp ALLOW OUT Anywhere",
    )

    assert result["status"] == "Erfuellt"
    assert result["rule_count"] == 1


def test_ufw_rules_active_with_ipv6_only_rules_is_fulfilled():
    result = _evaluate_ufw_rules_output(
        0,
        "Status: active\n[ 1] Anywhere (v6) on proton-de ALLOW IN Anywhere (v6)",
    )

    assert result["status"] == "Erfuellt"
    assert result["rule_count"] == 1


def test_ufw_rules_active_with_mixed_in_out_interface_rules_is_fulfilled():
    result = _evaluate_ufw_rules_output(
        0,
        "\n".join(
            [
                "Status: active",
                "[ 1] Anywhere on proton-de     ALLOW IN    Anywhere",
                "[ 2] Anywhere                  ALLOW OUT   Anywhere on proton-de",
            ]
        ),
    )

    assert result["status"] == "Erfuellt"
    assert result["rule_count"] == 2


def test_ufw_rules_active_without_numbered_rules_is_not_fulfilled():
    result = _evaluate_ufw_rules_output(
        0,
        "Status: active\nTo                         Action      From\n--                         ------      ----",
    )

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == "nein"
    assert result["rule_count"] == 0
    assert result["rules_detected"] is False


def test_ufw_rules_inactive_is_not_fulfilled():
    result = _evaluate_ufw_rules_output(0, "Status: inactive")

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == "UFW nicht aktiv"
    assert result["ufw_active"] is False
    assert result["rule_count"] == 0


def test_ufw_rules_command_uses_c_locale_for_localized_systems():
    assert _ufw_rules_spec()["command"] == "LANG=C LC_ALL=C ufw status numbered"


def test_ufw_rules_call_error_requires_root_status():
    result = _evaluate_ufw_rules_output(1, "ERROR: You need to be root")

    assert result["status"] == "Root-Rechte erforderlich"
    assert result["actual"] == "Root-Rechte fehlen"
    assert result["check_error"] == "ERROR: You need to be root"
    assert result["requires_root_read"] is True


def test_ufw_rules_empty_or_unexpected_output_requires_manual_review():
    empty = _evaluate_ufw_rules_output(0, "")
    unexpected = _evaluate_ufw_rules_output(0, "garbage")

    assert empty["status"] == "Manuelle Pruefung erforderlich"
    assert empty["actual"] == "Pruefung fehlgeschlagen"
    assert empty["rule_count"] == 0
    assert unexpected["status"] == "Manuelle Pruefung erforderlich"
    assert unexpected["check_error"] == "UFW-Statuszeile fehlt oder ist unerwartet."


def _umask_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "auth.umask_027"
    )


def _evaluate_umask_output(rc, output):
    return security_audit_controller._evaluate_baseline_check(
        _umask_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
    )


def test_umask_027_from_login_defs_is_fulfilled():
    result = _evaluate_umask_output(0, "/etc/login.defs:UMASK 027")

    assert result["status"] == "Erfuellt"
    assert result["expected"] == "027"
    assert result["actual"] == "027"
    assert result["config_source"] == "/etc/login.defs: 027"


def test_umask_022_from_login_defs_is_not_fulfilled():
    result = _evaluate_umask_output(0, "/etc/login.defs:UMASK 022")

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == "022"
    assert "entspricht jedoch nicht" in result["reason"]


def test_umask_lowercase_from_profile_is_fulfilled():
    result = _evaluate_umask_output(0, "/etc/profile:umask 027")

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "027"
    assert result["config_source"] == "/etc/profile: 027"


def test_umask_commented_entry_is_treated_as_not_set():
    result = _evaluate_umask_output(1, "/etc/login.defs:# UMASK 027")

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == "Nicht gesetzt"


def test_umask_missing_entry_is_treated_as_not_set():
    result = _evaluate_umask_output(1, "")

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == "Nicht gesetzt"
    assert "keine Standard-UMASK" in result["reason"]


def test_umask_multiple_sources_with_same_027_are_fulfilled():
    result = _evaluate_umask_output(
        0,
        "\n".join(
            [
                "/etc/login.defs:UMASK 027",
                "/etc/profile:umask 027",
                "/etc/profile.d/hardening.sh:\tumask\t027",
            ]
        ),
    )

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "027"
    assert "/etc/profile.d/hardening.sh: 027" in result["config_source"]


def test_umask_multiple_different_values_require_manual_review():
    result = _evaluate_umask_output(
        0,
        "\n".join(
            [
                "/etc/login.defs:UMASK 022",
                "/etc/profile:umask 027",
            ]
        ),
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "Mehrere Werte gefunden"
    assert result["conflict_detected"] is True
    assert "/etc/login.defs: 022" in result["config_source"]
    assert "/etc/profile: 027" in result["config_source"]


def test_umask_parser_accepts_whitespace_tabs_and_case_variants():
    result = _evaluate_umask_output(
        0,
        "\n".join(
            [
                "/etc/login.defs:   UMASK    027",
                "/etc/profile.d/x.sh:\tumask\t027\t",
            ]
        ),
    )

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "027"


def test_umask_unreadable_source_marks_manual_review_when_no_value_was_read():
    result = _evaluate_umask_output(
        2, "grep: /etc/profile.d/private.sh: Permission denied"
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "Pruefung fehlgeschlagen"
    assert "technisch nicht zuverlaessig" in result["reason"]


def _home_permissions_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "auth.home_permissions_checked"
    )


def _evaluate_home_permissions_output(rc, output):
    return security_audit_controller._evaluate_baseline_check(
        _home_permissions_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
    )


def test_home_permissions_700_are_fulfilled():
    result = _evaluate_home_permissions_output(0, "700 happy happy /home/happy")

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "700"
    assert result["config_source"] == "/home/happy"


def test_home_permissions_750_are_fulfilled_for_current_system_shape():
    result = _evaluate_home_permissions_output(0, "750 happy happy /home/happy")

    assert result["status"] == "Erfuellt"
    assert result["expected"] == "keine Schreibrechte fuer Gruppe oder andere Benutzer"
    assert result["actual"] == "750"
    assert result["config_source"] == "/home/happy"
    assert "keine Schreibrechte" in result["reason"]


def test_home_permissions_755_require_manual_review():
    result = _evaluate_home_permissions_output(0, "755 happy happy /home/happy")

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "755"
    assert "Andere Benutzer" in result["reason"]


def test_home_permissions_group_or_other_write_are_not_fulfilled():
    for mode in ("770", "775", "777", "720", "707"):
        result = _evaluate_home_permissions_output(0, f"{mode} happy happy /home/happy")

        assert result["status"] == "Nicht erfuellt"
        assert result["actual"] == mode
        assert "beschreibbar" in result["reason"]


def test_home_permissions_multiple_home_dirs_build_overall_status():
    result = _evaluate_home_permissions_output(
        0,
        "\n".join(
            [
                "750 happy happy /home/happy",
                "755 test test /home/test",
                "775 shared shared /home/shared",
            ]
        ),
    )

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == (
        "3 Home-Verzeichnisse geprueft; 1 erfuellt; 1 manuell; 1 nicht erfuellt"
    )
    assert "/home/shared: 775 - nicht erfuellt" in result["detail_output"]


def test_home_permissions_owner_mismatch_requires_manual_review():
    result = _evaluate_home_permissions_output(0, "750 root root /home/happy")

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "750"
    assert "Eigentuemer passt nicht" in result["reason"]


def test_home_permissions_extra_acl_requires_manual_review():
    result = _evaluate_home_permissions_output(
        0, "750 happy happy /home/happy acl=extra"
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "750, zusaetzliche ACLs vorhanden"
    assert "ACLs" in result["reason"]


def test_home_permissions_unreadable_directory_requires_manual_review():
    result = _evaluate_home_permissions_output(
        2, "ERROR /home/private Permission denied"
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "Pruefung fehlgeschlagen"
    assert result["check_error"] == "ERROR /home/private Permission denied"


def test_home_permissions_unusual_path_or_symlink_requires_manual_review():
    unusual = _evaluate_home_permissions_output(0, "750 happy happy /srv/happy")
    symlink = _evaluate_home_permissions_output(
        0, "750 happy happy /home/happy type=symlink"
    )

    assert unusual["status"] == "Manuelle Pruefung erforderlich"
    assert "Eigentuemer passt nicht" in unusual["reason"]
    assert symlink["status"] == "Manuelle Pruefung erforderlich"
    assert "kein normales Verzeichnis" in symlink["reason"]


def test_home_permissions_empty_home_requires_manual_review():
    result = _evaluate_home_permissions_output(0, "")

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "Keine Home-Verzeichnisse gefunden"


def _apt_upgradable_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "pkg.apt_upgradable_packages"
    )


def _evaluate_apt_upgradable_output(rc, output):
    return security_audit_controller._evaluate_baseline_check(
        _apt_upgradable_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
    )


def test_apt_upgradable_no_packages_is_fulfilled():
    result = _evaluate_apt_upgradable_output(0, "Listing...")

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "0"
    assert result["upgradable_count"] == 0
    assert result["upgradable_packages"] == []
    assert result["security_relevance_known"] is False


def test_apt_upgradable_single_package_requires_manual_review():
    result = _evaluate_apt_upgradable_output(
        0,
        "Listing...\ncurl/jammy-updates 7.81.0-1ubuntu1.21 amd64 [upgradable from: 7.81.0-1ubuntu1.20]",
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "1"
    assert "Es wurde 1 aktualisierbares APT-Paket gefunden." in result["reason"]
    assert result["upgradable_packages"][0]["package_name"] == "curl"
    assert result["upgradable_packages"][0]["candidate_version"] == "7.81.0-1ubuntu1.21"
    assert result["upgradable_packages"][0]["installed_version"] == "7.81.0-1ubuntu1.20"


def test_apt_upgradable_multiple_packages_parse_details():
    result = _evaluate_apt_upgradable_output(
        0,
        "\n".join(
            [
                "Listing...",
                "linux-firmware/jammy-updates,jammy-security 20240610 amd64 [upgradable from: 20240501]",
                "curl/jammy-updates 7.81.0-1ubuntu1.21 amd64 [upgradable from: 7.81.0-1ubuntu1.20]",
            ]
        ),
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "2"
    assert result["upgradable_count"] == 2
    assert (
        result["upgradable_packages"][0]["repository"] == "jammy-updates,jammy-security"
    )
    assert "2 aktualisierbare APT-Pakete:" in result["detail_output"]
    assert "linux-firmware" in result["detail_output"]


def test_apt_upgradable_package_name_with_architecture_suffix():
    result = _evaluate_apt_upgradable_output(
        0,
        "Listing...\nlibssl3:amd64/jammy-updates 3.0.2-0ubuntu1.20 amd64 [upgradable from: 3.0.2-0ubuntu1.19]",
    )

    assert result["upgradable_count"] == 1
    assert result["upgradable_packages"][0]["package_name"] == "libssl3:amd64"
    assert result["upgradable_packages"][0]["architecture"] == "amd64"


def test_apt_upgradable_third_party_repository_is_preserved():
    result = _evaluate_apt_upgradable_output(
        0,
        "Listing...\ncode/stable 1.101.2-1750797935 amd64 [upgradable from: 1.101.1-1750254731]",
    )

    assert result["upgradable_packages"][0]["repository"] == "stable"
    assert result["upgradable_packages"][0]["package_name"] == "code"


def test_apt_upgradable_held_packages_are_not_invented_as_findings():
    result = _evaluate_apt_upgradable_output(0, "Listing...")

    assert result["status"] == "Erfuellt"
    assert result["upgradable_count"] == 0


def test_apt_upgradable_ignores_warning_lines_on_stdout():
    result = _evaluate_apt_upgradable_output(
        0,
        "\n".join(
            [
                "WARNING: apt does not have a stable CLI interface. Use with caution in scripts.",
                "Listing...",
            ]
        ),
    )

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "0"


def test_apt_upgradable_network_or_cache_errors_are_manual_review():
    for output in (
        "E: Failed to fetch http://example.invalid/InRelease",
        "E: The package lists or status file could not be parsed or opened.",
        "bash: apt: command not found",
    ):
        result = _evaluate_apt_upgradable_output(100, output)

        assert result["status"] == "Manuelle Pruefung erforderlich"
        assert result["actual"] == "Pruefung fehlgeschlagen"
        assert result["check_error"] == output


def test_apt_upgradable_command_forces_c_locale_for_localized_systems():
    assert (
        _apt_upgradable_spec()["command"]
        == "LANG=C LC_ALL=C apt list --upgradable 2>/dev/null"
    )


def test_apt_upgradable_unexpected_output_requires_manual_review():
    result = _evaluate_apt_upgradable_output(0, "unerwartete Ausgabe")

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "Pruefung fehlgeschlagen"
    assert result["check_success"] is False
    assert result["check_error"] == "unerwartete Ausgabe"


def test_apt_repository_guard_check_returns_recommendation_for_signed_by_and_legacy_findings():
    spec = next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "pkg.apt_repository_signed_by_scoped"
    )
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.repository_guard_service = type(
        "DummyRepositoryGuardService",
        (),
        {
            "scan": lambda self: {
                "sources": [
                    {
                        "kind": "apt",
                        "enabled": True,
                        "file_path": "/etc/apt/sources.list.d/zorin.sources",
                        "uri": "https://packages.zorinos.com/stable",
                        "suite": "noble",
                        "components": ["main"],
                        "signed_by": "",
                    }
                ],
                "auxiliary_files": [
                    {
                        "file_path": "/etc/apt/sources.list.d/zorin.list.distUpgrade.disabled",
                        "state": "disabled",
                    }
                ],
                "global_keyrings": [
                    {
                        "file_path": "/etc/apt/trusted.gpg.d/zorin-os.gpg",
                        "scope": "third_party",
                    }
                ],
                "findings": [
                    {
                        "code": "repo_no_signed_by",
                        "summary": "Drittquelle nutzt keinen expliziten Keyring-Hinweis.",
                        "details": {
                            "file_path": "/etc/apt/sources.list.d/zorin.sources"
                        },
                    },
                    {
                        "code": "repo_disabled_file_present",
                        "summary": "Eine deaktivierte Repositorydatei wurde als Inventareintrag erkannt.",
                        "details": {
                            "file_path": "/etc/apt/sources.list.d/zorin.list.distUpgrade.disabled"
                        },
                    },
                    {
                        "code": "repo_global_third_party_keyring",
                        "summary": "Ein Drittanbieter-Schluessel liegt global unter trusted.gpg.d.",
                        "details": {"file_path": "/etc/apt/trusted.gpg.d/zorin-os.gpg"},
                    },
                ],
                "errors": [],
            }
        },
    )()

    result = security_audit_controller._evaluate_baseline_check(spec, app=app)

    assert result["status"] == "Empfehlung"
    assert result["actual"] == "3 Auffaelligkeit(en)"
    assert result["check_method"] == "python:RepositoryGuardService.scan"
    assert "/etc/apt/sources.list.d/zorin.sources" in result["detail_output"]
    assert "Globale Keyrings:" in result["detail_output"]
    assert "Erkannte Auffaelligkeiten:" in result["detail_output"]


def _critical_file_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "pkg.critical_file_permissions_checked"
    )


def _evaluate_critical_file_output(rc, output):
    return security_audit_controller._evaluate_baseline_check(
        _critical_file_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
    )


def _standard_critical_file_output():
    return "\n".join(
        [
            "644 root root /etc/passwd",
            "640 root shadow /etc/shadow",
            "440 root root /etc/sudoers",
        ]
    )


def test_critical_file_permissions_standard_debian_values_are_fulfilled():
    result = _evaluate_critical_file_output(0, _standard_critical_file_output())

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "Alle geprueften Dateien entsprechen den Sollwerten"
    assert "/etc/passwd: 644 root:root OK" in result["detail_output"]
    assert "/etc/shadow: 640 root:shadow OK" in result["detail_output"]
    assert "/etc/sudoers: 440 root:root OK" in result["detail_output"]


def test_critical_file_passwd_group_writable_is_not_fulfilled():
    result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "664 root root /etc/passwd",
                "640 root shadow /etc/shadow",
                "440 root root /etc/sudoers",
            ]
        ),
    )

    assert result["status"] == "Nicht erfuellt"
    assert "/etc/passwd" in result["actual"]
    assert "beschreibbar" in result["reason"]


def test_critical_file_shadow_world_readable_is_not_fulfilled():
    result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "644 root shadow /etc/shadow",
                "644 root root /etc/passwd",
                "440 root root /etc/sudoers",
            ]
        ),
    )

    assert result["status"] == "Nicht erfuellt"
    assert "/etc/shadow" in result["actual"]
    assert "Leserechte" in result["reason"]


def test_critical_file_sudoers_644_is_not_fulfilled():
    result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "644 root root /etc/passwd",
                "640 root shadow /etc/shadow",
                "644 root root /etc/sudoers",
            ]
        ),
    )

    assert result["status"] == "Nicht erfuellt"
    assert "/etc/sudoers" in result["actual"]


def test_critical_file_wrong_owner_or_group_is_not_fulfilled():
    owner_result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "644 admin root /etc/passwd",
                "640 root shadow /etc/shadow",
                "440 root root /etc/sudoers",
            ]
        ),
    )
    group_result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "644 root users /etc/passwd",
                "640 root shadow /etc/shadow",
                "440 root root /etc/sudoers",
            ]
        ),
    )

    assert owner_result["status"] == "Nicht erfuellt"
    assert "Eigentuemer" in owner_result["reason"]
    assert group_result["status"] == "Nicht erfuellt"
    assert "Gruppe" in group_result["reason"]


def test_critical_file_missing_file_requires_manual_review():
    result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "644 root root /etc/passwd",
                "640 root shadow /etc/shadow",
            ]
        ),
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "Datei nicht gefunden"
    assert "Datei nicht gefunden: /etc/sudoers" in result["detail_output"]


def test_critical_file_stat_error_requires_manual_review():
    result = _evaluate_critical_file_output(
        1,
        "stat: cannot statx '/etc/shadow': Permission denied",
    )

    assert result["status"] == "Root-Rechte erforderlich"
    assert result["actual"] == "Root-Rechte fehlen"
    assert "Administratorrechte" in result["reason"]
    assert result["requires_root_read"] is True


def test_detect_hardening_privilege_context_reports_existing_sudo_session(monkeypatch):
    monkeypatch.setattr(security_audit_controller.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(
        security_audit_controller,
        "check_sudo_nopasswd",
        lambda: True,
    )

    context = security_audit_controller._detect_hardening_privilege_context()

    assert context["is_root"] is False
    assert context["has_sudo_session"] is True
    assert context["root_available"] is True
    assert context["source"] == "sudo -n true"


def test_no_empty_password_accounts_without_privileges_returns_root_required(
    monkeypatch,
):
    spec = next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "auth.no_empty_password_accounts"
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_cmd",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("run_cmd should not be called")
        ),
    )

    result = security_audit_controller._evaluate_baseline_check(
        spec,
        root_context={
            "is_root": False,
            "has_sudo_session": False,
            "pkexec_authorized": False,
            "root_available": False,
            "source": "keine privilegierte Session",
        },
    )

    assert result["status"] == "Root-Rechte erforderlich"
    assert result["actual"] == "Root-Rechte fehlen"
    assert result["reason"] == (
        "Das Lesen von /etc/shadow benoetigt Administratorrechte, die NetMon aktuell nicht besitzt."
    )


def test_read_native_root_check_uses_python_for_unique_uid_gid_without_shell(
    monkeypatch,
):
    spec = next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "auth.unique_uid_gid"
    )
    monkeypatch.setattr(
        security_audit_controller,
        "_count_duplicate_uid_gid_native",
        lambda: 2,
    )

    rc, out, method = security_audit_controller._read_native_root_check(
        spec,
        root_context={
            "is_root": False,
            "has_sudo_session": False,
            "pkexec_authorized": False,
            "root_available": False,
            "source": "keine privilegierte Session",
        },
    )

    assert rc == 0
    assert out == "2"
    assert method == "python:/etc/passwd,/etc/group"


def test_critical_file_shadow_600_secure_special_case_is_fulfilled():
    result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "644 root root /etc/passwd",
                "600 root root /etc/shadow",
                "400 root root /etc/sudoers",
            ]
        ),
    )

    assert result["status"] == "Erfuellt"


def test_critical_file_mixed_correct_and_wrong_files_is_not_fulfilled():
    result = _evaluate_critical_file_output(
        0,
        "\n".join(
            [
                "644 root root /etc/passwd",
                "644 root shadow /etc/shadow",
                "440 root root /etc/sudoers",
            ]
        ),
    )

    assert result["status"] == "Nicht erfuellt"
    assert "/etc/shadow" in result["actual"]
    assert "/etc/passwd" not in result["actual"]


def test_security_baseline_filter_and_selection_update_detail_text():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_tree = DummyTree()
    app.security_baseline_detail_text = DummyText()
    app.security_baseline_detail_heading_var = DummyVar()
    app.security_baseline_filter_mode = "all"
    app.security_baseline_results = [
        {
            "id": "a",
            "group": "Kernel",
            "title": "Check A",
            "expected": "2",
            "actual": "2",
            "source": "sysctl",
            "status": "Erfuellt",
            "description": "A",
            "reason": "ok",
            "security_benefit": "benefit",
            "side_effects": "side",
            "exceptions": "exceptions",
            "command": "sysctl -n a",
            "config_source": "/etc/sysctl.d/a.conf",
            "lynis_reference": "",
        },
        {
            "id": "b",
            "group": "Firewall",
            "title": "Check B",
            "expected": "ja",
            "actual": "nein",
            "source": "Systembefehl",
            "status": "Nicht erfuellt",
            "description": "B",
            "reason": "bad",
            "security_benefit": "benefit",
            "side_effects": "side",
            "exceptions": "exceptions",
            "command": "cmd",
            "config_source": "src",
            "lynis_reference": "ref",
        },
    ]

    security_audit_controller.refresh_security_baseline_table(app)

    assert app.security_baseline_tree.rows[0]["values"][0] == "Nicht erfuellt"
    assert app.security_baseline_detail_text.value == "Noch kein Check ausgewaehlt."
    assert app.security_baseline_current_view == "list"

    app.security_baseline_tree.selection_set("0")
    security_audit_controller.on_security_baseline_select(app)

    assert "Check B" in app.security_baseline_detail_text.value
    assert app.security_baseline_current_view == "detail"
    assert app.security_baseline_detail_heading_var.get() == "Check B"

    security_audit_controller.apply_security_baseline_filter(app, "kernel")

    assert len(app.security_baseline_visible_rows) == 1
    assert app.security_baseline_visible_rows[0]["id"] == "a"
    assert app.security_baseline_current_view == "list"


def test_active_baseline_profile_defaults_and_supports_override():
    default_profile = security_audit_controller._active_baseline_profile()

    assert default_profile["id"] == "zorin_desktop_development"
    assert default_profile["distribution"] == "Zorin OS"

    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "ubuntu_server_hardening"

    profile = security_audit_controller._active_baseline_profile(app)

    assert profile["id"] == "ubuntu_server_hardening"
    assert profile["profile"] == "Server / Haertung"

    app.security_baseline_profile_id = "desktop_safe_v1"

    profile = security_audit_controller._active_baseline_profile(app)

    assert profile["id"] == "desktop_safe_v1"
    assert profile["profile"] == "Desktop Safe"
    assert profile["requires_snapshot"] is True
    assert "whoopsie.service" in {
        item["name"] for item in profile["sections"]["services"]["auto_optional"]
    }


def test_baseline_profile_choice_items_filter_out_fedora_on_mint():
    app = netmon_app.App.__new__(netmon_app.App)
    app._read_os_release = lambda: {
        "ID": "linuxmint",
        "ID_LIKE": "ubuntu debian",
        "NAME": "Linux Mint",
        "PRETTY_NAME": "Linux Mint 22",
    }

    items = dict(security_audit_controller.baseline_profile_choice_items(app))

    assert "linuxmint_desktop_development" in items
    assert "linuxmint_vpn_multi_interface" in items
    assert "desktop_safe_v1" in items
    assert "fedora_workstation_review" not in items
    assert "zorin_desktop_development" not in items
    assert "ubuntu_desktop_development" in items


def test_active_baseline_profile_falls_back_to_system_compatible_profile():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "fedora_workstation_review"
    app._read_os_release = lambda: {
        "ID": "linuxmint",
        "ID_LIKE": "ubuntu debian",
        "NAME": "Linux Mint",
        "PRETTY_NAME": "Linux Mint 22",
    }

    profile = security_audit_controller._active_baseline_profile(app)

    assert profile["id"] == "linuxmint_desktop_development"
    assert profile["distribution"] == "Linux Mint"


def test_recommended_baseline_profile_id_prefers_mint_profile_on_mint():
    app = netmon_app.App.__new__(netmon_app.App)
    app._read_os_release = lambda: {
        "ID": "linuxmint",
        "ID_LIKE": "ubuntu debian",
        "NAME": "Linux Mint",
        "PRETTY_NAME": "Linux Mint 22",
    }

    profile_id = security_audit_controller._recommended_baseline_profile_id(app)

    assert profile_id == "linuxmint_desktop_development"


def test_baseline_profile_choice_label_includes_distribution_and_profile():
    label = security_audit_controller._baseline_profile_choice_label(
        security_audit_controller.SECURITY_BASELINE_PROFILES[
            "linuxmint_desktop_development"
        ]
    )

    assert label == "Linux Mint | Desktop / Development"


def test_recommended_baseline_profile_id_prefers_fedora_review_on_fedora():
    app = netmon_app.App.__new__(netmon_app.App)
    app._read_os_release = lambda: {
        "ID": "fedora",
        "ID_LIKE": "fedora",
        "NAME": "Fedora Linux",
        "PRETTY_NAME": "Fedora Linux 42",
    }

    profile_id = security_audit_controller._recommended_baseline_profile_id(app)

    assert profile_id == "fedora_workstation_review"


def test_baseline_checks_are_enriched_with_profile_and_hardening_metadata():
    app = netmon_app.App.__new__(netmon_app.App)

    checks = security_audit_controller._baseline_checks(app)
    ufw_rules = next(item for item in checks if item["id"] == "fw.ufw_rules_non_empty")
    sysctl_item = next(
        item for item in checks if item["id"] == "sysctl.kernel.kptr_restrict"
    )

    assert "zorin_desktop_development" in ufw_rules["profile_targets"]
    assert "linuxmint_desktop_development" in ufw_rules["profile_targets"]
    assert "desktop_safe_v1" in ufw_rules["profile_targets"]
    assert ufw_rules["platform_family"] == "debian_like"
    assert ufw_rules["apply_strategy"] == "manual_profile_required"
    assert "UFW-Regeln" in ufw_rules["remediation_summary"]
    assert "exportieren" in ufw_rules["rollback_hint"]
    assert sysctl_item["apply_strategy"] == "planned"
    assert "sysctl" in sysctl_item["remediation_summary"]


def test_active_ufw_baseline_profile_supports_desktop_safe_v1():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "desktop_safe_v1"

    profile = security_audit_controller._active_ufw_baseline_profile(app)

    assert profile is not None
    assert profile["id"] == "desktop_development_minimal_v1"
    assert "desktop_safe_v1" in profile["profile_targets"]

    app.security_baseline_profile_id = "linuxmint_desktop_development"
    profile = security_audit_controller._active_ufw_baseline_profile(app)
    assert profile is not None
    assert "linuxmint_desktop_development" in profile["profile_targets"]


def test_apply_security_baseline_profile_choice_switches_profile_and_saves():
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.security_baseline_profile_choice_var = DummyVar()
    app.security_baseline_profile_var = DummyVar()
    app.security_baseline_version_var = DummyVar()
    app.security_baseline_reference_var = DummyVar()
    app.security_baseline_date_var = DummyVar()
    app.security_baseline_last_check_var = DummyVar()
    app.security_baseline_status_var = DummyVar()
    app.security_baseline_lynis_summary_var = DummyVar()
    app.security_baseline_optional_services_var = DummyVar()
    app.security_baseline_tree = DummyTree()
    app.security_baseline_detail_text = DummyText()
    app.security_baseline_results = []
    app.security_baseline_filter_mode = "all"
    seen = []
    app.save_settings = lambda log_success=False: seen.append(log_success)

    label = dict(security_audit_controller.baseline_profile_choice_items())[
        "desktop_safe_v1"
    ]
    security_audit_controller.apply_security_baseline_profile_choice(app, label)

    assert app.security_baseline_profile_id == "desktop_safe_v1"
    assert app.security_baseline_profile_choice_var.get() == label
    assert "Desktop Safe" in app.security_baseline_profile_var.get()
    assert (
        "whoopsie.service deaktivieren"
        in app.security_baseline_optional_services_var.get()
    )
    assert seen == [False]


def test_apply_security_baseline_profile_choice_reruns_existing_results(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.security_baseline_results = [{"id": "boot.uefi_active"}]
    app.security_baseline_checks = [{"id": "cached"}]
    app.security_baseline_checks_profile_id = "zorin_desktop_development"
    seen = {"rerun": 0, "saved": []}
    app.save_settings = lambda log_success=False: seen["saved"].append(log_success)

    def fake_rerun(target_app, *, run_cmd_fn=None):
        assert target_app is app
        seen["rerun"] += 1

    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        fake_rerun,
    )

    label = dict(security_audit_controller.baseline_profile_choice_items())[
        "desktop_safe_v1"
    ]
    security_audit_controller.apply_security_baseline_profile_choice(app, label)

    assert app.security_baseline_profile_id == "desktop_safe_v1"
    assert app.security_baseline_checks == []
    assert app.security_baseline_checks_profile_id == ""
    assert seen["rerun"] == 1
    assert seen["saved"] == [False]


def test_baseline_checks_include_profile_specific_advisories_for_desktop_safe():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "desktop_safe_v1"

    checks = security_audit_controller._baseline_checks(app)
    titles = {item["title"] for item in checks}

    assert "Optionaler Dienst: whoopsie.service" in titles
    assert "Dienst manuell pruefen: snapd.service" in titles
    assert "Profil-Hinweis: Lynis: deleted_files_in_use" in titles


def test_desktop_safe_profile_marks_selected_packages_as_recommendations():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "desktop_safe_v1"
    spec = next(
        item
        for item in security_audit_controller._baseline_checks(app)
        if item["id"] == "tools.clamav_installed"
    )

    result = security_audit_controller._evaluate_baseline_check(
        spec,
        app=app,
        run_cmd_fn=lambda _cmd, timeout=0: (1, ""),
    )

    assert result["status"] == "Empfehlung"
    assert result["actual"] == "nein"


def test_build_sysctl_dropin_content_uses_expected_values():
    content = security_audit_controller._build_sysctl_dropin_content(
        [
            {
                "id": "sysctl.kernel.kptr_restrict",
                "expected": "2",
            },
            {
                "id": "sysctl.net.ipv4.conf.all.rp_filter",
                "expected": "2",
            },
        ]
    )

    assert "# NetMon Security Baseline" in content
    assert "kernel.kptr_restrict = 2" in content
    assert "net.ipv4.conf.all.rp_filter = 2" in content


def test_active_ufw_baseline_profile_selects_desktop_server_and_vpn_variants():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "zorin_desktop_development"

    profile = security_audit_controller._active_ufw_baseline_profile(app)

    assert profile["id"] == "desktop_development_minimal_v1"
    assert profile["default_incoming"] == "deny"
    assert profile["default_outgoing"] == "allow"

    app.security_baseline_profile_id = "ubuntu_server_hardening"
    server_profile = security_audit_controller._active_ufw_baseline_profile(app)
    assert server_profile["id"] == "server_hardening_minimal_v1"
    assert "SSH" in server_profile["post_apply_note"]

    app.security_baseline_profile_id = "zorin_vpn_multi_interface"
    vpn_profile = security_audit_controller._active_ufw_baseline_profile(app)
    assert vpn_profile["id"] == "vpn_multi_interface_minimal_v1"
    assert "VPN-Interfaces" in vpn_profile["post_apply_note"]


def test_security_baseline_apply_plan_contains_preview_and_rollback_text():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "zorin_desktop_development"

    plan = security_audit_controller._security_baseline_apply_plan(app)

    assert plan["actions"] == ["sysctl", "ufw"]
    assert "/etc/sysctl.d/99-zz-netmon-hardening.conf" in plan["preview_text"]
    assert "UFW Defaults: incoming=deny, outgoing=allow" in plan["preview_text"]
    assert "allow in on lo" in plan["preview_text"]
    assert "Drop-in-Datei sichern" in plan["rollback_text"]
    assert "Default-Policies" in plan["rollback_text"]


def test_security_baseline_apply_plan_includes_optional_services_for_desktop_safe():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "desktop_safe_v1"

    plan = security_audit_controller._security_baseline_apply_plan(app)

    assert "services_optional" in plan["actions"]
    assert "Optionale Dienste" in plan["preview_text"]
    assert "whoopsie.service deaktivieren" in plan["preview_text"]
    assert "systemd-bsod.service deaktivieren" in plan["preview_text"]


def test_server_profile_evaluates_strict_rp_filter_mode():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "ubuntu_server_hardening"
    spec = next(
        item
        for item in security_audit_controller._baseline_checks(app)
        if item["id"] == "sysctl.net.ipv4.conf.default.rp_filter"
    )

    fulfilled = security_audit_controller._evaluate_baseline_check(
        spec,
        app=app,
        run_cmd_fn=lambda _cmd, timeout=0: (0, "1"),
    )
    deviation = security_audit_controller._evaluate_baseline_check(
        spec,
        app=app,
        run_cmd_fn=lambda _cmd, timeout=0: (0, "2"),
    )

    assert fulfilled["status"] == "Erfuellt"
    assert deviation["status"] == "Bewusste Abweichung"


def test_rp_filter_mismatch_mentions_ufw_override(tmp_path, monkeypatch):
    monkeypatch.setattr(
        security_audit_controller,
        "_sysctl_ufw_override_value",
        lambda _spec: "1",
    )
    dropin = tmp_path / "99-zz-netmon-hardening.conf"
    dropin.write_text(
        "net.ipv4.conf.all.rp_filter = 2\n",
        encoding="utf-8",
    )
    spec = {
        "id": "sysctl.net.ipv4.conf.all.rp_filter",
        "group": "Kernel",
        "title": "net.ipv4.conf.all.rp_filter",
        "expected": "2",
        "source": "sysctl",
        "description": "test",
        "security_benefit": "test",
        "side_effects": "test",
        "exceptions": "test",
        "command": "sysctl -n net.ipv4.conf.all.rp_filter",
        "config_source": str(dropin),
        "check_kind": "rp_filter",
    }

    result = security_audit_controller._evaluate_baseline_check(
        spec,
        run_cmd_fn=lambda _cmd, timeout=0: (0, "1"),
    )

    assert result["status"] == "Bewusste Abweichung"
    assert "Strict mode 1" in result["reason"]
    assert "/etc/ufw/sysctl.conf setzt denselben Wert auf 1" in result["reason"]
    assert "ufw.service" in result["reason"]


def test_sysctl_mismatch_mentions_configured_dropin(tmp_path, monkeypatch):
    monkeypatch.setattr(
        security_audit_controller,
        "_sysctl_ufw_override_value",
        lambda _spec: None,
    )
    dropin = tmp_path / "99-zz-netmon-hardening.conf"
    dropin.write_text(
        "\n".join(
            [
                "# NetMon Security Baseline",
                "net.ipv4.conf.all.log_martians = 1",
            ]
        ),
        encoding="utf-8",
    )
    spec = {
        "id": "sysctl.net.ipv4.conf.all.log_martians",
        "group": "Kernel",
        "title": "net.ipv4.conf.all.log_martians",
        "expected": "1",
        "source": "sysctl",
        "description": "test",
        "security_benefit": "test",
        "side_effects": "test",
        "exceptions": "test",
        "command": "sysctl -n net.ipv4.conf.all.log_martians",
        "config_source": str(dropin),
        "check_kind": "sysctl",
    }

    result = security_audit_controller._evaluate_baseline_check(
        spec,
        run_cmd_fn=lambda _cmd, timeout=0: (0, "0"),
    )

    assert result["status"] == "Nicht erfuellt"
    assert result["actual"] == "0"
    assert "Drop-in-Datei den Sollwert enthaelt" in result["reason"]
    assert "spaetere Ueberschreibungen" in result["reason"]


def test_sysctl_mismatch_mentions_ufw_override(tmp_path, monkeypatch):
    monkeypatch.setattr(
        security_audit_controller,
        "_sysctl_ufw_override_value",
        lambda _spec: "0",
    )
    dropin = tmp_path / "99-zz-netmon-hardening.conf"
    dropin.write_text(
        "net.ipv4.conf.default.log_martians = 1\n",
        encoding="utf-8",
    )
    spec = {
        "id": "sysctl.net.ipv4.conf.default.log_martians",
        "group": "Kernel",
        "title": "net.ipv4.conf.default.log_martians",
        "expected": "1",
        "source": "sysctl",
        "description": "test",
        "security_benefit": "test",
        "side_effects": "test",
        "exceptions": "test",
        "command": "sysctl -n net.ipv4.conf.default.log_martians",
        "config_source": str(dropin),
        "check_kind": "sysctl",
    }

    result = security_audit_controller._evaluate_baseline_check(
        spec,
        run_cmd_fn=lambda _cmd, timeout=0: (0, "0"),
    )

    assert result["status"] == "Nicht erfuellt"
    assert "/etc/ufw/sysctl.conf setzt denselben Wert auf 0" in result["reason"]
    assert "ufw.service" in result["reason"]


def test_optional_services_overview_text_reflects_active_profile():
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "desktop_safe_v1"

    text = security_audit_controller._optional_services_overview_text(app)

    assert "whoopsie.service deaktivieren" in text
    assert "separat bestaetigt" in text


def test_build_security_baseline_transfer_package_contains_sysctl_and_ufw():
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile_id = "zorin_desktop_development"

    package = security_audit_controller.build_security_baseline_transfer_package(app)

    assert package["schema"] == "netmon.security-baseline.transfer"
    assert package["baseline"]["id"] == "zorin_desktop_development"
    assert package["sysctl"]["entries"][0]["key"] == "kernel.kptr_restrict"
    assert package["ufw"]["default_incoming"] == "deny"
    assert package["ufw"]["rules"][0]["iface"] == "lo"


def test_validate_security_baseline_transfer_package_normalizes_payload():
    payload = {
        "schema": "netmon.security-baseline.transfer",
        "schema_version": 1,
        "baseline": {
            "id": "zorin_desktop_development",
            "profile": "Desktop / Development",
            "os_family": "debian_like",
        },
        "sysctl": {
            "dropin_path": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
            "entries": [
                {
                    "id": "sysctl.kernel.kptr_restrict",
                    "title": "kernel.kptr_restrict",
                    "key": "kernel.kptr_restrict",
                    "expected": "2",
                }
            ],
        },
        "ufw": {
            "id": "desktop_development_minimal_v1",
            "name": "Desktop UFW",
            "default_incoming": "deny",
            "default_outgoing": "allow",
            "rules": [{"type": "interface", "direction": "in", "iface": "lo"}],
        },
    }

    package = security_audit_controller._validate_security_baseline_transfer_package(
        payload
    )

    assert (
        package["sysctl"]["entries"][0]["command"] == "sysctl -n kernel.kptr_restrict"
    )
    assert package["ufw"]["rules"][0]["iface"] == "lo"


def test_clear_security_baseline_transfer_resets_loaded_state():
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_transfer_var = DummyVar("loaded")
    app.security_baseline_transfer_package = {
        "baseline": {"id": "zorin_desktop_development"}
    }
    app.security_baseline_transfer_source_path = "/tmp/transfer.json"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"info": 0}

    ok = security_audit_controller.clear_security_baseline_transfer(
        app,
        showinfo_fn=lambda *args, **kwargs: seen.__setitem__("info", seen["info"] + 1),
    )

    assert ok is True
    assert app.security_baseline_transfer_package is None
    assert app.security_baseline_transfer_source_path == ""
    assert app.security_baseline_transfer_var.get() == "Transferpaket: keines geladen"
    assert seen["info"] == 1


def test_import_security_baseline_transfer_loads_state_without_apply(tmp_path):
    package = {
        "schema": "netmon.security-baseline.transfer",
        "schema_version": 1,
        "baseline": {
            "id": "ubuntu_server_hardening",
            "profile": "Server / Haertung",
            "os_family": "debian_like",
        },
        "sysctl": {
            "dropin_path": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
            "entries": [
                {
                    "id": "sysctl.kernel.kptr_restrict",
                    "title": "kernel.kptr_restrict",
                    "key": "kernel.kptr_restrict",
                    "expected": "2",
                }
            ],
        },
        "ufw": {
            "id": "server_hardening_minimal_v1",
            "name": "Server UFW",
            "default_incoming": "deny",
            "default_outgoing": "allow",
            "rules": [{"type": "interface", "direction": "in", "iface": "lo"}],
        },
    }
    path = tmp_path / "transfer.json"
    path.write_text(__import__("json").dumps(package), encoding="utf-8")

    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.security_baseline_profile_var = DummyVar()
    app.security_baseline_version_var = DummyVar()
    app.security_baseline_reference_var = DummyVar()
    app.security_baseline_date_var = DummyVar()
    app.security_baseline_last_check_var = DummyVar()
    app.security_baseline_status_var = DummyVar()
    app.security_baseline_lynis_summary_var = DummyVar()
    app.security_baseline_transfer_var = DummyVar()
    app.security_baseline_tree = DummyTree()
    app.security_baseline_detail_text = DummyText()
    app.log_messages = []
    app.log_safe = app.log_messages.append

    ok = security_audit_controller.import_security_baseline_transfer(
        app,
        str(path),
        askyesno_fn=lambda *args, **kwargs: False,
        showinfo_fn=lambda *args, **kwargs: None,
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert app.security_baseline_profile_id == "ubuntu_server_hardening"
    assert (
        app.security_baseline_transfer_package["baseline"]["id"]
        == "ubuntu_server_hardening"
    )
    assert "Quelle: transfer.json" in app.security_baseline_transfer_var.get()


def test_security_baseline_transfer_comparison_text_contains_profile_and_differences():
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.security_baseline_transfer_package = {
        "baseline": {
            "id": "ubuntu_server_hardening",
            "profile": "Server / Haertung",
            "reference": "Ubuntu 24.04 Server",
            "os_family": "debian_like",
        },
        "sysctl": {
            "entries": [
                {
                    "id": "sysctl.kernel.kptr_restrict",
                    "key": "kernel.kptr_restrict",
                    "expected": "1",
                }
            ]
        },
        "ufw": {
            "default_incoming": "deny",
            "default_outgoing": "deny",
            "rules": [{"type": "interface", "direction": "in", "iface": "lo"}],
        },
    }

    text = security_audit_controller.security_baseline_transfer_comparison_text(app)

    assert "Vergleich lokales Profil vs. importiertes Transferpaket" in text
    assert "Desktop / Development" in text
    assert "Server / Haertung" in text
    assert "kernel.kptr_restrict: 2 != 1" in text
    assert (
        "Defaults: incoming=deny, outgoing=allow | incoming=deny, outgoing=deny" in text
    )


def test_security_baseline_transfer_package_text_contains_loaded_package_details():
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_transfer_package = {
        "schema": "netmon.security-baseline.transfer",
        "schema_version": 1,
        "exported_at": "2026-07-19T11:15:00",
        "baseline": {
            "id": "ubuntu_server_hardening",
            "profile": "Server / Haertung",
            "version": "2026.07",
            "reference": "Ubuntu 24.04 Server",
            "os_family": "debian_like",
            "distribution": "Zorin OS",
            "base_distribution": "Ubuntu",
            "roles": ["server", "vpn"],
        },
        "sysctl": {
            "dropin_path": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
            "entries": [
                {
                    "id": "sysctl.kernel.kptr_restrict",
                    "key": "kernel.kptr_restrict",
                    "expected": "2",
                }
            ],
        },
        "ufw": {
            "default_incoming": "deny",
            "default_outgoing": "allow",
            "rules": [{"type": "interface", "direction": "in", "iface": "lo"}],
        },
        "notes": ["Nur freigegebene Schritte."],
    }
    app.security_baseline_transfer_source_path = (
        "/tmp/netmon_security_baseline_transfer_ubuntu_server_hardening_2026-07-19.json"
    )

    text = security_audit_controller.security_baseline_transfer_package_text(app)

    assert "Geladenes Transferpaket" in text
    assert (
        "Source: netmon_security_baseline_transfer_ubuntu_server_hardening_2026-07-19.json"
        in text
    )
    assert "Server / Haertung" in text
    assert "kernel.kptr_restrict = 2" in text
    assert "Defaults: incoming=deny, outgoing=allow" in text
    assert "allow in on lo" in text
    assert "Nur freigegebene Schritte." in text


def test_apply_security_baseline_profile_uses_imported_transfer_package(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"sysctl": [], "ufw": [], "rerun": 0}
    package = {
        "schema": "netmon.security-baseline.transfer",
        "schema_version": 1,
        "baseline": {"id": "custom_profile", "profile": "Imported Profile"},
        "sysctl": {
            "dropin_path": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
            "entries": [
                {
                    "id": "sysctl.kernel.kptr_restrict",
                    "title": "kernel.kptr_restrict",
                    "command": "sysctl -n kernel.kptr_restrict",
                    "check_kind": "sysctl",
                    "expected": "2",
                }
            ],
        },
        "ufw": {
            "id": "imported_ufw_profile",
            "name": "Imported UFW",
            "default_incoming": "deny",
            "default_outgoing": "allow",
            "rules": [{"type": "interface", "direction": "in", "iface": "lo"}],
        },
    }

    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_sysctl",
        lambda _app, **kwargs: seen["sysctl"].append(kwargs) or True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_ufw",
        lambda _app, **kwargs: seen["ufw"].append(kwargs) or True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )
    app.ensure_sudo_session = lambda reason: True

    ok = security_audit_controller.apply_security_baseline_profile(
        app,
        transfer_package=package,
        askyesno_fn=lambda *args, **kwargs: True,
        showinfo_fn=lambda *args, **kwargs: None,
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["sysctl"][0]["override_specs"][0]["id"] == "sysctl.kernel.kptr_restrict"
    assert seen["ufw"][0]["override_profile"]["id"] == "imported_ufw_profile"
    assert seen["rerun"] == 1


def test_apply_security_baseline_ufw_applies_profile_and_reruns_checks(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.ensure_sudo_session = (
        lambda reason: reason == "Security Baseline UFW-Haertung anwenden"
    )
    app._new_rollback_transaction = netmon_app.App._new_rollback_transaction.__get__(
        app, netmon_app.App
    )
    app.log_messages = []
    app.log_safe = app.log_messages.append
    app.log_debug_safe = lambda _msg: None
    app.security_baseline_profile_id = "zorin_desktop_development"

    seen = {"rerun": 0, "confirm": 0, "info": 0}

    verbose_inactive = "\n".join(
        [
            "Status: inactive",
            "Logging: off",
            "Default: deny (incoming), allow (outgoing), disabled (routed)",
        ]
    )
    numbered_empty = "Status: active"
    verbose_active = "\n".join(
        [
            "Status: active",
            "Logging: off",
            "Default: deny (incoming), allow (outgoing), disabled (routed)",
            "To                         Action      From",
            "--                         ------      ----",
            "Anywhere on lo             ALLOW IN    Anywhere",
            "Anywhere                   ALLOW OUT   Anywhere on lo",
        ]
    )

    command_log = []
    ufw_sysctl_content = {
        "text": "\n".join(
            [
                "# Don't log Martian Packets",
                "net/ipv4/conf/all/log_martians=0",
                "net/ipv4/conf/default/log_martians=0",
            ]
        )
        + "\n"
    }

    def fake_run_cmd(args, timeout=0):
        command_log.append(tuple(args))
        if args == [
            "sudo",
            "-n",
            "env",
            "LANG=C",
            "LC_ALL=C",
            "ufw",
            "status",
            "verbose",
        ]:
            count = sum(
                1
                for item in command_log
                if item
                == (
                    "sudo",
                    "-n",
                    "env",
                    "LANG=C",
                    "LC_ALL=C",
                    "ufw",
                    "status",
                    "verbose",
                )
            )
            return 0, verbose_inactive if count == 1 else verbose_active
        if args == [
            "sudo",
            "-n",
            "env",
            "LANG=C",
            "LC_ALL=C",
            "ufw",
            "status",
            "numbered",
        ]:
            return 0, numbered_empty
        if args == ["sudo", "-n", "ufw", "--force", "enable"]:
            return 0, "enabled"
        if args == ["sudo", "-n", "ufw", "allow", "in", "on", "lo"]:
            return 0, "rule added"
        if args == ["sudo", "-n", "ufw", "allow", "out", "on", "lo"]:
            return 0, "rule added"
        if args == ["sudo", "-n", "test", "-f", "/etc/ufw/sysctl.conf"]:
            return 0, ""
        if args == ["sudo", "-n", "cat", "/etc/ufw/sysctl.conf"]:
            return 0, ufw_sysctl_content["text"]
        if args[:4] == ["sudo", "-n", "cp", "-a"]:
            assert args[4] == "/etc/ufw/sysctl.conf"
            assert args[5].startswith("/etc/ufw/sysctl.conf.netmon-backup-")
            return 0, "backup"
        if args[:3] == ["sudo", "-n", "cp"] and args[4] == "/etc/ufw/sysctl.conf":
            ufw_sysctl_content["text"] = (
                __import__("pathlib").Path(args[3]).read_text(encoding="utf-8")
            )
            return 0, "copied"
        if args == ["sudo", "-n", "chmod", "0644", "/etc/ufw/sysctl.conf"]:
            return 0, "mode"
        if args == [
            "sudo",
            "-n",
            "sysctl",
            "-e",
            "-q",
            "-p",
            "/etc/ufw/sysctl.conf",
        ]:
            return 0, "loaded"
        raise AssertionError(args)

    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )

    ok = security_audit_controller.apply_security_baseline_ufw(
        app,
        run_cmd_fn=fake_run_cmd,
        askyesno_fn=lambda *args, **kwargs: seen.__setitem__(
            "confirm", seen["confirm"] + 1
        )
        or True,
        showinfo_fn=lambda *args, **kwargs: seen.__setitem__("info", seen["info"] + 1),
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["confirm"] == 1
    assert seen["info"] == 1
    assert seen["rerun"] == 1
    assert any(cmd[-3:] == ("allow", "in", "on", "lo")[-3:] for cmd in command_log)
    assert any(cmd[-3:] == ("allow", "out", "on", "lo")[-3:] for cmd in command_log)
    assert any(
        "Security Baseline UFW-Haertung angewendet" in message
        for message in app.log_messages
    )
    assert "net/ipv4/conf/all/log_martians=1" in ufw_sysctl_content["text"]
    assert "net/ipv4/conf/default/log_martians=1" in ufw_sysctl_content["text"]
    assert any(
        "Security Baseline UFW-sysctl" in message for message in app.log_messages
    )
    assert any("Weitere Dienstfreigaben" in message for message in app.log_messages)


def test_build_ufw_sysctl_override_content_updates_log_martians_only():
    content = "\n".join(
        [
            "# UFW sysctl",
            "net/ipv4/conf/all/log_martians=0",
            "net/ipv4/conf/default/log_martians=0",
            "net/ipv4/conf/all/accept_redirects=0",
        ]
    )

    rendered, changed = security_audit_controller._build_ufw_sysctl_override_content(
        content,
        security_audit_controller.SECURITY_BASELINE_UFW_SYSCTL_OVERRIDES,
    )

    assert changed is True
    assert "net/ipv4/conf/all/log_martians=1" in rendered
    assert "net/ipv4/conf/default/log_martians=1" in rendered
    assert "net/ipv4/conf/all/accept_redirects=0" in rendered


def test_apply_security_baseline_profile_runs_supported_steps_once(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"confirm": 0, "sudo": 0, "sysctl": [], "ufw": [], "rerun": 0, "info": []}

    def fake_sysctl(_app, **kwargs):
        seen["sysctl"].append(kwargs)
        return True

    def fake_ufw(_app, **kwargs):
        seen["ufw"].append(kwargs)
        return True

    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_sysctl",
        fake_sysctl,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_ufw",
        fake_ufw,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )
    app.ensure_sudo_session = (
        lambda reason: seen.__setitem__("sudo", seen["sudo"] + 1)
        or reason == "Security Baseline Profil-Haertung anwenden"
    )

    ok = security_audit_controller.apply_security_baseline_profile(
        app,
        askyesno_fn=lambda *args, **kwargs: seen.__setitem__(
            "confirm", seen["confirm"] + 1
        )
        or True,
        showinfo_fn=lambda _title, message, parent=None: seen["info"].append(message),
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["confirm"] == 1
    assert seen["sudo"] == 1
    assert seen["rerun"] == 1
    assert seen["sysctl"][0]["require_confirmation"] is False
    assert seen["sysctl"][0]["require_sudo_session"] is False
    assert seen["sysctl"][0]["rerun_baseline"] is False
    assert seen["ufw"][0]["require_confirmation"] is False
    assert seen["ufw"][0]["require_sudo_session"] is False
    assert seen["ufw"][0]["rerun_baseline"] is False
    assert "Angewendete Schritte: sysctl, ufw" in seen["info"][0]
    assert "Rollback-Hinweise" in seen["info"][0]


def test_apply_security_baseline_profile_applies_optional_services_for_desktop_safe(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "desktop_safe_v1"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"confirm": 0, "sudo": 0, "sysctl": [], "ufw": [], "rerun": 0, "info": []}
    command_log = []

    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_sysctl",
        lambda _app, **kwargs: seen["sysctl"].append(kwargs) or True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_ufw",
        lambda _app, **kwargs: seen["ufw"].append(kwargs) or True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )
    app.ensure_sudo_session = (
        lambda reason: seen.__setitem__("sudo", seen["sudo"] + 1) or True
    )

    def fake_run_cmd(args, timeout=0):
        command_log.append(tuple(args))
        if args == [
            "systemctl",
            "list-unit-files",
            "whoopsie.service",
            "--no-legend",
            "--no-pager",
        ]:
            return 0, "whoopsie.service enabled"
        if args == [
            "systemctl",
            "list-unit-files",
            "systemd-bsod.service",
            "--no-legend",
            "--no-pager",
        ]:
            return 0, "systemd-bsod.service static"
        if args == ["sudo", "-n", "systemctl", "disable", "--now", "whoopsie.service"]:
            return 0, "Removed whoopsie.service."
        if args == [
            "sudo",
            "-n",
            "systemctl",
            "disable",
            "--now",
            "systemd-bsod.service",
        ]:
            return 0, "Removed systemd-bsod.service."
        raise AssertionError(args)

    ok = security_audit_controller.apply_security_baseline_profile(
        app,
        run_cmd_fn=fake_run_cmd,
        askyesno_fn=lambda *args, **kwargs: seen.__setitem__(
            "confirm", seen["confirm"] + 1
        )
        or True,
        showinfo_fn=lambda _title, message, parent=None: seen["info"].append(message),
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["confirm"] == 2
    assert seen["sudo"] == 1
    assert seen["rerun"] == 1
    assert "Angewendete Schritte: sysctl, ufw, optionale Dienste" in seen["info"][0]
    assert any(
        "Optionaldienst deaktiviert: whoopsie.service" in message
        for message in app.log_messages
    )
    assert any(
        "Optionaldienst deaktiviert: systemd-bsod.service" in message
        for message in app.log_messages
    )
    assert (
        "sudo",
        "-n",
        "systemctl",
        "disable",
        "--now",
        "whoopsie.service",
    ) in command_log


def test_apply_security_baseline_profile_can_skip_optional_services(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "desktop_safe_v1"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"rerun": 0}

    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_sysctl",
        lambda _app, **kwargs: True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_ufw",
        lambda _app, **kwargs: True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )
    app.ensure_sudo_session = lambda reason: True

    def fake_run_cmd(args, timeout=0):
        if args == [
            "systemctl",
            "list-unit-files",
            "whoopsie.service",
            "--no-legend",
            "--no-pager",
        ]:
            return 0, "whoopsie.service enabled"
        if args == [
            "systemctl",
            "list-unit-files",
            "systemd-bsod.service",
            "--no-legend",
            "--no-pager",
        ]:
            return 0, "systemd-bsod.service static"
        raise AssertionError(args)

    answers = iter([True, False])
    ok = security_audit_controller.apply_security_baseline_profile(
        app,
        run_cmd_fn=fake_run_cmd,
        askyesno_fn=lambda *args, **kwargs: next(answers),
        showinfo_fn=lambda *args, **kwargs: None,
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["rerun"] == 1
    assert any(
        "Optionaldienste übersprungen" in message for message in app.log_messages
    )


def test_apply_security_baseline_profile_prefers_custom_confirmation_dialog(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"confirm": [], "rerun": 0}

    app.confirm_security_baseline_apply = (
        lambda title, **kwargs: seen["confirm"].append((title, kwargs)) or True
    )
    app.ensure_sudo_session = lambda reason: True

    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_sysctl",
        lambda _app, **kwargs: True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_ufw",
        lambda _app, **kwargs: True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )

    ok = security_audit_controller.apply_security_baseline_profile(
        app,
        showinfo_fn=lambda *args, **kwargs: None,
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["rerun"] == 1
    assert len(seen["confirm"]) == 1
    assert seen["confirm"][0][0] == "Baseline-Haertung anwenden"
    assert seen["confirm"][0][1]["profile_name"] == "Desktop / Development"
    assert "Sysctl Drop-in" in seen["confirm"][0][1]["preview_text"]
    assert "UFW Defaults" in seen["confirm"][0][1]["preview_text"]


def test_apply_security_baseline_profile_uses_custom_dialog_for_default_askyesno(
    monkeypatch,
):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"confirm": 0, "rerun": 0}

    app.confirm_security_baseline_apply = (
        lambda title, **kwargs: seen.__setitem__("confirm", seen["confirm"] + 1) or True
    )
    app.ensure_sudo_session = lambda reason: True

    monkeypatch.setattr(
        security_audit_controller.messagebox,
        "askyesno",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("plain askyesno should not be used")
        ),
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_sysctl",
        lambda _app, **kwargs: True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_ufw",
        lambda _app, **kwargs: True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )

    ok = security_audit_controller.apply_security_baseline_profile(
        app,
        askyesno_fn=security_audit_controller.messagebox.askyesno,
        showinfo_fn=lambda *args, **kwargs: None,
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["confirm"] == 1
    assert seen["rerun"] == 1


def test_app_value_falls_back_to_bound_methods():
    app = netmon_app.App.__new__(netmon_app.App)

    value = security_audit_controller._app_value(
        app,
        "confirm_security_baseline_apply",
    )

    assert callable(value)


def test_apply_security_baseline_profile_stops_after_partial_failure(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"rerun": 0}

    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_sysctl",
        lambda _app, **kwargs: True,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "apply_security_baseline_ufw",
        lambda _app, **kwargs: False,
    )
    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )
    app.ensure_sudo_session = lambda reason: True

    ok = security_audit_controller.apply_security_baseline_profile(
        app,
        askyesno_fn=lambda *args, **kwargs: True,
        showinfo_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showinfo called")
        ),
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is False
    assert seen["rerun"] == 0
    assert any(
        "teilweise angewendet: sysctl" in message for message in app.log_messages
    )


def test_apply_security_baseline_sysctl_writes_dropin_and_reruns_checks(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.ensure_sudo_session = (
        lambda reason: reason == "Security Baseline Sysctl-Haertung anwenden"
    )
    app._new_rollback_transaction = netmon_app.App._new_rollback_transaction.__get__(
        app, netmon_app.App
    )
    app.log_messages = []
    app.log_safe = app.log_messages.append
    app.log_debug_safe = lambda _msg: None
    app.security_baseline_profile_id = "zorin_desktop_development"

    monkeypatch.setattr(
        security_audit_controller,
        "_sysctl_baseline_specs",
        lambda _app=None: [
            {
                "id": "sysctl.kernel.kptr_restrict",
                "expected": "2",
                "check_kind": "sysctl",
            },
            {"id": "sysctl.kernel.sysrq", "expected": "0", "check_kind": "sysctl"},
        ],
    )
    monkeypatch.setattr(
        security_audit_controller,
        "_sysctl_dropin_path",
        lambda _app=None: "/etc/sysctl.d/99-zz-netmon-hardening.conf",
    )

    seen = {"rerun": 0, "confirm": 0, "info": 0}

    def fake_run_cmd(args, timeout=0):
        if args[:4] == ["sudo", "-n", "test", "-f"]:
            return 1, ""
        if args[:3] == ["sudo", "-n", "cp"]:
            return 0, ""
        if args[:4] == ["sudo", "-n", "chmod", "0644"]:
            return 0, ""
        if args[:4] == ["sudo", "-n", "sysctl", "--system"]:
            return 0, "sysctl reloaded"
        raise AssertionError(args)

    monkeypatch.setattr(
        security_audit_controller,
        "run_security_baseline_checks",
        lambda _app, run_cmd_fn=None: seen.__setitem__("rerun", seen["rerun"] + 1),
    )

    ok = security_audit_controller.apply_security_baseline_sysctl(
        app,
        run_cmd_fn=fake_run_cmd,
        askyesno_fn=lambda *args, **kwargs: seen.__setitem__(
            "confirm", seen["confirm"] + 1
        )
        or True,
        showinfo_fn=lambda *args, **kwargs: seen.__setitem__("info", seen["info"] + 1),
        showerror_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("showerror called")
        ),
    )

    assert ok is True
    assert seen["confirm"] == 1
    assert seen["info"] == 1
    assert seen["rerun"] == 1
    assert "Security Baseline Sysctl-Haertung angewendet" in app.log_messages[-1]


def test_lynis_findings_parser_groups_relevant_lines():
    findings = security_audit_controller._parse_lynis_findings(
        "\n".join(
            [
                "Warning: Firewall disabled",
                "Suggestion: Enable AppArmor",
                "Hardening index : 77",
                "OK: Nothing special",
            ]
        )
    )

    assert [item["category"] for item in findings] == [
        "Warnung",
        "Empfehlung",
        "Hardening",
    ]
    assert findings[0]["line"] == "Warning: Firewall disabled"


def test_lynis_references_use_structured_rules_and_clear_stale_dynamic_matches():
    app = netmon_app.App.__new__(netmon_app.App)
    app.lynis_last_output = "Warning: Firewall disabled\nSuggestion: Enable AppArmor"
    rows = [
        {
            "id": "fw.ufw_active",
            "lynis_reference": "old",
            "lynis_reference_dynamic": True,
        },
        {
            "id": "sysctl.net.ipv4.conf.all.rp_filter",
            "lynis_reference": "static rp_filter explanation",
        },
    ]

    attached = security_audit_controller._attach_lynis_references(app, rows)

    assert attached[0]["lynis_reference"].startswith("Warnung:")
    assert "Firewall disabled" in attached[0]["lynis_reference"]
    assert attached[0]["lynis_findings"][0]["category"] == "Warnung"
    assert attached[1]["lynis_reference"] == "static rp_filter explanation"

    app.lynis_last_output = "Suggestion: Enable AppArmor"
    refreshed = security_audit_controller._attach_lynis_references(app, attached)

    assert refreshed[0]["lynis_reference"] == ""
    assert "lynis_findings" not in refreshed[0]


def _secure_boot_spec():
    return next(
        item
        for item in security_audit_controller.SECURITY_BASELINE_CHECKS
        if item["id"] == "boot.secure_boot_state"
    )


def _evaluate_secure_boot_output(rc, output, profile="Desktop / Development"):
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_profile = profile
    return security_audit_controller._evaluate_baseline_check(
        _secure_boot_spec(),
        run_cmd_fn=lambda _cmd, timeout=0: (rc, output),
        app=app,
    )


def test_secure_boot_enabled_is_fulfilled():
    result = _evaluate_secure_boot_output(0, "SecureBoot enabled")

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "aktiviert"
    assert result["secure_boot_supported"] is True
    assert result["secure_boot_enabled"] is True
    assert result["check_success"] is True


def test_secure_boot_disabled_desktop_profile_is_manual_hint():
    result = _evaluate_secure_boot_output(0, "SecureBoot disabled")

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "deaktiviert"
    assert result["severity"] == "Hinweis"
    assert result["secure_boot_enabled"] is False


def test_secure_boot_disabled_setup_mode_is_visible_in_actual_value():
    result = _evaluate_secure_boot_output(
        0,
        "SecureBoot disabled\nPlatform is in Setup Mode",
    )

    assert result["status"] == "Manuelle Pruefung erforderlich"
    assert result["actual"] == "deaktiviert; Plattform im Setup Mode"
    assert result["platform_mode"] == "setup"
    assert "Setup Mode" in result["reason"]


def test_secure_boot_enabled_user_mode_is_visible_in_actual_value():
    result = _evaluate_secure_boot_output(
        0,
        "SecureBoot enabled\nPlatform is in User Mode",
    )

    assert result["status"] == "Erfuellt"
    assert result["actual"] == "aktiviert; Plattform im User Mode"
    assert result["platform_mode"] == "user"


def test_secure_boot_legacy_bios_or_no_efi_is_not_applicable():
    result = _evaluate_secure_boot_output(
        1,
        "EFI variables are not supported on this system",
    )

    assert result["status"] == "Nicht anwendbar"
    assert result["actual"] == "nicht unterstuetzt oder kein UEFI-Zugriff"
    assert result["secure_boot_supported"] is False


def test_secure_boot_mokutil_missing_requires_manual_review():
    result = _evaluate_secure_boot_output(127, "mokutil: not found")

    assert result["status"] == "Fehler bei der Pruefung"
    assert result["actual"] == "Pruefung fehlgeschlagen"
    assert result["mokutil_available"] is False
    assert result["check_success"] is False


def test_secure_boot_efi_access_error_requires_manual_review():
    result = _evaluate_secure_boot_output(1, "Failed to read SecureBoot")

    assert result["status"] == "Fehler bei der Pruefung"
    assert result["actual"] == "Pruefung fehlgeschlagen"
    assert result["check_error"] == "Failed to read SecureBoot"


def test_secure_boot_unexpected_localized_output_requires_manual_review():
    result = _evaluate_secure_boot_output(0, "SecureBoot deaktiviert")

    assert result["status"] == "Fehler bei der Pruefung"
    assert result["actual"] == "Pruefung fehlgeschlagen"
    assert result["check_success"] is False


def test_secure_boot_disabled_server_profile_is_not_fulfilled():
    result = _evaluate_secure_boot_output(0, "SecureBoot disabled", "Server / Haertung")

    assert result["status"] == "Nicht erfuellt"
    assert result["severity"] == "Mittel"
    assert "setzt aktivierten Secure Boot voraus" in result["reason"]


def test_secure_boot_disabled_testlab_and_dual_boot_profiles_are_manual_hints():
    testlab = _evaluate_secure_boot_output(0, "SecureBoot disabled", "Testlabor")
    dual_boot = _evaluate_secure_boot_output(0, "SecureBoot disabled", "Dual-Boot")

    assert testlab["status"] == "Manuelle Pruefung erforderlich"
    assert testlab["severity"] == "Hinweis"
    assert dual_boot["status"] == "Manuelle Pruefung erforderlich"
    assert dual_boot["severity"] == "Hinweis"


def test_secure_boot_command_forces_c_locale():
    assert _secure_boot_spec()["command"] == "LANG=C LC_ALL=C mokutil --sb-state"


def test_language_files_include_security_baseline_keys():
    import json

    with open("netmon/lang/de.json", "r", encoding="utf-8") as handle:
        de = json.load(handle)
    with open("netmon/lang/en.json", "r", encoding="utf-8") as handle:
        en = json.load(handle)

    for key in (
        "baseline_group_summary",
        "baseline_group_checks",
        "baseline_group_details",
        "lynis_subtab_baseline",
        "lynis_subtab_hardening",
        "lynis_subtab_audit",
        "baseline_group_hardening",
        "baseline_group_hardening_actions",
        "group_right_quick_actions",
        "baseline_btn_run",
        "baseline_btn_show_all",
        "baseline_btn_show_deviations",
        "baseline_btn_show_manual",
        "baseline_btn_show_kernel",
        "baseline_btn_apply_all",
        "baseline_btn_timeshift",
        "baseline_btn_apply_sysctl",
        "baseline_btn_apply_ufw",
        "baseline_btn_export_transfer",
        "baseline_btn_import_transfer",
        "baseline_btn_show_transfer",
        "baseline_btn_compare_transfer",
        "baseline_btn_clear_transfer",
        "baseline_hardening_intro",
        "baseline_hardening_scope",
        "baseline_hardening_timeshift_hint",
        "baseline_optional_services_overview_none",
        "baseline_optional_services_overview_value",
        "baseline_timeshift_title",
        "baseline_timeshift_missing",
        "baseline_timeshift_failed",
        "baseline_timeshift_missing_log",
        "baseline_timeshift_started_log",
        "baseline_timeshift_failed_log",
        "baseline_transfer_status_default",
        "baseline_transfer_status_loaded",
        "baseline_detail_note_text",
        "baseline_detail_root_required",
        "baseline_detail_privilege_source",
        "baseline_detail_profiles",
        "baseline_detail_platform",
        "baseline_detail_apply_supported",
        "baseline_detail_apply_strategy",
        "baseline_detail_remediation",
        "baseline_detail_rollback",
        "baseline_apply_sysctl_title",
        "baseline_apply_sysctl_confirm",
        "baseline_apply_sysctl_failed",
        "baseline_apply_sysctl_success",
        "baseline_apply_all_title",
        "baseline_apply_all_unsupported",
        "baseline_apply_all_confirm",
        "baseline_apply_all_success",
        "baseline_apply_all_applied_steps",
        "baseline_apply_all_rollback_label",
        "baseline_transfer_export_title",
        "baseline_transfer_export_failed",
        "baseline_transfer_export_success",
        "baseline_transfer_import_title",
        "baseline_transfer_import_failed",
        "baseline_transfer_import_apply_now",
        "baseline_transfer_import_success",
        "baseline_transfer_clear_title",
        "baseline_transfer_clear_success",
        "baseline_transfer_show_title",
        "baseline_transfer_show_missing",
        "baseline_transfer_show_heading",
        "baseline_transfer_show_notes",
        "baseline_transfer_compare_title",
        "baseline_transfer_compare_missing",
        "baseline_transfer_compare_heading",
        "baseline_transfer_compare_section_profile",
        "baseline_transfer_compare_section_sysctl",
        "baseline_transfer_compare_section_ufw",
        "baseline_transfer_compare_local",
        "baseline_transfer_compare_imported",
        "baseline_transfer_compare_none",
        "tooltip_right_quick_timeshift",
        "baseline_apply_ufw_title",
        "baseline_apply_ufw_confirm",
        "baseline_apply_ufw_status_failed",
        "baseline_apply_ufw_verify_failed",
        "baseline_apply_ufw_success",
    ):
        assert key in de
        assert key in en


def test_security_baseline_state_persists_via_existing_security_baseline_file(tmp_path):
    app = netmon_app.App.__new__(netmon_app.App)
    app.security_baseline_path = str(tmp_path / "security_base.json")
    app.integrity_baseline = {"a": {"sha": "x"}}
    app.device_baseline = {"/dev/input/event1": "input-event"}
    app.input_access_baseline = {"/dev/input/event1": {"123": "testproc"}}
    app.security_baseline_last_checked = "19.07.2026 01:53"
    app.security_baseline_results = [
        {"id": "fw.ufw_active", "status": "Erfuellt", "title": "UFW aktiv"}
    ]
    app.lynis_last_result = {"hardening_index": "77", "warnings": "0", "tests": "248"}
    app.lynis_security_baseline_state = (
        security_audit_controller._lynis_security_baseline_state(app)
    )

    assert app._save_security_baseline()

    loaded_app = netmon_app.App.__new__(netmon_app.App)
    loaded_app.security_baseline_path = app.security_baseline_path

    assert loaded_app._load_security_baseline()
    assert (
        loaded_app.lynis_security_baseline_state["last_checked"] == "19.07.2026 01:53"
    )
    assert (
        loaded_app.lynis_security_baseline_state["results"][0]["id"] == "fw.ufw_active"
    )

    assert security_audit_controller.restore_security_baseline_state(loaded_app) is True
    assert loaded_app.security_baseline_last_checked == "19.07.2026 01:53"
    assert loaded_app.security_baseline_results[0]["status"] == "Erfuellt"


def test_run_lynis_quick_starts_expected_scan(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    seen = {"log": []}

    monkeypatch.setattr(netmon_app, "has_cmd", lambda name: name == "lynis")

    class ImmediateThread:
        def __init__(self, target=None, args=(), daemon=None):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(netmon_app.threading, "Thread", ImmediateThread)

    def fake_run_cmd(cmd, timeout):
        seen["cmd"] = cmd
        seen["timeout"] = timeout
        return 0, "\x1b[1;32mOK\x1b[0m"

    monkeypatch.setattr(netmon_app, "run_cmd", fake_run_cmd)
    app.after = lambda _delay, callback: callback()
    app.open_lynis_tab = lambda: seen.setdefault("opened", 0) or seen.__setitem__(
        "opened", seen.get("opened", 0) + 1
    )
    app.clear_lynis_output = lambda: seen.setdefault("cleared", 0) or seen.__setitem__(
        "cleared", seen.get("cleared", 0) + 1
    )
    app.update_lynis_output = lambda text, append=False: seen.setdefault(
        "outputs", []
    ).append((text, append))
    app.log = seen["log"].append
    app.log_safe = seen["log"].append
    app.lynis_status_var = DummyVar()
    app.lynis_hardening_index_var = DummyVar("stale")
    app.lynis_summary_var = DummyVar()
    app.dep_status = {"lynis": True}
    app.btn_lynis_quick = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()
    app.btn_lynis_full = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()

    app.run_lynis_quick()

    assert seen["cmd"] == ["lynis", "audit", "system", "--no-colors"]
    assert seen["timeout"] == 120
    assert app.lynis_last_output == "=== Lynis Schnellaudit (eingeschränkt) ===\nOK"
    assert app.lynis_hardening_index_var.get() == "Hardening Index: -"
    assert seen["log"][-1] == "Lynis Schnellaudit abgeschlossen."


def test_run_lynis_full_requests_sudo_and_uses_expected_scan(monkeypatch):
    app = netmon_app.App.__new__(netmon_app.App)
    seen = {"log": []}

    monkeypatch.setattr(netmon_app, "has_cmd", lambda name: name == "lynis")
    monkeypatch.setattr(
        netmon_app.messagebox,
        "showinfo",
        lambda title, message, parent=None: seen.setdefault(
            "info", (title, message, parent)
        ),
    )

    class ImmediateThread:
        def __init__(self, target=None, args=(), daemon=None):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    monkeypatch.setattr(netmon_app.threading, "Thread", ImmediateThread)

    def fake_run_cmd(cmd, timeout):
        seen["cmd"] = cmd
        seen["timeout"] = timeout
        return 0, "Warning"

    monkeypatch.setattr(netmon_app, "run_cmd", fake_run_cmd)
    app.after = lambda _delay, callback: callback()
    app.open_lynis_tab = lambda: None
    app.clear_lynis_output = lambda: None
    app.update_lynis_output = lambda text, append=False: seen.setdefault(
        "outputs", []
    ).append((text, append))
    app.log = seen["log"].append
    app.log_safe = seen["log"].append
    app.lynis_status_var = DummyVar()
    app.lynis_hardening_index_var = DummyVar("stale")
    app.lynis_summary_var = DummyVar()
    app.dep_status = {"lynis": True}
    app.ensure_sudo_session = (
        lambda reason: seen.setdefault("sudo_reason", reason) or True
    )
    app.btn_lynis_quick = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()
    app.btn_lynis_full = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()

    app.run_lynis_full()

    assert seen["info"][0] == "Lynis Vollscan"
    assert seen["sudo_reason"] == "Lynis Full Security Scan"
    assert seen["cmd"] == ["sudo", "lynis", "audit", "system", "--no-colors"]
    assert seen["timeout"] == 600
    assert app.lynis_hardening_index_var.get() == "Hardening Index: -"
    assert (
        app.lynis_last_output
        == "=== Lynis Vollständiger Sicherheitsscan (sudo) ===\nWarning"
    )
    assert seen["log"][-1] == "Lynis Vollscan abgeschlossen."


def test_finish_lynis_audit_marks_timeout_cleanly():
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []

    app.lynis_status_var = DummyVar()
    app.lynis_hardening_index_var = DummyVar()
    app.lynis_summary_var = DummyVar()
    app.dep_status = {"lynis": True}
    app.btn_lynis_quick = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()
    app.btn_lynis_full = type(
        "DummyButton",
        (),
        {"configure": lambda self, **kwargs: setattr(self, "last", kwargs)},
    )()
    app.update_lynis_output_calls = []
    app.update_lynis_output = (
        lambda text, append=False: app.update_lynis_output_calls.append((text, append))
    )
    app.log = logs.append

    app._finish_lynis_audit(124, "Command timed out", mode="full")

    assert app.lynis_status_var.get() == "Timeout"
    assert app.lynis_hardening_index_var.get() == "Hardening Index: -"
    assert logs[-1] == "Lynis Vollscan Timeout (rc=124)."


# ── Runde 10: Sysctl-Injektion ueber importiertes Transferpaket (R10-01) ──────


def _malicious_sysctl_transfer_package(entry):
    """Gueltiges Transfer-Geruest mit einem manipulierten Sysctl-Eintrag."""
    return {
        "schema": "netmon.security-baseline.transfer",
        "schema_version": 1,
        "baseline": {
            "id": "zorin_desktop_development",
            "profile": "Desktop / Development",
            "os_family": "debian_like",
        },
        "sysctl": {
            "dropin_path": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
            "entries": [entry],
        },
    }


def test_sanitize_transfer_sysctl_entries_rejects_unknown_key():
    with pytest.raises(ValueError, match="nicht erlaubten Sysctl-Schluessel"):
        security_audit_controller._sanitize_transfer_sysctl_entries(
            [{"key": "kernel.core_pattern", "expected": "|/tmp/evil.sh"}]
        )


def test_sanitize_transfer_sysctl_entries_rejects_pipe_and_newline_value():
    with pytest.raises(ValueError, match="ungueltigen Sysctl-Wert"):
        security_audit_controller._sanitize_transfer_sysctl_entries(
            [
                {
                    "key": "kernel.kptr_restrict",
                    "expected": "2\nkernel.core_pattern = |/tmp/x",
                }
            ]
        )
    with pytest.raises(ValueError, match="ungueltigen Sysctl-Wert"):
        security_audit_controller._sanitize_transfer_sysctl_entries(
            [{"key": "kernel.kptr_restrict", "expected": "|/tmp/evil.sh"}]
        )


def test_sanitize_transfer_sysctl_entries_derives_id_from_key_only():
    # Ein boesartiges id-Feld darf nicht uebernommen werden: die id wird
    # ausschliesslich aus dem validierten key abgeleitet.
    normalized = security_audit_controller._sanitize_transfer_sysctl_entries(
        [
            {
                "id": "sysctl.kernel.core_pattern",
                "key": "kernel.kptr_restrict",
                "expected": "2",
            }
        ]
    )

    assert normalized[0]["id"] == "sysctl.kernel.kptr_restrict"
    assert normalized[0]["expected"] == "2"


def test_sanitize_transfer_sysctl_entries_accepts_legitimate_baseline_keys():
    normalized = security_audit_controller._sanitize_transfer_sysctl_entries(
        [
            {"key": "kernel.kptr_restrict", "expected": "2"},
            {"key": "net.ipv4.conf.all.rp_filter", "expected": "2"},
        ]
    )

    assert [item["id"] for item in normalized] == [
        "sysctl.kernel.kptr_restrict",
        "sysctl.net.ipv4.conf.all.rp_filter",
    ]


def test_validate_transfer_package_rejects_core_pattern_injection():
    package = _malicious_sysctl_transfer_package(
        {"key": "kernel.core_pattern", "expected": "|/tmp/evil.sh"}
    )

    with pytest.raises(ValueError):
        security_audit_controller._validate_security_baseline_transfer_package(package)


def test_build_sysctl_dropin_content_drops_injected_directive():
    # Zweite Verteidigungslinie: selbst wenn ein manipulierter Spec direkt an den
    # Dropin-Builder gelangt, darf die injizierte Direktive nicht geschrieben werden.
    content = security_audit_controller._build_sysctl_dropin_content(
        [
            {"id": "sysctl.kernel.core_pattern", "expected": "|/tmp/evil.sh"},
            {"id": "sysctl.kernel.kptr_restrict", "expected": "2"},
        ]
    )

    assert "core_pattern" not in content
    assert "/tmp/evil.sh" not in content
    assert "kernel.kptr_restrict = 2" in content


def test_build_sysctl_dropin_content_drops_multiline_value():
    content = security_audit_controller._build_sysctl_dropin_content(
        [{"id": "sysctl.kernel.kptr_restrict", "expected": "2\nkernel.sysrq = 1"}]
    )

    # Der mehrzeilige Wert wird komplett verworfen (kein Teil-Schreiben).
    assert "kptr_restrict" not in content
    assert "sysrq" not in content


def test_import_transfer_with_injected_sysctl_is_refused_without_apply(tmp_path):
    package = _malicious_sysctl_transfer_package(
        {"key": "kernel.core_pattern", "expected": "|/tmp/evil.sh"}
    )
    path = tmp_path / "malicious-transfer.json"
    path.write_text(__import__("json").dumps(package), encoding="utf-8")

    app = netmon_app.App.__new__(netmon_app.App)
    app.tr = lambda _key, fallback: fallback
    app.security_baseline_profile_id = "zorin_desktop_development"
    app.log_messages = []
    app.log_safe = app.log_messages.append
    seen = {"error": 0}

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("Apply-Pfad darf bei manipuliertem Paket nie laufen")

    ok = security_audit_controller.import_security_baseline_transfer(
        app,
        str(path),
        run_cmd_fn=fail_if_called,
        askyesno_fn=fail_if_called,
        showinfo_fn=fail_if_called,
        showerror_fn=lambda *args, **kwargs: seen.__setitem__(
            "error", seen["error"] + 1
        ),
    )

    assert ok is False
    assert seen["error"] == 1


# ── Runde-11-Haertungen (UFW-sysctl) ─────────────────────────────────────────
# R11-H1: Die Schreibsenke /etc/ufw/sysctl.conf traegt jetzt dieselbe
# Key-Allowlist und Wert-Validierung wie _render_sysctl_dropin_content.


def test_build_ufw_sysctl_override_content_rejects_key_outside_allowlist():
    content = "# UFW sysctl\nnet/ipv4/conf/all/log_martians=0\n"

    rendered, changed = security_audit_controller._build_ufw_sysctl_override_content(
        content,
        {"kernel.core_pattern": "|/tmp/payload"},
    )

    assert changed is False
    assert "core_pattern" not in rendered
    assert "payload" not in rendered


def test_build_ufw_sysctl_override_content_rejects_invalid_value():
    content = "# UFW sysctl\nnet/ipv4/conf/all/log_martians=0\n"

    rendered, changed = security_audit_controller._build_ufw_sysctl_override_content(
        content,
        {"net.ipv4.conf.all.log_martians": "1\nkernel.core_pattern=|/tmp/payload"},
    )

    assert changed is False
    assert "core_pattern" not in rendered
    assert "net/ipv4/conf/all/log_martians=0" in rendered


def test_build_ufw_sysctl_override_content_keeps_allowed_entries():
    content = "# UFW sysctl\nnet/ipv4/conf/all/log_martians=0\n"

    rendered, changed = security_audit_controller._build_ufw_sysctl_override_content(
        content,
        {
            "net.ipv4.conf.all.log_martians": "1",
            "kernel.core_pattern": "|/tmp/payload",
        },
    )

    assert changed is True
    assert "net/ipv4/conf/all/log_martians=1" in rendered
    assert "core_pattern" not in rendered


# R11-H2: run_cmd fuehrt stderr mit stdout zusammen. Eine sudo-Warnung mit rc=0
# darf bei Read-Modify-Write nicht als root in eine Root-Konfigdatei
# zurueckgeschrieben werden - der Lauf bricht stattdessen ab.


@pytest.mark.parametrize(
    "line",
    [
        "sudo: unable to resolve host proglab: Name or service not known",
        "sudo: unable to send audit message: Operation not permitted",
        "irgendein freitext ohne gleichheitszeichen",
    ],
)
def test_implausible_sysctl_config_line_detects_stderr_noise(line):
    content = f"{line}\n# UFW sysctl\nnet/ipv4/conf/all/log_martians=0\n"

    assert security_audit_controller._implausible_sysctl_config_line(content) == line


def test_implausible_sysctl_config_line_accepts_clean_config():
    content = "\n".join(
        [
            "# UFW sysctl",
            "",
            "net/ipv4/conf/all/log_martians=0",
            "net.ipv4.conf.default.log_martians = 1",
            "  kernel.dmesg_restrict=1",
        ]
    )

    assert security_audit_controller._implausible_sysctl_config_line(content) == ""


def test_apply_ufw_sysctl_overrides_aborts_on_stderr_contaminated_read():
    calls = []
    noise = "sudo: unable to resolve host proglab: Name or service not known"

    def fake_runner(args, timeout=None):
        calls.append(list(args))
        if args[:3] == ["sudo", "-n", "test"]:
            return 0, ""
        if args[:3] == ["sudo", "-n", "cat"]:
            return 0, f"{noise}\nnet/ipv4/conf/all/log_martians=0\n"
        return 0, ""

    ok, message = security_audit_controller._apply_ufw_sysctl_overrides(
        "/etc/ufw/sysctl.conf",
        run_cmd_fn=fake_runner,
    )

    assert ok is False
    assert "Unerwarteter Inhalt" in message
    # Entscheidend: kein cp/chmod/sysctl -p nach dem verseuchten Read.
    assert not any(call[2] in {"cp", "chmod", "sysctl"} for call in calls)


def test_read_existing_sysctl_dropin_raises_on_stderr_contaminated_read():
    def fake_runner(args, timeout=None):
        if args[:3] == ["sudo", "-n", "test"]:
            return 0, ""
        return 0, "sudo: unable to send audit message: Operation not permitted\n"

    with pytest.raises(RuntimeError, match="Unerwarteter Inhalt"):
        security_audit_controller._read_existing_sysctl_dropin(
            "/etc/sysctl.d/99-zz-netmon-hardening.conf",
            run_cmd_fn=fake_runner,
        )


# R11-Nachtest: Der rp_filter-Zweig von _evaluate_baseline_check haengt den
# ufw-Konflikthinweis an die Begruendung an. Ein Validierungs-Agent hatte hier
# eine Diagnose-Luecke gemeldet, weil der Zweig den Low-Level-Helfer
# _sysctl_ufw_override_value nicht direkt aufruft - er nutzt aber den Wrapper
# _sysctl_ufw_override_hint. Der Test haelt das Verhalten fest.


def _rp_filter_spec():
    return [
        spec
        for spec in security_audit_controller.SECURITY_BASELINE_CHECKS
        if spec.get("id") == "sysctl.net.ipv4.conf.all.rp_filter"
    ][0]


def test_rp_filter_branch_reports_ufw_override_conflict(monkeypatch):
    files = {
        "/etc/sysctl.d/99-zz-netmon-hardening.conf": "net.ipv4.conf.all.rp_filter = 2\n",
        "/etc/ufw/sysctl.conf": "# ufw\nnet/ipv4/conf/all/rp_filter=1\n",
    }
    monkeypatch.setattr(
        security_audit_controller, "_read_text_file", lambda path: files[str(path)]
    )

    result = security_audit_controller._evaluate_baseline_check(
        _rp_filter_spec(),
        run_cmd_fn=lambda _args, timeout=None: (0, "1"),
    )

    assert result["status"] == "Bewusste Abweichung"
    assert "/etc/ufw/sysctl.conf setzt denselben Wert auf 1" in result["reason"]


def test_rp_filter_branch_omits_hint_without_conflict(monkeypatch):
    files = {
        "/etc/sysctl.d/99-zz-netmon-hardening.conf": "net.ipv4.conf.all.rp_filter = 2\n",
        "/etc/ufw/sysctl.conf": "# ufw ohne rp_filter\n",
    }
    monkeypatch.setattr(
        security_audit_controller, "_read_text_file", lambda path: files[str(path)]
    )

    result = security_audit_controller._evaluate_baseline_check(
        _rp_filter_spec(),
        run_cmd_fn=lambda _args, timeout=None: (0, "2"),
    )

    assert result["status"] == "Erfuellt"
    assert "/etc/ufw/sysctl.conf" not in result["reason"]
