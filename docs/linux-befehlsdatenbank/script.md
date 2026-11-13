---
id: "script"
name: "script"
command: "script"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "script"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 634
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3; nur Version, Aufzeichnung offen"
---

# script – Terminalaufzeichnung als aktive Ausführung verstehen

## 1. Kurzbeschreibung

script startet einen Terminalkontext und zeichnet dessen Ausgabe beziehungsweise optional Eingabe auf.

## 2. Was macht der Befehl?

Ohne expliziten Befehl kann eine interaktive Shell starten. -c führt eine Befehlszeichenfolge aus. Ausgabelog und Timinglog sind unterschiedliche Daten. Eingabeprotokollierung kann auch Kennwörter erfassen, selbst wenn das Terminal sie nicht sichtbar ausgibt.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/script.1.html)

## 3. Syntax

```text
script [OPTIONEN] [AUSGABEDATEI]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c BEFEHL | Tatsächlich ausführen |
| -O DATEI | Ausgabelog |
| -T DATEI | Timinglog |
| -I DATEI | Eingabelog, sensibel |
| -e | Kindstatus zurückgeben |
| -a | An Log anhängen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
script -c FESTER_EIGENER_BEFEHL -O NEUES_LOG -T NEUES_TIMING
```

Keine Shell aufgezeichnet und kein Pseudoterminal gestartet. Platzhalter sind kein geprüfter Probelauf.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Aufzeichnungskonzepte vor einer bewusst freigegebenen Sitzung verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausführung hat alle Nebenwirkungen des Programms. Logs können Geheimnisse und Terminalsteuerzeichen enthalten. Keine vorhandenen Logdateien überschreiben.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Hängt | Interaktive Shell wartet |
| Passwort im Log | Eingabeprotokollierung ist kein Datenschutzmodus |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** util-linux 2.39.3; nur Version, Aufzeichnung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| scriptreplay | Logwiedergabe |
| tee | Einfache Ausgabekopie |
| bash | Shellkontext |

Ausgangsdatensatz 634 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
