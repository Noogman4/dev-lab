---
id: "rsync"
name: "rsync"
command: "rsync"
category: "DNS & Internet"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dns", "internet", "synchronisation", "kopieren", "backup"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten lokal geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 164
reviewed_at: "2026-11-13"
locally_checked_version: "rsync 3.2.7 (Protokoll 31)"
---

# rsync – Dateien und Ordner effizient abgleichen, lokal und über SSH

## 1. Kurzbeschreibung

`rsync` kopiert und **synchronisiert** Dateien und Ordner – innerhalb eines Rechners oder zwischen Rechnern, meist über SSH. Es überträgt nur, was sich geändert hat, und kann dabei Rechte, Zeitstempel, Verknüpfungen und auf Wunsch ACLs und erweiterte Attribute erhalten. Damit ist es ein Standardwerkzeug für Sicherungen, Spiegelungen und Bereitstellungen.

**Root-Rechte sind für eigene Dateien nicht nötig.** Nur das Erhalten fremder Eigentümer (`-o`) und von Gerätedateien erfordert laut [Debian-Manpage zu rsync](https://manpages.debian.org/trixie/rsync/rsync.1.en.html) Root-Rechte auf der Empfängerseite.

## 2. Was macht der Befehl?

`rsync QUELLE ZIEL` vergleicht Quelle und Ziel. Standardmäßig gilt eine Datei als unverändert, wenn Größe und Änderungszeit übereinstimmen; mit `-c` wird stattdessen eine Prüfsumme verglichen. Geänderte Dateien werden übertragen, bei entfernten Zielen mit einem Verfahren, das nur geänderte Teile sendet.

### Die Schrägstrich-Regel

Ein **abschließender Schrägstrich an der Quelle** verändert das Ergebnis:

| Aufruf | Ergebnis |
| --- | --- |
| `rsync -a quelle ziel/` | Legt `ziel/quelle/...` an (Ordner wird mitkopiert). |
| `rsync -a quelle/ ziel/` | Kopiert den **Inhalt** von `quelle` direkt nach `ziel/`. |

Die Manpage beschreibt das als „copy the contents of this directory“ gegenüber „copy the directory by name“. Im Test führte `rsync -a quelle ziel/` zu `ziel/quelle/a.txt`.

### Entfernte Ziele

`BENUTZER@HOST:PFAD` als Quelle oder Ziel nutzt standardmäßig SSH. Auf beiden Seiten muss `rsync` installiert sein.

## 3. Syntax

```text
rsync [OPTIONEN] QUELLE ... ZIEL
rsync [OPTIONEN] QUELLE ... [BENUTZER@]HOST:ZIEL
rsync [OPTIONEN] [BENUTZER@]HOST:QUELLE ZIEL
```

```bash
rsync -av ~/Dokumente/ /media/usb/Dokumente/
rsync -avn --delete projekt/ server:/srv/projekt/
rsync -aP grosse-datei.iso server:/daten/
```

Das bisherige NetMon-Beispiel `rsync --help` zeigt die Optionsübersicht. Der Platzhalter `rsync [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-a`, `--archive` | Archivmodus: `-rlptgoD`. | Laut Manpage **ohne** `-A`, `-X`, `-H`. |
| `-v`, `-i` | Ausführlich bzw. Änderungsübersicht je Datei. | `-i` zeigt z. B. `>f.s.......`. |
| `-n`, `--dry-run` | Probelauf ohne Änderungen. | Vor `--delete` immer verwenden. |
| `--delete` | Im Ziel löschen, was in der Quelle fehlt. | Größte Gefahrenquelle. |
| `-z` | Daten bei der Übertragung komprimieren. | Lohnt nur übers Netz. |
| `-e BEFEHL` | Andere Remote-Shell, z. B. `-e "ssh -p 2222"`. | – |
| `-P` | `--partial --progress`: Teilübertragungen behalten, Fortschritt anzeigen. | Für große Dateien. |
| `--exclude=MUSTER`, `--include=MUSTER` | Dateien aus- bzw. einschließen. | Reihenfolge beachten. |
| `-H`, `-A`, `-X` | Harte Links, ACLs, erweiterte Attribute erhalten. | Für vollständige Systemsicherungen. |
| `-c`, `--checksum` | Prüfsumme statt Größe/Zeit vergleichen. | Langsamer, gründlicher. |
| `-u`, `--update` | Neuere Dateien im Ziel nicht überschreiben. | – |
| `-b`, `--backup-dir=ORDNER` | Ersetzte oder gelöschte Dateien sichern. | Sicherheitsnetz bei `--delete`. |
| `-x` | Dateisystemgrenzen nicht überschreiten. | – |
| `--remove-source-files` | Übertragene Dateien in der Quelle löschen. | Verschieben statt Kopieren. |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Einen Ordner in einen anderen spiegeln und den Effekt von `--delete` gefahrlos vorab sehen. Alles geschieht lokal mit eigenen Übungsdateien.

### Schritt 1: Übungsdaten

```bash
uebung="$(mktemp -d -t netmon-rsync-XXXXXX)" || exit 1
cd "$uebung" || exit 1
mkdir -p quelle/sub ziel
echo a > quelle/a.txt
echo b > quelle/sub/b.txt
echo alt > ziel/nur-im-ziel.txt
```

### Schritt 2: Inhalt übertragen

```bash
rsync -av quelle/ ziel/
```

Die Liste nennt `a.txt`, `sub/` und `sub/b.txt`. `ziel/nur-im-ziel.txt` bleibt erhalten.

### Schritt 3: Löschen nur simulieren

```bash
rsync -av --delete --dry-run quelle/ ziel/
```

Die Ausgabe zeigt `deleting nur-im-ziel.txt` und endet mit `(DRY RUN)`. Die Datei ist danach noch da.

### Schritt 4: Änderung erkennen

```bash
echo neu >> quelle/a.txt
rsync -ai quelle/ ziel/
```

`-i` zeigt `>f.s....... a.txt`: Datei wird gesendet (`>f`), Größe (`s`) hat sich geändert.

## 6. Typische Anwendungsfälle

- **Sicherungen auf externe Laufwerke:** `rsync -aH --delete ~/ /media/usb/sicherung/` – nach Probelauf.
- **Server-Bereitstellungen:** Webseiten auf einen Server übertragen.
- **Große Dateien übertragen** mit Fortsetzbarkeit (`-P`).
- **Systemumzüge** mit `-aHAX` als Root.
- **Ordner abgleichen** ohne alles neu zu kopieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `rsync` schreibt, überschreibt und löscht. Der Kopf verwendet `caution`.

- **`--delete` mit falscher Richtung oder falschem Pfad** löscht Daten im Ziel. Werden Quelle und Ziel vertauscht oder ist die Quelle (etwa ein nicht eingehängtes Laufwerk) leer, wird das Ziel geleert.
- **Schrägstrich-Fehler:** Ohne oder mit `/` an der Quelle entsteht eine andere Struktur; mit `--delete` kann das ganze Inhalte entfernen.
- **Überschreiben:** Geänderte Dateien im Ziel werden ohne Rückfrage ersetzt.
- **`--remove-source-files`** löscht in der Quelle.
- **Unvollständige Sicherungen:** `-a` erhält keine ACLs, erweiterten Attribute und harten Links; dafür `-A`, `-X`, `-H`.
- **Entfernte Ziele:** SSH-Zugangsdaten und Rechte auf dem Server bestimmen, was überschrieben werden kann.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `rsync: [sender] change_dir "..." failed: No such file or directory (2)`, Rückgabewert `23` | Quelle existiert nicht (im Test). | Pfad prüfen. |
| Unerwarteter Unterordner im Ziel | Quelle ohne abschließenden Schrägstrich. | `quelle/` verwenden. |
| `rsync: command not found` auf der Gegenseite | rsync fehlt auf dem Server. | Dort installieren. |
| `Permission denied` | Fehlende Schreibrechte im Ziel oder SSH-Anmeldung. | Rechte und Zugang prüfen. |
| Dateien werden jedes Mal neu übertragen | Zeitstempel weichen ab (z. B. FAT-Dateisysteme). | `--modify-window=1` (laut Manpage Genauigkeit des Zeitvergleichs) oder `-c`. |

Wichtige Rückgabewerte laut Manpage: `0` Erfolg, `23` Teilübertragung wegen Fehler, `24` Teilübertragung wegen verschwundener Quelldateien. **Prüfpunkt:** Nur `23` wurde praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Vor jedem `--delete` einen Probelauf mit `-n`** und die Liste lesen.
2. **Schrägstriche bewusst setzen:** `quelle/ ziel/` für „Inhalt in Ziel“.
3. **Mit `-i` sehen, was sich ändert.**
4. **`--backup-dir`** als Sicherheitsnetz bei Spiegelungen.
5. **Prüfen, ob Laufwerke eingehängt sind,** bevor eine Sicherung mit `--delete` läuft.

### Prüfstand

- **Geprüfte Version:** rsync 3.2.7 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt** im Testordner (nur lokal): Kopie ohne und mit Schrägstrich, `-av`, `--delete --dry-run` (nichts gelöscht), `--delete` (Datei im Ziel entfernt), `-ai` nach Änderung, nicht vorhandene Quelle (Rückgabe 23).
- **Nicht geprüft:** Übertragungen über SSH, `-AXH`, `--backup-dir` mit tatsächlichen Sicherungsdateien, Fortsetzen mit `-P`, Rückgabewerte außer 23.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `cp -a` | Einfaches lokales Kopieren mit Metadaten. |
| `scp`, `sftp` | Dateiübertragung über SSH ohne Abgleich. |
| `tar` | Archivieren; über eine Pipe auch zum Übertragen. |
| `ssh` | Transportweg für entfernte Ziele. |

Ausgangseintrag: Datensatz 164 in `index.json` (`rsync`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Abgleichprinzip, Schrägstrich-Regel, Optionen, Löschrisiken und einen lokal geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
