---
id: "journalctl_u"
name: "journalctl -u"
command: "journalctl -u"
category: "Systemd Aufgaben"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd Aufgaben", "journalctl -u"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 581
reviewed_at: "2026-11-13"
locally_checked_version: "journalctl vorhanden; Unitfilter praktisch offen"
---

# journalctl -u – Journal auf eine Unit begrenzen

## 1. Kurzbeschreibung

journalctl -u ist eine Filteraufgabe von journalctl; nach -u muss eine Unit oder ein Muster stehen.

## 2. Was macht der Befehl?

Ein Unitfilter ist umfassender als eine Suche nach dem Unitnamen im Nachrichtentext. Er berücksichtigt passende strukturierte Felder und zugehörige Managermeldungen. System- und Benutzerunits verwenden unterschiedliche Kontexte. Ein leerer Trefferbereich beweist keine fehlerfreie Anwendung.

Quelle, am 2026-11-13 gelesen: [Systemd: journalctl-Unitfilter](https://man7.org/linux/man-pages/man1/journalctl.1.html); lokale CLI-Hilfe gelesen

## 3. Syntax

```text
journalctl -u UNIT [WEITERE OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -u UNIT | Systemunit auswählen; wiederholbar. |
| --user-unit=UNIT | Benutzerunit gezielt auswählen. |
| -b | Auf den aktuellen Boot begrenzen, wenn ohne ID verwendet. |
| --since ZEIT | Zeituntergrenze. |
| -n ZAHL | Begrenzte Zahl letzter Einträge. |
| --no-pager | Keine interaktive Seitendarstellung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
journalctl --no-pager -b -u TEST.service -n 20
```

Das Muster würde höchstens 20 passende Einträge aus dem aktuellen Boot zeigen. Es wurde weder eine Unit angelegt noch eine Journalabfrage ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Gezielte Dienstdiagnose vorbereiten; strukturierte Filter statt bloßer Textsuche verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine unnötig breite Logsammlung weitergeben. Zeitbasis, Rotation, Rechte und Namespace können den sichtbaren Ausschnitt beschränken. Es wird kein Protokoll geschrieben oder gelöscht.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Option requires argument | Unitname nach -u fehlt. |
| Keine Einträge | Unitart, Boot, Zeitraum und Sichtbarkeit prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** journalctl vorhanden; Unitfilter praktisch offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| journalctl -f | Neue Einträge verfolgen. |
| journalctl | Weitere Filter. |
| systemctl status | Zustand und kurzer Logausschnitt. |

Ausgangsdatensatz 581 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
