---
id: "lastb"
name: "lastb"
command: "lastb"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "lastb"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 601
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# lastb – Fehlgeschlagene Anmeldungen aus einer Datei lesen

## 1. Kurzbeschreibung

lastb zeigt fehlgeschlagene Anmeldeversuche aus Btmp-Daten.

## 2. Was macht der Befehl?

Die normale Quelle ist /var/log/btmp, nicht die Wtmp-Datei erfolgreicher Sitzungen. -f wählt eine eigene Datei. Leere Datensätze sind beim util-linux-Parser zulässig; ein leerer Datenbestand belegt aber keine Abwesenheit früherer Angriffe.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/last.1@@util-linux.html)

## 3. Syntax

```text
lastb [OPTIONEN] [BENUTZER oder TTY ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -f DATEI | Andere Btmp-Datei wählen |
| -n ZAHL | Ausgabe begrenzen |
| -R | Hostnamenfeld ausblenden |
| -d | DNS-Auflösung, kann Netzwerk nutzen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
: > own.btmp
LC_ALL=C lastb -f own.btmp -n 2 -R > result.txt
test ! -s own.btmp
cat result.txt
printf "Eigene leere Btmp verarbeitet\n"
```

### Schritt 3: Ergebnis einordnen

Nur der Leerdatei-Pfad wurde geprüft, keine tatsächlichen Anmeldeereignisse. System-Btmp und DNS wurden nicht verwendet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Format und Quelle einer später freigegebenen Analyse verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Reale Authentisierungshistorie ist vertraulich. Keine Systemprotokolle anlegen oder bereinigen. Fehlende Einträge sind kein Sicherheitsbeweis.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Permission denied | Nicht vorsorglich sudo ergänzen |
| Quelle fehlt | Ausgewählten Pfad prüfen, keine Systemdatei erzeugen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** util-linux 2.39.3. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| last | Erfolgreiche Sitzungen |
| lastlog | Letzte Anmeldung je Konto |
| ac | Summierte Sitzungszeit |

Ausgangsdatensatz 601 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
