from netmon.app import App
import inspect


def test_safe_attach_chad_context_menu_ignores_missing_widget():
    app = App.__new__(App)
    app.attach_chad_context_menu = lambda widget, title: (_ for _ in ()).throw(
        AssertionError("should not be called")
    )

    app.safe_attach_chad_context_menu("missing_widget", "DNS Analyse")


def test_safe_attach_chad_context_menu_logs_attach_errors():
    app = App.__new__(App)
    widget = object()
    logs = []

    app.some_text = widget
    app.log = logs.append

    def fail_attach(_widget, _title):
        raise RuntimeError("boom")

    app.attach_chad_context_menu = fail_attach

    app.safe_attach_chad_context_menu("some_text", "DNS Analyse")

    assert logs
    assert "some_text" in logs[0]
    assert "boom" in logs[0]


def test_attach_all_chad_context_menus_registers_expected_targets():
    app = App.__new__(App)
    calls = []

    app.safe_attach_chad_context_menu = lambda widget_name, title: calls.append(
        (widget_name, title)
    )

    app.attach_all_chad_context_menus()

    assert calls == [
        ("text", "NetMon Log Analyse"),
        ("dns_text", "DNS Analyse"),
        ("nmap_text", "Nmap Analyse"),
        ("mtr_text", "MTR Analyse"),
        ("iftop_text", "iftop Analyse"),
        ("htop_text", "htop Analyse"),
        ("linux_help_text", "Linux Hilfe Analyse"),
        ("hdd_info_text", "HDD Analyse"),
        ("security_detail", "Security Analyse"),
        ("process_guard_detail", "Process Guard Analyse"),
        ("clamav_output_text", "ClamAV Analyse"),
        ("packet_capture_text", "Packet Capture Analyse"),
        ("lynis_text", "Lynis Analyse"),
        ("rkhunter_text", "rkhunter Analyse"),
        ("startup_guard_details_text", "Startup Guard Eintrag Analyse"),
        ("chad_analysis_text", "Chad Verlauf Analyse"),
    ]


def test_attach_chad_context_menu_source_contains_paste_action():
    source = inspect.getsource(App.attach_chad_context_menu)

    assert 'label="Einfügen"' in source
    assert "def paste_from_clipboard" in source
    assert "_show_chad_activation_required_popup" in source


def test_show_context_menu_source_contains_auto_close_support():
    source = inspect.getsource(App._show_context_menu)

    assert "_schedule_active_context_menu_close" in source


def test_schedule_active_context_menu_close_uses_ten_seconds():
    source = inspect.getsource(App._schedule_active_context_menu_close)

    assert "10000" in source


def test_context_menu_close_is_bound_to_click_not_focus_out():
    source = inspect.getsource(App.__init__)

    assert (
        'self.bind("<Button-1>", self._handle_app_click_for_context_menu, add="+")'
        in source
    )
    assert 'self.bind("<FocusOut>", self._handle_app_focus_out, add="+")' not in source
