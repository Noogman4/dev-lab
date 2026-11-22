---
id: "iperf3"
name: "iperf3"
command: "iperf3"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "iperf3"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 408
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; iperf3 fehlt"
---

# iperf3 – iperf3-Messrichtung und Ergebnisberichte verstehen

## 1. Kurzbeschreibung

iperf3 misst Durchsatz durch selbst erzeugten TCP-, UDP- oder unterstützten SCTP-Verkehr. Ein Test braucht einen passenden iperf3-Server und Client. Es ist kein passiver Geschwindigkeitssensor; normale unprivilegierte Ports benötigen meist kein Root.

## 2. Was macht der Befehl?

Die Kontrollverbindung nutzt TCP, auch wenn Testdaten über UDP laufen. Standardrichtung ist Client zu Server; -R dreht den Datenfluss um. sender und receiver bezeichnen Rollen, nicht immer dieselben Rechner. Unterschiede zwischen Sende- und Empfangsrate sowie UDP-Verlust/Jitter müssen mit Intervall und Richtung gelesen werden. Die Webmanpage weist selbst auf mögliche Unterschiede zur installierten Manpage hin. iperf 2 ist inkompatibel.

Quelle, am 2026-11-13 gelesen: [ESnet: iperf3-Aufrufhandbuch](https://software.es.net/iperf/invoking.html)

## 3. Syntax

```text
iperf3 -s [OPTIONEN]
iperf3 -c SERVER [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-p PORT` | Kontroll-/Serverport wählen; Standard 5201. |
| `-R` | Server sendet Testdaten zum Client. |
| `-u`, `-b RATE` | UDP und gewünschte Senderate; keine Empfangsgarantie. |
| `-t SEKUNDEN`, `-i SEKUNDEN` | Dauer und Berichtsintervall unterscheiden. |
| `-P ANZAHL` | Parallele Datenströme, zusätzliche Last. |
| `-J` | JSON-Bericht, normalerweise erst zum Testende vollständig. |
| `-1` | Server nach einem Client beenden; betrifft Serverrolle. |
| `-F DATEI` | Datei als Quelle/Senke, kein zuverlässiger Dateitransfer. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
iperf3 -c SERVER -p 5201 -t 5 -i 1 -R
```

Das Muster würde den Client fünf Sekunden Daten vom freigegebenen Server empfangen lassen. Der Client bleibt Initiator der Kontrollverbindung. Eine niedrige Rate könnte auch durch Server-CPU oder Empfangspfad entstehen. Weder Listener noch Verbindungen wurden dafür angelegt; alle Ergebnisse bleiben offen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Richtungsabhängige Engpässe untersuchen: Upload-/Downloadrolle getrennt planen. Berichte automatisieren: JSON der konkreten Version prüfen, statt Terminalspalten vorauszusetzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Test kann die Verbindung auslasten und andere Dienste beeinträchtigen. Listener können von anderen Clients genutzt werden. Dateimodus kann eigene Daten überschreiben oder übertragen; keine echten Dateien verwenden. Dauer, Rate, Richtung und autorisierte Gegenstelle sind vor echter Ausführung festzulegen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| UDP scheitert trotz Verbindung | TCP-Kontrolle und UDP-Datenpfad getrennt prüfen. |
| JSON noch leer | Vollständiger Bericht entsteht oft erst am Ende. |
| sender/receiver verwechselt | -R und jeweilige Prozessrolle berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; iperf3 fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `iperf` | Iperf-2-Familie mit anderem Protokoll. |
| `ss` | Socketstatus. |
| `bmon` | Beobachtet Interfacezähler. |

Ausgangsdatensatz 408 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
