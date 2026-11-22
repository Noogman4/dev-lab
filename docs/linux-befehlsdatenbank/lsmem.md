---
id: "lsmem"
name: "lsmem"
command: "lsmem"
category: "Hardware"
language: "de"
root_required: false
risk_level: "safe"
tags: ["lsmem", "hardware"]
status: "Keine reale Speicherkarte ausgelesen oder umgeschaltet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 389
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale util-linux-Manpage gelesen"
---

# lsmem – Speicherbereiche statt aktueller Speichernutzung anzeigen

## 1. Kurzbeschreibung

`lsmem` zeigt vom Kernel beschriebene Speicherbereiche und deren Zustand. **Für die gewöhnliche lesbare Übersicht sind keine Root-Rechte nötig.** Es schaltet Speicher nicht selbst online oder offline.

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt Speicherblöcke, zusammengefasste Bereiche und verschiedene Ausgaben. Diese Sicht beantwortet nicht dieselbe Frage wie `free`, das aktuelle Nutzungsinformationen zusammenfasst.

Mehrere Blöcke können zu einem Bereich zusammengefasst werden. Die gewählten Kriterien beeinflussen deshalb Zeilenzahl und bestimmte Bereichsangaben. Eine Zeile entspricht nicht automatisch einem physisch gesteckten RAM-Modul.

## 3. Syntax

```bash
lsmem
lsmem --bytes
lsmem --all
```

Die Auswahl verändert die Darstellung beziehungsweise Gruppierung, nicht den tatsächlichen Speicherzustand.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `--all` | Einzelne Blöcke statt Zusammenfassung. | Mehr Zeilen. |
| `--bytes` | Größen in Bytes. | Einheitenvergleich erleichtert. |
| `--output LISTE` | Spalten ausdrücklich festlegen. | Lokale Spaltenunterstützung prüfen. |
| `--json` | Strukturierte Ausgabe. | Schema und Datentypen beachten. |
| `--split LISTE` | Kriterien der Bereichstrennung wählen. | Zusammenfassung kann Details verdecken. |
| `--summary` | Zusammenfassungsdarstellung wählen. | Nicht aktuelle Prozessnutzung. |
| `--help` | Optionen und Spalten lesen. | Kein Speicherzustandswechsel. |

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter Aufruf `lsmem --bytes` würde Größen ohne verkürzte Einheiten zeigen. Er wurde für dieses Dokument nicht ausgeführt.

Ein fiktiver Bereich mit Zustand `online` bedeutet, dass der Kernel ihn entsprechend beschreibt. Daraus folgt nicht, dass er gerade vollständig von Anwendungen belegt oder für eine einzelne Anwendung frei verfügbar wäre.

Für die physische Modulbelegung wäre eine andere passende Quelle nötig. Für aktuelle Nutzung `free` oder prozessbezogene Werkzeuge betrachten. Die Fragen nicht vermischen.

## 6. Typische Anwendungsfälle

- Kernel-Speicherbereiche für eine konkrete Diagnose beschreiben.
- Online-/Offlinezustände lesend unterscheiden.
- Gruppierungsunterschiede in Berichten erklären.
- Eine ausdrücklich gewählte strukturierte Ansicht vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Ansicht ist lesend. Ein gemeldeter entfernbarer Bereich ist trotzdem keine Freigabe, ein Modul im laufenden Betrieb herauszunehmen. Physische und Kernelverwaltung brauchen passende Hardwareunterstützung und Planung.

Zusammengefasste Angaben können Unterschiede einzelner Blöcke verdecken. Den Bericht entsprechend seinen Auswahlkriterien interpretieren.

## 8. Häufige Fehler

- **Speicherbereich gleich RAM-Riegel:** Andere Einheit.
- **Online gleich aktuell benutzt:** Zustand und Belegung unterscheiden.
- **Zeilenzahl ändert sich, Hardware geändert:** Gruppierung könnte anders sein.
- **Anzeigefeld als Änderungsfreigabe:** Kein sicherer Hotplugplan.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die konkrete Frage wählen. Für Nutzungsprobleme nicht automatisch eine Speicherbereichsverwaltung beginnen.

In Skripten benötigte Spalten ausdrücklich wählen. Einen Bericht mit anderen Gruppierungskriterien nicht ungeprüft zeilenweise vergleichen.

## 10. Verwandte Befehle

- `free`: Aktuelle Speichernutzung.
- `dmidecode`: Firmwareangaben zu Modulen und Ausbau.
- `lshw`: Hardwarezusammenfassung.
- `chmem`: Speicherverwaltung mit verändernden Funktionen.

**Prüfstand:** Lokale Manpage gelesen. Keine realen Speicherbereiche verändert und keine Modul- oder Hotplugaktion ausgeführt.

Ausgangsdatensatz 389 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
