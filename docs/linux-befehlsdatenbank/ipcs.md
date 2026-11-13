---
id: "ipcs"
name: "ipcs"
command: "ipcs"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "ipcs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 598
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; IPC-Bestand nicht abgefragt"
---

# ipcs – System-V-IPC-Bestand lesend anzeigen

## 1. Kurzbeschreibung

ipcs zeigt Informationen zu System-V-IPC-Ressourcen im sichtbaren Namespace.

## 2. Was macht der Befehl?

Standardmäßig werden Shared Memory, Queues und Semaphore berücksichtigt. Die Anzeige ist keine vollständige POSIX-IPC-Inventur. Mit -i wird eine konkrete Objekt-ID zusammen mit ihrer Ressourcenart gewählt. Sichtbarkeit und Detailumfang hängen von Kernel, /proc und Berechtigungen ab.

Quelle, am 2026-11-13 gelesen: [util-linux: ipcs-Handbuch](https://man7.org/linux/man-pages/man1/ipcs.1.html); lokale Hilfe gelesen

## 3. Syntax

```text
ipcs [RESSOURCENOPTION] [AUSGABEOPTION]
ipcs -m oder -q oder -s -i ID
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -m | Shared-Memory-Segmente. |
| -q | Nachrichtenqueues. |
| -s | Semaphorgruppen. |
| -i ID | Details zu einem Objekt der gewählten Art. |
| -c | Ersteller und Eigentümer. |
| -l | Ressourcenlimits statt Objektinhalt. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ipcs -m -i EIGENE_BESTAETIGTE_SHMID
```

Das Muster würde eine zuvor bekannte eigene Segment-ID abfragen. Es ist nicht ausgeführt worden. Es wird keine beliebige vorhandene ID als Testziel verwendet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Objektarten und Kennungen verstehen; eine gezielte spätere IPC-Diagnose vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Objektnamen, Besitzer und PIDs können vertraulich sein. Eine Momentaufnahme legitimiert keine anschließende Entfernung. Alte IDs können ungültig werden. Keine IPC-Ressource gelesen, angelegt oder gelöscht.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| ID fehlt | Ressourcenart zusammen mit -i angeben. |
| Andere Prozesse nicht sichtbar | IPC-Namespace und Rechte berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; IPC-Bestand nicht abgefragt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ipcrm | Entfernung mit deutlich anderer Wirkung. |
| lsipc | Andere Anzeige. |
| ipcmk | Anlage ist keine lesende Diagnose. |

Ausgangsdatensatz 598 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
