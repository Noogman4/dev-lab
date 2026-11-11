"""Complete Chad Setup scrolling in normal and isolated Analysis modes."""

import os
import subprocess
import time
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock

import pytest

from netmon.ui.tabs.chad_settings_tab import build_chad_settings_tab
from tests.test_terminal_dock_v39 import open_dock, spin, workspace as workspace


@pytest.fixture(autouse=True)
def require_isolation():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"


def build_setup(root, app):
    root.geometry("1280x700")
    strings = [
        "chad_settings_summary_state_var",
        "chad_settings_summary_critical_var",
        "chad_settings_summary_warning_var",
        "chad_settings_summary_notice_var",
        "chad_settings_summary_info_var",
        "chad_settings_api_status_var",
        "chad_settings_model_var",
        "chad_settings_latency_var",
        "chad_settings_last_analysis_var",
        "chad_settings_tokens_var",
        "openai_api_key_var",
        "chad_model_var",
        "chad_profile_var",
        "chad_analysis_mode_var",
        "chad_systemcheck_profile_var",
    ]
    for name in strings:
        setattr(app, name, tk.StringVar(master=root, value="Test"))
    app.openai_api_key_var.set("TEST-KEIN-SCHLUESSEL")
    app.chad_model_choices = ["fixture-a", "fixture-b"]
    app.chad_model_var.set("fixture-a")
    booleans = ["var_auto_switch_to_chad", "var_chad_preview_popup"]
    for prefix, suffixes in (
        (
            "chad_filter_",
            [
                "relevant",
                "critical",
                "recommendations",
                "beginner",
                "rawdata",
                "technical",
                "hide_normal_services",
                "ignore_harmless_processes",
                "ignore_dev_environment",
            ],
        ),
        (
            "chad_focus_",
            [
                "security",
                "dns",
                "network",
                "process",
                "firewall",
                "performance",
                "optimization",
                "rootkit",
            ],
        ),
        (
            "chad_answer_",
            ["short", "detailed", "step", "linux_help", "risk", "recommendations"],
        ),
    ):
        booleans.extend(prefix + suffix + "_var" for suffix in suffixes)
    for name in booleans:
        setattr(app, name, tk.BooleanVar(master=root, value=False))
    app.chad_settings_recent_analysis_rows = [
        {
            key: tk.StringVar(master=root, value="–")
            for key in (
                "timestamp_var",
                "type_var",
                "status_var",
                "warning_var",
                "critical_var",
            )
        }
        for _ in range(3)
    ]
    for name in (
        "save_ai_config",
        "load_ai_config",
        "clear_api_key",
        "delete_saved_api_key",
        "apply_chad_model_selection",
        "apply_chad_profile",
        "apply_chad_systemcheck_profile",
        "mark_chad_profile_custom",
    ):
        setattr(app, name, Mock())
    build_chad_settings_tab(app)
    return app.chad_settings_canvas, app.chad_settings_scrollbar


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def assert_visible(canvas, widget):
    assert widget.winfo_rooty() >= canvas.winfo_rooty()
    assert (
        widget.winfo_rooty() + widget.winfo_height()
        <= canvas.winfo_rooty() + canvas.winfo_height()
    )


@pytest.mark.parametrize("workspace", [False, "natural"], indirect=True)
def test_whole_setup_scrolls_and_focus_reveals_controls(workspace):
    root, app, errors = workspace
    canvas, bar = build_setup(root, app)
    if app.__dict__.get("page_canvas") is not None:
        open_dock(root, app, errors)
    app.nb.select(app.tab_chad_settings)
    root.update()
    assert bar.winfo_ismapped()
    assert app.chad_settings_scroll_frame.winfo_reqheight() > canvas.winfo_height()
    assert bar.winfo_rootx() >= canvas.winfo_rootx() + canvas.winfo_width()
    assert (
        bar.winfo_rooty() + bar.winfo_height()
        <= root.winfo_rooty() + root.winfo_height()
    )
    assert app.openai_api_key_entry.cget("show") == "*"
    # Wheel over a read-only combobox scrolls the form, not its model choice.
    canvas.yview_moveto(0)
    app.chad_model_combo.focus_force()
    root.update()
    before = canvas.yview()[0]
    app.chad_model_combo.event_generate("<Button-5>")
    root.update()
    assert canvas.yview()[0] > before
    before = canvas.yview()[0]
    app.chad_model_combo.event_generate("<MouseWheel>", delta=-1)
    root.update()
    assert canvas.yview()[0] > before
    assert app.chad_model_var.get() == "fixture-a"
    app.apply_chad_model_selection.assert_not_called()
    # Focus navigation makes the last setting and then the API entry visible.
    last = next(
        child
        for child in descendants(app.chad_settings_scroll_frame)
        if isinstance(child, ttk.Checkbutton)
        and str(child.cget("variable")) == str(app.chad_answer_recommendations_var)
    )
    last.focus_force()
    root.update()
    assert canvas.yview()[0] > 0
    assert_visible(canvas, last)
    last.invoke()
    assert app.chad_answer_recommendations_var.get() is True
    app.mark_chad_profile_custom.assert_called_once_with()
    app.openai_api_key_entry.focus_force()
    root.update()
    assert_visible(canvas, app.openai_api_key_entry)
    app.openai_api_key_entry.selection_range(2, 6)
    root.geometry("1280x900")
    root.update()
    assert app.openai_api_key_var.get() == "TEST-KEIN-SCHLUESSEL"
    assert app.openai_api_key_entry.selection_present()
    assert tuple(bar.get()) == canvas.yview()
    command = root.tk.splitlist(bar.cget("command"))
    root.tk.call(*command, "moveto", "1")
    root.update()
    assert_visible(canvas, last)
    if app.__dict__.get("page_canvas") is not None:
        assert app.page_canvas.yview() == (0, 1)
        until = time.monotonic() + 0.2
        spin(root, lambda: time.monotonic() >= until)
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/chad-setup-analysis.png",
            ],
            check=True,
            timeout=10,
        )
    for name in (
        "save_ai_config",
        "load_ai_config",
        "clear_api_key",
        "delete_saved_api_key",
    ):
        getattr(app, name).assert_not_called()
    assert not errors.called


def test_setup_fits_when_tall_and_removes_private_bindings_on_destroy(workspace):
    root, app, errors = workspace
    canvas, bar = build_setup(root, app)
    app.nb.select(app.tab_chad_settings)
    root.geometry("1280x2200")
    root.update()
    assert canvas.yview() == (0, 1) and tuple(bar.get()) == (0, 1)
    app.chad_model_combo.event_generate("<Button-5>")
    root.update()
    assert canvas.yview() == (0, 1) and app.chad_model_var.get() == "fixture-a"
    tag = next(tag for tag in canvas.bindtags() if tag.startswith("ChadSetupScroll"))
    assert root.tk.call("bind", tag, "<MouseWheel>")
    app.tab_chad_settings.destroy()
    root.update()
    for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>", "<FocusIn>"):
        assert root.tk.call("bind", tag, sequence) == ""
    assert not errors.called
