---
id: "cat"
name: "cat"
command: "cat"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "cat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 622
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# cat – Dateien hintereinander ausgeben

## 1. Kurzbeschreibung

cat verbindet Dateiinhalte in der angegebenen Reihenfolge auf der Standardausgabe.

## 2. Was macht der Befehl?

Ohne Datei oder bei - liest cat die Standardeingabe. Die normale Ausgabe fügt zwischen Dateien keine zusätzlichen Zeilen ein. -n nummeriert alle, -b nur nichtleere Zeilen und hat Vorrang.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cat.1.html)

## 3. Syntax

```text
cat [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n | Alle Ausgabezeilen nummerieren |
| -b | Nur nichtleere Zeilen |
| -A | Steuerzeichen sichtbar darstellen |
| -s | Mehrere Leerzeilen zusammenfassen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins\n' > a.txt
printf 'zwei\n' > b.txt
cat a.txt b.txt > joined.txt
printf 'eins\nzwei\n' > expected.txt
cmp joined.txt expected.txt
cat joined.txt
```

### Schritt 3: Ergebnis einordnen

Die Ausgabedatei enthält beide eigenen Zeilen in Reihenfolge; cmp prüft die Bytes. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine Textdateien zusammenführen oder Steuerzeichen mit -A sichtbar untersuchen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Binärdaten nicht blind auf Terminals ausgeben. cat ist weder Editor noch sichere Parsergrenze. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Leerzeilen erscheinen unnummeriert | Mit -b werden nur nichtleere Zeilen nummeriert, auch zusammen mit -n |
| Dateien laufen zusammen | cat ergänzt zwischen Dateien kein fehlendes Zeilenende |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| tac | Datensätze in umgekehrter Reihenfolge |
| nl | Konfigurierbare Zeilennummerierung |
| less | Interaktive Anzeige |

Ausgangsdatensatz 622 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
