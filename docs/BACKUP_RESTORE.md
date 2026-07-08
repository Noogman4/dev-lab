# Backup und Restore

## Uebersicht
In diesem Repository gibt es drei Hilfsskripte:

- `scripts/backup_dev_lab.sh`
- `scripts/restore_dev_lab_backup.sh`
- `scripts/restore_selected_dev_lab_backup.sh`
- `scripts/backup_restore_menu.sh`

Damit lassen sich Projekt, VS-Code-Einstellungen und relevante Konfigurationen sichern und wiederherstellen.

Fuer eine einfache Bedienung gibt es zusaetzlich ein kleines Menue:

```bash
/workspaces/dev-lab/scripts/backup_restore_menu.sh
```

## Backup erstellen
Standardziel:

```bash
/workspaces/dev-lab/scripts/backup_dev_lab.sh
```

Optional mit eigenem Zielordner:

```bash
/workspaces/dev-lab/scripts/backup_dev_lab.sh --output-dir /tmp/dev-lab-backups
```

Standardmaessig werden folgende Bereiche gesichert:

- `/workspaces/dev-lab`
- `/workspaces/dev-lab/.vscode` falls vorhanden
- `~/.vscode-server/data/Machine` falls vorhanden
- `~/.vscode-server/data/User` falls vorhanden
- `/workspaces/dev-lab/AGENTS.md`
- `~/.codex`
- `~/.bashrc`
- `~/.profile`
- optional VS-Code-Extensionsliste via `code --list-extensions`

Die Ausgabe landet standardmaessig unter:

```bash
~/backups/dev-lab/
```

Jeder Lauf erzeugt einen eigenen Ordner mit:

- Projekt-Archiv
- VS-Code-Archiv
- Konfig-Archiv
- optional Extensions-Liste
- Manifest-Datei

## Vorhandenes Backup
Aktuell existiert dieses Backup:

```bash
/home/vscode/backups/dev-lab/backup-2026-04-12-125154
```

## Komplettes Restore
Vorher pruefen mit Dry-Run:

```bash
/workspaces/dev-lab/scripts/restore_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154   --dry-run
```

Testweise in einen Zielordner entpacken:

```bash
/workspaces/dev-lab/scripts/restore_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154   --restore-root /tmp/restore-test
```

Echtes Restore an den Originalpfaden:

```bash
/workspaces/dev-lab/scripts/restore_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154
```

## Selektives Restore
Nur Projekt wiederherstellen:

```bash
/workspaces/dev-lab/scripts/restore_selected_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154   --project
```

Nur VS-Code-Einstellungen wiederherstellen:

```bash
/workspaces/dev-lab/scripts/restore_selected_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154   --vscode
```

Nur Konfigurationen wiederherstellen:

```bash
/workspaces/dev-lab/scripts/restore_selected_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154   --configs
```

Mehrere Bereiche kombinieren:

```bash
/workspaces/dev-lab/scripts/restore_selected_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154   --vscode --configs
```

Auch hier ist ein Dry-Run moeglich:

```bash
/workspaces/dev-lab/scripts/restore_selected_dev_lab_backup.sh   --backup-dir /home/vscode/backups/dev-lab/backup-2026-04-12-125154   --project --dry-run
```

## Hinweise
- Die Restore-Skripte entpacken standardmaessig nach `/`.
- Fuer einen sicheren Test zuerst `--dry-run` oder `--restore-root /tmp/restore-test` verwenden.
- Das Backup-Skript ignoriert fluechtige Dateiaenderungen waehrend des Packens, damit laufende Logs den Sicherungslauf nicht abbrechen.
- Ein Restore ueberschreibt vorhandene Dateien an denselben Pfaden mit den Versionen aus dem Backup.
