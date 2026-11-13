---
id: "readlink"
name: "readlink"
command: "readlink"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "readlink"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 192
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# readlink – Gespeicherten Linktext von aufgelösten Pfaden trennen

## 1. Kurzbeschreibung

readlink zeigt ohne Kanonisierungsoption den in einem symbolischen Link gespeicherten Zieltext. Dieser Text kann relativ sein und muss auf kein existierendes Objekt zeigen.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Ein normaler Dateipfad ohne Symlink liefert im einfachen Lesemodus keinen Linktext und einen Fehlerstatus. -f, -e und -m wechseln dagegen in einen anderen Modus: Sie bilden kanonische Pfade mit unterschiedlichen Anforderungen an vorhandene Komponenten. -f erlaubt eine fehlende letzte Komponente, -e verlangt alle Komponenten, -m lässt auch weitere fehlende Komponenten zu. Ein erfolgreich berechneter Pfad ist daher je nach Modus ausdrücklich kein Existenzbeweis. GNU empfiehlt für Kanonisierung den deutlicher benannten Befehl realpath.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt readlink invocation](https://www.gnu.org/software/coreutils/manual/html_node/readlink-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
readlink [OPTIONEN] DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| ohne Kanonisierungsoption | Gespeicherten Text eines Symlinks lesen |
| -f | Kanonisieren, alle außer letzter Komponente müssen zugänglich vorhanden sein |
| -e | Kanonisieren, alle Komponenten müssen existieren |
| -m | Fehlende Komponenten für die Berechnung zulassen |
| -v | Auch Diagnosen ausgeben, normalerweise zurückhaltend |
| -z | Ausgabe mit NUL abschließen |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Es werden nur ein eigener Symlink und eine eigene normale Textdatei verwendet. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-readlink-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
mkdir daten
printf 'eigener Inhalt\n' > daten/notiz.txt
ln -s -- daten/notiz.txt verweis
readlink -- verweis > linktext.txt
printf 'daten/notiz.txt\n' > erwartet.txt
cmp linktext.txt erwartet.txt
readlink -e -- verweis > aufgeloest.txt
printf '%s/daten/notiz.txt\n' "$uebung" > erwartet-absolut.txt
cmp aufgeloest.txt erwartet-absolut.txt
if readlink -- daten/notiz.txt > kein-link.txt; then
    printf 'Unerwartet: normale Datei als Symlink behandelt\n' >&2
    exit 1
fi
cat linktext.txt aufgeloest.txt
)
```

### Schritt 3: Ergebnis verstehen

Der erste Aufruf liefert genau den gespeicherten relativen Text daten/notiz.txt. Mit -e wird im eigenen vorhandenen Baum ein absoluter Pfad berechnet. Der letzte Aufruf prüft ausdrücklich den negativen Fall einer normalen Datei; sein erwarteter Fehler wird abgefangen und nicht mit einem allgemeinen Programmerfolg verwechselt.

## 6. Typische Anwendungsfälle

Verweise untersuchen oder in einem bekannten eigenen Baum Linktext und tatsächliche Zielauflösung vergleichen. Dabei den ausgewählten Modus und dessen Existenzregeln immer mit nennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Link kann auf fremde Pfade zeigen und sich parallel verändern. Ein kanonisierter Name ist keine Zugriffskontrolle für eine spätere Dateiöffnung; zwischen Prüfung und Verwendung kann ein Austausch stattfinden. Eine leere Ausgabe kann ein Fehler sein und darf nicht als leerer erlaubter Zielpfad weiterverarbeitet werden.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Keine Ausgabe bei normaler Datei | Ohne -f/-e/-m wird ein Symlink erwartet, Status prüfen |
| Ergebnis beginnt nicht mit / | Gespeicherter relativer Linktext ist noch kein absoluter Zielpfad |
| -f erfolgreich obwohl Datei fehlt | Letzte Komponente darf in diesem Modus fehlen, bei Bedarf -e wählen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den Modus bewusst auswählen und den Status unmittelbar auswerten. Für beliebige Dateinamen NUL-Ausgabe mit einem geeigneten Empfänger verwenden; Shell-Befehlsersetzung entfernt abschließende Newlines. Keinen Dateizugriff allein aufgrund einer früheren Textauflösung für sicher erklären.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur gespeicherter Text, vorhandene Zielauflösung und Nicht-Link-Fall geprüft, keine Rennen oder fremden Ziele. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| realpath | Bevorzugte Kanonisierungsschnittstelle |
| ln | Link anlegen |
| stat | Link- oder Zielmetadaten anzeigen |

Herkunft: Originaldatensatz 192 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
