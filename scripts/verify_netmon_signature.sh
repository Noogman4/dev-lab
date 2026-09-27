#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Verwendung: $0 <public_key_file> <SHA256SUMS.minisig> <SHA256SUMS>" >&2
  exit 1
fi

PUBKEY_FILE="$1"
SIGNATURE_FILE="$2"
MESSAGE_FILE="$3"
PUBKEY_VALUE=""

for path in "$PUBKEY_FILE" "$SIGNATURE_FILE" "$MESSAGE_FILE"; do
  if [[ ! -f "$path" ]]; then
    echo "Datei nicht gefunden: $path" >&2
    exit 1
  fi
done

if ! command -v minisign >/dev/null 2>&1; then
  echo "minisign ist nicht installiert." >&2
  exit 1
fi

PUBKEY_VALUE="$(awk 'NF && $1 != "untrusted" { print; exit }' "$PUBKEY_FILE")"

if [[ -z "$PUBKEY_VALUE" ]]; then
  echo "Kein gueltiger Minisign-Public-Key in $PUBKEY_FILE gefunden." >&2
  exit 1
fi

if [[ -n "${NETMON_EXPECTED_MINISIGN_PUBKEY:-}" ]] && \
   [[ "$PUBKEY_VALUE" != "$NETMON_EXPECTED_MINISIGN_PUBKEY" ]]; then
  echo "Der Public Key stimmt nicht mit NETMON_EXPECTED_MINISIGN_PUBKEY ueberein." >&2
  exit 1
fi

minisign -V -P "$PUBKEY_VALUE" -x "$SIGNATURE_FILE" -m "$MESSAGE_FILE"
