---
id: "times"
name: "times"
command: "times"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "times"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 511
reviewed_at: "2026-11-13"
locally_checked_version: "Bash 5.2.21"
---

# times – Kumulierte CPU-Zeit der Shell anzeigen

## 1. Kurzbeschreibung

times ist ein Shell-Builtin und zeigt aufgelaufene CPU-Zeiten der Shell und ihrer Kinder.

## 2. Was macht der Befehl?

Bash gibt zwei Zahlenpaare aus: Benutzer- und Systemzeit der Shell sowie entsprechende Zeiten ihrer Kinder. Das ist keine Stoppuhr für den letzten Befehl. Sehr kleine Läufe können wegen der Ausgabeauflösung als Null erscheinen. Es gibt keine Dateinamenargumente und kein versionsunabhängiges --help.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: Bash 5.2 `help times`; [Bash-Projekt](https://www.gnu.org/software/bash/) (Handbuchabruf online fehlgeschlagen)

## 3. Syntax

```text
times
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| ohne Argument | Kumulierte Benutzer- und Systemzeiten ausgeben. |
| help times | Bash-interne Hilfe lesen. |
| Shell-Kontext | Werte gehören zur aufrufenden Shell, nicht zum ganzen Rechner. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
bash --noprofile --norc -c 'times; printf "Shellzeiten angezeigt\n"'
```

### Schritt 3: Ergebnis einordnen

Die Messung stammt aus einer neu gestarteten Bash. Die konkreten Zahlen sind laufabhängig; geprüft ist der erfolgreiche Builtin-Aufruf, nicht eine Mindestdauer. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Shell-interne Zeitwerte verstehen; Abgrenzung zur Einzelmessung mit time vermitteln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine stark belastete Arbeitsmaschine wird nicht vermessen. Werte verschiedener Shell-Lebensdauern sind nicht direkt vergleichbar. Es werden keine Limits und keine Prozessprioritäten verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Command not found | Builtin der verwendeten Shell prüfen. |
| Immer 0m0.000s | Kurze CPU-Zeit und Ausgabeauflösung beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** Bash 5.2.21. Praktisch geprüft: Builtin in neuer Shell geprüft; quantitative Zeitmessung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| time | Einzelnen Befehl messen. |
| wait | Eigene Kinder abwarten. |
| ps | Prozessdaten abfragen. |

Ausgangsdatensatz 511 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
