---
id: "systemd_notify"
name: "systemd-notify"
command: "systemd-notify"
category: "Systemd & Dienste"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systemd & Dienste", "systemd-notify"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 575
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; keine Benachrichtigung versandt"
---

# systemd-notify – Dienstbereitschaft an den Manager melden

## 1. Kurzbeschreibung

systemd-notify übermittelt Statusinformationen eines Dienstes an den Service-Manager.

## 2. Was macht der Befehl?

--ready meldet Bereitschaft; es startet keinen Dienst. Ob die Nachricht akzeptiert und zugeordnet wird, hängt vom Benachrichtigungskanal, dem Dienstkontext und NotifyAccess ab. Eine bloße Erfolgsanzeige eines Shellbefehls beweist keine korrekt implementierte Bereitschaftslogik der Anwendung.

Quelle, am 2026-11-13 gelesen: [Systemd: systemd-notify-Handbuch](https://man7.org/linux/man-pages/man1/systemd-notify.1.html); lokale Hilfe gelesen

## 3. Syntax

```text
systemd-notify [OPTIONEN] [VARIABLE=WERT ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --ready | READY=1 melden. |
| --status=TEXT | Statusbeschreibung übermitteln. |
| --stopping | Beginnende Beendigung melden. |
| --reloading | Beginnende Konfigurationsneuladung melden. |
| --no-block | Bestätigung nicht abwarten; kann Zuordnungsrennen begünstigen. |
| --pid=PID | Prozesszuordnung beeinflussen; Rechte und Version beachten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-notify --ready --status='Eigener Dienst bereit'
```

Das Muster gehört ausschließlich in einen dafür eingerichteten Dienstkontext. Es wurde nicht ausgeführt und kein READY-Zustand an einen realen Manager gesendet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Benachrichtigende Dienste verstehen; Anwendungsbereitschaft vom bloßen Prozessstart unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Bereitschaftsmeldungen können abhängige Abläufe zu früh starten. NOTIFY_SOCKET nicht auf fremde Ziele setzen. Privilegierte Prozesszuordnung nicht für einen Test benutzen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| NOTIFY_SOCKET fehlt | Kein eingerichteter Benachrichtigungskontext. |
| Nachricht ignoriert | Zuordnung, Lebensdauer und NotifyAccess prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; keine Benachrichtigung versandt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| systemd.service | Type=notify und Dienstkonzept. |
| systemctl | Unitzustände. |
| systemd-cat | Logeinträge statt Bereitschaft. |

Ausgangsdatensatz 575 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
