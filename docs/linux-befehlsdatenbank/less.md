---
id: "less"
name: "less"
command: "less"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "less"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 629
reviewed_at: "2026-11-13"
locally_checked_version: "less 590; Version gelesen, Interaktivbetrieb offen"
---

# less – Dateien seitenweise betrachten

## 1. Kurzbeschreibung

less ist ein interaktiver Pager mit Such- und Navigationsfunktionen.

## 2. Was macht der Befehl?

Die Anzeige editiert die Eingabe nicht automatisch. Shell-Escapes, Editorkommandos und Eingabevorverarbeitung über LESSOPEN können jedoch weitere Programme starten. -R reicht bestimmte ANSI-Farbcodes durch; -r ist eine breitere und riskantere Rohdarstellung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/less.1.html)

## 3. Syntax

```text
less [OPTIONEN] DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -N | Zeilennummern |
| -S | Lange Zeilen abschneiden statt umbrechen |
| -R | Bestimmte Farbcodes durchreichen |
| q | Beenden |
| /MUSTER | Vorwärtssuche |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
less -N EIGENE_TEXTDATEI
```

Kein interaktiver Pager gestartet. Ein späterer Test müsste Konfiguration, Vorverarbeitung und Eingabedaten berücksichtigen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Lange eigene Textdateien navigieren; Anzeige von Bearbeitung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbekannte Steuersequenzen und LESSOPEN-Helfer vermeiden. Nicht als unbeschränktes privilegiertes Dateilesewerkzeug freigeben. Keine History oder Benutzersitzung geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Anzeige wartet | q beendet bewusst |
| Andere Ausgabe | Umgebung und Optionen prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** less 590; Version gelesen, Interaktivbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| more | Weiterer Pager |
| head | Begrenzter Auszug |
| cat | Direkte Ausgabe |

Ausgangsdatensatz 629 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
