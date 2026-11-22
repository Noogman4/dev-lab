---
id: "yarn"
name: "yarn"
command: "yarn"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "yarn"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 474
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; yarn fehlt"
---

# yarn – Yarn Classic und moderne Yarn-Versionen nicht mischen

## 1. Kurzbeschreibung

yarn ist eine JavaScript-Projektverwaltung mit mehreren deutlich verschiedenen CLI-Generationen. Yarn 1 Classic und moderne Yarn-Versionen haben unterschiedliche Befehle, Konfigurationen und Installationsmodelle.

## 2. Was macht der Befehl?

Classic dokumentiert list, während aktuelle Anleitungen andere Informationsbefehle verwenden. Moderne Installationen durchlaufen Auflösung, Fetch, Link und Build. Ein unveränderliches Lockfile verhindert nicht automatisch alle Dateischreibvorgänge oder Codeausführung. Die Projektkonfiguration kann eine bestimmte Yarn-Version und Plugins auswählen; der bloße Aufrufname reicht zur Einordnung nicht.

Quelle, am 2026-11-13 gelesen: [Yarn: aktuelles install-Handbuch](https://yarnpkg.com/cli/install) und [Yarn Classic: list](https://classic.yarnpkg.com/en/docs/cli/list)

## 3. Syntax

```text
yarn KOMMANDO [OPTIONEN]
Yarn 1 Classic: yarn list --depth=0
Modern: yarn install --immutable
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version` | Gewählte CLI-Version ermitteln; Starter können projektabhängig sein. |
| `list --depth=0` | Classic: direkte Abhängigkeitsansicht. |
| `install --immutable` | Modern: bei nötiger Lockänderung abbrechen. |
| `--immutable-cache` | Modern: Cacheänderungen nicht zulassen. |
| `--check-cache` | Modern: Pakete erneut holen und Prüfsummen vergleichen; nicht offline. |
| `add`, `remove`, `up` | Projektabhängigkeiten verändern, versionsabhängige Befehle. |
| `run`, `dlx` | Code ausführen, gegebenenfalls temporär herunterladen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Nur Yarn 1 Classic, nicht ausgeführt: yarn list --depth=0
```

Das Muster ist bewusst als Classic-Form markiert. Tiefe null zeigt direkte Abhängigkeiten, nicht zwingend jede transitive Bibliothek. Ohne lokale Yarninstallation wurde weder diese Form noch ein moderner Ersatz ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Anleitungen zuordnen:** Zuerst CLI-Generation und Lockformat feststellen. **Projektaktionen planen:** Manifest, Lock, Linker und ausführbare Skripte getrennt betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein argumentloser Start ist kein sicherer Ersatz für Hilfe. Plugins, yarnPath und Projektskripte können Code ausführen. Immutable ist keine Ausführungssandbox. Keine Corepack-Aktivierung, Yarninstallation, Registryabfrage oder Änderung fremder Projekte vorgenommen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| list wird anders behandelt | Classic-Anleitung auf moderner CLI oder umgekehrt. |
| Immutable-Abbruch | Lock-/Manifeststand passt nicht; nicht automatisch neu generieren. |
| node_modules fehlt | Moderne Projekte können Plug-n-Play verwenden; Linker klären. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; yarn fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `npm` | Andere CLI-/Locksemantik. |
| `pnpm` | Anderes Store-/Linkmodell. |
| `corepack` | Starterverwaltung; kann Versionen beschaffen. |

Ausgangsdatensatz 474 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
