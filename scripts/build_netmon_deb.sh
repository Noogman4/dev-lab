#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PKG_NAME="netmon"
PKG_VERSION="$(python3 "$ROOT_DIR/scripts/read_netmon_version.py")"
DOCS_VERSION="$PKG_VERSION"
PKG_ARCH="all"
MAINTAINER="Mr. Happy <netmon.proglab@protonmail.ch>"

BUILD_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/netmon-debbuild.XXXXXX")"
PKG_DIR="$BUILD_ROOT/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}"
OUT_DEB="$ROOT_DIR/dist/${PKG_NAME}_${PKG_VERSION}_${PKG_ARCH}.deb"
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
copy_file "$ROOT_DIR/packaging/netmon.doc-base" "$PKG_DIR/usr/share/doc-base/netmon.netmon"
gzip -9n -c "$ROOT_DIR/packaging/changelog" > "$DOCS_ROOT/changelog.gz"
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
Depends: python3, python3-tk, python3-psutil, python3-pil, python3-pil.imagetk, udisks2, cryptsetup
Recommends: network-manager, systemd-resolved, dnsutils, wireguard-tools, ufw, traceroute, mtr, nmap, iproute2, iftop, htop, lynis, rkhunter, clamav, clamav-freshclam, speedtest-cli, mpv, whois
Suggests: wireshark, tshark, projectm, projectm-pulseaudio, python3-pypdf2, python3-docx, python3-pygame, python3-pgzero
Description: Linux-Netzwerkmonitor mit Security-, VPN- und Radio-Funktionen
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

NETMON_STATE_DIR="/var/lib/netmon"
NETMON_INSTALL_DNS_STATE="$NETMON_STATE_DIR/install-dns-nm.state"
ASSET_DIR="/usr/share/netmon/assets/log-pics"

restore_legacy_install_dns() {
  [ -f "$NETMON_INSTALL_DNS_STATE" ] || return 0
  if ! command -v nmcli >/dev/null 2>&1; then
    echo "NetMon: DNS recovery requires nmcli; retained $NETMON_INSTALL_DNS_STATE." >&2
    return 1
  fi

  /usr/bin/python3 -I - "$NETMON_STATE_DIR" <<'PYDNS'
import fcntl
import os
import stat
import subprocess
import sys
import uuid


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def restore(directory):
    name = "install-dns-nm.state"
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        # All cooperating readers/writers must lock this stable directory inode.
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        try:
            state_fd = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
            )
        except FileNotFoundError:
            return 0  # Another cooperating invocation already finished.
        with os.fdopen(state_fd, "rb") as state:
            initial = os.fstat(state.fileno())
            if not stat.S_ISREG(initial.st_mode):
                raise ValueError("recovery state is not a regular file")
            data = state.read()
            if signature(os.fstat(state.fileno())) != signature(initial):
                raise ValueError("recovery state changed while reading")
            text = data.decode("utf-8")
            if "\0" in text or "\r" in text:
                raise ValueError("unexpected NUL or CR in legacy state")
            records = text.split("\n") if text else []
            if records and records[-1] == "":
                records.pop()
            rows = []
            seen = set()
            for number, record in enumerate(records, 1):
                fields = record.split("|")
                if len(fields) != 3:
                    raise ValueError(f"line {number}: expected UUID|DNS|IGNORE")
                identity = str(uuid.UUID(fields[0]))
                if fields[0].lower() != identity:
                    raise ValueError(f"line {number}: expected a complete UUID")
                if identity in seen:
                    raise ValueError(f"line {number}: duplicate UUID {identity}")
                seen.add(identity)
                rows.append((identity, fields[1], fields[2] or "no"))

            failed = False
            for identity, dns, ignore in rows:
                if subprocess.run(
                    ["nmcli", "connection", "show", "uuid", identity],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                ).returncode:
                    print(
                        f"NetMon: DNS restore failed: unavailable UUID {identity}.",
                        file=sys.stderr,
                    )
                    failed = True
                    continue
                if subprocess.run(
                    [
                        "nmcli",
                        "connection",
                        "modify",
                        "uuid",
                        identity,
                        "ipv4.dns",
                        dns,
                        "ipv4.ignore-auto-dns",
                        ignore,
                    ],
                    check=False,
                ).returncode:
                    print(
                        f"NetMon: DNS restore failed: cannot modify UUID {identity}.",
                        file=sys.stderr,
                    )
                    failed = True
                    continue
                if subprocess.run(
                    ["nmcli", "connection", "up", "uuid", identity], check=False
                ).returncode:
                    print(
                        f"NetMon: DNS restore failed: cannot activate UUID {identity}.",
                        file=sys.stderr,
                    )
                    failed = True
            if failed:
                raise ValueError("restoration incomplete")

            # Recheck both the opened snapshot and the current directory entry.
            # This is NOT atomic against root writers ignoring the directory lock.
            state.seek(0)
            if (
                state.read() != data
                or signature(os.fstat(state.fileno())) != signature(initial)
                or signature(os.stat(name, dir_fd=directory_fd, follow_symlinks=False))
                != signature(initial)
            ):
                raise ValueError(
                    "recovery state changed; current file must be retained"
                )
            os.unlink(name, dir_fd=directory_fd)
            return 0
    finally:
        os.close(directory_fd)


