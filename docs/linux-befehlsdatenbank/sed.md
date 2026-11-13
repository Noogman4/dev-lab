---
id: "sed"
name: "sed"
command: "sed"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "sed"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 674
reviewed_at: "2026-11-13"
locally_checked_version: "GNU sed 4.9"
---

# sed – Textströme ohne Änderung der Quelle bearbeiten

## 1. Kurzbeschreibung

sed führt ein Bearbeitungsprogramm auf einem Textstrom aus.

## 2. Was macht der Befehl?

Ohne -i geht die Ausgabe auf Standardausgabe. s/MUSTER/ERSATZ/ ersetzt standardmäßig den ersten Treffer je ausgewähltem Musterraum, g alle passenden Treffer darin. -n unterdrückt die automatische Ausgabe. Befehle wie e, r und w haben zusätzliche Wirkungen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sed.1.html)

## 3. Syntax

```text
sed [OPTIONEN] 'PROGRAMM' [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -e PROGRAMM | Bearbeitungsprogramm |
| -n | Nur explizit drucken |
| -E | Erweiterte Regex |
| -i | Eingaben ersetzen |
| --sandbox | GNU-Sperre für e/r/w |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'alt alt\n' > own.txt
cp own.txt before.txt
sed --sandbox 's/alt/neu/g' own.txt > result.txt
printf 'neu neu\n' > expected.txt
cmp result.txt expected.txt
cmp own.txt before.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Beide Treffer werden geändert, die eigene Quelldatei bleibt bytegleich. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einfache eigene Texttransformationen zunächst auf Standardausgabe prüfen, bevor ein Schreibziel gewählt wird.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbekannte Sed-Programme nicht ausführen. -i zusammen mit fehlerhaften Druckregeln kann Originaldaten zerstören. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nur erster Treffer je Zeile ersetzt | Beim s-Befehl g nur bei gewünschter globaler Ersetzung ergänzen |
| Ausgabe doppelt | -n unterdrückt die automatische Ausgabe, wenn p ausdrücklich druckt |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU sed 4.9. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| awk | Feld- und datensatzbezogene Programme |
| grep | Zeilen nur auswählen |
| tr | Einzelne Zeichenklassen übersetzen |

Ausgangsdatensatz 674 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
