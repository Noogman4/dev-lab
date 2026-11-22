"""Real Tk flows plus virtual-clock reminders; no user state or real commands."""

from dataclasses import replace
import os
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from netmon.features import linux_help_controller as reader
from netmon.features import linux_help_quiz_controller as controller
from netmon.services.lang_service import LangService
from netmon.services import linux_help_quiz_service as quiz
from netmon.ui.tabs.linux_help_tab import build_linux_help_tab
from tests.test_linux_help_unified_markdown import app as app
from tests.test_linux_help_quiz import entry


@pytest.fixture
def quiz_app(app, tmp_path):
    bank = quiz.load_questions()
    app.linux_help_data = [
        reader.normalize_linux_help_entry(app, entry(q))
        for q in bank
        if q.kind == "command"
    ]
    app.linux_help_glossary = [
        reader.normalize_linux_help_glossary_entry(app, entry(q))
        for q in bank
        if q.kind == "glossary"
    ]
    reader.rebuild_linux_help_indexes(app)
    reader.rebuild_linux_help_glossary_indexes(app)
    app.linux_help_quiz_state = quiz.QuizState(tmp_path / "quiz-state/quiz.json")
    app.callback_errors = []
    app.report_callback_exception = lambda *args: app.callback_errors.append(args)
    yield app
    assert app.callback_errors == []


def one_question(app, *, kind="Befehle und Glossar"):
    window = controller.open_linux_help_quiz(app)
    window.kind.set(kind)
    window.count.set("1")
    assert window.start()
    app.update()
    return window, window.questions[0][0]


def test_english_quiz_keeps_stable_selection_ids(quiz_app):
    app = quiz_app
    catalogs = Path(__file__).resolve().parents[1] / "netmon" / "lang"
    english = LangService(str(catalogs)).load("en")
    app.tr = english.get

    window, question = one_question(app, kind="Glossary")
    assert window.title() == "Linux learning quiz"
    assert window.category.get() == "All categories"
    assert question.kind == "glossary"
    window.choice.set(question.answer)
    assert window.answer()
    assert window.feedback_label.cget("text").startswith("Correct!\nCorrect answer:")

    window.auto_kind.set("Glossary")
    assert window.save_settings()
    assert app.linux_help_quiz_state.data["settings"]["kind"] == "glossary"


def test_button_and_reopening_use_single_nonmodal_quiz_window(quiz_app):
    app = quiz_app
    app.linux_help_tree.destroy()
    app.tools_nb = ttk.Notebook(app)
    app.tools_nb.pack(fill="both", expand=True)
    for name in (
        "refresh_linux_help_list",
        "clear_linux_help_filters",
        "reload_linux_help_data",
        "linux_help_new_entry",
        "linux_help_edit_selected",
        "linux_help_delete_selected",
        "on_linux_help_select",
        "show_linux_help_tree_menu",
    ):
        setattr(app, name, lambda *_a, **_kw: None)
    build_linux_help_tab(app)
    app.btn_linux_help_quiz.invoke()
    window = app.linux_help_quiz_window
    window.kind.set("Glossar")
    app.btn_linux_help_quiz.invoke()
    assert app.linux_help_quiz_window is window and window.kind.get() == "Glossar"
    assert app.grab_current() is None
    assert app.btn_linux_help_quiz.grid_info()["row"] == 1
    window.close()
    app.btn_linux_help_quiz.invoke()
    assert app.linux_help_quiz_window is not window
    assert app.linux_help_quiz_scheduler.handle is None


def test_correct_answer_round_summary_and_restart(quiz_app):
    window, q = one_question(quiz_app)
    assert not window.answer()
    assert "auswählen" in window.status.get()
    window.choice.set(q.answer)
    assert window.answer()
    assert "Richtig!" in window.feedback_label.cget("text")
    assert q.explanation in window.feedback_label.cget("text")
    assert not window.answer()  # double-click cannot increase counters
    assert window.state.statistics()["total"] == [1, 1]
    window.next_question()
    assert window.round_id is None
    assert "abgeschlossen" in window.round_status.get()
    assert window.tabs.select() == str(window.stats_tab)
    text = window.stats_text.get("1.0", "end")
    assert "100 %" in text and "Verschiedene geübte Einträge: 1" in text
    assert window.close()
    reopened = controller.open_linux_help_quiz(quiz_app)
    assert reopened.state.statistics()["total"] == [1, 1]


