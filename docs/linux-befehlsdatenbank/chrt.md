---
id: "chrt"
name: "chrt"
command: "chrt"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "chrt"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 481
reviewed_at: "2026-11-13"
locally_checked_version: "chrt / util-linux 2.39.3"
---

# chrt – Schedulingattribute der eigenen Test-Shell nur lesen

## 1. Kurzbeschreibung

chrt liest oder verändert Schedulerpolicy und Priorität eines Tasks. Mit --pid und ausschließlich einer PID werden Attribute angezeigt. Ein zusätzlicher Prioritätsoperand kann daraus einen Änderungsauftrag machen.

## 2. Was macht der Befehl?

Echtzeitprioritäten sind nicht Nice-Werte. Policies wie FIFO und RR können bei falscher Verwendung andere Tasks verdrängen. Threads können unterschiedliche Attribute besitzen. Die aktuelle Onlinefassung enthält neuere util-linux-Funktionen; lokal wird die reine Leseform mit util-linux 2.39.3 geprüft.

Quelle, am 2026-11-13 gelesen: [util-linux: chrt-Handbuch](https://man7.org/linux/man-pages/man1/chrt.1.html)

## 3. Syntax

```text
chrt --pid PID
chrt [POLICY_OPTIONEN] PRIORITAET BEFEHL [ARGUMENTE]
chrt --pid [POLICY_OPTIONEN] PRIORITAET PID
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--pid PID` | Attribute bestehenden Tasks lesen, wenn keine Priorität angegeben. |
| `--all-tasks` | Alle Threads der ausgewählten PID einbeziehen. |
| `--max` | Zulässige Prioritätsbereiche anzeigen. |
| `--fifo`, `--rr` | Echtzeitpolicy auswählen; schreibender Einsatz gesondert. |
| `--other`, `--batch`, `--idle` | Andere Schedulerpolicies, nicht identisch mit nice. |
| `--version` | Werkzeugversion ausgeben. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
chrt --version
LC_ALL=C chrt --pid "$$"
```

### Schritt 3: Ergebnis einordnen

$$ bezeichnet die hier neu gestartete Bash-Test-Shell. Nur deren Policy und Priorität werden gelesen. Konkrete geerbte Werte sind umgebungsabhängig und kein festes Soll. Der Aufruf enthält keine neue Priorität und verändert deshalb keine Schedulingattribute. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Schedulerbegriffe lernen:** Policy, Echtzeitpriorität und Nice-Wert auseinanderhalten. **Diagnose planen:** Threadumfang und Rechte ausdrücklich benennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Änderungen können CAP_SYS_NICE oder passende Limits benötigen und das System beeinträchtigen. Keine Echtzeitpolicy, Priorität, Limits oder Kernelparameter gesetzt. Es wurde nur der eigene kurzlebige Shellprozess gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not permitted bei Änderung | Rechte-/Limitgrenze, nicht automatisch eskalieren. |
| Priorität 0 | Bei Normalpolicies kein Nice-Wert. |
| Onlineoption fehlt | Neuere Handbuchversion nicht lokal voraussetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** chrt / util-linux 2.39.3. Praktisch geprüft: Nur chrt --pid auf der eigenen Test-Shell ausgeführt. Keine Attribute geändert. Echtzeit-, Mehrthread-, Berechtigungs- und neuere Versionsfunktionen praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nice` | Nice-Anpassung für neue Prozesse. |
| `ionice` | I/O-Priorität statt CPU-Schedulerpolicy. |
| `taskset` | CPU-Affinität, weitere andere Eigenschaft. |

Ausgangsdatensatz 481 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
