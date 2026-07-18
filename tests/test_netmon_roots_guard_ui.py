import inspect
import os
from types import SimpleNamespace

import pytest

from netmon.app import App
from netmon.features import chad_controller
from netmon.ui.tabs.security_tabs import build_roots_baseline_guard_tab


class _DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_roots_guard_ui_source_is_present():
    source = inspect.getsource(build_roots_baseline_guard_tab)

    assert 'text=app.tr("security_tab_roots_baseline_guard", "Roots Baseline Guard")' in source
    assert 'text="System Integrity Status"' in source
    assert 'text="Überwachte Bereiche"' in source
    assert 'text="Baseline Verwaltung"' in source
    assert 'text="Mit Root lesen / prüfen"' in source
    assert 'text="Baseline Änderungen"' in source
    assert 'text="Chad Analyse"' in source
    assert 'text="Verlauf / History"' in source
    assert 'text="Vertrauenswürdige Änderungen"' in source
    assert "app.roots_baseline_guard_whitelist_list = tk.Listbox(" in source
    assert 'app.open_selected_roots_baseline_guard_whitelist_entry' in source
    assert "app.roots_root_mode_status_label = tk.Label(" in source
    assert "app.roots_baseline_guard_pane = ttk.Panedwindow(" in source
    assert "app.roots_baseline_guard_results_table = ttk.Treeview(" in source
    assert 'selectmode="extended"' in source
    assert "app.roots_baseline_guard_root_mode_var.trace_add(" in source


def test_roots_guard_app_wrappers_are_present():
    app_source = inspect.getsource(App)

    assert "def attach_copy_paste_context_menu(self, widget):" in app_source
    assert "def update_chad_output_layout(self):" in app_source
    assert "def refresh_roots_baseline_guard_status(self):" in app_source
    assert "def refresh_roots_baseline_guard_root_mode_status(self):" in app_source
    assert "def get_roots_baseline_guard_selection_text(self) -> str:" in app_source
    assert "def open_selected_roots_baseline_guard_parent_folder(self):" in app_source
    assert "def copy_selected_roots_baseline_guard_path(self):" in app_source
    assert "def open_roots_baseline_guard_info_path(self):" in app_source
    assert "def roots_baseline_guard_read_current_state(self):" in app_source
    assert "def roots_baseline_guard_create_baseline(self):" in app_source
    assert "def roots_baseline_guard_check_baseline(self):" in app_source
    assert "def roots_baseline_guard_update_baseline(self):" in app_source
    assert "def roots_baseline_guard_show_last_comparison(self):" in app_source
    assert "def clear_roots_baseline_guard_view(self):" in app_source


def test_roots_guard_copy_prefers_treeview_selection_text():
    clipboard = {"text": ""}
    dummy = SimpleNamespace()
    dummy.__dict__["roots_baseline_guard_results_table"] = object()
    dummy.chad_analysis_status_var = _DummyVar("")
    dummy.get_treeview_selection_text = lambda _table: "row1\trow2"
    dummy.get_roots_baseline_guard_analysis_text = lambda: "analysis fallback"
    dummy.get_roots_baseline_guard_selection_text = lambda: App.get_roots_baseline_guard_selection_text(
        dummy
    )
    dummy.clipboard_clear = lambda: clipboard.__setitem__("text", "")
    dummy.clipboard_append = lambda text: clipboard.__setitem__("text", text)

    App.copy_roots_baseline_guard_to_clipboard(dummy)

    assert clipboard["text"] == "row1\trow2"
    assert dummy.chad_analysis_status_var.get() == (
        "Roots Baseline Guard Auswahl in Zwischenablage kopiert."
    )


