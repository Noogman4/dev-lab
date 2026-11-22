---
id: "join"
name: "join"
command: "join"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "join"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 664
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# join – Sortierte Datensätze über einen Schlüssel verbinden

## 1. Kurzbeschreibung

join verbindet Zeilen zweier Dateien anhand gleicher Feldwerte.

## 2. Was macht der Befehl?

Beide Eingaben müssen zum gewählten Schlüssel nach derselben Locale sortiert sein. Standard ist Feld 1 mit Leerraumtrennung. Mehrere gleiche Schlüssel können mehrere Kombinationen erzeugen; dies ist keine automatische Eindeutigkeitsprüfung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/join.1.html)

## 3. Syntax

```text
join [OPTIONEN] DATEI1 DATEI2
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -1 FELD | Schlüssel links |
| -2 FELD | Schlüssel rechts |
| -t ZEICHEN | Trenner |
| -a NUMMER | Nicht verbundene Zeilen zusätzlich |
| --check-order | Sortierung prüfen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'a Anna\nb Bert\n' > names.txt
printf 'a 2\nb 5\n' > values.txt
LC_ALL=C join --check-order names.txt values.txt > result.txt
printf 'a Anna 2\nb Bert 5\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Zwei eigene eindeutige Schlüssel verbinden Name und Zahl. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zwei einfache eigene Tabellen über einen bekannten Feldschlüssel verbinden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht sortierte Daten und doppelte Schlüssel können fachlich falsche Erwartungen erzeugen. Kein CSV-Quotingparser. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Schlüssel wird nicht verbunden | Sortierung, ausgewähltes Feld und denselben Trenner prüfen |
| Zu viele Ergebniszeilen | Mehrere identische Schlüssel können mehrere Kombinationen erzeugen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sort | Schlüsselordnung vorbereiten |
| paste | Positionsweise statt schlüsselbasiert verbinden |
| comm | Sortierte ganze Zeilen vergleichen |

Ausgangsdatensatz 664 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
