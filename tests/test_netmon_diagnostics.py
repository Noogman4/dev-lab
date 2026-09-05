import json
import inspect
import zipfile
from types import SimpleNamespace

from netmon import app as app_module
from netmon.app import App
from netmon.core import crash, diagnostics, support_bundle
from netmon import main


def test_redact_sensitive_text_masks_known_patterns():
    text = (
        "Authorization: Bearer abc123 "
        "api_key=secret123 "
        "mail test@example.com "
        "path /home/happy/project"
    )

    redacted = diagnostics.redact_sensitive_text(text)

    assert "abc123" not in redacted
    assert "secret123" not in redacted
    assert "test@example.com" not in redacted
    assert "/home/happy" not in redacted
    assert "[EMAIL_REDACTED]" in redacted
    assert "/home/[USER_REDACTED]" in redacted


def test_write_diagnostic_report_writes_structured_json(tmp_path, monkeypatch):
    monkeypatch.setattr(
        diagnostics,
        "get_netmon_documents_dir",
        lambda: str(tmp_path / "Documents" / "NetMon"),
    )
    monkeypatch.setattr(diagnostics, "current_os_label", lambda: "Ubuntu 24.04 LTS")
    monkeypatch.setattr(
        diagnostics,
        "diagnostic_system_info",
        lambda: {
            "os": "Ubuntu 24.04 LTS",
            "platform": "Linux-6.x",
            "system": "Linux",
            "release": "6.x",
            "machine": "x86_64",
            "python_version": "3.12",
            "python_executable": "/usr/bin/python3",
            "distribution": {
                "id": "ubuntu",
                "version_id": "24.04",
                "name": "Ubuntu",
                "pretty_name": "Ubuntu 24.04 LTS",
            },
        },
    )

    path = diagnostics.write_diagnostic_report(
        kind="startup-error",
        title="Startup failure",
        detail="api_key=hidden",
        exc=RuntimeError("boom"),
        context={"last_action": "DNS", "email": "user@example.com"},
    )

    payload = json.loads(
        (
            tmp_path / "Documents" / "NetMon" / "diagnostics" / path.split("/")[-1]
        ).read_text(encoding="utf-8")
    )

    assert path.endswith(".json")
    assert payload["kind"] == "startup-error"
    assert payload["title"] == "Startup failure"
    assert payload["netmon_version"]
    assert payload["system"]["os"] == "Ubuntu 24.04 LTS"
    assert payload["system"]["distribution"]["id"] == "ubuntu"
    assert payload["exception"]["type"] == "RuntimeError"
    assert payload["exception"]["message"] == "boom"
    assert payload["detail"] == "api_key=[REDACTED]"
    assert payload["context"]["email"] == "[EMAIL_REDACTED]"


def test_latest_diagnostic_report_path_returns_newest_report(tmp_path, monkeypatch):
    monkeypatch.setattr(
        diagnostics,
        "get_netmon_documents_dir",
        lambda: str(tmp_path / "Documents" / "NetMon"),
    )
    reports_dir = tmp_path / "Documents" / "NetMon" / "diagnostics"
    reports_dir.mkdir(parents=True, exist_ok=True)
    older = reports_dir / "netmon-crash-20260101-000000-aaaa.json"
    newer = reports_dir / "netmon-crash-20260101-000001-bbbb.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")

    latest = diagnostics.latest_diagnostic_report_path()

    assert latest == str(newer)


def test_diagnostic_reports_dir_uses_documents_folder(tmp_path, monkeypatch):
    docs_dir = tmp_path / "Documents" / "NetMon"
    monkeypatch.setattr(diagnostics, "get_netmon_documents_dir", lambda: str(docs_dir))

    result = diagnostics.diagnostic_reports_dir()

    assert result == str(docs_dir / "diagnostics")
    assert (docs_dir / "diagnostics").is_dir()


def test_write_startup_error_log_returns_log_and_diagnostic_path(tmp_path, monkeypatch):
    log_path = tmp_path / "startup_error.log"
    monkeypatch.setattr(main, "get_startup_error_log_path", lambda: str(log_path))
    monkeypatch.setattr(main, "current_os_label", lambda: "Fedora Linux 42")
    monkeypatch.setattr(
        main,
        "write_diagnostic_report",
        lambda **_kwargs: str(tmp_path / "diag.json"),
    )

    returned_log, diagnostic_path = main._write_startup_error_log(
        "Startup failure",
        detail="Display missing",
    )

    text = log_path.read_text(encoding="utf-8")

    assert returned_log == str(log_path)
    assert diagnostic_path == str(tmp_path / "diag.json")
    assert "Startup failure" in text
    assert "os=Fedora Linux 42" in text
    assert "diagnostic_report=" in text
    assert "Display missing" in text


