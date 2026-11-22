---
id: "systemctl_stop"
name: "systemctl stop"
command: "systemctl stop"
category: "Systemd Aufgaben"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd Aufgaben", "systemctl stop"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 587
reviewed_at: "2026-11-13"
locally_checked_version: "systemctl vorhanden; Stop und Signalwirkung offen"
---

# systemctl stop – Eine Unit geordnet deaktivieren

## 1. Kurzbeschreibung

systemctl stop fordert das Stoppen der ausgewählten Unit an.

## 2. Was macht der Befehl?

Die Wirkung hängt von Unitart, Stopkommandos und Prozessbehandlung ab. Bei Services können nach einer Schonfrist zusätzliche Signale folgen. Stop deaktiviert nicht automatisch die dauerhafte Installationszuordnung. Ein weiterhin aktiver Socket oder Timer kann später erneut aktivieren.

Quelle, am 2026-11-13 gelesen: [Systemd: Prozessbeendigung von Units](https://man7.org/linux/man-pages/man5/systemd.kill.5.html); lokal gelesenes `systemctl(1)`, Abschnitt stop

## 3. Syntax

```text
systemctl [OPTIONEN] stop UNIT ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --user | Benutzermanager wählen. |
| --no-block | Nicht auf Stopabschluss warten; kein Trockenlauf. |
| --no-ask-password | Interaktive Rechteabfrage unterdrücken. |
| UNIT | Exakte bekannte Auswahl; keine unkontrollierten Muster. |
| disable | Separate Installationsänderung, kein Synonym. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemctl stop TEST.service
```

Das Muster wurde nicht ausgeführt. Es könnte Programme beenden und Verbindungen trennen. TEST.service ist weder als vorhandenes Ziel noch als harmlose Dummyunit vorausgesetzt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Geplante Beendigung einer bekannten Unit verstehen; Stopphase und spätere Reaktivierung berücksichtigen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht gespeicherte Arbeit und laufende Clients können betroffen sein. Der Manager kann nach Zeitablauf verbliebene Prozesse beenden. Keine Stopaktion, kein Signal und keine Dienständerung getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dienst kommt wieder | Aktivierungsquelle wie Socket oder Timer separat prüfen. |
| Auftrag erfolgreich, Anwendung meldet Stopfehler | Managerabschluss und einzelne ExecStop-Diagnose unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** systemctl vorhanden; Stop und Signalwirkung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl disable | Startzuordnung ändern. |
| systemctl status | Zustand prüfen. |
| systemd.kill | Konfiguration der Prozessbeendigung. |

Ausgangsdatensatz 587 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
