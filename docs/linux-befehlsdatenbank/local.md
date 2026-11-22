---
id: "local"
name: "local"
command: "local"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "local"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 547
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# local – Variablen innerhalb einer Funktion begrenzen

## 1. Kurzbeschreibung

local legt in Bash funktionslokale Variablen an.

## 2. Was macht der Befehl?

Das Builtin ist nur innerhalb einer Funktion zulässig. Bash verwendet dynamische Sichtbarkeit: von der Funktion aufgerufene Funktionen können den lokalen Wert sehen. Nach Rückkehr wird ein zuvor verdeckter äußerer Wert wieder sichtbar. local ist keine allgemeine POSIX-Shellanweisung. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help local`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
local [OPTIONEN] NAME[=WERT]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| NAME=WERT | Lokalen Wert setzen. |
| -a | Lokales indiziertes Array. |
| -r | Lokale Variable schreibschützen. |
| -i | Arithmetisches Attribut; unbekannte Ausdrücke vermeiden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
lesson_value=aussen
lesson_function() {
  local lesson_value=innen
  test "$lesson_value" = innen
  printf 'Funktionswert=%s\n' "$lesson_value"
}
lesson_function
test "$lesson_value" = aussen
printf 'Aussenwert=%s\n' "$lesson_value"
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Die Funktion sieht innen; nach ihrer Rückkehr bleibt außen unverändert. Nur selbst benannte Testvariablen der neuen Shell werden verwendet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Hilfsfunktionen vor unbeabsichtigten globalen Überschreibungen schützen; Sichtbarkeit im Skript erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Lokale Werte sind kein Geheimnisspeicher. Attribute können weitere Auswertung auslösen. Zuweisung aus einem fehlschlagenden Befehl besser vom local-Aufruf trennen, damit dessen Status nicht verdeckt wird.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Can only be used in a function | Aufrufkontext korrigieren. |
| Kindfunktion sieht Wert | Dynamische Sichtbarkeit von Bash beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| declare | Attribute und globale Option -g. |
| unset | Variablen entfernen. |
| export | Kindumgebung statt Funktionssichtbarkeit. |

Ausgangsdatensatz 547 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
