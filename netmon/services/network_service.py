"""Compatibility wrapper for the NetMon network service."""

try:
    from netmon.netmon_network_service import NetmonNetworkService
except ModuleNotFoundError:
    try:
        from tools.netmon_network_service import NetmonNetworkService
    except ModuleNotFoundError:
        NetmonNetworkService = None


__all__ = ["NetmonNetworkService"]
