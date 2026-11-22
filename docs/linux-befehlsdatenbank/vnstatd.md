---
id: "vnstatd"
name: "vnstatd"
command: "vnstatd"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "vnstatd"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 419
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; vnstatd fehlt"
---

# vnstatd – Interfacezähler dauerhaft in vnStat speichern

## 1. Kurzbeschreibung

vnstatd ist der Datensammler von vnStat. Er liest Interfacezähler und schreibt eine Datenbank. Der Start ist eine echte Hintergrund-/Speicheraktion, auch wenn keine eigenen Messpakete erzeugt werden.

## 2. Was macht der Befehl?

Die normale Statistik benötigt auf vielen Systemen keine Rootrechte, aber Schreibrechte am Datenbank-/Logpfad. Dienstinstallation und Privilegabgabe sind getrennte administrative Aufgaben. Lese-/Aktualisierungs- und Speicherintervalle sind verschieden: Werte können vor dem Speichern nur im Speicher liegen. Zählerüberläufe, Neustarts und Zeit-/Zeitzonenänderungen beeinflussen die Auswertung. Das Handbuch beschreibt den lokalen Zeitbezug ausdrücklich als Grenze.

Quelle, am 2026-11-13 gelesen: [vnStat-Projekt: vnstatd-Handbuch](https://humdi.net/vnstat/man/vnstatd.html)

## 3. Syntax

```text
vnstatd [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--config DATEI` | Ausdrückliche Konfiguration lesen. |
| `--nodaemon` | Im Vordergrund sammeln; trotzdem kein Trockenlauf. |
| `--daemon` | Hintergrundprozess starten. |
| `--noadd` | Automatisches Anlegen von Interfaceeinträgen verhindern, nicht sämtliche Dateierzeugung. |
| `--initdb` | Datenbank anlegen/prüfen und beenden; kann weiterhin schreiben. |
| `--sync` | Zählerbasis synchronisieren, Verkehr seit vorherigem Stopp kann ignoriert werden. |
| `--user`, `--group` | Identität beim Rootstart abgeben; keine Kontenerzeugung. |
| `--pidfile DATEI` | Sperr-/PID-Datei, laut Handbuch bei nodaemon ohne Wirkung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur Plan: eigene Konfiguration mit neuem Datenpfad, vorgesehene Interfaces und definierte Intervalle.
```

Die Intervalle sind mit Einheit zu dokumentieren: UpdateInterval in Sekunden, SaveInterval in Minuten. Ein neuer Datenpfad allein genügt nicht zur Simulation, da der Sammler weiterhin reale Interfaces lesen würde. Deshalb wurde weder Daemon noch initdb gestartet und keine bestehende Datenbank angesprochen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Langzeitmessung planen: Sammler und Abfragewerkzeug auseinanderhalten. Datenqualität beurteilen: Erfassungsauflösung, Speicherzeit und Lücken erfassen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Datenbank- und Logschreibvorgänge persistieren Nutzungsverhalten. SIGHUP kann speichern, neu laden und weitere Datenbankarbeiten auslösen; Signale sind keine passive Diagnose. Keine produktiven Dienste starten, stoppen oder umkonfigurieren. Systemzeit nicht für ein Beispiel ändern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| DB nicht schreibbar | Eigentümer und vorgesehenen eigenen Pfad prüfen. |
| Werte fehlen nach Abbruch | Cache und Speicherintervall unterscheiden. |
| Zu viele Interfaces | Automatische Aufnahme und Konfigurationsstand prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; vnstatd fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `vnstat` | Fragt gespeicherte Daten ab. |
| `systemctl` | Dienstverwaltung mit realen Änderungen. |
| `bmon` | Momentane Zählersicht. |

Ausgangsdatensatz 419 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
