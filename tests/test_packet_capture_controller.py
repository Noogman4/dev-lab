from netmon.features import packet_capture_controller


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyButton:
    def __init__(self):
        self.calls = []

    def configure(self, **kwargs):
        self.calls.append(kwargs)


class DummyText:
    def __init__(self):
        self.value = ""
        self.state = "disabled"

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]

    def delete(self, _start, _end):
        self.value = ""

    def insert(self, _where, text):
        self.value += text

    def see(self, _where):
        return None

    def index(self, _where):
        return "1.0" if not self.value else "2.0"


class ImmediateThread:
    def __init__(self, target=None, daemon=None):
        self.target = target
        self.daemon = daemon

    def start(self):
        if self.target is not None:
            self.target()


def test_packet_capture_set_running_state_updates_button_states():
    app = type("DummyApp", (), {})()
    app.dep_status = {"tshark": True, "dumpcap": False}
    app.btn_packet_capture_start = DummyButton()
    app.btn_packet_capture_stop = DummyButton()
    app.l_capture = object()
    light_calls = []
    app.set_light = lambda light, color: light_calls.append((light, color))

    packet_capture_controller.packet_capture_set_running_state(app, True)
    packet_capture_controller.packet_capture_set_running_state(app, False)

    assert app.btn_packet_capture_start.calls[0]["state"] == "disabled"
    assert app.btn_packet_capture_stop.calls[0]["state"] == "normal"
    assert app.btn_packet_capture_start.calls[1]["state"] == "normal"
    assert app.btn_packet_capture_stop.calls[1]["state"] == "disabled"
    assert light_calls == [(app.l_capture, "green"), (app.l_capture, "red")]


def test_packet_capture_app_value_falls_back_to_bound_methods():
    app = type(
        "DummyApp",
        (),
        {"set_light": lambda self, light, color: (light, color)},
    )()

    value = packet_capture_controller._app_value(app, "set_light")

    assert callable(value)


def test_packet_capture_ready_returns_true_if_any_capture_tool_exists():
    app = type("DummyApp", (), {})()
    app.dep_status = {"tshark": False, "dumpcap": True}

    assert packet_capture_controller._packet_capture_ready(app) is True


def test_packet_capture_ready_returns_false_without_tools():
    app = type("DummyApp", (), {})()
    app.dep_status = {"tshark": False, "dumpcap": False}

    assert packet_capture_controller._packet_capture_ready(app) is False


def test_packet_capture_needs_separator_only_for_non_empty_append():
    empty_widget = DummyText()
    filled_widget = DummyText()
    filled_widget.value = "existing\n"

    assert (
        packet_capture_controller._packet_capture_needs_separator(empty_widget, False)
        is False
    )
    assert (
        packet_capture_controller._packet_capture_needs_separator(filled_widget, False)
        is True
    )
    assert (
        packet_capture_controller._packet_capture_needs_separator(filled_widget, True)
        is False
    )


def test_packet_capture_output_segment_trims_and_appends_newline():
    assert (
        packet_capture_controller._packet_capture_output_segment("demo line  \n")
        == "demo line\n"
    )


def test_packet_capture_button_states_cover_running_and_ready_paths():
    assert packet_capture_controller._packet_capture_button_states(
        running=True,
        ready=True,
    ) == {"start": "disabled", "stop": "normal"}
    assert packet_capture_controller._packet_capture_button_states(
        running=False,
        ready=True,
    ) == {"start": "normal", "stop": "disabled"}


def test_packet_capture_button_states_disable_both_when_not_ready():
    assert packet_capture_controller._packet_capture_button_states(
        running=False,
        ready=False,
    ) == {"start": "disabled", "stop": "disabled"}


def test_packet_capture_apply_button_states_updates_available_buttons():
    app = type("DummyApp", (), {})()
    app.btn_packet_capture_start = DummyButton()
    app.btn_packet_capture_stop = DummyButton()

    packet_capture_controller._packet_capture_apply_button_states(
        app,
        {"start": "normal", "stop": "disabled"},
    )

    assert app.btn_packet_capture_start.calls == [{"state": "normal"}]
    assert app.btn_packet_capture_stop.calls == [{"state": "disabled"}]


