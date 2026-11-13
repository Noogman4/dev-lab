---
id: "darkstat"
name: "darkstat"
command: "darkstat"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: true
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "darkstat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 405
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; darkstat fehlt"
---

# darkstat – Paketstatistik sammeln und Webanzeige begrenzen

## 1. Kurzbeschreibung

darkstat zeichnet Netzwerkstatistiken aus Paketen auf und bietet sie über einen HTTP-Dienst an. Ein normaler Start ist damit Mitschnitt und Serverstart. Live-Capture benötigt typischerweise besondere Rechte; diese Rechte dürfen danach nicht unnötig beibehalten werden.

## 2. Was macht der Befehl?

Gezählt wird nur Verkehr, der am Capturepunkt sichtbar ist. Ein gewöhnlicher Host sieht nicht automatisch das gesamte geswitchte LAN. Interfaceauswahl, Capturefilter und Definition des lokalen Netzes bestimmen die Auswertung. -r liest alternativ eine PCAP-Datei; dieser Modus ist nicht mit -i kombinierbar und keine allgemeine Zusicherung gegen sonstige Prozesseffekte.

Quelle, am 2026-11-13 gelesen: [darkstat-Projekthandbuch](https://manpages.debian.org/trixie/darkstat/darkstat.8.en.html)

## 3. Syntax

```text
darkstat -i INTERFACE [OPTIONEN]
darkstat -r PCAP-DATEI [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i NAME` | Live-Capturepunkt auswählen. |
| `-r DATEI` | Vorhandene PCAP statt Liveinterface lesen. |
| `--no-dns` | Rückwärtsnamensauflösung unterlassen. |
| `--no-promisc` | Selbst keinen Promiscuousmodus anfordern; fremde Änderungen dadurch nicht ausschließen. |
| `-b ADRESSE`, `-p PORT` | HTTP-Bindung festlegen; Standard bindet laut Handbuch an alle Interfaces. |
| `--no-daemon` | Im Vordergrund bleiben; trotzdem kein Trockenlauf. |
| `-f FILTER` | Capture mit BPF-Ausdruck eingrenzen. |
| `--import`, `--export` | Statistikdatenbank lesen/schreiben; Pfadbezug zur Chroot beachten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur Plan: Capturepunkt LERNINTERFACE; HTTP ausschließlich Loopback; keine DNS-Auflösung.
```

Der Plan benennt drei getrennte Entscheidungen: Beobachtungspunkt, Zugänglichkeit der Auswertung und zusätzliche Namensanfragen. Keine Liveaufnahme oder Weboberfläche wurde gestartet. Eine Anzeige von null Bytes könnte am ausgewählten Interface liegen und beweist keine Ruhe im ganzen Netz.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Verkehrsbilanzen planen: Sichtbaren Capturebereich und lokale Netzdefinition festhalten. Datenschutz prüfen: Wer kann die Statistikseite erreichen und welche Hosts werden sichtbar?

## 7. Risiken, Nebenwirkungen und Vorsicht

Der HTTP-Dienst kann interne Kommunikationsdaten offenlegen. Mitschnitt, DNS-Auflösung, Datenbankexport und Hintergrundprozesse sind reale Nebenwirkungen. Schutzmechanismen wie Privilegabgabe und Chroot nicht für einen schnellen Test abschalten. Keine bestehende Datenbank oder Dienstinstanz bearbeiten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Paketdaten | Capturepunkt, Rechte und Filter prüfen. |
| Graph leer, Hosttabelle gefüllt | Definition des lokalen Netzes prüfen. |
| Webseite zu weit erreichbar | Bindadresse und Veröffentlichung benötigen eine eigene Konfigurationsprüfung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; darkstat fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `tcpflow` | Rekonstruiert Nutzdaten statt nur Statistik. |
| `vnstat` | Zählerbasierte Langzeitstatistik. |
| `ss` | Zeigt lokale Sockets, keinen allgemeinen Capture. |

Ausgangsdatensatz 405 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
