---
id: "sha224sum"
name: "sha224sum"
command: "sha224sum"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "sha224sum"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 676
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# sha224sum – Eine 224-Bit-Prüfsumme vergleichen

## 1. Kurzbeschreibung

sha224sum erzeugt oder prüft einen Digest mit 224 Bit.

## 2. Was macht der Befehl?

Ein Manifest enthält Werte und Dateinamen. Die Prüfung liest die darin genannten Dateien; sie muss auf bekannte eigene Ziele beschränkt bleiben. Unterschiedliche SHA-Varianten sind verschiedene Algorithmen und nicht austauschbare Beschriftungen. Eine SHA-2-Prüfsumme ist ohne vertrauenswürdige Referenz weder Authentisierung noch Signatur.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sha224sum.1.html)

## 3. Syntax

```text
sha224sum [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c DATEI | Manifest prüfen |
| --status | Nur Rückgabestatus |
| --strict | Ungültige Zeilen beanstanden |
| --tag | Algorithmusmarkierte Ausgabe |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'eigener Inhalt\n' > own.txt
sha224sum own.txt > own.digest
sha224sum -c own.digest
printf 'geändert\n' > own.txt
if sha224sum --status -c own.digest; then exit 1; fi
printf 'Eigene Byteaenderung erkannt\n'
```

### Schritt 3: Ergebnis einordnen

Die unveränderte eigene Datei besteht die Prüfung; danach wird die eigene Änderung erkannt. Das testet den Manifestablauf, nicht kryptografische Kollisionsresistenz. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine eigene Textdaten nachvollziehbar untersuchen oder umformen. Die gewählte Operation und Ausgabequelle vor einer Verwendung in Skripten ausdrücklich festlegen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Prüfwert und Datei aus derselben unzuverlässigen Quelle beweisen keine Herkunft. Eine SHA-2-Prüfsumme ist ohne vertrauenswürdige Referenz weder Authentisierung noch Signatur. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unerwartete Ausgabe | Optionen, Eingabeformat und Locale prüfen |
| Permission denied | Pfad- und Leserechte prüfen, nicht automatisch sudo ergänzen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| b2sum | Andere Digestfamilie |
| md5sum | Schwache Legacy-Prüfung |
| cmp | Direkter Bytevergleich |

Ausgangsdatensatz 676 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
