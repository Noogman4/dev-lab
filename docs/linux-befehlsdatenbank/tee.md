---
id: "tee"
name: "tee"
command: "tee"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "tee"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 640
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# tee – Daten gleichzeitig ausgeben und in eine Datei schreiben

## 1. Kurzbeschreibung

tee kopiert Standardeingabe auf Standardausgabe und in benannte Dateien.

## 2. Was macht der Befehl?

Ohne -a werden vorhandene Ziele überschrieben. Mehrere Ziele sind getrennte Schreibvorgänge, keine atomare Transaktion. Fehler einer Pipeline und Fehler beim Schreiben müssen in Skripten ausdrücklich berücksichtigt werden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/tee.1.html)

## 3. Syntax

```text
tee [OPTIONEN] [AUSGABEDATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -a | Anhängen statt Überschreiben |
| -i | Interruptsignal ignorieren, kein Sicherungsmodus |
| --output-error=MODUS | GNU-Fehlerverhalten steuern |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eigene Daten\n' > own.txt
tee copy.txt < own.txt > output.txt
cmp own.txt copy.txt
cmp own.txt output.txt
cat output.txt
```

### Schritt 3: Ergebnis einordnen

Dateikopie und Standardausgabe werden jeweils byteweise gegen die eigenen Eingabedaten geprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Dieselben eigenen Eingabedaten zugleich anzeigen und in ein ausdrücklich neues Ziel schreiben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein privilegierter tee-Aufruf kann Systemdateien ändern. Keine solchen Ziele und kein Anhängemodus an Benutzerdateien getestet. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zieldatei hat alten Inhalt verloren | Ohne -a wird das Ziel überschrieben |
| Pipeline wirkt erfolgreich trotz Teilfehler | Schreibfehler und Status aller relevanten Pipelineglieder getrennt prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cat | Daten ohne Dateiverzweigung ausgeben |
| printf | Eigene Eingabe erzeugen |
| wc | Weitergeleitete Daten zählen |

Ausgangsdatensatz 640 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
