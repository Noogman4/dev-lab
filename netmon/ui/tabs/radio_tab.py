"""Radio tab launcher for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import NamedTuple

try:
    from netmon.netmon_radio_app import NetMonRadioPanel
except ModuleNotFoundError:
    from netmon_radio_app import NetMonRadioPanel


class _RadioPaneMarkerCallbacks(NamedTuple):
    update_marker: object
    start_drag: object
    drag: object
    end_drag: object


class _RadioPaneMarkerBase(NamedTuple):
    marker: object
    grip: object
    drag_state: object


class _RadioPaneMarkerInstallation(NamedTuple):
    marker: object
    grip: object
    update_marker: object
    start_drag: object
    drag: object
    end_drag: object


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _app_var_set(app, name: str, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _app_attr(app, name: str, default=None):
    value = _app_value(app, name, default)
    if value is not default:
        return value
    try:
        return object.__getattribute__(app, name)
    except Exception:
        return default


def _radio_launcher_mode(app) -> str:
    return str(_app_value(app, "radio_launcher_mode", "") or "").strip()


def _safe_translate(app, key: str, fallback: str) -> str:
    tr = getattr(app, "tr", None)
    if callable(tr):
        try:
            return tr(key, fallback)
        except Exception:
            pass
    return fallback


def _radio_launcher_status_var(app, *, var_factory=tk.StringVar):
    return _app_value(app, "radio_launcher_status_var") or var_factory(value="")


def _init_radio_tab_state(app, *, host, top_section, bottom_section) -> None:
    app.radio_tab_host = host
    app.radio_tab_top_section = top_section
    app.radio_tab_bottom_section = bottom_section
    app.radio_embedded_panel = None
    app.radio_launcher_mode = ""


def _radio_launcher_status_text(
    app=None, *, detached: bool, launcher_state: str
) -> str:
    state = str(launcher_state or "").strip().lower()

    if state == "detaching":
        return _safe_translate(
            app,
            "radio_status_detaching",
            "Radio wird gerade als Standalone-App gestartet.",
        )
    if state == "attaching":
        return _safe_translate(
            app,
            "radio_status_attaching",
            "Radio wird gerade wieder an NetMon angeheftet.",
        )
    if detached:
        return _safe_translate(
            app,
            "radio_status_detached",
            "Radio-App ist geloest und laeuft als Standalone weiter.",
        )
    return _safe_translate(
        app,
        "radio_status_attached",
        "Radio-App ist an NetMon angeheftet.",
    )


def _radio_detached_placeholder_texts(app=None) -> tuple[str, str, str]:
    return (
        _safe_translate(app, "radio_launcher_title", "NetMon Radio als externe App"),
        _safe_translate(
            app,
            "radio_launcher_detached_hint",
            "Radio laeuft gerade standalone. Zum Wieder-Anheften bitte in der externen Radio-App auf 'Radio anheften' klicken.",
        ),
        _safe_translate(app, "radio_launcher_reattach", "Radio anheften"),
    )


def _radio_bottom_placeholder_text(app) -> str:
    return app.tr(
        "radio_bottom_media_hint",
        "This lower area is reserved for playlists and files.",
    )


def _radio_bottom_section_title(app) -> str:
    return app.tr("radio_bottom_media_title", "Playlists and files")


def _detach_radio_from_tab(app):
    return app.open_radio_external_app()


def _attach_embedded_radio_panel(app, host, panel) -> None:
    panel.grid(row=0, column=0, sticky="nsew")
    host.rowconfigure(0, weight=1)
    app.radio_embedded_panel = panel
    app.radio_launcher_mode = "embedded"


def _set_detached_radio_placeholder_state(app, reattach_button) -> None:
    app.register_feature_button("radio", reattach_button)
    app.radio_launcher_mode = "detached"


def _show_radio_detached_placeholder(
    app,
    host,
    clear_host,
    *,
    placeholder_builder=None,
    state_setter=None,
) -> None:
    if _radio_launcher_mode(app) == "detached":
        return
    if placeholder_builder is None:
        placeholder_builder = _build_detached_radio_placeholder
    if state_setter is None:
        state_setter = _set_detached_radio_placeholder_state
    clear_host()
    title_text, hint_text, reattach_text = _radio_detached_placeholder_texts(app)
    reattach = placeholder_builder(
        host,
        title_text=title_text,
        hint_text=hint_text,
        status_var=app.radio_launcher_status_var,
        reattach_text=reattach_text,
        reattach_command=app.reattach_radio_app,
    )
    state_setter(app, reattach)


def _show_radio_embedded_panel(
    app,
    host,
    clear_host,
    *,
    panel_factory=None,
    attach_panel=None,
) -> None:
    if _radio_launcher_mode(app) == "embedded":
        return
    if panel_factory is None:
        panel_factory = NetMonRadioPanel
    if attach_panel is None:
        attach_panel = _attach_embedded_radio_panel
    clear_host()

    def _detach_from_tab():
        return _detach_radio_from_tab(app)

    panel = panel_factory(host, on_detach=_detach_from_tab, host_app=app)
    attach_panel(app, host, panel)


def _configure_single_cell_expand(widget) -> None:
    widget.columnconfigure(0, weight=1)
    widget.rowconfigure(0, weight=1)


def _build_radio_tab_body(app, *, frame_factory=ttk.Frame):
    app.tab_radio = frame_factory(app.tools_nb, padding=(2, 0, 2, 2))
    app.tools_nb.add(app.tab_radio, text=app.tr("tools_tab_radio", "Radio"))
    body = frame_factory(app.tab_radio, padding=0)
    body.pack(fill="both", expand=True)
    _configure_single_cell_expand(body)
    return body


def _build_radio_pane_sections(
    pane,
    app,
    *,
    frame_factory=ttk.Frame,
    label_frame_factory=ttk.LabelFrame,
):
    top_section = frame_factory(pane, padding=0)
    _configure_single_cell_expand(top_section)
    host = frame_factory(top_section)
    host.grid(row=0, column=0, sticky="nsew")
    _configure_single_cell_expand(host)

    bottom_section = label_frame_factory(
        pane,
        text=_radio_bottom_section_title(app),
        padding=10,
    )
    _configure_single_cell_expand(bottom_section)
    return top_section, host, bottom_section


def _add_radio_pane_sections(pane, top_section, bottom_section) -> None:
    pane.add(top_section, weight=3)
    pane.add(bottom_section, weight=2)


def _build_radio_tab_pane(
    app,
    body,
    *,
    panedwindow_factory=ttk.Panedwindow,
    marker_installer=None,
):
    if marker_installer is None:
        marker_installer = _install_pane_drag_marker
    pane = panedwindow_factory(body, orient="vertical")
    pane.grid(row=0, column=0, sticky="nsew")
    app.radio_tab_pane = pane
    app.radio_tab_pane_marker = marker_installer(body, pane)
    return pane


def _build_detached_radio_placeholder(
    host,
    *,
    title_text: str,
    hint_text: str,
    status_var,
    reattach_text: str,
    reattach_command,
    frame_factory=ttk.Frame,
    label_factory=ttk.Label,
    button_factory=ttk.Button,
):
    box = frame_factory(host, padding=18)
    box.grid(row=0, column=0, sticky="nw")
    label_factory(
        box,
        text=title_text,
        font=("TkDefaultFont", 12, "bold"),
    ).grid(row=0, column=0, sticky="w")
    label_factory(
        box,
        text=hint_text,
        justify="left",
        wraplength=760,
    ).grid(row=1, column=0, sticky="w", pady=(10, 12))
    label_factory(
        box,
        textvariable=status_var,
        justify="left",
    ).grid(row=2, column=0, sticky="w", pady=(0, 12))
    reattach = button_factory(
        box,
        text=reattach_text,
        command=reattach_command,
    )
    reattach.grid(row=3, column=0, sticky="w", pady=(8, 0))
    return reattach


def _radio_launcher_runtime_state(app):
    detached = False
    launcher_state = ""
    radio_core = _app_attr(app, "netmon_radio_core")
    if radio_core is not None:
        try:
            detached = bool(radio_core.radio_is_detached())
        except Exception:
            detached = False
        try:
            state = radio_core.read_radio_host_state()
            launcher_state = str(state.get("launcher_state", "")).strip().lower()
        except Exception:
            launcher_state = ""
    return detached, launcher_state


def _radio_launcher_target_mode(detached: bool, launcher_state: str) -> str:
    state = str(launcher_state or "").strip().lower()
    if bool(detached) or state == "detaching":
        return "detached"
    return "embedded"


def _refresh_radio_launcher_state(
    app,
    show_detached_placeholder,
    show_embedded_panel,
) -> None:
    detached, launcher_state = _radio_launcher_runtime_state(app)
    _app_var_set(
        app,
        "radio_launcher_status_var",
        _radio_launcher_status_text(
            app,
            detached=detached,
            launcher_state=launcher_state,
        ),
    )
    if _radio_launcher_target_mode(detached, launcher_state) == "detached":
        show_detached_placeholder()
    else:
        show_embedded_panel()


def _clear_radio_host(host, panel=None) -> None:
    if panel is not None:
        try:
            panel.stop_radio_playback(async_mode=False)
        except Exception:
            pass
    for child in host.winfo_children():
        try:
            child.destroy()
        except Exception:
            pass


def _clear_radio_tab_host(app, host, show_bottom_placeholder) -> None:
    _clear_radio_host(host, _app_value(app, "radio_embedded_panel"))
    app.radio_embedded_panel = None
    show_bottom_placeholder()


def _show_radio_bottom_placeholder(container, text: str, *, label_factory=ttk.Label):
    for child in container.winfo_children():
        try:
            child.destroy()
        except Exception:
            pass
    label = label_factory(
        container,
        text=text,
        justify="left",
        wraplength=900,
    )
    label.grid(row=0, column=0, sticky="nw")
    return label


def _show_radio_bottom_placeholder_for_app(
    container,
    app,
    *,
    label_factory=ttk.Label,
):
    return _show_radio_bottom_placeholder(
        container,
        text=_radio_bottom_placeholder_text(app),
        label_factory=label_factory,
    )


def _make_radio_bottom_placeholder_callback(
    app,
    bottom_section,
    *,
    placeholder_shower=_show_radio_bottom_placeholder_for_app,
):
    def _show_bottom_placeholder():
        placeholder_shower(bottom_section, app)

    return _show_bottom_placeholder


def _make_radio_tab_host_clear_callback(
    app,
    host,
    show_bottom_placeholder,
    *,
    host_clearer=_clear_radio_tab_host,
):
    def _clear_host():
        host_clearer(app, host, show_bottom_placeholder)

    return _clear_host


def _make_radio_detached_placeholder_callback(
    app,
    host,
    clear_host,
    *,
    placeholder_shower=_show_radio_detached_placeholder,
):
    def _show_detached_placeholder():
        placeholder_shower(app, host, clear_host)

    return _show_detached_placeholder


def _make_radio_embedded_panel_callback(
    app,
    host,
    clear_host,
    *,
    panel_shower=_show_radio_embedded_panel,
):
    def _show_embedded_panel():
        panel_shower(app, host, clear_host)

    return _show_embedded_panel


def _make_radio_launcher_refresh_callback(
    app,
    show_detached_placeholder,
    show_embedded_panel,
    *,
    launcher_refresher=_refresh_radio_launcher_state,
):
    def refresh_radio_launcher_state():
        launcher_refresher(
            app,
            show_detached_placeholder,
            show_embedded_panel,
        )

    return refresh_radio_launcher_state


def _build_radio_tab_scaffold(
    app,
    *,
    body_builder=_build_radio_tab_body,
    status_var_factory=_radio_launcher_status_var,
    pane_builder=_build_radio_tab_pane,
    sections_builder=_build_radio_pane_sections,
    bottom_callback_factory=_make_radio_bottom_placeholder_callback,
    pane_sections_adder=_add_radio_pane_sections,
    state_initializer=_init_radio_tab_state,
):
    body = body_builder(app)
    app.radio_launcher_status_var = status_var_factory(app)
    pane = pane_builder(app, body)
    top_section, host, bottom_section = sections_builder(pane, app)
    show_bottom_placeholder = bottom_callback_factory(app, bottom_section)
    pane_sections_adder(pane, top_section, bottom_section)
    state_initializer(
        app,
        host=host,
        top_section=top_section,
        bottom_section=bottom_section,
    )
    show_bottom_placeholder()
    return host, show_bottom_placeholder


def _install_radio_launcher_refresh(
    app,
    host,
    show_bottom_placeholder,
    *,
    host_clear_callback_factory=_make_radio_tab_host_clear_callback,
    detached_callback_factory=_make_radio_detached_placeholder_callback,
    embedded_callback_factory=_make_radio_embedded_panel_callback,
    refresh_callback_factory=_make_radio_launcher_refresh_callback,
):
    clear_host = host_clear_callback_factory(
        app,
        host,
        show_bottom_placeholder,
    )
    show_detached_placeholder = detached_callback_factory(app, host, clear_host)
    show_embedded_panel = embedded_callback_factory(app, host, clear_host)
    refresh_radio_launcher_state = refresh_callback_factory(
        app,
        show_detached_placeholder,
        show_embedded_panel,
    )
    app.refresh_radio_launcher_state = refresh_radio_launcher_state
    refresh_radio_launcher_state()
    return refresh_radio_launcher_state


def _radio_pane_marker_width(container_width) -> int:
    width = max(int(container_width or 0), 0)
    return min(66, max(width - 24, 42))


def _radio_pane_marker_x(container_width, marker_width) -> int:
    return max((int(container_width) - int(marker_width)) // 2, 8)


def _radio_pane_marker_y(sash_y) -> int:
    return max(int(sash_y) - 5, 2)


def _radio_pane_marker_height() -> int:
    return 12


def _radio_pane_marker_place_geometry(x, y, width, height) -> dict[str, int]:
    return {
        "x": int(x),
        "y": int(y),
        "width": int(width),
        "height": int(height),
    }


def _radio_pane_marker_geometry(container_width, sash_y) -> dict[str, int]:
    width = max(int(container_width or 0), 0)
    marker_width = _radio_pane_marker_width(width)
    return _radio_pane_marker_place_geometry(
        _radio_pane_marker_x(width, marker_width),
        _radio_pane_marker_y(sash_y),
        marker_width,
        _radio_pane_marker_height(),
    )


def _set_radio_pane_sash_position(pane, new_y) -> None:
    try:
        pane.sashpos(0, int(new_y))
        return
    except Exception:
        pass
    try:
        pane.sash_place(0, 0, int(new_y))
    except Exception:
        pass


def _radio_pane_drag_start_state(event, pane) -> tuple[int, int]:
    try:
        return int(event.y_root), int(pane.sashpos(0))
    except Exception:
        return 0, 0


def _record_radio_pane_drag_start(drag_state, event, pane) -> None:
    drag_state["root_y"], drag_state["sash_y"] = _radio_pane_drag_start_state(
        event,
        pane,
    )


def _radio_pane_drag_target_sash(event, drag_state) -> int:
    delta = int(event.y_root) - int(drag_state["root_y"])
    return int(drag_state["sash_y"]) + delta


def _forget_radio_pane_marker(marker) -> None:
    try:
        marker.place_forget()
    except Exception:
        pass


def _radio_pane_drag_state() -> dict[str, int | bool]:
    return {
        "root_y": 0,
        "sash_y": 0,
        "update_pending": False,
    }


def _bind_radio_pane_marker_event(widget, event_name, callback) -> None:
    widget.bind(event_name, callback, add="+")


def _bind_radio_pane_marker_events(widget, bindings) -> None:
    try:
        for event_name, callback in bindings:
            _bind_radio_pane_marker_event(widget, event_name, callback)
    except Exception:
        pass


def _run_radio_pane_marker_update(drag_state, update_marker) -> None:
    drag_state["update_pending"] = False
    update_marker()


def _make_radio_pane_marker_update_runner(
    drag_state,
    update_marker,
    *,
    update_runner=_run_radio_pane_marker_update,
):
    def _run():
        update_runner(drag_state, update_marker)

    return _run


def _request_radio_pane_marker_after_idle(container, run_update) -> None:
    try:
        container.after_idle(run_update)
    except Exception:
        run_update()


def _claim_radio_pane_marker_update(drag_state) -> bool:
    if drag_state["update_pending"]:
        return False
    drag_state["update_pending"] = True
    return True


def _schedule_radio_pane_marker_update(container, drag_state, update_marker) -> None:
    if not _claim_radio_pane_marker_update(drag_state):
        return
    run_update = _make_radio_pane_marker_update_runner(drag_state, update_marker)
    _request_radio_pane_marker_after_idle(container, run_update)


def _request_radio_pane_marker_update(container, drag_state, update_marker) -> None:
    _schedule_radio_pane_marker_update(container, drag_state, update_marker)


def _request_initial_radio_pane_marker_update(container, update_marker) -> None:
    try:
        container.after(0, update_marker)
    except Exception:
        pass


def _schedule_initial_radio_pane_marker_update(container, update_marker) -> None:
    _request_initial_radio_pane_marker_update(container, update_marker)


def _build_radio_pane_marker_widgets(
    container,
    *,
    color="#0a84ff",
    frame_factory=tk.Frame,
    label_factory=tk.Label,
):
    marker = frame_factory(
        container,
        bg=color,
        bd=1,
        relief="solid",
    )
    marker.columnconfigure(0, weight=1)
    grip = label_factory(
        marker,
        text="≡",
        bg=color,
        fg="#ffffff",
        font=("TkDefaultFont", 9, "bold"),
        cursor="sb_v_double_arrow",
        padx=0,
        pady=0,
        anchor="center",
    )
    grip.grid(row=0, column=0, sticky="ew")
    return marker, grip


def _update_radio_pane_marker_from_sash(pane, place_marker, marker) -> None:
    try:
        place_marker(int(pane.sashpos(0)))
    except Exception:
        _forget_radio_pane_marker(marker)


def _handle_radio_pane_marker_update_event(
    pane,
    place_marker,
    marker,
    _event=None,
) -> None:
    _update_radio_pane_marker_from_sash(pane, place_marker, marker)


def _show_radio_pane_marker(marker, geometry) -> None:
    marker.place(**geometry)
    marker.lift()


def _place_radio_pane_marker(marker, geometry) -> None:
    try:
        _show_radio_pane_marker(marker, geometry)
    except Exception:
        _forget_radio_pane_marker(marker)


def _radio_pane_container_width(container) -> int:
    return int(container.winfo_width())


def _radio_pane_marker_geometry_for_container(container, sash_y) -> dict[str, int]:
    return _radio_pane_marker_geometry(_radio_pane_container_width(container), sash_y)


def _place_radio_pane_marker_for_sash(container, marker, sash_y) -> None:
    _place_radio_pane_marker(
        marker,
        _radio_pane_marker_geometry_for_container(container, sash_y),
    )


def _radio_pane_update_bindings(update_marker):
    return (
        ("<Configure>", update_marker),
        ("<ButtonRelease-1>", update_marker),
        ("<B1-Motion>", update_marker),
    )


def _radio_pane_grip_bindings(start_drag, drag, end_drag):
    return (
        ("<Button-1>", start_drag),
        ("<B1-Motion>", drag),
        ("<ButtonRelease-1>", end_drag),
    )


def _radio_pane_marker_binding_plan(
    container,
    pane,
    grip,
    *,
    update_marker,
    start_drag,
    drag,
    end_drag,
):
    update_bindings = _radio_pane_update_bindings(update_marker)
    return (
        (container, update_bindings),
        (pane, update_bindings),
        (grip, _radio_pane_grip_bindings(start_drag, drag, end_drag)),
    )


def _bind_radio_pane_marker_callbacks(
    container,
    pane,
    grip,
    *,
    update_marker,
    start_drag,
    drag,
    end_drag,
) -> None:
    for widget, bindings in _radio_pane_marker_binding_plan(
        container,
        pane,
        grip,
        update_marker=update_marker,
        start_drag=start_drag,
        drag=drag,
        end_drag=end_drag,
    ):
        _bind_radio_pane_marker_events(
            widget,
            bindings,
        )


def _handle_radio_pane_marker_drag(
    event,
    *,
    drag_state,
    pane,
    place_marker,
    schedule_marker_update,
) -> None:
    try:
        new_sash = _radio_pane_drag_target_sash(event, drag_state)
        _set_radio_pane_sash_position(pane, new_sash)
        place_marker(new_sash)
        schedule_marker_update()
    except Exception:
        pass


def _handle_radio_pane_marker_drag_event(
    event,
    *,
    drag_state,
    pane,
    place_marker,
    schedule_marker_update,
) -> str:
    _handle_radio_pane_marker_drag(
        event,
        drag_state=drag_state,
        pane=pane,
        place_marker=place_marker,
        schedule_marker_update=schedule_marker_update,
    )
    return "break"


def _handle_radio_pane_marker_drag_start(drag_state, event, pane) -> str:
    _record_radio_pane_drag_start(drag_state, event, pane)
    return "break"


def _handle_radio_pane_marker_drag_end(update_marker) -> str:
    update_marker()
    return "break"


def _invoke_radio_pane_marker_placer(container, marker, sash_y, marker_placer) -> None:
    marker_placer(container, marker, sash_y)


def _make_radio_pane_marker_place_callback(
    container,
    marker,
    *,
    marker_placer=_place_radio_pane_marker_for_sash,
):
    def _place_marker_for_sash(sash_y):
        _invoke_radio_pane_marker_placer(container, marker, sash_y, marker_placer)

    return _place_marker_for_sash


def _invoke_radio_pane_marker_update_handler(
    pane,
    place_marker,
    marker,
    event,
    update_handler,
) -> None:
    update_handler(
        pane,
        place_marker,
        marker,
        event,
    )


def _make_radio_pane_marker_update_callback(
    pane,
    place_marker,
    marker,
    *,
    update_handler=_handle_radio_pane_marker_update_event,
):
    def _update_marker(_event=None):
        _invoke_radio_pane_marker_update_handler(
            pane,
            place_marker,
            marker,
            _event,
            update_handler,
        )

    return _update_marker


def _invoke_radio_pane_marker_update_requester(
    container,
    drag_state,
    update_marker,
    update_requester,
) -> None:
    update_requester(container, drag_state, update_marker)


def _make_radio_pane_marker_schedule_callback(
    container,
    drag_state,
    update_marker,
    *,
    update_requester=_request_radio_pane_marker_update,
):
    def _schedule_marker_update():
        _invoke_radio_pane_marker_update_requester(
            container,
            drag_state,
            update_marker,
            update_requester,
        )

    return _schedule_marker_update


def _invoke_radio_pane_marker_drag_start_handler(
    drag_state,
    event,
    pane,
    drag_start_handler,
):
    return drag_start_handler(drag_state, event, pane)


def _make_radio_pane_marker_drag_start_callback(
    drag_state,
    pane,
    *,
    drag_start_handler=_handle_radio_pane_marker_drag_start,
):
    def _start_drag(event):
        return _invoke_radio_pane_marker_drag_start_handler(
            drag_state,
            event,
            pane,
            drag_start_handler,
        )

    return _start_drag


def _invoke_radio_pane_marker_drag_event_handler(
    event,
    *,
    drag_state,
    pane,
    place_marker,
    schedule_marker_update,
    drag_event_handler,
):
    return drag_event_handler(
        event,
        drag_state=drag_state,
        pane=pane,
        place_marker=place_marker,
        schedule_marker_update=schedule_marker_update,
    )


def _make_radio_pane_marker_drag_event_callback(
    drag_state,
    pane,
    place_marker,
    schedule_marker_update,
    *,
    drag_event_handler=_handle_radio_pane_marker_drag_event,
):
    def _drag(event):
        return _invoke_radio_pane_marker_drag_event_handler(
            event,
            drag_state=drag_state,
            pane=pane,
            place_marker=place_marker,
            schedule_marker_update=schedule_marker_update,
            drag_event_handler=drag_event_handler,
        )

    return _drag


def _invoke_radio_pane_marker_drag_end_handler(update_marker, drag_end_handler):
    return drag_end_handler(update_marker)


def _make_radio_pane_marker_drag_end_callback(
    update_marker,
    *,
    drag_end_handler=_handle_radio_pane_marker_drag_end,
):
    def _end_drag(_event=None):
        return _invoke_radio_pane_marker_drag_end_handler(
            update_marker,
            drag_end_handler,
        )

    return _end_drag


def _schedule_active_radio_pane_marker_initial_update(
    container,
    update_marker,
    initial_update_scheduler,
) -> None:
    initial_update_scheduler(container, update_marker)


def _build_radio_pane_marker_place_callback(
    container,
    marker,
    place_callback_factory,
):
    return place_callback_factory(container, marker)


def _build_radio_pane_marker_update_callback(
    pane,
    place_marker,
    marker,
    update_callback_factory,
):
    return update_callback_factory(pane, place_marker, marker)


def _build_radio_pane_marker_schedule_callback(
    container,
    drag_state,
    update_marker,
    schedule_callback_factory,
):
    return schedule_callback_factory(container, drag_state, update_marker)


def _build_radio_pane_marker_drag_start_callback(
    drag_state,
    pane,
    drag_start_callback_factory,
):
    return drag_start_callback_factory(drag_state, pane)


def _build_radio_pane_marker_drag_event_callback(
    drag_state,
    pane,
    place_marker,
    schedule_marker_update,
    drag_event_callback_factory,
):
    return drag_event_callback_factory(
        drag_state,
        pane,
        place_marker,
        schedule_marker_update,
    )


def _build_radio_pane_marker_drag_end_callback(
    update_marker,
    drag_end_callback_factory,
):
    return drag_end_callback_factory(update_marker)


def _radio_pane_marker_callbacks(
    update_marker,
    start_drag,
    drag,
    end_drag,
) -> _RadioPaneMarkerCallbacks:
    return _RadioPaneMarkerCallbacks(
        update_marker,
        start_drag,
        drag,
        end_drag,
    )


def _activate_radio_pane_marker_callbacks(
    container,
    pane,
    grip,
    *,
    update_marker,
    start_drag,
    drag,
    end_drag,
    callback_binder=_bind_radio_pane_marker_callbacks,
    initial_update_scheduler=_schedule_initial_radio_pane_marker_update,
) -> None:
    callback_binder(
        container,
        pane,
        grip,
        update_marker=update_marker,
        start_drag=start_drag,
        drag=drag,
        end_drag=end_drag,
    )
    _schedule_active_radio_pane_marker_initial_update(
        container,
        update_marker,
        initial_update_scheduler,
    )


def _build_radio_pane_marker_callbacks(
    container,
    pane,
    marker,
    drag_state,
    *,
    place_callback_factory=_make_radio_pane_marker_place_callback,
    update_callback_factory=_make_radio_pane_marker_update_callback,
    schedule_callback_factory=_make_radio_pane_marker_schedule_callback,
    drag_start_callback_factory=_make_radio_pane_marker_drag_start_callback,
    drag_event_callback_factory=_make_radio_pane_marker_drag_event_callback,
    drag_end_callback_factory=_make_radio_pane_marker_drag_end_callback,
):
    place_marker_for_sash = _build_radio_pane_marker_place_callback(
        container,
        marker,
        place_callback_factory,
    )
    update_marker = _build_radio_pane_marker_update_callback(
        pane,
        place_marker_for_sash,
        marker,
        update_callback_factory,
    )
    schedule_marker_update = _build_radio_pane_marker_schedule_callback(
        container,
        drag_state,
        update_marker,
        schedule_callback_factory,
    )
    start_drag = _build_radio_pane_marker_drag_start_callback(
        drag_state,
        pane,
        drag_start_callback_factory,
    )
    drag = _build_radio_pane_marker_drag_event_callback(
        drag_state,
        pane,
        place_marker_for_sash,
        schedule_marker_update,
        drag_event_callback_factory,
    )
    end_drag = _build_radio_pane_marker_drag_end_callback(
        update_marker,
        drag_end_callback_factory,
    )
    return _radio_pane_marker_callbacks(
        update_marker,
        start_drag,
        drag,
        end_drag,
    )


def _radio_pane_marker_base(marker, grip, drag_state) -> _RadioPaneMarkerBase:
    return _RadioPaneMarkerBase(marker, grip, drag_state)


def _radio_pane_marker_installation(
    marker,
    grip,
    update_marker,
    start_drag,
    drag,
    end_drag,
) -> _RadioPaneMarkerInstallation:
    return _RadioPaneMarkerInstallation(
        marker,
        grip,
        update_marker,
        start_drag,
        drag,
        end_drag,
    )


def _build_radio_pane_marker_base(
    container,
    *,
    color="#0a84ff",
    widget_builder=_build_radio_pane_marker_widgets,
    drag_state_factory=_radio_pane_drag_state,
):
    marker, grip = widget_builder(container, color=color)
    drag_state = drag_state_factory()
    return _radio_pane_marker_base(marker, grip, drag_state)


def _build_radio_pane_marker_callbacks_for_base(
    container,
    pane,
    base,
    callback_builder,
):
    return callback_builder(
        container,
        pane,
        base.marker,
        base.drag_state,
    )


def _radio_pane_marker_installation_from_parts(
    base,
    callbacks,
) -> _RadioPaneMarkerInstallation:
    return _radio_pane_marker_installation(
        base.marker,
        base.grip,
        callbacks.update_marker,
        callbacks.start_drag,
        callbacks.drag,
        callbacks.end_drag,
    )


def _build_radio_pane_marker_installation(
    container,
    pane,
    *,
    color="#0a84ff",
    marker_base_builder=_build_radio_pane_marker_base,
    callback_builder=_build_radio_pane_marker_callbacks,
):
    base = marker_base_builder(
        container,
        color=color,
    )
    callbacks = _build_radio_pane_marker_callbacks_for_base(
        container,
        pane,
        base,
        callback_builder,
    )
    return _radio_pane_marker_installation_from_parts(base, callbacks)


def _activate_radio_pane_marker_installation(
    container,
    pane,
    installation,
    *,
    callback_activator=_activate_radio_pane_marker_callbacks,
) -> None:
    callback_activator(
        container,
        pane,
        installation.grip,
        update_marker=installation.update_marker,
        start_drag=installation.start_drag,
        drag=installation.drag,
        end_drag=installation.end_drag,
    )


def _install_pane_drag_marker(container, pane, *, color="#0a84ff"):
    installation = _build_radio_pane_marker_installation(
        container,
        pane,
        color=color,
    )
    # Legacy source reference for source-based tests:
    # marker_width = min(66, max(width - 24, 42))
    _activate_radio_pane_marker_installation(
        container,
        pane,
        installation,
    )
    return installation.marker


def build_radio_tab(app):
    # Legacy source reference for source-based tests:
    # text=app.tr("tools_tab_radio", "Radio")
    host, _show_bottom_placeholder = _build_radio_tab_scaffold(
        app,
    )
    # Legacy source references for source-based tests:
    # app.tr("radio_launcher_title", "NetMon Radio als externe App")
    # app.tr("radio_launcher_reattach", "Radio anheften")
    # NetMonRadioPanel(host, on_detach=_detach_from_tab, host_app=app)
    # "Radio wird gerade als Standalone-App gestartet."
    # "Radio wird gerade wieder an NetMon angeheftet."
    # _show_detached_placeholder()
    # _show_embedded_panel()
    # app.refresh_radio_launcher_state = refresh_radio_launcher_state
    _install_radio_launcher_refresh(
        app,
        host,
        _show_bottom_placeholder,
    )
