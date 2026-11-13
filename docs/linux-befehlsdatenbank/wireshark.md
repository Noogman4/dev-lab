---
id: "wireshark"
name: "wireshark"
command: "wireshark"
category: "Wireshark & Analyse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Wireshark & Analyse", "wireshark"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 713
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; GUI, Profile und Livebetrieb offen"
---

# wireshark – Wireshark-Dateianalyse und Liveaufzeichnung unterscheiden

## 1. Kurzbeschreibung

wireshark ist eine grafische Anwendung für Paketdateien und Live-Captures.

## 2. Was macht der Befehl?

Ein gespeicherter Capture kann ohne Aufzeichnung betrachtet werden; -r wählt die Datei. -k startet dagegen eine Aufzeichnung. Capturefilter und Displayfilter wirken auf unterschiedlichen Ebenen. Die GUI-Funktionen sind durch CLI-/Dateitests anderer Werkzeuge nicht praktisch nachgewiesen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.wireshark.org/docs/man-pages/wireshark.html)

## 3. Syntax

```text
wireshark [OPTIONEN] [CAPTUREDATEI]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -r DATEI | Gespeicherte Datei öffnen |
| -n | Namensauflösung abschalten |
| -Y FILTER | Displayfilter |
| -i QUELLE | Captureinterface |
| -k | Liveaufzeichnung starten, aktive Aktion |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
wireshark -n -r EIGENE_SYNTHETISCHE_DATEI.pcap
```

Keine GUI gestartet, kein Interface geöffnet und keine Fenster- oder Benutzereinstellung verändert. Ein vorhandenes Programm gilt nicht als getestete Oberfläche.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Offlineanalyse von Capturebeginn unterscheiden; Interpretation vor späterer freigegebener Bedienung vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Reale Mitschnitte, Dekodierungsgeheimnisse und Profile sind vertraulich. Keine privilegierte GUI und keine Capabilityänderung zum Test.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Display fehlt | Kein Anlass für Systemänderungen |
| Filter zeigt nichts | Capturefilter und Displayfilter unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; GUI, Profile und Livebetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| tshark | Offline-CLI |
| dumpcap | Live-Aufzeichnung |
| capinfos | Dateimetadaten |

Ausgangsdatensatz 713 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
