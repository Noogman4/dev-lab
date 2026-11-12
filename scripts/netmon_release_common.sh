#!/usr/bin/env bash
# Shared production-only lifecycle. Caller must enable set -euo pipefail.

require_release_snapshot() {
  # ROOT_DIR is the private git export of NETMON_RELEASE_COMMIT made by
  # netmon_release_source.py; WORKSPACE_DIR only supplies dist/ artifacts.
  WORKSPACE_DIR="${NETMON_RELEASE_WORKSPACE:-}"
  if [[ ! "${NETMON_RELEASE_COMMIT:-}" =~ ^[0-9a-f]{40}$ \
        || -z "$WORKSPACE_DIR" || "$WORKSPACE_DIR" == "$ROOT_DIR" \
        || -e "$ROOT_DIR/.git" || ! -d "$WORKSPACE_DIR/.git" ]]; then
    echo "Release-Abbruch: Produktions-Bundles nur ueber netmon_release_source.py aus einem Commit-Snapshot." >&2
    return 1
  fi
  readonly WORKSPACE_DIR
}

begin_release_build() {
  local label="$1"
  require_release_snapshot
  OUTPUT_DIR="$WORKSPACE_DIR/dist/$label"
  RELEASE_WORK=""
  RELEASE_PREVIOUS=""
  trap 'release_cleanup "$?"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  umask 077
  local path
  for path in "$WORKSPACE_DIR/dist" "$WORKSPACE_DIR/dist/.release-work" "$WORKSPACE_DIR/dist/.release-history"; do
    if [[ -L "$path" || ( -e "$path" && ! -d "$path" ) ]]; then
      echo "Release-Abbruch: Unsicherer Ausgabepfad: $path" >&2
      return 1
    fi
    mkdir -p -- "$path"
  done
  local lock="$WORKSPACE_DIR/dist/.$label.lock"
  if [[ -L "$lock" ]]; then
    echo "Release-Abbruch: Lock-Datei darf kein Symlink sein." >&2
    return 1
  fi
  exec {RELEASE_LOCK_FD}>"$lock"
  if ! flock -n "$RELEASE_LOCK_FD"; then
    echo "Release-Abbruch: Ein Build fuer $label laeuft bereits." >&2
    return 1
  fi
  # Retain older output, but remove it from the current-success location even
  # when this attempt fails at preflight. Never present it as this build's result.
  if [[ -L "$OUTPUT_DIR" || ( -e "$OUTPUT_DIR" && ! -d "$OUTPUT_DIR" ) ]]; then
    echo "Release-Abbruch: Unsicherer Produktionspfad: $OUTPUT_DIR" >&2
    return 1
  fi
  if [[ -d "$OUTPUT_DIR" ]]; then
    RELEASE_PREVIOUS="$(mktemp -d "$WORKSPACE_DIR/dist/.release-history/$label.previous.XXXXXX")"
    python3 -c 'import os, sys; os.rename(sys.argv[1], sys.argv[2])' \
      "$OUTPUT_DIR" "$RELEASE_PREVIOUS/previous-output"
    echo "Vorheriger Build archiviert (kein Ergebnis dieses Laufs): $RELEASE_PREVIOUS" >&2
  fi
  RELEASE_WORK="$(mktemp -d "$WORKSPACE_DIR/dist/.release-work/$label.XXXXXX")"
  BUILD_DIR="$RELEASE_WORK"
}

release_cleanup() {
  local status="$1"
  if [[ -n "$RELEASE_WORK" ]]; then
    rm -rf -- "$RELEASE_WORK"
  fi
  if (( status != 0 )); then
    echo "Release fehlgeschlagen: kein neuer Produktions-Build freigegeben." >&2
  fi
}

require_release_signing() {
  if ! command -v minisign >/dev/null 2>&1; then
    echo "Release-Abbruch: minisign ist nicht installiert." >&2
    return 1
  fi
  if [[ -z "${NETMON_MINISIGN_SECRET_KEY:-}" || ! -f "$NETMON_MINISIGN_SECRET_KEY" || ! -r "$NETMON_MINISIGN_SECRET_KEY" ]]; then
    echo "Release-Abbruch: NETMON_MINISIGN_SECRET_KEY fehlt oder ist nicht lesbar." >&2
    return 1
  fi
  if [[ ! -f "$RELEASE_MINISIGN_PUBKEY" ]] || ! cmp -s "$RELEASE_MINISIGN_PUBKEY" "$PINNED_MINISIGN_PUBKEY"; then
    echo "Release-Abbruch: Der Public Key stimmt nicht mit dem Repository-Pin ueberein." >&2
    return 1
  fi
}

