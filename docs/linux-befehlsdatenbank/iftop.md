---
id: "iftop"
name: "iftop"
command: "iftop"
category: "Prozesse & Jobs"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Prozesse & Jobs", "iftop"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 487
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# iftop – Interfaceverkehr nach Hostpaaren messen

## 1. Kurzbeschreibung

iftop erfasst Pakete auf einem Interface und stellt Datenraten nach Hostpaaren dar. Es ordnet Verkehr nicht automatisch lokalen Prozessen zu. Live-Erfassung benötigt passende Capture-Rechte.

## 2. Was macht der Befehl?

Die Anzeige mittelt über verschiedene Zeitfenster. Host- und Portauflösung können zusätzliche Vorgänge auslösen. Ein Bildschirmfilter wirkt später als ein Capture-Filter und begrenzt nicht unbedingt Summen oder erfasste Daten. Richtung kann sich auf das Interface oder bei Netzgrenzenauswahl auf das angegebene Netz beziehen.

Quelle, am 2026-11-13 gelesen: [iftop-Projekt: Manpage](https://manpages.debian.org/trixie/iftop/iftop.8.en.html)

## 3. Syntax

```text
iftop [OPTIONEN] [-i INTERFACE] [-f CAPTURE_FILTER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i LINK` | Capture-Interface ausdrücklich auswählen. |
| `-n`, `-N` | Hostnamen- beziehungsweise Servicenamenauflösung unterlassen. |
| `-B` | Byte/s statt bit/s. |
| `-P` | Ports anzeigen. |
| `-f AUSDRUCK` | Capture-Filter; als ein Shellargument zitieren. |
| `-F NETZ/MASKE`, `-G IPV6/PRAEFIX` | Analysegrenze und Richtungsbezug festlegen. |
| `-t` | Textausgabe, weiterhin echte Paketerfassung. |
| `-p` | Promiscuous Mode anfordern; kein passiver Anzeige-Schalter. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
iftop -n -N -i eth-lernen -f 'host 192.0.2.1'
```

Das erfundene Interface und die Dokumentationsadresse werden nicht benutzt. Der Ausdruck wäre ein Capture-Filter. Weder -n noch Textausgabe verhindert die eigentliche Paketerfassung. Ein Wert von 8 Mbit/s entspräche rechnerisch 1 MB/s vor abweichender Einheitenbasis und ohne Anwendungsübertragungsbeweis.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Netzlast verstehen:** Zeitfenster, Einheit und Richtung dokumentieren. **Werkzeugwahl:** Hostpaarstatistik von Prozesszuordnung und aktiven Durchsatztests trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Erfassung kann vertrauliche Kommunikationsbeziehungen zeigen. Namensauflösung kann zusätzlichen Netzverkehr erzeugen. Keine Interfaces geöffnet, keine Pakete erfasst, keine Capture-Rechte gesetzt und keine Netztests ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Capture-Rechte | Voraussetzung fehlt; keine pauschalen Capabilities setzen. |
| Summen passen nicht zum Bildschirmfilter | Anzeige- und Capture-Filter unterscheiden. |
| Rate achtfach anders | bit/s gegenüber Byte/s prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nethogs` | Andere, prozessbezogene Zuordnung. |
| `tcpdump` | Paketerfassung mit eigener Ausgabe. |
| `bmon` | Interfacezähler statt Hostpaar-Capture. |

Ausgangsdatensatz 487 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
