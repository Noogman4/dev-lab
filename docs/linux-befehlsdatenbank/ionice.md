---
id: "ionice"
name: "ionice"
command: "ionice"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "ionice"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 488
reviewed_at: "2026-11-13"
locally_checked_version: "ionice / util-linux 2.39.3"
---

# ionice – I/O-Priorität der eigenen Shell nur lesen

## 1. Kurzbeschreibung

ionice zeigt und setzt I/O-Schedulingklasse und -Priorität. Die reine Form -p PID ohne neue Klasse oder Prioritätsstufe liest Attribute; ein Programmoperand startet dagegen ein Programm.

## 2. Was macht der Befehl?

I/O-Priorität und CPU-Nice-Wert sind verschiedene Eigenschaften. Best-effort und Realtime besitzen Stufen 0–7, wobei kleinere Zahlen höhere Priorität bedeuten. Idle hat keine solche Stufe. Die Wirkung hängt auch vom verwendeten I/O-Scheduler ab; die erfolgreiche Attributanzeige beweist keine bestimmte Bandbreiten- oder Latenzwirkung.

Quelle, am 2026-11-13 gelesen: [util-linux: ionice-Handbuch](https://man7.org/linux/man-pages/man1/ionice.1.html)

## 3. Syntax

```text
ionice -p PID
ionice [-c KLASSE] [-n STUFE] BEFEHL [ARGUMENTE]
ionice [-c KLASSE] [-n STUFE] -p PID
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-p PID` | Bestehenden Task auswählen; ohne Setzwerte lesen. |
| `-c KLASSE` | None, Realtime, Best-effort oder Idle setzen. |
| `-n 0..7` | Klassenabhängige Stufe, nicht CPU-Nice. |
| `-P PGID`, `-u UID` | Breitere Prozessgruppen-/Benutzerauswahl. |
| `-t` | Setzfehler ignorieren und Programm trotzdem starten; kein zuverlässiger Erfolgsbeweis. |
| `--version` | Werkzeugstand anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
ionice --version
LC_ALL=C ionice -p "$$"
```

### Schritt 3: Ergebnis einordnen

$$ ist die eigene neue Bash-Test-Shell. Die angezeigte geerbte Klasse ist umgebungsabhängig. Es wird weder -c noch -n angegeben, also nichts gesetzt. Kein I/O-Lastgenerator und kein echtes Gerät ist Teil des Tests. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Prioritäten verstehen:** Gespeichertes Attribut von realer Schedulerwirkung trennen. **Diagnose eingrenzen:** Exakte eigene PID statt breiter Benutzer-/Gruppenauswahl.

## 7. Risiken, Nebenwirkungen und Vorsicht

Hohe I/O-Priorität kann andere Arbeit verdrängen. Rechte und Schedulerunterstützung variieren. Keine Prioritätsklasse, Prozessgruppe, Limits oder Systemkonfiguration verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| None angezeigt | Kein explizit gesetztes Attribut, nicht automatisch kein I/O. |
| Keine messbare Wirkung | Scheduler und Workload beeinflussen die Wirkung. |
| Programm lief trotz Setzfehler | -t kann genau dies erlauben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** ionice / util-linux 2.39.3. Praktisch geprüft: Nur ionice -p auf eigener Test-Shell ausgeführt. Keine Klasse oder Priorität geändert. I/O-Schedulerwirkung, Last-, Geräte- und Rechtefälle praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `nice` | CPU-Nice statt I/O-Klasse. |
| `chrt` | CPU-Schedulerpolicy. |
| `iotop` | I/O-Messwerte mit weiteren Voraussetzungen. |

Ausgangsdatensatz 488 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
