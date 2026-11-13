---
id: "renice"
name: "renice"
command: "renice"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "renice"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 506
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# renice – Nice-Werte laufender Prozesse ändern

## 1. Kurzbeschreibung

renice verändert die Scheduling-Gewichtung bereits laufender Prozesse.

## 2. Was macht der Befehl?

Ein höherer Nice-Wert bedeutet geringere Bevorzugung bei CPU-Konkurrenz. Der Wert ist keine feste Prozentquote und keine Echtzeitpriorität. util-linux verwendet bei -n üblicherweise einen absoluten Zielwert; POSIXLY_CORRECT kann die Interpretation relativ machen. Neuere Langoptionen sind nicht auf jeder installierten Version verfügbar.

Quelle, am 2026-11-13 gelesen: [util-linux renice-Handbuch](https://man7.org/linux/man-pages/man1/renice.1.html)

## 3. Syntax

```text
renice -n WERT -p PID
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n WERT | Zielwert; Umgebungs- und Implementierungsunterschiede beachten. |
| -p | Folgende Kennungen als PIDs behandeln. |
| -g | Prozessgruppen auswählen; breiter Änderungsbereich. |
| -u | Alle passenden Benutzerprozesse auswählen. |
| --version | Version ohne Prioritätsänderung lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
renice -n 10 -p EIGENE_TEST_PID
```

Unter üblicher util-linux-Umgebung würde ein eigener Testprozess Nice 10 erhalten. Dafür müssten PID und bisheriger Wert sicher festgestellt sein. Die Zeile wurde nicht ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

CPU-intensive eigene Hintergrundaufgaben bei Konkurrenz zurückstellen; eine bereits gestartete Aufgabe nach gesonderter Freigabe anders gewichten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unprivilegierte Benutzer können meist nur eigene Prozesse weniger bevorzugen. Ein späteres Zurücksetzen kann Rechte oder passende Limits erfordern. -u und -g können viele Prozesse verändern. Keine bestehende Priorität verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Permission denied | Eigentum, CAP_SYS_NICE und Ressourcenlimits prüfen. |
| Unerwarteter Wert | Absolute und relative Interpretation sowie POSIXLY_CORRECT vergleichen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| nice | Neue Befehle mit Nice-Wert starten. |
| ps | Nice-Wert anzeigen. |
| taskset | CPU-Zulässigkeit statt Gewichtung. |

Ausgangsdatensatz 506 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
