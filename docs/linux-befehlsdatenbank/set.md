---
id: "set"
name: "set"
command: "set"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "set"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 555
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# set – Shelloptionen und Positionsparameter setzen

## 1. Kurzbeschreibung

set verändert Shelloptionen oder Positionsparameter; ohne Argumente kann es viele Shellwerte ausgeben.

## 2. Was macht der Befehl?

Minusoptionen aktivieren, entsprechende Plusoptionen deaktivieren. set -- trennt Optionen von neuen Positionsparametern. errexit (-e) hat wichtige Kontextausnahmen, etwa if-Tests und Teile von &&/||-Listen; es ist keine vollständige Fehlerbehandlung. pipefail beeinflusst den Status einer Pipeline, macht sie aber nicht atomar. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help set`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
set [OPTIONEN] [-- ARGUMENTE ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -- ARGUMENTE | Positionsparameter gezielt ersetzen. |
| -u | Nicht gesetzte Parameter bei Expansion als Fehler behandeln. |
| -e | Bei bestimmten Nichtnullstatus abbrechen; Kontextausnahmen beachten. |
| -o pipefail | Pipelinefehler berücksichtigen. |
| -x | Befehle samt expandierten Argumenten protokollieren. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
set -- 'eins zwei' drei
test "$#" -eq 2
test "$1" = 'eins zwei'
printf 'Parameterzahl=%s Erster=[%s]\n' "$#" "$1"
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Nur die Positionsparameter der neuen Übungsshell werden gesetzt. Ein Argument mit Leerzeichen bleibt zusammen; die Shelloptionen der Benutzersitzung werden nicht verändert. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Skriptargumente vorbereiten; Optionen bewusst und mit Fehlerbehandlung einsetzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

set -x kann Geheimnisse offenlegen. -e und -u können ältere Skripte unerwartet abbrechen lassen. Zustandsänderungen bleiben auf die neue Shell beschränkt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Option statt Argument erkannt | set -- vor Daten verwenden. |
| Trotz -e kein Abbruch | Befehl steht möglicherweise in einem ausgenommenen Prüfkontext. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| shopt | Zusätzliche Bash-Optionen. |
| getopts | Skriptoptionen lesen. |
| unset | Variablen entfernen. |

Ausgangsdatensatz 555 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
