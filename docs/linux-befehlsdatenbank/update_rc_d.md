---
id: "update_rc_d"
name: "update-rc.d"
command: "update-rc.d"
category: "Systemd & Dienste"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd & Dienste", "update-rc.d"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 579
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Runlevelverknüpfungen nicht angefasst"
---

# update-rc.d – Debian-SysV-Startlinks verwalten

## 1. Kurzbeschreibung

update-rc.d verwaltet Start- und Stopverknüpfungen von SysV-Init-Skripten auf Debian-Systemen.

## 2. Was macht der Befehl?

Die Links betreffen Runlevelabläufe und sind vom aktuellen Dienstprozess getrennt. Das Werkzeug nutzt Abhängigkeitsinformationen aus dem LSB-Kopf des Init-Skripts. defaults respektiert vorhandene Konfiguration; willkürliches Entfernen und Neuaufbauen ist kein neutraler Test.

Quelle, am 2026-11-13 gelesen: [Debian init-system-helpers: update-rc.d-Handbuch](https://manpages.debian.org/bookworm/init-system-helpers/update-rc.d.8.en.html)

## 3. Syntax

```text
update-rc.d DIENST defaults
update-rc.d DIENST disable oder enable [RUNLEVEL ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| defaults | Vorgesehene Verknüpfungen einrichten. |
| defaults-disabled | Vorgaben in deaktivierter Form einrichten. |
| disable / enable | Startzuordnungen verändern. |
| remove | Verknüpfungen entfernen. |
| -f | Bestimmte Schutzprüfung bei remove übergehen; destruktiven Bereich nicht vergrößern. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
update-rc.d TESTDIENST defaults
```

Der Musteraufruf würde reale Startlinks verwalten und wurde deshalb nicht ausgeführt. TESTDIENST ist kein vorhandenes oder neu angelegtes Dienstskript.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Ältere Debian-Paketkonfiguration verstehen; Startzuordnung von Laufzustand unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Links können Dienste beim Booten unerwartet starten oder auslassen. Nicht für systemd-Units ohne Prüfung dieselbe Wirkung annehmen. Keine rc-Verknüpfung oder Initdatei geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Missing LSB tags | Skriptmetadaten und Paketzugehörigkeit prüfen. |
| Keine Änderung bei defaults | Vorhandene bewusste Konfiguration kann respektiert werden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Runlevelverknüpfungen nicht angefasst. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| service | Aktuellen Dienst bedienen. |
| chkconfig | Andere SysV-Implementierung. |
| systemctl | Systemd-Verwaltung. |

Ausgangsdatensatz 579 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
