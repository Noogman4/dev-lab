"""Shared validation for Secure Browser allowlists and policy exceptions."""

from __future__ import annotations

import re
from urllib.parse import urlparse


def normalize_allowed_domain(value: str) -> str | None:
    """Accept a concrete DNS/IPv4 host, optionally supplied as an HTTP(S) URL.

    Wildcards belong only in generated subdomain patterns, never in user input.
    IPv6 authorities are unsupported by the existing pattern generator.
    """
    if not isinstance(value, str) or any(
        ord(char) < 32 or ord(char) == 127 for char in value
    ):
        return None
    raw = value.strip()
    if not raw or len(raw) > 4096 or any(char.isspace() for char in raw):
        return None
    try:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.netloc.endswith(":")
        ):
            return None
        host = parsed.hostname.encode("idna").decode("ascii").lower().removesuffix(".")
        labels = host.split(".")
        if len(host) > 253 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in labels
        ):
            return None
        port = parsed.port
        if port is not None and not 1 <= port <= 65535:
            return None
        return f"{host}:{port}" if port is not None else host
    except (ValueError, UnicodeError):
        return None


def require_allowed_domains(values: list[str]) -> list[str]:
    """Reject the whole submitted allowlist if any entry is invalid."""
    normalized: list[str] = []
    for value in values:
        host = normalize_allowed_domain(value)
        if host is None:
            raise ValueError(
                "Ungültige erlaubte Domain: konkrete HTTP(S)-Hosts ohne Wildcards erforderlich."
            )
        if host not in normalized:
            normalized.append(host)
    if not normalized:
        raise ValueError("Mindestens eine gültige erlaubte Domain ist erforderlich.")
    return normalized


def validate_website_filter(payload: dict) -> None:
    """Ensure filter exceptions remain anchored to concrete hostnames.

    An explicitly absent WebsiteFilter (compatible profile) remains supported.
    Generated '*.example.com' patterns are allowed; global host masks are not.
    """
    policies = payload.get("policies", {})
    if not isinstance(policies, dict):
        raise ValueError("policies muss ein JSON-Objekt sein.")
    if "WebsiteFilter" not in policies:
        return
    website_filter = policies["WebsiteFilter"]
    if not isinstance(website_filter, dict):
        raise ValueError("WebsiteFilter muss ein JSON-Objekt sein.")
    exceptions = website_filter.get("Exceptions", [])
    if not isinstance(exceptions, list):
        raise ValueError("WebsiteFilter.Exceptions muss eine Liste sein.")
    for pattern in exceptions:
        match = (
            re.fullmatch(r"(https?|\*)://([^/]+)/[^\s]*", pattern)
            if isinstance(pattern, str)
            else None
        )
        if match is None or any(ord(char) < 32 or ord(char) == 127 for char in pattern):
            raise ValueError("Ungültige WebsiteFilter-Ausnahme.")
        authority = match[2].removeprefix("*.")
        # Canonical equality also rules out userinfo, escaped hosts and other
        # syntax whose browser interpretation could differ from our parser.
        if normalize_allowed_domain(authority) != authority:
            raise ValueError(
                "WebsiteFilter-Ausnahmen benötigen einen konkreten Host; globale Wildcards sind verboten."
            )
