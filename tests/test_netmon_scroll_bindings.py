import inspect

from netmon.app import App


def test_local_mousewheel_bindings_are_present():
    app_source = inspect.getsource(App)

    assert "self.after(1200, self.attach_all_local_mousewheel_bindings)" in app_source
    assert "def attach_local_mousewheel_binding(self, widget_name: str):" in app_source
    assert 'widget.bind("<MouseWheel>", _on_mousewheel, add="+")' in app_source
    assert 'widget.bind("<Button-4>", _on_wheel_up, add="+")' in app_source
    assert 'widget.bind("<Button-5>", _on_wheel_down, add="+")' in app_source
    assert 'widget.bind("<Shift-MouseWheel>", _on_shift_mousewheel, add="+")' in app_source
    assert 'widget.bind("<Shift-Button-4>", _on_shift_wheel_up, add="+")' in app_source
    assert 'widget.bind("<Shift-Button-5>", _on_shift_wheel_down, add="+")' in app_source
    assert 'widget.bind("<Button-1>", _focus_widget, add="+")' in app_source
    assert "focus_required = True" in app_source
    assert "if focus_required and not _widget_has_focus():" in app_source
    assert "self._local_mousewheel_target_names = tuple(targets)" in app_source
    assert "def _deactivate_local_mousewheel_scroll(self, event=None):" in app_source
    assert "self._deactivate_local_mousewheel_scroll(event)" in app_source
    assert '"dns_text"' in app_source
    assert '"security_detail"' in app_source
    assert '"repository_guard_detail_text"' in app_source
    assert '"process_guard_tree"' in app_source
    assert '"process_guard_detail"' in app_source
    assert '"chad_chat_input"' in app_source
    assert '"chad_analysis_text"' in app_source
    assert '"roots_baseline_guard_canvas"' in app_source
    assert '"roots_baseline_guard_info_text"' in app_source
    assert '"clamav_canvas"' in app_source
    assert '"firewall_tab_summary_text"' in app_source
