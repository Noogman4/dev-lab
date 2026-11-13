---
id: "ldd"
name: "ldd"
command: "ldd"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "ldd"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 284
reviewed_at: "2026-11-13"
locally_checked_version: "ldd / glibc 2.39 (Ubuntu 2.39-0ubuntu8.9); gcc 13.3.0"
---

# ldd – Dynamische Bibliotheksabhängigkeiten nachvollziehen

## 1. Kurzbeschreibung

ldd zeigt benötigte Shared Libraries und ihre Auflösung durch den Laufzeitlinker. Es ist kein allgemeiner sicherer Scanner für unbekannte Programme. Die Originaleinstufung als sicher lesend wird wegen möglicher Codeausführung korrigiert.

## 2. Was macht der Befehl?

Beim üblichen glibc-Verfahren wird der Loader in einem Trace-Modus verwendet. Die Ausgabe nennt angeforderte Bibliotheken, gefundene Pfade und Ladeadressen; diese Adressen können sich ändern. Das ist eine Sicht auf die aktuelle Auflösung samt transitiven Abhängigkeiten. Später per dlopen geladene Komponenten werden dadurch nicht vollständig vorausgesagt. not found bezeichnet eine in diesem Kontext nicht aufgelöste Abhängigkeit, nicht zwingend eine auf dem Rechner insgesamt fehlende Datei.

Quelle, am 2026-11-13 gelesen: [Linux-man-pages: ldd](https://man7.org/linux/man-pages/man1/ldd.1.html) und lokale Manpage

## 3. Syntax

```text
ldd [OPTIONEN] DATEI...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version` | Version von ldd lesen. |
| `-v` | Zusätzliche Informationen einschließlich Symbolversionen. |
| `-u` | Unbenutzte direkte Abhängigkeiten melden; kein automatischer Löschauftrag. |
| `-d` | Datenrelokationen durchführen und fehlende Objekte melden. |
| `-r` | Auch Funktionsrelokationen verarbeiten; weitergehender Loaderbetrieb. |
| `--help` | Schnittstelle lesen, ohne ein Ziel zu laden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-284-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
ldd --version
printf '#include <stdio.h>
int main(void) { puts("Eigener Code"); return 0; }
' > lernen.c
gcc lernen.c -o lernen
env -u LD_PRELOAD -u LD_AUDIT -u LD_LIBRARY_PATH ldd ./lernen

```

### Schritt 3: Ergebnis auswerten

Beim eigenen dynamisch gelinkten Testprogramm wurde libc.so.6 zu einem Systembibliothekspfad aufgelöst; Loader und linux-vdso wurden ebenfalls angezeigt. Die konkreten Hexadressen sind kein erwarteter Festwert. Der Quelltext wurde selbst geschrieben und die Anwendung nicht direkt gestartet. Das Lesen/Laden installierter Laufzeitbibliotheken ist Teil dieses Tests, keine Änderung dieser Bibliotheken. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Abhängigkeiten eines vertrauenswürdigen eigenen Builds untersuchen. Ladefehler eingrenzen: Architektur, Suchkontext und Symbolversionen getrennt betrachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Primärhandbuch warnt ausdrücklich vor ldd auf nicht vertrauenswürdigen ausführbaren Dateien: Manche Implementierungen oder Interpreterfälle können fremden Code ausführen. Stattdessen bieten readelf -d oder objdump -p eine statische Sicht auf direkte NEEDED-Einträge, jedoch keinen vollständigen Auflösungsbaum. Auch statische Parser müssen aktuell sein. Keine LD_PRELOAD-Tricks oder ldconfig-Systemänderungen als Beispiel. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| not a dynamic executable | Statisches Programm, falsche Architektur oder ungeeignetes Format prüfen. |
| not found | Benötigten Namen und Suchregeln prüfen; keine fremden Bibliotheken blind kopieren. |
| Adressen ändern sich | Ladeadressen sind Laufzeitdetails. |
| Unbekanntes Ziel | Nicht mit ldd ausprobieren; statische Metadaten bevorzugen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** ldd / glibc 2.39 (Ubuntu 2.39-0ubuntu8.9); gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `readelf -d` | Direkte dynamische ELF-Einträge lesen. |
| `objdump -p` | Weitere statische Abhängigkeitsansicht. |
| `ld` | Linkt Artefakte beim Build, anderer Zweck als ldd. |

Ausgangsdatensatz 284 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