def test_packet_capture_apply_button_states_tolerates_missing_buttons():
    app = type("DummyApp", (), {})()

    packet_capture_controller._packet_capture_apply_button_states(
        app,
        {"start": "normal", "stop": "disabled"},
    )


def test_packet_capture_clear_widget_clears_text_when_present():
    widget = DummyText()
    widget.value = "existing text"

    assert packet_capture_controller._packet_capture_clear_widget(widget) is True
    assert widget.value == ""


def test_packet_capture_clear_widget_returns_false_without_widget():
    assert packet_capture_controller._packet_capture_clear_widget(None) is False


def test_packet_capture_apply_output_replaces_existing_text():
    widget = DummyText()
    widget.value = "existing\n"

    assert (
        packet_capture_controller._packet_capture_apply_output(
            widget,
            "fresh line",
            replace=True,
        )
        is True
    )
    assert widget.value == "fresh line\n"


def test_packet_capture_apply_output_appends_with_separator():
    widget = DummyText()
    widget.value = "existing\n"

    assert (
        packet_capture_controller._packet_capture_apply_output(
            widget,
            "next line",
            replace=False,
        )
        is True
    )
    assert widget.value == "existing\n\nnext line\n"


def test_packet_capture_show_file_info_falls_back_to_filesystem_size(tmp_path):
    capture_file = tmp_path / "capture.pcapng"
    capture_file.write_bytes(b"abc123")

    app = type("DummyApp", (), {})()
    app.dep_status = {"capinfos": False}
    app.packet_capture_output_path = str(capture_file)
    app.packet_capture_text = DummyText()
    app.packet_capture_size_var = DummyVar("")
    app.packet_capture_packets_var = DummyVar("")

    packet_capture_controller.packet_capture_show_file_info(app)

    assert "Capture-Datei Info" in app.packet_capture_text.value
    assert str(capture_file) in app.packet_capture_text.value
    assert app.packet_capture_size_var.get()


def test_packet_capture_has_existing_file_returns_true_only_for_real_file(tmp_path):
    capture_file = tmp_path / "capture.pcapng"
    capture_file.write_bytes(b"abc123")
    missing_file = tmp_path / "missing.pcapng"

    existing_app = type("DummyApp", (), {})()
    existing_app.packet_capture_output_path = str(capture_file)

    missing_app = type("DummyApp", (), {})()
    missing_app.packet_capture_output_path = str(missing_file)

    assert (
        packet_capture_controller._packet_capture_has_existing_file(existing_app)
        is True
    )
    assert (
        packet_capture_controller._packet_capture_has_existing_file(missing_app)
        is False
    )


