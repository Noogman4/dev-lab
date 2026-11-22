---
id: "bg"
name: "bg"
command: "bg"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "bg"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 479
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21; lokale help-Ausgabe gelesen, Jobsteuerung nicht praktisch ausgeführt"
---

# bg – Gestoppten Shelljob im Hintergrund fortsetzen

## 1. Kurzbeschreibung

bg ist hier das Bash-Builtin für Jobsteuerung, kein systemweiter Prozessmanager. Es setzt einen vorhandenen gestoppten Job derselben Shell im Hintergrund fort.

## 2. Was macht der Befehl?

Ein Job kann aus einer Pipeline mit mehreren Prozessen bestehen. Die Jobspezifikation %1 ist nicht die PID 1. Ohne Angabe verwendet Bash ihren aktuellen Job, der sich inzwischen geändert haben kann. Für sinnvolle Terminal-Jobsteuerung sind eine passende interaktive Shell und ein steuerndes Terminal erforderlich.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: Bash 5.2.21, `help bg`; [Bash: Job-Control-Builtins](https://www.gnu.org/software/bash/manual/html_node/Job-Control-Builtins.html) (Webabruf scheiterte; lokale Hilfe gelesen)

## 3. Syntax

```text
bg [JOBSPEZIFIKATION...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `%1` | Jobnummer 1 dieser Shell auswählen. |
| `%+` | Aktueller Job. |
| `%-` | Vorheriger Job. |
| Ohne Angabe | Aktuellen Job verwenden; Auswahl vorher prüfen. |
| `help bg` | Bash-eigene Hilfe lesen; kein Aufruf des Jobs. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur in einer eigenen interaktiven Übung:
jobs -l
bg %1
```

Das Muster setzt einen eindeutig eigenen, zuvor gestoppten Job voraus und wird hier nicht ausgeführt. jobs -l müsste die Identität zuerst zeigen. bg setzt Rechen-/Datei-/Netzaktivität dieses Jobs fort; es verschiebt keinen beliebigen Dienst.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Shellbedienung verstehen:** Vordergrund, Hintergrund und Stop unterscheiden. **Anleitungen prüfen:** Jobnummern nur im Kontext derselben Shell auswerten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fortgesetzter Code kann Dateien und Systeme verändern. Ein Hintergrundjob ist nicht automatisch vom Terminal getrennt und kann bei Eingabeversuchen erneut stoppen. Keine vorhandenen Jobs gestoppt, fortgesetzt oder signalisiert. Nur die lokale Builtin-Hilfe wurde gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No job control | Shell/Terminal unterstützt die nötige Jobsteuerung nicht. |
| No such job | Jobspezifikation gilt nicht mehr oder gehört zu anderer Shell. |
| Job stoppt erneut | Terminaleingabe/-ausgabe und Programmverhalten prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Bash 5.2.21; lokale help-Ausgabe gelesen, Jobsteuerung nicht praktisch ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `fg` | Job in den Vordergrund holen. |
| `jobs` | Jobtabelle derselben Shell. |
| `disown` | Jobtabelleneintrag beziehungsweise HUP-Behandlung. |

Ausgangsdatensatz 479 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
