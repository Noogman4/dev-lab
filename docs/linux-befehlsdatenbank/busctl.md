---
id: "busctl"
name: "busctl"
command: "busctl"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "busctl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 563
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; kein funktionaler D-Bus-Test"
---

# busctl – D-Bus-Schnittstellen gezielt untersuchen

## 1. Kurzbeschreibung

busctl kann D-Bus-Namen und Schnittstellen anzeigen, Methoden aufrufen sowie Eigenschaften setzen.

## 2. Was macht der Befehl?

Buswahl, Dienstname, Objektpfad und Interface sind getrennte Adressen. list fragt Namen ab; call und set-property können echte Aktionen auslösen. Eine Introspektion beschreibt eine Schnittstelle, bestätigt aber keine gefahrlose Methodenausführung. Automatische Aktivierung eines Zieldienstes ist zusätzlich zu beachten.

Quelle, am 2026-11-13 gelesen: [Systemd: busctl-Handbuch](https://man7.org/linux/man-pages/man1/busctl.1.html); lokale Programmhilfe gelesen

## 3. Syntax

```text
busctl [OPTIONEN] UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --system / --user | Systembus oder Benutzerbus auswählen. |
| list | Namen am gewählten Bus auflisten. |
| introspect DIENST OBJEKT | Schnittstelle eines Objekts abfragen. |
| call | Methode mit passender D-Bus-Signatur aufrufen. |
| --auto-start=no | Automatische Aktivierung des Zielnamens unterbinden. |
| --no-pager | Keinen Pager starten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
busctl --user --no-pager list
```

Das Muster würde den realen Benutzerbus abfragen. Es ist hier bewusst nicht ausgeführt worden. Eine Namensliste wäre noch kein Nachweis für die Bereitschaft sämtlicher Dienste.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Adressierung und Datentypen in vorhandenen D-Bus-Diagnosen verstehen; gezielte Abfragen vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Monitor- und Captureausgaben können vertrauliche Nachrichten enthalten. Methoden sind keine bloßen Texte. Systembuszugriff und Polkitrechte nicht pauschal erweitern. Keine Busverbindung hergestellt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Failed to connect to bus | Passender Bus und Sitzung fehlen möglicherweise. |
| Invalid signature | D-Bus-Datentypen und Argumentreihenfolge prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; kein funktionaler D-Bus-Test. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemctl | Dienstmanager über eigene Schnittstelle. |
| systemd-notify | Separater Benachrichtigungskanal. |
| dbus-send | Anderer D-Bus-Client. |

Ausgangsdatensatz 563 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
