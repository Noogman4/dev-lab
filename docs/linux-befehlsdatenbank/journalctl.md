---
id: "journalctl"
name: "journalctl"
command: "journalctl"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "journalctl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 599
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; reale und synthetische Journaldateien funktional ungeprüft"
---

# journalctl – Journalquellen, Filter und Änderungsoptionen unterscheiden

## 1. Kurzbeschreibung

journalctl liest gespeicherte Systemd-Journale und bietet daneben Verwaltungsfunktionen.

## 2. Was macht der Befehl?

Quelle, Zeitraum und Filter sollten vor einer Auswertung feststehen. --file wählt Journaldateien; das ist kein Import beliebiger Textlogs. -u und -f sind die gesonderten Aufgabenformen der Datensätze 581 und 580. Die sichtbare Datenmenge hängt von Aufbewahrung und Rechten ab.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Systemd-255-Programmhilfe `journalctl --help`; [Online-Journalhandbuch](https://man7.org/linux/man-pages/man1/journalctl.1.html)

## 3. Syntax

```text
journalctl [OPTIONEN] [FELD=WERT ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --file=PFAD | Ausgewählte binäre Journaldatei lesen. |
| --since / --until | Zeitraum begrenzen. |
| -b | Boot auswählen. |
| -n ZAHL | Letzte Einträge begrenzen. |
| -o json | Strukturierte Ausgabe. |
| --vacuum-time / --vacuum-size | Archivierte Journaldaten löschen; kein Lesemodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
journalctl --no-pager --file=EIGENE_TESTDATEI.journal -n 10 -o json
```

Das Muster setzt eine selbst bereitgestellte gültige Journaldatei voraus und bleibt unausgeführt. Eine normale Textdatei wäre kein Ersatz. Es wurde kein reales Journal exportiert oder als Fixture kopiert.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Logquellen und begrenzte Auszüge verstehen; strukturierte Ausgabe für spätere Analysen planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Logs können Geheimnisse enthalten. --rotate, --flush, --sync, --setup-keys und Vacuumoptionen haben aktive Wirkungen. Keine realen Journale gelesen, verändert oder gelöscht.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No journal files | Quelle fehlt oder ist nicht sichtbar; keinen Journaldienst starten. |
| Leerer Ausschnitt | Filter, Zeitraum und Rotation getrennt prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; reale und synthetische Journaldateien funktional ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| journalctl -u | Unitfilter. |
| journalctl -f | Fortlaufende Anzeige. |
| systemd-cat | Schreibender Journaltransport. |

Ausgangsdatensatz 599 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
