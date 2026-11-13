---
id: "in"
name: "in"
command: "in"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "safe"
tags: ["bash builtins", "in"]
status: "Lokale for-/case-Hilfen und beide Verwendungskontexte praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 89
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# in – Listen und Musterauswahl in der Shell einleiten

## 1. Kurzbeschreibung

`in` ist ein Shell-Schlüsselwort in bestimmten Sprachkonstruktionen. In einer `for`-Schleife leitet es die Liste ein; bei `case` trennt es den geprüften Wert von den Musterzweigen. **Root-Rechte sind nicht nötig.**

Es ist kein eigenständiges Programm und kein allgemeiner Operator zur Prüfung, ob etwas Mitglied einer Sammlung ist. Die Bedeutung wird durch die umgebende Grammatik bestimmt.

## 2. Was macht der Befehl?

Bei `for name in ...` stehen nach `in` die Werte, die nach Shellauswertung nacheinander verarbeitet werden. Bei `case "$wert" in` folgen dagegen Muster und deren Anweisungen. Die beiden Verwendungen besitzen unterschiedliche Aufgaben, obwohl dasselbe Wort erscheint.

Die lokal gelesenen Primärquellen sind `help for` und `help case` aus Bash 5.2.21. Weiterführend sind [Bash-Schleifen](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html) und [bedingte Konstruktionen](https://www.gnu.org/software/bash/manual/html_node/Conditional-Constructs.html) verlinkt. Ein normales Datenwort `in` wird nicht an jeder beliebigen Stelle als Sprachbaustein ausgewertet.

## 3. Syntax

```text
for NAME in WERT1 WERT2 ...; do
  BEFEHLE
done

case "$wert" in
  MUSTER) BEFEHLE ;;
esac
```

Bei einer for-Schleife kann die ausdrückliche `in`-Liste fehlen; dann werden die Positionsparameter wie bei `"$@"` durchlaufen. In der gewöhnlichen case-Grammatik ist das trennende `in` dagegen erforderlich. Die Erweiterung `select` in Bash verwendet ebenfalls eine passende Listenform.

## 4. Wichtige Optionen

`in` besitzt keine Optionen. Es müssen die vollständigen umgebenden Formen unterschieden werden:

| Kontext | Bedeutung von in | Passender Abschluss |
| --- | --- | --- |
| `for NAME in WERTE` | Beginn einer Werteliste. | Körper mit do/done. |
| `case WERT in` | Beginn der Musterzweige. | esac. |
| `select NAME in WERTE` | Liste eines Bash-Auswahlmenüs. | Körper mit do/done. |
| Zitiertes Datenwort `"in"` | Gewöhnlicher Text in einer Datenposition. | Kein eigener Grammatikrahmen. |

Optionen eines späteren Zielprogramms gehören nicht zu `in`. Auch eine Zeichenfolge `-in` aus einem anderen Werkzeug ist etwas anderes.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine feste Liste durchlaufen

```bash
for farbe in rot blau; do
  printf 'Farbe: %s\n' "$farbe"
done
```

`rot` und `blau` sind zwei eigene Textwerte. `in` trennt den Variablennamen `farbe` von dieser Liste. Erwartet werden die Zeilen `Farbe: rot` und `Farbe: blau`.

### Schritt 2: Eine Musterauswahl vergleichen

```bash
wahl=blau
case "$wahl" in
  blau) printf 'Blaue Auswahl\n' ;;
  *) printf 'Andere Auswahl\n' ;;
esac
```

Hier folgt nach `in` keine Liste von nacheinander auszuführenden Werten. Stattdessen werden Musterzweige geprüft. `blau` passt zum ersten Muster; erwartet wird nur `Blaue Auswahl`.

### Schritt 3: Zusammenhang benennen

Beide Beispiele enthalten `in`, führen aber unterschiedliche Kontrollstrukturen aus. Ohne `for` beziehungsweise `case` ist dieses Wort keine sinnvolle Aktion. Die Übung verwendet ausschließlich Variablen und Ausgaben, keine echten Dateien oder Desktopfarben.

## 6. Typische Anwendungsfälle

### Listenverarbeitung lesen

`in` zeigt in einer kurzen for-Schleife, wo die vorbereiteten Daten beginnen. Bei Variablen und Arrays muss weiterhin das richtige Quoting dafür sorgen, dass die gewünschten Elemente erhalten bleiben.

### Auswahlstruktur erkennen

Bei case zeigt dasselbe Wort den Wechsel vom ausgewerteten Wert zu den möglichen Mustern. So lässt sich ein Skript auch ohne Kenntnis aller enthaltenen Arbeitsbefehle besser gliedern.

### Shell und andere Sprachen auseinanderhalten

Eine Mitgliedschaftsprüfung aus Python lässt sich nicht allein durch Übernahme des Wortes `in` in eine Bashbedingung verwandeln. Für Shellentscheidungen die passenden vollständigen Konstruktionen verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Schlüsselwort selbst verändert keine Dateien. Eine falsch gebildete Liste kann aber echte Aktionen mit falschen oder zusätzlichen Werten ausführen. Unzitierte Variablen können aufgeteilt und als Dateinamensmuster ausgewertet werden.

Die Wahl eines case-Musters macht Eingabetext nicht zu vertrauenswürdigem Code. Ein passender Dateiname beweist keinen sicheren Dateiinhalt. Befehle im gewählten Körper besitzen ihre normalen Nebenwirkungen. Keine Textdaten mit `eval` in eine vermeintlich bequemere Konstruktion einsetzen.

## 8. Häufige Fehler

- **`in --help` eingegeben:** Es gibt kein eigenständiges Hilfsprogramm dieses Sprachbausteins.
- **Mitgliedschaftsoperator erwartet:** Bash benötigt eine andere, vollständige Prüfung.
- **Case-Liste wie for interpretiert:** Musterzweige werden ausgewählt, nicht alle Datenwerte durchlaufen.
- **Argumentgrenzen verloren:** Liste aus unzitiertem Text gebildet.
- **Falschen Abschluss verwendet:** case benötigt esac, die Schleife done.

## 9. Sichere Varianten oder Tipps für Einsteiger

Jeweils die gesamte Konstruktion betrachten. Kleine feste Listen und einfache Muster verwenden, bevor externe Eingaben verarbeitet werden. Bei Bash-Arrays `"${liste[@]}"` elementweise übergeben; bei Skriptargumenten `"$@"` verwenden, wenn deren Grenzen erhalten bleiben sollen.

**Prüfstand:** Lokale Bash-5.2.21-Hilfen zu for und case gelesen. Beide Beispiele in einer getrennten Bash ohne persönliche Startdateien ausgeführt; drei erwartete Ausgabezeilen, Status 0. Keine Benutzerdateien verändert. select-Menüs und fremde Eingabedaten für diesen Eintrag nicht praktisch geprüft.

## 10. Verwandte Befehle

- `for`: listengesteuerte Wiederholung.
- `case`, `esac`: Musterauswahl und deren Abschluss.
- `select`: interaktive Bash-Auswahlschleife.
- `do`, `done`: Körper einer Schleife abgrenzen.

Ausgangseintrag: Datensatz 89 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
