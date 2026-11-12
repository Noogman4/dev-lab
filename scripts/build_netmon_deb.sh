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
FEATURE_TOOLS="network-manager, systemd-resolved, dnsutils, wireguard-tools, ufw, traceroute, mtr, nmap, iproute2, iftop, htop, lynis, rkhunter, clamav, clamav-freshclam, speedtest-cli, mpv, pipewire-bin, whois, python3-keyring, python3-gi, gir1.2-vte-2.91"
EXTRA_TOOLS="wireshark, tshark, projectm, projectm-pulseaudio, python3-pypdf2, python3-docx, python3-openpyxl, python3-pygame, python3-pgzero, sudo, gnome-keyring"
DEPENDENCIES="$PYTHON_DEPENDS, udisks2, cryptsetup"
RELATIONSHIPS="Recommends: $FEATURE_TOOLS
Suggests: $EXTRA_TOOLS"
RELEASE_BUILD=0
RELEASE_COMMIT=""
if [[ $# == 1 && "$1" == "--release" ]]; then
  # Official lane: only a clean, committed package source gets a receipt that
  # the signed production bundles accept. Plain local builds never get one.
  RELEASE_BUILD=1
  RELEASE_COMMIT="$(python3 "$ROOT_DIR/scripts/netmon_release_deb_receipt.py" preflight)"
  shift
fi
if (( $# )); then
  if [[ "$1" == "--help" && $# == 1 ]]; then
    echo "Usage: $0 [--release | --test-version ${DOCS_VERSION}~v4dnstestYYYYMMDD.N]"
    echo "  --release  official build from a clean commit, with release receipt"
    echo "  (none)     local test build; never accepted by signed release bundles"
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
  DEPENDENCIES="$PYTHON_DEPENDS"
  RELATIONSHIPS="Suggests: $FEATURE_TOOLS, $EXTRA_TOOLS, udisks2, cryptsetup"
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
copy_file_if_exists "$ROOT_DIR/netmon_radio_app.py" "$APP_ROOT/netmon_radio_app.py"

copy_tree "$ROOT_DIR/netmon/config" "$APP_PY_ROOT/config"
copy_tree "$ROOT_DIR/netmon/core" "$APP_PY_ROOT/core"
copy_tree "$ROOT_DIR/netmon/features" "$APP_PY_ROOT/features"
rm -f "$APP_PY_ROOT/features/Code-the-Classics.zip"
copy_tree "$ROOT_DIR/netmon/lang" "$APP_PY_ROOT/lang"
copy_tree "$ROOT_DIR/netmon/modules" "$APP_PY_ROOT/modules"
copy_tree "$ROOT_DIR/netmon/services" "$APP_PY_ROOT/services"
copy_tree "$ROOT_DIR/netmon/ui" "$APP_PY_ROOT/ui"

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
gzip -9n -c "$ROOT_DIR/packaging/netmon-uninstall.1" > "$MAN_ROOT/netmon-uninstall.1.gz"

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
install -m 0755 "$ROOT_DIR/scripts/netmon_uninstall_menu.sh" "$PKG_DIR/usr/bin/netmon-uninstall"

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

cat > "$PKG_DIR/usr/share/applications/netmon-uninstall.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=NetMon entfernen
Comment=NetMon deinstallieren und Reste bereinigen
Exec=/usr/bin/netmon-uninstall
Icon=netmon
Terminal=true
Categories=System;Settings;
StartupNotify=true
Keywords=uninstall;remove;NetMon;
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

ASSET_DIR="/usr/share/netmon/assets/log-pics"

# Legacy DNS state is deliberately left untouched by package hooks.

seed_log_pics_dir() {
  TARGET_DIR="$1"
  [ -n "$TARGET_DIR" ] || return 0
  mkdir -p "$TARGET_DIR" >/dev/null 2>&1 || return 0
  if [ -d "$ASSET_DIR" ]; then
    find "$ASSET_DIR" -maxdepth 1 -type f \
      \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | while IFS= read -r SRC; do
      BASENAME="$(basename "$SRC")"
      if [ ! -e "$TARGET_DIR/$BASENAME" ]; then
        cp "$SRC" "$TARGET_DIR/$BASENAME" >/dev/null 2>&1 || true
      fi
    done
  fi
}

documents_root_for_home() {
  HOME_DIR="$1"
  [ -n "$HOME_DIR" ] || return 1
  if [ -d "$HOME_DIR/Documents" ]; then
    printf '%s\n' "$HOME_DIR/Documents"
    return 0
  fi
  if [ -d "$HOME_DIR/Dokumente" ]; then
    printf '%s\n' "$HOME_DIR/Dokumente"
    return 0
  fi
  printf '%s\n' "$HOME_DIR/Documents"
}

seed_netmon_log_pics_for_home() {
  HOME_DIR="$1"
  DOC_ROOT="$(documents_root_for_home "$HOME_DIR")"
  [ -n "$DOC_ROOT" ] || return 0
  seed_log_pics_dir "$DOC_ROOT/NetMon/Log-Pics"
}

seed_netmon_log_pics_for_home "/etc/skel"

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
  "$PKG_DIR/usr/bin/netmon-uninstall" \
  "$APP_PY_ROOT/app.py" \
  "$APP_PY_ROOT/core/rkhunter_manager.py" \
  "$TOOLS_ROOT/secure_browser_manager/browser_container_builder.py"

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
