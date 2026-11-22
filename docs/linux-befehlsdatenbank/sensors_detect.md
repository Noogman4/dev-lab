---
id: "sensors_detect"
name: "sensors-detect"
command: "sensors-detect"
category: "Hardware"
language: "de"
root_required: true
risk_level: "danger"
tags: ["sensors_detect", "hardware"]
status: "Keinerlei Hardwareprobes oder automatische Antworten ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 394
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale lm-sensors-Manpage gelesen"
---

# sensors-detect – aktive Hardwareerkennung vor einem Einsatz bewusst bewerten

## 1. Kurzbeschreibung

`sensors-detect` sucht interaktiv nach unterstützten Hardwaremonitoringchips. **Die tiefen Hardwarezugriffe benötigen administrative Rechte.** Es ist kein gewöhnlicher gefahrloser Ersatz für das Lesen vorhandener Messwerte.

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt mehrere Erkennungsstufen, darunter Zugriffe auf controllernahe Schnittstellen und I2C-/SMBus-Bereiche. Vor Erkennung ist nicht in jedem Fall bekannt, welcher Chip auf den Zugriff antwortet.

Das Handbuch warnt ausdrücklich vor möglichen Problemen durch ungeeignete Probes, von Busblockaden bis zu seltenen Hardwarefolgen. Diese konkrete Warnung stammt aus der Werkzeugdokumentation, nicht aus einer pauschalen Bewertung aller Sensorabfragen.

## 3. Syntax

```text
sensors-detect
sensors-detect --auto
```

Das sind ausschließlich Syntaxangaben. Keine Form wurde gestartet. Auch der Aufruf ohne Optionen beginnt einen interaktiven Erkennungsablauf.

## 4. Wichtige Optionen

| Form | Wirkung | Entscheidender Punkt |
| --- | --- | --- |
| Ohne Option | Interaktive Erkennung. | Fragen und tatsächliche Probearten verstehen. |
| `--auto` | Vorgesehene Standardantworten übernehmen. | Laut Handbuch keine Sicherheitsgarantie. |

Eine automatisch beantwortete Frage ist nicht automatisch harmlos. Es werden hier keine weiteren unbestätigten „Dry-run“- oder Sicherheitsoptionen erfunden.

## 5. Beispiel erklärt Schritt für Schritt

Eine sichere Dokumentationsübung startet keinen Erkennungslauf. Zuerst die konkrete Frage festlegen: Fehlt ein erwarteter Messwert, oder soll tatsächlich unbekannte Monitoringhardware identifiziert werden?

Für den ersten Fall zunächst vorhandene `sensors`-Ausgabe, Treiberlage und Geräteunterlagen betrachten. Eine fehlende Temperaturanzeige allein ist noch keine Begründung für alle tiefen Probearten.

Soll später eine reale Erkennung nötig sein, müssen betroffene Maschine, Betriebszustand, Herstellervorgaben und möglicher Ausfall geklärt sein. Kein Ausführen der Syntaxzeilen dieses Dokuments voraussetzen.

Hier wurde nur die lokale Manpage gelesen. Es entstanden weder neue Modulvorschläge aus einem Lauf noch geänderte Startkonfigurationen.

## 6. Typische Anwendungsfälle

- Einen begründeten Erkennungsbedarf auf einem geeigneten eigenen Testsystem planen.
- Die Ursache fehlender Monitoringschnittstellen systematisch eingrenzen.
- Aktive Hardwareerkennung von normalem Messwertlesen unterscheiden.
- Risiken automatischer Standardantworten erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Probes können ungeeignete Chips ansprechen und das System oder einen Bus stören. Das Handbuch rät ausdrücklich davon ab, ausgelassene Schritte ohne ausreichendes Wissen zu erzwingen.

Ein fehlender Messwert ist kein Anlass, pauschal `--auto` mit erhöhten Rechten auszuführen. Vorschläge zu Treibern oder dauerhaftem Laden sind außerdem eigene spätere Änderungen.

## 8. Häufige Fehler

- **`--auto` gleich sicher:** Nur Antwortautomatisierung.
- **Gleiches Risiko wie `sensors`:** Andere Zugriffsart.
- **Alle Probes erzwingen:** Übersprungene Stufen können bewusst vermieden sein.
- **Erkennungsergebnis gleich dauerhafte Einrichtung:** Zusätzliche Maßnahmen wären getrennt nötig.

## 9. Sichere Varianten oder Tipps für Einsteiger

Vorhandene Leseschnittstellen und Herstellerdokumentation zuerst nutzen. Wenn kein begründeter Bedarf besteht, keinen Erkennungslauf starten.

Eine dokumentierte Planung mit unbekannten Punkten ist besser als ein nur vermeintlich erfolgreicher Automatismus. Offenbleibende Hardwareunterstützung ausdrücklich als Prüfpunkt festhalten.

## 10. Verwandte Befehle

- `sensors`: Bereitgestellte Messwerte lesen.
- `modinfo`: Treiberinformationen betrachten.
- `lsmod`: Geladene Module anzeigen.
- `acpi`, `upower`: Andere bereits bereitgestellte Informationen.

**Prüfstand:** Ausschließlich lokale Manpage gelesen. Keine Hardwareprobe, automatische Antwort, Moduländerung oder Systemkonfiguration ausgeführt.

Ausgangsdatensatz 394 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
