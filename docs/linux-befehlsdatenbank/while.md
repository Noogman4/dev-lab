---
id: "while"
name: "while"
command: "while"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "while"]
status: "Lokale while-/read-Hilfen und begrenzter Textstrom praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 97
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# while – Bedingungen wiederholen und Text zeilenweise verarbeiten

## 1. Kurzbeschreibung

`while` ist ein Shell-Schlüsselwort für Wiederholung bei erfolgreicher Bedingung. Der Körper läuft so lange, wie die vorangestellte Befehlsliste Status 0 liefert. **Root-Rechte sind für die Konstruktion nicht nötig.** Die enthaltenen Befehle bestimmen die tatsächlichen Nebenwirkungen.

Ein häufiger sinnvoller Einsatz ist das schrittweise Lesen einer überschaubaren Textquelle. Dabei müssen Zeilengrenzen, Leerraum und das Ende der Eingabe bewusst behandelt werden.

## 2. Was macht der Befehl?

Vor jedem Durchlauf wird die Bedingung ausgeführt. Bei Erfolg folgt der Körper zwischen `do` und `done`; bei Nichterfolg endet die Wiederholung. Wenn die Bedingung sofort fehlschlägt, läuft der Körper kein einziges Mal.

Die Primärquellen sind die lokal gelesenen Hilfen `help while` und `help read` aus Bash 5.2.21. Weiterführend: [Bash-Schleifen](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html). Das Schlüsselwort besitzt keine eingebaute Begrenzung der Laufzeit oder Anzahl von Durchläufen.

## 3. Syntax

```text
while BEDINGUNG; do
  BEFEHLE
done
```

Die Bedingung muss ein sinnvoller Befehl beziehungsweise eine Befehlsliste sein. Ein bloßer eingegebener Text ist nicht automatisch ein Wahrheitswert. In einer Zeile trennt gewöhnlich das Semikolon die Bedingung von `do`; bei Mehrzeiligkeit ist ein passender Zeilenumbruch möglich.

## 4. Wichtige Optionen

`while` hat keine gewöhnlichen Optionen. Im Textlesebeispiel sind mehrere eigenständige Elemente wichtig:

| Element | Funktion | Grenze |
| --- | --- | --- |
| `read -r zeile` | Eine Zeile ohne Rückstrich-Auswertung einlesen. | Das ist eine Option von read, nicht while. |
| `IFS=` vor read | Unbeabsichtigtes Aufteilen/Abschneiden von Rand-Leerraum vermeiden. | Absichtlich für den Leseaufruf gewählt. |
| `do`, `done` | Schleifenkörper abgrenzen. | Nicht durch Einrückung ersetzbar. |
| `break` | Schleife vorzeitig verlassen. | Verbleibende Eingaben werden nicht automatisch bearbeitet. |
| `continue` | Rest des Durchlaufs überspringen. | Notwendigen Fortschritt nicht überspringen. |
| Prozesssubstitution `<(...)` | Ausgabe als Eingabequelle bereitstellen. | Bash-spezifisch, keine beliebige sh-Syntax. |

Ein Wechsel von while zu until kehrt die Wiederholungsbedingung um. Er repariert keine fehlerhafte oder nebenwirkungsreiche Prüfung.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen kleinen eigenen Textstrom verarbeiten

```bash
anzahl=0
while IFS= read -r zeile || [ -n "$zeile" ]; do
  anzahl=$((anzahl + 1))
  printf 'Zeile %s: <%s>\n' "$anzahl" "$zeile"
done < <(printf 'eins zwei\n\nEnde ohne Umbruch')
printf 'Gesamt: %s\n' "$anzahl"
```

Die Quelle ist ein eigener `printf`-Aufruf. Es wird keine vorhandene Benutzerdatei gelesen. Der Text enthält eine Zeile mit Leerzeichen, eine Leerzeile und eine letzte Zeile ohne abschließenden Zeilenumbruch.

