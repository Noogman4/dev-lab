#!/usr/bin/env python3
"""Read NetMon's canonical application version without importing the app."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSTANTS_FILE = ROOT / "netmon" / "config" / "constants.py"


def read_netmon_version(path: Path = CONSTANTS_FILE) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "NETMON_APP_VERSION"
            for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            version = node.value.value.strip()
            if version:
                return version
    raise ValueError(f"NETMON_APP_VERSION fehlt in {path}")


if __name__ == "__main__":
    print(read_netmon_version())
