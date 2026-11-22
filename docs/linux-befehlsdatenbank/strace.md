---
id: "strace"
name: "strace"
command: "strace"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "strace"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 507
reviewed_at: "2026-11-13"
locally_checked_version: "strace 6.8; nur Versionsaufruf"
---

# strace – Systemaufrufe eines Programms beobachten

## 1. Kurzbeschreibung

strace protokolliert Systemaufrufe und empfangene Signale eines Programms.

## 2. Was macht der Befehl?

Beim Programmaufruf wird das Ziel wirklich ausgeführt; -p hängt sich an einen bestehenden Prozess. Ein Trace zeigt die Schnittstelle zum Kernel, keine vollständige Erklärung der Anwendungslogik. Einträge mit ENOENT können reguläre Suchversuche sein. Die Beobachtung beeinflusst Laufzeit und kann Zeitfehler verändern.

Quelle, am 2026-11-13 gelesen: [strace-Projekthandbuch](https://man7.org/linux/man-pages/man1/strace.1.html)

## 3. Syntax

```text
strace [OPTIONEN] BEFEHL [ARGUMENTE]
strace [OPTIONEN] -p PID
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -e trace=SYSCALLS | Kommagetrennte Auswahl tatsächlicher Systemaufrufnamen. |
| -e trace=openat,read,close | Konkrete Auswahl von Systemaufrufen. |
| -o PFAD | Trace in Datei schreiben; vorhandene Datei kann überschrieben werden. |
| -f | Neu erzeugten Kindern folgen. |
| -c | Zusammenfassung statt einzelner Ereignisse. |
| -s ZAHL | Maximale angezeigte Zeichenkettenlänge; keine Datenschutzgarantie. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
strace -e trace=openat,read,close -o EIGENER_NEUER_PFAD cat EIGENE_TESTDATEI
```

Ein späterer isolierter Versuch würde cat starten und ausgewählte Dateiaufrufe protokollieren. Trace und Programmausgabe wären getrennt zu prüfen. Das Funktionsmuster bleibt unausgeführt; nur die lokale Hilfe wurde gelesen.

### Schritt 3: Aussagegrenze festhalten

Ein Hilfe-/Versionsaufruf wird unten gesondert belegt. Er bestätigt nur die lokale Schnittstelle, nicht den Ablauf des Musters.

## 6. Typische Anwendungsfälle

Fehlende Dateien oder Zugriffsprobleme einer eigenen Anwendung analysieren; Systemaufrufe im Unterricht erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Trace-Dateien können Inhalte, Pfade und Geheimnisse enthalten. ptrace-Schutz nicht umgehen. Injektions- und Fault-Optionen verändern Verhalten aktiv und sind keine reine Beobachtung. Keine Prozesse angehängt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not permitted | Sandbox, Yama oder ptrace-Rechte verhindern Beobachtung. |
| Viele Fehler im Trace | Fehlgeschlagene Suchversuche vom tatsächlichen Anwendungsfehler unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** strace 6.8; nur Versionsaufruf. Praktisch geprüft: Nur Hilfe/Version ausgeführt; Beispiel, echte Netz-/Geräte-/Sitzungszugriffe und zustandsändernde Modi nicht praktisch geprüft. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ltrace | Bibliotheksaufrufe beobachten. |
| ps | Prozess zuerst identifizieren. |
| perf | Andere Leistungsdiagnose mit eigenen Rechten. |

Ausgangsdatensatz 507 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
