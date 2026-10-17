# Security Finding: Ungepruefte Restore-Archive

Datum: 17.10.2026. Codex Security Cloud, validiertes High-Finding:
"Restore scripts extract untrusted archive members directly under the restore root".
Gemeldete Revision: `c6a6c5b`. Arbeitsbasis der Korrektur: `bfaacf11`.

Dieser Bericht dokumentiert die lokal implementierte und getestete Korrektur
vor der Freigabe von Commit und Push. Ein Deployment wurde nicht ausgefuehrt.

## Bestaetigte Ursache

Beide Restore-Skripte riefen `tar -xzf ... -C "$RESTORE_ROOT"` auf, ohne
Mitgliedspfade oder Typen zu autorisieren. `RESTORE_ROOT` war standardmaessig
`/`. Das selektive Restore filterte nur Archivnamen. Das vorhandene Textmanifest
war eine Informationsliste und weder kryptografisch gebunden noch ausgewertet.
Der Dry-Run listete Inhalte lediglich auf. Auch das interaktive Menue waehlte
Originalpfade standardmaessig aus.

Die analysierte Backup-Erzeugung sicherte Projekt, VS-Code-Einstellungen sowie
Codex-/Shell-Konfigurationen. Daraus wurden die erlaubten Pfade je Kategorie
abgeleitet. Die NetMon-Dokumentenexports und andere NetMon-Module sind nicht
Teil dieser Aenderung.

## Gemeinsamer abgesicherter Ablauf

`scripts/dev_lab_backup.py` implementiert Backup und Restore zentral. Die drei
bestehenden CLI-Skripte delegieren dorthin; das Menue verwendet dieselben
Schnittstellen. Es gibt keinen direkten Tar-Extraktionspfad ins Restore-Ziel.

1. Ein unabhaengig bezogener Public Key muss explizit angegeben werden und
   ausserhalb des Backup-Ordners liegen. Ein mitgelieferter Angreifer-Key wird
   nicht automatisch als vertrauenswuerdig behandelt.
2. Private Snapshots von Manifest und Signatur werden mit Minisign geprueft,
   bevor JSON-Inhalte ausgewertet werden. Das neue Format `dev-lab-backup-v1`
   bindet Archivnamen, Kategorie, Archivgroesse und -hash sowie Mitgliedspfade,
   Typen, Groessen, eingeschraenkte Modi und Dateihashes.
3. Die Pfadregeln kommen aus dem vertrauenswuerdigen Helfer und lokal gesetzten
   Projekt-/Home-Pfaden. Das Manifest kann diese Regeln nicht erweitern.
   `etc/cron.d/payload` ist unter den normalen Projekt-/Home-Pfaden in keiner
   Kategorie autorisiert.
4. Alle ausgewaehlten Archive werden als regulaere Dateien ohne Symlink-Folgen
   geoeffnet und in ein privates Zwischenverzeichnis mit Modus 0700 kopiert.
   Verifiziert und gelesen werden danach ausschliesslich diese Snapshots.
5. Der Tar-Parser liest effektive Mitgliedspfade, einschliesslich PAX-Pfaden.
   Absolute oder nicht normalisierte Pfade, Traversierung, Symlinks, Hardlinks,
   Spezialdateien, Sparse-Dateien und doppelte Mitglieder werden abgelehnt.
   Das tatsaechliche Inventar muss exakt mit dem signierten Inventar uebereinstimmen.
6. Erst nach erfolgreicher Pruefung der gesamten Auswahl und vorhandener
   Zielpfade beginnt die Kopierphase. Freigegebene regulaere Dateien werden
   ueber Verzeichnisdeskriptoren und `O_NOFOLLOW` atomar ersetzt. Vorhandene
   Symlinks oder Hardlinks am Dateiziel werden abgelehnt. Archiv-Eigentuemer
   und sonstige privilegierte Metadaten werden nicht angewendet.

Neue Backups erzeugen ausschliesslich regulaere Datei- und Verzeichnismitglieder.
Symlinks und Spezialdateien in den Quellen werden ausgelassen; Hardlinks auf
regulaere Quelldateien werden als unabhaengige Datei-Kopien gesichert. Der
Signaturschluessel darf nicht in einer gesicherten Quelle liegen. Ein fehlender
Key oder fehlendes Minisign fuehrt zum Abbruch. Persoenliche Backup-Keys sind
vom bestehenden NetMon-Release-Key getrennt.

Der Standard ist ein neues privates temporaeres Restore-Verzeichnis.
`--restore-root /` wird abgelehnt. Originalpfade erfordern den ausdruecklichen
Modus `--restore-original-paths` mit effektiver Benutzer-ID 0; auch dann bleiben
Signatur und Pfadregeln verbindlich. Das Menue eskaliert keine Rechte und bietet
Originalpfade nicht als Standard an. Ein Dry-Run fuehrt dieselben Inhaltspruefungen
aus und schreibt keine Zieldateien.

## Tests und Nachweise

