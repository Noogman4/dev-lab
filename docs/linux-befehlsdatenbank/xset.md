---
id: "xset"
name: "xset"
command: "xset"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["xset", "hardware"]
status: "Keine Anzeige-, Tastatur- oder Energiespareinstellung verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 398
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale xset-Manpage gelesen"
---

# xset – X11-Einstellungen lesen, ohne Bildschirmschoner mit Sperre gleichzusetzen

## 1. Kurzbeschreibung

`xset` liest oder verändert bestimmte Einstellungen eines X-Servers, etwa Tastaturwiederholung und DPMS. **Root-Rechte sind für die eigene passend autorisierte Sitzung nicht nötig.** Viele Formen sind echte Änderungen.

## 2. Was macht der Befehl?

Die lokale Manpage nennt `q` als Zustandsabfrage. Andere Befehlswörter verändern Einstellungen des angesprochenen X-Servers. Das ist nicht automatisch die globale Verwaltung einer Wayland-Sitzung.

Bildschirmschoner, Energiesparen und sichere Bildschirmsperre sind verschiedene Funktionen. Ein dunkler Bildschirm beweist keine gesperrte Sitzung; ein abgeschalteter X-Bildschirmschoner ist umgekehrt keine vollständige Freigabe aller Desktop-Richtlinien.

## 3. Syntax

```bash
xset q
```

Die Buchstaben sind eigene Argumente. Ein allgemeines GNU-Langoptionsschema wird nicht vorausgesetzt. Für die reine Frage keine Änderungsargumente ergänzen.

## 4. Wichtige Optionen

| Form | Wirkung | Grenze |
| --- | --- | --- |
| `q` | Einstellungen abfragen. | Sicht des gewählten X-Servers. |
| `-display NAME` | X-Ziel auswählen. | Sitzungsautorisierung nötig. |
| `r on`, `r off` | Tastenwiederholung ändern. | Kann Bedienung beeinflussen. |
| `s ...` | X-Bildschirmschoner verwalten. | Kein universeller Sperrdienst. |
| `+dpms`, `-dpms` | DPMS aktivieren/deaktivieren. | Energiesparverhalten ändert sich. |
| `dpms force ...` | Zustand sofort anfordern. | Bildschirm kann dunkel werden. |
| `-version` | Programmversion zeigen. | Kein Bildschirmzustandsbericht. |

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter `xset q`-Aufruf würde mehrere Einstellungsbereiche anzeigen. Zunächst den tatsächlich relevanten Bereich lesen und den X-Sitzungsbezug festhalten.

Die Abfrage wurde hier nicht ausgeführt. Es wurden keine echten Tastaturparameter oder Bildschirmtimeouts erhoben.

Angenommen, eine Ausgabe nennt einen X-Screensaverwert. Daraus allein lässt sich nicht die sichere automatische Sperre des Desktops ableiten. Dafür müsste die zuständige Sitzungs- beziehungsweise Sperrverwaltung betrachtet werden.

## 6. Typische Anwendungsfälle

- X11-Wiederholungs- oder Energiesparwerte lesend verstehen.
- Eine alte Desktopanleitung auf ihren tatsächlichen Geltungsbereich prüfen.
- Einen konkret benannten Änderungsbedarf vorbereiten.
- Bildschirmblanking und sichere Sperre unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

DPMS- und Wiederholungsänderungen können die Bedienung stören. Deaktivierte Energiesparfunktionen erhöhen möglicherweise den Verbrauch; eine sofortige DPMS-Anforderung kann die sichtbare Ausgabe unterbrechen.

Keine X-Zugriffskontrolle abschalten, nur um den Aufruf aus einem fremden Kontext zu ermöglichen. Das wäre eine andere und weiterreichende Änderung.

## 8. Häufige Fehler

- **`q` mit Änderung kombinieren:** Keine reine Bestandsaufnahme mehr.
- **Dunkel gleich gesperrt:** Unterschiedliche Schutzfunktion.
- **X11-Wert global unter Wayland:** Kontext beachten.
- **Energiesparen dauerhaft abgeschaltet:** Ursache bleibt möglicherweise ungelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit der reinen Abfrage beginnen und nur den benötigten Abschnitt betrachten. Für normale Desktopkonfiguration die vorgesehenen Systemeinstellungen nutzen.

Vor Änderungen Ausgangswerte und Rückweg festhalten. Ein scheinbar funktionierender Workaround ist kein Nachweis für die richtige dauerhafte Einstellung.

## 10. Verwandte Befehle

- `xrandr`: Ausgänge und Modi.
- `xinput`: Eingabegeräteeigenschaften.
- Desktop-Sperrverwaltung: Sichere Sitzungssperre.
- `loginctl`: Sitzungsinformationen und Verwaltung mit eigener Wirkung.

**Prüfstand:** Lokale Manpage gelesen. Kein X-Serverkontakt und keine Änderung an Sperre, DPMS oder Tastaturverhalten.

Ausgangsdatensatz 398 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
