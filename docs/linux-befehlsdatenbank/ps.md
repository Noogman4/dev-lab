---
id: "ps"
name: "ps"
command: "ps"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "ps"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 504
reviewed_at: "2026-11-13"
locally_checked_version: "procps-ng 4.0.4"
---

# ps – Einen Prozess als Momentaufnahme anzeigen

## 1. Kurzbeschreibung

ps zeigt ausgewählte Prozessinformationen zu einem bestimmten Zeitpunkt.

## 2. Was macht der Befehl?

Die procps-ng-Version versteht mehrere Optionsfamilien. Unix-Optionen mit Bindestrich und BSD-Optionen ohne Bindestrich können Auswahl und Darstellung unterschiedlich beeinflussen. Mehrere Auswahloptionen bilden häufig eine Vereinigung, keine Schnittmenge. Deshalb wählt die Übung genau eine PID und legt ihre Spalten ausdrücklich fest.

Quelle, am 2026-11-13 gelesen: [procps-ng ps-Handbuch](https://man7.org/linux/man-pages/man1/ps.1.html)

## 3. Syntax

```text
ps [OPTIONEN]
ps -p PID -o SPALTEN
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p PID | Prozess nach numerischer PID auswählen. |
| -o FORMAT | Gewünschte Spalten wie pid,ppid,stat,comm. |
| -e | Alle sichtbaren Prozesse auswählen. |
| -L | Threads anzeigen. |
| --sort SCHLÜSSEL | Ausgabe nach einem unterstützten Feld sortieren. |
| aux | Gängige BSD-Kombination; nicht mit -aux gleichsetzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
probe_dir=$(mktemp -d) || exit 1
cd "$probe_dir" || exit 1
ps --version
ps -p "$$" -o pid=,ppid=,stat=,comm= > process.txt
cat process.txt
awk -v pid="$$" '$1 == pid {found=1} END {exit !found}' process.txt
printf 'Eigene PID gefunden
'
```

### Schritt 3: Ergebnis einordnen

Die Tabelle enthält die eigene Übungsshell mit Eltern-PID, Zustand und kurzem Befehlsnamen. Ein laufender Prozess kann während der Abfrage schlafen; STAT ist keine dauerhafte Zustandszusage. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

PID und Elternbeziehung prüfen; ein bekanntes Programm identifizieren; kompakte Diagnoseausgaben mit festen Feldern erstellen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Vollständige Argumentlisten können Zugangsdaten enthalten. Die Prozessliste kann sich sofort nach der Abfrage ändern. Sichtbarkeit in Namespaces und /proc-Schutz ist begrenzt. Keine Prozesssteuerung findet statt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nur wenige Prozesse | Standardauswahl und sichtbaren PID-Namespace prüfen. |
| Unerwartete Treffer | Auswahloptionen können additiv wirken. |
| Andere Spalten | Format ausdrücklich mit -o setzen; Skripte nicht auf Bildschirmbreite aufbauen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** procps-ng 4.0.4. Praktisch geprüft: Eigene PID und vier Felder geprüft; andere Auswahlfamilien und Rechtefälle offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pstree | Prozessbeziehungen als Baum. |
| top | Wiederholte Beobachtung. |
| pgrep | PID-Suche nach Kriterien. |

Ausgangsdatensatz 504 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
