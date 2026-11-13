---
id: "ltrace"
name: "ltrace"
command: "ltrace"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "ltrace"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 494
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; ltrace fehlt"
---

# ltrace – Bibliotheksaufrufe beobachten heißt Programm ausführen

## 1. Kurzbeschreibung

ltrace startet ein Programm unter Beobachtung oder hängt sich an einen vorhandenen Prozess. Es protokolliert dynamische Bibliotheksaufrufe und gegebenenfalls Systemaufrufe. Das Zielprogramm läuft dabei tatsächlich.

## 2. Was macht der Befehl?

Bibliotheksaufruf und Kernel-Systemaufruf sind verschiedene Ebenen. Statisch gelinkte, inline ausgeführte oder anders gebundene Funktionen können der normalen Bibliothekssicht entgehen. Argumentdarstellung hängt von Prototypbeschreibungen ab. Eine fehlende Zeile ist deshalb kein Beweis, dass eine Funktion oder Wirkung nie vorkam.

Quelle, am 2026-11-13 gelesen: [ltrace-Projekt: Manpage](https://man7.org/linux/man-pages/man1/ltrace.1.html)

## 3. Syntax

```text
ltrace [OPTIONEN] [--] BEFEHL [ARGUMENTE]
ltrace [OPTIONEN] -p PID
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-e FILTER` | Welche Bibliotheksaufrufe verfolgt/angezeigt werden. |
| `-S` | Systemaufrufe zusätzlich anzeigen. |
| `-p PID` | An vorhandenen Prozess anhängen; echte Beobachtung mit Rechtebedingungen. |
| `-f` | Kindprozessen folgen; erweitert Umfang. |
| `-o DATEI` | Protokoll in Datei schreiben. |
| `-s ANZAHL` | Maximal angezeigte Stringlänge; keine Datenzugriffsisolation. |
| `-c` | Aufruf-/Zeitstatistik statt Einzelprotokoll. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ltrace -o ./eigene-spur.txt -- /usr/bin/printf "Lerntext\n"
```

Das Muster wurde nicht ausgeführt, weil ltrace fehlt. Es würde printf wirklich starten und eine neue Spurdatei schreiben; Bibliotheksnamen und Aufrufanzahl wären buildabhängig. Es ist keine statische Analyse eines Programmfiles.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Abläufe untersuchen:** Nur eindeutig eigenen kleinen Testcode unter Beobachtung starten. **Spuren lesen:** Traceebene und fehlende Funktionsprototypen als Grenzen erfassen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Anhängen verändert Timing und kann sensible Argumente offenlegen. Tracingrechte beziehungsweise ptrace-Restriktionen nicht durch Systemkonfiguration umgehen. Fremde Programme können während des Trace beliebige eigene Nebenwirkungen haben. Keine Prozesse angehängt oder Programme unter ltrace gestartet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not permitted | Tracingrichtlinie oder Rechte begrenzen Zugriff. |
| Keine erwarteten Calls | Statische Bindung, Inlinecode oder Filter möglich. |
| Argumente unplausibel | Prototypbeschreibung und ABI prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; ltrace fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `strace` | Vor allem Kernel-Systemaufrufe. |
| `perf` | Andere Mess-/Samplingverfahren. |
| `lsof` | Offene Referenzen statt Aufrufverlauf. |

Ausgangsdatensatz 494 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
