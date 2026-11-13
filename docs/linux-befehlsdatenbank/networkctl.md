---
id: "networkctl"
name: "networkctl"
command: "networkctl"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "networkctl"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 435
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# networkctl – Die Sicht von systemd-networkd verstehen

## 1. Kurzbeschreibung

networkctl zeigt und verändert Links aus Sicht von systemd-networkd. Ein unmanaged-Link kann von einem anderen Dienst betreut werden; er ist dadurch nicht automatisch unbenutzbar.

## 2. Was macht der Befehl?

OPERATIONAL und SETUP sind unterschiedliche Zustandsachsen. carrier beschreibt Trägerzustand, routable einen konfigurierten routbaren Adresszustand. configured bedeutet erfolgreiche Konfiguration aus Dienstsicht. Keiner dieser Werte ist eine vollständige Prüfung von DNS, Internet oder einer Anwendung. Die aktuelle Online-Dokumentation enthält neuere Befehle als ältere installierte systemd-Versionen.

Quelle, am 2026-11-13 gelesen: [systemd: networkctl-Handbuch](https://www.freedesktop.org/software/systemd/man/latest/networkctl.html)

## 3. Syntax

```text
networkctl [OPTIONEN] {list|status} [LINK]
networkctl [OPTIONEN] KOMMANDO [LINK]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list` | Übersicht der Links und Zustände. |
| `status LINK` | Details zum ausgewählten Link. |
| `--no-pager`, `--full` | Ausgabe direkt und ohne Kürzung. |
| `--stats` | Zusätzliche Linkzähler. |
| `reload` | Konfiguration neu laden; kann Links rekonfigurieren. |
| `reconfigure LINK` | Link rekonfigurieren, lädt Dateien nicht selbst neu. |
| `up`, `down`, `delete` | Linkzustand ändern beziehungsweise virtuelle Geräte löschen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
networkctl --no-pager status eth-lernen
Erfundene Kombination: carrier / unmanaged
```

Die Kombination würde Träger, aber keine Verwaltung durch networkd beschreiben. Der erfundene Link wird nicht abgefragt. Ein fehlender networkd-Dienst wäre kein Grund, ihn nur für die Diagnose zu starten.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Zuständigkeit klären:** Kernelzustand und Verwaltungsdienst unterscheiden. **Konfiguration bewerten:** Setupstatus neben dem Betriebszustand lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

reload ist keine harmlose Dateiansicht. Erneuerung, Rekonfiguration und down können die eigene Verbindung beeinflussen. Neuere edit/mask-Befehle schreiben Konfigurationsdateien. Keine Dienste wurden gestartet, Dateien geändert oder Links abgefragt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| unmanaged | Zuständigen Manager ermitteln; nicht automatisch übernehmen. |
| routable, aber Dienst unerreichbar | Routingpfad, DNS und Anwendung getrennt prüfen. |
| Unbekannter Unterbefehl | Versionsgrenze des Handbuchs beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `systemd-networkd` | Zugehöriger Verwaltungsdienst. |
| `ip` | Kernelobjekte direkt anzeigen. |
| `nmcli` | Alternative Manageroberfläche. |

Ausgangsdatensatz 435 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