def test_packet_capture_start_async_skips_file_info_for_permission_error_without_capture_file(
    monkeypatch, tmp_path
):
    capture_file = tmp_path / "capture.pcapng"

    class FakeProc:
        def __init__(self, *_args, **_kwargs):
            self.stdout = iter(
                [
                    "Capturing on 'enp4s0'\n",
                    'tshark: You do not have permission to capture on device "enp4s0".\n',
                    "(socket: Operation not permitted)\n",
                    "dumpcap: Operation not permitted\n",
                ]
            )

        def wait(self):
            return 1

    app = type("DummyApp", (), {})()
    app.dep_status = {"tshark": True, "dumpcap": True}
    app.packet_capture_running = False
    app.packet_capture_cancel_requested = False
    app.packet_capture_started_at = 0.0
    app.packet_capture_output_path = ""
    app.packet_capture_active_process = None
    app.packet_capture_text_after_id = None
    app.packet_capture_text = DummyText()
    app.packet_capture_interface_var = DummyVar("enp4s0")
    app.packet_capture_file_var = DummyVar(str(capture_file))
    app.packet_capture_filter_var = DummyVar("")
    app.packet_capture_status_var = DummyVar("")
    app.packet_capture_runtime_var = DummyVar("")
    app.packet_capture_packets_var = DummyVar("")
    app.packet_capture_size_var = DummyVar("")
    app.btn_packet_capture_start = DummyButton()
    app.btn_packet_capture_stop = DummyButton()
    app.tab_packet_capture = object()
    app.logged = []
    app.permission_hint_calls = 0
    app.selected_tabs = []

    app._select_security_tab = lambda tab: app.selected_tabs.append(tab)
    app.log = lambda message: app.logged.append(message)
    app._looks_like_dumpcap_permission_issue = (
        lambda text: "operation not permitted" in str(text).lower()
    )
    app.show_dumpcap_permission_hint = lambda: setattr(
        app, "permission_hint_calls", app.permission_hint_calls + 1
    )
    app.after = lambda _delay, callback: callback()

    monkeypatch.setattr(packet_capture_controller.subprocess, "Popen", FakeProc)
    monkeypatch.setattr(packet_capture_controller.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        packet_capture_controller, "call_in_ui_thread", lambda _app, fn: fn()
    )

    packet_capture_controller.packet_capture_start_async(app)

    assert (
        "You do not have permission to capture on device"
        not in app.packet_capture_text.value
    )
    assert "Capture fehlgeschlagen: keine Berechtigung" in app.packet_capture_text.value
    assert "Hinweis: Capture wurde mit Fehler beendet." in app.packet_capture_text.value
    assert "Capture-Datei nicht gefunden" not in app.packet_capture_text.value
    assert app.permission_hint_calls == 1


def test_packet_capture_looks_like_permission_issue_detects_tshark_text_without_dumpcap():
    app = type("DummyApp", (), {})()
    app._looks_like_dumpcap_permission_issue = lambda _text: False

    assert (
        packet_capture_controller._packet_capture_looks_like_permission_issue(
            app,
            'tshark: You do not have permission to capture on device "enp4s0".',
        )
        is True
    )


def test_packet_capture_open_target_path_prefers_existing_file(tmp_path):
    capture_file = tmp_path / "capture.pcapng"
    capture_file.write_bytes(b"abc123")

    app = type("DummyApp", (), {})()
    app.packet_capture_output_path = str(capture_file)

    assert packet_capture_controller._packet_capture_open_target_path(app) == str(
        capture_file
    )


def test_packet_capture_open_target_path_falls_back_to_parent_directory(tmp_path):
    target_file = tmp_path / "captures" / "future.pcapng"

    app = type("DummyApp", (), {})()
    app.packet_capture_output_path = str(target_file)

    assert packet_capture_controller._packet_capture_open_target_path(app) == str(
        target_file.parent
    )


def test_packet_capture_wireshark_launcher_reads_launcher_mapping():
    app = type("DummyApp", (), {})()
    app.dep_status = {
        "wireshark_launcher": {
            "kind": "binary",
            "target": "/usr/bin/wireshark",
        }
    }

    assert packet_capture_controller._packet_capture_wireshark_launcher(app) == {
        "kind": "binary",
        "target": "/usr/bin/wireshark",
    }


def test_packet_capture_wireshark_command_builds_binary_command():
    assert packet_capture_controller._packet_capture_wireshark_command(
        {"kind": "binary", "target": "/usr/bin/wireshark"},
        "/tmp/capture.pcapng",
    ) == ["/usr/bin/wireshark", "/tmp/capture.pcapng"]


def test_packet_capture_wireshark_command_requires_xdg_open_for_desktop_file():
    try:
        packet_capture_controller._packet_capture_wireshark_command(
            {"kind": "desktop_file", "target": "org.wireshark.Wireshark.desktop"},
            "/tmp/capture.pcapng",
            has_cmd_fn=lambda _name: False,
        )
    except RuntimeError as exc:
        assert str(exc) == "xdg-open ist nicht verfügbar."
    else:
        assert False


def test_packet_capture_open_location_command_builds_xdg_open_command():
    assert packet_capture_controller._packet_capture_open_location_command(
        "/tmp/captures",
        has_cmd_fn=lambda name: name == "xdg-open",
    ) == ["xdg-open", "/tmp/captures"]


