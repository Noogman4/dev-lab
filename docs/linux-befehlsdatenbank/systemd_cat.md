---
id: "systemd_cat"
name: "systemd-cat"
command: "systemd-cat"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-cat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 569
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Journaltransport nicht getestet"
---

# systemd-cat – Programmausgabe ins Journal schreiben

## 1. Kurzbeschreibung

systemd-cat leitet Eingaben oder Programmausgaben an das systemd-Journal.

## 2. Was macht der Befehl?

Ohne Programm liest es die Standardeingabe. Mit Programmargument wird das Programm tatsächlich gestartet und seine Ausgabe mit dem Journal verbunden. Dies ist ein schreibender Protokollierungsvorgang, keine Anzeige vorhandener Logs. stdout und stderr können unterschiedlich priorisiert werden.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-cat-Handbuch](https://man7.org/linux/man-pages/man1/systemd-cat.1.html)

## 3. Syntax

```text
systemd-cat [OPTIONEN] [BEFEHL [ARGUMENTE]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -t KENNUNG | Journal-Identifier festlegen. |
| -p PRIORITÄT | Priorität für Eingabe beziehungsweise Standardausgabe. |
| --stderr-priority=STUFE | Priorität der Fehlerausgabe. |
| --level-prefix=BOOL | Prioritätspräfixe aus dem Eingabetext berücksichtigen oder ignorieren. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-cat -t EIGENE_KENNUNG printf TESTTEXT
```

Der Musteraufruf würde printf starten und einen echten Journaleintrag schreiben. Genau deshalb wurde er hier nicht ausgeführt; TESTTEXT ist kein beobachteter Logeintrag.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Loggingpfade eigener später freigegebener Programme verstehen; Ausgabe und Journaltransport unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Protokolle können dauerhaft gespeichert oder weitergeleitet werden. Keine Kennwörter oder Testspam einspeisen. Auch das gestartete Programm behält alle eigenen Nebenwirkungen. Kein Journaleintrag erzeugt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Journal-Socket fehlt | Passende Journalingumgebung nicht vorhanden. |
| Nichts auf Terminal | Ausgabe geht absichtlich ins Journal. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Journaltransport nicht getestet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| journalctl | Gespeicherte Einträge lesen. |
| logger | Andere Protokollierungsschnittstelle. |
| systemd-run | Programme über Manager starten. |

Ausgangsdatensatz 569 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
