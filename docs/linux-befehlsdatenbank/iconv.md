---
id: "iconv"
name: "iconv"
command: "iconv"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "iconv"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 663
reviewed_at: "2026-11-13"
locally_checked_version: "glibc 2.39-0ubuntu8.9"
---

# iconv – Zeichencodierung ausdrücklich konvertieren

## 1. Kurzbeschreibung

iconv wandelt zwischen angegebenen Zeichencodierungen um.

## 2. Was macht der Befehl?

Quellcodierung wird nicht zuverlässig automatisch erkannt. -f und -t sollten deshalb bewusst gesetzt werden. //IGNORE und -c können Daten verwerfen, //TRANSLIT kann Zeichen ersetzen. Erfolgreiche Ausgabe ist dann nicht automatisch verlustfrei.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/iconv.1.html)

## 3. Syntax

```text
iconv [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -f CODE | Quellcodierung |
| -t CODE | Zielcodierung |
| -o DATEI | Ausgabeziel |
| -l | Bekannte Codierungen |
| -c | Nicht darstellbare Zeichen auslassen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf 'Grüße\n' > own.utf8
iconv -f UTF-8 -t ISO-8859-1 own.utf8 > own.latin1
iconv -f ISO-8859-1 -t UTF-8 own.latin1 > back.utf8
cmp own.utf8 back.utf8
cat back.utf8
```

### Schritt 3: Ergebnis einordnen

Die gewählten eigenen Zeichen sind in Latin-1 darstellbar; der Rückweg ergibt identische UTF-8-Bytes. Andere Zeichensätze und Fehlerfälle bleiben offen. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Bekannte Textcodierungen bewusst umwandeln und bei Bedarf eine Rückwandlung als zusätzlichen Datencheck nutzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine verlustbehafteten Optionen im Test. Zeichencodierung und Zeilenenden sind getrennte Probleme. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Invalid or incomplete multibyte | Quellcodierung und vollständige Eingabebytes prüfen |
| Ausgabe verliert Zeichen | -c, //IGNORE und //TRANSLIT können auslassen oder ersetzen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** glibc 2.39-0ubuntu8.9. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| recode | Andere Konvertierungsschnittstelle |
| od | Codierte Bytes untersuchen |
| cmp | Eigene Rückwandlung vergleichen |

Ausgangsdatensatz 663 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
