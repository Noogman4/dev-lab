---
id: "bridge"
name: "bridge"
command: "bridge"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "bridge"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 423
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# bridge – Bridge-Zustand nach Objekt lesen

## 1. Kurzbeschreibung

bridge aus iproute2 verwaltet Linux-Bridges. Lesende Anzeigen und Änderungen am Weiterleitungsverhalten sind unterschiedliche Operationen. Das Werkzeug erstellt nicht durch seinen bloßen Aufruf eine neue Bridge.

## 2. Was macht der Befehl?

Eine Bridge verbindet Ports auf Schicht 2. Ihre FDB ordnet MAC-Adressen Ports zu; die MDB betrifft Multicast-Mitgliedschaften, die VLAN-Tabelle die VLAN-Zulassung. Keine davon ist die IPv4-ARP-Tabelle. Ein gelernter FDB-Eintrag kann altern und beweist weder die Identität noch die aktuelle Erreichbarkeit eines Endgeräts. Ausgaben gelten für den ausgewählten Netzwerk-Namensraum; virtuelle Ports können denselben Verkehr mehrfach sichtbar machen.

Quelle, am 2026-11-13 gelesen: [iproute2: bridge-Handbuch](https://man7.org/linux/man-pages/man8/bridge.8.html)

## 3. Syntax

```text
bridge [OPTIONEN] OBJEKT { KOMMANDO | help }
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `link show` | Port- und Bridge-Eigenschaften anzeigen. |
| `fdb show` | MAC-Weiterleitungseinträge lesen; add/del/flush ändern sie. |
| `vlan show` | VLAN-Zuordnung anzeigen; kein IP-Routingbericht. |
| `mdb show` | Multicast-Einträge anzeigen. |
| `-s`, `-d` | Statistiken beziehungsweise zusätzliche Details. |
| `-j`, `-p` | JSON beziehungsweise dessen lesbare Einrückung. |
| `-batch DATEI` | Befehle ausführen, keine harmlose Importvorschau. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
bridge -j link show master br-lernen
```

br-lernen ist hier ein erfundener Name. show fordert nur Portinformationen der genannten Bridge an; -j ändert das Ausgabeformat. Eine leere Liste kann an fehlenden Ports, falschem Namen oder anderem Namensraum liegen. Sie ist kein Nachweis eines ausgefallenen Netzwerks.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Bestand verstehen:** Bridge-Ports, MAC-Lernen und VLAN-Zulassung getrennt untersuchen. **Konfiguration prüfen:** Anzeigen mit der beabsichtigten Topologie vergleichen, bevor Änderungen geplant werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Änderungen benötigen gewöhnlich CAP_NET_ADMIN. Falsches VLAN-Filtering, STP, Learning oder Hairpin-Verhalten kann Schleifen, Isolation oder Verbindungsabbrüche verursachen. Batchmodus hat keinen allgemeinen Transaktions-Rollback. Hier wurde kein Kernelzustand abgefragt oder geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Objekt verwechselt | FDB, MDB und Nachbarcache beantworten verschiedene Fragen. |
| Bridge fehlt | Name und Namensraum klären; nichts automatisch anlegen. |
| Operation not permitted | Rechte des gewählten Modus prüfen; keine Rechte pauschal erweitern. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip link` | Links einschließlich Bridges anlegen und anzeigen. |
| `ip neigh` | IP-Nachbarauflösung statt MAC-Weiterleitung. |
| `tc` | Verkehrsklassifizierung und Queuing. |

Ausgangsdatensatz 423 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
