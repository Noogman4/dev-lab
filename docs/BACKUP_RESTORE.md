# Backup und Restore

Die drei CLI-Skripte und das Menue verwenden gemeinsam
`scripts/dev_lab_backup.py`. Voraussetzung: Linux, Python ab 3.11 und `minisign`.
Es werden keine Python-Zusatzpakete benoetigt.

- `scripts/backup_dev_lab.sh`: signiertes Backup erstellen
- `scripts/restore_dev_lab_backup.sh`: alle vorhandenen signierten Kategorien pruefen und wiederherstellen
- `scripts/restore_selected_dev_lab_backup.sh`: ausgewaehlte Kategorien wiederherstellen
- `scripts/backup_restore_menu.sh`: interaktive Bedienung mit separatem Ziel und Dry-Run als Standard

## Vertrauensmodell und neues Format

Ein Backup enthaelt bis zu drei `.tar.gz`-Archive, `manifest.json` und
`manifest.json.minisig`. Das signierte Manifest bindet jeden Archivnamen und
seine Kategorie, Groesse und SHA-256-Summe sowie alle Mitgliedspfade, Typen,
Groessen, eingeschraenkten Modi und Dateihashes. Fehlende oder falsche Signaturen,
fehlende Archive, zusaetzliche Tar-Archive und unpassende Inventare fuehren zum
Abbruch. Ein Tar-Dateiname allein autorisiert keinen Archivinhalt.

Der oeffentliche Backup-Schluessel muss **vorher unabhaengig vertrauenswuerdig
bezogen** worden sein und mit `--trusted-public-key` angegeben werden. Er darf
nicht im Backup-Ordner liegen. Einen Schluessel, den der Anbieter eines fremden
Backups mitliefert, nicht als Vertrauensanker uebernehmen. Auch die Skripte muessen
aus einem vertrauenswuerdigen Checkout stammen.

Dies sind persoenliche Backup-Schluessel. Der bestehende NetMon-Release-Key ist
davon getrennt und wird fuer diese Aenderung nicht benutzt oder veraendert.

Alte Backups mit rein informativem `manifest-*.txt` werden abgelehnt. Es gibt
keinen unsignierten Restore-Modus und keine automatische Migration, die fremde
Archive nachtraeglich als vertrauenswuerdig signiert. Aus vertrauenswuerdigen
Originalquellen ein neues signiertes Backup erstellen. Vorhandene alte Archive
bleiben unveraendert. Die fruehere optionale separate VS-Code-Extensionsliste
ist nicht Bestandteil des neuen Formats.

## Erlaubte Kategorien und Pfade

`PROJECT` ist standardmaessig das Repository, in dem die Skripte liegen; `HOME`
ist das Home-Verzeichnis des aufrufenden Benutzers. Diese Bezeichnungen in der
Tabelle beschreiben Pfade, keine aus dem Archiv eingelesenen Einstellungen.

| Kategorie | Erlaubte Quellen und Mitglieder |
| --- | --- |
| `project` | Das Projektverzeichnis mit seinen regulaeren Dateien und Verzeichnissen |
| `vscode` | `PROJECT/.vscode`, `HOME/.vscode-server/data/Machine`, `HOME/.vscode-server/data/User` und deren regulaere Inhalte |
| `configs` | Genau `PROJECT/AGENTS.md`, `HOME/.bashrc`, `HOME/.profile` sowie `HOME/.codex` und dessen regulaere Inhalte |

Absolute Quellpfade werden im Tar ohne fuehrenden Slash gespeichert. Ein
Projekt unter `/workspaces/dev-lab` liegt im Restore-Ziel daher unter
`workspaces/dev-lab`. `etc/cron.d/payload` ist in keiner Kategorie erlaubt.

Bei einem Umzug koennen die **bekannten urspruenglichen** Quellpfade explizit mit
`--project-root /workspaces/dev-lab --home-root /home/vscode` angegeben werden.
Diese Optionen setzen die lokale Pfadregel, nicht das Restore-Ziel. Die Pfade
nicht ungeprueft aus fremden Backup-Angaben uebernehmen. `/` ist fuer beide
Quellwurzeln verboten.

## Backup-Schluessel vorbereiten

Einen eigenen vorhandenen Backup-Schluessel verwenden. Falls noch keiner
existiert, kann er bewusst und getrennt vom Release-Key eingerichtet werden:

```bash
install -d -m 700 ~/.config/dev-lab-backup
minisign -G \
  -s ~/.config/dev-lab-backup/backup.key \
  -p ~/.config/dev-lab-backup/backup.pub
```

Den privaten Key mit Passphrase schuetzen, separat sichern und ausserhalb aller
Backup-Quellen aufbewahren. Der Backup-Ersteller bricht ab, wenn der angegebene
Key selbst innerhalb einer gesicherten Quelle liegt. Den Public Key unabhaengig
auf das Restore-System uebertragen und kontrollieren.

## Signiertes Backup erstellen

Aus dem Repository:

```bash
bash scripts/backup_dev_lab.sh \
  --signing-key ~/.config/dev-lab-backup/backup.key
```

Optional mit eigenem Ausgabeordner und bekannten Quellpfaden:

```bash
bash scripts/backup_dev_lab.sh \
  --signing-key ~/.config/dev-lab-backup/backup.key \
  --output-dir /tmp/dev-lab-backups \
  --project-root /workspaces/dev-lab \
  --home-root /home/vscode
```

