from tools.netmon_state_coordinator import NetmonStateCoordinator


def test_state_coordinator_normalizes_internet_suspend_state():
    c = NetmonStateCoordinator()

    state = c.normalize_internet_suspend_state(
        {
            "ufw_was_active": 1,
            "killswitch_was_active": "",
            "vpn_was_active": "yes",
            "vpn_profile": " proton__ipv4 ",
            "vpn_interface": None,
        }
    )

    assert state == {
        "ufw_was_active": True,
        "killswitch_was_active": False,
        "vpn_was_active": True,
        "vpn_profile": "proton__ipv4",
        "vpn_interface": "",
    }


def test_state_coordinator_finalize_restore_state():
    c = NetmonStateCoordinator()
    pending = {
        "ufw_was_active": True,
        "killswitch_was_active": True,
        "vpn_was_active": True,
        "vpn_profile": "proton",
        "vpn_interface": "proton__ipv4",
    }

    assert c.finalize_internet_restore_state(pending, restore_complete=False) == pending
    assert c.finalize_internet_restore_state(pending, restore_complete=True) == c.default_internet_suspend_state()
