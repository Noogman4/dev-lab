---
id: "elif"
name: "elif"
command: "elif"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "elif"]
status: "Lokale if-Hilfe und dreiteilige Auswahl praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 79
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# elif – Weitere Bedingungen einer if-Auswahl prüfen

## 1. Kurzbeschreibung

`elif` erweitert eine Shell-if-Auswahl um eine weitere Bedingung. Es bedeutet sinngemäß „andernfalls, falls diese Bedingung erfüllt ist“. **Root-Rechte sind nicht nötig.** Es ist ein Sprachschlüsselwort und kein eigenständiges Programm mit einer `--help`-Option.

Die Bedingungen werden nacheinander geprüft. Sobald ein Zweig ausgewählt wurde, werden spätere `elif`-Bedingungen dieser Auswahl nicht mehr ausgeführt.

## 2. Was macht der Befehl?

`if` und `elif` bewerten Befehlsstatus: 0 bedeutet für die Auswahl Erfolg, ein anderer Status Nichterfolg. Ein Vergleich mit `[` ist nur eine Möglichkeit, einen solchen Status zu erzeugen. Auch ein anderer bewusst gewählter Prüfbefehl kann als Bedingung dienen.

Damit ist die Reihenfolge wichtig. Eine breite frühe Bedingung kann engere spätere Fälle vollständig verdecken. Grundlage dieser Dokumentation sind die lokal gelesene Hilfe `help if` in Bash 5.2.21 und das eigene Beispiel. Weiterführend: [Bash-Bedingungskonstrukte](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html); der Onlineabruf war hier nicht verfügbar.

## 3. Syntax

```text
if BEDINGUNG1; then
  BEFEHLE1
elif BEDINGUNG2; then
  BEFEHLE2
else
  STANDARD_BEFEHLE
fi
```

Es können mehrere `elif`-Zweige vorkommen. `else` ist optional. Jede `elif`-Bedingung benötigt ihr eigenes `then`; abgeschlossen wird die gesamte Auswahl nur einmal mit `fi`.

## 4. Wichtige Optionen

`elif` besitzt keine Optionen. Zu unterscheiden sind folgende Bausteine:

| Baustein | Rolle | Hinweis |
| --- | --- | --- |
| `if` | Erste Bedingung beginnen. | Muss vor einem zugehörigen elif stehen. |
| `elif BEDINGUNG` | Weitere Prüfung bei bisherigem Nichterfolg. | Die Bedingung wird nicht immer ausgeführt. |
| `then` | Befehle des passenden Zweigs beginnen. | Auch nach jedem elif nötig. |
| `else` | Restfall ohne weitere Prüfung. | Kein zweites Bedingungsargument. |
| `fi` | Gesamte Auswahl abschließen. | Nicht jedes elif einzeln schließen. |

`-lt` im folgenden Beispiel gehört zum Vergleichsbefehl `[`, nicht zu `elif`. Die Leerzeichen um dessen Argumente und vor `]` sind Teil eines korrekten Aufrufs.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine eigene Zahl festlegen

```bash
wert=7
if [ "$wert" -lt 0 ]; then
  printf 'Negativ\n'
elif [ "$wert" -lt 10 ]; then
  printf 'Einstellig und nicht negativ\n'
else
  printf 'Mindestens zehn\n'
fi
```

### Schritt 2: Erste Bedingung betrachten

7 ist nicht kleiner als 0. Der erste Vergleich liefert daher Nichterfolg und der erste Ausgabebefehl wird nicht ausgeführt. Erst deshalb kommt der `elif`-Vergleich an die Reihe.

### Schritt 3: Zweite Bedingung einordnen

7 ist kleiner als 10. Der zweite Zweig passt und gibt `Einstellig und nicht negativ` aus. Der Zusatz „nicht negativ“ ergibt sich hier aus der bereits erfolglos geprüften ersten Bedingung. Die zweite Bedingung allein würde auch für negative Zahlen zutreffen.

Das Beispiel zeigt deshalb nicht nur Syntax, sondern die Bedeutung der Reihenfolge. Der `else`-Zweig bleibt in diesem Durchlauf unberührt. Alle Aktionen sind reine Ausgaben.

## 6. Typische Anwendungsfälle

### Mehrere Zahlenbereiche unterscheiden

Grenzen von eng nach weit oder in einer klar erklärten Reihenfolge prüfen. Randwerte ausdrücklich mitdenken, damit etwa 0 oder 10 nicht versehentlich falsch eingeordnet werden.

### Prüfergebnisse unterschiedlich behandeln

Ein Skript kann zwischen mehreren bekannten Zuständen unterscheiden. Wenn ein Prüfbefehl mehrere verschiedene Fehlerstatus besitzt, reicht ein bloßes Wahr/Falsch-Schema unter Umständen nicht aus; den konkreten Status vorher erfassen.

### Alternative Abläufe verständlich halten

Einige wenige `elif`-Zweige können übersichtlicher als tiefe Verschachtelung sein. Für viele feste Textwerte ist häufig `case` verständlicher.

## 7. Risiken, Nebenwirkungen und Vorsicht

Bedingungen sind ausführbare Befehle. Sie können selbst Dateien lesen, schreiben oder Netzwerke kontaktieren. Ein späteres `elif` wird nur bei Bedarf ausgeführt; solche Nebenwirkungen können deshalb vom vorherigen Verlauf abhängen.

Ungeprüfter Text ist nicht automatisch eine gültige Zahl. Das Beispiel verwendet einen festen Testwert; bei echten Eingaben sind Formatprüfung und erlaubter Wertebereich zusätzliche Aufgaben. Keine Benutzereingaben mit `eval` in Bedingungen verwandeln. Eine falsch sortierte Auswahl kann logisch falsche Aktionen auslösen, obwohl die Shell keinen Syntaxfehler erkennt.

## 8. Häufige Fehler

- **`else if` statt `elif`:** Das kann eine zusätzliche verschachtelte Auswahl bedeuten und einen weiteren Abschluss benötigen.
- **`then` vergessen:** Jede neue Bedingung braucht einen zugehörigen Zweigbeginn.
- **Breite Bedingung zuerst:** Spätere Fälle werden unerreichbar.
- **Status mit Textausgabe verwechselt:** Entscheidend ist der Rückgabestatus, nicht ein gedrucktes Wort „true“.
- **Zahlvergleich auf beliebigen Text angewendet:** Eingabe zuerst validieren.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit wenigen festen Werten beginnen. Jeden Zweig und die Randwerte gezielt prüfen; ein erfolgreicher Test eines einzigen Zweigs beweist nicht die ganze Auswahllogik. Reine Ausgaben verwenden, bevor echte Aktionen eingebaut werden.

**Prüfstand:** Lokale if-Hilfe von Bash 5.2.21 gelesen. Beispiel mit Wert 7 in einer getrennten Bash ohne persönliche Startdateien ausgeführt; genau die erwartete zweite Ausgabe, Status 0. Keine Benutzerdateien verändert. Negative Werte, Randwerte und ungültige Eingaben für diesen Eintrag nicht praktisch geprüft.

## 10. Verwandte Befehle

- `if`, `then`, `else`, `fi`: weitere Teile derselben Auswahlgrammatik.
- `case`: Auswahl anhand von Textmustern.
- `test`, `[`: Vergleichsbefehle mit eigenem Argumentformat.
- `[[ ... ]]`: Bash-Bedingung mit anderer Auswertungs- und Mustersyntax.

Ausgangseintrag: Datensatz 79 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
