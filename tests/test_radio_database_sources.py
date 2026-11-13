"""Source-picker/importer agreement, including the default UI selection."""

import json
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from netmon import netmon_radio_app as ui
from netmon.features import radio_controller as radio


class Flag:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


@pytest.mark.parametrize("website_id", ["shoutcast_api", "fmstream"])
def test_website_click_opens_only_the_fixed_url(monkeypatch, website_id):
    calls = []
    monkeypatch.setattr(
        ui.subprocess, "Popen", lambda argv, **options: calls.append((argv, options))
    )
    assert ui.NetMonRadioApp.open_radio_database_website(SimpleNamespace(), website_id)
    assert len(calls) == 1
    assert calls[0][0] == [
        "/usr/bin/xdg-open",
        ui.RADIO_DATABASE_WEBSITES[website_id][1],
    ]
    assert calls[0][1]["stdin"] == ui.subprocess.DEVNULL
    assert calls[0][1]["start_new_session"] is True


@pytest.mark.parametrize(
    "website_id",
    [
        "unknown",
        "https://evil.example",
        "http://127.0.0.1/",
        "fmstream\n",
        None,
        {},
        [],
    ],
)
def test_website_action_cannot_open_arbitrary_metadata(monkeypatch, website_id):
    monkeypatch.setattr(
        ui.subprocess, "Popen", lambda *_a, **_k: pytest.fail("Unregistered URL opened")
    )
    assert not ui.NetMonRadioApp.open_radio_database_website(
        SimpleNamespace(), website_id
    )


@pytest.mark.parametrize("gio_available", [True, False])
def test_website_launcher_fallback_and_failure_feedback(monkeypatch, gio_available):
    calls, messages = [], []

    def launch(argv, **_options):
        calls.append(argv)
        if len(calls) == 1 or not gio_available:
            raise FileNotFoundError("launcher missing")

    monkeypatch.setattr(ui.subprocess, "Popen", launch)
    monkeypatch.setattr(
        ui.messagebox,
        "showerror",
        lambda *args, **kwargs: messages.append((args, kwargs)),
    )
    app = SimpleNamespace(tr=lambda _key, fallback: fallback)
    assert (
        ui.NetMonRadioApp.open_radio_database_website(app, "fmstream") is gio_available
    )
    assert calls == [
        ["/usr/bin/xdg-open", "https://fmstream.org/index.php"],
        ["/usr/bin/gio", "open", "https://fmstream.org/index.php"],
    ]
    assert len(messages) == (0 if gio_available else 1)
    if messages:
        assert "https://fmstream.org/index.php" in messages[0][0][1]


def test_website_buttons_are_click_only_and_separate_from_import_selection():
    root = tk.Tk()
    root.withdraw()
    try:
        opened = []
        app = SimpleNamespace(
            tr=lambda _key, fallback: fallback,
            open_radio_database_website=opened.append,
            radio_database_source_vars={"radio_browser_api": Flag(True)},
        )
        frame = ui.NetMonRadioApp._add_radio_database_website_links(app, root)
        widgets = frame.winfo_children()
        buttons = [widget for widget in widgets if isinstance(widget, ttk.Button)]
        assert len(buttons) == 2
        assert not any(isinstance(widget, ttk.Checkbutton) for widget in widgets)
        assert opened == []
        assert not set(ui.RADIO_DATABASE_WEBSITES).intersection(IMPORTABLE)
        for (website_id, (label, url)), button in zip(
            ui.RADIO_DATABASE_WEBSITES.items(), buttons
        ):
            assert label in button.cget("text")
            assert any(
                isinstance(widget, ttk.Label) and widget.cget("text") == url
                for widget in widgets
            )
            button.invoke()
            assert opened[-1] == website_id
        assert radio._radio_database_source_ids_for_download(app) == [
            "radio_browser_api"
        ]
    finally:
        root.destroy()


IMPORTABLE = {
    **radio.RADIO_BROWSER_SOURCE_ENDPOINTS,
    **radio.ICECAST_SOURCE_ENDPOINTS,
    **radio.RADIO_M3U_SOURCE_ENDPOINTS,
    **radio.RADIO_VERIFIED_SOURCE_ENDPOINTS,
}
UNSUPPORTED = [
    "radio_browser_country",
    "radio_browser_tag",
    "shoutcast_api",
    "icecast_directory",
    "icecast_json",
    "fmstream",
    "streamurl_link",
    "airable",
    "community_radio_api",
    "radio_api",
]


@pytest.mark.parametrize("source_id", IMPORTABLE)
def test_every_supported_source_uses_its_bounded_sandbox_importer(
    monkeypatch, source_id
):
    calls = []

    def fetch(url, **options):
        calls.append((url, options))
        return [{"name": "Example Radio", "url": "https://example.com/live"}]

    monkeypatch.setattr(radio.radio_sandbox, "fetch_catalog", fetch)
    assert radio._download_radio_source_payload(source_id)[0]["name"] == "Example Radio"
    endpoint = IMPORTABLE[source_id]
    expected = (
        {"kind": "verified"}
        if source_id == "verified_radio_streams"
        else (
            {"kind": "iprd"}
            if source_id == "iprd_all"
            else (
                {"kind": "m3u"}
                if source_id in radio.RADIO_M3U_SOURCE_ENDPOINTS
                else (
                    {"kind": "xml"}
                    if source_id in radio.ICECAST_SOURCE_ENDPOINTS
                    else {"post": endpoint.endswith(("/stations", "/search"))}
                )
            )
        )
    )
    assert calls == [(endpoint, expected)]


