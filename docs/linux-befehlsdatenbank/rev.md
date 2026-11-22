---
id: "rev"
name: "rev"
command: "rev"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "rev"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 633
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# rev – Zeichen innerhalb jeder Zeile umkehren

## 1. Kurzbeschreibung

rev kehrt die Zeichenfolge einzelner Zeilen um, nicht die Reihenfolge der Zeilen.

## 2. Was macht der Befehl?

Das Werkzeug hält jede bearbeitete Zeile intern vor. Sehr lange Zeilen können deshalb viel Speicher beanspruchen. Zeichenverarbeitung hängt von Locale und Implementierung ab; die Übung verwendet nur ASCII.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/rev.1.html)

## 3. Syntax

```text
rev [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| ohne Option | Jede Zeile umkehren |
| --help | Lokale Optionen |
| --version | Implementierungsversion |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'abc\ndef\n' > own.txt
LC_ALL=C rev own.txt > result.txt
printf 'cba\nfed\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Die zwei Zeilen behalten ihre Reihenfolge, ihre drei Zeichen werden jeweils umgekehrt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einfache zeilenweise Zeichenumkehr durchführen; bei nicht-ASCII-Zeichen die konkrete Locale und Implementierung prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Kein allgemeiner Unicode-Graphemumkehrer; kombinierende Zeichen können andere Erwartungen erfordern. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Wörter bleiben rückwärts | rev kehrt Zeichen pro Zeile um, nicht die Reihenfolge ganzer Zeilen |
| Lange Zeile benötigt viel Speicher | Das Werkzeug puffert die jeweils zu verarbeitende Zeile |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| tac | Zeilen- beziehungsweise Datensatzfolge umkehren |
| tr | Zeichen übersetzen |
| fold | Zeilenbreite begrenzen |

Ausgangsdatensatz 633 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
