---
id: "yes"
name: "yes"
command: "yes"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["yes", "grundlagen & hilfe"]
status: "Kein unbegrenzter Ausgabelauf gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 379
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4 gelesen"
---

# yes – wiederholte Ausgabe und automatische Bestätigung auseinanderhalten

## 1. Kurzbeschreibung

`yes` gibt eine Zeile wiederholt aus, bis es beendet wird oder der Ausgabekanal nicht mehr nutzbar ist. Ohne Text wird üblicherweise `y` wiederholt. **Root-Rechte sind nicht nötig.**

## 2. Was macht der Befehl?

Die lokale GNU-Manpage beschreibt eine Endlosschleife für Ausgabe. Das Werkzeug versteht nicht die Bedeutung einer nachgeschalteten Frage. Es bestätigt nur mechanisch durch Text, wenn dieser an ein anderes Programm geleitet wird.

Damit sind reine Ausgabedemonstration und automatische Zustimmung zu echten Änderungen sehr verschieden. Ein beliebiger nachgeschalteter Prozess kann diesen Text unterschiedlich interpretieren.

## 3. Syntax

```text
yes [TEXT ...]
yes --help
```

Ein Aufruf nur mit eigenem Text ist nicht von selbst begrenzt. Für ein kleines Beispiel muss der Ausgabekanal begrenzt werden.

## 4. Wichtige Optionen

| Form | Aufgabe | Grenze |
| --- | --- | --- |
| Ohne Text | Wiederholt `y`. | Kann Antworten ungeprüft bejahen. |
| Mit Text | Wiederholt die zusammengesetzte Zeile. | Keine Bedeutungskontrolle. |
| `--help` | Hilfe anzeigen und beenden. | Kein Endloslauf. |
| `--version` | Version anzeigen und beenden. | Kein Lasttest. |

Es gibt keine hier vorausgesetzte allgemeine Option für „genau drei Zeilen“. Die Begrenzung im Beispiel stammt vom nachgeschalteten `head`.

## 5. Beispiel erklärt Schritt für Schritt

```bash
yes 'Eigener Beispieltext' | head -n 3
```

`yes` erzeugt den Text wiederholt. `head` nimmt drei Zeilen und beendet seinen Lesezugriff. Danach kann der Schreiber wegen geschlossenem Pipeende enden.

Das Beispiel wurde nicht gestartet. Es erzeugt keine tatsächliche lokale Messung. In Shells mit `pipefail` kann der Status des geschlossenen Schreibkanals außerdem als Fehler der gesamten Pipeline sichtbar werden, obwohl die drei Zeilen beabsichtigt waren.

Eine solche Statusbedeutung vor Einsatz in Tests oder Skripten klären. Sie ist kein allgemeiner Systemdefekt.

## 6. Typische Anwendungsfälle

- Begrenzte eigene Beispielausgabe erzeugen.
- Pipes und deren Ende erklären.
- Kontrollierten Testdatenstrom unter ausdrücklich begrenztem Umfang planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbegrenzt kann der Aufruf CPU und Ausgabekanal belasten. Eine Umleitung in eine Datei kann Speicher füllen.

`yes` vor Installations-, Lösch- oder Reparaturprogrammen kann Rückfragen automatisch bestätigen. Nicht verwenden, um unklare Entscheidungen oder erforderliche Zustimmung zu umgehen. Die Bedeutung jeder Frage bleibt unbekannt.

## 8. Häufige Fehler

- **Automatisches Ende erwartet:** Ohne Begrenzung nicht vorgesehen.
- **Alle Fragen bedeuten dasselbe:** Programm versteht sie nicht.
- **Pipelinefehler nach `head` als Defekt:** Geschlossenes Pipeende berücksichtigen.
- **Dateiausgabe unbegrenzt:** Ziel kann volllaufen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für wenige feste Meldungen einfach `printf` verwenden. `yes` nur einsetzen, wenn ein wiederholter Datenstrom wirklich gebraucht und dessen Ende geplant ist.

Keine pauschale automatische Zustimmung in Verwaltungsbeispielen. Eine konkrete dokumentierte nicht interaktive Schnittstelle des Zielprogramms ist fachlich separat zu bewerten.

## 10. Verwandte Befehle

- `printf`: Endliche kontrollierte Ausgabe.
- `head`: Begrenzte Eingabemenge lesen.
- `seq`: Begrenzte Zahlenfolge.
- `timeout`: Laufdauer begrenzen; eigener Statuskontext.

**Prüfstand:** Lokale Manpage gelesen. Keine Endlosausgabe und keine Verwaltungsfrage automatisch bestätigt.

Ausgangsdatensatz 379 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
