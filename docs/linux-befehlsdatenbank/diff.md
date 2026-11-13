---
id: "diff"
name: "diff"
command: "diff"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "diff"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 656
reviewed_at: "2026-11-13"
locally_checked_version: "GNU diffutils 3.10"
---

# diff – Zeilenunterschiede nachvollziehbar anzeigen

## 1. Kurzbeschreibung

diff vergleicht Textdateien und beschreibt Unterschiede.

## 2. Was macht der Befehl?

Status 0 bedeutet gleich, 1 Unterschiede, 2 Fehler. -u liefert Kontext mit Änderungszeilen; das ist Dateninhalt, noch keine angewendete Änderung. Ignorieroptionen können fachlich wichtige Unterschiede verdecken.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/diff.1.html)

## 3. Syntax

```text
diff [OPTIONEN] DATEI1 DATEI2
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -u | Unified-Kontext |
| -r | Verzeichnisse rekursiv |
| -q | Nur Unterschied melden |
| -w | Leerraum ignorieren, bewusst verwenden |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eins\n' > a.txt
printf 'zwei\n' > b.txt
if diff -u a.txt b.txt > own.diff; then code=0; else code=$?; fi
test "$code" -eq 1
grep -q '^-eins' own.diff
grep -q '^+zwei' own.diff
cat own.diff
```

### Schritt 3: Ergebnis einordnen

Der erwartete Unterschied wird als Status 1 behandelt und inhaltlich geprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zwei Textfassungen vergleichen und den Unified-Bericht als Änderungsbeschreibung getrennt vom Anwenden lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine automatische Anwendung eines fremden Diff. Ein ausgeblendeter Unterschied ist keine Bytegleichheit. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 1 im Skript | Erkannte Unterschiede sind ein fachliches Ergebnis, Status 2 bedeutet Fehler |
| Änderung fehlt im Bericht | Ignorieroptionen wie -w können Unterschiede verdecken |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cmp | Bytevergleich |
| patch | Änderungsbeschreibung anwenden |
| diff3 | Drei Fassungen vergleichen |

Ausgangsdatensatz 656 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
