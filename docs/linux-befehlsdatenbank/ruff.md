---
id: "ruff"
name: "ruff"
command: "ruff"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "ruff"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 523
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Ruff-Funktionsprüfung offen"
---

# ruff – Python-Code mit Ruff prüfen

## 1. Kurzbeschreibung

Ruff bietet Lintprüfung und Formatierung als getrennte Unterbefehle.

## 2. Was macht der Befehl?

ruff check meldet Regelverletzungen; mit --fix werden Dateien geändert. ruff format schreibt normalerweise formatierten Code. Konfiguration kann aus pyproject.toml, ruff.toml oder .ruff.toml stammen. Gewählte Regeln, Version und Dateiauswahl bestimmen, was tatsächlich geprüft wird. Ruff ist lokal nicht vorhanden.

Quelle, am 2026-11-13 gelesen: [Ruff-Linter](https://docs.astral.sh/ruff/linter/), [Ruff-Konfiguration und CLI](https://docs.astral.sh/ruff/configuration/)

## 3. Syntax

```text
ruff check [OPTIONEN] DATEI
ruff format [OPTIONEN] DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| check | Lintanalyse; ohne --fix keine beabsichtigte Quelltextänderung. |
| --select F | Ausgewählte Regelfamilie prüfen. |
| --isolated | Automatische Konfiguration ignorieren. |
| --no-cache | Cache nicht verwenden. |
| --fix | Automatisch korrigieren; Review erforderlich. |
| format --check | Format nur prüfen, nicht schreiben. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ruff check --isolated --no-cache --select F EIGENE_DATEI.py
```

Das unausgeführte Muster begrenzt die Regeln auf die F-Familie und vermeidet Projektkonfiguration und Cache. Es würde keinen vollständigen Qualitätsnachweis liefern.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Unbenutzte Namen und typische Fehler finden; Lint- und Formatprüfung getrennt aufbauen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unsafe-Fixes können Verhalten verändern. Auch sichere Korrekturen vor Übernahme ansehen. Eine bestandene Lintprüfung ersetzt weder Typprüfung noch Tests. Kein Programm nachinstalliert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 1 | Regelverletzungen gefunden, nicht automatisch Werkzeugfehler. |
| Unerwartete Regeln | Konfigurationssuche und Versionsstand prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Ruff-Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| black | Python-Formatierung. |
| mypy | Typanalyse. |
| pytest | Ausführung von Tests. |

Ausgangsdatensatz 523 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