`tests/test_dev_lab_backup.py` enthaelt **95 bestandene Testfaelle** mit echten
Minisign-Signaturen und ausschliesslich temporaeren Quellen und Restore-Zielen.
Auch boesartige Archive werden im Test absichtlich mit einem Test-Key signiert,
damit die Pfad-/Typpruefung unabhaengig von der Signatur nachgewiesen wird.

| Szenario | Ergebnis |
| --- | --- |
| `etc/cron.d/payload` in jeder Kategorie, vollstaendig/selektiv, Restore/Dry-Run | Abbruch ohne Zielanlage |
| Absolute Pfade, `..`, doppelte Separatoren, Steuerzeichen, Backslashes | Abbruch |
| Symlink-/Hardlink-Mitglieder innerhalb erlaubter Praefixe | Abbruch im echten Tar-Parser |
| FIFO-, Zeichen- und Blockgeraete innerhalb erlaubter Praefixe | Abbruch |
| PAX-Pfad ueberschreibt erlaubten Namen mit `etc/cron.d/payload` | Abbruch |
| Geltende Signatur, aber falsche Mitgliedsgroesse, -hash, -modus oder -pfad | Abbruch wegen Inventarabweichung |
| Manipuliertes Manifest, ungueltige/fehlende Signatur, ersetztes Archiv | Abbruch ohne Zielanlage |
| Falscher unabhaengiger Public Key oder Key innerhalb des Backups | Abbruch |
| Symlink, FIFO oder Verzeichnis statt der Archivdatei | Abbruch ohne Blockieren |
| Vorhandene Ziel-Symlinks oder Hardlinks | Abbruch, externe Sentinel-Datei unveraendert |
| Gueltiges erstes und boesartiges spaeteres Archiv | Vorhandene Zieldatei bleibt unveraendert |
| Gueltiges komplettes Backup | Exakt die gesicherten Dateien und leeren Verzeichnisse restauriert |
| Selektive Kategorien, einzeln und kombiniert | Nur die ausgewaehlten Pfade restauriert |
| Restore ohne Zielangabe | Separates Ziel mit 0700; Originaldateien unveraendert |
| Fehlender Signaturschluessel, Legacy-Textmanifest, implizites `/` | Abbruch |

Gesamtpruefung auf dem finalen Code:

- `.venv/bin/python -m pytest -q -rs`: **2721 bestanden, 2 uebersprungen**.
  Die bestehenden Tk-Smoke-Tests in `test_netmon_roots_guard_ui.py` und
  `test_vpn_slots_tab.py` koennen Display `:0` nicht erreichen.
- ShellCheck fuer alle vier betroffenen Shell-Skripte: fehlerfrei.
- Black und Ruff fuer den neuen Helfer und seine Tests: fehlerfrei.
- `python3 -m py_compile scripts/dev_lab_backup.py`: erfolgreich.
- `git diff --check`: fehlerfrei.
- Ein separater lokaler Test mit einem temporaeren passwortgeschuetzten
  Minisign-Key bestaetigte die Backup-Erstellung und die Passphrase-Eingabe.

Bei der Implementierung wurde ein regulaeres 0711-Vorfahrenverzeichnis unter
`/tmp/user` beruecksichtigt: Die sichere Pfadwanderung verwendet `O_PATH`, um
keine unnoetigen Leserechte auf Vorfahren zu verlangen. `O_DIRECTORY` und
`O_NOFOLLOW` bleiben verbindlich. Der finale Testlauf funktioniert innerhalb
der Sandbox.

## Kompatibilitaet und Grenzen

Die neue Anleitung steht in [BACKUP_RESTORE.md](../BACKUP_RESTORE.md).
Alte unsignierte Backups werden nicht automatisch als vertrauenswuerdig
importiert. Es gibt keinen unsignierten Bypass. Neue signierte Backups muessen
aus geprueften Originalquellen erstellt werden; bestehende Archive wurden nicht
veraendert. Die fruehere optionale separate VS-Code-Extensionsliste ist kein
Bestandteil des neuen Formats.

Neue Dateien gehoeren dem aufrufenden Benutzer und erhalten 0600 bzw. 0700;
neue Verzeichnisse erhalten 0700. Bei privilegiertem Originalpfad-Restore sind
dies root-eigene Dateien. Benoetigte Eigentuemer muessen bewusst administrativ
gesetzt werden. Ein Fehler waehrend der Kopierphase kann einen teilweise
restaurierten Stand hinterlassen; eine Transaktion ueber alle Dateien ist nicht
implementiert. Eingabefehler werden vor der Kopierphase erkannt.

Es wurden keine bestehenden privaten Schluessel gelesen oder veraendert, keine
NetMon-Schluessel rotiert, keine echten Originalpfade restauriert und keine neuen
Python-Abhaengigkeiten eingefuehrt. Fuer Backups ist das bereits im Projekt
verwendete Minisign nun erforderlich. `secure-browser/` blieb unberuehrt.
