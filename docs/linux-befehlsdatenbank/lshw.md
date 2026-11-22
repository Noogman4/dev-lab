---
id: "lshw"
name: "lshw"
command: "lshw"
category: "Hardware"
language: "de"
root_required: true
risk_level: "caution"
tags: ["lshw", "hardware"]
status: "Keine Hardwareprobe oder Berichtserstellung ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 387
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale lshw-Manpage gelesen"
---

# lshw – Hardwareklassen gezielt und mit gefilterter Ausgabe betrachten

## 1. Kurzbeschreibung

`lshw` erstellt einen Hardwarebaum aus mehreren Systemquellen. **Für eine vollständige Erfassung werden häufig administrative Rechte benötigt; nicht privilegierte Ansichten können unvollständig sein.** Hilfe und verfügbare Grundinformationen benötigen nicht pauschal Root.

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt Hardwareklassen, Ausgabeformate und Erkennungswege. Ein erkannter Eintrag ist nicht automatisch ein Nachweis der tatsächlichen Funktion unter jeder Anwendung.

Für eine kleine Frage nicht den gesamten Baum erzeugen. Klasse und Darstellung lassen sich begrenzen. Datenschutzfilter entfernen bestimmte empfindliche Angaben, ersetzen aber nicht die Sichtprüfung vor einer Weitergabe.

## 3. Syntax

```text
lshw -help
lshw -short -sanitize
lshw -class network -sanitize
```

Die dokumentierte Schreibweise verwendet einfache Bindestriche auch bei längeren Optionsnamen. Kein universelles GNU-Schema daraus ableiten.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-short` | Kompakte Hardwarepfade. | Keine vollständigen Details. |
| `-class KLASSE` | Klasse auswählen. | Ausgabegrenze ist kein universeller Verzicht auf jede andere Ermittlung. |
| `-sanitize` | Bestimmte sensible Daten entfernen. | Ergebnis zusätzlich prüfen. |
| `-businfo` | Busbezogene Liste. | Nicht dieselbe Darstellung wie Dateipfade. |
| `-json`, `-xml` | Strukturierte Ausgabe. | Passenden Parser verwenden. |
| `-dump DATEI` | SQLite-Ausgabe speichern. | Zusätzlicher Schreibvorgang. |
| `-help` | Bedienung anzeigen. | Keine breite Erfassung erforderlich. |

## 5. Beispiel erklärt Schritt für Schritt

Für einen fiktiven Netzwerkgeräte-Supportfall wäre `lshw -class network -sanitize` ein eingegrenzter Plan. Die Klasse betrifft Hardwareangaben, nicht den Beweis einer funktionierenden Internetverbindung.

Der Aufruf wurde nicht gestartet. Weder MAC-Adressen noch Seriennummern oder echte Treiberzuordnungen wurden erhoben.

Eine spätere Ausgabe trotz Filter vor Weitergabe lesen. Fehlende Felder können durch Rechte oder Erkennungsgrenzen entstehen und sind kein automatischer Hardwaredefekt.

## 6. Typische Anwendungsfälle

- Eine bekannte Hardwareklasse für einen Supportbericht betrachten.
- Hardwarepfade und Buszuordnung nachvollziehen.
- Strukturierte Daten für eine kontrollierte lokale Auswertung vorbereiten.
- Erkanntes Gerät und tatsächliche Anwendungsfunktion trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Breite Hardwareerkennung kann verschiedene Geräteschnittstellen ansprechen. Zusätzliche Tests nicht unbesehen aktivieren. Fehlende Details rechtfertigen keine pauschale Rechteausweitung.

Berichte und Datenbankausgaben können vertraulich sein. Ein Filter ist keine Garantie gegen jede Identifikation. Auch das Ausgabeziel muss vor Überschreiben wichtiger Dateien geschützt werden.

## 8. Häufige Fehler

- **Filter gleich vollständige Anonymität:** Manuelle Kontrolle bleibt nötig.
- **Klasse gleich Internettest:** Unterschiedliche Frage.
- **Unprivilegierte Lücke gleich Defekt:** Rechte berücksichtigen.
- **`-dump` als Bildschirmausgabe:** Schreibt eine Datenbank.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe, begrenzter Klasse und Filter beginnen. Nur den benötigten Ausschnitt eines tatsächlichen Berichts weitergeben.

Für eine einzelne Busübersicht können `lspci` oder `lsusb` leichter verständlich sein. Ein umfangreicher Bericht ist nicht automatisch die bessere Diagnose.

## 10. Verwandte Befehle

- `lspci`, `lsusb`: Busbezogene Übersichten.
- `dmidecode`: Firmwaretabellen.
- `lscpu`: CPU-Topologie.
- `inxi`: Zusammenfassung mit anderer Oberfläche.

**Prüfstand:** Lokale Manpage gelesen. Kein Hardwaretest, SQLite-Dump oder privilegierter Gerätezugriff ausgeführt.

Ausgangsdatensatz 387 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
