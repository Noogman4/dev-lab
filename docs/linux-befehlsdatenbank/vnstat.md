---
id: "vnstat"
name: "vnstat"
command: "vnstat"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "vnstat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 418
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; vnstat fehlt"
---

# vnstat – Gespeicherte Netzwerkverbrauchsstatistik lesen

## 1. Kurzbeschreibung

vnstat zeigt langfristige Verkehrsstatistiken aus seiner Datenbank. Es ist kein Paketmitschnitt und kein Durchsatztest. Abfragen lesbarer Daten brauchen normalerweise kein Root; Datenbankänderungen benötigen passende Schreibrechte.

## 2. Was macht der Befehl?

vnstatd sammelt Interfacezähler, vnstat fragt die gespeicherten Werte ab. Datenlücken, ausgeschalteter Sammler und Interfacewechsel begrenzen die Aussage. Tages-/Monatsmengen und Raten sind verschiedene Größen. Virtuelle und physische Interfaces dürfen nicht unkritisch addiert werden. Neuere CLI-Funktionen und Datenbankformate sind versionsabhängig; die Webfassung ist kein Nachweis der lokalen Installation.

Quelle, am 2026-11-13 gelesen: [vnStat-Projekt: vnstat-Handbuch](https://humdi.net/vnstat/man/vnstat.html)

## 3. Syntax

```text
vnstat [OPTIONEN] [-i INTERFACE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-d`, `-m`, `-h` | Tages-, Monats-, Stundenberichte; -h bedeutet hier nicht Hilfe. |
| `--help`, `--longhelp` | Kurze/vollständige Optionenliste. |
| `--db DATEI`, `--dbdir ORDNER` | Alternative Datenbank beziehungsweise Ordner wählen; lokale Unterstützung prüfen. |
| `--json` | Strukturierte Daten; jsonversion und Byteeinheiten beachten. |
| `--live` | Aktuelle Zähler beobachten, keine reine Datenbankabfrage. |
| `--add`, `--remove` | Überwachungseinträge verändern; remove verliert Daten. |
| `--merge` | Daten in Zielbestand zusammenführen; schreibend und nicht einfach rückgängig zu machen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
vnstat --db EIGENE-DATENBANK -i LERNINTERFACE --days 7
```

Das Muster würde sieben gespeicherte Tageswerte der ausdrücklich gewählten eigenen Datenbank lesen. Es setzt eine passende vorher erzeugte Datenbank voraus, die hier mangels Programm nicht angelegt wurde. Leere Zeiträume sind keine gemessenen Nullmengen; Sammlerstand und Abdeckung müssten zusätzlich bekannt sein.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Verbrauch auswerten: Zeitabdeckung und Interfaceidentität festhalten. Berichte automatisieren: API-Version und Einheiten der JSON-Ausgabe prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Add/Remove/Merge sind reale Verwaltungsaktionen. Datenbanken können sensible Nutzungszeiten offenlegen. Kein Liveinterface lesen und keinen Sammler starten, um fehlende Übungsdaten zu erzeugen. Datenbankschema und Konfiguration nicht blind aus anderen Versionen übernehmen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Interface fehlt in DB | Existenz im Betriebssystem und Datenbankeintrag unterscheiden. |
| Werte veraltet | Sammlung und Speicherintervall prüfen. |
| Stundenhilfe statt Hilfe erwartet | -h ist Stundenansicht, --help ist Hilfe. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; vnstat fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `vnstatd` | Sammelt und persistiert Zähler. |
| `nload` | Momentane Anzeige. |
| `bmon` | Modulare Zählersicht. |

Ausgangsdatensatz 418 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
