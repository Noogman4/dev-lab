---
id: "mypy"
name: "mypy"
command: "mypy"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "mypy"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 518
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; keine mypy-Ausführung"
---

# mypy – Python-Typen statisch prüfen

## 1. Kurzbeschreibung

mypy analysiert Typinformationen in Python-Code, ohne das Programm als normalen Anwendungslauf auszuführen.

## 2. Was macht der Befehl?

Annotationen und importierte Typbeschreibungen bilden das Prüfmodell. Unannotierter Code und Any können die Aussagekraft begrenzen. Plugins sind ausführbarer Python-Code; auch Konfiguration und Cache sind keine neutralen Details. mypy fehlt lokal.

Quelle, am 2026-11-13 gelesen: [mypy: Kommandozeilenreferenz](https://mypy.readthedocs.io/en/stable/command_line.html)

## 3. Syntax

```text
mypy [OPTIONEN] DATEI oder VERZEICHNIS
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --strict | Bündel strenger Prüfungen; Umfang versionsabhängig. |
| --config-file DATEI | Konfiguration ausdrücklich wählen. |
| --config-file= | Automatische Konfigurationssuche abschalten. |
| -m MODUL | Ein Modul prüfen. |
| -p PAKET | Paket rekursiv prüfen. |
| --exclude MUSTER | Rekursive Dateisuche filtern; keine allgemeine Importsperre. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
mypy --config-file= EIGENE_DATEI.py
```

Das unausgeführte Muster würde eine eigene Datei ohne automatisch gefundene Projektkonfiguration prüfen. Ein späterer Test müsste mypy-Version, Abhängigkeiten und Cachezugriffe gesondert festhalten.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Falsche Argumenttypen früh finden; Schnittstellen mit Typannotationen absichern.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Garantie für Laufzeitfehlerfreiheit. Unbekannte Plugins und Konfiguration nicht laden. Fehler nicht pauschal durch ignore-missing-imports verstecken; dadurch sinkt die Prüftiefe.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Missing stubs | Passende Typinformationen und Interpreterumgebung prüfen. |
| Keine Fehler trotz Problem | Annotationsabdeckung und Any-Anteile untersuchen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; keine mypy-Ausführung. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pytest | Laufzeitverhalten testen. |
| ruff | Lintregeln. |
| black | Formatierung. |

Ausgangsdatensatz 518 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
