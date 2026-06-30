import inspect

from netmon.app import App
from netmon.ui.tabs.security_tabs import build_security_tabs, build_startup_guard_tab


def test_startup_guard_security_ui_source_is_present():
    source = inspect.getsource(build_security_tabs)
    startup_source = inspect.getsource(build_startup_guard_tab)

    assert 'app.tab_startup_guard = ttk.Frame(app.security_nb, padding=10)' in source
    assert 'text=app.tr("security_tab_startup_guard", "Startup Guard")' in source
    assert "build_startup_guard_tab(app)" in source

    assert 'text=app.tr("startup_guard_group_basic", "Basis")' in startup_source
    assert 'text=app.tr("startup_guard_group_analysis", "Analyse")' in startup_source
    assert 'text=app.tr("startup_guard_group_trust", "Vertrauen")' in startup_source
    assert 'text=app.tr("startup_guard_btn_baseline", "Baseline erstellen")' in startup_source
    assert 'text=app.tr("startup_guard_btn_check", "Startup prüfen")' in startup_source
    assert 'text=app.tr("startup_guard_btn_clear", "Ergebnis leeren")' in startup_source
    assert "command=app.startup_guard_create_baseline" in startup_source
    assert "command=app.startup_guard_check" in startup_source
    assert "command=app.clear_startup_guard_output" in startup_source
    assert "command=app.analyze_selected_startup_entry_with_chad" in startup_source
    assert "command=app.analyze_startup_guard_changes_with_chad" in startup_source
    assert "command=app.startup_guard_mark_selected_trusted" in startup_source
    assert "command=app.startup_guard_remove_selected_trusted" in startup_source
    assert "command=app.startup_guard_show_trustlist" in startup_source
    assert "command=app.startup_guard_reset_trustlist" in startup_source
    assert "textvariable=app.startup_guard_run_status_var" in startup_source
    assert "textvariable=app.startup_guard_visible_count_var" in startup_source
    assert "app.startup_guard_pane = ttk.Panedwindow(" in startup_source
    assert 'orient="vertical"' in startup_source
    assert "app.startup_guard_pane.add(tree_frame, weight=3)" in startup_source
    assert "app.startup_guard_pane.add(details_frame, weight=2)" in startup_source
    assert "app.startup_guard_tree = ttk.Treeview(" in startup_source
    assert "app.attach_startup_guard_tree_context_menu()" in startup_source
    assert "app.startup_guard_details_text = tk.Text(" in startup_source
    assert 'app.startup_guard_tree.bind(' in startup_source


def test_startup_guard_app_wrapper_uses_shared_builder():
    app_source = inspect.getsource(App)

    assert "def build_startup_guard_tab(self):" in app_source
    assert "build_startup_guard_tab(self)" in app_source
    assert "def startup_guard_reset_trustlist(self):" in app_source
    assert "self.startup_guard_run_status_var = tk.StringVar(" in app_source
    assert "self.startup_guard_visible_count_var = tk.StringVar(" in app_source
    assert "def get_startup_guard_analysis_text(self) -> str:" in app_source
    assert "def copy_startup_guard_to_clipboard(self):" in app_source
    assert "def paste_startup_guard_selection_from_clipboard(self):" in app_source
    assert "def select_all_startup_guard_entries(self):" in app_source
    assert "def analyze_startup_guard_tree_selection_with_chad(self):" in app_source
    assert "def copy_startup_guard_as_chad_prompt(self):" in app_source
    assert "def attach_startup_guard_tree_context_menu(self):" in app_source
