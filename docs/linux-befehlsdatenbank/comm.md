---
id: "comm"
name: "comm"
command: "comm"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "comm"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 653
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# comm – Sortierte Zeilenmengen vergleichen

## 1. Kurzbeschreibung

comm verteilt den Vergleich zweier sortierter Dateien auf drei Ausgabespalten.

## 2. Was macht der Befehl?

Spalte 1 enthält nur links, Spalte 2 nur rechts, Spalte 3 gemeinsame Zeilen. Beide Eingaben müssen nach denselben Locale-Regeln sortiert sein. Das Werkzeug ist kein unsortierter Mengenvergleich und keine automatische Dublettenbereinigung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/comm.1.html)

## 3. Syntax

```text
comm [OPTIONEN] DATEI1 DATEI2
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -1 | Erste Spalte unterdrücken |
| -2 | Zweite Spalte unterdrücken |
| -3 | Gemeinsame Spalte unterdrücken |
| --check-order | Sortierung prüfen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'a\nb\n' > a.txt
printf 'b\nc\n' > b.txt
LC_ALL=C comm --check-order -12 a.txt b.txt > common.txt
printf 'b\n' > expected.txt
cmp common.txt expected.txt
cat common.txt
```

### Schritt 3: Ergebnis einordnen

Mit -12 bleibt nur die gemeinsame Spalte; sie enthält b. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zwei sortierte Zeilenbestände in linke, rechte und gemeinsame Beiträge aufteilen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Sortierreihenfolge kann ein irreführendes Ergebnis erzeugen. Locale für Vorverarbeitung und Vergleich gleich setzen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Sortierwarnung | Beide Eingaben mit denselben Locale-Regeln sortieren |
| Mehr als eine Spalte erscheint | Spalten gezielt mit -1, -2 und -3 unterdrücken |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sort | Eingaben passend ordnen |
| uniq | Benachbarte gleiche Zeilen gruppieren |
| join | Nach Feldschlüsseln verbinden |

Ausgangsdatensatz 653 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
