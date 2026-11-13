---
id: "continue"
name: "continue"
command: "continue"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "continue"]
status: "Lokale Primärhilfe und begrenztes Zahlenbeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 75
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# continue – Einen Schleifendurchlauf überspringen

## 1. Kurzbeschreibung

`continue` ist ein Shell-Builtin, das den Rest des aktuellen Schleifendurchlaufs überspringt und mit dem nächsten Schritt der Schleife fortfährt. **Root-Rechte sind nicht nötig.** Anders als `break` beendet es die Schleife nicht grundsätzlich.

Die Wirkung ist sinnvoll, wenn einzelne Eingaben nicht verarbeitet werden sollen, die übrigen aber weiterhin an der Reihe sind. Das ist eine Ablaufentscheidung, kein automatisches Rückgängigmachen bereits ausgeführter Aktionen.

## 2. Was macht der Befehl?

Bei einer normalen `for`-Liste geht es zum nächsten Listenelement. Bei `while` oder `until` wird die Schleifenbedingung erneut betrachtet. Bei einer arithmetischen Bash-for-Schleife erfolgt der dafür vorgesehene Fortschaltungsschritt.

Eine positive Ebenenzahl kann sich auf eine weiter außen liegende Schleife beziehen. Das ist fortgeschrittener Kontrollfluss und erschwert bei vielen Ebenen das Verständnis. Primärquelle ist die lokal gelesene Hilfe `help continue` aus Bash 5.2.21. Das [Bash-Handbuch zu Schleifen](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html) ist weiterführend verlinkt; der Onlineabruf war hier nicht verfügbar.

## 3. Syntax

```text
continue
continue ANZAHL
```

Ohne Argument gilt eine Ebene. `ANZAHL` ist eine positive ganze Zahl, keine Prozessnummer. Der Aufruf gehört in eine aktive Schleife; eine eigenständige externe Anwendung dieses Namens wird nicht vorausgesetzt.

## 4. Wichtige Optionen

`continue` besitzt keine allgemeine Optionsfamilie. Die Hilfe liest man in Bash mit `help continue`.

| Form | Bedeutung | Abgrenzung |
| --- | --- | --- |
| `continue` | Rest des aktuellen innersten Durchlaufs überspringen. | Weitere Durchläufe können folgen. |
| `continue 1` | Eine Ebene ausdrücklich nennen. | Entspricht dem Normalfall. |
| `continue 2` | Nächsten Durchlauf der zweiten äußeren Schleife erreichen. | Innere Abläufe werden verlassen. |
| `break` | Schleife verlassen. | Kein Ersatz, wenn weiter verarbeitet werden soll. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Kleine feste Liste verwenden

```bash
for zahl in 1 2 3; do
  if [ "$zahl" -eq 2 ]; then
    continue
  fi
  printf '%s\n' "$zahl"
done
printf 'Fertig\n'
```

Es werden nur Shellvariablen und Ausgaben verwendet. Keine Dateien oder Systemeinstellungen sind beteiligt.

### Schritt 2: Den übersprungenen Teil erkennen

Bei 1 ist die Bedingung falsch und die Zahl wird ausgegeben. Bei 2 springt `continue` vor dem `printf` zum nächsten Durchlauf. Deshalb fehlt genau diese Ausgabe. Anschließend wird 3 verarbeitet. Die Anweisung hinter `done` läuft nach dem Ende der Liste.

### Schritt 3: Ausgabe kontrollieren

```text
1
3
Fertig
```

Mit `break` an derselben Stelle würde bereits die 3 fehlen, weil die Schleife bei 2 ganz verlassen würde. Der Vergleich hilft, beide Befehle auseinanderzuhalten.

## 6. Typische Anwendungsfälle

### Unpassende Eingaben überspringen

Ein Verarbeitungslauf kann bekannte unerwünschte Werte auslassen und mit den übrigen fortfahren. Dabei sollte klar sein, ob ein übersprungener Wert nur unwichtig ist oder als Fehler gemeldet werden muss.

### Leere Datensätze behandeln

Eine Schleife kann leere Zeilen früh erkennen. Danach werden nur relevante Datensätze durch die eigentliche Verarbeitung geführt. Ein Zähler oder notwendige Abschlussarbeiten müssen trotzdem korrekt erfolgen.

### Einzelschritte verständlich halten

Ein früher übersprungener Sonderfall kann tiefe Verschachtelung vermeiden. Zu viele Sprungstellen machen den Ablauf wiederum schwerer lesbar; nicht jede Bedingung braucht ein `continue`.

## 7. Risiken, Nebenwirkungen und Vorsicht

In einer `while`-Schleife kann eine Endlosschleife entstehen, wenn der notwendige Zählerschritt hinter `continue` liegt. Dann bleibt die Bedingung unverändert und derselbe Fall wird ständig wiederholt. Fortschaltung deshalb so planen, dass jeder Pfad einen begrenzten nächsten Zustand erreicht.

Bereinigung oder Statusmeldungen im übersprungenen Rest des Körpers werden nicht ausgeführt. Bereits ausgeführte Schreibaktionen bleiben bestehen. In Pipelines oder Subshells steuert `continue` nur den passenden eigenen Schleifenkontext, nicht beliebige äußere Abläufe. Eine Ebenenzahl sollte aus dem konkreten Aufbau erklärt werden.

## 8. Häufige Fehler

- **Schleife sollte ganz enden:** Dafür ist `break` gedacht.
- **Zähler wird nie erhöht:** `continue` überspringt die Fortschaltung und erzeugt einen Dauerlauf.
- **Aufruf außerhalb einer Schleife:** Es fehlt der gültige Kontext.
- **Wichtige Aufräumaktion fehlt:** Sie lag hinter der Sprungstelle.
- **Mehrere Ebenen verwechselt:** `continue 2` kann große Teile der inneren Verarbeitung auslassen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer festen kurzen `for`-Liste beginnen. Den letzten gemeinsamen Schritt einer realen Verarbeitung nicht unbedacht hinter Sprungstellen legen. Bei `while` immer prüfen, wie die Schleife auf jedem Pfad vorankommt und endet.

**Prüfstand:** Lokale Bash-5.2.21-Hilfe gelesen. Das Zahlenbeispiel in einer eigenen Bash ohne persönliche Startdateien ausgeführt; exakt `1`, `3`, `Fertig`, Status 0. Keine Benutzerdateien verändert. Verschachtelte Ebenen und arithmetische Schleifen wurden für diesen Eintrag nicht praktisch geprüft.

## 10. Verwandte Befehle

- `break`: Schleife vorzeitig beenden.
- `return`: Funktion oder eingelesenes Skript verlassen.
- `for`: Listen oder arithmetische Durchläufe verarbeiten.
- `while`, `until`: bedingungsabhängige Schleifen.

Ausgangseintrag: Datensatz 75 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
