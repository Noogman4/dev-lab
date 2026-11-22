---
id: "python"
name: "python"
command: "python"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "python"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 293
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# python – Den unversionierten Python-Aufruf richtig einordnen

## 1. Kurzbeschreibung

python ist ein unversionierter Interpretername. Je nach Distribution und Umgebung kann er Python 3, historisch Python 2 oder gar kein Programm bezeichnen. Ein vorhandenes python3 beweist nicht, dass auch python verfügbar ist.

## 2. Was macht der Befehl?

PEP 394 beschreibt diese Unterschiede und die besondere Rolle virtueller Umgebungen. Dort soll python auf den Interpreter der Umgebung verweisen. PATH, Shebang und aktive Umgebung bestimmen, was tatsächlich startet. Für eindeutig Python-3-abhängige Programme ist außerhalb einer festgelegten Umgebung ein expliziter python3-Aufruf verständlicher. Optionen der aktuellen CPython-3-Dokumentation dürfen nicht ungeprüft auf einen älteren python-Interpreter übertragen werden.

Quelle, am 2026-11-13 gelesen: [Python-Projekt: PEP 394](https://peps.python.org/pep-0394/) und [CPython-3-Aufrufhandbuch](https://docs.python.org/3/using/cmdline.html)

## 3. Syntax

```text
python [INTERPRETEROPTIONEN] SKRIPT [ARGUMENTE...]
python -c CODE
python -m MODUL [ARGUMENTE...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version` / `-V` | Tatsächlichen Interpreterstand prüfen. |
| `-c CODE` | Code ausführen, nicht nur anzeigen. |
| `-m MODUL` | Importierbares Modul als Programm ausführen; ohne .py-Endung. |
| `-B` | Bei passenden CPython-Versionen implizites Bytecodeschreiben unterdrücken. |
| `-I` | CPython-3-Isolationsmodus ab 3.4; kein Dateisystem-/Netzsandboxing. |
| `-S` | Automatischen site-Import unterdrücken; Details versionsabhängig. |
| `-h` | Hilfe der tatsächlich gefundenen Variante lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-293-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
command -v python || exit 1
python --version
printf 'print("Hallo Python")
' > lernen.py
python lernen.py

```

### Schritt 3: Ergebnis auswerten

Das Muster würde zuerst den gefundenen Namen und die Version zeigen und erst dann das selbst geschriebene Skript starten. Die einfache print-Form ist absichtlich kein anspruchsvoller Versionstest. Hier existiert python nicht im PATH: Die Prüfung endet an der ersten Voraussetzung. Es wurde weder ein Alias noch ein systemweiter Symlink angelegt und kein python3-Test als python-Nachweis ausgegeben. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Portabilität prüfen: Interpretername und Sprachversion ausdrücklich festhalten. Virtuelle Umgebungen verstehen: Der unversionierte Name kann dort eine präzise Bedeutung haben, ohne die Systeminstallation zu ändern.

## 7. Risiken, Nebenwirkungen und Vorsicht

Interpreter führen Code und importierte Module mit Benutzerrechten aus. Ein fremder Arbeitsordner kann bei üblichen Suchpfaden Module einschleusen. Keine sudo-pip-Installation und keine Änderung des System-Python zur Lösung eines Namensproblems. PEP-Empfehlung ist kein Beweis über den lokalen Zustand. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| command not found | python kann absichtlich fehlen; dokumentierten Interpreter verwenden. |
| SyntaxError auf anderem Rechner | Version und Implementierung vergleichen. |
| ModuleNotFoundError | Paketumgebung des konkreten Interpreters prüfen. |
| Falscher Interpreter nach Aktivierung | PATH und Umgebung lesen, keine fremden Dateien überschreiben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `python3` | Expliziter Python-3-Aufruf. |
| `python3 -m venv` | Erzeugt eine eigene Umgebung; hier nicht ausgeführt. |
| `python3-config` | Buildparameter, kein Interpreterersatz. |

Ausgangsdatensatz 293 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
