#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_VERSION="$(python3 "$ROOT_DIR/scripts/read_netmon_version.py")"
DOCS_VERSION="$PKG_VERSION"
BUILD_DIR="$ROOT_DIR/dist/site-release-update"
PUBLIC_DIR="$BUILD_DIR/public_html"
DIST_DIR="$PUBLIC_DIR/dist"
DIST_DOCS_DIR="$DIST_DIR/docs"
VERIFY_DIR="$PUBLIC_DIR/verify"
EN_DIR="$PUBLIC_DIR/en"
SUMS_FILE="$DIST_DIR/SHA256SUMS"
MINISIGN_PUBKEY_TARGET="$VERIFY_DIR/netmonroots.minisign.pub"
MINISIGN_VERIFY_SCRIPT="$VERIFY_DIR/verify_netmon_signature.sh"
PINNED_MINISIGN_PUBKEY="$ROOT_DIR/docs/security/netmonroots.minisign.pub"
RELEASE_MINISIGN_PUBKEY="${NETMON_MINISIGN_PUBKEY:-$PINNED_MINISIGN_PUBKEY}"

sign_release() {
  if [[ "${NETMON_ALLOW_UNSIGNED_BUILD:-0}" == "1" ]]; then
    cp "$PINNED_MINISIGN_PUBKEY" "$MINISIGN_PUBKEY_TARGET"
    echo "WARNUNG: Explizit angeforderter unsignierter Test-Build." >&2
    return 0
  fi

  if ! command -v minisign >/dev/null 2>&1; then
    echo "Release-Abbruch: minisign ist nicht installiert." >&2
    exit 1
  fi

  if [[ -z "${NETMON_MINISIGN_SECRET_KEY:-}" ]]; then
    echo "Release-Abbruch: NETMON_MINISIGN_SECRET_KEY ist nicht gesetzt." >&2
    exit 1
  fi

  if [[ ! -f "$NETMON_MINISIGN_SECRET_KEY" ]]; then
    echo "Release-Abbruch: Minisign-Secret-Key nicht gefunden: $NETMON_MINISIGN_SECRET_KEY" >&2
    exit 1
  fi

  if [[ ! -f "$RELEASE_MINISIGN_PUBKEY" ]]; then
    echo "Release-Abbruch: Minisign-Public-Key fehlt: $RELEASE_MINISIGN_PUBKEY" >&2
    exit 1
  fi

  if ! cmp -s "$RELEASE_MINISIGN_PUBKEY" "$PINNED_MINISIGN_PUBKEY"; then
    echo "Release-Abbruch: Der Public Key stimmt nicht mit dem Repository-Pin ueberein." >&2
    exit 1
  fi

  minisign -S -s "$NETMON_MINISIGN_SECRET_KEY" -m "$SUMS_FILE" -x "$DIST_DIR/SHA256SUMS.minisig"
  cp "$RELEASE_MINISIGN_PUBKEY" "$MINISIGN_PUBKEY_TARGET"
  "$MINISIGN_VERIFY_SCRIPT" \
    "$MINISIGN_PUBKEY_TARGET" \
    "$DIST_DIR/SHA256SUMS.minisig" \
    "$SUMS_FILE"

  echo "Signatur erzeugt: $DIST_DIR/SHA256SUMS.minisig"
}

require_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Fehlende Datei: $path" >&2
    exit 1
  fi
}

ensure_no_embedded_stats_token() {
  if grep -Eq 'stats_token"\s*=>\s*"[^"]+' "$ROOT_DIR/site/download-config.php"; then
    echo "Unsicherer Build-Abbruch: site/download-config.php enthaelt einen fest eingebauten stats_token." >&2
    echo "Bitte NETMON_STATS_TOKEN nur serverseitig setzen und keine Secrets ins Repo oder Upload-Bundle legen." >&2
    exit 1
  fi
  if grep -Eq '^[[:space:]]*SetEnv[[:space:]]+NETMON_STATS_TOKEN[[:space:]]+[^#[:space:]]+' "$ROOT_DIR/site/.htaccess" "$ROOT_DIR/site/htaccess"; then
    echo "Unsicherer Build-Abbruch: Eine htaccess-Vorlage enthaelt einen fest eingebauten NETMON_STATS_TOKEN." >&2
    echo "Bitte Tokens nur serverseitig im Hosting setzen und nicht im Repo versionieren." >&2
    exit 1
  fi
}

require_file "$ROOT_DIR/dist/netmon_${PKG_VERSION}_all.deb"
require_file "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.pdf"
require_file "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.html"
require_file "$ROOT_DIR/site/latest-version.json"
require_file "$ROOT_DIR/site/download-config.php"
require_file "$ROOT_DIR/site/downloads.html"
require_file "$ROOT_DIR/site/docs.html"
require_file "$ROOT_DIR/site/security-audit.html"
require_file "$ROOT_DIR/site/security-audit-r10.html"
require_file "$ROOT_DIR/site/netmon_security_audit_2026_r11.pdf"
require_file "$ROOT_DIR/site/netmon_security_audit_2026_r12.pdf"
require_file "$ROOT_DIR/site/en/downloads.html"
require_file "$ROOT_DIR/site/en/docs.html"
require_file "$ROOT_DIR/site/en/security-audit.html"
require_file "$PINNED_MINISIGN_PUBKEY"
require_file "$ROOT_DIR/scripts/verify_netmon_download.sh"
require_file "$ROOT_DIR/scripts/verify_netmon_signature.sh"

