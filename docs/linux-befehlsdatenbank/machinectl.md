---
id: "machinectl"
name: "machinectl"
command: "machinectl"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "machinectl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 565
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Maschinenmanager und Images ungeprüft"
---

# machinectl – Registrierte Maschinen und Container verwalten

## 1. Kurzbeschreibung

machinectl steuert den systemd-Maschinenmanager und kann Informationen zu registrierten Instanzen liefern.

## 2. Was macht der Befehl?

Registrierte laufende Maschinen und gespeicherte Images sind unterschiedliche Objekte. Das Werkzeug ist keine universelle Verwaltung aller Virtualisierungsprodukte. list und show unterscheiden sich von start, shell, poweroff oder remove, die reale Aktionen auslösen können. machinectl fehlt lokal.

Quelle, am 2026-11-13 gelesen: [Systemd: machinectl-Handbuch](https://man7.org/linux/man-pages/man1/machinectl.1.html)

## 3. Syntax

```text
machinectl [OPTIONEN] UNTERBEFEHL [NAME ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| list | Registrierte laufende Maschinen auflisten. |
| list-images | Verfügbare Images auflisten. |
| show NAME | Eigenschaften gezielt lesen. |
| status NAME | Für Menschen gedachte Statusdarstellung. |
| --no-pager | Pager vermeiden. |
| shell / start / remove | Aktive Ausführung oder Änderung; kein Lesemodus. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
machinectl --no-pager show TESTMASCHINE
```

Die nicht ausgeführte Abfrage würde eine bereits registrierte freigegebene Instanz betreffen. TESTMASCHINE ist ein Platzhalter; es wurde keine Maschine gestartet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Maschinenregistrierung von Images unterscheiden; eine gezielte Diagnose vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Shellstart kann in einem anderen Benutzer- oder Maschinenkontext ausführen. Entfernen eines Images ist destruktiv. Polkit- und Managerzugriff nicht für eine Leseübung erweitern.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Manager nicht erreichbar | systemd-machined und Umgebung prüfen, nicht starten. |
| Name fehlt | Registrierung und Imagebestand getrennt betrachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Maschinenmanager und Images ungeprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemd-run | Transiente Einheiten. |
| systemctl | Dienstmanager. |
| systemd-detect-virt | Eigene Laufumgebung erkennen. |

Ausgangsdatensatz 565 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
