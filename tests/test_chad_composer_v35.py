"""Real Tk send/newline shortcuts and bounded composer growth; offline only."""

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


@pytest.mark.parametrize("action", ["<Return>", "<KP_Enter>", "button"])
def test_send_controls_call_existing_action_once_without_adding_newline(
    chad_app, action
):
    root, app = chad_app
    app.send_chad_chat_message = Mock(return_value=None)
    field = app.chad_chat_input
    field.insert("1.0", "Eine Rückfrage")
    field.focus_force()
    root.update()
    if action == "button":
        app.btn_chad_send.invoke()
    else:
        field.event_generate(action)
    root.update()
    app.send_chad_chat_message.assert_called_once_with()
    assert field.get("1.0", "end-1c") == "Eine Rückfrage"


@pytest.mark.parametrize("key", ["<Shift-Return>", "<Shift-KP_Enter>"])
def test_shift_enter_inserts_newline_at_cursor_without_sending(chad_app, key):
    root, app = chad_app
    app.send_chad_chat_message = Mock()
    field = app.chad_chat_input
    field.insert("1.0", "einszwei")
    field.mark_set("insert", "1.4")
    field.focus_force()
    root.update()
    field.event_generate(key)
    root.update()
    assert field.get("1.0", "end-1c") == "eins\nzwei"
    app.send_chad_chat_message.assert_not_called()


def test_pasted_multiline_text_grows_to_cap_and_clear_shrinks(chad_app):
    root, app = chad_app
    field = app.chad_chat_input
    root.update()
    assert int(field.cget("height")) == 3
    content = "\n".join(f"Zeile {i}" for i in range(30))
    root.clipboard_clear()
    root.clipboard_append(content)
    field.focus_force()
    field.event_generate("<<Paste>>")
    root.update()
    assert field.get("1.0", "end-1c") == content
    assert int(field.cget("height")) == 12
    field.see("end")
    root.update()
    assert field.dlineinfo("end-1c") is not None
    field.tag_add("sel", "2.0", "2.end")
    selection = field.tag_ranges("sel")
    field.insert("end-1c", "\nEine weitere Zeile")
    root.update()
    assert int(field.cget("height")) == 12
    assert field.tag_ranges("sel") == selection
    field.delete("1.0", "end")
    root.update()
    assert int(field.cget("height")) == 3


@pytest.mark.parametrize("source", ["history menu", "history shortcut", "input menu"])
def test_paste_goes_to_chad_composer(chad_app, source):
    root, app = chad_app
    app.send_chad_chat_message = Mock()
    history = app.chad_analysis_text
    field = app.chad_chat_input
    controller.append_to_chad_output(app, "Chad Antwort", "Vorhandener Verlauf")
    existing_history = history.get("1.0", "end-1c")
    app.attach_all_chad_context_menus()
    content = "System-Log: Beispiel\nEine zweite Zeile mit Umlauten äöü."
    root.clipboard_clear()
    root.clipboard_append(content)
    root.update()

    if source == "history shortcut":
        history.focus_force()
        root.update()
        history.event_generate("<Control-v>")
    else:
        widget, menu = (
            (history, history._chad_context_menu)
            if source == "history menu"
            else (field, field._netmon_context_menu)
        )
        if source == "history menu":
            assert menu.entrycget(1, "label") == "In Chat-Eingabe einfügen"
        widget.event_generate("<Button-3>", x=12, y=10)
        root.update()
        assert menu.winfo_ismapped()
        y = menu.yposition(1) + 4
        menu.event_generate("<Enter>", x=10, y=y)
        menu.event_generate("<Motion>", x=10, y=y)
        menu.event_generate("<Button-1>", x=10, y=y)
        menu.event_generate("<ButtonRelease-1>", x=10, y=y)
    root.update()

    assert field.get("1.0", "end-1c") == content
    assert root.focus_get() is field
    assert history.get("1.0", "end-1c") == existing_history
    assert str(history.cget("state")) == "disabled"
    app.send_chad_chat_message.assert_not_called()


