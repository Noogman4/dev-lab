---
id: "patch"
name: "patch"
command: "patch"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "patch"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 669
reviewed_at: "2026-11-13"
locally_checked_version: "GNU patch 2.7.6"
---

# patch – Eine selbst erzeugte Textänderung gezielt anwenden

## 1. Kurzbeschreibung

patch wendet eine Differenzbeschreibung auf Dateien an.

## 2. Was macht der Befehl?

Pfadkomponenten werden mit -p gekürzt; falsche Auswahl kann andere Dateien treffen. --dry-run prüft die geplante Anwendung, schreibt aber das Ergebnis nicht. Fuzz und Offsets können eine Änderung an nicht exakt passendem Kontext anwenden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/patch.1.html)

## 3. Syntax

```text
patch [OPTIONEN] [ORIGINALDATEI [PATCHDATEI]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --dry-run | Vorschau |
| -p ZAHL | Pfadbestandteile entfernen |
| --fuzz=0 | Kein unscharfer Kontextabgleich |
| --batch | Nicht interaktiv fragen |
| -i DATEI | Patchquelle |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'alt\n' > own.txt
cat > own.patch <<'PATCHDATA'
--- own.txt
+++ own.txt
@@ -1 +1 @@
-alt
+neu
PATCHDATA
patch --dry-run --batch --fuzz=0 -p0 -i own.patch
patch --batch --fuzz=0 -p0 -i own.patch
printf 'neu\n' > expected.txt
cmp own.txt expected.txt
cat own.txt
```

### Schritt 3: Ergebnis einordnen

Ein eigener Einzeilenpatch wird erst vorgeprüft, dann im privaten Ordner angewendet und byteweise kontrolliert. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Kleine eigene Textdaten nachvollziehbar untersuchen oder umformen. Die gewählte Operation und Ausgabequelle vor einer Verwendung in Skripten ausdrücklich festlegen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Patches und enthaltene Zielpfade vor jeder Anwendung lesen. Keine Projektdatei und kein realer Checkout gepatcht. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unerwartete Ausgabe | Optionen, Eingabeformat und Locale prüfen |
| Permission denied | Pfad- und Leserechte prüfen, nicht automatisch sudo ergänzen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU patch 2.7.6. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cat | Unveränderte Textausgabe |
| od | Byteansicht |
| wc | Mengenangaben |

Ausgangsdatensatz 669 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
