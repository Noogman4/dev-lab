---
id: "cmp"
name: "cmp"
command: "cmp"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "cmp"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 652
reviewed_at: "2026-11-13"
locally_checked_version: "GNU diffutils 3.10"
---

# cmp – Zwei Dateien byteweise vergleichen

## 1. Kurzbeschreibung

cmp vergleicht Bytes und kann einen Unterschied oder Gleichheit per Status melden.

## 2. Was macht der Befehl?

Status 0 bedeutet gleich, 1 verschieden, 2 Fehler. Diese Unterscheidung ist für Skripte wesentlich. Ohne -s wird normalerweise der erste Unterschied beschrieben. -l zeigt mehrere abweichende Bytepositionen und Werte.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cmp.1.html)

## 3. Syntax

```text
cmp [OPTIONEN] DATEI1 DATEI2
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -s | Keine Meldungen, Status bleibt |
| -l | Alle Unterschiede |
| -n ZAHL | Vergleich begrenzen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf abc > a.bin
cp a.bin b.bin
cmp -s a.bin b.bin
printf abd > b.bin
if cmp -s a.bin b.bin; then code=0; else code=$?; fi
test "$code" -eq 1
printf 'Byteunterschied erkannt\n'
```

### Schritt 3: Ergebnis einordnen

Sowohl der Gleichheitsfall als auch Status 1 bei eigener Änderung werden geprüft. Status 2 würde den Test nicht bestehen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Zwei kleine Dateien direkt bytegenau vergleichen und Gleichheit von Verschiedenheit sowie Lesefehlern unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein begrenzter Vergleich beweist nur Gleichheit des gewählten Bereichs. Keine Quell- oder Zieldatei wird durch cmp verändert. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 1 wird als Ausführungsfehler behandelt | Er bedeutet erkannte Verschiedenheit, Status 2 einen Fehler |
| Ausgabe sieht anders als Hexdump aus | -l gibt Bytewerte in Oktal aus, nicht automatisch hexadezimal |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU diffutils 3.10. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| diff | Zeilenorientierter Vergleich |
| sha256sum | Manifestvergleich |
| od | Einzelne Bytewerte darstellen |

Ausgangsdatensatz 652 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
