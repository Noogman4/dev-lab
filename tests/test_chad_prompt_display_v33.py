"""Fold only successful submitted prompts; preserve copy, history and exports."""

import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import Mock

import pytest

from netmon.features import chad_controller as controller
from netmon.services.ai_online_service import AiOnlineService
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app
PROMPT = "PRIVATE_PROMPT_START\nBitte zuerst prüfen.\n```bash\nresolvectl status\n```\nPRIVATE_PROMPT_END"
RESULT = "Ergebnis vollständig.\n```bash\nsystemctl --failed\n```\nDanach die Ausgabe prüfen."


def prepare(app, root, monkeypatch, *, status="completed", deferred=False):
    app.chad_pending_files = []
    app.chad_online_result = ""
    app.chad_chat_history = []
    app.log_safe = lambda *args: None
    app.confirm_chad_send = lambda *args: True
    app.clipboard_clear = root.clipboard_clear
    app.clipboard_append = root.clipboard_append
    service = app.ai_online_service = AiOnlineService()
    service.api_key = "private-fixture-not-real"
    calls = []

    def transport(url, headers, payload, timeout):
        calls.append(payload)
        if status == "http_error":
            return 401, '{"error":{"message":"Unauthorized"}}'
        return 200, json.dumps(
            {
                "status": status,
                "output_text": RESULT,
                "incomplete_details": {"reason": "max_output_tokens"},
            }
        )

    monkeypatch.setattr(service, "_post_json", transport)
    workers = []

    class Thread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            if deferred:
                workers.append(self.target)
            else:
                self.target()

    monkeypatch.setattr(controller.threading, "Thread", Thread)
    monkeypatch.setattr(
        controller, "call_in_ui_thread", lambda app, callback: callback()
    )
    controller.set_chad_direct_prompt(app, "PATH Guard", PROMPT)
    root.update()
    return calls, workers


def test_success_folds_prompt_but_keeps_full_text_and_selection(chad_app, monkeypatch):
    root, app = chad_app
    root.geometry("1024x768")
    calls, _ = prepare(app, root, monkeypatch)
    widget = app.chad_analysis_text
    start = widget.search("PRIVATE_PROMPT_START", "1.0")
    assert widget.dlineinfo(start) is not None
    assert not app.__dict__.get("chad_prompt_views")
    app.run_chad_online_analysis()
    root.update()
    entry = app.chad_output_entries[0]
    view = app.chad_prompt_views[0]
    assert entry["prompt_collapsed"] is True
    assert calls[0]["input"] == PROMPT
    assert app.chad_analysis_current_prompt == PROMPT
    assert PROMPT in controller.get_chad_transcript_text(app)
    assert RESULT in controller.get_chad_transcript_text(app)
    assert "Verwendeten Prompt anzeigen" not in controller.get_chad_transcript_text(app)
    assert widget.search("PRIVATE_PROMPT_START", "1.0") == ""
    hidden_line = widget.dlineinfo(
        widget.search("PRIVATE_PROMPT_START", "1.0", elide=True)
    )
    assert hidden_line is None or hidden_line[3] == 0
    assert widget.dlineinfo(widget.search("Ergebnis vollständig", "1.0")) is not None
    assert view["button"].cget("text") == "Verwendeten Prompt anzeigen"
    collapsed_lines = widget.count("1.0", "end", "displaylines")[0]
    answer = widget.search("Ergebnis vollständig", "1.0")
    widget.tag_add("sel", answer, f"{answer} lineend")
    selection = widget.tag_ranges("sel")
    view["button"].invoke()
    root.update()
    assert entry["prompt_collapsed"] is False
    assert widget.dlineinfo(widget.search("PRIVATE_PROMPT_START", "1.0")) is not None
    assert widget.count("1.0", "end", "displaylines")[0] > collapsed_lines
    assert widget.tag_ranges("sel") == selection
    assert view["button"].cget("text") == "Prompt einklappen"
    app.chad_code_blocks[0]["button"].invoke()
    assert root.clipboard_get() == "resolvectl status"
    view["button"].invoke()
    root.update()
    assert widget.tag_ranges("sel") == selection
    assert not app.chad_code_blocks[0]["button"].winfo_ismapped()
    app.chad_code_blocks[1]["button"].invoke()
    assert root.clipboard_get() == "systemctl --failed"


