---
id: "dirs"
name: "dirs"
command: "dirs"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "dirs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 539
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# dirs – Den Verzeichnisstapel anzeigen

## 1. Kurzbeschreibung

dirs zeigt den Verzeichnisstapel der aktuellen Bash.

## 2. Was macht der Befehl?

Der Stapel ist Shellzustand und keine Auflistung aller Ordner auf der Festplatte. pushd und popd verändern ihn. +N zählt von links und -N von rechts, jeweils ab Null. dirs -c leert den Stapel und ist damit keine reine Anzeige. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help dirs`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Directory-Stack-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
dirs [-lpv] [+N oder -N]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -v | Eintrag mit Stapelindex pro Zeile. |
| -p | Eintrag pro Zeile. |
| -l | Vollständige Pfade statt Tildekürzung. |
| -c | Stapel leeren; nur Shellzustand ändern. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
mkdir alpha
pushd alpha >/dev/null
dirs -v
test "${#DIRSTACK[@]}" -ge 2
popd >/dev/null
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Ein eigener Unterordner wird auf den Stapel gelegt. Die Anzeige und die Arraygröße bestätigen mindestens zwei Einträge; danach wird zur Übungsbasis zurückgekehrt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Navigation innerhalb eigener Arbeitsordner verstehen; Stapelpositionen vor popd kontrollieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Einträge sind keine garantierten existierenden Verzeichnisse. Nach fehlgeschlagenem cd oder pushd nicht mit Schreibaktionen fortfahren. Nur die neue Shell ist betroffen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein erwarteter Eintrag | Möglicherweise andere Shell oder zuvor geleerter Stapel. |
| Falscher Index | Zählrichtung und Beginn bei Null beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pushd | Verzeichnis hinzufügen. |
| popd | Eintrag entfernen und meist wechseln. |
| pwd | Aktuelles Verzeichnis. |

Ausgangsdatensatz 539 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