def test_wrong_and_unknown_answers_are_repeated_and_removed_after_correct_answer(
    quiz_app,
):
    window, q = one_question(quiz_app)
    assert window.answer(unknown=True)
    window.next_question()
    window.category.set("Alle Kategorien")
    assert window.start(errors_only=True)
    assert window.questions[0][0] == q
    window.choice.set((q.answer + 1) % 4)
    assert window.answer()
    assert "Leider falsch" in window.feedback_label.cget("text")
    window.next_question()
    assert window.start(errors_only=True)
    window.choice.set(q.answer)
    assert window.answer()
    window.next_question()
    assert not window.start(errors_only=True)
    assert window.state.statistics()["total"] == [3, 1]


def test_read_filter_and_reader_do_not_pretend_learning_success(quiz_app):
    window = controller.open_linux_help_quiz(quiz_app)
    window.read_only.set(True)
    assert not window.start()
    target = quiz.load_questions()[0]
    item = reader.get_linux_help_command_by_id(quiz_app, target.entry_id)
    quiz_app.linux_help_reading_state.change(item, read=True)
    assert window.start() and len(window.questions) == 1
    assert window.questions[0][0].id == target.id
    window.open_reader()
    opened = quiz_app.linux_help_reader_window
    assert opened.entry["id"] == target.entry_id
    assert window.state.statistics()["total"] == [0, 0]
    assert quiz_app.grab_current() is None
    window.answer(unknown=True)
    assert quiz_app.linux_help_reading_state.get(item)["read"]


@pytest.mark.parametrize(
    "finish,confirm", [(False, False), (False, True), (True, False)]
)
def test_closing_round_keeps_completed_answers(quiz_app, monkeypatch, finish, confirm):
    window, q = one_question(quiz_app)
    confirmations = []
    from netmon.ui import linux_help_quiz as ui

    monkeypatch.setattr(
        ui.messagebox,
        "askyesno",
        lambda *_a, **_kw: confirmations.append(True) or confirm,
    )
    if finish:
        window.choice.set(q.answer)
        assert window.answer()
    assert window.close() == (confirm or finish)
    assert len(confirmations) == (0 if finish else 1)
    assert window.state.statistics()["total"] == ([1, 1] if finish else [0, 0])


def test_document_changed_during_round_is_not_counted(quiz_app, monkeypatch):
    window, q = one_question(quiz_app)
    original = reader.load_entry_document
    monkeypatch.setattr(
        reader,
        "load_entry_document",
        lambda item: replace(original(item), source="changed"),
    )
    window.choice.set(q.answer)
    assert not window.answer()
    assert "verändert" in window.status.get()
    assert window.state.statistics()["total"] == [0, 0]
    window.refresh_bank()
    window.refresh_stats()
    assert "Ausgesetzte Fragen" in window.stats_text.get("1.0", "end")


def test_save_error_allows_retry_without_duplicate_answer(quiz_app, monkeypatch):
    window, q = one_question(quiz_app)
    window.choice.set(q.answer)
    original = quiz.write_private_json

    def fail(*_args):
        raise OSError("synthetic full disk")

    monkeypatch.setattr(quiz, "write_private_json", fail)
    assert not window.answer() and not window.answered
    assert "nicht gespeichert" in window.status.get()
    monkeypatch.setattr(quiz, "write_private_json", original)
    assert window.answer()
    assert window.state.statistics()["total"] == [1, 1]


def test_corrupt_storage_is_visible_and_does_not_start_round(quiz_app):
    window = controller.open_linux_help_quiz(quiz_app)
    path = window.state.path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("invalid")
    assert not window.start()
    assert "nicht gelesen" in window.status.get()
    assert path.read_text() == "invalid"


