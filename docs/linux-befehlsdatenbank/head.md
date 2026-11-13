---
id: "head"
name: "head"
command: "head"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "head"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 627
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# head – Den Anfang einer Datei begrenzt anzeigen

## 1. Kurzbeschreibung

head gibt ohne Mengenoption die ersten zehn Zeilen aus.

## 2. Was macht der Befehl?

-n zählt Zeilen, -c Bytes. Negative GNU-Mengenwerte bedeuten alle außer den letzten Elementen. Bei mehreren Dateien können Dateiköpfe erscheinen. Früh beendetes Lesen einer Pipeline kann beim Erzeuger SIGPIPE bewirken.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/head.1.html)

## 3. Syntax

```text
head [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n ZAHL | Zeilenanzahl |
| -c ZAHL | Byteanzahl |
| -q | Dateiköpfe unterdrücken |
| -v | Dateiköpfe erzwingen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins\nzwei\ndrei\n' > own.txt
head -n 2 own.txt > result.txt
printf 'eins\nzwei\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Genau die ersten zwei eigenen Zeilen werden verglichen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einen begrenzten Dateianfang betrachten; bei Binärdaten die Byteoption statt einer Zeilenannahme wählen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auszüge können sensible Daten enthalten und ersetzen keine Prüfung des restlichen Dokuments. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Pipeline-Erzeuger meldet Broken pipe | head kann seinen Bedarf decken und die Pipe früh schließen |
| Negativer Wert zeigt fast alles | Bei GNU head bedeutet -n -N alle außer den letzten N Zeilen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| tail | Dateiende oder Beginn ab Zeilennummer |
| sed | Ausgewählte Zeilenbereiche |
| wc | Gesamtmenge bestimmen |

Ausgangsdatensatz 627 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
