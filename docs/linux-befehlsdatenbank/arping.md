---
id: "arping"
name: "arping"
command: "arping"
category: "Netzwerk Grundlagen"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "arping"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 422
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; arping fehlt"
---

# arping – Aktive ARP-Proben im lokalen Netz verstehen

## 1. Kurzbeschreibung

Hier ist arping aus iputils beschrieben. Es sendet IPv4-ARP-Pakete auf einem Link und benötigt CAP_NET_RAW beziehungsweise passende Privilegien. Andere Programme gleichen Namens können andere Optionen besitzen.

## 2. Was macht der Befehl?

ARP arbeitet im lokalen Layer-2-Bereich und ist kein gerouteter Internet-Ping. Antwortende MAC-Adressen sind Beobachtungen, keine sichere Identität. Normale Erreichbarkeitsprobe, Duplicate Address Detection und unaufgeforderte Ankündigungen haben unterschiedliche Semantik. Insbesondere DAD wertet das Ausbleiben einer Antwort als Erfolg; dies darf nicht mit der Statusregel des normalen Modus verwechselt werden.

Quelle, am 2026-11-13 gelesen: [iputils: arping-Handbuch](https://manpages.debian.org/trixie/iputils-arping/arping.8.en.html)

## 3. Syntax

```text
arping [-I INTERFACE] [-c ANZAHL] [-w SEKUNDEN] [OPTIONEN] IPv4-ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-I NAME` | Ausgangsinterface ausdrücklich wählen. |
| `-c ANZAHL` | Anzahl begrenzen; zusammen mit Deadline verändert sich Erfolgsbedingung. |
| `-w SEKUNDEN` | Gesamtablauf zeitlich begrenzen. |
| `-i SEKUNDEN` | Paketabstand festlegen. |
| `-f` | Nach erster bestätigender Antwort beenden. |
| `-D` | Adressduplikatprobe; 0 bedeutet keine Antworten. |
| `-U`, `-A` | Unaufgeforderte Ankündigungen können Nachbarcaches ändern; keine Anzeigeoptionen. |
| `-h`, `-V` | Hilfe oder Version ohne Zielprobe. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
arping -I LERNINTERFACE -c 3 -i 1 IPv4-ZIEL
```

Das Muster würde drei begrenzte ARP-Anfragen auf dem ausgewählten lokalen Link senden. Es wird nicht ausgeführt. Eine Antwort könnte lokale Nachbarerreichbarkeit belegen, nicht DNS, Routing oder Anwendungszugriff. Ein späterer DAD-Test müsste mit seiner eigenen umgekehrten Erfolgsregel ausgewertet werden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Linkdiagnose planen: Lokale Nachbarprobe von geroutetem ICMP unterscheiden. Adresskonflikte verstehen: DAD-Bedingung ausdrücklich dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

ARP-Verkehr kann Nachbarzustand beeinflussen. Ankündigungsmodi nicht als harmlose Tests einsetzen. Keine Setuid-/Capabilityänderungen, keine gefälschten Ankündigungen und keine Tests auf realen Interfaces in dieser Aufgabe.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ziel hinter Router antwortet nicht | ARP wird nicht über Router weitergeleitet. |
| DAD erfolgreich ohne Antwort | Genau die dokumentierte Erfolgsbedingung. |
| Option anders | Implementierung iputils gegenüber anderem arping prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; arping fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `arp` | Cache lesen/verändern statt aktive Probe. |
| `ip neigh` | Nachbarverwaltung. |
| `ping` | ICMP auf IP-Ebene. |

Ausgangsdatensatz 422 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
