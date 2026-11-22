---
id: "iotop"
name: "iotop"
command: "iotop"
category: "Prozesse & Jobs"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Prozesse & Jobs", "iotop"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 489
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; iotop fehlt"
---

# iotop – I/O-Zähler nicht mit sofortigem Gerätetransfer verwechseln

## 1. Kurzbeschreibung

iotop zeigt prozess-/threadbezogene I/O-Messwerte. Hier ist die Python-iotop-Variante des gelesenen Handbuchs beschrieben; iotop-c kann unter demselben Namen eine andere Oberfläche liefern.

## 2. Was macht der Befehl?

Prozess-I/O und aktueller Gerätetransfer unterscheiden sich durch Cache und zeitversetztes Schreiben. Akkumulierte Mengen seit Monitorstart sind keine Datenrate. Fehlende Kernel-Accountingfunktionen oder Rechte begrenzen die Messung. Eine leere Ansicht kann auch aus der Auswahl nur aktuell aktiver Tasks entstehen.

Quelle, am 2026-11-13 gelesen: [iotop-Projekt: Manpage der Python-Variante](https://manpages.debian.org/trixie/iotop/iotop.8.en.html)

## 3. Syntax

```text
iotop [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-b` | Batchmodus statt interaktiver Oberfläche. |
| `-n ANZAHL` | Messiterationen begrenzen. |
| `-d SEKUNDEN` | Intervall festlegen. |
| `-p PID` | Taskauswahl einschränken. |
| `-P` | Prozesse statt einzelner Threads. |
| `-o` | Nur aktuell I/O-aktive Einträge. |
| `-a` | Akkumulierte Menge seit Start statt Bandbreite. |
| `i` interaktiv | I/O-Priorität ändern, keine Anzeigeaktion. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
iotop -b -n 2 -d 1 -p EIGENE_TEST_PID
```

Das Muster wird nicht ausgeführt und setzt einen eigens erzeugten Task voraus. Zwei Abtastungen belegen keine langfristige Last. Für neuere Kernel kann task_delayacct erforderlich sein; diese Voraussetzung wird hier nicht durch einen Sysctl-Eingriff hergestellt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**I/O-Berichte verstehen:** Menge, Rate und Warteanteile trennen. **Voraussetzungen bewerten:** Accounting- und Rechtegrenzen offen benennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Liveabfragen benötigen abhängig von Variante/Kernel besondere Rechte. Aktivieren von Accounting verändert das System und kann Aufwand erzeugen. Keine Kernelparameter gesetzt, keine Capture-/Adminrechte erweitert und kein Monitor gestartet. Iotop fehlt lokal.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Accounting deaktiviert | Prüfpunkt offen lassen, keinen Sysctl setzen. |
| Total ungleich Current | Cache und I/O-Neuordnung berücksichtigen. |
| Prozess fehlt bei -o | Vielleicht im Intervall nicht I/O-aktiv. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; iotop fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ionice` | I/O-Attribute lesen/ändern. |
| `pidstat` | Andere Prozess-Intervallmessung. |
| `iostat` | Gerätebezogene andere Ebene. |

Ausgangsdatensatz 489 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
