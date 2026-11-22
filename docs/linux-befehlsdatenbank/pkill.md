---
id: "pkill"
name: "pkill"
command: "pkill"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Prozesse & Jobs", "pkill"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 501
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# pkill – Prozesse anhand eines Musters signalisieren

## 1. Kurzbeschreibung

pkill sucht passende Prozesse und sendet ihnen ein Signal. Schon ein Aufruf ohne Signaloption kann Programme beenden.

## 2. Was macht der Befehl?

Die procps-ng-Implementierung verwendet standardmäßig SIGTERM. Der Name ist ein regulärer Ausdruck, kein festes Dateimuster. Mehrere Auswahlkriterien werden gemeinsam angewendet. Prozessnamen sind in der üblichen /proc-Darstellung auf 15 Zeichen begrenzt; die vollständige Befehlszeile ist eine andere Datenquelle. Ein passender Name beweist weder Besitz noch Zweck eines Prozesses.

Quelle, am 2026-11-13 gelesen: [procps-ng-Handbuch pgrep/pkill](https://man7.org/linux/man-pages/man1/pgrep.1.html)

## 3. Syntax

```text
pkill [SIGNALOPTION] [AUSWAHLOPTIONEN] MUSTER
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -TERM | SIGTERM an ausgewählte Prozesse; keine reine Abfrage. |
| -x | Gesamten Namen beziehungsweise mit -f die gesamte Befehlszeile passend verlangen. |
| -f | Vollständige Befehlszeile als Suchtext; dadurch anderer, oft größerer Trefferbereich. |
| -P PID | Auf direkte Kinder dieses Elternprozesses beschränken. |
| -u UID | Nach effektiver Benutzerkennung filtern. |
| -e | Signalisierte Prozesse ausgeben; keine Vorschau. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
pgrep -a -P EIGENE_SHELL_PID -x lernprozess
pkill -TERM -P EIGENE_SHELL_PID -x lernprozess
```

Die erste Zeile wäre eine lesende Vorprüfung. Die zweite würde passende direkte Kinder tatsächlich signalisieren. Zwischen beiden Abfragen kann sich der Prozessbestand ändern; eine Vorschau beseitigt dieses Rennen nicht. Beide Zeilen bleiben hier unausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Gezielt einen zuvor identifizierten eigenen Arbeitsprozess beenden; Signalauswahl in administrativen Abläufen erklären. Für reine Bestandslisten pgrep verwenden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Breite Muster oder -f können fremde beziehungsweise wichtige Prozesse erfassen. SIGTERM kann Datenverlust verursachen; SIGKILL verhindert geregeltes Aufräumen. Benutzer- und Prozessgruppenfilter ersetzen keine eindeutige Identitätsprüfung. Keine Signale an laufende Benutzerprozesse getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Treffer / Status 1 | Muster, Namenslänge und Auswahl prüfen; nicht blind breiter suchen. |
| Operation not permitted | Signalrechte fehlen; nicht vorsorglich sudo einsetzen. |
| Status 0 | Mindestens eine erfolgreiche Signalisierung; kein Beweis für das gewünschte fachliche Ende aller Ziele. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pgrep | Treffer lesend suchen. |
| kill | Signal an bereits bestimmte PID senden. |
| ps | Prozessidentität und Elternbeziehung prüfen. |

Ausgangsdatensatz 501 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
