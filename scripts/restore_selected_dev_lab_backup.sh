#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR=""
RESTORE_ROOT="/"
DRY_RUN=0
RESTORE_PROJECT=0
RESTORE_VSCODE=0
RESTORE_CONFIGS=0

usage() {
  cat <<'EOF'
Usage: restore_selected_dev_lab_backup.sh --backup-dir DIR [selection] [--restore-root DIR] [--dry-run]

Restores selected archive groups created by backup_dev_lab.sh.

Selection:
  --project         Restore the dev-lab project archive.
  --vscode          Restore VS Code / remote settings archive.
  --configs         Restore Codex and shell config archive.

Options:
  --backup-dir DIR   Backup folder containing the .tar.gz archives.
  --restore-root DIR Restore into this root instead of /. Useful for tests.
  --dry-run          Only show what would be restored.
  -h, --help         Show this help.

Examples:
  ./scripts/restore_selected_dev_lab_backup.sh --backup-dir ~/backups/dev-lab/backup-2026-04-12-125154 --project --dry-run
  ./scripts/restore_selected_dev_lab_backup.sh --backup-dir ~/backups/dev-lab/backup-2026-04-12-125154 --vscode --configs
  ./scripts/restore_selected_dev_lab_backup.sh --backup-dir ~/backups/dev-lab/backup-2026-04-12-125154 --project --restore-root /tmp/restore-test
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
    --project)
      RESTORE_PROJECT=1
      ;;
    --vscode)
      RESTORE_VSCODE=1
      ;;
    --configs)
      RESTORE_CONFIGS=1
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

if [[ $RESTORE_PROJECT -eq 0 && $RESTORE_VSCODE -eq 0 && $RESTORE_CONFIGS -eq 0 ]]; then
  echo "Fehler: Mindestens eine Auswahl ist erforderlich: --project, --vscode oder --configs." >&2
  usage >&2
  exit 2
fi

mkdir -p "$RESTORE_ROOT"

find_archive() {
  local pattern="$1"
  find "$BACKUP_DIR" -maxdepth 1 -type f -name "$pattern" | sort | tail -n 1 || true
}

selected_archives=()

if [[ $RESTORE_PROJECT -eq 1 ]]; then
  archive=$(find_archive 'dev-lab-project-*.tar.gz')
  if [[ -n "$archive" ]]; then
    selected_archives+=("$archive")
  else
    echo "Fehler: Projekt-Archiv nicht gefunden." >&2
    exit 2
  fi
fi

if [[ $RESTORE_VSCODE -eq 1 ]]; then
  archive=$(find_archive 'vscode-settings-*.tar.gz')
  if [[ -n "$archive" ]]; then
    selected_archives+=("$archive")
  else
    echo "Fehler: VS-Code-Archiv nicht gefunden." >&2
    exit 2
  fi
fi

if [[ $RESTORE_CONFIGS -eq 1 ]]; then
  archive=$(find_archive 'dev-configs-*.tar.gz')
  if [[ -n "$archive" ]]; then
    selected_archives+=("$archive")
  else
    echo "Fehler: Konfig-Archiv nicht gefunden." >&2
    exit 2
  fi
fi

echo "Backup-Ordner: $BACKUP_DIR"
echo "Restore-Ziel: $RESTORE_ROOT"
if [[ $DRY_RUN -eq 1 ]]; then
  echo "Modus: dry-run"
else
  echo "Modus: restore"
fi
echo "Auswahl:"
[[ $RESTORE_PROJECT -eq 1 ]] && echo "- project"
[[ $RESTORE_VSCODE -eq 1 ]] && echo "- vscode"
[[ $RESTORE_CONFIGS -eq 1 ]] && echo "- configs"
echo

for archive in "${selected_archives[@]}"; do
  echo "Archiv: $archive"
  if [[ $DRY_RUN -eq 1 ]]; then
    tar -tzf "$archive" | sed 's/^/  - /'
  else
    tar -xzf "$archive" -C "$RESTORE_ROOT"
    echo "  Wiederhergestellt nach: $RESTORE_ROOT"
  fi
  echo
done

if [[ $DRY_RUN -eq 1 ]]; then
  echo "Dry-run abgeschlossen. Keine Dateien wurden geschrieben."
else
  echo "Selektives Restore abgeschlossen."
fi
