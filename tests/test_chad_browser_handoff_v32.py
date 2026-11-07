"""Private Tk clipboard/browser handoff; no actual browser or API requests."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from netmon import app as app_module
from netmon.features import chad_controller as controller
from netmon.ui.tabs.chad_tab import build_chad_analysis_content
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app


def prepare(app, root, monkeypatch):
    app.chad_analysis_current_prompt = (
        "Empfehlung prüfen.\n```bash\nresolvectl status\n```"
    )
    app.chad_chat_history = [{"role": "user", "content": "Nicht der Analyse-Prompt"}]
    app.chad_pending_files = []
    app.ai_online_service = Mock()
    app.clipboard_clear = root.clipboard_clear
    app.clipboard_append = root.clipboard_append
    opener = Mock(return_value=True)
    monkeypatch.setattr(app, "_open_url_with_xdg_open", opener)
    return opener


@pytest.mark.parametrize(
    "language,geometry", [("de", "650x480"), ("de", "1024x768"), ("en", "820x480")]
)
def test_real_button_copies_only_prepared_prompt_and_is_visible(
    chad_app, monkeypatch, language, geometry
):
    root, app = chad_app
    app.lang = json.loads(
        (Path(__file__).parents[1] / "netmon/lang" / f"{language}.json").read_text()
    )
    for child in app.tab_chad_analysis.winfo_children():
        child.destroy()
    build_chad_analysis_content(app, {})
    root.geometry(geometry)
    opener = prepare(app, root, monkeypatch)
    controller.append_to_chad_output(app, "Chad Antwort", "Alte Antwort nicht kopieren")
    prompt = app.chad_analysis_current_prompt
    history = list(app.chad_chat_history)
    entries = list(app.chad_output_entries)
    root.clipboard_clear()
    root.clipboard_append("old clipboard")
    root.update()
    app.btn_chad_browser.invoke()
    root.update()
    assert root.clipboard_get() == prompt
    opener.assert_called_once_with("https://chatgpt.com/", label="ChatGPT")
    assert app.chad_chat_history == history
    assert app.chad_output_entries == entries
    assert app.chad_analysis_current_prompt == prompt
    assert app.ai_online_service.mock_calls == []
    assert (
        str(app.btn_chad_browser.cget("text")) == app.lang["chad_btn_copy_open_chatgpt"]
    )
    for button in (app.btn_chad_import_file, app.btn_chad_browser, app.btn_chad_online):
        assert button.winfo_ismapped()
        assert root.winfo_rootx() <= button.winfo_rootx()
        assert (
            button.winfo_rootx() + button.winfo_width()
            <= root.winfo_rootx() + root.winfo_width()
        )
    assert app.lang["chad_browser_prompt_copied"] == app.chad_analysis_status_var.get()


@pytest.mark.parametrize("prompt", [None, "", " \n "])
def test_no_prompt_preserves_clipboard_and_does_not_open_browser(
    chad_app, monkeypatch, prompt
):
    root, app = chad_app
    opener = prepare(app, root, monkeypatch)
    app.chad_analysis_current_prompt = prompt
    root.clipboard_clear()
    root.clipboard_append("keep clipboard")
    assert not controller.copy_prompt_and_open_chatgpt(app)
    assert root.clipboard_get() == "keep clipboard"
    opener.assert_not_called()
    assert "vorbereiten" in app.chad_analysis_status_var.get()


def test_clipboard_failure_does_not_launch_or_expose_raw_exception(
    chad_app, monkeypatch
):
    root, app = chad_app
    opener = prepare(app, root, monkeypatch)
    app.clipboard_append = Mock(side_effect=RuntimeError("private fixture content"))
    assert not controller.copy_prompt_and_open_chatgpt(app)
    opener.assert_not_called()
    assert "nicht kopiert" in app.chad_analysis_status_var.get()
    assert "private fixture content" not in app.chad_analysis_status_var.get()


@pytest.mark.parametrize("raises", [False, True])
def test_browser_failure_keeps_copied_prompt_for_manual_use(
    chad_app, monkeypatch, raises
):
    root, app = chad_app
    opener = prepare(app, root, monkeypatch)
    opener.return_value = False
    if raises:
        opener.side_effect = OSError("private fixture error")
    assert not controller.copy_prompt_and_open_chatgpt(app)
    assert root.clipboard_get() == app.chad_analysis_current_prompt
    assert "selbst öffnen" in app.chad_analysis_status_var.get()
    assert "private fixture error" not in app.chad_analysis_status_var.get()


def test_disabled_chad_does_not_disable_browser_choice_and_images_stay_local(
    chad_app, monkeypatch
):
    root, app = chad_app
    opener = prepare(app, root, monkeypatch)
    app.chad_enabled_var.set(False)
    controller.update_chad_controls_state(app)
    assert app.btn_chad_online.instate(["disabled"])
    assert not app.btn_chad_browser.instate(["disabled"])
    app.chad_pending_files = [{"type": "image", "path": "/private/not-opened.png"}]
    original = app.chad_analysis_current_prompt + "\npassword=private-fixture-secret"
    app.chad_analysis_current_prompt = original
    app.btn_chad_browser.invoke()
    assert "private-fixture-secret" not in root.clipboard_get()
    assert "[REDACTED]" in root.clipboard_get()
    assert app.chad_analysis_current_prompt == original
    assert app.chad_pending_files == [
        {"type": "image", "path": "/private/not-opened.png"}
    ]
    assert "Bilder bitte manuell" in app.chad_analysis_status_var.get()
    opener.assert_called_once_with("https://chatgpt.com/", label="ChatGPT")
    assert app.ai_online_service.mock_calls == []


def test_real_url_opener_receives_only_fixed_url_after_clipboard_is_ready(
    chad_app, monkeypatch
):
    root, app = chad_app
    app.chad_analysis_current_prompt = "Private fixture never in URL or logs"
    app.clipboard_clear = root.clipboard_clear
    app.clipboard_append = root.clipboard_append
    logs = []
    app.log_safe = logs.append
    calls = []
    monkeypatch.setattr(app_module.shutil, "which", lambda program: "/usr/bin/xdg-open")

    def launch(args, **kwargs):
        assert root.clipboard_get() == app.chad_analysis_current_prompt
        calls.append(args)
        return Mock()

    monkeypatch.setattr(app_module.subprocess, "Popen", launch)
    app.btn_chad_browser.invoke()
    assert calls == [["xdg-open", "https://chatgpt.com/"]]
    assert logs and all(app.chad_analysis_current_prompt not in line for line in logs)
