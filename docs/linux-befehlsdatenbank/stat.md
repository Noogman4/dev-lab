---
id: "stat"
name: "stat"
command: "stat"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "stat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 199
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# stat – Dateimetadaten und Dateiidentität gezielt auslesen

## 1. Kurzbeschreibung

GNU stat zeigt Metadaten einer Datei oder eines Dateisystems. Es kann konkrete Werte wie Dateilänge, Modus, Inode und Hardlinkzahl getrennt von einer dekorierten ls-Ansicht ausgeben.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Ohne -L wird ein übergebener Symlink selbst beschrieben, mit -L dessen Ziel. -f wechselt auf Dateisysteminformationen, deren Formatcodes andere Bedeutungen haben können. %s ist die logische Größe in Bytes, %b die Anzahl zugeordneter Blöcke und %B deren berichtete Einheit. Eine Inodenummer ist nur zusammen mit dem Dateisystem-/Gerätekontext sinnvoll. %x, %y und %z betreffen Zugriffs-, Inhaltsänderungs- und Statusänderungszeit; die letzte ist keine Erstellungszeit. Eine Erstellungszeit kann als %w vorliegen oder unbekannt sein.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt stat invocation](https://www.gnu.org/software/coreutils/manual/html_node/stat-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
stat [OPTIONEN] DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -c FORMAT | Gezielte Ausgabe mit anschließendem Newline |
| --printf=FORMAT | Escape-Sequenzen interpretieren, Newline ausdrücklich angeben |
| -L | Symlinkziel statt Link selbst beschreiben |
| -f | Dateisystem statt Dateimetadaten |
| %s | Logische Bytezahl |
| %a | Modus als Oktalzahl |
| %d:%i | Dateisystem-/Gerätekennung und Inode gemeinsam |
| %h | Zahl der Hardlinks |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Es werden ausschließlich eine neue eigene Textdatei und ein eigener Symlink im Übungsordner betrachtet. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-stat-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
printf 'abc' > eigene-datei.txt
chmod 0600 -- eigene-datei.txt
ln -s -- eigene-datei.txt verweis
LC_ALL=C stat -c '%s %a' -- eigene-datei.txt > werte.txt
printf '3 600\n' > erwartet.txt
cmp werte.txt erwartet.txt
test "$(LC_ALL=C stat -c '%F' -- verweis)" = 'symbolic link'
test "$(stat -L -c '%s' -- verweis)" = 3
stat -c '%d:%i %h %n' -- eigene-datei.txt
cat werte.txt
)
```

### Schritt 3: Ergebnis verstehen

Die Datei enthält genau drei Bytes ohne Newline und hat nach dem eigenen chmod den Modus 600. Der erste Vergleich prüft beide Angaben. Ohne -L wird der Link als symbolic link erkannt, mit -L die Länge seiner eigenen Zieldatei gelesen. Konkrete Inodenummern werden nur angezeigt, nicht als konstante Testausgabe festgeschrieben.

## 6. Typische Anwendungsfälle

Größen- und Rechteangaben in einer eigenen Übung vergleichen oder Hardlinkidentität, Zeitfelder und Linktypen gezielt erklären. Zum Formatprüfen ist file zuständig, zum rekursiven Belegungsvergleich du.

## 7. Risiken, Nebenwirkungen und Vorsicht

Metadaten können vertrauliche Namen und Kennungen enthalten. Eine Abfrage kann je nach Pfad entfernte Dateisysteme oder Automount-Verhalten berühren. --cached=never ist deshalb keine folgenlose Standardergänzung. Eine einzelne Statusabfrage ist keine sichere Zusicherung für eine spätere Öffnung, weil Datei und Pfad inzwischen ausgetauscht werden können.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| ctime wird als Erstellungszeit gelesen | %z ist Statusänderung, %w kann echte Birth-Zeit oder unbekannt sein |
| Symlinklänge statt Zieldateilänge | Ohne -L gilt das Linkobjekt |
| Ein Formatcode liefert unter -f etwas anderes | Datei- und Dateisystemformate nicht mischen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Formatstring zitieren und die benötigten Felder sowie den Modus ausdrücklich benennen. Für Skripte mit unkontrollierten Namen nicht ungeprüft einen Newline-Trenner als eindeutig annehmen. Auch passende Metadaten beweisen weder sicheren Inhalt noch vertrauenswürdige Herkunft.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur eigene Datei-/Linkmetadaten geprüft, keine Fernsysteme, Automounts oder Zeitstempelauswertung. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ls | Menschenlesbare Metadatenansicht |
| du | Rekursive belegte Größe |
| readlink | Gespeicherten Linktext lesen |

Herkunft: Originaldatensatz 199 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