def test_packet_capture_open_location_command_requires_xdg_open():
    try:
        packet_capture_controller._packet_capture_open_location_command(
            "/tmp/captures",
            has_cmd_fn=lambda _name: False,
        )
    except RuntimeError as exc:
        assert str(exc) == "xdg-open ist nicht verfügbar."
    else:
        assert False


def test_packet_capture_filter_reads_trimmed_var_value():
    app = type("DummyApp", (), {})()
    app.packet_capture_filter_var = DummyVar("  tcp port 443  ")

    assert packet_capture_controller._packet_capture_filter(app) == "tcp port 443"


def test_packet_capture_start_command_prefers_tshark_with_filter():
    app = type("DummyApp", (), {})()
    app.dep_status = {"tshark": True, "dumpcap": True}
    app.packet_capture_filter_var = DummyVar("udp port 53")

    cmd, tool = packet_capture_controller._packet_capture_start_command(
        app,
        "eth0",
        "/tmp/test.pcapng",
    )

    assert tool == "tshark"
    assert cmd == [
        "tshark",
        "-i",
        "eth0",
        "-f",
        "udp port 53",
        "-w",
        "/tmp/test.pcapng",
    ]


def test_packet_capture_start_command_falls_back_to_dumpcap_without_filter():
    app = type("DummyApp", (), {})()
    app.dep_status = {"tshark": False, "dumpcap": True}
    app.packet_capture_filter_var = DummyVar("")

    cmd, tool = packet_capture_controller._packet_capture_start_command(
        app,
        "wlan0",
        "/tmp/test.pcapng",
    )

    assert tool == "dumpcap"
    assert cmd == ["dumpcap", "-i", "wlan0", "-w", "/tmp/test.pcapng"]


def test_packet_capture_start_command_returns_empty_without_tools():
    app = type("DummyApp", (), {})()
    app.dep_status = {"tshark": False, "dumpcap": False}
    app.packet_capture_filter_var = DummyVar("tcp")

    cmd, tool = packet_capture_controller._packet_capture_start_command(
        app,
        "eth0",
        "/tmp/test.pcapng",
    )

    assert cmd is None
    assert tool == ""


def test_packet_capture_capinfos_summary_extracts_packets_and_size():
    summary = packet_capture_controller._packet_capture_capinfos_summary(
        "Number of packets: 42\nFile size: 12 kB",
        "1 kB",
    )

    assert summary == {"packets": "42", "size_text": "12 kB"}


def test_packet_capture_capinfos_summary_keeps_defaults_without_matches():
    summary = packet_capture_controller._packet_capture_capinfos_summary(
        "Capture file details",
        "7 kB",
    )

    assert summary == {"packets": "-", "size_text": "7 kB"}


def test_packet_capture_summary_value_extracts_trimmed_suffix():
    assert (
        packet_capture_controller._packet_capture_summary_value(
            "File size:   12 kB  ",
            "-",
        )
        == "12 kB"
    )


def test_packet_capture_summary_value_uses_default_for_empty_suffix():
    assert (
        packet_capture_controller._packet_capture_summary_value(
            "Number of packets:",
            "fallback",
        )
        == "fallback"
    )


def test_packet_capture_completion_status_prefers_stop_over_return_code():
    assert (
        packet_capture_controller._packet_capture_completion_status(True, 5)
        == "gestoppt"
    )


def test_packet_capture_completion_status_maps_success_and_error_codes():
    assert (
        packet_capture_controller._packet_capture_completion_status(False, 0)
        == "abgeschlossen"
    )
    assert (
        packet_capture_controller._packet_capture_completion_status(False, 9)
        == "Fehler (9)"
    )


def test_packet_capture_size_text_formats_existing_file_size(tmp_path):
    capture_file = tmp_path / "capture.pcapng"
    capture_file.write_bytes(b"abc123")

    assert packet_capture_controller._packet_capture_size_text(str(capture_file))


def test_packet_capture_size_text_raises_for_missing_file(tmp_path):
    missing_file = tmp_path / "missing.pcapng"

    try:
        packet_capture_controller._packet_capture_size_text(str(missing_file))
    except FileNotFoundError:
        assert True
    else:
        assert False


