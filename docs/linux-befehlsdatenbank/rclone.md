---
id: "rclone"
name: "rclone"
command: "rclone"
category: "Backup & Sync"
language: "de"
root_required: false
risk_level: "caution"
tags: ["backup & sync", "rclone"]
status: "Quellen geprüft; lokales Kopierbeispiel und Backends praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 67
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielle Unterbefehlsreferenzen geprüft"
---

# rclone – Dateien gezielt kopieren und Synchronisation unterscheiden

## 1. Kurzbeschreibung

`rclone` überträgt und verwaltet Dateien zwischen lokalen Verzeichnissen und zahlreichen Speicher-Backends. Dazu zählen je nach Einrichtung entfernte Server und Cloudspeicher. **Für eigene lokale Dateien sind keine Root-Rechte nötig.** Kontoberechtigungen eines Cloudziels sind eine andere Frage als Linux-Root-Rechte.

Der Unterbefehl bestimmt die Wirkung. `copy`, `sync` und `move` sind keine austauschbaren Schreibweisen. Dieses Dokument beginnt mit einer lokalen Kopie; ein verbundenes Cloudkonto ist dafür nicht nötig.

## 2. Was macht der Befehl?

`copy` überträgt neue oder geänderte Dateien und lässt zusätzliche Dateien am Ziel stehen. Vorhandene passende Zieldateien können trotzdem ersetzt werden. `sync` gleicht das Ziel an die Quelle an und kann dort zusätzliche Dateien löschen. `move` entfernt erfolgreich übertragene Quelldaten nach seinem eigenen Ablauf.

