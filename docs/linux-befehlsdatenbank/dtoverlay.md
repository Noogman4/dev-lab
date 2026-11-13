---
id: "dtoverlay"
name: "dtoverlay"
command: "dtoverlay"
category: "Raspberry Pi"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Raspberry Pi", "dtoverlay"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 527
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Geräte- und Ladeprüfung offen"
---

# dtoverlay – Device-Tree-Overlays zur Laufzeit verwalten

## 1. Kurzbeschreibung

dtoverlay kann auf passenden Raspberry-Pi-Systemen Overlays anzeigen, laden und entfernen.

## 2. Was macht der Befehl?

Overlays ergänzen die Hardwarebeschreibung. Laden und Entfernen können im Kernel Geräte erzeugen oder abbauen; dies ist eine reale Systemänderung. Bereits beim Booten eingebaute Overlays werden nicht wie Laufzeit-Overlays aufgelistet oder entfernt. Die Reihenfolge des Laufzeitstapels ist relevant.

Quelle, am 2026-11-13 gelesen: [Raspberry Pi: dtoverlay-Implementierung und Hilfe](https://raw.githubusercontent.com/raspberrypi/utils/master/dtmerge/dtoverlay.c)

## 3. Syntax

```text
dtoverlay -h [OVERLAY]
dtoverlay -l
dtoverlay OVERLAY [PARAMETER=WERT ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -h | Werkzeug- oder Overlayhilfe. |
| -l | Aktive Laufzeit-Overlays auflisten. |
| -a | Verfügbare Overlays anzeigen. |
| -r | Overlay entfernen; verändert Kernelzustand. |
| -D | Vorbereiten statt anwenden; schreibt eine dtbo-Datei, ist nicht schreibfrei. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
dtoverlay -h TEST_OVERLAY
```

Ein vorab ausgewählter Overlayname würde seine Parameterhilfe liefern. TEST_OVERLAY ist ein Platzhalter. Hier erfolgte weder eine Hardwareabfrage noch ein Ladeversuch.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Overlayparameter verstehen; geplante Hardwarekonfiguration fachlich vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Aktive Geräte können verschwinden; Treiber reagieren unterschiedlich. Ein Overlay ist keine beliebig rücknehmbare Textänderung. Hardware-, Firmware- und Kernelstand müssen zusammenpassen. Keine Pi-Werkzeuge vorhanden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Overlay fehlt | Paket, Verzeichnis und exakten Namen prüfen. |
| Nicht entfernbar | Boot-Overlay und Stapelreihenfolge beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Geräte- und Ladeprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| dtparam | Parameter des Basisbaums. |
| raspi-config | Systemkonfiguration. |
| pinout | Pinbelegung nachschlagen. |

Ausgangsdatensatz 527 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