def test_get_startup_error_log_path_uses_documents_folder(tmp_path, monkeypatch):
    docs_dir = tmp_path / "Documents" / "NetMon"
    monkeypatch.setattr(main, "get_netmon_documents_dir", lambda: str(docs_dir))

    path = main.get_startup_error_log_path()

    assert path == str(docs_dir / "diagnostics" / "startup_error.log")
    assert (docs_dir / "diagnostics").is_dir()


def test_startup_support_form_metadata_collects_fields():
    metadata = main._startup_support_form_metadata(
        detail="DISPLAY fehlt",
        contact_name="Happy",
        contact_email="happy@example.com",
        last_step="NetMon starten",
        repro_status="immer",
        description="Start bricht sofort ab",
    )

    assert metadata["startup_report"]["bootstrap_detail"] == "DISPLAY fehlt"
    assert metadata["startup_report"]["contact_name"] == "Happy"
    assert metadata["startup_report"]["contact_email"] == "happy@example.com"
    assert metadata["startup_report"]["last_step"] == "NetMon starten"
    assert metadata["startup_report"]["repro_status"] == "immer"
    assert metadata["startup_report"]["description"] == "Start bricht sofort ab"


def test_create_startup_support_package_passes_metadata(monkeypatch, tmp_path):
    package_path = tmp_path / "netmon-support-startup.zip"
    package_path.write_text("zip", encoding="utf-8")
    recorded = {}

    monkeypatch.setattr(
        main,
        "create_support_package",
        lambda metadata=None: (
            recorded.setdefault("metadata", metadata),
            str(package_path),
        )[1],
    )

    result = main._create_startup_support_package(
        detail="TkError",
        form_data={
            "contact_name": "Happy",
            "contact_email": "happy@example.com",
            "last_step": "Start aus Menü",
            "repro_status": "immer",
            "description": "Fenster erscheint nicht",
        },
    )

    assert result == str(package_path)
    assert recorded["metadata"]["stage"] == "startup"
    assert recorded["metadata"]["startup_detail"] == "TkError"
    assert recorded["metadata"]["startup_report"]["contact_name"] == "Happy"
    assert (
        recorded["metadata"]["startup_report"]["description"]
        == "Fenster erscheint nicht"
    )


def test_open_support_dir_with_xdg_open_uses_documents_support_dir(
    monkeypatch, tmp_path
):
    docs_dir = tmp_path / "Documents" / "NetMon"
    recorded = {}

    monkeypatch.setattr(main, "get_netmon_documents_dir", lambda: str(docs_dir))
    monkeypatch.setattr(
        main.subprocess,
        "Popen",
        lambda args, **kwargs: (
            recorded.setdefault("args", args),
            recorded.setdefault("kwargs", kwargs),
            object(),
        )[2],
    )

    result = main._open_support_dir_with_xdg_open()

    assert result is True
    assert recorded["args"] == ["xdg-open", str(docs_dir / "support")]


def test_run_system_action_async_requires_phrase_when_strict_protection_is_enabled():
    app = App.__new__(App)
    recorded = {}
    app.strict_protection_var = SimpleNamespace(get=lambda: True)
    app.settings = {"strict_protection": True}
    app.tr = lambda _key, default, **_kwargs: default
    # Inertes Stub-Kommando + Abbruch im Bestätigungsdialog: der Test prüft nur
    # die require_phrase-Weitergabe und darf nie den echten Job-Thread starten
    # (ein echtes ["systemctl", "reboot"] würde den Host ohne Passwort rebooten).
    app._system_action_commands = lambda action: [(["true"], False)]

    def confirm(*_args, **kwargs):
        recorded["kwargs"] = kwargs
        return False

    app._confirm_danger_action = confirm
    app.log = lambda _message: None

    app.run_system_action_async("Reboot")

    assert recorded["kwargs"]["require_phrase"] == "AUSFUEHREN"


def test_run_system_action_async_skips_phrase_when_strict_protection_is_disabled():
    app = App.__new__(App)
    recorded = {}
    app.strict_protection_var = SimpleNamespace(get=lambda: False)
    app.settings = {"strict_protection": False}
    app.tr = lambda _key, default, **_kwargs: default
    app._system_action_commands = lambda action: [(["true"], False)]

    def confirm(*_args, **kwargs):
        recorded["kwargs"] = kwargs
        return False

    app._confirm_danger_action = confirm
    app.log = lambda _message: None

    app.run_system_action_async("Reboot")

    assert recorded["kwargs"]["require_phrase"] == ""


