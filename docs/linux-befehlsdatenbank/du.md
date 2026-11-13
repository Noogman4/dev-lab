---
id: "du"
name: "du"
command: "du"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "du"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 182
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# du – Dateibelegung und logische Länge auseinanderhalten

## 1. Kurzbeschreibung

du schätzt den für Dateien und Verzeichnisbäume belegten Speicher. Es beantwortet eine andere Frage als df, das den Zustand eines ganzen Dateisystems meldet.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Die normale Ausgabe verwendet belegte Blöcke, nicht die logische Dateilänge. --apparent-size zeigt dagegen die sichtbare Länge, -b kombiniert das mit der Einheit ein Byte. Sparse-Dateien können deshalb eine große logische Länge bei geringer Belegung haben. Verzeichnismetadaten, Hardlinks, Kompression, CoW und Snapshots beeinflussen die Einordnung: du ist keine Garantie, wie viel Platz eine Löschung tatsächlich freigeben würde. Hardlinks werden standardmäßig nicht mehrfach als derselbe Dateiinhalt gezählt; -l ändert diese Regel. Ohne Zielargument wird der aktuelle Baum untersucht.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt du invocation](https://www.gnu.org/software/coreutils/manual/html_node/du-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
du [OPTIONEN] [DATEI_ODER_ORDNER ...]
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -s | Nur Summe je Argument |
| -h | Lesbare Größen in 1024er-Einheiten |
| -b | Logische Länge in Bytes |
| -B1 | Belegte Größe in Byteeinheiten |
| -d TIEFE | Berichtstiefe begrenzen, nicht die zugrunde liegende Summierung |
| -x | Andere Dateisysteme beim Abstieg auslassen |
| -L | Symlinkziele einbeziehen, Suchbereich kann wachsen |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Es entsteht ausschließlich eine neue kleine Sparse-Datei mit 1 MiB logischer Länge. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-du-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
truncate -s 1048576 -- eigene-sparse.bin
LC_ALL=C du -b -- eigene-sparse.bin > logisch.txt
LC_ALL=C du -B1 -- eigene-sparse.bin > belegt.txt
test "$(cut -f1 logisch.txt)" -eq 1048576
cat logisch.txt belegt.txt
)
```

### Schritt 3: Ergebnis verstehen

truncate erzeugt die eigene Datei ohne Nutzdatenblöcke vollständig ausschreiben zu müssen. du -b muss 1048576 melden; du -B1 zeigt die tatsächliche lokale Belegung, deren konkrete Zahl absichtlich nicht vorausgesetzt wird. Der Test belegt die logische Länge und beide Aufrufarten, keine allgemeine Speicherersparnis auf jedem Dateisystem.

## 6. Typische Anwendungsfälle

Belegung eigener Ordner vergleichen, große Teilbäume eingrenzen oder Dateilänge und belegte Blöcke getrennt dokumentieren. -h eignet sich zum Lesen, eine explizite Einheit für berechenbare Vergleiche.

## 7. Risiken, Nebenwirkungen und Vorsicht

Große rekursive Läufe können viele Metadaten lesen und langsame beziehungsweise entfernte Dateisysteme belasten. -L erweitert den Wirkungsbereich durch Links. Nicht lesbare Bereiche machen Summen unvollständig. Geschützte fremde Bäume nicht allein für eine vollständigere Zahl mit sudo öffnen. Geöffnete bereits gelöschte Dateien erscheinen nicht mehr unter ihrem alten Pfad, können aber weiterhin Platz im Dateisystem belegen.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| du und df stimmen nicht überein | Dateibaum und Dateisystembelegung sind verschiedene Messgrößen |
| Hardlinks verändern Summen | Argumentreihenfolge und Mehrfachzählung mit -l berücksichtigen |
| Tiefenbegrenzung spart kaum Zeit | -d begrenzt Berichtzeilen, die Summierung benötigt weiterhin tiefere Daten |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zielpfad und gewünschte Messgröße zuerst festlegen. Die Einheit ausdrücklich benennen; -h nicht als exakte Bytezahl weiterverarbeiten. Bei Sparse-, Snapshot- oder CoW-Daten die sichtbare du-Zahl nicht mit einer garantierten Freigabemenge gleichsetzen.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine fremden Bäume, Netzlaufwerke, CoW-Snapshots oder Mehrfach-Hardlinks geprüft. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| df | Freier Speicher des Dateisystems |
| stat | Länge und Blöcke einer Datei |
| ls | Dateilänge in der langen Ansicht |

Herkunft: Originaldatensatz 182 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
