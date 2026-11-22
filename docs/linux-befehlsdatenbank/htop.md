---
id: "htop"
name: "htop"
command: "htop"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "htop"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 486
reviewed_at: "2026-11-13"
locally_checked_version: "htop 3.3.0: lokale Hilfe gelesen; keine Monitorfunktion praktisch geprüft"
---

# htop – Prozessansicht mit ausdrücklich begrenzter Bedienung

## 1. Kurzbeschreibung

htop ist eine interaktive Prozessansicht. Neben Anzeigen kann es Signale senden und Prioritäten ändern. Markierte Prozesse können gemeinsam Ziel einer Aktion werden.

## 2. Was macht der Befehl?

Prozess, Thread und Prozessbaum sind verschiedene Darstellungen. CPU-Prozentwerte hängen von Ansicht und Normierung ab; Speicherwerte können gemeinsam genutzte Seiten enthalten. Sortierung verändert Positionen, daher ist eine Bildschirmzeile keine stabile Prozessidentität. Die aktuelle Online-Manpage enthält neuere Funktionen als manche Distributionspakete.

Quelle, am 2026-11-13 gelesen: [htop-Projekt: Manpage](https://manpages.debian.org/trixie/htop/htop.1.en.html) und lokale htop-Hilfe

## 3. Syntax

```text
htop [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-p PID,PID...` | Angezeigte PIDs auswählen. |
| `-u [BENUTZER]` | Benutzerfilter, je lokaler Syntax. |
| `-d ZAHL` | Aktualisierungsabstand in Zehntelsekunden, nicht Sekunden. |
| `-t` | Prozessbaum anzeigen. |
| `-s SPALTE` | Sortierung wählen. |
| `--readonly` | In unterstützten Versionen System-/Prozessänderungsfunktionen deaktivieren. |
| `F9`, `F7`, `F8` | Signal- beziehungsweise Prioritätsaktionen; nicht als Anzeige behandeln. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
htop --readonly -p EIGENE_TEST_PID -d 20
```

Der Platzhalter muss durch eine eigens erzeugte und überprüfte Test-PID ersetzt werden; hier erfolgt kein Start. 20 bedeutet zwei Sekunden. --readonly darf nur benutzt werden, wenn die lokale Hilfe es bestätigt; Ablehnung nicht durch ungeprüften Normalstart umgehen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Ressourcen verstehen:** Threadanzeige, Prozessbaum und Sortierung bewusst wählen. **TUI-Bedienung planen:** Anzeige von Signal-/Prioritätsfunktionen trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Auswahl oder Mehrfachmarkierung kann mehrere Prozesse betreffen. Einstellungen können in Benutzerdateien gespeichert werden. Keine Oberfläche gestartet, keine Signale oder Prioritätsänderungen und keine Benutzerkonfiguration verändert. Nur lokale Hilfe gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| PID fehlt | Prozess bereits beendet, falscher Namensraum oder Filter. |
| Zeile bewegt sich | Sortiermomentaufnahme, keine stabile Identität. |
| Readonly unbekannt | Versionsgrenze; keinen echten Prozess ohne passenden Schutz starten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** htop 3.3.0: lokale Hilfe gelesen; keine Monitorfunktion praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ps` | Gezielte Momentaufnahme. |
| `btop` | Andere Ressourcen-TUI. |
| `pgrep` | Gezielte Prozessauswahl. |

Ausgangsdatensatz 486 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
