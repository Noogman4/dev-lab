---
id: "disown"
name: "disown"
command: "disown"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "disown"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 482
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21; Hilfe gelesen, keine Jobentkopplung praktisch geprüft"
---

# disown – Jobtabelle und HUP-Behandlung gezielt ändern

## 1. Kurzbeschreibung

disown ist hier das Bash-Builtin. Es entfernt ausgewählte Jobs aus der Jobtabelle oder markiert sie mit -h gegen eine bestimmte SIGHUP-Weitergabe der Shell. Es startet keinen Dienst.

## 2. Was macht der Befehl?

Ein Jobtabelleneintrag gehört zur aktuellen Shell. disown macht aus dem Programm weder einen Daemon noch garantiert es Weiterlaufen nach Logout: Terminaldeskriptoren, Sitzungsverwaltung und andere Signale bleiben relevant. -h lässt den Eintrag bestehen und verändert die HUP-Behandlung; normales disown entfernt ihn. Jobnummer und PID sind unterschiedliche Identifikatoren.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: Bash 5.2.21, `help disown`; [Bash-Jobsteuerung](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) als Projektverweis

## 3. Syntax

```text
disown [-h] [-a|-r] [JOBSPEZIFIKATION|PID...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `%1` | Konkreten Job dieser Shell wählen. |
| `-h` | Job markieren, damit Bash bei eigenem SIGHUP nicht SIGHUP an ihn sendet. |
| `-a` | Ohne einzelne Jobs alle berücksichtigen. |
| `-r` | Nur laufende Jobs auswählen. |
| Ohne Argument | Aktueller Job; vorher Identität prüfen. |
| `help disown` | Lokale Builtin-Semantik lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur als Plan einer eigenen Shellübung:
jobs -l
disown -h %1
```

Das Muster wurde nicht ausgeführt. %1 müsste zuvor als eigener Übungsjob identifiziert werden. -h verschiebt weder Ein-/Ausgabe noch Startdateien. Ein späterer Test müsste SIGHUP, Terminalverlust und das konkrete Programm getrennt untersuchen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Shelllebensdauer verstehen:** Jobverwaltung von Prozess-/Sitzungsverwaltung trennen. **Fehlerberichte erklären:** Fehlenden jobs-Eintrag nicht mit beendetem Prozess gleichsetzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Entfernte Einträge sind nicht mehr bequem über fg/bg auswählbar. Bereits laufender Code behält seine Wirkungen. Keine echten Jobs entkoppelt und keine Logout-/HUP-Versuche an einer Benutzersitzung. Nur lokale Hilfe gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No such job | Falsche Shell oder bereits beendeter Job. |
| Prozess endet trotzdem | Andere Signale, Terminal oder Sitzungsrichtlinie möglich. |
| Job bleibt bei -h sichtbar | Das ist beabsichtigt; -h entfernt nicht. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Bash 5.2.21; Hilfe gelesen, keine Jobentkopplung praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `jobs` | Tabelle derselben Shell. |
| `nohup` | Start mit ignoriertem HUP und eigener Umleitungssemantik. |
| `fg` | Vorhandenen Job in Vordergrund holen. |

Ausgangsdatensatz 482 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
