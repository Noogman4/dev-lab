"""System monitor scrolling with real widgets and synthetic monitor values."""

import os
import subprocess
from tkinter import ttk
from types import MethodType, SimpleNamespace
from unittest.mock import Mock

import pytest

from netmon.app import App
from netmon.ui.tabs.system_tab import build_system_monitor, build_system_tab
from tests.test_terminal_dock_v39 import open_dock, workspace as workspace


@pytest.fixture(autouse=True)
def require_isolation():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"


@pytest.mark.parametrize("workspace", [False, "natural"], indirect=True)
def test_system_monitor_scrolls_without_changing_other_subtabs(workspace):
    root, host, errors = workspace
    root.geometry("1280x600")
    main = ttk.Frame(host.nb)
    host.nb.add(main, text="System")
    notebook = ttk.Notebook(main)
    notebook.pack(fill="both", expand=True)
    siblings = []
    for name in ("HDD", "Links", "VPN"):
        page = ttk.Frame(notebook)
        notebook.add(page, text=name)
        ttk.Label(page, text=f"Unchanged {name}").pack()
        siblings.append((page, tuple(page.winfo_children()), page.bindtags()))
    app = SimpleNamespace(
        system_nb=notebook,
        tr=lambda key, default=None: default or key,
        system_monitor_refresh=Mock(),
        clear_swap_async=Mock(),
        resize_swap_async=Mock(),
        _load_sysinfo_static=Mock(),
        _update_sysinfo_dynamic=Mock(),
    )
    app._system_row = MethodType(App._system_row, app)
    app._build_sysinfo_group = MethodType(App._build_sysinfo_group, app)
    app._build_system_tab = lambda: build_system_monitor(app)
    global_wheel = root.bind_all("<Button-5>")
    build_system_tab(app)
    app._load_sysinfo_static.assert_called_once_with()
    app._update_sysinfo_dynamic.assert_called_once_with()
    if host.__dict__.get("page_canvas") is not None:
        open_dock(root, host, errors)
    host.nb.select(main)
    notebook.select(app.tab_system)
    root.update()
    form = app.system_monitor_form
    canvas, bar = form.canvas, form.scrollbar
    assert bar.winfo_ismapped()
    assert form.content.winfo_reqheight() > canvas.winfo_height()
    assert bar.winfo_rootx() >= canvas.winfo_rootx() + canvas.winfo_width()
    assert bar.winfo_rooty() + bar.winfo_height() <= (
        root.winfo_rooty() + root.winfo_height()
    )
    app.system_cpu_var.set("CPU: 42 % (synthetic)")
    app.system_cpu_bar_widget.configure(value=42)
    App._set_sysinfo_value(app, "sw_python", "Synthetic Python")
    command = root.tk.splitlist(bar.cget("command"))
    root.tk.call(*command, "moveto", 1)
    root.update()
    assert canvas.yview()[0] > 0
    assert bar.get() == pytest.approx(canvas.yview())
    group = app.system_sysinfo_group
    assert group.winfo_rooty() >= canvas.winfo_rooty()
    assert group.winfo_rooty() + group.winfo_height() <= (
        canvas.winfo_rooty() + canvas.winfo_height()
    )
    # Focus reaches the refresh control at the top without invoking its action.
    app.btn_system_monitor_refresh.focus_force()
    root.update()
    assert app.btn_system_monitor_refresh.winfo_rooty() >= canvas.winfo_rooty()
    assert canvas.yview()[0] < 0.05
    before = canvas.yview()[0]
    app.system_cpu_bar_widget.event_generate("<Button-5>")
    root.update()
    assert canvas.yview()[0] > before
    before = canvas.yview()[0]
    app.system_cpu_bar_widget.event_generate("<MouseWheel>", delta=120)
    root.update()
    assert canvas.yview()[0] < before
    root.geometry("1280x800")
    root.update()
    root.tk.call(*command, "moveto", 1)
    root.update()
    assert app.system_cpu_var.get() == "CPU: 42 % (synthetic)"
    assert app.system_cpu_bar_widget.cget("value") == 42
    assert app.sysinfo_vars["sw_python"].get() == "Synthetic Python"
    assert bar.get() == pytest.approx(canvas.yview())
    if host.__dict__.get("page_canvas") is not None:
        assert host.page_canvas.yview() == (0, 1)
        subprocess.run(
            ["import", "-window", str(root.winfo_id()), "/work/system-analysis.png"],
            check=True,
            timeout=10,
        )
    for page, children, tags in siblings:
        assert tuple(page.winfo_children()) == children
        assert page.bindtags() == tags
        notebook.select(page)
        root.update()
        assert all(widget.winfo_ismapped() for widget in children)
    app.system_monitor_refresh.assert_not_called()
    app.clear_swap_async.assert_not_called()
    app.resize_swap_async.assert_not_called()
    assert root.bind_all("<Button-5>") == global_wheel
    app.tab_system.destroy()
    root.update()
    for sequence in form.sequences:
        assert root.tk.call("bind", form.tag, sequence) == ""
    assert len(notebook.tabs()) == len(siblings)
    assert not errors.called
