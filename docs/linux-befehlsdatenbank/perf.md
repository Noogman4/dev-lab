---
id: "perf"
name: "perf"
command: "perf"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "perf"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 498
reviewed_at: "2026-11-13"
locally_checked_version: "Kein Messlauf; Starterdatei gelesen, keine ausgeführte perf-Version ermittelt"
---

# perf – Performancewerkzeuge mit versions- und rechteabhängiger Messung

## 1. Kurzbeschreibung

perf ist eine Familie von Linux-Analysewerkzeugen. Unterbefehle wie stat, record und report haben verschiedene Datenquellen und Nebenwirkungen. Das vorhandene /usr/bin/perf ist lokal zunächst ein Distributionsstarter.

## 2. Was macht der Befehl?

stat zählt Ereignisse, record zeichnet Samples auf und report wertet passende Aufzeichnungen aus. Ereignisverfügbarkeit hängt von Kernel, CPU/PMU, Virtualisierung und Rechten ab. Multiplexierte Zähler können skaliert sein; die tatsächlich gemessene Laufzeit muss berücksichtigt werden. Ein einzelner Messlauf beweist weder Repräsentativität noch eine Ursache.

Quelle, am 2026-11-13 gelesen: [Linux/perf: Übersicht](https://man7.org/linux/man-pages/man1/perf.1.html), [stat](https://man7.org/linux/man-pages/man1/perf-stat.1.html) und lokal gelesener Starter /usr/bin/perf

## 3. Syntax

```text
perf [GLOBALE_OPTIONEN] UNTERBEFEHL [ARGUMENTE]
perf stat [OPTIONEN] -- BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `stat -e EREIGNIS` | Bestimmtes Zählereignis auswählen. |
| `stat -p PID` | Vorhandenen Prozess beobachten; Ziel vorher eindeutig prüfen. |
| `stat -a` | Systemweite CPU-Erfassung, wesentlich breiterer Umfang. |
| `stat -r ANZAHL` | Zielkommando mehrfach ausführen; jede Wiederholung hat dessen Wirkungen. |
| `stat --null` | Keine Zähler starten; Zielkommando läuft trotzdem. |
| `stat -o DATEI` | Statistik in Datei schreiben. |
| `record`, `report` | Aufzeichnen und Auswerten sind getrennte Abläufe. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
perf stat --null -- /usr/bin/printf "Lerntext\n"
```

Das Muster wurde nicht ausgeführt. Es würde printf tatsächlich starten, aber keine Performancezähler eröffnen. Ein Null-Lauf wäre nur ein Ablauf-/Zeitmessfall, kein PMU-Nachweis. Der gelesene lokale Starter kann bei fehlendem kernelpassendem Werkzeug mit Status 2 abbrechen; daraus wurde kein Installationsauftrag gemacht.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Messungen planen:** Ereignisse, Zielumfang und Laufzeit festlegen. **Ergebnisse lesen:** Nicht unterstützte, nicht gezählte und hochgerechnete Werte unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Tracing-/Samplingdaten können sensible Ausführungspfade enthalten. Rechtebeschränkungen nicht mit perf_event_paranoid-, Capability- oder Mountänderungen umgehen. Keine Zähler eröffnet, Aufzeichnungen erzeugt, BPF-Programme geladen oder Prozesse angehängt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Passendes perf fehlt | Starter ist nicht das eigentliche Werkzeug; keine Pakete nachinstallieren. |
| Permission denied | Kernel-/Berechtigungsgrenze dokumentieren. |
| not supported/not counted | Ereignis-/Hardwaregrenze oder Messzeitproblem; kein Nullverbrauchsbeweis. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Kein Messlauf; Starterdatei gelesen, keine ausgeführte perf-Version ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `time` | Andere Laufzeit-/Ressourcensicht. |
| `ltrace` | Bibliotheksaufrufe, andere Beobachtungsebene. |
| `pidstat` | Intervallbezogene Prozessstatistik. |

Ausgangsdatensatz 498 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
