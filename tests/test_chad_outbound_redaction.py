"""Text bound for the OpenAI API uses NetMon's shared redaction contract.

Synthetic credentials only; the transport is always faked.
"""

import json
from types import SimpleNamespace

import pytest

from netmon.core import log_redaction as redact
from netmon.features import chad_controller as controller
from netmon.features.process_guard_controller import format_process_guard_details
from netmon.services.ai_analysis_service import AiAnalysisService
from netmon.services.ai_online_service import AiOnlineService
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app

SECRET = "SYNTHETIC_CHAD_SECRET_42"

CREDENTIAL_FORMS = [
    f"mysql --password {SECRET} --host db",
    f"tool --api-key '{SECRET} two words'",
    f"tool --auth-token {SECRET}",
    f"Authorization: Basic {SECRET}",
    f"Authorization: Bearer {SECRET}",
    f"Cookie: session={SECRET}; other=1",
    f"Set-Cookie: session={SECRET}; secure",
    f"-----BEGIN OPENSSH PRIVATE KEY-----\n{SECRET}\n-----END OPENSSH PRIVATE KEY-----",
    f"key sk-proj-{SECRET}",
    f"https://admin:{SECRET}@example.invalid/path",
    f"PresharedKey = {SECRET}",
    f"preshared_key: {SECRET}",
    f"PrivateKey = {SECRET}",
    f"password={SECRET}",
    f"sshpass -p {SECRET} ssh backup@host",
    f"sshpass -p'{SECRET}' rsync -a src host:dst",
    f"mysql -u root -p{SECRET} app",
    f"mysqldump -p'{SECRET}' app",
    f"curl -u admin:{SECRET} https://example.invalid",
    f"curl --user 'admin:{SECRET}' https://example.invalid",
    f"docker login -u me -p {SECRET} registry.example.invalid",
]

UNCHANGED = [
    "Ein API-Token erlaubt Zugriff auf eine API.",
    "ssh -p 2222 host",
    "sshpass -f /run/pw ssh -p 2222 host",
    "mysql -P 3306 -u root -p app",
    "curl --user-agent a:b https://example.invalid",
    "docker run -p 80:80 nginx",
    "rsync -p src dst",
    "UFW BLOCK IN=eth0 SRC=192.0.2.22 DPT=22",
]


@pytest.mark.parametrize("text", CREDENTIAL_FORMS)
def test_ai_sanitizer_uses_shared_filter_for_all_credential_forms(text):
    result = AiAnalysisService().sanitize_content(text)
    assert SECRET not in result
    assert "REDACTED" in result
    assert redact.redact_sensitive_text(result) == result


@pytest.mark.parametrize("text", UNCHANGED)
def test_shared_filter_keeps_ports_and_prose_readable(text):
    assert redact.redact_sensitive_text(text) == text


def test_curl_redaction_keeps_user_name():
    result = redact.redact_sensitive_text(f"curl -u admin:{SECRET} https://x")
    assert result == "curl -u admin:[REDACTED] https://x"


def test_process_guard_cmdline_is_redacted_in_chad_prompt():
    finding = {
        "pid": 4242,
        "name": "mysql",
        "cmdline": ["mysql", "-u", "root", "--password", SECRET, "--host", "db"],
    }
    details = format_process_guard_details(finding)
    prompt = controller.build_chad_analysis_prompt(
        SimpleNamespace(), "Process Guard Fund Analyse", details
    )
    assert SECRET not in prompt
    assert "--password [REDACTED]" in prompt


def _capturing_service(monkeypatch):
    service = AiOnlineService()
    service.api_key = "private-fake-key"
    calls = []

    def transport(url, headers, payload, timeout):
        calls.append(payload)
        return 200, json.dumps({"status": "completed", "output_text": "ok"})

    monkeypatch.setattr(service, "_post_json", transport)
    return service, calls


@pytest.mark.parametrize("text", CREDENTIAL_FORMS)
def test_online_analyze_redacts_at_final_boundary(monkeypatch, text):
    service, calls = _capturing_service(monkeypatch)
    ok, _ = service.analyze("Direkter Prompt:\n" + text)
    assert ok
    assert SECRET not in json.dumps(calls[0])


def test_online_chat_redacts_local_messages_at_final_boundary(monkeypatch):
    service, calls = _capturing_service(monkeypatch)
    assistant_text = "Beispiel: mysql -u root -p"
    history = [
        {"role": "user", "content": f"Mein Befehl: sshpass -p {SECRET} ssh host"},
        {"role": "assistant", "content": assistant_text},
        {"role": "user", "content": f"Und PresharedKey = {SECRET}?"},
    ]
    before = json.dumps(history)
    ok, _ = service.chat(history)
    assert ok
    payload = json.dumps(calls[0])
    assert SECRET not in payload
    assert calls[0]["input"][2]["content"][0]["text"] == assistant_text
    assert json.dumps(history) == before


@pytest.mark.parametrize(
    "prepare",
    [
        lambda app: controller.set_chad_direct_prompt(
            app, "Linux-Hilfe", f"Erkläre: sshpass -p {SECRET} ssh host"
        ),
        lambda app: controller.set_chad_analysis(
            app,
            "Process Guard Fund Analyse",
            format_process_guard_details(
                {"pid": 1, "cmdline": ["curl", "-u", f"admin:{SECRET}", "https://x"]}
            ),
        ),
    ],
)
def test_prepared_preview_is_exactly_the_request_text(monkeypatch, chad_app, prepare):
    _root, app = chad_app
    prepare(app)
    preview = app.chad_analysis_current_prompt
    assert SECRET not in preview
    assert any(entry.get("text") == preview for entry in app.chad_output_entries)

    service, calls = _capturing_service(monkeypatch)
    ok, _ = service.analyze(preview)
    assert ok
    assert calls[0]["input"] == preview


@pytest.mark.parametrize("program", ["mysql", "curl", "docker login", "sshpass"])
def test_program_patterns_stay_linear_on_long_lines(program):
    import time

    started = time.perf_counter()
    redact.redact_sensitive_text((program + " ") * 10000)
    assert time.perf_counter() - started < 1.0
