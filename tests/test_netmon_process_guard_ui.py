import inspect

from netmon.app import App
from netmon.ui.tabs.security_tabs import build_security_tabs


def test_process_guard_security_ui_source_is_present():
    source = inspect.getsource(build_security_tabs)

    assert 'app.tab_process_guard = ttk.Frame(app.security_nb, padding=10)' in source
    assert 'text=app.tr("security_tab_process_guard", "Process Guard")' in source
    assert "textvariable=app.process_guard_monitoring_status_var" in source
    assert "textvariable=app.process_guard_filter_status_var" in source
    assert "textvariable=app.process_guard_visible_count_var" in source
    assert 'text=app.tr("process_guard_group_title", "Process Guard")' in source
    assert "process_guard_btn_row1 = ttk.Frame(process_guard_frame)" in source
    assert "process_guard_btn_row2 = ttk.Frame(process_guard_frame)" in source
    assert "process_guard_btn_row3 = ttk.Frame(process_guard_frame)" in source
    assert 'text=app.tr("process_guard_btn_check", "Prozesse prüfen")' in source
    assert "command=app.run_process_guard_check" in source
    assert "command=app.start_process_guard_monitoring" in source
    assert "command=app.stop_process_guard_monitoring" in source
    assert "command=app.analyze_process_guard_with_chad" in source
    assert "command=app.analyze_selected_process_guard_with_chad" in source
    assert "command=app.mark_selected_process_guard_trusted" in source
    assert "command=app.remove_selected_process_guard_trusted" in source
    assert "command=app.show_process_guard_trustlist" in source
    assert "command=app.reset_process_guard_trustlist" in source
    assert 'command=lambda: app.set_process_guard_filter("all")' in source
    assert 'command=lambda: app.set_process_guard_filter("high_medium")' in source
    assert 'command=lambda: app.set_process_guard_filter("high")' in source
    assert "textvariable=app.process_guard_status_var" in source
    assert "app.process_guard_pane = ttk.Panedwindow(" in source
    assert 'orient="vertical"' in source
    assert "app.process_guard_pane.add(process_guard_tree_frame, weight=3)" in source
    assert "app.process_guard_pane.add(process_guard_detail_frame, weight=2)" in source
    assert "app.process_guard_tree = ttk.Treeview(" in source
    assert "app.attach_process_guard_tree_context_menu()" in source
    assert 'text=app.tr("process_guard_details_title", "Details")' in source
    assert "app.process_guard_detail = tk.Text(" in source
    assert 'app.process_guard_tree.bind("<<TreeviewSelect>>", app.on_process_guard_select)' in source


def test_process_guard_app_wrappers_are_present():
    app_source = inspect.getsource(App)

    assert "self.process_guard_status_var = tk.StringVar(" in app_source
    assert "self.process_guard_monitoring_status_var = tk.StringVar(" in app_source
    assert "self.process_guard_filter_status_var = tk.StringVar(" in app_source
    assert "self.process_guard_visible_count_var = tk.StringVar(" in app_source
    assert "self.l_process_guard = self.make_light(amp_extra, \"Process Guard\")" in app_source
    assert "def run_process_guard_check(self):" in app_source
    assert "def start_process_guard_monitoring(self):" in app_source
    assert "def stop_process_guard_monitoring(self):" in app_source
    assert "def analyze_process_guard_with_chad(self):" in app_source
    assert "def analyze_selected_process_guard_with_chad(self):" in app_source
    assert "def mark_selected_process_guard_trusted(self):" in app_source
    assert "def remove_selected_process_guard_trusted(self):" in app_source
    assert "def show_process_guard_trustlist(self):" in app_source
    assert "def reset_process_guard_trustlist(self):" in app_source
    assert "def get_process_guard_analysis_text(self) -> str:" in app_source
    assert "def copy_process_guard_to_clipboard(self):" in app_source
    assert "def paste_process_guard_selection_from_clipboard(self):" in app_source
    assert "def select_all_process_guard_findings(self):" in app_source
    assert "def analyze_process_guard_tree_selection_with_chad(self):" in app_source
    assert "def copy_process_guard_as_chad_prompt(self):" in app_source
    assert "def attach_process_guard_tree_context_menu(self):" in app_source
    assert "def set_process_guard_filter(self, filter_mode: str):" in app_source
    assert "def on_process_guard_select(self, _event=None):" in app_source
    assert 'tab = self.__dict__.get("tab_process_guard")' in app_source
    assert '"process_guard_detail"' in app_source
    assert "if process_guard_controller is None:" in app_source


def test_process_guard_controller_is_recovered_after_bulk_import_failure():
    app_source = inspect.getsource(App)

    assert "if process_guard_controller is None:" in app_source
    module_source = inspect.getsource(__import__("netmon.app", fromlist=["App"]))
    assert (
        "import netmon.features.process_guard_controller as process_guard_controller"
        in module_source
    )
