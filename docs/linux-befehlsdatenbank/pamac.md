---
id: "pamac"
name: "pamac"
command: "pamac"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "pamac"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 466
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; pamac fehlt"
---

# pamac – Pamac-CLI von Oberfläche und AUR-Build trennen

## 1. Kurzbeschreibung

pamac ist die Kommandozeilenoberfläche zu libpamac. pamac-manager ist die grafische Oberfläche. Unterstützte zusätzliche Paketquellen hängen vom Build und der Konfiguration ab.

## 2. Was macht der Befehl?

Die früheren Wikiadressen waren nicht erreichbar; geprüft wurden die originale Projektbeschreibung und die CLI-Quelldatei mit Parser und Hilfetexten. list zeigt standardmäßig Installiertes, search kann nach Quelle gefiltert werden. build ist ein AUR-/PKGBUILD-Pfad und nicht gleichbedeutend mit einer harmlosen Metadatensuche.

Quelle, am 2026-11-13 gelesen: [Manjaro: Projektbeschreibung](https://raw.githubusercontent.com/manjaro/pamac/master/README.md) und [pamac-cli: originaler Parser/Hilfetexte](https://raw.githubusercontent.com/manjaro/pamac-cli/master/src/cli.vala)

## 3. Syntax

```text
pamac [--help|--version]
pamac {list|search|info|install|build|upgrade|remove} [OPTIONEN] [ZIELE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list --installed` | Installierte Pakete anzeigen. |
| `search --installed TEXT` | Installierten Bestand durchsuchen. |
| `search --repos TEXT` | Repositorysuche wählen. |
| `info --no-aur PAKET` | AUR-Suche für diese Informationsform abschalten. |
| `clone` | Builddateien herunterladen; schreibt Dateien. |
| `build` | PKGBUILD vorbereiten/ausführen und Transaktion planen. |
| `--dry-run` | Nur bei unterstützten Änderungsunterbefehlen; kein pauschaler globaler Schalter. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
pamac list --installed
```

Das nicht ausgeführte Muster wäre eine Bestandsanzeige. Es beweist keine Vollständigkeit anderer Ökosysteme wie Flatpak oder Snap. Die lokale CLI fehlt; auch die im Quelltext gelesene Option ist deshalb nicht auf diesem Rechner funktional geprüft.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Manjaro-Anleitungen verstehen:** CLI, GUI und Paketquellen unterscheiden. **AUR-Bewertung:** Buildrezept und Quelle vor Ausführung separat prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Buildrezepte sind ausführbarer Code, keine passiven Paketbeschreibungen. Transaktionen können privilegiert über Dienste vermittelt werden. Kein GUI-/Daemonstart, keine Downloads, Builds, Cachebereinigung oder Paketänderung vorgenommen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| AUR not supported | Build-/Konfigurationsgrenze, keine automatische Aktivierung. |
| Option unbekannt | Unterbefehl und lokale Version prüfen. |
| Paket nur im AUR | Andere Vertrauenskette als Distributionsrepository. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; pamac fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pacman` | libalpm-basierte andere CLI. |
| `pamac-manager` | Grafische Oberfläche, nicht dieser Aufruf. |
| `makepkg` | Ausführung von Buildrezepten. |

Ausgangsdatensatz 466 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
