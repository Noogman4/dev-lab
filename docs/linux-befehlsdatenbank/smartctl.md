---
id: "smartctl"
name: "smartctl"
command: "smartctl"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "smartctl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 245
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; smartctl fehlt"
---

# smartctl – SMART-Berichte und Selbsttests auseinanderhalten

## 1. Kurzbeschreibung

`smartctl` liest Laufwerksinformationen und steuert SMART-/Selbsttestfunktionen. Reine Berichte und zustandsändernde Test-/Einstellbefehle sind getrennte Aufgaben. Gerätekommunikation benötigt passende Zugriffsrechte.

## 2. Was macht der Befehl?

ATA, SCSI und NVMe liefern unterschiedliche Felder und Fehlersemantik. Rohwerte von Herstellerattributen sind nicht pauschal identisch zu interpretieren. Ein positives Gesundheitsurteil ist kein Garant gegen plötzliche Ausfälle. Ein Log vergangener Selbsttests ist nicht derselbe Vorgang wie das Starten eines neuen Tests. Bridge-/RAID-Zugriff muss zum Gerät passen.

Quelle, am 2026-11-13 gelesen: [smartmontools-Projekthandbuch, einschließlich Statusbits](https://manpages.debian.org/trixie/smartmontools/smartctl.8.en.html)

## 3. Syntax

```text
smartctl [OPTIONEN] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i` | Identifikation anzeigen. |
| `-a`, `-x` | Umfangreiche Berichte; -x enthält weitere Informationen, Protokollabhängigkeit beachten. |
| `-j` | Strukturierte Ausgabe; lokale Version/Schema prüfen. |
| `-d TYP` | Protokoll-/Bridgezugriff festlegen; falscher Typ kann problematisch sein. |
| `--scan-open` | Gefundene Geräte auch öffnen; kein bloßes Hilfeprogramm. |
| `-t TEST` | Selbsttest starten; verändert Laufwerkszustand und erzeugt Last. |
| `-X` | Passenden laufenden Selbsttest abbrechen; keine reine Anzeige. |
| `-V` | Programmversion ohne Zielabfrage anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundenes Gesundheitsmuster:
SMART overall-health self-assessment test result: PASSED
```

Diese einzelne Zeile würde nur das jeweilige SMART-Gesamturteil ausdrücken. Fehlerlogs, Attribute, Tests, Schnittstelle und Zeitpunkt fehlen noch. Der Abschlussstatus ist eine Bitmaske: Ein Aufruffehler, ein Öffnungsfehler und ein gemeldeter Laufwerksfehler sind verschiedene Bits; ein beliebiger Nichtnullwert darf nicht einfach als sicherer Plattendefekt gelesen werden.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Bericht verstehen:** Identifikation, aktuelle Warnungen und historische Logs zusammen betrachten. **Diagnoseplanung:** Lesenden Logabruf von einem bewusst gestarteten Selbsttest unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Geräteabfragen können Laufwerke aufwecken, Protokollzustände beeinflussen oder Daten offenlegen. Einstellungen, Captive-Tests und Passthroughs sind keine harmlosen Zusätze. Seriennummern vor Weitergabe prüfen. Keine Geräte geöffnet, keine Tests gestartet, keine Dienste aktiviert; Programm fehlt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| PASSED trotz Ausfällen | Gesamturteil deckt nicht alle Fehler ab. |
| Nichtnullstatus | Einzelne Statusbits und Meldungen auswerten. |
| USB-Bericht unvollständig | Bridge/Protokoll unterstützt Funktionen eventuell nicht; nichts erzwingen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; smartctl fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nvme` | NVMe-spezifische Verwaltung. |
| `hdparm` | ATA-Parameter, teilweise schreibend. |
| `smartd` | Dauerhafte Überwachung; Einrichtung wäre ein eigener Auftrag. |

Ausgangsdatensatz 245 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