def test_paste_from_history_leaves_draft_when_chad_disabled(chad_app):
    root, app = chad_app
    app.attach_all_chad_context_menus()
    app.chad_chat_input.insert("1.0", "Entwurf")
    app.chad_enabled_var.set(False)
    controller.update_chad_controls_state(app)
    root.clipboard_clear()
    root.clipboard_append("Log aus der Zwischenablage")

    app.chad_analysis_text._chad_context_menu.invoke(1)

    assert app.chad_chat_input.get("1.0", "end-1c") == "Entwurf"
    assert app.chad_analysis_status_var.get() == "Chad-Anbindung ist deaktiviert."


def test_soft_wrapping_and_window_resize_update_height_without_changing_text(chad_app):
    root, app = chad_app
    field = app.chad_chat_input
    root.geometry("650x480")
    content = "Ein längerer Satz für die Eingabe. " * 12
    field.insert("1.0", content)
    root.update()
    narrow = int(field.cget("height"))
    assert 3 < narrow <= 12
    root.geometry("1500x700")
    root.update()
    assert 3 <= int(field.cget("height")) < narrow
    assert field.get("1.0", "end-1c") == content


def test_send_button_uses_actual_controller_and_preserves_multiline_payload(
    chad_app, monkeypatch
):
    root, app = chad_app
    app.chad_chat_history = []
    app.chad_pending_files = []
    app.log_safe = lambda *args: None
    app.ai_online_service = AiOnlineService()
    app.ai_online_service.api_key = "private-fixture-not-real"
    calls = []

    def transport(url, headers, payload, timeout):
        calls.append(payload)
        return 200, json.dumps(
            {"status": "completed", "output_text": "Vollständige Antwort"}
        )

    monkeypatch.setattr(app.ai_online_service, "_post_json", transport)

    class ImmediateThread:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(controller.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        controller, "call_in_ui_thread", lambda app, callback: callback()
    )
    content = "\n".join(f"Meine Frage {i}" for i in range(9))
    app.chad_chat_input.insert("1.0", content)
    root.update()
    assert int(app.chad_chat_input.cget("height")) == 9
    app.btn_chad_send.invoke()
    root.update()
    assert len(calls) == 1
    assert calls[0]["input"][-1]["content"][0]["text"] == content
    assert app.chad_chat_history[0] == {"role": "user", "content": content}
    assert app.chad_chat_history[-1]["content"] == "Vollständige Antwort"
    assert app.chad_chat_input.get("1.0", "end-1c") == ""
    assert int(app.chad_chat_input.cget("height")) == 3


def test_chad_disable_applies_to_send_button_and_shift_newline(chad_app):
    root, app = chad_app
    app.send_chad_chat_message = Mock()
    app.chad_chat_input.insert("1.0", "Entwurf bleibt")
    app.chad_enabled_var.set(False)
    controller.update_chad_controls_state(app)
    root.update()
    assert app.btn_chad_send.instate(["disabled"])
    assert not app.btn_chad_browser.instate(["disabled"])
    app.btn_chad_send.invoke()
    app.chad_chat_input.event_generate("<Shift-Return>")
    root.update()
    app.send_chad_chat_message.assert_not_called()
    assert app.chad_chat_input.get("1.0", "end-1c") == "Entwurf bleibt"
    app.chad_enabled_var.set(True)
    controller.update_chad_controls_state(app)
    assert not app.btn_chad_send.instate(["disabled"])


def test_destroy_cancels_pending_resize(chad_app):
    root, app = chad_app
    errors = []
    root.report_callback_exception = lambda *args: errors.append(args)
    app.chad_chat_input.insert("1.0", "Noch nicht berechnet\n" * 20)
    app.chad_chat_input.event_generate("<<Modified>>")
    app.chad_chat_input.destroy()
    root.update()
    assert not errors


def test_compact_composer_visual_fixture(chad_app):
    root, app = chad_app
    root.geometry("1100x700")
    app.chad_dev_filter_status_var.set("Kompakte Eingabe mit Senden und Shift+Enter")
    controller.append_to_chad_output(
        app, "Chad Antwort", "Stelle deine nächste Rückfrage unten."
    )
    app.chad_chat_input.insert("1.0", "Meine Rückfrage …")
    root.update()
    assert app.btn_chad_send.winfo_ismapped()
    if shutil.which("import"):
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/chad-compact-composer.png",
            ],
            check=True,
            timeout=10,
        )
        assert Path("/work/chad-compact-composer.png").is_file()