Nach der [copy-Referenz](https://rclone.org/commands/rclone_copy/) werden bei einem Verzeichnis dessen **Inhalte** kopiert: Aus `quelle/notiz.txt` wird in `ziel` die Datei `ziel/notiz.txt`, nicht automatisch `ziel/quelle/notiz.txt`. Die [sync-Referenz](https://rclone.org/commands/rclone_sync/) beschreibt die zusätzliche Löschwirkung. Eine einfache Spiegelung ist keine unabhängige Versionssicherung.

## 3. Syntax

```text
rclone UNTERBEFEHL [OPTIONEN] ...
rclone copy QUELLE ZIEL [OPTIONEN]
rclone sync QUELLE ZIEL [OPTIONEN]
rclone check QUELLE ZIEL [OPTIONEN]
```

Lokale absolute Pfade sind gewöhnliche Dateisystempfade. Ein eingerichtetes Remote verwendet meist `NAME:PFAD`. Der Doppelpunkt ist also bedeutsam. Ein versehentlich als Remote interpretierter Name kann einen anderen Speicher als erwartet auswählen.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `--dry-run` | Geplante Änderungen melden, ohne sie durchzuführen. | Bei Remotes sind Zugriffe und Auflistungen trotzdem möglich. |
| `-i`, `--interactive` | Vor Änderungen nachfragen. | Bestätigungen ersetzen keine korrekte Pfadprüfung. |
| `-P`, `--progress` | Laufende Übertragungsstatistik anzeigen. | Keine automatische Inhaltsprüfung aller Dateien. |
| `--checksum` | Vergleich nach Größe und verfügbaren Prüfsummen bevorzugen. | Abhängig von Backend und unterstützten Hashes. |
| `--exclude MUSTER` | Bestimmte Pfade ausschließen. | Aufbewahrung und Löschwirkung zusammen betrachten. |
| `--config DATEI` | Konfiguration ausdrücklich auswählen. | Datei kann Zugangsdaten enthalten. |
| `check --download` | Zum Vergleich Daten beider Seiten lesen. | Kann Datenverkehr und Kosten verursachen. |

Die [check-Referenz](https://rclone.org/commands/rclone_check/) trennt Größen-/Hashvergleich, vollständiges Lesen und einseitige Prüfung. `--size-only` prüft ausdrücklich nur die Größe und beweist keine Inhaltsgleichheit.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Getrennte lokale Übungsordner anlegen

Das Beispiel benötigt ein installiertes rclone. Es wurde hier mangels Programm nicht praktisch ausgeführt. Keine echten Konten oder bestehenden Synchronisationsziele einsetzen.

```bash
(
  uebung="$(mktemp -d -t netmon-rclone-XXXXXX)" || exit 1
  mkdir "$uebung/quelle" "$uebung/ziel" || exit 1
  printf 'Eigene Notiz\n' > "$uebung/quelle/notiz.txt" || exit 1
  printf 'Bleibt erhalten\n' > "$uebung/ziel/extra.txt" || exit 1
  rclone copy "$uebung/quelle" "$uebung/ziel" --dry-run || exit 1
  rclone copy "$uebung/quelle" "$uebung/ziel" || exit 1
  cmp -- "$uebung/quelle/notiz.txt" "$uebung/ziel/notiz.txt" || exit 1
  test -f "$uebung/ziel/extra.txt" || exit 1
  printf 'Testordner: %s\n' "$uebung"
)
```

### Schritt 2: Vorschau und echte Kopie auseinanderhalten

Der erste rclone-Aufruf darf noch keine Testdatei kopieren. Erst der zweite schreibt `notiz.txt` ins Ziel. Beide Aufrufe nennen lokale Pfade; es gibt keine Cloudübertragung. Der ursprüngliche Zielinhalt `extra.txt` muss bei `copy` erhalten bleiben.

### Schritt 3: Ergebnisse prüfen

Ein stilles `cmp` mit Status 0 bestätigt gleichen Inhalt dieser einen Datei. `test -f` kontrolliert die zusätzliche Zieldatei. Würde derselbe Aufbau mit `sync` betrieben, wäre gerade diese Zusatzdatei löschgefährdet. Deshalb wird kein tatsächlicher Sync-Aufruf als beiläufiger nächster Schritt ausgeführt.

## 6. Typische Anwendungsfälle

### Ergänzende Dateikopie

Neue Dateien in eine vorhandene Ablage kopieren, ohne dort zusätzliche Bestände absichtlich zu entfernen. Das schützt nicht automatisch vor dem Überschreiben einer gleichnamigen Zieldatei.

### Geplante Spiegelung

Ein dediziertes Ziel soll genau den Quellbestand abbilden. Dafür ist `sync` geeignet, wenn Löschungen ausdrücklich gewollt und Vorschau sowie Aufbewahrung geprüft sind.

### Übertragungen kontrollieren

Nach einer Kopie verfügbare Größen oder Prüfsummen vergleichen. Ein Backend ohne passende Hashes benötigt eine andere Vergleichsmethode; eine schnelle Prüfung kann dann schwächer sein als erwartet.

## 7. Risiken, Nebenwirkungen und Vorsicht

`sync`, `delete`, `purge` und `move` können Daten entfernen. Ein leerer oder falsch ausgewählter Quellordner kann beim Spiegeln besonders folgenschwer sein. Filteränderungen beeinflussen, welcher Bestand überhaupt betrachtet wird.

Cloudzugang kann Kosten, Bandbreite und vertrauliche Daten betreffen. Konfigurationsdateien und Tokens schützen. „Obscure“-Darstellungen sind nicht automatisch starke Verschlüsselung; eine zusätzliche Verschlüsselungsschicht muss bewusst eingerichtet werden. Dateirechte, Symlinks und andere Metadaten sind zwischen Backends nicht immer gleich darstellbar. Quelle und Ziel nicht unbedacht überlappen lassen.

## 8. Häufige Fehler

- **Zielordnerstruktur anders erwartet:** rclone kopiert Verzeichnisinhalte.
- **Zusätzliche Zieldateien verschwinden:** `sync` statt `copy` gewählt.
- **Remote nicht gefunden:** Namen, Doppelpunkt und ausgewählte Konfiguration prüfen.
- **Vorschau als Netzwerklosigkeit verstanden:** Auch lesende Remoteprüfung kann Kontakt aufnehmen.
- **Prüfung nur nach Größe:** Unterschiedliche Inhalte können dieselbe Größe haben.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst lokale getrennte Ordner, danach ein bewusst angelegtes Testziel verwenden. Vorschau lesen und Richtung kontrollieren. Für wichtige Daten frühere Versionen oder ein getrenntes Backup erhalten, statt sich allein auf Spiegelung zu verlassen.

**Prüfstand:** Offizielle Referenzen zu `copy`, `sync` und `check` gelesen. rclone lokal nicht installiert. Beispiel nicht ausgeführt, kein Remote eingerichtet oder kontaktiert, keine Daten übertragen. Backend-Metadaten, Verschlüsselung und Löschschutz bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

- `rsync`: Dateikopie und Abgleich mit anderer Syntax.
- `restic`, `borg`: versionierte Sicherungen statt bloßer Spiegelung.
- `cmp`: lokale Dateien inhaltlich vergleichen.
- `scp`, `sftp`: Dateiübertragung über SSH mit anderem Bedienmodell.

Ausgangseintrag: Datensatz 67 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
