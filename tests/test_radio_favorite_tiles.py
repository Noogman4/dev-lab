"""Favorite cards with synthetic pixels; no radio streams or external logos."""

import hashlib
import struct
import threading
import time
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import pytest

from netmon import netmon_radio_app as app_ui
from netmon.core import radio_logo
from netmon.features import radio_controller
from netmon.ui import radio_favorites as ui


def pixels():
    return radio_logo.MAGIC + b"".join(
        struct.pack(">HH", 2, 2) + b"\x32\xac\xb4\xff" * 4 for _ in radio_logo.SIZES
    )


def station(key, name="", favicon=""):
    return {"id": str(key), "name": name or f"Radio {key}", "favicon": favicon}


@pytest.fixture
def cards(tmp_path):
    root = tk.Tk()
    root.geometry("880x420")
    calls = []
    widget = ui.RadioFavoriteTiles(
        root,
        cache_dir=tmp_path,
        limiter=threading.BoundedSemaphore(2),
        on_select=lambda key: calls.append(("select", key)),
        on_play=lambda key: calls.append(("play", key)),
        on_context=lambda key, event: calls.append(("context", key)),
        theme=app_ui.DARK_THEME,
        loader=lambda url, cache: pixels(),
    )
    widget.pack(fill="both", expand=True)
    root.update()
    yield root, widget, calls
    root.destroy()


def wait_for(root, predicate):
    end = time.monotonic() + 3
    while not predicate():
        assert time.monotonic() < end, "Logo test timed out"
        root.update()
        time.sleep(0.005)


def test_fetch_is_protected_and_cached_without_parent_image_codec(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        ui.radio_sandbox, "fetch_logo", lambda url: calls.append(url) or pixels()
    )
    monkeypatch.setattr(
        ui.Image, "open", lambda *a, **k: pytest.fail("Parent image codec")
    )
    url = "https://example.com/logo.png"
    assert ui.load_logo(url, tmp_path) == pixels()
    assert ui.load_logo(url, tmp_path) == pixels()
    assert calls == [url]


def test_cache_symlink_is_not_followed_and_corrupt_pixels_are_replaced(
    tmp_path, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        ui.radio_sandbox, "fetch_logo", lambda url: calls.append(url) or pixels()
    )
    url = "https://example.com/logo.png"
    outside = tmp_path / "untouched"
    outside.write_bytes(b"private fixture")
    cached = tmp_path / (hashlib.sha256(url.encode()).hexdigest() + ".pixels")
    cached.symlink_to(outside)
    assert ui.load_logo(url, tmp_path) == pixels()
    assert not cached.is_symlink()
    assert outside.read_bytes() == b"private fixture"
    cached.write_bytes(b"broken raw cache")
    assert ui.load_logo(url, tmp_path) == pixels()
    assert len(calls) == 2


def test_invalid_schemes_do_not_start_logo_work(cards):
    root, view, calls = cards
    view.loader = lambda *args: pytest.fail("Unexpected logo fetch")
    view.show_stations([station("a", favicon="file:///etc/passwd"), station("b")])
    root.update()
    assert len(view.cards) == 2
    assert view.pending == set() and view.poll is None
    assert calls == []
    assert all(
        "image" not in [card.type(item) for item in card.find_all()]
        for card in view.cards.values()
    )
    assert all(
        "oval" in [card.type(item) for item in card.find_all()]
        for card in view.cards.values()
    )


@pytest.mark.parametrize("failure", ["absent", "exception", "malformed"])
def test_failed_logo_keeps_our_vector_icon_and_name(cards, failure):
    root, view, calls = cards

    def load(*args):
        if failure == "exception":
            raise OSError("synthetic offline")
        return None if failure == "absent" else b"bad image"

    view.loader = load
    view.show_stations([station("a", "Mein Sender", "https://example.com/a")])
    wait_for(root, lambda: not view.pending)
    card = view.cards["a"]
    assert any(
        card.itemcget(item, "text") == "Mein Sender"
        for item in card.find_all()
        if card.type(item) == "text"
    )
    assert not any(card.type(item) == "image" for item in card.find_all())
    assert calls == []
    assert view.poll is None


