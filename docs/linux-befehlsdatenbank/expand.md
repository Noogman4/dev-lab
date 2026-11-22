---
id: "expand"
name: "expand"
command: "expand"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "expand"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 624
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# expand – Tabulatoren an Tabstopps in Leerzeichen umsetzen

## 1. Kurzbeschreibung

expand ersetzt Tabulatoren durch passende Leerzeichen.

## 2. Was macht der Befehl?

Ein Tab ist keine konstante Zahl Leerzeichen: Die aktuelle Spaltenposition bestimmt den Abstand zum nächsten Tabstopp. Standardmäßig liegen Stopps acht Spalten auseinander. -i beschränkt Umwandlung auf den Anfangsbereich.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/expand.1.html)

## 3. Syntax

```text
expand [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -t ZAHL | Abstand der Tabstopps |
| -i | Nur anfängliche Tabs |
| --help | Implementierungshilfe |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'a\tb\n' > own.txt
expand -t 4 own.txt > result.txt
printf 'a   b\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Nach a ergänzt der Tab drei Leerzeichen bis zum nächsten Vierer-Stopp. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einrückungen vor der Anzeige vereinheitlichen, wenn die Tabstoppbreite ausdrücklich feststeht.

## 7. Risiken, Nebenwirkungen und Vorsicht

Layoutänderungen können Quelltext oder tabgetrennte Daten fachlich verändern. Kein In-place-Modus im Beispiel. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zu viele Leerzeichen | Tabstopps sind Spaltenpositionen, keine feste Ersatzlänge |
| Späterer Tab bleibt erhalten | Mit -i werden nur anfängliche Tabs umgewandelt |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| unexpand | Leerraum durch Tabs ersetzen |
| od | Tabbytes erkennen |
| cat | Steuerzeichen anzeigen |

Ausgangsdatensatz 624 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
