"""The startup tour offer must never block NetMon and can be switched off."""

import os
from types import SimpleNamespace

import pytest

from netmon.app import App


def _bare_app(settings):
    # App.__new__ skips Tk init; set what getattr() would otherwise resolve
    # through Tk's __getattr__ (which recurses without a Tcl interpreter).
    app = App.__new__(App)
    app.settings = settings
    app._quickstart_tour_offer_done = False
    app._netmon_closing = False
    app.guided_tour = None
    return app


def test_offer_is_scheduled_not_shown_synchronously(monkeypatch):
    app = _bare_app({"guided_tour_offer_on_startup": True, "guided_tour_completed": {}})
    calls = []
    monkeypatch.setattr(
        App,
        "_offer_guided_tour_when_visible",
        lambda self, attempts_left=100: calls.append("scheduled"),
    )
    monkeypatch.setattr(
        App,
        "_show_guided_tour_startup_dialog",
        lambda self, on_choice=None: pytest.fail("startup must not open it inline"),
    )
    assert app.maybe_offer_quickstart_tour() is True
    assert calls == ["scheduled"]
    assert app.maybe_offer_quickstart_tour() is False  # only once per start


def test_offer_respects_disabled_setting():
    app = _bare_app({"guided_tour_offer_on_startup": False})
    assert app.maybe_offer_quickstart_tour() is False


def test_offer_waits_until_main_window_is_visible():
    shown, scheduled = [], []
    fake = SimpleNamespace(
        winfo_viewable=lambda: 0,
        after=lambda delay, callback: scheduled.append((delay, callback)),
        _show_guided_tour_startup_dialog=lambda on_choice=None: shown.append(on_choice),
        _on_guided_tour_offer_choice=lambda tour: None,
    )
    fake._offer_guided_tour_when_visible = (
        lambda attempts_left=100: App._offer_guided_tour_when_visible(
            fake, attempts_left
        )
    )
    App._offer_guided_tour_when_visible(fake)
    assert shown == [] and len(scheduled) == 1
    fake.winfo_viewable = lambda: 1
    scheduled[0][1]()
    assert shown == [fake._on_guided_tour_offer_choice]


def _tk_root():
    tk = pytest.importorskip("tkinter")
    if not os.environ.get("DISPLAY", "").strip():
        pytest.skip("Kein DISPLAY für den Tk-Test verfügbar.")
    try:
        return tk, tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk nicht verfügbar: {exc}")


def _buttons(widget, ttk):
    for child in widget.winfo_children():
        if isinstance(child, (ttk.Button, ttk.Checkbutton)):
            yield child
        yield from _buttons(child, ttk)


@pytest.mark.parametrize("dont_ask", [False, True])
def test_dialog_is_non_modal_and_can_disable_the_offer(dont_ask):
    tk, root = _tk_root()
    from tkinter import ttk

    saved = []
    root.settings = {"guided_tour_offer_on_startup": True}
    root.var_guided_tour_offer_on_startup = tk.BooleanVar(value=True)
    root.tr = lambda key, fallback=None: fallback or key
    root.save_settings = lambda log_success=True: saved.append(dict(root.settings))
    root._guided_tour_startup_mode = lambda: "quickstart"
    choices = []
    try:
        result = App._show_guided_tour_startup_dialog(root, on_choice=choices.append)
        assert result == ""  # returned immediately, no wait_window
        assert root.grab_current() is None  # no modal grab
        dialogs = [w for w in root.winfo_children() if isinstance(w, tk.Toplevel)]
        assert len(dialogs) == 1
        widgets = {str(w.cget("text")): w for w in _buttons(dialogs[0], ttk)}
        if dont_ask:
            widgets["Don't offer the tour at startup again"].invoke()
        widgets["Später"].invoke()
        assert choices == [""]
        assert not dialogs[0].winfo_exists()
        assert saved[-1]["guided_tour_offer_on_startup"] is (not dont_ask)
        assert root.var_guided_tour_offer_on_startup.get() is (not dont_ask)
    finally:
        root.destroy()
