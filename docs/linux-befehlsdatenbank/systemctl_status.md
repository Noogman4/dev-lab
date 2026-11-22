---
id: "systemctl_status"
name: "systemctl status"
command: "systemctl status"
category: "Systemd Aufgaben"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd Aufgaben", "systemctl status"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 586
reviewed_at: "2026-11-13"
locally_checked_version: "systemctl vorhanden; Statusabfrage nicht ausgeführt"
---

# systemctl status – Unitstatus als Momentaufnahme lesen

## 1. Kurzbeschreibung

systemctl status zeigt einen für Menschen gedachten Laufzustand und gegebenenfalls letzte Journaleinträge.

## 2. Was macht der Befehl?

Loaded, Active und Unit-File-Status beschreiben unterschiedliche Ebenen. active (exited) kann für eine Oneshot-Unit ohne dauerhaften Prozess korrekt sein. Status ist keine stabile Maschinenschnittstelle; für gezielte Felder eignet sich show. Die Abfrage kann Unitmetadaten in den Manager laden, startet den Dienst aber nicht als start-Aktion.

Quelle, am 2026-11-13 gelesen: Lokal gelesenes Systemd-255-Handbuch und CLI-Hilfe; [systemctl-Statusreferenz](https://man7.org/linux/man-pages/man1/systemctl.1.html)

## 3. Syntax

```text
systemctl [OPTIONEN] status UNIT
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --no-pager | Keine Seitendarstellung starten. |
| --full | Namen nicht abkürzen. |
| -n 0 | Logausschnitt unterdrücken. |
| --user | Benutzerunitkontext. |
| show -p ActiveState | Alternative für gezielte Eigenschaftsauswertung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemctl --no-pager --full -n 0 status TEST.service
```

Die unausgeführte Abfrage würde Status ohne Journalausschnitt zeigen. Ein Nichtnullstatus kann einen inaktiven oder fehlenden Zustand ausdrücken; die konkrete Diagnose wäre zusätzlich zu lesen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Laufzustände interpretieren; Statusanzeige vom Anwendungs-Gesundheitstest unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Prozessnamen, Pfade und Logs können vertraulich sein. Status 0 allein beweist keine funktionierende Anwendung. Kein echter Manager oder Journalbestand wurde dafür abgefragt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 3 | Häufig Unit nicht aktiv; nicht automatisch Syntaxfehler. |
| active (exited) | Unittyp und RemainAfterExit prüfen. |
| Manager fehlt | Vorhandenes systemctl ist kein Systemd-Bootnachweis. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** systemctl vorhanden; Statusabfrage nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl show | Eigenschaften gezielt. |
| journalctl -u | Historische Logs. |
| ps | Prozessaufnahme separat. |

Ausgangsdatensatz 586 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
