"""Whole Setup and D-Scan forms in private normal and Analysis workspaces."""

import os
import subprocess
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from netmon.app import App
from netmon.ui.tabs.download_scan_tab import build_download_scan_content
from netmon.ui.tabs.settings_tab import build_settings_backup, build_settings_content
from tests.test_terminal_dock_v39 import open_dock, workspace as workspace


class PassiveUI(SimpleNamespace):
    def __getattr__(self, name):
        if name.endswith("_var") or name.startswith("var_"):
            value = tk.StringVar(self.root, value="")
        else:
            value = Mock(return_value=None)
        setattr(self, name, value)
        return value


@pytest.fixture(autouse=True)
def require_isolation():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def prepare(workspace):
    root, host, errors = workspace
    root.geometry("1280x600")
    app = PassiveUI(root=root, nb=host.nb, settings={})
    app.tr = lambda key, default=None: default or key
    app._language_choice_values = lambda: ["Deutsch", "English"]
    app.get_privacy_vpn_options = lambda: []
    app._guided_tour_launcher_specs = lambda: App._guided_tour_launcher_specs(app)
    app._guided_tour_status_symbol = lambda name: "–"
    app._support_form_placeholders = lambda: {
        key: "Test"
        for key in ("contact_name", "contact_email", "last_step", "repro", "details")
    }
    app._build_settings_backup_tab = lambda frame: build_settings_backup(app, frame)
    for name in (
        "enabled",
        "autostart",
        "enable_killswitch",
        "disable_ipv6",
        "vpn_choice",
    ):
        setattr(app, f"isp_stealth_{name}", tk.StringVar(root, value=""))
    app.tab_settings = ttk.Frame(app.nb)
    app.nb.add(app.tab_settings, text="Setup")
    app.tab_download_scan = ttk.Frame(app.nb)
    app.nb.add(app.tab_download_scan, text="D-Scan")
    build_settings_content(app, {"test": "Test"}, ["Test DNS"])
    build_download_scan_content(app)
    if host.__dict__.get("page_canvas") is not None:
        open_dock(root, host, errors)
    return root, host, app, errors


def move(root, form, fraction):
    command = root.tk.splitlist(form.scrollbar.cget("command"))
    root.tk.call(*command, "moveto", fraction)
    root.update()
    assert form.scrollbar.get() == pytest.approx(form.canvas.yview())


def visible(form, widget):
    assert widget.winfo_rooty() >= form.canvas.winfo_rooty()
    assert widget.winfo_rooty() + widget.winfo_height() <= (
        form.canvas.winfo_rooty() + form.canvas.winfo_height()
    )


@pytest.mark.parametrize("workspace", [False, "natural"], indirect=True)
def test_setup_all_subpages_and_scan_are_bounded_scrollable_forms(workspace):
    root, host, app, errors = prepare(workspace)
    global_wheel = root.bind_all("<Button-5>")
    app.nb.select(app.tab_settings)
    for name, form in app.settings_scroll_forms.items():
        page = form.wrap.master
        app.settings_nb.select(page)
        root.update()
        assert form.scrollbar.winfo_ismapped(), name
        assert form.canvas.winfo_height() < form.content.winfo_reqheight(), name
        assert form.scrollbar.winfo_rootx() >= (
            form.canvas.winfo_rootx() + form.canvas.winfo_width()
        )
        assert form.canvas.winfo_rooty() + form.canvas.winfo_height() <= (
            root.winfo_rooty() + root.winfo_height()
        )
        move(root, form, 1)
        assert form.canvas.yview()[0] > 0
        controls = [
            w
            for w in descendants(form.content)
            if w.winfo_ismapped()
            and isinstance(w, (ttk.Button, ttk.Checkbutton, ttk.Entry, tk.Text))
        ]
        last = max(controls, key=lambda w: w.winfo_rooty() + w.winfo_height())
        visible(form, last)
        move(root, form, 0)
        last.focus_force()
        root.update()
        visible(form, last)
        if name == "general":
            combo = next(w for w in controls if isinstance(w, ttk.Combobox))
            combo.set("Deutsch")
            move(root, form, 0)
            combo.event_generate("<Button-5>")
            root.update()
            assert form.canvas.yview()[0] > 0
            assert combo.get() == "Deutsch"
            combo.event_generate("<MouseWheel>", delta=120)
            root.update()
        # Notebook headings stay fixed while only this subpage scrolls.
        assert app.settings_nb.winfo_rooty() < form.canvas.winfo_rooty()
    App.return_to_guided_tour_tab(app)
    assert app.settings_nb.select() == str(app.settings_tours_tab)
    assert str(app.settings_backup_tab) in app.settings_nb.tabs()
    app.nb.select(app.tab_download_scan)
    form = app.download_scan_form
    root.update()
    assert form.content.winfo_reqheight() > form.canvas.winfo_height()
    move(root, form, 1)
    visible(form, app.download_scan_result_text)
    checkbox = next(
        w
        for w in descendants(form.content)
        if isinstance(w, ttk.Checkbutton)
        and str(w.cget("variable")) == str(app.download_scan_prequarantine_startup_var)
    )
    checkbox.focus_force()
    root.update()
    visible(form, checkbox)
    checkbox.invoke()
    app.on_download_scan_prequarantine_startup_toggle.assert_called_once_with()
    move(root, form, 1)
    text = app.download_scan_result_text
    text.configure(state="normal")
    text.delete("1.0", "end")
    text.insert("1.0", "\n".join(f"Result {i}" for i in range(500)))
    text.configure(state="disabled")
    text.yview_moveto(0)
    root.update()
    before = form.canvas.yview()
    text.event_generate("<Button-5>")
    root.update()
    assert text.yview()[0] > 0 and form.canvas.yview() == before
    text.yview_moveto(0)
    text.event_generate("<Button-4>")
    root.update()
    assert form.canvas.yview()[0] < before[0]
    root.geometry("1280x800")
    root.update()
    move(root, form, 1)
    visible(form, text)
    assert root.bind_all("<Button-5>") == global_wheel
    if host.__dict__.get("page_canvas") is not None:
        assert host.page_canvas.yview() == (0, 1)
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/download-scan-form-analysis.png",
            ],
            check=True,
            timeout=10,
        )
        app.nb.select(app.tab_settings)
        app.settings_nb.select(app.settings_scroll_forms["general"].wrap.master)
        move(root, app.settings_scroll_forms["general"], 1)
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/settings-form-analysis.png",
            ],
            check=True,
            timeout=10,
        )
    for name in (
        "restart_netmon_only",
        "reset_network_stack",
        "apply_settings_from_ui",
        "scan_download_file_async",
        "enable_download_scan_temp_folder",
    ):
        getattr(app, name).assert_not_called()
    assert not errors.called


def test_form_bindings_are_removed_on_destroy(workspace):
    root, host, app, errors = prepare(workspace)
    forms = list(app.settings_scroll_forms.values()) + [app.download_scan_form]
    for form in forms:
        assert root.tk.call("bind", form.tag, "<Button-5>")
    app.tab_settings.destroy()
    app.tab_download_scan.destroy()
    root.update()
    for form in forms:
        for sequence in form.sequences:
            assert root.tk.call("bind", form.tag, sequence) == ""
    assert not errors.called
