---
id: "mawk"
name: "mawk"
command: "mawk"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "mawk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 666
reviewed_at: "2026-11-13"
locally_checked_version: "mawk 1.3.4 20240123"
---

# mawk – Text mit der Mawk-Implementierung bearbeiten

## 1. Kurzbeschreibung

mawk ist eine eigenständige Awk-Implementierung.

## 2. Was macht der Befehl?

Die Grundsprache verarbeitet Datensätze mit Mustern und Aktionen. GNU-Erweiterungen sind nicht automatisch verfügbar. -W version ist eine implementierungsspezifische Versionsabfrage; andere awk-Programme können andere Optionen verwenden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://manpages.debian.org/testing/mawk/mawk.1.en.html)

## 3. Syntax

```text
mawk [OPTIONEN] 'PROGRAMM' [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -F TRENNER | Feldtrennung |
| -v NAME=WERT | Vorabwert |
| -f DATEI | Programmdatei |
| -W version | Mawk-Version |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'Anna 2\nBert 5\n' > own.txt
mawk '$2 > 3 { print $1 }' own.txt > result.txt
printf 'Bert\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Eine feste Regel wählt nur den eigenen Datensatz mit Wert über 3. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Portable Awk-Grundregeln mit der konkret benannten Mawk-Implementierung anwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Awk-Code kann system(), Umleitungen und externe Prozesse nutzen. Diese Wege sind nicht Teil des Tests. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| GNU-Funktion unbekannt | Mawk und Gawk sind verschiedene Implementierungen |
| Feldvergleich überrascht | Eingabefelder und erwartete numerische beziehungsweise textuelle Bedeutung prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** mawk 1.3.4 20240123. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| awk | Generischer Programmname |
| gawk | GNU-Implementierung |
| cut | Einfache Feldauswahl |

Ausgangsdatensatz 666 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