@pytest.mark.parametrize("source_id", UNSUPPORTED + ["unknown-source"])
def test_old_unsupported_selection_cannot_reach_download(monkeypatch, source_id):
    app = SimpleNamespace(
        radio_database_source_vars={source_id: Flag(True), "icecast_json": Flag(False)}
    )
    assert radio._radio_database_source_ids_for_download(app) == []
    monkeypatch.setattr(
        radio.radio_sandbox,
        "fetch_catalog",
        lambda *_a, **_k: pytest.fail("Unsupported source contacted"),
    )
    with pytest.raises(ValueError, match="nicht unterstützt"):
        radio._download_radio_source_payload(source_id)


def test_source_rows_show_only_active_sources_and_select_all_uses_them():
    root = tk.Tk()
    root.withdraw()
    try:
        frame = ttk.Frame(root)
        app = SimpleNamespace(
            radio_database_source_vars={},
            radio_database_source_status_labels={},
            radio_database_select_all_var=tk.BooleanVar(master=root, value=True),
            radio_database_exclusive_mode_var=tk.BooleanVar(master=root, value=True),
            _radio_database_indicator_image=lambda: None,
            _radio_database_source_label=lambda _source, label: label,
            on_radio_database_source_toggle=lambda _source: None,
            tr=lambda _key, fallback: fallback,
        )
        for name in (
            "_radio_database_attr",
            "_radio_database_source_vars",
            "_radio_database_var_bool",
            "_radio_database_var_set",
            "_sync_radio_database_select_all_state",
        ):
            setattr(app, name, getattr(ui.NetMonRadioApp, name).__get__(app))
        for row, (source_id, label, url) in enumerate(ui.RADIO_DATABASE_SOURCES):
            ui.NetMonRadioApp._add_radio_database_source_row(
                app, frame, row_idx=row, source_id=source_id, label=label, url=url
            )
        boxes = [
            widget
            for widget in frame.winfo_children()
            if isinstance(widget, ttk.Checkbutton)
        ]
        assert len(boxes) == len(ui.RADIO_DATABASE_SOURCES)
        assert not set(UNSUPPORTED).intersection(
            source[0] for source in ui.RADIO_DATABASE_SOURCES
        )
        before = len(frame.winfo_children())
        for source in UNSUPPORTED:
            assert (
                ui.NetMonRadioApp._add_radio_database_source_row(
                    app,
                    frame,
                    row_idx=99,
                    source_id=source,
                    label=source,
                    url="https://example.com",
                )
                == 99
            )
        assert len(frame.winfo_children()) == before
        for (source_id, _label, _url), box in zip(ui.RADIO_DATABASE_SOURCES, boxes):
            assert box.instate(["disabled"]) == (source_id in UNSUPPORTED)
            if source_id in UNSUPPORTED:
                assert not bool(root.getvar(box.cget("variable")))
                assert "Kein Direktimport" in box.cget("text")
        assert set(app.radio_database_source_vars) == set(IMPORTABLE)
        assert radio._radio_database_source_ids_for_download(app) == [
            "radio_browser_api"
        ]
        ui.NetMonRadioApp.on_radio_database_select_all_changed(app)
        assert set(radio._radio_database_source_ids_for_download(app)) == set(
            IMPORTABLE
        )
        assert all(
            not box._netmon_source_var.get()
            for source, box in zip(ui.RADIO_DATABASE_SOURCES, boxes)
            if source[0] in UNSUPPORTED
        )
    finally:
        root.destroy()


def test_legacy_source_selection_imports_without_unsupported_source_failure(
    monkeypatch, tmp_path
):
    path, meta = tmp_path / "catalog.json", tmp_path / "meta.json"
    path.write_text("[]")
    meta.write_text("{}")
    logs, progress, summaries, contacted = [], [], [], []
    app = SimpleNamespace(
        radio_db_path=str(path),
        radio_db_meta_path=str(meta),
        radio_database_source_vars={
            source: Flag(
                source not in radio.RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS
            )
            for source, _label, _url in ui.RADIO_DATABASE_SOURCES
        },
        log=logs.append,
    )

    def fetch(url, **_options):
        assert url in IMPORTABLE.values()
        contacted.append(url)
        return [{"name": "Updated Radio", "url": "https://example.com/live"}]

    monkeypatch.setattr(radio.radio_sandbox, "fetch_catalog", fetch)
    monkeypatch.setattr(radio, "_schedule_ui", lambda _app, callback: callback())
    monkeypatch.setattr(radio, "refresh_radio_ui", lambda _app: None)
    monkeypatch.setattr(
        radio,
        "_set_radio_database_import_progress",
        lambda *_a, **_k: progress.append(_a[3]),
    )
    monkeypatch.setattr(
        radio,
        "_show_radio_database_import_summary",
        lambda _app, summary: summaries.append(summary),
    )
    thread = radio.download_radio_db(app)
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert contacted
    assert json.loads(path.read_text())[0]["name"] == "Updated Radio"
    assert json.loads(meta.read_text())["count"] == 1
    assert summaries and not summaries[0]["errors"]
    assert any("Import abgeschlossen" in message for message in progress)
    assert not any("fehlgeschlagen" in message for message in logs)


@pytest.mark.parametrize("source_vars", [None, {}])
def test_update_without_source_popup_uses_radio_browser_only(source_vars):
    app = SimpleNamespace(radio_database_source_vars=source_vars)
    assert radio._radio_database_source_ids_for_download(app) == ["radio_browser_api"]


def test_omitted_optional_source_is_not_enabled_implicitly():
    app = SimpleNamespace(radio_database_source_vars={"radio_browser_api": Flag(True)})
    assert radio._radio_database_source_ids_for_download(app) == ["radio_browser_api"]
