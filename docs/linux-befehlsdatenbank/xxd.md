---
id: "xxd"
name: "xxd"
command: "xxd"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "xxd"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 643
reviewed_at: "2026-11-13"
locally_checked_version: "xxd 2023-10-25"
---

# xxd – Hexdarstellung erzeugen und zurückwandeln

## 1. Kurzbeschreibung

xxd kann Bytes als Hexdump darstellen und eine passende Darstellung wieder in Bytes zurückwandeln.

## 2. Was macht der Befehl?

-p erzeugt einfachen Hextext ohne Adress- und Zeichenspalte. -r -p dekodiert dieses Format. Der Rückweg ist ein Schreibvorgang und nicht bloß eine andere Anzeige. Klassische Dumpformate enthalten zusätzlich Offsetinformationen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://manpages.debian.org/bookworm/xxd/xxd.1.en.html)

## 3. Syntax

```text
xxd [OPTIONEN] [EINGABE [AUSGABE]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p | Einfacher Hextext |
| -r | Rückumwandlung |
| -l ZAHL | Bytebegrenzung |
| -s OFFSET | Startoffset |
| -g ZAHL | Bytegruppierung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'AB\000C' > own.bin
xxd -p own.bin > own.hex
xxd -r -p own.hex > back.bin
cmp own.bin back.bin
cat own.hex
```

### Schritt 3: Ergebnis einordnen

Die vier eigenen Bytes durchlaufen Hin- und Rückweg; cmp bestätigt identische Bytes. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine eigene Bytes hexadezimal darstellen und bei passender Formatwahl zurückwandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Dumps können unerwartete Daten und Offsets enthalten. Rückwandlung nur in ein neues eigenes Ziel, keine Geräte und keine vorhandenen Binärdateien. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Rückwandlung ergibt unerwartete Bytes | Normales Dumpformat und mit -p erzeugtes Plainformat passend rückwandeln |
| Vorhandenes Ziel enthält Restdaten | Rückwandlungsmodus und Schreibziel nicht ungeprüft als vollständiges Ersetzen verstehen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** xxd 2023-10-25. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| od | Zahlentypen auswählen |
| hexdump | Kanonische Byteansicht |
| cmp | Roundtrip bytegenau vergleichen |

Ausgangsdatensatz 643 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
