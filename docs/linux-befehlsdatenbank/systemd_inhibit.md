---
id: "systemd_inhibit"
name: "systemd-inhibit"
command: "systemd-inhibit"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-inhibit"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 574
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Sperren und Managerzugriff nicht getestet"
---

# systemd-inhibit – Inhibitor-Sperren als Systemwirkung verstehen

## 1. Kurzbeschreibung

systemd-inhibit kann für die Laufzeit eines Befehls eine Sperre gegen bestimmte Systemaktionen halten.

## 2. Was macht der Befehl?

Der Befehl erwirbt die Sperre vor dem Programmstart und gibt sie danach frei. Das kann etwa Ruhemodus oder Herunterfahren beeinflussen. --list ist von einem neuen Sperrauftrag zu unterscheiden. Rechte, Sperrart und entgegenwirkende administrative Aktionen bestimmen die tatsächliche Wirkung.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-inhibit-Handbuch](https://man7.org/linux/man-pages/man1/systemd-inhibit.1.html)

## 3. Syntax

```text
systemd-inhibit [OPTIONEN] BEFEHL [ARGUMENTE]
systemd-inhibit --list
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --list | Vorhandene Inhibitoren anzeigen. |
| --what=ARTEN | Betroffene Aktionen wie sleep oder shutdown. |
| --mode=block oder delay | Blockieren oder zeitlich verzögern; Grenzen beachten. |
| --who=TEXT | Urheberbeschreibung. |
| --why=TEXT | Begründung der Sperre. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-inhibit --list
```

Das Muster würde den laufenden Manager nach bestehenden Sperren fragen. Es wurde nicht ausgeführt. Insbesondere wurde keine neue Sperre erworben.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Eine spätere Wartungssperre fachlich planen; Grund und Geltungsbereich vorhandener Sperren verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auch eine nur für ein eigenes Programm gehaltene Sperre beeinflusst das Gesamtsystem. --user-ähnliche Erwartungen nicht auf dieses Werkzeug übertragen. Kein Schlaf-, Shutdown- oder Idle-Verhalten geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Zugriff verweigert | Policy und Sessionkontext prüfen, keine Rechte erweitern. |
| System schläft trotzdem | Sperrart, zuständige Aktion und administrative Übersteuerung beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Sperren und Managerzugriff nicht getestet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| loginctl | Sitzungsmanager. |
| systemctl | Systemaktionen. |
| systemd-run | Programm über Manager ausführen. |

Ausgangsdatensatz 574 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
