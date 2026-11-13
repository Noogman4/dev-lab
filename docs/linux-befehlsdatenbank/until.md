---
id: "until"
name: "until"
command: "until"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "until"]
status: "Lokale Primärhilfe und auf drei Durchläufe begrenzte Schleife praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 96
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# until – Wiederholen, bis eine Bedingung erfolgreich ist

## 1. Kurzbeschreibung

`until` ist ein Shell-Schlüsselwort für eine bedingungsabhängige Schleife. Ihr Körper läuft, solange die Bedingung **nicht** erfolgreich ist. Sobald die Bedingung Status 0 liefert, endet die Wiederholung. **Root-Rechte sind für die Konstruktion nicht nötig.**

Es ist kein eigenständiges Programm mit `--help`. Die konkrete Wirkung ergibt sich aus Bedingung und wiederholten Befehlen.

## 2. Was macht der Befehl?

Vor jedem möglichen Durchlauf wird die Bedingung ausgeführt. Ist sie bereits beim ersten Mal erfolgreich, läuft der Körper überhaupt nicht. Andernfalls werden die Anweisungen zwischen `do` und `done` ausgeführt und danach die Bedingung erneut geprüft.

Die Logik ist gegenüber `while` umgekehrt: `while` wiederholt bei Erfolg, `until` bei Nichterfolg. Primärquelle ist die lokal gelesene Hilfe `help until` aus Bash 5.2.21. Weiterführend: [Bash-Schleifen](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html). Ein Prüfstatus ist nicht automatisch eine fachliche Aussage, dass ein externer Dienst sicher oder korrekt funktioniert.

## 3. Syntax

```text
until BEDINGUNG; do
  BEFEHLE
done
```

Die Bedingung ist eine Befehlsliste. Ein Semikolon oder passender Zeilenumbruch trennt sie von `do`. `done` beendet den Körper. Anders als bei manchen Sprachkonstruktionen mit Prüfung am Ende ist hier kein erster Durchlauf garantiert.

## 4. Wichtige Optionen

`until` besitzt keine Optionsliste. Folgende Elemente steuern den Ablauf:

| Element | Bedeutung | Hinweis |
| --- | --- | --- |
| `BEDINGUNG` | Vor jedem Durchlauf geprüfter Status. | 0 beendet die Wiederholung. |
| `do` | Körper beginnen. | Dort liegt die wiederholte Aktion. |
| `done` | Körper abschließen. | Danach wird erneut geprüft. |
| `break` | Schleife zusätzlich verlassen. | Etwa bei gesonderter Fehlergrenze. |
| `continue` | Rest des Durchlaufs überspringen. | Darf notwendige Fortschaltung nicht verhindern. |

Zähler und erlaubte Höchstzahl sind eigene Skriptlogik. Das Schlüsselwort enthält keinen eingebauten Zeit- oder Wiederholungsgrenzwert.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen begrenzten eigenen Zustand anlegen

```bash
versuch=0
until [ "$versuch" -ge 3 ]; do
  printf 'Versuch %s\n' "$versuch"
  versuch=$((versuch + 1))
done
printf 'Grenze erreicht\n'
```

Der Körper besteht nur aus einer Textausgabe und einer eigenen Variablenänderung. Es werden keine echten Verbindungen versucht oder Systemzustände abgefragt.

### Schritt 2: Bedingung verstehen

Zu Beginn ist 0 noch nicht größer oder gleich 3. Der Vergleich liefert Nichterfolg, also läuft der Körper. Danach wird der Wert erhöht. Dasselbe passiert bei 1 und 2. Beim nächsten Test mit 3 liefert die Bedingung Erfolg und die Wiederholung endet.

### Schritt 3: Erwartete Ausgabe prüfen

```text
Versuch 0
Versuch 1
Versuch 2
Grenze erreicht
```

Die erste Versuchszahl ist 0, weil genau dieser Ausgangswert gewählt wurde. Eine fachliche Nummerierung ab 1 wäre eine andere bewusste Darstellung. Der Text `Grenze erreicht` steht außerhalb und wird erst nach dem Schleifenende ausgegeben.

## 6. Typische Anwendungsfälle

### Auf einen begrenzten Testzustand warten

Ein eigener Laborablauf prüft, ob eine bekannte Voraussetzung erreicht wurde. Dabei müssen Bedingung und Abbruchgrenzen zur tatsächlichen Aufgabe passen.

### Wiederholungsversuche planen

Ein gesondert gewählter Prüfbefehl kann mehrfach versucht werden. Zusätzlich Höchstzahl, Zeitlimit und sinnvolle Pause festlegen. Ständige erfolglose Prüfung ist kein zuverlässiger Wiederherstellungsmechanismus.

### Gegenüberstellung mit while

Bei einer Lernaufgabe lässt sich dieselbe fachliche Grenze mit umgekehrter Bedingung ausdrücken. Diejenige Form wählen, die den beabsichtigten Zustand am klarsten beschreibt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Bleibt die Bedingung immer erfolglos, kann die Schleife unbegrenzt laufen. Ein fehlender Zählerschritt oder ein `continue` an der falschen Stelle kann das versehentlich erzeugen. Enge Schleifen verbrauchen CPU; wiederholte externe Aktionen können Last oder Kosten verursachen.

Schon die Bedingung kann schreiben, Netzwerkverkehr erzeugen oder andere Nebenwirkungen besitzen. Ein erwartetes negatives Prüfergebnis und ein tatsächlicher Prüffehler können beide Nichterfolg liefern. Beide nicht blind als Anlass für endlose Wiederholung behandeln. Bereits ausgeführte Aktionen werden beim späteren Schleifenende nicht zurückgenommen.

## 8. Häufige Fehler

- **Umgekehrte Logik erwartet:** until läuft bei Nichterfolg, nicht wie while bei Erfolg.
- **Körper läuft nie:** Die Bedingung war bereits beim Start erfolgreich.
- **Dauerlauf:** Zustand ändert sich nicht oder Fortschaltung wird übersprungen.
- **Unbegrenzte Wiederholung eines Fehlers:** Es fehlt eine ausdrückliche Höchstgrenze.
- **Abschlussmeldung als Erfolg betrachtet:** Das Ende einer Schleife beweist nicht den Erfolg aller enthaltenen Aktionen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst mit festen kleinen Zahlen und Ausgaben arbeiten. Vor einer echten Warteschleife festlegen, wann sie erfolgreich endet und wann sie erfolglos abbrechen muss. Erwartete Anzahl und Randfälle ausdrücklich prüfen.

**Prüfstand:** Bash 5.2.21 und lokale until-Hilfe gelesen. Beispiel in einer getrennten Bash ohne persönliche Startdateien ausgeführt; genau drei Versuchsausgaben und Abschluss, Status 0. Keine Benutzerdateien, Geräte oder Netzwerkverbindungen verwendet. Zeitlimits, externe Prüffehler und verschachtelte Schleifen nicht praktisch geprüft.

## 10. Verwandte Befehle

- `while`: bei erfolgreicher Bedingung wiederholen.
- `for`: vorbereitete Liste oder begrenzte arithmetische Durchläufe.
- `break`, `continue`: Schleifenfluss beeinflussen.
- `sleep`: bewusste Pause in einem entsprechend geplanten Ablauf.

Ausgangseintrag: Datensatz 96 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
