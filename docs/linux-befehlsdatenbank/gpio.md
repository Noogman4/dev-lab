---
id: "gpio"
name: "gpio"
command: "gpio"
category: "Raspberry Pi"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Raspberry Pi", "gpio"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 529
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Hardware und elektrische Wirkung ungeprüft"
---

# gpio – WiringPi-GPIO-Befehle richtig zuordnen

## 1. Kurzbeschreibung

gpio bezeichnet hier das WiringPi-Werkzeug für Raspberry-Pi-GPIOs; der Name ist keine universelle Linux-GPIO-Schnittstelle.

## 2. Was macht der Befehl?

WiringPi-, BCM- und physische Pin-Nummern sind unterschiedliche Nummerierungen. Dieselbe Zahl kann einen anderen Anschluss meinen. Unterstützte Modelle und Zugriffswege hängen von WiringPi-Version und Board ab. gpio darf nicht mit raspi-gpio, pinctrl oder libgpiod gleichgesetzt werden.

Quelle, am 2026-11-13 gelesen: [WiringPi: gpio-Quelltext mit Nutzungshilfe](https://raw.githubusercontent.com/WiringPi/WiringPi/master/gpio/gpio.c)

## 3. Syntax

```text
gpio [-g oder -1] UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -g | BCM-Nummerierung verwenden. |
| -1 | Physische Steckplatznummern verwenden. |
| readall | Pinübersicht; trotzdem Hardwarezugriff. |
| read PIN | Pegel lesen. |
| mode PIN MODUS | Pinmodus ändern. |
| write PIN WERT | Ausgangspegel setzen; echte elektrische Wirkung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
gpio -h
```

Nur ein nicht ausgeführtes Hilfemuster. Kein Pin wurde gelesen, umgeschaltet oder elektrisch angesteuert. Vor realem Einsatz sind Schaltung und Nummerierung zu klären.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Historische WiringPi-Anleitungen einordnen; Pin-Nummerierungen vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Pegel oder Moduswechsel können angeschlossene Geräte beeinflussen und bei ungeeigneter Beschaltung beschädigen. Beispielwerte nie blind auf Hardware übertragen. Kein gpio installiert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Falscher Pin reagiert | Nummerierung -g/-1 und Standardmodus vergleichen. |
| Board nicht unterstützt | Konkrete WiringPi-Version und Hardware abgleichen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Hardware und elektrische Wirkung ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| pinout | Belegungsdiagramm. |
| pinctrl | Separates Raspberry-Pi-Werkzeug. |
| gpioget | Separates libgpiod-Werkzeug. |

Ausgangsdatensatz 529 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
