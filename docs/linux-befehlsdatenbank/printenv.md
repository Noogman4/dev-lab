---
id: "printenv"
name: "printenv"
command: "printenv"
category: "Shell & Skripting"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Shell & Skripting", "printenv"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 550
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# printenv – Einzelne Umgebungswerte ausgeben

## 1. Kurzbeschreibung

printenv zeigt die Umgebung seines Prozesses oder ausgewählte benannte Werte.

## 2. Was macht der Befehl?

Shellvariablen ohne Export gehören nicht automatisch zur Umgebung des gestarteten printenv. Für einen bekannten Namen wird dessen Wert ausgegeben; fehlt der Name, liefert GNU printenv einen Nichtnullstatus. Eine Ausgabe aller Werte kann Geheimnisse preisgeben.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: GNU coreutils `printenv --help`; [Handbuchverweis](https://www.gnu.org/software/coreutils/manual/html_node/printenv-invocation.html) (Onlineabruf gestört)

## 3. Syntax

```text
printenv [OPTIONEN] [VARIABLE ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| VARIABLE | Nur diese Umgebungsvariable lesen. |
| -0 | Werte mit NUL statt Zeilenende abschließen. |
| --version | Implementierung anzeigen. |
| ohne Namen | Gesamte Umgebung anzeigen; für Diagnose meist zu breit. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
env -i LESSON_VALUE=eigen /usr/bin/printenv LESSON_VALUE > value.txt
test "$(cat value.txt)" = eigen
if env -i /usr/bin/printenv LESSON_MISSING; then exit 1; fi
printf 'Vorhandenen und fehlenden Eigenwert geprueft
'
```

### Schritt 3: Ergebnis einordnen

Ein eigener vorhandener Wert und ein in leerer Umgebung fehlender Name werden unterschieden. Keine reale vollständige Benutzerumgebung wird ausgegeben. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Vererbung einer gezielten Programmeinstellung prüfen; fehlende Variable von leerem Wert unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausgaben nicht ungeprüft in Supportberichte kopieren. Ein leerer ausgegebener Wert mit Status 0 unterscheidet sich von einem nicht vorhandenen Namen. Keine Konfiguration wird gesetzt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Shellwert fehlt | Exportattribut und Kindumgebung prüfen. |
| Mehrzeiliger Wert | Zeilentrennung ist nicht immer eindeutige Datenstruktur; -0 berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Eigene vorhandene und fehlende Variable geprüft; komplexe Werte und andere Implementierungen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| env | Kindumgebung aufbauen. |
| export | Vererbung markieren. |
| set | Kann zusätzliche Shellvariablen zeigen. |

Ausgangsdatensatz 550 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
