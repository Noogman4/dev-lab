---
id: "cksum"
name: "cksum"
command: "cksum"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "cksum"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 651
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# cksum – CRC-Dateiprüfsummen von Kryptografie unterscheiden

## 1. Kurzbeschreibung

cksum berechnet traditionell eine CRC-Prüfsumme mit Bytelänge.

## 2. Was macht der Befehl?

Der POSIX-Standardmodus schützt gegen zufällige Übertragungsfehler, nicht gegen gezielte Manipulation. Neuere GNU-Versionen bieten zusätzliche Algorithmen und Formate. Eine nackte Zahl ohne Angabe von Algorithmus und Quelle ist kein belastbarer Authentizitätsnachweis.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/cksum.1.html)

## 3. Syntax

```text
cksum [OPTIONEN] [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| ohne Option | CRC und Länge |
| -a ALGORITHMUS | GNU-Algorithmusauswahl |
| --tag | Markiertes Ausgabeformat, versionsabhängig |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
printf abc > own.txt
cksum < own.txt > first.txt
cksum < own.txt > second.txt
cmp first.txt second.txt
awk '$2 != 3 {exit 1}' first.txt
printf abcd > own.txt
cksum < own.txt > changed.txt
if cmp -s first.txt changed.txt; then exit 1; fi
cat first.txt
```

### Schritt 3: Ergebnis einordnen

Gleiche eigene Bytes liefern dieselbe Ausgabe mit Länge 3; die Änderung auf vier Bytes wird unterschieden. Kein kryptografischer Sicherheitsnachweis. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

CRC und Bytezahl für eigene Dateien bestimmen oder mit einem ausdrücklich bekannten Referenzverfahren vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Für Angreiferschutz geeignete Authentisierung und vertrauenswürdige Referenzwerte nötig. Für eigene zugängliche Dateien sind keine Root-Rechte nötig. Ausgabeumleitungen können Ziele überschreiben; niemals dieselbe Datei unkontrolliert zugleich als Eingabe und Ausgabe verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ergebnis weicht von anderem Prüftool ab | CRC, Länge und gewählten Algorithmus auseinanderhalten |
| Prüfsumme stimmt und Herkunft ist trotzdem unklar | Der Wert authentisiert weder Absender noch Manifest |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur der konkrete eigene Datenfall aus Abschnitt 5 geprüft; fremde Daten, andere Versionen und nicht verwendete Modi bleiben offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sum | Historische einfache Prüfsummen |
| sha256sum | Kryptografischer Digest |
| wc | Bytezahl allein |

Ausgangsdatensatz 651 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
