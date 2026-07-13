#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PKG_NAME="netmon-test"
PKG_VERSION="0"
PKG_ARCH="all"
MAINTAINER="Mr. Happy <netmon.proglab@protonmail.ch>"

BUILD_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/netmon-test-debbuild.XXXXXX")"
PKG_DIR="$BUILD_ROOT/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"
OUT_DEB="$ROOT_DIR/dist/Test.deb"
APP_ROOT="$PKG_DIR/usr/lib/netmon"
APP_PY_ROOT="$APP_ROOT/netmon"
TOOLS_ROOT="$APP_ROOT/tools"
ASSETS_ROOT="$PKG_DIR/usr/share/netmon/assets"
FUN_ASSETS_ROOT="$ASSETS_ROOT/fun"

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
  "$PKG_DIR/usr/bin" \
  "$PKG_DIR/usr/share/applications" \
  "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

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
copy_tree "$ROOT_DIR/netmon/lang" "$APP_PY_ROOT/lang"
copy_tree "$ROOT_DIR/netmon/modules" "$APP_PY_ROOT/modules"
copy_tree "$ROOT_DIR/netmon/services" "$APP_PY_ROOT/services"
copy_tree "$ROOT_DIR/netmon/ui" "$APP_PY_ROOT/ui"

copy_file "$ROOT_DIR/tools/netmon.png" "$TOOLS_ROOT/netmon.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon-radio.png" "$TOOLS_ROOT/netmon-radio.png"
copy_file_if_exists "$ROOT_DIR/tools/it_lexikon_linux_hilfe.json" "$TOOLS_ROOT/it_lexikon_linux_hilfe.json"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_banner.png" "$TOOLS_ROOT/netmon_roots_banner.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_splash.png" "$TOOLS_ROOT/netmon_roots_splash.png"
copy_tree_if_exists "$ROOT_DIR/tools/secure_browser_manager" "$TOOLS_ROOT/secure_browser_manager"
rm -rf "$TOOLS_ROOT/secure_browser_manager/tests"
rm -f \
  "$TOOLS_ROOT/secure_browser_manager/README.md" \
  "$TOOLS_ROOT/secure_browser_manager/container_inventory.md" \
  "$APP_PY_ROOT/modules/secure_browser/README.md" \
  "$APP_PY_ROOT/modules/secure_browser/resources/icons/.gitkeep"

copy_tree_if_exists "$ROOT_DIR/tools/Log-Pics" "$ASSETS_ROOT/log-pics"
copy_file_if_exists "$ROOT_DIR/netmon/features/Code-the-Classics.zip" \
  "$FUN_ASSETS_ROOT/Code-the-Classics.zip"

find "$APP_ROOT" -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" \) -prune -exec rm -rf {} +
find "$APP_ROOT" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
find "$APP_ROOT" -type d -empty -delete

cat > "$PKG_DIR/usr/bin/netmon" <<'EOF'
#!/bin/sh
set -eu
NETMON_HOME="/usr/lib/netmon"
export PYTHONPATH="$NETMON_HOME${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 -m netmon "$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/netmon"

cat > "$PKG_DIR/usr/share/applications/netmon.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=NetMon Test
Comment=NetMon Test Build
Exec=/usr/bin/netmon
Icon=netmon
Terminal=false
Categories=Network;System;Security;
StartupNotify=true
StartupWMClass=NetMon
EOF

if command -v convert >/dev/null 2>&1; then
  convert "$ROOT_DIR/tools/netmon.png" -resize 256x256 \
    "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/netmon.png"
else
  copy_file "$ROOT_DIR/tools/netmon.png" "$PKG_DIR/usr/share/pixmaps/netmon.png"
fi

cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: net
Priority: optional
Architecture: ${PKG_ARCH}
Maintainer: ${MAINTAINER}
Depends: python3, python3-tk, python3-psutil, python3-pil, python3-pil.imagetk, udisks2, cryptsetup
Recommends: network-manager, systemd-resolved, dnsutils, wireguard-tools, ufw, traceroute, mtr, nmap, iproute2, iftop, htop, lynis, rkhunter, clamav, clamav-freshclam, speedtest-cli, mpv, whois
Description: NetMon Test Build
 Minimales Testpaket ohne zusaetzliche Dokumentation.
EOF

cat > "$PKG_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

cat > "$PKG_DIR/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

find "$PKG_DIR" -type d -exec chmod 0755 {} +
find "$PKG_DIR" -type f -exec chmod 0644 {} +
chmod 0755 "$PKG_DIR/DEBIAN/postinst" "$PKG_DIR/DEBIAN/prerm" "$PKG_DIR/usr/bin/netmon"

(
  cd "$PKG_DIR"
  find . -type f ! -path './DEBIAN/*' -print0 \
    | sort -z \
    | xargs -0 md5sum > DEBIAN/md5sums
)

rm -f "$OUT_DEB"
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT_DEB"

echo "Built: $OUT_DEB"
