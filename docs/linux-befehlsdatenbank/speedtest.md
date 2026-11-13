---
id: "speedtest"
name: "speedtest"
command: "speedtest"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "speedtest"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 415
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Wrapper nennt speedtest-cli 2.1.3, keine ausgeführte Version"
---

# speedtest – Den tatsächlich installierten Speedtest-Client bestimmen

## 1. Kurzbeschreibung

Der Name speedtest ist mehrdeutig. Hier verweist der lokale Startcode auf das Pythonprojekt speedtest-cli; der offizielle Ookla-Client hat eine andere CLI. Ein normaler Test überträgt echte Daten und benötigt üblicherweise kein Root.

## 2. Was macht der Befehl?

Die folgenden Optionen gehören zum gelesenen speedtest-cli-Projekt und dürfen nicht ungeprüft auf Ooklas gleichnamiges Programm übertragen werden. Der Test wählt externe Server und erzeugt Download-/Uploadlast. Das Ergebnis hängt von Gegenstelle, Pfad, Rechner und Client ab; es ist kein unabhängiger Vertragsnachweis. Die Projektlatenz ist keine ICMP-Pingmessung. Der Wrapper nennt Paket 2.1.3, was hier nicht als ausgeführte Programmversion ausgegeben wird.

Quelle, am 2026-11-13 gelesen: [speedtest-cli-Projekt und CLI](https://github.com/sivel/speedtest-cli), lokale speedtest-cli-Manpage und gelesener /usr/bin/speedtest-Wrapper; kein Inhaltsbeleg aus der nicht erreichbaren Ookla-Seite

## 3. Syntax

```text
speedtest [OPTIONEN]   (hier: Pythonprojekt speedtest-cli)
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--help`, `--version` | Lokale Variante erkennen, ohne Messung anzufordern. |
| `--no-download`, `--no-upload` | Jeweilige Teilmessung auslassen; kein allgemeiner Offlinemodus. |
| `--server ID` | Serverkennung auswählen, kein beliebiger Hostname. |
| `--list` | Serverliste abrufen; kann bereits Netzverkehr auslösen. |
| `--json`, `--csv` | Strukturierte Ausgabe; Raten laut Projekthilfe in bit/s. |
| `--bytes` | Terminalraten in Byte; verändert JSON-/CSV-Einheiten nicht. |
| `--share` | Ergebnisfreigabe anfordern; hier ausgeschlossen. |
| `--secure` | HTTPS für unterstützte Steuerkontakte wählen, keine Programmisolation. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
speedtest --help
Nur späterer Messplan: Implementierung, Server-ID, Zeitpunkt, Datenbudget und Einheiten festhalten.
```

Hilfe wäre vor einem echten Messlauf zuerst zu lesen. Es wurde nur der installierte Wrapper und das Handbuch gelesen, kein Clientlauf gestartet. Insbesondere --list, --json und ein parameterloser Aufruf sind keine harmlosen Offline-Tests. Konkrete Download-/Uploadwerte werden nicht erfunden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Implementierungen unterscheiden: Gleichnamige Clients und ihre Argumente zuordnen. Messprotokolle vorbereiten: Einheiten und externe Gegenstelle festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Datenübertragung kann Kosten, Last und Offenlegung der öffentlichen Adresse verursachen. Ergebnisfreigabe und externe Serverkontakte sind reale Aktionen. Keine Nutzungsbedingungen automatisch bestätigen oder fremde Installationsskripte ausführen. Die Ookla-Webseite war nicht erreichbar; deren Optionsdetails bleiben offen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Option unbekannt | Andere speedtest-Implementierung. |
| Bytesoption ändert JSON nicht | Projekt definiert strukturierte Raten weiter als bit/s. |
| Latenz weicht von ping ab | Andere Messmethode und Gegenstelle. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Wrapper nennt speedtest-cli 2.1.3, keine ausgeführte Version. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `iperf3` | Messung mit eigener gesondert freigegebener Gegenstelle. |
| `ping` | ICMP statt Speedtest-Verfahren. |
| `bmon` | Vorhandene Last beobachten. |

Ausgangsdatensatz 415 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
