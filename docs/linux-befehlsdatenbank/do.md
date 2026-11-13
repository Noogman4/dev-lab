---
id: "do"
name: "do"
command: "do"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "do"]
status: "Lokale Hilfen zu for und while sowie Schleifenbeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 77
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# do – Den Anweisungsteil einer Shellschleife beginnen

## 1. Kurzbeschreibung

`do` ist ein Shell-Schlüsselwort, das den auszuführenden Körper einer Schleife einleitet. Es ist **kein eigenständiges Programm** und hat keine allgemeinen Kommandozeilenoptionen. **Root-Rechte sind dafür nicht nötig.**

In einer Befehlsdatenbank ist dieser Eintrag als Sprachbaustein zu verstehen. Die Wirkung ergibt sich erst zusammen mit `for`, `while` oder `until` und dem abschließenden `done`.

## 2. Was macht der Befehl?

Die Shell erkennt an `do`, wo die wiederholt auszuführenden Anweisungen beginnen. Bei `for` steht davor die Liste oder Fortschaltungsform. Bei `while` und `until` steht davor eine Bedingung in Form von Befehlen und deren Status.

Das Schlüsselwort selbst führt keine Arbeit aus und erzeugt keine Ausgabe. Welche Daten gelesen oder geschrieben werden, bestimmen die Befehle im Körper. Primärquellen für die konkrete Installation sind die lokal gelesenen Hilfen `help for`, `help while` und `help until` aus Bash 5.2.21. Weiterführend: [Bash-Schleifengrammatik](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html); der Onlineabruf war hier nicht verfügbar.

## 3. Syntax

```text
for NAME in WERTE; do
  BEFEHLE
done

while BEDINGUNG; do
  BEFEHLE
done
```

Vor `do` muss die vorherige Befehlsliste passend abgeschlossen werden. In einer Zeile wird dafür gewöhnlich ein Semikolon verwendet. Auf getrennten Zeilen kann ein Zeilenumbruch den Abschluss übernehmen. Großgeschriebenes `DO` ist nicht dasselbe Schlüsselwort.

## 4. Wichtige Optionen

`do` hat keine Optionen. Die folgenden Bausteine bestimmen seinen Kontext:

| Baustein | Aufgabe | Abgrenzung |
| --- | --- | --- |
| `for` | Werte oder Durchläufe festlegen. | Beginnt die Schleifenkonstruktion. |
| `while` | Solange Bedingung erfolgreich ist wiederholen. | Erfolg bedeutet Status 0. |
| `until` | Bis zur erfolgreichen Bedingung wiederholen. | Umgekehrte Wiederholungsbedingung. |
| `do` | Schleifenkörper beginnen. | Kein zusätzlicher Funktionsaufruf. |
| `done` | Schleifenkörper abschließen. | Muss zur passenden Schleife gehören. |

Bash besitzt weitere Schleifenformen wie `select` und die arithmetische `for`-Form. Auch dort gehört der Körper in den vorgesehenen Grammatikrahmen; daraus entsteht keine allgemeine Option von `do`.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine feste Liste verwenden

```bash
for name in Anna Ben; do
  printf 'Hallo %s\n' "$name"
done
```

Die Werte sind einfache Übungsnamen. Es werden keine Benutzerkonten ausgewählt oder bearbeitet. Die Variable `name` gehört nur zum Beispielablauf.

### Schritt 2: Den Körper erkennen

Alles zwischen `do` und dem zugehörigen `done` gehört zum wiederholten Anweisungsteil. Im ersten Durchlauf ist `name` gleich `Anna`, im zweiten gleich `Ben`. `printf` benutzt die Variable als Datenargument, nicht als auszuführenden Befehl.

### Schritt 3: Ausgabe prüfen

```text
Hallo Anna
Hallo Ben
```

Das Schlüsselwort erscheint nicht in der Ausgabe. Es strukturiert den Ablauf. Würde vor `do` das Semikolon ohne passenden Zeilenumbruch fehlen, wäre die Grammatik beschädigt; zusätzliche Root-Rechte würden daran nichts ändern.

## 6. Typische Anwendungsfälle

### Listen verarbeiten

Ein klar abgegrenzter Körper beschreibt, was mit jedem vorbereiteten Wert passieren soll. Die Liste kann feste Übungsdaten oder später sorgfältig bestimmte Eingaben enthalten.

### Bedingungsgesteuerte Wiederholung

Bei `while` oder `until` steht im Körper die eigentliche Arbeit. Der Ablauf muss außerdem einen Weg besitzen, auf dem die Bedingung schließlich zum Ende führt.

### Skripte verständlich lesen

Einrückung unter `do` macht deutlich, welche Befehle mehrfach ausgeführt werden. Einrückung ersetzt aber nicht die erforderlichen Schlüsselwörter.

## 7. Risiken, Nebenwirkungen und Vorsicht

`do` selbst ist passiv. Ein versehentlich zu großer Körper kann jedoch zusätzliche Schreib- oder Löschbefehle mehrfach ausführen. Beim Umbau einer Schleife darauf achten, welche Anweisungen innerhalb und welche hinter `done` stehen.

Eine `while`-Schleife kann unbegrenzt laufen, wenn sich ihre Bedingung nie ändert. In Übungen feste kleine Listen wählen. Fremde Texte nicht mit `eval` als Schleifenkörper ausführen. Quoting und erlaubte Eingaben sind eigene Sicherheitsfragen und werden nicht durch das Schlüsselwort gelöst.

## 8. Häufige Fehler

- **`do --help` eingegeben:** `do` ist kein separat aufrufbares Hilfsprogramm.
- **Trennzeichen fehlt:** Schleifenkopf und Körper sind syntaktisch nicht getrennt.
- **`done` fehlt:** Shell wartet auf Abschluss oder meldet unerwartetes Ende.
- **Einrückung allein verwendet:** Shell benötigt trotzdem die Schlüsselwörter.
- **Arbeit versehentlich außerhalb:** Ein Befehl hinter `done` läuft erst nach der Schleife.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer kurzen festen Liste beginnen und zunächst nur Text ausgeben. Mehrzeilige Schreibweise sauber einrücken. Eine spätere eigene Skriptdatei zusätzlich mit `bash -n DATEI` syntaktisch prüfen; dabei werden ihre Anweisungen nicht als normaler Skriptlauf ausgeführt, die inhaltliche Wirkung ist dadurch aber nicht bewiesen.

**Prüfstand:** Lokale Bash-5.2.21-Schleifenhilfen gelesen. Die vollständige Begrüßungsschleife in einer getrennten Bash ohne persönliche Startdateien ausgeführt; beide erwarteten Zeilen, Status 0. Keine Benutzerkonten oder Dateien verändert. Andere Shells und unbegrenzte Bedingungen nicht praktisch geprüft.

## 10. Verwandte Befehle

- `done`: zugehöriger Abschluss des Körpers.
- `for`, `while`, `until`: Konstruktionen, die einen solchen Körper enthalten.
- `break`, `continue`: Ablauf innerhalb einer Schleife beeinflussen.
- `then`: entsprechender Beginn eines bedingten Zweigs, anderer Kontext.

Ausgangseintrag: Datensatz 77 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
