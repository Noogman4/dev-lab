---
id: "systemd_run"
name: "systemd-run"
command: "systemd-run"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-run"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 576
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; transiente Units und Ausführung offen"
---

# systemd-run – Programme in transienten Units ausführen

## 1. Kurzbeschreibung

systemd-run erstellt vorübergehende Units und kann darin Programme tatsächlich starten.

## 2. Was macht der Befehl?

Transient bedeutet zur Laufzeit erzeugt, nicht nebenwirkungsfrei. Service- und Scope-Modus unterscheiden sich in Start- und Verwaltungskontext. Mit --user wird ein anderer Manager adressiert, aber weiterhin echte Arbeit ausgeführt. Timer-, Socket- oder Pfadoptionen können zusätzliche Aktivierungswege erzeugen.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-run-Handbuch](https://man7.org/linux/man-pages/man1/systemd-run.1.html)

## 3. Syntax

```text
systemd-run [OPTIONEN] BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --user | Benutzermanager verwenden. |
| --unit=NAME | Gezielten transienten Unitnamen wählen. |
| --scope | Scope statt Service verwenden. |
| --wait | Bei transientem Service auf dessen Ende warten; nicht mit --scope kombinieren. |
| --collect | Nicht mehr benötigte Unit aufräumen lassen. |
| --no-block | Auftrag einreihen ohne Abschluss abzuwarten; keine Trockenübung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-run --user --unit=EIGENE_TESTUNIT --wait PROGRAMM
```

Das unausgeführte Muster würde eine echte Unit anlegen und PROGRAMM ausführen. Ein eigener Name allein isoliert weder Dateizugriffe noch Netzwerkeffekte des Programms.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Transiente Services und Scopes verstehen; einen später genehmigten Einzellauf planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Es entstehen Managerzustand, Prozesse und möglicherweise Logs. Programme können andere Arbeitsverzeichnisse und Umgebungen als die interaktive Shell erhalten. Keine Unit, kein Timer und kein Prozess über systemd-run gestartet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| User bus fehlt | Benutzermanager und Sitzung fehlen möglicherweise. |
| Status nur Start bestätigt | Startabschluss vom späteren Programmende unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; transiente Units und Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl | Unit verwalten. |
| systemd-cat | Ausgabe protokollieren. |
| timeout | Direkten neuen Befehl zeitlich begrenzen. |

Ausgangsdatensatz 576 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
