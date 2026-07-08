"""NetMon network/firewall/vpn command service layer."""

from __future__ import annotations

from typing import Callable, Sequence, Tuple


class NetmonNetworkService:
    """Thin command adapter around the injected command runner."""

    def __init__(self, runner: Callable[..., Tuple[int, str]]):
        self._runner = runner

    def run(self, args: Sequence[str], timeout: int = 15) -> Tuple[int, str]:
        return self._runner(list(args), timeout=timeout)

    def file_exists(self, path: str) -> Tuple[int, str]:
        return self.run(["sudo", "-n", "test", "-f", path], timeout=5)

    def wg_quick_up(self, profile: str, timeout: int = 20) -> Tuple[int, str]:
        return self.run(["sudo", "-n", "wg-quick", "up", profile], timeout=timeout)

    def wg_quick_down(self, profile: str, timeout: int = 12) -> Tuple[int, str]:
        return self.run(["sudo", "-n", "wg-quick", "down", profile], timeout=timeout)

    def ufw_enable_force(self, timeout: int = 20) -> Tuple[int, str]:
        return self.run(["sudo", "-n", "ufw", "--force", "enable"], timeout=timeout)

    def ufw_status(self, verbose: bool = False, timeout: int = 12) -> Tuple[int, str]:
        if verbose:
            return self.run(["sudo", "-n", "ufw", "status", "verbose"], timeout=timeout)
        return self.run(["sudo", "-n", "ufw", "status"], timeout=timeout)

    def ufw_default(self, action: str, direction: str, timeout: int = 20) -> Tuple[int, str]:
        return self.run(["sudo", "-n", "ufw", "default", action, direction], timeout=timeout)

    def ufw_allow_on_iface(self, direction: str, iface: str, timeout: int = 20) -> Tuple[int, str]:
        return self.run(["sudo", "-n", "ufw", "allow", direction, "on", iface], timeout=timeout)

    def ufw_delete_allow_on_iface(self, direction: str, iface: str, timeout: int = 20) -> Tuple[int, str]:
        return self.run(["sudo", "-n", "ufw", "delete", "allow", direction, "on", iface], timeout=timeout)

    def ufw_allow_udp_endpoint(self, ip: str, port: str, timeout: int = 20) -> Tuple[int, str]:
        return self.run(
            [
                "sudo",
                "-n",
                "ufw",
                "allow",
                "out",
                "to",
                ip,
                "port",
                str(port),
                "proto",
                "udp",
            ],
            timeout=timeout,
        )

    def ufw_delete_allow_udp_endpoint(self, ip: str, port: str, timeout: int = 20) -> Tuple[int, str]:
        return self.run(
            [
                "sudo",
                "-n",
                "ufw",
                "delete",
                "allow",
                "out",
                "to",
                ip,
                "port",
                str(port),
                "proto",
                "udp",
            ],
            timeout=timeout,
        )

