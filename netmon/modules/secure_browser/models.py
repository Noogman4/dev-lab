"""Data models for the NetMon Secure Browser module."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class BrowserContainer:
    """Minimal container model for future Secure Browser integration."""

    name: str
    path: Path
    binary_path: Path
    profile_path: Path
    homepage_url: str
    allowed_domains: list[str] = field(default_factory=list)
    icon_path: Path | None = None
    menu_entry_path: Path | None = None
    status: str = "prepared"
