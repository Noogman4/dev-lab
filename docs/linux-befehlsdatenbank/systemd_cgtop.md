---
id: "systemd_cgtop"
name: "systemd-cgtop"
command: "systemd-cgtop"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-cgtop"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 571
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Accountingwerte nicht praktisch geprüft"
---

# systemd-cgtop – Ressourcenverbrauch von Cgroups beobachten

## 1. Kurzbeschreibung

systemd-cgtop zeigt Ressourcenwerte für Kontrollgruppen und aktualisiert sie wiederholt.

## 2. Was macht der Befehl?

CPU, Speicher und I/O sind verschiedene Messgrößen. Verfügbare Accountingdaten hängen vom Kernel und der Gruppenkonfiguration ab. Fehlende Werte bedeuten nicht automatisch Nullverbrauch. Hier werden keine Accountingoptionen aktiviert, um Daten für eine Übung zu erzeugen.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-cgtop-Handbuch](https://man7.org/linux/man-pages/man1/systemd-cgtop.1.html); lokale Hilfe gelesen

## 3. Syntax

```text
systemd-cgtop [OPTIONEN] [CGROUP]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -b | Batchmodus ohne interaktive Bedienung. |
| -n ZAHL | Anzahl der Aktualisierungen begrenzen. |
| -m | Nach Speicherwerten ordnen. |
| -c | Nach CPU-Werten ordnen. |
| -r | Rohe Zahlen statt lesbarer Skalierung. |
| --depth=ZAHL | Anzeigetiefe begrenzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-cgtop -b -n 1
```

Eine einzige Anzeige wäre zeitlich begrenzt, würde aber echte Cgroups lesen. Sie wurde hier nicht ausgeführt. Die erste Anzeige allein wäre kein belastbarer Leistungsbenchmark.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Ressourcenübersichten vorbereiten; Gruppensummen von einzelnen Prozesswerten unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Summen verschachtelter Gruppen nicht beliebig addieren. Für fehlende Werte keine Systemkonfiguration ändern. Kein interaktiver Dauerlauf und keine Ressourcenregel angefasst.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Wert fehlt | Accountingunterstützung und Sichtbarkeit prüfen. |
| Anzeige läuft weiter | Iterationsgrenze ausdrücklich setzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Accountingwerte nicht praktisch geprüft. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemd-cgls | Mitglieder anzeigen. |
| top | Einzelprozesse. |
| systemctl | Ressourcen- und Unitinformationen. |

Ausgangsdatensatz 571 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
