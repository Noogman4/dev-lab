---
id: "tc"
name: "tc"
command: "tc"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "tc"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 445
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# tc – Queueing-Objekte statt pauschaler Bandbreitenbegrenzung

## 1. Kurzbeschreibung

tc aus iproute2 zeigt und verändert Traffic-Control-Objekte des Linux-Kernels. Lesende show-Formen sind von Änderungen an Queues, Klassen, Filtern und Aktionen zu trennen.

## 2. Was macht der Befehl?

Eine qdisc bestimmt die Warteschlangenbehandlung; klassenfähige qdiscs können Unterklassen enthalten. Filter ordnen Pakete zu oder lösen Aktionen aus. Shaping verzögert den ausgehenden Versand; Policing kann bei Grenzüberschreitung verwerfen und ist kein gleichwertiger Puffer. Ein Zähler beschreibt nur seinen konkreten Anknüpfungspunkt und Zeitraum.

Quelle, am 2026-11-13 gelesen: [iproute2: tc-Handbuch](https://man7.org/linux/man-pages/man8/tc.8.html)

## 3. Syntax

```text
tc [OPTIONEN] {qdisc|class|filter} show dev LINK
tc [OPTIONEN] OBJEKT {add|change|replace|delete} PARAMETER
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `qdisc show` | Warteschlangendisziplinen anzeigen. |
| `class show` | Klassen der ausgewählten Struktur. |
| `filter show` | Klassifikatoren und Aktionen lesen. |
| `-s`, `-d` | Zähler beziehungsweise Details ergänzen. |
| `-j`, `-p` | JSON und lesbare Formatierung. |
| `replace`, `delete` | Bestehende Struktur verändern oder entfernen. |
| `-batch` | Verwaltungsbefehle aus Datei ausführen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
tc -s qdisc show dev eth-lernen
```

Das Muster würde Queues und Zähler des erfundenen Interfaces anzeigen. dropped, overlimits und backlog sind unterschiedliche Größen und nicht pauschal dieselbe Verlustzahl. Keine qdisc wurde gelesen, angelegt oder ersetzt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Verkehrssteuerung verstehen:** Queue, Klasse und Filter unterscheiden. **Planung prüfen:** Richtung, Anknüpfungspunkt, Einheiten und vorhandene Hierarchie festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Änderungen erfordern meist CAP_NET_ADMIN und können Verkehr verzögern, verwerfen oder umleiten. Das Löschen einer Wurzelstruktur kann weitere Konfiguration entfernen. Einheiten wie bit/s, Byte und Zeit nicht austauschen. Kein Netem-, BPF- oder Shaping-Test am Host.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| File exists | Anlage kollidiert mit vorhandener Struktur; nicht automatisch ersetzen. |
| Keine Klassen | Nicht jede qdisc ist klassenfähig. |
| Unerwarteter Zähler | Richtung, Hierarchie und Messintervall prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ip link` | Zugehöriger Link. |
| `ss` | Socketbezogene Daten. |
| `ethtool` | Treiber-/Offload-Ebene. |

Ausgangsdatensatz 445 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