ensure_no_embedded_stats_token
python3 "$ROOT_DIR/scripts/check_release_consistency.py"

rm -rf "$BUILD_DIR"
mkdir -p "$DIST_DOCS_DIR" "$VERIFY_DIR" "$EN_DIR"

cp "$ROOT_DIR/site/latest-version.json" "$PUBLIC_DIR/latest-version.json"
cp "$ROOT_DIR/site/download-config.php" "$PUBLIC_DIR/download-config.php"
cp "$ROOT_DIR/site/downloads.html" "$PUBLIC_DIR/downloads.html"
cp "$ROOT_DIR/site/docs.html" "$PUBLIC_DIR/docs.html"
cp "$ROOT_DIR/site/security-audit.html" "$PUBLIC_DIR/security-audit.html"
cp "$ROOT_DIR/site/security-audit.html" "$PUBLIC_DIR/security-audit-r12.html"
cp "$ROOT_DIR/site/security-audit-r10.html" "$PUBLIC_DIR/security-audit-r10.html"
cp "$ROOT_DIR/site/netmon_security_audit_2026_r12.pdf" "$PUBLIC_DIR/netmon_security_audit_2026.pdf"
cp "$ROOT_DIR/site/netmon_security_audit_2026_r11.pdf" "$PUBLIC_DIR/netmon_security_audit_2026_r11.pdf"
cp "$ROOT_DIR/site/netmon_security_audit_2026_r12.pdf" "$PUBLIC_DIR/netmon_security_audit_2026_r12.pdf"
cp "$ROOT_DIR/site/en/downloads.html" "$EN_DIR/downloads.html"
cp "$ROOT_DIR/site/en/docs.html" "$EN_DIR/docs.html"
cp "$ROOT_DIR/site/en/security-audit.html" "$EN_DIR/security-audit.html"

cp "$ROOT_DIR/dist/netmon_${PKG_VERSION}_all.deb" "$DIST_DIR/"
cp "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.pdf" "$DIST_DOCS_DIR/"
cp "$ROOT_DIR/dist/docs/netmon_dokumentation_${DOCS_VERSION}.html" "$DIST_DOCS_DIR/"

cp "$ROOT_DIR/scripts/verify_netmon_download.sh" "$VERIFY_DIR/"
cp "$ROOT_DIR/scripts/verify_netmon_signature.sh" "$MINISIGN_VERIFY_SCRIPT"

(
  cd "$DIST_DIR"
  sha256sum \
    "netmon_${PKG_VERSION}_all.deb" \
    "docs/netmon_dokumentation_${DOCS_VERSION}.pdf" \
    "docs/netmon_dokumentation_${DOCS_VERSION}.html" \
    > "$SUMS_FILE"
)

sign_release

(
  cd "$BUILD_DIR"
  zip -rq netmonroots_release_update.zip public_html
)

echo "Fertig:"
echo "  Ordner: $PUBLIC_DIR"
echo "  ZIP:    $BUILD_DIR/netmonroots_release_update.zip"
echo
echo "Upload fuer Release-Update:"
echo "  public_html/latest-version.json"
echo "  public_html/download-config.php"
echo "  public_html/downloads.html"
echo "  public_html/docs.html"
echo "  public_html/security-audit.html"
echo "  public_html/security-audit-r12.html"
echo "  public_html/security-audit-r10.html"
echo "  public_html/netmon_security_audit_2026.pdf"
echo "  public_html/netmon_security_audit_2026_r11.pdf"
echo "  public_html/netmon_security_audit_2026_r12.pdf"
echo "  public_html/en/downloads.html"
echo "  public_html/en/docs.html"
echo "  public_html/en/security-audit.html"
echo "  public_html/dist/netmon_${PKG_VERSION}_all.deb"
echo "  public_html/dist/SHA256SUMS"
echo "  public_html/dist/docs/netmon_dokumentation_${DOCS_VERSION}.pdf"
echo "  public_html/dist/docs/netmon_dokumentation_${DOCS_VERSION}.html"
echo "  public_html/verify/verify_netmon_download.sh"
echo "  public_html/verify/verify_netmon_signature.sh"
if [[ -f "$DIST_DIR/SHA256SUMS.minisig" ]]; then
  echo "  public_html/dist/SHA256SUMS.minisig"
fi
if [[ -f "$MINISIGN_PUBKEY_TARGET" ]]; then
  echo "  public_html/verify/netmonroots.minisign.pub"
fi
