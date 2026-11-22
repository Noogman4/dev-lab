---
id: "history"
name: "history"
command: "history"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["history", "grundlagen & hilfe"]
status: "Keine persönliche History gelesen oder verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 357
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# history – Bash-Befehlsverlauf anzeigen und Änderungen bewusst trennen

## 1. Kurzbeschreibung

`history` zeigt oder verändert den Befehlsverlauf einer Bash-Sitzung. Manche Formen lesen nur, andere löschen Einträge oder schreiben eine Datei. **Root-Rechte sind nicht nötig.**

## 2. Was macht der Befehl?

Grundlage ist die lokale Hilfe `help history`. Der Speicher der laufenden Shell und eine gespeicherte Historydatei sind verschiedene Ebenen. Mehrere Terminals können zudem unterschiedliche noch nicht gemeinsam gespeicherte Einträge besitzen.

Eine Verlaufsliste ist kein vollständiges, manipulationssicheres Ausführungsprotokoll. Einstellungen, nicht interaktive Aufrufe oder bewusste Änderungen beeinflussen, was darin steht.

## 3. Syntax

```bash
history 10
help history
```

Die erste Form würde die letzten zehn Einträge anzeigen. Sie wurde hier nicht auf die persönliche Sitzung angewendet. Gelesen wurde ausschließlich die Hilfe.

## 4. Wichtige Optionen

| Form | Wirkung | Grenze |
| --- | --- | --- |
| `history N` | Letzte N Einträge anzeigen. | Kann Geheimnisse offenlegen. |
| `-a` | Neue Sitzungseinträge anhängen. | Schreibt eine Datei. |
| `-n` | Noch nicht gelesene Dateieinträge übernehmen. | Ändert die Sitzungsliste. |
| `-r` | Datei in die Liste einlesen. | Kann Einträge ergänzen beziehungsweise verdoppeln. |
| `-w` | Aktuelle Liste speichern. | Kann vorhandene Dateiinhalte ersetzen. |
| `-d NUMMER` | Bestimmten Eintrag entfernen. | Verändert den Verlauf. |
| `-c` | Sitzungsliste leeren. | Keine universelle Geheimnislöschung. |

`HISTFILE` beeinflusst das Dateiziel. Ohne geklärten Kontext nicht beliebige Schreib- oder Löschformen an die Anzeige anhängen.

## 5. Beispiel erklärt Schritt für Schritt

Für eine eigene spätere Suche zunächst nur `history 10` betrachten. Ein Benutzer könnte darin den früher verwendeten Aufruf wiedererkennen. Nummer und Text bedeuten noch nicht, dass die Operation erfolgreich war.

Vor einer Wiederholung den vollständigen Befehl lesen. Eine alte Zeile kann heute andere Dateien treffen oder einen inzwischen unerwünschten Verwaltungsauftrag enthalten.

Dieses Beispiel bleibt eine Beschreibung. Es wurden keine tatsächlichen Befehlszeilen, Passwörter oder privaten Pfade des Benutzers eingelesen. Es wurde auch keine Testhistorie in die persönliche Liste eingetragen.

## 6. Typische Anwendungsfälle

- Einen eigenen früheren Aufruf wiederfinden.
- Zwischen mehreren eigenen Sitzungen den Speicherstand verstehen.
- Eine versehentlich sichtbare Geheimniseingabe erkennen.
- Den Unterschied zwischen Bedienhilfe und revisionsfestem Protokoll erklären.

## 7. Risiken, Nebenwirkungen und Vorsicht

Verlauf kann Token, Passwörter, private Pfade und Servernamen enthalten. Ganze Listen nicht ungeprüft weitergeben. Eine entfernte Zeile macht ein bereits offengelegtes Geheimnis nicht wieder sicher.

Schreib- und Löschoptionen können Informationen verändern oder verlieren. Insbesondere `-w` ist kein bloßer Anzeigeparameter. Automatische Wiederholung alter Zeilen kann echte Änderungen auslösen.

## 8. Häufige Fehler

- **Verlauf gleich Erfolgsbeleg:** Ergebnisstatus fehlt.
- **Eine Sitzung gleich alle Sitzungen:** Speicherstände unterscheiden sich.
- **Leeren gleich vollständige Löschung:** Andere Dateien und Mitschnitte bleiben möglich.
- **Alte Zeile blind erneut starten:** Ziele und Kontext können sich geändert haben.

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur den benötigten Ausschnitt betrachten und sensible Werte vor Weitergabe entfernen. Gefundene Aufrufe bewusst neu formulieren, statt unkontrollierte Historyexpansion zu verwenden.

Bei offengelegten Zugangsdaten ist deren Erneuerung eine eigene Maßnahme; das Entfernen einer Zeile allein löst die Offenlegung nicht.

## 10. Verwandte Befehle

- `help history`: Lokale Optionen.
- `fc`: Historybearbeitung und gegebenenfalls Ausführung; andere Wirkung.
- `set`: Shelloptionen einschließlich verlaufsbezogener Funktionen.
- `journalctl`: Systemprotokolle mit anderem Zweck.

**Prüfstand:** Nur lokale Builtinhilfe gelesen. Keine persönliche Historydatei geöffnet, geleert oder überschrieben.

Ausgangsdatensatz 357 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
