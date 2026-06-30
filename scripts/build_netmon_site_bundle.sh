#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_VERSION="1.1.15"
DOCS_VERSION="1.1.15"
CURRENT_AUDIT_HTML="security-audit.html"
CURRENT_AUDIT_VERSIONED_HTML="security-audit-r4.html"
BUILD_DIR="$ROOT_DIR/dist/site-build"
PUBLIC_DIR="$BUILD_DIR/public_html"
DIST_DOCS_DIR="$PUBLIC_DIR/dist/docs"
TOOLS_DIR="$PUBLIC_DIR/tools"
DOCS_DIR="$PUBLIC_DIR/docs"
VERIFY_DIR="$PUBLIC_DIR/verify"
EN_DIR="$PUBLIC_DIR/en"
SCREENSHOTS_DIR="$PUBLIC_DIR/screenshots"
DATA_DIR="$PUBLIC_DIR/data"
SUMS_FILE="$PUBLIC_DIR/dist/SHA256SUMS"
MINISIGN_PUBKEY_TARGET="$VERIFY_DIR/netmonroots.minisign.pub"
MINISIGN_VERIFY_SCRIPT="$VERIFY_DIR/verify_netmon_signature.sh"

maybe_sign_release() {
  if ! command -v minisign >/dev/null 2>&1; then
    echo "Hinweis: minisign nicht gefunden, Signatur wird uebersprungen."
    return 0
  fi

  if [[ -z "${NETMON_MINISIGN_SECRET_KEY:-}" ]]; then
    echo "Hinweis: NETMON_MINISIGN_SECRET_KEY nicht gesetzt, Signatur wird uebersprungen."
    return 0
  fi

  if [[ ! -f "$NETMON_MINISIGN_SECRET_KEY" ]]; then
    echo "Hinweis: Minisign-Secret-Key nicht gefunden: $NETMON_MINISIGN_SECRET_KEY"
    return 0
  fi

  minisign -S -s "$NETMON_MINISIGN_SECRET_KEY" -m "$SUMS_FILE" -x "$PUBLIC_DIR/dist/SHA256SUMS.minisig"

  if [[ -n "${NETMON_MINISIGN_PUBKEY:-}" && -f "${NETMON_MINISIGN_PUBKEY}" ]]; then
    cp "$NETMON_MINISIGN_PUBKEY" "$MINISIGN_PUBKEY_TARGET"
  fi

  echo "Signatur erzeugt: $PUBLIC_DIR/dist/SHA256SUMS.minisig"
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Fehlende Datei: $path" >&2
    exit 1
  fi
}

