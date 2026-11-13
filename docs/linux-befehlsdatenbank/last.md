---
id: "last"
name: "last"
command: "last"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "last"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 600
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# last – Loginhistorie aus ausgewählter Wtmp-Datei lesen

## 1. Kurzbeschreibung

last aus util-linux zeigt Login- und Logoutinformationen aus Wtmp-Daten.

## 2. Was macht der Befehl?

Die normale Quelle ist eine reale Sitzungsdatei; -f wählt stattdessen eine ausdrückliche Datei. Das ist keine Anzeige gerade aktiver Prozesse und keine vollständige Sicherheitsprüfung. Die util-linux- und GNU-acct-Varianten unterscheiden sich in Optionen. Hier gilt die lokal vorhandene util-linux-Schnittstelle.

Quelle, am 2026-11-13 gelesen: [util-linux: last-Primärhandbuch](https://man7.org/linux/man-pages/man1/last.1@@util-linux.html); lokale Hilfe und Version gelesen

## 3. Syntax

```text
last [OPTIONEN] [BENUTZER oder TTY ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -f DATEI | Andere Wtmp-Datei als Systemstandard wählen. |
| -n ZAHL | Anzahl angezeigter Login-Datensätze begrenzen. |
| -R | Hostnamensfeld nicht anzeigen. |
| -d | DNS-Rückauflösung; kann Netzwerkanfragen auslösen. |
| -x | Zusätzliche Systemereignisse. |
| --time-format iso | Zeitdarstellung mit Zeitzoneninformation. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
: > own.wtmp
LC_ALL=C last -f own.wtmp -n 3 -R > own-result.txt
test ! -s own.wtmp
grep -q 'begins ' own-result.txt
cat own-result.txt
printf 'Nur eigene leere Wtmp-Datei verarbeitet
'
```

### Schritt 3: Ergebnis einordnen

Geprüft ist ausschließlich der erfolgreiche Leerdatei-Pfad mit ausdrücklich gewählter eigener Datei. Die Ausgabe enthält keine tatsächliche Sitzung. Zeiten im Fußtext sind kein Nachweis einer Anmeldung. Echte Sitzungsdatensätze, Uhrsprünge und Rotation bleiben ungeprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einzelsitzungen in einer freigegebenen Datenquelle verstehen; Quelle, Zeitraum und Darstellungsformat bewusst wählen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Loginhistorie enthält personenbezogene Daten. -d kann Netzwerkauflösung auslösen und wurde nicht genutzt. Leere Daten sind kein Beweis, dass niemand angemeldet war. Keine echte Wtmp-/Btmp-Datei gelesen oder angelegt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Quelle fehlt | Keine Systemdatei als Probe erzeugen. |
| Keine Sitzungen | Datei kann leer, rotiert oder unvollständig sein. |
| Andere Optionen | util-linux und GNU acct nicht vermischen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** util-linux 2.39.3. Praktisch geprüft: Eigene leere Datei verarbeitet; keine Login-/Logoutdatensätze, DNS- oder Systemhistorie geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ac | Sitzungszeiten summieren. |
| who | Aktuelle Sitzungen, andere Datenquelle. |
| journalctl | Andere Protokollquelle. |

Ausgangsdatensatz 600 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
