---
id: "systemd_tmpfiles"
name: "systemd-tmpfiles"
command: "systemd-tmpfiles"
category: "Systemd & Dienste"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd & Dienste", "systemd-tmpfiles"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 578
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; lokale Hilfe 255 berücksichtigt, keine Dateiregel angewendet"
---

# systemd-tmpfiles – Dateiregeln von Tmpfiles sicher einordnen

## 1. Kurzbeschreibung

systemd-tmpfiles erstellt, bereinigt oder entfernt Dateien anhand von Regeln.

## 2. Was macht der Befehl?

Der Name beschränkt das Werkzeug nicht auf harmlose temporäre Dateien. Regeltypen können Modi, Eigentum, Inhalte und Löschung betreffen. --cat-config zeigt Konfiguration; --create, --clean und --remove wenden unterschiedliche Aktionen an. Die installierte Version 255 bietet nicht automatisch jede Option neuer Onlinehandbücher.

Quelle, am 2026-11-13 gelesen: [Systemd: tmpfiles-Werkzeug](https://man7.org/linux/man-pages/man8/systemd-tmpfiles.8.html), [Regelformat tmpfiles.d](https://man7.org/linux/man-pages/man5/tmpfiles.d.5.html); lokale Hilfe gelesen

## 3. Syntax

```text
systemd-tmpfiles [OPTIONEN] [KONFIGURATION ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --cat-config | Regeldateien anzeigen statt anwenden. |
| --create | Passende Erzeugungs- und Änderungsregeln anwenden. |
| --clean | Zeitabhängige Bereinigung ausführen. |
| --remove | Entfernungsregeln anwenden. |
| --prefix=PFAD | Anzuwendende Regeln nach Präfix begrenzen; kein alleiniger Sicherheitsbeweis. |
| --user | Benutzerkonfiguration; weiterhin reale Dateiaktionen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-tmpfiles --cat-config /ABSOLUTER/EIGENER/PFAD/lesson.conf
```

Das Muster würde nur den ausgewählten Regeltext anzeigen. Es wurde nicht ausgeführt; insbesondere gab es keinen Aufruf mit --create, --clean oder --remove.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Paket-Dateiregeln verstehen; Anzeigen und Anwenden einer Konfiguration unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Regeltypen, Pfade und Globs können umfangreiche Lösch- oder Rechteänderungen verursachen. --user und --root ersetzen keine genaue Regelprüfung. Kein Cleanup und keine Änderung von Systemdateien.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Falsche Regeln gewählt | Dateiname, absolute Auswahl und Prioritäten prüfen. |
| Neuere Option unbekannt | Lokale CLI-Hilfe gilt für den installierten Stand. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; lokale Hilfe 255 berücksichtigt, keine Dateiregel angewendet. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemd-sysusers | Kontenregeln. |
| find | Dateisuche, ohne Löschen verwenden. |
| install | Gezielte Dateiinstallation. |

Ausgangsdatensatz 578 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
