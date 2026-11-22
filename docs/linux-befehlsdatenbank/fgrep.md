---
id: "fgrep"
name: "fgrep"
command: "fgrep"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "fgrep"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 660
reviewed_at: "2026-11-13"
locally_checked_version: "GNU grep 3.11; historischer Wrapper"
---

# fgrep – Historischen Fgrep-Aufruf als Literalsuche verstehen

## 1. Kurzbeschreibung

fgrep ist die historische Form für grep -F.

## 2. Was macht der Befehl?

Punkt, Stern und Klammern im Muster werden als Text statt Regexoperatoren behandelt. Der ältere Programmname ist veraltet; grep -F beschreibt die Absicht direkt. Mehrere Muster und Optionsargumente bleiben dennoch zu zitieren.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/grep.1.html)

## 3. Syntax

```text
fgrep [OPTIONEN] FESTTEXT [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -x | Ganze Zeile vergleichen |
| -i | Groß-/Kleinschreibung ignorieren |
| -n | Zeilennummern |
| grep -F | Moderne Form |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'a.b\naxb\n' > own.txt
fgrep 'a.b' own.txt > result.txt
printf 'a.b\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Nur die eigene Zeile mit echtem Punkt passt. Eine eventuelle GNU-Obsoleszenzwarnung ist kein Funktionsfehler. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Ältere feste Suchmuster erkennen und mit grep -F ausdrücklich als Text behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Literal bedeutet nicht geheimnisfrei; Ausgaben können private Inhalte enthalten. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Punkt passt nur als Punkt | Das ist beabsichtigt: feste Suche statt regulärer Ausdruck |
| Historischer Name fehlt | Für neue Aufrufe grep -F verwenden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU grep 3.11; historischer Wrapper. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| grep | Moderne Form mit -F |
| egrep | Historische erweiterte Regexsuche |
| rg | Literale Suche mit -F |

Ausgangsdatensatz 660 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