copy_release_file() {
  local source="$1" target="$2"
  if [[ "$target" == */ ]]; then
    target+="${source##*/}"
  fi
  # Open every source component with O_NOFOLLOW, then copy from that FD.
  # A preflight -L check alone would leave a check/use race before cp/convert.
  # Committed content comes from the snapshot; only dist/ from the workspace.
  local source_root="$ROOT_DIR"
  if [[ "$source" == "$WORKSPACE_DIR/dist/"* ]]; then
    source_root="$WORKSPACE_DIR"
  fi
  python3 "$ROOT_DIR/scripts/copy_netmon_release_input.py" \
    --source-root "$source_root" --destination-root "$WORKSPACE_DIR" \
    "$BUILD_DIR" "$source" "$target"
}

stage_release_deb() {
  # Copy first, then prove the private staged bytes: what gets signed is the
  # receipt-bound DEB from build_netmon_deb.sh --release for the current HEAD.
  local source="$WORKSPACE_DIR/dist/netmon_${PKG_VERSION}_all.deb" target="$1"
  copy_release_file "$source" "$target/"
  RELEASE_DEB_SHA256="$(python3 "$ROOT_DIR/scripts/netmon_release_deb_receipt.py" verify \
    "$source" "$target/netmon_${PKG_VERSION}_all.deb" --version "$PKG_VERSION" \
    --commit "$NETMON_RELEASE_COMMIT" --sha256-only)"
  readonly RELEASE_DEB_SHA256
  RELEASE_STAGED_DEB="$target/netmon_${PKG_VERSION}_all.deb"
}

stage_release_docs() {
  # dist/docs is generated, not committed. Accept it only byte-identical to
  # the copies inside the receipt-approved DEB staged above.
  local target="$1" name
  for name in "netmon_dokumentation_${DOCS_VERSION}.pdf" "netmon_dokumentation_${DOCS_VERSION}.html"; do
    copy_release_file "$WORKSPACE_DIR/dist/docs/$name" "$target/"
  done
  python3 "$ROOT_DIR/scripts/netmon_release_deb_receipt.py" docs \
    "$RELEASE_STAGED_DEB" --sha256 "$RELEASE_DEB_SHA256" \
    "$target/netmon_dokumentation_${DOCS_VERSION}.pdf" \
    "$target/netmon_dokumentation_${DOCS_VERSION}.html"
}

write_release_checksums() {
  # Preserve the approved digest, rather than approving staged bytes again by
  # hashing them after the receipt check. Later gates reject any replacement.
  (
    cd "$PUBLIC_DIR/dist" || exit
    printf '%s  %s\n' "$RELEASE_DEB_SHA256" "netmon_${PKG_VERSION}_all.deb"
    sha256sum \
      "docs/netmon_dokumentation_${DOCS_VERSION}.pdf" \
      "docs/netmon_dokumentation_${DOCS_VERSION}.html"
  ) > "$SUMS_FILE"
}

sign_release() {
  # The optional override was compared with this pin at preflight. Publish
  # only the workspace pin, through the same no-follow staging path.
  copy_release_file "$PINNED_MINISIGN_PUBKEY" "$MINISIGN_PUBKEY_TARGET"
  minisign -S -s "$NETMON_MINISIGN_SECRET_KEY" -m "$SUMS_FILE" -x "$PUBLIC_DIR/dist/SHA256SUMS.minisig"
  bash "$ROOT_DIR/scripts/verify_netmon_signature.sh" \
    "$MINISIGN_PUBKEY_TARGET" "$PUBLIC_DIR/dist/SHA256SUMS.minisig" "$SUMS_FILE"
}

finish_release_build() {
  local kind="$1" filename="$2"
  # Download checksums stay compatible. A second signed manifest binds the
  # complete deployable tree, excluding only itself and its own signature.
  python3 "$ROOT_DIR/scripts/verify_netmon_release_bundle.py" "$PUBLIC_DIR" \
    --kind "$kind" --write-manifest --release-deb-sha256 "$RELEASE_DEB_SHA256"
  minisign -S -s "$NETMON_MINISIGN_SECRET_KEY" \
    -m "$PUBLIC_DIR/verify/RELEASE-SHA256SUMS" \
    -x "$PUBLIC_DIR/verify/RELEASE-SHA256SUMS.minisig"
  find "$PUBLIC_DIR" -type d -exec chmod 755 {} +
  find "$PUBLIC_DIR" -type f -exec chmod 644 {} +
  chmod 755 "$PUBLIC_DIR/verify/verify_netmon_download.sh" "$MINISIGN_VERIFY_SCRIPT"
  (
    cd "$BUILD_DIR" || exit
    zip -rq "$filename" public_html
  )
  # The verifier reconstructs a fresh upload tree from the authenticated ZIP
  # bytes and atomically promotes that independent snapshot itself. The mutable
  # workspace is checked for packaging changes, then cleaned by the EXIT trap.
  python3 "$ROOT_DIR/scripts/verify_netmon_release_bundle.py" "$BUILD_DIR/$filename" \
    --kind "$kind" --upload-directory "$PUBLIC_DIR" --release-deb-sha256 "$RELEASE_DEB_SHA256" \
    --promote-to "$OUTPUT_DIR"
}
