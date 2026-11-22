---
id: "locale"
name: "locale"
command: "locale"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "locale"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 603
reviewed_at: "2026-11-13"
locally_checked_version: "glibc 2.39; Version gelesen, Kategorien nicht praktisch geprüft"
---

# locale – Sprach- und Zeichensatzeinstellungen anzeigen

## 1. Kurzbeschreibung

locale zeigt die wirksamen Locale-Kategorien und vorhandene Localeinformationen.

## 2. Was macht der Befehl?

LC_ALL hat bei gesetztem Wert Vorrang vor den Kategorievariablen; LANG dient als Vorgabe. Diese Werte beeinflussen etwa Sortierung, Zahlenformate und Zeicheneinordnung. Die Anzeige erzeugt keine fehlenden Locales und setzt keine systemweite Sprache.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/locale.1.html)

## 3. Syntax

```text
locale [OPTIONEN] [KATEGORIE oder SCHLÜSSEL ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -a | Verfügbare Locales auflisten |
| -m | Verfügbare Zeichentabellen |
| -k | Schlüssel mit Werten |
| -c | Kategorienamen ergänzen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
LC_ALL=C locale -k LC_NUMERIC
```

Das Muster würde die C-Locale nur für diesen Kindaufruf auswählen. Es wurde nicht ausgeführt; keine Benutzer- oder Systemkonfiguration geändert.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Reproduzierbare Textverarbeitung planen; Zahlenformat und Localevererbung verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eine Localezuweisung kann Parserannahmen ändern. UTF-8-Verfügbarkeit nicht aus bloßem Namen ableiten. --all-locales ist eine Bestandsliste, kein Installationsschritt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Cannot set locale | Gewählte Locale fehlt oder Variablen sind widersprüchlich |
| Andere Sortierung | LC_COLLATE und aktive Kategorien prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** glibc 2.39; Version gelesen, Kategorien nicht praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| localectl | Systemvorgaben |
| sort | Localeabhängige Ordnung |
| iconv | Zeichencodierung |

Ausgangsdatensatz 603 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