def test_settings_opt_in_validation_snooze_and_new_start_interval(quiz_app):
    app = quiz_app
    controller.initialize_linux_help_quiz(app)
    scheduler = app.linux_help_quiz_scheduler
    clock = [100]
    scheduler.now = lambda: clock[0]
    assert scheduler.handle is None
    window = controller.open_linux_help_quiz(app)
    assert not window.auto_enabled.get()
    window.auto_enabled.set(True)
    window.auto_minutes.set("0")
    assert not window.save_settings() and scheduler.handle is None
    window.auto_minutes.set("7")
    window.auto_count.set("3")
    window.auto_kind.set("Glossar")
    assert window.save_settings()
    assert scheduler.due == 520
    window.snooze()
    assert not window.winfo_exists() and scheduler.due == 700
    scheduler.reset()
    assert scheduler.due == 520  # regular interval, never a stored deadline
    window = controller.open_linux_help_quiz(app, automatic=True)
    assert window.count.get() == "3" and window.kind.get() == "Glossar"
    assert window.round_id is not None
    assert len(window.questions) == 3
    assert all(q.kind == "glossary" for q, _item in window.questions)
    window.auto_enabled.set(False)
    assert window.save_settings() and scheduler.handle is None
    assert str(window.snooze_button.cget("state")) == "disabled"


class FakeRoot:
    def __init__(self):
        self.callbacks = {}
        self.sequence = 0

    def bind(self, *_args, **_kwargs):
        pass

    def after(self, delay, callback):
        self.sequence += 1
        self.callbacks[self.sequence] = (delay, callback)
        return self.sequence

    def after_cancel(self, handle):
        self.callbacks.pop(handle, None)

    def run(self, scheduler):
        self.callbacks.pop(scheduler.handle)[1]()


def test_scheduler_defers_dialogs_existing_window_and_only_opens_once(
    tmp_path, monkeypatch
):
    state = quiz.QuizState(tmp_path / "quiz.json")
    state.save_settings({**quiz.DEFAULT_SETTINGS, "enabled": True})
    app = SimpleNamespace(linux_help_quiz_state=state)
    root, clock, blocked, opened = FakeRoot(), [0], [False], []
    scheduler = controller.QuizScheduler(app, root, now=lambda: clock[0])
    monkeypatch.setattr(controller, "_visible_dialog", lambda _root: blocked[0])

    def open_quiz(_app, **kwargs):
        opened.append(kwargs)
        app.linux_help_quiz_window = SimpleNamespace(winfo_exists=lambda: True)

    monkeypatch.setattr(controller, "open_linux_help_quiz", open_quiz)
    assert scheduler.due == 3600 and len(root.callbacks) == 1
    clock[0] = 3600
    blocked[0] = True
    root.run(scheduler)
    assert opened == [] and list(root.callbacks.values())[0][0] == 30000
    blocked[0] = False
    app.linux_help_quiz_window = SimpleNamespace(winfo_exists=lambda: True)
    root.run(scheduler)
    assert opened == []
    app.linux_help_quiz_window = None
    root.run(scheduler)
    assert opened == [{"automatic": True}]
    assert not root.callbacks
    scheduler.reset(minutes=10)
    assert scheduler.due == 4200
    root.run(scheduler)
    assert len(opened) == 1
    state.save_settings(quiz.DEFAULT_SETTINGS)
    root.run(scheduler)
    assert scheduler.handle is None and scheduler.due is None
    scheduler._destroyed(SimpleNamespace(widget=root))
    assert scheduler.closed


def test_real_tk_modal_and_nonmodal_dialog_detection(quiz_app):
    app = quiz_app
    app.update()
    assert not controller._visible_dialog(app)
    dialog = tk.Toplevel(app)
    app.update()
    assert controller._visible_dialog(app)
    dialog.grab_set()
    assert controller._visible_dialog(app)
    dialog.grab_release()
    dialog.destroy()
    assert not controller._visible_dialog(app)


def test_full_command_round_can_be_answered_at_minimum_size_without_processes(
    quiz_app, monkeypatch
):
    import subprocess

    window = controller.open_linux_help_quiz(quiz_app)
    window.geometry("680x740")
    window.kind.set("Befehle")
    window.count.set("30")
    assert window.start()
    assert len(window.questions) == 30
    assert all(q.kind == "command" for q, _item in window.questions)
    monkeypatch.setattr(
        subprocess, "Popen", lambda *_a, **_kw: pytest.fail("Quiz started a process")
    )
    for index, (question, _item) in enumerate(window.questions):
        quiz_app.update()
        assert window.index == index
        assert window.question_canvas.yview()[0] == 0
        window.choice.set(question.answer)
        assert window.answer()
        quiz_app.update()
        assert window.question_canvas.yview()[1] >= 0.99
        window.next_question()
    assert window.state.statistics()["total"] == [30, 30]
    assert window.state.statistics()["distinct"] == 30
    assert window.round_id is None