### Schritt 2: Ende und letzte Daten verstehen

`read` kann am Eingabeende Nichterfolg melden, obwohl es noch Text ohne abschließenden Trenner gelesen hat. Die zusätzliche Bedingung `[ -n "$zeile" ]` verarbeitet diesen letzten nichtleeren Rest trotzdem. Bei endgültig leerer Eingabe schlagen beide Teile fehl und die Schleife endet.

### Schritt 3: Erwartete Ausgabe prüfen

```text
Zeile 1: <eins zwei>
Zeile 2: <>
Zeile 3: <Ende ohne Umbruch>
Gesamt: 3
```

Die Eingabeumleitung am gesamten Konstrukt hält den Körper hier in der aufrufenden Bash. Der Zähler ist deshalb anschließend verfügbar. Eine gewöhnliche Pipeline in die Schleife kann je nach Shell und Einstellungen einen anderen Subshellkontext erzeugen.

## 6. Typische Anwendungsfälle

### Texte schrittweise bearbeiten

Statt eine gesamte große Liste in ein Array zu lesen, kann ein Skript Zeilen nacheinander verarbeiten. Die konkrete Quelle und längste Zeile müssen trotzdem zur Aufgabe passen.

### Begrenzte Wiederholungsprüfung

Eine Zustandsprüfung kann mehrfach stattfinden. Zusätzlich eine sinnvolle Höchstzahl, Pause und Abbruchbedingung festlegen; ein Dauertest braucht solche Regeln.

### Eingabefehler sichtbar behandeln

Ein Parser kann pro Datensatz prüfen und verständlich melden, was übersprungen oder abgelehnt wurde. Ein sauber gelesenes Textfragment ist dadurch noch kein vertrauenswürdiger Code oder Dateipfad.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine immer erfolgreiche Bedingung kann eine Endlosschleife erzeugen. Ohne Pause kann sie CPU beanspruchen; mit wiederholten Arbeitsbefehlen auch Dateien oder Netzwerkziele belasten. Ein `continue` vor der Zustandsänderung kann den Abbruch verhindern.

Bedingungen sind echte Befehle und können selbst Nebenwirkungen haben. Erwarteter Eingabeabschluss und echter Lesefehler müssen in anspruchsvollen Abläufen gesondert bewertet werden. Das gezeigte Textmuster ist kein Protokoll für beliebige binäre Daten: Bashvariablen können eingebettete NUL-Bytes nicht unverändert speichern.

## 8. Häufige Fehler

- **Letzte Zeile fehlt:** Eingabe hatte keinen abschließenden Zeilenumbruch.
- **Rückstriche verändern sich:** `read -r` fehlte.
- **Leerraum geht verloren:** Ungeeignete IFS- oder spätere Aufteilungsregeln.
- **Zähler nach Pipeline unverändert:** Schleife lief in einer Subshell.
- **Dauerlauf:** Bedingung oder Fortschaltung endet nicht wie gedacht.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer festen kleinen Textquelle beginnen und Elementgrenzen sichtbar ausgeben. Anschließend Grenzfälle wie Leerzeilen und fehlenden Endumbruch kontrollieren. Für echte Aktionen Eingaben validieren und sie als Daten statt Shellcode weitergeben.

**Prüfstand:** Bash 5.2.21, lokale while-/read-Hilfen gelesen. Vollständiges Beispiel in einer getrennten Bash ohne persönliche Startdateien ausgeführt; alle drei Datensätze und Zähler 3 bestätigt, Status 0. Keine Benutzerdateien verändert. Lesefehler, binäre Daten, große Quellen und echte Dauerschleifen nicht praktisch geprüft.

## 10. Verwandte Befehle

- `until`: bei Nichterfolg wiederholen.
- `for`: vorbereitete Werte durchlaufen.
- `readarray`: Eingaben vollständig in ein Array sammeln.
- `read`: eigentlicher Zeilenlesebefehl.

Ausgangseintrag: Datensatz 97 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
