---
id: "lxc_stop"
name: "lxc-stop"
command: "lxc-stop"
category: "Virtualisierung"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Virtualisierung", "lxc-stop"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 694
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Stop-/Signalwirkung offen"
---

# lxc-stop – Containerstop und erzwungene Beendigung unterscheiden

## 1. Kurzbeschreibung

lxc-stop fordert die Beendigung eines klassischen LXC-Containers an.

## 2. Was macht der Befehl?

Im Standardablauf wird zunächst ein konfiguriertes Halt-Signal an Init gesendet und gewartet; nach Zeitablauf kann erzwungene Beendigung folgen. -r ist Neustart, keine Statusabfrage. Signalvorgaben können in der Containerkonfiguration abweichen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://linuxcontainers.org/lxc/manpages/man1/lxc-stop.1.html)

## 3. Syntax

```text
lxc-stop -n NAME [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n NAME | Zielcontainer |
| -t SEKUNDEN | Wartefrist |
| -k | Sofortige harte Beendigung |
| --nokill | Nach Frist nicht hart töten |
| -r | Neustart |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lxc-stop -n EIGENER_FREIGEGEBENER_CONTAINER --nokill -t 5
```

Nicht ausgeführt; auch --nokill sendet im vorgesehenen Ablauf eine echte Beendigungsanforderung.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Geordnetes Herunterfahren von hartem Abbruch unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Verbindungen, ungesicherte Daten und laufende Dienste sind betroffen. Keine Signale und kein Containerzustand verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Stop dauert | Init und konfigurierte Signale berücksichtigen |
| Nicht beendet | Keine automatische Eskalation zum harten Kill |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Stop-/Signalwirkung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lxc-start | Start |
| lxc-ls | Bestand |
| systemctl stop | Andere Dienstebene |

Ausgangsdatensatz 694 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
