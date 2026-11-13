---
id: "avahi_browse"
name: "avahi-browse"
command: "avahi-browse"
category: "NetMon Spezial / Diagnoseideen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["NetMon Spezial / Diagnoseideen", "avahi-browse"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 401
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# avahi-browse – mDNS-Dienste mit DNS-SD entdecken

## 1. Kurzbeschreibung

avahi-browse fragt über den Avahi-Daemon nach im Netz angekündigten DNS-SD-Diensten. Es öffnet die gefundenen Dienste nicht selbst. Die Anzeige kann echte Multicastanfragen auslösen und ist deshalb keine rein lokale Dateiabfrage.

## 2. Was macht der Befehl?

Ein Diensttyp wie _http._tcp ist vom Instanznamen und vom Hostnamen zu unterscheiden. Das Ergebnis beschreibt Ankündigungen, keine garantierte Erreichbarkeit oder Vertrauenswürdigkeit. + kennzeichnet neu erschienene, - verschwundene und = aufgelöste Dienste. Ohne Beendigungsoption beobachtet der Aufruf weiter. Normale Benutzer können einen passend eingerichteten Daemon nutzen; dessen Einrichtung ist ein eigener administrativer Vorgang.

Quelle, am 2026-11-13 gelesen: [Avahi-Projekthandbuch: avahi-browse](https://manpages.debian.org/trixie/avahi-utils/avahi-browse.1.en.html) und lokale Manpage

## 3. Syntax

```text
avahi-browse [OPTIONEN] DIENSTTYP
avahi-browse [OPTIONEN] --all
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-a` | Alle gefundenen Diensttypen durchsuchen, nicht nur einen. |
| `-r` | Gefundene Instanzen zusätzlich auflösen. |
| `-t` | Nach einer annähernd vollständigen Momentaufnahme beenden; kein Vollständigkeitsbeweis. |
| `-c` | Nur den vorhandenen Cache ausgeben und beenden; kein frischer Erreichbarkeitstest. |
| `-p -k` | Semikolonformat ohne sprechende Typdatenbanknamen; Escaping beachten. |
| `-l` | Lokale eigene Dienste ausblenden. |
| `-d DOMAIN` | Browsingdomain wählen; Vorgabe meist local. |
| `-f` | Bei fehlendem Daemon warten; nicht mit sofortigem Erfolg verwechseln. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
avahi-browse -r -t _http._tcp
```

Der Aufruf würde nach angekündigten Webdiensten suchen und gefundene Instanzen in Host/Port auflösen. Ein =-Eintrag wäre kein HTTP-Aufruf und kein Nachweis eines funktionierenden Webservers. Namen und TXT-Daten sind fremde Eingaben und dürfen nicht als Shellcode weiterverwendet werden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Dienstsuche verstehen: Ankündigung von tatsächlichem Verbindungsaufbau trennen. Fehlersuche planen: Domain, Interface und Daemonkontext festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Multicastverkehr erreicht andere Teilnehmer. Dienstnamen und TXT-Felder können interne Informationen enthalten oder gefälscht sein. Keine automatisch gefundenen Ziele öffnen, keine Firewall- oder Daemonkonfiguration für diese Übung ändern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Failed to connect to daemon | Dienst oder Sitzungszugriff fehlt; hier keinen Dienst starten. |
| Keine Treffer | Keine Ankündigungen sichtbar, Cache oder Netzsegment eingeschränkt; kein Beweis fehlender Geräte. |
| Skript wartet dauerhaft | Standard ist Beobachtung; -t und -c bewusst unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `avahi-resolve` | Löst konkrete Namen/Adressen auf. |
| `avahi-daemon` | Bearbeitet die mDNS-/DNS-SD-Kommunikation. |
| `getent` | Andere NSS-basierte Namenssicht. |

Ausgangsdatensatz 401 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
