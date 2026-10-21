#!/usr/bin/env bash
# Shared production-only lifecycle. Caller must enable set -euo pipefail.

begin_release_build() {
  local label="$1"
  OUTPUT_DIR="$ROOT_DIR/dist/$label"
  RELEASE_WORK=""
  RELEASE_PREVIOUS=""
  trap 'release_cleanup "$?"' EXIT
  trap 'exit 130' INT
  trap 'exit 143' TERM
  umask 077
  local path
  for path in "$ROOT_DIR/dist" "$ROOT_DIR/dist/.release-work" "$ROOT_DIR/dist/.release-history"; do
    if [[ -L "$path" || ( -e "$path" && ! -d "$path" ) ]]; then
      echo "Release-Abbruch: Unsicherer Ausgabepfad: $path" >&2
      return 1
    fi
    mkdir -p -- "$path"
  done
  local lock="$ROOT_DIR/dist/.$label.lock"
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
    RELEASE_PREVIOUS="$(mktemp -d "$ROOT_DIR/dist/.release-history/$label.previous.XXXXXX")"
    python3 -c 'import os, sys; os.rename(sys.argv[1], sys.argv[2])' \
      "$OUTPUT_DIR" "$RELEASE_PREVIOUS/previous-output"
    echo "Vorheriger Build archiviert (kein Ergebnis dieses Laufs): $RELEASE_PREVIOUS" >&2
  fi
  RELEASE_WORK="$(mktemp -d "$ROOT_DIR/dist/.release-work/$label.XXXXXX")"
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

sign_release() {
  minisign -S -s "$NETMON_MINISIGN_SECRET_KEY" -m "$SUMS_FILE" -x "$PUBLIC_DIR/dist/SHA256SUMS.minisig"
  cp "$RELEASE_MINISIGN_PUBKEY" "$MINISIGN_PUBKEY_TARGET"
  bash "$ROOT_DIR/scripts/verify_netmon_signature.sh" \
    "$MINISIGN_PUBKEY_TARGET" "$PUBLIC_DIR/dist/SHA256SUMS.minisig" "$SUMS_FILE"
}

finish_release_build() {
  local kind="$1" filename="$2"
  # Download checksums stay compatible. A second signed manifest binds the
  # complete deployable tree, excluding only itself and its own signature.
  python3 "$ROOT_DIR/scripts/verify_netmon_release_bundle.py" "$PUBLIC_DIR" \
    --kind "$kind" --write-manifest
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
  # Inspect the actual ZIP bytes, using the repository verifier, never a verifier
  # supplied by the archive. Only a verified ZIP and its directory are promoted.
  python3 "$ROOT_DIR/scripts/verify_netmon_release_bundle.py" "$BUILD_DIR/$filename" \
    --kind "$kind" --upload-directory "$PUBLIC_DIR"
  # The upload directory is also an output. Recheck it after packaging so a
  # changed source cannot leave a valid ZIP beside an invalid upload directory.
  bash "$ROOT_DIR/scripts/verify_netmon_signature.sh" \
    "$MINISIGN_PUBKEY_TARGET" "$PUBLIC_DIR/dist/SHA256SUMS.minisig" "$SUMS_FILE"
  (
    cd "$PUBLIC_DIR/dist" || exit
    sha256sum -c SHA256SUMS
  )
  if [[ -e "$OUTPUT_DIR" || -L "$OUTPUT_DIR" ]]; then
    echo "Release-Abbruch: Produktionsziel wurde waehrend des Builds belegt." >&2
    return 1
  fi
  # os.rename fails on EXDEV; unlike mv it never falls back to a partial copy.
  python3 -c 'import os, sys; os.rename(sys.argv[1], sys.argv[2])' \
    "$BUILD_DIR" "$OUTPUT_DIR"
  RELEASE_WORK=""
}
