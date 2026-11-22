---
id: "uname"
name: "uname"
command: "uname"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["uname", "grundlagen & hilfe"]
status: "Keine vollständige Hostkennung erhoben"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 372
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4 gelesen"
---

# uname – Kernel- und Architekturangaben gezielt anzeigen

## 1. Kurzbeschreibung

`uname` zeigt ausgewählte Systeminformationen wie Kernelname, Kernelrelease oder Maschinenarchitektur. **Root-Rechte sind nicht nötig.** Es aktualisiert weder Kernel noch Betriebssystem.

## 2. Was macht der Befehl?

Die lokale GNU-Manpage beschreibt mehrere getrennte Felder. Ohne Option wird der Kernelname angezeigt. Ein Kernelrelease ist nicht dieselbe Angabe wie die Version einer Linux-Distribution.

In Containern und anderen isolierten Umgebungen können Kernel- und Benutzerlandinformationen unterschiedliche Bezüge haben. Eine Ausgabe darf deshalb nicht pauschal als vollständige Beschreibung des gesamten Systems gelten.

## 3. Syntax

```bash
uname -s
uname -r
uname -m
```

Mit einer einzelnen Auswahl bleibt die Ausgabe auf die benötigte Frage begrenzt. Eine komplette lokale Hostausgabe wurde für diesen Eintrag nicht erhoben.

## 4. Wichtige Optionen

| Option | Inhalt | Abgrenzung |
| --- | --- | --- |
| `-s` | Kernelname. | Nicht vollständiger Distributionsname. |
| `-r` | Kernelrelease. | Kein alleiniger Sicherheitsnachweis. |
| `-v` | Kernelversions-/Buildangabe. | Kann längere lokale Details enthalten. |
| `-m` | Maschinenarchitektur. | Nicht automatisch jede Paketarchitektur. |
| `-n` | Knotenname. | Kann persönlichen Hostnamen offenlegen. |
| `-a` | Mehrere Felder zusammen. | Breitere Datenweitergabe. |
| `--version` | Version des GNU-Werkzeugs. | Andere Version als Kernelrelease. |

## 5. Beispiel erklärt Schritt für Schritt

Für die Frage nach der gemeldeten Maschinenarchitektur wäre `uname -m` passend. Ein fiktiver Wert `x86_64` beschreibt die Ausgabeart, nicht einen hier neu gemessenen Hostbefund.

Vor dem Auswählen eines Pakets zusätzlich dessen tatsächliche Plattform- und Distributionsanforderungen lesen. Gleiche Maschinenarchitektur allein garantiert nicht, dass ein Paket oder Binärprogramm passt.

Auch eine Kernelversionsnummer allein beantwortet nicht jede Frage nach Sicherheitsupdates. Distributionen können Korrekturen in ihre eigene Paketlinie übernehmen.

## 6. Typische Anwendungsfälle

- Kernelrelease für einen gezielten Fehlerbericht notieren.
- Architektur bei der Vorbereitung eines passenden Builds berücksichtigen.
- Kernelname und Distributionsangaben auseinanderhalten.
- Eine bewusst kleine Systemangabe weitergeben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Anzeige ist lesend. Breite Ausgaben können Namen und Builddetails offenlegen, die für eine Anfrage nicht nötig sind.

Aus einer bekannten Nummer keine konkrete Verwundbarkeit ohne Paket- und Distributionskontext behaupten. Ebenso bedeutet eine neue Nummer nicht automatisch vollständige Sicherheit.

## 8. Häufige Fehler

- **Kernel gleich Distribution:** Unterschiedliche Ebenen.
- **`--version` gleich Kernel:** Beschreibt das Werkzeug.
- **Architektur als Paketfreigabe:** Weitere Anforderungen fehlen.
- **Containeransicht als kompletter Host:** Ausführungskontext beachten.

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur das benötigte Feld wählen. Für Distributionsinformationen gegebenenfalls die passende lokale Betriebssystembeschreibung hinzunehmen.

Einen Kernelwechsel nicht aufgrund einer ungewohnten Ausgabe starten. Erst klären, welcher Zustand beabsichtigt ist und wie die Distribution ihn verwaltet.

## 10. Verwandte Befehle

- `hostname`: Knotenname und Namenskontext.
- `lscpu`: CPU-Topologie und weitere Angaben.
- `arch`: Architekturbezogene Kurzangabe.
- Paketverwaltung: Installierten Kernelpaketstand lesen.

**Prüfstand:** Lokale Manpage gelesen. Keine Kerneländerung und keine vollständige Hostinventur.

Ausgangsdatensatz 372 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
