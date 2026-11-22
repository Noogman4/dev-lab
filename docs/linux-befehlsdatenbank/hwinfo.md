---
id: "hwinfo"
name: "hwinfo"
command: "hwinfo"
category: "Hardware"
language: "de"
root_required: true
risk_level: "caution"
tags: ["hwinfo", "hardware"]
status: "Distributionshandbuch geprüft; keine Hardwareprobe ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 384
reviewed_at: "2026-11-13"
locally_checked_version: "hwinfo lokal nicht installiert"
---

# hwinfo – eine gezielte Hardwareklasse statt eines pauschalen Vollberichts untersuchen

## 1. Kurzbeschreibung

`hwinfo` ermittelt Hardwareinformationen und kann Zusammenfassungen oder ausführliche Berichte erzeugen. **Für manche Bereiche und vollständige Prüfungen sind zusätzliche Rechte nötig; einfache verfügbare Angaben können ohne Root lesbar sein.**

## 2. Was macht der Befehl?

Die [Debian-Manpage zu hwinfo](https://manpages.debian.org/trixie/hwinfo/hwinfo.8.en.html) beschreibt ausgewählte Hardwareklassen und aktive Ermittlung. Das ist nicht immer nur das Lesen einer einzelnen vorbereiteten Textdatei.

Ein Aufruf ohne bewusste Auswahl kann einen sehr breiten Bericht erzeugen. Für eine konkrete Frage besser nur die benötigte Klasse vorsehen. Nicht jede Plattform wird vollständig erkannt.

## 3. Syntax

```text
hwinfo --help
hwinfo --cpu --short
hwinfo --netcard --short
```

Die Formen sind dokumentierte Pläne. Das Werkzeug ist lokal nicht installiert; es wurde keine Geräteerkennung gestartet.

## 4. Wichtige Optionen

| Option | Aufgabe | Grenze |
| --- | --- | --- |
| `--cpu` | CPU-Bereich untersuchen. | Nicht vollständiger Leistungstest. |
| `--netcard` | Netzwerkkarten betrachten. | Keine Aussage über Internetfunktion. |
| `--short` | Kürzere Darstellung. | Benötigt passende Hardwareauswahl. |
| `--only GERÄT` | Ausgabe auf ein Ziel eingrenzen. | Ebenfalls mit Hardwareklasse kombinieren. |
| `--log DATEI` | Bericht speichern. | Zusätzliche Datei. |
| `--save-config ...` | Erkannte Konfiguration speichern. | Systemweiter Schreibvorgang, keine Anzeigeoption. |
| `--help` | Bedienung zeigen. | Kein Vollscan. |

## 5. Beispiel erklärt Schritt für Schritt

Für eine fiktive Frage zur erkannten CPU-Klasse wäre `hwinfo --cpu --short` enger als eine unbeschränkte Bestandsaufnahme.

Ein späterer Bericht müsste zeigen, welche Quelle und Geräteklasse tatsächlich erkannt wurde. Ein kurzer Eintrag ist kein Benchmark und kein Beweis vollständiger Treiberfunktion.

Der Aufruf wurde nicht ausgeführt. Es wurde auch keine dauerhafte Hardwarekonfiguration unter systemweiten Verzeichnissen gespeichert. Fehlende lokale Installation wird nicht durch unaufgeforderte Paketinstallation ersetzt.

## 6. Typische Anwendungsfälle

- Eine bestimmte Hardwareklasse für einen Supportfall beschreiben.
- Eine breit angelegte Inventur bewusst eingrenzen.
- Erkannte Geräte von tatsächlich funktionierenden Anwendungen unterscheiden.
- Einen bekannten Bericht unter dokumentierter Auswahl vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Hardwareerkennung kann verschiedene Schnittstellen ansprechen und Ressourcen beanspruchen. Besondere Probe- oder Firmwaremodi nicht ungeprüft einschalten.

Berichte können Seriennummern, Adressen und Netzstruktur enthalten. Vor Weitergabe prüfen. Eine kurze Ausgabe ist nicht automatisch anonym.

## 8. Häufige Fehler

- **`--short` allein als klare Geräteauswahl:** Darstellung und Untersuchung unterscheiden.
- **Gerät erkannt gleich voll funktionsfähig:** Treiber und Anwendung fehlen als Nachweis.
- **Speicheroption als Diagnose lesen:** Kann systemweit schreiben.
- **Fehlender Eintrag gleich fehlende Hardware:** Erkennungsgrenzen berücksichtigen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit Handbuch und einer einzelnen Klasse beginnen. Für eine einfache CPU- oder USB-Frage kann ein engeres Werkzeug übersichtlicher sein.

Keine umfassende privilegierte Probe starten, wenn die benötigte Information bereits aus einer geeigneten lesenden Quelle hervorgeht.

## 10. Verwandte Befehle

- `lscpu`: CPU-Informationen.
- `lspci`, `lsusb`: Busbezogene Geräteübersicht.
- `lshw`: Andere Hardwarezusammenfassung.
- `inxi`: Supportorientierte Übersicht mit Filtern.

**Prüfstand:** Handbuch gelesen. Keine Hardwareprobe, Systemablage oder Gerätekonfiguration verändert.

Ausgangsdatensatz 384 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
