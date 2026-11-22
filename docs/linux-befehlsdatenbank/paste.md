---
id: "paste"
name: "paste"
command: "paste"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "paste"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 668
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# paste – Gleich positionierte Zeilen nebeneinander setzen

## 1. Kurzbeschreibung

paste verbindet entsprechende Zeilen mehrerer Eingaben mit Trennzeichen.

## 2. Was macht der Befehl?

Es verbindet nach Position, nicht nach Schlüssel wie join. Standardtrenner ist Tab. -s verarbeitet eine Datei zeilenweise in einer Ausgabezeile; unterschiedliche Eingabelängen erzeugen entsprechend leere Beiträge.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/paste.1.html)

## 3. Syntax

```text
paste [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -d LISTE | Trennerfolge |
| -s | Serieller Modus |
| -z | GNU-NUL-Datensätze |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'Anna\nBert\n' > names.txt
printf '2\n5\n' > values.txt
paste -d : names.txt values.txt > result.txt
printf 'Anna:2\nBert:5\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Die jeweils gleich positionierten eigenen Zeilen werden zusammengefügt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zwei einfache gleichartig geordnete Zeilenfolgen nebeneinanderstellen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Positionelle Verbindung prüft keine sachliche Zuordnung. Vertauschte Reihenfolgen können unbemerkt falsche Datensätze erzeugen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Falsche Zeilen kombiniert | paste verbindet nach Position, für Schlüsselverknüpfung join prüfen |
| Leere Spalten am Ende | Eine Eingabedatei kann weniger Zeilen als die andere haben |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| join | Schlüsselbasiert verbinden |
| cut | Spalten auswählen |
| cat | Dateien hintereinander ausgeben |

Ausgangsdatensatz 668 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
