---
id: "caller"
name: "caller"
command: "caller"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "caller"]
status: "Lokale Primärhilfe und verschachtelter Funktionsaufruf praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 73
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# caller – Den Aufrufkontext einer Bash-Funktion untersuchen

## 1. Kurzbeschreibung

`caller` ist ein Bash-Builtin für Diagnoseausgaben über den aktuellen Funktionsaufruf. Es kann zeigen, aus welcher Zeile und welchem Kontext eine Funktion erreicht wurde. **Root-Rechte sind dafür nicht nötig.** Es untersucht den Ablauf der eigenen Shell, nicht beliebige fremde Prozesse.

## 2. Was macht der Befehl?

Beim Aufrufen einer Funktion entsteht ein Aufrufrahmen. Verschachtelte Funktionen bilden mehrere solcher Rahmen. `caller` kann einen passenden Rahmen abfragen und dessen Kontext auf die Standardausgabe schreiben.

Ohne Argument enthält die Ausgabe Zeile und Quelldatei. Mit einer nichtnegativen Rahmennummer kommt ein Funktionsname hinzu. `0` bezeichnet den nächsten verfügbaren Aufrufrahmen; größere Zahlen gehen weiter zurück. Primärquelle ist die lokal gelesene Hilfe `help caller` aus Bash 5.2.21. Die weiterführende Onlinebeschreibung steht im [Bash-Handbuch](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html); dessen Abruf war hier nicht verfügbar, daher beruht die konkrete Prüfung auf der installierten Hilfe und dem Test.

## 3. Syntax

```text
caller
caller RAHMENNUMMER
```

`RAHMENNUMMER` ist ein ganzzahliges Argument, kein Prozessbezeichner und keine Dateizeile, zu der gesprungen wird. `caller` verändert den Kontrollfluss nicht. Es kann erfolglos enden, wenn kein passender Rahmen existiert. Ein Aufruf außerhalb einer Funktion muss deshalb keine brauchbare Ausgabe liefern.

## 4. Wichtige Optionen

Es gibt keine gewöhnliche Optionsliste wie bei einem externen Programm. Die lokale Hilfe wird über `help caller` gelesen.

| Form | Zweck | Erwartung |
| --- | --- | --- |
| `caller` | Unmittelbaren Kontext ohne Funktionsnamenspalte abfragen. | Zeile und Quelle, sofern verfügbar. |
| `caller 0` | Ersten verfügbaren Rahmen mit Namen abfragen. | Für einfache Diagnose meist ausreichend. |
| `caller 1` | Eine weitere Ebene betrachten. | Nur wenn diese Ebene tatsächlich existiert. |
| `help caller` | Installierte Semantik nachlesen. | Keine Diagnose eines anderen Prozesses. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Zwei eigene Funktionen definieren

Das Beispiel nutzt nur Shellfunktionen und die Diagnoseausgabe. Es erstellt keine Dateien und führt keine Systemänderung aus.

```bash
innen() {
  caller 0
}
aussen() {
  innen
}
aussen
```

### Schritt 2: Aufrufweg nachvollziehen

Der letzte Aufruf startet `aussen`. Dessen Körper ruft `innen` auf. In `innen` fragt `caller 0` ab, von wo diese Funktion erreicht wurde. Daher ist als aufrufende Funktion `aussen` zu erwarten und nicht der Name des Builtins `caller`.

### Schritt 3: Ausgabe lesen

Bei der hier ausgeführten zusammenhängenden Befehlszeichenfolge lautete die Ausgabe:

```text
5 aussen environment
```

Die 5 bezeichnet in diesem konkreten Test die Aufrufzeile. `environment` beschreibt den hier verwendeten `bash -c`-Kontext. Beim Speichern als eigenes Skript kann dort stattdessen dessen Pfad stehen, und eingefügte Leerzeilen verändern Zeilennummern. Die genaue Beispielzahl ist deshalb kein universeller Sollwert für jedes Terminal.

## 6. Typische Anwendungsfälle

### Unerwarteten Funktionsaufruf finden

Eine Hilfsfunktion wird an mehreren Stellen verwendet. Eine vorübergehende Diagnose kann zeigen, welcher Weg im fehlerhaften Fall genommen wurde.

### Eigene Fehlermeldungen ergänzen

Ein Skript kann Fehlermeldungen mit einer nachvollziehbaren Aufrufstelle versehen. Das ist hilfreicher als eine allgemeine Meldung ohne Kontext, erfordert aber saubere Behandlung fehlender Rahmen.

### Einfache Aufrufkette verstehen

Fortgeschrittene Skripte können mehrere Rahmennummern abfragen. Nicht einfach unbegrenzt hochzählen, ohne den Rückgabestatus zu prüfen. Eine fehlende Ebene ist kein Beweis für einen Fehler im untersuchten Programm.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der lesende Diagnosebefehl verändert keine Datei. Seine Ausgabe kann dennoch interne Skriptpfade und Funktionsnamen offenlegen. Vor Veröffentlichung von Fehlerprotokollen diese Informationen prüfen.

Ein erfolgloser `caller` kann in einem Skript mit strenger Fehlerbehandlung Konsequenzen haben. In Diagnosefunktionen einen fehlenden Rahmen bewusst behandeln, statt dadurch eine andere Fehlerursache zu verdecken. Stackausgaben sind außerdem keine sichere Identitätsbestätigung: Dateinamen, Funktionsnamen und Aufrufweg allein beweisen keine Vertrauenswürdigkeit eines Programms.

## 8. Häufige Fehler

- **Keine Ausgabe am Prompt:** Es gibt möglicherweise keinen passenden aktiven Funktionsrahmen.
- **Rahmennummer mit Zeilennummer verwechselt:** Das Argument wählt die Ebene, die Ausgabe enthält die Zeile.
- **Ausgabe exakt wie im Beispiel erwartet:** Quelle und Zeilen hängen vom Ausführungskontext ab.
- **Andere Shell benutzt:** `caller` ist nicht in jeder Shell verfügbar.
- **Diagnose ändert Programmstatus:** Rückgabewerte im Fehlerpfad bewusst sichern und behandeln.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst zwei kleine eigene Funktionen verwenden. Ausgabe und Kontrollfluss getrennt betrachten: `caller` meldet Kontext, während `return` tatsächlich eine Funktion verlässt. Diagnose nur so ausführlich protokollieren, wie für die Fehlersuche nötig.

**Prüfstand:** Lokale Bash-5.2.21-Hilfe gelesen. Das verschachtelte Beispiel in einer separaten Bash ohne persönliche Startdateien ausgeführt; Ausgabe `5 aussen environment`, Status 0. Keine Benutzerdateien gelesen oder geändert. Mehrstufige Stackausgabe, Traps und Verhalten anderer Shells nicht praktisch geprüft.

## 10. Verwandte Befehle

- `declare -F`: Funktionsnamen anzeigen, andere Diagnoseebene.
- `type NAME`: Einordnung eines Befehls untersuchen.
- `set -x`: Befehlsablauf protokollieren, kann vertrauliche Argumente sichtbar machen.
- `return`: Funktion verlassen statt deren Aufrufkontext nur anzuzeigen.

Ausgangseintrag: Datensatz 73 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
