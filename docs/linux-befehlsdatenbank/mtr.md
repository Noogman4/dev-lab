---
id: "mtr"
name: "mtr"
command: "mtr"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "mtr"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 433
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# mtr – Hop-Messungen ohne falsche Verlustdiagnose erklären

## 1. Kurzbeschreibung

mtr kombiniert wiederholte Laufzeitmessungen mit einer Hop-Darstellung. Es sendet aktiv Pakete; ein Reportmodus ist kein passiver Bericht über früheren Verkehr.

## 2. Was macht der Befehl?

Antwortzeiten sind Round-Trip-Zeiten einschließlich Rückweg. Router können Diagnoseantworten begrenzen oder niedriger priorisieren als weitergeleiteten Verkehr. Verlust an einem Zwischenhop allein beweist deshalb keinen Weiterleitungsverlust. Pfade können wechseln und Rückwege asymmetrisch sein. Aussagekräftige Vermutungen erfordern den Verlauf bis zum Ziel und weitere Beobachtungen.

Quelle, am 2026-11-13 gelesen: [mtr-Projekthandbuch](https://manpages.debian.org/trixie/mtr-tiny/mtr.8.en.html)

## 3. Syntax

```text
mtr [OPTIONEN] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-r` | Begrenzten Bericht erstellen und beenden. |
| `-c ANZAHL` | Messzyklen, nicht globale Höchstzahl aller Pakete. |
| `-n` | Numerische Hopanzeige, keine Rückwärtsauflösung. |
| `-4`, `-6` | Probe-IP-Familie wählen. |
| `-i SEKUNDEN` | Sendeintervall beeinflussen. |
| `--tcp`, `--udp` | Andere Probenprotokolle; eigene Filter-/Rechtebedingungen. |
| `--json` | Strukturierte Ausgabe, soweit einkompiliert. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
mtr -n -r -c 3 192.0.2.1
```

192.0.2.1 ist eine Dokumentationsadresse, kein freigegebenes Messziel. Drei Zyklen wären eine kurze, statistisch schwache Stichprobe. Ein gedachter Zwischenhop mit Verlust und ein verlustfreies Ziel erlauben keinen Schluss auf entsprechende Paketverluste des Nutzverkehrs. Das Muster wurde nicht ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Störungen eingrenzen:** Zielmessung und Hopantworten gemeinsam interpretieren. **Vergleiche vorbereiten:** Zeitpunkt, Protokoll, Ziel und Messdauer festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Jeder Lauf erzeugt Verkehr; mehrere Instanzen oder kurze Intervalle erhöhen Last. Hostnamen und AS-Lookups können zusätzliche DNS-Abfragen verursachen. Rechte können beim Hilfsprogramm mtr-packet liegen. Es wurden keine Pakete gesendet und keine Fähigkeiten am System geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| ??? oder keine Antwort | Filter/Rate-Limit möglich; Router nicht automatisch ausgefallen. |
| Hoher Zwischenhopverlust | Bis zum Ziel vergleichen; Antwortpriorität beachten. |
| Permission denied | Lokale Pakethelferkonfiguration prüfen, nicht setuid/capabilities ändern. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ping` | Laufzeit zu einem Ziel. |
| `traceroute` | Hoporientierte aktive Diagnose. |
| `ss` | Lokale Sockets ohne Hopmessung. |

Ausgangsdatensatz 433 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
