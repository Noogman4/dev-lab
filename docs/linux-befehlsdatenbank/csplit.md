---
id: "csplit"
name: "csplit"
command: "csplit"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "csplit"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 654
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# csplit – Dateien anhand von Kontext in Teile schreiben

## 1. Kurzbeschreibung

csplit erzeugt mehrere Ausgabedateien an Zeilen- oder Mustergrenzen.

## 2. Was macht der Befehl?

Ein Zahlenmuster kopiert bis vor die bezeichnete Zeile. /REGEX/ trennt vor der passenden Zeile; Prozentmuster überspringen Bereiche. Standardnamen wie xx00 können mit bestehenden Dateien kollidieren.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/csplit.1.html)

## 3. Syntax

```text
csplit [OPTIONEN] DATEI MUSTER ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -f PRÄFIX | Ausgabename |
| -n ZAHL | Ziffernbreite |
| -s | Größenmeldungen unterdrücken |
| -k | Teile bei Fehler behalten |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins\nMARK\nzwei\n' > own.txt
csplit -s -f part- own.txt '/^MARK$/'
printf 'eins\n' > expected.txt
cmp part-00 expected.txt
cat part-00 part-01 > joined.txt
cmp own.txt joined.txt
cat joined.txt
```

### Schritt 3: Ergebnis einordnen

Der erste Teil endet vor MARK, der zweite enthält MARK und den Rest. Zusammensetzen ergibt die eigene Originaldatei. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einen eigenen strukturierten Text an bekannten Zeilen oder Mustern in benannte Teile zerlegen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Mehrere Dateien werden geschrieben. Nur im neuen privaten Ordner testen; Fehlerbehandlung kann bereits erzeugte Teile wieder entfernen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unerwartete oder leere Teildatei | Trennung erfolgt vor der passenden Zeile, nicht grundsätzlich danach |
| Teile fehlen nach Fehler | Fehlerbehandlung und -k zum bewussten Behalten unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| split | Nach festen Mengen aufteilen |
| sed | Bereiche auswählen |
| cat | Geordnete Teile zusammenführen |

Ausgangsdatensatz 654 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
