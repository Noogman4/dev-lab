---
id: "ln"
name: "ln"
command: "ln"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "ln"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 186
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# ln – Hardlinks und symbolische Links unterscheiden

## 1. Kurzbeschreibung

ln legt einen weiteren Dateinamen an. Ohne -s entsteht ein Hardlink, mit -s ein symbolischer Link, der eine Zielzeichenfolge enthält.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Hardlinks auf normale Dateien teilen auf demselben Dateisystem dieselbe Dateiidentität und denselben Inhalt. Eine Änderung über einen Namen ist über den anderen sichtbar; das ist keine unabhängige Kopie. Symlinks enthalten dagegen einen Pfad. Relative Ziele werden vom Verzeichnis des Links aus aufgelöst, nicht vom späteren Arbeitsverzeichnis des Lesers. Ein nicht existentes Ziel verhindert die Anlage eines Symlinks nicht. Ein schon belegter Linkname wird normalerweise abgelehnt. -f kann vorhandene Ziele ersetzen und ist deshalb keine sichere Standardergänzung.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt ln invocation](https://www.gnu.org/software/coreutils/manual/html_node/ln-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
ln [OPTIONEN] ZIEL LINKNAME
ln [OPTIONEN] -t ORDNER ZIEL ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -s | Symbolischen Link statt Hardlink anlegen |
| -r | Mit -s einen relativ berechneten Zielpfad erzeugen |
| -T | Letztes Argument als Linknamen statt Zielordner behandeln |
| -n | Symlink auf einen Ordner am letzten Argument nicht wie diesen Ordner behandeln |
| -i | Vor Ersetzen nachfragen |
| -f | Bestehenden Linknamen ersetzen, aktive Entfernung möglich |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Alle Links zeigen ausschließlich auf neue eigene Daten im Übungsordner. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-ln-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
printf 'erste Fassung\n' > original.txt
ln -- original.txt zweiter-name.txt
mkdir unter
ln -s -- ../original.txt unter/verweis.txt
test original.txt -ef zweiter-name.txt
test "$(readlink -- unter/verweis.txt)" = ../original.txt
printf 'zweite Fassung\n' > original.txt
cmp original.txt zweiter-name.txt
cmp original.txt unter/verweis.txt
stat -c '%i %h %n' -- original.txt zweiter-name.txt
)
```

### Schritt 3: Ergebnis verstehen

Der erste ln-Aufruf erzeugt einen Hardlink. Der Shelltest -ef vergleicht Dateiidentität. Der zweite Aufruf erzeugt im Unterordner einen Symlink mit dem Text ../original.txt. Nach dem Schreiben der zweiten eigenen Fassung sehen beide Wege denselben Inhalt. Die gemeinsamen Inodenummern gelten nur innerhalb dieses Dateisystems; ein entfernter Inode mit derselben Zahl wäre kein Identitätsbeweis.

## 6. Typische Anwendungsfälle

Alternative Namen für eigene Daten einrichten oder Programme auf ein bewusst ausgewähltes Ziel verweisen lassen. Eine Sicherung bleibt eine getrennte Aufgabe, da ein Hardlink dieselben Inhaltsänderungen mitmacht.

## 7. Risiken, Nebenwirkungen und Vorsicht

Links können unbeabsichtigt auf fremde oder inzwischen geänderte Pfade zeigen. Mit -f können vorhandene Namen entfernt werden. Hardlinks sind keine Sicherung gegen Inhaltsänderungen und überschreiten normalerweise keine Dateisystemgrenze. Bei Symlinks auf Verzeichnisse genau unterscheiden, ob der Link selbst ersetzt oder innerhalb seines Ziels ein weiterer Name angelegt würde.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Datei vorhanden | Linkname bereits belegt, nicht blind -f ergänzen |
| Relativer Symlink zeigt ins Leere | Ziel relativ zum Linkverzeichnis berechnen |
| Invalid cross-device link | Hardlinks brauchen dasselbe Dateisystem |

## 9. Sichere Varianten oder Tipps für Einsteiger

Neue eindeutige Linknamen und überprüfbare relative Ziele verwenden. readlink zeigt gespeicherten Linktext, realpath die aufgelöste Pfadform. Bei exakter Zielnamenabsicht -T verstehen und vor einem Ersetzen Zieltyp und Rechte prüfen.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine Ersetzungsoptionen, Dateisystemwechsel oder Verzeichnis-Hardlinks geprüft. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| readlink | Gespeicherten Symlinkinhalt lesen |
| realpath | Zielpfad auflösen |
| cp | Eine getrennte Datei statt gemeinsamer Dateiidentität erzeugen |

Herkunft: Originaldatensatz 186 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
