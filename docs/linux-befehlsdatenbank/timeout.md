---
id: "timeout"
name: "timeout"
command: "timeout"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "timeout"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 510
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# timeout – Einen neu gestarteten Befehl zeitlich begrenzen

## 1. Kurzbeschreibung

timeout startet einen Befehl und kann ihn nach Ablauf einer Frist signalisieren.

## 2. Was macht der Befehl?

GNU timeout sendet bei Fristüberschreitung üblicherweise SIGTERM. Eine zweite Frist mit -k kann SIGKILL nachschicken. Ein Timeout macht Nebenwirkungen des gestarteten Programms nicht rückgängig. Deshalb prüft die Übung nur einen Befehl, der selbständig vor der Frist endet.

Quelle, am 2026-11-13 gelesen: Lokal gelesene Primärquelle: GNU-coreutils-Programmhilfe `timeout --help`; [Projektverweis](https://www.gnu.org/software/coreutils/) (Onlineabruf fehlgeschlagen)

## 3. Syntax

```text
timeout [OPTIONEN] DAUER BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| DAUER | Zahl mit optional s, m, h oder d; 0 deaktiviert die Frist. |
| -s SIGNAL | Signal bei Fristablauf auswählen. |
| -k DAUER | Zusätzliche Wartezeit bis SIGKILL. |
| --preserve-status | Programmstatus auch bei Fristablauf übernehmen. |
| --foreground | Terminalzugriff ermöglichen; Kinder werden in diesem Modus nicht mit begrenzt. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
timeout --version | head -n 1
timeout 3s bash --noprofile --norc -c 'printf "Vor Fristende fertig\n"'
```

### Schritt 3: Ergebnis einordnen

Der eigene printf-Befehl endet regulär mit Status 0. Der Fristablauf wurde nicht ausgelöst und die Signalwirkung somit nicht funktional geprüft. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Eigene automatisierte Diagnosebefehle begrenzen; Hänger mit ausdrücklich geprüfter Aufräumstrategie behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Abbruch kann Dateien unvollständig hinterlassen. Ein ignoriertes TERM und nicht erfasste Kinder können den erwarteten Ablauf verändern. Keine realen Benutzerprogramme und kein erzwungener Abbruch getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Status 124 | Frist überschritten, sofern --preserve-status nicht aktiv. |
| Status 125, 126 oder 127 | Fehler von timeout, nicht ausführbares oder fehlendes Programm unterscheiden. |
| Status 137 | SIGKILL erhalten; Herkunft genauer untersuchen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: Nur reguläres Ende vor Frist geprüft; Fristablauf und Signale nicht getestet. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| time | Dauer messen. |
| wait | Auf eigene Kinder warten. |
| kill | Signale gezielt behandeln. |

Ausgangsdatensatz 510 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