def test_startup_support_dialog_source_mentions_support_folder_and_hint():
    source = inspect.getsource(main._show_startup_support_dialog)

    assert "Supportordner öffnen" in source
    assert "Das Supportpaket kannst du später an den Support" in source


def test_append_crash_dump_returns_diagnostic_path_and_writes_pointer(
    tmp_path, monkeypatch
):
    crash_log = tmp_path / "crash.log"
    monkeypatch.setattr(crash, "CRASH_LOG_PATH", str(crash_log))
    monkeypatch.setattr(crash, "current_os_label", lambda: "Debian GNU/Linux 13")
    monkeypatch.setattr(
        crash,
        "write_diagnostic_report",
        lambda **_kwargs: str(tmp_path / "diag.json"),
    )

    try:
        raise ValueError("kaputt")
    except ValueError as exc:
        diagnostic_path = crash._append_crash_dump(
            "unit-test",
            type(exc),
            exc,
            exc.__traceback__,
        )

    text = crash_log.read_text(encoding="utf-8")

    assert diagnostic_path == str(tmp_path / "diag.json")
    assert "origin=unit-test" in text
    assert "os=Debian GNU/Linux 13" in text
    assert "diagnostic_report=" in text
    assert "ValueError: kaputt" in text


def test_record_diagnostic_action_tracks_last_action_context():
    dummy = SimpleNamespace(
        _diagnostic_last_action="",
        _diagnostic_last_area="",
        _diagnostic_last_action_at="",
        _diagnostic_last_details={},
    )

    context = App._record_diagnostic_action(
        dummy,
        "Tab gewechselt: Security",
        "main-tabs",
        details={"selected_tab": "Security"},
    )

    assert context["action"] == "Tab gewechselt: Security"
    assert context["area"] == "main-tabs"
    assert context["at"]
    assert context["details"] == {"selected_tab": "Security"}


def test_diagnostic_ui_state_includes_last_action_context():
    dummy = SimpleNamespace(
        _preferred_theme_name="pop",
        radio_detached=True,
        nb=None,
        system_nb=None,
        tools_nb=None,
        security_nb=None,
        _diagnostic_last_action="Tab gewechselt: Radio",
        _diagnostic_last_area="tools-tabs",
        _diagnostic_last_action_at="2026-06-07T12:00:00+00:00",
        _diagnostic_last_details={"selected_tab": "Radio"},
    )
    dummy._selected_notebook_tab_label = lambda notebook: (
        App._selected_notebook_tab_label(dummy, notebook)
    )
    dummy._diagnostic_last_action_context = lambda: App._diagnostic_last_action_context(
        dummy
    )

    state = App._diagnostic_ui_state(dummy)

    assert state["theme"] == "pop"
    assert state["radio_detached"] is True
    assert state["last_action"]["action"] == "Tab gewechselt: Radio"
    assert state["last_action"]["area"] == "tools-tabs"


def test_diagnostic_ui_state_includes_runtime_snapshot():
    class DummyVar:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    dummy = SimpleNamespace(
        _preferred_theme_name="dark",
        radio_detached=False,
        nb=None,
        system_nb=None,
        tools_nb=None,
        security_nb=None,
        public_ip="203.0.113.10",
        country="DE",
        dns_guard_state="active",
        last_dns_consistency_ok=True,
        dot_enabled=True,
        dot_running=False,
        security_filter_mode="warn",
        security_events=[{"id": 1}, {"id": 2}],
        security_visible_events=[{"id": 2}],
        security_last_alarm="Portscan",
        dns_guard_status_var=DummyVar("DNS Guard: aktiv"),
        dot_status_var=DummyVar("DoT: aktiv"),
        vpn_status_text_var=DummyVar("VPN: an | IP: 203.0.113.10 | Land: DE"),
        nm_dns_header_var=DummyVar("NM DNS: 9.9.9.9"),
        ufw_logging_status_var=DummyVar("UFW Logging: high"),
        _diagnostic_last_action="Tab gewechselt: Security",
        _diagnostic_last_area="main-tabs",
        _diagnostic_last_action_at="2026-06-07T12:00:00+00:00",
        _diagnostic_last_details={"selected_tab": "Security"},
    )
    dummy._selected_notebook_tab_label = lambda notebook: (
        App._selected_notebook_tab_label(dummy, notebook)
    )
    dummy._diagnostic_last_action_context = lambda: App._diagnostic_last_action_context(
        dummy
    )
    dummy._diagnostic_var_value = lambda var_name: App._diagnostic_var_value(
        dummy, var_name
    )
    dummy._diagnostic_runtime_state = lambda: App._diagnostic_runtime_state(dummy)

    state = App._diagnostic_ui_state(dummy)

    assert state["runtime_state"]["public_ip"] == "203.0.113.10"
    assert state["runtime_state"]["country"] == "DE"
    assert state["runtime_state"]["dns_guard_state"] == "active"
    assert state["runtime_state"]["dns_consistency_ok"] is True
    assert state["runtime_state"]["dot_enabled"] is True
    assert state["runtime_state"]["security_events_count"] == 2
    assert state["runtime_state"]["security_visible_events_count"] == 1
    assert state["runtime_state"]["ufw_logging_status"] == "UFW Logging: high"