try:
    status = restore(sys.argv[1])
except (OSError, ValueError) as error:
    print(
        f"NetMon: DNS recovery failed for {sys.argv[1]}/install-dns-nm.state: {error}; "
        "check the retained state; earlier successful changes may remain.",
        file=sys.stderr,
    )
    status = 1
sys.exit(status)
PYDNS
  # Keep the directory inode as the shared lock anchor.
}

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
restore_legacy_install_dns

exit 0
EOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

cat > "$PKG_DIR/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e

NETMON_STATE_DIR="/var/lib/netmon"
NETMON_INSTALL_DNS_STATE="$NETMON_STATE_DIR/install-dns-nm.state"

restore_netmon_install_dns() {
  [ "${1:-}" = "remove" ] || [ "${1:-}" = "deconfigure" ] || return 0
  [ -f "$NETMON_INSTALL_DNS_STATE" ] || return 0
  if ! command -v nmcli >/dev/null 2>&1; then
    echo "NetMon: DNS recovery requires nmcli; retained $NETMON_INSTALL_DNS_STATE." >&2
    return 1
  fi

  /usr/bin/python3 -I - "$NETMON_STATE_DIR" <<'PYDNS'
import fcntl
import os
import stat
import subprocess
import sys
import uuid


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def restore(directory):
    name = "install-dns-nm.state"
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        # All cooperating readers/writers must lock this stable directory inode.
        fcntl.flock(directory_fd, fcntl.LOCK_EX)
        try:
            state_fd = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
            )
        except FileNotFoundError:
            return 0  # Another cooperating invocation already finished.
        with os.fdopen(state_fd, "rb") as state:
            initial = os.fstat(state.fileno())
            if not stat.S_ISREG(initial.st_mode):
                raise ValueError("recovery state is not a regular file")
            data = state.read()
            if signature(os.fstat(state.fileno())) != signature(initial):
                raise ValueError("recovery state changed while reading")
            text = data.decode("utf-8")
            if "\0" in text or "\r" in text:
                raise ValueError("unexpected NUL or CR in legacy state")
            records = text.split("\n") if text else []
            if records and records[-1] == "":
                records.pop()
            rows = []
            seen = set()
            for number, record in enumerate(records, 1):
                fields = record.split("|")
                if len(fields) != 3:
                    raise ValueError(f"line {number}: expected UUID|DNS|IGNORE")
                identity = str(uuid.UUID(fields[0]))
                if fields[0].lower() != identity:
                    raise ValueError(f"line {number}: expected a complete UUID")
                if identity in seen:
                    raise ValueError(f"line {number}: duplicate UUID {identity}")
                seen.add(identity)
                rows.append((identity, fields[1], fields[2] or "no"))

            failed = False
            for identity, dns, ignore in rows:
                if subprocess.run(
                    ["nmcli", "connection", "show", "uuid", identity],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                ).returncode:
                    print(
                        f"NetMon: DNS restore failed: unavailable UUID {identity}.",
                        file=sys.stderr,
                    )
                    failed = True
                    continue
                if subprocess.run(
                    [
                        "nmcli",
                        "connection",
                        "modify",
                        "uuid",
                        identity,
                        "ipv4.dns",
                        dns,
                        "ipv4.ignore-auto-dns",
                        ignore,
                    ],
                    check=False,
                ).returncode:
                    print(
                        f"NetMon: DNS restore failed: cannot modify UUID {identity}.",
                        file=sys.stderr,
                    )
                    failed = True
                    continue
                if subprocess.run(
                    ["nmcli", "connection", "up", "uuid", identity], check=False
                ).returncode:
                    print(
                        f"NetMon: DNS restore failed: cannot activate UUID {identity}.",
                        file=sys.stderr,
                    )
                    failed = True
            if failed:
                raise ValueError("restoration incomplete")

            # Recheck both the opened snapshot and the current directory entry.
            # This is NOT atomic against root writers ignoring the directory lock.
            state.seek(0)
            if (
                state.read() != data
                or signature(os.fstat(state.fileno())) != signature(initial)
                or signature(os.stat(name, dir_fd=directory_fd, follow_symlinks=False))
                != signature(initial)
            ):
                raise ValueError(
                    "recovery state changed; current file must be retained"
                )
            os.unlink(name, dir_fd=directory_fd)
            return 0
    finally:
        os.close(directory_fd)


try:
    status = restore(sys.argv[1])
except (OSError, ValueError) as error:
    print(
        f"NetMon: DNS recovery failed for {sys.argv[1]}/install-dns-nm.state: {error}; "
        "check the retained state; earlier successful changes may remain.",
        file=sys.stderr,
    )
    status = 1
sys.exit(status)
PYDNS
  # Keep the directory inode as the shared lock anchor.
}

restore_netmon_install_dns "${1:-}"
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
rm -f "$OUT_DEB"
dpkg-deb --root-owner-group --build "$PKG_DIR" "$OUT_DEB"

echo "Built: $OUT_DEB"
