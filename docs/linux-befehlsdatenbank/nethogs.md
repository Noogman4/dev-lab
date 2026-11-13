---
id: "nethogs"
name: "nethogs"
command: "nethogs"
category: "Prozesse & Jobs"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Prozesse & Jobs", "nethogs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 495
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; nethogs fehlt"
---

# nethogs – Erfassten Verkehr Prozessen zuordnen mit Sichtgrenzen

## 1. Kurzbeschreibung

nethogs erfasst Netzwerkverkehr und versucht ihn Prozessen zuzuordnen. Es benötigt Capture- und Prozesssichtrechte; ein PID-Filter macht daraus keine ausschließlich lokale Dateiabfrage.

## 2. Was macht der Befehl?

Zuordnung kann bei kurzlebigen Verbindungen, unvollständiger Prozesssicht oder wiederverwendeten PIDs scheitern. Die Anzeige ist kein vollständiger Verlauf aller Netzaktivität und kein Beweis eines schädlichen Prozesses. Mengen und Raten sind unterschiedliche Ansichten. Das gelesene Handbuch enthält eine missverständliche Einheitenzeile; konkrete Faktorannahmen werden daraus nicht übernommen.

Quelle, am 2026-11-13 gelesen: [NetHogs-Projekt: Manpage](https://manpages.debian.org/trixie/nethogs/nethogs.8.en.html)

## 3. Syntax

```text
nethogs [OPTIONEN] [INTERFACE...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-d SEKUNDEN` | Aktualisierungsintervall. |
| `-c ANZAHL` | Anzahl Aktualisierungen; 0 bedeutet unbegrenzt. |
| `-t` | Traceausgabe; weiterhin Liveerfassung. |
| `-v 2` | Gesamtbytes statt Rate; passend zur beschriebenen Variante. |
| `-P PID` | Prozessanzeige begrenzen, PID-Wiederverwendung bleibt möglich. |
| `-l` | Komplette Befehlszeilen anzeigen; sensible Argumente möglich. |
| `-p` | Promiscuous Mode; erhöht Erfassungsumfang. |
| `-a` | Auch weitere Interfaces überwachen; kein allgemeiner Schutzmodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
nethogs -t -c 2 -d 1 eth-lernen
```

Der erfundene Link wird nicht geöffnet. Zwei Aktualisierungen wären eine kurze Beobachtung mit begrenzter Aussagekraft. Auch ein nicht zugeordnetes Paket kann realer Verkehr sein. Ein späterer Test müsste Capturequelle, Prozesssicht und Einheiten getrennt dokumentieren.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Netzlast eingrenzen:** Zuordnungshinweise mit Prozessidentität und Zeitfenster abgleichen. **Daten schützen:** Nur erforderliche Metadaten erfassen und Protokolle vertraulich behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Capture kann vertrauliche Verbindungsdaten erfassen. Breite Capabilities gewähren erheblichen Zugriff; sie werden für diese Dokumentation nicht gesetzt. Ein hoher Wert berechtigt nicht zum Beenden des Prozesses. Nethogs fehlt lokal; keine Pakete erfasst oder Prozesse verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unbekannte Zuordnung | Prozessende, Rechte oder fehlende Sicht möglich. |
| PID später andere Anwendung | PID ist keine dauerhafte Identität. |
| Bytezahl als Rate gelesen | Ansichtsmodus und Intervall prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; nethogs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `iftop` | Hostpaar- statt Prozesszuordnung. |
| `ss` | Lokale Socketmomentaufnahme. |
| `tcpdump` | Paketerfassung mit anderer Detailtiefe. |

Ausgangsdatensatz 495 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
