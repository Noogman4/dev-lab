---
id: "masscan"
name: "masscan"
command: "masscan"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: true
risk_level: "danger"
tags: ["NetMon Spezial / Diagnoseideen", "masscan"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 409
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; masscan fehlt"
---

# masscan – Masscan-Konfiguration vor einem Scan lesen

## 1. Kurzbeschreibung

masscan ist ein aktiver Portscanner mit eigener Paketverarbeitung. Ein gewöhnlicher Scan erzeugt reale Netzwerkpakete und braucht typischerweise besondere Rechte. Es ist keine harmlose Statusabfrage und keine vollständige Ersatzimplementierung aller Nmap-Funktionen.

## 2. Was macht der Befehl?

Zielmenge, Portmenge und Senderate sind getrennte Größen. Schon eine kleine Portliste kann bei einem großen CIDR-Bereich sehr viele Versuche erzeugen. --echo gibt die wirksame Konfiguration aus und beendet den Aufruf, statt den Scan zu starten. Bannererfassung geht über die reine Portreaktion hinaus. Der eigene TCP/IP-Stack kann mit dem Hoststack kollidieren; daraus folgt keine Freigabe, zur Übung IP-Adressen oder Firewallregeln zu ändern.

Quelle, am 2026-11-13 gelesen: [Masscan-Projekt: README und Konfigurationsmodus](https://github.com/robertdavidgraham/masscan/blob/master/README.md)

## 3. Syntax

```text
masscan ZIELBEREICH -p PORTLISTE [OPTIONEN]
masscan [KONFIGURATIONSOPTIONEN] --echo
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-p PORTLISTE` | Ports ausdrücklich festlegen, Bereich inklusive Grenzen zählen. |
| `--rate ANZAHL` | Gewünschte Paketrate, keine Zusicherung verträglicher Last. |
| `-c DATEI` | Konfigurationsdatei einlesen; Inhalt vollständig prüfen. |
| `--echo` | Konfiguration anzeigen und beenden. |
| `--excludefile DATEI` | Ziele ausschließen; kein Ersatz für eine korrekt begrenzte Zielmenge. |
| `-oX DATEI` | XML-Ergebnisse schreiben. |
| `--banners` | Zusätzliche Protokollinteraktion; weitergehender Eingriff. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur Erklärungsmuster: masscan -p80 192.0.2.1 --rate 1 --echo
```

192.0.2.1 ist eine Dokumentationsadresse, kein freigegebenes reales Ziel. Das Muster erklärt ausschließlich den Echo-Modus: Konfiguration lesen statt senden. Es wurde wegen fehlendem Programm auch nicht als Offlineprüfung ausgeführt. Das Entfernen von --echo würde aus demselben Muster einen echten Sendeauftrag machen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Scanplanung prüfen: Ziel- und Portumfang vorab rechnen. Konfiguration verstehen: Anzeige der Parameter von tatsächlicher Netzaktivität unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Bereiche oder hohe Raten können sehr viele Systeme ansprechen. Scans und Bannererfassung können Dienste belasten und Alarmierungen auslösen. Keine Flächenscans, keine Quelladress-/Firewalländerungen und keine Scans fremder Ziele in dieser Aufgabe.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nmap-Option unbekannt | Nur dokumentierte Masscan-Optionen übernehmen. |
| Keine Portmeldung | Keine eindeutige Aussage über Host oder Filter. |
| Banner fehlt trotz offenem Port | Stack-/Protokollverhalten unterscheidet sich vom einfachen Scan. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; masscan fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nping` | Gezielte Paketdiagnose. |
| `nmap` | Andere Scanarchitektur. |
| `ss` | Lokale Sockets ohne Scan externer Ziele. |

Ausgangsdatensatz 409 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
