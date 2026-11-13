---
id: "ls"
name: "ls"
command: "ls"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "ls"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 188
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# ls – Dateinamen und Metadaten kontrolliert anzeigen

## 1. Kurzbeschreibung

ls zeigt Informationen über Dateien und Verzeichnisse. Ohne Pfad wird das aktuelle Verzeichnis aufgelistet, normalerweise ohne Namen mit führendem Punkt.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Die Darstellung hängt unter anderem von Terminal, Locale und gewählten Optionen ab. -l zeigt Metadaten wie Rechte, Hardlinkzahl, Eigentümer, Größe und einen Zeitstempel. Die angezeigte Dateigröße ist nicht automatisch der belegte Speicher. Bei einem Verzeichnis beschreibt dessen eigene Größe nicht die Summe seines Inhalts. -d wählt das Verzeichnis selbst. Der normale lange Zeitstempel bezeichnet mtime; ctime ist die Zeit der Metadatenänderung und keine allgemeine Erstellungszeit. Dateinamen können Leerzeichen, Newlines und Steuerzeichen enthalten, weshalb ein hübsches Listing keine universelle maschinenlesbare Dateiliste ist.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt ls invocation](https://www.gnu.org/software/coreutils/manual/html_node/ls-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
ls [OPTIONEN] [DATEI_ODER_ORDNER ...]
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -l | Lange Metadatenansicht |
| -A | Punktnamen außer . und .. |
| -d | Verzeichnisobjekt statt dessen Inhalt |
| -h | Größen lesbar skalieren, mit -l oder -s |
| -n | Numerische Benutzer-/Gruppenkennung in langer Ansicht |
| -b | Nichtgrafische Zeichen als Escape darstellen |
| -1 | Einen Eintrag pro Zeile |
| --color=never | Farbcodes abschalten |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Es werden nur eigene Dateien in einem neuen Datenordner angezeigt. Der Vergleich nutzt einfache ASCII-Namen. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-ls-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
mkdir daten
printf 'eigener Text\n' > daten/notiz.txt
printf 'eigene Vorgabe\n' > daten/.vorgabe
LC_ALL=C ls -1Ab --color=never -- daten > liste.txt
printf '.vorgabe\nnotiz.txt\n' > erwartet.txt
cmp liste.txt erwartet.txt
LC_ALL=C ls -ld -- daten > objekt.txt
grep -q '^d' objekt.txt
cat liste.txt objekt.txt
)
```

### Schritt 3: Ergebnis verstehen

Im ersten Listing erscheinen genau die beiden selbst angelegten Namen. Das zweite Listing beschreibt wegen -d den Ordner daten selbst, erkennbar am führenden d. Konkrete Benutzerkennungen und Zeiten werden nicht fest vorgegeben. Die Syntaxkombination ist getestet, eine vollständige Prüfung aller ACL-, SELinux- oder Symlinkfälle ist das nicht.

## 6. Typische Anwendungsfälle

Bekannte eigene Ordner überblicken und Dateimetadaten vor einer weiteren Bearbeitung lesen. Für konkrete Messwerte stat, für Speicherbelegung du und für ausgewählte Pfade find vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Metadaten und Dateinamen können vertrauliche Inhalte verraten. -R kann große Bäume erfassen, -L die Betrachtung auf Linkziele verändern. Ungequotete Ausgabe kann in nachgeschalteten Skripten falsch zerlegt werden. Ein Alias oder Umgebungsoptionen können Farbe und Darstellungsregeln ergänzen. Ein erfolgreicher Befehl garantiert keinen unveränderten Zustand unmittelbar danach.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Versteckte Datei fehlt | Punktnamen werden ohne -a oder -A ausgelassen |
| Ordnergröße ist unerwartet klein | Die eigene Verzeichnisgröße ist keine rekursive Inhaltssumme |
| Ausgabe verändert sich in einer Pipe | Terminalabhängige Formatierung und Quotierung berücksichtigen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für Menschen passende Anzeigeoptionen ausdrücklich wählen. ls-Ausgabe nicht mit einfachen Leerraumtrennungen als sichere Dateiliste parsen; für beliebige Namen etwa find -print0 und einen passenden Empfänger verwenden. Rechtezeichen und tatsächliche Zugriffsentscheidung einschließlich ACLs getrennt beurteilen.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur einfache Namen und Verzeichnis-/Dateiansicht geprüft, keine ACL-/Spezialdatei- oder Fremdbaumsuche. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| stat | Ausgewählte Metadatenfelder |
| du | Belegung des Dateibaums |
| find | Dateiauswahl mit NUL-Ausgabe |

Herkunft: Originaldatensatz 188 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
