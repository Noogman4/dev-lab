---
id: "rc_service"
name: "rc-service"
command: "rc-service"
category: "Systemd & Dienste"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd & Dienste", "rc-service"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 566
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Dienstskripte und neue Optionen offen"
---

# rc-service – OpenRC-Dienstskripte gezielt ansprechen

## 1. Kurzbeschreibung

rc-service findet ein OpenRC-Dienstskript und ruft dessen Aktion auf.

## 2. Was macht der Befehl?

Der Befehl gehört zu OpenRC, nicht pauschal zu SysV oder systemd. Die Wirkung hängt vom jeweiligen Dienstskript ab. status ist von start, stop und restart zu unterscheiden. Ausführung kann Abhängigkeiten berücksichtigen; deren Unterdrückung ist keine sichere Testoption. rc-service fehlt hier.

Quelle, am 2026-11-13 gelesen: [OpenRC: rc-service-Primärhandbuch](https://raw.githubusercontent.com/OpenRC/openrc/master/man/rc-service.8)

## 3. Syntax

```text
rc-service [OPTIONEN] DIENST AKTION
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -l | Bekannte Dienste auflisten. |
| -e DIENST | Existenz eines Dienstes prüfen. |
| -r DIENST | Pfad des Dienstskripts ermitteln. |
| -i | Bei fehlendem Dienst Erfolg melden; kann Probleme verdecken. |
| -D | Abhängigkeiten überspringen; verändert Ausführungslogik. |
| -Z | Neuere Dry-run-Variante; lokale Unterstützung zuerst prüfen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
rc-service TESTDIENST status
```

Das Muster würde das Statusverhalten eines konkreten Dienstskripts ausführen. Es wurde nicht aufgerufen; auch ein als status benannter Skriptpfad wird nicht blind als nebenwirkungsfrei angenommen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

OpenRC-Anleitungen verstehen; richtigen Dienstnamen und Skriptpfad ermitteln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Start- und Stopaktionen verändern Systembetrieb. Lokale Skripte können zusätzliche Befehle ausführen. Keine Dienstskripte gestartet und keine Abhängigkeiten geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dienst unbekannt | Auflösungsort und Init-System prüfen. |
| Status 0 trotz fehlendem Dienst | Option -i kann genau dieses Verhalten auslösen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Dienstskripte und neue Optionen offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| rc-update | OpenRC-Startzuordnungen. |
| service | Andere Dienstschnittstelle. |
| systemctl | Systemd-Schnittstelle. |

Ausgangsdatensatz 566 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
