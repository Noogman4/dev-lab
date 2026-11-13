---
id: "readarray"
name: "readarray"
command: "readarray"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "readarray"]
status: "Lokale readarray-/mapfile-Hilfe und Leerzeilenbeispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 92
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# readarray – Zeilen als getrennte Bash-Arrayelemente einlesen

## 1. Kurzbeschreibung

`readarray` liest Eingaben in ein indiziertes Bash-Array. Es ist ein anderer Name für `mapfile`. **Für eigene lesbare Eingaben sind keine Root-Rechte nötig.** Das Werkzeug kann viele Daten im Arbeitsspeicher sammeln; große oder unbegrenzte Quellen deshalb bewusst begrenzen.

Es ist nicht dasselbe wie ein gewöhnlicher einzelner `read`-Aufruf. Ein Array enthält mehrere getrennte Elemente und kann Leerzeichen innerhalb einer Zeile erhalten.

## 2. Was macht der Befehl?

Standardmäßig wird von der Standardeingabe gelesen und ein Element pro Zeile gespeichert. Ohne ausdrücklich genannten Arraynamen wird `MAPFILE` verwendet. Ohne `-t` bleibt der gelesene Zeilentrenner grundsätzlich im Element; `-t` entfernt den jeweiligen abschließenden Trenner.

