---
id: "killall"
name: "killall"
command: "killall"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Prozesse & Jobs", "killall"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 492
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# killall – Namensauswahl kann viele Prozesse treffen

## 1. Kurzbeschreibung

killall aus Linux-psmisc signalisiert passende Prozesse nach Kommandonamen. Es bedeutet nicht kontrolliertes Beenden genau einer Anwendung. Andere Betriebssysteme können unter diesem Namen deutlich andere Programme anbieten.

## 2. Was macht der Befehl?

Ohne Signalangabe wird TERM verwendet. Ein regulärer Ausdruck oder Benutzerfilter erweitert die Auswahl; -g betrifft Prozessgruppen. Bei langen Namen begrenzt die verfügbare Prozessnameninformation die Eindeutigkeit. Ein Name allein ist kein Eigentums- oder Auftragsnachweis.

Quelle, am 2026-11-13 gelesen: [psmisc: killall-Manpage](https://manpages.debian.org/trixie/psmisc/killall.1.en.html)

## 3. Syntax

```text
killall [OPTIONEN] NAME...
killall --list
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--list`, `-l` | Nur bekannte Signalnamen ausgeben. |
| `--signal NAME`, `-s NAME` | Gewünschtes Signal. |
| `--interactive`, `-i` | Vor Signalisierung fragen; keine Simulation. |
| `--exact`, `-e` | Unvollständig verfügbare lange Namen nicht nur nach kurzem Präfix treffen. |
| `--regexp`, `-r` | Namen als reguläre Ausdrücke interpretieren. |
| `--process-group`, `-g` | Prozessgruppen signalisieren. |
| `--wait`, `-w` | Kann bei ignorierten Signalen oder Zombies unbegrenzt warten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
killall --list
```

Das Muster ist eine reine Namensliste und wurde nicht als Signaltest ausgeführt. Keine konkrete Prozessauswahl wird als kopierfertiger Beendigungsauftrag angegeben. Ein späterer praktischer Test müsste ausschließlich eigens erzeugte Prozesse eindeutig abgrenzen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Anleitungen prüfen:** Namensfilter, Gruppe und Signal getrennt lesen. **Eingriffe planen:** Vor einer echten Aktion konkrete Prozessidentitäten und Folgen prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Breite Namen, Regex und -u können mehrere wichtige Programme treffen. -i bestätigt einen Eingriff und ist kein Dry-run. Nach erfolgreichem Senden kann ein Prozess weiterlaufen. Keine Prozesse ausgewählt, signalisiert oder beendet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Mehrere Instanzen getroffen | Auswahl war namensbezogen, nicht PID-eindeutig. |
| Langer Name unklar | -e verhindert bestimmte Präfixtreffer, ersetzt aber keine Identitätsprüfung. |
| -w endet nicht | Zombie/ignoriertes Signal möglich; keine automatische KILL-Folge. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `kill` | Explizite PID-/Signalwahl. |
| `pgrep` | Prozesse zunächst nur auswählen. |
| `pkill` | Andere signalgebende Filteroberfläche. |

Ausgangsdatensatz 492 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
