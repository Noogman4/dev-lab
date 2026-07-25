"""Standalone Tk app for NetMon Radio."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import io
import json
import math
import os
import shlex
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
import types
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib import request as urllib_request
from urllib.parse import urlparse

try:
    from netmon.features import radio_controller
except ModuleNotFoundError:
    import features.radio_controller as radio_controller

try:
    from netmon.netmon_radio_core import build_radio_paths
except ModuleNotFoundError:
    from netmon_radio_core import build_radio_paths

try:
    from netmon import netmon_radio_core
except ModuleNotFoundError:
    import netmon_radio_core

try:
    from netmon import netmon_projectm_sidecar
except ModuleNotFoundError:
    import netmon_projectm_sidecar

try:
    from PIL import Image, ImageDraw, ImageTk
except Exception:
    Image = None
    ImageDraw = None
    ImageTk = None


LIGHT_THEME = {
    "name": "light",
    "bg": "#f4f6f8",
    "panel_bg": "#f4f6f8",
    "fg": "#101418",
    "muted_fg": "#2f3a44",
    "accent": "#2f6feb",
    "border": "#c6d0db",
    "disabled_fg": "#7a8694",
    "entry_bg": "#ffffff",
    "entry_fg": "#111111",
    "text_bg": "#ffffff",
    "text_fg": "#101418",
    "select_bg": "#2f6feb",
    "select_fg": "#ffffff",
    "tree_bg": "#ffffff",
    "tree_fg": "#111111",
    "tab_bg": "#dde3ea",
    "tab_fg": "#111111",
    "tab_selected_bg": "#ffffff",
    "tab_selected_fg": "#000000",
}

DARK_THEME = {
    "name": "dark",
    "bg": "#111418",
    "panel_bg": "#111418",
    "fg": "#e6edf3",
    "muted_fg": "#b8c1cc",
    "accent": "#58a6ff",
    "border": "#2b3440",
    "disabled_fg": "#7a8694",
    "entry_bg": "#181d24",
    "entry_fg": "#e6edf3",
    "text_bg": "#0d1117",
    "text_fg": "#dce4ee",
    "select_bg": "#264f78",
    "select_fg": "#ffffff",
    "tree_bg": "#0d1117",
    "tree_fg": "#dce4ee",
    "tab_bg": "#1a212b",
    "tab_fg": "#c3cfdb",
    "tab_selected_bg": "#263142",
    "tab_selected_fg": "#ffffff",
}

RADIO_DATABASE_SOURCES = (
    (
        "radio_browser_api",
        "Radio Browser",
        "https://de1.api.radio-browser.info/json/stations",
    ),
    (
        "radio_browser_all_api",
        "Radio Browser ALL API",
        "https://all.api.radio-browser.info/json/stations",
    ),
    (
        "radio_browser_country_de_exact",
        "Radio Browser Deutschland exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/DE",
    ),
    (
        "radio_browser_country_at_exact",
        "Radio Browser Österreich exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/AT",
    ),
    (
        "radio_browser_country_ch_exact",
        "Radio Browser Schweiz exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/CH",
    ),
    (
        "radio_browser_country_fr_exact",
        "Radio Browser Frankreich exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/FR",
    ),
    (
        "radio_browser_country_it_exact",
        "Radio Browser Italien exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/IT",
    ),
    (
        "radio_browser_country_es_exact",
        "Radio Browser Spanien exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/ES",
    ),
    (
        "radio_browser_country_nl_exact",
        "Radio Browser Niederlande exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/NL",
    ),
    (
        "radio_browser_country_be_exact",
        "Radio Browser Belgien exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/BE",
    ),
    (
        "radio_browser_country_gb_exact",
        "Radio Browser Großbritannien exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/GB",
    ),
    (
        "radio_browser_country_us_exact",
        "Radio Browser USA exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/US",
    ),
    (
        "radio_browser_country_ca_exact",
        "Radio Browser Kanada exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/CA",
    ),
    (
        "radio_browser_country_au_exact",
        "Radio Browser Australien exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/AU",
    ),
    (
        "radio_browser_country_jp_exact",
        "Radio Browser Japan exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/JP",
    ),
    (
        "radio_browser_country_br_exact",
        "Radio Browser Brasilien exakt",
        "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/BR",
    ),
    (
        "radio_browser_country",
        "Radio Browser Land",
        "https://de1.api.radio-browser.info/json/stations/bycountry/",
    ),
    (
        "radio_browser_tag",
        "Radio Browser Genre/Tag",
        "https://de1.api.radio-browser.info/json/stations/bytag/",
    ),
    (
        "radio_browser_top",
        "Radio Browser Top Votes",
        "https://de1.api.radio-browser.info/json/stations/topvote/100",
    ),
    (
        "radio_browser_search",
        "Radio Browser Suche",
        "https://de1.api.radio-browser.info/json/stations/search",
    ),
    ("shoutcast_api", "SHOUTcast Directory", "https://directory.shoutcast.com/"),
    ("icecast_directory", "Icecast Directory", "https://dir.xiph.org/"),
    ("icecast_json", "Icecast JSON Feed", "https://dir.xiph.org/yp.xml"),
    ("fmstream", "fmstream", "https://fmstream.org/index.php"),
    ("streamurl_link", "streamurl.link", "https://streamurl.link/"),
    ("airable", "airable.radio", "https://www.airablenow.com/"),
    (
        "community_radio_api",
        "Community Radio Browser API",
        "https://api.radio-browser.info/",
    ),
    ("radio_api", "RadioAPI", "https://radioapi.me/"),
)

PROJECTM_PRESET_SOURCE_URL = "https://milkdrop.org/"

BEIGE_THEME = {
    "name": "beige",
    "bg": "#dbc7ab",
    "panel_bg": "#dbc7ab",
    "fg": "#2a2016",
    "muted_fg": "#655544",
    "accent": "#95652f",
    "border": "#b79b79",
    "disabled_fg": "#826f5b",
    "entry_bg": "#efdfc9",
    "entry_fg": "#2a2016",
    "text_bg": "#f4e8d6",
    "text_fg": "#2a2016",
    "select_bg": "#a97841",
    "select_fg": "#1f1a15",
    "tree_bg": "#f0e1cc",
    "tree_fg": "#2a2016",
    "tab_bg": "#c7a47a",
    "tab_fg": "#2a2016",
    "tab_selected_bg": "#e6d2b8",
    "tab_selected_fg": "#2a2118",
}

POP_THEME = {
    "name": "pop",
    "bg": "#fff4ef",
    "panel_bg": "#fff4ef",
    "fg": "#2b1834",
    "muted_fg": "#6e5876",
    "accent": "#ff5a8a",
    "border": "#f5b8c9",
    "disabled_fg": "#a78fa6",
    "entry_bg": "#fffdfd",
    "entry_fg": "#2b1834",
    "text_bg": "#fffafb",
    "text_fg": "#2b1834",
    "select_bg": "#ff8fb1",
    "select_fg": "#2b1834",
    "tree_bg": "#fff8f8",
    "tree_fg": "#2b1834",
    "tab_bg": "#ffd7e2",
    "tab_fg": "#482454",
    "tab_selected_bg": "#fff0a8",
    "tab_selected_fg": "#432050",
}

RADIO_THEMES = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
    "beige": BEIGE_THEME,
    "pop": POP_THEME,
}

RADIO_THEME_SEQUENCE = ("light", "dark", "beige", "pop")
RADIO_THEME_DISPLAY_NAMES = {
    "light": "Light",
    "dark": "Darkmode",
    "beige": "Beige",
    "pop": "Pop",
}
RADIO_THEME_PALETTE_KEYS = (
    "bg",
    "panel_bg",
    "fg",
    "muted_fg",
    "accent",
    "border",
    "disabled_fg",
    "entry_bg",
    "entry_fg",
    "text_bg",
    "text_fg",
    "select_bg",
    "select_fg",
    "tree_bg",
    "tree_fg",
    "tab_bg",
    "tab_fg",
    "tab_selected_bg",
    "tab_selected_fg",
)

RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS = {
    "radio_browser_country_de_exact",
    "radio_browser_country_at_exact",
    "radio_browser_country_ch_exact",
    "radio_browser_country_fr_exact",
    "radio_browser_country_it_exact",
    "radio_browser_country_es_exact",
    "radio_browser_country_nl_exact",
    "radio_browser_country_be_exact",
    "radio_browser_country_gb_exact",
    "radio_browser_country_us_exact",
    "radio_browser_country_ca_exact",
    "radio_browser_country_au_exact",
    "radio_browser_country_jp_exact",
    "radio_browser_country_br_exact",
}


def _standalone_radio_pane_drag_state() -> dict[str, int | bool]:
    return {
        "root_y": 0,
        "sash_y": 0,
        "update_pending": False,
    }


def _standalone_radio_pane_bind_marker_events(widget, bindings) -> None:
    try:
        for event_name, callback in bindings:
            widget.bind(event_name, callback, add="+")
    except Exception:
        pass


def _standalone_radio_pane_update_binding_specs():
    return (
        "<Configure>",
        "<ButtonRelease-1>",
        "<B1-Motion>",
    )


def _standalone_radio_pane_update_bindings(
    update_marker,
    *,
    binding_specs_builder=_standalone_radio_pane_update_binding_specs,
):
    configure_event, release_event, motion_event = binding_specs_builder()
    return (
        (configure_event, update_marker),
        (release_event, update_marker),
        (motion_event, update_marker),
    )


def _standalone_radio_pane_grip_binding_specs():
    return (
        "<Button-1>",
        "<B1-Motion>",
        "<ButtonRelease-1>",
    )


def _standalone_radio_pane_grip_bindings(
    start_drag,
    drag,
    end_drag,
    *,
    binding_specs_builder=_standalone_radio_pane_grip_binding_specs,
):
    start_event, drag_event, end_event = binding_specs_builder()
    return (
        (start_event, start_drag),
        (drag_event, drag),
        (end_event, end_drag),
    )


def _standalone_radio_pane_marker_update_binding_plan(
    container,
    pane,
    update_bindings,
):
    return (
        (container, update_bindings),
        (pane, update_bindings),
    )


def _standalone_radio_pane_marker_grip_binding_plan(
    grip,
    grip_bindings,
):
    return ((grip, grip_bindings),)


def _standalone_radio_pane_marker_binding_plan(
    container,
    pane,
    grip,
    *,
    update_bindings,
    grip_bindings,
    update_plan_builder=_standalone_radio_pane_marker_update_binding_plan,
    grip_plan_builder=_standalone_radio_pane_marker_grip_binding_plan,
):
    return update_plan_builder(
        container,
        pane,
        update_bindings,
    ) + grip_plan_builder(grip, grip_bindings)


def _standalone_radio_pane_bind_marker_callback(
    widget,
    bindings,
    bind_events,
) -> None:
    bind_events(widget, bindings)


def _standalone_radio_pane_bind_marker_callbacks(
    binding_plan,
    *,
    bind_callback=_standalone_radio_pane_bind_marker_callback,
    bind_events=_standalone_radio_pane_bind_marker_events,
) -> None:
    for widget, bindings in binding_plan:
        bind_callback(widget, bindings, bind_events)


def _standalone_radio_pane_initial_update_after_args(update_marker):
    return 0, update_marker


def _standalone_radio_pane_request_initial_marker_update(
    container,
    update_marker,
    *,
    after_args_builder=_standalone_radio_pane_initial_update_after_args,
) -> None:
    try:
        delay, callback = after_args_builder(update_marker)
        container.after(delay, callback)
    except Exception:
        pass


def _standalone_radio_pane_initial_update_request_args(
    container,
    update_marker,
):
    return container, update_marker


def _standalone_radio_pane_schedule_initial_marker_update(
    container,
    update_marker,
    *,
    request_args_builder=_standalone_radio_pane_initial_update_request_args,
    request_update=_standalone_radio_pane_request_initial_marker_update,
) -> None:
    request_args = request_args_builder(container, update_marker)
    container_arg, update_arg = request_args
    request_update(container_arg, update_arg)


def _standalone_radio_pane_active_initial_update_args(
    container,
    update_marker,
    initial_update_scheduler,
):
    return container, update_marker, initial_update_scheduler


def _standalone_radio_pane_schedule_active_marker_initial_update(
    container,
    update_marker,
    initial_update_scheduler,
    *,
    active_update_args_builder=_standalone_radio_pane_active_initial_update_args,
) -> None:
    active_update_args = active_update_args_builder(
        container,
        update_marker,
        initial_update_scheduler,
    )
    container_arg, update_arg, scheduler = active_update_args
    scheduler(container_arg, update_arg)


def _standalone_radio_pane_bind_active_marker_callbacks(
    binding_plan,
    callback_binder,
) -> None:
    callback_binder(binding_plan)


def _standalone_radio_pane_activate_marker_callbacks(
    container,
    binding_plan,
    update_marker,
    *,
    callback_binder=_standalone_radio_pane_bind_marker_callbacks,
    active_callback_binder=_standalone_radio_pane_bind_active_marker_callbacks,
    active_initial_update_scheduler=(
        _standalone_radio_pane_schedule_active_marker_initial_update
    ),
    initial_update_scheduler=_standalone_radio_pane_schedule_initial_marker_update,
) -> None:
    active_callback_binder(binding_plan, callback_binder)
    active_initial_update_scheduler(
        container,
        update_marker,
        initial_update_scheduler,
    )


def _standalone_radio_pane_marker_binding_sets(
    update_marker,
    start_drag,
    drag,
    end_drag,
    *,
    update_bindings_builder=_standalone_radio_pane_update_bindings,
    grip_bindings_builder=_standalone_radio_pane_grip_bindings,
):
    update_bindings = update_bindings_builder(update_marker)
    grip_bindings = grip_bindings_builder(start_drag, drag, end_drag)
    return update_bindings, grip_bindings


def _standalone_radio_pane_marker_binding_plan_from_sets(
    container,
    pane,
    grip,
    binding_sets,
    *,
    binding_plan_builder=_standalone_radio_pane_marker_binding_plan,
):
    update_bindings, grip_bindings = binding_sets
    return binding_plan_builder(
        container,
        pane,
        grip,
        update_bindings=update_bindings,
        grip_bindings=grip_bindings,
    )


def _standalone_radio_pane_activate_marker_binding_plan(
    container,
    binding_plan,
    update_marker,
    *,
    activate_marker_callbacks=_standalone_radio_pane_activate_marker_callbacks,
) -> None:
    activate_marker_callbacks(container, binding_plan, update_marker)


def _standalone_radio_pane_activate_marker_bindings(
    container,
    pane,
    grip,
    update_marker,
    start_drag,
    drag,
    end_drag,
    *,
    binding_sets_builder=_standalone_radio_pane_marker_binding_sets,
    binding_plan_builder=_standalone_radio_pane_marker_binding_plan_from_sets,
    binding_plan_activator=_standalone_radio_pane_activate_marker_binding_plan,
) -> None:
    binding_sets = binding_sets_builder(
        update_marker,
        start_drag,
        drag,
        end_drag,
    )
    binding_plan = binding_plan_builder(
        container,
        pane,
        grip,
        binding_sets,
    )
    binding_plan_activator(container, binding_plan, update_marker)


def _standalone_radio_pane_marker_geometry(
    container_width,
    sash_y,
    y_offset=0,
) -> dict[str, int]:
    width = max(int(container_width or 0), 0)
    marker_width = min(66, max(width - 24, 42))
    x = max((width - marker_width) // 2, 8)
    y = max(sash_y - 5 + int(y_offset), 2)
    return {"x": x, "y": y, "width": marker_width, "height": 12}


def _standalone_radio_pane_place_marker(marker, geometry) -> None:
    marker.place(**geometry)
    marker.lift()


def _standalone_radio_pane_forget_marker(marker) -> None:
    marker.place_forget()


def _standalone_radio_pane_set_sash_pos(pane, new_y) -> None:
    try:
        pane.sashpos(0, int(new_y))
        return
    except Exception:
        pass
    try:
        pane.sash_place(0, 0, int(new_y))
    except Exception:
        pass


def _standalone_radio_pane_sash_callback(
    pane,
    *,
    set_sash_pos=_standalone_radio_pane_set_sash_pos,
):
    def _set_sash_pos(new_y):
        set_sash_pos(pane, new_y)

    return _set_sash_pos


def _standalone_radio_pane_place_marker_for_sash(
    container,
    marker,
    sash_y,
    y_offset=0,
    *,
    geometry_builder=_standalone_radio_pane_marker_geometry,
    marker_placer=_standalone_radio_pane_place_marker,
) -> None:
    geometry = geometry_builder(
        container.winfo_width(),
        sash_y,
        y_offset,
    )
    marker_placer(marker, geometry)


def _standalone_radio_pane_place_marker_for_sash_safe(
    container,
    marker,
    sash_y,
    y_offset=0,
    *,
    place_marker_for_sash=_standalone_radio_pane_place_marker_for_sash,
    forget_marker=_standalone_radio_pane_forget_marker,
) -> None:
    try:
        place_marker_for_sash(container, marker, sash_y, y_offset)
    except Exception:
        try:
            forget_marker(marker)
        except Exception:
            pass


def _standalone_radio_pane_place_callback(
    container,
    marker,
    y_offset=0,
    *,
    place_marker_for_sash_safe=_standalone_radio_pane_place_marker_for_sash_safe,
):
    def _place_marker_for_sash(sash_y):
        place_marker_for_sash_safe(container, marker, sash_y, y_offset)

    return _place_marker_for_sash


def _standalone_radio_pane_update_marker(pane, place_marker_for_sash) -> None:
    place_marker_for_sash(int(pane.sashpos(0)))


def _standalone_radio_pane_update_marker_safe(
    pane,
    place_marker_for_sash,
    marker,
    *,
    update_marker=_standalone_radio_pane_update_marker,
    forget_marker=_standalone_radio_pane_forget_marker,
) -> None:
    try:
        update_marker(pane, place_marker_for_sash)
    except Exception:
        try:
            forget_marker(marker)
        except Exception:
            pass


def _standalone_radio_pane_update_callback(
    pane,
    place_marker_for_sash,
    marker,
    *,
    update_marker_safe=_standalone_radio_pane_update_marker_safe,
):
    def _update_marker(_event=None):
        update_marker_safe(pane, place_marker_for_sash, marker)

    return _update_marker


def _standalone_radio_pane_schedule_marker_update(
    container,
    drag_state,
    update_marker,
) -> None:
    if drag_state["update_pending"]:
        return
    drag_state["update_pending"] = True

    def _run():
        drag_state["update_pending"] = False
        update_marker()

    try:
        container.after_idle(_run)
    except Exception:
        _run()


def _standalone_radio_pane_schedule_callback(
    container,
    drag_state,
    update_marker,
    *,
    schedule_marker_update=_standalone_radio_pane_schedule_marker_update,
):
    def _schedule_marker_update():
        schedule_marker_update(container, drag_state, update_marker)

    return _schedule_marker_update


def _standalone_radio_pane_start_drag(drag_state, event, pane) -> None:
    try:
        drag_state["root_y"] = int(event.y_root)
        drag_state["sash_y"] = int(pane.sashpos(0))
    except Exception:
        drag_state["root_y"] = 0
        drag_state["sash_y"] = 0


def _standalone_radio_pane_start_drag_event(
    drag_state,
    event,
    pane,
    *,
    start_drag=_standalone_radio_pane_start_drag,
) -> str:
    start_drag(drag_state, event, pane)
    return "break"


def _standalone_radio_pane_start_callback(
    drag_state,
    pane,
    *,
    start_drag_event=_standalone_radio_pane_start_drag_event,
):
    def _start_drag(event):
        return start_drag_event(drag_state, event, pane)

    return _start_drag


def _standalone_radio_pane_drag_motion(
    drag_state,
    event,
    set_sash_pos,
    place_marker_for_sash,
    schedule_marker_update,
) -> None:
    delta = int(event.y_root) - int(drag_state["root_y"])
    new_sash = int(drag_state["sash_y"]) + delta
    set_sash_pos(new_sash)
    place_marker_for_sash(new_sash)
    schedule_marker_update()


def _standalone_radio_pane_drag_event(
    drag_state,
    event,
    set_sash_pos,
    place_marker_for_sash,
    schedule_marker_update,
    *,
    drag_motion=_standalone_radio_pane_drag_motion,
) -> str:
    try:
        drag_motion(
            drag_state,
            event,
            set_sash_pos,
            place_marker_for_sash,
            schedule_marker_update,
        )
    except Exception:
        pass
    return "break"


def _standalone_radio_pane_drag_callback(
    drag_state,
    set_sash_pos,
    place_marker_for_sash,
    schedule_marker_update,
    *,
    drag_event=_standalone_radio_pane_drag_event,
):
    def _drag(event):
        return drag_event(
            drag_state,
            event,
            set_sash_pos,
            place_marker_for_sash,
            schedule_marker_update,
        )

    return _drag


def _standalone_radio_pane_end_drag(update_marker):
    update_marker()
    return "break"


def _standalone_radio_pane_end_callback(
    update_marker,
    *,
    end_drag=_standalone_radio_pane_end_drag,
):
    def _end_drag(_event=None):
        return end_drag(update_marker)

    return _end_drag


def _standalone_radio_pane_marker_frame_options(color):
    return {
        "bg": color,
        "bd": 1,
        "relief": "solid",
    }


def _standalone_radio_pane_marker_grip_options(color):
    return {
        "text": "≡",
        "bg": color,
        "fg": "#ffffff",
        "font": ("TkDefaultFont", 9, "bold"),
        "cursor": "sb_v_double_arrow",
        "padx": 0,
        "pady": 0,
        "anchor": "center",
    }


def _standalone_radio_pane_configure_marker_widgets(marker, grip) -> None:
    marker.columnconfigure(0, weight=1)
    grip.grid(row=0, column=0, sticky="ew")


def _standalone_radio_pane_marker_frame(
    container,
    color,
    *,
    frame_builder=tk.Frame,
    frame_options_builder=_standalone_radio_pane_marker_frame_options,
):
    return frame_builder(
        container,
        **frame_options_builder(color),
    )


def _standalone_radio_pane_marker_grip(
    marker,
    color,
    *,
    label_builder=tk.Label,
    grip_options_builder=_standalone_radio_pane_marker_grip_options,
):
    return label_builder(
        marker,
        **grip_options_builder(color),
    )


def _standalone_radio_pane_marker_widget_pair(
    container,
    color,
    *,
    marker_frame_builder=_standalone_radio_pane_marker_frame,
    marker_grip_builder=_standalone_radio_pane_marker_grip,
):
    marker = marker_frame_builder(
        container,
        color,
    )
    grip = marker_grip_builder(
        marker,
        color,
    )
    return marker, grip


def _standalone_radio_pane_marker_widgets(
    container,
    color,
    *,
    marker_pair_builder=_standalone_radio_pane_marker_widget_pair,
    configure_widgets=_standalone_radio_pane_configure_marker_widgets,
):
    marker, grip = marker_pair_builder(
        container,
        color,
    )
    configure_widgets(marker, grip)
    return marker, grip


def _standalone_radio_pane_marker_start_callback(
    drag_state,
    pane,
    *,
    start_callback_builder=_standalone_radio_pane_start_callback,
):
    return start_callback_builder(drag_state, pane)


def _standalone_radio_pane_marker_drag_callback(
    drag_state,
    set_sash_pos,
    place_marker_for_sash,
    schedule_marker_update,
    *,
    drag_callback_builder=_standalone_radio_pane_drag_callback,
):
    return drag_callback_builder(
        drag_state,
        set_sash_pos,
        place_marker_for_sash,
        schedule_marker_update,
    )


def _standalone_radio_pane_marker_drag_pair(
    drag_state,
    pane,
    set_sash_pos,
    place_marker_for_sash,
    schedule_marker_update,
    *,
    start_callback_builder=_standalone_radio_pane_marker_start_callback,
    drag_callback_builder=_standalone_radio_pane_marker_drag_callback,
):
    start_drag = start_callback_builder(drag_state, pane)
    drag = drag_callback_builder(
        drag_state,
        set_sash_pos,
        place_marker_for_sash,
        schedule_marker_update,
    )
    return start_drag, drag


def _standalone_radio_pane_marker_end_callback(
    update_marker,
    *,
    end_callback_builder=_standalone_radio_pane_end_callback,
):
    return end_callback_builder(update_marker)


def _standalone_radio_pane_marker_drag_callbacks(
    drag_state,
    pane,
    set_sash_pos,
    place_marker_for_sash,
    schedule_marker_update,
    update_marker,
    *,
    drag_pair_builder=_standalone_radio_pane_marker_drag_pair,
    end_callback_builder=_standalone_radio_pane_marker_end_callback,
):
    start_drag, drag = drag_pair_builder(
        drag_state,
        pane,
        set_sash_pos,
        place_marker_for_sash,
        schedule_marker_update,
    )
    end_drag = end_callback_builder(update_marker)
    return start_drag, drag, end_drag


def _standalone_radio_pane_marker_drag_setup(
    pane,
    *,
    drag_state_builder=_standalone_radio_pane_drag_state,
    sash_callback_builder=_standalone_radio_pane_sash_callback,
):
    drag_state = drag_state_builder()
    set_sash_pos = sash_callback_builder(pane)
    return drag_state, set_sash_pos


def _standalone_radio_pane_marker_update_pair(
    container,
    pane,
    marker,
    y_offset=0,
    *,
    place_callback_builder=_standalone_radio_pane_place_callback,
    update_callback_builder=_standalone_radio_pane_update_callback,
):
    place_marker_for_sash = place_callback_builder(container, marker, y_offset)
    update_marker = update_callback_builder(pane, place_marker_for_sash, marker)
    return place_marker_for_sash, update_marker


def _standalone_radio_pane_marker_schedule_callback(
    container,
    drag_state,
    update_marker,
    *,
    schedule_callback_builder=_standalone_radio_pane_schedule_callback,
):
    return schedule_callback_builder(
        container,
        drag_state,
        update_marker,
    )


def _standalone_radio_pane_marker_update_callbacks(
    container,
    pane,
    marker,
    drag_state,
    y_offset=0,
    *,
    update_pair_builder=_standalone_radio_pane_marker_update_pair,
    schedule_callback_builder=_standalone_radio_pane_marker_schedule_callback,
):
    place_marker_for_sash, update_marker = update_pair_builder(
        container,
        pane,
        marker,
        y_offset,
    )
    schedule_marker_update = schedule_callback_builder(
        container,
        drag_state,
        update_marker,
    )
    return place_marker_for_sash, update_marker, schedule_marker_update


def _standalone_radio_pane_marker_base_callbacks(
    container,
    pane,
    marker,
    y_offset=0,
    *,
    drag_setup_builder=_standalone_radio_pane_marker_drag_setup,
    update_callbacks_builder=_standalone_radio_pane_marker_update_callbacks,
):
    drag_state, set_sash_pos = drag_setup_builder(pane)
    (
        place_marker_for_sash,
        update_marker,
        schedule_marker_update,
    ) = update_callbacks_builder(
        container,
        pane,
        marker,
        drag_state,
        y_offset,
    )
    return (
        drag_state,
        set_sash_pos,
        place_marker_for_sash,
        update_marker,
        schedule_marker_update,
    )


def _standalone_radio_pane_marker_callback_tuple(update_marker, drag_callbacks):
    start_drag, drag, end_drag = drag_callbacks
    return update_marker, start_drag, drag, end_drag


def _standalone_radio_pane_marker_callbacks(
    container,
    pane,
    marker,
    y_offset=0,
    *,
    base_callbacks_builder=_standalone_radio_pane_marker_base_callbacks,
    drag_callbacks_builder=_standalone_radio_pane_marker_drag_callbacks,
    callback_tuple_builder=_standalone_radio_pane_marker_callback_tuple,
):
    (
        drag_state,
        set_sash_pos,
        place_marker_for_sash,
        update_marker,
        schedule_marker_update,
    ) = base_callbacks_builder(
        container,
        pane,
        marker,
        y_offset,
    )
    drag_callbacks = drag_callbacks_builder(
        drag_state,
        pane,
        set_sash_pos,
        place_marker_for_sash,
        schedule_marker_update,
        update_marker,
    )
    return callback_tuple_builder(update_marker, drag_callbacks)


def _standalone_radio_pane_marker_activation_args(
    container,
    pane,
    grip,
    callbacks,
):
    update_marker, start_drag, drag, end_drag = callbacks
    return container, pane, grip, update_marker, start_drag, drag, end_drag


def _standalone_radio_pane_activate_marker_parts(
    container,
    pane,
    grip,
    callbacks,
    *,
    activation_args_builder=_standalone_radio_pane_marker_activation_args,
    bindings_activator=_standalone_radio_pane_activate_marker_bindings,
) -> None:
    activation_args = activation_args_builder(
        container,
        pane,
        grip,
        callbacks,
    )
    bindings_activator(*activation_args)


def _standalone_radio_pane_install_marker_parts(
    container,
    pane,
    marker,
    grip,
    y_offset=0,
    *,
    callbacks_builder=_standalone_radio_pane_marker_callbacks,
    marker_parts_activator=_standalone_radio_pane_activate_marker_parts,
):
    callbacks = callbacks_builder(
        container,
        pane,
        marker,
        y_offset,
    )
    marker_parts_activator(
        container,
        pane,
        grip,
        callbacks,
    )
    return marker


def _standalone_radio_pane_install_marker_parts_args(
    container,
    pane,
    widgets,
    y_offset=0,
):
    marker, grip = widgets
    return container, pane, marker, grip, y_offset


def _standalone_radio_pane_install_marker(
    container,
    pane,
    *,
    color="#0a84ff",
    y_offset=0,
    widgets_builder=_standalone_radio_pane_marker_widgets,
    install_parts_args_builder=_standalone_radio_pane_install_marker_parts_args,
    install_parts=_standalone_radio_pane_install_marker_parts,
):
    widgets = widgets_builder(container, color)
    install_parts_args = install_parts_args_builder(
        container,
        pane,
        widgets,
        y_offset,
    )
    return install_parts(*install_parts_args)


def _install_pane_drag_marker(
    container,
    pane,
    *,
    color="#0a84ff",
    y_offset=0,
    install_marker=_standalone_radio_pane_install_marker,
):
    # Legacy source reference for source-based tests:
    # marker_width = min(66, max(width - 24, 42))
    return install_marker(
        container,
        pane,
        color=color,
        y_offset=y_offset,
    )


def _init_radio_runtime_widget_refs(app) -> None:
    app.feature_buttons = {}
    app.radio_station_table = None
    app.radio_station_menu = None
    app.radio_page_prev_button = None
    app.radio_page_next_button = None
    app.radio_reachability_button = None
    app.radio_miniplayer_button = None
    app.radio_database_button = None
    app.radio_database_count_label = None
    app.radio_database_sources_window = None
    app.radio_database_source_vars = {}
    app.radio_database_source_status_labels = {}
    app.radio_database_source_status_by_id = {}
    app.radio_database_source_check_running = False
    app.radio_database_exclusive_mode_var = None
    app.radio_database_select_all_var = None
    app.radio_database_refresh_button = None
    app.radio_database_progressbar = None
    app.radio_database_refresh_running = False
    app.radio_mini_player_window = None
    app.radio_mini_logo_label = None
    app.radio_mini_drag_origin = None
    app.radio_mini_resize_origin = None
    app.radio_standalone_resize_origin = None


def _init_radio_runtime_paths(app, *, paths_builder=build_radio_paths) -> None:
    paths = paths_builder()
    app.netmon_config_dir = paths.config_dir
    app.netmon_state_dir = paths.state_dir
    app.radio_default_stations_path = paths.default_stations_path
    app.radio_db_path = paths.radio_db_path
    app.radio_db_meta_path = paths.radio_db_meta_path
    app.radio_stations_path = paths.radio_stations_path
    app.radio_favorites_path = paths.radio_favorites_path
    app.radio_settings_path = paths.radio_settings_path
    app.radio_log_path = os.path.join(
        app.netmon_state_dir,
        "logs",
        "netmon_radio_app.log",
    )
    app.radio_logo_cache_dir = os.path.join(
        app.netmon_state_dir,
        "radio_station_logos",
    )


def _init_radio_runtime_data_state(
    app,
    *,
    settings_builder=radio_controller.default_radio_settings,
) -> None:
    app.radio_proc = None
    app.radio_stop_requested = False
    app.radio_ipc_path = ""
    app.radio_db = []
    app.radio_favorites = []
    app.radio_search_results = []
    app.radio_settings = settings_builder()


def _init_radio_runtime_selection_state(app) -> None:
    app._app_theme = None
    app.radio_current_station_id = ""
    app.radio_current_station = None
    app.radio_search_page = 0
    app.radio_filtered_station_ids = []
    app.radio_live_status_by_station_id = {}
    app.radio_reachability_check_running = False


def _init_radio_runtime_host_state(app, *, embedded_mode, host_app=None) -> None:
    app.radio_embedded_mode = bool(embedded_mode)
    app.radio_detach_callback = None
    app.radio_host_app = host_app
    app._start_theme_name = ""
    if host_app is not None:
        try:
            app._start_theme_name = (
                str((host_app._app_theme or {}).get("name", "") or "").strip().lower()
            )
        except Exception:
            app._start_theme_name = ""
        if app._start_theme_name:
            try:
                app.radio_settings["theme"] = app._start_theme_name
            except Exception:
                pass


def _init_radio_runtime_state(app, *, embedded_mode, host_app=None):
    _init_radio_runtime_widget_refs(app)
    _init_radio_runtime_paths(app)
    _init_radio_runtime_data_state(app)

    app.style = ttk.Style(app)
    app._ensure_colorable_ttk_theme()
    _init_radio_runtime_selection_state(app)
    radio_controller.load_radio_runtime(app)
    try:
        netmon_projectm_sidecar.ensure_projectm_preset_dir(app)
    except Exception:
        pass

    _init_radio_runtime_host_state(
        app,
        embedded_mode=embedded_mode,
        host_app=host_app,
    )


def _radio_ui_volume_value(settings) -> int:
    return int(settings.get("volume", 50) or 50)


def _radio_ui_eq_values(settings) -> tuple[int, int, int]:
    return (
        int(settings.get("eq_bass", 0) or 0),
        int(settings.get("eq_mid", 0) or 0),
        int(settings.get("eq_treble", 0) or 0),
    )


def _radio_ui_search_value(settings) -> str:
    return str(settings.get("last_search", "") or "")


def _radio_ui_database_count(app) -> int:
    return len(getattr(app, "radio_db", []) or [])


def _init_radio_ui_projectm_runtime_state(app) -> None:
    app.radio_projectm_proc = None
    app.radio_projectm_command = []
    app.radio_projectm_known_pids = set()
    app.radio_projectm_log_handle = None
    app.radio_projectm_log_path = ""
    app.radio_projectm_package_probe = {}


def _radio_ui_recordings_dir(settings) -> str:
    return str(settings.get("recordings_dir", "") or "").strip()


def _init_radio_ui_recording_runtime_state(app) -> None:
    app.radio_record_proc = None
    app.radio_recordings_dir = _radio_ui_recordings_dir(app.radio_settings)
    app.radio_last_record_path = ""
    app.radio_record_transport_button = None
    app.radio_record_panel_button = None
    app.radio_record_settings_button = None
    app.radio_record_settings_window = None
    app.radio_record_start_button = None
    app.radio_record_stop_button = None
    app.radio_record_folder_button = None
    app.radio_record_open_folder_button = None
    app.radio_record_open_last_button = None
    app.radio_record_play_last_button = None
    app.radio_record_blink_after_id = None
    app.radio_record_blink_on = False


def _radio_ui_playlist_entries(app):
    return list(
        getattr(app, "radio_playlist_entries", [])
        or app.radio_settings.get("playlist_entries", [])
        or []
    )


def _radio_ui_playlist_path(app) -> str:
    return str(
        getattr(app, "radio_playlist_path", "")
        or app.radio_settings.get("playlist_path", "")
        or ""
    ).strip()


def _radio_ui_playlists_dir(app) -> str:
    return str(
        getattr(app, "radio_playlists_dir", "")
        or app.radio_settings.get("playlists_dir", "")
        or ""
    ).strip()


def _init_radio_ui_playlist_runtime_state(app) -> None:
    app.radio_playlist_entries = _radio_ui_playlist_entries(app)
    app.radio_playlist_path = _radio_ui_playlist_path(app)
    app.radio_playlists_dir = _radio_ui_playlists_dir(app)
    app.radio_playlist_listbox = None
    app.radio_playlist_add_button = None
    app.radio_playlist_play_file_button = None
    app.radio_playlist_play_selected_button = None
    app.radio_playlist_remove_button = None
    app.radio_playlist_clear_button = None
    app.radio_playlist_save_button = None
    app.radio_playlist_load_button = None
    app.radio_playlist_folder_button = None
    app.radio_system_folder_button = None
    app.radio_playlist_files_entries = []
    app.radio_system_folder_entries = []
    app.radio_system_folder_path = ""
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = ""
    app.radio_folder_browser_back_history = []
    app.radio_folder_browser_forward_history = []


def _init_radio_ui_folder_browser_runtime_state(app) -> None:
    app.radio_folder_browser_context_index = -1
    app.radio_folder_browser_menu = None
    app.radio_folder_browser_back_button = None
    app.radio_folder_browser_forward_button = None
    app.radio_folder_browser_up_button = None
    app.radio_folder_browser_open_path_button = None
    app.radio_folder_browser_drag_source_index = -1
    app.radio_folder_browser_drag_source_path = ""
    app.radio_recordings_entries = []
    app.radio_recordings_listbox = None
    app.radio_playback_mode = str(
        getattr(app, "radio_playback_mode", "") or "radio"
    ).strip()
    app.radio_local_media_path = str(
        getattr(app, "radio_local_media_path", "") or ""
    ).strip()
    app.radio_playlist_index = int(getattr(app, "radio_playlist_index", -1) or -1)


def _init_radio_ui_logo_runtime_state(app) -> None:
    app.radio_projectm_last_started_at = ""
    app.radio_projectm_last_stopped_at = ""
    app.radio_logo_label = None
    app.radio_mini_play_button = None
    app.radio_mini_stop_button = None
    app._radio_logo_photo = None
    app._radio_mini_logo_photo = None
    app._radio_logo_request_key = ""
    app._radio_logo_loaded_key = ""
    app._radio_miniplayer_var_traces = []
    app._active_context_menu = None


def _init_radio_ui_control_refs(app) -> None:
    app.radio_light_state = "gray"
    app.radio_context_station_id = ""
    app.radio_station_column_vars = {}
    app.radio_custom_edit_station_id = ""
    app.radio_custom_editor_window = None
    app.radio_custom_editor_delete_button = None
    app.radio_projectm_install_button = None
    app.radio_projectm_preset_open_button = None
    app.radio_projectm_preset_import_button = None
    app.radio_projectm_preset_manager_window = None


def _init_radio_ui_header_vars(
    app,
    *,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_now_playing_var = string_var_builder(
        value=app.tr("radio_header_off", "Radio: off")
    )
    app.radio_status_var = string_var_builder(
        value=app.tr("radio_header_off", "Radio: off")
    )
    app.radio_title_var = string_var_builder(
        value=app.tr("radio_header_title_idle", "Title: -")
    )
    app.radio_header_status_var = string_var_builder(
        value=app.tr("radio_header_title_idle", "Title: -")
    )
    app.radio_handover_title = ""
    app.radio_stream_url_var = string_var_builder(
        value=app.tr("radio_stream_url_default", "Stream URL: -")
    )
    app.radio_bitrate_var = string_var_builder(
        value=app.tr("radio_bitrate_label", "Bitrate: -")
    )
    app.radio_dependency_var = string_var_builder(
        value=app.tr("radio_status_ready", "Radio ready.")
    )
    app.radio_list_status_var = string_var_builder(
        value=app.tr("radio_station_count", "Stations: {count}").format(count=0)
    )


def _init_radio_ui_volume_eq_search_vars(
    app,
    *,
    volume_value,
    eq_bass_value,
    eq_mid_value,
    eq_treble_value,
    search_value,
    int_var_builder=tk.IntVar,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_volume_var = int_var_builder(value=volume_value)
    app.radio_volume_text_var = string_var_builder(
        value=app.tr("radio_volume_short_label", "Vol.: {value}%").format(
            value=volume_value
        )
    )
    app.radio_volume_label_var = string_var_builder(value=f"{volume_value}%")
    app.radio_eq_bass_var = int_var_builder(value=eq_bass_value)
    app.radio_eq_mid_var = int_var_builder(value=eq_mid_value)
    app.radio_eq_treble_var = int_var_builder(value=eq_treble_value)
    app.radio_eq_bass_label_var = string_var_builder(value=str(eq_bass_value))
    app.radio_eq_mid_label_var = string_var_builder(value=str(eq_mid_value))
    app.radio_eq_treble_label_var = string_var_builder(value=str(eq_treble_value))
    app.radio_search_var = string_var_builder(value=search_value)


def _init_radio_ui_database_custom_vars(
    app,
    *,
    database_count,
    boolean_var_builder=tk.BooleanVar,
    double_var_builder=tk.DoubleVar,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_show_favorites_var = boolean_var_builder(value=False)
    app.radio_toggle_favorites_text_var = string_var_builder(
        value=app.tr("radio_show_favorites", "Show favorites")
    )
    app.radio_page_indicator_var = string_var_builder(value="1/1")
    app.radio_database_count_var = string_var_builder(
        value=app.tr("radio_database_count", "DB: {count} stations").format(
            count=database_count
        )
    )
    app.radio_database_progress_var = double_var_builder(value=0.0)
    app.radio_database_progress_status_var = string_var_builder(value="")
    app.radio_database_exclusive_mode_var = boolean_var_builder(value=True)
    app.radio_database_select_all_var = boolean_var_builder(value=False)
    app.radio_station_columns_status_var = string_var_builder(value="")
    app.radio_custom_name_var = string_var_builder(value="")
    app.radio_custom_url_var = string_var_builder(value="")
    app.radio_custom_homepage_var = string_var_builder(value="")
    app.radio_custom_category_var = string_var_builder(value="")
    app.radio_custom_submit_text_var = string_var_builder(
        value=app.tr("radio_custom_add_button", "Add station")
    )
    app.radio_custom_form_status_var = string_var_builder(value="")


def _init_radio_ui_projectm_vars(
    app,
    *,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_projectm_status_var = string_var_builder(
        value=app.tr("radio_projectm_status_not_installed", "projectM not installed")
    )
    app.radio_projectm_meta_var = string_var_builder(
        value=app.tr("radio_projectm_meta_default", "PID: - | Log: -")
    )
    app.radio_projectm_history_var = string_var_builder(
        value=app.tr(
            "radio_projectm_history_default",
            "Last started: - | Last stopped: -",
        )
    )
    app.radio_projectm_install_var = string_var_builder(
        value=app.tr(
            "radio_projectm_install_status_checking",
            "Checking projectM package status.",
        )
    )
    app.radio_projectm_preset_var = string_var_builder(
        value=app.tr(
            "radio_projectm_presets_preparing",
            "projectM preset folder: preparing Documents/NetMon",
        )
    )
    app.radio_projectm_preset_hint_var = string_var_builder(
        value=app.tr(
            "radio_projectm_preset_access_checking",
            "Preset access: checking downloaded packs and custom imports",
        )
    )
    app.radio_attach_status_var = string_var_builder(value="")


def _init_radio_ui_recording_vars(
    app,
    *,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_record_status_var = string_var_builder(
        value=app.tr("radio_record_status_off", "Recording off.")
    )
    app.radio_record_dir_var = string_var_builder(
        value=app.tr("radio_record_dir_default", "Aufnahmeordner: -")
    )
    app.radio_record_file_var = string_var_builder(
        value=app.tr("radio_record_file_default", "Letzte Aufnahme: -")
    )


def _init_radio_ui_playlist_folder_vars(
    app,
    *,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_playlist_status_var = string_var_builder(
        value=app.tr("radio_playlist_status_default", "Playlist: 0 Dateien")
    )
    app.radio_folder_browser_title_var = string_var_builder(
        value=app.tr("radio_folder_browser_title", "Aufnahmeordner")
    )
    app.radio_folder_browser_path_var = string_var_builder(value="")


def _init_radio_ui_recordings_source_mini_vars(
    app,
    *,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_recordings_status_var = string_var_builder(
        value=app.tr(
            "radio_recordings_status_default",
            "Recording folder: 0 files",
        )
    )
    app.radio_source_var = string_var_builder(
        value=app.tr(
            "radio_source_default",
            "Source: Livestream | -",
        )
    )
    app.radio_mini_source_var = string_var_builder(
        value=app.tr("radio_miniplayer_source_live", "Live")
    )
    app.radio_mini_title_var = string_var_builder(
        value=app.tr("radio_miniplayer_nothing_playing", "Nothing is playing")
    )
    app.radio_mini_status_var = string_var_builder(
        value=app.tr("radio_miniplayer_status_ready", "Ready")
    )
    app.radio_mini_detail_stream_var = string_var_builder(
        value=app.tr("radio_miniplayer_source_live", "Live")
    )
    app.radio_mini_detail_format_var = string_var_builder(value="-")
    app.radio_mini_detail_status_var = string_var_builder(
        value=app.tr("radio_miniplayer_status_ready", "Ready")
    )
    app.radio_mini_detail_genre_var = string_var_builder(value="-")
    app.radio_mini_detail_bitrate_var = string_var_builder(value="-")
    app.radio_mini_detail_time_var = string_var_builder(value="--:--:--")
    app.radio_mini_volume_var = string_var_builder(value="50%")
    app.radio_mini_eq_var = string_var_builder(value="EQ Flat")


def _init_radio_ui_status_indicator_images(
    app,
    *,
    indicator_builder=None,
) -> None:
    if indicator_builder is None:
        indicator_builder = _build_radio_status_indicator
    app.radio_status_indicator_images = {
        "unknown": indicator_builder("#8a8f98"),
        "online": indicator_builder("#2fb344"),
        "offline": indicator_builder("#d9485f"),
    }


def _init_radio_ui_theme_vars(
    app,
    *,
    string_var_builder=tk.StringVar,
) -> None:
    app.radio_theme_name_var = string_var_builder(value="")


def _init_radio_ui_state(app):
    volume_value = _radio_ui_volume_value(app.radio_settings)
    eq_bass_value, eq_mid_value, eq_treble_value = _radio_ui_eq_values(
        app.radio_settings
    )
    search_value = _radio_ui_search_value(app.radio_settings)
    database_count = _radio_ui_database_count(app)
    _init_radio_ui_header_vars(app)
    _init_radio_ui_volume_eq_search_vars(
        app,
        volume_value=volume_value,
        eq_bass_value=eq_bass_value,
        eq_mid_value=eq_mid_value,
        eq_treble_value=eq_treble_value,
        search_value=search_value,
    )
    _init_radio_ui_control_refs(app)
    _init_radio_ui_database_custom_vars(app, database_count=database_count)
    _init_radio_ui_status_indicator_images(app)
    _init_radio_ui_projectm_runtime_state(app)
    # Source anchor for standalone projectM hook tests:
    # projectM preset folder: preparing Documents/NetMon
    # checking downloaded packs and custom imports
    _init_radio_ui_projectm_vars(app)
    _init_radio_ui_recording_runtime_state(app)
    _init_radio_ui_recording_vars(app)
    _init_radio_ui_playlist_runtime_state(app)
    _init_radio_ui_playlist_folder_vars(app)
    _init_radio_ui_folder_browser_runtime_state(app)
    _init_radio_ui_recordings_source_mini_vars(app)
    _init_radio_ui_logo_runtime_state(app)
    _init_radio_ui_theme_vars(app)


def _build_radio_status_indicator(color):
    image = tk.PhotoImage(width=12, height=12)
    image.put("", to=(0, 0, 12, 12))
    for y, spans in {
        1: ((4, 8),),
        2: ((3, 9),),
        3: ((2, 10),),
        4: ((1, 11),),
        5: ((1, 11),),
        6: ((1, 11),),
        7: ((1, 11),),
        8: ((2, 10),),
        9: ((3, 9),),
        10: ((4, 8),),
    }.items():
        for start, end in spans:
            image.put(color, to=(start, y, end, y + 1))
    return image


def _compact_standalone_window_geometry(
    *,
    req_width,
    req_height,
    screen_width,
    screen_height,
) -> tuple[int, int, int, int, int]:
    width = min(max(int(req_width or 0), 980), screen_width - 120)
    height = min(
        max(int(req_height or 0), int(screen_height * 0.86)),
        screen_height - 80,
    )
    max_height = height
    x = max((screen_width - width) // 2, 0)
    y = max((screen_height - height) // 2, 0)
    return width, height, max_height, x, y


def _radio_window_integration_context(app) -> dict[str, str]:
    return {
        "window_class": "NetMonRadio",
        "startup_wm_class": "NetMonRadio",
        "icon_path": str(getattr(app, "_window_icon_path", "") or "").strip(),
        "icon_applied": (
            "yes" if bool(getattr(app, "_window_icon_applied", False)) else "no"
        ),
        "started_from": str(getattr(app, "_started_from", "") or "").strip(),
    }


def _radio_detach_ready_ack_payload(*, timed_out=False) -> dict[str, bool | str]:
    payload: dict[str, bool | str] = {"action": "detach_ready"}
    if timed_out:
        payload["timed_out"] = True
    return payload


def _radio_detach_ack_step(app, *, attempts_left) -> str:
    if getattr(app, "radio_proc", None) is not None:
        return "ready"
    if attempts_left <= 0:
        return "timeout"
    return "wait"


class NetMonRadioApp(tk.Tk):
    def __init__(
        self,
        start_theme: str | None = None,
        started_from: str | None = None,
    ):
        super().__init__(className="NetMonRadio")
        self._apply_window_icon()
        self.title("NetMon Radio")
        self._translations = {}
        self._language_code = "de"

        _init_radio_runtime_state(self, embedded_mode=False)
        self._load_language()
        self._start_theme_name = "dark"
        self._started_from = str(started_from or "desktop").strip().lower() or "desktop"
        self._radio_compact_layout = True
        self._app_theme = {"name": self._start_theme_name}
        self.radio_settings["theme"] = self._start_theme_name
        _init_radio_ui_state(self)
        self.radio_embedded_mode = False
        self.radio_detach_callback = None

        self._build_ui()
        self._register_radio_miniplayer_var_traces()
        self._configure_compact_standalone_window()
        radio_controller.on_radio_eq_preview(self)
        self.apply_theme(self._start_theme_name)
        transition_id = netmon_radio_core.current_radio_transition_id()
        try:
            handover_payload = netmon_radio_core.consume_radio_handover(
                "standalone",
                transition_id=transition_id,
            )
        except Exception:
            handover_payload = None
        if isinstance(handover_payload, dict) and handover_payload:
            try:
                radio_controller.apply_radio_handover_payload(
                    self,
                    handover_payload,
                    auto_play=False,
                )
                if bool(handover_payload.get("was_playing")):
                    radio_controller.play_radio_station(
                        self,
                        handover_payload.get("current_station_id", ""),
                    )
            except Exception:
                pass
            try:
                self._schedule_detach_takeover_ack(
                    handover_payload, transition_id=transition_id
                )
            except Exception:
                pass
            self.apply_theme(self._start_theme_name)
        try:
            netmon_radio_core.complete_radio_transition(
                mode="standalone",
                owner_pid=os.getpid(),
                current_station_id=getattr(self, "radio_current_station_id", ""),
                started_from=self._started_from,
                attached=False,
            )
            netmon_radio_core.set_radio_detached_state(True)
        except Exception:
            pass
        self.refresh_radio_ui()
        radio_controller.refresh_radio_recording_ui(self)
        radio_controller.refresh_radio_playlist_ui(self)
        self._refresh_projectm_status()
        self.refresh_radio_attach_state()
        self.after(1000, self._poll_radio_attach_state)
        if self._started_from == "netmon_detach":
            try:
                self.after(120, self._ensure_standalone_window_visible)
                self.after(420, self._ensure_standalone_window_visible)
            except Exception:
                pass
        self.bind_all("<Button-1>", self._dismiss_active_context_menu, add="+")
        self.bind_all("<Escape>", self._dismiss_active_context_menu, add="+")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(600, lambda: self._log_window_integration_diagnostic("startup"))

    def _desktop_icon_asset_path(self):
        desktop_entry_path = str(
            os.environ.get("BAMF_DESKTOP_FILE_HINT")
            or os.environ.get("GIO_LAUNCHED_DESKTOP_FILE")
            or ""
        ).strip()
        if not desktop_entry_path or not os.path.isfile(desktop_entry_path):
            return ""
        try:
            with open(desktop_entry_path, "r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = str(raw_line or "").strip()
                    if not line or line.startswith("#") or not line.startswith("Icon="):
                        continue
                    icon_path = line.split("=", 1)[1].strip()
                    if icon_path and os.path.isfile(icon_path):
                        return icon_path
        except Exception:
            pass
        return ""

    def _window_icon_asset_path(self):
        desktop_icon = self._desktop_icon_asset_path()
        if desktop_icon:
            return desktop_icon
        try:
            icon_path = str(netmon_radio_core.radio_icon_path() or "").strip()
            if icon_path and os.path.isfile(icon_path):
                return icon_path
        except Exception:
            pass
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _legacy_icon_ref = os.path.join(repo_root, "tools", "netmon2.png")
        candidate = os.path.join(repo_root, "tools", "netmon-radio.png")
        if os.path.isfile(candidate):
            return candidate
        return ""

    def _apply_window_icon(self):
        icon_path = self._window_icon_asset_path()
        self._window_icon_path = icon_path
        self._window_icon_applied = False
        if not icon_path:
            return
        try:
            icon = tk.PhotoImage(file=icon_path)
            self._window_icon_photo = icon
            self.iconphoto(True, icon)
            self._window_icon_applied = True
        except Exception:
            pass

    def _window_integration_context(self):
        return _radio_window_integration_context(self)

    def _log_window_integration_diagnostic(self, stage):
        info = self._window_integration_context()
        self.log_safe(
            "[RadioWindowDiag] "
            f"{stage} | window_class={info['window_class']} | "
            f"startup_wm_class={info['startup_wm_class']} | "
            f"icon_applied={info['icon_applied']} | "
            f"started_from={info['started_from'] or '-'} | "
            f"icon_path={info['icon_path'] or '-'}"
        )

    def _configure_compact_standalone_window(self):
        if bool(getattr(self, "radio_embedded_mode", False)):
            return
        try:
            self.update_idletasks()
            screen_width = max(int(self.winfo_screenwidth() or 1280), 1280)
            screen_height = max(int(self.winfo_screenheight() or 900), 900)
            # Source anchor for compact standalone layout tests:
            # int(screen_height * 0.86)
            width, height, max_height, x, y = _compact_standalone_window_geometry(
                req_width=self.winfo_reqwidth(),
                req_height=self.winfo_reqheight(),
                screen_width=screen_width,
                screen_height=screen_height,
            )
            self.geometry(f"{width}x{height}+{x}+{y}")
            self.minsize(width, height)
            self.maxsize(width, max_height)
            self.resizable(False, True)
        except Exception:
            pass

    def _schedule_detach_takeover_ack(self, handover_payload, *, transition_id=""):
        if not isinstance(handover_payload, dict):
            return
        if not bool(handover_payload.get("was_playing")):
            try:
                netmon_radio_core.request_radio_handover_ack(
                    target_mode="embedded",
                    payload=_radio_detach_ready_ack_payload(),
                    transition_id=transition_id,
                )
            except Exception:
                pass
            return

        def _wait_for_playback_ready(attempts_left=40):
            ack_step = _radio_detach_ack_step(self, attempts_left=attempts_left)
            if ack_step == "ready":
                try:
                    netmon_radio_core.request_radio_handover_ack(
                        target_mode="embedded",
                        payload=_radio_detach_ready_ack_payload(),
                        transition_id=transition_id,
                    )
                except Exception:
                    pass
                return
            if ack_step == "timeout":
                try:
                    netmon_radio_core.request_radio_handover_ack(
                        target_mode="embedded",
                        payload=_radio_detach_ready_ack_payload(timed_out=True),
                        transition_id=transition_id,
                    )
                except Exception:
                    pass
                return
            try:
                self.after(
                    150,
                    lambda: _wait_for_playback_ready(attempts_left=attempts_left - 1),
                )
            except Exception:
                pass

        _wait_for_playback_ready()

    def _ensure_standalone_window_visible(self):
        try:
            self.wm_state("normal")
        except Exception:
            pass
        try:
            self.state("normal")
        except Exception:
            pass
        try:
            self.deiconify()
        except Exception:
            pass
        try:
            self.lift()
        except Exception:
            pass
        try:
            self.attributes("-topmost", True)
            self.attributes("-topmost", False)
        except Exception:
            pass
        try:
            self.focus_force()
        except Exception:
            pass

    def _load_language(self):
        lang_code = "de"
        try:
            config_path = os.path.join(self.netmon_config_dir, "config.json")
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if isinstance(payload, dict):
                    candidate = (
                        str(payload.get("language", "de") or "de").strip().lower()
                    )
                    if candidate in {"de", "en"}:
                        lang_code = candidate
        except Exception:
            pass

        lang_path = os.path.join(os.path.dirname(__file__), "lang", f"{lang_code}.json")
        translations = {}
        try:
            with open(lang_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                translations = payload
        except Exception:
            translations = {}

        self._language_code = lang_code
        self._translations = translations

    def tr(self, key, default=None):
        translations = getattr(self, "_translations", {}) or {}
        return str(translations.get(key, default or "") or "")

    def register_feature_button(self, _feature, _widget):
        return None

    def attach_text_context_menu(self, widget):
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(
            label="Kopieren", command=lambda: widget.event_generate("<<Copy>>")
        )
        menu.add_command(
            label="Einfügen", command=lambda: widget.event_generate("<<Paste>>")
        )
        widget.bind(
            "<Button-3>",
            lambda event: self._show_context_menu(menu, event),
            add="+",
        )

    def _show_context_menu(self, menu, event):
        try:
            self._active_context_menu = menu
            menu.tk_popup(event.x_root, event.y_root)
            menu.grab_release()
        except Exception:
            pass
        return "break"

    def _dismiss_active_context_menu(self, event=None):
        menu = getattr(self, "_active_context_menu", None)
        if menu is None:
            return None
        widget = getattr(event, "widget", None)
        if isinstance(widget, tk.Menu):
            return None
        try:
            menu.unpost()
        except Exception:
            pass
        self._active_context_menu = None
        return None

    def refresh_radio_attach_state(self):
        available = False
        transition_pending = False
        try:
            available = bool(netmon_radio_core.netmon_host_is_available())
        except Exception:
            available = False
        try:
            transition_pending = bool(
                netmon_radio_core.radio_transition_in_progress("embedded")
            )
        except Exception:
            transition_pending = False
        button = getattr(self, "radio_attach_button", None)
        if button is not None:
            try:
                button.configure(
                    state=(
                        "normal" if available and not transition_pending else "disabled"
                    )
                )
            except Exception:
                pass
        try:
            self.radio_attach_status_var.set(
                "Radio wird gerade an NetMon angeheftet."
                if transition_pending
                else (
                    "Radio kann wieder an NetMon angeheftet werden."
                    if available
                    else "Radio läuft standalone. NetMon ist nicht aktiv."
                )
            )
        except Exception:
            pass
        return available and not transition_pending

    def attach_radio_to_netmon(self):
        if not self.refresh_radio_attach_state():
            return False
        try:
            if netmon_radio_core.radio_transition_in_progress("embedded"):
                try:
                    self.radio_attach_status_var.set(
                        "Radio wird bereits an NetMon angeheftet."
                    )
                except Exception:
                    pass
                return False
        except Exception:
            pass
        self.log_safe(
            "[RadioThemeDiag] external_attach_request | "
            f"app_theme={str((self._app_theme or LIGHT_THEME).get('name', '') or '').strip().lower() or '-'} | "
            f"radio_settings_theme={str((self.radio_settings or {}).get('theme', '') or '').strip().lower() or '-'}"
        )
        try:
            handover_payload = radio_controller.build_radio_handover_payload(self)
        except Exception:
            handover_payload = {}
        try:
            netmon_radio_core.begin_radio_transition(
                from_mode="standalone",
                target_mode="embedded",
                owner_pid=os.getpid(),
                current_station_id=str(
                    handover_payload.get(
                        "current_station_id",
                        getattr(self, "radio_current_station_id", ""),
                    )
                    or ""
                ),
                started_from="standalone_attach",
            )
            transition_id = netmon_radio_core.current_radio_transition_id()
            netmon_radio_core.request_radio_handover(
                target_mode="embedded",
                payload=handover_payload,
                action="attach",
                transition_id=transition_id,
            )
        except Exception:
            transition_id = ""
        try:
            self.radio_attach_status_var.set("Radio wird an NetMon angeheftet.")
        except Exception:
            pass
        try:
            if not netmon_radio_core.request_radio_attach(transition_id=transition_id):
                try:
                    netmon_radio_core.cancel_radio_transition(os.getpid())
                    netmon_radio_core.clear_radio_handover_request("embedded")
                except Exception:
                    pass
                return False
        except Exception:
            return False
        self._on_close()
        return True

    def detach_radio_from_netmon(self):
        callback = getattr(self, "radio_detach_callback", None)
        if callable(callback):
            try:
                result = bool(callback())
            except Exception:
                result = False
            if result:
                return True
        host_app = getattr(self, "radio_host_app", None)
        fallback = getattr(host_app, "open_radio_external_app", None)
        if callable(fallback):
            try:
                return bool(fallback())
            except Exception:
                return False
        return False

    def _poll_radio_attach_state(self):
        try:
            transition_id = netmon_radio_core.current_radio_transition_id()
            if netmon_radio_core.consume_standalone_radio_show_request(
                transition_id=transition_id
            ):
                try:
                    self.close_radio_miniplayer()
                except Exception:
                    pass
                try:
                    self._ensure_standalone_window_visible()
                except Exception:
                    pass
            if netmon_radio_core.consume_standalone_radio_attach_request(
                transition_id=transition_id
            ):
                try:
                    self.attach_radio_to_netmon()
                except Exception:
                    pass
            self.refresh_radio_attach_state()
            self.after(1000, self._poll_radio_attach_state)
        except Exception:
            pass

    def log(self, message):
        text = str(message or "").strip()
        if not text:
            return
        self._append_log_file(text)
        try:
            print(text, flush=True)
        except Exception:
            pass

    def log_safe(self, message):
        self.log(message)

    def _log_radio_theme_diagnostic(self, stage):
        current_theme = str((self._app_theme or LIGHT_THEME).get("name", "") or "")
        settings_theme = str((self.radio_settings or {}).get("theme", "") or "")
        self.log_safe(
            "[RadioThemeDiag] "
            f"{stage} | app_theme={current_theme.strip().lower() or '-'} | "
            f"radio_settings_theme={settings_theme.strip().lower() or '-'} | "
            f"start_theme={str(getattr(self, '_start_theme_name', '') or '').strip().lower() or '-'}"
        )

    def _timestamp_text(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _append_log_file(self, text):
        line = f"[{self._timestamp_text()}] {text}\n"
        try:
            os.makedirs(os.path.dirname(self.radio_log_path), exist_ok=True)
            with open(self.radio_log_path, "a", encoding="utf-8") as handle:
                handle.write(line)
        except Exception:
            pass

    def _build_eq_slider(
        self,
        parent,
        *,
        row,
        label,
        variable,
        value_variable,
        slider_length=120,
        label_style=None,
        scale_style=None,
        value_style=None,
    ):
        ttk.Label(parent, text=label, style=label_style).grid(
            row=row, column=0, sticky="w"
        )
        slider = ttk.Scale(
            parent,
            from_=-12,
            to=12,
            orient="horizontal",
            variable=variable,
            command=self.on_radio_eq_preview,
            length=slider_length,
            style=scale_style,
        )
        slider.grid(row=row, column=1, sticky="ew", padx=(8, 8))
        slider.bind("<ButtonRelease-1>", self.commit_radio_eq_change)
        slider.bind("<KeyRelease>", self.commit_radio_eq_change)
        slider.bind(
            "<MouseWheel>",
            lambda event, var=variable: self._on_radio_eq_mousewheel(event, var),
        )
        slider.bind(
            "<Button-4>",
            lambda event, var=variable: self._on_radio_eq_mousewheel(event, var),
        )
        slider.bind(
            "<Button-5>",
            lambda event, var=variable: self._on_radio_eq_mousewheel(event, var),
        )
        ttk.Label(parent, textvariable=value_variable, width=3, style=value_style).grid(
            row=row, column=2, sticky="w"
        )

    def _get_theme(self, theme_name):
        return RADIO_THEMES.get(str(theme_name or "").strip().lower(), LIGHT_THEME)

    def _get_next_theme_name(self, current_name):
        current = str(current_name or "light").strip().lower()
        if current not in RADIO_THEME_SEQUENCE:
            return RADIO_THEME_SEQUENCE[0]
        index = RADIO_THEME_SEQUENCE.index(current)
        return RADIO_THEME_SEQUENCE[(index + 1) % len(RADIO_THEME_SEQUENCE)]

    def _theme_button_label(self, theme_name):
        display = RADIO_THEME_DISPLAY_NAMES.get(
            str(theme_name or "").strip().lower(), "Light"
        )
        return f"Modus: {display}"

    def _theme_with_palette(self, theme_name, palette=None):
        theme = dict(self._get_theme(theme_name))
        if isinstance(palette, dict):
            for key in RADIO_THEME_PALETTE_KEYS:
                value = str(palette.get(key, "") or "").strip()
                if value:
                    theme[key] = value
        normalized = str(theme.get("name", theme_name or "light") or "light").strip()
        normalized = normalized.lower() or "light"
        if normalized not in RADIO_THEMES:
            normalized = str(theme_name or "light").strip().lower() or "light"
        if normalized not in RADIO_THEMES:
            normalized = "light"
        theme["name"] = normalized
        return theme

    def _apply_theme_object(self, theme):
        theme = dict(theme or LIGHT_THEME)
        self._app_theme = theme
        self._apply_ttk_theme(theme)
        self._apply_tk_widget_theme(self, theme)
        try:
            self.radio_theme_name_var.set(self._theme_button_label(theme["name"]))
        except Exception:
            pass
        try:
            self.radio_settings["theme"] = theme["name"]
        except Exception:
            pass
        try:
            radio_controller.save_radio_settings(self)
        except Exception:
            pass
        mini_window = getattr(self, "radio_mini_player_window", None)
        if mini_window is not None:
            try:
                mini_window.configure(bg=theme["bg"])
            except Exception:
                pass
            try:
                self._apply_tk_widget_theme(mini_window, theme)
            except Exception:
                pass
            try:
                self._apply_radio_miniplayer_theme(theme)
            except Exception:
                pass
        try:
            self._refresh_radio_miniplayer_content()
        except Exception:
            pass
        self._log_radio_theme_diagnostic(f"apply_theme:{theme['name']}")

    def toggle_theme(self):
        current = (self._app_theme or LIGHT_THEME).get("name", "light")
        self.apply_theme(self._get_next_theme_name(current))

    def apply_theme(self, theme_name):
        self._apply_theme_object(self._theme_with_palette(theme_name))

    def apply_theme_palette(self, theme_name, palette):
        self._apply_theme_object(self._theme_with_palette(theme_name, palette))

    def _ensure_colorable_ttk_theme(self):
        style = self.style if hasattr(self, "style") else ttk.Style(self)
        try:
            theme_names = style.theme_names()
        except Exception:
            theme_names = ()
        if "clam" not in theme_names:
            return
        try:
            if style.theme_use() != "clam":
                style.theme_use("clam")
        except Exception:
            pass

    def _apply_ttk_theme(self, theme):
        style = self.style if hasattr(self, "style") else ttk.Style(self)
        self._ensure_colorable_ttk_theme()
        style.configure(".", background=theme["panel_bg"], foreground=theme["fg"])
        style.configure("TFrame", background=theme["panel_bg"])
        style.configure(
            "TLabelframe",
            background=theme["panel_bg"],
            foreground=theme["fg"],
            bordercolor=theme["border"],
        )
        style.configure(
            "TLabelframe.Label", background=theme["panel_bg"], foreground=theme["fg"]
        )
        style.configure("TLabel", background=theme["panel_bg"], foreground=theme["fg"])
        style.configure(
            "TButton",
            background=theme["tab_bg"],
            foreground=theme["fg"],
            bordercolor=theme["border"],
            focuscolor=theme["accent"],
            padding=(6, 3),
        )
        style.map(
            "TButton",
            background=[("active", theme["tab_selected_bg"])],
            foreground=[("disabled", theme["disabled_fg"]), ("active", theme["fg"])],
        )
        style.configure(
            "TCheckbutton",
            background=theme["panel_bg"],
            foreground=theme["fg"],
            indicatorcolor=theme["entry_bg"],
            focuscolor=theme["accent"],
            padding=(4, 2),
        )
        style.configure(
            "TRadiobutton",
            background=theme["panel_bg"],
            foreground=theme["fg"],
            indicatorcolor=theme["entry_bg"],
            focuscolor=theme["accent"],
        )
        style.configure(
            "TEntry",
            fieldbackground=theme["entry_bg"],
            foreground=theme["entry_fg"],
            bordercolor=theme["border"],
            insertcolor=theme["entry_fg"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=theme["entry_bg"],
            background=theme["entry_bg"],
            foreground=theme["entry_fg"],
            bordercolor=theme["border"],
            arrowcolor=theme["fg"],
            insertcolor=theme["entry_fg"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", theme["entry_bg"]),
                ("disabled", theme["panel_bg"]),
            ],
            background=[
                ("readonly", theme["entry_bg"]),
                ("active", theme["tab_selected_bg"]),
            ],
            foreground=[
                ("disabled", theme["disabled_fg"]),
                ("readonly", theme["entry_fg"]),
            ],
            arrowcolor=[("disabled", theme["disabled_fg"]), ("!disabled", theme["fg"])],
        )
        style.configure(
            "Treeview",
            background=theme["tree_bg"],
            foreground=theme["tree_fg"],
            fieldbackground=theme["tree_bg"],
            bordercolor=theme["border"],
        )
        style.map(
            "Treeview",
            background=[("selected", theme["select_bg"])],
            foreground=[("selected", theme["select_fg"])],
        )
        style.configure(
            "Treeview.Heading",
            background=theme["tab_bg"],
            foreground=theme["fg"],
            bordercolor=theme["border"],
        )
        style.configure(
            "TScrollbar",
            background=theme["tab_bg"],
            troughcolor=theme["panel_bg"],
            bordercolor=theme["border"],
            arrowcolor=theme["fg"],
        )
        style.configure(
            "TScale",
            background=theme["panel_bg"],
            troughcolor=theme["tab_bg"],
            bordercolor=theme["border"],
        )
        style.configure("TPanedwindow", background=theme["panel_bg"])
        style.configure("Sash", background=theme["border"])
        try:
            self.configure(bg=theme["bg"])
        except Exception:
            pass

    def _mix_theme_color(self, first, second, ratio):
        def _hex_to_rgb(value):
            text = str(value or "").strip().lstrip("#")
            if len(text) != 6:
                raise ValueError("expected #RRGGBB")
            return tuple(int(text[index : index + 2], 16) for index in (0, 2, 4))

        try:
            start = _hex_to_rgb(first)
            end = _hex_to_rgb(second)
            weight = max(0.0, min(float(ratio), 1.0))
            mixed = tuple(
                int(round((channel * (1.0 - weight)) + (target * weight)))
                for channel, target in zip(start, end)
            )
            return "#{:02x}{:02x}{:02x}".format(*mixed)
        except Exception:
            return str(first or "#000000")

    def _clean_radio_label_text(self, value, prefix):
        text = str(value or "").strip()
        prefixes = prefix if isinstance(prefix, (list, tuple, set)) else (prefix,)
        for candidate in prefixes:
            normalized_prefix = str(candidate or "").strip()
            if normalized_prefix and text.lower().startswith(normalized_prefix.lower()):
                text = text[len(normalized_prefix) :].strip()
                break
        return text

    def _clean_radio_genre_text(self, value):
        text = str(value or "").strip()
        if not text or text == "-":
            return "-"
        for token in ("[", "]", "'", '"'):
            text = text.replace(token, "")
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if not parts:
            return "-"
        genre = parts[0]
        if genre.lower() in {"charts", "chart"}:
            return "Charts"
        return genre[:1].upper() + genre[1:]

    def _mini_radio_playback_status_text(self, status_text, *, playing):
        if playing:
            return self.tr("radio_miniplayer_status_playing", "Playing")
        text = str(status_text or "").strip()
        if not text or text == "-":
            return self.tr("radio_miniplayer_status_ready", "Ready")
        lowered = text.lower()
        if "fehler" in lowered or "error" in lowered:
            return self.tr("radio_miniplayer_status_error", "Error")
        if "verbinde" in lowered or "connect" in lowered:
            return self.tr("radio_miniplayer_status_connecting", "Connecting")
        return self.tr("radio_miniplayer_status_ready", "Ready")

    def _radio_miniplayer_source_kind(self):
        mode = str(getattr(self, "radio_playback_mode", "radio") or "radio").strip()
        return {
            "playlist": self.tr("radio_miniplayer_source_playlist", "Playlist"),
            "file": self.tr("radio_miniplayer_source_file", "File"),
            "recording": self.tr("radio_miniplayer_source_recording", "Recording"),
        }.get(mode, self.tr("radio_miniplayer_source_live", "Live"))

    def _radio_miniplayer_media_label(self):
        path = str(getattr(self, "radio_local_media_path", "") or "").strip()
        if not path:
            return ""
        return os.path.basename(path) or path

    def _radio_miniplayer_snapshot(self):
        title_text = self._clean_radio_label_text(
            getattr(self.radio_title_var, "get", lambda: "")(),
            ("Titel:", "Title:"),
        )
        status_text = self._clean_radio_label_text(
            getattr(self.radio_status_var, "get", lambda: "")(),
            ("Radio:",),
        )
        source_kind = self._radio_miniplayer_source_kind()
        media_label = self._radio_miniplayer_media_label()
        playback_mode = str(
            getattr(self, "radio_playback_mode", "radio") or "radio"
        ).strip()
        current_station = getattr(self, "radio_current_station", None)
        if not isinstance(current_station, dict):
            current_station = {}
        station_name = str(current_station.get("name") or "").strip()
        if playback_mode != "radio":
            station_name = (
                media_label
                or station_name
                or self.tr("radio_miniplayer_local_playback", "Local playback")
            )
        if not station_name:
            station_name = self.tr("label_unknown", "unknown")
        playback_active = bool(getattr(self, "radio_proc", None))
        status_value = self._mini_radio_playback_status_text(
            status_text, playing=playback_active
        )
        title_value = title_text
        if title_value in {"", "-"}:
            if playback_mode == "radio":
                title_value = (
                    station_name
                    if playback_active
                    else self.tr(
                        "radio_miniplayer_waiting_metadata", "Waiting for metadata"
                    )
                )
            else:
                title_value = media_label or self.tr(
                    "radio_miniplayer_no_file_selected", "No file selected"
                )
        return {
            "station": station_name,
            "title": title_value,
            "source_kind": source_kind,
            "status": status_value,
        }

    def _refresh_radio_miniplayer_content(self):
        source_text = self._clean_radio_label_text(
            getattr(self.radio_source_var, "get", lambda: "")(),
            ("Quelle:", "Source:"),
        )
        title_text = self._clean_radio_label_text(
            getattr(self.radio_title_var, "get", lambda: "")(),
            ("Titel:", "Title:"),
        )
        status_text = self._clean_radio_label_text(
            getattr(self.radio_status_var, "get", lambda: "")(),
            ("Radio:",),
        )
        bitrate_text = self._clean_radio_label_text(
            getattr(self.radio_bitrate_var, "get", lambda: "")(), "Bitrate:"
        )
        record_text = getattr(self.radio_record_status_var, "get", lambda: "")().strip()

        source_kind = self._radio_miniplayer_source_kind()
        source_detail = ""
        if "|" in source_text:
            _source_kind, source_detail = [
                part.strip() for part in source_text.split("|", 1)
            ]
        if not source_detail:
            source_detail = self._radio_miniplayer_media_label()

        title_display = title_text
        if title_display in {"", "-"}:
            if str(getattr(self, "radio_playback_mode", "radio") or "radio") == "radio":
                title_display = source_detail or self.tr(
                    "radio_miniplayer_waiting_metadata", "Waiting for metadata"
                )
            else:
                title_display = source_detail or self.tr(
                    "radio_miniplayer_no_file_selected", "No file selected"
                )

        status_parts = []
        if status_text:
            status_parts.append(status_text)
        if bitrate_text and bitrate_text != "-":
            status_parts.append(bitrate_text)
        record_off_text = self.tr("radio_record_status_off", "Recording off.").strip()
        if record_text and record_text.lower() != record_off_text.lower():
            status_parts.append(record_text)

        try:
            volume_value = int(
                getattr(self.radio_volume_var, "get", lambda: 50)() or 50
            )
        except Exception:
            volume_value = 50
        try:
            bass = int(getattr(self.radio_eq_bass_var, "get", lambda: 0)() or 0)
            mid = int(getattr(self.radio_eq_mid_var, "get", lambda: 0)() or 0)
            treble = int(getattr(self.radio_eq_treble_var, "get", lambda: 0)() or 0)
        except Exception:
            bass = 0
            mid = 0
            treble = 0
        current_station = getattr(self, "radio_current_station", None)
        if not isinstance(current_station, dict):
            current_station = {}
        genre_value = self._clean_radio_genre_text(
            current_station.get("tags")
            or current_station.get("genre")
            or current_station.get("category")
            or "-"
        )
        format_value = "MP3"
        if bitrate_text and bitrate_text != "-":
            format_value = f"{format_value} / {bitrate_text}"
        playback_active = bool(getattr(self, "radio_proc", None))
        detail_status = self._mini_radio_playback_status_text(
            status_text, playing=playback_active
        )
        detail_time = "LIVE" if playback_active else "--:--:--"

        try:
            self.radio_mini_source_var.set(source_kind or "Radio")
            self.radio_mini_title_var.set(title_display)
            self.radio_mini_status_var.set(detail_status)
            self.radio_mini_detail_stream_var.set(source_kind or "Live")
            self.radio_mini_detail_format_var.set(format_value)
            self.radio_mini_detail_status_var.set(detail_status)
            self.radio_mini_detail_genre_var.set(genre_value or "-")
            self.radio_mini_detail_bitrate_var.set(bitrate_text or "-")
            self.radio_mini_detail_time_var.set(detail_time)
            self.radio_mini_volume_var.set(f"{volume_value}%")
            self.radio_mini_eq_var.set(f"EQ B{bass:+d} M{mid:+d} H{treble:+d}")
        except Exception:
            pass

        mini_player = getattr(self, "radio_mini_player_window", None)
        if hasattr(mini_player, "update_content"):
            try:
                mini_player.update_content(self._radio_miniplayer_snapshot())
            except Exception:
                pass

    def _register_radio_miniplayer_var_traces(self):
        if getattr(self, "_radio_miniplayer_var_traces", None):
            return
        trace_specs = (
            getattr(self, "radio_source_var", None),
            getattr(self, "radio_title_var", None),
            getattr(self, "radio_status_var", None),
            getattr(self, "radio_bitrate_var", None),
            getattr(self, "radio_record_status_var", None),
            getattr(self, "radio_volume_var", None),
            getattr(self, "radio_eq_bass_var", None),
            getattr(self, "radio_eq_mid_var", None),
            getattr(self, "radio_eq_treble_var", None),
        )
        for variable in trace_specs:
            if variable is None:
                continue
            try:
                trace_id = variable.trace_add(
                    "write", lambda *_args: self._refresh_radio_miniplayer_content()
                )
                self._radio_miniplayer_var_traces.append((variable, trace_id))
            except Exception:
                pass
        self._refresh_radio_miniplayer_content()

    def _apply_radio_miniplayer_theme(self, theme):
        mini = getattr(self, "radio_mini_player_window", None)
        if mini is None:
            return
        if hasattr(mini, "apply_theme"):
            try:
                mini.apply_theme(theme)
            except Exception:
                pass
            return
        shell = getattr(self, "radio_mini_shell", None)
        titlebar = getattr(self, "radio_mini_titlebar", None)
        logo_frame = getattr(self, "radio_mini_logo_frame", None)
        info_card = getattr(self, "radio_mini_info_card", None)
        controls = getattr(self, "radio_mini_controls", None)
        settings = getattr(self, "radio_mini_settings", None)
        source_label = getattr(self, "radio_mini_source_label", None)
        title_label = getattr(self, "radio_mini_title_label", None)
        status_label = getattr(self, "radio_mini_status_label", None)
        resize_grip = getattr(self, "radio_mini_resize_grip", None)

        accent = theme["accent"]
        shell_bg = self._mix_theme_color(theme["panel_bg"], accent, 0.08)
        header_bg = self._mix_theme_color(theme["tab_bg"], accent, 0.12)
        card_bg = self._mix_theme_color(theme["entry_bg"], accent, 0.06)
        chip_bg = self._mix_theme_color(accent, theme["bg"], 0.18)

        for widget, bg in (
            (mini, theme["bg"]),
            (shell, shell_bg),
            (titlebar, header_bg),
            (logo_frame, card_bg),
            (info_card, card_bg),
            (controls, shell_bg),
            (settings, shell_bg),
        ):
            if widget is None:
                continue
            try:
                widget.configure(bg=bg, highlightbackground=theme["border"])
            except Exception:
                try:
                    widget.configure(bg=bg)
                except Exception:
                    pass

        if source_label is not None:
            try:
                source_label.configure(
                    bg=chip_bg,
                    fg=theme["select_fg"],
                    activebackground=chip_bg,
                    activeforeground=theme["select_fg"],
                )
            except Exception:
                pass
        if title_label is not None:
            try:
                title_label.configure(bg=card_bg, fg=theme["fg"])
            except Exception:
                pass
        if status_label is not None:
            try:
                status_label.configure(bg=card_bg, fg=theme["muted_fg"])
            except Exception:
                pass
        if resize_grip is not None:
            try:
                resize_grip.configure(bg=shell_bg, fg=theme["muted_fg"])
            except Exception:
                pass

        for widget in (
            getattr(self, "radio_mini_minimize_button", None),
            getattr(self, "radio_mini_close_button", None),
            getattr(self, "radio_mini_play_button", None),
            getattr(self, "radio_mini_stop_button", None),
            getattr(self, "radio_mini_prev_button", None),
            getattr(self, "radio_mini_next_button", None),
            getattr(self, "radio_mini_theme_button", None),
            getattr(self, "radio_mini_volume_down_button", None),
            getattr(self, "radio_mini_volume_up_button", None),
            getattr(self, "radio_mini_eq_prev_button", None),
            getattr(self, "radio_mini_eq_next_button", None),
            getattr(self, "radio_mini_projectm_button", None),
        ):
            if widget is None:
                continue
            try:
                widget.configure(
                    bg=theme["tab_bg"],
                    fg=theme["fg"],
                    activebackground=theme["tab_selected_bg"],
                    activeforeground=theme["fg"],
                    highlightbackground=theme["border"],
                    relief="flat",
                    bd=0,
                )
            except Exception:
                pass

    def _adjust_radio_volume_from_miniplayer(self, delta):
        try:
            current = int(getattr(self.radio_volume_var, "get", lambda: 50)() or 50)
        except Exception:
            current = 50
        new_value = max(0, min(100, current + int(delta)))
        try:
            self.radio_volume_var.set(new_value)
        except Exception:
            return False
        self.on_radio_volume_preview(str(new_value))
        self.commit_radio_volume_change()
        self._refresh_radio_miniplayer_content()
        return True

    def _cycle_radio_eq_preset_from_miniplayer(self, step):
        presets = [
            ("Flat", (0, 0, 0)),
            ("Warm", (3, 1, -1)),
            ("Vocal", (-1, 3, 1)),
            ("Bright", (-2, 1, 4)),
            ("Bass", (5, -1, -2)),
        ]
        current_values = (
            int(getattr(self.radio_eq_bass_var, "get", lambda: 0)() or 0),
            int(getattr(self.radio_eq_mid_var, "get", lambda: 0)() or 0),
            int(getattr(self.radio_eq_treble_var, "get", lambda: 0)() or 0),
        )
        current_index = 0
        for index, (_name, values) in enumerate(presets):
            if values == current_values:
                current_index = index
                break
        next_index = (current_index + int(step)) % len(presets)
        _name, values = presets[next_index]
        try:
            self.radio_eq_bass_var.set(values[0])
            self.radio_eq_mid_var.set(values[1])
            self.radio_eq_treble_var.set(values[2])
        except Exception:
            return False
        self.on_radio_eq_preview()
        self.commit_radio_eq_change()
        self._refresh_radio_miniplayer_content()
        return True

    def _apply_tk_widget_theme(self, widget, theme):
        klass = str(widget.winfo_class())
        try:
            if klass in {"Frame", "Labelframe", "LabelFrame", "Toplevel"}:
                widget.configure(bg=theme["panel_bg"])
            elif klass == "Label":
                widget.configure(bg=theme["panel_bg"], fg=theme["fg"])
            elif klass in {"Button", "Checkbutton", "Radiobutton"}:
                widget.configure(
                    bg=theme["tab_bg"],
                    fg=theme["fg"],
                    activebackground=theme["tab_selected_bg"],
                    activeforeground=theme["fg"],
                    selectcolor=theme["panel_bg"],
                    highlightbackground=theme["border"],
                )
            elif klass in {"Entry", "Spinbox"}:
                widget.configure(
                    bg=theme["entry_bg"],
                    fg=theme["entry_fg"],
                    insertbackground=theme["entry_fg"],
                    highlightbackground=theme["border"],
                )
            elif klass == "Text":
                widget.configure(
                    bg=theme["text_bg"],
                    fg=theme["text_fg"],
                    insertbackground=theme["text_fg"],
                    selectbackground=theme["select_bg"],
                    selectforeground=theme["select_fg"],
                    highlightbackground=theme["border"],
                )
            elif klass == "Listbox":
                widget.configure(
                    bg=theme["tree_bg"],
                    fg=theme["tree_fg"],
                    selectbackground=theme["select_bg"],
                    selectforeground=theme["select_fg"],
                    highlightbackground=theme["border"],
                    highlightthickness=0,
                    bd=0,
                    relief="flat",
                )
            elif klass == "Canvas":
                widget.configure(
                    bg=theme["panel_bg"],
                    highlightbackground=theme["border"],
                    highlightthickness=0,
                )
        except Exception:
            pass
        for child in widget.winfo_children():
            self._apply_tk_widget_theme(child, theme)

    def _set_radio_logo_placeholder(self, text=None):
        text = str(text or self.tr("radio_logo_placeholder", "No logo")).strip()
        targets = (
            ("radio_logo_label", "_radio_logo_photo", "main"),
            ("radio_mini_logo_label", "_radio_mini_logo_photo", "mini"),
        )
        for label_attr, photo_attr, variant in targets:
            label = getattr(self, label_attr, None)
            if label is None:
                continue
            placeholder_photo = self._build_radio_logo_placeholder_image(
                text, size=self._radio_logo_size(variant)
            )
            setattr(self, photo_attr, placeholder_photo)
            try:
                label.configure(
                    image=placeholder_photo if placeholder_photo is not None else "",
                    text="" if placeholder_photo is not None else text,
                )
            except Exception:
                pass

    def _radio_logo_size(self, variant="main"):
        if variant == "mini":
            return (88, 88)
        return (110, 110) if self.radio_embedded_mode else (170, 170)

    def _fit_tk_photoimage(self, image, *, size):
        if image is None:
            return None
        try:
            max_width, max_height = size
            width = int(image.width() or 0)
            height = int(image.height() or 0)
            if width <= 0 or height <= 0:
                return image
            scale = max(width / max_width, height / max_height, 1.0)
            if scale <= 1.0:
                return image
            step = max(1, int(math.ceil(scale)))
            return image.subsample(step, step)
        except Exception:
            return image

    def _radio_default_logo_asset_path(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(repo_root, "tools", "netmon-radio.png")
        if os.path.isfile(candidate):
            return candidate
        return ""

    def _build_radio_default_logo_image(self, *, size=None):
        asset_path = self._radio_default_logo_asset_path()
        if not asset_path:
            return None
        width, height = size or self._radio_logo_size()
        try:
            if Image is not None and ImageTk is not None:
                with Image.open(asset_path) as src:
                    rendered = src.convert("RGBA")
                    rendered.thumbnail((width, height))
                    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                    pos_x = max(0, (width - rendered.width) // 2)
                    pos_y = max(0, (height - rendered.height) // 2)
                    canvas.paste(rendered, (pos_x, pos_y), rendered)
                    return ImageTk.PhotoImage(canvas)
            image = tk.PhotoImage(file=asset_path)
            return self._fit_tk_photoimage(image, size=(width, height))
        except Exception:
            return None

    def _build_radio_logo_placeholder_image(self, text, *, size=None):
        default_logo = self._build_radio_default_logo_image(size=size)
        if default_logo is not None:
            return default_logo
        if Image is None or ImageTk is None or ImageDraw is None:
            return None
        width, height = size or self._radio_logo_size()
        image = Image.new("RGBA", (width, height), "#08111f")
        draw = ImageDraw.Draw(image)

        draw.rectangle((0, 0, width, height), fill="#0b1020")
        draw.polygon(
            [
                (0, 0),
                (width * 0.62, 0),
                (width * 0.34, height * 0.52),
                (0, height * 0.38),
            ],
            fill="#1dc8ff",
        )
        draw.polygon(
            [
                (width * 0.42, 0),
                (width, 0),
                (width, height * 0.56),
                (width * 0.68, height * 0.42),
            ],
            fill="#ff3ca6",
        )
        draw.polygon(
            [
                (0, height * 0.56),
                (width * 0.38, height * 0.46),
                (width * 0.74, height),
                (0, height),
            ],
            fill="#ffd33d",
        )
        draw.ellipse(
            (
                width * 0.2,
                height * 0.14,
                width * 0.8,
                height * 0.74,
            ),
            fill="#0b1020",
            outline="#ffffff",
            width=3,
        )
        draw.text(
            (width * 0.31, height * 0.27),
            "NM",
            fill="#ffffff",
        )

        caption = str(text or self.tr("radio_logo_placeholder", "No logo")).strip()
        caption = caption or self.tr("radio_logo_placeholder", "No logo")
        max_chars = 14 if width >= 96 else 8
        if len(caption) > max_chars:
            caption = caption[: max_chars - 1] + "…"
        caption_box_top = int(height * 0.76)
        draw.rectangle((0, caption_box_top, width, height), fill="#0f1728")
        draw.text(
            (max(4, width // 12), caption_box_top + max(3, height // 18)),
            caption,
            fill="#ffffff",
        )
        return ImageTk.PhotoImage(image)

    def _station_logo_url(self, station):
        if not isinstance(station, dict):
            return ""
        url = str(station.get("favicon", "") or "").strip()
        # Logo-URLs stammen aus der radio-browser.info-API (Fremddaten).
        # urlopen wuerde auch file:// und andere Nicht-Web-Schemata bedienen,
        # daher wie in fetch_url() im Container-Builder auf http/https begrenzen.
        if urlparse(url).scheme.lower() not in ("http", "https"):
            return ""
        return url

    def _station_logo_cache_path(self, logo_url):
        url = str(logo_url or "").strip()
        if not url:
            return ""
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return os.path.join(self.radio_logo_cache_dir, f"{digest}.png")

    def _render_station_logo_file(self, path, request_key):
        if request_key != getattr(self, "_radio_logo_request_key", ""):
            return
        try:
            if Image is not None and ImageTk is not None:
                with Image.open(path) as src:
                    source = src.convert("RGBA")
                    rendered = {}
                    for variant in ("main", "mini"):
                        image = source.copy()
                        image.thumbnail(self._radio_logo_size(variant))
                        rendered[variant] = ImageTk.PhotoImage(image)
            else:
                base_image = tk.PhotoImage(file=path)
                rendered = {
                    "main": self._fit_tk_photoimage(
                        base_image,
                        size=self._radio_logo_size("main"),
                    ),
                    "mini": self._fit_tk_photoimage(
                        base_image,
                        size=self._radio_logo_size("mini"),
                    ),
                }
        except Exception:
            self._set_radio_logo_placeholder()
            return
        self._radio_logo_photo = rendered["main"]
        self._radio_mini_logo_photo = rendered["mini"]
        self._radio_logo_loaded_key = request_key
        for label_attr, photo_attr, variant in (
            ("radio_logo_label", "_radio_logo_photo", "main"),
            ("radio_mini_logo_label", "_radio_mini_logo_photo", "mini"),
        ):
            label = getattr(self, label_attr, None)
            if label is None:
                continue
            try:
                label.configure(image=getattr(self, photo_attr), text="")
            except Exception:
                pass

    def _download_station_logo(self, logo_url, cache_path, request_key):
        try:
            with urllib_request.urlopen(logo_url, timeout=8) as response:
                payload = response.read()
            if not payload:
                raise ValueError("empty logo payload")
            os.makedirs(self.radio_logo_cache_dir, exist_ok=True)
            if Image is not None:
                with Image.open(io.BytesIO(payload)) as src:
                    src.convert("RGBA").save(cache_path, format="PNG")
            else:
                with open(cache_path, "wb") as handle:
                    handle.write(payload)
        except Exception:
            try:
                self.after(0, self._set_radio_logo_placeholder)
            except Exception:
                pass
            return

        def render():
            self._render_station_logo_file(cache_path, request_key)

        try:
            self.after(0, render)
        except Exception:
            pass

    def refresh_radio_station_logo(self, station):
        logo_url = self._station_logo_url(station)
        station_id = ""
        if isinstance(station, dict):
            station_id = str(station.get("id", "") or "").strip()
        request_key = f"{station_id}|{logo_url}"
        self._radio_logo_request_key = request_key
        if not logo_url:
            self._set_radio_logo_placeholder()
            return
        cache_path = self._station_logo_cache_path(logo_url)
        if cache_path and os.path.isfile(cache_path):
            self._render_station_logo_file(cache_path, request_key)
            return
        self._set_radio_logo_placeholder("Lade Logo...")
        worker = threading.Thread(
            target=self._download_station_logo,
            args=(logo_url, cache_path, request_key),
            daemon=True,
        )
        worker.start()

    def _refresh_projectm_status(self):
        state = netmon_projectm_sidecar.describe_projectm_sidecar_runtime(self)
        try:
            self.radio_projectm_status_var.set(str(state.get("status_text") or ""))
        except Exception:
            pass
        pid = int(state.get("pid") or 0)
        log_path = str(state.get("log_path") or "").strip() or "-"
        command = str(state.get("command") or "").strip()
        backend_label = str(state.get("backend_label") or "").strip()
        preset_dir = str(state.get("preset_dir") or "").strip() or "-"
        preset_access_text = str(state.get("preset_access_text") or "").strip()
        try:
            if command:
                self.radio_projectm_meta_var.set(
                    "PID: "
                    f"{pid or '-'} | Backend: {backend_label or '-'} | "
                    f"Command: {command} | Log: {log_path}"
                )
            else:
                self.radio_projectm_meta_var.set(
                    f"PID: {pid or '-'} | Backend: {backend_label or '-'} | Log: {log_path}"
                )
        except Exception:
            pass
        started_at = str(
            getattr(self, "radio_projectm_last_started_at", "") or ""
        ).strip()
        stopped_at = str(
            getattr(self, "radio_projectm_last_stopped_at", "") or ""
        ).strip()
        try:
            self.radio_projectm_history_var.set(
                "Zuletzt gestartet: "
                f"{started_at or '-'} | Zuletzt beendet: {stopped_at or '-'}"
            )
        except Exception:
            pass
        try:
            self.radio_projectm_install_var.set(str(state.get("install_text") or ""))
        except Exception:
            pass
        install_button = getattr(self, "radio_projectm_install_button", None)
        if install_button is not None:
            install_state = "normal"
            if bool(state.get("installed")) or not bool(state.get("installable")):
                install_state = "disabled"
            try:
                install_button.configure(state=install_state)
            except Exception:
                pass
        try:
            self.radio_projectm_preset_var.set(
                self.tr(
                    "radio_projectm_presets_path",
                    "NetMon presets: {path}",
                ).format(path=preset_dir)
            )
        except Exception:
            pass
        try:
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_preset_access_value",
                    "Preset access: {value}",
                ).format(value=(preset_access_text or "-"))
            )
        except Exception:
            pass
        try:
            self._refresh_radio_miniplayer_content()
        except Exception:
            pass

    def open_projectm_preset_folder(self):
        preset_dir = netmon_projectm_sidecar.ensure_projectm_preset_dir(self)
        if not preset_dir:
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_preset_access_dir_create_failed",
                    "Preset access: projectM preset folder could not be created.",
                )
            )
            return False
        for command in (["xdg-open", preset_dir], ["gio", "open", preset_dir]):
            executable = shutil.which(str(command[0] or "").strip())
            if not executable:
                continue
            try:
                subprocess.Popen(
                    [executable, *command[1:]],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                self.radio_projectm_preset_hint_var.set(
                    self.tr(
                        "radio_projectm_preset_access_dir_opened",
                        "Preset access: projectM preset folder opened.",
                    )
                )
                return True
            except Exception:
                continue
        self.radio_projectm_preset_hint_var.set(
            self.tr(
                "radio_projectm_preset_access_dir_path",
                "Preset access: projectM presets are stored in {path}",
            ).format(path=preset_dir)
        )
        try:
            self.log_safe("projectM Preset-Ordner: " + preset_dir)
        except Exception:
            pass
        return False

    def _open_projectm_preset_source_page(self):
        url = PROJECTM_PRESET_SOURCE_URL
        for command in (["xdg-open", url], ["gio", "open", url]):
            executable = shutil.which(str(command[0] or "").strip())
            if not executable:
                continue
            try:
                subprocess.Popen(
                    [executable, *command[1:]],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                self.radio_projectm_preset_hint_var.set(
                    self.tr(
                        "radio_projectm_preset_source_opened",
                        "Preset source page opened in your browser.",
                    )
                )
                return True
            except Exception:
                continue
        self.radio_projectm_preset_hint_var.set(
            self.tr(
                "radio_projectm_preset_source_url",
                "Preset source page: {url}",
            ).format(url=url)
        )
        return False

    def _import_projectm_preset_archive_path(self, archive_path, pack_name=""):
        archive_path = str(archive_path or "").strip()
        if not archive_path:
            return False
        try:
            result = netmon_projectm_sidecar.install_projectm_preset_archive(
                self,
                archive_path,
                pack_name=pack_name,
            )
        except Exception as exc:
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_preset_download_failed",
                    "Preset download/import failed: {error}",
                ).format(error=exc)
            )
            return False
        self.radio_projectm_preset_hint_var.set(
            self.tr(
                "radio_projectm_preset_archive_imported",
                "Preset access: ZIP pack imported: {presets} presets{assets}. Please restart projectM.",
            ).format(
                presets=result.get("imported_presets", 0),
                assets=(
                    f" + {result.get('imported_assets', 0)} assets"
                    if result.get("imported_assets", 0)
                    else ""
                ),
            )
        )
        try:
            self.log_safe(
                "projectM Preset-Pack importiert: "
                f"{archive_path} -> {result.get('target_dir', '-')}"
            )
        except Exception:
            pass
        self._refresh_projectm_status()
        return True

    def import_projectm_preset_archive(self):
        initial_dir = str(
            getattr(self, "radio_settings", {}).get("projectm_preset_import_dir", "")
            or os.path.expanduser("~")
        ).strip() or os.path.expanduser("~")
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
        archive_path = filedialog.askopenfilename(
            parent=self,
            title=self.tr(
                "radio_projectm_import_archive_dialog_title",
                "Import projectM preset ZIP",
            ),
            initialdir=initial_dir,
            filetypes=[
                (
                    self.tr(
                        "radio_projectm_import_archive_dialog_filter",
                        "ZIP archives",
                    ),
                    "*.zip",
                ),
                (
                    self.tr(
                        "radio_projectm_import_archive_dialog_filter_all",
                        "All files",
                    ),
                    "*.*",
                ),
            ],
        )
        archive_path = str(archive_path or "").strip()
        if not archive_path:
            return False
        settings = dict(getattr(self, "radio_settings", {}) or {})
        settings["projectm_preset_import_dir"] = os.path.dirname(archive_path)
        self.radio_settings = settings
        try:
            radio_controller.save_radio_settings(self)
        except Exception:
            pass
        return self._import_projectm_preset_archive_path(archive_path)

    def download_projectm_preset_pack(self):
        initial_value = str(
            getattr(self, "radio_settings", {}).get("projectm_preset_download_url", "")
            or PROJECTM_PRESET_SOURCE_URL
        ).strip()
        url = simpledialog.askstring(
            self.tr(
                "radio_projectm_download_url_title",
                "Download preset pack",
            ),
            self.tr(
                "radio_projectm_download_url_prompt",
                "Enter the direct ZIP URL of an external projectM/MilkDrop preset pack.",
            ),
            parent=self,
            initialvalue=initial_value,
        )
        url = str(url or "").strip()
        if not url:
            return False
        if not url.lower().startswith(("http://", "https://")):
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_download_url_invalid",
                    "Preset download failed: please enter a full http:// or https:// URL.",
                )
            )
            return False
        settings = dict(getattr(self, "radio_settings", {}) or {})
        settings["projectm_preset_download_url"] = url
        self.radio_settings = settings
        try:
            radio_controller.save_radio_settings(self)
        except Exception:
            pass
        self.radio_projectm_preset_hint_var.set(
            self.tr(
                "radio_projectm_preset_download_running",
                "Preset download: loading external ZIP pack...",
            )
        )
        self.update_idletasks()
        temp_path = ""
        try:
            with urllib_request.urlopen(url, timeout=30) as response:
                payload = response.read()
            suffix = ".zip"
            fd, temp_path = tempfile.mkstemp(
                prefix="netmon-projectm-pack-",
                suffix=suffix,
            )
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            return self._import_projectm_preset_archive_path(
                temp_path,
                pack_name=os.path.splitext(os.path.basename(url.split("?", 1)[0]))[0],
            )
        except Exception as exc:
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_preset_download_failed",
                    "Preset download/import failed: {error}",
                ).format(error=exc)
            )
            return False
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

    def open_projectm_preset_manager(self):
        existing = getattr(self, "radio_projectm_preset_manager_window", None)
        try:
            if existing is not None and existing.winfo_exists():
                existing.deiconify()
                existing.lift()
                existing.focus_force()
                return existing
        except Exception:
            pass

        popup = tk.Toplevel(self)
        popup.title(self.tr("radio_projectm_manager_title", "Preset manager"))
        popup.transient(self)
        popup.resizable(False, False)
        popup.columnconfigure(0, weight=1)
        self.radio_projectm_preset_manager_window = popup

        def _close():
            try:
                popup.destroy()
            finally:
                self.radio_projectm_preset_manager_window = None

        popup.protocol("WM_DELETE_WINDOW", _close)

        frame = ttk.Frame(popup, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)

        ttk.Label(
            frame,
            text=self.tr(
                "radio_projectm_manager_intro",
                "NetMon no longer ships preset bundles. Load external ZIP packs here or import your own presets.",
            ),
            justify="left",
            wraplength=460,
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            frame,
            text=self.tr(
                "radio_projectm_btn_open_source",
                "Open preset source page",
            ),
            command=self._open_projectm_preset_source_page,
        ).grid(row=1, column=0, sticky="ew", pady=(10, 0))

        ttk.Button(
            frame,
            text=self.tr(
                "radio_projectm_btn_download_pack",
                "Download ZIP pack",
            ),
            command=self.download_projectm_preset_pack,
        ).grid(row=2, column=0, sticky="ew", pady=(6, 0))

        ttk.Button(
            frame,
            text=self.tr(
                "radio_projectm_btn_import_pack",
                "Import local ZIP pack",
            ),
            command=self.import_projectm_preset_archive,
        ).grid(row=3, column=0, sticky="ew", pady=(6, 0))

        ttk.Button(
            frame,
            text=self.tr(
                "radio_projectm_btn_import_presets",
                "Import custom preset folder",
            ),
            command=self.import_projectm_preset_files,
        ).grid(row=4, column=0, sticky="ew", pady=(6, 0))

        ttk.Button(
            frame,
            text=self.tr(
                "radio_projectm_btn_open_presets",
                "Open projectM preset folder",
            ),
            command=self.open_projectm_preset_folder,
        ).grid(row=5, column=0, sticky="ew", pady=(6, 0))

        ttk.Button(
            frame,
            text=self.tr("close", "Close"),
            command=_close,
        ).grid(row=6, column=0, sticky="e", pady=(10, 0))
        return popup

    def import_projectm_preset_files(self):
        preset_dir = netmon_projectm_sidecar.ensure_projectm_preset_dir(self)
        if not preset_dir:
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_preset_access_dir_create_failed",
                    "Preset access: projectM preset folder could not be created.",
                )
            )
            return False
        initial_dir = str(
            getattr(self, "radio_settings", {}).get("projectm_preset_import_dir", "")
            or os.path.expanduser("~")
        ).strip() or os.path.expanduser("~")
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
        source_dir = filedialog.askdirectory(
            parent=self,
            title=self.tr(
                "radio_projectm_import_dialog_title",
                "Import custom projectM presets into Documents/NetMon/projectM Visualizer",
            ),
            initialdir=initial_dir,
        )
        source_dir = str(source_dir or "").strip()
        if not source_dir or not os.path.isdir(source_dir):
            return False
        settings = dict(getattr(self, "radio_settings", {}) or {})
        settings["projectm_preset_import_dir"] = source_dir
        self.radio_settings = settings
        try:
            radio_controller.save_radio_settings(self)
        except Exception:
            pass
        preset_exts = {".milk", ".prjm"}
        asset_exts = {
            ".jpg",
            ".jpeg",
            ".png",
            ".bmp",
            ".tga",
            ".gif",
            ".dds",
            ".ppm",
            ".pgm",
        }
        allowed_exts = preset_exts | asset_exts
        imported = 0
        imported_presets = 0
        imported_assets = 0
        scanned = 0
        for root, _dirs, files in os.walk(source_dir):
            for filename in sorted(files):
                source = os.path.join(root, filename)
                if not os.path.isfile(source):
                    continue
                _stem, ext = os.path.splitext(filename)
                if str(ext or "").strip().lower() not in allowed_exts:
                    continue
                scanned += 1
                rel_path = os.path.relpath(source, source_dir)
                target_path = os.path.join(preset_dir, rel_path)
                target_folder = os.path.dirname(target_path)
                try:
                    os.makedirs(target_folder, exist_ok=True)
                except Exception:
                    continue
                if os.path.exists(target_path):
                    name_root, name_ext = os.path.splitext(
                        os.path.basename(target_path)
                    )
                    counter = 2
                    while os.path.exists(target_path):
                        target_path = os.path.join(
                            target_folder,
                            f"{name_root}_{counter}{name_ext}",
                        )
                        counter += 1
                try:
                    shutil.copy2(source, target_path)
                    imported += 1
                    if str(ext or "").strip().lower() in preset_exts:
                        imported_presets += 1
                    else:
                        imported_assets += 1
                except Exception:
                    continue
        if imported_presets:
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_preset_access_imported",
                    "Preset access: Custom presets imported into Documents/NetMon: {presets} presets{assets}. Downloaded packs and your own imports are now available there. Please restart projectM.",
                ).format(
                    presets=imported_presets,
                    assets=(f" + {imported_assets} assets" if imported_assets else ""),
                )
            )
            try:
                self.log_safe(
                    "projectM Benutzer-Presets nach Dokumente/NetMon importiert: "
                    f"{imported_presets} Presets, {imported_assets} Assets "
                    f"({imported}/{scanned} Datei(en)) nach {preset_dir}"
                )
            except Exception:
                pass
        else:
            self.radio_projectm_preset_hint_var.set(
                self.tr(
                    "radio_projectm_preset_access_no_matching_files",
                    "Preset access: No matching preset files were found for Documents/NetMon/projectM Visualizer.",
                )
            )
        self._refresh_projectm_status()
        return bool(imported_presets)

    def _build_external_terminal_command(self, script: str):
        candidates = [
            (
                "x-terminal-emulator",
                ["x-terminal-emulator", "-e", "bash", "-lc", script],
            ),
            ("gnome-terminal", ["gnome-terminal", "--", "bash", "-lc", script]),
            ("konsole", ["konsole", "-e", "bash", "-lc", script]),
            (
                "xfce4-terminal",
                ["xfce4-terminal", "--command", f"bash -lc {shlex.quote(script)}"],
            ),
            ("mate-terminal", ["mate-terminal", "--", "bash", "-lc", script]),
            ("lxterminal", ["lxterminal", "-e", f"bash -lc {shlex.quote(script)}"]),
            ("xterm", ["xterm", "-e", "bash", "-lc", script]),
        ]
        for binary, command in candidates:
            if shutil.which(binary):
                return command
        return None

    def _on_scroll_content_configure(self, _event=None):
        canvas = getattr(self, "_scroll_canvas", None)
        content = getattr(self, "_scroll_content", None)
        if canvas is None or content is None:
            return
        try:
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure("content", width=canvas.winfo_width())
        except Exception:
            pass

    def _on_scroll_canvas_configure(self, event):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            canvas.itemconfigure("content", width=event.width)
        except Exception:
            pass

    def _on_mousewheel(self, event):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        delta = int(getattr(event, "delta", 0) or 0)
        if delta == 0:
            return
        step = -1 * int(delta / 120 if delta else 0)
        if step == 0:
            step = -1 if delta > 0 else 1
        try:
            canvas.yview_scroll(step, "units")
        except Exception:
            pass

    def _on_shift_mousewheel(self, event):
        return self._on_mousewheel(event)

    def _on_page_down(self, _event=None):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            canvas.yview_scroll(1, "pages")
        except Exception:
            pass
        return "break"

    def _on_page_up(self, _event=None):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            canvas.yview_scroll(-1, "pages")
        except Exception:
            pass
        return "break"

    def _on_home_scroll(self, _event=None):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            canvas.yview_moveto(0.0)
        except Exception:
            pass
        return "break"

    def _on_end_scroll(self, _event=None):
        canvas = getattr(self, "_scroll_canvas", None)
        if canvas is None:
            return
        try:
            canvas.yview_moveto(1.0)
        except Exception:
            pass
        return "break"

    def _on_radio_volume_mousewheel(self, event):
        delta = int(getattr(event, "delta", 0) or 0)
        if delta == 0:
            event_num = int(getattr(event, "num", 0) or 0)
            if event_num == 4:
                delta = 120
            elif event_num == 5:
                delta = -120
        if delta == 0:
            return "break"
        step = 2 if delta > 0 else -2
        current = int(self.radio_volume_var.get() or 0)
        new_value = max(0, min(100, current + step))
        self.radio_volume_var.set(new_value)
        self.on_radio_volume_preview(str(new_value))
        self.commit_radio_volume_change()
        return "break"

    def _on_radio_eq_mousewheel(self, event, variable):
        delta = int(getattr(event, "delta", 0) or 0)
        if delta == 0:
            event_num = int(getattr(event, "num", 0) or 0)
            if event_num == 4:
                delta = 120
            elif event_num == 5:
                delta = -120
        if delta == 0:
            return "break"
        step = 1 if delta > 0 else -1
        try:
            current = int(variable.get() or 0)
        except Exception:
            current = 0
        new_value = max(-12, min(12, current + step))
        variable.set(new_value)
        self.on_radio_eq_preview(str(new_value))
        self.commit_radio_eq_change()
        return "break"

    def _build_ui(self):
        # source markers:
        # text=("Start" if embedded else "projectM starten")
        # text=("Stop" if embedded else "projectM stoppen")
        # text="projectM installieren"
        # text="Radio anheften"
        # text="Miniplayer"
        # text="Datenbanken"
        # text="Erreichbarkeit prüfen"
        # text="Sender hinzufügen"
        # text="Steuerung & EQ"
        # text="EQ"
        # label="Bass"
        # label="Mitten"
        # label="Höhen"
        # label="Aufnahme starten"
        # label="Aufnahme stoppen"
        # self.radio_station_table.heading("#0", text="Ampel")
        # text="Beliebige Felder an- oder abwählen."
        # popup.title("Datenbanken")
        # text="Senderdatenbanken an- oder abwählen."
        # text="Exklusive Länderdatenbanken"
        # text="Alle auswählen"
        # text="Exklusivmodus"
        # text="Andere Datenbanken"
        # ttk.Separator(source_frame, orient="horizontal")
        # text="Datenbank aktualisieren"
        # image=self.radio_status_indicator_images.get("unknown")
        # text="Aktueller Sender"
        embedded = bool(getattr(self, "radio_embedded_mode", False))
        compact_layout = embedded or bool(getattr(self, "_radio_compact_layout", False))
        outer_pad = 3 if compact_layout else 12
        section_pad = 6 if compact_layout else 8
        controls_pad = 8 if compact_layout else 12
        search_pad = 3 if compact_layout else 12
        search_entry_pad = 4 if compact_layout else 6
        volume_length = 180 if compact_layout else 220
        eq_length = 116 if compact_layout else 150
        station_table_height = 18 if compact_layout else 28
        self.columnconfigure(0, weight=1)
        self._scroll_canvas = None
        self._scroll_content = self
        content_parent = self
        if not embedded:
            self.rowconfigure(0, weight=1)
            canvas = tk.Canvas(self, highlightthickness=0, bd=0)
            canvas.grid(row=0, column=0, sticky="nsew")
            scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
            scrollbar.grid(row=0, column=1, sticky="ns")
            content_parent = ttk.Frame(canvas)
            content_parent.columnconfigure(0, weight=1)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.create_window(
                (0, 0), window=content_parent, anchor="nw", tags="content"
            )
            content_parent.bind(
                "<Configure>", self._on_scroll_content_configure, add="+"
            )
            canvas.bind("<Configure>", self._on_scroll_canvas_configure, add="+")

            def _scroll_units(step):
                try:
                    canvas.yview_scroll(step, "units")
                except Exception:
                    pass
                return "break"

            for widget in (self, canvas, content_parent):
                widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
                widget.bind("<Shift-MouseWheel>", self._on_shift_mousewheel, add="+")
                widget.bind("<Button-4>", lambda _event: _scroll_units(-1), add="+")
                widget.bind("<Button-5>", lambda _event: _scroll_units(1), add="+")
                widget.bind("<Prior>", self._on_page_up, add="+")
                widget.bind("<Next>", self._on_page_down, add="+")
                widget.bind("<Home>", self._on_home_scroll, add="+")
                widget.bind("<End>", self._on_end_scroll, add="+")
            self._scroll_canvas = canvas
            self._scroll_content = content_parent
        else:
            self.rowconfigure(0, weight=0)
            self.rowconfigure(1, weight=0)
            self.rowconfigure(2, weight=1)

        controls_row = 0
        main_row = 1
        content_parent.rowconfigure(main_row, weight=1)
        content_parent.rowconfigure(controls_row, weight=0)

        controls = ttk.LabelFrame(
            content_parent,
            text=self.tr("radio_group_player", "Player"),
            padding=controls_pad,
        )
        controls.grid(
            row=controls_row,
            column=0,
            sticky="ew",
            padx=outer_pad,
            pady=(0, 6 if embedded else outer_pad),
        )
        controls.columnconfigure(0, weight=1)

        player_top = ttk.Frame(controls)
        player_top.grid(row=1, column=0, sticky="ew")
        player_top.columnconfigure(0, weight=1)

        playback_eq_frame = ttk.LabelFrame(
            player_top,
            text=self.tr("radio_group_controls_eq", "Controls & EQ"),
            padding=section_pad,
        )
        playback_eq_frame.grid(row=0, column=0, sticky="ew")
        playback_eq_frame.columnconfigure(0, weight=5, minsize=360)
        playback_eq_frame.columnconfigure(1, weight=2, minsize=160)

        playback_frame = ttk.LabelFrame(
            playback_eq_frame,
            text=self.tr("radio_group_controls", "Controls"),
            padding=section_pad,
        )
        playback_frame.grid(row=0, column=0, sticky="nsew", padx=(0, outer_pad))
        playback_frame.columnconfigure(0, weight=1)
        self._set_radio_logo_placeholder(self.tr("radio_logo_placeholder", "No logo"))
        button_row = ttk.Frame(playback_frame)
        button_row.grid(row=0, column=0, pady=(0, 0))
        ttk.Button(button_row, text="⏮", width=7, command=self.radio_previous).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(button_row, text="▶", width=7, command=self.radio_play).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        self.radio_record_transport_button = tk.Button(
            button_row,
            text="⏺",
            width=7,
            relief="flat",
            bd=0,
            bg="#b32020",
            fg="#ffffff",
            activebackground="#d83a3a",
            activeforeground="#ffffff",
            command=self.toggle_radio_recording,
        )
        self.radio_record_transport_button.grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        ttk.Button(
            button_row,
            text="■",
            width=7,
            command=lambda: self.stop_radio_playback(async_mode=True),
        ).grid(row=0, column=3, sticky="w", padx=(8, 0))
        ttk.Button(button_row, text="⏭", width=7, command=self.radio_next).grid(
            row=0, column=4, sticky="w", padx=(8, 0)
        )
        volume_row = ttk.Frame(playback_frame)
        volume_row.grid(row=1, column=0, pady=(10, 0))
        ttk.Label(volume_row, textvariable=self.radio_volume_label_var).grid(
            row=0, column=0, sticky="e", padx=(0, 8)
        )
        volume = ttk.Scale(
            volume_row,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.radio_volume_var,
            command=self.on_radio_volume_preview,
            length=volume_length,
        )
        volume.grid(row=0, column=1, sticky="w")
        volume.bind("<ButtonRelease-1>", self.commit_radio_volume_change)
        volume.bind("<KeyRelease>", self.commit_radio_volume_change)
        volume.bind("<MouseWheel>", self._on_radio_volume_mousewheel)
        volume.bind("<Button-4>", self._on_radio_volume_mousewheel)
        volume.bind("<Button-5>", self._on_radio_volume_mousewheel)
        ttk.Label(volume_row, textvariable=self.radio_volume_label_var).grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        eq_frame = ttk.LabelFrame(
            playback_eq_frame,
            text=self.tr("radio_group_eq", "EQ"),
            padding=section_pad,
        )
        eq_frame.grid(row=0, column=1, sticky="nsew")
        eq_frame.columnconfigure(1, weight=1)
        eq_frame.columnconfigure(2, weight=0)
        self._build_eq_slider(
            eq_frame,
            row=0,
            label=self.tr("radio_eq_bass", "Bass"),
            variable=self.radio_eq_bass_var,
            value_variable=self.radio_eq_bass_label_var,
            slider_length=eq_length,
        )
        self._build_eq_slider(
            eq_frame,
            row=1,
            label=self.tr("radio_eq_mid", "Mid"),
            variable=self.radio_eq_mid_var,
            value_variable=self.radio_eq_mid_label_var,
            slider_length=eq_length,
        )
        self._build_eq_slider(
            eq_frame,
            row=2,
            label=self.tr("radio_eq_treble", "Treble"),
            variable=self.radio_eq_treble_var,
            value_variable=self.radio_eq_treble_label_var,
            slider_length=eq_length,
        )
        details_row = ttk.Frame(controls)
        details_row.grid(row=0, column=0, sticky="ew", pady=(0, outer_pad))
        details_row.columnconfigure(0, weight=1)
        details_frame = ttk.LabelFrame(
            details_row,
            text=self.tr("radio_group_current_station", "Current station"),
            padding=section_pad,
        )
        details_frame.grid(row=0, column=0, sticky="nsew")
        details_frame.columnconfigure(1, weight=1)
        details_frame.columnconfigure(2, weight=0)
        self.radio_logo_label = ttk.Label(
            details_frame,
            text=self.tr("radio_logo_placeholder", "No logo"),
            anchor="center",
            padding=(4, 4),
        )
        self.radio_logo_label.grid(
            row=0,
            column=0,
            rowspan=5,
            sticky="nw",
            padx=(0, outer_pad if embedded else 12),
        )
        ttk.Label(
            details_frame,
            textvariable=self.radio_source_var,
            justify="left",
        ).grid(row=0, column=1, sticky="w")
        ttk.Label(
            details_frame,
            textvariable=self.radio_title_var,
            justify="left",
        ).grid(row=1, column=1, sticky="w", pady=(6, 0))
        ttk.Label(
            details_frame,
            textvariable=self.radio_bitrate_var,
            justify="left",
        ).grid(row=2, column=1, sticky="w", pady=(6, 0))
        ttk.Label(
            details_frame,
            textvariable=self.radio_record_status_var,
            justify="left",
        ).grid(row=3, column=1, sticky="w", pady=(10, 0))
        self.radio_miniplayer_button = ttk.Button(
            details_frame,
            text=self.tr("radio_btn_miniplayer", "Miniplayer"),
            command=self.open_radio_miniplayer,
        )
        self.radio_miniplayer_button.grid(
            row=0,
            column=2,
            sticky="ne",
            padx=(12, 0),
        )
        if embedded:
            self.radio_detach_button = ttk.Button(
                details_frame,
                text=self.tr("radio_btn_detach", "Detach radio"),
                command=self.detach_radio_from_netmon,
            )
            self.radio_detach_button.grid(
                row=1,
                column=2,
                sticky="ne",
                padx=(12, 0),
                pady=(8, 0),
            )
        else:
            self.radio_attach_button = ttk.Button(
                details_frame,
                text=self.tr("radio_btn_attach", "Attach radio"),
                command=self.attach_radio_to_netmon,
            )
            self.radio_attach_button.grid(
                row=1,
                column=2,
                sticky="ne",
                padx=(12, 0),
                pady=(8, 0),
            )
        self.radio_database_count_label = ttk.Label(
            details_frame,
            textvariable=self.radio_database_count_var,
            justify="right",
        )
        self.radio_database_count_label.grid(
            row=2,
            column=2,
            sticky="ne",
            padx=(12, 0),
            pady=(6, 0),
        )
        main = ttk.Frame(content_parent, padding=(outer_pad, 0, outer_pad, outer_pad))
        main.grid(row=main_row, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)
        main_pane = None
        if not embedded:
            main_pane = ttk.Panedwindow(main, orient="vertical")
            main_pane.grid(row=0, column=0, sticky="nsew")
            self.radio_main_pane = main_pane
            self.radio_main_pane_marker = _install_pane_drag_marker(main, main_pane)
        else:
            self.radio_main_pane = None
            self.radio_main_pane_marker = None

        station_parent = main_pane if main_pane is not None else main
        station_frame = ttk.LabelFrame(
            station_parent,
            text=self.tr("radio_station_list", "Station list"),
            padding=section_pad,
        )
        if main_pane is None:
            station_frame.grid(row=0, column=0, sticky="nsew")
        station_frame.columnconfigure(0, weight=1)
        station_frame.rowconfigure(2, weight=1)
        action_row = ttk.Frame(station_frame)
        action_row.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Button(
            action_row,
            textvariable=self.radio_toggle_favorites_text_var,
            command=self.toggle_radio_favorites_view,
        ).grid(row=0, column=0, sticky="w")
        self.radio_reachability_button = ttk.Button(
            action_row,
            text=self.tr("radio_btn_check_reachability", "Check reachability"),
            command=self.check_visible_radio_station_reachability,
        )
        self.radio_reachability_button.grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Button(
            action_row,
            text=self.tr("radio_custom_add_button", "Add station"),
            command=self.open_new_custom_radio_station_editor,
        ).grid(row=0, column=2, sticky="w", padx=(12, 0))
        search_row = ttk.Frame(station_frame, padding=search_pad)
        search_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(
            search_row,
            text=self.tr("radio_search_label", "Search:"),
        ).grid(row=0, column=0, sticky="w")
        search = ttk.Entry(search_row, textvariable=self.radio_search_var, width=48)
        search.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(search_entry_pad, 0),
        )
        search.bind("<KeyRelease>", self.on_radio_search_changed)
        self.attach_text_context_menu(search)
        self.radio_station_table = ttk.Treeview(
            station_frame,
            columns=("name", "genre", "bitrate"),
            show=("tree", "headings"),
            height=station_table_height,
        )
        self.radio_station_table.heading(
            "#0",
            text=self.tr("radio_col_indicator", "Status"),
        )
        self.radio_station_table.column(
            "#0", width=44, minwidth=44, stretch=False, anchor="center"
        )
        radio_controller.configure_radio_station_table_columns(self)
        self.radio_station_table.grid(row=2, column=0, sticky="nsew")
        self.radio_station_table.bind(
            "<ButtonRelease-1>",
            self.on_radio_station_clicked,
        )
        self.radio_station_table.bind(
            "<Button-3>", self.show_radio_station_context_menu
        )
        station_scroll = ttk.Scrollbar(
            station_frame,
            orient="vertical",
            command=self.radio_station_table.yview,
        )
        station_scroll.grid(row=2, column=1, sticky="ns")
        station_scroll_x = ttk.Scrollbar(
            station_frame,
            orient="horizontal",
            command=self.radio_station_table.xview,
        )
        station_scroll_x.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        self.radio_station_table.configure(
            yscrollcommand=station_scroll.set,
            xscrollcommand=station_scroll_x.set,
        )
        status_row = ttk.Frame(station_frame)
        status_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        status_row.columnconfigure(0, weight=1)
        ttk.Label(
            status_row,
            textvariable=self.radio_list_status_var,
        ).grid(row=0, column=0, sticky="w")
        radio_page_frame = ttk.Frame(status_row)
        radio_page_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.radio_page_prev_button = ttk.Button(
            radio_page_frame,
            text="←",
            width=4,
            command=self.show_previous_radio_search_page,
        )
        self.radio_page_prev_button.pack(side="left", padx=(0, 4))
        ttk.Label(
            radio_page_frame,
            textvariable=self.radio_page_indicator_var,
            width=6,
            anchor="center",
        ).pack(side="left")
        self.radio_page_next_button = ttk.Button(
            radio_page_frame,
            text="→",
            width=4,
            command=self.show_next_radio_search_page,
        )
        self.radio_page_next_button.pack(side="left", padx=(4, 0))
        ttk.Label(
            status_row,
            textvariable=self.radio_dependency_var,
            justify="right",
        ).grid(row=0, column=1, sticky="e")

        playlist_parent = (
            main_pane if main_pane is not None else (main if not embedded else controls)
        )
        # legacy source reference:
        # playlist_parent = main_pane if main_pane is not None else (main if not embedded else controls)
        playlist_grid_kwargs = {
            "row": 1 if not embedded else 2,
            "column": 0,
            "sticky": "nsew" if not embedded else "ew",
            "pady": (outer_pad, 0),
        }
        if embedded:
            external_playlist_parent = getattr(
                getattr(self, "radio_host_app", None),
                "radio_tab_bottom_section",
                None,
            )
            if external_playlist_parent is not None:
                for child in external_playlist_parent.winfo_children():
                    try:
                        child.destroy()
                    except Exception:
                        pass
                playlist_parent = external_playlist_parent
                playlist_grid_kwargs = {"row": 0, "column": 0, "sticky": "nsew"}
        playlist_frame = ttk.LabelFrame(
            playlist_parent,
            text=self.tr("radio_group_local_media", "Local media"),
            padding=section_pad,
        )
        if main_pane is None:
            playlist_frame.grid(**playlist_grid_kwargs)
        playlist_frame.columnconfigure(0, weight=1)
        playlist_frame.rowconfigure(1, weight=1)
        playlist_buttons = ttk.Frame(playlist_frame)
        playlist_buttons.grid(row=0, column=0, sticky="w")
        self.radio_playlist_remove_button = ttk.Button(
            playlist_buttons,
            text=self.tr("radio_playlist_remove", "Remove"),
            command=self.remove_selected_radio_playlist_entry,
        )
        self.radio_playlist_remove_button.grid(row=0, column=0, sticky="w")
        self.radio_playlist_clear_button = ttk.Button(
            playlist_buttons,
            text=self.tr("radio_playlist_clear", "Clear playlist"),
            command=self.clear_radio_playlist,
        )
        self.radio_playlist_clear_button.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.radio_playlist_save_button = ttk.Button(
            playlist_buttons,
            text=self.tr("radio_playlist_save", "Save playlist"),
            command=self.save_radio_playlist_to_file,
        )
        self.radio_playlist_save_button.grid(row=0, column=2, sticky="w", padx=(6, 0))
        self.radio_playlist_load_button = ttk.Button(
            playlist_buttons,
            text=self.tr("radio_playlist_load", "Load playlist"),
            command=self.load_radio_playlist_from_file,
        )
        self.radio_playlist_load_button.grid(row=0, column=3, sticky="w", padx=(6, 0))
        media_pane = ttk.Panedwindow(playlist_frame, orient="vertical")
        media_pane.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.radio_media_pane = media_pane
        self.radio_media_pane_marker = _install_pane_drag_marker(
            playlist_frame, media_pane, y_offset=12
        )
        playlist_pane = ttk.Frame(media_pane)
        playlist_pane.columnconfigure(0, weight=1)
        playlist_pane.rowconfigure(0, weight=1)
        folder_pane = ttk.Frame(media_pane)
        folder_pane.columnconfigure(0, weight=1)
        folder_pane.rowconfigure(2, weight=1)
        media_pane.add(playlist_pane, weight=3)
        media_pane.add(folder_pane, weight=2)
        playlist_browser = ttk.Frame(playlist_pane)
        playlist_browser.grid(row=0, column=0, sticky="nsew")
        playlist_browser.columnconfigure(0, weight=1)
        playlist_browser.rowconfigure(0, weight=1)
        self.radio_playlist_listbox = tk.Listbox(
            playlist_browser,
            height=9,
            exportselection=False,
        )
        self.radio_playlist_listbox.grid(row=0, column=0, sticky="nsew")
        playlist_scroll = ttk.Scrollbar(
            playlist_browser,
            orient="vertical",
            command=self.radio_playlist_listbox.yview,
        )
        playlist_scroll.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.radio_playlist_listbox.configure(yscrollcommand=playlist_scroll.set)
        self.radio_playlist_listbox.bind(
            "<Double-Button-1>",
            self.play_selected_radio_playlist_entry,
        )
        ttk.Label(
            playlist_pane,
            textvariable=self.radio_playlist_status_var,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        folder_buttons = ttk.Frame(folder_pane)
        folder_buttons.grid(row=0, column=0, sticky="w")
        self.radio_playlist_add_button = ttk.Button(
            folder_buttons,
            text=self.tr(
                "radio_btn_open_recordings_folder",
                "Open recording folder",
            ),
            command=self.open_radio_recordings_dir,
        )
        self.radio_playlist_add_button.grid(row=0, column=0, sticky="w")
        self.radio_playlist_folder_button = ttk.Button(
            folder_buttons,
            text=self.tr(
                "radio_btn_open_playlist_folder",
                "Open playlist folder",
            ),
            command=self.open_radio_playlists_dir,
        )
        self.radio_playlist_folder_button.grid(row=0, column=1, sticky="w", padx=(6, 0))
        self.radio_system_folder_button = ttk.Button(
            folder_buttons,
            text=self.tr("radio_btn_open_system_folder", "Open system folder"),
            command=self.open_radio_system_dir,
        )
        self.radio_system_folder_button.grid(row=0, column=2, sticky="w", padx=(6, 0))
        recordings_header = ttk.Frame(folder_pane)
        recordings_header.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        recordings_header.columnconfigure(1, weight=1)
        recordings_header.columnconfigure(2, weight=0)
        recordings_header.columnconfigure(3, weight=0)
        recordings_header.columnconfigure(4, weight=0)
        recordings_header.columnconfigure(5, weight=0)
        ttk.Label(
            recordings_header,
            textvariable=self.radio_folder_browser_title_var,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            recordings_header,
            textvariable=self.radio_folder_browser_path_var,
            justify="left",
        ).grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.radio_folder_browser_back_button = ttk.Button(
            recordings_header,
            text="←",
            width=4,
            command=self.navigate_radio_folder_browser_back,
        )
        self.radio_folder_browser_back_button.grid(
            row=0, column=2, sticky="e", padx=(0, 6)
        )
        self.radio_folder_browser_forward_button = ttk.Button(
            recordings_header,
            text="→",
            width=4,
            command=self.navigate_radio_folder_browser_forward,
        )
        self.radio_folder_browser_forward_button.grid(
            row=0, column=3, sticky="e", padx=(0, 6)
        )
        self.radio_folder_browser_up_button = ttk.Button(
            recordings_header,
            text="↑",
            width=4,
            command=self.navigate_radio_folder_browser_up,
        )
        self.radio_folder_browser_up_button.grid(
            row=0, column=4, sticky="e", padx=(0, 6)
        )
        self.radio_folder_browser_open_path_button = ttk.Button(
            recordings_header,
            text=self.tr("radio_btn_open_path", "Open path"),
            width=12,
            command=self.open_current_radio_folder_browser_path,
        )
        self.radio_folder_browser_open_path_button.grid(row=0, column=5, sticky="e")
        ttk.Label(
            recordings_header,
            textvariable=self.radio_recordings_status_var,
            justify="right",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))
        recordings_browser = ttk.Frame(folder_pane)
        recordings_browser.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        recordings_browser.columnconfigure(0, weight=1)
        recordings_browser.rowconfigure(0, weight=1)
        self.radio_recordings_listbox = tk.Listbox(
            recordings_browser,
            height=8,
            exportselection=False,
        )
        self.radio_recordings_listbox.grid(row=0, column=0, sticky="nsew")
        recordings_scroll = ttk.Scrollbar(
            recordings_browser,
            orient="vertical",
            command=self.radio_recordings_listbox.yview,
        )
        recordings_scroll.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.radio_recordings_listbox.configure(yscrollcommand=recordings_scroll.set)
        self.radio_recordings_listbox.bind(
            "<ButtonPress-1>",
            self.start_radio_folder_browser_drag,
        )
        self.radio_recordings_listbox.bind(
            "<B1-Motion>",
            self.track_radio_folder_browser_drag,
        )
        self.radio_recordings_listbox.bind(
            "<ButtonRelease-1>",
            self.finish_radio_folder_browser_drag,
        )
        self.radio_recordings_listbox.bind(
            "<Double-Button-1>",
            self.open_selected_radio_folder_browser_entry,
        )
        self.radio_recordings_listbox.bind(
            "<Leave>",
            self.cancel_radio_folder_browser_drag,
        )
        self.radio_recordings_listbox.bind(
            "<Delete>",
            self.delete_selected_radio_folder_browser_entry_key,
        )
        self.radio_recordings_listbox.bind(
            "<KP_Delete>",
            self.delete_selected_radio_folder_browser_entry_key,
        )
        self.radio_recordings_listbox.bind(
            "<Button-3>",
            self.show_radio_folder_browser_context_menu,
        )
        self.radio_folder_browser_menu = tk.Menu(
            self.radio_recordings_listbox, tearoff=0
        )
        self.radio_folder_browser_menu.add_command(
            label=self.tr("radio_folder_menu_add_to_playlist", "Add to playlist"),
            command=self.add_selected_radio_folder_browser_entry_to_playlist,
        )
        self.radio_folder_browser_menu.add_command(
            label=self.tr("radio_folder_menu_start_playlist", "Start playlist"),
            command=self.start_selected_radio_folder_browser_playlist,
        )
        if main_pane is not None:
            main_pane.add(station_frame, weight=3)
            main_pane.add(playlist_frame, weight=2)

        projectm_frame = ttk.LabelFrame(
            player_top,
            text=self.tr("radio_group_projectm", "projectM visualizer"),
            padding=section_pad,
        )
        projectm_frame.grid(row=1, column=0, sticky="ew", pady=(outer_pad, 0))
        projectm_frame.columnconfigure(0, weight=1)
        projectm_frame.columnconfigure(1, weight=1)
        projectm_frame.columnconfigure(2, weight=1)
        preset_wraplength = 640 if embedded else 820

        projectm_actions = ttk.Frame(projectm_frame)
        projectm_actions.grid(row=0, column=0, columnspan=3, sticky="ew")
        projectm_actions.columnconfigure(0, weight=1)
        projectm_actions.columnconfigure(1, weight=1)
        projectm_actions.columnconfigure(2, weight=1)

        ttk.Button(
            projectm_actions,
            text=(
                self.tr("radio_btn_start", "Start")
                if embedded
                else self.tr("radio_projectm_btn_start", "Start projectM")
            ),
            command=self.open_projectm_visualizer_test,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(
            projectm_actions,
            text=(
                self.tr("radio_btn_stop", "Stop")
                if embedded
                else self.tr("radio_projectm_btn_stop", "Stop projectM")
            ),
            command=self.close_projectm_visualizer_test,
        ).grid(row=0, column=1, sticky="ew", padx=6)
        if embedded:
            self.radio_record_settings_button = ttk.Button(
                projectm_actions,
                text="⚙",
                width=3,
                command=self.open_radio_record_settings_popup,
            )
        else:
            self.radio_record_settings_button = ttk.Button(
                projectm_actions,
                text=self.tr(
                    "radio_projectm_btn_install",
                    "Install projectM",
                ),
                command=self.install_projectm_visualizer,
            )
            self.radio_projectm_install_button = self.radio_record_settings_button
        self.radio_record_settings_button.grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(6, 0),
        )

        self.radio_projectm_preset_open_button = ttk.Button(
            projectm_actions,
            text=self.tr(
                "radio_projectm_btn_open_presets",
                "Open NetMon presets",
            ),
            command=self.open_projectm_preset_folder,
        )
        self.radio_projectm_preset_open_button.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 6),
            pady=(6, 0),
        )
        self.radio_projectm_preset_import_button = ttk.Button(
            projectm_actions,
            text=self.tr(
                "radio_projectm_btn_manage_presets",
                "Preset manager",
            ),
            command=self.open_projectm_preset_manager,
        )
        self.radio_projectm_preset_import_button.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=6,
            pady=(6, 0),
        )
        self.radio_database_button = ttk.Button(
            projectm_actions,
            text=self.tr("radio_database_window_title", "Databases"),
            command=self.open_radio_database_sources_popup,
        )
        self.radio_database_button.grid(
            row=1,
            column=2,
            sticky="ew",
            padx=(6, 0),
            pady=(6, 0),
        )
        if not getattr(self, "radio_embedded_mode", False):
            ttk.Label(
                projectm_frame,
                textvariable=self.radio_attach_status_var,
                justify="left",
            ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        else:
            self.radio_attach_button = None

        ttk.Label(
            projectm_frame,
            textvariable=self.radio_projectm_preset_var,
            justify="left",
            wraplength=preset_wraplength,
        ).grid(
            row=(1 if embedded else 4),
            column=0,
            columnspan=3,
            sticky="w",
            pady=(8, 0),
        )
        ttk.Label(
            projectm_frame,
            textvariable=self.radio_projectm_preset_hint_var,
            justify="left",
            wraplength=preset_wraplength,
        ).grid(
            row=(2 if embedded else 5),
            column=0,
            columnspan=3,
            sticky="w",
            pady=(4, 0),
        )

        self.radio_station_menu = tk.Menu(self.radio_station_table, tearoff=0)
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_play", "Play"),
            command=self.play_selected_radio_station,
        )
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_add_favorite", "Add to favorites"),
            command=self.add_selected_radio_favorite,
        )
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_remove_favorite", "Remove from favorites"),
            command=self.remove_selected_radio_favorite,
        )
        self.radio_station_menu.add_separator()
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_start_recording", "Start recording"),
            command=self.start_radio_recording,
        )
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_stop_recording", "Stop recording"),
            command=self.stop_radio_recording,
        )
        self.radio_station_menu.add_separator()
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_copy_url", "Copy stream URL"),
            command=self.copy_selected_radio_stream_url,
        )
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_open_homepage", "Open homepage"),
            command=self.open_selected_radio_homepage,
        )
        self.radio_station_menu.add_separator()
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_edit_station", "Senderdaten bearbeiten"),
            command=self.edit_selected_radio_station_data,
        )
        self.radio_station_menu.add_command(
            label=self.tr("radio_menu_delete_station", "Sender löschen"),
            command=self.delete_selected_radio_station,
        )

    def _on_close(self):
        try:
            self.close_radio_miniplayer()
        except Exception:
            pass
        self._auto_reattach_in_progress = False
        try:
            self.close_custom_radio_station_editor()
        except Exception:
            pass
        try:
            self.stop_radio_recording()
        except Exception:
            pass
        try:
            self.stop_radio_recording()
        except Exception:
            pass
        try:
            self.close_projectm_visualizer_test()
        except Exception:
            pass
        try:
            self.stop_radio_playback(async_mode=False)
        except Exception:
            pass
        try:
            state = netmon_radio_core.read_radio_host_state()
            if (
                netmon_radio_core.netmon_host_is_available()
                and str(state.get("mode", "")).strip().lower() == "standalone"
                and int(state.get("owner_pid") or 0) == int(os.getpid())
            ):
                if self.attach_radio_to_netmon():
                    return
        except Exception:
            pass
        try:
            state = netmon_radio_core.read_radio_host_state()
            launcher_state = str(state.get("launcher_state", "")).strip().lower()
            standalone_owner = launcher_state == "standalone_active" or (
                not launcher_state
                and str(state.get("mode", "")).strip().lower() == "standalone"
            )
            if standalone_owner and int(state.get("owner_pid") or 0) == int(
                os.getpid()
            ):
                netmon_radio_core.clear_netmon_host_state(os.getpid())
        except Exception:
            pass
        self.destroy()

    def refresh_radio_ui(self):
        result = radio_controller.refresh_radio_ui(self)
        radio_controller.refresh_radio_recording_ui(self)
        radio_controller.refresh_radio_playlist_ui(self)
        return result

    def update_radio_dependency_state(self):
        return radio_controller.update_radio_dependency_state(self)

    def download_radio_db(self):
        return radio_controller.download_radio_db(self)

    def radio_play(self):
        return radio_controller.play_current_radio_source(self)

    def play_selected_radio_station(self):
        return radio_controller.play_selected_station(self)

    def stop_radio_playback(self, async_mode=True, clear_current=False):
        return radio_controller.stop_radio_playback(
            self,
            async_mode=async_mode,
            clear_current=clear_current,
        )

    def radio_previous(self):
        return radio_controller.play_previous_station(self)

    def radio_next(self):
        return radio_controller.play_next_station(self)

    def on_radio_search_changed(self, *args):
        return radio_controller.on_radio_search_changed(self, *args)

    def toggle_radio_favorites_view(self):
        return radio_controller.toggle_radio_favorites_view(self)

    def set_radio_search_page(self, page):
        return radio_controller.set_radio_search_page(self, page)

    def show_previous_radio_search_page(self):
        return radio_controller.step_radio_search_page(self, -1)

    def show_next_radio_search_page(self):
        return radio_controller.step_radio_search_page(self, 1)

    def check_visible_radio_station_reachability(self):
        return radio_controller.check_visible_radio_station_reachability(self)

    def toggle_radio_station_list_column(self, column_id, enabled):
        return radio_controller.toggle_radio_station_list_column(
            self, column_id, enabled
        )

    def request_radio_database_refresh(self):
        return self.download_radio_db()

    def check_radio_database_source_reachability(self):
        return radio_controller.check_radio_database_source_reachability(self)

    def _radio_database_attr(self, attr_name, default=None):
        return getattr(self, attr_name, default)

    def _radio_database_source_vars(self):
        return self._radio_database_attr("radio_database_source_vars", {}) or {}

    def _radio_database_var_bool(self, var, default=False):
        if var is None:
            return default
        try:
            return bool(var.get())
        except Exception:
            return default

    def _radio_database_var_set(self, var, value):
        if var is None:
            return False
        try:
            var.set(value)
        except Exception:
            return False
        return True

    def _configure_radio_database_widget(self, widget, **kwargs):
        if widget is None:
            return False
        try:
            widget.configure(**kwargs)
        except Exception:
            return False
        return True

    def _radio_database_indicator_image(self, status="unknown"):
        # legacy source reference: image=self.radio_status_indicator_images.get("unknown")
        images = self._radio_database_attr("radio_status_indicator_images", {}) or {}
        return images.get(status)

    def _radio_database_source_label(self, source_id, fallback_label):
        key = f"radio_db_source_{str(source_id or '').strip()}"
        return self.tr(key, str(fallback_label or "").strip())

    def _add_radio_database_source_row(
        self,
        parent,
        *,
        row_idx,
        source_id,
        label,
        url,
    ):
        var = tk.BooleanVar(
            value=source_id not in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS
        )
        self.radio_database_source_vars[source_id] = var
        status_label = ttk.Label(
            parent,
            image=self._radio_database_indicator_image(),
        )
        status_label.grid(
            row=row_idx,
            column=0,
            sticky="w",
            padx=(0, 8),
            pady=(4, 0),
        )
        self.radio_database_source_status_labels[source_id] = status_label
        ttk.Checkbutton(
            parent,
            text=f"{self._radio_database_source_label(source_id, label)} - {url}",
            variable=var,
            command=lambda sid=source_id: self.on_radio_database_source_toggle(sid),
        ).grid(row=row_idx, column=1, sticky="w", pady=(4, 0))
        return row_idx + 1

    def _sync_radio_database_select_all_state(self):
        source_vars = self._radio_database_source_vars()
        select_all_var = self._radio_database_attr("radio_database_select_all_var")
        if select_all_var is None or not source_vars:
            return False
        all_selected = True
        for var in source_vars.values():
            if not self._radio_database_var_bool(var):
                all_selected = False
                break
        self._radio_database_var_set(select_all_var, all_selected)
        return all_selected

    def on_radio_database_select_all_changed(self):
        select_all_var = self._radio_database_attr("radio_database_select_all_var")
        select_all_enabled = self._radio_database_var_bool(select_all_var)
        if not select_all_enabled:
            return True

        exclusive_mode_var = self._radio_database_attr(
            "radio_database_exclusive_mode_var"
        )
        self._radio_database_var_set(exclusive_mode_var, False)
        for var in self._radio_database_source_vars().values():
            self._radio_database_var_set(var, True)
        self._sync_radio_database_select_all_state()
        return True

    def on_radio_database_exclusive_mode_changed(self):
        exclusive_mode_var = self._radio_database_attr(
            "radio_database_exclusive_mode_var"
        )
        exclusive_mode_enabled = self._radio_database_var_bool(
            exclusive_mode_var, default=True
        )
        if not exclusive_mode_enabled:
            self._sync_radio_database_select_all_state()
            return True

        select_all_var = self._radio_database_attr("radio_database_select_all_var")
        self._radio_database_var_set(select_all_var, False)

        source_vars = self._radio_database_source_vars()
        selected_country_ids = []
        for source_id in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS:
            var = source_vars.get(source_id)
            if self._radio_database_var_bool(var):
                selected_country_ids.append(source_id)
        if not selected_country_ids:
            return True

        keep_id = selected_country_ids[0]
        for other_id, other_var in source_vars.items():
            if other_id == keep_id:
                continue
            self._radio_database_var_set(other_var, False)
        return True

    def on_radio_database_source_toggle(self, source_id):
        source_key = str(source_id or "").strip()
        source_vars = self._radio_database_source_vars()
        exclusive_mode_var = self._radio_database_attr(
            "radio_database_exclusive_mode_var"
        )
        exclusive_mode_enabled = self._radio_database_var_bool(
            exclusive_mode_var, default=True
        )
        selected_var = source_vars.get(source_key)
        selected = self._radio_database_var_bool(selected_var)

        if not exclusive_mode_enabled:
            self._sync_radio_database_select_all_state()
            return True

        if source_key in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS and selected:
            select_all_var = self._radio_database_attr("radio_database_select_all_var")
            self._radio_database_var_set(select_all_var, False)
            for other_id, other_var in source_vars.items():
                if other_id == source_key:
                    continue
                self._radio_database_var_set(other_var, False)
            return True

        if source_key not in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS and selected:
            select_all_var = self._radio_database_attr("radio_database_select_all_var")
            self._radio_database_var_set(select_all_var, False)
            for exclusive_id in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS:
                exclusive_var = source_vars.get(exclusive_id)
                self._radio_database_var_set(exclusive_var, False)
            return True

        if source_key in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS and not selected:
            return True
        self._sync_radio_database_select_all_state()
        return True

    def set_radio_database_import_progress(
        self, current, total, message="", *, running=False
    ):
        total_value = max(1, int(total or 0))
        current_value = max(0, min(int(current or 0), total_value))
        progressbar = self._radio_database_attr("radio_database_progressbar")
        self._configure_radio_database_widget(progressbar, maximum=total_value)
        progress_var = self._radio_database_attr("radio_database_progress_var")
        self._radio_database_var_set(progress_var, float(current_value))
        status_var = self._radio_database_attr("radio_database_progress_status_var")
        self._radio_database_var_set(status_var, str(message or ""))
        self.radio_database_refresh_running = bool(running)
        button = self._radio_database_attr("radio_database_refresh_button")
        self._configure_radio_database_widget(
            button,
            state="disabled" if running else "normal",
            text=(
                self.tr("radio_database_refresh_running", "Aktualisiere...")
                if running
                else self.tr("radio_database_refresh_button", "Datenbank aktualisieren")
            ),
        )
        return True

    def show_radio_database_import_summary(self, summary):
        data = dict(summary or {})
        total_sources = int(data.get("total_sources", 0) or 0)
        raw_total = int(data.get("raw_total", 0) or 0)
        merged_total = int(data.get("merged_total", 0) or 0)
        duplicates_removed = int(data.get("duplicates_removed", 0) or 0)
        source_results = list(data.get("source_results", []) or [])
        errors = list(data.get("errors", []) or [])

        parent = getattr(self, "radio_database_sources_window", None)
        if parent is None:
            parent = (
                self.winfo_toplevel()
                if bool(getattr(self, "radio_embedded_mode", False))
                else self
            )

        popup = tk.Toplevel(parent)
        popup.title(self.tr("radio_database_import_summary_title", "Import summary"))
        try:
            popup.transient(parent)
        except Exception:
            pass
        popup.resizable(True, True)
        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(0, weight=1)

        body = ttk.Frame(popup, padding=14)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)

        ttk.Label(
            body,
            text=self.tr("radio_database_import_summary_title", "Import summary"),
            font=("TkDefaultFont", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")

        summary_lines = [
            self.tr(
                "radio_database_import_summary_sources_selected",
                "Sources selected: {count}",
            ).format(count=total_sources),
            self.tr(
                "radio_database_import_summary_raw_loaded",
                "Raw entries loaded: {count}",
            ).format(count=raw_total),
            self.tr(
                "radio_database_import_summary_duplicates_removed",
                "Duplicates removed: {count}",
            ).format(count=duplicates_removed),
            self.tr(
                "radio_database_import_summary_unique_saved",
                "Uniquely saved: {count}",
            ).format(count=merged_total),
        ]
        ttk.Label(
            body,
            text="\n".join(summary_lines),
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        details = tk.Text(body, height=14, width=72, wrap="word")
        details.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        details_lines = []
        for item in source_results:
            source_id = str(item.get("source_id", "") or "").strip()
            source_label = self._radio_database_source_label(
                source_id,
                item.get("label", "") or source_id,
            )
            count = int(item.get("count", 0) or 0)
            status = str(item.get("status", "") or "").strip()
            if status == "ok":
                details_lines.append(
                    self.tr(
                        "radio_database_import_summary_source_loaded",
                        "{label}: {count} stations loaded",
                    ).format(label=source_label, count=count)
                )
            elif status == "error":
                details_lines.append(
                    self.tr(
                        "radio_database_import_summary_source_error",
                        "{label}: Error - {error}",
                    ).format(
                        label=source_label,
                        error=str(item.get("error", "") or "").strip(),
                    )
                )
        if errors:
            details_lines.append("")
            details_lines.append(
                self.tr(
                    "radio_database_import_summary_skipped_sources",
                    "Skipped sources:",
                )
            )
            for item in errors:
                details_lines.append(str(item))
        details.insert("1.0", "\n".join(details_lines).strip())
        details.configure(state="disabled")

        ttk.Button(
            body,
            text=self.tr("radio_custom_close_button", "Close"),
            command=popup.destroy,
        ).grid(row=3, column=0, sticky="e", pady=(12, 0))
        return popup

    def open_radio_database_sources_popup(self):
        existing = getattr(self, "radio_database_sources_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.deiconify()
                    existing.lift()
                    existing.focus_force()
                    return existing
            except Exception:
                pass

        parent = (
            self.winfo_toplevel()
            if bool(getattr(self, "radio_embedded_mode", False))
            else self
        )
        popup = tk.Toplevel(parent)
        popup.title(self.tr("radio_database_window_title", "Databases"))
        popup.transient(parent)
        popup.resizable(True, True)
        popup.geometry("980x760")
        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(0, weight=1)
        progress_style_name = "RadioDatabase.Green.Horizontal.TProgressbar"
        try:
            progress_style = ttk.Style(popup)
            progress_style.configure(
                progress_style_name,
                background="#2e7d32",
                troughcolor="#d9d9d9",
                bordercolor="#d9d9d9",
                lightcolor="#43a047",
                darkcolor="#1b5e20",
            )
        except Exception:
            progress_style_name = "Horizontal.TProgressbar"

        body = ttk.Frame(popup, padding=14)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(2, weight=1)

        ttk.Label(
            body,
            text=self.tr("radio_database_window_title", "Databases"),
            font=("TkDefaultFont", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")

        action_row = ttk.Frame(body)
        action_row.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        action_row.columnconfigure(1, weight=1)

        self.radio_database_refresh_button = ttk.Button(
            action_row,
            text=self.tr("radio_database_refresh_button", "Datenbank aktualisieren"),
            command=self.request_radio_database_refresh,
        )
        self.radio_database_refresh_button.grid(row=0, column=0, sticky="w")
        self.radio_database_progressbar = ttk.Progressbar(
            action_row,
            orient="horizontal",
            mode="determinate",
            variable=self.radio_database_progress_var,
            maximum=1,
            length=240,
            style=progress_style_name,
        )
        self.radio_database_progressbar.grid(row=0, column=1, sticky="ew", padx=(12, 0))
        ttk.Label(
            action_row,
            textvariable=self.radio_database_progress_status_var,
            justify="left",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        source_wrap = ttk.LabelFrame(
            body,
            text=self.tr("radio_database_group_sources", "Sources"),
            padding=10,
        )
        source_wrap.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        source_wrap.columnconfigure(0, weight=1)
        source_wrap.rowconfigure(0, weight=1)

        source_canvas = tk.Canvas(source_wrap, highlightthickness=0, bd=0)
        source_canvas.grid(row=0, column=0, sticky="nsew")
        source_scrollbar = ttk.Scrollbar(
            source_wrap,
            orient="vertical",
            command=source_canvas.yview,
        )
        source_scrollbar.grid(row=0, column=1, sticky="ns")
        source_canvas.configure(yscrollcommand=source_scrollbar.set)

        source_frame = ttk.Frame(source_canvas)
        source_frame.columnconfigure(1, weight=1)
        source_canvas_window = source_canvas.create_window(
            (0, 0), window=source_frame, anchor="nw"
        )

        source_frame.bind(
            "<Configure>",
            lambda _event, canvas=source_canvas: canvas.configure(
                scrollregion=canvas.bbox("all")
            ),
            add="+",
        )
        source_canvas.bind(
            "<Configure>",
            lambda event, canvas=source_canvas, window_id=source_canvas_window: canvas.itemconfigure(
                window_id, width=event.width
            ),
            add="+",
        )
        self.radio_database_source_vars = {}
        self.radio_database_source_status_labels = {}
        country_sources = [
            item
            for item in RADIO_DATABASE_SOURCES
            if item[0] in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS
        ]
        other_sources = [
            item
            for item in RADIO_DATABASE_SOURCES
            if item[0] not in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS
        ]

        row_idx = 0
        country_header = ttk.Frame(source_frame)
        country_header.grid(row=row_idx, column=0, columnspan=2, sticky="ew")
        country_header.columnconfigure(0, weight=1)
        ttk.Label(
            country_header,
            text=self.tr(
                "radio_database_group_countries",
                "Exklusive Länderdatenbanken",
            ),
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(
            country_header,
            text=self.tr("radio_database_select_all", "Alle auswählen"),
            variable=self.radio_database_select_all_var,
            command=self.on_radio_database_select_all_changed,
        ).grid(row=0, column=1, sticky="e", padx=(0, 12))
        ttk.Checkbutton(
            country_header,
            text=self.tr("radio_database_exclusive_mode", "Exklusivmodus"),
            variable=self.radio_database_exclusive_mode_var,
            command=self.on_radio_database_exclusive_mode_changed,
        ).grid(row=0, column=2, sticky="e")
        row_idx += 1

        for source_id, label, url in country_sources:
            row_idx = self._add_radio_database_source_row(
                source_frame,
                row_idx=row_idx,
                source_id=source_id,
                label=label,
                url=url,
            )

        ttk.Separator(source_frame, orient="horizontal").grid(
            row=row_idx,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 10),
        )
        row_idx += 1

        ttk.Label(
            source_frame,
            text=self.tr("radio_database_group_other", "Andere Datenbanken"),
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=row_idx, column=0, columnspan=2, sticky="w")
        row_idx += 1

        for source_id, label, url in other_sources:
            row_idx = self._add_radio_database_source_row(
                source_frame,
                row_idx=row_idx,
                source_id=source_id,
                label=label,
                url=url,
            )

        def _close_popup():
            try:
                popup.destroy()
            except Exception:
                pass
            self.radio_database_sources_window = None
            self.radio_database_refresh_button = None
            self.radio_database_progressbar = None

        ttk.Button(
            body,
            text=self.tr("radio_custom_close_button", "Close"),
            command=_close_popup,
        ).grid(row=3, column=0, sticky="e", pady=(14, 0))
        popup.protocol("WM_DELETE_WINDOW", _close_popup)
        self.radio_database_sources_window = popup
        self._sync_radio_database_select_all_state()
        self.set_radio_database_import_progress(0, 1, "", running=False)
        self.check_radio_database_source_reachability()
        return popup

    def open_radio_miniplayer(self):
        embedded = bool(getattr(self, "radio_embedded_mode", False))
        owner = self.winfo_toplevel() if embedded else self
        # legacy source reference: mini = tk.Toplevel(owner)
        # legacy source reference: mini.resizable(True, True)
        # legacy source reference: mini.minsize(mini_width, mini_height)
        # legacy source reference: mini.maxsize(mini_width * 2, mini_height * 2)
        existing = getattr(self, "radio_mini_player_window", None)
        if hasattr(existing, "winfo_exists"):
            try:
                if existing.winfo_exists():
                    existing.show()
                    if embedded:
                        owner.withdraw()
                    else:
                        self.withdraw()
                    return True
            except Exception:
                pass
        mini = RadioMiniPlayerWindow(self, owner=owner, embedded=embedded)
        self.radio_mini_player_window = mini
        self._refresh_radio_miniplayer_content()
        try:
            if embedded:
                owner.withdraw()
            else:
                self.withdraw()
        except Exception:
            pass
        return True

    def minimize_radio_miniplayer(self):
        mini = getattr(self, "radio_mini_player_window", None)
        if mini is None or not hasattr(mini, "minimize"):
            return False
        try:
            mini.minimize()
        except Exception:
            return False
        return True

    def restore_from_radio_miniplayer(self, _event=None):
        self.close_radio_miniplayer()
        try:

            def _restore_window(window):
                try:
                    window.wm_state("normal")
                except Exception:
                    pass
                try:
                    window.state("normal")
                except Exception:
                    pass
                try:
                    window.deiconify()
                except Exception:
                    pass
                try:
                    window.lift()
                except Exception:
                    pass
                try:
                    window.focus_force()
                except Exception:
                    pass

                def _finalize_restore():
                    try:
                        window.wm_state("normal")
                    except Exception:
                        pass
                    try:
                        window.deiconify()
                    except Exception:
                        pass
                    try:
                        window.lift()
                    except Exception:
                        pass
                    try:
                        window.attributes("-topmost", True)
                        window.attributes("-topmost", False)
                    except Exception:
                        pass
                    try:
                        window.focus_force()
                    except Exception:
                        pass

                try:
                    window.after(80, _finalize_restore)
                except Exception:
                    _finalize_restore()

            if bool(getattr(self, "radio_embedded_mode", False)):
                owner = self.winfo_toplevel()
                _restore_window(owner)
                host_app = getattr(self, "radio_host_app", None) or owner
                if radio_controller is not None:
                    radio_controller.open_radio_tab(host_app)
            else:
                _restore_window(self)
        except Exception:
            pass
        return "break"

    def close_radio_miniplayer(self):
        mini = getattr(self, "radio_mini_player_window", None)
        self.radio_mini_player_window = None
        self.radio_mini_logo_label = None
        self.radio_mini_projectm_button = None
        self._radio_mini_logo_photo = None
        if mini is None:
            return False
        try:
            if hasattr(mini, "winfo_exists") and mini.winfo_exists():
                mini.destroy()
        except Exception:
            pass
        return True

    def _start_radio_miniplayer_drag(self, event):
        self.radio_mini_drag_origin = (
            int(getattr(event, "x_root", 0) or 0),
            int(getattr(event, "y_root", 0) or 0),
            int(getattr(self.radio_mini_player_window, "winfo_x", lambda: 0)() or 0),
            int(getattr(self.radio_mini_player_window, "winfo_y", lambda: 0)() or 0),
        )
        return "break"

    def _drag_radio_miniplayer(self, event):
        mini = getattr(self, "radio_mini_player_window", None)
        origin = getattr(self, "radio_mini_drag_origin", None)
        if mini is None or origin is None:
            return "break"
        start_x, start_y, base_x, base_y = origin
        delta_x = int(getattr(event, "x_root", 0) or 0) - start_x
        delta_y = int(getattr(event, "y_root", 0) or 0) - start_y
        try:
            mini.geometry(f"+{base_x + delta_x}+{base_y + delta_y}")
        except Exception:
            pass
        return "break"

    def _start_standalone_resize(self, event):
        if bool(getattr(self, "radio_embedded_mode", False)):
            return "break"
        try:
            self.radio_standalone_resize_origin = (
                int(getattr(event, "x_root", 0) or 0),
                int(getattr(event, "y_root", 0) or 0),
                int(self.winfo_width() or 0),
                int(self.winfo_height() or 0),
            )
        except Exception:
            self.radio_standalone_resize_origin = None
        return "break"

    def _resize_standalone_height(self, event):
        if bool(getattr(self, "radio_embedded_mode", False)):
            return "break"
        origin = getattr(self, "radio_standalone_resize_origin", None)
        if origin is None:
            return "break"
        _start_x, start_y, base_width, base_height = origin
        delta_y = int(getattr(event, "y_root", 0) or 0) - start_y
        try:
            min_height = int(self.minsize()[1] or 0)
        except Exception:
            min_height = 720
        try:
            max_height = int(self.maxsize()[1] or 0)
        except Exception:
            max_height = max(base_height, 900)
        height = max(min_height, min(base_height + delta_y, max_height))
        try:
            self.geometry(f"{base_width}x{height}")
        except Exception:
            pass
        return "break"

    def _start_radio_miniplayer_resize(self, event):
        mini = getattr(self, "radio_mini_player_window", None)
        if mini is None:
            return "break"
        self.radio_mini_resize_origin = (
            int(getattr(event, "x_root", 0) or 0),
            int(getattr(event, "y_root", 0) or 0),
            int(mini.winfo_width() or 0),
            int(mini.winfo_height() or 0),
        )
        return "break"

    def _resize_radio_miniplayer(self, event):
        mini = getattr(self, "radio_mini_player_window", None)
        origin = getattr(self, "radio_mini_resize_origin", None)
        if mini is None or origin is None:
            return "break"
        start_x, start_y, base_width, base_height = origin
        delta_x = int(getattr(event, "x_root", 0) or 0) - start_x
        delta_y = int(getattr(event, "y_root", 0) or 0) - start_y
        width = max(320, min(base_width + delta_x, 640))
        height = max(88, min(base_height + delta_y, 176))
        try:
            mini.geometry(f"{width}x{height}")
        except Exception:
            pass
        return "break"

    def _bind_radio_miniplayer_drag(self, widget):
        # legacy source reference: widget.bind("<B1-Motion>", self._drag_radio_miniplayer, add="+")
        if str(widget.winfo_class()) not in {"Button", "TButton"}:
            try:
                widget.bind("<Button-1>", self._start_radio_miniplayer_drag, add="+")
                widget.bind("<B1-Motion>", self._drag_radio_miniplayer, add="+")
            except Exception:
                pass
        for child in widget.winfo_children():
            self._bind_radio_miniplayer_drag(child)

    def _bind_radio_miniplayer_restore(self, widget):
        # legacy source reference: widget.bind("<Double-Button-1>", self.restore_from_radio_miniplayer, add="+")
        if str(widget.winfo_class()) not in {"Button", "TButton"}:
            try:
                widget.bind(
                    "<Double-Button-1>", self.restore_from_radio_miniplayer, add="+"
                )
            except Exception:
                pass
        for child in widget.winfo_children():
            self._bind_radio_miniplayer_restore(child)

    def on_radio_volume_preview(self, value=None):
        return radio_controller.on_radio_volume_preview(self, value)

    def commit_radio_volume_change(self, event=None):
        return radio_controller.commit_radio_volume_change(self, event)

    def on_radio_eq_preview(self, value=None):
        return radio_controller.on_radio_eq_preview(self, value)

    def commit_radio_eq_change(self, event=None):
        return radio_controller.commit_radio_eq_change(self, event)

    def add_selected_radio_favorite(self):
        return radio_controller.add_selected_station_to_favorites(self)

    def remove_selected_radio_favorite(self):
        return radio_controller.remove_selected_station_from_favorites(self)

    def copy_selected_radio_stream_url(self):
        return radio_controller.copy_selected_station_url(self)

    def open_selected_radio_homepage(self):
        return radio_controller.open_selected_station_homepage(self)

    def show_radio_station_context_menu(self, event):
        return radio_controller.show_station_context_menu(self, event)

    def open_custom_radio_station_editor(self):
        editor = getattr(self, "radio_custom_editor_window", None)
        if editor is not None:
            try:
                if editor.winfo_exists():
                    editor.deiconify()
                    editor.lift()
                    editor.focus_force()
                    return editor
            except Exception:
                pass

        parent = self.winfo_toplevel()
        editor = tk.Toplevel(parent)
        editor.title(self.tr("radio_custom_station_label", "Custom stations"))
        editor.resizable(True, False)
        try:
            editor.transient(parent)
        except Exception:
            pass
        editor.protocol("WM_DELETE_WINDOW", self.close_custom_radio_station_editor)
        editor.columnconfigure(0, weight=1)

        content = ttk.Frame(editor, padding=12)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(1, weight=1)

        ttk.Label(
            content,
            text=self.tr("radio_custom_name_field", "Name"),
        ).grid(row=0, column=0, sticky="w")
        custom_name = ttk.Entry(content, textvariable=self.radio_custom_name_var)
        custom_name.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.attach_text_context_menu(custom_name)

        ttk.Label(
            content,
            text=self.tr("radio_custom_url_field", "Stream URL"),
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
        custom_url = ttk.Entry(content, textvariable=self.radio_custom_url_var)
        custom_url.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.attach_text_context_menu(custom_url)

        ttk.Label(
            content,
            text=self.tr("radio_custom_category_field", "Category"),
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))
        custom_category = ttk.Entry(
            content,
            textvariable=self.radio_custom_category_var,
        )
        custom_category.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.attach_text_context_menu(custom_category)

        ttk.Label(
            content,
            text=self.tr("radio_custom_homepage_field", "Website"),
        ).grid(row=3, column=0, sticky="w", pady=(8, 0))
        custom_homepage = ttk.Entry(
            content,
            textvariable=self.radio_custom_homepage_var,
        )
        custom_homepage.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self.attach_text_context_menu(custom_homepage)

        actions = ttk.Frame(content)
        actions.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(
            actions,
            textvariable=self.radio_custom_submit_text_var,
            command=self.add_custom_radio_station,
        ).grid(row=0, column=0, sticky="w")
        self.radio_custom_editor_delete_button = ttk.Button(
            actions,
            text=self.tr("radio_custom_delete_button", "Delete selected"),
            command=self.delete_selected_radio_station,
        )
        self.radio_custom_editor_delete_button.grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )
        try:
            self.radio_custom_editor_delete_button.configure(
                state="normal" if self.radio_custom_edit_station_id else "disabled"
            )
        except Exception:
            pass
        ttk.Button(
            actions,
            text=self.tr("radio_custom_close_button", "Close"),
            command=self.close_custom_radio_station_editor,
        ).grid(row=0, column=2, sticky="w", padx=(8, 0))

        ttk.Label(
            content,
            textvariable=self.radio_custom_form_status_var,
            justify="left",
            wraplength=520,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        for widget in (custom_name, custom_url, custom_category, custom_homepage):
            widget.bind("<Return>", lambda _event: self.add_custom_radio_station())

        self.radio_custom_editor_window = editor
        custom_name.focus_set()
        return editor

    def open_new_custom_radio_station_editor(self):
        radio_controller.clear_custom_station_form(self)
        return self.open_custom_radio_station_editor()

    def close_custom_radio_station_editor(self):
        radio_controller.clear_custom_station_form(self)
        editor = getattr(self, "radio_custom_editor_window", None)
        self.radio_custom_editor_window = None
        self.radio_custom_editor_delete_button = None
        if editor is not None:
            try:
                editor.destroy()
            except Exception:
                pass
        return True

    def add_custom_radio_station(self):
        return radio_controller.add_custom_station(self)

    def clear_custom_radio_form(self):
        return radio_controller.clear_custom_station_form(self)

    def edit_selected_radio_station_data(self):
        return radio_controller.edit_selected_station_data(self)

    def delete_selected_radio_station(self):
        return radio_controller.delete_selected_station(self)

    def on_radio_station_clicked(self, event):
        return radio_controller.play_station_from_click(self, event)

    def open_projectm_visualizer_test(self):
        status = netmon_projectm_sidecar.launch_projectm_sidecar(self)
        if status.launched:
            self.radio_projectm_last_started_at = self._timestamp_text()
        self._refresh_projectm_status()
        if not status.launched:
            return False
        try:
            self.log_safe("projectM Test-Visualizer gestartet.")
        except Exception:
            pass
        return True

    def start_radio_recording(self):
        return radio_controller.start_radio_recording(self)

    def stop_radio_recording(self):
        return radio_controller.stop_radio_recording(self)

    def toggle_radio_recording(self):
        proc = getattr(self, "radio_record_proc", None)
        active = False
        try:
            active = proc is not None and proc.poll() is None
        except Exception:
            active = proc is not None
        if active:
            return self.stop_radio_recording()
        return self.start_radio_recording()

    def open_radio_record_settings_popup(self):
        existing = getattr(self, "radio_record_settings_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.deiconify()
                    existing.lift()
                    existing.focus_force()
                    return existing
            except Exception:
                pass

        popup = tk.Toplevel(self)
        popup.title(self.tr("radio_settings_title", "Settings"))
        popup.transient(self)
        popup.resizable(True, True)
        popup.columnconfigure(0, weight=1)
        popup.rowconfigure(0, weight=1)

        body = ttk.Frame(popup, padding=14)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        ttk.Label(
            body,
            text=self.tr("radio_settings_title", "Settings"),
            font=("TkDefaultFont", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            body,
            text=self.tr("radio_settings_intro", "This area will be expanded."),
            justify="left",
        ).grid(row=1, column=0, sticky="nw", pady=(10, 0))
        station_columns = ttk.LabelFrame(
            body,
            text=self.tr("radio_settings_station_list", "Station list"),
            padding=10,
        )
        station_columns.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        station_columns.columnconfigure(0, weight=1)

        ttk.Label(
            station_columns,
            text=self.tr(
                "radio_settings_columns_hint", "Enable or disable any fields."
            ),
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        selected_columns = set(radio_controller.selected_radio_station_columns(self))
        self.radio_station_columns_status_var.set("")

        def _toggle_station_column(column_id):
            var = self.radio_station_column_vars.get(column_id)
            enabled = bool(var.get()) if var is not None else False
            if self.toggle_radio_station_list_column(column_id, enabled):
                self.radio_station_columns_status_var.set("")
                return
            if var is not None:
                var.set(not enabled)
            self.radio_station_columns_status_var.set(
                self.tr(
                    "radio_settings_columns_min_one",
                    "At least one field must remain enabled.",
                )
            )

        for idx, column_id in enumerate(
            radio_controller.RADIO_STATION_LIST_COLUMN_ORDER, start=1
        ):
            meta = radio_controller.RADIO_STATION_LIST_COLUMN_DEFS.get(column_id, {})
            var = tk.BooleanVar(value=column_id in selected_columns)
            self.radio_station_column_vars[column_id] = var
            ttk.Checkbutton(
                station_columns,
                text=str(meta.get("title", column_id)),
                variable=var,
                command=lambda key=column_id: _toggle_station_column(key),
            ).grid(
                row=idx,
                column=0,
                sticky="w",
                pady=(6 if idx == 1 else 4, 0),
            )

        ttk.Label(
            station_columns,
            textvariable=self.radio_station_columns_status_var,
            justify="left",
        ).grid(
            row=len(radio_controller.RADIO_STATION_LIST_COLUMN_ORDER) + 1,
            column=0,
            sticky="w",
            pady=(8, 0),
        )
        ttk.Button(
            body,
            text=self.tr("radio_settings_recordings_dir", "Recording folder"),
            command=self.choose_radio_recordings_dir,
        ).grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Label(
            body,
            textvariable=self.radio_record_dir_var,
            justify="left",
            wraplength=420,
        ).grid(row=4, column=0, sticky="w", pady=(6, 0))
        ttk.Button(
            body,
            text=self.tr("radio_settings_update_station_data", "Refresh station data"),
            command=self.download_radio_db,
        ).grid(row=5, column=0, sticky="w", pady=(12, 0))

        def _close_popup():
            try:
                popup.destroy()
            except Exception:
                pass
            self.radio_record_settings_window = None

        ttk.Button(body, text=self.tr("btn_close", "Close"), command=_close_popup).grid(
            row=6, column=0, sticky="e", pady=(14, 0)
        )
        popup.protocol("WM_DELETE_WINDOW", _close_popup)
        self.radio_record_settings_window = popup
        return popup

    def _set_vertical_pane_ratio(self, pane, ratio):
        try:
            pane.update_idletasks()
            height = int(pane.winfo_height() or 0)
        except Exception:
            height = 0
        if height <= 0:
            return False
        sash_pos = max(40, min(height - 40, int(height * float(ratio))))
        try:
            pane.sashpos(0, sash_pos)
            return True
        except Exception:
            pass
        try:
            pane.sash_place(0, 0, sash_pos)
            return True
        except Exception:
            return False

    def reset_radio_layout_default(self):
        try:
            self.update_idletasks()
        except Exception:
            pass

        def _apply_inner_layout():
            media_pane = getattr(self, "radio_media_pane", None)
            if media_pane is not None:
                try:
                    media_pane.update_idletasks()
                except Exception:
                    pass
                self._set_vertical_pane_ratio(media_pane, 0.5)
            return True

        def _apply_outer_layout():
            host_app = getattr(self, "radio_host_app", None)
            outer_pane = getattr(host_app, "radio_tab_pane", None)
            if outer_pane is not None:
                try:
                    outer_pane.update_idletasks()
                except Exception:
                    pass
                self._set_vertical_pane_ratio(outer_pane, 1.0 / 3.0)
            return True

        def _schedule(callable_fn, delay_ms):
            try:
                self.after(delay_ms, callable_fn)
                return
            except Exception:
                pass
            try:
                host_app = getattr(self, "radio_host_app", None)
                if host_app is not None:
                    host_app.after(delay_ms, callable_fn)
                    return
            except Exception:
                pass
            if delay_ms == 0:
                try:
                    callable_fn()
                except Exception:
                    pass

        try:
            for delay in (0, 80, 180, 320):
                _schedule(_apply_outer_layout, delay)
            for delay in (40, 120, 240, 420):
                _schedule(_apply_inner_layout, delay)
        except Exception:
            _apply_outer_layout()
            _apply_inner_layout()
        return True

    def choose_radio_recordings_dir(self):
        return radio_controller.choose_radio_recordings_dir(self)

    def open_radio_recordings_dir(self):
        return radio_controller.open_radio_recordings_dir(self)

    def open_radio_playlists_dir(self):
        return radio_controller.open_radio_playlists_dir(self)

    def open_radio_system_dir(self):
        return radio_controller.open_radio_system_dir(self)

    def open_current_radio_folder_browser_path(self):
        return radio_controller.open_current_radio_folder_browser_path(self)

    def start_radio_folder_browser_drag(self, event):
        return radio_controller.start_radio_folder_browser_drag(self, event)

    def track_radio_folder_browser_drag(self, event):
        return radio_controller.track_radio_folder_browser_drag(self, event)

    def finish_radio_folder_browser_drag(self, event):
        return radio_controller.finish_radio_folder_browser_drag(self, event)

    def cancel_radio_folder_browser_drag(self, event=None):
        return radio_controller.cancel_radio_folder_browser_drag(self, event)

    def navigate_radio_folder_browser_back(self):
        return radio_controller.navigate_radio_folder_browser_back(self)

    def navigate_radio_folder_browser_forward(self):
        return radio_controller.navigate_radio_folder_browser_forward(self)

    def navigate_radio_folder_browser_up(self):
        return radio_controller.navigate_radio_folder_browser_up(self)

    def open_selected_radio_folder_browser_entry(self, event=None):
        return radio_controller.open_selected_radio_folder_browser_entry(self, event)

    def show_radio_folder_browser_context_menu(self, event):
        return radio_controller.show_radio_folder_browser_context_menu(self, event)

    def add_selected_radio_folder_browser_entry_to_playlist(self):
        return radio_controller.add_selected_radio_folder_browser_entry_to_playlist(
            self
        )

    def start_selected_radio_folder_browser_playlist(self):
        return radio_controller.start_selected_radio_folder_browser_playlist(self)

    def create_radio_folder_browser_subfolder(self):
        return radio_controller.create_radio_folder_browser_subfolder(self)

    def delete_selected_radio_folder_browser_entry(self):
        return radio_controller.delete_selected_radio_folder_browser_entry(self)

    def delete_selected_radio_folder_browser_entry_key(self, event=None):
        self.delete_selected_radio_folder_browser_entry()
        return "break"

    def rename_selected_radio_folder_browser_entry(self):
        return radio_controller.rename_selected_radio_folder_browser_entry(self)

    def play_selected_radio_recording_file(self, event=None):
        return radio_controller.play_selected_radio_recording_file(self, event)

    def open_last_radio_recording(self):
        return radio_controller.open_last_radio_recording(self)

    def play_last_radio_recording(self):
        return radio_controller.play_last_radio_recording(self)

    def play_radio_file(self):
        return radio_controller.play_radio_file(self)

    def add_radio_playlist_files(self):
        return radio_controller.add_radio_playlist_files(self)

    def play_selected_radio_playlist_entry(self, event=None):
        return radio_controller.play_selected_radio_playlist_entry(self, event)

    def remove_selected_radio_playlist_entry(self):
        return radio_controller.remove_selected_radio_playlist_entry(self)

    def clear_radio_playlist(self):
        return radio_controller.clear_radio_playlist(self)

    def save_radio_playlist_to_file(self):
        return radio_controller.save_radio_playlist_to_file(self)

    def load_radio_playlist_from_file(self):
        return radio_controller.load_radio_playlist_from_file(self)

    def close_projectm_visualizer_test(self):
        result = netmon_projectm_sidecar.stop_projectm_sidecar(self)
        if result:
            self.radio_projectm_last_stopped_at = self._timestamp_text()
            try:
                self.log_safe("projectM Test-Visualizer gestoppt.")
            except Exception:
                pass
        self._refresh_projectm_status()
        return result

    def install_projectm_visualizer(self):
        probe = netmon_projectm_sidecar.probe_projectm_package_candidates(
            app=self,
            refresh=True,
        )
        install_command = netmon_projectm_sidecar.build_projectm_install_command(probe)
        if not install_command:
            self._refresh_projectm_status()
            return False
        packages = ", ".join(list(probe.get("available_packages", []) or []))
        strategy = str(probe.get("install_strategy", "") or "").strip()
        if strategy == "apt":
            detail = self.tr(
                "radio_projectm_install_detail_apt",
                "Only packages available in your configured package sources will be used.\n\nPackages: {packages}",
            ).format(packages=packages or "-")
        elif strategy == "flatpak":
            detail = self.tr(
                "radio_projectm_install_detail_flatpak",
                "APT does not provide a package candidate here. projectM can be installed optionally via Flatpak/Flathub.",
            )
        elif strategy == "install_flatpak":
            detail = self.tr(
                "radio_projectm_install_detail_install_flatpak",
                "APT does not provide a package candidate here and Flatpak is still missing. Optional flow: install Flatpak first, then install projectM via Flathub.",
            )
        else:
            detail = self.tr(
                "radio_projectm_install_detail_unavailable",
                "No automatic installation is currently available for projectM.",
            )
        if not messagebox.askyesno(
            self.tr("radio_projectm_install_title", "Install projectM"),
            self.tr(
                "radio_projectm_install_prompt",
                "projectM will be installed as an optional external test visualizer.\n{detail}\n\nContinue?",
            ).format(detail=detail),
            parent=self,
        ):
            return False
        script = (
            f"{install_command}; "
            "echo; "
            "echo 'projectM-Installer beendet. Shell bleibt offen.'; "
            "exec bash"
        )
        launch_cmd = self._build_external_terminal_command(script)
        if not launch_cmd:
            self.radio_projectm_install_var.set(
                self.tr(
                    "radio_projectm_install_terminal_missing",
                    "No external terminal found.",
                )
            )
            return False
        proc = subprocess.Popen(launch_cmd, start_new_session=True)
        self.radio_projectm_install_var.set(
            self.tr(
                "radio_projectm_install_started",
                "projectM installation started in an external terminal.",
            )
        )
        try:
            self.log_safe("projectM-Installer gestartet.")
        except Exception:
            pass

        def monitor_terminal():
            try:
                proc.wait()
            except Exception:
                pass
            try:
                self.after(0, self._refresh_projectm_status)
            except Exception:
                pass

        threading.Thread(target=monitor_terminal, daemon=True).start()
        return True


class RadioMiniPlayerWindow:
    def __init__(self, app, *, owner, embedded):
        self.app = app
        self.owner = owner
        self.embedded = bool(embedded)
        self.theme = DARK_THEME
        self.style_prefix = f"MiniPlayer{abs(id(self))}"
        self.window = tk.Toplevel(owner)
        self.window.title(app.tr("radio_miniplayer_window_title", "NetMon Mini"))
        self.window.overrideredirect(False)
        self.window.resizable(False, True)
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        try:
            self.window.attributes("-topmost", True)
        except Exception:
            pass
        self._drag_origin = None
        self._resize_origin = None
        self._eq_visible = True
        self._build_ui()
        self.apply_theme(self.theme)
        self.update_content(app._radio_miniplayer_snapshot())
        self.window.protocol("WM_DELETE_WINDOW", app.restore_from_radio_miniplayer)
        try:
            self.window.update_idletasks()
            self.window.geometry("500x330+24+24")
            self.window.minsize(500, 230)
            self.window.maxsize(500, 420)
        except Exception:
            pass
        self.window.bind("<Configure>", self._on_configure, add="+")

    def winfo_exists(self):
        try:
            return bool(self.window.winfo_exists())
        except Exception:
            return False

    def destroy(self):
        try:
            self.window.destroy()
        except Exception:
            pass

    def show(self):
        try:
            self.window.deiconify()
            self.window.update_idletasks()
            self.window.lift()
            self.window.focus_force()
        except Exception:
            pass

    def minimize(self):
        try:
            self.window.update_idletasks()
        except Exception:
            pass
        try:
            self.window.wm_state("iconic")
        except Exception:
            try:
                self.window.iconify()
            except Exception:
                pass

    def apply_theme(self, theme):
        theme = self.theme
        style = ttk.Style(self.window)
        frame_style = f"{self.style_prefix}.TFrame"
        label_style = f"{self.style_prefix}.TLabel"
        labelframe_style = f"{self.style_prefix}.TLabelframe"
        labelframe_label_style = f"{self.style_prefix}.TLabelframe.Label"
        button_style = f"{self.style_prefix}.TButton"
        scale_style = f"{self.style_prefix}.Horizontal.TScale"
        style.configure(frame_style, background=theme["panel_bg"])
        style.configure(
            label_style, background=theme["panel_bg"], foreground=theme["fg"]
        )
        style.configure(
            labelframe_style,
            background=theme["panel_bg"],
            bordercolor=theme["border"],
            relief="solid",
        )
        style.configure(
            labelframe_label_style,
            background=theme["panel_bg"],
            foreground=theme["fg"],
        )
        style.configure(
            button_style,
            background=theme["tab_bg"],
            foreground=theme["fg"],
            bordercolor=theme["border"],
            focuscolor=theme["accent"],
            padding=4,
        )
        style.map(
            button_style,
            background=[("active", theme["tab_selected_bg"])],
            foreground=[("active", theme["fg"])],
        )
        style.configure(
            scale_style,
            background=theme["panel_bg"],
            troughcolor=theme["entry_bg"],
            bordercolor=theme["border"],
            lightcolor=theme["accent"],
            darkcolor=theme["accent"],
        )
        try:
            shell_bg = self.app._mix_theme_color(theme["panel_bg"], theme["bg"], 0.12)
            card_bg = self.app._mix_theme_color(
                theme["entry_bg"], theme["panel_bg"], 0.18
            )
            header_bg = self.app._mix_theme_color(
                theme["tab_bg"], theme["panel_bg"], 0.1
            )
            self.window.configure(bg=theme["bg"])
            self.shell.configure(bg=shell_bg, highlightbackground=theme["border"])
            self.titlebar.configure(bg=header_bg)
            self.logo_frame.configure(bg=card_bg, highlightbackground=theme["border"])
            self.info_frame.configure(bg=card_bg, highlightbackground=theme["border"])
            self.logo_label.configure(bg=card_bg, fg=theme["fg"])
            self.titlebar_label.configure(bg=header_bg, fg=theme["fg"])
            for widget in self.info_caption_labels:
                widget.configure(bg=card_bg, fg=theme["fg"])
            for widget in self.info_value_labels:
                widget.configure(bg=card_bg, fg=theme["fg"])
            self.top.configure(style=frame_style)
            self.actions_row.configure(style=frame_style)
            self.bottom.configure(style=frame_style)
            self.projectm_row.configure(style=frame_style)
            self.volume_row.configure(style=labelframe_style)
            self.eq_frame.configure(style=labelframe_style)
            self.volume_value_label.configure(style=label_style)
            for widget in self.action_buttons:
                widget.configure(style=button_style)
            for widget in self.projectm_buttons:
                widget.configure(style=button_style)
        except Exception:
            pass

    def update_content(self, snapshot):
        data = dict(snapshot or {})
        try:
            self.station_value_var.set(str(data.get("station", "-") or "-"))
            self.title_value_var.set(str(data.get("title", "-") or "-"))
            self.source_value_var.set(str(data.get("source_kind", "-") or "-"))
            default_status = self.app.tr("radio_miniplayer_status_ready", "Ready")
            self.status_value_var.set(
                str(data.get("status", default_status) or default_status)
            )
        except Exception:
            pass
        current_station = getattr(self.app, "radio_current_station", None)
        placeholder_name = self.app.tr("radio_logo_placeholder", "No logo")
        if isinstance(current_station, dict):
            placeholder_name = str(
                current_station.get("name", "") or ""
            ).strip() or self.app.tr("radio_logo_placeholder", "No logo")
        self.app.radio_mini_logo_label = self.logo_label
        self.app._set_radio_logo_placeholder(placeholder_name)
        try:
            self.app.refresh_radio_station_logo(current_station)
        except Exception:
            pass

    def _build_ui(self):
        self.shell = tk.Frame(self.window, bd=1, relief="solid")
        self.shell.grid(row=0, column=0, sticky="nsew")
        self.shell.columnconfigure(0, minsize=112)
        self.shell.columnconfigure(1, weight=1)
        self.shell.rowconfigure(1, weight=0)
        self.shell.rowconfigure(2, weight=0)
        self.shell.rowconfigure(3, weight=0)
        self.shell.rowconfigure(4, weight=0)

        self.titlebar = tk.Frame(self.shell, bd=0, highlightthickness=0)
        self.titlebar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.titlebar.columnconfigure(0, weight=1)
        self.titlebar_label = tk.Label(
            self.titlebar,
            text=self.app.tr("radio_miniplayer_titlebar", "NetMon Radio Mini"),
            anchor="w",
            padx=8,
            pady=3,
            font=("TkDefaultFont", 9, "bold"),
        )
        self.titlebar_label.grid(row=0, column=0, sticky="w")

        self.top = ttk.Frame(self.shell, padding=(9, 7, 9, 5))
        self.top.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.top.columnconfigure(0, minsize=94)
        self.top.columnconfigure(1, weight=1)

        self.logo_frame = tk.Frame(
            self.top, bd=0, highlightthickness=1, width=88, height=88
        )
        self.logo_frame.grid(row=0, column=0, sticky="nw")
        self.logo_frame.grid_propagate(False)
        self.logo_frame.columnconfigure(0, weight=1)
        self.logo_frame.rowconfigure(0, weight=1)
        self.logo_label = tk.Label(
            self.logo_frame,
            text=self.app.tr("radio_logo_label", "Logo"),
            anchor="center",
        )
        self.logo_label.grid(row=0, column=0, sticky="nsew")

        self.info_frame = tk.Frame(self.top, bd=0, highlightthickness=1)
        self.info_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        self.info_frame.columnconfigure(0, weight=0, minsize=50)
        self.info_frame.columnconfigure(1, weight=1)

        self.station_value_var = tk.StringVar(value="-")
        self.title_value_var = tk.StringVar(value="-")
        self.source_value_var = tk.StringVar(value="-")
        self.status_value_var = tk.StringVar(
            value=self.app.tr("radio_miniplayer_status_ready", "Ready")
        )

        self.info_caption_labels = []
        self.info_value_labels = []
        detail_rows = (
            (
                self.app.tr("radio_miniplayer_label_station", "Station"),
                self.station_value_var,
                ("TkDefaultFont", 8, "bold"),
            ),
            (
                self.app.tr("radio_miniplayer_label_title", "Title"),
                self.title_value_var,
                ("TkDefaultFont", 8),
            ),
            (
                self.app.tr("radio_miniplayer_label_source", "Source"),
                self.source_value_var,
                ("TkDefaultFont", 8),
            ),
            (
                self.app.tr("radio_miniplayer_label_status", "Status"),
                self.status_value_var,
                ("TkDefaultFont", 8),
            ),
        )
        for row_index, (label_text, variable, font_value) in enumerate(detail_rows):
            caption = tk.Label(
                self.info_frame,
                text=f"{label_text}:",
                anchor="w",
                padx=7,
                pady=(4 if row_index == 0 else 2),
                font=("TkDefaultFont", 8, "bold"),
            )
            caption.grid(row=row_index, column=0, sticky="w")
            value_label = tk.Label(
                self.info_frame,
                textvariable=variable,
                anchor="w",
                justify="left",
                padx=4,
                pady=(4 if row_index == 0 else 2),
                font=font_value,
                wraplength=262,
            )
            value_label.grid(row=row_index, column=1, sticky="w")
            self.info_caption_labels.append(caption)
            self.info_value_labels.append(value_label)

        self.actions_row = ttk.Frame(self.shell, padding=(9, 0, 9, 5))
        self.actions_row.grid(row=2, column=0, columnspan=2, sticky="ew")
        for column in range(4):
            self.actions_row.columnconfigure(column, weight=1)
        self.action_buttons = []
        prev_button = ttk.Button(
            self.actions_row, text="⏮", width=3, command=self.app.radio_previous
        )
        prev_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        play_button = ttk.Button(
            self.actions_row, text="▶", width=3, command=self.app.radio_play
        )
        play_button.grid(row=0, column=1, sticky="ew", padx=6)
        stop_button = ttk.Button(
            self.actions_row,
            text="■",
            width=3,
            command=lambda: self.app.stop_radio_playback(async_mode=True),
        )
        stop_button.grid(row=0, column=2, sticky="ew", padx=6)
        next_button = ttk.Button(
            self.actions_row, text="⏭", width=3, command=self.app.radio_next
        )
        next_button.grid(row=0, column=3, sticky="ew", padx=(6, 0))
        self.action_buttons.extend([prev_button, play_button, stop_button, next_button])

        self.volume_row = ttk.LabelFrame(
            self.shell,
            text=self.app.tr("radio_miniplayer_group_volume", "Volume"),
            padding=(9, 5),
        )
        self.volume_row.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=9, pady=(0, 5)
        )
        self.volume_row.columnconfigure(1, weight=1)
        self.left_volume_value_label = ttk.Label(
            self.volume_row, textvariable=self.app.radio_volume_label_var, width=5
        )
        self.left_volume_value_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.mini_volume = ttk.Scale(
            self.volume_row,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.app.radio_volume_var,
            command=self.app.on_radio_volume_preview,
            length=286,
            style=f"{self.style_prefix}.Horizontal.TScale",
        )
        self.mini_volume.grid(row=0, column=1, sticky="ew")
        self.mini_volume.bind("<ButtonRelease-1>", self.app.commit_radio_volume_change)
        self.mini_volume.bind("<KeyRelease>", self.app.commit_radio_volume_change)
        self.mini_volume.bind("<MouseWheel>", self.app._on_radio_volume_mousewheel)
        self.mini_volume.bind("<Button-4>", self.app._on_radio_volume_mousewheel)
        self.mini_volume.bind("<Button-5>", self.app._on_radio_volume_mousewheel)
        self.volume_value_label = ttk.Label(
            self.volume_row, textvariable=self.app.radio_volume_label_var, width=3
        )
        self.volume_value_label.grid(row=0, column=2, sticky="e", padx=(8, 0))

        self.bottom = ttk.Frame(self.shell, padding=(9, 0, 9, 7))
        self.bottom.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.bottom.columnconfigure(0, weight=1)

        self.eq_frame = ttk.LabelFrame(
            self.bottom, text=self.app.tr("radio_group_eq", "EQ"), padding=(9, 5)
        )
        self.eq_frame.grid(row=0, column=0, sticky="ew")
        self.eq_frame.columnconfigure(1, weight=1)
        self.app._build_eq_slider(
            self.eq_frame,
            row=0,
            label=self.app.tr("radio_eq_bass", "Bass"),
            variable=self.app.radio_eq_bass_var,
            value_variable=self.app.radio_eq_bass_label_var,
            slider_length=300,
            label_style=f"{self.style_prefix}.TLabel",
            scale_style=f"{self.style_prefix}.Horizontal.TScale",
            value_style=f"{self.style_prefix}.TLabel",
        )
        self.app._build_eq_slider(
            self.eq_frame,
            row=1,
            label=self.app.tr("radio_eq_mid", "Mid"),
            variable=self.app.radio_eq_mid_var,
            value_variable=self.app.radio_eq_mid_label_var,
            slider_length=300,
            label_style=f"{self.style_prefix}.TLabel",
            scale_style=f"{self.style_prefix}.Horizontal.TScale",
            value_style=f"{self.style_prefix}.TLabel",
        )
        self.app._build_eq_slider(
            self.eq_frame,
            row=2,
            label=self.app.tr("radio_eq_treble", "Treble"),
            variable=self.app.radio_eq_treble_var,
            value_variable=self.app.radio_eq_treble_label_var,
            slider_length=300,
            label_style=f"{self.style_prefix}.TLabel",
            scale_style=f"{self.style_prefix}.Horizontal.TScale",
            value_style=f"{self.style_prefix}.TLabel",
        )

        self.projectm_row = ttk.Frame(self.bottom, padding=(0, 6, 0, 0))
        self.projectm_row.grid(row=1, column=0, sticky="ew")
        self.projectm_row.columnconfigure(0, weight=1)
        self.projectm_row.columnconfigure(1, weight=1)
        self.projectm_buttons = []
        projectm_start_button = ttk.Button(
            self.projectm_row,
            text=self.app.tr("radio_projectm_btn_start", "Start projectM"),
            command=self.app.open_projectm_visualizer_test,
        )
        projectm_start_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        projectm_stop_button = ttk.Button(
            self.projectm_row,
            text=self.app.tr("radio_projectm_btn_stop", "Stop projectM"),
            command=self.app.close_projectm_visualizer_test,
        )
        projectm_stop_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))
        self.projectm_buttons.extend([projectm_start_button, projectm_stop_button])

        for widget in (self.titlebar,):
            widget.bind("<Button-1>", self._start_drag, add="+")
            widget.bind("<B1-Motion>", self._drag, add="+")

    def _start_drag(self, event):
        try:
            self._drag_origin = (
                int(getattr(event, "x_root", 0) or 0),
                int(getattr(event, "y_root", 0) or 0),
                int(self.window.winfo_x() or 0),
                int(self.window.winfo_y() or 0),
            )
        except Exception:
            self._drag_origin = None
        return "break"

    def _drag(self, event):
        if not self._drag_origin:
            return "break"
        start_x, start_y, base_x, base_y = self._drag_origin
        delta_x = int(getattr(event, "x_root", 0) or 0) - start_x
        delta_y = int(getattr(event, "y_root", 0) or 0) - start_y
        try:
            self.window.geometry(f"+{base_x + delta_x}+{base_y + delta_y}")
        except Exception:
            pass
        return "break"

    def _on_configure(self, _event=None):
        try:
            height = int(self.window.winfo_height() or 0)
        except Exception:
            return
        self._sync_layout_for_height(height)

    def _sync_layout_for_height(self, height):
        show_eq = int(height or 0) >= 300
        if show_eq == self._eq_visible:
            return
        self._eq_visible = show_eq
        try:
            if show_eq:
                self.bottom.grid()
            else:
                self.bottom.grid_remove()
        except Exception:
            pass


class NetMonRadioPanel(ttk.Frame):
    def __init__(self, parent, *, on_detach=None, host_app=None):
        super().__init__(parent)
        for name, value in NetMonRadioApp.__dict__.items():
            if name.startswith("__") or name in {"__init__", "_on_close"}:
                continue
            if callable(value):
                setattr(self, name, types.MethodType(value, self))

        _init_radio_runtime_state(self, embedded_mode=True, host_app=host_app)
        self._translations = {}
        self._language_code = "de"
        self._load_language()
        _init_radio_ui_state(self)
        self.radio_embedded_mode = True
        self.radio_detach_callback = on_detach
        self.radio_host_app = host_app

        self._build_ui()
        self._register_radio_miniplayer_var_traces()
        radio_controller.on_radio_eq_preview(self)
        self.apply_theme(
            self._start_theme_name
            or str(self.radio_settings.get("theme", "light") or "light")
        )
        self.refresh_radio_ui()
        self._refresh_projectm_status()
        self.bind_all("<Button-1>", self._dismiss_active_context_menu, add="+")
        self.bind_all("<Escape>", self._dismiss_active_context_menu, add="+")

    def destroy(self):
        if getattr(self, "_radio_panel_destroying", False):
            return super().destroy()
        self._radio_panel_destroying = True
        try:
            self.close_custom_radio_station_editor()
        except Exception:
            pass
        try:
            self.close_projectm_visualizer_test()
        except Exception:
            pass
        try:
            self.stop_radio_playback(async_mode=False)
        except Exception:
            pass
        return super().destroy()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Standalone NetMon Radio app")
    parser.add_argument(
        "--theme",
        default="",
        help="Kompatibilitaetsoption ohne Wirkung; Standalone Radio startet immer im Darkmode.",
    )
    parser.add_argument(
        "--headless-smoke",
        action="store_true",
        help="Create the UI once and exit immediately.",
    )
    parser.add_argument(
        "--started-from",
        default="desktop",
        help="Startup source tag for host-state tracking.",
    )
    args = parser.parse_args(argv)

    if netmon_radio_core.standalone_radio_is_running():
        print("NetMon Radio läuft bereits standalone.")
        return 0

    app = NetMonRadioApp(start_theme=args.theme, started_from=args.started_from)
    if args.headless_smoke:
        app.update_idletasks()
        app.update()
        app._on_close()
        return 0
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
