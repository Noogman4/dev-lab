---
id: "mkdir"
name: "mkdir"
command: "mkdir"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "mkdir"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 189
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# mkdir – Verzeichnisse mit passenden Rechten anlegen

## 1. Kurzbeschreibung

mkdir legt neue Verzeichnisse an. Es verändert den Dateibaum und ist deshalb auch bei eigenen Dateien kein rein lesender Befehl.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Ohne -p führt ein bereits vorhandener Name gewöhnlich zu einem Fehler. -p erzeugt fehlende Eltern und akzeptiert vorhandene Verzeichnisse. Es macht aber eine vorhandene normale Datei nicht zum Verzeichnis und passt vorhandene Rechte nicht automatisch an. Die Rechte neuer Verzeichnisse hängen ohne besondere Vorgaben von Modus, umask und gegebenenfalls Default-ACLs ab. -m gilt für die ausdrücklich genannten neu angelegten Verzeichnisse; zusätzliche mit -p erzeugte Eltern folgen eigenen Anlageregeln. Auf einem fremden Ziel kann ein scheinbar harmloser mkdir-Aufruf daher mehr neue Objekte erzeugen als erwartet.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt mkdir invocation](https://www.gnu.org/software/coreutils/manual/html_node/mkdir-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
mkdir [OPTIONEN] ORDNER ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -p, --parents | Fehlende Eltern anlegen, vorhandene Verzeichnisse akzeptieren |
| -m MODUS | Modus der ausdrücklich benannten neuen Verzeichnisse |
| -v | Tatsächlich angelegte Namen melden |
| --help | Lokale Optionsbeschreibung lesen |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Die umask wird nur innerhalb der eigenen Übungs-Subshell gesetzt. Alle angelegten Verzeichnisse liegen unter dem neuen Temporärordner. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-mkdir-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
umask 0027
mkdir -p -m 0700 -- eltern/privat
test "$(stat -c '%a' -- eltern)" = 750
test "$(stat -c '%a' -- eltern/privat)" = 700
mkdir -p -m 0755 -- eltern/privat
test "$(stat -c '%a' -- eltern/privat)" = 700
stat -c '%a %n' -- eltern eltern/privat
)
```

### Schritt 3: Ergebnis verstehen

Der mit -p zusätzlich erzeugte Elternordner hat im geprüften eigenen Kontext 750; das ausdrücklich benannte neue privat erhält 700. Ein zweiter -p-Aufruf lässt dessen vorhandene Rechte trotz anderem -m unverändert. Die Subshellebene begrenzt die eigene umask. Vererbte Default-ACLs und Spezialbits anderer Verzeichnisse wurden nicht nachgestellt.

## 6. Typische Anwendungsfälle

Eigene Projektstrukturen vorbereiten oder einen privaten Unterordner bewusst mit restriktiven Rechten anlegen. Bei bestehendem Bestand Rechte erst prüfen und Änderungen als eigene Aufgabe behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Tippfehler kann an anderer Stelle einen ganzen neuen Pfad erzeugen. -p bedeutet nicht, dass alle Eltern dieselben -m-Rechte bekommen. Eine später vorgeschaltete Änderung mit chmod wäre eine zusätzliche Aktion und kann bestehende Zugriffe verändern. Fremde Systempfade nicht mit sudo zu einer Übung machen.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| File exists ohne -p | Der Name ist bereits vergeben, Zieltyp zuerst prüfen |
| Not a directory | Ein Pfadbestandteil ist eine normale Datei |
| Rechte bleiben trotz -p -m gleich | Bereits bestehende Verzeichnisse werden dadurch nicht umkonfiguriert |

## 9. Sichere Varianten oder Tipps für Einsteiger

Vor dem Schreiben den Arbeitsordner prüfen. Einen restriktiven Anfangskontext statt nachträglich offener Übergangsrechte bevorzugen. Gruppenrechte, setgid-Vererbung und Default-ACLs sind eigene Mechanismen; die einfache Zahlenprüfung garantiert deren Verhalten nicht überall.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine fremden Rechte, Default-ACLs, Spezialbits oder Systemverzeichnisse verändert. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| rmdir | Nur leere Verzeichnisse entfernen |
| install | Verzeichnisse oder Dateien mit Attributvorgaben anlegen |
| umask | Vorgaben für neue Objekte in der Shell |

Herkunft: Originaldatensatz 189 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
