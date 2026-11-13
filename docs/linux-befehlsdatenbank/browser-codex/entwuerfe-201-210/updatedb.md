---
id: "updatedb"
name: "updatedb"
command: "updatedb"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["suche", "datenbank", "dateinamen"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 205
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# updatedb – Suchdatenbank für locate aufbauen

## 1. Kurzbeschreibung

`updatedb` erstellt oder aktualisiert eine Dateinamen-Datenbank für `locate` beziehungsweise `plocate`. Der Standardlauf ist eine **Systemverwaltungsaufgabe** und kann privilegierte Rechte benötigen; eine ausdrücklich begrenzte **private Datenbank** kann ohne Root erzeugt werden.

## 2. Was macht der Befehl?

Der plocate-Implementierung zufolge wird die Standarddatenbank typischerweise per Timer aktualisiert. Sie enthält Pfade, nicht Dateiinhalte, kann aber sensible Namen offenlegen. `updatedb` existiert auch in anderen Implementierungen mit abweichenden Optionen. Hier gilt ausdrücklich die [Debian-plocate-Manpage](https://manpages.debian.org/trixie/plocate/updatedb.8.en.html).

## 3. Syntax

```bash
updatedb [OPTION]...
updatedb -l 0 -U "EIGENER_ORDNER" -o "PRIVATE_DB"
```

**Kein** Aufruf von `updatedb` ohne Begrenzung in der Einsteigerübung: Er würde die Standarddatenbank verändern.

## 4. Wichtige Optionen

| Option (plocate) | Bedeutung | Hinweis |
| --- | --- | --- |
| `-U PFAD` | Nur Unterbaum indizieren. | Pfad muss bewusst gewählt sein. |
| `-o DATEI` | Ziel der Datenbank. | Schreibt Datei; bestehende DB kann ersetzt werden. |
| `-l 0` | Sichtbarkeitsprüfung in DB deaktivieren. | Nur für **private, geschützte** Test-DB. |
| `-l 1` | Sichtbarkeitsprüfung aktivieren. | Wirksamkeit hängt auch von Besitzer/Rechten ab. |
| `-e PFADE` | Ausschlusspfade ergänzen. | Syntax implementierungsspezifisch. |
| `-v` | Gefundene Pfade ausgeben. | Kann sensible Namen offenlegen. |
| `--debug-pruning` | Filterentscheidungen anzeigen. | Nur Diagnose. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Isolierte eigene Pfade vorbereiten

```bash
uebung="$(mktemp -d -t netmon-updatedb-XXXXXX)"
chmod 700 "$uebung"
mkdir "$uebung/quelle"
printf 'Eigene Testnotiz\n' > "$uebung/quelle/notiz.txt"
```

### Schritt 2: Nur eigene Dateinamen erfassen (theoretisch)

```bash
updatedb -l 0 -U "$uebung/quelle" -o "$uebung/test.db"
chmod 600 "$uebung/test.db"
```

`-U` begrenzt den Baum, `-o` verlegt die Datenbank in den eigenen Ordner. `-l 0` ist **nur** vertretbar, weil der Ordner auf den eigenen Nutzer begrenzt ist. Dieser Befehl wurde nicht ausgeführt.

### Schritt 3: Metadaten kontrollieren

```bash
ls -l -- "$uebung/test.db"
```

Ob der private DB-Aufbau mit der tatsächlich installierten `updatedb`-Variante funktioniert, ist ein **Prüfpunkt**.

## 6. Typische Anwendungsfälle

**Schnelle Dateinamenssuche:** `locate` nutzt den Index. **Private Projektindizes:** Begrenzte Testdatenbank für eigene Pfade. **Fehlersuche:** Ausschlussregeln in `updatedb.conf` prüfen, statt das gesamte System ungeplant neu zu scannen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Aufbau liest viele Pfadnamen, verbraucht I/O und schreibt eine Datenbank. Fehlkonfiguration kann Pfade offenlegen; besonders `-l 0` und zu weit offene DB-Rechte sind riskant. Indexdaten können veraltet sein. Systemweite Aufrufe können Root beziehungsweise dedizierte Dienstrechte benötigen. Keine echten Systemscans als Dokumentationstest.

## 8. Häufige Fehler

| Problem | Ursache | Maßnahme |
| --- | --- | --- |
| `updatedb` fehlt | Andere Distribution / Paket. | Variante bestimmen. |
| `-l` unbekannt | Andere Implementierung. | Lokale Manpage prüfen. |
| Treffer fehlen | Ausschluss, Rechte, veralteter Index. | `updatedb.conf` und Zeitpunkt prüfen. |
| DB nicht lesbar | Besitzer-/Dateirechte. | Private DB nur für eigenen Nutzer. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst `command -v updatedb` und die zugehörige Manpage ansehen. Systemweite Datenbank nicht manuell aktualisieren, wenn ein Timer zuständig ist. Private Indizes nur in `0700`-Ordnern und mit restriktiven Rechten speichern.

**Prüfstand:** Debian-plocate-Manpage 1.1.23 am 2026-11-13 gelesen; keine lokale Version und kein Indexlauf geprüft. **Prüfpunkt:** Konkrete `updatedb`-Implementierung im Zielsystem vor Übernahme der Optionen feststellen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `plocate`, `locate` | Datenbank abfragen. |
| `find` | Dateisystem direkt durchsuchen. |
| `stat` | Existenz eines gefundenen Pfads prüfen. |
| `systemctl` | Timerstatus nur bei Admin-Auftrag untersuchen. |

**Ausgangseintrag:** `source_record` 205 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
