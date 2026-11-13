---
id: "python3"
name: "python3"
command: "python3"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "python3"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 294
reviewed_at: "2026-11-13"
locally_checked_version: "CPython 3.12.3"
---

# python3 – Python-3-Skripte kontrolliert ausführen

## 1. Kurzbeschreibung

python3 startet einen Python-3-Interpreter. Skript-, Modul-, Standardinput- und Ausdrucksmodus führen Code aus. Eine separate Bytecodekompilierung prüft andere Eigenschaften als ein tatsächlicher Programmlauf.

## 2. Was macht der Befehl?

-m sucht ein Modul über den Importmechanismus und führt es als Programm aus; es verlangt einen Modulnamen ohne .py. Der normale Suchpfad kann Arbeits- oder Skriptverzeichnis und Benutzerpakete enthalten. -I reduziert diese Einflüsse, während -S zusätzlich die automatische site-Initialisierung unterdrückt. Diese Optionen begrenzen Import-/Startkontext und sind keine Betriebssystem-Sandbox. Python-3-Nebenversionsunterschiede bleiben relevant.

Quelle, am 2026-11-13 gelesen: [CPython-3.12-Aufrufhandbuch](https://docs.python.org/3.12/using/cmdline.html) und [py_compile](https://docs.python.org/3.12/library/py_compile.html)

## 3. Syntax

```text
python3 [OPTIONEN] SKRIPT [ARGUMENTE...]
python3 [OPTIONEN] -m MODUL [ARGUMENTE...]
python3 [OPTIONEN] -c CODE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version`, `-VV` | Versions- beziehungsweise ausführlichen Buildstand lesen. |
| `-I` | Isolierter Import-/Umgebungsmodus; eigene Nebenmodule im Skriptordner werden nicht automatisch gefunden. |
| `-S` | site nicht automatisch importieren. |
| `-B` | Implizite .pyc-Erzeugung unterdrücken; explizites py_compile kann dennoch schreiben. |
| `-m py_compile DATEI` | Quelltext in Bytecode kompilieren; schreibt Cachedatei. |
| `-u` | Standardausgaben ungepuffert betreiben. |
| `-O` | Optimierung kann assert entfernen; keine allgemeine Sicherheitsverbesserung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-294-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
python3 -I -S --version
cat > lernen.py <<'PYTHON'
wert = 6 * 7
print("Hallo Python3", wert)
PYTHON
python3 -I -S -m py_compile lernen.py
python3 -I -S -B lernen.py

```

### Schritt 3: Ergebnis auswerten

Die Kompilierung endete ohne Fehlermeldung und schrieb Bytecode im eigenen __pycache__-Ordner. Sie führte den normalen Inhalt von lernen.py nicht aus. Der anschließende getrennte Skriptstart gab Hallo Python3 42 aus. -B beim Start macht den zuvor ausdrücklich erzeugten Cache nicht rückgängig. Keine Projektmodule oder fremden Pakete wurden importiert. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Eigene Skripte entwickeln: Syntax-/Bytecodekontrolle und Laufzeitprüfung getrennt halten. Umgebungsfehler eingrenzen: Interpreter und Importsuche ausdrücklich festlegen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Pythoncode und importierte Module können jede zulässige Benutzeraktion ausführen. Auch -I und -S verhindern nicht Datei-, Prozess- oder Netzzugriffe durch gestarteten Code. Fremde Pickle-Dateien oder eval-Eingaben sind keine sicheren Daten. Keine Paketinstallation, Dienständerung oder Aktivierung einer realen Anwendung gehört zu diesem Beispiel. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| ModuleNotFoundError mit -I | Eigenen Importkontext gezielt planen; Schutz nicht reflexartig entfernen. |
| Syntaxprüfung erfolgreich, NameError | Kompilierung prüft keine vollständigen Laufzeitwerte. |
| Unerwarteter Cache trotz -B | Explizites py_compile schreibt Bytecode selbst. |
| Assert fehlt | -O kann Assertions entfernen; nicht als zwingende Eingabevalidierung verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** CPython 3.12.3. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `python` | Unversionierter Name mit distributionsabhängiger Zuordnung. |
| `python3-config` | C-Buildparameter der Installation. |
| `pytest` | Führt Tests und beim Sammeln Modulcode aus. |

Ausgangsdatensatz 294 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
