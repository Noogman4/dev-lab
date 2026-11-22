---
id: "loginctl"
name: "loginctl"
command: "loginctl"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Systeminformationen", "loginctl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 605
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# loginctl – Sitzungen über Logind verwalten

## 1. Kurzbeschreibung

loginctl fragt Sitzungen und Benutzerzustände ab und besitzt aktive Steuerfunktionen.

## 2. Was macht der Befehl?

Sitzungs-ID, Benutzer-ID und Sitzplatz sind unterschiedliche Ziele. show-session liefert Eigenschaften; session-status ist für Menschen gedacht. terminate-session kann alle Prozesse einer Sitzung beenden. Linger verändert die Lebensdauer des Benutzermanagers über Anmeldungen hinaus.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/loginctl.1.html)

## 3. Syntax

```text
loginctl [OPTIONEN] AKTION [ZIEL ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| list-sessions | Sitzungen auflisten |
| show-session ID | Eigenschaften lesen |
| -p EIGENSCHAFT | Ausgabe begrenzen |
| --no-pager | Pager vermeiden |
| enable-linger | Dauerhafte Benutzerkonfiguration ändern |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
loginctl --no-pager show-session TESTID -p Active
```

Die ID ist ein Platzhalter; keine echte Sitzung wurde abgefragt, entsperrt, beendet oder für Linger eingerichtet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Sitzungsbegriffe verstehen; gezielte Diagnose vor aktiver Verwaltung planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Kill-, Terminate- und Lingeraktionen wirken auf Benutzer und Prozesse. Keine Rechteausweitung und keine Änderung einer laufenden Sitzung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unknown session | ID und Lebensdauer beachten |
| Nicht alle Eigenschaften | Rechte und Version prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| who | Andere Sitzungsquelle |
| w | Sitzungen und Aktivitäten |
| systemctl | Benutzermanager |

Ausgangsdatensatz 605 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
