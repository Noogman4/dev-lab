---
id: "getopts"
name: "getopts"
command: "getopts"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "getopts"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 545
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# getopts – Kurzoptionen im eigenen Skript auswerten

## 1. Kurzbeschreibung

getopts verarbeitet Optionsargumente in der aktuellen Shell schrittweise.

## 2. Was macht der Befehl?

Die Optionszeichenfolge legt zulässige Buchstaben fest. Ein nachgestellter Doppelpunkt verlangt einen Wert. OPTARG enthält den Wert, OPTIND zeigt das nächste unverarbeitete Argument an. Ein führender Doppelpunkt ermöglicht kontrollierte eigene Fehlerbehandlung. Für einen neuen Parse-Durchlauf OPTIND bewusst zurücksetzen. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help getopts`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
getopts OPTIONSZEICHENFOLGE VARIABLE [ARGUMENTE ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| a: | Option -a benötigt einen Wert. |
| führender Doppelpunkt | Stille Fehlerbehandlung mit ? oder :. |
| OPTARG | Wert beziehungsweise Fehlerdetail. |
| OPTIND | Index des nächsten Arguments, anfangs 1. |
| -- | Beendet die Optionsverarbeitung der Eingabeargumente. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
set -- -n wort rest
OPTIND=1
lesson_name=
while getopts ':n:' lesson_option; do
  case "$lesson_option" in
    n) lesson_name=$OPTARG ;;
    *) exit 1 ;;
  esac
done
shift "$((OPTIND - 1))"
test "$lesson_name" = wort
test "$1" = rest
printf 'Option=%s Rest=%s\n' "$lesson_name" "$1"
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Ein eigener Optionswert und ein verbleibendes Argument werden getrennt geprüft. Die Schleife endet regulär, sobald die Optionen verarbeitet sind. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kurzoptionen in eigenen Shellskripten robust verarbeiten; Fehlerfälle explizit behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

getopts wertet Daten aus, startet sie aber nicht als Befehle. Nicht durch eval nachträglich zu Code machen. GNU-getopt und Shell-getopts sind unterschiedliche Werkzeuge.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zweiter Durchlauf überspringt Werte | OPTIND für einen neuen Durchlauf zurücksetzen. |
| Fehlender Optionswert | Fall : beziehungsweise ? ausdrücklich behandeln. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| getopt | Separates Werkzeug mit anderer Schnittstelle. |
| set | Positionsparameter setzen. |
| shift | Verarbeitete Argumente entfernen. |

Ausgangsdatensatz 545 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
