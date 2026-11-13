---
id: "touch"
name: "touch"
command: "touch"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "zeitstempel"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 201
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# touch – Dateien anlegen und Zeitstempel ändern

## 1. Kurzbeschreibung

`touch` aktualisiert Zugriffszeit (`atime`) und Änderungszeit (`mtime`) einer Datei. Fehlt die Datei, legt GNU `touch` sie normalerweise leer an. **Root-Rechte sind für eigene Dateien nicht erforderlich.**

## 2. Was macht der Befehl?

Die Inhalte einer vorhandenen Datei werden nicht umgeschrieben. Ihre Zeitstempel ändern sich aber, was Synchronisation, Backups und Build-Werkzeuge beeinflussen kann. `ctime` (Metadatenänderungszeit) ist kein frei mit `touch` setzbarer Erstellungszeitpunkt. Bei symbolischen Links wird normalerweise das Ziel angesprochen. Die [GNU-coreutils-Manpage](https://manpages.debian.org/trixie/coreutils/touch.1.en.html) beschreibt die Auswahl der Zeitstempel.

## 3. Syntax

```bash
touch [OPTION]... DATEI...
touch -c -m -- "notiz.txt"
touch -r "vorlage.txt" -- "ziel.txt"
```

`--` beendet die Optionsauswertung. Ein Dateiname `-` hat bei GNU `touch` eine Sonderbedeutung (Standardausgabe); für eine tatsächlich so benannte Datei `./-` verwenden.

## 4. Wichtige Optionen

| Option | Bedeutung | Vorsicht |
| --- | --- | --- |
| `-a` | Nur Zugriffszeit ändern. | Dateisystem kann atime eingeschränkt verwalten. |
| `-m` | Nur Änderungszeit ändern. | Kann Build-/Sync-Logik beeinflussen. |
| `-c`, `--no-create` | Fehlende Datei nicht anlegen. | Existenz vorher prüfen. |
| `-d ZEIT` | Zeitangabe interpretieren. | Zeitzone und Format beachten. |
| `-t ZEIT` | Kompaktes Zeitformat verwenden. | Andere Syntax als `-d`. |
| `-r DATEI` | Zeiten einer Referenz übernehmen. | Referenz muss lesbar sein. |
| `-h` | Symlink selbst statt Ziel ändern. | Dateisystemunterstützung nötig. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

```bash
uebung="$(mktemp -d -t netmon-touch-XXXXXX)"
cd "$uebung" || exit 1
printf 'Testinhalt\n' > notiz.txt
stat -c '%n %s Byte %y' -- notiz.txt
```

### Schritt 2: Nur die Änderungszeit aktualisieren

```bash
touch -m -- notiz.txt
stat -c '%n %s Byte %y' -- notiz.txt
```

Der Inhalt bleibt gleich groß; die angezeigte `mtime` wird aktualisiert. Die tatsächliche Zeit hängt von Uhr und Dateisystemauflösung ab.

### Schritt 3: Fehlende Datei bewusst nicht erstellen

```bash
touch -c -- fehlt.txt
```

`fehlt.txt` wird nicht neu angelegt. Die Übung ist ein **nicht ausgeführtes Beispiel**.

## 6. Typische Anwendungsfälle

**Build-Prozesse:** Änderungszeit einer eigenen Testdatei aktualisieren. **Neue Markerdatei:** Eine leere Datei bewusst erzeugen. **Zeitvergleich:** Mit `-r` Zeitstempel einer Referenz übernehmen. Das ersetzt keine inhaltliche Dateiprüfung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein unbedachtes `touch` verändert Metadaten und kann Sicherungs- oder Verarbeitungsabläufe auslösen. Bei fehlenden Pfaden wird eine neue Datei erzeugt. Bei Symlinks ist der Unterschied zwischen Link und Ziel wichtig. Schreibrechte für Verzeichnis beziehungsweise Datei sind erforderlich; `sudo` ist keine Standardlösung.

## 8. Häufige Fehler

| Problem | Ursache | Lösung |
| --- | --- | --- |
| Datei unerwartet neu | Standardverhalten ohne `-c`. | `-c` und Pfad prüfen. |
| Falsche Zeit | Zeitzone oder Format. | `date` und `stat` vergleichen. |
| Berechtigung verweigert | Keine ausreichenden Rechte. | Eigene Testdatei verwenden. |
| Symlink-Ziel verändert | Standard folgt dem Link. | Verhalten von `-h` prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für reine Existenzkontrolle `test -e` statt `touch` einsetzen. In einem neuen temporären Ordner arbeiten und `-c` verwenden, wenn nichts erzeugt werden soll.

**Prüfstand:** Offizielle Debian-Manpage zu GNU coreutils 9.7 am 2026-11-13 gelesen. Die Beispielsyntax wurde fachlich abgeglichen; **keine Befehle ausgeführt, keine lokale Version geprüft**. Dateisystem- und Zeitauflösungsunterschiede bleiben offen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `stat` | Zeitstempel und Dateigröße anzeigen. |
| `date` | Zeitangaben und Zeitzonen prüfen. |
| `test` | Existenz ohne Änderung prüfen. |
| `install` | Dateien mit gezielten Rechten anlegen. |

**Ausgangseintrag:** `source_record` 201 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
