---
id: "split"
name: "split"
command: "split"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "split"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 681
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# split – Eine Datei in neue Teile zerlegen

## 1. Kurzbeschreibung

split schreibt Teile einer Eingabe in mehrere Ausgabedateien.

## 2. Was macht der Befehl?

Ohne Größenoption gelten typischerweise 1000 Zeilen pro Teil. -b teilt nach Bytes und kann Zeichen oder logische Datensätze trennen. -l hält Zeilen als Einheiten. Namen ergeben sich aus Präfix und Suffix.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/split.1.html)

## 3. Syntax

```text
split [OPTIONEN] [EINGABE [PRÄFIX]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -b MENGE | Bytegrenze |
| -l ZAHL | Zeilengrenze |
| -d | Numerische Suffixe |
| -a ZAHL | Suffixlänge |
| --filter=BEFEHL | Programm je Teil starten, aktive Ausführung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf abcdef > own.bin
split -b 3 own.bin part-
printf abc > expected.bin
cmp part-aa expected.bin
cat part-aa part-ab > joined.bin
cmp own.bin joined.bin
printf 'Eigene Teile bytegleich zusammengesetzt\n'
```

### Schritt 3: Ergebnis einordnen

Zwei Teile zu drei Bytes werden in bekannter Reihenfolge zusammengefügt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Große Textfolgen in einer kleinen eigenen Übung nach festen Zeilenmengen aufteilen und geordnet rekonstruieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausgabedateien können vorhandene Namen überschreiben. Nur neuer eigener Ordner; keine Filterprozesse und keine großen Dateien. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zeichen wird mitten im UTF-8-Code geteilt | -b begrenzt Bytes, für vollständige Zeilen -l verwenden |
| Teilnamen kollidieren | Eigenes neues Präfix und ausreichende Suffixlänge wählen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| csplit | Nach Mustern aufteilen |
| cat | Geordnete Teile zusammensetzen |
| wc | Teilgrößen bestimmen |

Ausgangsdatensatz 681 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
