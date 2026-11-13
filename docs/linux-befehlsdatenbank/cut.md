---
id: "cut"
name: "cut"
command: "cut"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "cut"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 655
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# cut – Felder nach einem einfachen Trenner auswählen

## 1. Kurzbeschreibung

cut wählt festgelegte Bytes, Zeichen oder getrennte Felder aus Zeilen.

## 2. Was macht der Befehl?

Feldzählung beginnt bei 1. Standardfeldtrenner ist Tab; -d setzt einen einzelnen anderen Trenner. Zeilen ohne Trenner werden ohne -s gewöhnlich unverändert ausgegeben. cut ist kein Parser für zitierte CSV-Felder.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cut.1.html)

## 3. Syntax

```text
cut AUSWAHLOPTION [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -f LISTE | Felder |
| -d ZEICHEN | Trenner |
| -s | Zeilen ohne Trenner weglassen |
| -b LISTE | Bytes, kann Multibytezeichen teilen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'Anna:2\nBert:5\n' > own.txt
cut -d : -f 2 own.txt > result.txt
printf '2\n5\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Das zweite Feld jedes eigenen Datensatzes wird exakt geprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Aus einfachen delimitergetrennten Daten bestimmte Felder ausgeben, wenn deren Grammatik keine zitierte CSV-Struktur benötigt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Byteauswahl und Zeichenwahl sind bei Multibytecodierung nicht automatisch gleich. Strukturierte CSV besser mit passendem Parser bearbeiten. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zeile ohne Trenner bleibt vollständig | Ohne -s wird sie gewöhnlich unverändert ausgegeben |
| Zitierter CSV-Wert wird zerteilt | cut interpretiert keine CSV-Zitierung oder eingebetteten Trenner |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| awk | Bedingte Feldverarbeitung |
| paste | Felder positionsweise kombinieren |
| join | Datensätze anhand eines Schlüssels verbinden |

Ausgangsdatensatz 655 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
