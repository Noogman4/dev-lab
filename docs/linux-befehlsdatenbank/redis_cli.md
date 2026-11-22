---
id: "redis_cli"
name: "redis-cli"
command: "redis-cli"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "redis-cli"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 522
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Redis-Verbindung offen"
---

# redis-cli – Redis-Kommandos bewusst an einen Server senden

## 1. Kurzbeschreibung

redis-cli ist der Kommandozeilenclient für Redis. Der nachgestellte Redis-Befehl entscheidet über Lesen oder Schreiben.

## 2. Was macht der Befehl?

Ohne ausdrückliches Ziel kann der Client einen lokalen Standardserver ansprechen. Eine andere Datenbanknummer ist keine Sicherheitsgrenze. TLS und Authentisierung sind getrennt zu konfigurieren. PING prüft eine Antwort des Servers, nicht die Unversehrtheit seiner Daten. redis-cli fehlt lokal.

Quelle, am 2026-11-13 gelesen: [Redis: CLI-Handbuch](https://redis.io/docs/latest/develop/tools/cli/)

## 3. Syntax

```text
redis-cli [OPTIONEN] [REDIS-BEFEHL [ARGUMENTE]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -h HOST, -p PORT | Verbindungsziel wählen. |
| -n NUMMER | Logische Datenbank auswählen. |
| --tls | TLS verwenden; Zertifikatsvertrauen passend einrichten. |
| --cacert DATEI | Vertrauenswürdiges CA-Zertifikat. |
| --raw | Rohdarstellung von Antworten. |
| -x | Letztes Befehlsargument aus Standardeingabe; kann Schreibdaten liefern. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
redis-cli -h TESTSERVER -p TESTPORT --tls --cacert EIGENE_CA_DATEI PING
```

Das Muster ist eine unausgeführte Verbindungsübung. PONG wäre eine erwartete, hier nicht gemessene Antwort. Ein freigegebener Server und passende ACL-Rechte wären erforderlich.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Gezielte Redis-Abfragen vorbereiten; Clientantwort und Transportfehler auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

FLUSHALL und FLUSHDB löschen Daten; -n schützt nicht vor FLUSHALL. URI, Argumente und Historie können Geheimnisse offenlegen. Wiederholungs- und Massenmodi können Server belasten. Keine Verbindung hergestellt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| NOAUTH / NOPERM | Authentisierung und ACL-Zulassung getrennt prüfen. |
| Connection refused | Ziel prüfen, keinen Redis-Dienst starten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Redis-Verbindung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| redis-server | Serverprozess. |
| psql | SQL-Client. |
| ss | Listener lesend prüfen, falls gesondert beauftragt. |

Ausgangsdatensatz 522 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