def test_valid_logo_deduplicates_requests_and_uses_only_raw_pixels_on_tk(
    cards, monkeypatch
):
    root, view, calls = cards
    threads = []
    url = "https://example.com/a"

    def load(source, _cache):
        threads.append(threading.current_thread())
        assert source == url
        return pixels()

    monkeypatch.setattr(ui.Image, "open", lambda *a, **k: pytest.fail("Parent codec"))
    view.loader = load
    view.show_stations([station("a", favicon=url), station("b", favicon=url)])
    wait_for(root, lambda: not view.pending)
    assert len(threads) == 1 and threads[0] is not threading.main_thread()
    assert all(
        any(card.type(item) == "image" for item in card.find_all())
        for card in view.cards.values()
    )
    view.show_stations([station("a", favicon=url), station("b", favicon=url)], "b")
    root.update()
    assert len(threads) == 1 and calls == []


def test_fitting_cards_do_not_scroll_into_empty_space(cards):
    root, view, calls = cards
    view.show_stations([station(i) for i in range(5)])
    root.update()
    first = view.cards["0"]
    top = first.winfo_rooty()
    assert view.body.winfo_height() < view.canvas.winfo_height()
    for target in (view.canvas, view.body, first):
        for event, options in (
            ("<Button-4>", {}),
            ("<Button-5>", {}),
            ("<MouseWheel>", {"delta": 120}),
            ("<MouseWheel>", {"delta": -120}),
        ):
            target.event_generate(event, **options)
            root.update()
            assert first.winfo_rooty() == top
    # The scrollbar uses the canvas API directly.
    for fraction in (1, 0, -1):
        view.canvas.yview_moveto(fraction)
        root.update()
        assert first.winfo_rooty() == top
    assert calls == []


def test_overflow_scrolls_and_resize_restores_fitting_cards_to_top(cards):
    root, view, calls = cards
    root.geometry("280x260")
    view.show_stations([station(i) for i in range(6)])
    root.update()
    assert view.body.winfo_height() > view.canvas.winfo_height()
    view.cards["0"].event_generate("<Button-5>")
    root.update()
    assert view.canvas.yview()[0] > 0
    view.canvas.yview_moveto(1)
    root.update()
    assert view.canvas.yview()[0] > 0
    root.geometry("880x420")
    root.update()
    assert view.body.winfo_height() < view.canvas.winfo_height()
    assert view.canvas.yview() == (0.0, 1.0)
    assert view.cards["0"].winfo_rooty() == view.canvas.winfo_rooty() + ui.CARD_GAP // 2
    assert calls == []


def test_resize_scroll_keyboard_and_exact_station_callbacks(cards):
    root, view, calls = cards
    view.show_stations([station(i) for i in range(12)], "0")
    root.update()
    assert view.columns >= 3
    root.geometry("280x300")
    root.update()
    assert view.columns == 1
    assert view.canvas.bbox("all")[3] > view.canvas.winfo_height()
    view.cards["2"].event_generate("<ButtonRelease-1>", x=20, y=20)
    root.update()
    assert calls == [("select", "2"), ("play", "2")]
    view.cards["4"].event_generate("<ButtonRelease-3>", x=20, y=20)
    root.update()
    assert calls[-2:] == [("select", "4"), ("context", "4")]
    view._navigate("4", "Down", None)
    assert view.selected == "5"
    assert calls[-1] == ("select", "5")
    view._activate("5")
    assert calls[-1] == ("play", "5")


def test_cancelled_logo_cannot_replace_new_page_or_touch_tk_after_destroy(cards):
    root, view, calls = cards
    began, release, finished = threading.Event(), threading.Event(), threading.Event()

    def load(*args):
        began.set()
        assert release.wait(2)
        finished.set()
        return pixels()

    view.loader = load
    view.show_stations([station("old", favicon="https://example.com/old")])
    assert began.wait(1)
    view.show_stations([station("new")])
    release.set()
    assert finished.wait(1)
    root.update()
    assert list(view.cards) == ["new"] and view.photos == {}
    view.destroy()
    assert view.stop.is_set() and view.poll is None
    assert calls == []


def test_long_names_have_two_fitting_lines_and_survive_theme_change(cards):
    root, view, calls = cards
    name = "Sehr langer Sendername " * 20
    for text in (name, "W" * 256, "日本のラジオ " * 20):
        fitted = ui.fit_name(text, view.font, 180)
        assert len(fitted.splitlines()) <= 2
        assert all(view.font.measure(line) <= 180 for line in fitted.splitlines())
        assert fitted.endswith("…")
    view.show_stations([station("a", name)])
    view.apply_theme(app_ui.LIGHT_THEME)
    root.update()
    assert view.canvas.cget("background") == app_ui.LIGHT_THEME["panel_bg"]
    assert calls == []


