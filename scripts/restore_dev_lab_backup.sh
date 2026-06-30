#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=""
RESTORE_ROOT="/"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: restore_dev_lab_backup.sh --backup-dir DIR [--restore-root DIR] [--dry-run]

Restores archives created by backup_dev_lab.sh.

Options:
  --backup-dir DIR   Backup folder containing the .tar.gz archives.
  --restore-root DIR Restore into this root instead of /. Useful for tests.
  --dry-run          Only show what would be restored.
  -h, --help         Show this help.

Examples:
  ./scripts/restore_dev_lab_backup.sh --backup-dir ~/backups/dev-lab/backup-2026-04-12-125154 --dry-run
  ./scripts/restore_dev_lab_backup.sh --backup-dir ~/backups/dev-lab/backup-2026-04-12-125154
  ./scripts/restore_dev_lab_backup.sh --backup-dir ~/backups/dev-lab/backup-2026-04-12-125154 --restore-root /tmp/restore-test
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup-dir)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Fehler: --backup-dir braucht einen Pfad." >&2
        exit 2
      fi
      BACKUP_DIR="$1"
      ;;
    --restore-root)
      shift
      if [[ $# -eq 0 ]]; then
        echo "Fehler: --restore-root braucht einen Pfad." >&2
        exit 2
      fi
      RESTORE_ROOT="$1"
      ;;
    --dry-run)
      DRY_RUN=1
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

if [[ -z "$BACKUP_DIR" ]]; then
  echo "Fehler: --backup-dir ist erforderlich." >&2
  usage >&2
  exit 2
fi

if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "Fehler: Backup-Ordner nicht gefunden: $BACKUP_DIR" >&2
  exit 2
fi

mkdir -p "$RESTORE_ROOT"

mapfile -t archives < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.tar.gz' | sort)

if [[ ${#archives[@]} -eq 0 ]]; then
  echo "Fehler: Keine .tar.gz-Archive in $BACKUP_DIR gefunden." >&2
  exit 2
fi

echo "Backup-Ordner: $BACKUP_DIR"
echo "Restore-Ziel: $RESTORE_ROOT"
if [[ $DRY_RUN -eq 1 ]]; then
  echo "Modus: dry-run"
else
  echo "Modus: restore"
fi
echo

for archive in "${archives[@]}"; do
  echo "Archiv: $archive"
  if [[ $DRY_RUN -eq 1 ]]; then
    tar -tzf "$archive" | sed 's/^/  - /'
  else
    tar -xzf "$archive" -C "$RESTORE_ROOT"
    echo "  Wiederhergestellt nach: $RESTORE_ROOT"
  fi
  echo
done

manifest_file=$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'manifest-*.txt' | sort | tail -n 1 || true)
if [[ -n "$manifest_file" ]]; then
  echo "Manifest: $manifest_file"
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "Dry-run abgeschlossen. Keine Dateien wurden geschrieben."
else
  echo "Restore abgeschlossen."
fi
