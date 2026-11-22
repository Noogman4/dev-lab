---
id: "lscpu"
name: "lscpu"
command: "lscpu"
category: "Hardware"
language: "de"
root_required: false
risk_level: "safe"
tags: ["lscpu", "hardware"]
status: "Keine echte CPU-Inventur oder Leistungsprüfung"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 386
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale util-linux-Manpage gelesen"
---

# lscpu – logische CPUs, Kerne und Virtualisierung unterscheiden

## 1. Kurzbeschreibung

`lscpu` zeigt CPU-Architektur und Topologieinformationen. **Root-Rechte sind für die gewöhnliche Ansicht nicht nötig.** Es ist kein Benchmark und verändert weder Takt noch Kernaktivierung.

## 2. Was macht der Befehl?

Die lokale Manpage nennt Quellen wie sysfs und `/proc/cpuinfo`. Zu unterscheiden sind logische CPUs, Kerne, Sockel und gegebenenfalls NUMA-Knoten.

In einer virtuellen Umgebung beschreibt die sichtbare Topologie häufig die Gastkonfiguration. Sie ist nicht automatisch die physische Gesamtausstattung des Hosts. Auch die sichtbare CPU-Zahl sagt nicht allein, wie viel Rechenzeit dem Prozess tatsächlich zusteht.

## 3. Syntax

```bash
lscpu
lscpu --extended=CPU,ONLINE
```

Die zweite Form verlangt ausdrücklich passende Spalten. Unterstützung und Bedeutung der verfügbaren Spalten der lokalen Fassung entnehmen.

## 4. Wichtige Optionen

| Option | Aufgabe | Grenze |
| --- | --- | --- |
| `--extended=LISTE` | Ausgewählte Tabellenansicht. | Spaltenliste ohne zusätzliche Leerzeichen. |
| `--parse=LISTE` | Verarbeitungsgünstige Darstellung. | Gewünschte Spalten ausdrücklich wählen. |
| `--json` | JSON-Ausgabe. | Schema und Version berücksichtigen. |
| `--online` | Online-CPUs bei passender Tabellenform. | Nicht allgemeine Hostverfügbarkeit. |
| `--offline` | Offline-CPUs bei passender Tabellenform. | Keine Aktivierung. |
| `--caches` | Cacheinformationen. | Geteilte Caches nicht mehrfach falsch zählen. |
| `--help` | Lokale Funktionen und Spalten lesen. | Kein Lasttest. |

## 5. Beispiel erklärt Schritt für Schritt

Geplant sei `lscpu --extended=CPU,ONLINE`. Ein späterer Bericht würde Kennungen und den gemeldeten Onlinezustand zeigen. Er würde keine CPU ein- oder ausschalten.

Die Ausgabe wurde hier nicht erhoben. Eine fiktive Liste mit vier Zeilen wäre keine Aussage über vier physische Sockel: Es könnten vier logische CPUs mit anderer Kern-/Sockelaufteilung sein.

Für eine Leistungsfrage zusätzlich Arbeitslast, Zuteilung und Zeitverhalten betrachten. Eine Topologieliste allein beantwortet sie nicht.

## 6. Typische Anwendungsfälle

- Architektur und CPU-Aufteilung für einen Fehlerbericht erklären.
- Logische und physische Einheiten unterscheiden.
- Eine ausdrücklich gewählte maschinenlesbare Ansicht vorbereiten.
- Virtualisierungsgrenzen der Systemanzeige verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Abfrage ist lesend. Ihre Interpretation kann dennoch falsche Kapazitätsannahmen erzeugen, besonders in Containern oder virtuellen Maschinen.

Standardausgaben und Spalten können sich zwischen Versionen ändern. Skripte sollten nicht nach zufälligen menschenlesbaren Zeilenpositionen auswerten.

## 8. Häufige Fehler

- **CPU-Zeilen gleich physische Kerne:** Topologie unterscheiden.
- **Gast gleich Host:** Sichtbarkeitsgrenze beachten.
- **Modellname gleich gemessene Leistung:** Kein Benchmark.
- **Cachegrößen blind addieren:** Geteilte Nutzung berücksichtigen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit der Übersicht und danach wenigen benötigten Spalten arbeiten. Für Skripte Format und Spalten ausdrücklich festlegen.

CPU-Aktivierung oder Taktverwaltung sind eigene Änderungen und nicht aus einem ungewohnten Bericht abzuleiten.

## 10. Verwandte Befehle

- `uname -m`: Kurze Architekturangabe.
- `lshw`: Hardwarezusammenfassung.
- `top`: Prozesslast statt Topologie.
- `chcpu`: CPU-Verwaltung; verändernde Funktion.

**Prüfstand:** Lokale Manpage gelesen. Keine echte Topologieliste veröffentlicht und keine CPU-Einstellung verändert.

Ausgangsdatensatz 386 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
