---
id: "tr"
name: "tr"
command: "tr"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "tr"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 683
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# tr – Zeichen übersetzen oder löschen

## 1. Kurzbeschreibung

tr verarbeitet Standardeingabe anhand zweier Zeichenmengen.

## 2. Was macht der Befehl?

Es ist kein Regex-Ersetzer und nimmt normalerweise keine Dateinamen als Datenquelle entgegen. Zeichenklassen müssen vor Shellinterpretation zitiert werden. Multibyte-Verarbeitung ist implementationsabhängig; der Test bleibt bei ASCII und C-Locale.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tr.1.html)

## 3. Syntax

```text
tr [OPTIONEN] MENGE1 [MENGE2] < EINGABE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -d | Zeichen löschen |
| -s | Wiederholungen zusammenfassen |
| -c | Menge ergänzen |
| [:lower:] | Klasse für Kleinbuchstaben |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'abc123\n' > own.txt
LC_ALL=C tr -d '0-9' < own.txt > letters.txt
LC_ALL=C tr '[:lower:]' '[:upper:]' < letters.txt > result.txt
printf 'ABC\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Ziffern verschwinden und eigene Kleinbuchstaben werden groß. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

ASCII-Zeichenklassen in eigener Eingabe übersetzen, löschen oder wiederholte Zeichen zusammenfassen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Löschung ist irreversibel, wenn das Ergebnis Originaldaten ersetzt. Keine Unicode-Normalisierung daraus ableiten. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dateiname wird als Zeichenmenge behandelt | Eingabe über Standardeingabe umleiten, nicht als Dateinamenargument ergänzen |
| Klasse wird von der Shell erweitert | Zeichenklassen wie [:lower:] zitieren |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sed | Musterbasierte Ersetzung |
| awk | Feld- und Datensatzverarbeitung |
| iconv | Zeichencodierung konvertieren |

Ausgangsdatensatz 683 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
