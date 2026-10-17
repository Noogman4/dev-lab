#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Shared authentication, member policy, staging and safe copy implementation.
exec python3 "$SCRIPT_DIR/dev_lab_backup.py" restore --all "$@"
