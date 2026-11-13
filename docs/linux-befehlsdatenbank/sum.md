---
id: "sum"
name: "sum"
command: "sum"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "sum"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 682
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# sum – Historische Dateisummen und Blockzahlen verstehen

## 1. Kurzbeschreibung

sum berechnet einfache BSD- oder System-V-Prüfsummen samt Blockzahl.

## 2. Was macht der Befehl?

Die Verfahren sind nicht kryptografisch. -r verwendet BSD und 1024-Byte-Blöcke, -s System V und 512-Byte-Blöcke. Die Blockzahl ist eine aufgerundete Ausgabegröße und keine Dateisystembelegung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sum.1.html)

## 3. Syntax

```text
sum [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -r | BSD-Verfahren |
| -s | System-V-Verfahren |
| --version | Implementierung feststellen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf abc > own.txt
sum -s own.txt > result.txt
grep -q '^294 1 ' result.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Für die drei eigenen ASCII-Bytes liefert die System-V-Variante 294 und einen 512-Byte-Ausgabeblock. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Historische einfache Prüfsummen mit dem ausdrücklich gewählten BSD- oder System-V-Verfahren verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht als Schutz gegen absichtliche Manipulation verwenden. Algorithmus und Blockeinheit immer mit angeben. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Andere Blockzahl als erwartet | -r zählt aufgerundete 1024-Byte-, -s 512-Byte-Blöcke |
| Werte stimmen trotz unterschiedlicher Daten | Die einfache Prüfsumme ist kein kollisionssicherer Inhaltsbeweis |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cksum | CRC mit Bytezahl |
| sha256sum | Kryptografischer Digest |
| wc | Bytezahl direkt |

Ausgangsdatensatz 682 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
