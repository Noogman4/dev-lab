---
id: "lastlog"
name: "lastlog"
command: "lastlog"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "lastlog"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 602
reviewed_at: "2026-11-13"
locally_checked_version: "Shadow-lastlog vorhanden; --help scheiterte vor Hilfeausgabe am Auditinterface, Status 1"
---

# lastlog – Letzte Anmeldung je Konto einordnen

## 1. Kurzbeschreibung

lastlog zeigt den letzten gespeicherten Login eines Kontos, keine vollständige Sitzungsfolge.

## 2. Was macht der Befehl?

Das Shadow-Werkzeug liest üblicherweise /var/log/lastlog und Benutzerinformationen. Ein Never logged in betrifft nur diese Datenquelle. Sparse-Dateigröße und tatsächlich belegter Speicher unterscheiden sich. Neuere lastlog2-Werkzeuge sind eigene Implementierungen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man8/lastlog.8.html)

## 3. Syntax

```text
lastlog [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -u NAME | Ein Konto auswählen |
| -b TAGE | Ältere Einträge filtern |
| -t TAGE | Neuere Einträge filtern |
| -C | Eintrag löschen, keine Abfrage |
| -S | Eintrag setzen, keine Abfrage |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lastlog -u TESTKONTO
```

Die Kontoabfrage bleibt unausgeführt. Ein hier versuchter --help-Aufruf scheiterte bereits mit Cannot open audit interface und Status 1; das ist weder gelesene Programmhilfe noch Funktionstest. Es erfolgte kein privilegierter Wiederholungsversuch.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Letzte Kontonutzung von vollständiger Loginchronik unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Setz- und Löschoptionen verändern Nachweise. NSS und Auditinitialisierung können zusätzliche Schnittstellen betreffen. Keine realen Kontodaten gelesen oder verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Never logged in | Keine Aussage über andere Protokolle |
| Auditfehler | Umgebungsgrenze dokumentieren, nicht umgehen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Shadow-lastlog vorhanden; --help scheiterte vor Hilfeausgabe am Auditinterface, Status 1. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| last | Sitzungsfolge |
| lastb | Fehlversuche |
| lslogins | Weitere Konteninformationen |

Ausgangsdatensatz 602 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
