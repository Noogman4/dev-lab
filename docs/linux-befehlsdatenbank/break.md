---
id: "break"
name: "break"
command: "break"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "break"]
status: "Lokale Primärhilfe und begrenztes Schleifenbeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 72
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# break – Eine laufende Shellschleife gezielt verlassen

## 1. Kurzbeschreibung

`break` ist ein Shell-Builtin, das eine laufende Schleife vorzeitig beendet. Es wird beispielsweise verwendet, sobald ein gesuchter Wert gefunden wurde. **Root-Rechte sind nicht nötig.** Der Befehl beendet nicht automatisch das ganze Skript und ist kein allgemeiner Prozess-Stoppbefehl.

## 2. Was macht der Befehl?

Innerhalb einer `for`-, `while`-, `until`- oder passenden `select`-Schleife springt `break` hinter das zugehörige Schleifenende. Befehle im übrigen aktuellen Schleifendurchlauf werden übersprungen; nach der Schleife kann das Skript weiterlaufen.

Mit einer positiven Zahl können mehrere verschachtelte Schleifen verlassen werden. Diese Zahl ist keine Prozessnummer. Bei schwer nachvollziehbarer Verschachtelung ist ein klarerer Funktionsaufbau häufig leichter zu warten. Primärquelle ist die lokal gelesene Hilfe `help break` aus Bash 5.2.21. Weiterführend: [Bash-Handbuch](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html); der Onlineabruf war hier nicht verfügbar, die lokale Hilfe und Ausführung wurden geprüft.

## 3. Syntax

```text
break
break ANZAHL
```

Ohne Zahl gilt eine Schleifenebene. `ANZAHL` muss eine positive ganze Zahl sein. Die Anwendung muss im aktiven Schleifenkontext erfolgen; ein isolierter Aufruf an einem gewöhnlichen Prompt erklärt deshalb die eigentliche Wirkung nicht.

## 4. Wichtige Optionen

`break` hat keine allgemeine `--help`-Option. Die Hilfe wird über `help break` gelesen.

| Form | Bedeutung | Hinweis |
| --- | --- | --- |
| `break` | Innerste aktive Schleife verlassen. | Code hinter deren `done` wird weiter ausgeführt. |
| `break 1` | Dasselbe ausdrücklich angeben. | Die 1 ist ein Argument, kein Schalter. |
| `break 2` | Zwei umschließende Schleifen verlassen. | Nur bei bewusst verstandener Verschachtelung verwenden. |
| `help break` | Installierte Hilfe lesen. | Führt keine Schleifenaktion aus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene begrenzte Schleife betrachten

Das Beispiel verwendet nur feste Zahlen und `printf`. Es liest oder verändert keine Dateien.

```bash
for zahl in 1 2 3 4; do
  if [ "$zahl" -eq 3 ]; then
    break
  fi
  printf '%s\n' "$zahl"
done
printf 'Fertig\n'
```

### Schritt 2: Die ersten Durchläufe verstehen

Für 1 und 2 ist der Vergleich mit 3 falsch. Der bedingte `break` wird deshalb nicht ausgeführt; `printf` zeigt die Zahl. Bei 3 ist die Bedingung erfüllt und `break` verlässt die gesamte Schleife. Die Ausgabe der 3 wird damit ebenso übersprungen wie der Durchlauf für 4.

### Schritt 3: Erwartete Ausgabe prüfen

```text
1
2
Fertig
```

`Fertig` beweist hier, dass der Ablauf nach `done` weitergeht. Würde stattdessen `exit` verwendet, könnte die gesamte laufende Shell beziehungsweise das Skript enden. Ein erfolgreicher Ablauf dieses Beispiels sagt nichts über sichere Bereinigung in einem echten Dateiverarbeitungsjob aus.

## 6. Typische Anwendungsfälle

### Suche nach dem ersten Treffer

Sobald ein passender Eintrag gefunden wurde, müssen weitere Einträge nicht mehr betrachtet werden. Das spart unnötige Arbeit, wenn nur ein Ergebnis benötigt wird.

### Begrenzte Wiederholungsversuche

Ein Versuch innerhalb einer Schleife ist erfolgreich; `break` beendet die weiteren Versuche. Daneben trotzdem eine maximale Anzahl und eindeutige Fehlerbehandlung vorsehen.

### Bedienmenü verlassen

Eine Menüschleife kann durch eine ausdrücklich ausgewählte Ende-Option beendet werden. Andere Programmbereiche können danach noch geordnet aufräumen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Sprung überspringt alle verbleibenden Befehle im betroffenen Schleifenkörper. Wenn dort Bereinigung, Freigabe einer Ressource oder notwendige Statusmeldung liegt, wird sie nicht mehr ausgeführt. Solche Aufgaben bewusst hinter die Schleife oder in einen geeigneten geordneten Abschluss legen.

`break` hebt keine bereits ausgeführten Aktionen auf. Eine zuvor geänderte Datei bleibt geändert. Bei Pipelines können Schleifen in einer Subshell laufen; ein dortiges `break` steuert nicht beliebige äußere Prozesse. Hohe Ebenenzahlen machen den Ablauf schwerer nachvollziehbar.

## 8. Häufige Fehler

- **Außerhalb einer Schleife aufgerufen:** Es fehlt der passende aktive Kontext.
- **Nur den aktuellen Durchlauf überspringen wollen:** Dafür ist `continue` vorgesehen.
- **Ganzes Skript beendet erwartet:** `break` wirkt auf Schleifen, nicht wie `exit`.
- **Falsche Verschachtelungsebene:** `break 2` springt weiter als `break`.
- **Bereinigung fehlt:** Sie stand hinter dem Sprung innerhalb des verlassenen Körpers.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer einzigen kleinen Schleife und sichtbaren Ausgaben beginnen. Erst danach mehrere Ebenen einführen. Abbruchbedingungen klar benennen und wichtige Abschlussarbeiten unabhängig vom verbleibenden Schleifenkörper planen.

**Prüfstand:** Lokale Bash-5.2.21-Hilfe gelesen. Das Zahlenbeispiel in einer separaten Bash ohne persönliche Startdateien ausgeführt; exakt `1`, `2`, `Fertig` erhalten, Status 0. Keine Benutzerdateien oder Systemkonfiguration verändert. Mehrfach verschachtelte, nebenläufige und Pipeline-Abläufe nicht praktisch geprüft.

## 10. Verwandte Befehle

- `continue`: nur den verbleibenden aktuellen Durchlauf überspringen.
- `return`: eine Funktion oder eingelesene Skriptdatei verlassen.
- `exit`: die ausführende Shell beenden.
- `for`, `while`, `until`: Schleifenkonstrukte, innerhalb derer `break` eingesetzt wird.

Ausgangseintrag: Datensatz 72 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
