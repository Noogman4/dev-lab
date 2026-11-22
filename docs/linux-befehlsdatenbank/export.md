---
id: "export"
name: "export"
command: "export"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "export"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 543
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# export – Variablen an Kindprozesse vererben

## 1. Kurzbeschreibung

export markiert Shellvariablen für die Umgebung später gestarteter Kindprozesse.

## 2. Was macht der Befehl?

Eine Zuweisung und ihr Export sind getrennte Eigenschaften. Kinder erhalten eine Kopie; Änderungen des Kindes ändern nicht automatisch die Elternshell. export -n nimmt das Exportattribut weg und löscht nicht den vorhandenen Shellwert. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help export`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
export [NAME[=WERT] ...]
export -n NAME
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| NAME=WERT | Wert zuweisen und exportieren. |
| -n NAME | Exportattribut entfernen. |
| -p | Exportierte Werte anzeigen; mögliche Geheimnisse. |
| -f NAME | Bash-Funktion exportieren; nicht portabel. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
export LESSON_VALUE=vererbt
/usr/bin/printenv LESSON_VALUE
export -n LESSON_VALUE
test "$LESSON_VALUE" = vererbt
if /usr/bin/printenv LESSON_VALUE; then exit 1; fi
printf 'Exportattribut getrennt geprueft\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Der erste Kindprozess sieht den Wert. Nach -n bleibt er in der Shell erhalten, ist im zweiten printenv aber nicht mehr vorhanden. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Gezielte Programmeinstellungen an eigene Kinder übergeben; Shellvariablen von Umgebungsvariablen unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Geheimnisse vollständig mit export -p protokollieren. Exportierte PATH- oder Loader-Variablen können die Ausführung verändern. Nur eine neue Testvariable verwendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kind sieht Variable nicht | Zuweisung allein reicht ohne Export nicht immer. |
| Wert nach -n noch vorhanden | -n entfernt das Attribut, nicht die Variable. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| env | Umgebung pro Aufruf. |
| unset | Variable entfernen. |
| printenv | Umgebung des Kindes lesen. |

Ausgangsdatensatz 543 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
