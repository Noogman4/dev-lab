---
id: "readonly"
name: "readonly"
command: "readonly"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "readonly"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 553
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# readonly – Eigene Shellvariablen schreibschützen

## 1. Kurzbeschreibung

readonly setzt ein Attribut, das spätere Änderungen einer Shellvariablen verhindert.

## 2. Was macht der Befehl?

Der Schreibschutz betrifft den Shellzustand und keine Datei auf dem Datenträger. Ein mit readonly gesetzter Wert lässt sich in derselben Shell nicht einfach mit unset löschen oder durch ein Gegenattribut entsperren. Der Schutz ist kein Sicherheitsmechanismus gegen andere Prozesse mit passenden Rechten. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help readonly`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
readonly [OPTIONEN] NAME[=WERT]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| NAME=WERT | Zuweisen und schreibschützen. |
| -p | Schreibgeschützte Deklarationen anzeigen. |
| -a, -A | Bash-Arrayattribute berücksichtigen. |
| -f | Funktion schreibschützen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
readonly lesson_fixed=fest
test "$lesson_fixed" = fest
if (lesson_fixed=anders) 2> own-error.txt; then exit 1; fi
test "$lesson_fixed" = fest
printf 'Eigener Wert bleibt schreibgeschuetzt\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Der erwartete Zuweisungsfehler tritt nur in einer Subshell auf und wird als Fehler behandelt. Der feste Wert bleibt erhalten; die neue Übungsshell endet anschließend. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Konstanten in eigenen Skripten kennzeichnen; versehentliche Überschreibungen erkennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht in einer benötigten Sitzung an produktiven Variablen ausprobieren. Ein Fehler kann nichtinteraktive Shells beenden. Keine reale Benutzerkonfiguration verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Readonly variable | Attribut absichtlich gesetzt; neue Shell für neue Werte verwenden. |
| Datei bleibt beschreibbar | Shellvariable und Dateirechte sind verschieden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| declare | Variablenattribute. |
| unset | Schreibgeschützte Werte nicht beliebig entfernbar. |
| export | Getrenntes Exportattribut. |

Ausgangsdatensatz 553 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
