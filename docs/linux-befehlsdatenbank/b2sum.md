---
id: "b2sum"
name: "b2sum"
command: "b2sum"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "b2sum"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 647
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# b2sum – BLAKE2b-Prüfsummen erzeugen und prüfen

## 1. Kurzbeschreibung

b2sum berechnet standardmäßig eine BLAKE2b-Prüfsumme mit 512 Bit.

## 2. Was macht der Befehl?

Ein gespeichertes Manifest kann spätere Byteänderungen erkennen, wenn das Manifest selbst vertrauenswürdig ist. Eine Prüfsumme ist weder Verschlüsselung noch Signatur. -l wählt eine zulässige Bitlänge; unterschiedliche Längen sind unterschiedliche Prüfformen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/b2sum.1.html)

## 3. Syntax

```text
b2sum [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c DATEI | Manifest prüfen |
| -l BITS | Digestlänge |
| --status | Nur Rückgabestatus |
| --strict | Ungültige Manifestzeilen als Fehler |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eigener Inhalt\n' > own.txt
b2sum own.txt > own.b2
b2sum -c own.b2
printf 'veraendert\n' > own.txt
if b2sum --status -c own.b2; then exit 1; fi
printf 'Aenderung erkannt\n'
```

### Schritt 3: Ergebnis einordnen

Erst besteht der eigene unveränderte Inhalt die Prüfung; danach wird die absichtliche Änderung erkannt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Ein eigenes vertrauenswürdiges Manifest erstellen und anschließend unveränderten sowie absichtlich veränderten Inhalt prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Manifeste können Pfade auf fremde Dateien enthalten. Keine unbekannten Manifestlisten prüfen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Datei wird nicht gefunden | Manifestpfade werden im aktuellen Arbeitskontext ausgewertet |
| Gleicher Inhalt hat anderen Digest | Gewählte BLAKE2b-Ausgabelänge und tatsächliche Bytes vergleichen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sha256sum | Andere Digestfamilie |
| cksum | CRC und Länge |
| cmp | Direkter Bytevergleich |

Ausgangsdatensatz 647 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
