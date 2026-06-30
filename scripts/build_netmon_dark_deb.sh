#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PKG_NAME="netmon-dark"
PKG_FILE_STEM="netmon_dark"
PKG_VERSION="1.1.2"
PKG_ARCH="all"
MAINTAINER="Mr. Happy <netmon.proglab@protonmail.ch>"

BUILD_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/netmon-dark-debbuild.XXXXXX")"
PKG_DIR="$BUILD_ROOT/${PKG_FILE_STEM}_${PKG_VERSION}_${PKG_ARCH}"
OUT_DEB="$ROOT_DIR/dist/${PKG_FILE_STEM}_${PKG_VERSION}_${PKG_ARCH}.deb"

cleanup() {
  rm -rf "$BUILD_ROOT"
}

trap cleanup EXIT

mkdir -p "$ROOT_DIR/dist"
mkdir -p \
  "$PKG_DIR/DEBIAN" \
  "$PKG_DIR/opt/netmon-dark/netmon/modules" \
  "$PKG_DIR/opt/netmon-dark/assets/log-pics" \
  "$PKG_DIR/usr/bin" \
  "$PKG_DIR/usr/share/applications" \
  "$PKG_DIR/usr/share/icons/hicolor/256x256/apps"

# App code (separate install root, same package module layout)
cp "$ROOT_DIR/netmon/__init__.py" "$PKG_DIR/opt/netmon-dark/netmon/__init__.py"
cp "$ROOT_DIR/netmon/__main__.py" "$PKG_DIR/opt/netmon-dark/netmon/__main__.py"
cp "$ROOT_DIR/netmon/app.py" "$PKG_DIR/opt/netmon-dark/netmon/app.py"
cp "$ROOT_DIR/netmon/dark_test.py" "$PKG_DIR/opt/netmon-dark/netmon/dark_test.py"
cp "$ROOT_DIR/netmon/netmon_ops.py" "$PKG_DIR/opt/netmon-dark/netmon/netmon_ops.py"
cp "$ROOT_DIR/netmon/netmon_network_service.py" "$PKG_DIR/opt/netmon-dark/netmon/netmon_network_service.py"
cp "$ROOT_DIR/netmon/netmon_state_coordinator.py" "$PKG_DIR/opt/netmon-dark/netmon/netmon_state_coordinator.py"
cp "$ROOT_DIR/netmon/netmon_security_parser.py" "$PKG_DIR/opt/netmon-dark/netmon/netmon_security_parser.py"
cp "$ROOT_DIR/netmon/netmon_security_store.py" "$PKG_DIR/opt/netmon-dark/netmon/netmon_security_store.py"
cp "$ROOT_DIR/netmon/modules/__init__.py" "$PKG_DIR/opt/netmon-dark/netmon/modules/__init__.py"
cp "$ROOT_DIR/netmon/modules/port_analysis.py" "$PKG_DIR/opt/netmon-dark/netmon/modules/port_analysis.py"
cp "$ROOT_DIR/netmon/modules/speedtest.py" "$PKG_DIR/opt/netmon-dark/netmon/modules/speedtest.py"

# Optional seed images for Log overlay
if [ -d "$ROOT_DIR/tools/Log-Pics" ]; then
  find "$ROOT_DIR/tools/Log-Pics" -maxdepth 1 -type f -print0 | while IFS= read -r -d '' SRC; do
    case "$SRC" in
      *.png|*.PNG|*.jpg|*.JPG|*.jpeg|*.JPEG)
        cp "$SRC" "$PKG_DIR/opt/netmon-dark/assets/log-pics/" || true
        ;;
    esac
  done
fi

# Launcher (dark test)
cat > "$PKG_DIR/usr/bin/netmon-dark" <<'LAUNCHER'
#!/bin/sh
set -eu
NETMON_HOME="/opt/netmon-dark"
export PYTHONPATH="$NETMON_HOME${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 -m netmon.dark_test "$@"
LAUNCHER
chmod 755 "$PKG_DIR/usr/bin/netmon-dark"

# Desktop entry
cat > "$PKG_DIR/usr/share/applications/netmon-dark.desktop" <<'DESKTOP'
[Desktop Entry]
Version=1.0
Type=Application
Name=NetMon Dark (Test)
Comment=NetMon Darkmode Testversion
Exec=/usr/bin/netmon-dark
Icon=netmon-dark
Terminal=false
Categories=Network;System;Security;
StartupNotify=true
StartupWMClass=NetMon
DESKTOP

# Icon
cp "$ROOT_DIR/tools/netmon.png" "$PKG_DIR/usr/share/icons/hicolor/256x256/apps/netmon-dark.png"

# Debian control
cat > "$PKG_DIR/DEBIAN/control" <<CONTROL
Package: ${PKG_NAME}
Version: ${PKG_VERSION}
Section: net
Priority: optional
Architecture: ${PKG_ARCH}
Maintainer: ${MAINTAINER}
Depends: python3, python3-tk, python3-psutil, python3-pil, python3-pil.imagetk, speedtest-cli
Recommends: ufw, wireguard-tools, nmap, traceroute, mtr-tiny, iftop, htop, clamav, clamav-freshclam, curl, dnsutils, whois
Description: NetMon Darkmode Testversion
 Separate Testversion von NetMon mit umschaltbarem Dark/Light UI,
 ohne Eingriff in die stabile Hauptversion.
CONTROL

# postinst/prerm minimal
cat > "$PKG_DIR/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi

ASSET_DIR="/opt/netmon-dark/assets/log-pics"
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
POSTINST
chmod 755 "$PKG_DIR/DEBIAN/postinst"

cat > "$PKG_DIR/DEBIAN/prerm" <<'PRERM'
#!/bin/sh
set -e
# Keine Userdaten entfernen.
exit 0
PRERM
chmod 755 "$PKG_DIR/DEBIAN/prerm"

# Build
rm -f "$OUT_DEB"
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT_DEB"

echo "Built: $OUT_DEB"
