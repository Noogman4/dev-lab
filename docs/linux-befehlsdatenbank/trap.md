---
id: "trap"
name: "trap"
command: "trap"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "trap"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 559
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# trap – Shellereignisse mit Trap behandeln

## 1. Kurzbeschreibung

trap hinterlegt Shellcode für bestimmte Ereignisse oder Signale.

## 2. Was macht der Befehl?

EXIT wird beim Ende der Shell behandelt; es ist kein an Prozesse versandtes Signal. Eine leere Aktion ignoriert ein Signal, während - die ursprüngliche Behandlung wiederherstellt. SIGKILL und SIGSTOP lassen sich nicht abfangen. Zeitpunkt und Inhalt der Expansion hängen von der Zitierung der Aktion ab. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help trap`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
trap [AKTION] EREIGNIS ...
trap -p [EREIGNIS ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p | Gesetzte Aktionen anzeigen. |
| -l | Signalnamen auflisten. |
| EXIT | Beim Ende dieser Shell ausführen. |
| ERR | Bash-Fehlerereignis mit Kontextausnahmen. |
| '' SIGNAL | Signal ignorieren; kann Abbruchverhalten verändern. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
trap 'printf "Eigener EXIT-Handler\n"' EXIT
printf 'Eigener Hauptteil\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Die neue Shell gibt zuerst ihren Hauptteil und beim regulären Ende den EXIT-Text aus. Keine Signale werden versandt, abgefangen oder in einer bestehenden Sitzung verändert. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Aufräumkonzepte in eigenen Skripten erklären; bewusstes Fehler- und Endeverhalten planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ungeprüfte Trap-Aktionen können beim Ende zusätzliche Änderungen auslösen. Ein Aufräumhandler darf fremde Dateien nicht anhand leerer oder falscher Pfade löschen. Hier wird ausschließlich printf ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Variable zu früh expandiert | Zitierung bei Registrierung und Ereignis unterscheiden. |
| Kein Handler bei SIGKILL | Nicht abfangbares Signal; keine Garantie für Aufräumen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| wait | Status eigener Kinder. |
| exec | Prozessersatz berücksichtigen. |
| set | Fehleroptionen und ERR-Kontext. |

Ausgangsdatensatz 559 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
