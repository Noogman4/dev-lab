---
id: "realpath"
name: "realpath"
command: "realpath"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "realpath"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 193
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# realpath – Pfadauflösung mit klarer Existenzanforderung verwenden

## 1. Kurzbeschreibung

realpath berechnet eine kanonische Pfadform. GNU realpath löst normalerweise Symlinks auf und entfernt überflüssige Slashes sowie .- und ..-Komponenten.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Die normale GNU-Vorgabe verlangt vorhandene Komponenten außer der letzten. -e verlangt einen vollständig vorhandenen Pfad. -m berechnet auch bei fehlenden Komponenten eine mögliche Pfadform; es legt diese Objekte nicht an. -P löst Links vor nachfolgenden ..-Komponenten auf, -L behandelt diese logischen Komponenten anders. --relative-to liefert eine Darstellung relativ zu einem gewählten Bezugsordner. Ein kanonischer Name bleibt nur eine Aussage über die Auflösung zum Prüfzeitpunkt und bindet eine spätere Dateiöffnung nicht an dieselbe Datei.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt realpath invocation](https://www.gnu.org/software/coreutils/manual/html_node/realpath-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
realpath [OPTIONEN] DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -e | Alle Pfadkomponenten müssen existieren |
| -m | Fehlende Komponenten zur Pfadberechnung zulassen |
| -P | Physische Symlinkauflösung, GNU-Vorgabe |
| -L | Logische Behandlung nachfolgender ..-Komponenten |
| -s | Symlinks nicht auflösen, nur Pfadkomponenten bereinigen |
| --relative-to=ORDNER | Ergebnis relativ zum Bezugsordner |
| -z | NUL-Ausgabe |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Eine kleine eigene Ordnerstruktur und ein eigener Link bilden den gesamten Prüfbereich. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-realpath-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
mkdir -p daten/unter
printf 'eigene Notiz\n' > daten/unter/notiz.txt
ln -s -- daten/unter verweis
realpath -e -- verweis/./notiz.txt > physisch.txt
printf '%s/daten/unter/notiz.txt\n' "$uebung" > erwartet.txt
cmp physisch.txt erwartet.txt
realpath -e --relative-to="$uebung/daten" -- verweis/notiz.txt > relativ.txt
printf 'unter/notiz.txt\n' > erwartet-relativ.txt
cmp relativ.txt erwartet-relativ.txt
realpath -m -- fehlt/unter/notiz.txt > berechnet.txt
test ! -e fehlt
cat physisch.txt relativ.txt berechnet.txt
)
```

### Schritt 3: Ergebnis verstehen

-e bestätigt die Auflösung im vollständig vorhandenen eigenen Baum. --relative-to bildet dieselbe Zielauswahl als unter/notiz.txt ab. -m berechnet anschließend einen Pfad zu einem nicht angelegten Bereich; test bestätigt, dass dadurch kein Ordner fehlt erzeugt wurde. Keine dieser Zeichenfolgen ist eine dauerhafte Dateibindung.

## 6. Typische Anwendungsfälle

Pfade eigener Dateien vereinheitlichen, relative Verweise berechnen oder Existenzanforderungen vor einer menschenlesbaren Meldung ausdrücklich machen. Eine sichere Öffnungsstrategie für veränderliche fremde Bäume ist eine andere Aufgabe.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein falsch gewähltes -m kann eine nicht vorhandene Datei scheinbar plausibel erscheinen lassen. -s -m ist eine lexikalische Berechnung ohne Symlinkauflösung und darf nicht als Beweis der realen Zielidentität dienen. Prüf- und Nutzungszeitpunkte können auseinanderliegen; der berechnete Pfad ist keine Sandbox und keine Garantie, einen Baum nicht zu verlassen.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Pfad wird ausgegeben aber existiert nicht | GNU-Vorgabe und -m erlauben bestimmte fehlende Komponenten, -e gezielt prüfen |
| .. ergibt unerwartetes Ziel | -P und -L haben bei Symlinks unterschiedliche Auflösungsregeln |
| Ergebnis ist relativ | --relative-to wurde bewusst gewählt, keine automatische absolute Ausgabe erwarten |

## 9. Sichere Varianten oder Tipps für Einsteiger

Im Dokumentieren des Ergebnisses den verwendeten Modus nennen. Für eine reine Existenzanforderung -e wählen, für geplante Namen -m ausdrücklich als Berechnung kennzeichnen. Bei beliebigen Dateinamen die Newline-Verluste von Befehlsersetzung und die NUL-Option berücksichtigen.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. -e, -m und relative Ausgabe im eigenen Baum geprüft, -L/-P-Sonderfälle und paralleler Austausch offen. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| readlink | Gespeicherter Linktext oder alternative Kanonisierung |
| dirname | Elternanteil rein als Zeichenfolge |
| ln | Verweise anlegen |

Herkunft: Originaldatensatz 193 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
