---
id: "false"
name: "false"
command: "false"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["false", "grundlagen & hilfe"]
status: "Statusbedeutung dokumentiert; keine Fehlerheilung behauptet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 354
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# false – einen absichtlich negativen Rückgabestatus erzeugen

## 1. Kurzbeschreibung

`false` beendet sich mit einem erfolglosen Rückgabestatus. Das ist seine vorgesehene Aufgabe. **Root-Rechte sind nicht nötig.** Im normalen Gebrauch wird kein Text ausgegeben.

## 2. Was macht der Befehl?

Nach der lokalen Bash-Hilfe ist der Zweck ausschließlich ein negatives Ergebnis. Eine Shellbedingung kann darauf reagieren. `false` sagt nichts über Netzwerk, Dateien oder den tatsächlichen Gesundheitszustand eines Systems aus.

Bash besitzt ein Builtin; daneben kann ein externes Programm existieren. Für Hilfsoptionen nicht ohne Prüfung dieselben Regeln annehmen. Beim Builtin hilft `help false`.

## 3. Syntax

```bash
false
if false; then
  printf '%s\n' 'Dieser Zweig wird nicht gewählt'
else
  printf '%s\n' 'Bedingung ist absichtlich negativ'
fi
```

Der Status steuert die Bedingung. Es wird kein fremder Fehler untersucht.

## 4. Wichtige Optionen

Für den normalen Zweck sind keine Optionen nötig. Argumente sind kein Grund, eine andere fachliche Bedeutung hineinzulesen.

| Ausdruck | Bedeutung | Folge |
| --- | --- | --- |
| `false` | Erfolgloser Status. | Negativer Bedingungsausgang. |
| `! false` | Shell verneint den Status. | Positiver Bedingungsausgang. |
| `true` | Gegenteilige einfache Statusfunktion. | Kein Test der Umgebung. |

## 5. Beispiel erklärt Schritt für Schritt

Im obigen `if` wird zunächst `false` ausgeführt. Die Shell erkennt den negativen Status und wählt den `else`-Zweig. Die erwartete Meldung beschreibt daher nur den selbst gewählten Kontrollfluss.

Der Ablauf ist aus der lokalen Hilfe beschrieben, nicht als unabhängiger Systemtest ausgeführt. Keine Datei muss dafür existieren und kein Dienst erreichbar sein.

Wird anschließend der Status einer anderen Aktion betrachtet, ist der frühere Status bereits ersetzt. Für Skripte immer den tatsächlich gemeinten Aufruf unmittelbar bewerten.

## 6. Typische Anwendungsfälle

- Einen negativen Zweig in einem eigenen Beispiel erklären.
- Kontrollfluss ohne absichtliche echte Systemstörung demonstrieren.
- Einen vorläufig bewusst erfolglosen Zustand kennzeichnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

In Skripten mit Abbruchregeln kann ein ungeschütztes `false` den Ablauf beenden. Deshalb nicht beiläufig in eine laufende Verwaltungssitzung mit unbekannten Einstellungen einfügen.

Eine Fehlerunterdrückung oder ein absichtlicher Status ersetzt keine fachliche Fehlerbehandlung. Keine echte fehlgeschlagene Operation durch einen willkürlichen Status als geklärt darstellen.

## 8. Häufige Fehler

- **Kein Text, also nichts passiert:** Der Status ist die Ausgabeinformation.
- **Negativ gleich Defekt:** Hier ist es beabsichtigt.
- **Später `$?` lesen:** Ein dazwischenliegender Befehl hat den Status ersetzt.
- **Hilfsoptionen überall gleich:** Builtin und externes Programm unterscheiden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für Übungen einen klaren `if`-Block nutzen. So wird der erwartete negative Status ausdrücklich behandelt.

Ein Beispiel mit `false` nicht als realen Fehlerbericht bezeichnen. Der Wert wurde absichtlich erzeugt, nicht aus der Umgebung gemessen.

## 10. Verwandte Befehle

- `true`: Positiven Status liefern.
- `test`: Eine tatsächliche Bedingung bewerten.
- `return`: Status einer Funktion setzen.
- `exit`: Shell beziehungsweise Skript beenden.

**Prüfstand:** Lokale Hilfe gelesen. Keine Dienste oder Dateien für einen Fehlerfall verändert.

Ausgangsdatensatz 354 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
