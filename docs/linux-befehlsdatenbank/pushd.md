---
id: "pushd"
name: "pushd"
command: "pushd"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "pushd"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 551
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# pushd – Verzeichnisse auf einem Stapel merken

## 1. Kurzbeschreibung

pushd fügt Verzeichnisse zum Bash-Stapel hinzu oder ordnet den Stapel um.

## 2. Was macht der Befehl?

Mit einem Pfad wird normalerweise in das Verzeichnis gewechselt und der bisherige Ort gemerkt. Ohne Argument werden die obersten beiden Einträge vertauscht. -n verändert nur den Stapel. Der Stapel gehört zur aktuellen Shell, nicht zu allen Terminals des Benutzers. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help pushd`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Directory-Stack-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
pushd [-n] [VERZEICHNIS oder +N oder -N]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| VERZEICHNIS | Verzeichnis hinzufügen und wechseln. |
| -n | Verzeichniswechsel unterdrücken. |
| +N / -N | Stapel rotieren; Richtungen unterscheiden. |
| ohne Argument | Oberste zwei Einträge vertauschen. |

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
mkdir 'eigener ordner'
pushd 'eigener ordner' >/dev/null
test "$PWD" = "$lesson_base/eigener ordner"
dirs -v
popd >/dev/null
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Der zitierte Pfad mit Leerzeichen bleibt ein Argument. Die Rückkehr wird mit popd vorgenommen; nur eigene Verzeichnisse sind beteiligt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Navigation zwischen eigenen Arbeitsordnern; Rückkehrpunkte bewusst merken.

## 7. Risiken, Nebenwirkungen und Vorsicht

Verzeichniswechsel kann alle nachfolgenden relativen Schreibpfade verändern. Fehler immer behandeln und Pfade zitieren. Keine Ordner werden durch pushd kopiert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No such file | Pfad und Anführungszeichen prüfen. |
| Directory stack empty | Ohne Argument sind zwei Einträge erforderlich. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| popd | Zum gemerkten Ort zurück. |
| dirs | Stapel anzeigen. |
| pwd | Arbeitsverzeichnis prüfen. |

Ausgangsdatensatz 551 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
