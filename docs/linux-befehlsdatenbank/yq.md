---
id: "yq"
name: "yq"
command: "yq"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "yq"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 687
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Implementierung und Ausführung offen"
---

# yq – Gleichnamige Yq-Implementierungen unterscheiden

## 1. Kurzbeschreibung

yq ist kein eindeutiger Implementierungsname: verbreitet sind Mike Farahs Go-Werkzeug und Kislyuks jq-Wrapper.

## 2. Was macht der Befehl?

Dieses Beispiel bezieht sich auf Mike Farah yq v4. eval verarbeitet YAML-Dokumente nacheinander. Der Python-Wrapper besitzt eine andere CLI und Darstellungslogik; Optionen sind nicht austauschbar. Lokales yq fehlt, deshalb wurde keine konkrete installierte Variante behauptet. Zusätzlich gelesen: [Kislyuk-yq-Projektdokumentation](https://github.com/kislyuk/yq).

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://mikefarah.gitbook.io/yq/commands/evaluate)

## 3. Syntax

```text
yq eval [OPTIONEN] AUSDRUCK DATEI ...  (Mike Farah v4)
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| eval | Ausdruck auswerten |
| -n | Neues Dokument ohne Eingabe |
| -i | Datei in-place ändern |
| -o=json | JSON-Ausgabe (Mike Farah) |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
yq eval ' .name ' EIGENE_YAML_DATEI
```

Nicht ausgeführtes Variantenmuster. Kein yq installiert, kein jq-Ersatzlauf als yq-Test gezählt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

YAML-Abfragen vor Einsatz anhand der tatsächlichen Variante auswählen.

## 7. Risiken, Nebenwirkungen und Vorsicht

-i kann Konfiguration ändern. Ausdruck und Umgebungszugriffe sind keine passiven Texte. Fremde YAML-Tags und Formatdetails gesondert prüfen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Option unbekannt | Andere Implementierung oder Version |
| Kommentare fehlen | Ein-/Ausgabeformat und Rundlaufgrenzen prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Implementierung und Ausführung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| jq | JSON-Filter |
| xmlstarlet | XML |
| cat | Nur Textanzeige |

Ausgangsdatensatz 687 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
