---
id: "ping"
name: "ping"
command: "ping"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "ping"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 439
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# ping – ICMP-Antworten mit begrenzter Aussagekraft

## 1. Kurzbeschreibung

ping aus iputils sendet ICMP-Echo-Anfragen und misst Antworten. Es ist ein aktiver Netztest und bestätigt bei Erfolg keine Erreichbarkeit eines bestimmten TCP-/UDP-Dienstes.

## 2. Was macht der Befehl?

Round-Trip-Time umfasst Hin- und Rückweg. Eine fehlende Echoantwort kann durch Filter, Rate-Limits, Paketverlust oder ein nicht erreichbares Ziel entstehen. Die Paketgröße von -s bezeichnet Nutzdaten vor dem ICMP-/IP-Overhead. Rechte hängen von ICMP-Datagramsockets, lokalen Freigaben und Sondermodi ab; pauschal ist weder immer Root noch immer keine Berechtigung korrekt.

Quelle, am 2026-11-13 gelesen: [iputils: ping-Handbuch](https://man7.org/linux/man-pages/man8/ping.8.html) sowie lokale ping-Manpage

## 3. Syntax

```text
ping [-4|-6] [-n] [-c ANZAHL] [-w SEKUNDEN] [-W SEKUNDEN] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-c ANZAHL` | Anzahl Echo-Anfragen begrenzen. |
| `-w SEKUNDEN` | Gesamte Deadline des Laufs. |
| `-W SEKUNDEN` | Antwortwartezeit mit eigener Semantik; kein identischer Ersatz für -w. |
| `-n` | Numerische Ausgabe; Hostnamen als Eingabe benötigen weiterhin Auflösung. |
| `-4`, `-6` | IP-Familie wählen. |
| `-I LINK` | Ausgangsinterface/Quelle je Syntax wählen. |
| `-f` | Flood-Modus; hier weder Beispiel noch Test. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ping -4 -n -c 2 -w 5 192.0.2.1
```

Das Muster ist auf zwei Anfragen und eine Deadline begrenzt. Die Dokumentationsadresse ist kein Testziel. Kein Paket wurde gesendet. Status 0 bedeutet bei dieser Implementierung Erfolg nach ihren Antwortregeln; 1 steht für fehlende beziehungsweise bei count+deadline unvollständige Antworten, 2 für andere Fehler.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Erreichbarkeit eingrenzen:** ICMP neben DNS, Routing und Anwendung betrachten. **Messungen erklären:** Mittelwert und Schwankung nicht als Bandbreite deuten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Wiederholungen und kurze Intervalle erzeugen Last. Keine Broadcast-, Flood- oder großflächigen Proben. Ein erfolgreicher Ping ist kein Integritäts- oder Sicherheitsnachweis des Zielsystems. Keine Rechte oder Netzkonfiguration wurden geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Antwort | Filter und Pfad offen; nicht automatisch Host ausgeschaltet. |
| Name nicht auflösbar | Resolverproblem von ICMP-Zieltest trennen. |
| Port soll geprüft werden | ICMP-Echo prüft keinen Anwendungsport. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ping6` | Historischer IPv6-Aufrufname. |
| `tracepath` | Aktive Pfad-/MTU-Diagnose. |
| `mtr` | Wiederholte Hopmessung. |

Ausgangsdatensatz 439 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