def test_apply_dns_records_action_and_delegates(monkeypatch):
    recorded = {}

    class DummyVar:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    def fake_apply_dns(app, **kwargs):
        recorded["delegated"] = kwargs
        return "dns-ok"

    monkeypatch.setattr(
        app_module,
        "dns_controller",
        SimpleNamespace(apply_dns=fake_apply_dns),
    )
    dummy = SimpleNamespace(
        dns_choice_var=DummyVar("quad9"),
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        ),
    )

    result = App.apply_dns(dummy)

    assert result == "dns-ok"
    assert recorded["action"] == "DNS anwenden"
    assert recorded["area"] == "dns"
    assert recorded["details"]["choice"] == "quad9"
    assert recorded["delegated"]["choice"] is None


def test_killswitch_on_records_action_and_delegates(monkeypatch):
    recorded = {}

    def fake_killswitch_on(app, **kwargs):
        recorded["delegated"] = kwargs
        return True

    monkeypatch.setattr(
        app_module,
        "firewall_controller",
        SimpleNamespace(killswitch_on=fake_killswitch_on),
    )
    dummy = SimpleNamespace(
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        )
    )

    result = App.killswitch_on(
        dummy,
        async_mode=False,
        ensure_sudo=False,
        refresh_ui=False,
        interactive_guard=False,
    )

    assert result is True
    assert recorded["action"] == "Killswitch aktivieren"
    assert recorded["area"] == "firewall"
    assert recorded["details"]["async_mode"] is False
    assert recorded["delegated"]["ensure_sudo"] is False


def test_security_scan_now_records_action_and_delegates(monkeypatch):
    recorded = {}

    def fake_security_scan_now(app):
        recorded["delegated"] = True

    monkeypatch.setattr(
        app_module,
        "security_monitoring_controller",
        SimpleNamespace(security_scan_now=fake_security_scan_now),
    )
    dummy = SimpleNamespace(
        security_events=[{"id": 1}, {"id": 2}, {"id": 3}],
        security_filter_mode="portscan",
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        ),
    )

    App.security_scan_now(dummy)

    assert recorded["action"] == "Security-Scan starten"
    assert recorded["area"] == "security"
    assert recorded["details"]["events_count"] == 3
    assert recorded["details"]["filter_mode"] == "portscan"
    assert recorded["delegated"] is True


def test_open_radio_external_app_records_action_before_unavailable_core(monkeypatch):
    recorded = {}

    monkeypatch.setattr(app_module, "netmon_radio_core", None)
    dummy = SimpleNamespace(
        radio_launcher_mode="embedded",
        radio_detached=False,
        log_safe=lambda _message: None,
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        ),
    )

    result = App.open_radio_external_app(dummy)

    assert result is False
    assert recorded["action"] == "Radio loslösen"
    assert recorded["area"] == "radio"
    assert recorded["details"]["launcher_mode"] == "embedded"


def test_vpn_switch_records_action_and_delegates(monkeypatch):
    recorded = {}

    def fake_vpn_switch(app, target, **kwargs):
        recorded["delegated"] = {"target": target, **kwargs}
        return "vpn-ok"

    monkeypatch.setattr(
        app_module,
        "vpn_controller",
        SimpleNamespace(
            vpn_switch=fake_vpn_switch, vpn_off=lambda *args, **kwargs: None
        ),
    )
    dummy = SimpleNamespace(
        after=lambda *_args, **_kwargs: None,
        update_vpn_status_text=lambda: None,
        _schedule_vpn_ip_country_refresh=lambda: recorded.update(
            {"ip_refresh_scheduled": True}
        ),
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        ),
    )

    result = App.vpn_switch(
        dummy,
        "wg0",
        ensure_sudo=False,
        refresh_ui=False,
        force_reconnect=True,
        skip_cleanup=True,
    )

    assert result == "vpn-ok"
    assert recorded["action"] == "VPN wechseln"
    assert recorded["area"] == "vpn"
    assert recorded["details"]["target"] == "wg0"
    assert recorded["delegated"]["target"] == "wg0"
    assert recorded["delegated"]["force_reconnect"] is True
    assert recorded["ip_refresh_scheduled"] is True


