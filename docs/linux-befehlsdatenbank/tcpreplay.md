---
id: "tcpreplay"
name: "tcpreplay"
command: "tcpreplay"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: true
risk_level: "danger"
tags: ["NetMon Spezial / Diagnoseideen", "tcpreplay"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 417
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; tcpreplay fehlt"
---

# tcpreplay – PCAP-Pakete kontrolliert erneut senden

## 1. Kurzbeschreibung

Tcpreplay sendet gespeicherte Capturepakete über eine ausgewählte Schnittstelle erneut. Eine PCAP ist dabei Eingabe eines aktiven Senders, keine harmlose Dokumentdatei. Raw-Injektion benötigt normalerweise besondere Rechte.

## 2. Was macht der Befehl?

Das Wiederholen von Frames stellt nicht automatisch eine neue gültige TCP-Sitzung her. Adressen, Sequenznummern, MAC-Ziele und Zeitbezüge stammen aus der Aufnahme und können im aktuellen Netz falsch sein. Ein erfolgreicher lokaler Sendebericht bestätigt keine Annahme durch Gegenstelle oder Anwendung. Aktuelle Projektfunktionen gehen über ältere Distributionspakete hinaus; Ausgabe- und Backendoptionen daher lokal prüfen.

Quelle, am 2026-11-13 gelesen: [Tcpreplay-Projekthandbuch](https://tcpreplay.appneta.com/reference/man/tcpreplay/)

## 3. Syntax

```text
 tcpreplay [OPTIONEN] PCAP-DATEI...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i NAME` | Primäres Sendeinterface ausdrücklich wählen. |
| `-I NAME` | Zweites Interface für passend aufgeteilten Verkehr. |
| `--pps RATE` | Pakete pro Sekunde statt ursprünglicher Zeitabstände. |
| `--mbps RATE` | Bitratenbegrenzung; nicht mit beliebigen anderen Geschwindigkeitsmodi kombinierbar. |
| `--loop ANZAHL` | Wiederholungen; Null kann Endlosschleife bedeuten, nicht null Sendungen. |
| `--limit ANZAHL` | Gesamtpaketgrenze. |
| `--duration SEKUNDEN` | Sendedauer begrenzen, versionsabhängig. |
| `--topspeed` | Maximal schnell senden; für die Übung ausgeschlossen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur Plan: eigene PCAP, isolierter autorisierter Testpfad, eine Wiederholung und feste Paketgrenze.
```

Im Plan sind Captureinhalt und Zielhardware vor einer Freigabe einzeln zu prüfen. Selbst eine eigene Aufnahme kann Adressen eines früheren Netzes enthalten. Hier wurde kein Interface geöffnet und kein Paket wiederholt; der Plan ist kein fertiger Geräteauftrag. Ein niedriges Tempo macht eine falsche Zielauswahl nicht richtig.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Laborwiedergabe verstehen: Paketwiederholung und zustandsabhängige Protokollinteraktion trennen. Messplanung: Anzahl, Rate und Capturezeitbasis dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Wiederholter Verkehr kann reale Aktionen, Fehlalarme oder hohe Last auslösen. Keine echten Benutzer-PCAPs, produktiven Interfaces, Dauerschleifen oder Topspeed-Modi verwenden. Keine MAC-/IP-/Firewalländerungen als Reparaturversuch. Eine Dateioption ist kein Beweis für Offlinebetrieb.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Pakete gesendet, keine Sitzung | Replay ist keine vollständige TCP-Neuverhandlung. |
| Falsches Linkformat | Capture-Linktyp und Sendeinterface passen nicht. |
| Anzahl unerwartet hoch | Loop, mehrere Dateien und Paketgrenze prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; tcpreplay fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `tcpflow` | Rekonstruiert Inhalte ohne erneutes Senden. |
| `tcprewrite` | Ändert Capturepakete; eigener schreibender Auftrag. |
| `tcpdump` | Erfasst beziehungsweise liest Pakete. |

Ausgangsdatensatz 417 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
