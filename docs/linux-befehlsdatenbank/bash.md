---
id: "bash"
name: "bash"
command: "bash"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "bash"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 536
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# bash – Bash bewusst als Interpreter starten

## 1. Kurzbeschreibung

bash interpretiert Shellcode aus einer Datei, einer Zeichenfolge oder der Standardeingabe.

## 2. Was macht der Befehl?

Ein neuer Bash-Prozess hat einen eigenen Shellzustand. -c führt die übergebene Zeichenfolge wirklich aus. Der erste nachfolgende Argumentwert wird dabei $0, die weiteren werden $1 und folgende. Profile und BASH_ENV können Startcode beeinflussen; --noprofile und --norc allein deaktivieren BASH_ENV nicht.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: `bash --help` und `help set`; [GNU-Bash-Projektverweis](https://www.gnu.org/software/bash/) (Onlinehandbuch nicht abrufbar)

## 3. Syntax

```text
bash [OPTIONEN] [SKRIPT [ARGUMENTE]]
bash -c CODE NAME [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --noprofile | Login-Profile nicht lesen. |
| --norc | Interaktive bashrc nicht lesen. |
| -c CODE | Code ausführen. |
| -n | Syntax lesen, ohne normale Befehle auszuführen. |
| -x | Ausgeführte Befehle protokollieren; mögliche Geheimnisse. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc -c 'test "$0" = demo && test "$1" = wert && printf "Argumentzuordnung stimmt\n"' demo wert
```

### Schritt 3: Ergebnis einordnen

Die geprüfte Zeichenfolge verarbeitet nur bekannte Argumente. Der Parametername demo wird nicht als Dateiname ausgeführt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Bash-Skripte explizit ausführen; Argumentübergabe von Daten und Code unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Shellcode kann sämtliche Benutzeraktionen ausführen. Unbekannte Startdateien und Eingaben nicht übernehmen. -n ist keine Sicherheitsbewertung und bestätigt keine externen Programme.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Erstes Argument fehlt | Bei -c wird der erste zusätzliche Wert $0. |
| Skript funktioniert nur unter Bash | Bash-Erweiterungen nicht automatisch in sh verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener -c-Fall geprüft; interaktiver Start, Profile und fremde Skripte offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sh | Portabler Einstieg mit anderer Implementierung. |
| dash | Kleinere Shell. |
| source | Datei im selben Shellprozess. |

Ausgangsdatensatz 536 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
