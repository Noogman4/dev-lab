"""Setup/removal of the protected radio output via explicit UI action only."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon.core import radio_fifo_output as fifo
from netmon.features import radio_controller as radio

ROOT = Path(__file__).resolve().parents[1]


class Dialogs:
    def __init__(self, answer=True, restart=False):
        self.answer = answer
        self.restart = restart
        self.calls = []

    def askyesno(self, title, text, parent=None):
        self.calls.append(("ask", text))
        if "neu starten?" in text:
            return self.restart
        return self.answer

    def showinfo(self, title, text, parent=None):
        self.calls.append(("info", text))

    def showerror(self, title, text, parent=None):
        self.calls.append(("error", text))


@pytest.fixture
def env(monkeypatch, tmp_path):
    p = fifo.paths(home=tmp_path / "home", config_home=tmp_path / "config")
    monkeypatch.setattr(fifo, "paths", lambda: p)
    monkeypatch.setattr(fifo, "SYSTEM_CONFIGS", ())
    monkeypatch.setattr(
        fifo,
        "socket_access_configured",
        lambda paths, roots=(): [],
    )
    refreshed = []
    monkeypatch.setattr(
        radio, "update_radio_dependency_state", lambda app: refreshed.append(app)
    )
    events = []
    monkeypatch.setattr(
        radio,
        "stop_radio_playback",
        lambda app, async_mode=True: events.append(("stop", async_mode)),
    )
    monkeypatch.setattr(
        fifo, "restart_audio_services", lambda run=None: events.append("restart")
    )
    monkeypatch.setattr(
        fifo, "wait_for_fifo", lambda paths: events.append("wait") or True
    )
    monkeypatch.setattr(radio, "_schedule_ui", lambda app, callback: callback())
    app = SimpleNamespace(events=events)
    return p, refreshed, app


def test_setup_requires_confirmation_and_creates_only_own_files(env):
    p, refreshed, app = env
    declined = Dialogs(answer=False)
    assert radio.manage_protected_radio_output(app, declined) is False
    assert not p.dropin.exists() and not p.state_dir.exists()
    assert str(p.dropin) in declined.calls[0][1]
    assert str(p.state_dir) in declined.calls[0][1]

    accepted = Dialogs(answer=True)
    assert radio.manage_protected_radio_output(app, accepted, spawn=sync) is True
    assert p.dropin.read_text() == fifo.dropin_text(p.fifo)
    # Restart declined: nothing restarted, user told when it takes effect.
    assert [c[0] for c in accepted.calls] == ["ask", "ask", "info"]
    assert "Neustart der Audiodienste" in accepted.calls[2][1]
    assert app.events == []
    assert refreshed == [app]  # declining changes nothing, so no refresh


def sync(target):
    target()


def test_confirmed_restart_stops_radio_first_then_restarts_off_ui(env):
    p, _refreshed, app = env
    dialogs = Dialogs(answer=True, restart=True)
    spawned = []
    radio.manage_protected_radio_output(app, dialogs, spawn=spawned.append)
    assert app.events == []  # nothing runs on the calling (Tk) thread
    spawned[0]()
    assert app.events == [("stop", False), "restart", "wait"]
    assert dialogs.calls[-1][0] == "info" and "bereit" in dialogs.calls[-1][1]


def test_failed_restart_is_reported(env, monkeypatch):
    p, _refreshed, app = env

    def broken(run=None):
        raise fifo.RadioOutputError("Audiodienste konnten nicht neu gestartet werden.")

    monkeypatch.setattr(fifo, "restart_audio_services", broken)
    dialogs = Dialogs(answer=True, restart=True)
    radio.manage_protected_radio_output(app, dialogs, spawn=sync)
    assert dialogs.calls[-1][0] == "error"
    assert "neu gestartet" in dialogs.calls[-1][1]


def test_restart_without_loaded_output_is_reported(env, monkeypatch):
    p, _refreshed, app = env
    monkeypatch.setattr(fifo, "wait_for_fifo", lambda paths: False)
    dialogs = Dialogs(answer=True, restart=True)
    radio.manage_protected_radio_output(app, dialogs, spawn=sync)
    assert dialogs.calls[-1][0] == "error"
    assert "nicht geladen" in dialogs.calls[-1][1]


def test_second_click_offers_removal_and_removes_own_files(env):
    p, _refreshed, app = env
    radio.manage_protected_radio_output(app, Dialogs())
    keep = Dialogs(answer=False)
    assert radio.manage_protected_radio_output(app, keep) is False
    assert p.dropin.exists() and "entfernen" in keep.calls[0][1]
    remove = Dialogs(restart=True)
    assert radio.manage_protected_radio_output(app, remove, spawn=sync) is True
    assert not p.dropin.exists() and not p.state_dir.exists()
    assert app.events[-2:] == [("stop", False), "restart"]  # no FIFO wait on removal
    assert "Entfernt" in remove.calls[-1][1]


def test_socket_access_blocks_setup_without_asking(env, monkeypatch):
    p, _refreshed, app = env
    monkeypatch.setattr(
        fifo, "socket_access_configured", lambda paths, roots=(): ["/etc/x.conf"]
    )
    dialogs = Dialogs()
    assert radio.manage_protected_radio_output(app, dialogs) is False
    assert [c[0] for c in dialogs.calls] == ["error"]
    assert "/etc/x.conf" in dialogs.calls[0][1]
    assert not p.dropin.exists()


def test_foreign_dropin_is_neither_overwritten_nor_removed(env):
    p, _refreshed, app = env
    p.config_dir.mkdir(parents=True)
    p.dropin.write_text("context.modules = []\n")
    dialogs = Dialogs()
    assert radio.manage_protected_radio_output(app, dialogs) is False
    assert dialogs.calls[-1][0] == "error"
    assert p.dropin.read_text() == "context.modules = []\n"


def test_setup_button_sits_in_player_section_below_detach():
    source = (ROOT / "netmon/netmon_radio_app.py").read_text()
    button = source.index("self.radio_output_setup_button = ttk.Button(")
    block = source[button : source.index("self.radio_database_count_label", button)]
    assert "details_frame," in block and "status_row" not in block
    assert "textvariable=self.radio_output_button_var" in block
    assert "command=self.manage_protected_radio_output" in block
    assert "row=2," in block and "column=2," in block
    assert "radio_controller.manage_protected_radio_output(self)" in source


class Var:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


@pytest.mark.parametrize("ready", [True, False])
def test_button_shows_state_and_status_row_stays_short(monkeypatch, ready):
    monkeypatch.setattr(radio, "_radio_output_ready", lambda app: ready)
    app = SimpleNamespace(radio_output_button_var=Var())
    hint = radio._radio_output_hint(app)
    if ready:
        assert hint == "" and app.radio_output_button_var.value == "✓ Ton geschützt"
    else:
        assert app.radio_output_button_var.value == "Ton einrichten…"
        assert hint == "Geschützte Tonausgabe fehlt – oben einrichten."


def test_hint_without_button_variable_does_not_fail(monkeypatch):
    monkeypatch.setattr(radio, "_radio_output_ready", lambda app: False)
    assert "fehlt" in radio._radio_output_hint(SimpleNamespace())


def test_new_texts_exist_in_german_and_english():
    keys = [
        "radio_output_button_ready",
        "radio_output_button_setup",
        "radio_output_missing_short",
        "radio_output_setup_title",
        "radio_output_setup_prompt",
        "radio_output_setup_done",
        "radio_output_remove_prompt",
        "radio_output_remove_done",
        "radio_output_socket_access",
        "radio_output_setup_failed",
        "radio_output_restart_prompt",
        "radio_output_restart_later",
        "radio_output_restart_not_loaded",
        "radio_output_not_ready",
        "radio_status_output_lost",
    ]
    for lang in ("de", "en"):
        data = json.loads((ROOT / f"netmon/lang/{lang}.json").read_text())
        assert all(data.get(k) for k in keys), lang