def test_packet_capture_file_info_text_formats_expected_lines():
    assert (
        packet_capture_controller._packet_capture_file_info_text(
            "/tmp/capture.pcapng",
            "12 kB",
        )
        == "=== Capture-Datei Info ===\nDatei: /tmp/capture.pcapng\nGröße: 12 kB"
    )


def test_packet_capture_file_info_text_keeps_passed_values():
    assert (
        packet_capture_controller._packet_capture_file_info_text(
            "",
            "-",
        )
        == "=== Capture-Datei Info ===\nDatei: \nGröße: -"
    )


def test_packet_capture_capinfos_text_formats_expected_header_and_body():
    assert (
        packet_capture_controller._packet_capture_capinfos_text(
            "Number of packets: 42\nFile size: 12 kB"
        )
        == "=== Capture-Datei Info ===\nNumber of packets: 42\nFile size: 12 kB"
    )


def test_packet_capture_capinfos_text_strips_surrounding_whitespace():
    assert (
        packet_capture_controller._packet_capture_capinfos_text(
            "\n  Number of packets: 42\n"
        )
        == "=== Capture-Datei Info ===\nNumber of packets: 42"
    )


def test_packet_capture_file_info_body_lines_format_expected_values():
    assert packet_capture_controller._packet_capture_file_info_body_lines(
        "/tmp/capture.pcapng",
        "12 kB",
    ) == [
        "Datei: /tmp/capture.pcapng",
        "Größe: 12 kB",
    ]


def test_packet_capture_file_info_body_lines_keep_passed_empty_values():
    assert packet_capture_controller._packet_capture_file_info_body_lines(
        "",
        "-",
    ) == [
        "Datei: ",
        "Größe: -",
    ]


def test_packet_capture_file_info_missing_message_uses_empty_selection_text():
    assert (
        packet_capture_controller._packet_capture_file_info_missing_message("")
        == "Noch keine Capture-Datei ausgewählt."
    )


def test_packet_capture_file_info_missing_message_uses_missing_file_text():
    assert (
        packet_capture_controller._packet_capture_file_info_missing_message(
            "/tmp/capture.pcapng"
        )
        == "Capture-Datei nicht gefunden: /tmp/capture.pcapng"
    )


def test_packet_capture_open_location_missing_message_uses_no_file_text():
    assert (
        packet_capture_controller._packet_capture_open_location_missing_message("", "")
        == "Noch keine Capture-Datei vorhanden."
    )


def test_packet_capture_open_location_missing_message_uses_invalid_target_text():
    assert (
        packet_capture_controller._packet_capture_open_location_missing_message(
            "/tmp/capture.pcapng",
            "",
        )
        == "Kein gültiger Pfad für Capture-Datei vorhanden."
    )


def test_packet_capture_wireshark_missing_message_uses_missing_launcher_text():
    assert (
        packet_capture_controller._packet_capture_wireshark_missing_message("", "")
        == "Wireshark ist nicht verfügbar. Installationshinweis: sudo apt install wireshark"
    )


def test_packet_capture_wireshark_missing_message_uses_missing_file_text():
    assert (
        packet_capture_controller._packet_capture_wireshark_missing_message(
            "wireshark",
            "",
        )
        == "Keine gültige Capture-Datei zum Öffnen gefunden."
    )


def test_packet_capture_stop_request_message_uses_no_running_capture_text():
    assert (
        packet_capture_controller._packet_capture_stop_request_message(False)
        == "Es läuft aktuell kein Capture."
    )


def test_packet_capture_stop_request_message_uses_stop_requested_text():
    assert (
        packet_capture_controller._packet_capture_stop_request_message(True)
        == "Capture-Stopp angefordert."
    )


def test_packet_capture_open_success_message_formats_expected_text():
    assert (
        packet_capture_controller._packet_capture_open_success_message(
            "Capture-Pfad",
            "/tmp/captures",
        )
        == "Capture-Pfad geöffnet: /tmp/captures"
    )


