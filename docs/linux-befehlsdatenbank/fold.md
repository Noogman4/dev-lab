---
id: "fold"
name: "fold"
command: "fold"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "fold"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 626
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# fold – Einzelne Zeilen auf eine Breite umbrechen

## 1. Kurzbeschreibung

fold bricht jede Eingabezeile nach einer Breitenregel um.

## 2. Was macht der Befehl?

Standardmäßig geht es um Darstellungsspalten; -b zählt Bytes. -s bevorzugt geeignete Leerstellen. Multibyte- und Steuerzeichenbehandlung muss zur installierten Version passen. Neuere Optionen nicht ungeprüft aus dem Onlinehandbuch übernehmen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/fold.1.html)

## 3. Syntax

```text
fold [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -w ZAHL | Breite einstellen |
| -b | Bytes zählen |
| -s | An Leerstellen umbrechen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'abcdefgh\n' > own.txt
LC_ALL=C fold -w 4 own.txt > result.txt
printf 'abcd\nefgh\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Der reine ASCII-Fall wird exakt nach vier Spalten geteilt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Lange einfache Textzeilen begrenzen und bewusst zwischen Spalten- und Bytebreite wählen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Umbruch verändert Datenstruktur. Byteumbrüche können mehrbytecodierte Zeichen zerlegen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Wort wird geteilt | Ohne -s muss fold keine Wortgrenze bevorzugen |
| UTF-8 wird beschädigt | Ein erzwungener Byteschnitt mit -b kann ein Mehrbytezeichen teilen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| fmt | Absatzorientierte Formatierung |
| wc | Byte- und Zeichenzahl |
| od | Bytegrenzen prüfen |

Ausgangsdatensatz 626 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
