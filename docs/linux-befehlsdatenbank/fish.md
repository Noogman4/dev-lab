---
id: "fish"
name: "fish"
command: "fish"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "fish"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 544
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Fish-Syntax und Ausführung offen"
---

# fish – Fish als eigenständige Shell verwenden

## 1. Kurzbeschreibung

fish ist eine interaktive Shell mit eigener Skriptsprache; sie ist kein austauschbarer Bash-Interpreter.

## 2. Was macht der Befehl?

Befehlsaufruf, Konfiguration und History lassen sich beim Start steuern. -N unterdrückt Konfigurationsdateien, -P historischen Zugriff. Ein mit -c übergebener Text wird wirklich als Fish-Code ausgeführt. Ein Bash-Syntaxcheck bestätigt keine Fish-Syntax. Fish fehlt lokal.

Quelle, am 2026-11-13 gelesen: [Fish: offizielle Startoptionen](https://fishshell.com/docs/current/cmds/fish.html)

## 3. Syntax

```text
fish [OPTIONEN] [DATEI [ARGUMENTE]]
fish -c CODE [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c CODE | Fish-Code ausführen; weitere Argumente in $argv. |
| -N | Keine Konfigurationsdateien lesen. |
| -P | Privater Modus ohne alte oder neue History. |
| -n | Fish-Syntax prüfen statt ausführen. |
| --version | Programmversion anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
fish -N -P -c 'printf "%s\n" wort'
```

Dies ist eine unausgeführte Fish-Leseübung. Sie würde einen bekannten Text ausgeben. Es wird weder eine vorhandene Fish-Sitzung verändert noch eine Login-Shell umgestellt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Shellunterschiede verstehen; ein eigenes Fish-Skript vor Einsatz prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Skripte und Konfiguration können beliebigen Code ausführen. Private History ist keine Ausführungsisolation. Keine Shell installiert und kein Benutzerprofil geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bash-Code scheitert | Fish-Sprache statt POSIX/Bash-Sprache verwenden. |
| Option fehlt | Installierte Fish-Version mit Referenz abgleichen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Fish-Syntax und Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| bash | Andere Shellsprache. |
| zsh | Weitere Shell. |
| sh | POSIX-Shellschnittstelle. |

Ausgangsdatensatz 544 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