def test_internet_disable_records_action_before_cancel():
    recorded = {}
    dummy = SimpleNamespace(
        _try_begin_network_operation=lambda _label: True,
        _confirm_danger_action=lambda *args, **kwargs: False,
        log=lambda _message: None,
        _end_network_operation=lambda: None,
        tr=lambda _key, default: default,
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        ),
    )

    result = App.internet_disable(dummy, interactive_guard=True)

    assert result is False
    assert recorded["action"] == "Internet deaktivieren"
    assert recorded["area"] == "network"
    assert recorded["details"]["interactive_guard"] is True


def test_internet_enable_records_action_before_cancel():
    recorded = {}
    dummy = SimpleNamespace(
        _try_begin_network_operation=lambda _label: True,
        _confirm_danger_action=lambda *args, **kwargs: False,
        log=lambda _message: None,
        _end_network_operation=lambda: None,
        tr=lambda _key, default: default,
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        ),
    )

    result = App.internet_enable(dummy, interactive_guard=True)

    assert result is False
    assert recorded["action"] == "Internet aktivieren"
    assert recorded["area"] == "network"
    assert recorded["details"]["interactive_guard"] is True


def test_apply_dnssec_mode_async_records_action_before_cancel():
    recorded = {}

    class DummyNotebook:
        def select(self, _tab):
            return None

    outputs = []
    logs = []
    dummy = SimpleNamespace(
        nb=DummyNotebook(),
        tab_dns=object(),
        get_preferred_dnssec_mode=lambda: "strict",
        confirm_dnssec_mode_activation=lambda _name: False,
        update_dns_output=lambda text, append=False: outputs.append((text, append)),
        log_safe=lambda message: logs.append(message),
        _record_diagnostic_action=lambda action, area, details=None: recorded.update(
            {"action": action, "area": area, "details": dict(details or {})}
        ),
    )

    App.apply_dnssec_mode_async(dummy)

    assert recorded["action"] == "DNSSEC-Modus anwenden"
    assert recorded["area"] == "dns"
    assert recorded["details"]["preferred_mode"] == "strict"
    assert outputs
    assert logs


def test_get_latest_diagnostic_report_path_prefers_remembered_file(tmp_path):
    report_path = tmp_path / "netmon-crash.json"
    report_path.write_text("{}", encoding="utf-8")
    dummy = SimpleNamespace(
        _latest_diagnostic_report_path="",
    )

    remembered = App._remember_diagnostic_report_path(dummy, str(report_path))
    resolved = App._get_latest_diagnostic_report_path(dummy)

    assert remembered == str(report_path)
    assert resolved == str(report_path)


def test_about_program_dialog_contains_diagnostic_actions_source():
    source = inspect.getsource(App.open_about_program_dialog)

    assert "Diagnosebericht öffnen" in source
    assert "Diagnoseordner öffnen" in source
    assert "get_netmon_documents_dir()" in source
    assert "Supportformular" in source
    assert "Supportpaket mit Formular erzeugen" in source
    assert "self._support_form_placeholders()" in source
    assert "Tipp: Supportpaket erzeugen, ZIP im Supportordner prüfen" in source
    assert 'self.tr("about_section_donation", "NetMon unterstützen")' in source
    assert 'self.tr("about_donation_button", "Spendenlink folgt")' in source


def test_bootstrap_failure_source_mentions_startup_support_dialog():
    source = inspect.getsource(main._report_bootstrap_failure)

    assert "_show_startup_support_dialog(" in source
    assert "NetMon konnte nicht gestartet werden." in source


def test_support_packages_dir_uses_documents_folder(tmp_path, monkeypatch):
    docs_dir = tmp_path / "Documents" / "NetMon"
    monkeypatch.setattr(
        support_bundle,
        "get_netmon_documents_dir",
        lambda: str(docs_dir),
    )

    result = support_bundle.support_packages_dir()

    assert result == str(docs_dir / "support")
    assert (docs_dir / "support").is_dir()


