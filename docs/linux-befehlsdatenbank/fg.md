---
id: "fg"
name: "fg"
command: "fg"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "fg"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 483
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21; Hilfe gelesen, interaktives fg praktisch offen"
---

# fg – Shelljob in den Vordergrund holen

## 1. Kurzbeschreibung

fg ist das Bash-Builtin für einen Job der aktuellen Shell. Es macht den gewählten Job zum Vordergrundjob und setzt einen gestoppten Job fort. Es ist kein Startbefehl für eine beliebige PID.

## 2. Was macht der Befehl?

Der Vordergrundjob erhält die terminalbezogene Bedienung; eine Pipeline kann mehrere Prozesse umfassen. Bash wartet auf sein Ende oder erneutes Stoppen. Der Rückgabestatus folgt dem in den Vordergrund geholten Kommando beziehungsweise einem Auswahlfehler. Eine Jobnummer wird aus der Jobtabelle derselben Shell gelesen, nicht aus einer globalen Prozessliste.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: Bash 5.2.21, `help fg`; [Bash-Jobsteuerung](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) als Projektverweis

## 3. Syntax

```text
fg [JOBSPEZIFIKATION]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `%1` | Konkrete Jobnummer derselben Shell. |
| `%+` | Aktueller Job. |
| `%-` | Vorheriger Job. |
| Ohne Angabe | Aktueller Job; kann sich inzwischen geändert haben. |
| `help fg` | Bash-interne Hilfe. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur Plan für einen eigenen interaktiven Übungsjob:
jobs -l
fg %1
```

Das Muster wurde nicht ausgeführt. Vor fg muss die Jobidentität feststehen. Danach würde die Shell Eingaben dem Job überlassen und auf ihn warten. Ein nichtinteraktives Skript ohne Jobsteuerung ist kein gleichwertiger Terminaltest.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Terminalbedienung lernen:** Vordergrundzuordnung von laufend/gestoppt unterscheiden. **Status verstehen:** Rückgabestatus des Jobs nicht mit dessen Start-PID verwechseln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fortgesetzter Code kann Dateien oder Netzwerk verändern. Nicht versehentlich einen fremden oder langen Job auswählen. Keine reale Benutzersitzung manipuliert, keine Prozesse gestoppt/fortgesetzt und kein Terminal umgehängt. Lokale Hilfe ist belegt, Funktionsablauf offen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No job control | Terminal-/Shellvoraussetzungen fehlen. |
| No such job | Job gehört anderer Shell oder existiert nicht mehr. |
| Shell wartet | Vordergrundprogramm läuft; kein automatischer Fehler. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Bash 5.2.21; Hilfe gelesen, interaktives fg praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `bg` | Fortsetzen im Hintergrund. |
| `jobs` | Jobidentität und Status lesen. |
| `wait` | Gezielt auf eigene Kinder warten. |

Ausgangsdatensatz 483 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
