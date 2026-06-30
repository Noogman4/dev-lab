#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Verwendung: $0 <SHA256SUMS> <datei> [weitere_dateien...]" >&2
  exit 1
fi

SUMS_FILE="$1"
shift

if [[ ! -f "$SUMS_FILE" ]]; then
  echo "SHA256SUMS nicht gefunden: $SUMS_FILE" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

cp "$SUMS_FILE" "$TMP_DIR/SHA256SUMS"

for file_path in "$@"; do
  if [[ ! -f "$file_path" ]]; then
    echo "Datei nicht gefunden: $file_path" >&2
    exit 1
  fi
  relative_path="$(basename "$file_path")"
  if [[ "$file_path" == */dist/docs/* ]]; then
    relative_path="docs/$(basename "$file_path")"
  fi
  mkdir -p "$TMP_DIR/$(dirname "$relative_path")"
  cp "$file_path" "$TMP_DIR/$relative_path"
done

(
  cd "$TMP_DIR"
  sha256sum -c SHA256SUMS
)
