---
id: "systemctl"
name: "systemctl"
command: "systemctl"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemctl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 568
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Managerbetrieb praktisch offen"
---

# systemctl – Systemd-Units und ihre Zustände unterscheiden

## 1. Kurzbeschreibung

systemctl fragt den systemd-Manager ab und kann Units sowie Systemzustände verändern.

## 2. Was macht der Befehl?

Laufzustand und Installationszustand sind getrennt. list-units zeigt geladene Units; list-unit-files installierte Unitdateien. --user adressiert einen Benutzermanager, nicht automatisch einen gefahrlosen Kontext. Eine ausgewählte Aktion bestimmt, ob nur gelesen oder verändert wird.

Quelle, am 2026-11-13 gelesen: [Systemd: systemctl-Handbuch](https://man7.org/linux/man-pages/man1/systemctl.1.html); lokale vollständige CLI-Hilfe gelesen

## 3. Syntax

```text
systemctl [OPTIONEN] AKTION [UNIT ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| status UNIT | Momentaner Status für Menschen. |
| show UNIT | Eigenschaften für gezielte Auswertung. |
| is-active / is-enabled | Lauf- beziehungsweise Installationszustand prüfen. |
| --user | Benutzermanager wählen. |
| --no-pager | Pager vermeiden. |
| --dry-run | Nur für bestimmte Aktionen unterstützt; kein allgemeiner Schutz für start/stop. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemctl --no-pager show TEST.service -p ActiveState -p SubState
```

Das unausgeführte Muster würde zwei Eigenschaften abfragen. Es würde weder starten noch aktivieren, kann aber einen echten Managerkontakt erfordern.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Dienstdiagnosen klar auswählen; Unitdatei, Aktivierung und laufenden Prozess getrennt betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Start, Stop, Maskierung und Systemaktionen können Betrieb unterbrechen. --no-block bedeutet nur nicht warten, nicht nicht ausführen. Kein Managerkontakt zum Funktionstest und keine Unitänderung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| System not booted with systemd | Vorhandenes Programm bedeutet nicht vorhandenen Manager. |
| Unit not found | Exakten Namen, Unitart und Manager prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Managerbetrieb praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| journalctl | Protokolle. |
| systemd-cgls | Cgroup-Zuordnung. |
| systemd-run | Transiente Ausführung. |

Ausgangsdatensatz 568 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