@pytest.mark.skipif(
    os.environ.get("NETMON_TEST_ISOLATED") != "1",
    reason="Requires private isolated desktop",
)
def test_full_app_builds_quiz_with_actual_catalog_and_smoke_startup_patches(
    monkeypatch,
):
    import subprocess

    from netmon.app import App
    from netmon.main import (
        _temporary_app_smoke_patches,
        _cancel_pending_after_callbacks,
    )

    errors = []
    # Startup queries are synthetic; this test exercises the real widget builders.
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **_kw: subprocess.CompletedProcess(args, 1, stdout="", stderr=""),
    )
    monkeypatch.setattr(App, "security_build_baseline", lambda *_a: None)
    monkeypatch.setattr(
        App, "report_callback_exception", lambda *_args: errors.append(_args)
    )
    with _temporary_app_smoke_patches(App):
        app = App(start_theme="light")
        try:
            app.update_idletasks()
            app.update()
            app.btn_linux_help_quiz.invoke()
            window = app.linux_help_quiz_window
            assert len(window.pool) == 225 and window.suspended == []
            for label, kind, category in (
                ("Befehle", "command", "Bash Builtins"),
                ("Glossar", "glossary", "Python"),
            ):
                window.kind.set(label)
                assert category in window.category_combo.cget("values")
                window.category_combo.set(category)
                window.count.set("1")
                assert window.start()
                q = window.questions[0][0]
                assert q.kind == kind and q.category == category
                window.choice.set(q.answer)
                assert window.answer()
                window.reader_button.invoke()
                assert app.linux_help_reader_window.winfo_exists()
                app.linux_help_reader_window.destroy()
                window.next_question()
            assert window.state.statistics()["total"][0] >= 2
            assert window.close()
            assert errors == []
        finally:
            _cancel_pending_after_callbacks(app)
            app.destroy()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_theme_and_narrow_window_all_controls_visible(quiz_app, theme):
    from netmon.app import App, LIGHT_THEME, DARK_THEME

    app = quiz_app
    palette = DARK_THEME if theme == "dark" else LIGHT_THEME
    app.style = ttk.Style(app)
    app._app_theme = palette
    app._ensure_colorable_ttk_theme = lambda: App._ensure_colorable_ttk_theme(app)
    app._apply_tk_widget_theme = lambda widget, colors: App._apply_tk_widget_theme(
        app, widget, colors
    )
    App._apply_ttk_theme(app, palette)
    window = controller.open_linux_help_quiz(app)
    window.count.set("25")
    assert window.start()
    for width, height in ((780, 820), (680, 740)):
        window.geometry(f"{width}x{height}")
        app.update()
        q = window.questions[window.index][0]
        window.choice.set(q.answer)
        if not window.answered:
            assert window.answer()
        app.update()
        for widget in (
            window.answer_button,
            window.unknown_button,
            window.next_button,
            window.reader_button,
            window.snooze_button,
        ):
            assert (
                widget.winfo_rooty() + widget.winfo_height()
                <= window.winfo_rooty() + window.winfo_height()
            )
            assert (
                widget.winfo_rootx() + widget.winfo_width()
                <= window.winfo_rootx() + window.winfo_width()
            )
        assert window.option_buttons[0].cget("background") == palette["tab_bg"]
        if os.environ.get("NETMON_TEST_ISOLATED") == "1":
            from PIL import ImageGrab

            x, y = window.winfo_rootx(), window.winfo_rooty()
            ImageGrab.grab(
                bbox=(x, y, x + window.winfo_width(), y + window.winfo_height()),
                xdisplay=os.environ["DISPLAY"],
            ).save(f"/work/quiz-{theme}-{width}.png")
    for tab, name in (
        (window.stats_tab, "statistics"),
        (window.settings_tab, "settings"),
    ):
        window.tabs.select(tab)
        app.update()
        if os.environ.get("NETMON_TEST_ISOLATED") == "1":
            x, y = window.winfo_rootx(), window.winfo_rooty()
            ImageGrab.grab(
                bbox=(x, y, x + window.winfo_width(), y + window.winfo_height()),
                xdisplay=os.environ["DISPLAY"],
            ).save(f"/work/quiz-{theme}-{name}.png")
