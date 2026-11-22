---
id: "upower"
name: "upower"
command: "upower"
category: "Hardware"
language: "de"
root_required: false
risk_level: "safe"
tags: ["upower", "hardware"]
status: "Nur Hilfe ausgeführt; keine echten Energieobjekte abgefragt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 395
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Manpage und upower --help mit Status 0 gelesen"
---

# upower – Energiegeräte über den Systemdienst lesend betrachten

## 1. Kurzbeschreibung

`upower` ist ein Kommandozeilenclient für den UPower-Dienst. Es kann Energiegeräte aufzählen, Details lesen und Änderungen beobachten. **Für übliche freigegebene Zustandsabfragen sind keine Root-Rechte nötig.**

## 2. Was macht der Befehl?

Die lokale Manpage ist knapp und teilweise unvollständig. Deshalb wurde zusätzlich `upower --help` tatsächlich ausgeführt. Die Hilfe nennt Objektauflistung, Detailanzeige und Beobachtung.

Geräte werden über Objektpfade des Dienstes angesprochen. Ein solcher Pfad ist kein Dateipfad zu einer vom Benutzer zu öffnenden JSON-Datei. Quelle, Gerätetyp und Aktualität bestimmen die Aussage der Daten.

## 3. Syntax

```text
upower --help
upower --enumerate
upower --show-info OBJEKTPFAD
```

`OBJEKTPFAD` muss aus der bekannten passenden Dienstansicht stammen. Nicht automatisch den ersten Eintrag als Laptopakku behandeln; andere Energiegeräte können ebenfalls vorhanden sein.

## 4. Wichtige Optionen

| Option | Aufgabe | Grenze |
| --- | --- | --- |
| `--enumerate` | Geräteobjekte auflisten. | Keine vollständige Detailansicht. |
| `--show-info` | Gewähltes Objekt genauer betrachten. | Richtige Objektidentität nötig. |
| `--dump` | Details aller Objekte ausgeben. | Größerer Datenumfang. |
| `--monitor` | Änderungen fortlaufend melden. | Kein automatisch begrenzter Einmalaufruf. |
| `--monitor-detail` | Änderungen mit Details zeigen. | Kann längere Ausgaben erzeugen. |
| `--help` | Bedienung anzeigen. | Der hier tatsächlich ausgeführte Aufruf. |

Die lokale Versionsoption nennt laut Hilfe Client und Dienst. Sie wird deshalb nicht mit einer garantiert kontaktfreien reinen Datei-Versionsabfrage gleichgesetzt.

## 5. Beispiel erklärt Schritt für Schritt

Zuerst wäre `upower --enumerate` eine geplante Auswahlhilfe. Danach das tatsächlich gemeinte eigene Energiegerät bestimmen und dessen Objektpfad ausdrücklich an `--show-info` übergeben.

Diese Zustandsabfragen wurden nicht durchgeführt. Es wurden keine realen Akkuladungen oder Gerätekennungen erhoben. Erfolgreich geprüft wurde nur die Hilfeausgabe mit Status `0`.

Eine später gelesene Restzeit ist eine Prognose. Sie hängt von Zustand und Verbrauch ab und ist kein garantierter Abschaltzeitpunkt.

## 6. Typische Anwendungsfälle

- Ein bestimmtes Energiegerät der Desktopumgebung zuordnen.
- Akkuinformationen für eine eigene Diagnose lesen.
- Ladezustandsänderungen unter begrenztem Beobachtungsauftrag verfolgen.
- Dienstobjekte von gewöhnlichen Dateipfaden unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der beschriebene Zugriff liest Dienstinformationen. Ausführliche Berichte können trotzdem eindeutige Gerätedetails enthalten. Vor Weitergabe prüfen, welche Felder wirklich nötig sind.

Ein nicht erreichbarer Dienst bedeutet nicht automatisch, dass ein Akku defekt ist. Umgebung und Dienstzugriff zuerst klären. Keine Energie- oder Dienstkonfiguration zur Herstellung einer Anzeige ungefragt ändern.

## 8. Häufige Fehler

- **Erstes Objekt immer Hauptakku:** Gerätetyp prüfen.
- **Objektpfad als Datei lesen:** Andere Schnittstelle.
- **Restzeit als feste Zusage:** Schätzung bleibt veränderlich.
- **Monitor läuft weiter:** Fortlaufende Beobachtung bewusst beenden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Hilfe und klarer Einzelgerätefrage beginnen. Breiten Dump nur wählen, wenn dessen Umfang gebraucht wird.

Bei fehlenden Feldern Quelle und Unterstützung als Prüfpunkt festhalten. Eine unvollständige Anzeige ist kein Auftrag zum Laden neuer Treiber.

## 10. Verwandte Befehle

- `acpi`: Andere Energie-/Temperaturansicht.
- `sensors`: Hardwaremonitoringwerte.
- `inxi -B`: Zusammengefasste Akkuinformationen.
- `systemctl`: Dienstzustand mit lesenden und verändernden Formen.

**Prüfstand:** Hilfe lokal erfolgreich gelesen. Keine Energieobjektinventur, Beobachtung oder Systemänderung durchgeführt.

Ausgangsdatensatz 395 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
