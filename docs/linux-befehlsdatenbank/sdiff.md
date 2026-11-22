---
id: "sdiff"
name: "sdiff"
command: "sdiff"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "sdiff"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 673
reviewed_at: "2026-11-13"
locally_checked_version: "GNU diffutils 3.10"
---

# sdiff – Unterschiede nebeneinander darstellen

## 1. Kurzbeschreibung

sdiff vergleicht zwei Textdateien in nebeneinanderstehenden Spalten.

## 2. Was macht der Befehl?

Ohne -o ist es eine Vergleichsausgabe; mit -o wird eine interaktive Mergeauswahl mit Schreibziel gestartet. Breitenbegrenzung kann lange Inhalte verdecken. Wie bei diff ist Status 1 ein erkannter Unterschied, kein allgemeiner Werkzeugfehler.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sdiff.1.html)

## 3. Syntax

```text
sdiff [OPTIONEN] DATEI1 DATEI2
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -w ZAHL | Anzeigebreite |
| -s | Gemeinsame Zeilen ausblenden |
| -o DATEI | Interaktiver Merge ins Ziel |
| -W | Leerraum ignorieren, kann Unterschiede verdecken |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'links\n' > a.txt
printf 'rechts\n' > b.txt
if sdiff -w 50 a.txt b.txt > result.txt; then code=0; else code=$?; fi
test "$code" -eq 1
grep -q links result.txt
grep -q rechts result.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Der eigene Unterschied ist auf beiden Seiten sichtbar; interaktiver Merge und -o wurden nicht verwendet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zwei kleine Textfassungen nebeneinander beurteilen; der hier geprüfte Anzeigemodus schreibt keinen Merge.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine automatische Konfliktlösung aus Spaltenanzeige ableiten. Ausgabekürzung von echten Inhaltsverlusten unterscheiden. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zeilen erscheinen abgeschnitten | Gewählte Anzeigebreite begrenzt die Ansicht, Originalinhalt separat lesen |
| Programm wartet auf Eingabe | Mit -o wird eine interaktive Auswahl für ein Schreibziel gestartet |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| diff | Unified- statt Seitenansicht |
| diff3 | Drei Fassungen |
| cmp | Unformatierter Bytevergleich |

Ausgangsdatensatz 673 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