def test_packet_capture_open_success_message_uses_trimmed_label():
    assert (
        packet_capture_controller._packet_capture_open_success_message(
            " Wireshark ",
            "/tmp/capture.pcapng",
        )
        == "Wireshark geöffnet: /tmp/capture.pcapng"
    )


def test_packet_capture_open_location_result_message_uses_success_text():
    assert (
        packet_capture_controller._packet_capture_open_location_result_message(
            "/tmp/captures"
        )
        == "Capture-Pfad geöffnet: /tmp/captures"
    )


def test_packet_capture_open_location_result_message_uses_error_text():
    assert (
        packet_capture_controller._packet_capture_open_location_result_message(
            "/tmp/captures",
            "xdg-open ist nicht verfügbar.",
        )
        == "Capture-Pfad konnte nicht geöffnet werden: xdg-open ist nicht verfügbar."
    )


def test_packet_capture_wireshark_result_message_uses_success_text():
    assert (
        packet_capture_controller._packet_capture_wireshark_result_message(
            "/tmp/capture.pcapng"
        )
        == "Wireshark geöffnet: /tmp/capture.pcapng"
    )


def test_packet_capture_wireshark_result_message_uses_error_text():
    assert (
        packet_capture_controller._packet_capture_wireshark_result_message(
            "/tmp/capture.pcapng",
            "gtk-launch ist nicht verfügbar.",
        )
        == "Wireshark konnte nicht geöffnet werden: gtk-launch ist nicht verfügbar."
    )


def test_packet_capture_start_failure_messages_return_output_and_log_texts():
    assert packet_capture_controller._packet_capture_start_failure_messages(
        "dumpcap permission denied"
    ) == (
        "Capture konnte nicht gestartet werden: dumpcap permission denied",
        "Packet Capture fehlgeschlagen: dumpcap permission denied",
    )


def test_packet_capture_start_failure_messages_strip_surrounding_whitespace():
    assert packet_capture_controller._packet_capture_start_failure_messages(
        "  Fehler  "
    ) == (
        "Capture konnte nicht gestartet werden: Fehler",
        "Packet Capture fehlgeschlagen: Fehler",
    )


def test_packet_capture_stop_failure_messages_return_output_and_log_texts():
    assert packet_capture_controller._packet_capture_stop_failure_messages(
        "terminate failed"
    ) == (
        "Capture-Stopp fehlgeschlagen: terminate failed",
        "Packet Capture-Stopp fehlgeschlagen: terminate failed",
    )


def test_packet_capture_stop_failure_messages_strip_surrounding_whitespace():
    assert packet_capture_controller._packet_capture_stop_failure_messages(
        "  Fehler  "
    ) == (
        "Capture-Stopp fehlgeschlagen: Fehler",
        "Packet Capture-Stopp fehlgeschlagen: Fehler",
    )


def test_packet_capture_state_log_message_uses_started_state():
    assert (
        packet_capture_controller._packet_capture_state_log_message(
            "gestartet",
            "eth0",
        )
        == "Packet Capture gestartet (eth0)."
    )


def test_packet_capture_state_log_message_uses_stopped_state():
    assert (
        packet_capture_controller._packet_capture_state_log_message(
            "gestoppt",
            "wlan0",
        )
        == "Packet Capture gestoppt (wlan0)."
    )


def test_packet_capture_missing_tool_message_matches_expected_text():
    assert (
        packet_capture_controller._packet_capture_missing_tool_message()
        == "Packet Capture ist nicht verfügbar: tshark oder dumpcap fehlt."
    )


def test_packet_capture_missing_tool_message_is_stable_string():
    assert isinstance(
        packet_capture_controller._packet_capture_missing_tool_message(), str
    )
    assert "tshark" in packet_capture_controller._packet_capture_missing_tool_message()


def test_packet_capture_start_guard_message_uses_running_capture_text():
    assert (
        packet_capture_controller._packet_capture_start_guard_message(True, "eth0")
        == "Ein Capture läuft bereits."
    )


