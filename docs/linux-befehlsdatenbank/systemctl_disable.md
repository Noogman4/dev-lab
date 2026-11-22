---
id: "systemctl_disable"
name: "systemctl disable"
command: "systemctl disable"
category: "Systemd Aufgaben"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd Aufgaben", "systemctl disable"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 582
reviewed_at: "2026-11-13"
locally_checked_version: "systemctl vorhanden; keine Linkänderung"
---

# systemctl disable – Startverknüpfungen einer Unit deaktivieren

## 1. Kurzbeschreibung

systemctl disable verändert die Installationszuordnung einer Unit, stoppt sie standardmäßig aber nicht.

## 2. Was macht der Befehl?

Die Aufgabenform gehört zum Programm systemctl. Betroffene Verknüpfungen können auch manuell angelegt worden sein; disable ist daher nicht immer die genaue Umkehr eines früheren enable. Also=-Verknüpfungen und andere Aktivierungswege sind mitzudenken. Eine deaktivierte Unit kann weiterhin anderweitig gestartet werden.

Quelle, am 2026-11-13 gelesen: Lokal gelesenes Systemd-255-Handbuch `systemctl(1)`, Abschnitt disable, und CLI-Hilfe; [Primärhandbuch online](https://man7.org/linux/man-pages/man1/systemctl.1.html)

## 3. Syntax

```text
systemctl [OPTIONEN] disable UNIT ...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --user | Benutzerkontext; weiterhin Änderung. |
| --runtime | Nur Laufzeitkonfiguration, keine Trockenübung. |
| --now | Zusätzlich stoppen; erweitert die Wirkung. |
| --no-reload | Implizites Einlesen durch den Manager unterdrücken; Linkänderung bleibt. |
| is-enabled UNIT | Separate Zustandsabfrage als Alternative. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemctl disable TEST.service
```

Die Zeile würde reale Startlinks entfernen und bleibt deshalb unausgeführt. Keine Service-Datei wurde angelegt und kein späterer Bootzustand verändert.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Eine später freigegebene Startkonfigurationsänderung planen; Laufzustand und Aktivierung auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Aktive Socket-, Timer- oder Abhängigkeitsaktivierung kann den Dienst weiter starten. disable ist keine Zugriffssperre wie mask. --now könnte laufende Arbeit unterbrechen. Kein Dienst deaktiviert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dienst läuft weiter | Ohne --now erwartbar; Laufzustand getrennt betrachten. |
| Startet später trotzdem | Andere Aktivierungswege und globalen Benutzerkontext prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** systemctl vorhanden; keine Linkänderung. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl enable | Installationszuordnung herstellen. |
| systemctl stop | Aktuell deaktivieren. |
| systemctl mask | Stärkere Startsperre mit eigenem Risiko. |

Ausgangsdatensatz 582 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
