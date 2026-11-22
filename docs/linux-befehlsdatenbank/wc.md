---
id: "wc"
name: "wc"
command: "wc"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "wc"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 642
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# wc – Zeilenenden, Wörter und Bytes getrennt zählen

## 1. Kurzbeschreibung

wc liefert Mengenangaben für Eingabedaten.

## 2. Was macht der Befehl?

-l zählt Newline-Zeichen, nicht abstrakte sichtbare Textzeilen. -c zählt Bytes, -m Zeichen gemäß Locale. Wortgrenzen hängen von Zeicheneinordnung und Implementierung ab. Eine letzte Zeile ohne Newline erhöht -l nicht.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/wc.1.html)

## 3. Syntax

```text
wc [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -l | Newlines |
| -w | Wörter |
| -c | Bytes |
| -m | Zeichen |
| -L | Maximale Darstellungsbreite |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins zwei\n' > own.txt
test "$(wc -l < own.txt)" -eq 1
test "$(wc -w < own.txt)" -eq 2
test "$(wc -c < own.txt)" -eq 10
wc -l -w -c own.txt
```

### Schritt 3: Ergebnis einordnen

Der eigene ASCII-Text besitzt eine Newline, zwei Wörter und zehn Bytes. Unicode- und Leerraumspezialfälle bleiben offen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zeilenenden, Wörter, Bytes oder Zeichen zählen und die gewählte Einheit im Ergebnis nennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Zählungen prüfen weder Inhalt noch Herkunft. Dateiname und Summenzeile bei Mehrdateiausgabe nicht mit Daten verwechseln. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Letzte sichtbare Zeile fehlt bei -l | Ohne abschließendes Newline zählt sie nicht als weiteres Newline |
| Bytes und Zeichen unterscheiden sich | Mehrbytecodierung und gewählte Locale berücksichtigen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| od | Byteinhalt prüfen |
| awk | Felder und Datensätze verarbeiten |
| head | Lesemenge begrenzen |

Ausgangsdatensatz 642 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