def test_create_support_package_writes_zip_with_manifest_and_files(
    tmp_path, monkeypatch
):
    docs_dir = tmp_path / "Documents" / "NetMon"
    diagnostics_dir = docs_dir / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    report_path = diagnostics_dir / "netmon-crash-1.json"
    report_path.write_text('{"ok": true}', encoding="utf-8")
    crash_log = diagnostics_dir / "crash.log"
    crash_log.write_text("boom", encoding="utf-8")

    monkeypatch.setattr(
        support_bundle,
        "get_netmon_documents_dir",
        lambda: str(docs_dir),
    )
    monkeypatch.setattr(
        support_bundle,
        "support_bundle_inputs",
        lambda: [str(report_path), str(crash_log)],
    )

    package_path = support_bundle.create_support_package(
        metadata={"summary": "NetMon startet nicht"}
    )

    assert package_path.endswith(".zip")
    with zipfile.ZipFile(package_path) as archive:
        names = set(archive.namelist())
        assert "manifest.json" in names
        assert "files/netmon-crash-1.json" in names
        assert "files/crash.log" in names
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["metadata"]["summary"] == "NetMon startet nicht"


def test_create_support_package_app_method_remembers_path(monkeypatch, tmp_path):
    package_path = tmp_path / "netmon-support-1.zip"
    package_path.write_text("zip", encoding="utf-8")
    recorded = {}

    monkeypatch.setattr(
        app_module,
        "create_support_package",
        lambda metadata=None: (
            recorded.setdefault("metadata", metadata),
            str(package_path),
        )[1],
    )
    dummy = SimpleNamespace(
        _latest_support_package_path="",
        log_safe=lambda _message: None,
    )
    dummy._diagnostic_last_action_context = lambda: {"action": "DNS anwenden"}
    dummy._diagnostic_runtime_state = lambda: {"public_ip": "203.0.113.10"}
    dummy._remember_support_package_path = lambda path: (
        App._remember_support_package_path(dummy, path)
    )

    result = App.create_support_package(dummy)

    assert result == str(package_path)
    assert recorded["metadata"]["last_action"]["action"] == "DNS anwenden"
    assert recorded["metadata"]["runtime_state"]["public_ip"] == "203.0.113.10"


def test_create_support_package_app_method_merges_support_form_metadata(
    monkeypatch, tmp_path
):
    package_path = tmp_path / "netmon-support-2.zip"
    package_path.write_text("zip", encoding="utf-8")
    recorded = {}

    monkeypatch.setattr(
        app_module,
        "create_support_package",
        lambda metadata=None: (
            recorded.setdefault("metadata", metadata),
            str(package_path),
        )[1],
    )
    dummy = SimpleNamespace(
        _latest_support_package_path="",
        log_safe=lambda _message: None,
    )
    dummy._diagnostic_last_action_context = lambda: {"action": "Radio lösen"}
    dummy._diagnostic_runtime_state = lambda: {"radio_detached": True}
    dummy._remember_support_package_path = lambda path: (
        App._remember_support_package_path(dummy, path)
    )

    result = App.create_support_package(
        dummy,
        extra_metadata={
            "user_report": {
                "contact_email": "Platzhalter: E-Mail-Adresse (optional)",
                "details": "Radio-Icon wird nicht übernommen",
            }
        },
    )

    assert result == str(package_path)
    assert recorded["metadata"]["last_action"]["action"] == "Radio lösen"
    assert recorded["metadata"]["runtime_state"]["radio_detached"] is True
    assert (
        recorded["metadata"]["user_report"]["contact_email"]
        == "Platzhalter: E-Mail-Adresse (optional)"
    )
    assert (
        recorded["metadata"]["user_report"]["details"]
        == "Radio-Icon wird nicht übernommen"
    )


def test_build_about_support_form_metadata_skips_placeholder_values():
    dummy = SimpleNamespace()
    dummy._support_form_placeholders = lambda: App._support_form_placeholders(dummy)
    dummy._support_form_clean_value = lambda value, placeholder="": (
        App._support_form_clean_value(
            dummy,
            value,
            placeholder,
        )
    )

    metadata = App._build_about_support_form_metadata(
        dummy,
        contact_name="Platzhalter: Name oder Kürzel (optional)",
        contact_email="Platzhalter: E-Mail-Adresse (optional)",
        last_step="Radio lösen",
        repro_status="Platzhalter: z. B. immer / manchmal / noch unklar",
        details="Platzhalter: kurze Fehlerbeschreibung, Beobachtungen, gewünschtes Verhalten",
    )

    assert metadata["user_report"]["contact_name"] == ""
    assert metadata["user_report"]["contact_email"] == ""
    assert metadata["user_report"]["last_step"] == "Radio lösen"
    assert metadata["user_report"]["repro_status"] == ""
    assert metadata["user_report"]["details"] == ""


