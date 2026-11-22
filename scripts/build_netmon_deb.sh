#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PKG_NAME="netmon"
PKG_VERSION="$(python3 "$ROOT_DIR/scripts/read_netmon_version.py")"
DOCS_VERSION="$PKG_VERSION"
PKG_ARCH="all"
MAINTAINER="Mr. Happy <netmon.proglab@protonmail.ch>"

TEST_BUILD=0
PACKAGE_SUMMARY="Linux-Netzwerkmonitor mit Security-, VPN- und Radio-Funktionen"
PYTHON_DEPENDS="python3 (>= 3.11), python3-tk, python3-psutil, python3-pil, python3-pil.imagetk"
FEATURE_TOOLS="network-manager, systemd-resolved, dnsutils, wireguard-tools, ufw, traceroute, mtr, nmap, iftop, htop, lynis, rkhunter, clamav, clamav-freshclam, speedtest-cli, mpv, pipewire-bin, librsvg2-2 (>= 2.46), libcairo2, whois, python3-keyring, python3-gi, gir1.2-vte-2.91"
EXTRA_TOOLS="wireshark, tshark, projectm, projectm-pulseaudio, python3-pypdf2, python3-docx, python3-openpyxl, python3-pygame, python3-pgzero, sudo, gnome-keyring"
BROWSER_DEPENDS="bubblewrap (>= 0.9.0), slirp4netns (>= 1.2.1), dbus-daemon, dbus-bin, util-linux, nftables, iproute2"
DEPENDENCIES="$PYTHON_DEPENDS, udisks2, cryptsetup, $BROWSER_DEPENDS"
RELATIONSHIPS="Recommends: netmon-manager (>= 1.0.0~beta1), netmon-web-browser-runtime, weston, $FEATURE_TOOLS
Suggests: $EXTRA_TOOLS"
RELEASE_BUILD=0
RELEASE_COMMIT=""
WITH_PROJECTM_ADAPTERS=0
if [[ $# == 1 && "$1" == "--with-projectm-adapters" ]]; then
  # Local machine-specific test package. This lane never gets a release receipt.
  WITH_PROJECTM_ADAPTERS=1
  PKG_ARCH="$(dpkg --print-architecture)"
  if [[ "$PKG_ARCH" != "amd64" ]]; then
    echo "The current projectM adapters support amd64 only." >&2
    exit 2
  fi
  DEPENDENCIES+=", libc6 (>= 2.34), libstdc++6 (>= 13.2.0), libgcc-s1, libgl1, libegl1, libx11-6"
  python3 -I - "$ROOT_DIR" <<'PY'
import sys

sys.path.insert(0, sys.argv[1])
from netmon.core import projectm_frontend, projectm_native

payload = projectm_frontend.PAYLOAD
for validate in (projectm_native.artifact, projectm_native.gpu_artifact):
    binary = validate(payload)
    header = binary.read_bytes()[:20]
    if header[:6] != b"\x7fELF\x02\x01" or header[18:20] != b"\x3e\x00":
        raise ValueError("projectM adapter is not an amd64 ELF executable")
PY
  shift
fi
if [[ $# == 1 && "$1" == "--release" ]]; then
  # Official lane: only a clean, committed package source gets a receipt that
  # the signed production bundles accept. Plain local builds never get one.
  RELEASE_BUILD=1
  RELEASE_COMMIT="$(python3 "$ROOT_DIR/scripts/netmon_release_deb_receipt.py" preflight)"
  shift
fi
if (( $# )); then
  if [[ "$1" == "--help" && $# == 1 ]]; then
    echo "Usage: $0 [--release | --with-projectm-adapters | --test-version ${DOCS_VERSION}~v4dnstestYYYYMMDD.N]"
    echo "  --release  official build from a clean commit, with release receipt"
    echo "  (none)     local test build; never accepted by signed release bundles"
    echo "  --with-projectm-adapters  local amd64 build with verified existing adapters"
    exit 0
  fi
  if [[ "$1" != "--test-version" || $# != 2 ]]; then
    echo "Unsupported build arguments; use --help." >&2
    exit 2
  fi
  version_suffix="${2#"$DOCS_VERSION"~v4dnstest}"
  if [[ "$2" != "$DOCS_VERSION"~v4dnstest* || ! "$version_suffix" =~ ^[0-9]{8}\.[0-9]+$ ]]; then
    echo "Test version must be ${DOCS_VERSION}~v4dnstestYYYYMMDD.N" >&2
    exit 2
  fi
  dpkg --validate-version "$2"
  PKG_VERSION="$2"
  TEST_BUILD=1
  PACKAGE_SUMMARY="TESTBUILD NetMon V4 DNS (DHCP/ISP-Freigabe gesperrt)"
  DEPENDENCIES="$PYTHON_DEPENDS, $BROWSER_DEPENDS"
  RELATIONSHIPS="Suggests: $FEATURE_TOOLS, $EXTRA_TOOLS, udisks2, cryptsetup, netmon-web-browser-runtime, weston"
fi

# The split manager owns launchers that old combined packages still ship.
# Do not generate a new split App with an old, incompatible package identity.
if ! dpkg --compare-versions "$PKG_VERSION" ge '1.1.22~beta3'; then
  echo "Split packaging requires App version >= 1.1.22~beta3. Raise release metadata consistently first." >&2
  exit 2
fi

BUILD_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/netmon-debbuild.XXXXXX")"
PKG_DIR="$BUILD_ROOT/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"
OUT_DEB="$ROOT_DIR/dist/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
OUT_RECEIPT="$OUT_DEB.release.json"
if [[ -e "$OUT_DEB" || -L "$OUT_DEB" || -e "$OUT_RECEIPT" || -L "$OUT_RECEIPT" ]]; then
  echo "Refusing to overwrite existing package or receipt: $OUT_DEB" >&2
  exit 1
fi
APP_ROOT="$PKG_DIR/usr/lib/netmon"
APP_PY_ROOT="$APP_ROOT/netmon"
TOOLS_ROOT="$APP_ROOT/tools"
ASSETS_ROOT="$PKG_DIR/usr/share/netmon/assets"
FUN_ASSETS_ROOT="$ASSETS_ROOT/fun"
DOCS_ROOT="$PKG_DIR/usr/share/doc/netmon"
MAN_ROOT="$PKG_DIR/usr/share/man/man1"

cleanup() {
  rm -rf "$BUILD_ROOT"
}

trap cleanup EXIT

copy_file() {
  local src="$1"
  local dst="$2"
  install -D -m 0644 "$src" "$dst"
}

copy_tree() {
  local src="$1"
  local dst="$2"
  mkdir -p "$dst"
  cp -a "$src"/. "$dst"/
}

copy_tree_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -d "$src" ]; then
    copy_tree "$src" "$dst"
  fi
}

copy_file_if_exists() {
  local src="$1"
  local dst="$2"
  if [ -f "$src" ]; then
    copy_file "$src" "$dst"
  fi
}

mkdir -p "$ROOT_DIR/dist"
mkdir -p \
  "$PKG_DIR/DEBIAN" \
  "$APP_PY_ROOT" \
  "$TOOLS_ROOT" \
  "$ASSETS_ROOT/log-pics" \
  "$FUN_ASSETS_ROOT" \
  "$DOCS_ROOT" \
  "$MAN_ROOT" \
  "$PKG_DIR/usr/bin" \
  "$PKG_DIR/usr/share/applications" \
  "$PKG_DIR/usr/share/doc-base" \
  "$PKG_DIR/usr/share/metainfo" \
  "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$PKG_DIR/usr/share/lintian/overrides"

# Runtime code and packaged defaults.
copy_file "$ROOT_DIR/netmon/__init__.py" "$APP_PY_ROOT/__init__.py"
copy_file "$ROOT_DIR/netmon/__main__.py" "$APP_PY_ROOT/__main__.py"
copy_file "$ROOT_DIR/netmon/main.py" "$APP_PY_ROOT/main.py"
copy_file "$ROOT_DIR/netmon/app.py" "$APP_PY_ROOT/app.py"
copy_file "$ROOT_DIR/netmon/netmon_ops.py" "$APP_PY_ROOT/netmon_ops.py"
copy_file "$ROOT_DIR/netmon/netmon_network_service.py" "$APP_PY_ROOT/netmon_network_service.py"
copy_file "$ROOT_DIR/netmon/netmon_state_coordinator.py" "$APP_PY_ROOT/netmon_state_coordinator.py"
copy_file "$ROOT_DIR/netmon/netmon_security_parser.py" "$APP_PY_ROOT/netmon_security_parser.py"
copy_file "$ROOT_DIR/netmon/netmon_security_store.py" "$APP_PY_ROOT/netmon_security_store.py"
copy_file "$ROOT_DIR/netmon/netmon_projectm_sidecar.py" "$APP_PY_ROOT/netmon_projectm_sidecar.py"
copy_file "$ROOT_DIR/netmon/netmon_radio_app.py" "$APP_PY_ROOT/netmon_radio_app.py"
copy_file "$ROOT_DIR/netmon/netmon_radio_core.py" "$APP_PY_ROOT/netmon_radio_core.py"
copy_file "$ROOT_DIR/tools/netmon-linux-befehlsdatenbank-v1.csv" "$APP_PY_ROOT/linux-befehle.csv"
copy_file "$ROOT_DIR/tools/netmon-linux-befehlsdatenbank-v1.csv" "$APP_PY_ROOT/netmon-linux-befehlsdatenbank-v1.csv"
# Ship exactly the validated catalog and its documents, without review backups.
python3 -I - "$ROOT_DIR" "$APP_ROOT" <<'LINUX_HELP_DOCS'
import hashlib
from pathlib import Path
import sys

root, target = map(Path, sys.argv[1:])
sys.path.insert(0, str(root))
from netmon.services import linux_help_markdown_service as markdown

records, _sources = markdown._catalog(str(markdown.DOCUMENT_DIR))
output = target / "docs/linux-befehlsdatenbank"
output.mkdir(parents=True, exist_ok=True)
output.parent.chmod(0o755)
output.chmod(0o755)
for record in records.values():
    entry = {"id": record["id"], "name": record["name"], "cmd": record["name"]}
    if markdown.load_command_document(entry) is None:
        raise ValueError("Missing Linux command documentation")
    data = markdown._read_regular(
        markdown.DOCUMENT_DIR / record["document"], markdown.MAX_BYTES
    )
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError("Linux command documentation changed during packaging")
    destination = output / record["document"]
    destination.write_bytes(data)
    destination.chmod(0o644)
(output / "index.json").write_bytes(
    markdown._read_regular(
        markdown.DOCUMENT_DIR / "index.json", markdown.MAX_CATALOG_BYTES
    )
)
(output / "index.json").chmod(0o644)
LINUX_HELP_DOCS
python3 -I - "$ROOT_DIR" "$APP_ROOT" <<'LINUX_GLOSSARY_DOCS'
import hashlib
from pathlib import Path
import sys

root, target = map(Path, sys.argv[1:])
sys.path.insert(0, str(root))
from netmon.services import linux_help_glossary_service as glossary
from netmon.services import linux_help_markdown_service as markdown

records, _sources = glossary.catalog()
output = target / "docs/linux-glossar"
output.mkdir(parents=True, exist_ok=True)
output.parent.chmod(0o755)
output.chmod(0o755)
for record in records.values():
    entry = {"id": record["id"], "name": record["term"], "entry_type": "glossary"}
    if glossary.load_glossary_document(entry) is None:
        raise ValueError("Missing glossary documentation")
    data = markdown._read_regular(
        glossary.DOCUMENT_DIR / record["document"], markdown.MAX_BYTES
    )
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError("Glossary documentation changed during packaging")
    destination = output / record["document"]
    destination.write_bytes(data)
    destination.chmod(0o644)
(output / "index.json").write_bytes(
    markdown._read_regular(
        glossary.DOCUMENT_DIR / "index.json", markdown.MAX_CATALOG_BYTES
    )
)
(output / "index.json").chmod(0o644)
LINUX_GLOSSARY_DOCS
copy_file "$ROOT_DIR/docs/linux-komponenten/Zorin-OS-Komponenten.md" "$APP_ROOT/docs/linux-komponenten/Zorin-OS-Komponenten.md"
copy_file "$ROOT_DIR/docs/linux-komponenten/Linux-Mint-Komponenten.md" "$APP_ROOT/docs/linux-komponenten/Linux-Mint-Komponenten.md"
copy_file "$ROOT_DIR/docs/linux-quiz/questions.json" "$APP_ROOT/docs/linux-quiz/questions.json"
copy_file_if_exists "$ROOT_DIR/netmon_radio_app.py" "$APP_ROOT/netmon_radio_app.py"

copy_tree "$ROOT_DIR/netmon/config" "$APP_PY_ROOT/config"
copy_tree "$ROOT_DIR/netmon/core" "$APP_PY_ROOT/core"
copy_tree "$ROOT_DIR/netmon/features" "$APP_PY_ROOT/features"
rm -f "$APP_PY_ROOT/features/Code-the-Classics.zip"
copy_tree "$ROOT_DIR/netmon/lang" "$APP_PY_ROOT/lang"
copy_tree "$ROOT_DIR/netmon/modules" "$APP_PY_ROOT/modules"
copy_tree "$ROOT_DIR/netmon/services" "$APP_PY_ROOT/services"
copy_tree "$ROOT_DIR/netmon/ui" "$APP_PY_ROOT/ui"
if (( WITH_PROJECTM_ADAPTERS )); then
  copy_tree "$ROOT_DIR/netmon/native/projectm_pcm" "$APP_PY_ROOT/native/projectm_pcm"
  rm -f "$APP_PY_ROOT/native/projectm_pcm/.gitignore"
  python3 -I - "$APP_PY_ROOT/native/projectm_pcm/build" <<'PY'
import hashlib
import json
from pathlib import Path
import subprocess
import sys

directory = Path(sys.argv[1])
for executable, metadata in (
    ("pcm-renderer", "build.json"),
    ("egl-renderer", "egl-build.json"),
):
    binary, manifest = directory / executable, directory / metadata
    if binary.is_symlink() or manifest.is_symlink():
        raise ValueError("Adapter staging refuses symbolic links")
    record = json.loads(manifest.read_text())
    before = hashlib.sha256(binary.read_bytes()).hexdigest()
    if before != record["binary_sha256"]:
        raise ValueError("Adapter changed before package staging")
    subprocess.run(["/usr/bin/strip", "--strip-unneeded", str(binary)], check=True)
    record["unstripped_binary_sha256"] = before
    record["packaging_transform"] = "strip --strip-unneeded"
    record["binary_sha256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(record, indent=2) + "\n")
PY
fi

# Runtime tool assets referenced by the application via repo-relative paths.
copy_file "$ROOT_DIR/tools/__init__.py" "$TOOLS_ROOT/__init__.py"
copy_file "$ROOT_DIR/tools/netmon.png" "$TOOLS_ROOT/netmon.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon-radio.png" "$TOOLS_ROOT/netmon-radio.png"
copy_file_if_exists "$ROOT_DIR/tools/it_lexikon_linux_hilfe.json" "$TOOLS_ROOT/it_lexikon_linux_hilfe.json"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_banner.png" "$TOOLS_ROOT/netmon_roots_banner.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_splash.png" "$TOOLS_ROOT/netmon_roots_splash.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_startup.png" "$TOOLS_ROOT/netmon_roots_startup.png"
copy_tree_if_exists "$ROOT_DIR/tools/secure_browser_manager" "$TOOLS_ROOT/secure_browser_manager"
rm -rf "$TOOLS_ROOT/secure_browser_manager/tests"
rm -f \
  "$TOOLS_ROOT/secure_browser_manager/README.md" \
  "$TOOLS_ROOT/secure_browser_manager/container_inventory.md" \
  "$APP_PY_ROOT/modules/secure_browser/README.md" \
  "$APP_PY_ROOT/modules/secure_browser/resources/icons/.gitkeep"

# Seed images for log overlay.
copy_tree_if_exists "$ROOT_DIR/tools/Log-Pics" "$ASSETS_ROOT/log-pics"

# Bundled fun assets consumed via fixed system paths.
copy_file "$ROOT_DIR/netmon/features/Code-the-Classics.zip" \
  "$FUN_ASSETS_ROOT/Code-the-Classics.zip"
if (( RELEASE_BUILD )); then
  (
    cd "$FUN_ASSETS_ROOT"
    sha256sum --check "$ROOT_DIR/packaging/fun-assets.sha256"
  )
fi

# Bundled documentation for About dialog and offline reference.
copy_file_if_exists \
  "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.pdf" \
  "$DOCS_ROOT/netmon_dokumentation_${DOCS_VERSION}.pdf"
copy_file_if_exists \
  "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.html" \
  "$DOCS_ROOT/netmon_dokumentation_${DOCS_VERSION}.html"
copy_file_if_exists \
  "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.pdf" \
  "$DOCS_ROOT/netmon_dokumentation.pdf"
copy_file_if_exists \
  "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.html" \
  "$DOCS_ROOT/netmon_dokumentation.html"
copy_file_if_exists "$ROOT_DIR/THIRD_PARTY_NOTICES.md" "$DOCS_ROOT/THIRD_PARTY_NOTICES.md"
copy_file "$ROOT_DIR/packaging/copyright" "$DOCS_ROOT/copyright"
if [[ -f "$DOCS_ROOT/netmon_dokumentation.html" && -f "$DOCS_ROOT/netmon_dokumentation.pdf" ]]; then
  copy_file "$ROOT_DIR/packaging/netmon.doc-base" "$PKG_DIR/usr/share/doc-base/netmon.netmon"
fi
if (( TEST_BUILD )); then
  {
    printf '%s\n\n' "netmon ($PKG_VERSION) unstable; urgency=low"
    printf '  * Isolated DNS integration test build; not an official release.\n'
    printf '  * DHCP/ISP release remains disabled; maintainer scripts do not restore DNS.\n\n'
    printf ' -- %s  %s\n\n' "$MAINTAINER" "$(date -u -R)"
    cat "$ROOT_DIR/packaging/changelog"
  } | gzip -9n > "$DOCS_ROOT/changelog.gz"
  {
    printf '# NetMon V4 DNS TESTBUILD\n\nPaketversion: %s\n\n' "$PKG_VERSION"
    cat "$ROOT_DIR/README-DNS-INTEGRATION.md"
  } > "$DOCS_ROOT/TEST-BUILD.md"
  copy_file "$ROOT_DIR/docs/DNS-F1-F6-REPORT.md" "$DOCS_ROOT/DNS-F1-F6-REPORT.md"
else
  gzip -9n -c "$ROOT_DIR/packaging/changelog" > "$DOCS_ROOT/changelog.gz"
fi
gzip -9n -c "$ROOT_DIR/packaging/netmon.1" > "$MAN_ROOT/netmon.1.gz"

# Remove transient Python caches from copied trees.
find "$APP_ROOT" -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" \) -prune -exec rm -rf {} +
find "$APP_ROOT" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
find "$APP_ROOT" -type d -empty -delete

# Launcher
cat > "$PKG_DIR/usr/bin/netmon" <<'EOF'
#!/bin/sh
set -eu
NETMON_HOME="/usr/lib/netmon"
export PYTHONPATH="$NETMON_HOME${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 -m netmon "$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/netmon"

# Desktop entry
cat > "$PKG_DIR/usr/share/applications/netmon.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=NetMon
Comment=Netzwerk, Security, VPN, Radio und Diagnose in einer GUI
Exec=/usr/bin/netmon
Icon=netmon
Terminal=false
Categories=Network;System;Security;
StartupNotify=true
StartupWMClass=NetMon
Keywords=network;security;firewall;VPN;DNS;diagnostics;
EOF


if (( TEST_BUILD )); then
  sed -i 's/^Name=NetMon$/Name=NetMon V4 DNS Test/' "$PKG_DIR/usr/share/applications/netmon.desktop"
fi

copy_file \
  "$ROOT_DIR/packaging/netmon.metainfo.xml" \
  "$PKG_DIR/usr/share/metainfo/netmon.metainfo.xml"
copy_file \
  "$ROOT_DIR/packaging/netmon.lintian-overrides" \
  "$PKG_DIR/usr/share/lintian/overrides/netmon"

# Icon
if command -v convert >/dev/null 2>&1; then
  convert "$ROOT_DIR/tools/netmon.png" -resize 256x256 \
    "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/netmon.png"
else
  copy_file "$ROOT_DIR/tools/netmon.png" "$PKG_DIR/usr/share/pixmaps/netmon.png"
fi

# Debian control
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: net
Priority: optional
Architecture: ${PKG_ARCH}
Maintainer: ${MAINTAINER}
Depends: ${DEPENDENCIES}
${RELATIONSHIPS}
Description: ${PACKAGE_SUMMARY}
 Die Anwendung bietet Netzwerkdiagnose, DNS- und Firewall-Steuerung,
 Security-Checks, VPN-Slots, Radio-Funktionen und weitere Linux-Werkzeuge
 in einer grafischen Oberflaeche.
EOF

# postinst/prerm minimal
cat > "$PKG_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

# Personal resources are prepared as the user on first launch, using XDG
# Documents. Package hooks must not create an English Documents directory in
# /etc/skel or write into existing home directories.

exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

cat > "$PKG_DIR/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e

# Package removal never restores or reactivates legacy DNS profiles.
case "${1:-}" in
  remove|deconfigure)
    # Preserve the protected receipt. Never remove the recovery helper while
    # an activation/rollback still depends on it. No firewall write is allowed.
    if [ -e /var/lib/netmon/ufw-snapshot/state.json ] || [ -L /var/lib/netmon/ufw-snapshot/state.json ]; then
      if ! /usr/bin/python3 -I -c '
import os, stat, sys
path = "/usr/lib/netmon/netmon/core/ufw_snapshot.py"
current = "/"
for part in [""] + path.strip("/").split("/"):
    current = os.path.join(current, part)
    info = os.lstat(current)
    if info.st_uid != 0 or info.st_mode & 0o022:
        sys.exit("Unprotected removal helper")
    if current == path:
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            sys.exit("Unsafe removal helper")
    elif not stat.S_ISDIR(info.st_mode):
        sys.exit("Unsafe helper directory")
os.execv("/usr/bin/python3", ["/usr/bin/python3", "-I", path, "removal"])
' <<'JSON'
{}
JSON
      then
        echo "NetMon: aktive oder ungeklärte Firewall-Transaktion. Erst ausdrücklich wiederherstellen oder manuell geprüft abschließen; Paket bleibt erhalten." >&2
        exit 1
      fi
    fi
    # Stop only tunnels created by NetMon, using the protected creation receipt
    # and original teardown snapshot. Never infer ownership from a profile name.
    if [ -e /var/lib/netmon/wg-quick-ownership ] || [ -L /var/lib/netmon/wg-quick-ownership ]; then
      echo "NetMon: Trenne nachweislich von NetMon gestartete WireGuard-Verbindungen."
      if ! /usr/bin/python3 -I -c '
import os, stat, sys
path = "/usr/lib/netmon/netmon/core/nm_ownership.py"
current = "/"
for part in [""] + path.strip("/").split("/"):
    current = os.path.join(current, part)
    info = os.lstat(current)
    if info.st_uid != 0 or info.st_mode & 0o022:
        sys.exit("Unprotected VPN removal helper")
    if current == path:
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            sys.exit("Unsafe VPN removal helper")
    elif not stat.S_ISDIR(info.st_mode):
        sys.exit("Unsafe VPN helper directory")
os.execv("/usr/bin/python3", ["/usr/bin/python3", "-I", path, "wg-cleanup"])
'; then
        echo "NetMon: VPN konnte nicht sicher getrennt werden. Deinstallation abgebrochen; Hilfsprogramm und Eigentumsnachweise bleiben erhalten." >&2
        exit 1
      fi
    fi
    ;;
esac
exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# Normalize permissions inherited from the development worktree.
find "$PKG_DIR" -type d -exec chmod 0755 {} +
find "$PKG_DIR" -type f -exec chmod 0644 {} +
chmod 0755 \
  "$PKG_DIR/DEBIAN/postinst" \
  "$PKG_DIR/DEBIAN/prerm" \
  "$PKG_DIR/usr/bin/netmon" \
  "$APP_PY_ROOT/app.py" \
  "$APP_PY_ROOT/core/rkhunter_manager.py" \
  "$TOOLS_ROOT/secure_browser_manager/browser_container_builder.py"
if (( WITH_PROJECTM_ADAPTERS )); then
  chmod 0755 "$APP_PY_ROOT/native/projectm_pcm/build/pcm-renderer" \
    "$APP_PY_ROOT/native/projectm_pcm/build/egl-renderer"
fi

# Debian binary packages conventionally carry checksums for installed files.
(
  cd "$PKG_DIR"
  find . -type f ! -path './DEBIAN/*' -print0 \
    | sort -z \
    | xargs -0 md5sum > DEBIAN/md5sums
)

# Build
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT_DEB"

if (( RELEASE_BUILD )); then
  if ! python3 "$ROOT_DIR/scripts/netmon_release_deb_receipt.py" write "$OUT_DEB" \
    --version "$PKG_VERSION" --commit "$RELEASE_COMMIT"; then
    rm -f -- "$OUT_DEB"
    echo "Release-DEB verworfen: Quellstand hat sich waehrend des Builds geaendert." >&2
    exit 1
  fi
else
  echo "Lokaler Testbuild ohne Release-Beleg; nicht fuer signierte Bundles." >&2
fi

echo "Built: $OUT_DEB"
