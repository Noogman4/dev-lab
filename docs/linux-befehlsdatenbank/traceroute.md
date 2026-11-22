---
id: "traceroute"
name: "traceroute"
command: "traceroute"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "traceroute"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 447
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# traceroute – Hopantworten als Messung statt vollständige Topologie

## 1. Kurzbeschreibung

traceroute für Linux sendet Proben mit steigender TTL beziehungsweise Hop-Limit. Es rekonstruiert Antwortpunkte, nicht garantiert alle Router oder den unveränderten Pfad einer Anwendung.

## 2. Was macht der Befehl?

Die Standardmethode verwendet UDP; ICMP und TCP sind gesonderte Methoden mit anderen Rechten und Filterreaktionen. Jede Zeit ist eine Round-Trip-Messung zu einer Probe. Lastverteilung und asymmetrische Rückwege können mehrere Adressen oder schwankende Zeiten erklären. Ein Stern bedeutet fehlende rechtzeitige Antwort, nicht zwingend fehlende Weiterleitung.

Quelle, am 2026-11-13 gelesen: [Traceroute für Linux: Projekthandbuch](https://man7.org/linux/man-pages/man8/traceroute.8.html)

## 3. Syntax

```text
traceroute [OPTIONEN] ZIEL [PAKETLAENGE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-4`, `-6` | Adressfamilie erzwingen. |
| `-n` | Keine symbolische Hopauflösung. |
| `-m HOPS` | Maximale TTL/Hopzahl. |
| `-q ANZAHL` | Proben je Hop, nicht gesamte Paketzahl. |
| `-w SEKUNDEN` | Maximale Antwortwartezeit; weitere adaptive Parameter möglich. |
| `-I`, `-T` | ICMP-Echo beziehungsweise TCP-SYN-Methode. |
| `-p PORT` | UDP-Basisport oder fester TCP-Port, methodenabhängig. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
traceroute -4 -n -m 3 -q 1 -w 1 192.0.2.1
```

Die dokumentarische Zieladresse wird nicht angesprochen. Die Auswahl bedeutet höchstens drei Hopstufen mit jeweils einer Probe bei dieser Standardform. Sie ist keine Freigabe des gesamten Zielpfads. Ein späteres TCP-Ergebnis wäre nicht direkt mit einer UDP-Messung gleichzusetzen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Pfaddiagnose erklären:** Protokoll, Zeitpunkt und Antwortgrenzen dokumentieren. **Fehlerberichte lesen:** Stern, Unreachable-Marker und RTT auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auch geringe Probeanzahl erzeugt echten Verkehr. Protokollwechsel dürfen keine ungefragten Versuche an fremden Systemen sein. Privilegien hängen von Methode und Installation ab. Hier keine Netztests, Quelladressänderungen oder Firewallanpassungen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Sterne am Zwischenhop | Antwortfilterung/Rate-Limit möglich. |
| !X | Kommunikation administrativ untersagt. |
| Andere Route bei Wiederholung | Lastverteilung oder Pfadwechsel; keine feste Topologie behaupten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `tracepath` | UDP-/Path-MTU-Diagnose. |
| `mtr` | Wiederholte Hopstatistik. |
| `ping` | Echo-Test eines Ziels. |

Ausgangsdatensatz 447 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
