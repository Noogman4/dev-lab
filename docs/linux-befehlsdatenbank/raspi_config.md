---
id: "raspi_config"
name: "raspi-config"
command: "raspi-config"
category: "Raspberry Pi"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Raspberry Pi", "raspi-config"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 531
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Menü- und Änderungsabläufe offen"
---

# raspi-config – Raspberry-Pi-Konfiguration gezielt vorbereiten

## 1. Kurzbeschreibung

raspi-config ist eine Oberfläche für Systemkonfiguration und keine reine Statusanzeige.

## 2. Was macht der Befehl?

Menüpunkte und nichtinteraktive Funktionen können Bootdateien, Dienste, Schnittstellen und weitere Systemparameter verändern. Die aktuelle Herstellerbeschreibung und ältere Implementierungen unterscheiden sich in Menüstruktur und Dateipfaden. Für neuere Raspberry Pi OS-Versionen liegt config.txt häufig unter /boot/firmware; ältere Skripte verwenden /boot.

Quelle, am 2026-11-13 gelesen: [raspi-config: offizieller Paketquelltext](https://raw.githubusercontent.com/RPi-Distro/raspi-config/master/raspi-config), [Hersteller: Konfigurationswege](https://www.raspberrypi.com/documentation/computers/configuration.html#configuration-methods)

## 3. Syntax

```text
raspi-config
raspi-config nonint FUNKTION [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| interaktiver Start | Konfigurationsmenü; Auswahl kann Änderungen auslösen. |
| nonint | Benannte Funktion ohne Menü aufrufen; keine automatische Trockenübung. |
| get_-Funktionen | Versionsabhängige Abfragen, deren konkreten Quelltext prüfen. |
| do_-Funktionen | Können Konfiguration ändern und Neustartbedarf erzeugen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
raspi-config
```

Der bloße Menüstart wurde nicht durchgeführt. Für die Leseübung werden nur Wirkung und Rechtebedarf betrachtet; ein Menüpunkt ist nicht ausgewählt worden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Konfigurationsmöglichkeiten einer bekannten Pi-Installation verstehen; eine spätere einzelne Änderung vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Kein pauschaler Probelauf auf einem produktiven Pi. SSH-, Netzwerk- oder Bootänderungen können den Zugang unterbrechen. Viele Konfigurationsaktionen benötigen Root. Keine Systemdatei geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Menüpunkt fehlt | Release und Paketversion passen möglicherweise nicht zur Anleitung. |
| Änderung erst nach Neustart sichtbar | Neustartbedarf und betroffene Komponente prüfen; keinen Neustart auslösen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Menü- und Änderungsabläufe offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| dtparam | Laufzeitparameter. |
| dtoverlay | Laufzeit-Overlays. |
| systemctl | Dienstzustände getrennt prüfen. |

Ausgangsdatensatz 531 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
