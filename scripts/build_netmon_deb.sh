#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PKG_NAME="netmon"
PKG_VERSION="1.1.17"
DOCS_VERSION="1.1.17"
PKG_ARCH="all"
MAINTAINER="Mr. Happy <netmon.proglab@protonmail.ch>"

BUILD_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/netmon-debbuild.XXXXXX")"
PKG_DIR="$BUILD_ROOT/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"
OUT_DEB="$ROOT_DIR/dist/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
APP_ROOT="$PKG_DIR/opt/netmon"
APP_PY_ROOT="$APP_ROOT/netmon"
TOOLS_ROOT="$APP_ROOT/tools"
DOCS_ROOT="$PKG_DIR/usr/share/netmon/docs"

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
  "$APP_ROOT/assets/log-pics" \
  "$TOOLS_ROOT" \
  "$DOCS_ROOT" \
  "$PKG_DIR/usr/bin" \
  "$PKG_DIR/usr/share/applications" \
  "$PKG_DIR/usr/share/metainfo" \
  "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

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
copy_tree "$ROOT_DIR/netmon/lang" "$APP_PY_ROOT/lang"
copy_tree "$ROOT_DIR/netmon/modules" "$APP_PY_ROOT/modules"
copy_tree "$ROOT_DIR/netmon/services" "$APP_PY_ROOT/services"
copy_tree "$ROOT_DIR/netmon/ui" "$APP_PY_ROOT/ui"

# Runtime tool assets referenced by the application via repo-relative paths.
copy_file "$ROOT_DIR/tools/netmon.png" "$TOOLS_ROOT/netmon.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon-radio.png" "$TOOLS_ROOT/netmon-radio.png"
copy_file_if_exists "$ROOT_DIR/tools/it_lexikon_linux_hilfe.json" "$TOOLS_ROOT/it_lexikon_linux_hilfe.json"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_banner.png" "$TOOLS_ROOT/netmon_roots_banner.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_splash.png" "$TOOLS_ROOT/netmon_roots_splash.png"
copy_file_if_exists "$ROOT_DIR/tools/netmon_roots_startup.png" "$TOOLS_ROOT/netmon_roots_startup.png"
copy_tree_if_exists "$ROOT_DIR/tools/secure_browser_manager" "$TOOLS_ROOT/secure_browser_manager"

# Seed images for log overlay.
copy_tree_if_exists "$ROOT_DIR/tools/Log-Pics" "$APP_ROOT/assets/log-pics"

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
copy_file_if_exists "$ROOT_DIR/LICENSE" "$DOCS_ROOT/LICENSE"
copy_file_if_exists "$ROOT_DIR/THIRD_PARTY_NOTICES.md" "$DOCS_ROOT/THIRD_PARTY_NOTICES.md"
copy_file_if_exists \
  "$ROOT_DIR/CODE_THE_CLASSICS_LICENSE.txt" \
  "$DOCS_ROOT/CODE_THE_CLASSICS_LICENSE.txt"

# Remove transient Python caches from copied trees.
find "$APP_ROOT" -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" \) -prune -exec rm -rf {} +
find "$APP_ROOT" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

# Launcher
cat > "$PKG_DIR/usr/bin/netmon" <<'EOF'
#!/bin/sh
set -eu
NETMON_HOME="/opt/netmon"
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
EOF

copy_file \
  "$ROOT_DIR/packaging/netmon.metainfo.xml" \
  "$PKG_DIR/usr/share/metainfo/netmon.metainfo.xml"

# Icon
copy_file "$ROOT_DIR/tools/netmon.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/netmon.png"

# Debian control
cat > "$PKG_DIR/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: net
Priority: optional
Architecture: ${PKG_ARCH}
Maintainer: ${MAINTAINER}
Depends: python3, python3-tk, python3-psutil, python3-pil, python3-pil.imagetk, udisks2, cryptsetup
Recommends: network-manager, systemd-resolved, dnsutils, wireguard-tools, ufw, traceroute, mtr, nmap, iproute2, iftop, htop, lynis, rkhunter, clamav, clamav-freshclam, speedtest-cli, mpv, whois
Suggests: wireshark, tshark, projectm, projectm-pulseaudio, python3-pypdf2, python3-docx, python3-pygame, python3-pgzero
Description: NetMon - Linux Netzwerkmonitor mit Security-, VPN- und Radio-Funktionen
 NetMon bietet Netzwerkdiagnose, DNS- und Firewall-Steuerung, Security-Checks,
 VPN-Slots, Radio-Funktionen, projectM-Preset-Manager fuer externe Packs und weitere Linux-Werkzeuge
 in einer GUI.
EOF

# postinst/prerm minimal
cat > "$PKG_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

ASSET_DIR="/opt/netmon/assets/log-pics"

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

seed_log_pics_dir "/etc/skel/Bilder/Log-Pics"
seed_log_pics_dir "/etc/skel/Pictures/Log-Pics"

if [ -n "${SUDO_USER:-}" ] && [ "${SUDO_USER}" != "root" ]; then
  USER_HOME="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
  if [ -n "$USER_HOME" ] && [ -d "$USER_HOME" ]; then
    seed_log_pics_dir "$USER_HOME/Bilder/Log-Pics"
    seed_log_pics_dir "$USER_HOME/Pictures/Log-Pics"
    chown "$SUDO_USER":"$SUDO_USER" "$USER_HOME/Bilder" "$USER_HOME/Bilder/Log-Pics" >/dev/null 2>&1 || true
    chown "$SUDO_USER":"$SUDO_USER" "$USER_HOME/Pictures" "$USER_HOME/Pictures/Log-Pics" >/dev/null 2>&1 || true
    chown "$SUDO_USER":"$SUDO_USER" "$USER_HOME/Bilder/Log-Pics"/* >/dev/null 2>&1 || true
    chown "$SUDO_USER":"$SUDO_USER" "$USER_HOME/Pictures/Log-Pics"/* >/dev/null 2>&1 || true
  fi
fi

exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

cat > "$PKG_DIR/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
# Keine Userdaten entfernen.
exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# Build
rm -f "$OUT_DEB"
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT_DEB"

echo "Built: $OUT_DEB"
