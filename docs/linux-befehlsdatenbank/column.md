---
id: "column"
name: "column"
command: "column"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "column"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 623
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# column – Einfache Felder als Tabelle darstellen

## 1. Kurzbeschreibung

column formatiert Listen oder getrennte Felder für eine lesbare Tabellenansicht.

## 2. Was macht der Befehl?

-t aktiviert Tabellenmodus, -s definiert Eingabetrenner. Das Werkzeug ist kein vollwertiger CSV-Parser für zitierte Felder mit eingebetteten Trennern. Bildschirmbreite und neuere Farbkonfiguration können Darstellung beeinflussen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/column.1.html)

## 3. Syntax

```text
column [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -t | Tabellenmodus |
| -s ZEICHEN | Eingabetrenner |
| -o TEXT | Ausgabetrenner |
| -N NAMEN | Spaltennamen, lokale Version beachten |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'Name:Zahl\nAnna:2\n' > own.txt
column -t -s : -o ' / ' own.txt > result.txt
cat result.txt
grep -q 'Anna' result.txt
```

### Schritt 3: Ergebnis einordnen

Name und Zahl werden als zwei Felder dargestellt. Geprüft ist der einfache Trennerfall, keine CSV-Zitierlogik. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einfache getrennte Daten für Menschen ausrichten; das strukturierte Original für weitere Verarbeitung erhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausrichtung ist Präsentation, keine Garantie maschinenlesbarer Struktur. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zitierte CSV-Felder zerfallen | column -s behandelt Trenner, nicht die vollständige CSV-Grammatik |
| Tabelle wirkt verschoben | Tabs, Ausgabetrenner und verfügbare Breite unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cut | Einfache Feldauswahl |
| paste | Zeilen nebeneinander verbinden |
| awk | Feldabhängige Verarbeitung |

Ausgangsdatensatz 623 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
