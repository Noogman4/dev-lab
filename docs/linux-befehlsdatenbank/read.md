---
id: "read"
name: "read"
command: "read"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "read"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 552
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# read – Eine Zeile ohne unbeabsichtigte Aufteilung lesen

## 1. Kurzbeschreibung

read liest Eingabe und weist Teile davon Shellvariablen zu.

## 2. Was macht der Befehl?

IFS steuert die Feldaufteilung. IFS= zusammen mit -r ist ein verbreitetes Muster, um eine Textzeile einschließlich Randabständen und Backslashes zu übernehmen. EOF kann einen Nichtnullstatus liefern, auch wenn eine letzte nicht abgeschlossene Zeile bereits Daten enthält. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help read`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
read [OPTIONEN] [VARIABLE ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -r | Backslashes nicht als Escape behandeln. |
| -a ARRAY | Felder in Array speichern; Bash-Erweiterung. |
| -t SEKUNDEN | Wartezeit begrenzen; Kontextabhängigkeit beachten. |
| -u FD | Anderen Deskriptor lesen. |
| -s | Terminaleingabe nicht anzeigen; kein vollständiger Geheimnisschutz. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
printf '%s\n' '  eins\zwei  ' > own-line.txt
IFS= read -r lesson_line < own-line.txt
test "$lesson_line" = '  eins\zwei  '
printf '[%s]\n' "$lesson_line"
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Die Randabstände und der Backslash bleiben erhalten. Es wird aus einer eigenen Datei statt vom Terminal gelesen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Textdateien zeilenweise verarbeiten; Daten nicht als Shellcode interpretieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

read ohne Eingabequelle kann unbegrenzt warten. Pipelines können einen Subshellkontext erzeugen. Passwörter nicht in Testausgaben darstellen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Backslash fehlt | -r fehlt möglicherweise. |
| Variable nach Pipeline leer | Shellkontext der Pipeline berücksichtigen. |
| Letzte Zeile verloren | EOF und bereits gelesene Daten gemeinsam behandeln. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mapfile | Mehrere Zeilen in Array. |
| printf | Daten kontrolliert ausgeben. |
| IFS | Shellvariable für Feldtrennung. |

Ausgangsdatensatz 552 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
