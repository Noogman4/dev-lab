---
id: "hexdump"
name: "hexdump"
command: "hexdump"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "hexdump"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 628
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# hexdump – Eigene Bytes als Hexdump lesen

## 1. Kurzbeschreibung

hexdump stellt Bytes in gewählten Zahlen- und Zeichenformaten dar.

## 2. Was macht der Befehl?

-C kombiniert hexadezimale Bytes mit einer ASCII-Näherung. Die linke Adresse ist ein Offset innerhalb der Eingabe, keine physische Speicheradresse. Mehrbyte-Zahlenformate können die Byteordnung des Systems berücksichtigen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/hexdump.1.html)

## 3. Syntax

```text
hexdump [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -C | Kanonisches Byteformat |
| -n ZAHL | Lesemenge begrenzen |
| -s OFFSET | Bytes überspringen |
| -v | Wiederholte Zeilen nicht zusammenfassen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'AB\000C' > own.bin
hexdump -C own.bin > result.txt
cat result.txt
grep -q '41 42 00 43' result.txt
```

### Schritt 3: Ergebnis einordnen

Die eigenen vier Bytes 41, 42, 00 und 43 werden sichtbar. Die ASCII-Spalte ersetzt das Nullbyte durch eine Darstellung, nicht durch Datenänderung. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Dateiköpfe und kleine Bytebereiche untersuchen; Offsets und tatsächlich gelesene Länge festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Hexdump kann Geheimnisse lesbar machen. Keine Geräte oder Prozessspeicher als Eingabe verwenden. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Stern statt weiterer Zeilen | Gleiche Blöcke werden ohne -v zusammengefasst |
| Zahlen scheinen vertauscht | Mehrbyteformate und Byteordnung von der Einzelbyteansicht unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| od | Explizite Zahlentypen |
| xxd | Hexdump und Rückumwandlung |
| strings | Druckbare Zeichenfolgen |

Ausgangsdatensatz 628 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
