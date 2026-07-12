import os
from types import SimpleNamespace

import pytest

from netmon.features import vpn_controller
from netmon.ui.tabs import vpn_slots_tab


def test_vpn_slot_choices_match_configured_slot_count():
    choices = vpn_slots_tab._vpn_slot_choices()

    assert choices == [str(slot_no) for slot_no in range(1, 11)]


def test_wg_profiles_returns_list_copy():
    app = type("DummyApp", (), {"wg_profiles": ("wg-a", "wg-b")})()

    assert vpn_slots_tab._wg_profiles(app) == ["wg-a", "wg-b"]


def test_primary_vpn_slot_value_uses_defaults_for_missing_entries():
    app = type(
        "DummyApp",
        (),
        {"primary_vpn_slots": [{"custom_name": "Work", "profile": "wg-a"}]},
    )()

    assert (
        vpn_slots_tab._primary_vpn_slot_value(app, 0, "custom_name", "fallback")
        == "Work"
    )
    assert (
        vpn_slots_tab._primary_vpn_slot_value(app, 1, "profile", "fallback")
        == "fallback"
    )


def test_vpn_profile_delete_button_uses_profile_from_selected_table_row():
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
        deleted_profiles = []
        app = SimpleNamespace(
            system_nb=ttk.Notebook(root),
            wg_profiles=["proton", "work"],
            vpn_slots=[
                {"slot": 1, "custom_name": "", "profile": ""},
                {"slot": 2, "custom_name": "Other", "profile": "proton"},
            ],
            primary_vpn_slots=[],
        )
        app.system_nb.pack()
        app.tr = lambda _key, default=None: default or _key
        app.attach_text_context_menu = lambda *_args, **_kwargs: None
        app.attach_simple_tree_context_menu = lambda *_args, **_kwargs: None
        app.register_feature_button = lambda *_args, **_kwargs: None
        app.add_tooltip = lambda *_args, **_kwargs: None
        app.assign_vpn_slot = lambda: None
        app.clear_vpn_slot = lambda **_kwargs: None
        app.test_vpn_slot = lambda: None
        app.delete_selected_vpn_profile = lambda: deleted_profiles.append(
            app.vpn_profile_var.get()
        )
        app.save_primary_vpn_slot = lambda _slot_no: None
        app.apply_manual_wireguard_profile = lambda: None
        app.clear_manual_wireguard_form = lambda: None
        app._sync_manual_wg_slot_controls = lambda: None
        app._base_wg_profile_name = lambda profile: vpn_controller.base_wg_profile_name(
            app, profile
        )
        app._vpn_slot_status = lambda slot: (
            ("bereit", "green") if slot.get("profile") else ("frei", "gray")
        )
        app._on_vpn_form_field_changed = lambda *_args: setattr(
            app, "_vpn_form_dirty", True
        )
        app.load_vpn_slot_into_form = (
            lambda slot_no: vpn_controller.load_vpn_slot_into_form(app, slot_no)
        )
        app.refresh_vpn_slots_table = lambda: vpn_controller.refresh_vpn_slots_table(
            app
        )
        app.update_vpn_slot_buttons = lambda: None
        app.on_vpn_slot_select = lambda event=None: vpn_controller.on_vpn_slot_select(
            app, event
        )
        app.on_vpn_table_select = lambda event=None: vpn_controller.on_vpn_table_select(
            app, event
        )

        vpn_slots_tab.build_vpn_slots_tab(app)
        app.vpn_table.selection_set("vpn-slot-2")
        app.vpn_table.event_generate("<<TreeviewSelect>>")
        root.update()
        app.btn_vpn_delete.invoke()

        assert app.vpn_slot_choice.get() == "2"
        assert app.vpn_profile_var.get() == "proton"
        assert deleted_profiles == ["proton"]
    finally:
        root.destroy()
