---
id: "sort"
name: "sort"
command: "sort"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "sort"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 680
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# sort – Text nach ausdrücklich gewählter Ordnung sortieren

## 1. Kurzbeschreibung

sort ordnet Textzeilen nach Vergleichsregeln.

## 2. Was macht der Befehl?

Lexikalische, numerische und Versionssortierung sind verschieden. Locale beeinflusst die Ordnung. -k 2,2 begrenzt einen Schlüssel auf Feld 2; -k 2 reicht dagegen standardmäßig weiter. -u entfernt nach Vergleichsregeln gleiche Zeilen, nicht zwingend nur byteidentische.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sort.1.html)

## 3. Syntax

```text
sort [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n | Numerische Ordnung |
| -k FELD,FELD | Begrenzter Schlüssel |
| -t ZEICHEN | Feldtrenner |
| -s | Stabile Reihenfolge bei gleichem Schlüssel |
| -u | Gleiche Vergleichswerte zusammenfassen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf '10\n2\n1\n' > own.txt
LC_ALL=C sort -n own.txt > result.txt
printf '1\n2\n10\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Die eigenen Zahlen werden numerisch statt lexikalisch geordnet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Textdaten nach ausdrücklich festgelegten Schlüsseln und einer passenden Locale ordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Große Sortierungen können temporäre Dateien und erheblichen Speicher benötigen. Nur kleine eigene Daten verwendet. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| 10 steht vor 2 | Textvergleich und numerisches -n unterscheiden |
| Schlüssel reicht zu weit | -k 2,2 begrenzt auf Feld 2, -k 2 reicht weiter |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| uniq | Benachbarte gleiche Zeilen |
| comm | Sortierte Bestände vergleichen |
| join | Nach sortiertem Schlüssel verbinden |

Ausgangsdatensatz 680 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
