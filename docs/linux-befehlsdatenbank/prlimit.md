---
id: "prlimit"
name: "prlimit"
command: "prlimit"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "prlimit"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 503
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# prlimit – Ressourcenlimits abfragen und bewusst begrenzen

## 1. Kurzbeschreibung

prlimit liest oder setzt die Ressourcenlimits eines Prozesses. Eine Zuweisung verändert den Zielprozess.

## 2. Was macht der Befehl?

Softlimit und Hardlimit sind getrennte Schranken. Das Softlimit darf das Hardlimit nicht überschreiten. Unprivilegiertes Absenken eines Hardlimits kann für den Prozess nicht einfach rückgängig gemacht werden. Ohne Zuweisung bleibt die hier verwendete Abfrage lesend. Mit einem nachgestellten Programm startet prlimit dieses Programm tatsächlich.

Quelle, am 2026-11-13 gelesen: [util-linux prlimit-Handbuch](https://man7.org/linux/man-pages/man1/prlimit.1.html)

## 3. Syntax

```text
prlimit [OPTIONEN] --pid PID
prlimit [LIMIT=SOFT:HARD] BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --pid PID | Gezielt diesen Prozess abfragen oder ändern. |
| --nofile | Offene Dateideskriptoren; ohne Wert nur lesen. |
| --nofile=SOFT:HARD | Beide Werte setzen; keine Abfrage. |
| --cpu | CPU-Zeitlimit in Sekunden. |
| --as | Virtueller Adressraum in Bytes. |
| --output SPALTEN | Ausgabefelder ausdrücklich festlegen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
prlimit --version
prlimit --pid "$$" --nofile --output RESOURCE,SOFT,HARD,UNITS > limits.txt
cat limits.txt
grep -q NOFILE limits.txt
printf 'Nur Limitabfrage ausgefuehrt
'
```

### Schritt 3: Ergebnis einordnen

Es wird ausschließlich das Dateideskriptorlimit der eigenen Übungsshell abgefragt. Der fehlende Gleichheitswert ist entscheidend: Kein Limit wurde gesetzt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Fehler durch zu wenige Dateideskriptoren untersuchen; Soft- und Hardlimits vergleichen; später gesondert freigegebene Kindprozesse begrenzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine einzelne Zahl bei einer Limitzuweisung setzt beide Grenzen. Bei SOFT: bleibt das bisherige Hardlimit, bei :HARD das Softlimit erhalten. Unbeabsichtigte Grenzsenkungen können Arbeit abbrechen lassen. Keine Limitänderung getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not permitted | Berechtigungen oder Hardlimit verhindern eine Erhöhung. |
| Invalid argument | Softlimit größer als Hardlimit oder ungültige Einheit. |
| Andere Werte im Folgebefehl | PID und Vererbung beachten; nicht jede Shell ist derselbe Prozess. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** util-linux 2.39.3. Praktisch geprüft: Nur eigenes NOFILE gelesen; Änderungen, Vererbung und privilegierte Fälle offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ulimit | Limits der Shell und ihrer Kinder. |
| ps | PID bestimmen. |
| timeout | Laufzeit eines neu gestarteten Befehls begrenzen. |

Ausgangsdatensatz 503 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
