---
id: "raspinfo"
name: "raspinfo"
command: "raspinfo"
category: "Raspberry Pi"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Raspberry Pi", "raspinfo"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 532
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Sammlung, sudo- und Gerätepfade offen"
---

# raspinfo – Umfassenden Pi-Diagnosebericht einordnen

## 1. Kurzbeschreibung

raspinfo sammelt zahlreiche Diagnoseangaben eines Raspberry Pi in einer Ausgabe.

## 2. Was macht der Befehl?

Das Herstellerskript ruft mehrere Werkzeuge auf und liest unter anderem System-, Firmware-, Boot- und Protokolldaten. Es enthält auch sudo-Aufrufe, etwa für Kernel- und Firmwarelogs sowie Pininformationen. Ein vermeintlich einfacher Bericht ist deshalb mehr als ein einzelner harmloser Textabruf.

Quelle, am 2026-11-13 gelesen: [raspberrypi/utils: raspinfo-Quelltext](https://raw.githubusercontent.com/raspberrypi/utils/master/raspinfo/raspinfo)

## 3. Syntax

```text
raspinfo
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| ohne Argumente | Sammelbericht erzeugen; viele Unteraufrufe. |
| Standardausgabe | Kann in Datei umgeleitet werden; dabei Ziel nicht überschreiben. |
| Implementierungsprüfung | Skriptversion und aufgerufene Werkzeuge vor dem Start lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
raspinfo > NEUE_EIGENE_BERICHTSDATEI
```

Das Muster wurde nicht ausgeführt. Die Umleitung würde eine Datei anlegen beziehungsweise überschreiben und der Bericht würde reale Systemdaten sammeln. Ein eigener Dateipfad allein isoliert diese Unteraufrufe nicht.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Umfang eines später ausdrücklich freigegebenen Supportberichts verstehen; gezielte Einzelabfrage gegen breite Sammlung abwägen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Berichte können Adressen, Seriennummern, Konfiguration und Logs enthalten. Eingebaute Filter sind keine vollständige Anonymisierung. Unerwartete sudo-Abfragen und Gerätezugriffe vermeiden. Kein Diagnosebericht erzeugt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Teilabschnitt fehlt | Unterwerkzeug fehlt oder wird vom Board nicht unterstützt. |
| sudo-Abfrage | Aufrufkette prüfen; keine zusätzlichen Rechte pauschal gewähren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Sammlung, sudo- und Gerätepfade offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| vcgencmd | Einzelne Firmwareabfragen. |
| dmesg | Kernelprotokoll. |
| rpi-eeprom-update | Bootloader-Werkzeug, nicht beliebig starten. |

Ausgangsdatensatz 532 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
