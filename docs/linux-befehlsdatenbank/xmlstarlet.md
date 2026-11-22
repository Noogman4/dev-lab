---
id: "xmlstarlet"
name: "xmlstarlet"
command: "xmlstarlet"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "xmlstarlet"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 686
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; XPath und Parserverhalten offen"
---

# xmlstarlet – XML mit einem strukturierten Werkzeug abfragen

## 1. Kurzbeschreibung

xmlstarlet bietet XML-Auswahl, Bearbeitung, Formatierung und Validierung als Unterbefehle.

## 2. Was macht der Befehl?

sel verwendet XPath statt regulärer Textsuche. XML-Namensräume gehören zur Struktur: Ein Defaultnamespace im Dokument ist bei XPath nicht automatisch ohne Präfix auswählbar. ed, insbesondere mit In-place-Option, ist ein anderer schreibender Modus.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://xmlstar.sourceforge.net/doc/UG/xmlstarlet-ug.html)

## 3. Syntax

```text
xmlstarlet UNTERBEFEHL [OPTIONEN] [DATEI]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| sel -t | Ausgabevorlage beginnen |
| -v XPATH | Wert ausgeben |
| -N p=URI | Namespacepräfix binden |
| val | Validierungsmodus |
| ed | XML bearbeiten, schreibender Ablauf möglich |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
xmlstarlet sel -t -v '/root/item' EIGENE_XML_DATEI
```

xmlstarlet fehlt. Die einfache XPath-Abfrage bleibt eine Leseübung; kein XML-Dokument oder Schema verarbeitet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

XML-Struktur statt bloßer Zeichenfolgen beurteilen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Externe Ressourcen, DTDs und Optionen des XML-Parsers beeinflussen Verhalten. Keine unbekannten XML-/XSLT-Dateien oder Netzressourcen laden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Leeres Ergebnis | Namespace und XPath prüfen |
| Parsefehler | Wohlgeformtheit von Schemagültigkeit unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; XPath und Parserverhalten offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| jq | JSON-Struktur |
| yq | Varianten für YAML |
| xmllint | Anderes XML-Werkzeug |

Ausgangsdatensatz 686 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
