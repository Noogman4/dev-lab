---
id: "groups"
name: "groups"
command: "groups"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["groups", "grundlagen & hilfe"]
status: "Keine persönlichen Gruppenlisten erhoben"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 355
reviewed_at: "2026-11-13"
locally_checked_version: "GNU-coreutils-Manpage 9.4 gelesen"
---

# groups – Gruppenmitgliedschaften mit dem richtigen Kontext anzeigen

## 1. Kurzbeschreibung

`groups` zeigt Gruppenmitgliedschaften. Ohne Benutzernamen betrachtet die GNU-Variante den aktuellen Prozesskontext; mit Namen fragt sie dessen Zuordnung ab. **Für übliche lesende Abfragen sind keine Root-Rechte nötig.**

## 2. Was macht der Befehl?

Die lokale Manpage weist ausdrücklich auf den Unterschied hin: Nach Änderungen der Gruppendatenbank kann die noch laufende Sitzung andere Gruppen besitzen als eine neue Abfrage für den Benutzer.

Eine angezeigte Gruppe erklärt mögliche Rechte, beweist aber nicht allein den Zugriff auf jede betreffende Ressource. Dateirechte, ACLs, Dienstregeln und andere Schutzsysteme können zusätzlich wirken.

## 3. Syntax

```text
groups
groups BENUTZERNAME
groups --help
```

`BENUTZERNAME` durch einen tatsächlich gemeinten Namen ersetzen. Für die Erklärung wird keine persönliche Kontoliste des Rechners ausgelesen.

## 4. Wichtige Optionen

Der normale Funktionsumfang ist klein:

| Form | Aufgabe | Kontext |
| --- | --- | --- |
| Ohne Namen | Gruppen des aktuellen Prozesses anzeigen. | Bereits gestartete Sitzung. |
| Mit Namen | Mitgliedschaften dieser Identität abfragen. | Aktuelle Namensdienst-/Datenbankzuordnung. |
| `--help` | Bedienung erklären. | Keine Gruppenänderung. |
| `--version` | Programmversion zeigen. | Kein Nachweis tatsächlicher Berechtigungen. |

Das Werkzeug fügt niemanden einer Gruppe hinzu und entfernt auch keine Mitgliedschaft.

## 5. Beispiel erklärt Schritt für Schritt

Angenommen, eine Mitgliedschaft wurde zuvor durch einen autorisierten Administrator geändert. Eine bereits laufende Shell muss diesen neuen Prozesskontext nicht automatisch erhalten.

Ein späterer Vergleich zwischen `groups` und `groups BENUTZERNAME` könnte deshalb unterschiedliche Ergebnisse liefern. Das ist zunächst ein Kontextunterschied, kein Beweis einer unerlaubten Kontomanipulation.

Eine neue Anmeldung kann für die beabsichtigte Sitzung relevant sein. Sie wird hier weder erzwungen noch durch einen automatischen Gruppenwechsel ersetzt. Es wurden keine echten Gruppenlisten ausgegeben.

## 6. Typische Anwendungsfälle

- Eine eigene Rechtefrage mit dem aktuellen Sitzungskontext verbinden.
- Unterschied zwischen Kontozuordnung und laufendem Prozess erklären.
- Vor einer geplanten Rechteänderung den benötigten Kontext bestimmen.
- Einen Fehlerbericht ohne vorschnelle Rechteausweitung vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Anzeige ist lesend, kann aber interne Rollen und Zugriffsmöglichkeiten offenlegen. Gruppenlisten vor öffentlicher Weitergabe auf Notwendigkeit prüfen.

Eine Mitgliedschaft kann sehr weitreichende Rechte bedeuten. Nicht einfach eine privilegierte Gruppe hinzufügen, weil eine einzelne Anwendung scheitert. Zuerst den tatsächlichen Zugriffsbedarf klären.

## 8. Häufige Fehler

- **Neue Kontozuordnung sofort in alter Shell erwartet:** Prozesskontext bleibt zunächst bestehen.
- **Gruppe gleich garantierter Zugriff:** Weitere Regeln können fehlen.
- **Name unbekannt:** Namensdienst und Schreibweise prüfen.
- **`groups` als Verwaltungstool:** Es zeigt, statt Mitgliedschaften zu ändern.

## 9. Sichere Varianten oder Tipps für Einsteiger

Für eine konkrete Diagnose nur die tatsächlich benötigte Identität betrachten. Numerische Kennungen und weitere Identitätsangaben liefert `id`.

Keine systemweite Rechteänderung aus einer einzelnen Anzeige ableiten. Beobachtung, Ursache und geplante Maßnahme getrennt dokumentieren.

## 10. Verwandte Befehle

- `id`: Benutzer- und Gruppenkennungen genauer anzeigen.
- `getent group`: Namensdienstinformationen lesen.
- `newgrp`: Gruppenbezogenen Sitzungskontext verändern.
- `usermod`: Kontoverwaltung; echte Änderung.

**Prüfstand:** Lokale Manpage gelesen. Keine Konten, Gruppen oder Sitzungsrechte verändert.

Ausgangsdatensatz 355 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
