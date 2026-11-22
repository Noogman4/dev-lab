---
id: "lsinput"
name: "lsinput"
command: "lsinput"
category: "Hardware"
language: "de"
root_required: true
risk_level: "caution"
tags: ["lsinput", "hardware"]
status: "Verfügbare Debian-Manpage geprüft; aktuelle Zusatzoptionen nicht behauptet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 388
reviewed_at: "2026-11-13"
locally_checked_version: "lsinput lokal nicht installiert"
---

# lsinput – vom Kernel bereitgestellte Eingabegeräte auflisten

## 1. Kurzbeschreibung

`lsinput` aus `input-utils` listet Eingabegeräte des Linux-Kernels mit zusätzlichen Geräteinformationen. **Der Zugriff auf geschützte Eingabegeräteknoten kann besondere Rechte benötigen.** Das reine Lesen der Dokumentation braucht keine Root-Rechte.

## 2. Was macht der Befehl?

Die erreichbare [Debian-Manpage](https://manpages.debian.org/bookworm/input-utils/lsinput.8.en.html) beschreibt den einfachen Aufruf. Sie betrifft eine ältere Paketfassung; eine neuere lokale Fassung konnte mangels Installation nicht geprüft werden.

Die Auflistung ist von einem Mitschnitt tatsächlicher Tastatur- oder Mausereignisse zu unterscheiden. Sie beantwortet zunächst die Frage nach sichtbaren Geräteobjekten, nicht nach jeder Eingabefunktion einer Desktopanwendung.

## 3. Syntax

```bash
lsinput
```

Die geprüfte Manpage nennt keine erforderlichen Optionen. Ein allgemeines `--help` wird deshalb nicht aus dem Datenbankplatzhalter erfunden. Zusätzliche Funktionen bleiben bis zur Prüfung der tatsächlichen Paketfassung offen.

## 4. Wichtige Optionen

Für die hier belegte Grundfunktion ist keine Optionsliste nötig.

| Aspekt | Bedeutung | Grenze |
| --- | --- | --- |
| Geräteübersicht | Sichtbare Kernel-Eingabegeräte. | Nicht automatisch physische Einzelgeräte. |
| Rechte | Zugriff auf betreffende Geräteknoten. | Nicht pauschal alle Eingaberechte freigeben. |
| Paketfassung | Tatsächlicher Funktionsumfang. | Älteres Handbuch garantiert keine neuen Optionen. |

Ein physisches Gerät kann mehrere logische Eingabeschnittstellen bereitstellen. Umgekehrt kann ein Gerät virtuell sein. Die Anzahl der Einträge ist deshalb keine sichere Anzahl vorhandener Tastaturen oder Mäuse.

## 5. Beispiel erklärt Schritt für Schritt

Angenommen, eine eigene Tastatur erscheint in einer später autorisierten Übersicht mehrfach. Zunächst die Geräteangaben zuordnen. Eine zusätzliche Medien- oder Steuerfunktion kann einen eigenen logischen Eintrag erzeugen.

Der geplante `lsinput`-Aufruf wurde nicht ausgeführt. Es wurden weder Gerätepfade des Benutzers geöffnet noch echte Tastendrücke aufgenommen.

Für einen Anwendungsfehler müsste anschließend klar sein, welche Eingabeschnittstelle die Sitzung tatsächlich verwendet. Ein gelisteter Eintrag allein bestätigt keine vollständige Funktion in jeder Anwendung.

## 6. Typische Anwendungsfälle

- Einen bekannten Eingabegerätebestand überblicken.
- Physische und logische Eingabeeinheiten auseinanderhalten.
- Eine Gerätezuordnung für einen gezielten Supportfall vorbereiten.
- Auflistung und Ereignismitschnitt begrifflich trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Eingabegeräterecht kann besonders sensibel sein, weil andere Werkzeuge darüber tatsächliche Eingaben beobachten können. Nicht zur Behebung eines einfachen Lesefehlers die Gerätedateien allgemein lesbar machen.

Gerätenamen und Kennungen können private Details verraten. Nur die tatsächlich benötigten Angaben weitergeben. Keine zusätzlichen Ereignisleser ohne passenden Auftrag starten.

## 8. Häufige Fehler

- **Mehrere Einträge gleich mehrere physische Geräte:** Logische Funktionen berücksichtigen.
- **Kein Zugriff gleich defekte Tastatur:** Rechte und Sitzungskontext fehlen.
- **Liste als Eingabemitschnitt lesen:** Unterschiedlicher Datentyp.
- **Beliebige neue Optionen voraussetzen:** Tatsächliche Fassung prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst Dokumentation und vorhandenen Sitzungskontext klären. Für eine Grundübersicht keine dauerhafte Gruppen- oder udev-Rechteänderung vornehmen.

Bei X11 kann `xinput` eine andere Ebene zeigen. Unter Wayland ist dessen Sicht nicht automatisch die globale Eingabeansicht.

## 10. Verwandte Befehle

- `xinput`: X11-Eingabegeräte.
- `libinput`: Andere Eingabediagnose; Unterbefehlwirkung beachten.
- `input-events`: Ereignisbeobachtung mit anderem Datenschutzumfang.
- `lsusb`: USB-Geräteebene.

**Prüfstand:** Erreichbares Distributionshandbuch gelesen. Keine Geräteliste oder Eingaben erhoben; nicht belegte Optionen bleiben Prüfpunkt.

Ausgangsdatensatz 388 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
