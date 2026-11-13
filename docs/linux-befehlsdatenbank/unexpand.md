---
id: "unexpand"
name: "unexpand"
command: "unexpand"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "unexpand"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 641
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# unexpand – Leerzeichen nach Tabstopps verdichten

## 1. Kurzbeschreibung

unexpand ersetzt geeignete Leerzeichenfolgen durch Tabulatoren.

## 2. Was macht der Befehl?

Standardmäßig wird anfänglicher Leerraum bearbeitet; -a erweitert den Bereich. Das Layout hängt von der vereinbarten Tabstoppbreite ab. Die Umwandlung ist nicht immer eine bytegenaue Umkehr von expand, weil unterschiedliche Eingaben gleich aussehen können.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/unexpand.1.html)

## 3. Syntax

```text
unexpand [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -a | Alle geeigneten Bereiche |
| -t ZAHL | Tabstoppabstand |
| --first-only | Nur anfängliche Bereiche |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf '    x\n' > own.txt
unexpand -t 4 own.txt > result.txt
printf '\tx\n' > expected.txt
cmp result.txt expected.txt
od -An -tx1 result.txt
```

### Schritt 3: Ergebnis einordnen

Die vier anfänglichen Leerzeichen werden bei Vierer-Tabstopps durch Byte 09 ersetzt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einrückung kompakter speichern, wenn das anschließende Anzeigeprogramm dieselbe Tabstoppbreite verwendet.

## 7. Risiken, Nebenwirkungen und Vorsicht

Tabs können in Datendateien Trennzeichen sein; eine optisch gleiche Anzeige belegt keine gleiche Struktur. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Layout passt nur in manchen Editoren | Erzeugte Tabs benötigen dieselben vereinbarten Tabstopps |
| Nicht jeder Leerraum wird ersetzt | Vorgabe bearbeitet den Anfangsbereich, -a erweitert die Auswahl |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| expand | Tabs in Leerzeichen umwandeln |
| od | Tabbytes nachweisen |
| column | Tabellarische Darstellung |

Ausgangsdatensatz 641 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
