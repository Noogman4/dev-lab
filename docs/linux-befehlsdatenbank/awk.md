---
id: "awk"
name: "awk"
command: "awk"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "awk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 646
reviewed_at: "2026-11-13"
locally_checked_version: "awk -> mawk 1.3.4 20240123"
---

# awk – Datensätze mit Awk-Feldregeln verarbeiten

## 1. Kurzbeschreibung

awk ist eine Textverarbeitungssprache mit Muster-Aktions-Regeln.

## 2. Was macht der Befehl?

$0 bezeichnet den Datensatz, $1 das erste Feld, NF die Feldzahl. Standardfeldtrennung fasst üblichen Leerraum zusammen. Der Name awk kann auf verschiedene Implementierungen zeigen; lokal ist es mawk. Ein Awk-Programm ist Code, kein passives Suchmuster.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/awk.1p.html)

## 3. Syntax

```text
awk [OPTIONEN] 'PROGRAMM' [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -F TRENNER | Feldseparator |
| -v NAME=WERT | Wert vor Programmbeginn setzen |
| -f DATEI | Awk-Programmdatei |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'Anna:2\nBert:5\n' > own.txt
awk -F: '{ total += $2 } END { print total }' own.txt > result.txt
test "$(cat result.txt)" = 7
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Die zweite Spalte zweier eigener Datensätze wird numerisch zu 7 summiert. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Felder eigener Textdatensätze auswählen oder anhand einer ausdrücklichen Bedingung ausgeben.

## 7. Risiken, Nebenwirkungen und Vorsicht

system(), Ausgabeumleitungen und Pipelines im Awk-Code können externe Aktionen auslösen. Nur fester selbst geschriebener Code. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Falsches Feld ausgewählt | Standardtrennung und explizites -F unterscheiden, Feldzählung beginnt bei 1 |
| Erweiterung wird abgelehnt | Die tatsächliche awk-Implementierung feststellen, hier lokal mawk |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** awk -> mawk 1.3.4 20240123. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mawk | Lokale Implementierung |
| gawk | GNU-Erweiterungen |
| cut | Einfache Feldauswahl |

Ausgangsdatensatz 646 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
