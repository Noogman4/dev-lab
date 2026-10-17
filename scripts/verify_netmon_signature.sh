#!/usr/bin/env bash
set -euo pipefail

# Trust anchor from the independently maintained repository (SECURITY.md).
# Never derive this value from downloaded files or environment variables.
readonly PINNED_MINISIGN_PUBKEY='RWQE0L1nGF+/VDIfeLCEp4x2UutfhhdCmPKSMTZY05kXJprqXyXfzo9R'

if [[ $# -ne 3 ]]; then
  echo "Verwendung: $0 <public_key_file> <SHA256SUMS.minisig> <SHA256SUMS>" >&2
  exit 1
fi

PUBKEY_FILE="$1"
SIGNATURE_FILE="$2"
MESSAGE_FILE="$3"

for path in "$PUBKEY_FILE" "$SIGNATURE_FILE" "$MESSAGE_FILE"; do
  if [[ ! -f "$path" || ! -r "$path" ]]; then
    echo "Datei nicht gefunden oder nicht lesbar: $path" >&2
    exit 1
  fi
done

# Require exactly the Minisign comment line and the canonical key line.
# Compare inside awk so binary/NUL bytes cannot disappear in shell substitution.
if ! LC_ALL=C awk -v pinned="$PINNED_MINISIGN_PUBKEY" '
  NR == 1 && /^untrusted comment: / { next }
  NR == 2 && $0 == pinned { next }
  { invalid = 1 }
  END { exit (invalid || NR != 2) }
' "$PUBKEY_FILE"; then
  echo "Ungueltige Public-Key-Datei oder Public Key stimmt nicht mit dem festen NetMon-Pin ueberein: $PUBKEY_FILE" >&2
  exit 1
fi

if ! command -v minisign >/dev/null 2>&1; then
  echo "minisign ist nicht installiert." >&2
  exit 1
fi

# Use the constant directly; never re-read the supplied key after validation.
minisign -V -P "$PINNED_MINISIGN_PUBKEY" -x "$SIGNATURE_FILE" -m "$MESSAGE_FILE"
