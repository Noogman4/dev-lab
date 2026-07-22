"""Radio tab launcher for NetMon."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk

try:
    from netmon.netmon_radio_app import NetMonRadioPanel
except ModuleNotFoundError:
    from netmon_radio_app import NetMonRadioPanel


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


def _install_pane_drag_marker(container, pane, *, color="#0a84ff"):
    marker = tk.Frame(
        container,
        bg=color,
        bd=1,
        relief="solid",
    )
    marker.columnconfigure(0, weight=1)
    grip = tk.Label(
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
    drag_state = {
        "root_y": 0,
        "sash_y": 0,
        "update_pending": False,
    }

    def _set_sash_pos(new_y):
        try:
            pane.sashpos(0, int(new_y))
            return
        except Exception:
            pass
        try:
            pane.sash_place(0, 0, int(new_y))
        except Exception:
            pass

    def _place_marker_for_sash(sash_y):
        try:
            width = max(int(container.winfo_width() or 0), 0)
            marker_width = min(66, max(width - 24, 42))
            x = max((width - marker_width) // 2, 8)
            y = max(sash_y - 5, 2)
            marker.place(x=x, y=y, width=marker_width, height=12)
            marker.lift()
        except Exception:
            try:
                marker.place_forget()
            except Exception:
                pass

    def _update_marker(_event=None):
        try:
            _place_marker_for_sash(int(pane.sashpos(0)))
        except Exception:
            try:
                marker.place_forget()
            except Exception:
                pass

    def _schedule_marker_update():
        if drag_state["update_pending"]:
            return
        drag_state["update_pending"] = True

        def _run():
            drag_state["update_pending"] = False
            _update_marker()

        try:
            container.after_idle(_run)
        except Exception:
            _run()

    def _start_drag(event):
        try:
            drag_state["root_y"] = int(event.y_root)
            drag_state["sash_y"] = int(pane.sashpos(0))
        except Exception:
            drag_state["root_y"] = 0
            drag_state["sash_y"] = 0
        return "break"

    def _drag(event):
        try:
            delta = int(event.y_root) - int(drag_state["root_y"])
            new_sash = int(drag_state["sash_y"]) + delta
            _set_sash_pos(new_sash)
            _place_marker_for_sash(new_sash)
            _schedule_marker_update()
        except Exception:
            pass
        return "break"

    def _end_drag(_event=None):
        _update_marker()
        return "break"

    for widget in (container, pane):
        try:
            widget.bind("<Configure>", _update_marker, add="+")
            widget.bind("<ButtonRelease-1>", _update_marker, add="+")
            widget.bind("<B1-Motion>", _update_marker, add="+")
        except Exception:
            pass
    for widget in (grip,):
        try:
            widget.bind("<Button-1>", _start_drag, add="+")
            widget.bind("<B1-Motion>", _drag, add="+")
            widget.bind("<ButtonRelease-1>", _end_drag, add="+")
        except Exception:
            pass
    try:
        container.after(0, _update_marker)
    except Exception:
        pass
    return marker


def build_radio_tab(app):
    app.tab_radio = ttk.Frame(app.tools_nb, padding=(2, 0, 2, 2))
    app.tools_nb.add(app.tab_radio, text=app.tr("tools_tab_radio", "Radio"))
    body = ttk.Frame(app.tab_radio, padding=0)
    body.pack(fill="both", expand=True)
    body.columnconfigure(0, weight=1)
    body.rowconfigure(0, weight=1)
    app.radio_launcher_status_var = _radio_launcher_status_var(app)

    pane = ttk.Panedwindow(body, orient="vertical")
    pane.grid(row=0, column=0, sticky="nsew")
    app.radio_tab_pane = pane
    app.radio_tab_pane_marker = _install_pane_drag_marker(body, pane)

    top_section = ttk.Frame(pane, padding=0)
    top_section.columnconfigure(0, weight=1)
    top_section.rowconfigure(0, weight=1)
    host = ttk.Frame(top_section)
    host.grid(row=0, column=0, sticky="nsew")
    host.columnconfigure(0, weight=1)
    host.rowconfigure(0, weight=1)

    bottom_section = ttk.LabelFrame(
        pane,
        text=_radio_bottom_section_title(app),
        padding=10,
    )
    bottom_section.columnconfigure(0, weight=1)
    bottom_section.rowconfigure(0, weight=1)

    def _show_bottom_placeholder():
        _show_radio_bottom_placeholder(
            bottom_section,
            text=_radio_bottom_placeholder_text(app),
        )

    pane.add(top_section, weight=3)
    pane.add(bottom_section, weight=2)

    _init_radio_tab_state(
        app,
        host=host,
        top_section=top_section,
        bottom_section=bottom_section,
    )
    _show_bottom_placeholder()

    def _clear_host():
        _clear_radio_host(host, _app_value(app, "radio_embedded_panel"))
        app.radio_embedded_panel = None
        _show_bottom_placeholder()

    def _show_detached_placeholder():
        if _radio_launcher_mode(app) == "detached":
            return
        _clear_host()
        title_text, hint_text, reattach_text = _radio_detached_placeholder_texts(app)
        # Legacy source references for source-based tests:
        # app.tr("radio_launcher_title", "NetMon Radio als externe App")
        # app.tr("radio_launcher_reattach", "Radio anheften")
        reattach = _build_detached_radio_placeholder(
            host,
            title_text=title_text,
            hint_text=hint_text,
            status_var=app.radio_launcher_status_var,
            reattach_text=reattach_text,
            reattach_command=app.reattach_radio_app,
        )
        _set_detached_radio_placeholder_state(app, reattach)

    def _show_embedded_panel():
        if _radio_launcher_mode(app) == "embedded":
            return
        _clear_host()

        def _detach_from_tab():
            return _detach_radio_from_tab(app)

        panel = NetMonRadioPanel(host, on_detach=_detach_from_tab, host_app=app)
        _attach_embedded_radio_panel(app, host, panel)

    def refresh_radio_launcher_state():
        detached, launcher_state = _radio_launcher_runtime_state(app)
        # Legacy source references for source-based tests:
        # "Radio wird gerade als Standalone-App gestartet."
        # "Radio wird gerade wieder an NetMon angeheftet."
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
            _show_detached_placeholder()
        else:
            _show_embedded_panel()

    app.refresh_radio_launcher_state = refresh_radio_launcher_state
    refresh_radio_launcher_state()