def test_packet_capture_start_guard_message_uses_missing_interface_text():
    assert (
        packet_capture_controller._packet_capture_start_guard_message(False, "")
        == "Bitte zuerst ein Capture-Interface auswählen."
    )


def test_packet_capture_file_info_error_message_formats_expected_text():
    assert (
        packet_capture_controller._packet_capture_file_info_error_message(
            "permission denied"
        )
        == "Datei-Info konnte nicht gelesen werden: permission denied"
    )


def test_packet_capture_file_info_error_message_strips_surrounding_whitespace():
    assert (
        packet_capture_controller._packet_capture_file_info_error_message("  Fehler  ")
        == "Datei-Info konnte nicht gelesen werden: Fehler"
    )


def test_packet_capture_completion_failure_messages_return_output_and_log_texts():
    assert packet_capture_controller._packet_capture_completion_failure_messages(
        "eth0",
        7,
    ) == (
        "Hinweis: Capture wurde mit Fehler beendet. Fehlende Rechte für tshark/dumpcap sind häufig die Ursache.",
        "Packet Capture fehlgeschlagen (eth0, rc=7).",
    )


def test_packet_capture_completion_failure_messages_keep_interface_and_rc():
    messages = packet_capture_controller._packet_capture_completion_failure_messages(
        "wlan0",
        3,
    )

    assert messages[1] == "Packet Capture fehlgeschlagen (wlan0, rc=3)."


def test_packet_capture_wireshark_failure_log_message_formats_expected_text():
    assert (
        packet_capture_controller._packet_capture_wireshark_failure_log_message(
            "gtk-launch ist nicht verfügbar."
        )
        == "Wireshark-Start fehlgeschlagen: gtk-launch ist nicht verfügbar."
    )


def test_packet_capture_wireshark_failure_log_message_strips_whitespace():
    assert (
        packet_capture_controller._packet_capture_wireshark_failure_log_message(
            "  Fehler  "
        )
        == "Wireshark-Start fehlgeschlagen: Fehler"
    )


def test_packet_capture_open_location_failure_log_message_formats_expected_text():
    assert (
        packet_capture_controller._packet_capture_open_location_failure_log_message(
            "xdg-open ist nicht verfügbar."
        )
        == "Capture-Datei öffnen fehlgeschlagen: xdg-open ist nicht verfügbar."
    )


def test_packet_capture_open_location_failure_log_message_strips_whitespace():
    assert (
        packet_capture_controller._packet_capture_open_location_failure_log_message(
            "  Fehler  "
        )
        == "Capture-Datei öffnen fehlgeschlagen: Fehler"
    )


def test_packet_capture_missing_tool_log_message_matches_expected_text():
    assert (
        packet_capture_controller._packet_capture_missing_tool_log_message()
        == "Packet Capture fehlgeschlagen: tshark/dumpcap fehlt."
    )


def test_packet_capture_missing_tool_log_message_mentions_required_tools():
    message = packet_capture_controller._packet_capture_missing_tool_log_message()

    assert "tshark" in message
    assert "dumpcap" in message


def test_packet_capture_interfaces_ready_message_joins_multiple_interfaces():
    assert (
        packet_capture_controller._packet_capture_interfaces_ready_message(
            ["eth0", "wlan0", "lo"]
        )
        == "Verfügbare Interfaces: eth0, wlan0, lo"
    )


def test_packet_capture_interfaces_ready_message_handles_single_interface():
    assert (
        packet_capture_controller._packet_capture_interfaces_ready_message(["eth0"])
        == "Verfügbare Interfaces: eth0"
    )


def test_packet_capture_no_interfaces_message_matches_expected_text():
    assert (
        packet_capture_controller._packet_capture_no_interfaces_message()
        == "Keine Capture-Interfaces gefunden. Prüfe tshark, dumpcap oder iproute2."
    )


def test_packet_capture_no_interfaces_message_mentions_required_tools():
    message = packet_capture_controller._packet_capture_no_interfaces_message()

    assert "tshark" in message
    assert "iproute2" in message


