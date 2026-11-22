---
id: "shopt"
name: "shopt"
command: "shopt"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "shopt"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 557
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# shopt – Zusätzliche Bash-Optionen steuern

## 1. Kurzbeschreibung

shopt zeigt und verändert Bash-Optionen, die teilweise über set hinausgehen.

## 2. Was macht der Befehl?

-s aktiviert und -u deaktiviert eine benannte Option. Mit -q lässt sich der Zustand ohne Ausgabe prüfen; ein deaktivierter Zustand liefert Nichtnullstatus und ist nicht automatisch ein Werkzeugfehler. nullglob kann bewirken, dass ein nicht passendes Dateimuster vollständig aus der Argumentliste verschwindet. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help shopt`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/The-Shopt-Builtin.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
shopt [-pqsu] [OPTION ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p | Zustand in Shellform anzeigen. |
| -q | Nur Status prüfen. |
| -s OPTION | Option einschalten. |
| -u OPTION | Option ausschalten. |
| -o | Auf set -o-Optionen begrenzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
shopt -s nullglob
lesson_matches=(./niemals-vorhanden-*.lesson)
test "${#lesson_matches[@]}" -eq 0
shopt -q nullglob
shopt -u nullglob
printf 'Nullglob nur in neuer Shell geprueft\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Im neuen leeren Übungsordner findet das Muster nichts. Mit nullglob entsteht ein leeres Array; die Wirkung wurde ausschließlich in einer neuen Shell getestet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Globverhalten in eigenen Skripten erklären; Optionen gezielt statt pauschal aktivieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Veränderte Expansion kann nachfolgende Programme mit ganz anderen Argumenten starten. Kein echtes Lösch- oder Schreibprogramm mit einem Glob getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| shopt fehlt | Bash-Builtin nicht in jeder sh vorhanden. |
| Status 1 bei -q | Option kann schlicht ausgeschaltet sein. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| set | Grundlegende Shelloptionen. |
| bash | Implementierung. |
| declare | Arraydarstellung. |

Ausgangsdatensatz 557 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
