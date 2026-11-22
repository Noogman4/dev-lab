---
id: "iperf"
name: "iperf"
command: "iperf"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "iperf"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 407
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; iperf fehlt"
---

# iperf – Durchsatz mit iperf 2 planen und interpretieren

## 1. Kurzbeschreibung

Der Programmname iperf bezeichnet hier iperf 2. Client und Server erzeugen beziehungsweise empfangen echte Testlast. Normale Tests an unprivilegierten Ports benötigen meist kein Root. iperf 2 und iperf3 sprechen unterschiedliche Protokolle.

## 2. Was macht der Befehl?

Gemessen werden Daten am Socketniveau zwischen zwei Endpunkten, nicht automatisch die Geschwindigkeit eines Internetanschlusses. TCP wird durch Pfad, Hostleistung und Staukontrolle beeinflusst. UDP misst bei vorgegebener Senderate unter anderem Verlust und Jitter; eine hohe vorgegebene Rate beweist keine ebenso hohe Empfangskapazität. Eine gesonderte Zustimmung beider Testendpunkte wäre vor echter Nutzung nötig.

Quelle, am 2026-11-13 gelesen: [iperf-2-Projekthandbuch](https://manpages.debian.org/trixie/iperf/iperf.1.en.html)

## 3. Syntax

```text
iperf -s [OPTIONEN]
iperf -c SERVER [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-s`, `-c SERVER` | Empfängerrolle beziehungsweise Client wählen. |
| `-p PORT` | Port festlegen; iperf-2-Standard gewöhnlich 5001. |
| `-u` | UDP statt TCP; Server-/Clientmodus passend wählen. |
| `-b RATE` | Zielrate setzen; Unterstützung für TCP ist versionsabhängig. |
| `-t SEKUNDEN` | Testdauer begrenzen, auf Rolle/Version achten. |
| `-i SEKUNDEN` | Berichtsintervall, nicht dasselbe wie Paketabstand. |
| `-P ANZAHL` | Parallele Ströme erzeugen; erhöht Last. |
| `-f m` | Ausgabe in Mbit/s; Groß-/Kleinschreibung der Einheiten beachten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
iperf -c SERVER -p 5001 -t 5 -i 1 -f m
```

Das Muster setzt einen vorher separat freigegebenen iperf-2-Server voraus. Es würde fünf Sekunden TCP-Verkehr erzeugen. Eine Ergebnisrate wäre als Test dieses Pfads mit diesen Hosts zu lesen. Ein iperf3-Server am selben Port wäre kein kompatibler Ersatz. Hier wurde weder Client noch Server gestartet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Messplanung: Endpunkte, Protokoll, Richtung und Dauer dokumentieren. Ergebnisse vergleichen: Gleiche Versionen und Einheiten verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Tests beanspruchen reale Bandbreite und können andere Verbindungen stören. Server öffnen Listener; Hintergrund-/Dauermodi nicht unbemerkt aktivieren. UDP ohne passende Begrenzung kann viel mehr senden als der Pfad aufnehmen kann. Keine Firewalländerung für diese Übung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Connection refused | Kein passender Server oder falscher Port. |
| Protokollfehler | iperf 2 und 3 verwechselt. |
| Unterschiedliche Ergebnisse | Richtung, Parallelität, CPU und Empfangs-/Senderbericht vergleichen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; iperf fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `iperf3` | Eigenständige inkompatible Messwerkzeugfamilie. |
| `ping` | Echolatenz, kein Durchsatztest. |
| `bmon` | Beobachtet vorhandene Interfacezähler. |

Ausgangsdatensatz 407 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
