---
id: "more"
name: "more"
command: "more"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "more"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 630
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3; Version gelesen, Interaktivbetrieb offen"
---

# more – Einfaches seitenweises Lesen einordnen

## 1. Kurzbeschreibung

more zeigt Text seitenweise und ist vom direkten cat-Aufruf zu unterscheiden.

## 2. Was macht der Befehl?

Interaktive Tasten hängen von der Implementierung ab. util-linux more kennt Suche und weitere Befehle; moderne Varianten bieten teilweise Rückwärtsnavigation. Bei umgeleiteter Ausgabe entsteht kein Nachweis für die interaktive Bedienung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/more.1.html)

## 3. Syntax

```text
more [OPTIONEN] DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -d | Bedienhinweise |
| -s | Leerzeilen zusammenfassen |
| +ZAHL | Anfangszeile wählen |
| q | Beenden |
| Leertaste | Nächste Seite |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
more EIGENE_TEXTDATEI
```

Das Muster bleibt unausgeführt. Eine Terminaldarstellung und ihre Tasten wurden nicht mit einer Benutzersitzung getestet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Pagerkonzepte in Anleitungen verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Pager können Shell- oder Editorwege besitzen. Fremde Dateien und erhöhte Rechte nicht kombinieren. Keine Terminaleinstellungen oder History verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Wartet auf Eingabe | Bewusst beenden |
| Option anders | BusyBox und util-linux unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** util-linux 2.39.3; Version gelesen, Interaktivbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| less | Erweiterter Pager |
| head | Anfang |
| tail | Ende |

Ausgangsdatensatz 630 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
