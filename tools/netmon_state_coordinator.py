"""NetMon state coordination helpers."""

from __future__ import annotations


class NetmonStateCoordinator:
    """Centralizes state-shape and transition helpers for network/security flows."""

    def default_internet_suspend_state(self):
        return {
            "ufw_was_active": False,
            "killswitch_was_active": False,
            "vpn_was_active": False,
            "vpn_profile": "",
            "vpn_interface": "",
        }

    def normalize_internet_suspend_state(self, state):
        base = self.default_internet_suspend_state()
        if not isinstance(state, dict):
            return base
        merged = {**base, **state}
        merged["ufw_was_active"] = bool(merged.get("ufw_was_active"))
        merged["killswitch_was_active"] = bool(merged.get("killswitch_was_active"))
        merged["vpn_was_active"] = bool(merged.get("vpn_was_active"))
        merged["vpn_profile"] = (merged.get("vpn_profile") or "").strip()
        merged["vpn_interface"] = (merged.get("vpn_interface") or "").strip()
        return merged

    def capture_internet_suspend_state(
        self,
        *,
        ufw_was_active,
        killswitch_was_active,
        vpn_was_active,
        vpn_profile,
        vpn_interface,
    ):
        return self.normalize_internet_suspend_state(
            {
                "ufw_was_active": ufw_was_active,
                "killswitch_was_active": killswitch_was_active,
                "vpn_was_active": vpn_was_active,
                "vpn_profile": vpn_profile,
                "vpn_interface": vpn_interface,
            }
        )

    def finalize_internet_restore_state(self, state, restore_complete):
        if restore_complete:
            return self.default_internet_suspend_state()
        return self.normalize_internet_suspend_state(state)

    def capture_stealth_runtime_state(
        self,
        *,
        ipv6_was_disabled,
        killswitch_was_on,
        vpn_was_active,
        vpn_profile,
        dns_choice,
    ):
        return {
            "ipv6_was_disabled": bool(ipv6_was_disabled),
            "killswitch_was_on": bool(killswitch_was_on),
            "vpn_was_active": bool(vpn_was_active),
            "vpn_profile": (vpn_profile or "").strip(),
            "dns_choice": (dns_choice or "System (DHCP/auto)").strip()
            or "System (DHCP/auto)",
        }
