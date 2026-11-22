---
id: "whatis"
name: "whatis"
command: "whatis"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["whatis", "grundlagen & hilfe"]
status: "Keine Handbuchdatenbank verändert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 375
reviewed_at: "2026-11-13"
locally_checked_version: "man-db 2.12.0; lokale Manpage gelesen"
---

# whatis – kurze Handbuchbeschreibungen zu einem bekannten Namen lesen

## 1. Kurzbeschreibung

`whatis` zeigt Kurzbeschreibungen passender Handbuchnamen. Es hilft, wenn der Name bekannt ist und seine Aufgabe kurz eingeordnet werden soll. **Root-Rechte sind nicht nötig.**

## 2. Was macht der Befehl?

Die lokale man-db-Manpage beschreibt die Suche im Handbuchindex. Gefunden wird Dokumentation, nicht automatisch eine tatsächlich im Suchpfad ausführbare Datei.

Ein Treffer enthält normalerweise den Namen und Abschnitt. Mehrere gleichnamige Seiten können verschiedene Dinge behandeln, etwa einen Shellaufruf und eine Bibliotheksfunktion.

## 3. Syntax

```bash
whatis printf
whatis -s 1 printf
```

Die zweite Form grenzt auf Benutzerbefehle ein. Für die eingebaute Bash-Variante kann trotzdem zusätzlich `help printf` erforderlich sein.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-s ABSCHNITT` | Abschnitt auswählen. | Andere Themen bleiben ausgeblendet. |
| `-r` | Namensmuster als regulären Ausdruck lesen. | Keine Volltextsuche im Handbuch. |
| `-w` | Wildcardmuster verwenden. | Muster vor Shellauswertung quotieren. |
| `-l` | Beschreibung nicht auf Terminalbreite kürzen. | Anzeige kann breiter werden. |
| `-M PFAD` | Andere Handbuchhierarchie wählen. | Quelle und Fassung beachten. |

Für eine Aufgabe ohne bekannten Namen ist `apropos` geeigneter, weil dessen Suche auch Beschreibungen berücksichtigt.

## 5. Beispiel erklärt Schritt für Schritt

Ein geplanter Aufruf `whatis -s 1 printf` würde die passende Kurzbeschreibung suchen. Er wurde hier nicht als echte Indexsuche ausgeführt. Gelesen wurde die lokale Manpage.

Ein fiktiver Treffer `printf (1)` verweist auf Abschnitt 1. Er ist kein Beweis, dass die persönliche Shell genau diese externe Variante verwendet. Dafür wäre `type printf` die andere Frage.

Für die vollständige Bedienung anschließend `man 1 printf` lesen. Die Kurzbeschreibung allein enthält nicht alle Risiken und Besonderheiten.

## 6. Typische Anwendungsfälle

- Einen bekannten Namen kurz erklären.
- Passende Handbuchabschnitte unterscheiden.
- Dokumentation vor einer ausführlichen Lektüre auswählen.
- Verwechslungen zwischen Funktion und Benutzerprogramm vermeiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Suche ist lesend. Ein Treffer ist aber keine Empfehlung zur sofortigen Ausführung. Verwaltungsbefehle können in einer kurzen Zeile harmloser wirken, als sie tatsächlich sind.

Ein fehlender Treffer kann auf fehlende Dokumentation oder einen veralteten Index zurückgehen. Kein automatisches Installieren oder systemweites Neubauen der Datenbank daraus ableiten.

## 8. Häufige Fehler

- **Treffer gleich installierter ausführbarer Befehl:** Andere Datenquelle.
- **Kurzbeschreibung als komplette Anleitung:** Details fehlen.
- **Muster unquotiert:** Shell kann Namen verändern.
- **Keine Beschreibung gleich Funktion fehlt:** Index und Dokumentation prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem genauen Namen anfangen, dann bei Bedarf den Abschnitt festlegen. Für die konkrete Ausführung die tatsächlich verwendete Variante und ihre lokale Hilfe betrachten.

Eine neue Datenbankerstellung über `mandb` ist eine separate Verwaltungsaktion und für die Dokumentation hier nicht erforderlich.

## 10. Verwandte Befehle

- `man -f`: Entsprechende Kurzbeschreibungssuche.
- `apropos`: Nach Aufgaben und Stichwörtern suchen.
- `man`: Vollständige Seite lesen.
- `type`: Tatsächliche Shellauflösung.

**Prüfstand:** Lokale Manpage gelesen. Keine Indexaktualisierung, Paketinstallation oder Arbeitsaktion ausgeführt.

Ausgangsdatensatz 375 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
