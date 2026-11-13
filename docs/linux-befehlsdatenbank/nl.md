---
id: "nl"
name: "nl"
command: "nl"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "nl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 631
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# nl – Zeilen mit definierter Nummerierung ausgeben

## 1. Kurzbeschreibung

nl nummeriert logische Textzeilen nach gewählten Regeln.

## 2. Was macht der Befehl?

Standardmäßig werden im Textkörper nur nichtleere Zeilen nummeriert. Abschnittstrenner können logische Seiten bilden und den Zähler zurücksetzen. Für einen einfachen durchgehenden Übungsfall wird -ba ausdrücklich gewählt.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/nl.1.html)

## 3. Syntax

```text
nl [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -b a | Alle Körperzeilen nummerieren |
| -w ZAHL | Breite des Zahlenfelds |
| -s TEXT | Trenner |
| -v ZAHL | Startwert |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins\n\nzwei\n' > own.txt
nl -ba -w 1 -s : own.txt > result.txt
printf '1:eins\n2:\n3:zwei\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Auch die eigene Leerzeile erhält mit -ba eine Nummer. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Lesbare Zeilennummern mit ausdrücklich gewählter Breite, Anfangszahl und Trennung erzeugen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Logische Seitentrenner und Formatierung vor maschineller Weiterverarbeitung beachten. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Leerzeilen haben keine Nummer | Für alle Körperzeilen -b a wählen |
| Zähler beginnt erneut | Logische Seitentrenner können die Nummerierung zurücksetzen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cat | Einfache Nummerierung mit -n |
| wc | Newlines zählen |
| sed | Zeilen auswählen |

Ausgangsdatensatz 631 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
