"""ICY title publication must still belong to the current playback.

Transport/parser limits are exercised against radio_fetch and radio_sandbox in
test_radio_metadata_boundary and test_radio_fetch.
"""

from types import SimpleNamespace

import pytest

from netmon.features import radio_controller as radio


def test_old_playback_title_is_not_scheduled(monkeypatch):
    proc = object()
    app = SimpleNamespace(radio_proc=proc)

    def read(app, proc):
        app.radio_proc = object()
        return "old title", {}

    monkeypatch.setattr(radio, "_read_radio_stream_title", read)
    monkeypatch.setattr(radio, "_schedule_ui", lambda *args: pytest.fail("stale title"))
    radio._poll_radio_metadata(app, proc)


def test_queued_title_checks_playback_again(monkeypatch):
    proc = object()
    app = SimpleNamespace(radio_proc=proc)
    queued = []
    monkeypatch.setattr(radio, "_read_radio_stream_title", lambda *args: ("old", {}))
    monkeypatch.setattr(radio, "_schedule_ui", lambda app, cb: queued.append(cb))
    monkeypatch.setattr(radio.time, "sleep", lambda _: setattr(app, "radio_proc", None))
    monkeypatch.setattr(
        radio, "_set_radio_title_text", lambda *args: pytest.fail("stale title")
    )
    radio._poll_radio_metadata(app, proc)
    queued[0]()