@pytest.mark.parametrize("status", ["http_error", "incomplete"])
def test_failure_and_partial_answers_do_not_collapse_prompt(
    chad_app, monkeypatch, status
):
    root, app = chad_app
    prepare(app, root, monkeypatch, status=status)
    app.run_chad_online_analysis()
    root.update()
    assert not app.chad_output_entries[0].get("prompt_collapsed")
    assert not app.chad_prompt_views
    app.chad_analysis_text.see("1.0")
    root.update()
    assert app.chad_analysis_text.dlineinfo("2.0") is not None
    assert app.chad_output_entries[-1]["kind"] == "error"


@pytest.mark.parametrize(
    "retry", ["missing_key", "cancelled", "http_error", "incomplete"]
)
def test_retry_expands_previously_completed_prompt_and_keeps_it_on_failure(
    chad_app, monkeypatch, retry
):
    root, app = chad_app
    calls, _ = prepare(app, root, monkeypatch)
    app.run_chad_online_analysis()
    assert app.chad_output_entries[0]["prompt_collapsed"] is True
    if retry == "missing_key":
        app.ai_online_service.api_key = ""
    elif retry == "cancelled":
        app.confirm_chad_send = lambda *args: False
    elif retry == "http_error":
        monkeypatch.setattr(
            app.ai_online_service, "_post_json", lambda *a, **k: (500, "{}")
        )
    else:
        monkeypatch.setattr(
            app.ai_online_service,
            "_post_json",
            lambda *a, **k: (200, '{"status":"incomplete","output_text":"partial"}'),
        )
    app.run_chad_online_analysis()
    root.update()
    assert app.chad_output_entries[0]["prompt_collapsed"] is False
    assert app.chad_prompt_views[0]["button"].cget("text") == "Prompt einklappen"
    assert len(calls) == 1


def test_followups_filters_new_preparation_and_clear_keep_fold_state(
    chad_app, monkeypatch
):
    root, app = chad_app
    prepare(app, root, monkeypatch)
    app.run_chad_online_analysis()
    old_button = app.chad_prompt_views[0]["button"]
    controller.append_to_chad_output(app, "Du", "Rückfrage sichtbar")
    controller.append_to_chad_output(app, "Chad Antwort", "Antwort auf Rückfrage")
    assert not old_button.winfo_exists()
    assert app.chad_output_entries[0]["prompt_collapsed"] is True
    app.chad_output_filter_var.set("Nur Antworten")
    controller.refresh_chad_output_view(app)
    assert not app.chad_prompt_views
    assert "Antwort auf Rückfrage" in controller.get_chad_transcript_text(app)
    app.chad_output_filter_var.set("Alles")
    controller.refresh_chad_output_view(app)
    assert app.chad_prompt_views[0]["entry"]["prompt_collapsed"] is True
    controller.set_chad_direct_prompt(app, "Neuer Auftrag", "NEUER_PROMPT_SICHTBAR")
    root.update()
    assert not app.chad_output_entries[-1].get("prompt_collapsed")
    assert "NEUER_PROMPT_SICHTBAR" in controller.get_chad_transcript_text(app)
    button = app.chad_prompt_views[0]["button"]
    controller.clear_chad_analysis(app)
    assert not app.chad_prompt_views
    assert not button.winfo_exists()
    assert controller.get_chad_transcript_text(app) == ""


