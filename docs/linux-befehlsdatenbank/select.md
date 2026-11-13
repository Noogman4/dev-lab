---
id: "select"
name: "select"
command: "select"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "select"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 554
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# select – Eine Auswahl aus einer Liste auswerten

## 1. Kurzbeschreibung

select ist in Bash ein Sprachkonstrukt für nummerierte Auswahlmenüs.

## 2. Was macht der Befehl?

Die Menüwörter werden ausgegeben und eine Eingabe gelesen. Die gewählte Zeichenfolge landet in der Schleifenvariablen; die rohe Antwort in REPLY. Eine ungültige Nummer ergibt einen leeren Auswahlwert. Die Schleife endet nicht automatisch nach einer gültigen Auswahl; break oder EOF beendet sie. Die Angaben beziehen sich ausdrücklich auf Bash; andere Shells können abweichen.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help select`; [GNU-Handbuchverweis](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html) (Onlineabruf fehlgeschlagen; Funktionsangaben mit der installierten Primärhilfe geprüft)

## 3. Syntax

```text
select NAME in WORT ...; do BEFEHLE; done
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| PS3 | Eingabeaufforderung für select. |
| REPLY | Ursprüngliche Eingabe. |
| NAME | Gewähltes Wort oder leer bei ungültiger Nummer. |
| break | Schleife ausdrücklich verlassen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -u BASH_ENV bash --noprofile --norc <<'BASHCASE'
set -e
select lesson_choice in eins zwei; do
  test "$REPLY" = 2 || exit 1
  test "$lesson_choice" = zwei || exit 1
  printf 'Auswahl=%s\n' "$lesson_choice"
  break
done <<'CHOICE'
2
CHOICE
BASHCASE
```

### Schritt 3: Ergebnis einordnen

Die eigene feste Eingabe 2 wählt zwei. Menüausgabe auf Standardfehler ist dabei normal und kein Testfehler. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine eigene Auswahlmenüs entwerfen; gültige und ungültige Eingaben unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Menü bestätigt keine Freigabe durch den Benutzer, wenn die Eingabe aus einer Datei stammt. Für reale Aktionen eigene bewusste Bestätigung erforderlich. Hier wird nur Text ausgegeben.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Schleife bleibt offen | break beziehungsweise EOF fehlt. |
| Leerer Auswahlwert | Eingabe war keine gültige Nummer. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Eigener abgegrenzter Shellfall geprüft; fremde Startdateien, andere Shells und weitere Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| read | Eingabe ohne Menü. |
| case | Auswahlzweige bearbeiten. |
| bash | Benötigte Shellsprache. |

Ausgangsdatensatz 554 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
