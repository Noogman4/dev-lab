---
id: "xrandr"
name: "xrandr"
command: "xrandr"
category: "Hardware"
language: "de"
root_required: false
risk_level: "caution"
tags: ["xrandr", "hardware"]
status: "Keine Bildschirme abgefragt oder umgestellt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 397
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale xrandr-Manpage gelesen"
---

# xrandr – X11-Ausgänge abfragen und Bildschirmänderungen gezielt planen

## 1. Kurzbeschreibung

`xrandr` liest oder verändert Ausgänge und Modi eines X-Servers über RandR. **Root-Rechte sind für die eigene passend autorisierte X-Sitzung nicht nötig.** Änderungen können die sichtbare Bedienung unmittelbar beeinflussen.

## 2. Was macht der Befehl?

Die lokale Manpage beschreibt Auflösung, Orientierung und Anordnung. Ohne gewünschte Änderung wird der Ausgangszustand angezeigt. Ein Stern kennzeichnet dabei den aktuellen, ein Plus den bevorzugten Modus.

Die Schnittstelle ist auf X11 bezogen. Bei Wayland nicht davon ausgehen, dass eine Xwayland-Ansicht alle physischen Monitore global konfigurieren kann. Die tatsächliche Desktopverwaltung ist gesondert zu berücksichtigen.

## 3. Syntax

```bash
xrandr --query
xrandr --current
```

Änderungsschablone nur zur Erklärung:

```text
xrandr --output AUSGANG --mode MODUS
```

Ausgang und Modus müssen aus der passenden tatsächlichen Sitzung stammen. Hier wird kein realer Anschlussname vorausgesetzt.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `--query` | Aktuellen Bericht anfordern. | Keine gewünschte Modusänderung. |
| `--current` | Vorhandenen Zustand ohne Hardwarepolling abfragen. | Daten können entsprechend begrenzt sein. |
| `--output NAME` | Ausgang auswählen. | Nachfolgende Änderungen darauf beziehen. |
| `--mode NAME` | Modus setzen. | Kann Anzeige verändern. |
| `--rotate ...` | Orientierung ändern. | Reale Darstellungsänderung. |
| `--off` | Gewählten Ausgang abschalten. | Bedienbild kann verschwinden. |
| `--dryrun` | Vorgesehene Aktionen ohne Anwenden betrachten. | Kein realer Funktionstest. |

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter Einstieg wäre `xrandr --query`. Zunächst Ausgänge, Verbindung und aktuellen Modus zuordnen. Ein bevorzugter Modus ist nicht automatisch der gerade verwendete.

Der Bericht wurde hier nicht erhoben. Es wurden weder Monitorbezeichnungen noch aktuelle Auflösungen des Benutzers gelesen.

Vor einer späteren Änderung den gewünschten Ausgang und tatsächlich angebotenen Modus ausdrücklich festhalten. Die alte Konfiguration und ein Bedienrückweg müssen bekannt sein; ein unpassender Modus kann die weitere Arbeit erschweren.

## 6. Typische Anwendungsfälle

- Eine X11-Ausgangsübersicht für einen gezielten Fehlerbericht betrachten.
- Aktuellen und bevorzugten Modus unterscheiden.
- Eine geplante Mehrmonitoranordnung beschreiben.
- Grenzen älterer X11-Anleitungen unter Wayland erkennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Modi, Abschalten oder Verschieben von Ausgängen können die Anzeige praktisch unbenutzbar machen. Nicht ohne Rückweg am einzigen sichtbaren Ausgang experimentieren.

Ein Dry-run bestätigt nicht, dass Darstellung und Anwendungen nach einer echten Änderung wie gewünscht funktionieren. Treiber, RandR-Fassung und Desktopverwaltung beeinflussen das Ergebnis.

## 8. Häufige Fehler

- **Bevorzugt gleich aktuell:** Zeichen in der Ausgabe unterscheiden.
- **Anschlussnamen aus fremder Anleitung übernehmen:** Lokale Zuordnung fehlt.
- **Xwayland als globale Waylandverwaltung:** Reichweite prüfen.
- **Änderungsoption an Abfrage anhängen:** Wirkung ist dann nicht mehr rein lesend.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer reinen Abfrage anfangen. Für normale Desktopänderungen kann die vorhandene Systemeinstellung einen leichter nachvollziehbaren Rückweg bieten.

Keine Startskripte mit pauschalem Abschalten von Ausgängen erstellen, bevor die konkrete Gerätekonfiguration und Sitzung eindeutig feststehen.

## 10. Verwandte Befehle

- `xset`: Weitere X11-Einstellungen.
- `xinput`: Eingabegeräte des X-Servers.
- Desktop-Anzeigeeinstellungen: Vorgesehener Verwaltungsweg des Compositors.
- `lspci -k`: Grafikgeräte-/Treiberkontext, kein Bildschirmmoduswechsel.

**Prüfstand:** Lokale Manpage gelesen. Keine Bildschirmabfrage, Modusänderung oder X-Zugriffskonfiguration ausgeführt.

Ausgangsdatensatz 397 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