@pytest.mark.parametrize("replace", ["prepare_same_text", "clear"])
def test_delayed_completion_never_collapses_a_new_entry(chad_app, monkeypatch, replace):
    root, app = chad_app
    _, workers = prepare(app, root, monkeypatch, deferred=True)
    submitted = app.chad_output_entries[0]
    app.run_chad_online_analysis()
    if replace == "prepare_same_text":
        controller.set_chad_direct_prompt(app, "Neuer Auftrag", PROMPT)
        new_entry = app.chad_output_entries[-1]
    else:
        controller.clear_chad_analysis(app)
    workers.pop()()
    root.update()
    if replace == "prepare_same_text":
        assert submitted["prompt_collapsed"] is True
        assert "prompt_collapsed" not in new_entry
        assert app.chad_output_entries[-1]["title"] == "Chad Antwort: PATH Guard"
    else:
        assert not app.chad_prompt_views
        assert all(entry["text"] != PROMPT for entry in app.chad_output_entries)


def test_save_load_and_browser_copy_preserve_full_prompt(
    chad_app, monkeypatch, tmp_path
):
    root, app = chad_app
    prepare(app, root, monkeypatch)
    app.run_chad_online_analysis()
    path = tmp_path / "analysis.json"
    monkeypatch.setattr(
        controller.filedialog, "asksaveasfilename", lambda **k: str(path)
    )
    controller.save_chad_analysis_to_file(app)
    data = json.loads(path.read_text())
    assert data["current_prompt"] == PROMPT
    assert data["output_entries"][0]["text"] == PROMPT
    assert data["output_entries"][0]["prompt_collapsed"] is True
    assert PROMPT in data["transcript"]
    controller.clear_chad_analysis(app)
    monkeypatch.setattr(controller.filedialog, "askopenfilename", lambda **k: str(path))
    controller.load_chad_analysis_from_file(app)
    root.update()
    assert app.chad_output_entries[0]["prompt_collapsed"] is True
    assert (
        app.chad_prompt_views[0]["button"].cget("text") == "Verwendeten Prompt anzeigen"
    )
    opener = Mock(return_value=True)
    monkeypatch.setattr(app, "_open_url_with_xdg_open", opener)
    controller.copy_prompt_and_open_chatgpt(app)
    assert root.clipboard_get() == PROMPT
    opener.assert_called_once_with("https://chatgpt.com/", label="ChatGPT")
    app.chad_prompt_views[0]["button"].invoke()
    assert app.chad_output_entries[0]["prompt_collapsed"] is False


def test_old_json_has_no_invented_fold_state(chad_app, monkeypatch, tmp_path):
    root, app = chad_app
    prepare(app, root, monkeypatch)
    path = tmp_path / "old.json"
    path.write_text(
        json.dumps(
            {"current_prompt": PROMPT, "output_entries": app.chad_output_entries}
        )
    )
    monkeypatch.setattr(controller.filedialog, "askopenfilename", lambda **k: str(path))
    controller.load_chad_analysis_from_file(app)
    assert not app.chad_prompt_views
    assert "prompt_collapsed" not in app.chad_output_entries[0]


def test_prompt_title_that_resembles_an_answer_still_folds_its_own_entry(
    chad_app, monkeypatch
):
    root, app = chad_app
    prepare(app, root, monkeypatch)
    controller.set_chad_direct_prompt(app, "Chad Analyse", PROMPT)
    submitted = app.chad_output_entries[-1]
    assert submitted["kind"] == "answer"
    app.run_chad_online_analysis()
    assert submitted["prompt_collapsed"] is True
    assert not app.chad_output_entries[0].get("prompt_collapsed")


def test_collapsed_visual_fixture(chad_app, monkeypatch):
    root, app = chad_app
    root.geometry("1100x700")
    prepare(app, root, monkeypatch)
    app.run_chad_online_analysis()
    root.update()
    if shutil.which("import"):
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/chad-prompt-collapsed.png",
            ],
            check=True,
            timeout=10,
        )
        assert Path("/work/chad-prompt-collapsed.png").is_file()
