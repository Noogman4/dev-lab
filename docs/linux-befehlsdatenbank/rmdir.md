---
id: "rmdir"
name: "rmdir"
command: "rmdir"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "rmdir"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 197
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# rmdir – Nur leere Verzeichnisse entfernen

## 1. Kurzbeschreibung

rmdir entfernt vorhandene leere Verzeichnisse. Ein Verzeichnis mit Inhalt wird nicht rekursiv geleert, sondern normalerweise mit einer Fehlermeldung abgelehnt.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Damit ist die Wirkung enger als bei rm -r, aber weiterhin eine reale Änderung am Dateibaum. Auch eine unsichtbare Punktdatei zählt als Inhalt. -p versucht nach dem ausgewählten Verzeichnis zusätzlich seine Eltern zu entfernen, bis ein Hindernis auftritt. Bei mehreren Argumenten oder -p können bereits einzelne Verzeichnisse verschwunden sein, bevor ein späterer Fehler den Gesamtstatus ungleich null macht. --ignore-fail-on-non-empty unterdrückt genau bestimmte Nichtleer-Fehler und macht nicht sämtliche anderen Ursachen harmlos.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt rmdir invocation](https://www.gnu.org/software/coreutils/manual/html_node/rmdir-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
rmdir [OPTIONEN] ORDNER ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -p, --parents | Auch die angegebenen übergeordneten Pfadkomponenten entfernen versuchen |
| -v | Erfolgreiche Entfernungen melden |
| --ignore-fail-on-non-empty | Nichtleer-Fehler unterdrücken, übrige Fehler bleiben relevant |
| --help | Lokale Syntax und Optionen lesen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen einordnen

Das Muster würde nur zwei eigens neu angelegte Ordner verwenden. Die Löschschritte wurden nicht ausgeführt; auch der Nichtleer-Fehler ist hier keine neu gemessene Ausgabe.

### Schritt 2: Nicht ausgeführtes Muster lesen

Die folgenden Zeilen sind ausdrücklich ein Erklärungsmuster, kein ausgeführter Test und keine gemessene Ausgabe.

```text
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-rmdir-XXXXXX) || exit 1
cd "$uebung" || exit 1
mkdir -- leer daten
printf 'eigener Inhalt\n' > daten/notiz.txt
rmdir -- ./leer
if rmdir -- ./daten; then
    printf 'Unerwartet: nichtleeren Ordner entfernt\n' >&2
    exit 1
fi
)
```

### Schritt 3: Wirkung und Grenze verstehen

Der erste Aufruf würde den eigenen leeren Ordner entfernen. Der zweite müsste den Ordner daten wegen notiz.txt ablehnen; der erwartete Fehler wird im Muster ausdrücklich abgefangen. Es wird kein Befehl ergänzt, um diesen Schutz durch rekursives Leeren zu umgehen. Die Variante mit -p ist nicht Bestandteil des Musters.

## 6. Typische Anwendungsfälle

Einen bereits leeren eigenen Projektunterordner gezielt aufräumen oder in einem separat freigegebenen Ablauf kontrollieren, dass kein Inhalt entfernt werden muss.

## 7. Risiken, Nebenwirkungen und Vorsicht

-p kann mehr Eltern entfernen als beabsichtigt, besonders bei einem langen relativen oder absoluten Pfad. Ein leeres Verzeichnis kann für eine Anwendung dennoch benötigt werden. Ein teilweise erfolgreicher Lauf wird durch einen späteren Fehler nicht rückgängig gemacht. Gegen parallel hinzukommenden Inhalt ist eine vorherige Anzeige keine dauerhafte Zusicherung.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Directory not empty | Auch Punktdateien oder Unterordner zählen, nicht reflexartig rm -r ergänzen |
| No such file or directory | Name oder Zustand hat sich geändert, tatsächlichen Pfad prüfen |
| Eltern bleiben nach -p bestehen | Ein späterer Elternordner war nicht leer oder nicht entfernbar, Teilstand prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für die enge Absicht nur den einen Ordner nennen und zunächst auf -p verzichten. Rückgabestatus und verbliebene Pfade nach einem später erlaubten Aufräumen abgleichen. Ein Fehler wegen vorhandenen Inhalts ist ein hilfreiches Schutzsignal und kein Anlass, die Aufgabe automatisch auf Rekursion auszuweiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Keine Verzeichnisse entfernt und kein -p-Lauf ausgeführt; nur Version gelesen. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mkdir | Verzeichnisse anlegen |
| rm | Weitergehendes Entfernen einschließlich Rekursion |
| find | Leere Verzeichnisse zunächst nur auswählen und anzeigen |

Herkunft: Originaldatensatz 197 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
