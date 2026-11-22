---
id: "psql"
name: "psql"
command: "psql"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "psql"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 520
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Serverzugriffe offen"
---

# psql – PostgreSQL mit psql bedienen

## 1. Kurzbeschreibung

psql ist ein Terminalclient für PostgreSQL mit SQL und eigenen Metabefehlen.

## 2. Was macht der Befehl?

SQL wird an den Server gesendet; Backslash-Befehle werden im Client ausgewertet und können auch Dateien oder Shellkommandos betreffen. -c und -f führen Anweisungen tatsächlich aus. Ohne ausdrückliche Ziele können Umgebungsvariablen die Verbindung beeinflussen. psql fehlt lokal.

Quelle, am 2026-11-13 gelesen: [PostgreSQL: psql-Handbuch](https://www.postgresql.org/docs/current/app-psql.html)

## 3. Syntax

```text
psql [OPTIONEN] [DATENBANK [BENUTZER]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -h HOST, -p PORT | Server beziehungsweise Socketverzeichnis und Port. |
| -U BENUTZER, -d DATENBANK | Datenbankidentität auswählen. |
| -X | Keine persönliche psql-Startdatei lesen. |
| -c BEFEHL | SQL oder einen einzelnen Metabefehl ausführen. |
| -v ON_ERROR_STOP=1 | Bei Skriptfehlern anhalten. |
| -f DATEI | Datei mit Befehlen ausführen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
psql -X -h TESTSERVER -U LESEKONTO -d TESTDATENBANK -v ON_ERROR_STOP=1 -c 'SELECT 1;'
```

Ein späterer freigegebener Verbindungsversuch würde Startdateien vermeiden und einen einfachen SQL-Ausdruck auswerten. Die Zeile bleibt unausgeführt; sie beweist keine vorhandene Datenbank.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

SQL in einer gewählten Testdatenbank untersuchen; automatisierte Abfragen mit bewusstem Fehlerverhalten vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Metabefehle sind kein reines SQL und können lokale Nebenwirkungen haben. Zugangsdaten nicht in URI veröffentlichen. Ein Clientstatus allein ersetzt keine Prüfung der Datenbanktransaktion. Keine Verbindung oder Transaktion ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Role/database does not exist | Standardnamen nicht mit tatsächlich eingerichtetem Konto verwechseln. |
| Skript läuft nach SQL-Fehler weiter | ON_ERROR_STOP und Transaktionskonzept prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Serverzugriffe offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| postgres | Server. |
| mysql | Anderer SQL-Client. |
| sqlite3 | Serverlose Datenbankdatei. |

Ausgangsdatensatz 520 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
