---
id: "iw"
name: "iw"
command: "iw"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "iw"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 430
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; iw fehlt"
---

# iw – WLAN-Fähigkeiten und aktuellen Link trennen

## 1. Kurzbeschreibung

iw ist das nl80211-basierte WLAN-Werkzeug für moderne Linux-Treiber. Es kann Fähigkeiten und Linkzustand anzeigen, aber auch Scans, Verbindungen und Funkkonfiguration anfordern.

## 2. Was macht der Befehl?

phy bezeichnet das physische Funkgerät, dev eine WLAN-Schnittstelle. Fähigkeiten sind nicht gleich aktive Betriebsparameter. Die angezeigte TX-Bitrate ist ein Funklinkwert und kein gemessener Nutzdatendurchsatz. WPA-Verbindungen benötigen einen zuständigen Authentifizierungsdienst; iw connect ist kein vollständiger Ersatz für dessen Schlüssel- und Profilverwaltung.

Quelle, am 2026-11-13 gelesen: [Linux Wireless: iw-Dokumentation](https://wireless.docs.kernel.org/en/latest/en/users/documentation/iw.html)

## 3. Syntax

```text
iw [OPTIONEN] dev [SCHNITTSTELLE] KOMMANDO
iw phy [PHY] KOMMANDO
iw help
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list` | Unterstützte Funkfähigkeiten anzeigen. |
| `dev ... link` | Aktuelle Verbindung auslesen. |
| `dev ... station dump` | Stationsbezogene Zähler und Linkdaten. |
| `dev ... scan` | Scan anfordern; kann Funkverkehr erzeugen. |
| `dev ... get power_save` | Energiesparstatus abfragen. |
| `set ...` | Konfigurationsänderung; kein allgemeiner Lesemodus. |
| `help` | Lokale Befehle prüfen; iw fehlt hier. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
iw dev wlan-lernen link
Erfundene Signalanzeige: -60 dBm
```

Der erfundene Gerätename wird nicht benutzt. -60 dBm wäre ein Leistungspegel, kein Prozentwert. Ein höherer negativer Wert wie -50 dBm bedeutet mehr Empfangsleistung. Eine positive Linkanzeige würde weder DHCP noch DNS oder Internetzugang bestätigen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**WLAN verstehen:** Hardwarefähigkeiten von aktuellem Link unterscheiden. **Fehler eingrenzen:** Funk-, Adress- und Anwendungsebene nacheinander prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Scans, Verbindungswechsel, Monitorinterfaces und regulatorische Änderungen sind echte Geräteoperationen. Sendeleistung kann in mBm statt dBm erwartet werden; Werte niemals aus einer anderen Einheit übernehmen. Keine Funkabfrage oder Zustandsänderung wurde ausgeführt, iw ist nicht installiert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Not connected | Keine Assoziation, nicht automatisch ein Hardwaredefekt. |
| Operation not supported | Treiber-/Firmware- und Befehlsgrenzen prüfen. |
| Bitrate mit Downloadrate verwechselt | Funkoverhead und Ende-zu-Ende-Pfad fehlen in diesem Wert. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; iw fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `iwconfig` | Ältere Wireless-Extensions-Oberfläche. |
| `nmcli` | Profil- und Verbindungsverwaltung. |
| `ip address` | IP-Konfiguration getrennt vom Funklink. |

Ausgangsdatensatz 430 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
