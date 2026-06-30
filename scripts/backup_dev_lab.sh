#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/workspaces/dev-lab"
DEFAULT_OUTPUT_DIR="${HOME}/backups/dev-lab"
TIMESTAMP="$(date +%F-%H%M%S)"
OUTPUT_DIR="${DEFAULT_OUTPUT_DIR}"
BACKUP_DIR=""

usage() {
  cat <<'EOF'
Usage: backup_dev_lab.sh [--output-dir DIR]

Creates backup archives for:
- the dev-lab project
- VS Code/Remote settings when present
- Codex and shell config files when present
- optional VS Code extension list

Examples:
  ./scripts/backup_dev_lab.sh
  ./scripts/backup_dev_lab.sh --output-dir /tmp/dev-lab-backups
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Fehler: --output-dir braucht einen Pfad." >&2
        exit 2
      fi
      OUTPUT_DIR="$1"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Fehler: Unbekanntes Argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

mkdir -p "$OUTPUT_DIR"
BACKUP_DIR="${OUTPUT_DIR}/backup-${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

created_files=()
skipped_items=()

create_archive() {
  local archive_name="$1"
  shift
  local existing=()

  for item in "$@"; do
    if [[ -e "$item" ]]; then
      existing+=("$item")
    else
      skipped_items+=("$item")
    fi
  done

  if [[ ${#existing[@]} -eq 0 ]]; then
    echo "Uebersprungen: ${archive_name} (keine Quellen gefunden)"
    return 0
  fi

  local archive_path="${BACKUP_DIR}/${archive_name}"
  tar --warning=no-file-changed --ignore-failed-read -czf "$archive_path" "${existing[@]}"
  created_files+=("$archive_path")
  echo "Erstellt: $archive_path"
}

create_archive   "dev-lab-project-${TIMESTAMP}.tar.gz"   "$PROJECT_ROOT"

create_archive   "vscode-settings-${TIMESTAMP}.tar.gz"   "${PROJECT_ROOT}/.vscode"   "${HOME}/.vscode-server/data/Machine"   "${HOME}/.vscode-server/data/User"

create_archive   "dev-configs-${TIMESTAMP}.tar.gz"   "${PROJECT_ROOT}/AGENTS.md"   "${HOME}/.codex"   "${HOME}/.bashrc"   "${HOME}/.profile"

if command -v code >/dev/null 2>&1; then
  extensions_file="${BACKUP_DIR}/vscode-extensions-${TIMESTAMP}.txt"
  if code --list-extensions >"$extensions_file" 2>/dev/null; then
    created_files+=("$extensions_file")
    echo "Erstellt: $extensions_file"
  else
    rm -f "$extensions_file"
    echo "Hinweis: VS Code Extensions konnten nicht exportiert werden."
  fi
else
  echo "Hinweis: 'code' nicht gefunden, Extensions-Liste uebersprungen."
fi

manifest_path="${BACKUP_DIR}/manifest-${TIMESTAMP}.txt"
{
  echo "Backup erstellt: $(date --iso-8601=seconds)"
  echo "Zielordner: ${BACKUP_DIR}"
  echo
  echo "Archive/Dateien:"
  if [[ ${#created_files[@]} -eq 0 ]]; then
    echo "- keine"
  else
    for item in "${created_files[@]}"; do
      echo "- ${item}"
    done
  fi
  echo
  echo "Uebersprungene Quellen:"
  if [[ ${#skipped_items[@]} -eq 0 ]]; then
    echo "- keine"
  else
    for item in "${skipped_items[@]}"; do
      echo "- ${item}"
    done
  fi
} >"$manifest_path"
created_files+=("$manifest_path")

echo
printf 'Backup abgeschlossen. Ziel: %s\n' "$BACKUP_DIR"
printf 'Dateien: %s\n' "${#created_files[@]}"
