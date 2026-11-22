---
id: "whereis"
name: "whereis"
command: "whereis"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["whereis", "grundlagen & hilfe"]
status: "Suchumfang dokumentiert; keine Programme gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 376
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale util-linux-Manpage gelesen"
---

# whereis – Programm-, Quellen- und Handbuchorte suchen

## 1. Kurzbeschreibung

`whereis` sucht zu einem Namen nach Programmdateien, Quelltexten und Handbüchern in vorgesehenen Suchorten. **Root-Rechte sind nicht nötig.** Es durchsucht nicht automatisch jede Datei des Rechners.

## 2. Was macht der Befehl?

Die lokale util-linux-Manpage beschreibt Standardsuchorte und die Berücksichtigung von `PATH` beziehungsweise `MANPATH`. Der Name wird als Suchname behandelt, nicht einfach als unveränderter vollständiger Dateipfad.

Eine gefundene Programmdatei muss nicht diejenige sein, die eine persönliche Shell tatsächlich verwenden würde. Aliase, Funktionen und andere Auflösungsregeln sind eine andere Ebene.

## 3. Syntax

```bash
whereis ls
whereis -b ls
whereis -m ls
```

Die eingeschränkten Formen wählen Programme beziehungsweise Handbücher. Die Suchergebnisse wurden für diesen Eintrag nicht als tatsächliche Pfadliste des Rechners erhoben.

## 4. Wichtige Optionen

| Option | Auswahl | Grenze |
| --- | --- | --- |
| `-b` | Programmdateien. | Kein Integritätsnachweis. |
| `-m` | Handbücher. | Dokumentation kann getrennt vorliegen. |
| `-s` | Quellorte. | Quellpakete sind häufig nicht installiert. |
| `-l` | Wirksame Suchorte anzeigen. | Erklärt die Reichweite. |
| `-B VERZEICHNISSE` | Programmsuchorte begrenzen. | Liste mit `-f` abschließen. |
| `-M VERZEICHNISSE` | Handbuchsuchorte begrenzen. | Andere Quellen bewusst auslassen. |
| `-f` | Verzeichnisliste beenden. | Danach beginnen die Suchnamen. |

## 5. Beispiel erklärt Schritt für Schritt

```bash
whereis -b ls
```

Der geplante Aufruf sucht nur nach passenden Programmdateien. Eine Ausgabe würde Fundorte darstellen, das Programm `ls` aber nicht ausführen.

Für eine konkrete manuelle Pfadbegrenzung wäre beispielsweise `whereis -b -B /usr/bin -f ls` die dokumentierte Argumentstruktur. Das ist keine Garantie, dass jede Installation dort liegt.

Beide Formen sind anhand der lokalen Manpage beschrieben, nicht als tatsächliche Fundmeldung ausgeführt.

## 6. Typische Anwendungsfälle

- Handbuch und Programmdatei zu einem Namen zuordnen.
- Suchreichweite einer Installation verstehen.
- Einen gezielt begrenzten Ort betrachten.
- Fehlende Quellpakete von vorhandenen Binärprogrammen unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Suche ist lesend. Ein Fund bestätigt weder sichere Eigentümerrechte noch passende Version oder unveränderte Inhalte.

Mehrere Fundorte sind nicht automatisch verdächtig. Unterschiedliche legitime Installationswege können nebeneinander bestehen. Vor Lösch- oder Bereinigungsmaßnahmen die tatsächliche Zuständigkeit klären.

## 8. Häufige Fehler

- **Wie Shellauflösung lesen:** Aliase und Funktionen fehlen als Kontext.
- **Keine Quellen gleich defekte Installation:** Quellen können absichtlich fehlen.
- **`-f` vergessen:** Verzeichnisliste und Namen werden falsch getrennt.
- **Vollständige Dateisuche erwartet:** Suchorte sind begrenzt.

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur den benötigten Dateityp auswählen. Für die Frage nach dem tatsächlichen Shellaufruf `type -a NAME` verwenden.

Gefundene Dateien nicht aufgrund ihres Namens ausführen oder entfernen. Herkunft und Verwendungszweck bleiben eigene Fragen.

## 10. Verwandte Befehle

- `type`: Shellauflösung.
- `command -v`: Kurze Verfügbarkeitsabfrage.
- `which`: PATH-Dateisuche.
- `man -w`: Handbuchort gezielt anzeigen.

**Prüfstand:** Lokale Manpage gelesen. Keine Funddatei gestartet, verschoben oder gelöscht.

Ausgangsdatensatz 376 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
