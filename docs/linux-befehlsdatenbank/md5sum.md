---
id: "md5sum"
name: "md5sum"
command: "md5sum"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "md5sum"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 667
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# md5sum – MD5 nur mit klarer Sicherheitsgrenze verwenden

## 1. Kurzbeschreibung

md5sum berechnet und prüft MD5-Werte.

## 2. Was macht der Befehl?

MD5 ist kollisionsgebrochen und ungeeignet als Sicherheitsnachweis gegen gezielte Manipulation. Vorhandene Legacy-Manifeste können dennoch zufällige Byteänderungen anzeigen. Der Referenzwert muss unabhängig vertrauenswürdig sein; eine Prüfsumme ist keine Signatur.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/md5sum.1.html)

## 3. Syntax

```text
md5sum [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c DATEI | Manifest prüfen |
| --status | Nur Prüfstatus |
| --strict | Fehlerhafte Zeilen beanstanden |
| -b | Binärmodusmarkierung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eigene Datei\n' > own.txt
md5sum own.txt > own.md5
md5sum -c own.md5
printf 'anders\n' > own.txt
if md5sum --status -c own.md5; then exit 1; fi
printf 'Legacy-Pruefung unterscheidet Byteaenderung\n'
```

### Schritt 3: Ergebnis einordnen

Die eigene Byteänderung wird erkannt. Das demonstriert keine Kollisionsresistenz oder Authentizität. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Bestehende Legacy-Manifeste auf zufällige Byteänderungen prüfen und die Grenzen gegen absichtliche Manipulation ausdrücklich benennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Für neue sicherheitsbezogene Anwendungen geeignetes Verfahren und echte Authentisierung wählen. Nur eigene Manifestpfade prüfen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Prüfung meldet Datei fehlt | Relative Manifestnamen im richtigen Arbeitsverzeichnis auswerten |
| Wert stimmt und Datei ist dennoch nicht vertrauenswürdig | MD5-Prüfung ersetzt keine verlässliche Herkunft oder Signatur |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sha256sum | Andere Digestfamilie |
| b2sum | BLAKE2b |
| cmp | Direkter Bytevergleich |

Ausgangsdatensatz 667 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
