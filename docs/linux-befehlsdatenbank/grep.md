---
id: "grep"
name: "grep"
command: "grep"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "grep"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 662
reviewed_at: "2026-11-13"
locally_checked_version: "GNU grep 3.11"
---

# grep – Zeilen nach bewusst gewählter Mustersprache suchen

## 1. Kurzbeschreibung

grep filtert Eingabezeilen anhand eines Musters.

## 2. Was macht der Befehl?

-F ist Literalsuche, -E erweitert die Regexsprache. Status 0 bedeutet Treffer, 1 kein Treffer, 2 einen Fehler. -q kann früh enden; Rückgabestatus und Diagnose müssen gemeinsam betrachtet werden. Das fehlerhaft zitierte lokale Indexbeispiel wurde nicht übernommen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/grep.1.html)

## 3. Syntax

```text
grep [OPTIONEN] -e MUSTER [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -F | Fester Text |
| -E | Erweiterte Regex |
| -n | Zeilennummern |
| -e MUSTER | Muster eindeutig als Option |
| -v | Auswahl umkehren |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'INFO gut\nERROR defekt\n' > own.txt
grep -n -F -e ERROR own.txt > result.txt
printf '2:ERROR defekt\n' > expected.txt
cmp result.txt expected.txt
if grep -F -e NICHTDA own.txt; then code=0; else code=$?; fi
test "$code" -eq 1
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Trefferzeile samt Nummer und der erwartete Status 1 beim Nichttreffer werden geprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Bekannte eigene Textdateien nach festen Zeichenfolgen oder bewusst gewählter Regexsprache durchsuchen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Rekursion kann fremde Logs und Geheimnisse lesen. Nur einzelne eigene Dateien verwendet. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 1 trotz lesbarer Datei | Kein Treffer ist ein eigenes Ergebnis, kein Lesefehler |
| Muster beginnt mit Minus | Es ausdrücklich mit -e als Muster übergeben |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU grep 3.11. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| rg | Rekursive Suche mit Ignoreregeln |
| awk | Feldabhängige Bedingungen |
| sed | Zeilenauswahl und Bearbeitung |

Ausgangsdatensatz 662 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
