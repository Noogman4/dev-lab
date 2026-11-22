#!/usr/bin/env python3
"""Build the independent, unsigned local NetMon management package."""

import argparse
import gzip
import hashlib
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0~beta1"
FIRST_SPLIT_APP = "1.1.22~beta3"
MODULES = (
    "netmon/__init__.py",
    "netmon/config/__init__.py",
    "netmon/config/constants.py",
    "netmon/core/__init__.py",
    "netmon/core/import_limits.py",
    "netmon/core/private_logs.py",
    "netmon/core/private_state.py",
    "netmon/core/log_redaction.py",
    "netmon/core/state.py",
    "netmon/core/utils.py",
    "netmon/core/user_files.py",
    "netmon/core/user_backup.py",
    "netmon/core/lifecycle.py",
    "netmon/core/trusted_sudo.py",
    "netmon/core/privilege_launcher.py",
    "netmon/install_assistant.py",
    "netmon/manage_assistant.py",
)


def build(output):
    output = Path(output).resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("Refusing to overwrite package: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="netmon-manager-build-") as folder:
        tree = Path(folder) / "package"

        def put(name, content, mode=0o644):
            target = tree / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            target.chmod(mode)

        for name in MODULES:
            put("usr/lib/netmon-manager/" + name, (ROOT / name).read_bytes())
        # Only the private copies are relocated. Each helper still requires its
        # fixed installed path, root ownership and safe parent/file metadata.
        for name in ("ufw_snapshot.py", "nm_ownership.py"):
            source = (ROOT / "netmon/core" / name).read_text()
            if 'HELPER = "/usr/lib/netmon/netmon/core/' + name + '"' not in source:
                raise ValueError("Unexpected protected helper layout: " + name)
            relocated = source.replace("/usr/lib/netmon", "/usr/lib/netmon-manager")
            put("usr/lib/netmon-manager/netmon/core/" + name, relocated.encode())
        for name in ("netmon-manage", "netmon-install"):
            put("usr/bin/" + name, (ROOT / "packaging" / name).read_bytes(), 0o755)
        put(
            "usr/bin/netmon-uninstall",
            (ROOT / "scripts/netmon_uninstall_menu.sh").read_bytes(),
            0o755,
        )
        for name in ("netmon-install.desktop", "netmon-uninstall.desktop"):
            put(
                "usr/share/applications/" + name,
                (ROOT / "packaging" / name).read_bytes(),
            )
        put(
            "usr/share/pixmaps/netmon-manager.png",
            (ROOT / "tools/netmon.png").read_bytes(),
        )
        put(
            "usr/share/doc/netmon-manager/copyright",
            (ROOT / "packaging/copyright").read_bytes(),
        )
        put(
            "usr/share/doc/netmon-manager/README.md",
            (ROOT / "docs/NETMON_MANAGER.md").read_bytes(),
        )
        put(
            "usr/share/man/man1/netmon-uninstall.1.gz",
            gzip.compress(
                (ROOT / "packaging/netmon-uninstall.1").read_bytes(), mtime=0
            ),
        )
        installed_size = (
            sum(p.stat().st_size for p in tree.rglob("*") if p.is_file()) + 1023
        ) // 1024
        put(
            "DEBIAN/control",
            (
                f"Package: netmon-manager\nVersion: {VERSION}\nArchitecture: all\n"
                "Maintainer: Mr. Happy <netmon.proglab@protonmail.ch>\n"
                "Section: admin\nPriority: optional\n"
                f"Installed-Size: {installed_size}\n"
                "Depends: python3 (>= 3.11), python3-tk, sudo, x-terminal-emulator\n"
                f"Breaks: netmon (<< {FIRST_SPLIT_APP})\n"
                f"Replaces: netmon (<< {FIRST_SPLIT_APP})\n"
                "Description: Independent NetMon installation, backup and removal assistant\n"
                " Keeps working after the NetMon application has been removed.\n"
            ).encode(),
        )
        for phase in ("postinst", "postrm"):
            put(
                "DEBIAN/" + phase,
                b"#!/bin/sh\nset -e\nif command -v update-desktop-database >/dev/null 2>&1; then\n"
                b"  update-desktop-database /usr/share/applications || true\nfi\nexit 0\n",
                0o755,
            )
        sums = []
        for path in sorted(tree.rglob("*")):
            if path.is_dir():
                path.chmod(0o755)
            elif path.parts[len(tree.parts)] != "DEBIAN":
                sums.append(
                    hashlib.md5(path.read_bytes()).hexdigest()
                    + "  "
                    + str(path.relative_to(tree))
                )
        tree.chmod(0o755)
        put("DEBIAN/md5sums", ("\n".join(sums) + "\n").encode())
        subprocess.run(
            [
                "/usr/bin/dpkg-deb",
                "--root-owner-group",
                "--build",
                str(tree),
                str(output),
            ],
            check=True,
        )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / f"dist/netmon-manager_{VERSION}_all.deb"
    )
    args = parser.parse_args()
    print(build(args.output))


if __name__ == "__main__":
    main()
