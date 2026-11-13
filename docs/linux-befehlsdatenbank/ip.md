---
id: "ip"
name: "ip"
command: "ip"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "ip"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 429
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# ip – Netzwerkobjekt und Operation ausdrücklich wählen

## 1. Kurzbeschreibung

ip aus iproute2 ist eine gemeinsame Oberfläche für Links, Adressen, Routen und weitere Netzwerkobjekte. Sein Risiko hängt vom Unterbefehl ab: show liest, add/delete/set/flush können das System verändern.

## 2. Was macht der Befehl?

Ein Link kann aktiv sein, ohne passende Adresse oder Route zu besitzen. Adressen gehören zu Interfaces; Routing entscheidet anhand von Tabellen und Regeln über den nächsten Hop. Der aktuelle Netzwerk-Namensraum begrenzt alle Anzeigen. Für Skripte sind vollständige Objekt-/Kommandonamen und strukturierte Felder belastbarer als kontextabhängige Abkürzungen.

Quelle, am 2026-11-13 gelesen: [iproute2: ip-Handbuch](https://man7.org/linux/man-pages/man8/ip.8.html)

## 3. Syntax

```text
ip [OPTIONEN] OBJEKT { KOMMANDO | help }
ip -batch DATEI
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `link show`, `address show`, `route show` | Getrennte lesende Objektansichten. |
| `-4`, `-6` | IP-Familie gezielt auswählen. |
| `-brief` | Verdichtete Darstellung. |
| `-json`, `-pretty` | Strukturierte Ausgabe und Einrückung. |
| `-statistics`, `-details` | Zusätzliche Zähler beziehungsweise Eigenschaften. |
| `-resolve` | Namensauflösung kann Netzverkehr auslösen. |
| `-netns NAME` | Anderen Netzwerk-Namensraum verwenden; Rechte beachten. |
| `-batch`, `-force` | Befehlsdatei ausführen und optional trotz Fehlern fortfahren; kein Rollback. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ip -json -4 address show dev eth-lernen
```

Das Muster würde IPv4-Adressobjekte des erfundenen Links anzeigen. Es verändert keine Adresse. Die JSON-Liste muss nach Feldern ausgewertet werden; feste Zeilenpositionen sind kein stabiles Datenmodell. Auch eine vorhandene Adresse belegt keine erreichbare Gegenstelle.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Bestand ordnen:** Link-, Adress- und Routingebene getrennt prüfen. **Automatisierung vorbereiten:** JSON verwenden und den tatsächlichen Rückgabestatus kontrollieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

flush kann viele Objekte entfernen. Batchdateien sind ausführbare Verwaltungsaufträge; -force macht sie nicht atomar. Änderungen benötigen meist CAP_NET_ADMIN und können die eigene Verbindung beenden. Keine realen Links, Adressen, Routen oder Namensräume wurden für diese Dokumentation angefasst.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Falsche Familie | IPv4 und IPv6 explizit unterscheiden. |
| Leere Liste | Filter und Namensraum klären; nicht automatisch konfigurieren. |
| Teilweise ausgeführter Batch | Fehlerfortsetzung ist keine Transaktion; Zustand kann bereits verändert sein. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `bridge` | Bridge-spezifische Objekte. |
| `ss` | Socketzustand. |
| `networkctl` | Sicht des zuständigen Netzwerkdienstes. |

Ausgangsdatensatz 429 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