Standardausgabe: `~/backups/dev-lab/backup-ZEITSTEMPEL/`, mit Verzeichnismodus
0700. Der Ausgabeordner darf nicht innerhalb einer gesicherten Quelle liegen.
Symlinks und Spezialdateien werden beim Erstellen ausgelassen. Regulaere Dateien
mit mehreren Hardlinks werden als unabhaengige regulaere Dateien gesichert;
das Backup enthaelt keine Hardlink-Mitglieder. Quellen duerfen waehrend des
Backups nicht veraendert werden; Lesefehler fuehren zum Abbruch. Unvollstaendige
Backups ohne gueltige Signatur werden vom Restore abgelehnt.

## Pruefen und in ein separates Ziel wiederherstellen

Zuerst das komplette Backup pruefen, ohne Zieldateien zu schreiben:

```bash
bash scripts/restore_dev_lab_backup.sh \
  --backup-dir /pfad/zum/backup-ZEITSTEMPEL \
  --trusted-public-key ~/.config/dev-lab-backup/backup.pub \
  --dry-run
```

Mit denselben Optionen ohne `--dry-run` wird ein **neues privates** Verzeichnis
`dev-lab-restore-*` im temporaeren Verzeichnis erzeugt und dessen Pfad ausgegeben.
Die Originaldateien werden dabei nicht angefasst. Fuer ein bestimmtes separates
Ziel:

```bash
bash scripts/restore_dev_lab_backup.sh \
  --backup-dir /pfad/zum/backup-ZEITSTEMPEL \
  --trusted-public-key ~/.config/dev-lab-backup/backup.pub \
  --restore-root /tmp/restore-test
```

Signatur und Pfadregeln werden auch beim Dry-Run vollstaendig geprueft. Die
gewaehlten Archive werden als private Snapshots eingelesen und unter einem
Zwischenverzeichnis mit Modus 0700 geprueft. Erst wenn **alle ausgewaehlten**
Archive und vorhandenen Zielpfade gueltig sind, werden freigegebene regulaere
Dateien ins Ziel kopiert. Es gibt kein direktes `tar -x` ins Restore-Ziel.
Die Pruefung arbeitet lokal ohne Netzwerk.

## Selektiv wiederherstellen

```bash
bash scripts/restore_selected_dev_lab_backup.sh \
  --backup-dir /pfad/zum/backup-ZEITSTEMPEL \
  --trusted-public-key ~/.config/dev-lab-backup/backup.pub \
  --vscode --configs \
  --restore-root /tmp/restore-test \
  --dry-run
```

Erlaubte Auswahlflags: `--project`, `--vscode`, `--configs`, auch kombiniert.
Ohne `--dry-run` wird nur die Auswahl ins separate Ziel kopiert.

## Originalpfade nur ausdruecklich und privilegiert

`--restore-root /` wird abgelehnt. Nur `--restore-original-paths` aktiviert die
Wiederherstellung an den Originalpfaden; dafuer ist ein ausdruecklicher Aufruf
mit effektiver Benutzer-ID 0 erforderlich. Das Menue bietet diesen Modus nicht
als Standard oder automatische Eskalation an. Vor einem solchen Aufruf zuerst
ins separate Verzeichnis wiederherstellen und den Inhalt pruefen.

Die erlaubten Quellpfade und der unabhaengig vertraute Public Key bleiben auch
in diesem Modus verbindlich. Bei einem privilegierten Aufruf kann das
Home-Verzeichnis wechseln; die bekannten urspruenglichen Pfade dann explizit
mit `--home-root` und `--project-root` setzen. Archiv-Eigentuemer, ACLs, xattrs,
Setuid-/Setgid-/Sticky-Bits und Gruppen-/Weltrechte werden nicht restauriert.
Neue Dateien gehoeren dem aufrufenden Benutzer, in diesem Modus also root;
benoetigte Eigentuemer muessen anschliessend bewusst administrativ gesetzt werden.

## Weitere Grenzen

- Absolute Pfade, `..`, mehrdeutige Pfade, Links, Spezialdateien, Sparse-Dateien
  und doppelte Tar-Mitglieder fuehren zum Abbruch.
- Vorhandene Symlinks in Zielpfaden und vorhandene Hardlinks an Dateizielen
  werden abgelehnt. Kopien verwenden Verzeichnisdeskriptoren und `O_NOFOLLOW`.
- Identische Dateien, die etwa in `project` und `configs` vorkommen, werden
  dedupliziert. Widerspruechliche Mehrfachbelegungen werden abgelehnt.
- Neue Verzeichnisse erhalten 0700, Dateien 0600 bzw. 0700 bei gesetztem
  Eigentuemer-Ausfuehrungsbit. Vorhandene regulaere Dateien werden atomar ersetzt.
- Grenzen: 200.000 Mitglieder, 8 GiB pro Datei und insgesamt 64 GiB Nutzdaten.
  Das signierte JSON-Manifest darf hoechstens 64 MiB gross sein.
- Nach erfolgreicher Vorpruefung koennen spaetere Betriebssystemfehler einen
  teilweise kopierten Stand hinterlassen; es gibt keine transaktionale Ruecknahme
  ueber mehrere Dateien. Bei Eingabefehlern beginnt die Kopierphase nicht.
