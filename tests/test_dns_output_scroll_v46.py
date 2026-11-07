"""DNS output scrolling with the real tab, normal and analysis layouts."""

import os
import subprocess
import tkinter as tk
from unittest.mock import Mock

import pytest

from netmon.ui.tabs.dns_tab import build_dns_tab
from tests.test_terminal_dock_v39 import open_dock, workspace as workspace


@pytest.fixture(autouse=True)
def require_isolation():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"


@pytest.mark.parametrize("workspace", [False, "natural"], indirect=True)
def test_dns_output_scrollbar_in_normal_and_analysis_modes(workspace):
    root, app, errors = workspace
    root.geometry("1280x900")
    app.dns_guard_enabled_var = tk.BooleanVar(master=root, value=False)
    for name in (
        "dns_resolver_status_var",
        "dns_conflict_status_var",
        "dns_guard_status_var",
        "dns_guard_last_action_var",
        "dot_status_var",
        "dot_profile_var",
        "dot_server_var",
        "dot_mode_var",
        "dot_last_test_var",
        "manual_dns_entry_var",
    ):
        setattr(app, name, tk.StringVar(master=root, value="Isolierter Test"))
    app.register_feature_button = lambda *args: None
    app.attach_text_context_menu = lambda *args: None
    app.attach_chad_context_menu = Mock()
    build_dns_tab(app)
    app.attach_chad_context_menu.assert_called_once_with(app.dns_text, "DNS-Analyse")
    if app.__dict__.get("page_canvas") is not None:
        open_dock(root, app, errors)
    app.nb.select(app.tab_dns)
    root.update()
    text, bar = app.dns_text, app.dns_output_scrollbar
    content = "\n".join(f"DNS-Ausgabe Zeile {i:03}" for i in range(200))
    app.update_dns_output(content)
    root.update()
    assert bar.winfo_ismapped() and text.winfo_height() >= 80
    assert bar.winfo_rootx() >= text.winfo_rootx() + text.winfo_width()
    assert (
        bar.winfo_rooty() + bar.winfo_height()
        <= root.winfo_rooty() + root.winfo_height()
    )
    assert text.get("1.0", "end-1c") == content
    assert text.dlineinfo("199.0") is not None
    assert tuple(bar.get()) == text.yview()
    # Call the actual Tk scrollbar command in both directions.
    command = root.tk.splitlist(bar.cget("command"))
    root.tk.call(*command, "moveto", "0")
    root.update()
    assert text.yview()[0] == 0 and text.dlineinfo("1.0") is not None
    root.tk.call(*command, "moveto", "1")
    root.update()
    assert text.yview()[0] > 0 and text.dlineinfo("200.0") is not None
    text.tag_add("sel", "197.0", "197.end")
    selected = text.get("sel.first", "sel.last")
    root.geometry("1280x1000")
    root.update()
    assert text.get("sel.first", "sel.last") == selected
    assert tuple(bar.get()) == text.yview()
    if app.__dict__.get("page_canvas") is not None:
        assert app.page_canvas.yview() == (0, 1)
        subprocess.run(
            [
                "import",
                "-window",
                str(root.winfo_id()),
                "/work/dns-output-analysis.png",
            ],
            check=True,
            timeout=10,
        )
    app.clear_dns_output()
    root.update()
    assert text.get("1.0", "end-1c") == "" and tuple(bar.get()) == (0, 1)
    assert not errors.called