def test_roots_guard_chad_analysis_falls_back_to_treeview_selection():
    prepared = {}
    dummy = SimpleNamespace()
    dummy.__dict__["roots_baseline_guard_results_table"] = object()
    dummy.chad_analysis_status_var = _DummyVar("")
    dummy.get_roots_baseline_guard_analysis_text = lambda: ""
    dummy.get_treeview_selection_text = lambda _table: "path\tchange"
    dummy.is_chad_enabled = lambda: True
    dummy._show_chad_activation_required_popup = lambda: prepared.setdefault(
        "popup", True
    )
    dummy.prepare_chad_analysis = lambda title, text: prepared.update(
        {"title": title, "text": text}
    )
    dummy.get_roots_baseline_guard_selection_text = lambda: App.get_roots_baseline_guard_selection_text(
        dummy
    )

    App.analyze_roots_baseline_guard_tree_selection_with_chad(dummy)

    assert prepared == {
        "title": "Roots Baseline Guard Analyse",
        "text": "path\tchange",
    }


def test_roots_guard_button_analysis_uses_same_chad_flow_as_context_menu():
    calls = {"count": 0}
    dummy = SimpleNamespace()
    dummy.analyze_roots_baseline_guard_tree_selection_with_chad = lambda: calls.__setitem__(
        "count", calls["count"] + 1
    )

    App.analyze_roots_baseline_guard_with_chad(dummy)

    assert calls["count"] == 1


def test_chad_chat_input_uses_copy_paste_context_menu():
    app_source = inspect.getsource(App)

    assert "self.chad_chat_input = tk.Text(" in app_source
    assert 'height=6,' in app_source
    assert "self.attach_copy_paste_context_menu(self.chad_chat_input)" in app_source


def test_chad_output_layout_is_refreshed_after_view_update():
    controller_source = inspect.getsource(chad_controller)

    assert "app.update_chad_output_layout()" in controller_source


def test_roots_guard_builder_smoke_when_display_is_available():
    tk = pytest.importorskip("tkinter")
    ttk = pytest.importorskip("tkinter.ttk")

    if not os.environ.get("DISPLAY", "").strip():
        pytest.skip("Kein DISPLAY für Tk-Smoke-Test verfügbar.")

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk-Smoke-Test nicht möglich: {exc}")

    try:
        root.withdraw()
        dummy = SimpleNamespace()
        dummy.security_nb = ttk.Notebook(root)
        dummy.security_nb.pack()
        dummy.tr = lambda _key, default=None: default or _key
        dummy.cget = root.cget
        dummy.attach_selection_copy_shortcuts = lambda *_args, **_kwargs: None
        dummy.attach_text_context_menu = lambda *_args, **_kwargs: None
        dummy.on_roots_baseline_guard_result_select = lambda *_args, **_kwargs: None
        dummy.on_roots_baseline_guard_whitelist_select = (
            lambda *_args, **_kwargs: None
        )
        dummy.open_selected_roots_baseline_guard_whitelist_entry = (
            lambda *_args, **_kwargs: None
        )
        dummy.refresh_roots_baseline_guard_root_mode_status = (
            lambda *_args, **_kwargs: None
        )
        dummy.roots_baseline_guard_read_current_state = lambda: None
        dummy.roots_baseline_guard_create_baseline = lambda: None
        dummy.roots_baseline_guard_check_baseline = lambda: None
        dummy.roots_baseline_guard_update_baseline = lambda: None
        dummy.roots_baseline_guard_show_last_comparison = lambda: None
        dummy.load_roots_baseline_guard_demo_cases = lambda: None
        dummy.analyze_roots_baseline_guard_with_chad = lambda: None
        dummy.explain_selected_roots_baseline_guard_change = lambda: None
        dummy.add_selected_roots_baseline_guard_change_to_whitelist = lambda: None
        dummy.remove_selected_roots_baseline_guard_change_from_whitelist = lambda: None
        dummy.show_roots_baseline_guard_whitelist = lambda: None

        build_roots_baseline_guard_tab(dummy)

        assert hasattr(dummy, "roots_baseline_guard_results_table")
        assert hasattr(dummy, "roots_root_mode_status_label")
        assert hasattr(dummy, "roots_baseline_guard_root_mode_var")
        assert hasattr(dummy, "roots_baseline_guard_pane")
    finally:
        root.destroy()
