---
id: "glances"
name: "glances"
command: "glances"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "glances"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 485
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; glances fehlt"
---

# glances – Monitoringmodus und Datenweitergabe ausdrücklich wählen

## 1. Kurzbeschreibung

glances ist ein erweiterbarer Ressourcenmonitor mit Terminal-, Server-, Web- und Exportmodi. Ein Start kann daher Daten sammeln, speichern oder über einen Listener anbieten.

## 2. Was macht der Befehl?

Plugins bestimmen, welche Ressourcen und externen Schnittstellen verwendet werden. Prozessfilter begrenzen die dargestellte Auswahl, nicht alle Datenzugriffe. CPU-Prozentwerte hängen vom Normalisierungsmodus ab; Netzwerkdarstellung kann bit/s oder Byte/s verwenden. Die aktuelle Referenz beschreibt Glances 4.5.8, lokal ist es nicht vorhanden.

Quelle, am 2026-11-13 gelesen: [Glances-Projekt: Kommandoreferenz](https://glances.readthedocs.io/en/latest/cmds.html)

## 3. Syntax

```text
glances [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-t SEKUNDEN` | Aktualisierungsintervall. |
| `-f REGEX` | Prozessanzeige filtern. |
| `--disable-plugin NAME` | Bestimmtes Plugin deaktivieren. |
| `--stdout FELDER` | Statistik an stdout statt normale Darstellung. |
| `--export MODUL` | Datenexport aktivieren, Ziel und Geheimnisse prüfen. |
| `-s`, `-w` | Server- beziehungsweise Webservermodus starten. |
| `-B ADRESSE` | Listener-Bindung festlegen. |
| `--disable-check-update` | Online-Versionsprüfung abschalten, kein allgemeiner Netzschutz. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
glances --disable-check-update -t 3
```

Das Muster startet hier nichts. Selbst ohne Versionsprüfung könnten Plugins, Exporte oder Konfiguration weitere Zugriffe auslösen. Drei Sekunden sind der Aktualisierungsabstand, keine Begrenzung der gesamten Laufzeit.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Messansichten verstehen:** Einheiten, Intervalle und Normalisierung benennen. **Betrieb planen:** Lokale Anzeige, Datenausgabe und Serverbetrieb getrennt freigeben.

## 7. Risiken, Nebenwirkungen und Vorsicht

TUI-Aktionen können Prozesse signalisieren oder Nice-Werte ändern. Web/API-/MCP-/Exportfunktionen können sensible Betriebsdaten offenlegen. Keine Listener, Browser, Plugins oder Exporte gestartet und keine Prozesse verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Daten fehlen | Plugin-/Rechte-/Plattformgrenze prüfen. |
| CPU-Werte anders als in anderem Tool | Normalisierung und Messintervall vergleichen. |
| Quiet als ungefährlich verstanden | -q betrifft die Oberfläche, nicht alle Erfassungs-/Netzwirkungen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; glances fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `htop` | Prozess-TUI. |
| `atop` | Intervall- und Rohprotokollmonitor. |
| `ps` | Gezielte Momentaufnahme. |

Ausgangsdatensatz 485 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
