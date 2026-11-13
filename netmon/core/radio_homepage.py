"""Canonical station addresses for display/copy, never browser navigation.

These syntax checks do not attest DNS answers or redirects. An ambient browser
cannot be pinned to our network policy, so this module never opens an address.
"""

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit

_LOCAL_SUFFIXES = (
    "localhost",
    "local",
    "localdomain",
    "lan",
    "home",
    "home.arpa",
    "internal",
    "intranet",
    "corp",
    "test",
    "invalid",
    "example",
    "onion",
    "i2p",
)


def normalize_homepage_url(value):
    if not isinstance(value, str) or len(value) > 4096:
        return ""
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return ""
    url = value.strip()
    if not url or "\\" in url or any(char.isspace() for char in url):
        return ""
    if re.search(r"%(?![0-9a-fA-F]{2})|%(?:0[0-9a-f]|1[0-9a-f]|20|7f)", url, re.I):
        return ""
    try:
        parsed = urlsplit(url)
        default_port = {"http": 80, "https": 443}.get(parsed.scheme)
        if (
            default_port is None
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or "%" in parsed.netloc
            or parsed.netloc.endswith(":")
            or parsed.port not in {None, default_port}
        ):
            return ""
        raw_host = parsed.hostname
        raw_authority = f"[{raw_host}]" if ":" in raw_host else raw_host
        if parsed.netloc.lower() not in {
            raw_authority.lower(),
            f"{raw_authority}:{default_port}".lower(),
        }:
            return ""
        host = parsed.hostname.encode("idna").decode("ascii").lower().removesuffix(".")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            labels = host.split(".")
            if (
                len(host) > 253
                or len(labels) < 2
                # WHATWG also treats abbreviated/octal/hex numeric hosts as IPs.
                or re.fullmatch(r"(?:[0-9]+|0x[0-9a-f]+)", labels[-1])
                or any(
                    not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                    for label in labels
                )
                or any(
                    host == suffix or host.endswith("." + suffix)
                    for suffix in _LOCAL_SUFFIXES
                )
            ):
                return ""
            authority = host
        else:
            if (
                not address.is_global
                or address.is_multicast
                or address.is_unspecified
                or address.is_reserved
            ):
                return ""
            authority = (
                f"[{address.compressed}]" if address.version == 6 else str(address)
            )
        return urlunsplit(
            (parsed.scheme, authority, parsed.path, parsed.query, parsed.fragment)
        )
    except (ValueError, UnicodeError):
        return ""
