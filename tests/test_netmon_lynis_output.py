from netmon import app as netmon_app
from netmon.features import security_audit_controller


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


def test_finish_lynis_audit_stores_clean_output_and_updates_summary():
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []

    app.lynis_status_var = DummyVar()
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
    assert app.lynis_last_result["suggestions"] == "2"
    assert app.lynis_last_result["hardening_index"] == "88"
    assert logs[-1] == "Lynis Schnellaudit abgeschlossen."


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
    assert (
        app.lynis_last_output
        == "=== Lynis Vollständiger Sicherheitsscan (sudo) ===\nWarning"
    )
    assert seen["log"][-1] == "Lynis Vollscan abgeschlossen."


def test_finish_lynis_audit_marks_timeout_cleanly():
    app = netmon_app.App.__new__(netmon_app.App)
    logs = []

    app.lynis_status_var = DummyVar()
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
    assert logs[-1] == "Lynis Vollscan Timeout (rc=124)."
