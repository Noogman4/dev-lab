---
id: "tac"
name: "tac"
command: "tac"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "tac"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 637
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# tac – Zeilenreihenfolge umkehren

## 1. Kurzbeschreibung

tac gibt Datensätze in umgekehrter Reihenfolge aus.

## 2. Was macht der Befehl?

Standardtrenner ist das Zeilenende, das zum vorhergehenden Datensatz gehört. Fehlt das letzte Zeilenende, kann die optische Zusammenstellung überraschen. -s wählt einen anderen Trenner; -r behandelt ihn als regulären Ausdruck.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tac.1.html)

## 3. Syntax

```text
tac [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -s TRENNER | Datensatzgrenze |
| -b | Trenner an Folgedatensatz binden |
| -r | Trenner als Regex |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins\nzwei\ndrei\n' > own.txt
tac own.txt > result.txt
printf 'drei\nzwei\neins\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Die drei eigenen abgeschlossenen Zeilen erscheinen in umgekehrter Reihenfolge. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eine bekannte Datensatzfolge rückwärts ausgeben; einen abweichenden Trenner ausdrücklich angeben.

## 7. Risiken, Nebenwirkungen und Vorsicht

tac kehrt keine Zeichen innerhalb einer Zeile um. Eingabedateien werden bei normaler Ausgabe nicht umgeschrieben. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zeilen scheinen verklebt | Ein fehlendes letztes Newline und die Bindung des Trenners berücksichtigen |
| Zeichenfolge bleibt unverändert | tac kehrt Datensatzreihenfolge um, nicht Zeichen innerhalb einer Zeile |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cat | Normale Verkettung |
| rev | Zeichen je Zeile umkehren |
| sort | Vergleichsbasierte Umordnung |

Ausgangsdatensatz 637 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
