---
id: "ulimit"
name: "ulimit"
command: "ulimit"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "ulimit"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 560
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# ulimit – Ressourcenlimits der Shell lesen

## 1. Kurzbeschreibung

ulimit ist ein Shell-Builtin für Ressourcenlimits der Shell und ihrer späteren Kinder.

## 2. Was macht der Befehl?

Ohne neuen Zahlenwert wird das gewählte Limit angezeigt. Soft- und Hardlimit sind verschieden; mit -S beziehungsweise -H kann gezielt gelesen werden. Eine Absenkung des Hardlimits ist unprivilegiert oft nicht rückgängig zu machen. Einheiten und verfügbare Optionen hängen von Ressource, Shell und Plattform ab. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help ulimit`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
ulimit [-S oder -H] RESSOURCENOPTION [NEUER_WERT]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -Sn | Softlimit offener Dateideskriptoren anzeigen. |
| -Hn | Dazugehöriges Hardlimit anzeigen. |
| -a | Alle verfügbaren Limits lesen. |
| -t | CPU-Zeit in Sekunden. |
| -v | Virtueller Speicher, Bash üblicherweise KiB. |
| NEUER_WERT | Mit Wert wird gesetzt; keine Abfrage mehr. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
printf 'Softlimit: '
ulimit -Sn
printf 'Hardlimit: '
ulimit -Hn
printf 'Limits ausschliesslich gelesen\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Beide Dateideskriptorgrenzen der neuen Shell werden nur gelesen. Es steht kein neuer Zahlenwert im Aufruf, daher findet keine Limitänderung statt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Grenzen bei Dateideskriptorfehlern verstehen; Shelllimit und Prozesslimit vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein falsch gesetztes Limit kann Prozesse oder die eigene Sitzung beeinträchtigen. Nicht alle Kernelressourcen lassen sich mit jeder Option sinnvoll begrenzen. Keine Grenzwerte verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Cannot modify limit | Hardlimit, Rechte oder Plattform verhindern Änderung. |
| Wert hat andere Einheit | Ressource und konkrete Shellhilfe prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| prlimit | Limits einer ausgewählten PID. |
| bash | Builtin-Kontext. |
| timeout | Zeitfrist für einen neuen Befehl. |

Ausgangsdatensatz 560 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
