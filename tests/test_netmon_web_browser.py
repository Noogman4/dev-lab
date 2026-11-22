"""The opt-in routes reviewed links and leaves the standard route available."""

from pathlib import Path
import stat
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from netmon.app import App
from netmon.features import links_controller, web_browser_controller as routing
from netmon.modules.secure_browser import session
from netmon.ui.linux_help_reader import LinuxHelpReader
from netmon.ui.tabs.settings_tab import build_settings_general_system


@pytest.fixture
def tk_root():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(str(exc))
    root.withdraw()
    try:
        yield root
    finally:
        root.destroy()


def test_setup_checkbox_is_default_off_and_saves_from_confirmed_row(tk_root):
    app = App.__new__(App)
    app.tr = lambda key, default=None: default or key
    app.settings = app._default_settings_payload()
    saved = []
    app.save_settings = lambda **_kwargs: saved.append(dict(app.settings))
    for name in (
        "autostart_var",
        "radio_desktop_launcher_var",
        "var_start_security_monitoring",
        "var_button_sound",
        "var_netmon_browser",
    ):
        setattr(app, name, tk.BooleanVar(tk_root))
    for name in ("var_language", "var_theme_choice", "var_isp_dns_fallback_profile"):
        setattr(app, name, tk.StringVar(tk_root))
    app._language_choice_values = lambda: ("Deutsch",)
    build_settings_general_system(app, tk_root, {"dark": "Dark"}, [])
    group = tk_root.winfo_children()[0]
    checks = {
        str(widget.cget("variable")): widget
        for widget in group.winfo_children()
        if isinstance(widget, ttk.Checkbutton)
    }
    browser = checks[str(app.var_netmon_browser)]
    assert browser.cget("text") == "Eigenen Browser aktivieren"
    assert not browser.instate(["selected"])
    assert app.settings[routing.SETTING] is False
    browser.invoke()
    browser.invoke()
    assert [payload[routing.SETTING] for payload in saved] == [True, False]


def test_web_openers_never_use_the_default_browser_after_protected_error(
    tk_root, monkeypatch
):
    url = "https://www.7-zip.org/faq.html"
    calls = []

    def rejected(app, target):
        calls.append((app, target))
        return False

    monkeypatch.setattr(routing, "_queue_link", rejected)
    monkeypatch.setattr(
        links_controller.subprocess,
        "Popen",
        lambda *_a, **_kw: pytest.fail("Opened the standard browser"),
    )
    app = App.__new__(App)
    app.settings = {routing.SETTING: True}
    assert not app._open_url_with_xdg_open(url)
    assert not links_controller.open_external_target(app, url)
    tk_root.settings = app.settings
    reader = LinuxHelpReader(tk_root)
    assert not reader.open_source(url)
    assert calls == [(app, url), (app, url), (tk_root, url)]


def test_standalone_radio_reading_existing_setting(tmp_path, monkeypatch):
    monkeypatch.setattr(routing, "_queue_link", lambda _app, _url: True)
    radio = SimpleNamespace(netmon_config_dir=tmp_path)
    config = tmp_path / "config.json"
    assert routing.route_radio_if_enabled(radio, "https://example.org/") is None
    config.write_text('{"netmon_browser_enabled": "false"}', encoding="utf-8")
    assert routing.route_radio_if_enabled(radio, "https://example.org/") is None
    config.write_text('{"netmon_browser_enabled": true}', encoding="utf-8")
    assert routing.route_radio_if_enabled(radio, "https://example.org/") is True


def test_profile_has_one_owner_and_is_reusable(tmp_path):
    profile = tmp_path / "browser"
    with session._lock_profile(profile):
        with pytest.raises(session.BrowserSandboxError, match="bereits"):
            with session._lock_profile(profile):
                pytest.fail("Profile ownership was duplicated")
    with session._lock_profile(profile):
        assert (profile / "session.lock").is_file()


def test_dedicated_browser_reuses_strict_policy_with_general_web_access():
    policy = session._browser_policies(Path("/state"), Path("/firefox"))["policies"]
    assert policy["DisableTelemetry"] is True
    assert policy["PasswordManagerEnabled"] is False
    assert policy["DNSOverHTTPS"] == {"Enabled": False, "Locked": True}
    assert policy["HttpsOnlyMode"] == "enabled"
    assert policy["EnableTrackingProtection"] == {
        "Category": "strict",
        "Locked": True,
        "BaselineExceptions": True,
        "ConvenienceExceptions": True,
    }
    assert policy["NetworkPrediction"] is False
    assert policy["DefaultDownloadDirectory"] == "${home}/Downloads"
    assert policy["Bookmarks"] == [
        {
            "Title": "NetMonRoots",
            "URL": "https://netmonroots.com/",
            "Placement": "menu",
        }
    ]
    assert policy["Preferences"][
        "toolkit.legacyUserProfileCustomizations.stylesheets"
    ] == {
        "Value": True,
        "Status": "user",
    }
    assert "WebsiteFilter" not in policy


def test_browser_requires_wayland_even_if_x11_display_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    with pytest.raises(session.BrowserSandboxError, match="Wayland-Sitzung"):
        session._wayland_socket()


def test_missing_provisioned_runtime_is_reported_without_starting(monkeypatch):
    missing = Path("/netmon-test-missing-browser/firefox")
    lstat = Path.lstat

    def trusted_root(path):
        if path == Path("/"):
            return SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_uid=0)
        return lstat(path)

    monkeypatch.setattr(Path, "lstat", trusted_root)
    monkeypatch.setattr(
        session,
        "_wayland_socket",
        lambda: pytest.fail("Started before checking the runtime"),
    )
    browser = session.BrowserSession(Path("/unused"), browser_dir=missing)
    browser.open("https://example.org/")
    try:
        assert browser._errors.get(timeout=5) == "Die eigene Firefox-Basis fehlt."
    finally:
        browser.close()
        browser._worker.join(timeout=5)