def test_settings_tab_contains_support_actions_source():
    source = inspect.getsource(App.build_settings_tab)

    assert "Supportpaket erzeugen" in source
    assert "Supportpaket öffnen" in source
    assert "Supportordner öffnen" in source
    assert (
        "Empfehlung: Paket erzeugen, kurz den Inhalt im Supportordner prüfen" in source
    )


def test_settings_tab_contains_backup_tab_source():
    source = inspect.getsource(App.build_settings_tab)
    backup_source = inspect.getsource(App._build_settings_backup_tab)
    backup_options_source = inspect.getsource(App.refresh_netmon_backup_folder_options)

    assert 'text=self.tr("settings_tab_backup", "Backup")' in source
    assert "def _build_settings_backup_tab(self, tab):" in backup_source
    assert 'text=self.tr("backup_group_snapshot", "System-Snapshot")' in backup_source
    assert 'text=self.tr("backup_group_data", "Datensicherung")' in backup_source
    assert 'text=self.tr("backup_group_netmon", "NetMon-Sicherung")' in backup_source
    assert (
        'text=self.tr("backup_btn_open_data_tool", "Datensicherung öffnen")'
        in backup_source
    )
    assert (
        'text=self.tr("backup_btn_open_restore_tool", "Wiederherstellung öffnen")'
        in backup_source
    )
    assert '"backup_btn_export_netmon_docs"' in backup_source
    assert '"NetMon-Sicherung exportieren"' in backup_source
    assert (
        "command=lambda: self.launch_data_backup_tool(restore=False)" in backup_source
    )
    assert "command=lambda: self.launch_data_backup_tool(restore=True)" in backup_source
    assert "command=self.export_netmon_documents_backup" in backup_source
    assert "command=self.open_netmon_documents_folder" in backup_source
    assert "command=self.open_security_baseline_transfer_folder" not in backup_source
    assert "command=self.export_security_baseline_transfer" not in backup_source
    assert "command=self.import_security_baseline_transfer" not in backup_source
    assert "command=self.show_security_baseline_transfer_package" not in backup_source
    assert (
        "command=self.show_security_baseline_transfer_comparison" not in backup_source
    )
    assert "command=self.clear_security_baseline_transfer" not in backup_source
    assert '"backup_netmon_full_folder"' in backup_options_source
    assert '"NetMon-Ordner komplett"' in backup_options_source


def test_backup_target_conflict_detects_nested_target():
    app = App.__new__(App)

    conflict = app._backup_target_conflict(
        "/home/happy/Dokumente/Backup",
        [{"label": "Dokumente", "path": "/home/happy/Dokumente"}],
    )
    no_conflict = app._backup_target_conflict(
        "/mnt/usb/netmon-backup",
        [{"label": "Dokumente", "path": "/home/happy/Dokumente"}],
    )

    assert conflict == {
        "label": "Dokumente",
        "path": "/home/happy/Dokumente",
    }
    assert no_conflict is None


def test_selected_backup_sources_skip_nested_netmon_when_documents_selected(
    monkeypatch,
):
    class _Var:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

    app = App.__new__(App)
    app.tr = lambda _key, default=None: default or _key
    app.backup_include_documents_var = _Var(True)
    app.backup_include_pictures_var = _Var(False)
    app.backup_include_desktop_var = _Var(False)
    app.backup_include_music_var = _Var(False)
    app.backup_include_videos_var = _Var(False)
    app.backup_include_downloads_var = _Var(False)
    app.backup_include_netmon_documents_var = _Var(True)

    monkeypatch.setattr(
        app_module.os.path,
        "expanduser",
        lambda value: value.replace("~", "/home/happy"),
    )
    monkeypatch.setattr(
        app_module.os.path,
        "exists",
        lambda path: path
        in {
            "/home/happy/Dokumente",
            "/home/happy/Dokumente/NetMon",
        },
    )

    selected = app._selected_backup_source_entries()

    assert selected == [{"label": "Dokumente", "path": "/home/happy/Dokumente"}]


def test_netmon_backup_full_toggle_deselects_individual_folders():
    class _Var:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = App.__new__(App)
    app.backup_netmon_full_var = _Var(True)
    app.backup_netmon_dir_vars = {
        "Config": _Var(True),
        "Security": _Var(True),
    }
    app.backup_selected_sources_var = _Var("")
    app._netmon_backup_selected_entries = lambda: [
        {"key": "__all__", "label": "NetMon komplett", "path": "/tmp/NetMon"}
    ]

    app._on_backup_netmon_full_toggle()

    assert app.backup_netmon_dir_vars["Config"].get() is False
    assert app.backup_netmon_dir_vars["Security"].get() is False
    assert (
        app.backup_selected_sources_var.get()
        == "NetMon-Auswahl: kompletter Dokumente/NetMon-Ordner"
    )


