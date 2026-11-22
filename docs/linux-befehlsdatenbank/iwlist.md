---
id: "iwlist"
name: "iwlist"
command: "iwlist"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "iwlist"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 432
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# iwlist – WLAN-Liste bedeutet nicht automatisch passiv

## 1. Kurzbeschreibung

iwlist liefert zusätzliche Wireless-Extensions-Informationen. Der gewählte Informationsbereich entscheidet über Wirkung und Sensibilität; scanning kann einen aktiven Funkscan auslösen.

## 2. Was macht der Befehl?

Frequenz- und Bitratenlisten betreffen Fähigkeiten des Geräts, nicht gemessene Übertragungsleistung. Scanergebnisse hängen von Treiber, Rechten und Zeitpunkt ab. Gewöhnliche Benutzer sehen unter Umständen nur ältere Ergebnisse. Ein nicht gefundener Netzname ist daher kein Beweis, dass es dieses Netz nicht gibt.

Quelle, am 2026-11-13 gelesen: [Wireless Tools: iwlist-Handbuch](https://manpages.debian.org/trixie/wireless-tools/iwlist.8.en.html)

## 3. Syntax

```text
iwlist [SCHNITTSTELLE] {frequency|rate|power|scanning}
iwlist --help
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `frequency` | Verfügbare Frequenzen und Kanalangaben. |
| `rate` | Unterstützte Bitraten, keine Durchsatzmessung. |
| `power`, `txpower` | Unterstützte Energie-/Sendeleistungsmerkmale. |
| `scanning` | Scan anfordern; privilegiert und möglicherweise aktiv. |
| `scanning last` | Vorhandene Scanergebnisse lesen, keinen neuen Scan anfordern. |
| `keys`, `wpakeys` | Kann geheime Schlüssel offenlegen; nicht als Anfängerbeispiel verwenden. |
| `--help` | Lokale Hilfe; Versionsmodus kann ebenfalls Interfaces untersuchen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
iwlist wlan-lernen frequency
```

Das Muster würde die Frequenzinformationen des erfundenen Geräts lesen. Eine angezeigte Liste ist keine Freigabe zur Nutzung jedes Kanals. Kanalzahlen und Frequenzzeilen müssen nicht eins zu eins zusammenpassen. Keine Funkschnittstelle wurde abgefragt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Altbestand erklären:** Treiberfähigkeiten von Umgebungserkennung trennen. **Diagnose planen:** Alter und Herkunft von Scanergebnissen dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Name list garantiert weder Passivität noch unkritische Daten. Scans können Funkverkehr und kurzfristige Linkbeeinflussung verursachen; Schlüsselanzeigen sind vertraulich. Keine Scans, Schlüsselabfragen oder Rechteänderungen wurden vorgenommen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Scan leer | Altes Ergebnis, Rechte oder Treibergrenze berücksichtigen. |
| Operation not supported | Wireless Extensions fehlen; moderne Werkzeuge prüfen. |
| Rate falsch interpretiert | Unterstützte Modulationsrate statt Nutzdatenleistung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `iwconfig` | Gemeinsame ältere WLAN-Oberfläche. |
| `iw` | Moderne Fähigkeiten und Linkinformationen. |
| `nmcli` | Manageransicht und Profile. |

Ausgangsdatensatz 432 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
