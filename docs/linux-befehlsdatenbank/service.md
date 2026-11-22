---
id: "service"
name: "service"
command: "service"
category: "Systemd & Dienste"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd & Dienste", "service"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 567
reviewed_at: "2026-11-13"
locally_checked_version: "Wrapper vorhanden; keine Dienstaktion ausgeführt"
---

# service – Distributionsabhängige Dienstschnittstelle verstehen

## 1. Kurzbeschreibung

service ruft auf Debian-Systemen ein Init-Skript auf oder leitet geeignete Aktionen an den Dienstmanager weiter.

## 2. Was macht der Befehl?

Der Wrapper bereinigt große Teile der Umgebung und setzt das Arbeitsverzeichnis. Unterstützte Aktionen hängen vom Zielskript beziehungsweise Manager ab. Eine gleichnamige systemd-Unit kann Vorrang vor einem Init-Skript haben. service allein beschreibt daher keinen universellen Dienstzustand.

Quelle, am 2026-11-13 gelesen: [Debian init-system-helpers: service-Handbuch](https://manpages.debian.org/bookworm/init-system-helpers/service.8.en.html)

## 3. Syntax

```text
service DIENST AKTION [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| status | Statusaktion des konkreten Ziels. |
| start / stop | Dienst tatsächlich aktivieren oder stoppen. |
| restart | Unterbrechung durch Neustart möglich. |
| --status-all | Viele SysV-Statusskripte ausführen; keine reine Dateiliste. |
| --help | Wrapperhilfe. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
service TESTDIENST status
```

Die Statusaktion wäre ein echter Aufruf des Zielskripts oder Managers. Sie wird hier nicht ausgeführt. TESTDIENST muss vor einem späteren Einsatz eindeutig aufgelöst werden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Ältere Debian-Anleitungen lesen; Wrapper und natives Init-System auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auch status kann Code eines lokalen Skripts ausführen. --status-all ruft viele Skripte auf. Keine Freigabe für Start/Stop durch eine zuvor gelesene Statusbeschreibung. Kein Dienst bedient.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unrecognized service | Name, Paket und Managerzuordnung prüfen. |
| Unterschiedliches Statusformat | Wrapper standardisiert nicht jede Zielausgabe. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Wrapper vorhanden; keine Dienstaktion ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl | Native systemd-Verwaltung. |
| rc-service | OpenRC. |
| update-rc.d | Debian-Startverknüpfungen. |

Ausgangsdatensatz 567 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
