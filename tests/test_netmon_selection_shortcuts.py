import inspect

from netmon.app import App
from netmon.ui.tabs.vpn_slots_tab import build_vpn_slots_tab


class DummyTreeview:
    def __init__(self, columns, rows, selected):
        self._columns = tuple(columns)
        self._rows = dict(rows)
        self._selected = tuple(selected)

    def __getitem__(self, key):
        if key == "columns":
            return self._columns
        raise KeyError(key)

    def selection(self):
        return self._selected

    def heading(self, column, option):
        if option == "text":
            return column.upper()
        raise KeyError(option)

    def item(self, item_id, option):
        if option == "values":
            return self._rows[item_id]
        raise KeyError(option)


def test_attach_all_selection_copy_shortcuts_registers_expected_targets():
    app = App.__new__(App)
    calls = []
    entry_calls = []

    app.safe_attach_selection_copy_shortcuts = lambda widget_name, kind: calls.append(
        (widget_name, kind)
    )
    app.safe_attach_entry_edit_shortcuts = lambda widget_name: entry_calls.append(
        widget_name
    )

    app.attach_all_selection_copy_shortcuts()

    assert calls == [
        ("text", "text"),
        ("dns_text", "text"),
        ("nmap_text", "text"),
        ("mtr_text", "text"),
        ("iftop_text", "text"),
        ("htop_text", "text"),
        ("linux_help_text", "text"),
        ("hdd_info_text", "text"),
        ("security_detail", "text"),
        ("clamav_output_text", "text"),
        ("packet_capture_text", "text"),
        ("lynis_text", "text"),
        ("rkhunter_text", "text"),
        ("startup_guard_details_text", "text"),
        ("process_guard_detail", "text"),
        ("chad_analysis_text", "text"),
        ("log_overlay_picker_list", "listbox"),
        ("linux_help_listbox", "listbox"),
        ("trace_table", "treeview"),
        ("conn_table", "treeview"),
        ("hdd_table", "treeview"),
        ("link_table", "treeview"),
        ("vpn_table", "treeview"),
        ("security_table", "treeview"),
        ("process_guard_tree", "treeview"),
        ("startup_guard_tree", "treeview"),
    ]
    assert entry_calls == [
        "conn_filter_entry",
        "hdd_name_entry",
        "link_target_entry",
        "vpn_custom_name_entry",
        "manual_wg_profile_name_entry",
        "manual_wg_private_key_entry",
        "manual_wg_public_key_entry",
        "manual_wg_endpoint_entry",
        "manual_wg_allowed_ips_entry",
        "manual_wg_dns_entry",
        "manual_wg_keepalive_entry",
        "openai_api_key_entry",
    ]


def test_attach_selection_copy_shortcuts_source_binds_ctrl_c_and_ctrl_v():
    source = inspect.getsource(App.attach_selection_copy_shortcuts)

    assert 'widget.bind("<Control-c>", handler, add="+")' in source
    assert 'widget.bind("<Control-C>", handler, add="+")' in source
    assert 'widget.bind("<Control-Insert>", handler, add="+")' in source
    assert 'widget.bind(\n                "<Control-v>",' in source
    assert 'widget.bind(\n                "<Shift-Insert>",' in source


def test_attach_entry_edit_shortcuts_source_binds_copy_and_paste():
    source = inspect.getsource(App.attach_entry_edit_shortcuts)

    assert 'entry_widget.bind("<Control-c>", copy_handler, add="+")' in source
    assert 'entry_widget.bind("<Control-v>", paste_handler, add="+")' in source
    assert 'entry_widget.bind("<Shift-Insert>", paste_handler, add="+")' in source


def test_attach_text_context_menu_source_contains_expected_actions():
    source = inspect.getsource(App.attach_text_context_menu)

    assert 'label="Ausschneiden"' in source
    assert 'label="Kopieren"' in source
    assert 'label="Einfügen"' in source
    assert 'label="Alles markieren"' in source
    assert "return self._show_context_menu(menu, event)" in source
    assert 'widget.bind("<Button-3>", show_menu, add="+")' in source


def test_vpn_slots_tab_source_attaches_context_menu_to_manual_inputs():
    source = inspect.getsource(build_vpn_slots_tab)

    assert "app.attach_text_context_menu(app.vpn_custom_name_entry)" in source
    assert "app.attach_text_context_menu(app.vpn_profile_combo)" in source
    assert "app.attach_text_context_menu(app.manual_wg_profile_name_entry)" in source
    assert "app.attach_text_context_menu(app.manual_wg_private_key_entry)" in source
    assert "app.attach_text_context_menu(app.manual_wg_public_key_entry)" in source
    assert "app.attach_text_context_menu(app.manual_wg_endpoint_entry)" in source
    assert "app.attach_text_context_menu(app.manual_wg_allowed_ips_entry)" in source
    assert "app.attach_text_context_menu(app.manual_wg_dns_entry)" in source
    assert "app.attach_text_context_menu(app.manual_wg_keepalive_entry)" in source
    assert "app.attach_text_context_menu(app.manual_wg_slot_combo)" in source


def test_get_treeview_selection_text_formats_headers_and_rows():
    app = App.__new__(App)
    treeview = DummyTreeview(
        columns=("proto", "state", "pid"),
        rows={
            "row1": ("tcp", "ESTAB", "123"),
            "row2": ("udp", "UNCONN", "456"),
        },
        selected=("row1", "row2"),
    )

    text = app.get_treeview_selection_text(treeview)

    assert text.splitlines()[0] == "PROTO\tSTATE\tPID"
    assert "tcp\tESTAB\t123" in text
    assert "udp\tUNCONN\t456" in text