def test_packet_capture_dumpcap_permission_message_matches_expected_text():
    assert (
        packet_capture_controller._packet_capture_dumpcap_permission_message()
        == "tshark ist vorhanden, aber dumpcap hat keine ausreichenden Berechtigungen."
    )


def test_packet_capture_dumpcap_permission_message_mentions_tshark_and_dumpcap():
    message = packet_capture_controller._packet_capture_dumpcap_permission_message()

    assert "tshark" in message
    assert "dumpcap" in message


def test_packet_capture_file_info_header_matches_expected_text():
    assert (
        packet_capture_controller._packet_capture_file_info_header()
        == "=== Capture-Datei Info ==="
    )


def test_packet_capture_file_info_header_mentions_capture_file_info():
    header = packet_capture_controller._packet_capture_file_info_header()

    assert "Capture-Datei Info" in header


def test_packet_capture_file_info_lines_format_expected_values():
    assert packet_capture_controller._packet_capture_file_info_lines(
        "/tmp/capture.pcapng",
        "12 kB",
    ) == [
        "=== Capture-Datei Info ===",
        "Datei: /tmp/capture.pcapng",
        "Größe: 12 kB",
    ]


def test_packet_capture_file_info_lines_keep_passed_empty_values():
    assert packet_capture_controller._packet_capture_file_info_lines(
        "",
        "-",
    ) == [
        "=== Capture-Datei Info ===",
        "Datei: ",
        "Größe: -",
    ]


def test_packet_capture_start_text_formats_expected_lines():
    assert (
        packet_capture_controller._packet_capture_start_text(
            "tshark",
            "eth0",
            "/tmp/capture.pcapng",
            "tcp port 443",
        )
        == "=== Packet Capture gestartet ===\n"
        "Tool: tshark\n"
        "Interface: eth0\n"
        "Datei: /tmp/capture.pcapng\n"
        "Filter: tcp port 443"
    )


def test_packet_capture_start_text_uses_dash_for_empty_filter():
    assert packet_capture_controller._packet_capture_start_text(
        "dumpcap",
        "wlan0",
        "/tmp/capture.pcapng",
        "",
    ).endswith("Filter: -")


def test_packet_capture_start_body_lines_format_expected_values():
    assert packet_capture_controller._packet_capture_start_body_lines(
        "tshark",
        "eth0",
        "/tmp/capture.pcapng",
        "tcp port 443",
    ) == [
        "Tool: tshark",
        "Interface: eth0",
        "Datei: /tmp/capture.pcapng",
        "Filter: tcp port 443",
    ]


def test_packet_capture_start_body_lines_use_dash_for_empty_filter():
    assert (
        packet_capture_controller._packet_capture_start_body_lines(
            "dumpcap",
            "wlan0",
            "/tmp/capture.pcapng",
            "",
        )[-1]
        == "Filter: -"
    )


def test_packet_capture_start_lines_format_expected_values():
    assert packet_capture_controller._packet_capture_start_lines(
        "tshark",
        "eth0",
        "/tmp/capture.pcapng",
        "tcp port 443",
    ) == [
        "=== Packet Capture gestartet ===",
        "Tool: tshark",
        "Interface: eth0",
        "Datei: /tmp/capture.pcapng",
        "Filter: tcp port 443",
    ]


def test_packet_capture_start_lines_use_dash_for_empty_filter():
    assert (
        packet_capture_controller._packet_capture_start_lines(
            "dumpcap",
            "wlan0",
            "/tmp/capture.pcapng",
            "",
        )[-1]
        == "Filter: -"
    )


def test_packet_capture_initial_file_name_prefers_current_path_basename():
    assert (
        packet_capture_controller._packet_capture_initial_file_name(
            "/tmp/captures/live_capture.pcapng",
            "/tmp/generated/default_capture.pcapng",
        )
        == "live_capture.pcapng"
    )


def test_packet_capture_initial_file_name_falls_back_to_generated_path():
    assert (
        packet_capture_controller._packet_capture_initial_file_name(
            "",
            "/tmp/generated/default_capture.pcapng",
        )
        == "default_capture.pcapng"
    )
