---
id: "jq"
name: "jq"
command: "jq"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "jq"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 665
reviewed_at: "2026-11-13"
locally_checked_version: "jq 1.7"
---

# jq – JSON strukturiert statt per Textmuster verarbeiten

## 1. Kurzbeschreibung

jq wertet JSON mit einer Filtersprache aus.

## 2. Was macht der Befehl?

Ein Filter kann null, einen oder mehrere Ausgabewerte erzeugen. -r gibt Zeichenketten ohne JSON-Zitierung aus. --arg übergibt einen Wert als Daten statt ihn in Filtercode einzubauen. -e erlaubt eine besondere Statusprüfung anhand des letzten Ergebnisses.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://jqlang.org/manual/)

## 3. Syntax

```text
jq [OPTIONEN] 'FILTER' [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -r | Rohe Zeichenketten |
| -e | Status nach Ergebnis |
| --arg NAME WERT | Stringparameter |
| -n | Ohne Eingabe einen Wert erzeugen |
| -c | Kompaktes JSON |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf '{"items":[{"name":"Anna","active":true},{"name":"Bert","active":false}]}\n' > own.json
jq -r '.items[] | select(.active == true) | .name' own.json > result.txt
printf 'Anna\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Nur der aktive eigene Eintrag wird strukturell ausgewählt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Strukturierte eigene JSON-Daten auswählen oder umformen und Datenparameter vom Filtercode trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Filter sind Code; fremde Module und komplexe Ausdrücke können Ressourcen beanspruchen. Keine echte Konfiguration gelesen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Filter erzeugt nichts | Ein Filter kann null Ergebnisse liefern, ohne dass JSON ungültig ist |
| Variable wird als Code interpretiert | Werte mit --arg übergeben und nicht in Filterquelltext einkleben |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** jq 1.7. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| yq | YAML-Werkzeuge mit unterschiedlichen Implementierungen |
| awk | Einfacher unstrukturierter Text |
| cat | Unveränderte JSON-Bytes anzeigen |

Ausgangsdatensatz 665 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
