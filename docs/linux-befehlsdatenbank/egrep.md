---
id: "egrep"
name: "egrep"
command: "egrep"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "egrep"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 659
reviewed_at: "2026-11-13"
locally_checked_version: "GNU grep 3.11; historischer Wrapper"
---

# egrep – Veralteten Egrep-Namen einordnen

## 1. Kurzbeschreibung

egrep ist der historische Aufruf für grep mit erweiterten regulären Ausdrücken.

## 2. Was macht der Befehl?

GNU empfiehlt grep -E; der historische Name kann eine Warnung ausgeben und ist nicht überall vorhanden. Klammern und Alternation gehören zum erweiterten Muster. Shellquoting und Regexsyntax sind zwei Auswertungsebenen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/grep.1.html)

## 3. Syntax

```text
egrep [OPTIONEN] MUSTER [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -i | Groß-/Kleinschreibung ignorieren |
| -n | Zeilennummern |
| -v | Nicht passende Zeilen |
| grep -E | Bevorzugte moderne Schreibweise |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'rot\ngruen\nblau\n' > own.txt
egrep '^(rot|blau)$' own.txt > result.txt
printf 'rot\nblau\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Die historische lokale Form findet zwei eigene Zeilen. Der lokale Wrapper gab dabei keine Obsoleszenzwarnung aus; für neue Aufrufe bleibt grep -E die Empfehlung. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Ältere Skripte verstehen und deren erweiterte reguläre Ausdrücke dem modernen Aufruf grep -E zuordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Suchbäume nicht rekursiv durchlaufen. Treffer können vertrauliche Inhalte enthalten. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Historischer Name fehlt | Die ausdrücklich gleichgerichtete Form grep -E wählen |
| Muster wird von der Shell verändert | Regex mit geeigneten einfachen Anführungszeichen schützen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU grep 3.11; historischer Wrapper. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| grep | Moderne Form mit -E |
| fgrep | Historische feste Suche |
| rg | Andere Suchimplementierung |

Ausgangsdatensatz 659 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
