---
id: "xinput"
name: "xinput"
command: "xinput"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["xinput", "hardware"]
status: "Keine Geräteereignisse aufgenommen oder Eigenschaften verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 396
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale xinput-Manpage 1.6.4 gelesen"
---

# xinput – X11-Eingabegeräte von Wayland-Geräten unterscheiden

## 1. Kurzbeschreibung

`xinput` listet und verwaltet Eingabegeräte eines X-Servers. **Root-Rechte sind bei passendem Zugriff auf die eigene X-Sitzung nicht nötig.** Einige Unterbefehle beobachten Eingaben oder verändern Gerätefunktionen.

## 2. Was macht der Befehl?

Die lokale Manpage erklärt Geräte, Eigenschaften und Ereignisse. Sie enthält einen ausdrücklichen Xwayland-Abschnitt: Dortige Geräte sind Protokollabbildungen und keine direkte globale Hardwareansicht.

Änderungen an Xwayland-Geräten betreffen höchstens passende X-Clients beziehungsweise können wirkungslos bleiben. Sie schalten nicht automatisch die Eingabe für native Wayland-Anwendungen um. Dafür ist der vorgesehene Weg des Compositors relevant.

## 3. Syntax

```text
xinput list
xinput list-props GERÄT
```

Das Gerät muss aus dem aktuellen passenden X-Kontext stammen. Numerische IDs können sich ändern. Keine feste alte Nummer als verlässliche dauerhafte Identität verwenden.

## 4. Wichtige Optionen

| Form | Aufgabe | Grenze |
| --- | --- | --- |
| `list --short` | Kurze Geräteübersicht. | Sicht des angesprochenen X-Servers. |
| `list --long` | Mehr Fähigkeiten anzeigen. | Keine vollständige Funktionsprüfung. |
| `list-props GERÄT` | Eigenschaften lesen. | Noch keine Änderung. |
| `set-prop ...` | Eigenschaft setzen. | Kann Eingabeverhalten verändern. |
| `disable GERÄT` | Gerät im betreffenden X-Kontext deaktivieren. | Kann Bedienung verlieren lassen. |
| `test`, `test-xi2` | Eingabeereignisse beobachten. | Datenschutzrelevanter Mitschnitt. |

Die Versionsabfrage kann laut Manpage auch den X-Server prüfen. Sie ist deshalb nicht als garantiert kontaktfreie reine Paketabfrage dokumentiert.

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter `xinput list --short`-Aufruf würde zunächst die sichtbaren Namen und IDs zeigen. Danach wäre zu prüfen, ob eine echte X11-Sitzung oder Xwayland vorliegt.

Der Aufruf wurde nicht ausgeführt. Es wurden keine persönlichen Gerätenamen oder Tastaturereignisse gelesen.

Ein fiktiver Eintrag `xwayland-pointer` wäre keine Bezeichnung für eine direkt vollständig steuerbare physische Maus. Ein globaler Wayland-Eingabefehler lässt sich daraus nicht durch zufällige X-Propertyänderungen beheben.

## 6. Typische Anwendungsfälle

- Eine X11-Gerätezuordnung erklären.
- Eigenschaften eines bekannten Geräts lesend betrachten.
- Xwayland-Grenzen einer älteren Anleitung erkennen.
- Eine gezielte Änderung erst nach klarer Zuordnung vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Deaktivierung, Tastenabbildung oder Modusänderung kann die eigene Bedienung beeinträchtigen. Vor jeder Änderung einen passenden Rückweg berücksichtigen.

Ereignisbeobachtung kann sensible Tastendrücke erfassen. Sie ist kein harmloser Bestandteil einer bloßen Geräteliste und wird hier nicht gestartet.

## 8. Häufige Fehler

- **Xwayland gleich globales Wayland:** Unterschiedliche Reichweite.
- **Alte ID wiederverwenden:** Zuordnung kann wechseln.
- **Testmodus als reine Auflistung:** Ereignisse werden beobachtet.
- **Root löst X-Zugriff:** Sitzungsautorisierung ist eine eigene Frage.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit lesender Liste und bekanntem Sitzungstyp beginnen. Für Wayland die vorgesehenen Systemeinstellungen beziehungsweise Compositorwerkzeuge verwenden.

Keine Zugriffsschutzregeln des X-Servers abschalten, nur um einen Diagnosebefehl starten zu können. Zuerst den richtigen eigenen Sitzungskontext wählen.

## 10. Verwandte Befehle

- `lsinput`: Kernel-Eingabegeräte mit anderer Sicht.
- `xset`: Bestimmte X11-Einstellungen.
- `xrandr`: X11-Anzeigeausgänge.
- `libinput`: Andere Eingabeebene; Unterbefehlwirkung beachten.

**Prüfstand:** Lokale Manpage gelesen. Kein X-Serverkontakt, Ereignismitschnitt oder Eingabewechsel durchgeführt.

Ausgangsdatensatz 396 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
