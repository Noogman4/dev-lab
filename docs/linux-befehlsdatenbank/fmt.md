---
id: "fmt"
name: "fmt"
command: "fmt"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "fmt"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 625
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# fmt – Absätze für eine Zielbreite neu umbrechen

## 1. Kurzbeschreibung

fmt formatiert Textabsätze und schreibt das Ergebnis auf Standardausgabe.

## 2. Was macht der Befehl?

Im Gegensatz zu fold kann fmt Eingabezeilen zu Absätzen zusammenführen. Einrückung und Absatzgrenzen beeinflussen das Resultat. Die Breite ist kein zuverlässiger harter Schnitt für überlange Einzelwörter.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/fmt.1.html)

## 3. Syntax

```text
fmt [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -w ZAHL | Zielbreite |
| -s | Nur aufteilen, keine Zeilen verbinden |
| -u | Abstände vereinheitlichen |
| -p TEXT | Präfixauswahl |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins zwei drei vier\n' > own.txt
fmt -w 10 own.txt > result.txt
cat result.txt
test "$(wc -l < result.txt)" -ge 2
```

### Schritt 3: Ergebnis einordnen

Der eigene kurze Absatz wird auf mehrere Zeilen verteilt; geprüft ist dieser konkrete Text, keine allgemeine Maximalbreitengarantie. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Fließtext für eine feste Lesebreite umbrechen; strukturierte Daten und Code davor getrennt behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht auf strukturierte Formate, Tabellen oder Code anwenden, wenn Zeilengrenzen Bedeutung tragen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Mehrere Zeilen werden verbunden | fmt formatiert Absätze, für reines Brechen -s prüfen |
| Sehr langes Wort überschreitet die Breite | Die Zielbreite erzwingt keinen beliebigen Schnitt im Wort |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| fold | Zeilen an einer Breite umbrechen |
| expand | Tabstopps auflösen |
| wc | Zeichen und Zeilen zählen |

Ausgangsdatensatz 625 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
