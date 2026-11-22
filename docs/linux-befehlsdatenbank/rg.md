---
id: "rg"
name: "rg"
command: "rg"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "rg"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 671
reviewed_at: "2026-11-13"
locally_checked_version: "ripgrep 14.1.0, Programm rg"
---

# rg – Ripgrep mit begrenztem Suchziel verwenden

## 1. Kurzbeschreibung

rg ist die Kommandozeile von ripgrep für schnelle Textsuche.

## 2. Was macht der Befehl?

Ohne genaue Ziele wird rekursiv gesucht; Ignoredateien, versteckte und binäre Dateien beeinflussen den Umfang. --no-config vermeidet die werkzeugeigene Konfiguration. -F bezeichnet feste Zeichenfolgen, nicht Regex. Ein Treffer ist keine Vollständigkeitsgarantie für ausgeschlossene Dateien.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://raw.githubusercontent.com/BurntSushi/ripgrep/master/GUIDE.md)

## 3. Syntax

```text
rg [OPTIONEN] MUSTER [PFAD ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --no-config | Konfiguration ignorieren |
| -F | Fester Text |
| -n | Zeilennummern |
| --hidden | Versteckte Dateien |
| --no-ignore | Ignoreregeln abschalten, Bereich vergrößern |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'a.b\naxb\n' > own.txt
rg --no-config --color=never -n -F 'a.b' own.txt > result.txt
printf '1:a.b\n' > expected.txt
cmp result.txt expected.txt
cat result.txt
```

### Schritt 3: Ergebnis einordnen

Explizite eigene Datei und festes Muster liefern genau den erwarteten Treffer. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine eigene Textdaten nachvollziehbar untersuchen oder umformen. Die gewählte Operation und Ausgabequelle vor einer Verwendung in Skripten ausdrücklich festlegen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine fremden Bäume durchsucht. Vorverarbeitungsoptionen können Programme ausführen und wurden nicht verwendet. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unerwartete Ausgabe | Optionen, Eingabeformat und Locale prüfen |
| Permission denied | Pfad- und Leserechte prüfen, nicht automatisch sudo ergänzen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** ripgrep 14.1.0, Programm rg. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cat | Unveränderte Textausgabe |
| od | Byteansicht |
| wc | Mengenangaben |

Ausgangsdatensatz 671 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
