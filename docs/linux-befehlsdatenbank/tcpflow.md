---
id: "tcpflow"
name: "tcpflow"
command: "tcpflow"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "tcpflow"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 416
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; tcpflow fehlt"
---

# tcpflow – TCP-Datenströme aus Paketen rekonstruieren

## 1. Kurzbeschreibung

tcpflow setzt erfasste TCP-Nutzdaten zu gerichteten Datenströmen zusammen und schreibt sie meist in Dateien. Es ist kein einfacher Socketstatusbefehl. Eigene Offline-PCAPs benötigen nur passende Dateirechte; Live-Capture braucht besondere Rechte.

## 2. Was macht der Befehl?

Eine Verbindung besteht gewöhnlich aus zwei Richtungen mit getrennten Ausgaben. TCP-Sequenznummern helfen bei Reihenfolge und Wiederholungen. Fehlende Capturepakete und die dokumentierten Einschränkungen bei IP-Fragmenten begrenzen die Rekonstruktion. Verschlüsselte Nutzdaten werden nicht allein durch TCP-Zusammensetzen zu Klartext. Flowdateien sind keine ursprünglichen Pakete und enthalten andere Strukturen als eine PCAP.

Quelle, am 2026-11-13 gelesen: [tcpflow-Projekthandbuch](https://manpages.debian.org/trixie/tcpflow-nox/tcpflow.1.en.html) und [Projektbeschreibung](https://github.com/simsong/tcpflow)

## 3. Syntax

```text
tcpflow [OPTIONEN] [CAPTUREFILTER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-r DATEI` | PCAP offline statt Live-Capture lesen. |
| `-i INTERFACE` | Live-Capturepunkt wählen; hier ausgeschlossen. |
| `-o ORDNER` | Ausgabeverzeichnis festlegen. |
| `-c` | Nutzdaten auf Konsole statt gewöhnlicher Flowdateien; sensible Ausgabe beachten. |
| `-a` | Weitere Scanner/Interpretationen aktivieren, etwa HTTP-Rekonstruktion. |
| `-b BYTES` | Maximal zu speichernde Bytes pro Flow begrenzen. |
| `-F`, `-T` | Dateinamentemplate beeinflussen; keine beliebigen fremden Templates übernehmen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Offline-Muster: tcpflow -r eigene.pcap -o NEUER-AUSGABEORDNER
```

Die PCAP müsste aus selbst erzeugtem, autorisiertem Testinhalt stammen. Getrennte Dateien für Hin- und Rückrichtung wären zu erwarten; ihre Namen kodieren Endpunkte. Hier wurde keine PCAP erzeugt oder verarbeitet. Rekonstruierte HTTP-Daten wären weiter als fremder Inhalt zu behandeln, nicht automatisch zu öffnen oder auszuführen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Transportrekonstruktion lernen: Pakete, Richtungsstrom und Anwendungsobjekt unterscheiden. Eigene Protokollfehler untersuchen: Captureabdeckung dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausgaben können Zugangsdaten, übertragene Dateien und interne Adressen enthalten. Viele Flows belegen Speicher und Dateideskriptoren. Scanner können zusätzliche Ergebnisse schreiben. Keine realen Benutzeraufzeichnungen, Liveinterfaces oder fremden PCAPs als Beispiel verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nur eine Richtung | Capture unvollständig oder asymmetrischer Pfad. |
| Unlesbarer Inhalt | Verschlüsselung, binäres Format oder Lücken. |
| Kein vollständiger Stream | Fragmentierung oder fehlende Pakete prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; tcpflow fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `tcpdump` | Paketmitschnitt statt Stromrekonstruktion. |
| `tcpreplay` | Sendet erfasste Pakete erneut, ganz andere Wirkung. |
| `ss` | Lokale Socketzustände. |

Ausgangsdatensatz 416 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
