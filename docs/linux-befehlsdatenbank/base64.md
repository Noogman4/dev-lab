---
id: "base64"
name: "base64"
command: "base64"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "base64"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 649
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# base64 – Binärdaten als Text kodieren und dekodieren

## 1. Kurzbeschreibung

base64 kodiert Daten in ein gewähltes Textalphabet und kann sie zurückwandeln.

## 2. Was macht der Befehl?

Kodierung verschleiert keine Geheimnisse und prüft keine Herkunft. Die Wahl des Alphabets und der Zeilenumbrüche muss zum Gegenüber passen. Bei basenc ist das Alphabet ausdrücklich erforderlich; die lokale Version bietet nicht alle neueren Onlinealphabete.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/base64.1.html)

## 3. Syntax

```text
base64 [OPTIONEN] [DATEI]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -d | Dekodieren |
| -w 0 | Zeilenumbruch beim Kodieren abschalten |
| -i | Fremdzeichen ignorieren, nur mit bewusstem Fehlerkonzept |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'AB\000C' > own.bin
base64 -w 0 own.bin > encoded.txt
base64 -d encoded.txt > back.bin
cmp own.bin back.bin
cat encoded.txt
printf '\n'
```

### Schritt 3: Ergebnis einordnen

Die vier eigenen Bytes durchlaufen Kodierung und Rückwandlung; cmp bestätigt Gleichheit. Fehlerhafte und fremde Eingaben wurden nicht funktional geprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene Bytes in eine textuelle Darstellung überführen; geheimen Inhalt durch Kodierung nicht als geschützt betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Dekodierte Daten bleiben unvertrauenswürdige Daten und dürfen nicht automatisch ausgeführt werden. -i kann beschädigte Eingaben weniger auffällig machen. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| URL-Text wird abgewiesen | Standard-Base64 und URL-Alphabet unterscheiden |
| Ausgabe hat Umbrüche | Beim GNU-Werkzeug -w 0 wählen, wenn das Transportformat eine einzelne Zeile verlangt |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| basenc | Unter anderem Base64url |
| base32 | Anderes Alphabet |
| cmp | Dekodierte Bytes vergleichen |

Ausgangsdatensatz 649 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
