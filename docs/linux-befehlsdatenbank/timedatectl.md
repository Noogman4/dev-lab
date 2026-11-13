---
id: "timedatectl"
name: "timedatectl"
command: "timedatectl"
category: "Systeminformationen"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systeminformationen", "timedatectl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 617
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# timedatectl – Zeiteinstellung von Synchronisierungszustand trennen

## 1. Kurzbeschreibung

timedatectl zeigt Zeitkonfiguration und kann Uhr, Zeitzone oder Synchronisierung ändern.

## 2. Was macht der Befehl?

RTC, Systemuhr und Zeitzonendarstellung sind verschiedene Ebenen. Aktivierter NTP-Dienst ist nicht automatisch bereits synchronisiert. show liefert auswählbare Eigenschaften; status ist für Menschen. Der Client kann reale Managerkommunikation auslösen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/timedatectl.1.html)

## 3. Syntax

```text
timedatectl [OPTIONEN] AKTION
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| status | Zeitstatus |
| show | Eigenschaften |
| -p EIGENSCHAFT | Gezielte Auswahl |
| set-time | Uhr ändern |
| set-timezone | Zeitzone ändern |
| set-ntp | Synchronisierung aktivieren oder deaktivieren |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
timedatectl show -p NTPSynchronized
```

Keine Uhr oder echter Manager abgefragt. Die Eigenschaft wäre eine Momentaufnahme, keine Garantie künftiger Genauigkeit.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Zeitfehler fachlich einordnen; Anzeige und Zeitquelle unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Uhrsprünge beeinflussen Protokolle, Zertifikate und Zeitsteuerung. Keine Zeitzone, RTC oder NTP-Konfiguration verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bus fehlt | Systemd-Umgebung prüfen |
| NTP aktiv, nicht synchron | Dienstaktivierung und Einregelung unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| date | Zeitdarstellung |
| hwclock | RTC mit Gerätewirkung |
| journalctl | Zeitbezogene Protokolle |

Ausgangsdatensatz 617 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
