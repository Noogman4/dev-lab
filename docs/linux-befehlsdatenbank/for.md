---
id: "for"
name: "for"
command: "for"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "for"]
status: "Lokale Primärhilfe und Array-Schleife mit Leerzeichen praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 85
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# for – Eine vorbereitete Liste zuverlässig durchlaufen

## 1. Kurzbeschreibung

`for` ist ein Shell-Schlüsselwort für Schleifen. Es führt einen Anweisungsteil für jedes Element einer Liste aus. Bash bietet zusätzlich eine arithmetische Variante. **Root-Rechte sind für die Schleife nicht nötig.** Die tatsächlichen Nebenwirkungen hängen von den wiederholten Befehlen ab.

## 2. Was macht der Befehl?

Beim Listentyp erhält die Schleifenvariable nacheinander jeden Wert. Der Körper zwischen `do` und `done` wird jeweils einmal ausgeführt. Die Liste wird zunächst durch die Shell ausgewertet. Quoting und Dateinamenexpansion beeinflussen deshalb, welche Elemente überhaupt entstehen.

Die Primärquelle für diese Anleitung ist die lokale Hilfe `help for` aus Bash 5.2.21. Die zusätzlich gelesene Hilfe `help 'for (('` beschreibt die arithmetische Form. Weiterführend: [Bash-Schleifen](https://www.gnu.org/software/bash/manual/html_node/Looping-Constructs.html); der Onlineabruf war zuvor nicht verfügbar.

## 3. Syntax

```text
for NAME in WERTE ...; do
  BEFEHLE
done

for NAME; do
  BEFEHLE
done

for (( START; BEDINGUNG; SCHRITT )); do
  BEFEHLE
done
```

Ohne ausdrückliche `in`-Liste werden die Positionsparameter wie bei `in "$@"` verarbeitet. Die arithmetische Form und die Arraybeispiele in dieser Anleitung sind Bash-spezifisch; ein beliebiges `/bin/sh` muss sie nicht unterstützen.

## 4. Wichtige Optionen

`for` besitzt keine gewöhnliche Optionsliste. Wichtig sind Liste und Schleifenkontrolle:

| Form | Aufgabe | Hinweis |
| --- | --- | --- |
| `in a b c` | Drei vorbereitete Werte durchlaufen. | Literale und Variablen bewusst unterscheiden. |
| `in "$@"` | Positionsparameter unverändert übernehmen. | Jedes Argument bleibt ein Element. |
| `in "${liste[@]}"` | Bash-Array elementweise verarbeiten. | Leerzeichen innerhalb eines Elements bleiben erhalten. |
| `break` | Schleife vorzeitig verlassen. | Restliche Werte entfallen. |
| `continue` | Rest eines Durchlaufs überspringen. | Nächster Wert kann folgen. |

`"$*"` ist kein gleichwertiger Ersatz für `"$@"`: Es fasst mehrere Parameter in einem Wort zusammen. Unzitierte Erweiterungen können Wörter aufteilen und Dateinamenmuster auswerten.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Zwei bewusst getrennte Werte anlegen

```bash
namen=("eins zwei" "drei")
for name in "${namen[@]}"; do
  printf 'Eintrag: <%s>\n' "$name"
done
```

Die Liste enthält zwei Elemente. Der erste Wert besitzt ein Leerzeichen. Das sind reine Textwerte und keine tatsächlich gesuchten Dateien.

### Schritt 2: Argumentgrenzen erhalten

`"${namen[@]}"` übergibt jedes Arrayelement als eigenes Wort. Die Schleifenvariable erhält deshalb erst den gesamten Text `eins zwei`, danach `drei`. Die erneute Zitierung von `"$name"` bei `printf` hält diese Grenze auch im Zielaufruf aufrecht.

### Schritt 3: Erwartete Ausgabe vergleichen

```text
Eintrag: <eins zwei>
Eintrag: <drei>
```

Es gibt genau zwei Durchläufe. Würde eine unzitierte Textvariable in die Liste eingesetzt, könnte eine zusätzliche Aufteilung stattfinden. Das Beispiel zeigt bewusst keine Verarbeitung einer mit `ls` erzeugten Menschenleseliste.

## 6. Typische Anwendungsfälle

### Bekannte Aufgaben wiederholen

Eine kleine Liste von bewusst ausgewählten Werten wird gleich behandelt. Vor schreibenden Aktionen zuerst dieselbe Liste nur anzeigen.

### Skriptargumente verarbeiten

`for argument in "$@"` berücksichtigt die vom Aufrufer übergebenen Argumentgrenzen. Ein Argument mit Leerzeichen bleibt dabei ein Argument, sofern es auch später korrekt weitergereicht wird.

### Dateinamenmuster verwenden

Ein Muster wie `*.txt` kann Dateien auswählen. Falls nichts passt, bleibt es bei üblichen Bash-Vorgaben als wörtlicher Text stehen. Einstellungen wie `nullglob` ändern das Verhalten. Eine Dateischleife muss deshalb auch den Fall ohne Treffer bewusst behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Schleife kann jeden enthaltenen Schreib-, Lösch- oder Netzwerkbefehl mehrfach ausführen. Die falsche Liste oder falsches Quoting vervielfacht dadurch Fehler. Namen mit führendem Minus können beim Zielprogramm als Optionen gelten; dessen Optionsende gegebenenfalls separat berücksichtigen.

Dateien können zwischen Auswahl und Verwendung ausgetauscht werden. Eine for-Liste ist keine abgesicherte Dateisystemtransaktion. `for x in $(ls ...)` ist kein zuverlässiges Verfahren für beliebige Dateinamen. Auch feste arithmetische Schleifen benötigen passende Grenzen, damit sie nicht unbeabsichtigt sehr lange laufen.

## 8. Häufige Fehler

- **Ein Name wird mehrere Werte:** Eine Erweiterung wurde nicht passend zitiert.
- **Nur ein großer Wert statt mehrerer:** Das gesamte Material wurde mit `"$*"` oder ähnlich zusammengefasst.
- **Wörtliches `*.txt` verarbeitet:** Es gab keinen Treffer und die verwendete Shell ließ das Muster stehen.
- **Syntaxfehler unter sh:** Bash-Array oder arithmetische Form in anderer Shell ausgeführt.
- **Erfolg trotz Einzelfehler angenommen:** Der Gesamtstatus ersetzt keine bewusste Behandlung jedes Durchlaufs.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit zwei oder drei festen Werten und `printf` beginnen. Erst nach Sichtkontrolle eine echte Aktion ergänzen. Für beliebige gefundene Dateinamen sind NUL-getrennte Verfahren oder passende `find -exec`-Aufrufe häufig geeigneter als eine zerlegte Textausgabe.

**Prüfstand:** Bash 5.2.21 und lokale for-Hilfe geprüft. Arraybeispiel in einer getrennten Bash ohne persönliche Startdateien ausgeführt; genau zwei erwartete Zeilen, Status 0. Keine Benutzerdateien gelesen oder verändert. Arithmetische Variante, Globbing-Einstellungen und Dateisystemrennen nicht praktisch geprüft.

## 10. Verwandte Befehle

- `while`, `until`: Wiederholung anhand einer Bedingung.
- `do`, `done`: Anfang und Ende des Schleifenkörpers.
- `break`, `continue`: Verlauf einer Schleife beeinflussen.
- `readarray`: vorbereitete Eingaben in ein Bash-Array lesen.

Ausgangseintrag: Datensatz 85 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
