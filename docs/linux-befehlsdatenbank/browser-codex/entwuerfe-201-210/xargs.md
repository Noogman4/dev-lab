---
id: "xargs"
name: "xargs"
command: "xargs"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["shell", "argumente", "pipeline"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 208
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# xargs – Eingaben in Befehlsargumente umwandeln

## 1. Kurzbeschreibung

`xargs` liest Elemente von der Standardeingabe und baut daraus Argumentlisten für einen anderen Befehl. Es führt diesen **wirklich aus**; sein Risiko hängt vom Zielbefehl ab. Für eine Ausgabe mit `printf` ist **kein Root nötig**.

## 2. Was macht der Befehl?

Standardmäßig trennt GNU `xargs` Eingaben an Leerraum und interpretiert bestimmte Anführungszeichen/Backslashes. Das ist für beliebige Dateinamen ungeeignet. `-0` verarbeitet Nullbyte-getrennte Elemente, etwa aus `find -print0`. Siehe [GNU-findutils-Handbuch](https://www.gnu.org/software/findutils/manual/html_node/find_html/xargs-options.html).

## 3. Syntax

```bash
ERZEUGER | xargs [OPTIONEN] PROGRAMM [ARGUMENTE ...]
printf '%s\0' 'a b' 'c' | xargs -0 -r -n 1 printf '<%s>\n'
```

Ohne ausdrücklich angegebenes Programm nutzt GNU `xargs` standardmäßig `echo`. Für nachvollziehbare Skripte den Zielbefehl immer angeben.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-0` | Nullbyte-getrennte Elemente. | Eingabe muss ebenfalls NUL verwenden. |
| `-r` | Bei leerer Eingabe nichts ausführen. | Bei GNU Standard, explizit klarer. |
| `-n N` | Maximal N Argumente je Aufruf. | Mehrere Prozesse möglich. |
| `-I {}` | Platzhalter ersetzen. | Meist ein Aufruf pro Eingabezeile. |
| `-P N` | Bis zu N parallele Aufrufe. | Reihenfolge und Last beachten. |
| `-t` | Aufruf vor Ausführung anzeigen. | Kein Dry-Run. |
| `-p` | Vor Ausführung nachfragen. | Benötigt Terminal. |
| `-a DATEI` | Eingaben aus Datei lesen. | Datei wird gelesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Zwei Argumente sicher erzeugen

```bash
printf '%s\0' 'eins zwei' 'drei'
```

Die Elemente sind durch Nullbytes getrennt, nicht durch Leerzeichen.

### Schritt 2: Argumente nur ausgeben

```bash
printf '%s\0' 'eins zwei' 'drei' | xargs -0 -r -n 1 printf '[%s]\n'
```

Erwartet werden zwei Zeilen: `[eins zwei]` und `[drei]`. Der Inhalt wird nicht als Shell-Code interpretiert.

### Schritt 3: Dateinamen-Pipeline als Muster

```bash
find "EIGENER_ORDNER" -type f -print0 | xargs -0 -r -n 1 printf '%s\n'
```

Nur nach Ersetzen durch einen eigenen Ordner verwenden. Beispiele sind **nicht ausgeführt**.

## 6. Typische Anwendungsfälle

**Dateinamen aus `find`:** NUL-getrennt sicher an einen lesenden Befehl weiterreichen. **Batching:** Große Argumentlisten in mehrere Aufrufe aufteilen. **Parallelisierung:** `-P` nur bei unabhängigen, idempotenten Aufgaben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein falscher Zielbefehl kann viele Dateien auf einmal verändern oder löschen. `-t` ist keine Simulation. Standard-Trennung zerstört Namen mit Leerzeichen und Zeilenumbrüchen. `-P` kann Rennen und Ressourcenlast erzeugen. Eingaben können mit `-` beginnen und beim Zielprogramm als Optionen gelten: dort `--` oder geeignete sichere Argumentposition verwenden. Kein `sudo` in Standardpipelines.

## 8. Häufige Fehler

| Problem | Ursache | Maßnahme |
| --- | --- | --- |
| Dateiname zerfällt | Leerraumtrennung. | `-print0` und `-0` kombinieren. |
| Befehl läuft unerwartet | Leereingabe-/Defaultverhalten. | `-r` und Zielbefehl angeben. |
| Reihenfolge variiert | `-P` parallel. | Zunächst seriell arbeiten. |
| Argument beginnt mit `-` | Ziel interpretiert Option. | `--` am Ziel korrekt platzieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst ausschließlich mit `printf` als Zielprogramm üben. Vor jeder schreibenden Pipeline die erzeugten Argumente anzeigen und anschließend den tatsächlichen Zielaufruf separat prüfen. Für schwierige Dateinamen `find -exec ... {} +` als Alternative erwägen.

**Prüfstand:** GNU-findutils-Handbuch am 2026-11-13 gelesen; keine Pipeline ausgeführt und keine lokale Version ermittelt. Spezielle Exitcodes und Parallelverhalten nicht praktisch geprüft.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `find` | Pfade sicher mit `-print0` liefern. |
| `printf` | Testausgabe und NUL-Trennung. |
| `parallel` | Eigenständiges Parallelisierungswerkzeug. |
| `sh` | Shell-Auswertung nur bei bewusstem Bedarf. |

**Ausgangseintrag:** `source_record` 208 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
