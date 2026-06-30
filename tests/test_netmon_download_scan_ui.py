import inspect

from netmon.app import App


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_download_scan_tab_source_contains_startup_checkbox():
    source = inspect.getsource(App.build_download_scan_tab)

    assert 'text="Temp-Ordner aktivieren"' in source
    assert 'text="Temp-Ordner deaktivieren"' in source
    assert 'text="Temp-Ordner öffnen"' in source
    assert 'text="Temp-Ordner leeren"' in source
    assert "command=self.disable_download_scan_temp_folder" in source
    assert (
        'text="Vor-Quarantäne bei NetMon-Start automatisch aktivieren"' in source
    )
    assert "variable=self.download_scan_prequarantine_startup_var" in source
    assert "command=self.on_download_scan_prequarantine_startup_toggle" in source


def test_prepare_download_scan_startup_state_only_prepares_when_enabled():
    app = App.__new__(App)
    app.download_scan_temp_dir_var = DummyVar("")
    app.download_scan_prequarantine_startup_var = DummyVar(False)

    calls = []
    app._normalized_download_scan_temp_dir = lambda: "/tmp/netmon-download-scan"
    app._refresh_download_scan_temp_security_status = lambda: calls.append("refresh")
    app.create_download_scan_temp_folder = lambda: calls.append("activate")
    app.after = lambda delay, callback: calls.append(("after", delay, callback))

    app.prepare_download_scan_startup_state()

    assert app.download_scan_temp_dir_var.get() == "/tmp/netmon-download-scan"
    assert calls == ["refresh"]

    app.download_scan_prequarantine_startup_var.set(True)
    calls.clear()

    app.prepare_download_scan_startup_state()

    assert app.download_scan_temp_dir_var.get() == "/tmp/netmon-download-scan"
    assert calls == ["refresh", ("after", 800, app.create_download_scan_temp_folder)]


def test_download_scan_prequarantine_startup_toggle_persists_setting():
    app = App.__new__(App)
    app.settings = {}
    app.download_scan_prequarantine_startup_var = DummyVar(True)

    calls = []
    app.save_settings = lambda log_success=False: calls.append(log_success)

    app.on_download_scan_prequarantine_startup_toggle()

    assert app.settings["download_scan_prequarantine_startup"] is True
    assert calls == [False]


def test_download_scan_prequarantine_startup_toggle_disables_active_mount():
    app = App.__new__(App)
    app.settings = {}
    app.download_scan_prequarantine_startup_var = DummyVar(False)

    calls = []
    app.save_settings = lambda log_success=False: calls.append(("save", log_success))
    app.disable_download_scan_temp_folder = lambda **kwargs: calls.append(
        ("disable_action", kwargs)
    )

    app.on_download_scan_prequarantine_startup_toggle()

    assert app.settings["download_scan_prequarantine_startup"] is False
    assert calls[0] == ("save", False)
    assert calls[1] == (
        "disable_action",
        {"log_message": "Vor-Quarantäne-Autostart deaktiviert"},
    )


def test_disable_download_scan_temp_folder_updates_status_and_result():
    app = App.__new__(App)

    calls = []
    app._disable_download_scan_secure_mount = lambda interactive=False: calls.append(
        ("disable", interactive)
    ) or True
    app._set_download_scan_status = lambda **kwargs: calls.append(("status", kwargs))
    app._update_download_scan_result_text = lambda message: calls.append(
        ("result", message)
    )
    app._normalized_download_scan_temp_dir = lambda: "/tmp/netmon-download-scan"

    result = app.disable_download_scan_temp_folder(log_message="manual disable")

    assert result is True
    assert calls[0] == ("disable", True)
    assert calls[1] == (
        "status",
        {
            "status": "🟡 ungeprüft",
            "result": "Vor-Quarantäne deaktiviert",
            "last_scan": "Noch kein Scan",
            "log_message": "manual disable",
        },
    )
    assert calls[2][0] == "result"