require_file "$ROOT_DIR/site/index.html"
require_file "$ROOT_DIR/site/latest-version.json"
require_file "$ROOT_DIR/site/aktuelles.html"
require_file "$ROOT_DIR/site/docs.html"
require_file "$ROOT_DIR/site/downloads.html"
require_file "$ROOT_DIR/site/tour.html"
require_file "$ROOT_DIR/site/legal.html"
require_file "$ROOT_DIR/site/impressum.html"
require_file "$ROOT_DIR/site/$CURRENT_AUDIT_HTML"
require_file "$ROOT_DIR/site/$CURRENT_AUDIT_VERSIONED_HTML"
require_file "$ROOT_DIR/site/styles.css"
require_file "$ROOT_DIR/site/app.js"
require_file "$ROOT_DIR/site/download.php"
require_file "$ROOT_DIR/site/download-stats.php"
require_file "$ROOT_DIR/site/download-lib.php"
require_file "$ROOT_DIR/site/download-config.php"
require_file "$ROOT_DIR/site/.htaccess"
require_file "$ROOT_DIR/site/LICENSE.txt"
require_file "$ROOT_DIR/site/THIRD_PARTY_NOTICES.md"
require_file "$ROOT_DIR/site/netmon_security_audit_2026.pdf"
require_file "$ROOT_DIR/site/netmon_security_audit_2026_r4.pdf"
require_file "$ROOT_DIR/site/data/.htaccess"
require_file "$ROOT_DIR/site/data/download-stats.json"
require_file "$ROOT_DIR/site/en/index.html"
require_file "$ROOT_DIR/site/en/updates.html"
require_file "$ROOT_DIR/site/en/docs.html"
require_file "$ROOT_DIR/site/en/downloads.html"
require_file "$ROOT_DIR/site/en/tour.html"
require_file "$ROOT_DIR/site/en/legal.html"
require_file "$ROOT_DIR/site/en/impressum.html"
require_file "$ROOT_DIR/site/en/security-audit.html"
require_file "$ROOT_DIR/site/screenshots/netmon-status-header-tour.png"
require_file "$ROOT_DIR/site/screenshots/netmon-dns-selection-tour.png"
require_file "$ROOT_DIR/site/screenshots/netmon-security-firewall-tour.png"
require_file "$ROOT_DIR/site/screenshots/netmon-roots-baseline-guard-tour.png"
require_file "$ROOT_DIR/site/screenshots/netmon-linux-help-glossary-tour.png"
require_file "$ROOT_DIR/site/screenshots/netmon-download-scan-tour.png"
require_file "$ROOT_DIR/site/screenshots/netmon-radio-projectm-tour.png"
require_file "$ROOT_DIR/site/screenshots/netmon-system-monitor-insight.png"
require_file "$ROOT_DIR/site/screenshots/netmon-clamav-insight.png"
require_file "$ROOT_DIR/site/screenshots/netmon-logs-diagnostics-insight.png"
require_file "$ROOT_DIR/site/screenshots/netmon-theme-studio-insight.png"
require_file "$ROOT_DIR/site/screenshots/netmon-table-details-insight.png"
require_file "$ROOT_DIR/site/screenshots/netmon-guided-actions-insight.png"
require_file "$ROOT_DIR/dist/netmon_${PKG_VERSION}_all.deb"
require_file "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.pdf"
require_file "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.html"
require_file "$ROOT_DIR/tools/Favicon.png"
require_file "$ROOT_DIR/tools/bannericon.png"
require_file "$ROOT_DIR/tools/netmon.png"
require_file "$ROOT_DIR/tools/netmon-radio.png"
require_file "$ROOT_DIR/docs/CHANGELOG.md"
require_file "$ROOT_DIR/scripts/verify_netmon_download.sh"

rm -rf "$BUILD_DIR"
mkdir -p "$DIST_DOCS_DIR" "$TOOLS_DIR" "$DOCS_DIR" "$VERIFY_DIR" "$EN_DIR" "$SCREENSHOTS_DIR" "$DATA_DIR"

cp "$ROOT_DIR/site/index.html" "$PUBLIC_DIR/index.html"
cp "$ROOT_DIR/site/latest-version.json" "$PUBLIC_DIR/latest-version.json"
cp "$ROOT_DIR/site/aktuelles.html" "$PUBLIC_DIR/aktuelles.html"
cp "$ROOT_DIR/site/docs.html" "$PUBLIC_DIR/docs.html"
cp "$ROOT_DIR/site/downloads.html" "$PUBLIC_DIR/downloads.html"
cp "$ROOT_DIR/site/tour.html" "$PUBLIC_DIR/tour.html"
cp "$ROOT_DIR/site/legal.html" "$PUBLIC_DIR/legal.html"
cp "$ROOT_DIR/site/impressum.html" "$PUBLIC_DIR/impressum.html"
cp "$ROOT_DIR/site/$CURRENT_AUDIT_HTML" "$PUBLIC_DIR/$CURRENT_AUDIT_HTML"
cp "$ROOT_DIR/site/$CURRENT_AUDIT_HTML" "$PUBLIC_DIR/$CURRENT_AUDIT_VERSIONED_HTML"
cp "$ROOT_DIR/site/styles.css" "$PUBLIC_DIR/styles.css"
cp "$ROOT_DIR/site/app.js" "$PUBLIC_DIR/app.js"
cp "$ROOT_DIR/site/download.php" "$PUBLIC_DIR/download.php"
cp "$ROOT_DIR/site/download-stats.php" "$PUBLIC_DIR/download-stats.php"
cp "$ROOT_DIR/site/download-lib.php" "$PUBLIC_DIR/download-lib.php"
cp "$ROOT_DIR/site/download-config.php" "$PUBLIC_DIR/download-config.php"
cp "$ROOT_DIR/site/robots.txt" "$PUBLIC_DIR/robots.txt"
cp "$ROOT_DIR/site/sitemap.xml" "$PUBLIC_DIR/sitemap.xml"
convert "$ROOT_DIR/tools/Favicon.png" -resize 256x256 "$PUBLIC_DIR/favicon.png"
cp "$ROOT_DIR/tools/bannericon.png" "$PUBLIC_DIR/bannericon.png"
cp "$ROOT_DIR/site/.htaccess" "$PUBLIC_DIR/.htaccess"
cp "$ROOT_DIR/site/LICENSE.txt" "$PUBLIC_DIR/LICENSE.txt"
cp "$ROOT_DIR/site/THIRD_PARTY_NOTICES.md" "$PUBLIC_DIR/THIRD_PARTY_NOTICES.md"
cp "$ROOT_DIR/site/netmon_security_audit_2026.pdf" "$PUBLIC_DIR/netmon_security_audit_2026.pdf"
cp "$ROOT_DIR/site/netmon_security_audit_2026_r4.pdf" "$PUBLIC_DIR/netmon_security_audit_2026_r4.pdf"
cp "$ROOT_DIR/site/data/.htaccess" "$DATA_DIR/.htaccess"
cp "$ROOT_DIR/site/data/download-stats.json" "$DATA_DIR/download-stats.json"

