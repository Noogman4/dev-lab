---
id: "yay"
name: "yay"
command: "yay"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "yay"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 475
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; yay fehlt; Quelle Entwicklungszweig v13.0+"
---

# yay – Yay-Standardaktion und AUR-Ausführung erkennen

## 1. Kurzbeschreibung

yay ist ein pacman-Wrapper mit AUR-Unterstützung. Ein Aufruf ohne Operation und Ziel entspricht laut Projektmanual -Syu. Er ist deshalb kein harmloser Verfügbarkeitstest.

## 2. Was macht der Befehl?

Die gelesene Projektdatei aus dem Entwicklungszweig beschreibt Yay v13.0+; lokal fehlt yay. Suchwörter ohne ausdrückliche Operation können eine Auswahl mit anschließender Installation öffnen. Repositorypakete und AUR-Buildrezepte sind unterschiedliche Vertrauensquellen. Ein Helfer automatisiert Abläufe, prüft aber nicht automatisch die Absicht jedes Rezepts.

Quelle, am 2026-11-13 gelesen: [Yay-Projekt: originale Manpage im next-Zweig](https://raw.githubusercontent.com/Jguer/yay/next/doc/yay.8)

## 3. Syntax

```text
yay OPERATION [OPTIONEN] [ZIELE]
yay --help
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-Ss TEXT` | Suche einschließlich AUR, kann Netzverkehr erzeugen. |
| `-Si PAKET` | Paketinformationen. |
| `-Q` | Installierte Pacman-Pakete abfragen. |
| `-G` | PKGBUILD herunterladen. |
| `-B` | PKGBUILD aus lokalem Verzeichnis bauen. |
| `--aur`, `--repo` | Zielauswahl begrenzen; Abhängigkeitsauflösung bleibt gesondert. |
| `-Sc` | Auch AUR-Cache bereinigen; kann eigene Quellen/Archive entfernen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
yay -Si lernpaket
```

Die Informationsform mit erfundenem Namen wurde nicht ausgeführt. Sie ist von yay lernpaket und einem argumentlosen Upgrade zu trennen. Ein Metadatentreffer wäre kein Freibrief für Download, Build oder Installation.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**AUR-Helfer vergleichen:** Jeweilige Standardaktion und Cachebehandlung prüfen. **Buildfreigabe vorbereiten:** Rezept, Quell-URLs und Skripte vor Ausführung lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

PKGBUILDs und Buildschritte führen Code aus. Automatische Bestätigungen und übersprungene Diffs reduzieren die Prüfung. Keine Paketquellen, Rezeptdateien, Buildcaches oder Bestände angefasst; kein privilegierter Helferstart.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Start aktualisiert unerwartet | Dokumentierte Standardaktion -Syu. |
| Paket nicht gefunden | Quelle und Schreibweise prüfen, keine fremden Repositories automatisch hinzufügen. |
| Build als Root verweigert | Nicht umgehen; richtige Ausführungsgrenze beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; yay fehlt; Quelle Entwicklungszweig v13.0+. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `paru` | Anderer AUR-Helfer. |
| `pacman` | Pakettransaktion. |
| `makepkg` | Ausführung des Buildrezepts. |

Ausgangsdatensatz 475 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
