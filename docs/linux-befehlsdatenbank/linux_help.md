---
id: "linux_help"
name: "."
command: "."
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "."]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 535
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# . – Datei in der aktuellen Shell ausführen

## 1. Kurzbeschreibung

Der Punkt . ist ein Shell-Builtin zum Einlesen und Ausführen einer Datei im aktuellen Shellkontext.

## 2. Was macht der Befehl?

Variablen, Funktionen und Verzeichniswechsel aus der Datei wirken anschließend in derselben Shell weiter. Das ist weder das Anzeigen einer Datei noch der Start eines isolierten Programms. Ein Pfad mit ./ vermeidet eine unbeabsichtigte Suche in PATH. Die feste Katalogkennung linux_help bleibt trotz des Befehlsnamens . unverändert. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help .`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
. DATEI [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| DATEI | Ausführbarer Shelltext; Leserechte genügen. |
| ./DATEI | Expliziter relativer Pfad statt Namenssuche. |
| ARGUMENTE | Während des Einlesens als Positionsparameter verfügbar. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
printf 'lesson_value=bereit
' > own-settings.sh
. ./own-settings.sh
test "$lesson_value" = bereit
printf 'Wert aus eigener Datei=%s\n' "$lesson_value"
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Die eigene Datei enthält nur eine bekannte Zuweisung. Der anschließend sichtbare Wert belegt die Ausführung im gleichen Shellkontext. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene geprüfte Funktionsdateien einbinden; Wirkung einer Aktivierungsdatei verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Dateien können beliebigen Code ausführen und Shellzustand verändern. Dateiendung .sh und fehlendes Ausführungsbit bieten keinen Schutz.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Datei wird nicht gefunden | Expliziten Pfad und Leserechte prüfen. |
| Wert bleibt nach bash DATEI nicht erhalten | Separate Shell und Einlesen mit . unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| source | Bash-Synonym. |
| bash | Separaten Interpreter starten. |
| export | Werte an Kindprozesse vererben. |

Ausgangsdatensatz 535 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
