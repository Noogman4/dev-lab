---
id: "return"
name: "return"
command: "return"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "return"]
status: "Lokale Primärhilfe und zwei Funktionspfade praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 93
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# return – Eine Funktion mit einem bewussten Status verlassen

## 1. Kurzbeschreibung

`return` ist ein Shell-Builtin zum Verlassen einer Funktion oder einer mit `source` beziehungsweise `.` eingelesenen Skriptdatei. **Root-Rechte sind nicht nötig.** Es beendet normalerweise nicht die gesamte aufrufende Shell; dafür ist `exit` der andere Mechanismus.

Der übergebene Wert ist ein Rückgabestatus. Ein Textresultat wird dagegen etwa über Standardausgabe oder eine ausdrücklich vereinbarte Variable geliefert.

## 2. Was macht der Befehl?

Die Ausführung des aktuellen Funktionskörpers endet sofort. An der Aufrufstelle kann der weitere Shellablauf den Status auswerten. Befehle hinter `return` im verlassenen Körper werden nicht mehr ausgeführt.

Ohne Argument wird der Status der zuletzt ausgeführten Anweisung übernommen. Ein zusätzliches `printf` unmittelbar davor kann daher einen älteren Fehlerstatus überdecken. Primärquelle ist die lokal gelesene Hilfe `help return` aus Bash 5.2.21; weiterführend: [Bash-Funktionen](https://www.gnu.org/software/bash/manual/html_node/Shell-Functions.html) und die Builtin-Beschreibung.

Außerhalb einer Funktion oder passenden eingelesenen Datei ist der Aufruf kein allgemeiner „zurück zum Prompt“-Befehl. Der Kontext muss stimmen.

## 3. Syntax

```text
return
return STATUS
```

Für eigene Statuskonventionen kleine Werte im üblichen Bereich 0–255 wählen: 0 für Erfolg, andere Werte für dokumentierte Fälle. Nicht auf unbegrenzt große Zahlen oder sprachübergreifend identische Spezialregeln vertrauen. Ein Status ist keine beliebig große Ergebnisspeicherung.

## 4. Wichtige Optionen

Es gibt keine gewöhnliche Optionsfamilie.

| Form | Bedeutung | Hinweis |
| --- | --- | --- |
| `return 0` | Funktionspfad als erfolgreich beenden. | Nur passend zum tatsächlichen Ergebnis setzen. |
| `return 2` | Eigenen dokumentierten Nichterfolgsfall melden. | Bedeutung muss die Funktion erklären. |
| `return` | Letzten Status übernehmen. | Vorherige Befehle können ihn verändert haben. |
| `status=$?` | Status unmittelbar sichern. | Danach kann er bewusst ausgegeben oder weitergereicht werden. |
| `help return` | Lokale Semantik lesen. | Kein Verlassen der Funktion durch den Hilfeaufruf. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine kleine Prüffunktion definieren

```bash
pruefe() {
  if [ "$1" != ja ]; then
    return 2
  fi
  printf 'Wert passt\n'
  return 0
}
```

Die Funktion erwartet hier einen ausdrücklich übergebenen Testwert. Alles außer `ja` wird als Fall 2 behandelt. Diese Konvention ist selbst festgelegt, keine universelle Bedeutung des Statuswerts 2 für alle Linuxprogramme.

### Schritt 2: Nichterfolg unmittelbar auswerten

```bash
if pruefe nein; then
  printf 'Unerwartet\n'
else
  status=$?
  printf 'Abgelehnt, Status %s\n' "$status"
fi
pruefe ja
```

`pruefe nein` erreicht `return 2` und gibt `Wert passt` nicht aus. Im Restfall wird der Funktionsstatus sofort gesichert. Der zweite Aufruf erreicht dagegen den normalen Ausgabeweg und endet mit 0.

### Schritt 3: Erwartete Ausgabe kontrollieren

```text
Abgelehnt, Status 2
Wert passt
```

Die Elternshell läuft nach dem ersten Nichterfolg weiter, weil dieser bewusst in der Auswahl behandelt wurde. Das Beispiel verändert keine Datei und erteilt keine reale Systemfreigabe.

## 6. Typische Anwendungsfälle

### Eingaben früh zurückweisen

Eine Funktion prüft Voraussetzungen am Anfang und verlässt bei klar definierten Fehlern den Körper. Dadurch bleibt der normale Arbeitsweg übersichtlich.

### Hilfsfunktion mit Statusschnittstelle

Ein Aufrufer entscheidet anhand dokumentierter Statuswerte, ob er fortfahren kann. Ausgabe und Status getrennt erklären, damit Protokolltext nicht als Erfolgserkennung dienen muss.

### Eingelesene Skriptdatei verlassen

Code, der bewusst in die aktuelle Shell eingelesen wird, kann mit `return` enden. Das ist ein anderer Ausführungskontext als ein separat gestartetes Skript und verlangt gesonderte Sorgfalt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Bereits ausgeführte Änderungen werden nicht rückgängig gemacht. Eine Datei bleibt geschrieben, auch wenn danach `return 2` folgt. Notwendige Abschlussarbeiten dürfen nicht versehentlich hinter der Sprungstelle stehen.

Ein pauschales `return 0` kann echte Fehler verschleiern. Umgekehrt kann ein erwarteter Nichterfolgsstatus bei strenger Fehlerbehandlung den größeren Ablauf beeinflussen, wenn er nicht passend behandelt wird. `return` und `exit` nicht austauschen: Ein falsch eingesetztes `exit` in eingelesenem Code kann die aufrufende Sitzung beenden.

## 8. Häufige Fehler

- **Text an return übergeben:** Rückgabestatus und Textausgabe verwechselt.
- **Außerhalb des gültigen Kontexts:** Kein Funktions- oder source-Aufruf aktiv.
- **Falscher Status übernommen:** Eine Meldung oder andere Anweisung lief zwischen Fehler und Sicherung.
- **Fehler wird als Erfolg gemeldet:** Letztes `return 0` ohne Bewertung früherer Schritte.
- **Aufräumcode fehlt:** Er wurde durch einen frühen Rücksprung übersprungen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Statuswerte je Funktion kurz dokumentieren und in kleinen eigenen Beispielen alle Pfade betrachten. Einen Fehlerstatus früh sichern und anschließend bewusst zurückgeben. Für Ausgabe feste `printf`-Formate verwenden, statt Eingabedaten zu Code zu machen.

**Prüfstand:** Bash 5.2.21 und lokale Hilfe gelesen. Beide Funktionspfade in einer getrennten Bash ohne persönliche Startdateien ausgeführt; Status 2 im ersten Pfad erfasst, zweiter Pfad erfolgreich, erwartete zwei Zeilen. Keine Benutzerdateien verändert. Eingelesene Skripte, Traps, ungewöhnliche Statuszahlen und `set -e`-Sonderfälle nicht praktisch geprüft.

## 10. Verwandte Befehle

- `function`: Funktionsdefinition.
- `exit`: gesamten ausführenden Shellprozess beenden.
- `break`, `continue`: Schleifenfluss statt Funktionsende steuern.
- `source`: Datei in die aktuelle Shell einlesen und ausführen.

Ausgangseintrag: Datensatz 93 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
