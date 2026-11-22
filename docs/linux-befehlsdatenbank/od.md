---
id: "od"
name: "od"
command: "od"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "od"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 632
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# od – Bytes ohne Textannahme darstellen

## 1. Kurzbeschreibung

od zeigt Daten in Oktal-, Hex- und weiteren Zahlenformaten.

## 2. Was macht der Befehl?

Der Standard ist eine Oktaldarstellung; -t wählt einen expliziten Typ. Ein-Byte-Hexformate vermeiden Mehrbyte-Endiannessverwechslungen. -An unterdrückt die Offsetadresse und verändert nicht den Dateiinhalt.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/od.1.html)

## 3. Syntax

```text
od [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -t x1 | Hexadezimale Einzelbytes |
| -A n | Keine Adresse |
| -N ZAHL | Lesemenge begrenzen |
| -j ZAHL | Bytes überspringen |
| -v | Wiederholungen vollständig |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'AB\000C' > own.bin
od -An -tx1 -v own.bin > result.txt
cat result.txt
grep -q '41 42 00 43' result.txt
```

### Schritt 3: Ergebnis einordnen

Die vier eigenen Bytes werden in explizitem Format geprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine Binärdaten ohne Terminalsteuerwirkung als ausdrücklich gewählte Zahlenform anzeigen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Geräte oder realen Speicherquellen lesen. Zahlenformat und Einheiten nie allein aus Bildschirmwerten ableiten. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ausgabe ist oktal | Den gewünschten Typ wie -t x1 ausdrücklich wählen |
| Mehrbytewert wirkt vertauscht | Byteordnung berücksichtigen oder Einzelbytes anzeigen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| hexdump | Kanonische kombinierte Ansicht |
| xxd | Hexdarstellung |
| cmp | Direkter Bytevergleich |

Ausgangsdatensatz 632 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
