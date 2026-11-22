---
id: "rfkill"
name: "rfkill"
command: "rfkill"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["rfkill", "hardware"]
status: "Keine Funkblockierung abgefragt oder verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 392
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale util-linux-Manpage 2.39.3 gelesen"
---

# rfkill – Funkblockierungen lesen und gezielte Änderungen unterscheiden

## 1. Kurzbeschreibung

`rfkill` zeigt Funkblockierungen und kann softwareseitige Sperren ändern. **Für lesbare Zustandsangaben sind nicht pauschal Root-Rechte nötig; Änderungen verlangen passende Geräteberechtigung beziehungsweise Autorisierung.**

## 2. Was macht der Befehl?

Die lokale Manpage unterscheidet Soft- und Hardwareblockierung. Eine aufgehobene Softsperre beseitigt keine weiterhin bestehende Hardwaresperre.

Ein nicht blockierter Adapter ist außerdem nicht automatisch verbunden. WLAN-Anmeldung, IP-Konfiguration und Bluetoothprofile sind weitere Zustände. Das Werkzeug repariert diese nicht durch bloße Freigabe.

## 3. Syntax

```bash
rfkill
rfkill list
rfkill --output ID,TYPE
```

Die alte `list`-Darstellung wird aus Kompatibilitätsgründen weitergeführt. Für Skripte nach Möglichkeit ausdrücklich gewählte Spalten statt wechselnder Standardansichten nutzen.

## 4. Wichtige Optionen

| Form | Zweck | Folge |
| --- | --- | --- |
| Ohne Unterbefehl | Zustandsübersicht. | Lesende Frage. |
| `--output LISTE` | Spalten festlegen. | Lokale Spaltennamen prüfen. |
| `--json` | JSON-Ausgabe. | Status und Schema beachten. |
| `event` | Änderungen fortlaufend beobachten. | Läuft länger als eine einmalige Abfrage. |
| `block ID/TYP` | Softsperre setzen. | Kann Verbindungen unterbrechen. |
| `unblock ID/TYP` | Softsperre aufheben. | Hardwaresperre kann bleiben. |
| `toggle ID/TYP` | Zustand umschalten. | Unbekannter Ausgangszustand macht Wirkung unklar. |

`all` hat breite Reichweite und ist für eine einzelne Gerätediagnose meist zu ungenau.

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter Aufruf `rfkill --output ID,TYPE` würde zunächst IDs und Typen sichtbar machen. Er wurde hier nicht ausgeführt; keine tatsächliche Funkliste wurde gelesen.

Angenommen, ein fiktiver Adapter wäre soft-unblockiert, aber hard-blockiert. Dann wäre ein wiederholtes `unblock` keine belegte Lösung. Zuerst die tatsächliche Hardware- oder Plattformursache klären.

Für eine spätere autorisierte Änderung die aktuelle Identität erneut zuordnen. Eine alte ID ohne Kontext ist keine sichere Zielwahl.

## 6. Typische Anwendungsfälle

- Fehlende Funkverfügbarkeit von einer reinen Verbindungsstörung unterscheiden.
- Soft- und Hardblocks erklären.
- Einen gewünschten einzelnen Adapter eindeutig benennen.
- Zustandsänderungen unter einem begrenzten Diagnoseauftrag beobachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Blockieren kann WLAN-Fernzugang oder Bluetooth-Eingabegeräte trennen. Freigeben kann zuvor bewusst deaktivierte Funkhardware aktivieren. Beides sind reale Systemaktionen.

Ein pauschales Umschalten ist schlecht nachvollziehbar, wenn der Ausgangszustand unbekannt ist. Stattdessen gewünschte Richtung und Ziel ausdrücklich festlegen.

## 8. Häufige Fehler

- **Unblock gleich verbunden:** Nur eine Sperrebene.
- **Hardblock per Software beseitigen wollen:** Hardwarezustand bleibt möglich.
- **`all` für ein Gerät:** Reichweite zu groß.
- **Eventbeobachtung als Einmalabfrage:** Laufzeit und Beenden berücksichtigen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit lesendem Zustand beginnen. Für Änderungen den einzelnen Adapter und die gewünschte Wirkung vorab beschreiben.

Keine dauerhafte Funk- oder Dienstkonfiguration verändern, nur um eine unklare Anzeige zu normalisieren. Die konkrete Ursache zuerst eingrenzen.

## 10. Verwandte Befehle

- `bluetoothctl`: Bluetoothgeräte und Verbindungen.
- `nmcli`: Netzwerkverbindungen und Funkverwaltung.
- `ip link`: Schnittstellenzustände.
- `systemd-rfkill`: Zustandsverwaltung im Dienstkontext.

**Prüfstand:** Lokale Manpage gelesen. Kein Funkgerät blockiert, freigegeben oder umgeschaltet.

Ausgangsdatensatz 392 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
