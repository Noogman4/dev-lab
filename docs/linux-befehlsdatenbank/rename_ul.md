---
id: "rename_ul"
name: "rename.ul"
command: "rename.ul"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "rename_ul"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 195
reviewed_at: "2026-11-13"
locally_checked_version: "Util-linux 2.39.3"
---

# rename.ul – Mit Util-linux eine bekannte Teilzeichenfolge ersetzen

## 1. Kurzbeschreibung

rename.ul ist auf diesem System die Rename-Variante von Util-linux. Sie erwartet einen Suchteilstring, einen Ersatz und die ausdrücklich ausgewählten Dateien; kein Perl-Programm.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Normalerweise wird das erste Vorkommen der Teilzeichenfolge im letzten Namensbestandteil ersetzt. -a ersetzt alle, -l das letzte Vorkommen. Wenn Suchtext oder Ersatz einen Slash enthalten, können auch Pfadteile betroffen sein; neue Eltern werden dadurch nicht automatisch erzeugt. Ohne Schutzoptionen ist ein vorhandenes Ziel nicht pauschal geschützt. -s ändert den Zieltext eines Symlinks statt seinen Namen. Diese Wirkungen sind von einer bloßen Vorschau mit -n -v zu unterscheiden. Neuere Online-Handbücher können zusätzliche Optionen enthalten, die lokale Hilfe von 2.39.3 ist für den Test maßgeblich.

[Gelesene Primärquelle: Util-linux rename(1)](https://man7.org/linux/man-pages/man1/rename.1.html). Zusätzlich lokale Manpage /usr/share/man/man1/rename.ul.1.gz und Hilfe von 2.39.3 gelesen.

## 3. Syntax

```text
rename.ul [OPTIONEN] SUCHTEXT ERSATZ DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -n, --no-act | Keine Umbenennung ausführen |
| -v | Vorgänge beziehungsweise Vorschau anzeigen |
| -o | Vorhandene Ziele nicht überschreiben |
| -a | Alle Vorkommen statt nur des ersten ersetzen |
| -l | Nur letztes Vorkommen ersetzen |
| -s | Zielzeichenfolge von Symlinks verändern statt Linknamen |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Zwei eigene Textdateien mit bekannten Namen werden zunächst in der Vorschau und dann ohne vorhandene Zielkollision umbenannt. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-rename_ul-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
printf 'erste eigene Datei\n' > eins.alt
printf 'zweite eigene Datei\n' > zwei.alt
LC_ALL=C rename.ul -n -v -o -- .alt .neu ./eins.alt ./zwei.alt
test -f eins.alt
test -f zwei.alt
rename.ul -o -- .alt .neu ./eins.alt ./zwei.alt
test ! -e eins.alt
test ! -e zwei.alt
printf 'erste eigene Datei\n' > erwartet-eins.txt
printf 'zweite eigene Datei\n' > erwartet-zwei.txt
cmp eins.neu erwartet-eins.txt
cmp zwei.neu erwartet-zwei.txt
printf 'Zwei eigene neue Namen und Inhalte geprueft\n'
)
```

### Schritt 3: Ergebnis verstehen

Die erste Ausführung meldet die Planung und belässt beide .alt-Namen. Die zweite Ausführung erzeugt die .neu-Namen; die vorherigen Namen verschwinden. Beide Inhalte werden gegen eigene erwartete Texte verglichen. Der Suchtext .alt ist hier eine wörtliche Zeichenfolge und keine Regex, weshalb keine Perl-Maskierung benutzt wird.

## 6. Typische Anwendungsfälle

Einfache Umbenennungen einer bekannten eigenen Dateigruppe. Sobald Bedingungen, Kollisionen oder Pfadänderungen kompliziert werden, den Plan einzeln prüfen und nicht die ganze Namensserie blind bearbeiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein leerer Suchtext, ein Slash oder eine breite Shellauswahl kann unerwartet viele Namen ändern. Auch mit -o ist eine Gruppe kein atomarer Gesamtvorgang; Teilstände sind möglich. -s verändert Linkziele. Diese Modi wurden nicht getestet. Die ursprüngliche Datenbankeinstufung als sicher lesend trifft auf eine echte Umbenennung nicht zu.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Perl-Ausdruck wird nicht ausgeführt | Util-linux nutzt Teilstrings, nicht Perl-Code |
| Vorschau zeigt nichts | -n zusätzlich mit -v verbinden und Auswahl prüfen |
| Nur Teilmenge umbenannt | Status und konkrete Kollisionsmeldungen lesen, nicht pauschal erneut ohne Schutz ausführen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Feste eigene Dateinamen, -n -v zur Prüfung und -o für den tatsächlichen Schritt verwenden. Die Vorschau kann zwischenzeitliche Änderungen nicht verhindern. In Skripten auch beachten, dass diese Familie einen besonderen Nicht-umbenannt-Status haben kann; die lokale Manpage nennt 4 für keinen umbenannten Eintrag.

**Prüfstand am 2026-11-13:** Util-linux 2.39.3. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur Vorschau und eigene kollisionsfreie Umbenennung geprüft, kein -s und kein vorhandenes Ziel überschrieben. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| rename | Je nach Installation andere Familie, hier Perl separat |
| mv | Einzelne gezielte Umbenennung |
| ls | Aktuelle Namen anzeigen |

Herkunft: Originaldatensatz 195 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
