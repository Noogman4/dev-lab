---
id: "uniq"
name: "uniq"
command: "uniq"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "uniq"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 684
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# uniq – Nur benachbarte gleiche Zeilen zusammenfassen

## 1. Kurzbeschreibung

uniq vergleicht aufeinanderfolgende Zeilen und fasst gleiche Gruppen zusammen.

## 2. Was macht der Befehl?

Gleiche Zeilen an getrennten Stellen bleiben getrennt. Für globales Deduplizieren wird oft zuerst sortiert; dadurch ändert sich aber die Reihenfolge. -c zählt Gruppengrößen, -d zeigt wiederholte Gruppen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/uniq.1.html)

## 3. Syntax

```text
uniq [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c | Gruppengröße |
| -d | Nur wiederholte Gruppen |
| -u | Nur einmalige Gruppen |
| -i | Groß-/Kleinschreibung ignorieren |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'a\na\nb\na\n' > own.txt
uniq own.txt > result.txt
printf 'a\nb\na\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Das letzte a bleibt erhalten, da es nicht an die erste a-Gruppe grenzt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Benachbarte Zeilengruppen zählen oder auswählen; globale Deduplizierung und Erhalt der ursprünglichen Reihenfolge gesondert planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Vorheriges Sortieren ist eine fachliche Änderung der Reihenfolge. Eingabeformat und Vergleichsoptionen bewusst wählen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Gleiche Zeile bleibt mehrfach | Nur unmittelbar benachbarte gleiche Zeilen bilden eine Gruppe |
| Reihenfolge geht verloren | Ein vorgeschaltetes sort ordnet die Daten tatsächlich neu |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sort | Gleiche Werte gruppieren |
| comm | Zwei sortierte Listen |
| awk | Bedingte Verarbeitung |

Ausgangsdatensatz 684 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
