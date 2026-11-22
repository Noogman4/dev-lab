---
id: "apropos"
name: "apropos"
command: "apropos"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["apropos", "grundlagen & hilfe"]
status: "Lokale Manpage geprüft; keine Datenbank neu aufgebaut"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 344
reviewed_at: "2026-11-13"
locally_checked_version: "man-db 2.12.0; lokale Manpage gelesen"
---

# apropos – Handbuchseiten nach einer Aufgabe suchen

## 1. Kurzbeschreibung

`apropos` sucht in Namen und Kurzbeschreibungen installierter Handbuchseiten. Es hilft, wenn die Aufgabe bekannt ist, der passende Befehlsname aber fehlt. **Root-Rechte sind für die Suche nicht nötig.**

## 2. Was macht der Befehl?

Grundlage ist die lokale man-db-Manpage. Gesucht wird in einem vorbereiteten Handbuchindex, nicht in sämtlichen Dateien und nicht automatisch im Internet. Ein Treffer beschreibt ein Thema; das zugehörige Programm wird nicht gestartet.

Die Ergebnisliste enthält normalerweise Name, Handbuchabschnitt und Kurzbeschreibung. Ein Name kann in verschiedenen Abschnitten vorkommen und dort unterschiedliche Dinge bezeichnen.

Eine erfolglose Suche beweist nicht, dass die Aufgabe unter Linux unmöglich ist. Handbuch, Index, Sprache oder Suchbegriff können fehlen beziehungsweise nicht passen.

## 3. Syntax

```bash
apropos archive
apropos -s 1 archive
apropos -w '*archive*'
```

Suchmuster quotieren, damit die Shell sie nicht vorher als Dateimuster expandiert. Die Beispiele wurden nicht als tatsächliche lokale Katalogsuche ausgeführt; die Syntax stammt aus der gelesenen Manpage.

## 4. Wichtige Optionen

| Option | Zweck | Auswahlgrenze |
| --- | --- | --- |
| `-r` | Regulären Ausdruck verwenden. | Dokumentierter Standard. |
| `-w` | Wildcardmuster verwenden. | Andere Mustersprache. |
| `-e` | Exakte Suche wählen. | Kann viele ähnliche Treffer ausblenden. |
| `-a` | Alle Suchbegriffe verlangen. | Sonst ist die Auswahl breiter. |
| `-s 1` | Auf Handbuchabschnitt 1 begrenzen. | Andere Abschnitte bleiben ausgeschlossen. |
| `-l` | Lange Zeilen nicht kürzen. | Hilfreich für vollständige Beschreibungen. |
| `-M PFAD` | Andere Handbuchhierarchie wählen. | Nur bekannte Quellen verwenden. |

Eine eingeschränkte Suche kann übersichtlicher sein, aber auch die gesuchte Seite absichtlich ausblenden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Aufgabe statt Programmnamen nennen

Für Archivwerkzeuge ist ein Begriff wie `archive` ein möglicher Einstieg. Englische Begriffe können nützlich sein, wenn die installierten Kurzbeschreibungen englisch sind.

### Schritt 2: Ergebnis mit Abschnitt lesen

Ein fiktiver Treffer `tar (1)` verweist auf eine Benutzerbefehl-Manpage. Ein gleichnamiger Treffer aus Abschnitt 3 könnte dagegen eine Programmierfunktion betreffen. Diese fiktive Zeile ist keine gemessene Suchausgabe.

### Schritt 3: Passende Seite gezielt öffnen

```bash
man 1 tar
```

Das wäre der anschließende Dokumentationsschritt. Er startet nicht die Archivoperation `tar`. Vor einer echten Nutzung erst die gewünschten Optionen und Ziele lesen.

## 6. Typische Anwendungsfälle

- Einen Befehlsnamen zu einer bekannten Aufgabe finden.
- Verwandte Handbuchthemen entdecken.
- Benutzerbefehle von Bibliotheksfunktionen unterscheiden.
- Eine bekannte Suche auf einen passenden Abschnitt begrenzen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Suche ist lesend. Ein Treffer ist trotzdem keine Empfehlung, den genannten Befehl sofort auszuführen. Besonders Verwaltungs- und Löschwerkzeuge können Folgen haben, die ihre Kurzbeschreibung nicht vollständig erklärt.

Eine andere Handbuchhierarchie kann andere Fassungen enthalten. Herkunft und lokale Programmversion für spätere konkrete Aufrufe berücksichtigen.

## 8. Häufige Fehler

- **Kein Treffer:** Begriff und Sprache ändern, ohne sofort Pakete zu installieren.
- **Wildcard unquotiert:** Shell hat das Muster möglicherweise bereits verändert.
- **Falscher Abschnitt:** Seite gezielt mit Abschnitt öffnen.
- **Index veraltet:** Als möglichen Grund benennen; nicht ungefragt systemweit neu aufbauen.
- **Treffer als ausgeführten Test ansehen:** Es wurde nur Dokumentation gefunden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem einfachen Begriff beginnen und danach eingrenzen. Den vollständigen Eintrag lesen, bevor eine Operation auf echte Daten geplant wird.

Für einen bereits bekannten Namen ist `whatis` oft direkter. Für die ausführliche Bedienung folgt `man`.

## 10. Verwandte Befehle

- `man -k`: Entsprechende Stichwortsuche.
- `whatis`: Kurzbeschreibung zu einem Namen.
- `man`: Ausführliche Handbuchseite.
- `info`: Weitere strukturierte Dokumentation.

**Prüfstand:** Lokale Manpage gelesen. Kein Indexupdate, keine Installation und kein gefundener Arbeitsbefehl ausgeführt.

Ausgangsdatensatz 344 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