def test_favorite_filter_and_pagination_switch_only_the_favorite_view(cards):
    root, view, _calls = cards
    view.pack_forget()
    parent = ttk.Frame(root)
    parent.pack(fill="both", expand=True)
    table = ttk.Treeview(parent, columns=("name",))
    table.grid(row=2, column=0)
    # Use a card grid in the same parent/cell as the real app.
    grid = ui.RadioFavoriteTiles(
        parent,
        cache_dir=view.cache_dir,
        limiter=view.limiter,
        on_select=lambda key: None,
        on_play=lambda key: None,
        on_context=lambda *args: None,
        theme=app_ui.DARK_THEME,
    )
    scroll = ttk.Scrollbar(parent)
    horizontal = ttk.Scrollbar(parent, orient="horizontal")
    horizontal.grid(row=3, column=0)
    favorites = [station(i) for i in range(55)]
    app = SimpleNamespace(
        radio_favorite_tiles=grid,
        radio_station_table=table,
        radio_station_scroll=scroll,
        radio_station_scroll_x=horizontal,
        radio_show_favorites_var=tk.BooleanVar(value=True),
        radio_favorites=favorites,
        radio_db=[station("other")],
        radio_search_var=tk.StringVar(value=""),
        radio_settings={},
        radio_current_station_id="",
        radio_search_page=0,
    )
    app.refresh_radio_favorite_tiles = (
        lambda rows, selected: app_ui.NetMonRadioApp.refresh_radio_favorite_tiles(
            app, rows, selected
        )
    )
    radio_controller.refresh_radio_station_table(app)
    root.update()
    assert len(grid.cards) == 50 and not table.winfo_ismapped()
    radio_controller.set_radio_search_page(app, 1)
    root.update()
    assert list(grid.cards) == [str(i) for i in range(50, 55)]
    app.radio_search_var.set("Radio 54")
    radio_controller.refresh_radio_station_table(app, reset_page=True)
    assert list(grid.cards) == ["54"]
    app.radio_show_favorites_var.set(False)
    app.radio_search_var.set("other")
    radio_controller.refresh_radio_station_table(app, reset_page=True)
    root.update()
    assert table.winfo_ismapped() and not grid.winfo_ismapped()
    assert grid.stop.is_set()
    assert table.get_children() == ("other",)


@pytest.mark.parametrize("mode", ["standalone", "embedded-light", "embedded-dark"])
def test_real_radio_builders_include_favorite_tiles_without_runtime_actions(
    monkeypatch, mode
):
    monkeypatch.setattr(app_ui, "prepare_user_files", lambda: None)
    monkeypatch.setattr(
        app_ui.netmon_projectm_sidecar, "ensure_projectm_preset_dir", lambda _app: None
    )
    monkeypatch.setattr(
        app_ui.NetMonRadioApp, "_refresh_projectm_status", lambda _app: None
    )
    monkeypatch.setattr(
        app_ui.NetMonRadioApp, "refresh_radio_attach_state", lambda _app: None
    )
    monkeypatch.setattr(
        app_ui.NetMonRadioApp, "stop_radio_recording", lambda _app: None
    )
    monkeypatch.setattr(
        app_ui.NetMonRadioApp, "stop_radio_playback", lambda _app, **kw: None
    )
    monkeypatch.setattr(
        app_ui.NetMonRadioApp, "close_projectm_visualizer_test", lambda _app: None
    )
    monkeypatch.setattr(radio_controller, "save_radio_settings", lambda _app: True)
    monkeypatch.setattr(
        radio_controller, "update_radio_dependency_state", lambda _app: None
    )

    def load(app):
        app.radio_favorites = [station("one", "Mein Favorit")]

    monkeypatch.setattr(radio_controller, "load_radio_runtime", load)
    for name in (
        "current_radio_transition_id",
        "consume_radio_handover",
        "complete_radio_transition",
        "set_radio_detached_state",
    ):
        monkeypatch.setattr(app_ui.netmon_radio_core, name, lambda *a, **kw: None)
    plays = []
    monkeypatch.setattr(
        radio_controller, "play_radio_station", lambda app, key: plays.append(key)
    )
    root = None
    if mode == "standalone":
        app = app_ui.NetMonRadioApp()
    else:
        root = tk.Tk()
        host = SimpleNamespace(_app_theme={"name": mode.removeprefix("embedded-")})
        app = app_ui.NetMonRadioPanel(root, host_app=host)
        app.pack(fill="both", expand=True)
    try:
        app.update()
        assert not app.radio_favorite_tiles.winfo_ismapped()
        app.toggle_radio_favorites_view()
        app.update()
        assert app.radio_favorite_tiles.winfo_ismapped()
        assert not app.radio_station_table.winfo_ismapped()
        assert list(app.radio_favorite_tiles.cards) == ["one"]
        assert plays == []
        app.radio_favorite_tiles._activate("one")
        assert plays == ["one"]
        assert radio_controller._selected_station_id(app) == "one"
        app.toggle_radio_favorites_view()
        app.update()
        assert app.radio_station_table.winfo_ismapped()
        assert not app.radio_favorite_tiles.winfo_ismapped()
    finally:
        app.destroy()
        if root is not None:
            root.destroy()


