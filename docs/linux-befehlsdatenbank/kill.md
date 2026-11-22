---
id: "kill"
name: "kill"
command: "kill"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "kill"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 491
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21 Builtin"
---

# kill – Signalprüfung von tatsächlichem Signalisieren trennen

## 1. Kurzbeschreibung

kill sendet Signale; es bedeutet nicht immer sofortiges Beenden. Hier wird das Bash-Builtin verwendet. Externe Programme gleichen Namens können zusätzliche Optionen besitzen.

## 2. Was macht der Befehl?

Ohne explizites Signal wird gewöhnlich TERM gewählt. TERM kann vom Ziel behandelt werden; KILL lässt keine eigene Aufräumroutine zu. Signal 0 führt nur Existenz-/Berechtigungsprüfungen durch. Ein solcher Erfolg beweist weder Anwendungsbereitschaft noch zukünftige Identität: PIDs können später wiederverwendet werden.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: Bash 5.2.21, `help kill`; [util-linux: kill zur Implementierungsabgrenzung](https://man7.org/linux/man-pages/man1/kill.1.html)

## 3. Syntax

```text
Bash: kill [-s SIGNAL] PID_ODER_JOBSPEZIFIKATION...
Bash: kill -l [SIGNAL]
Nur Prüfung: kill -s 0 POSITIVE_PID
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-s NAME` | Signal explizit benennen. |
| `-l [NAME]` | Signale auflisten oder Namen/Nummer umsetzen. |
| `-s 0` | Kein Signal senden, nur Fehlerprüfung. |
| Positive PID | Ein Prozess als Ziel. |
| PID 0 oder negative PID | Kann eine ganze Prozessgruppe/breite Menge auswählen; kein Anfängerbeispiel. |
| `--timeout` | Option bestimmter externer Implementierungen, nicht pauschal Bash. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
kill -l TERM
kill -s 0 "$$"
printf 'Eigene Shell-PID war prüfbar; kein Signal gesendet\n'
```

### Schritt 3: Ergebnis einordnen

kill -l TERM wandelt nur einen Signalnamen um. $$ ist ausschließlich die eigene neue Bash-Test-Shell. Die Nullsignalprüfung verändert ihren Laufzustand nicht. Es wird kein TERM/KILL oder anderes echtes Signal gesendet; eine Beendigungswirkung wurde nicht getestet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Skriptlogik verstehen:** Bereitschaft von bloßer PID-/Rechteprüfung trennen. **Wartung vorbereiten:** Zielidentität, Zuständigkeit und gewünschtes Signal ausdrücklich benennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein falsches Ziel kann Datenverlust oder Dienstunterbrechung auslösen. Prozessnamen und alte PIDs sind keine dauerhaften Identitäten. Keine Broad-/Gruppenziele, keine fremden Prozesse und keine Kill-Eskalationskette. Root ist nicht für jede Signalisierung nötig, berechtigt aber nicht zur Auswahl.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No such process | PID existiert im sichtbaren Namensraum nicht mehr. |
| Operation not permitted | Berechtigungsgrenze, kein Beweis fehlender Existenz. |
| Status 0, Anwendung hängt | Nullsignal ist kein Funktionstest. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21 Builtin. Praktisch geprüft: Signalnamensumsetzung und Nullsignalprüfung nur auf eigene Test-Shell ausgeführt. Keine echten Signale, Handler-, Beendigungs-, Gruppen- oder Rechtefälle geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pgrep` | Auswahl lesen, ohne Signale. |
| `killall` | Breite Namensauswahl mit anderer Semantik. |
| `jobs` | Shelljobs als eigener Kontext. |

Ausgangsdatensatz 491 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
