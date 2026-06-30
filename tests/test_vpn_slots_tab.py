from netmon.ui.tabs import vpn_slots_tab


def test_vpn_slot_choices_match_configured_slot_count():
    choices = vpn_slots_tab._vpn_slot_choices()

    assert choices[0] == "1"
    assert choices[-1] == str(len(choices))


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
