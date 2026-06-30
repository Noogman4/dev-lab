"""Compatibility wrapper for the NetMon state coordinator."""

try:
    from netmon.netmon_state_coordinator import NetmonStateCoordinator
except ModuleNotFoundError:
    try:
        from tools.netmon_state_coordinator import NetmonStateCoordinator
    except ModuleNotFoundError:
        NetmonStateCoordinator = None


__all__ = ["NetmonStateCoordinator"]
