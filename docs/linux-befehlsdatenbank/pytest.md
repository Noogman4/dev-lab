---
id: "pytest"
name: "pytest"
command: "pytest"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "pytest"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 521
reviewed_at: "2026-11-13"
locally_checked_version: "pytest 7.4.4 unter Python 3.12.3"
---

# pytest – Python-Tests gezielt ausführen

## 1. Kurzbeschreibung

pytest sammelt Python-Tests und führt sie aus. Auch die Sammlung kann bereits Python-Code laden.

## 2. Was macht der Befehl?

Testdateien, conftest.py und Plugins sind ausführbarer Code. Der Standardaufruf durchsucht Verzeichnisse; eine explizite Testdatei begrenzt die Auswahl. -k filtert Namen, eine Node-ID mit :: bezeichnet einen konkreten Test. Bestandene Tests belegen nur die geprüften Fälle, keine allgemeine Fehlerfreiheit.

Quelle, am 2026-11-13 gelesen: [pytest: Aufruf und Testauswahl](https://docs.pytest.org/en/stable/how-to/usage.html)

## 3. Syntax

```text
python3 -m pytest [OPTIONEN] [TESTPFAD[::TESTNAME]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -q | Kompakte Ausgabe. |
| -x | Nach dem ersten Fehlschlag stoppen. |
| -k AUSDRUCK | Tests anhand von Namen beziehungsweise Schlüsselwörtern auswählen. |
| --collect-only | Nur sammeln; Imports und Plugins können trotzdem laufen. |
| -p no:cacheprovider | pytest-Cacheplugin abschalten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'def test_split_preserves_words():
    assert "eins zwei".split() == ["eins", "zwei"]
' > test_sample.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider test_sample.py
printf 'Eigenen Test gezielt ausgefuehrt
'
```

### Schritt 3: Ergebnis einordnen

Ein eigener kleiner Verhaltenstest wird in einem neuen Ordner ohne automatisch geladene Drittplugins ausgeführt. Das Ergebnis ist ein bestandener Test; keine fremde Testsammlung wurde dabei gestartet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Funktionen durch Erwartungen absichern; einen Fehlerfall reproduzieren; die Testauswahl im Review nachvollziehbar machen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Tests können Netzwerk-, Datei- oder Systemaktionen auslösen. Plugin-Autoload-Abschaltung macht unbekannten Testcode nicht sicher. Keine Tests pauschal in fremden Verzeichnissen starten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 5 | Keine Tests gesammelt; ist kein erfolgreicher Funktionstest. |
| Importfehler | Interpreter, Pfade und Abhängigkeiten prüfen. |
| Status 1 | Mindestens ein Test fehlgeschlagen; Assertion und Ursache untersuchen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** pytest 7.4.4 unter Python 3.12.3. Praktisch geprüft: Eine eigene Testdatei ausgeführt; Plugin- und komplexe Fixturefälle offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mypy | Statische Typen prüfen. |
| ruff | Lintregeln. |
| venv | Interpreterumgebung trennen. |

Ausgangsdatensatz 521 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
