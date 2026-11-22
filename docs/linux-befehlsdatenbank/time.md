---
id: "time"
name: "time"
command: "time"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "time"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 509
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Time meldet Version UNKNOWN"
---

# time – Laufzeit und Ressourcenverbrauch messen

## 1. Kurzbeschreibung

time startet einen Befehl und misst dessen Ausführung. Shell-Schlüsselwort und externes GNU Time sind zu unterscheiden.

## 2. Was macht der Befehl?

Die verstrichene Zeit enthält Warten; user und sys erfassen verbrauchte CPU-Zeit im Benutzer- beziehungsweise Kernelmodus. Diese Werte messen verschiedene Dinge und müssen nicht addiert die reale Laufzeit ergeben. Für die hier beschriebenen GNU-Optionen wird ausdrücklich /usr/bin/time verwendet.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: GNU-Time-Programmhilfe `/usr/bin/time --help`; [Projektverweis](https://www.gnu.org/software/time/) (Onlineabruf fehlgeschlagen)

## 3. Syntax

```text
/usr/bin/time [OPTIONEN] BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p | Portables Format mit real, user und sys. |
| -o DATEI | Messwerte in Datei statt Standardfehler schreiben. |
| -a | Mit -o an Datei anhängen. |
| -v | Zusätzliche Ressourcenkennzahlen. |
| -f FORMAT | GNU-spezifisches Ausgabeformat. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
/usr/bin/time -p -o measurement.txt bash --noprofile --norc -c 'printf "Messlauf\n"'
cat measurement.txt
grep -q '^real ' measurement.txt
printf 'Messformat geprueft
'
```

### Schritt 3: Ergebnis einordnen

Der eigene kurze printf-Lauf ist abgeschlossen; die Messdatei enthält das portable Schema. Es wird keine Leistungszusage abgeleitet, da Auflösung und Systemlast die Werte beeinflussen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Programme vergleichbar vermessen; Wartezeit von CPU-Zeit unterscheiden; Messausgabe von Nutzdaten trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der gemessene Befehl wird tatsächlich ausgeführt und behält sämtliche Nebenwirkungen. Ausgabedateien können überschrieben werden. Keine produktiven Programme zur bloßen Messung starten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Option -o unbekannt | Möglicherweise Shell-time statt GNU Time verwendet. |
| Nutzdaten und Zeit gemischt | Standardausgabe und Standardfehler beziehungsweise -o unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU Time meldet Version UNKNOWN. Praktisch geprüft: Kurzer eigener Befehl mit -p/-o geprüft; Lastvergleiche und weitere Messgrößen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| times | Kumulierte Shell-CPU-Zeiten. |
| timeout | Laufzeit begrenzen statt messen. |
| type | Shell-Auflösung eines Namens prüfen. |

Ausgangsdatensatz 509 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
