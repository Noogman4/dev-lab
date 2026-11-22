---
id: "dash"
name: "dash"
command: "dash"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "dash"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 537
reviewed_at: "2026-11-13"
locally_checked_version: "Dash-Paket 0.5.12-6ubuntu5"
---

# dash – Skripte mit Dash ausführen

## 1. Kurzbeschreibung

dash ist ein eigener Shellinterpreter, der sich an der POSIX-Shellsprache orientiert.

## 2. Was macht der Befehl?

Dash ist kein Bash-Alias. Bash-Arrays, [[ ... ]] und andere Erweiterungen gehören nicht selbstverständlich zu seiner Sprache. Ein nichtinteraktiver Aufruf mit eigenem Skript vermeidet interaktive Startdateien. Das Programm prüft bei -n Syntax, nicht die tatsächliche Funktion externer Befehle.

Quelle, am 2026-11-13 gelesen: [Dash: mit dem Debian-Paket ausgeliefertes Handbuch](https://manpages.debian.org/bookworm/dash/dash.1.en.html)

## 3. Syntax

```text
dash [OPTIONEN] [SKRIPT [ARGUMENTE]]
dash -c CODE NAME [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c CODE | Befehlszeichenfolge ausführen. |
| -n | Syntax prüfen, ohne normale Skriptbefehle auszuführen. |
| -s | Befehle aus Standardeingabe. |
| -x | Ausführung protokollieren; kein Datenschutzmodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
cat > own.sh <<'DASHCODE'
value=$1
test "$value" = wort || exit 1
printf 'Dash-Argument=%s\n' "$value"
DASHCODE
dash -n own.sh
env -u ENV dash own.sh wort
```

### Schritt 3: Ergebnis einordnen

Das eigene Skript nutzt einfache Zuweisung, test und printf. Syntaxprüfung und Ausführung sind zwei getrennte erfolgreiche Schritte. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Portablen Shellcode auf einer weiteren Implementierung prüfen; Bash-Abhängigkeiten erkennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein erfolgreiches dash -n beweist keine fehlerfreie Logik. Fremde Skripte nicht für eine Kompatibilitätsprobe ausführen. Hier wurde keine Anmeldeshell geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bad substitution | Verwendete Erweiterung gehört möglicherweise nicht zur Dash-Sprache. |
| Unerwarteter Startcode | Login-/Interaktivmodus und ENV prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Dash-Paket 0.5.12-6ubuntu5. Praktisch geprüft: Eigenes minimales Skript geprüft; vollständige POSIX-Kompatibilität nicht behauptet. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| bash | Shell mit zusätzlichen Funktionen. |
| sh | Name kann auf Dash zeigen. |
| getopts | Optionen portabel verarbeiten. |

Ausgangsdatensatz 537 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
