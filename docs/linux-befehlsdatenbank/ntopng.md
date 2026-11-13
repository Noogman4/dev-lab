---
id: "ntopng"
name: "ntopng"
command: "ntopng"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: true
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "ntopng"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 414
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; ntopng fehlt"
---

# ntopng – Verkehrsanalyse mit ntopng einordnen

## 1. Kurzbeschreibung

ntopng analysiert Paket- oder Flowdaten und bietet eine Weboberfläche. Ein normaler Start kann Capture, Weblistener, Datenbankzugriffe und Zusatzabfragen auslösen. Er ist keine rein lesende Momentaufnahme.

## 2. Was macht der Befehl?

Der gewählte Eingang kann ein Interface, eine PCAP oder ein unterstützter Flowkanal sein. Sichtbarkeit hängt vom Beobachtungspunkt ab; fehlender Verkehr ist kein Nachweis fehlender Kommunikation. Protokollklassifikation ist eine Analyseentscheidung, kein kryptografischer Identitätsnachweis. CLI, Funktionsumfang und Lizenzvarianten ändern sich. Besondere Live-Capturerechte gelten getrennt von Datenverarbeitung und Webzugriff.

Quelle, am 2026-11-13 gelesen: [ntop-Projekt: ntopng-CLI](https://www.ntop.org/guides/ntopng/cli_options/cli_options.html)

## 3. Syntax

```text
ntopng KONFIGURATIONSDATEI
ntopng [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i EINGANG` | Capture-/Flowquelle oder PCAP wählen. |
| `-d ORDNER` | Beschreibbares Datenverzeichnis festlegen. |
| `-w [ADRESSE:]PORT` | HTTP-Endpunkt; lokale Bindung ausdrücklich planen. |
| `-r PARAMETER` | Redis-Verbindung, nicht allgemein eine PCAP-Leseoption. |
| `-n MODUS` | DNS-/Protokollauflösung steuern; Modusbedeutung prüfen. |
| `--offline` | Externe Zusatzkontakte vermeiden; keine allgemeine Prozesssandbox. |
| `--shutdown-when-done` | Nach PCAP-Verarbeitung beenden, versionsbezogen. |
| `--disable-login` | Authentisierung abschalten; für diese Übung ausgeschlossen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Offline-Analyseplan: eigene PCAP, neues Datenverzeichnis, getrennte Redis-Instanz, begrenzte Webbindung.
```

Der Plan wäre vor einem späteren Test vollständig zu konkretisieren. Eine PCAP-Eingabe allein isoliert weder Redis noch Weblistener oder Zusatzabfragen. Hier wurden weder Redis angesprochen, PCAP verarbeitet noch Webdienste gestartet. Keine echten Hostnamen oder Flowdaten werden als gemessen dargestellt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Analysearchitektur planen: Datenquelle, Speicherung und Zugriffsoberfläche getrennt wählen. Ausgaben bewerten: Klassifikation und Beobachtungsabdeckung nachvollziehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Flowdaten und Protokolldetails können vertraulich sein. Persistente Ablage und erreichbare Weboberflächen erfordern bewusste Freigabe. Keine bestehende Redis-Datenbank verwenden, Schutz-/Loginfunktionen deaktivieren oder produktive Dienste starten.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Redisfehler | Separaten vorgesehenen Datenbankkontext prüfen. |
| Lizenz-/Optionsunterschied | Installierte Edition und Version vergleichen. |
| Verkehr fehlt | Eingang und Capturebereich prüfen statt Netzfunktion zu unterstellen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; ntopng fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `darkstat` | Einfachere Paketstatistik. |
| `tcpflow` | TCP-Nutzdatenrekonstruktion. |
| `vnstat` | Zählerbasierte Statistik ohne volle Paketanalyse. |

Ausgangsdatensatz 414 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
