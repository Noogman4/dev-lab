---
id: "wavemon"
name: "wavemon"
command: "wavemon"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "wavemon"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 420
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; wavemon fehlt"
---

# wavemon – WLAN-Signalwerte ohne falsche Durchsatzschlüsse lesen

## 1. Kurzbeschreibung

wavemon zeigt WLAN-Geräteinformationen und Signalverläufe in einer Terminaloberfläche. Einige Ansichten lösen Scans aus oder speichern Einstellungen. Allgemeine Anzeigerechte und CAP_NET_ADMIN für bestimmte Operationen sind zu unterscheiden.

## 2. Was macht der Befehl?

dBm ist ein logarithmischer Leistungspegel, dB eine Verhältnisgröße. Bei negativen dBm-Werten ist -50 ein stärkeres Signal als -70; daraus folgt keine feste Nettoübertragungsrate. Qualität und verfügbare Rauschwerte hängen vom Treiber ab. Ein Scanfenster entdeckt sichtbare Funkankündigungen, es verifiziert keine sichere Accesspointidentität. Die Unterstützung moderner WLAN-Hardware kann von der beschriebenen älteren Version abweichen.

Quelle, am 2026-11-13 gelesen: [wavemon-Projekthandbuch](https://manpages.debian.org/trixie/wavemon/wavemon.1.en.html)

## 3. Syntax

```text
wavemon [-i INTERFACE] [-g]
wavemon -h
wavemon -v
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i NAME` | WLAN-Interface wählen, kein Verbindungsprofil. |
| `-g` | Terminalgeometrie prüfen; kein allgemeiner Nur-Lesemodus. |
| `F1` | Informationsansicht. |
| `F2` | Signalverlauf über die Zeit. |
| `F3` | Scanansicht; kann Funkabfragen und besondere Rechte benötigen. |
| `F7` | Einstellungen ändern und speichern, echte Benutzeränderung. |
| `q` | Beenden. |
| `-v` | Version lesen und beenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Erfundenes Pegelbeispiel: Signal -60 dBm, Rauschen -90 dBm → Abstand 30 dB.
```

Die Differenz erklärt den Signal-Rausch-Abstand, sofern beide Werte passend gemessen wären. Es handelt sich um reine Rechenwerte, nicht um eine Funkmessung. Ein SNR von 30 dB garantiert weder Internetzugang noch einen bestimmten Durchsatz. Keine Funkkarte oder Scanansicht wurde geöffnet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Signalbegriffe erklären: Leistung, Verhältnis, Qualität und Datenrate getrennt lesen. Fehlersuche planen: Treiberunterstützung und Interfacezuordnung dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Scans können Funkverkehr erzeugen und den Betriebsablauf beeinflussen. SSIDs und MAC-Adressen sind sensible Standortdaten. Keine Setuid-/Capabilityänderung aus einer alten Manpage übernehmen, keine Kanäle, Treiber oder Profile verändern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein unterstütztes Interface | Treiber/API oder Geräteverfügbarkeit prüfen. |
| Rauschen fehlt | Treiber liefert nicht alle Werte; keinen Nullwert erfinden. |
| Guter Pegel, schlechte Rate | Auslastung, Störungen und andere Pfadfaktoren bleiben offen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; wavemon fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `iw` | Moderne WLAN-Verwaltung und Status. |
| `iwconfig` | Ältere Wireless-Extensions-Sicht. |
| `nmcli` | Profilverwaltung statt Funkpegelhistogramm. |

Ausgangsdatensatz 420 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
