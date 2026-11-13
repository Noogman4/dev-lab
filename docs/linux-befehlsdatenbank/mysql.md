---
id: "mysql"
name: "mysql"
command: "mysql"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "mysql"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 519
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Verbindung und SQL offen"
---

# mysql – MySQL über einen Client ansprechen

## 1. Kurzbeschreibung

mysql ist ein SQL-Client; ein Aufruf startet nicht automatisch den Datenbankserver.

## 2. Was macht der Befehl?

Host, Benutzer und Datenbank legen die Verbindung fest. Optionsdateien können zusätzliche Einstellungen oder Startbefehle liefern. Die Client-Rechte auf dem Betriebssystem sind von Datenbankrollen getrennt. SELECT 1 ist ein kleines Abfragemuster, eine echte Verbindung wäre trotzdem ein Serverzugriff. mysql fehlt lokal.

Quelle, am 2026-11-13 gelesen: [MySQL 8.4: Client Options](https://dev.mysql.com/doc/refman/8.4/en/mysql-command-options.html)

## 3. Syntax

```text
mysql [OPTIONEN] [DATENBANK]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --host HOST | Verbindungsziel auswählen. |
| --user BENUTZER | Datenbankkonto. |
| -p | Kennwort interaktiv erfragen; keines als Argument hinterlegen. |
| --execute SQL | Anweisung ausführen und beenden. |
| --batch | Nichtinteraktive Ausgabe. |
| --no-defaults | Optionsdateien begrenzen; muss an der vorgeschriebenen frühen Position stehen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
mysql --host=TESTSERVER --user=LESEKONTO -p --execute='SELECT 1;' TESTDATENBANK
```

Vor einer Ausführung wären ein freigegebener Testserver, begrenzte Datenbankrechte und kontrollierte Client-Konfiguration erforderlich. Die Ausgabe 1 ist nur das erwartete SQL-Ergebnis, kein hier gemessener Wert.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

SQL-Abfragen an einer ausdrücklich gewählten Datenbank; Client- und Authentisierungsfehler verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Kennwörter in Argumenten oder URI können in Prozessliste und Historie sichtbar sein. SQL kann Daten dauerhaft ändern; --safe-updates ist keine vollständige Schreibsperre. Keine Verbindung hergestellt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Access denied | Datenbankkonto, Hostzuordnung und Authentisierung prüfen. |
| Connection refused | Ziel und Transport prüfen; keinen Server eigenmächtig starten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Verbindung und SQL offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mysqld | Serverprozess. |
| psql | PostgreSQL-Client. |
| sqlite3 | Lokale SQLite-Kommandozeile. |

Ausgangsdatensatz 519 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
