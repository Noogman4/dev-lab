---
id: "pipx"
name: "pipx"
command: "pipx"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "pipx"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 470
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; pipx fehlt"
---

# pipx – Python-CLI-Pakete getrennt von Projektbibliotheken

## 1. Kurzbeschreibung

pipx installiert Python-Anwendungen in eigenen virtuellen Umgebungen und stellt deren Startbefehle bereit. Diese Paketpfadtrennung ist keine Betriebssystemsandbox für ausgeführten Anwendungscode.

## 2. Was macht der Befehl?

Eine Anwendung und ihre Abhängigkeiten bilden eine verwaltete Umgebung. inject fügt Pakete in genau eine solche Umgebung ein, statt eine unabhängige Bibliothek für beliebige Projekte bereitzustellen. run kann temporär installieren und Code ausführen. Die aktuelle Dokumentation beschreibt auch neuere Backends und Ausgabeoptionen; ältere Versionen können abweichen.

Quelle, am 2026-11-13 gelesen: [PyPA/pipx: Übersicht](https://pipx.pypa.io/stable/) und [CLI-Referenz](https://pipx.pypa.io/stable/reference/cli.html)

## 3. Syntax

```text
pipx [--help|--version]
pipx {list|install|run|inject|upgrade|uninstall} [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list` | Verwaltete Anwendungen anzeigen. |
| `install` | Eigenes venv und Startverknüpfungen anlegen. |
| `run` | Temporäre Umgebung verwenden, gegebenenfalls herunterladen und ausführen. |
| `inject` | Zusätzliche Abhängigkeit in bestehendes App-venv. |
| `--python` | Interpreter auswählen, soweit vom Unterbefehl unterstützt. |
| `ensurepath` | Kann Shell-/PATH-Konfiguration ändern; kein reiner Statusbericht. |
| `uninstall` | Verwaltete Umgebung entfernen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
pipx list
```

Das Muster würde den pipx-Bestand anzeigen und ist nicht ausgeführt. Es ist weder pip list einer Projektumgebung noch ein Systempaketinventar. Eine fehlende Startverknüpfung und eine fehlende Anwendung sind getrennte Fehlerfälle.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**CLI-Umgebungen planen:** Anwendungen von Projektbibliotheken trennen. **Pfadfehler verstehen:** Verknüpfung und Interpreterumgebung gemeinsam prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installations-/Buildcode und gestartete Apps haben Benutzerrechte. Temporär bedeutet nicht wirkungslos; run kann Dateien und Netzwerk ansprechen. Pipx fehlt hier. Keine venvs, Startlinks, PATH-Einträge, Caches oder Benutzerkonfiguration verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Apps im Paket | Paket deklariert möglicherweise keine ausführbaren Entry Points. |
| Befehl fehlt im PATH | Verknüpfung und Suchpfad prüfen; ensurepath nicht ungefragt ausführen. |
| Abhängigkeit fürs Projekt fehlt | pipx-App-venv ist nicht die Projektumgebung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; pipx fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pip` | Pakete in einer ausgewählten Pythonumgebung. |
| `python3 -m venv` | Grundlage virtueller Paketumgebungen. |
| `uv` | Versionsabhängig möglicher pipx-Backend. |

Ausgangsdatensatz 470 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
