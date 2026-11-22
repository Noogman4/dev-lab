---
id: "help"
name: "--help"
command: "PROGRAMM --help"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["help", "grundlagen & hilfe"]
status: "Lokale Aufrufhilfen geprüft; kein eigenständiges Programm --help vorausgesetzt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 342
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-ls-Hilfe lokal mit Status 0 gelesen"
---

# --help – die Hilfeoption eines Programms richtig verwenden

## 1. Kurzbeschreibung

`--help` ist häufig eine **Option**, kein eigenständiger Linux-Befehl. Sie fordert bei unterstützenden Programmen eine kurze Bedienungsübersicht an. **Root-Rechte sind dafür normalerweise nicht nötig.**

Die richtige Form lautet beispielsweise `ls --help`. Ein allein eingegebenes `--help` sucht dagegen einen Programmnamen dieses Namens und ist kein allgemeiner Einstieg in alle Linux-Handbücher.

## 2. Was macht der Befehl?

Das angesprochene Programm entscheidet, wie es seine Argumente verarbeitet. Viele GNU-Werkzeuge zeigen mit `--help` Syntax, Optionen und einen Dokumentationsverweis. Andere Programme verwenden `-h`, eine eigene Unteraktion oder eine andere Schreibweise.

Grundlage sind die lokal gelesene GNU-ls-Hilfe und mehrere lokale Bash-Hilfetexte. Der [GNU-Hinweis zu gemeinsamen Optionen](https://www.gnu.org/s/coreutils/manual/html_node/Common-options.html) ordnet die Konvention ein; die Onlinevollseite war während der Erstellung nicht abrufbar. Daraus wird keine universelle Garantie für jedes Programm abgeleitet.

Auch ein Hilfsaufruf startet das jeweilige Programm. Bei unbekannten ausführbaren Dateien ist das Lesen eines vertrauenswürdigen Handbuchs sicherer als ihr Start nur aufgrund eines vermeintlich harmlosen Arguments.

## 3. Syntax

```bash
ls --help
```

Allgemeine Schablone:

```text
PROGRAMM --help
```

`PROGRAMM` durch einen bekannten tatsächlichen Namen ersetzen. Nicht bei einem privilegierten Änderungsauftrag zusätzlich beliebige Argumente anfügen und darauf vertrauen, dass die Hilfe jede andere Aktion sicher verdrängt.

## 4. Wichtige Optionen

| Form | Typische Aufgabe | Grenze |
| --- | --- | --- |
| `PROGRAMM --help` | Unterstützte lange Hilfeoption. | Nur verwenden, wenn dokumentiert. |
| `help cd` | Bash-Builtin-Hilfe. | Andere Oberfläche als GNU-Programmoptionen. |
| `man PROGRAMM` | Installiertes Handbuch lesen. | Benötigt passende Manpage. |
| `PROGRAMM --version` | Gegebenenfalls Version zeigen. | Ebenfalls nicht universell. |

`-h` ist nicht überall Hilfe. Bei `icat` verändert dieser Schalter beispielsweise die Behandlung von Sparse-Dateien. Deshalb keine festen Bedeutungen zwischen Programmen übertragen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Bekanntes Programm auswählen

`ls` gehört hier zur installierten GNU-Werkzeugsammlung. Der absolute Aufruf `/usr/bin/ls --help` wurde tatsächlich ausgeführt und lieferte Status `0`.

### Schritt 2: Syntax lesen

Die erste Zeile nennt die Form mit Optionen und Dateiangaben. Eckige Klammern in solchen Syntaxbeschreibungen kennzeichnen meist optionale Teile; sie werden nicht automatisch wörtlich mit eingegeben.

### Schritt 3: Eine einzelne Option nachschlagen

Die Beschreibung erklärt, was ein bestimmter Schalter macht. Erst danach wird ein normaler Arbeitsaufruf geplant. Der Hilfsaufruf selbst untersucht hier keine fremden Verzeichnisse.

### Schritt 4: Lokale Fassung bevorzugen

Ein Onlinebeispiel kann eine andere Version betreffen. Die lokale Hilfe zeigt, welche Funktionen diese Installation tatsächlich anbietet. Unklare Unterschiede bleiben ein Prüfpunkt.

## 6. Typische Anwendungsfälle

- Einen bekannten Befehl vor der ersten Verwendung kennenlernen.
- Argumentreihenfolge und Schreibweise klären.
- Eine Option vor einer Datei- oder Systemänderung verstehen.
- Ein Beispiel mit der installierten Fassung abgleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Hilfe startet Programmcode. Einen unbekannten Download deshalb nicht einfach mit `--help` ausführen. Zusätzliche Root-Rechte verbessern die Erklärung nicht und vergrößern den möglichen Schaden eines ungeeigneten Programms.

Eine kurze Hilfe kann wichtige Details auslassen. Bei destruktiven Funktionen die ausführliche Beschreibung und konkrete Zielpfade hinzunehmen.

## 8. Häufige Fehler

- **Allein `--help` eingeben:** Kein allgemeiner Hilfebefehl.
- **`-h` gleichsetzen:** Bedeutung ist programmspezifisch.
- **Unbekanntes Programm starten:** Hilfsargument schafft keine Isolation.
- **Optionsklammern kopieren:** Syntaxnotation zuerst übersetzen.
- **Keine Hilfe bekommen:** Passende Manpage oder Bash-`help` verwenden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst bekannte Programme ohne zusätzliche Rechte betrachten. Für Shell-Built-ins `help NAME`, für installierte Programme gegebenenfalls `man NAME` verwenden.

Nicht anhand einer kurzen Optionsüberschrift allein über riskante Aktionen entscheiden. Ziel, Umfang und Nebenwirkungen gehören weiterhin dazu.

## 10. Verwandte Befehle

- `help`: Bash-interne Dokumentation.
- `man`: Handbuchseiten.
- `info`: Strukturierte GNU-Handbücher.
- `apropos`: Suche nach einer Aufgabe in Handbuchbeschreibungen.

**Prüfstand:** GNU-ls-Hilfe lokal erfolgreich gelesen. Kein universeller Hilfevertrag und keine Systemaktion behauptet.

Ausgangsdatensatz 342 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