Ohne expliziten Startindex wird ein vorhandenes Zielarray vor der Zuweisung geleert. Mit `-O` ist ein bewusstes Einsetzen ab einem bestimmten Index möglich. Primärquellen sind die lokal gelesenen Hilfen `help readarray` und `help mapfile` aus Bash 5.2.21. Weiterführend: [Bash-Builtins](https://www.gnu.org/software/bash/manual/html_node/Bash-Builtins.html).

## 3. Syntax

```text
readarray [OPTIONEN] [ARRAYNAME]
readarray -t ARRAYNAME < EIGENE_DATEI
```

Die Umleitung liefert Eingabedaten. Die Datei wird gelesen, nicht als Shellskript ausgeführt. Eine einfache Pipeline kann den rechten Teil dagegen in einer Subshell ausführen; dann steht ein dort verändertes Array anschließend in der Elternshell möglicherweise nicht zur Verfügung.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze |
| --- | --- | --- |
| `-t` | Abschließenden Trenner entfernen. | Entfernt nicht allgemein Leerraum am Zeilenanfang oder -ende. |
| `-n N` | Höchstens N Elemente lesen. | 0 bedeutet alle, nicht null Elemente. |
| `-s N` | Erste N Eingabezeilen verwerfen. | Nicht mit einem Arrayindex verwechseln. |
| `-O INDEX` | Zuweisung ab diesem Index beginnen. | Vorhandenen Inhalt und mögliche Lücken berücksichtigen. |
| `-d ZEICHEN` | Anderen Eingabetrenner verwenden. | Es zählt das erste Zeichen des Arguments. |
| `-u FD` | Aus einem Dateideskriptor lesen. | Richtigen offenen Kanal sicherstellen. |
| `-C CALLBACK` | Nach festgelegter Menge Callback auswerten. | Kann Code ausführen; nicht für fremden Text verwenden. |
| `-c N` | Callback-Intervall festlegen. | Nur im Zusammenhang mit der Callback-Funktion sinnvoll. |

Ein leeres Argument für `-d` kann NUL als Trenner verwenden. Bashvariablen speichern selbst keine eingebetteten NUL-Bytes. Das ist bei Dateinamenprotokollen und binären Daten zu unterscheiden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Drei eigene Textzeilen liefern

```bash
readarray -t zeilen < <(printf '%s\n' 'eins zwei' '' 'drei')
printf 'Anzahl: %s\n' "${#zeilen[@]}"
for zeile in "${zeilen[@]}"; do
  printf '<%s>\n' "$zeile"
done
```

Die Bash-Prozesssubstitution `<(...)` liefert die Ausgabe eines eigenen `printf`-Aufrufs an die Eingabeumleitung. Sie ist Bash-spezifisch. Es wird keine bestehende Datei gelesen.

### Schritt 2: Die Elemente verstehen

Es entstehen drei Zeilen, davon eine leere mittlere Zeile. `-t` entfernt nur den Zeilenumbruch. Das Leerzeichen in `eins zwei` bleibt Bestandteil desselben Elements; die Leerzeile wird als leeres Element erhalten.

### Schritt 3: Ausgabe prüfen

```text
Anzahl: 3
<eins zwei>
<>
<drei>
```

Die Arrayanzahl und der leere Winkelklammerausdruck zeigen die erhaltenen Grenzen. Die zitierte Form `"${zeilen[@]}"` verarbeitet jedes Element einzeln, statt es erneut in Wörter aufzuteilen.

## 6. Typische Anwendungsfälle

### Kleine vorbereitete Textlisten

Eine überschaubare Liste wird mehrfach benötigt. Ein Array kann bequem sein, wenn die Datenmenge bekannt und begrenzt ist.

### Zeilen mit Leerzeichen erhalten

Ganze Zeilen bleiben zusammen. Das unterscheidet sich von einer unzitierten Kommandosubstitution, bei der Wörter anschließend aufgeteilt werden können.

### Eigene Verarbeitungsreihenfolge festlegen

Nach dem Einlesen können Elemente gezielt über Indizes betrachtet werden. Die ursprüngliche Reihenfolge bleibt zunächst erhalten; sortieren oder filtern sind zusätzliche eigene Aktionen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine sehr große Quelle kann viel Speicher beanspruchen. Bei unbegrenzter Eingabe oder einem nicht endenden Schreiber kann der Aufruf lange warten. `-n` begrenzt die Elementzahl, nicht automatisch die Bytezahl jedes Elements.

Vorhandene Arraydaten können ersetzt werden. `-C` führt einen Callback aus und erweitert die Funktion damit über bloßes Datensammeln hinaus. Fremde Callbackzeichenketten nicht übernehmen. Eingelesene Werte sind Daten und dürfen nicht anschließend ungeprüft mit `eval` ausgeführt oder als Optionen eines Zielprogramms interpretiert werden.

## 8. Häufige Fehler

- **Unerwartete Zeilenumbrüche im Element:** `-t` fehlte.
- **Leere Zeile verschwindet später:** Unzitierte Weitergabe statt korrekt zitierter Arrayexpansion.
- **Array nach Pipeline leer:** Subshellkontext beachten.
- **`-n 0` sollte nichts lesen:** In Bash bedeutet es unbegrenzt viele Elemente.
- **Andere Shell kennt den Befehl nicht:** Bash-Builtin, nicht allgemeines POSIX-Werkzeug.

## 9. Sichere Varianten oder Tipps für Einsteiger

Kleine eigene Daten mit `printf` verwenden, Zielarray benennen und Elementzahl kontrollieren. Für sehr große Datenströme ist eine schrittweise `while IFS= read -r ...`-Verarbeitung häufig geeigneter. Callback-Funktionen erst nach verstandenem Grundablauf einsetzen.

**Prüfstand:** Bash 5.2.21 und lokale readarray-/mapfile-Hilfen gelesen. Drei Zeilen einschließlich Leerzeile und Leerzeichen in einer getrennten Bash ohne persönliche Startdateien eingelesen; erwartete vier Ausgabezeilen, Status 0. Keine Benutzerdateien verändert. NUL-Trennung, Callbacks, Speichergrenzen und alternative Deskriptoren nicht praktisch geprüft.

## 10. Verwandte Befehle

- `mapfile`: Synonym in Bash.
- `read`: einzelne Eingabe lesen.
- `while`: Daten schrittweise verarbeiten.
- `declare -a`, `typeset -a`: indizierte Arrays deklarieren.

Ausgangseintrag: Datensatz 92 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
