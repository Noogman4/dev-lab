"""Offline API errors and actual Tk output; no credentials or network used."""

import json
import tkinter as tk

import pytest

from netmon.app import App
from netmon.features import chad_controller as controller
from netmon.services.ai_online_service import AiOnlineService


@pytest.mark.parametrize("operation", ["analyze", "chat"])
@pytest.mark.parametrize(
    "status,code",
    [
        (401, "invalid_api_key"),
        (401, "ip_not_authorized"),
        (403, "permission_denied"),
        (429, "insufficient_quota"),
    ],
)
def test_status_and_codes_survive_without_reflected_credentials(
    operation, status, code
):
    service = AiOnlineService()
    service.api_key = "synthetic-credential-for-test-only"
    body = json.dumps(
        {
            "error": {
                "message": f"Unauthorized {service.api_key} Bearer alternate-credential sk-proj-fake123456",
                "type": "invalid_request_error",
                "code": code,
            }
        }
    )
    calls = []

    def transport(url, headers, payload, timeout):
        assert url == "https://api.openai.com/v1/responses"
        assert headers["Authorization"] == "Bearer " + service.api_key
        calls.append(url)
        return status, body

    service._post_json = transport
    argument = (
        "fixture"
        if operation == "analyze"
        else [{"role": "user", "content": "fixture"}]
    )
    success, result = getattr(service, operation)(argument)
    assert not success and len(calls) == 1
    assert f"HTTP-Status: {status}" in result
    assert f"API-Code: {code}" in result
    assert "API-Typ: invalid_request_error" in result
    assert service.api_key not in result
    assert "alternate-credential" not in result
    assert "sk-proj-fake123456" not in result
    assert ("Speichern im Schlüsselbund" in result) == (status == 401)


@pytest.mark.parametrize(
    "body",
    [
        "",
        "<html>Unauthorized</html>",
        "null",
        "[]",
        '"Unauthorized"',
        '{"error":{"message":[],"code":{},"type":null}}',
    ],
)
def test_unknown_error_shapes_keep_http_status_without_raw_body(body):
    service = AiOnlineService()
    result = service._format_api_error(body, 401)
    assert "HTTP-Status: 401" in result
    assert "Unbekannter API-Fehler" in result
    assert "<html>" not in result


@pytest.mark.parametrize("operation", ["analyze", "chat"])
def test_transport_exception_is_redacted(operation):
    service = AiOnlineService()
    service.api_key = "synthetic-credential-for-test-only"

    def failed(*args, **kwargs):
        raise RuntimeError("Bearer " + service.api_key)

    service._post_json = failed
    argument = (
        "fixture"
        if operation == "analyze"
        else [{"role": "user", "content": "fixture"}]
    )
    success, result = getattr(service, operation)(argument)
    assert not success and service.api_key not in result
    assert "[REDACTED]" in result


@pytest.mark.parametrize("operation", ["analysis", "chat"])
@pytest.mark.parametrize("output_filter", ["Alles", "Nur Antworten", "Nur Ergebnisse"])
def test_real_tk_error_visible_under_all_filters_without_chat_history_pollution(
    monkeypatch, operation, output_filter
):
    root = tk.Tk()
    root.withdraw()
    app = App.__new__(App)
    app.lang = {}
    app.chad_enabled_var = tk.BooleanVar(master=root, value=True)
    for name in (
        "chad_analysis_status_var",
        "chad_online_status_var",
        "chad_chat_status_var",
        "chad_settings_api_status_var",
    ):
        setattr(app, name, tk.StringVar(master=root))
    app.chad_output_filter_var = tk.StringVar(master=root, value=output_filter)
    app.chad_analysis_text = tk.Text(root)
    app.chad_chat_input = tk.Text(root)
    app.chad_chat_input.insert("1.0", "Private fixture question")
    app.chad_chat_history = []
    app.chad_output_entries = []
    app.chad_analysis_current_prompt = "Private fixture analysis"
    app.chad_pending_files = [{"type": "text", "path": "not-read-fixture.txt"}]
    app.confirm_chad_send = lambda *args: True
    logs = []
    app.log_safe = logs.append
    service = app.ai_online_service = AiOnlineService()
    service.api_key = "synthetic-credential-for-test-only"
    service._post_json = lambda *args, **kwargs: (
        401,
        json.dumps(
            {
                "error": {
                    "message": "Unauthorized " + service.api_key,
                    "code": "invalid_api_key",
                }
            }
        ),
    )

    class ImmediateThread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(controller.threading, "Thread", ImmediateThread)
    try:
        if operation == "analysis":
            app.run_chad_online_analysis()
        else:
            app.send_chad_chat_message()
        output = app.chad_analysis_text.get("1.0", "end")
        assert "HTTP-Status: 401" in output
        assert "API-Code: invalid_api_key" in output
        assert "Speichern im Schlüsselbund" in output
        assert service.api_key not in output
        assert all(service.api_key not in line for line in logs)
        assert app.chad_output_entries[-1]["kind"] == "error"
        assert app.chad_output_filter_var.get() == output_filter
        assert app.chad_pending_files
        assert app.chad_analysis_current_prompt == "Private fixture analysis"
        assert all(row["role"] == "user" for row in app.chad_chat_history)
        assert app.chad_settings_api_status_var.get() == "API-Key vorhanden"
    finally:
        root.destroy()
