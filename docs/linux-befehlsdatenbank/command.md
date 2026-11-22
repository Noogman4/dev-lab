---
id: "command"
name: "command"
command: "command"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["command", "grundlagen & hilfe"]
status: "Auflösungsregeln dokumentiert; kein fremder Befehl gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 349
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# command – Befehle abfragen oder ohne Funktionswrapper aufrufen

## 1. Kurzbeschreibung

`command` ist ein Shell-Builtin zum Abfragen oder Ausführen eines Befehls. Bei der Ausführung wird die normale Suche nach gleichnamigen Shellfunktionen unterdrückt. **Root-Rechte sind nicht nötig.**

## 2. Was macht der Befehl?

Grundlage ist die lokale Hilfe `help command`. `command -v NAME` beschreibt, wie der Name verfügbar ist. `command NAME` führt dagegen eine Aktion aus.

Die Ausführung bleibt an Shell- und Suchpfadregeln gebunden. Das Vorsetzen von `command` bestätigt weder Eigentümer noch Integrität einer gefundenen Datei. Es ist keine allgemeine Absicherung gegen einen kontrollierten `PATH`.

## 3. Syntax

```bash
command -v printf
command -V printf
command printf '%s\n' 'Hallo NetMon'
```

Die ersten beiden Formen fragen ab; die dritte führt das gefundene beziehungsweise eingebaute `printf` aus. Eine solche Unterscheidung muss auch eine spätere Oberfläche erhalten.

## 4. Wichtige Optionen

| Option | Zweck | Aussagegrenze |
| --- | --- | --- |
| `-v` | Kurze Namensbeschreibung. | Muss kein absoluter Dateipfad sein. |
| `-V` | Ausführlichere Beschreibung. | Menschenlesbare Form nicht blind maschinell zerlegen. |
| `-p` | Vordefinierten Suchpfad verwenden. | Kein Nachweis für vertrauenswürdige Dateiinhalte. |

Ein Builtin kann gefunden werden, obwohl keine gleichnamige Datei benötigt wird. Deshalb ein Ergebnis nicht pauschal als ausführbaren Dateipfad behandeln.

## 5. Beispiel erklärt Schritt für Schritt

```bash
if command -v printf >/dev/null 2>&1; then
  command printf '%s\n' 'Ausgabe verfügbar'
fi
```

Die erste Zeile fragt nach Verfügbarkeit. Das feste Format behandelt die Nachricht als Daten. Die zweite Aktion wäre eine Ausgabe; sie ist nicht Bestandteil der bloßen Verfügbarkeitsprüfung.

Der Beispielablauf wurde nicht als eigener Lauf ausgeführt. Er basiert auf der lokalen Builtin-Hilfe. Persönliche Funktionsdefinitionen oder Suchpfade wurden nicht verändert.

Für sicherheitsrelevante privilegierte Aufrufe genügt dieser Aufbau allein nicht: Dann müssen Programmidentität, Umgebung und die am Ziel verwendete Identität zum Sicherheitskonzept passen.

## 6. Typische Anwendungsfälle

- Optionale Werkzeuge auf Verfügbarkeit prüfen.
- Einen gleichnamigen Funktionswrapper gezielt umgehen.
- Eine kurze Diagnose zur Namensauflösung anzeigen.
- Skripte mit einem dokumentierten Standardsuchpfad vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ohne Abfrageoption wird der nachfolgende Befehl wirklich ausgeführt. Eine Zeile wie `command VERWALTUNGSBEFEHL ...` bleibt ein Verwaltungsauftrag.

Ein kontrollierter `PATH` kann weiterhin eine unerwünschte Datei auswählen. Eine Verfügbarkeitsprüfung beweist außerdem nicht, dass das spätere Ziel unverändert dieselbe Datei ist. Keine Sicherheitsgarantie daraus ableiten.

## 8. Häufige Fehler

- **Abfrage mit Ausführung verwechseln:** `-v` beziehungsweise `-V` beachten.
- **Ausgabe immer als Pfad lesen:** Builtins sind möglich.
- **`command` als absolute Vertrauensprüfung:** Prüft keine Dateiintegrität.
- **Nach Verfügbarkeit jede Option voraussetzen:** Version und Fähigkeiten bleiben getrennt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für die erste Orientierung nur `command -v NAME` nutzen. Für detaillierte Bash-Auflösung ist `type -a NAME` hilfreich.

In eigenen Skripten zwischen „vorhanden“, „unterstützt benötigte Funktion“ und „geeignet vertrauenswürdig“ unterscheiden. Diese Aussagen benötigen unterschiedliche Belege.

## 10. Verwandte Befehle

- `type`: Bash-Auflösung ausführlicher betrachten.
- `builtin`: Eingebaute Funktion ausdrücklich ausführen.
- `which`: Externe PATH-Suche mit anderen Grenzen.
- `help command`: Lokale Builtin-Hilfe.

**Prüfstand:** Lokale Hilfe gelesen. Kein Programm über einen fremden Suchpfad ausgeführt und keine Herkunftsgarantie behauptet.

Ausgangsdatensatz 349 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
