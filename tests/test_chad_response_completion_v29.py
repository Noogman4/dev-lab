"""Bounded response budgets and visible incomplete answers without API calls."""

import json
import tkinter as tk

import pytest

from netmon.features import chad_controller as controller
from netmon.services.ai_online_service import AiOnlineService
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app


def invoke(service, operation):
    return (
        service.analyze("fixture")
        if operation == "analyze"
        else service.chat([{"role": "user", "content": "fixture"}])
    )


@pytest.mark.parametrize("operation", ["analyze", "chat"])
@pytest.mark.parametrize("nested", [False, True])
@pytest.mark.parametrize("reason", ["max_output_tokens", "content_filter", None])
def test_partial_output_is_preserved_with_explicit_failure_not_retried(
    operation, nested, reason
):
    service = AiOnlineService()
    service.api_key = "fixture-credential-not-real"
    partial = "Teilantwort. " * 300 + "END_OF_RECEIVED_PART"
    data = {
        "status": "incomplete",
        "incomplete_details": {"reason": reason},
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    if nested:
        data["output"] = [
            {"type": "message", "content": [{"type": "output_text", "text": partial}]}
        ]
    else:
        data["output_text"] = partial
    calls = []
    service._post_json = lambda *args, **kwargs: calls.append(args) or (
        200,
        json.dumps(data),
    )
    success, result = invoke(service, operation)
    assert not success and service.last_response_incomplete
    assert partial in result
    assert result.startswith("Antwort unvollständig:")
    assert ("Ausgabelimit erreicht" in result) == (reason == "max_output_tokens")
    assert ("API-Inhaltsfilter" in result) == (reason == "content_filter")
    assert len(calls) == 1
    assert service.last_usage["output_tokens"] == 20


@pytest.mark.parametrize("operation", ["analyze", "chat"])
def test_empty_incomplete_answer_is_not_reported_as_generic_empty_success(operation):
    service = AiOnlineService()
    service.api_key = "fixture-credential-not-real"
    service._post_json = lambda *args, **kwargs: (
        200,
        '{"status":"incomplete","incomplete_details":{"reason":"max_output_tokens"},"output":[]}',
    )
    success, result = invoke(service, operation)
    assert not success and "Ausgabelimit erreicht" in result


@pytest.mark.parametrize("operation", ["analyze", "chat"])
def test_incomplete_flag_resets_for_completed_http_failure_and_missing_key(operation):
    service = AiOnlineService()
    service.api_key = "fixture-credential-not-real"
    responses = iter(
        [
            (200, '{"status":"incomplete","output_text":"partial"}'),
            (200, '{"status":"completed","output_text":"complete"}'),
            (401, '{"message":"Unauthorized"}'),
        ]
    )
    service._post_json = lambda *args, **kwargs: next(responses)
    assert not invoke(service, operation)[0] and service.last_response_incomplete
    assert invoke(service, operation) == (True, "complete")
    assert not service.last_response_incomplete
    assert not invoke(service, operation)[0] and not service.last_response_incomplete
    service.last_response_incomplete = True
    service.api_key = ""
    assert not invoke(service, operation)[0] and not service.last_response_incomplete


@pytest.mark.parametrize("status", ["failed", "cancelled", "queued", "in_progress"])
def test_other_nonfinal_response_states_cannot_become_completed(status):
    service = AiOnlineService()
    service.api_key = "fixture-credential-not-real"
    service._post_json = lambda *args, **kwargs: (
        200,
        json.dumps({"status": status, "output_text": "not a complete answer"}),
    )
    success, result = service.analyze("fixture")
    assert not success and "nicht abgeschlossen" in result


@pytest.mark.parametrize("length,expected", [(100, 4096), (40000, 5120), (80000, 6400)])
@pytest.mark.parametrize(
    "files", [[], [{"type": "text", "path": "never-read-fixture"}]]
)
def test_analysis_request_has_bounded_room_for_report_and_no_retry(
    length, expected, files
):
    service = AiOnlineService()
    service.api_key = "fixture-credential-not-real"
    calls = []

    def transport(url, headers, payload, timeout):
        calls.append(payload)
        assert payload["max_output_tokens"] == expected
        assert 4096 <= payload["max_output_tokens"] <= 6400
        assert timeout >= 60
        return 200, '{"status":"completed","output_text":"Complete fixture."}'

    service._post_json = transport
    assert service.analyze("x" * length, files=files) == (True, "Complete fixture.")
    assert len(calls) == 1


@pytest.mark.parametrize("operation", ["analysis", "chat"])
def test_actual_chad_widgets_do_not_mark_partial_answers_completed(
    chad_app, monkeypatch, operation
):
    root, app = chad_app
    app.chad_analysis_current_prompt = "private fixture"
    app.chad_online_result = "previous complete result"
    app.chad_chat_history = []
    app.chad_pending_files = [{"type": "text", "path": "never-read-fixture"}]
    app.chad_settings_tokens_var = tk.StringVar(master=root)
    app.chad_output_filter_var.set("Nur Antworten")
    app.confirm_chad_send = lambda *args: True
    app.log_safe = lambda *args: None
    service = app.ai_online_service = AiOnlineService()
    service.api_key = "fixture-credential-not-real"
    partial = "Private response prefix. " * 100 + "TRUNCATED_SENTENCE"
    service._post_json = lambda *args, **kwargs: (
        200,
        json.dumps(
            {
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
                "output_text": partial,
                "usage": {"output_tokens": 1400},
            }
        ),
    )

    class ImmediateThread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(controller.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        controller,
        "update_chad_summary_from_result",
        lambda *args: pytest.fail(
            "partial response must not become a completed summary"
        ),
    )
    if operation == "analysis":
        app.run_chad_online_analysis()
        assert app.chad_online_status_var.get() == "Analyse unvollständig."
    else:
        app.chad_chat_input.insert("1.0", "Private question")
        app.send_chad_chat_message()
        assert app.chad_chat_status_var.get().startswith("Antwort unvollständig:")
    root.update()
    output = app.chad_analysis_text.get("1.0", "end")
    assert partial in output
    assert "Unvollständige API-Antwort" in output
    assert "Ausgabelimit erreicht" in output
    assert app.chad_online_result == "previous complete result"
    assert app.chad_pending_files
    assert all(row["role"] == "user" for row in app.chad_chat_history)
    assert "1400" in app.chad_settings_tokens_var.get()
