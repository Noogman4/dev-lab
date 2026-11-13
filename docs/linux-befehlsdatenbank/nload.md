---
id: "nload"
name: "nload"
command: "nload"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "nload"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 410
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; nload fehlt"
---

# nload – Eingehende und ausgehende Datenraten im Terminal lesen

## 1. Kurzbeschreibung

nload visualisiert aktuelle Interfacezähler und daraus berechnete Raten. Es erzeugt selbst keinen Durchsatztest. Für übliche Linuxzähler sind normalerweise keine Rootrechte nötig; es ist kein Mitschnitt einzelner Paketinhalte.

## 2. Was macht der Befehl?

Die Linuxquelle sind sysfs-/proc-Statistiken. Momentanrate, Mittelwert und Datenmenge beschreiben unterschiedliche Zeitbezüge. Ein Tunnelinterface und das tragende physische Interface können denselben Verkehr auf verschiedenen Ebenen zählen. Der beobachtete Maximalwert ist kein Nachweis der vertraglichen Anschlussgeschwindigkeit. Das ältere Handbuch ist versionsbezogen; konkrete Anzeige und Defaults der installierten Fassung gesondert prüfen.

Quelle, am 2026-11-13 gelesen: [nload-Projekthandbuch](https://manpages.debian.org/trixie/nload/nload.1.en.html)

## 3. Syntax

```text
nload [OPTIONEN] [INTERFACE...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-t MILLISEKUNDEN` | Anzeigeintervall; nicht Sekunden. Sehr kurze Intervalle verschlechtern Genauigkeit. |
| `-a SEKUNDEN` | Zeitfenster der Mittelwertberechnung. |
| `-u m`, `-u M` | Mbit/s beziehungsweise MByte/s. |
| `-U EINHEIT` | Einheit der Datenmenge ohne /s, getrennt von -u. |
| `-m` | Mehrere Interfaces ohne Graphen gleichzeitig zeigen. |
| `-i`, `-o` | Graphskalierung für Eingang/Ausgang, keine Geschwindigkeitsbegrenzung. |
| `F5` | Aktuelle Einstellungen in Benutzerkonfiguration speichern; echte Änderung. |
| `q` | Anzeige beenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
nload -t 1000 -a 60 -u m LERNINTERFACE
```

Das Muster würde jede Sekunde aktualisieren und den Mittelwert über 60 Sekunden berechnen. m bedeutet Mbit/s; der Großbuchstabe M wäre Byte/s. Der Interfacename bleibt Platzhalter. Es wurde keine interaktive Anzeige gestartet und insbesondere keine F5-Einstellung gespeichert.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Einheiten lernen: Rate und übertragene Menge getrennt lesen. Laufende Last beobachten: Interfaceauswahl und Zeitfenster dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Interaktive Speicherfunktionen können reale Benutzerkonfiguration verändern. Keine graphische Nullanzeige als Beweis für fehlenden Verkehr auf anderen Interfaces ausgeben. Interne Namen und Nutzungszeiten können sensible Informationen sein; hier wurden keine echten Statistiken erhoben.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Faktor 8 verschieden | Bit-/Byteeinheit prüfen. |
| Graph dauernd voll | Skalierung ist keine Bandbreitenbegrenzung. |
| Unruhige Rate | Intervall, Zählerauflösung und Mittelwertfenster prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; nload fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `bmon` | Modulare Interfaceanzeige. |
| `vnstat` | Persistente Langzeitstatistik. |
| `iperf3` | Erzeugt eigene Testlast. |

Ausgangsdatensatz 410 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
