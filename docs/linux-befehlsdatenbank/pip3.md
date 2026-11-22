---
id: "pip3"
name: "pip3"
command: "pip3"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "pip3"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 469
reviewed_at: "2026-11-13"
locally_checked_version: "pip3: pip 24.0, Python 3.12"
---

# pip3 – Python3-Bindung des Aufrufnamens prüfen

## 1. Kurzbeschreibung

pip3 ist gewöhnlich ein Starter für pip unter Python3. Er garantiert weder die gewünschte Python-Minorversion noch ein bestimmtes venv. Hier meldet er pip 24.0 für Python 3.12.

## 2. Was macht der Befehl?

Die interpretergebundene Form python3 -m pip macht die ausgewählte Python-Instanz deutlicher. Mehrere Pythoninstallationen können verschiedene Paketpfade verwenden. Ein eigener Hashvergleich prüft die lokale CLI-Funktion ohne Installation und ohne echten Paketbestand. Er zeigt keine allgemeine Gleichheit aller pip- und pip3-Starter auf anderen Rechnern.

Quelle, am 2026-11-13 gelesen: [PyPA: pip-Aufruf](https://pip.pypa.io/en/stable/cli/pip/), [hash](https://pip.pypa.io/en/stable/cli/pip_hash/) und [install](https://pip.pypa.io/en/stable/cli/pip_install/)

## 3. Syntax

```text
pip3 KOMMANDO [OPTIONEN]
python3 -m pip KOMMANDO [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version` | Version und Paketpfad zur Interpreterzuordnung. |
| `hash --algorithm sha256` | Digest einer lokalen Datei berechnen. |
| `show`, `list` | Pakete der gewählten Umgebung anzeigen. |
| `check` | Deklarierte Abhängigkeitskonsistenz, kein Anwendungstest. |
| `install --dry-run` | Planung kann Metadatenbuildcode benötigen; keine Sandbox. |
| `--no-index` | Indexsuche aus, direkte URLs nicht generell gesperrt. |
| `--user` | Benutzerinstallation, weiterhin echte Umgebungsänderung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-pip3-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'abc' > eigene-daten.txt
PIP_CONFIG_FILE=/dev/null pip3 --version
PIP_CONFIG_FILE=/dev/null pip3 --disable-pip-version-check --no-cache-dir hash --algorithm sha256 eigene-daten.txt
```

### Schritt 3: Ergebnis einordnen

Erwartet ist derselbe bekannte SHA-256-Digest der Bytes abc wie beim eigenständigen pip-Hashbeispiel. Die Datei ist Testmaterial, kein gültiges Distributionsarchiv. Hier sind beide lokalen Versionsangaben gleich; die Aufrufnamen werden trotzdem nicht allgemein als austauschbar erklärt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Mehrere Interpreter verwalten:** Exakte Bindung vor Projektaktionen klären. **Fehlerberichte präzisieren:** Programmversion und Pythonpfad gemeinsam nennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

pip3 ist kein Distributionspaketmanager und kein Befehl für automatische Systempython-Reparatur. Quelle/Buildbackends können Code ausführen. Keine Installation, Benutzersettingänderung oder Paketabfrage am echten Bestand; nur eigene Datei gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Modul nach Installation nicht importierbar | Interpreter/venv/Importname gesondert prüfen. |
| pip3 fehlt | python3 -m pip-Verfügbarkeit prüfen, nicht automatisch nachinstallieren. |
| Hash korrekt, Format falsch | Hash allein prüft weder Archivformat noch Herkunft. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** pip3: pip 24.0, Python 3.12. Praktisch geprüft: Eigene Drei-Byte-Datei mit pip3 hash gelesen; Digest und lokale Versionsbindung geprüft. Andere Interpreter, Installation, Buildcode und echte Paketumgebungen praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pip` | Gleiche Werkzeugfamilie, Starterbindung kann abweichen. |
| `python3` | Gewählter Interpreter. |
| `pipx` | CLI-Pakete in eigenen venvs. |

Ausgangsdatensatz 469 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
