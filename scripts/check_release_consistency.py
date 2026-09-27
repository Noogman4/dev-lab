#!/usr/bin/env python3
"""Fail when current release metadata disagrees with the app version."""

from __future__ import annotations

import json

from read_netmon_version import ROOT, read_netmon_version


def main() -> int:
    version = read_netmon_version()
    errors: list[str] = []

    public_key_path = ROOT / "docs" / "security" / "netmonroots.minisign.pub"
    public_key_lines = [
        line.strip()
        for line in public_key_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(public_key_lines) != 2 or not public_key_lines[1].startswith("RW"):
        errors.append(f"{public_key_path.relative_to(ROOT)}: ungueltiges Key-Format")
        public_key_id = ""
        public_key = ""
    else:
        public_key_id = public_key_lines[0].rsplit(" ", 1)[-1]
        public_key = public_key_lines[1]

    latest_path = ROOT / "site" / "latest-version.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    if latest.get("version") != version:
        errors.append(
            f"{latest_path.relative_to(ROOT)}: erwartet Version {version}, "
            f"gefunden {latest.get('version')!r}"
        )

    required_snippets = {
        "README.md": [f"netmon_{version}_all.deb"],
        "SECURITY.md": [f"`{version}` | Yes", public_key_id, public_key],
        "docs/README.md": [f"Paket- und App-Stand: `{version}`"],
        "docs/CONFIGURATION.md": [f"constants.py`: `{version}`"],
        "docs/DEB_PACKAGING_PLAN.md": [f"Paketstand: `{version}`"],
        "docs/CHANGELOG.md": [f"Version {version}"],
        "packaging/changelog": [f"netmon ({version})"],
        "packaging/netmon.1": [f'"NetMon {version}"'],
        "packaging/netmon-uninstall.1": [f'"NetMon {version}"'],
        "site/download-config.php": [
            f"NetMon {version} package",
            f"netmon_{version}_all.deb",
            f"netmon_dokumentation_{version}.html",
            f"netmon_dokumentation_{version}.pdf",
            "netmon_security_audit_2026_r12.pdf",
        ],
        "site/index.html": [f"<strong>{version}</strong>"],
        "site/en/index.html": [f"<strong>{version}</strong>"],
        "site/downloads.html": [
            f"netmon_{version}_all.deb",
            public_key_id,
            public_key,
        ],
        "site/en/downloads.html": [
            f"netmon_{version}_all.deb",
            public_key_id,
            public_key,
        ],
        "site/docs.html": [f"netmon_dokumentation_{version}.html"],
        "site/en/docs.html": [f"netmon_dokumentation_{version}.html"],
        "site/security-audit.html": [f"NetMon Roots v{version}", "Runde&nbsp;12"],
        "site/en/security-audit.html": [
            f"NetMon Roots v{version}",
            "Round 12",
        ],
    }
    for relative_path, snippets in required_snippets.items():
        path = ROOT / relative_path
        content = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in content:
                errors.append(f"{relative_path}: fehlt {snippet!r}")

    if errors:
        print("Release-Metadaten sind nicht konsistent:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Release-Metadaten konsistent: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
