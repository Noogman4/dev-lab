---
id: "nice"
name: "nice"
command: "nice"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "nice"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 496
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# nice – Aktuellen Nice-Wert ohne Anpassung auslesen

## 1. Kurzbeschreibung

GNU nice startet normalerweise ein Programm mit angepasster Niceness. Ohne Programmoperand gibt es nur die aktuelle Niceness aus. Diese reine Anzeige wird hier geprüft.

## 2. Was macht der Befehl?

Kleinere Nice-Werte begünstigen den Prozess, größere reduzieren seinen relativen CPU-Anspruch. GNU -n bezeichnet eine Addition zum geerbten Wert, keinen absoluten Zielwert. Die Wirkung hängt von konkurrierender Last und Schedulingkontext ab. Nice ist weder CPU-Limit noch I/O-Priorität oder Echtzeitpolicy.

Quelle, am 2026-11-13 gelesen: Lokale Primärquelle: GNU-coreutils-Manpage nice; [Projektverweis nice](https://www.gnu.org/software/coreutils/nice) (Online-Vollabruf nicht verfügbar)

## 3. Syntax

```text
nice
nice [-n AENDERUNG] BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Ohne BEFEHL | Aktuelle Niceness anzeigen. |
| `-n N`, `--adjustment=N` | N zum geerbten Nice-Wert addieren. |
| Ohne -n mit Programm | GNU-Vorgabe ist Anpassung um +10. |
| Werte -20 bis 19 | GNU/Linux-Nicenessbereich, kein Prozentwert. |
| `--version`, `--help` | CLI-Stand und lokale Semantik prüfen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
nice --version
nice > /dev/null
aktueller_wert="$(nice)"
printf 'Aktueller Nice-Wert: %s\n' "$aktueller_wert"
```

### Schritt 3: Ergebnis einordnen

Der angezeigte Wert wird nicht als festes Soll vorausgesetzt. Kein nice-Aufruf besitzt einen Programmoperanden oder -n; dadurch wird keine neue Niceness gesetzt. Dies ist ein Funktionstest der Anzeige, kein Nachweis einer messbaren Prioritätswirkung. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Prioritäten verstehen:** Relativen Wert von Ressourcenlimit trennen. **Skripte prüfen:** Additive nice-Anpassung nicht mit renice-Syntax gleichsetzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Höhere Priorität benötigt gegebenenfalls Rechte/Limits und kann andere Arbeit beeinträchtigen. Ein Programmstart unter nice führt trotzdem dessen gesamten Code aus. Keine Priorität eigener oder fremder Prozesse geändert und keine Last erzeugt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Wert anders als erwartet | Geerbten Wert und additive Anpassung berücksichtigen. |
| Operation not permitted | Rechte-/Limitgrenze bei begünstigender Änderung. |
| Keine Laufzeitverbesserung | Nice garantiert weder CPU-Anteil noch Beschleunigung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur Version und nice ohne Programmoperand ausgeführt, Wert gelesen. Keine Niceness gesetzt. Lastwirkung, negative Anpassung, Rechte und andere Implementierungen praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `renice` | Vorhandene Prozesse, eigene Optionssemantik. |
| `chrt` | Schedulerpolicy und Echtzeitpriorität. |
| `ionice` | I/O-Priorität. |

Ausgangsdatensatz 496 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
