---
id: "popd"
name: "popd"
command: "popd"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "popd"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 549
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# popd – Zum vorherigen Stapelverzeichnis zurückkehren

## 1. Kurzbeschreibung

popd entfernt einen Eintrag aus dem Bash-Verzeichnisstapel und wechselt normalerweise das Verzeichnis.

## 2. Was macht der Befehl?

Ohne Argument wird der oberste Eintrag entfernt und der neue oberste zum Arbeitsverzeichnis. -n unterdrückt den Verzeichniswechsel. Indizes zählen ab Null; +N von links und -N von rechts. Der Befehl entfernt keine Dateien oder Verzeichnisse vom Datenträger. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help popd`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Directory-Stack-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
popd [-n] [+N oder -N]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| ohne Argument | Obersten Eintrag entfernen und wechseln. |
| -n | Nur Stapel bearbeiten. |
| +N | Eintrag vom linken Ende aus wählen. |
| -N | Eintrag vom rechten Ende aus wählen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
lesson_base=$PWD
mkdir sub
pushd sub >/dev/null
popd >/dev/null
test "$PWD" = "$lesson_base"
printf 'Zum eigenen Ausgangsordner zurueck\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Ein Wechsel in einen neuen eigenen Unterordner wird per popd rückgängig gemacht. Die Dateien bleiben bestehen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Navigation nach einem Unterordnerbesuch fortsetzen; Stapelpositionen verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nach Fehlern nicht unter Annahme eines erfolgten Wechsels weiter schreiben. popd in einer separaten Kind-Shell ändert nicht das Verzeichnis der Elternshell.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Directory stack empty | Kein weiterer Eintrag vorhanden. |
| Falsches Ziel | Stapel vorher mit dirs -v ansehen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pushd | Verzeichnis merken. |
| dirs | Stapel anzeigen. |
| cd | Direkter Verzeichniswechsel. |

Ausgangsdatensatz 549 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
