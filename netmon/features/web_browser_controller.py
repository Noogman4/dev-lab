"""Route GUI HTTP(S) links to the optional NetMon browser."""

import json
from pathlib import Path
import subprocess
from tkinter import messagebox

from netmon.core.state import get_netmon_state_dir

SETTING = "netmon_browser_enabled"


def route_if_enabled(app, url):
    """Return None for the standard route, or the result of protected routing."""
    if app.__dict__.get("settings", {}).get(SETTING) is not True:
        return None
    return _queue_link(app, url)


def route_radio_if_enabled(radio, url):
    host = radio.__dict__.get("radio_host_app")
    if host is not None:
        return route_if_enabled(host, url)
    directory = radio.__dict__.get("netmon_config_dir")
    if directory is None:
        return None
    try:
        with (Path(directory) / "config.json").open(encoding="utf-8") as source:
            config = json.load(source)
    except (OSError, ValueError):
        return None
    if isinstance(config, dict) and config.get(SETTING) is True:
        return _queue_link(radio, url)
    return None


def _queue_link(app, url):
    from netmon.modules.secure_browser.session import (
        BrowserSandboxError,
        BrowserSession,
    )

    if app.__dict__.get("_netmon_closing", False):
        return False
    session = app.__dict__.get("_web_browser_session")
    try:
        if session is None:
            session = BrowserSession(Path(get_netmon_state_dir()) / "web-browser")
            session.open(url)
            app._web_browser_session = session
            app.bind("<Destroy>", lambda event: _on_destroy(app, event), add="+")
            app.after(250, _poll_errors, app, session)
        else:
            session.open(url)
    except (BrowserSandboxError, OSError) as exc:
        _show_error(app, str(exc))
        return False
    return True


def _show_error(app, detail):
    messagebox.showerror(
        app.tr("settings_netmon_browser", "Eigenen Browser aktivieren"),
        detail,
        parent=app,
    )


def _offer_standard_browser(app, session, detail, url):
    confirmed = messagebox.askyesno(
        app.tr("netmon_browser_x11_title", "Link im Standardbrowser öffnen"),
        detail
        + "\n\n"
        + app.tr(
            "netmon_browser_x11_fallback",
            "Diesen Link einmalig im System-Standardbrowser außerhalb der "
            "NetMon-Sandbox öffnen?",
        ),
        default=messagebox.NO,
        parent=app,
    )
    if (
        confirmed
        and app.__dict__.get("_web_browser_session") is session
        and not app.__dict__.get("_netmon_closing", False)
    ):
        try:
            subprocess.Popen(
                ["/usr/bin/xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            _show_error(app, str(exc))


def _poll_errors(app, session):
    if app.__dict__.get("_web_browser_session") is session:
        error = session.take_error()
        if error is not None:
            detail, fallback_url = error
            if fallback_url is None:
                _show_error(app, detail)
            elif not app.__dict__.get("_netmon_closing", False):
                _offer_standard_browser(app, session, detail, fallback_url)
        if app.__dict__.get("_web_browser_session") is session:
            app.after(250, _poll_errors, app, session)


def close_session(app):
    session = app.__dict__.pop("_web_browser_session", None)
    if session is not None:
        session.close()


def _on_destroy(app, event):
    if event.widget is app:
        close_session(app)
