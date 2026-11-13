---
id: "diff3"
name: "diff3"
command: "diff3"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "diff3"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 657
reviewed_at: "2026-11-13"
locally_checked_version: "GNU diffutils 3.10"
---

# diff3 – Drei Fassungen mit gemeinsamer Basis vergleichen

## 1. Kurzbeschreibung

diff3 vergleicht drei Textstände und kann ein Mergeergebnis erzeugen.

## 2. Was macht der Befehl?

Für -m ist die Reihenfolge eigene Fassung, ältere Basis, andere Fassung entscheidend. Beide Seiten können dieselbe Basiszeile unterschiedlich ändern; dann entstehen Konfliktmarkierungen. Die Standardausgabe ist keine automatisch freigegebene neue Originaldatei.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/diff3.1.html)

## 3. Syntax

```text
diff3 [OPTIONEN] EIGEN BASIS ANDERE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -m | Merge auf Standardausgabe |
| -A | Konfliktinformation einbeziehen |
| -L NAME | Ausgabelabel |
| -E | Bestimmter Merge-Skriptmodus |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'links\n' > mine.txt
printf 'basis\n' > base.txt
printf 'rechts\n' > other.txt
if diff3 -m mine.txt base.txt other.txt > merged.txt; then code=0; else code=$?; fi
test "$code" -eq 1
grep -q '^<<<<<<<' merged.txt
cat merged.txt
```

### Schritt 3: Ergebnis einordnen

Die absichtliche Kollision liefert Status 1 und Markierungen. Konflikte sind sichtbar, nicht automatisch gelöst. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zwei Änderungen gegen eine bekannte gemeinsame Basis vergleichen und Konflikte sichtbar machen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Reihenfolgeverwechslung kann falsche Mergeentscheidungen erzeugen. Ausgabe prüfen, bevor eine Originaldatei ersetzt wird. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Merge enthält Markierungen | Dieselben Basisbereiche wurden unterschiedlich geändert und benötigen Entscheidung |
| Falsche Reihenfolge | Eigene Fassung, ältere Basis und andere Fassung nicht vertauschen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| diff | Zwei Fassungen |
| sdiff | Nebeneinanderansicht und interaktive Auswahl |
| patch | Vorbereitete Änderungen anwenden |

Ausgangsdatensatz 657 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
