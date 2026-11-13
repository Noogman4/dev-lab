---
id: "declare"
name: "declare"
command: "declare"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "declare"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 538
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# declare – Variablenattribute und Arrays erklären

## 1. Kurzbeschreibung

declare verwaltet Bash-Variablen, Attribute und Funktionen.

## 2. Was macht der Befehl?

Innerhalb einer Funktion erzeugt declare üblicherweise lokale Variablen; -g fordert den globalen Bereich an. Ein Attribut ist mehr als Textspeicherung: -i wertet Zuweisungen arithmetisch aus, -n erzeugt eine Namensreferenz. Nicht vertrauenswürdige Ausdrücke oder Referenzziele sind deshalb problematisch. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help declare`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
declare [OPTIONEN] NAME[=WERT]
declare -p NAME
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -a | Numerisch indiziertes Array. |
| -A | Assoziatives Array. |
| -p NAME | Deklaration ausgewählter Variablen anzeigen. |
| -r | Schreibschutz setzen. |
| -x | Exportattribut setzen. |
| -n | Namensreferenz auf andere Variable. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
declare -a lesson_words=(eins zwei)
test "${lesson_words[1]}" = zwei
declare -p lesson_words
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Das eigene Array hat zwei Elemente; Index 1 bezeichnet das zweite. Die Deklarationsausgabe ist nicht aus fremden Daten erneut ausgeführt worden. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Arrays strukturieren; ausgewählte Attribute nachvollziehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

declare ohne Namen kann viele vertrauliche Variablen offenlegen. Arithmetik und Namensreferenzen mit unbekannten Eingaben vermeiden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Andere Sichtbarkeit | Funktionslokalität und -g unterscheiden. |
| Nicht unter sh verfügbar | Bash-spezifisches Builtin beziehungsweise andere Syntax. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| local | Funktionslokale Variablen. |
| readonly | Schreibschutz. |
| export | Umgebungsvererbung. |

Ausgangsdatensatz 538 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
