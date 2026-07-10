#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_VERSION="${NETMON_RELEASE_VERSION:-1.1.17}"
DOCS_VERSION="${NETMON_DOCS_VERSION:-$PKG_VERSION}"
BUILD_DIR="$ROOT_DIR/dist/site-release-update"
PUBLIC_DIR="$BUILD_DIR/public_html"
DIST_DIR="$PUBLIC_DIR/dist"
DIST_DOCS_DIR="$DIST_DIR/docs"
VERIFY_DIR="$PUBLIC_DIR/verify"
EN_DIR="$PUBLIC_DIR/en"
SUMS_FILE="$DIST_DIR/SHA256SUMS"
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

  minisign -S -s "$NETMON_MINISIGN_SECRET_KEY" -m "$SUMS_FILE" -x "$DIST_DIR/SHA256SUMS.minisig"

  if [[ -n "${NETMON_MINISIGN_PUBKEY:-}" && -f "${NETMON_MINISIGN_PUBKEY}" ]]; then
    cp "$NETMON_MINISIGN_PUBKEY" "$MINISIGN_PUBKEY_TARGET"
  fi

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
require_file "$ROOT_DIR/site/en/downloads.html"
require_file "$ROOT_DIR/site/en/docs.html"
require_file "$ROOT_DIR/scripts/verify_netmon_download.sh"
require_file "$ROOT_DIR/scripts/verify_netmon_signature.sh"

ensure_no_embedded_stats_token

rm -rf "$BUILD_DIR"
mkdir -p "$DIST_DOCS_DIR" "$VERIFY_DIR" "$EN_DIR"

cp "$ROOT_DIR/site/latest-version.json" "$PUBLIC_DIR/latest-version.json"
cp "$ROOT_DIR/site/download-config.php" "$PUBLIC_DIR/download-config.php"
cp "$ROOT_DIR/site/downloads.html" "$PUBLIC_DIR/downloads.html"
cp "$ROOT_DIR/site/docs.html" "$PUBLIC_DIR/docs.html"
cp "$ROOT_DIR/site/en/downloads.html" "$EN_DIR/downloads.html"
cp "$ROOT_DIR/site/en/docs.html" "$EN_DIR/docs.html"

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

maybe_sign_release

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
echo "  public_html/en/downloads.html"
echo "  public_html/en/docs.html"
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