def test_netmon_backup_item_toggle_disables_full_selection():
    class _Var:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    app = App.__new__(App)
    app.backup_netmon_full_var = _Var(True)
    app.backup_netmon_selected_dir_keys = ["Config"]
    app.backup_selected_sources_var = _Var("")
    app._netmon_backup_selected_entries = lambda: [
        {"key": "Security", "label": "Security", "path": "/tmp/NetMon/Security"}
    ]

    app._on_backup_netmon_item_toggle("Config")

    assert app.backup_netmon_full_var.get() is False
    assert app.backup_netmon_selected_dir_keys == []
    assert (
        app.backup_selected_sources_var.get() == "NetMon-Auswahl: 1 Ordner -> Security"
    )


def test_export_netmon_documents_backup_copies_selected_folders(monkeypatch, tmp_path):
    class _Var:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    docs_dir = tmp_path / "Documents" / "NetMon"
    config_dir = docs_dir / "Config"
    logs_dir = docs_dir / "Logs"
    config_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text('{"ok": true}', encoding="utf-8")
    (logs_dir / "latest.log").write_text("hello", encoding="utf-8")

    export_root = tmp_path / "external"
    export_root.mkdir()
    info_calls = []
    error_calls = []
    log_entries = []

    app = App.__new__(App)
    app.settings = {}
    app.tr = lambda _key, default, **_kwargs: default
    app.backup_netmon_full_var = _Var(False)
    app.backup_netmon_dir_vars = {
        "Config": _Var(True),
        "Logs": _Var(False),
    }
    app.backup_status_var = _Var("")
    app._append_backup_log = lambda text, clear=False: log_entries.append((text, clear))

    monkeypatch.setattr(app_module, "get_netmon_documents_dir", lambda: str(docs_dir))
    monkeypatch.setattr(
        app_module.filedialog, "askdirectory", lambda **_kwargs: str(export_root)
    )
    monkeypatch.setattr(
        app_module.messagebox,
        "showinfo",
        lambda *args, **kwargs: info_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        app_module.messagebox,
        "showerror",
        lambda *args, **kwargs: error_calls.append((args, kwargs)),
    )

    result = app.export_netmon_documents_backup()

    export_dirs = sorted(export_root.glob("netmon_documents_backup_*"))
    assert result is True
    assert error_calls == []
    assert info_calls == []
    assert len(export_dirs) == 1
    exported_dir = export_dirs[0]
    assert (exported_dir / "Config" / "config.json").read_text(
        encoding="utf-8"
    ) == '{"ok": true}'
    assert not (exported_dir / "Logs").exists()

    manifest = json.loads(
        (exported_dir / "netmon_documents_backup_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["export_dir"] == str(exported_dir)
    assert manifest["selection"] == [
        {
            "label": "Config",
            "target": str(exported_dir / "Config"),
        }
    ]
    assert "NetMon-Sicherung exportiert" in app.backup_status_var.get()
    assert len(log_entries) == 2


def test_is_trusted_update_url_accepts_only_netmonroots_https():
    accept = App._is_trusted_update_url
    assert accept("https://netmonroots.com/downloads.html") is True
    assert accept("http://netmonroots.com/downloads.html") is True
    assert accept("https://cdn.netmonroots.com/dist/x.deb") is True
    for bad in (
        "https://evil.example.com/x",
        "https://netmonroots.com.evil.com/x",
        "file:///etc/passwd",
        "vnc://netmonroots.com",
        "ftp://netmonroots.com/x",
        "//netmonroots.com/x",
        "",
    ):
        assert accept(bad) is False


def test_open_url_with_xdg_open_rejects_non_web_scheme(monkeypatch):
    app = App.__new__(App)
    logs = []
    app.log_safe = logs.append
    opened = []
    monkeypatch.setattr(main.shutil, "which", lambda _name: "/usr/bin/xdg-open")
    monkeypatch.setattr(
        app_module.subprocess,
        "Popen",
        lambda args, **kwargs: opened.append(args) or object(),
    )

    for blocked in ("file:///etc/passwd", "vnc://host/x", "javascript:alert(1)", "x"):
        assert app._open_url_with_xdg_open(blocked, label="Test") is False
    assert opened == []

    assert app._open_url_with_xdg_open("https://netmonroots.com/x") is True
    assert opened == [["xdg-open", "https://netmonroots.com/x"]]
