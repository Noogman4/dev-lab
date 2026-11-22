---
id: "mapfile"
name: "mapfile"
command: "mapfile"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "mapfile"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 548
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# mapfile – Zeilen in ein Bash-Array einlesen

## 1. Kurzbeschreibung

mapfile liest Eingabe in ein indiziertes Array; readarray ist ein Bash-Synonym.

## 2. Was macht der Befehl?

Mit -t wird der abschließende Trenner entfernt. Die Anzahl eingelesener Elemente ist von der Anzahl der Wörter zu unterscheiden: Leerzeichen innerhalb einer Zeile bleiben Teil eines Elements. Ohne expliziten Startindex wird das Zielarray gewöhnlich zuvor geleert. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help mapfile`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
mapfile [OPTIONEN] [ARRAY]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -t | Abschließenden Zeilentrenner entfernen. |
| -n ZAHL | Höchstens diese Zahl Zeilen; 0 bedeutet alle. |
| -s ZAHL | Anfangszeilen überspringen. |
| -u FD | Aus Dateideskriptor lesen. |
| -C FUNKTION | Callback ausführen; deshalb kein passiver Datenleser in jedem Modus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
printf '%s\n' 'eins zwei' 'drei' > own-lines.txt
mapfile -t lesson_lines < own-lines.txt
test "${#lesson_lines[@]}" -eq 2
test "${lesson_lines[0]}" = 'eins zwei'
printf 'Erste Zeile=%s\n' "${lesson_lines[0]}"
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Zwei eigene Zeilen werden zu zwei Elementen. Das Leerzeichen in der ersten Zeile erzeugt kein zusätzliches Arrayelement. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene kleine Textlisten verarbeiten; Zeilen unverändert statt durch Wortaufteilung übernehmen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Sehr große Dateien können viel Speicher belegen. Callbackoptionen führen Shellcode aus. Fremde Arraynamen und arithmetische Indizes nicht ungeprüft übernehmen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Array nach Pipeline leer | Befehl kann in einer Subshell gelaufen sein; Dateiumleitung nutzen. |
| Zeilenende enthalten | -t und tatsächlichen Trenner prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| read | Eine Zeile lesen. |
| declare | Arraytyp festlegen. |
| bash | Benötigte Shellimplementierung. |

Ausgangsdatensatz 548 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
