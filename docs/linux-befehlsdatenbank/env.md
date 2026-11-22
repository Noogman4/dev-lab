---
id: "env"
name: "env"
command: "env"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "env"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 540
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# env – Umgebung eines Kindbefehls gezielt setzen

## 1. Kurzbeschreibung

env kann Umgebungsvariablen anzeigen oder mit einer veränderten Umgebung einen Befehl starten.

## 2. Was macht der Befehl?

NAME=WERT vor dem Befehlsnamen verändert die Umgebung dieses Starts und nicht rückwirkend die Elternshell. Ohne Befehl zeigt env die resultierende Umgebung an. -i beginnt mit leerer Umgebung; benötigte Programmpfade und Variablen müssen dann bewusst feststehen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: GNU coreutils `env --help`; [Handbuchverweis](https://www.gnu.org/software/coreutils/manual/html_node/env-invocation.html) (GNU-Onlineabruf gestört)

## 3. Syntax

```text
env [OPTIONEN] [NAME=WERT ...] [BEFEHL [ARGUMENTE]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -i | Mit leerer Umgebung beginnen. |
| -u NAME | Variable für diesen Start entfernen. |
| -C VERZEICHNIS | GNU-Option für Arbeitsverzeichnis des Starts. |
| -0 | Umgebung mit NUL-Trenner ausgeben. |
| -S TEXT | GNU-Splitting etwa für Shebang-Zeilen; keine normale Shellinterpretation. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -i LESSON_VALUE=wort /usr/bin/printenv LESSON_VALUE > result.txt
test "$(cat result.txt)" = wort
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Ein einzelner eigener Wert wird ohne geerbte Umgebung an printenv übergeben. Es werden keine fremden Umgebungsvariablen ausgegeben. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Reproduzierbare Kindumgebungen vorbereiten; einzelne Variablen für einen Aufruf entfernen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine leere Umgebung ist keine Sandbox. Der gestartete Befehl behält Benutzerrechte. Vollständige env-Ausgaben können Tokens und Kennwörter enthalten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Programm nicht gefunden | Bei leerer Umgebung ausdrücklichen Programmpfad verwenden. |
| Elternshell unverändert | Kindumgebung wirkt nicht rückwärts. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Ein eigener Wert mit -i geprüft; weitere Startmodi und fremde Umgebungen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| export | Variable für spätere Kinder markieren. |
| printenv | Ausgewählte Umgebungswerte lesen. |
| unset | Variable der aktuellen Shell entfernen. |

Ausgangsdatensatz 540 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
