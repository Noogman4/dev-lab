---
id: "find"
name: "find"
command: "find"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "find"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 184
reviewed_at: "2026-11-13"
locally_checked_version: "GNU findutils 4.9.0"
---

# find – Dateibäume mit ausdrücklich gewählten Tests durchsuchen

## 1. Kurzbeschreibung

GNU find durchsucht angegebene Startpfade und wertet für jeden Eintrag einen Ausdruck aus. Dieser Ausdruck kann nur auswählen und drucken, aber auch Programme ausführen oder Dateien löschen.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Zwischen benachbarten Tests gilt normalerweise UND. -a bindet stärker als -o; Klammern sind für gemischte Bedingungen entscheidend. -name vergleicht den letzten Namen, -path den Suchpfad. Shellmuster müssen zitiert werden, damit die Shell sie nicht vor find expandiert. -print0 transportiert auch Namen mit Newlines eindeutig. Das fehlerhaft zitierte /home-Beispiel des Ausgangsdatensatzes wird durch einen kleinen eigenen Baum ersetzt. -delete ist eine aktive Löschaktion und schaltet Tiefendurchlauf ein; es ist kein Zusatz, den man unbesehen an eine Suchzeile hängt.

[Gelesene Primärquelle: GNU find(1)](https://man7.org/linux/man-pages/man1/find.1.html). Ergänzend lokale Hilfe und lokale GNU-findutils-Manpage /usr/share/man/man1/find.1.gz gelesen.

## 3. Syntax

```text
find [-H | -L | -P] STARTPFAD ... [AUSDRUCK]
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -P | Symlinks nicht verfolgen, normale Vorgabe |
| -maxdepth N | Abstiegstiefe begrenzen |
| -type f | Normale Dateien auswählen |
| -name MUSTER | Basename mit Shellmuster vergleichen |
| -print | Einen Treffer pro Zeile ausgeben |
| -print0 | Treffer mit NUL trennen |
| -exec BEFEHL ... | Programm ausführen, zusätzliche Wirkung |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Es wird nur ein neu angelegter eigener Testbaum durchsucht. Die Übung enthält keine ausführenden oder löschenden find-Aktionen. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-find-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
mkdir -p daten/unter
printf 'a\n' > daten/a.log
printf 'b\n' > daten/unter/b.txt
printf 'c\n' > daten/unter/c.bin
find ./daten -maxdepth 2 -type f \( -name '*.log' -o -name '*.txt' \) -print > treffer.txt
LC_ALL=C sort treffer.txt > sortiert.txt
printf './daten/a.log\n./daten/unter/b.txt\n' > erwartet.txt
cmp sortiert.txt erwartet.txt
cat sortiert.txt
)
```

### Schritt 3: Ergebnis verstehen

Alle Namen sind eigene feste Testdaten. -type f wird mit der gesamten geklammerten ODER-Bedingung verknüpft. Es erscheinen die .log- und .txt-Datei, nicht die .bin-Datei. sort wird nur für den stabilen Vergleich eingesetzt; die Durchlaufreihenfolge von find selbst wird nicht als garantiert behauptet. Die Präfixe ./ verhindern eine Verwechslung der Startpfade mit Optionen.

## 6. Typische Anwendungsfälle

Bekannte eigene Bäume nach Namen oder Dateityp eingrenzen. Erst die gedruckte Auswahl verstehen und die Rechte- sowie Versionsbedingungen für eine spätere aktive Aktion separat prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

-exec, -execdir und -delete sind keine reine Anzeige. -L kann in zusätzliche Bereiche führen. Eine Trefferliste ist bei parallel veränderten Dateibäumen kein dauerhafter Identitätsnachweis. Ein Startpfad / oder ein fremder Homebaum ist kein sinnvoller Einsteigertest. -delete und -prune haben durch den Tiefendurchlauf Wechselwirkungen.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Zu viele Treffer bei ODER | UND bindet stärker, die gewollte Gruppierung ausdrücklich klammern |
| Dateimuster schon vor der Suche verändert | *.log vor der Shell durch Anführungszeichen schützen |
| Dateiname mit Minus gilt als Ausdruck | Startpfade mit ./ oder absolut angeben, -- ist hier kein allgemeiner Ausweg |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zielbaum und rein lesende Aktion ausdrücklich angeben. Für beliebige Namen NUL-Ausgabe und einen passenden Empfänger verwenden. Die Suche nicht ungeprüft in eine Löschpipeline umwandeln. Für reale aktive Aktionen ist eine eigene Freigabe nötig.

**Prüfstand am 2026-11-13:** GNU findutils 4.9.0. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine -exec-/Löschaktion, Geräte-, Zeit- oder Rechtefilter praktisch geprüft. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| locate | Suche in einem möglicherweise veralteten Index |
| ls | Anzeige eines bekannten Verzeichnisses |
| grep | Dateiinhalte statt Pfadnamen durchsuchen |

Herkunft: Originaldatensatz 184 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
