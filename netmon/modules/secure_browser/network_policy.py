"""Destination rules for the slirp uplink in a private browser namespace."""

from ipaddress import collapse_addresses, ip_interface, ip_network
import json
import socket
import subprocess

IP = "/usr/sbin/ip"
NFT = "/usr/sbin/nft"
SLIRP_DNS = "10.0.2.3"
SLIRP_INTERFACE = "tap0"

# Special-use destinations such as private, shared, link-local, transition,
# multicast and broadcast networks. IPv6 additionally requires global unicast.
_BLOCKED_V4 = (
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "172.16.0.0/12",
    "192.0.0.0/24",
    "192.0.2.0/24",
    "192.88.99.0/24",
    "192.168.0.0/16",
    "198.18.0.0/15",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "224.0.0.0/3",
)
_BLOCKED_V6 = ("2001::/23", "2001:db8::/32", "2002::/16", "3fff::/20")
_ADDRESS_GROUPS = 0x10 | 0x100  # RTMGRP_IPV4_IFADDR | RTMGRP_IPV6_IFADDR


def host_address_monitor():
    """Subscribe before taking the address snapshot so changes are observable."""
    monitor = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW, socket.NETLINK_ROUTE)
    try:
        monitor.bind((0, _ADDRESS_GROUPS))
    except OSError:
        monitor.close()
        raise
    return monitor


def host_networks(env, timeout):
    snapshot = subprocess.run(
        [IP, "-j", "address", "show"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=timeout,
    )
    return [
        ip_interface(f"{address['local']}/{address['prefixlen']}").network
        for interface in json.loads(snapshot.stdout)
        for address in interface["addr_info"]
        if address["family"] in {"inet", "inet6"}
    ]


def ruleset(host_networks):
    blocked = {
        4: [ip_network(cidr) for cidr in _BLOCKED_V4],
        6: [ip_network(cidr) for cidr in _BLOCKED_V6],
    }
    for network in host_networks:
        blocked[network.version].append(network)
    ipv4, ipv6 = (
        ", ".join(str(net) for net in collapse_addresses(blocked[version]))
        for version in (4, 6)
    )
    return f"""table inet netmon_browser {{
    chain output {{
        type filter hook output priority filter; policy drop;
        oifname "lo" accept
        oifname "{SLIRP_INTERFACE}" ip daddr {SLIRP_DNS} meta l4proto {{ tcp, udp }} th dport 53 accept
        oifname "{SLIRP_INTERFACE}" ip daddr != {{ {ipv4} }} accept
        oifname "{SLIRP_INTERFACE}" ip6 daddr 2000::/3 ip6 daddr != {{ {ipv6} }} accept
    }}
}}
"""
