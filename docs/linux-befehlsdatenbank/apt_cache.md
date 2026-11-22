---
id: "apt_cache"
name: "apt-cache"
command: "apt-cache"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Paketverwaltung", "apt-cache"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 451
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# apt-cache – Lokale Paketmetadaten richtig interpretieren

## 1. Kurzbeschreibung

apt-cache durchsucht und zeigt den lokalen APT-Metadatenbestand. Es installiert keine Pakete. Metadaten können unabhängig von gerade erreichbaren Repositories gelesen werden und veraltet sein.

## 2. Was macht der Befehl?

show beschreibt angebotene Paketversionen; policy erklärt Kandidaten und Prioritäten. depends zeigt Vorwärtsabhängigkeiten, rdepends umgekehrte Beziehungen. Ein angezeigtes Paket muss nicht installiert sein. Der Cache kann bei Bedarf erzeugt werden; eine reine Informationsaufgabe ist daher nicht automatisch ein Nachweis, dass keinerlei Cachedatei geschrieben wird.

Quelle, am 2026-11-13 gelesen: [APT-Team: apt-cache-Handbuch](https://manpages.debian.org/trixie/apt/apt-cache.8.en.html)

## 3. Syntax

```text
apt-cache [OPTIONEN] {show|search|policy|depends|rdepends} PAKET_ODER_MUSTER
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `show PAKET` | Paketdatensätze anzeigen. |
| `search REGEX` | Namen und Beschreibungen nach POSIX-Muster durchsuchen. |
| `--names-only` | Suche auf Paket-/Provide-Namen begrenzen. |
| `policy [PAKET]` | Prioritäten und Kandidaten erklären. |
| `depends`, `rdepends` | Abhängigkeitsrichtung beachten. |
| `gencaches` | Cache erzeugen; keine Repositoryaktualisierung. |
| `-o SCHLUESSEL=WERT` | Konfiguration überschreiben; Pfade sind nicht automatisch isoliert. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
apt-cache policy lernpaket
```

Das erfundene Paket wird nicht abgefragt. Installed, Candidate und Version table wären verschiedene Felder. Eine Kandidatenversion folgt Quellen und Prioritäten; sie ist nicht allein eine Aussage über die höchste irgendwo veröffentlichte Version.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Paketaufklärung:** Kandidat und Herkunft vor einer Transaktion verstehen. **Abhängigkeiten lesen:** Benötigte Pakete von abhängigen Verbrauchern unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Kein automatisches apt update als Folge einer leeren Abfrage. Cachezustand und Konfiguration beeinflussen Ergebnisse; Suchmuster mit Shellzeichen zitieren. Es wurden keine echten Paketbestände abgefragt, Caches erzeugt oder Quellen geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Candidate: (none) | Kein Kandidat unter aktueller Konfiguration; Ursache gesondert prüfen. |
| Suche liefert unerwartete Treffer | Regex und Shell-Expansion unterscheiden. |
| Abhängigkeit mehrfach aufgeführt | Alternativen und virtuelle Provides lesen, nicht jede Zeile als Pflichtinstallation deuten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt-get` | Transaktionen mit derselben Paketbasis. |
| `apt-mark` | Installationsmarkierungen. |
| `dpkg-query` | Lokaler dpkg-Status. |

Ausgangsdatensatz 451 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
