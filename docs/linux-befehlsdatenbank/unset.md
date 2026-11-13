---
id: "unset"
name: "unset"
command: "unset"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "unset"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 561
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# unset – Eigene Variablen oder Funktionen entfernen

## 1. Kurzbeschreibung

unset entfernt Shellvariablen beziehungsweise Funktionen im aktuellen Shellkontext.

## 2. Was macht der Befehl?

Ein leerer Wert und eine nicht gesetzte Variable sind unterschiedliche Zustände. -v und -f benennen die beabsichtigte Art ausdrücklich. Bei Namensreferenzen wirkt -n auf die Referenz selbst statt auf deren Ziel. Schreibgeschützte Variablen lassen sich nicht einfach entfernen. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help unset`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
unset [-v oder -f oder -n] NAME ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -v NAME | Variable entfernen. |
| -f NAME | Funktion entfernen. |
| -n NAME | Namensreferenz selbst entfernen. |
| NAME | Bekannter Bezeichner, kein auszuwertender Fremdtext. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
lesson_unused=
test "${lesson_unused+x}" = x
unset -v lesson_unused
test "${lesson_unused+x}" != x
printf 'Leer und nicht gesetzt unterschieden\n'
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Die eigene zunächst leere Variable ist vorhanden; nach unset fehlt sie. Die Parameterexpansion prüft Existenz, ohne einen unbekannten Wert als Code auszuführen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Temporäre eigene Shellwerte entfernen; fehlende Konfiguration von leerem Wert unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Spezielle Variablen wie PATH, IFS oder Shellzustandsvariablen können weitere Befehle beeinflussen. Nur eigene Testnamen entfernen. Arrayindizes und Referenzziele nicht ungeprüft aus Fremdeingaben bilden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Readonly variable | Schreibschutz verhindert Entfernen. |
| Falsches Objekt entfernt | Mit -v oder -f die Art eindeutig angeben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| export | Exportattribut verwalten. |
| declare | Variablenattribute. |
| readonly | Entfernen verhindern. |

Ausgangsdatensatz 561 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
