#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_BACKUP_BASE="${HOME}/backups/dev-lab"
DEFAULT_RESTORE_TEST_ROOT="/tmp/restore-test"

usage() {
  cat <<'EOF'
Usage: backup_restore_menu.sh

Interactive helper for:
- creating a backup
- restoring all archives
- restoring only project, VS Code settings, or configs

The script suggests the newest backup folder automatically.
EOF
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

find_latest_backup_dir() {
  find "$DEFAULT_BACKUP_BASE" -mindepth 1 -maxdepth 1 -type d -name 'backup-*' 2>/dev/null | sort | tail -n 1 || true
}

prompt_with_default() {
  local prompt="$1"
  local default_value="$2"
  local answer
  read -r -p "$prompt [$default_value]: " answer
  if [[ -z "$answer" ]]; then
    printf '%s
' "$default_value"
  else
    printf '%s
' "$answer"
  fi
}

run_backup() {
  local output_dir
  output_dir=$(prompt_with_default "Backup-Zielordner" "$DEFAULT_BACKUP_BASE")
  "$SCRIPT_DIR/backup_dev_lab.sh" --output-dir "$output_dir"
}

choose_backup_dir() {
  local latest_backup
  latest_backup=$(find_latest_backup_dir)
  if [[ -z "$latest_backup" ]]; then
    read -r -p "Backup-Ordner: " latest_backup
  else
    latest_backup=$(prompt_with_default "Backup-Ordner" "$latest_backup")
  fi
  printf '%s
' "$latest_backup"
}

choose_restore_root() {
  local target_mode restore_root
  echo "Restore-Ziel waehlen:"
  echo "1) Originalpfade (/)"
  echo "2) Testziel ($DEFAULT_RESTORE_TEST_ROOT)"
  echo "3) Eigener Zielordner"
  read -r -p "Auswahl [1]: " target_mode
  target_mode=${target_mode:-1}

  case "$target_mode" in
    1)
      printf '/
'
      ;;
    2)
      printf '%s
' "$DEFAULT_RESTORE_TEST_ROOT"
      ;;
    3)
      read -r -p "Eigener Zielordner: " restore_root
      if [[ -z "$restore_root" ]]; then
        echo "Fehler: Zielordner leer." >&2
        exit 2
      fi
      printf '%s
' "$restore_root"
      ;;
    *)
      echo "Fehler: Ungueltige Auswahl." >&2
      exit 2
      ;;
  esac
}

choose_dry_run() {
  local answer
  read -r -p "Erst Dry-Run ausfuehren? [Y/n]: " answer
  answer=${answer:-Y}
  if [[ "$answer" =~ ^([Yy]|[Jj])$ ]]; then
    return 0
  fi
  return 1
}

run_restore_all() {
  local backup_dir restore_root
  backup_dir=$(choose_backup_dir)
  restore_root=$(choose_restore_root)

  if choose_dry_run; then
    "$SCRIPT_DIR/restore_dev_lab_backup.sh" --backup-dir "$backup_dir" --restore-root "$restore_root" --dry-run
  else
    "$SCRIPT_DIR/restore_dev_lab_backup.sh" --backup-dir "$backup_dir" --restore-root "$restore_root"
  fi
}

run_restore_selected() {
  local backup_dir restore_root selection_flag
  backup_dir=$(choose_backup_dir)
  restore_root=$(choose_restore_root)

  echo "Selektives Restore:"
  echo "1) Nur Projekt"
  echo "2) Nur VS-Code"
  echo "3) Nur Configs"
  echo "4) VS-Code + Configs"
  read -r -p "Auswahl [1]: " selection_flag
  selection_flag=${selection_flag:-1}

  case "$selection_flag" in
    1)
      selection_flag="--project"
      ;;
    2)
      selection_flag="--vscode"
      ;;
    3)
      selection_flag="--configs"
      ;;
    4)
      selection_flag="--vscode --configs"
      ;;
    *)
      echo "Fehler: Ungueltige Auswahl." >&2
      exit 2
      ;;
  esac

  if choose_dry_run; then
    # shellcheck disable=SC2086
    "$SCRIPT_DIR/restore_selected_dev_lab_backup.sh" --backup-dir "$backup_dir" --restore-root "$restore_root" $selection_flag --dry-run
  else
    # shellcheck disable=SC2086
    "$SCRIPT_DIR/restore_selected_dev_lab_backup.sh" --backup-dir "$backup_dir" --restore-root "$restore_root" $selection_flag
  fi
}

echo "Backup / Restore Menue"
echo "1) Backup erstellen"
echo "2) Alles wiederherstellen"
echo "3) Selektiv wiederherstellen"
echo "4) Beenden"
read -r -p "Auswahl [1]: " main_choice
main_choice=${main_choice:-1}

case "$main_choice" in
  1)
    run_backup
    ;;
  2)
    run_restore_all
    ;;
  3)
    run_restore_selected
    ;;
  4)
    echo "Beendet."
    ;;
  *)
    echo "Fehler: Ungueltige Auswahl." >&2
    exit 2
    ;;
esac
