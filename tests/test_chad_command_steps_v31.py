"""Step-by-step instructions reach all Chad paths; buttons copy one command."""

import json

import pytest

from netmon.features import chad_controller as controller
from netmon.services.ai_analysis_service import AiAnalysisService
from netmon.services.ai_online_service import AiOnlineService
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app

COMMANDS = [
    "systemctl --failed --no-pager",
    "resolvectl status",
    "resolvectl query example.com",
]
STEP_RESPONSE = """Empfehlung: Fehlgeschlagene Dienste zuerst nur anzeigen.
```bash
systemctl --failed --no-pager
```
Prüfung: Bei 0 Einträgen ist kein fehlgeschlagener Dienst gemeldet.

Empfehlung: Den Resolver und seine DNS-Server prüfen.
```bash
resolvectl status
```
Prüfung: Die angezeigten Server mit dem ausgewählten Profil vergleichen.

Empfehlung: Anschließend eine Namensauflösung prüfen.
```bash
resolvectl query example.com
```
Prüfung: Die tatsächliche Ausgabe einfügen, bevor Änderungen geplant werden."""


def assert_step_guidance(text):
    assert "zuerst Empfehlung und Zweck" in text
    assert "Genau einen zusammengehörigen Terminalbefehl pro Codeblock" in text
    assert "Prüfbefehl in einem eigenen Codeblock" in text
    assert "keine Shell-Prompts" in text
    assert "keine Erläuterungen, Kommentare oder Beispielausgaben" in text
    assert "kein Gesamtskript" in text
    assert "niemals mechanisch pro Zeile trennen" in text
    assert "um das Ergebnis bitten" in text


@pytest.mark.parametrize(
    "title", ["PATH Guard", "DNS", "Security", "Startup Guard", "rkhunter"]
)
def test_exported_prompts_request_individual_steps_and_keep_sanitization(title):
    prompt = AiAnalysisService().build_prompt(
        title, "Resolver unerwartet\npassword=private-fixture-value"
    )
    assert_step_guidance(prompt)
    assert prompt.index("Terminalbefehle Schritt") < prompt.index("Daten:")
    assert "Resolver unerwartet" in prompt
    assert "private-fixture-value" not in prompt
    assert "[REDACTED]" in prompt


@pytest.mark.parametrize("method", ["analyze", "chat"])
@pytest.mark.parametrize("with_image", [False, True])
def test_transport_gets_guidance_even_for_direct_prompts_and_followups(
    monkeypatch, method, with_image, chad_image_snapshot
):
    service = AiOnlineService()
    service.api_key = "private-fake-key"
    calls = []
    image_url = "data:image/png;base64,cHJpdmF0ZQ=="
    monkeypatch.setattr(service, "image_to_data_url", lambda path: image_url)

    def transport(url, headers, payload, timeout):
        calls.append(payload)
        return 200, json.dumps({"status": "completed", "output_text": STEP_RESPONSE})

    monkeypatch.setattr(service, "_post_json", transport)
    files = [{"type": "image", "snapshot": chad_image_snapshot}] if with_image else []
    direct_prompt = "Nur diese Beobachtung prüfen."
    history = [
        {"role": "user", "content": "DNS prüfen"},
        {"role": "assistant", "content": "Bitte den Zustand zeigen."},
        {"role": "user", "content": direct_prompt},
    ]
    before = json.dumps(history)
    ok, response = getattr(service, method)(
        direct_prompt if method == "analyze" else history, files=files
    )
    assert ok and response == STEP_RESPONSE
    assert len(calls) == 1
    payload = calls[0]
    assert_step_guidance(payload["instructions"])
    if method == "analyze" and not with_image:
        assert payload["input"] == direct_prompt
    else:
        latest = payload["input"][-1]
        assert latest["role"] == "user"
        assert latest["content"][0] == {"type": "input_text", "text": direct_prompt}
        images = [item for item in latest["content"] if item["type"] == "input_image"]
        assert len(images) == int(with_image)
        if images:
            assert images[0]["image_url"] == image_url
    assert json.dumps(history) == before
    assert "private-fake-key" not in payload["instructions"]


def test_each_step_has_its_own_real_copy_button_and_explanation(chad_app):
    root, app = chad_app
    controller.append_to_chad_output(app, "Chad Antwort: Prüfschritte", STEP_RESPONSE)
    root.update()
    assert len(app.chad_code_blocks) == 3
    for block, command in zip(app.chad_code_blocks, COMMANDS):
        block["button"].invoke()
        assert root.clipboard_get() == command
        assert block["code"] == command
        assert "Empfehlung" not in root.clipboard_get()
        assert "Prüfung" not in root.clipboard_get()
    transcript = controller.get_chad_transcript_text(app)
    assert STEP_RESPONSE in transcript
    assert transcript.index(COMMANDS[0]) < transcript.index("Prüfung:")
    assert transcript.index("Prüfung:") < transcript.index(COMMANDS[1])


def test_multiline_command_remains_one_copy_operation(chad_app):
    root, app = chad_app
    command = "for name in alpha beta; do\n    printf '%s\\n' \"$name\"\ndone"
    source = f"Empfehlung: Ein zusammengehöriger Befehl.\n```bash\n{command}\n```\nPrüfung danach."
    controller.append_to_chad_output(app, "Chad Antwort: Schleife", source)
    root.update()
    assert len(app.chad_code_blocks) == 1
    app.chad_code_blocks[0]["button"].invoke()
    assert root.clipboard_get() == command