cp "$ROOT_DIR/site/en/index.html" "$EN_DIR/index.html"
cp "$ROOT_DIR/site/en/updates.html" "$EN_DIR/updates.html"
cp "$ROOT_DIR/site/en/docs.html" "$EN_DIR/docs.html"
cp "$ROOT_DIR/site/en/downloads.html" "$EN_DIR/downloads.html"
cp "$ROOT_DIR/site/en/tour.html" "$EN_DIR/tour.html"
cp "$ROOT_DIR/site/en/legal.html" "$EN_DIR/legal.html"
cp "$ROOT_DIR/site/en/impressum.html" "$EN_DIR/impressum.html"
cp "$ROOT_DIR/site/en/security-audit.html" "$EN_DIR/security-audit.html"

for screenshot in \
  netmon-status-header-tour.png \
  netmon-dns-selection-tour.png \
  netmon-security-firewall-tour.png \
  netmon-roots-baseline-guard-tour.png \
  netmon-linux-help-glossary-tour.png \
  netmon-download-scan-tour.png \
  netmon-radio-projectm-tour.png \
  netmon-system-monitor-insight.png \
  netmon-clamav-insight.png \
  netmon-logs-diagnostics-insight.png \
  netmon-theme-studio-insight.png \
  netmon-table-details-insight.png \
  netmon-guided-actions-insight.png
do
  cp "$ROOT_DIR/site/screenshots/$screenshot" "$SCREENSHOTS_DIR/"
done

cp "$ROOT_DIR/dist/netmon_${PKG_VERSION}_all.deb" "$PUBLIC_DIR/dist/"
cp "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.pdf" "$DIST_DOCS_DIR/"
cp "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.html" "$DIST_DOCS_DIR/"

cp "$ROOT_DIR/tools/netmon.png" "$TOOLS_DIR/"
cp "$ROOT_DIR/tools/netmon-radio.png" "$TOOLS_DIR/"
cp "$ROOT_DIR/docs/CHANGELOG.md" "$DOCS_DIR/"
cp "$ROOT_DIR/scripts/verify_netmon_download.sh" "$VERIFY_DIR/"
cp "$ROOT_DIR/scripts/verify_netmon_signature.sh" "$MINISIGN_VERIFY_SCRIPT"

(
  cd "$PUBLIC_DIR/dist"
  sha256sum \
    netmon_${PKG_VERSION}_all.deb \
    docs/netmon_dokumentation_${DOCS_VERSION}.pdf \
    docs/netmon_dokumentation_${DOCS_VERSION}.html \
    > "$SUMS_FILE"
)

maybe_sign_release

(
  cd "$BUILD_DIR"
  zip -rq netmonroots_public_html.zip public_html
)

echo "Fertig:"
echo "  Ordner: $PUBLIC_DIR"
echo "  ZIP:    $BUILD_DIR/netmonroots_public_html.zip"
