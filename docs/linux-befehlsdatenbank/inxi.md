---
id: "inxi"
name: "inxi"
command: "inxi"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["inxi", "hardware"]
status: "Keine tatsächliche Hardware- oder Netzwerkübersicht erhoben"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 385
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale inxi-Manpage gelesen"
---

# inxi – einen begrenzten Supportbericht mit Datenschutzfiltern erstellen

## 1. Kurzbeschreibung

`inxi` fasst System- und Hardwareinformationen aus mehreren Quellen zusammen. **Für viele Übersichten sind keine Root-Rechte nötig; einzelne Details verlangen zusätzliche Zugriffsrechte.** Der Umfang wird durch Optionen gewählt.

## 2. Was macht der Befehl?

Die lokale ausführliche Manpage erklärt Datenklassen und Datenschutzfilter. `inxi` greift dafür auf verschiedene vorhandene Systeminformationen und gegebenenfalls Hilfsprogramme zurück.

Ein Bericht ist keine unabhängige Prüfung aller Geräte. Fehlende Informationen können an Rechten, Werkzeugen oder Plattformunterstützung liegen. Die Zusammenfassung muss mit ihrem Aufrufumfang gelesen werden.

## 3. Syntax

```bash
inxi -b -z
inxi -G -z
```

Die erste Form plant eine Basisübersicht mit Filter, die zweite Grafikangaben mit Filter. Es wurde keine davon für einen tatsächlichen Hostbericht ausgeführt.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-b` | Kurze Basisübersicht. | Mehr als nur ein einzelnes Feld. |
| `-F` | Breite Übersicht. | Nicht automatisch alle Detailklassen. |
| `-G` | Grafikbereich. | Treiberangabe ist kein vollständiger Funktionstest. |
| `-B` | Akkuinformationen. | Nur soweit vorhanden. |
| `-z` | Datenschutzfilter einschalten. | Ausgabe trotzdem manuell prüfen. |
| `-Z` | Filterwirkung aufheben. | Kann private Angaben wieder sichtbar machen. |
| `-c 0` | Farbausgabe abschalten. | Keine Datenanonymisierung. |

Zusätzliche Detailstufen können weitere Informationen offenlegen. Nicht pauschal alles aktivieren, nur weil ein Supportfall besteht.

## 5. Beispiel erklärt Schritt für Schritt

```bash
inxi -b -z
```

Der geplante Aufruf wählt einen begrenzteren Bericht als eine umfassende Detailkombination. `-z` aktiviert beschriebene Filter für bestimmte Identifikationsdaten.

Vor einer Weitergabe den gesamten tatsächlichen Text lesen. Ein Filter kann nur die von ihm erkannten Felder behandeln; Kontext oder andere Angaben können weiterhin persönlich sein.

Hier wurde nur die Manpage gelesen. Es entstand kein tatsächlicher Supportbericht, kein Upload und keine neue Hardwareinventur.

## 6. Typische Anwendungsfälle

- Eine gezielte Systemübersicht für einen freigegebenen Supportfall vorbereiten.
- Grafik-, Akku- oder andere Bereiche einzeln beschreiben.
- Berichtsumfang und Sichtbarkeit bewusst begrenzen.
- Unterschied zwischen Datenquelle und zusammengefasster Anzeige verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Berichte können Gerätekennungen, Namen und Netzwerkdaten enthalten. Auch eine gefilterte Ausgabe ist nicht automatisch vollständig anonym.

Manche Zusatzfunktionen haben eigene Datenquellen oder Netzwerkbezug. Nur die tatsächlich benötigten dokumentierten Optionen wählen. Ein Ausgabewerkzeug ist kein Anlass für automatische Treiber- oder Paketänderungen.

## 8. Häufige Fehler

- **`-z` als vollständige Anonymitätsgarantie:** Ergebnis prüfen.
- **`-Z` mit Filter verwechseln:** Gegenteilige Wirkung.
- **Gerät sichtbar gleich funktionsfähig:** Anwendungstest fehlt.
- **Mehr Details gleich bessere Diagnose:** Unnötige Datenmenge kann stören.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer kleinen gezielten Auswahl und `-z` anfangen. Nur benötigte Teile weitergeben. Fehlende Felder als Grenze dokumentieren, statt sofort mehr Rechte anzufordern.

Für eine einzelne CPU- oder Busfrage kann das zuständige engere Werkzeug leichter nachvollziehbar sein.

## 10. Verwandte Befehle

- `lscpu`: CPU-Daten.
- `lspci`, `lsusb`: Busgeräte.
- `lshw`: Hardwarebaum mit eigenen Filtern.
- `uname`: Begrenzte Kernelangaben.

**Prüfstand:** Lokale Manpage gelesen. Keine persönlichen Hardwaredaten oder Netzwerkkennungen erhoben und nichts übertragen.

Ausgangsdatensatz 385 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
