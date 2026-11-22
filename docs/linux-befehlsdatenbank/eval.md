---
id: "eval"
name: "eval"
command: "eval"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "eval"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 541
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# eval – Zusammengesetzten Text als Shellcode ausführen

## 1. Kurzbeschreibung

eval verbindet seine Argumente und interpretiert das Ergebnis erneut als Shellcode.

## 2. Was macht der Befehl?

Es gibt eine zweite Auswertungsstufe. Zeichen, die zuvor Daten waren, können beim erneuten Parsen Operatoren oder Expansionen werden. eval ist daher keine sichere Methode, um unbekannte Texte oder Dateinamen auszuführen. Ein Array oder direkter Funktionsaufruf vermeidet in vielen Fällen diese zusätzliche Codeebene. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help eval`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
eval [ARGUMENT ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Argumente | Werden mit Zwischenräumen zu Shelltext verbunden. |
| Rückgabestatus | Status des ausgewerteten Befehls. |
| Keine Argumente | Erfolgreicher leerer Aufruf, kein Verarbeitungstest. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
eval 'lesson_value=fest'
test "$lesson_value" = fest
printf 'Feste Zuweisung ausgewertet\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Nur eine fest im Beispiel geschriebene Zuweisung wird ausgewertet. Es wird keinerlei Fremdeingabe an eval übergeben. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Vorhandene Shellskripte verstehen; eine notwendige zusätzliche Auswertungsstufe im Review erkennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Eingaben können Befehle einschleusen. Auch scheinbar ausreichende Anführungszeichen schützen nicht jede Auswertungsstufe. Keine generischen Kommandozeichenfolgen aus Benutzerdaten bilden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Sonderzeichen werden aktiv | Zweite Shellauswertung beachten. |
| Argumentgrenzen gehen verloren | Direkte Argumentübergabe oder Bash-Array verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| bash | Ausführender Interpreter. |
| printf | Daten mit festem Format ausgeben. |
| declare | Variablen ohne Codeaufbau verwalten. |

Ausgangsdatensatz 541 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
