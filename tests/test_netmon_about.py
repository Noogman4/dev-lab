"""About contact tests; no real mail client, update request or App startup."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import tkinter as tk
from tkinter import ttk

import pytest

from netmon import app as app_module
from netmon.app import App, DARK_THEME, LIGHT_THEME
from netmon.config.constants import NETMON_APP_VERSION, NETMON_SUPPORT_EMAIL
from netmon.services.lang_service import LangService

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def about_app(monkeypatch):
    app = App.__new__(App)
    try:
        tk.Tk.__init__(app)
    except tk.TclError as exc:
        pytest.skip(f"Tk display required (run with xvfb-run): {exc}")
    app.geometry("200x100+0+0")
    app.style = ttk.Style(app)
    app._get_about_program_system_info = lambda: {
        "netmon": NETMON_APP_VERSION,
        "distribution": "Synthetic Linux",
        "kernel": "test",
        "python": "3.12",
    }
    app._get_available_program_documentation_path = lambda: ""
    app.check_about_latest_version = Mock()
    app.log_safe = Mock()
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/xdg-open")
    monkeypatch.setattr(app_module.subprocess, "Popen", Mock())
    try:
        yield app
    finally:
        app.destroy()


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


@pytest.mark.parametrize("language", ["de", "en"])
@pytest.mark.parametrize("theme", [LIGHT_THEME, DARK_THEME], ids=["light", "dark"])
def test_about_support_is_visible_clickable_and_theme_aware(about_app, language, theme):
    app = about_app
    app.lang = LangService(str(ROOT / "netmon" / "lang")).load(language)
    app._apply_ttk_theme(theme)
    app.open_about_program_dialog()
    win = app.about_program_window
    app.update()
    widgets = list(descendants(win))
    contacts = [
        widget
        for widget in widgets
        if "text" in widget.keys() and NETMON_SUPPORT_EMAIL in widget.cget("text")
    ]
    assert len(contacts) == 1
    contact = contacts[0]
    assert isinstance(contact, ttk.Button)
    assert contact.cget("text") == f"Support: {NETMON_SUPPORT_EMAIL}"
    assert win.title() == app.lang["about_title"]
    assert contact.winfo_viewable()
    # Outside the scrolling body: visible immediately and at minimum size.
    assert contact.master.master is win
    win.geometry("560x420")
    app.update()
    assert contact.winfo_rooty() >= win.winfo_rooty()
    assert contact.winfo_rooty() + contact.winfo_height() <= (
        win.winfo_rooty() + win.winfo_height()
    )
    assert contact.winfo_rootx() + contact.winfo_width() <= (
        win.winfo_rootx() + win.winfo_width()
    )
    style = contact.cget("style") or "TButton"
    assert app.style.lookup(style, "foreground") == theme["fg"]
    assert app.style.lookup(style, "background") == theme["tab_bg"]
    other_theme = DARK_THEME if theme is LIGHT_THEME else LIGHT_THEME
    app._apply_ttk_theme(other_theme)
    assert app.style.lookup(style, "foreground") == other_theme["fg"]
    assert app.style.lookup(style, "background") == other_theme["tab_bg"]
    contact.invoke()
    app_module.subprocess.Popen.assert_called_once_with(
        ["xdg-open", f"mailto:{NETMON_SUPPORT_EMAIL}"],
        stdout=app_module.subprocess.DEVNULL,
        stderr=app_module.subprocess.DEVNULL,
    )
    app.open_about_program_dialog()
    assert app.about_program_window is win
    app.check_about_latest_version.assert_called_once_with(auto_open=True, manual=False)
    sections = {
        widget.cget("text") for widget in widgets if isinstance(widget, ttk.LabelFrame)
    }
    assert app.lang["about_section_docs"] in sections
    assert app.lang["about_section_credits"] in sections
    assert app.lang["about_section_license"] in sections


def test_support_address_matches_published_contact():
    assert NETMON_SUPPORT_EMAIL == "support@netmonroots.com"
    for path in ("README.md", "site/impressum.html", "site/en/impressum.html"):
        assert f"mailto:{NETMON_SUPPORT_EMAIL}" in (ROOT / path).read_text("utf-8")


@pytest.mark.parametrize("language", ["de", "en"])
def test_about_fallback_includes_support_contact(monkeypatch, language):
    app = App.__new__(App)
    app.lang = LangService(str(ROOT / "netmon" / "lang")).load(language)
    showinfo = Mock()
    monkeypatch.setattr(app_module, "tk", None)
    monkeypatch.setattr(app_module.messagebox, "showinfo", showinfo)
    app.open_about_program_dialog()
    title, text = showinfo.call_args.args
    assert title == app.lang["about_title"]
    assert f"Support: {NETMON_SUPPORT_EMAIL}" in text
    assert NETMON_APP_VERSION in text


@pytest.mark.parametrize("failure", ["missing_opener", "launch_failure"])
def test_support_mail_handler_failure_is_controlled(monkeypatch, failure):
    app = SimpleNamespace(log_safe=Mock())
    opener = Mock(side_effect=OSError("synthetic failure"))
    monkeypatch.setattr(app_module.subprocess, "Popen", opener)
    monkeypatch.setattr(
        app_module.shutil,
        "which",
        lambda name: None if failure == "missing_opener" else "/usr/bin/xdg-open",
    )
    assert App.open_netmon_support_email(app) is False
    app.log_safe.assert_called_once()
    assert opener.call_count == (0 if failure == "missing_opener" else 1)


@pytest.mark.parametrize("language", ["de", "en"])
@pytest.mark.parametrize("theme", [LIGHT_THEME, DARK_THEME], ids=["light", "dark"])
def test_about_text_wraps_to_available_width_on_resize(about_app, language, theme):
    app = about_app
    app.lang = LangService(str(ROOT / "netmon" / "lang")).load(language)
    app._apply_ttk_theme(theme)
    app.open_about_program_dialog()
    win = app.about_program_window
    previous = None
    for width in (560, 900, 560):
        win.geometry(f"{width}x420")
        app.update()
        labels = [
            widget
            for widget in descendants(win)
            if isinstance(widget, (ttk.Label, tk.Label))
            and float(widget.cget("wraplength") or 0) > 0
        ]
        assert len(labels) >= 20
        for label in labels:
            assert float(label.cget("wraplength")) <= label.winfo_width()
            assert label.winfo_reqwidth() <= label.winfo_width()
        current = float(labels[0].cget("wraplength"))
        if previous is not None:
            assert (current > previous) is (width == 900)
        previous = current
