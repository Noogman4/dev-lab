---
id: "jobs"
name: "jobs"
command: "jobs"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "jobs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 490
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# jobs – Nur die Jobtabelle der eigenen Shell anzeigen

## 1. Kurzbeschreibung

jobs ist hier das Bash-Builtin zur Anzeige der Jobtabelle dieser Shell. Es zeigt keine vollständige systemweite Prozessliste. jobs -x kann zusätzlich ein Kommando ausführen und ist deshalb gesondert zu behandeln.

## 2. Was macht der Befehl?

Eine asynchrone Pipeline bekommt eine Jobnummer und kann mehrere Prozesse enthalten. %+ und %- bezeichnen shellbezogene Auswahlzustände. Jobnummer, Prozessgruppenführer und einzelne PID sind nicht dasselbe. Eine neue Shell hat eine andere Tabelle; die Anzeige eines fremden Terminals wird dadurch nicht verfügbar.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: Bash 5.2.21, `help jobs`; [Bash-Projekthandbuch](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) als Projektverweis

## 3. Syntax

```text
jobs [-l|-p|-r|-s|-n] [JOBSPEZIFIKATION...]
jobs -x BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-l` | PIDs zusätzlich zum Jobstatus anzeigen. |
| `-p` | Nur PID des Prozessgruppenführers. |
| `-r`, `-s` | Laufende beziehungsweise gestoppte Jobs. |
| `-n` | Nur seit letzter Mitteilung geänderte Zustände. |
| `-x BEFEHL` | Jobspezifikationen ersetzen und BEFEHL ausführen, keine reine Anzeige. |
| `%1` | Jobnummer derselben Shell, nicht PID 1. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-jobs-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
sleep 1 &
kind_pid=$!
jobs -l > jobs.txt
cat jobs.txt
jobs -p | rg -x "$kind_pid"
wait "$kind_pid"
printf 'Eigener Job beendet\n'
```

### Schritt 3: Ergebnis einordnen

Die Übung startet ausschließlich einen eigenen einsekündigen sleep-Prozess. Dessen gespeicherte PID muss in jobs -p auftauchen. wait wartet auf sein normales Ende; kein Signal wird gesendet. Dies prüft die Jobtabelle und nicht interaktives fg/bg oder Terminal-Jobsteuerung. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Shellabläufe verstehen:** Eigene Hintergrundjobs zuverlässig zuordnen. **Skriptstatus lesen:** Start-PID und Abschlussstatus getrennt erfassen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Hintergrundstart führt das Programm tatsächlich aus. jobs selbst ist in der Anzeigeform lesend; -x kann beliebigen angegebenen Code starten. Keine bestehenden Benutzerjobs angefasst oder fremden Prozesse signalisiert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Leere Tabelle trotz laufendem Dienst | jobs kennt nur Jobs dieser Shell. |
| PID unerwartet | Pipeline-/Prozessgruppenbezug prüfen. |
| Job inzwischen beendet | Momentaufnahme und kurze Lebensdauer berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener einsekündiger Hintergrundjob mit jobs -l/-p angezeigt und normal abgewartet. Keine Signale. Interaktive Jobsteuerung, Pipelines und andere Shells praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `bg` | Gestoppten Job im Hintergrund fortsetzen. |
| `fg` | Job in Vordergrund holen. |
| `wait` | Auf eigene Kinder warten. |

Ausgangsdatensatz 490 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