def test_transient_failure_is_retried_once_and_success_is_cached(cards, monkeypatch):
    root, view, _ = cards
    monkeypatch.setattr(ui, "RETRY_DELAY_MS", 20)
    calls, errors = [], []
    view.on_logo_error = errors.append

    def load(url, _cache):
        calls.append(url)
        if len(calls) == 1:
            raise ui.radio_sandbox.LogoError("network")
        return pixels()

    view.loader = load
    url = "https://radio.example/icon.png"
    rows = [station("one", favicon=url)]
    view.show_stations(rows)
    wait_for(root, lambda: view.photos.get(url) is not None)
    assert calls == [url, url] and errors == ["network"]
    assert url not in view.failures
    assert view.retry is None
    view.show_stations(rows)
    root.update()
    assert len(calls) == 2


def test_repeated_failure_has_a_cooldown_and_deactivation_cancels_retry(
    cards, monkeypatch
):
    root, view, _ = cards
    monkeypatch.setattr(ui, "RETRY_DELAY_MS", 20)
    calls = []

    def fail(url, _cache):
        calls.append(url)
        raise ui.radio_sandbox.LogoError("http")

    view.loader = fail
    url = "https://radio.example/missing.png"
    rows = [station("one", favicon=url)]
    view.show_stations(rows)
    wait_for(root, lambda: view.failures.get(url, (0,))[0] == 2)
    view.deactivate()
    view.show_stations(rows)
    root.update()
    assert calls == [url, url]
    assert url not in view.photos  # Failed placeholders never enter the image cache.
    assert view.retry is None
    view.failures[url] = (2, time.monotonic() - 1, "http")
    view.show_stations(rows)
    wait_for(root, lambda: len(calls) == 3 and not view.pending)
    assert view.retry is not None
    view.deactivate()
    assert view.retry is None and not view.pending


def test_missing_icon_with_homepage_uses_and_caches_only_protected_pixels(
    cards, monkeypatch
):
    root, view, _ = cards
    calls = []
    home = "https://radio.example/"
    row = station("one")
    row["homepage"] = home

    def fetch(url, **options):
        calls.append((url, options))
        return pixels()

    monkeypatch.setattr(ui.radio_sandbox, "fetch_logo", fetch)
    monkeypatch.setattr(
        ui.Image, "open", lambda *a, **kw: pytest.fail("parent image codec")
    )
    view.loader = ui.load_logo
    view.show_stations([row])
    key = ui.logo_key(row)
    wait_for(root, lambda: view.photos.get(key) is not None)
    assert calls == [("", {"homepage": home})]
    assert ui.load_logo(key, view.cache_dir) == pixels()
    assert len(calls) == 1


@pytest.mark.parametrize(
    "source_size,bounds",
    [
        ((8, 8), (0, 0, 52, 52)),
        ((32, 16), (0, 13, 52, 39)),
        ((16, 32), (13, 0, 39, 52)),
    ],
)
def test_small_favorite_logos_fill_their_standard_box(
    cards, monkeypatch, source_size, bounds
):
    from PIL import ImageTk

    root, view, calls = cards
    width, height = source_size
    payload = radio_logo.MAGIC + b"".join(
        struct.pack(">HH", width, height) + b"\xff\0\0\x80" * (width * height)
        for _ in radio_logo.SIZES
    )
    view.loader = lambda *_args: payload
    monkeypatch.setattr(
        ui.Image, "open", lambda *a, **kw: pytest.fail("Encoded codec in tile renderer")
    )
    url = "https://radio.example/tiny.png"
    view.show_stations([station("tiny", favicon=url)])
    wait_for(root, lambda: view.photos.get(url) is not None)
    image = ImageTk.getimage(view.photos[url])
    assert image.size == (52, 52) and image.getbbox() == bounds
    assert image.getpixel((26, 26)) == (255, 0, 0, 128)
    assert calls == []
